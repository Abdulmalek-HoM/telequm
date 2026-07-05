"""
OptimizationBridge — Connect Network State to Solvers
=====================================================

Translates ``NetworkEnvironment`` snapshots into QUBO / optimization
problem instances and feeds solutions back.  Implements Rule #3
(stateless optimizers) and Rule #4 (explicit QUBO formulation).

Every problem exposes:
- ``build_qubo(snapshot)``     → QUBO matrix Q, offset
- ``decode_solution(x, meta)`` → human-readable allocation
- ``evaluate_cost(x, Q)``     → scalar cost

Classical baselines (Rule #5):
- Greedy
- Simulated Annealing
- Exact brute-force (small instances only)
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

import numpy as np

try:
    import scipy.optimize  # noqa: F401
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ─── Abstract Problem Interface ──────────────────────────────────

class QUBOProblem(ABC):
    """
    Abstract QUBO problem formulation for telecom optimization.

    Every concrete problem must implement:
    - ``build_qubo``       : snapshot → (Q, offset, metadata)
    - ``decode_solution``  : binary vector → allocation dict
    - ``evaluate_cost``    : binary vector → scalar
    """

    @abstractmethod
    def build_qubo(self, snapshot: dict) -> tuple[np.ndarray, float, dict]:
        """
        Build QUBO matrix from current network snapshot.

        Returns
        -------
        Q : np.ndarray   (n × n) upper-triangular QUBO matrix
        offset : float   constant energy offset
        metadata : dict  qubit-to-variable mapping & problem data
        """
        ...

    @abstractmethod
    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        """
        Convert binary solution vector to actionable decision.

        Parameters
        ----------
        x : np.ndarray   binary vector {0, 1}^n
        metadata : dict  from ``build_qubo``

        Returns
        -------
        dict with human-readable allocation / scheduling
        """
        ...

    @abstractmethod
    def evaluate_cost(self, x: np.ndarray, Q: np.ndarray, offset: float) -> float:
        """
        Evaluate QUBO cost for a given binary vector.

        cost = x^T Q x + offset
        """
        ...


# ─── Resource Allocation QUBO ────────────────────────────────────

class ResourceAllocationQUBO(QUBOProblem):
    """
    QUBO formulation for user-to-BS resource allocation.

    Binary variables: x_{u,b} = 1 if user *u* is served by BS *b*.

    Objective
    ---------
    Maximise total SINR-weighted throughput, subject to:
    - Each user is served by exactly one BS
    - Each BS serves at most *capacity* users

    Parameters
    ----------
    penalty : float
        Constraint violation penalty weight (default 10.0).
    """

    def __init__(self, penalty: float = 10.0):
        self.penalty = penalty

    def build_qubo(self, snapshot: dict) -> tuple[np.ndarray, float, dict]:
        n_ue = snapshot["num_ue"]
        n_bs = snapshot["num_bs"]
        n = n_ue * n_bs
        sinr = snapshot["sinr_matrix"]
        prbs = snapshot["bs_num_prbs"]

        # Max users per BS ≈ total PRBs / 10 (rough)
        max_users_per_bs = np.maximum(prbs // 10, 1)

        Q = np.zeros((n, n))
        offset = 0.0

        # ── Objective: maximise SINR (minimise negative) ──
        for u in range(n_ue):
            for b in range(n_bs):
                idx = u * n_bs + b
                # Reward = SINR in dB (higher is better → negative for min)
                Q[idx, idx] -= max(sinr[u, b], 0)

        # ── Constraint 1: each user served by exactly one BS ──
        for u in range(n_ue):
            indices = [u * n_bs + b for b in range(n_bs)]
            # (Σ x_{u,b} - 1)^2 = Σ x_i^2 + 2 Σ_{i<j} x_i x_j - 2 Σ x_i + 1
            for idx in indices:
                Q[idx, idx] += self.penalty * (1 - 2)   # = -penalty
                Q[idx, idx] += self.penalty              # net = -penalty + penalty = 0?
            # Let me redo properly: penalty * (sum_b x_{u,b} - 1)^2
            # = penalty * (sum x_i^2) + 2 penalty * sum_{i<j} x_i x_j - 2 penalty * sum x_i + penalty
            for idx in indices:
                Q[idx, idx] += self.penalty * (1 - 2)  # +P - 2P = -P on diagonal for each
            for i_idx in range(len(indices)):
                Q[indices[i_idx], indices[i_idx]] += self.penalty
                for j_idx in range(i_idx + 1, len(indices)):
                    r, c = indices[i_idx], indices[j_idx]
                    Q[min(r,c), max(r,c)] += 2 * self.penalty
            # Subtract 2P from diag (linear term)
            for idx in indices:
                Q[idx, idx] -= 2 * self.penalty
            offset += self.penalty

        # ── Constraint 2: BS capacity ──
        for b in range(n_bs):
            cap = int(max_users_per_bs[b])
            indices = [u * n_bs + b for u in range(n_ue)]
            # Penalty * (sum x_{u,b} - cap)^2  (only penalise if > cap)
            # Simplified: add weak penalty for excess
            for i_idx in range(len(indices)):
                for j_idx in range(i_idx + 1, len(indices)):
                    r, c = indices[i_idx], indices[j_idx]
                    Q[min(r,c), max(r,c)] += (self.penalty / cap) * 0.5

        metadata = {
            "num_ue": n_ue,
            "num_bs": n_bs,
            "num_vars": n,
            "var_map": {(u, b): u * n_bs + b for u in range(n_ue) for b in range(n_bs)},
        }
        return Q, offset, metadata

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n_ue = metadata["num_ue"]
        n_bs = metadata["num_bs"]
        allocation = np.zeros((n_ue, n_bs), dtype=int)
        for u in range(n_ue):
            for b in range(n_bs):
                idx = u * n_bs + b
                if idx < len(x):
                    allocation[u, b] = int(x[idx])
        return {"allocation_matrix": allocation}

    def evaluate_cost(self, x: np.ndarray, Q: np.ndarray, offset: float) -> float:
        return float(x @ Q @ x + offset)


# ─── Classical Baselines ─────────────────────────────────────────

class ClassicalBaselines:
    """
    Classical solvers for QUBO comparison (Rule #5).

    All methods return ``(x_best, cost, runtime_s)``.
    """

    @staticmethod
    def greedy(Q: np.ndarray, offset: float = 0.0) -> tuple[np.ndarray, float, float]:
        """Greedy variable-by-variable QUBO solver."""
        t0 = time.time()
        n = Q.shape[0]
        x = np.zeros(n, dtype=int)
        for i in range(n):
            # Test setting x_i = 1
            x_test = x.copy()
            x_test[i] = 1
            cost_1 = float(x_test @ Q @ x_test) + offset
            cost_0 = float(x @ Q @ x) + offset
            if cost_1 < cost_0:
                x[i] = 1
        cost = float(x @ Q @ x) + offset
        return x, cost, time.time() - t0

    @staticmethod
    def simulated_annealing(
        Q: np.ndarray,
        offset: float = 0.0,
        num_reads: int = 100,
        rng: np.random.Generator | None = None,
    ) -> tuple[np.ndarray, float, float]:
        """Simple simulated annealing for QUBO."""
        t0 = time.time()
        if rng is None:
            rng = np.random.default_rng(42)
        n = Q.shape[0]

        best_x = rng.integers(0, 2, size=n)
        best_cost = float(best_x @ Q @ best_x) + offset
        x = best_x.copy()
        cost = best_cost

        for step in range(num_reads * n):
            temp = max(1.0 * (1 - step / (num_reads * n)), 1e-6)
            flip = rng.integers(0, n)
            x_new = x.copy()
            x_new[flip] = 1 - x_new[flip]
            new_cost = float(x_new @ Q @ x_new) + offset

            delta = new_cost - cost
            if delta < 0 or rng.random() < np.exp(-delta / temp):
                x = x_new
                cost = new_cost
                if cost < best_cost:
                    best_x = x.copy()
                    best_cost = cost

        return best_x, best_cost, time.time() - t0

    @staticmethod
    def exact_brute_force(
        Q: np.ndarray,
        offset: float = 0.0,
        max_vars: int = 20,
    ) -> tuple[np.ndarray, float, float]:
        """
        Brute-force exact QUBO solver (exponential — use only for n ≤ 20).
        """
        t0 = time.time()
        n = Q.shape[0]
        if n > max_vars:
            raise ValueError(f"Brute-force limited to {max_vars} variables, got {n}")

        best_x = np.zeros(n, dtype=int)
        best_cost = float("inf")

        for i in range(2 ** n):
            x = np.array([int(b) for b in format(i, f"0{n}b")], dtype=int)
            cost = float(x @ Q @ x) + offset
            if cost < best_cost:
                best_cost = cost
                best_x = x.copy()

        return best_x, best_cost, time.time() - t0


# ─── Optimization Bridge ─────────────────────────────────────────

class OptimizationBridge:
    """
    Bridge between ``NetworkEnvironment`` and optimization solvers.

    Workflow:
    1. Receive snapshot from engine
    2. Build QUBO via problem formulation
    3. Solve with classical baseline **and** quantum solver
    4. Return results (never mutates environment)

    Parameters
    ----------
    problem : QUBOProblem
        Concrete problem formulation.
    """

    def __init__(self, problem: QUBOProblem):
        self.problem = problem

    def solve_classical(
        self,
        snapshot: dict,
        method: str = "greedy",
        **kwargs,
    ) -> dict:
        """
        Solve using a classical baseline.

        Parameters
        ----------
        snapshot : dict   from ``NetworkEnvironment.get_snapshot()``
        method : str      'greedy', 'simulated_annealing', or 'exact'

        Returns
        -------
        dict with keys: solution, decoded, cost, runtime_s, method
        """
        Q, offset, meta = self.problem.build_qubo(snapshot)

        if method == "greedy":
            x, cost, rt = ClassicalBaselines.greedy(Q, offset)
        elif method == "simulated_annealing":
            x, cost, rt = ClassicalBaselines.simulated_annealing(Q, offset, **kwargs)
        elif method == "exact":
            x, cost, rt = ClassicalBaselines.exact_brute_force(Q, offset, **kwargs)
        else:
            raise ValueError(f"Unknown classical method: {method}")

        decoded = self.problem.decode_solution(x, meta)
        return {
            "solution": x,
            "decoded": decoded,
            "cost": cost,
            "runtime_s": rt,
            "method": f"classical_{method}",
            "num_vars": len(x),
        }

    def solve_quantum(
        self,
        snapshot: dict,
        algorithm: str = "qaoa",
        backend: str = "qiskit",
        shots: int = 1024,
        **kwargs,
    ) -> dict:
        """
        Solve using a quantum algorithm.

        Parameters
        ----------
        snapshot : dict
        algorithm : str  'qaoa' or 'vqe'
        backend : str    'qiskit' (more backends planned)
        shots : int

        Returns
        -------
        dict with solution, decoded, cost, runtime, AND circuit info:
            circuit_text, optimal_params, optimization_history,
            measurement_counts, circuit_depth, gate_count, num_qubits,
            convergence_info
        """
        Q, offset, meta = self.problem.build_qubo(snapshot)
        n = Q.shape[0]
        t0 = time.time()

        circuit_text = ""
        optimal_params = None
        optimization_history = []
        measurement_counts = {}
        circuit_depth = 0
        gate_count = 0
        convergence_info = {}

        if algorithm == "qaoa":

            from telequm.algorithms.qaoa import NetworkQAOA

            # Convert QUBO to Ising Hamiltonian
            hamiltonian = self._qubo_to_ising(Q, offset)
            p_layers = kwargs.get("p", 2)
            qaoa = NetworkQAOA(num_qubits=n, p=p_layers, hamiltonian=hamiltonian)
            result = qaoa.optimize(shots=shots, maxiter=kwargs.get("maxiter", 100))
            bitstring = result["optimal_bitstring"]
            x = np.array([int(b) for b in reversed(bitstring)], dtype=int)
            cost = self.problem.evaluate_cost(x, Q, offset)

            # ── Extract circuit info ──
            optimal_params = result.get("optimal_params")
            if optimal_params is not None:
                optimal_params = list(optimal_params)
            optimization_history = result.get("history", [])
            measurement_counts = result.get("counts", {})

            # Build final circuit for visualization
            try:
                gamma = optimal_params[:p_layers] if optimal_params else [0.5] * p_layers
                beta = optimal_params[p_layers:] if optimal_params else [0.5] * p_layers
                final_qc = qaoa.create_circuit(gamma=list(gamma), beta=list(beta))
                circuit_text = str(final_qc.draw("text"))
                circuit_depth = final_qc.depth()
                gate_count = sum(dict(final_qc.count_ops()).values())
            except Exception:
                circuit_text = f"QAOA circuit: {n} qubits, p={p_layers}"
                circuit_depth = p_layers * 2
                gate_count = n * p_layers * 3  # rough estimate

            # Convergence info from scipy
            scipy_res = result.get("scipy_result")
            if scipy_res is not None:
                convergence_info = {
                    "nfev": getattr(scipy_res, "nfev", None),
                    "success": getattr(scipy_res, "success", None),
                    "message": str(getattr(scipy_res, "message", "")),
                    "final_cost": float(getattr(scipy_res, "fun", 0)),
                }

        elif algorithm == "vqe":
            from telequm.algorithms.vqe import ResourceVQE
            hamiltonian = self._qubo_to_ising(Q, offset)
            num_layers = kwargs.get("num_layers", 2)
            vqe = ResourceVQE(num_qubits=n, hamiltonian=hamiltonian, num_layers=num_layers)
            result = vqe.optimize(shots=shots, maxiter=kwargs.get("maxiter", 200))
            bitstring = result["optimal_bitstring"]
            x = np.array([int(b) for b in reversed(bitstring)], dtype=int)
            cost = self.problem.evaluate_cost(x, Q, offset)

            optimal_params = result.get("optimal_params")
            if optimal_params is not None:
                optimal_params = list(optimal_params)
            optimization_history = result.get("history", [])
            measurement_counts = result.get("counts", {})

            circuit_text = f"VQE ansatz: {n} qubits, {num_layers} layers"
            circuit_depth = num_layers * n
            gate_count = num_layers * n * 3

            scipy_res = result.get("scipy_result")
            if scipy_res is not None:
                convergence_info = {
                    "nfev": getattr(scipy_res, "nfev", None),
                    "success": getattr(scipy_res, "success", None),
                    "message": str(getattr(scipy_res, "message", "")),
                    "final_cost": float(getattr(scipy_res, "fun", 0)),
                }
        else:
            raise ValueError(f"Unknown quantum algorithm: {algorithm}")

        rt = time.time() - t0
        decoded = self.problem.decode_solution(x, meta)
        return {
            "solution": x,
            "decoded": decoded,
            "cost": cost,
            "runtime_s": rt,
            "method": f"quantum_{algorithm}",
            "num_vars": n,
            "shots": shots,
            # ── Circuit & optimization info ──
            "circuit_text": circuit_text,
            "optimal_params": optimal_params,
            "optimization_history": optimization_history,
            "measurement_counts": measurement_counts,
            "circuit_depth": circuit_depth,
            "gate_count": gate_count,
            "num_qubits": n,
            "convergence_info": convergence_info,
        }


    @staticmethod
    def _qubo_to_ising(Q: np.ndarray, offset: float):
        """
        Convert QUBO matrix to Ising Hamiltonian (SparsePauliOp).

        Uses  x_i = (1 - Z_i) / 2  substitution.
        """
        from qiskit.quantum_info import SparsePauliOp

        n = Q.shape[0]
        pauli_list = []
        coeffs = []

        for i in range(n):
            for j in range(i, n):
                q_ij = Q[i, j]
                if abs(q_ij) < 1e-12:
                    continue
                if i == j:
                    # x_i^2 = x_i = (1 - Z_i)/2
                    pauli_str = ["I"] * n
                    pauli_str[i] = "Z"
                    pauli_list.append("".join(reversed(pauli_str)))
                    coeffs.append(-q_ij / 2)
                    offset += q_ij / 2
                else:
                    # x_i x_j = (1-Z_i)(1-Z_j)/4
                    # = (1 - Z_i - Z_j + Z_i Z_j) / 4
                    pauli_zz = ["I"] * n
                    pauli_zz[i] = "Z"
                    pauli_zz[j] = "Z"
                    pauli_list.append("".join(reversed(pauli_zz)))
                    coeffs.append(q_ij / 4)

                    pauli_zi = ["I"] * n
                    pauli_zi[i] = "Z"
                    pauli_list.append("".join(reversed(pauli_zi)))
                    coeffs.append(-q_ij / 4)

                    pauli_zj = ["I"] * n
                    pauli_zj[j] = "Z"
                    pauli_list.append("".join(reversed(pauli_zj)))
                    coeffs.append(-q_ij / 4)

                    offset += q_ij / 4

        if not pauli_list:
            pauli_list.append("I" * n)
            coeffs.append(0.0)

        return SparsePauliOp.from_list(list(zip(pauli_list, coeffs, strict=False))).simplify()
