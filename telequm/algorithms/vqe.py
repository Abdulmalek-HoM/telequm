"""
VQE Implementation for Telecom Resource Allocation
===================================================

Variational Quantum Eigensolver for solving resource allocation
and optimization problems in telecommunications.
"""

from typing import Dict, List, Optional, Callable
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit.primitives import Estimator

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class ResourceVQE:
    """
    VQE optimizer for telecom resource allocation problems.
    
    This class provides a flexible VQE implementation suitable for
    resource allocation, spectrum management, and load balancing.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits
    ansatz : str or QuantumCircuit
        Ansatz type: 'hardware_efficient', 'uccsd', or custom circuit
    num_layers : int
        Number of variational layers (default: 2)
    hamiltonian : SparsePauliOp
        Problem Hamiltonian
    
    Example
    -------
    >>> from telequm.algorithms import ResourceVQE
    >>> from telequm.core.hamiltonians import create_resource_allocation_hamiltonian
    >>> H, meta = create_resource_allocation_hamiltonian(4, 6, demand, capacity)
    >>> vqe = ResourceVQE(num_qubits=24, hamiltonian=H)
    >>> result = vqe.optimize()
    """
    
    def __init__(
        self,
        num_qubits: int,
        ansatz: str = "hardware_efficient",
        num_layers: int = 2,
        hamiltonian = None
    ):
        self.num_qubits = num_qubits
        self.ansatz_type = ansatz
        self.num_layers = num_layers
        self.hamiltonian = hamiltonian
        self.optimal_params = None
        self.optimal_value = None
        self.optimization_history = []
        
        # Build ansatz circuit
        if isinstance(ansatz, QuantumCircuit):
            self.ansatz = ansatz
        else:
            self.ansatz = self._build_ansatz()
        
        self.num_params = len(self.ansatz.parameters)
    
    def _build_ansatz(self) -> QuantumCircuit:
        """Build the variational ansatz circuit."""
        qc = QuantumCircuit(self.num_qubits, name=f"VQE-{self.ansatz_type}")
        
        param_idx = 0
        
        if self.ansatz_type == "hardware_efficient":
            for layer in range(self.num_layers):
                # Rotation layer
                for qubit in range(self.num_qubits):
                    ry = Parameter(f"θ_{param_idx}")
                    rz = Parameter(f"θ_{param_idx + 1}")
                    qc.ry(ry, qubit)
                    qc.rz(rz, qubit)
                    param_idx += 2
                
                # Entanglement layer (linear)
                for i in range(self.num_qubits - 1):
                    qc.cx(i, i + 1)
                
                qc.barrier()
        
        elif self.ansatz_type == "alternating":
            for layer in range(self.num_layers):
                # RY on all qubits
                for qubit in range(self.num_qubits):
                    ry = Parameter(f"θ_{param_idx}")
                    qc.ry(ry, qubit)
                    param_idx += 1
                
                # CZ entanglement (alternating pattern)
                if layer % 2 == 0:
                    for i in range(0, self.num_qubits - 1, 2):
                        qc.cz(i, i + 1)
                else:
                    for i in range(1, self.num_qubits - 1, 2):
                        qc.cz(i, i + 1)
        
        return qc
    
    def compute_energy(
        self,
        params: np.ndarray,
        shots: int = 1024
    ) -> float:
        """
        Compute expectation value of Hamiltonian.
        
        Parameters
        ----------
        params : np.ndarray
            Variational parameters
        shots : int
            Number of measurement shots
        
        Returns
        -------
        float
            Energy expectation value
        """
        # Bind parameters
        param_dict = {p: v for p, v in zip(self.ansatz.parameters, params)}
        bound_circuit = self.ansatz.assign_parameters(param_dict)
        
        # Compute expectation using sampling
        energy = self._sample_expectation(bound_circuit, shots)
        
        self.optimization_history.append(energy)
        return energy
    
    def _sample_expectation(self, circuit: QuantumCircuit, shots: int) -> float:
        """Compute expectation via sampling."""
        qc = circuit.copy()
        qc.measure_all()
        
        backend = AerSimulator()
        job = backend.run(qc, shots=shots)
        counts = job.result().get_counts()
        
        if self.hamiltonian is None:
            # Default: count number of 1s (minimize active qubits)
            energy = 0.0
            for bitstring, count in counts.items():
                energy += bitstring.count("1") * count / shots
            return energy
        
        # Compute Hamiltonian expectation
        energy = 0.0
        for bitstring, count in counts.items():
            prob = count / shots
            # Convert to ±1 
            state = [1 if b == "0" else -1 for b in bitstring]
            
            for pauli_term, coeff in zip(
                self.hamiltonian.paulis.to_labels(),
                self.hamiltonian.coeffs
            ):
                term_value = 1.0
                for k, p in enumerate(reversed(pauli_term)):
                    if p == "Z":
                        term_value *= state[k]
                    elif p in ["X", "Y"]:
                        # For X and Y terms, we'd need different measurement bases
                        # Simplified: treat as contribution to uncertainty
                        pass
                energy += float(coeff.real) * term_value * prob
        
        return energy
    
    def optimize(
        self,
        initial_params: Optional[np.ndarray] = None,
        method: str = "COBYLA",
        shots: int = 1024,
        maxiter: int = 200,
        callback: Optional[Callable] = None
    ) -> Dict:
        """
        Run VQE optimization.
        
        Parameters
        ----------
        initial_params : np.ndarray, optional
            Initial variational parameters
        method : str
            Scipy optimization method
        shots : int
            Measurement shots per evaluation
        maxiter : int
            Maximum iterations
        callback : callable, optional
            Callback function called after each iteration
        
        Returns
        -------
        Dict
            Optimization results
        """
        if not SCIPY_AVAILABLE:
            raise ImportError("scipy required for VQE optimization")
        
        if initial_params is None:
            initial_params = np.random.uniform(-np.pi, np.pi, self.num_params)
        
        self.optimization_history = []
        
        def objective(params):
            energy = self.compute_energy(params, shots)
            if callback:
                callback(params, energy)
            return energy
        
        result = minimize(
            objective,
            initial_params,
            method=method,
            options={"maxiter": maxiter}
        )
        
        self.optimal_params = result.x
        self.optimal_value = result.fun
        
        # Get optimal state
        param_dict = {p: v for p, v in zip(self.ansatz.parameters, self.optimal_params)}
        optimal_circuit = self.ansatz.assign_parameters(param_dict)
        optimal_circuit.measure_all()
        
        backend = AerSimulator()
        job = backend.run(optimal_circuit, shots=shots * 10)
        counts = job.result().get_counts()
        optimal_bitstring = max(counts, key=counts.get)
        
        return {
            "optimal_params": self.optimal_params,
            "optimal_energy": self.optimal_value,
            "history": self.optimization_history,
            "optimal_bitstring": optimal_bitstring,
            "counts": counts,
            "scipy_result": result
        }
    
    def get_resource_assignment(self, bitstring: str) -> Dict:
        """
        Interpret bitstring as resource assignment.
        
        Parameters
        ----------
        bitstring : str
            Optimal bitstring from VQE
        
        Returns
        -------
        Dict
            Resource assignment mapping
        """
        assignment = {}
        for i, bit in enumerate(reversed(bitstring)):
            assignment[f"resource_{i}"] = "active" if bit == "1" else "inactive"
        return assignment


def create_vqe_circuit(
    num_qubits: int,
    num_layers: int = 2,
    entanglement: str = "linear"
) -> QuantumCircuit:
    """
    Create a parameterized VQE ansatz circuit.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits
    num_layers : int
        Number of variational layers
    entanglement : str
        Entanglement pattern
    
    Returns
    -------
    QuantumCircuit
        Parameterized ansatz
    """
    vqe = ResourceVQE(num_qubits=num_qubits, num_layers=num_layers)
    return vqe.ansatz


def run_vqe_optimization(
    hamiltonian,
    num_layers: int = 2,
    shots: int = 1024,
    maxiter: int = 200
) -> Dict:
    """
    Convenience function to run VQE on a Hamiltonian.
    
    Parameters
    ----------
    hamiltonian : SparsePauliOp
        Problem Hamiltonian
    num_layers : int
        Ansatz layers
    shots : int
        Measurement shots
    maxiter : int
        Maximum iterations
    
    Returns
    -------
    Dict
        Optimization results
    """
    num_qubits = hamiltonian.num_qubits
    vqe = ResourceVQE(
        num_qubits=num_qubits,
        num_layers=num_layers,
        hamiltonian=hamiltonian
    )
    return vqe.optimize(shots=shots, maxiter=maxiter)
