"""
Additional Telecom Problem Formulations
========================================

- RoutingOptimization: shortest weighted path
- BeamSelection: discrete beam selection from codebook
- EnergyEfficiency: cell on/off + user reassignment
- HandoverOptimization: minimise unnecessary handovers
- BSPlacementProblem: facility location for BS siting
- QuantumNetworkRouting: fidelity-weighted path for quantum networks
"""

from __future__ import annotations

import numpy as np

from telequm.core.network_snapshot import UniversalNetworkSnapshot
from telequm.problems.base_problem import BaseProblem


class RoutingOptimization(BaseProblem):
    """
    Shortest-path routing QUBO.

    Variables: x_{i,j} ∈ {0,1} — edge (i,j) included in path.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0):
        super().__init__(snapshot)
        self.penalty = penalty

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n = self.snapshot.num_cells
        Q = np.zeros((n * n, n * n))
        offset = 0.0
        sinr = self.snapshot.sinr_matrix if self.snapshot.num_users > 0 else np.zeros((1, n))

        # Edge cost: inverse of max SINR on that link
        for i in range(n):
            for j in range(n):
                if i != j:
                    idx = i * n + j
                    avg_sinr = np.mean(sinr[:, j]) if sinr.shape[0] > 0 else 0
                    Q[idx, idx] = -max(avg_sinr, 0.1)

        metadata = {"num_nodes": n, "num_vars": n * n}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n = metadata["num_nodes"]
        edges = []
        for i in range(n):
            for j in range(n):
                if x[i * n + j] == 1:
                    edges.append((i, j))
        return {"edges": edges}

    def compute_metrics(self, solution: dict) -> dict:
        return {"num_edges": len(solution.get("decoded", {}).get("edges", []))}


class BeamSelection(BaseProblem):
    """
    Discrete beam selection from codebook QUBO.

    Variables: x_{u,b} ∈ {0,1} — user u uses beam b.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, num_beams: int = 8, penalty: float = 10.0):
        super().__init__(snapshot)
        self.num_beams = num_beams
        self.penalty = penalty

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n = n_ue * self.num_beams
        Q = np.zeros((n, n))
        offset = 0.0
        rng = np.random.default_rng(42)
        beam_gains = rng.uniform(0, 1, (n_ue, self.num_beams))

        for u in range(n_ue):
            for b in range(self.num_beams):
                idx = u * self.num_beams + b
                Q[idx, idx] -= beam_gains[u, b]

        # One beam per user
        for u in range(n_ue):
            indices = [u * self.num_beams + b for b in range(self.num_beams)]
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    r, c = min(indices[i], indices[j]), max(indices[i], indices[j])
                    Q[r, c] += 2 * self.penalty

        metadata = {"num_ue": n_ue, "num_beams": self.num_beams, "num_vars": n}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        assignments = {}
        for u in range(metadata["num_ue"]):
            for b in range(metadata["num_beams"]):
                if x[u * metadata["num_beams"] + b] == 1:
                    assignments[u] = b
        return {"beam_assignments": assignments}

    def compute_metrics(self, solution: dict) -> dict:
        return {"num_assigned": len(solution.get("decoded", {}).get("beam_assignments", {}))}


class EnergyEfficiency(BaseProblem):
    """
    Cell on/off + user reassignment for energy savings.

    Variables: y_c ∈ {0,1} — cell c is ON; x_{u,c} — user assignment.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0,
                 power_per_cell_w: float = 500.0):
        super().__init__(snapshot)
        self.penalty = penalty
        self.power_per_cell = power_per_cell_w

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n_cell = self.snapshot.num_cells
        n_y = n_cell
        n_x = n_ue * n_cell
        n = n_y + n_x
        Q = np.zeros((n, n))
        offset = 0.0

        # Energy cost: penalise active cells
        for c in range(n_cell):
            Q[c, c] += self.power_per_cell / 1000  # normalised

        # SINR reward for assignments
        sinr = self.snapshot.sinr_matrix
        for u in range(n_ue):
            for c in range(n_cell):
                idx = n_y + u * n_cell + c
                Q[idx, idx] -= max(sinr[u, c], 0)

        metadata = {"num_ue": n_ue, "num_cells": n_cell, "num_vars": n, "n_y": n_y}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n_cell = metadata["num_cells"]
        metadata["n_y"]
        active_cells = [c for c in range(n_cell) if x[c] == 1]
        return {"active_cells": active_cells, "energy_saved_pct": (1 - len(active_cells) / n_cell) * 100}

    def compute_metrics(self, solution: dict) -> dict:
        decoded = solution.get("decoded", {})
        return {
            "active_cells": len(decoded.get("active_cells", [])),
            "energy_saved_pct": decoded.get("energy_saved_pct", 0),
        }


class HandoverOptimization(BaseProblem):
    """
    Handover minimisation QUBO.

    Variables: x_{u,c} — user u assigned to cell c.
    Penalises assignments that differ from current serving cell.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0,
                 handover_cost: float = 5.0):
        super().__init__(snapshot)
        self.penalty = penalty
        self.handover_cost = handover_cost

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n_cell = self.snapshot.num_cells
        n = n_ue * n_cell
        Q = np.zeros((n, n))
        offset = 0.0
        sinr = self.snapshot.sinr_matrix
        serving = self.snapshot.user_serving_cells

        for u in range(n_ue):
            for c in range(n_cell):
                idx = u * n_cell + c
                # SINR reward
                Q[idx, idx] -= max(sinr[u, c], 0)
                # Handover penalty
                if serving[u] >= 0 and c != serving[u]:
                    Q[idx, idx] += self.handover_cost

        metadata = {"num_ue": n_ue, "num_cells": n_cell, "num_vars": n}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n_cell = metadata["num_cells"]
        serving = self.snapshot.user_serving_cells
        handovers = 0
        for u in range(metadata["num_ue"]):
            for c in range(n_cell):
                if x[u * n_cell + c] == 1 and serving[u] >= 0 and c != serving[u]:
                    handovers += 1
        return {"num_handovers": handovers, "allocation_matrix": x}

    def compute_metrics(self, solution: dict) -> dict:
        return {"num_handovers": solution.get("decoded", {}).get("num_handovers", 0)}


