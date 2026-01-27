"""
QAOA Implementation for Telecom Network Optimization
=====================================================

Quantum Approximate Optimization Algorithm for solving combinatorial
optimization problems in telecommunications networks.
"""

from typing import Dict, List, Optional, Tuple, Callable
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit.primitives import Sampler

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class NetworkQAOA:
    """
    QAOA optimizer for network optimization problems.
    
    This class provides a high-level interface for applying QAOA to
    common telecom optimization problems like Max-Cut, graph partitioning,
    and load balancing.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits (typically equals number of network nodes)
    p : int
        Number of QAOA layers (default: 2)
    hamiltonian : SparsePauliOp, optional
        Problem Hamiltonian (can be set later)
    
    Example
    -------
    >>> import networkx as nx
    >>> from telequm.algorithms import NetworkQAOA
    >>> from telequm.core.hamiltonians import create_max_cut_hamiltonian
    >>> G = nx.petersen_graph()
    >>> H = create_max_cut_hamiltonian(G)
    >>> qaoa = NetworkQAOA(num_qubits=10, p=2, hamiltonian=H)
    >>> result = qaoa.optimize()
    """
    
    def __init__(
        self,
        num_qubits: int,
        p: int = 2,
        hamiltonian = None
    ):
        self.num_qubits = num_qubits
        self.p = p
        self.hamiltonian = hamiltonian
        self.optimal_params = None
        self.optimal_value = None
        self.optimization_history = []
        
    def create_circuit(
        self,
        gamma: Optional[List[float]] = None,
        beta: Optional[List[float]] = None
    ) -> QuantumCircuit:
        """
        Create the QAOA circuit.
        
        Parameters
        ----------
        gamma : list of float, optional
            Problem Hamiltonian parameters
        beta : list of float, optional
            Mixer Hamiltonian parameters
        
        Returns
        -------
        QuantumCircuit
            QAOA circuit
        """
        qc = QuantumCircuit(self.num_qubits, name=f"QAOA-p{self.p}")
        
        # Initial state: uniform superposition
        qc.h(range(self.num_qubits))
        
        # Create parameters if not provided
        use_params = gamma is None or beta is None
        if use_params:
            gamma_params = [Parameter(f"γ_{i}") for i in range(self.p)]
            beta_params = [Parameter(f"β_{i}") for i in range(self.p)]
        else:
            gamma_params = gamma
            beta_params = beta
        
        for layer in range(self.p):
            # Problem unitary (cost layer)
            g = gamma_params[layer] if use_params else gamma[layer]
            self._apply_cost_layer(qc, g)
            
            # Mixer unitary
            b = beta_params[layer] if use_params else beta[layer]
            self._apply_mixer_layer(qc, b)
        
        qc.measure_all()
        return qc
    
    def _apply_cost_layer(self, qc: QuantumCircuit, gamma):
        """Apply the problem/cost Hamiltonian unitary."""
        if self.hamiltonian is None:
            # Default: all pairs ZZ coupling (complete graph Max-Cut)
            for i in range(self.num_qubits):
                for j in range(i + 1, self.num_qubits):
                    qc.rzz(2 * gamma, i, j)
        else:
            # Use provided Hamiltonian
            for pauli_term, coeff in zip(
                self.hamiltonian.paulis.to_labels(),
                self.hamiltonian.coeffs
            ):
                if pauli_term.count("Z") == 2:
                    # ZZ term
                    indices = [k for k, p in enumerate(reversed(pauli_term)) if p == "Z"]
                    if len(indices) == 2:
                        qc.rzz(2 * gamma * float(coeff.real), indices[0], indices[1])
                elif pauli_term.count("Z") == 1:
                    # Single Z term
                    idx = next(k for k, p in enumerate(reversed(pauli_term)) if p == "Z")
                    qc.rz(2 * gamma * float(coeff.real), idx)
    
    def _apply_mixer_layer(self, qc: QuantumCircuit, beta):
        """Apply the mixer Hamiltonian unitary (X mixer)."""
        for i in range(self.num_qubits):
            qc.rx(2 * beta, i)
    
    def compute_expectation(
        self,
        params: np.ndarray,
        shots: int = 1024
    ) -> float:
        """
        Compute expectation value of the Hamiltonian.
        
        Parameters
        ----------
        params : np.ndarray
            Array of [gamma_0, ..., gamma_p-1, beta_0, ..., beta_p-1]
        shots : int
            Number of measurement shots
        
        Returns
        -------
        float
            Expectation value
        """
        gamma = params[:self.p]
        beta = params[self.p:]
        
        qc = self.create_circuit(gamma=list(gamma), beta=list(beta))
        
        # Execute
        backend = AerSimulator()
        job = backend.run(qc, shots=shots)
        counts = job.result().get_counts()
        
        # Compute expectation
        expectation = 0.0
        for bitstring, count in counts.items():
            # Convert bitstring to ±1 assignment
            assignment = [1 if b == "0" else -1 for b in bitstring]
            # Compute cost
            cost = self._compute_cost(assignment)
            expectation += cost * count / shots
        
        self.optimization_history.append(expectation)
        return expectation
    
    def _compute_cost(self, assignment: List[int]) -> float:
        """Compute cost for a given ±1 assignment."""
        if self.hamiltonian is None:
            # Default Max-Cut on complete graph
            cost = 0.0
            for i in range(len(assignment)):
                for j in range(i + 1, len(assignment)):
                    cost += 0.5 * (1 - assignment[i] * assignment[j])
            return cost
        else:
            # Use Hamiltonian
            cost = 0.0
            for pauli_term, coeff in zip(
                self.hamiltonian.paulis.to_labels(),
                self.hamiltonian.coeffs
            ):
                term_value = 1.0
                for k, p in enumerate(reversed(pauli_term)):
                    if p == "Z":
                        term_value *= assignment[k]
                cost += float(coeff.real) * term_value
            return cost
    
    def optimize(
        self,
        initial_params: Optional[np.ndarray] = None,
        method: str = "COBYLA",
        shots: int = 1024,
        maxiter: int = 100
    ) -> Dict:
        """
        Run QAOA optimization.
        
        Parameters
        ----------
        initial_params : np.ndarray, optional
            Initial parameters [gamma, beta]
        method : str
            Scipy optimization method (default: 'COBYLA')
        shots : int
            Measurement shots per evaluation
        maxiter : int
            Maximum iterations
        
        Returns
        -------
        Dict
            Optimization result with keys:
            - optimal_params: Best parameters found
            - optimal_value: Best cost value
            - history: Optimization history
            - optimal_bitstring: Most likely optimal solution
        """
        if not SCIPY_AVAILABLE:
            raise ImportError("scipy required for optimization")
        
        if initial_params is None:
            initial_params = np.random.uniform(0, np.pi, 2 * self.p)
        
        self.optimization_history = []
        
        result = minimize(
            self.compute_expectation,
            initial_params,
            args=(shots,),
            method=method,
            options={"maxiter": maxiter}
        )
        
        self.optimal_params = result.x
        self.optimal_value = result.fun
        
        # Get optimal bitstring
        gamma = self.optimal_params[:self.p]
        beta = self.optimal_params[self.p:]
        qc = self.create_circuit(gamma=list(gamma), beta=list(beta))
        
        backend = AerSimulator()
        job = backend.run(qc, shots=shots * 10)
        counts = job.result().get_counts()
        optimal_bitstring = max(counts, key=counts.get)
        
        return {
            "optimal_params": self.optimal_params,
            "optimal_value": self.optimal_value,
            "history": self.optimization_history,
            "optimal_bitstring": optimal_bitstring,
            "counts": counts,
            "scipy_result": result
        }