class BSPlacementProblem(BaseProblem):
    """
    Base Station Placement — Facility Location QUBO.

    Given K candidate sites and U users, decide which sites to
    activate.  Variables: y_k ∈ {0,1} — site k is built.

    Objective: maximise coverage (SINR) minus building cost.
    Constraint: total active sites ≤ budget.
    """

    def __init__(
        self,
        snapshot: UniversalNetworkSnapshot,
        penalty: float = 10.0,
        build_cost: float = 1.0,
        max_sites: int | None = None,
    ):
        super().__init__(snapshot)
        self.penalty = penalty
        self.build_cost = build_cost
        # Default: can build at most ceil(K/2) sites
        self.max_sites = max_sites or max(1, (snapshot.num_cells + 1) // 2)

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n_cell = self.snapshot.num_cells
        n_ue = self.snapshot.num_users
        # --- site selection vars: y_k for k in [0, n_cell) ---
        n = n_cell
        Q = np.zeros((n, n))
        offset = 0.0
        sinr = self.snapshot.sinr_matrix  # (n_ue, n_cell)

        # Reward: aggregate SINR coverage each site provides
        for k in range(n_cell):
            coverage = float(np.sum(np.maximum(sinr[:, k], 0)))
            Q[k, k] -= coverage
            # Building cost
            Q[k, k] += self.build_cost

        # Budget constraint: (Σ y_k - B)^2  (soft)
        B = self.max_sites
        for i in range(n_cell):
            Q[i, i] += self.penalty * (1 - 2 * B)
            for j in range(i + 1, n_cell):
                Q[i, j] += 2 * self.penalty
        offset += self.penalty * B * B

        metadata = {"num_cells": n_cell, "num_ue": n_ue, "num_vars": n,
                     "max_sites": self.max_sites}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        selected = [k for k in range(metadata["num_cells"]) if x[k] == 1]
        return {
            "selected_sites": selected,
            "num_selected": len(selected),
            "budget": metadata["max_sites"],
        }

    def compute_metrics(self, solution: dict) -> dict:
        dec = solution.get("decoded", {})
        return {
            "sites_selected": dec.get("num_selected", 0),
            "budget": dec.get("budget", 0),
            "utilisation_pct": (dec.get("num_selected", 0) / max(dec.get("budget", 1), 1)) * 100,
        }


class QuantumNetworkRouting(BaseProblem):
    """
    Quantum Network Routing — Fidelity-Weighted Path QUBO.

    Route entanglement or QKD keys through a network of quantum
    repeaters.  Each link has a fidelity F_{ij} ∈ (0,1]; the total
    path fidelity is the product along the path.

    We convert to an additive objective by taking −log(F), so the
    QUBO minimises total loss, which is equivalent to maximising
    end-to-end fidelity.

    Variables: x_{i,j} ∈ {0,1} — link (i,j) selected.
    """

    def __init__(
        self,
        snapshot: UniversalNetworkSnapshot,
        penalty: float = 10.0,
        base_fidelity: float = 0.95,
    ):
        super().__init__(snapshot)
        self.penalty = penalty
        self.base_fidelity = base_fidelity

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n = self.snapshot.num_cells  # nodes = repeater sites
        num_vars = n * n
        Q = np.zeros((num_vars, num_vars))
        offset = 0.0

        np.random.default_rng(42)
        # Assign per-link fidelities based on distance
        positions = self.snapshot.cell_positions  # (n, 2)
        fidelity_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    d = float(np.linalg.norm(positions[i] - positions[j]))
                    # Fidelity drops with distance
                    f = self.base_fidelity * np.exp(-d / 2000)
                    fidelity_matrix[i, j] = max(f, 0.01)
                    idx = i * n + j
                    Q[idx, idx] = -np.log(max(fidelity_matrix[i, j], 1e-6))
                    # negative log → lower is better → minimise = max fidelity

        metadata = {
            "num_nodes": n, "num_vars": num_vars,
            "fidelity_matrix": fidelity_matrix,
        }
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n = metadata["num_nodes"]
        fid = metadata.get("fidelity_matrix", np.ones((n, n)))
        edges = []
        total_fidelity = 1.0
        for i in range(n):
            for j in range(n):
                if x[i * n + j] == 1:
                    edges.append((i, j))
                    total_fidelity *= fid[i, j]
        return {
            "edges": edges,
            "total_fidelity": total_fidelity,
            "num_hops": len(edges),
        }

    def compute_metrics(self, solution: dict) -> dict:
        dec = solution.get("decoded", {})
        return {
            "num_hops": dec.get("num_hops", 0),
            "end_to_end_fidelity": dec.get("total_fidelity", 0),
        }