def create_qaoa_circuit(
    num_qubits: int,
    p: int = 1,
    graph_edges: Optional[List[Tuple[int, int]]] = None
) -> QuantumCircuit:
    """
    Create a parameterized QAOA circuit.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits
    p : int
        Number of QAOA layers
    graph_edges : list of tuples, optional
        Edge list for problem graph. If None, uses complete graph.
    
    Returns
    -------
    QuantumCircuit
        Parameterized QAOA circuit
    """
    qaoa = NetworkQAOA(num_qubits=num_qubits, p=p)
    return qaoa.create_circuit()


def run_qaoa_optimization(
    hamiltonian,
    p: int = 2,
    shots: int = 1024,
    maxiter: int = 100
) -> Dict:
    """
    Convenience function to run QAOA on a Hamiltonian.
    
    Parameters
    ----------
    hamiltonian : SparsePauliOp
        Problem Hamiltonian
    p : int
        Number of QAOA layers
    shots : int
        Measurement shots
    maxiter : int
        Maximum optimization iterations
    
    Returns
    -------
    Dict
        Optimization results
    """
    num_qubits = hamiltonian.num_qubits
    qaoa = NetworkQAOA(num_qubits=num_qubits, p=p, hamiltonian=hamiltonian)
    return qaoa.optimize(shots=shots, maxiter=maxiter)
