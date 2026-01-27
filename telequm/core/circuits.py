"""
Reusable Quantum Circuits for Telecommunications
================================================

This module provides pre-built quantum circuits commonly used in 
telecom applications, including entanglement, QFT, and variational ansätze.
"""

from typing import Optional
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def create_bell_state(qc: Optional[QuantumCircuit] = None, q0: int = 0, q1: int = 1) -> QuantumCircuit:
    """
    Create a Bell state (maximally entangled two-qubit state).
    
    The Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2 is fundamental for quantum
    communication and teleportation protocols.
    
    Parameters
    ----------
    qc : QuantumCircuit, optional
        Existing circuit to append to. If None, creates a new 2-qubit circuit.
    q0 : int
        Index of first qubit (default: 0)
    q1 : int
        Index of second qubit (default: 1)
    
    Returns
    -------
    QuantumCircuit
        Circuit that creates Bell state
    
    Example
    -------
    >>> from telequm.core.circuits import create_bell_state
    >>> qc = create_bell_state()
    >>> print(qc)
    """
    if qc is None:
        qc = QuantumCircuit(2, name="Bell State")
    
    qc.h(q0)
    qc.cx(q0, q1)
    
    return qc


def create_ghz_state(num_qubits: int = 3) -> QuantumCircuit:
    """
    Create a GHZ (Greenberger–Horne–Zeilinger) state.
    
    The GHZ state is a maximally entangled state of n qubits:
    |GHZ⟩ = (|00...0⟩ + |11...1⟩)/√2
    
    Useful for quantum network protocols and multiparty quantum communication.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits in the GHZ state (default: 3)
    
    Returns
    -------
    QuantumCircuit
        Circuit that creates GHZ state
    """
    qc = QuantumCircuit(num_qubits, name=f"GHZ-{num_qubits}")
    
    qc.h(0)
    for i in range(num_qubits - 1):
        qc.cx(i, i + 1)
    
    return qc


def create_qft_circuit(num_qubits: int, inverse: bool = False) -> QuantumCircuit:
    """
    Create a Quantum Fourier Transform circuit.
    
    QFT is essential for quantum phase estimation and Shor's algorithm,
    both critical for cryptographic applications in telecommunications.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits for the QFT
    inverse : bool
        If True, create the inverse QFT (default: False)
    
    Returns
    -------
    QuantumCircuit
        QFT circuit
    """
    qc = QuantumCircuit(num_qubits, name=f"{'Inverse ' if inverse else ''}QFT-{num_qubits}")
    
    def _qft_rotations(circuit: QuantumCircuit, n: int) -> QuantumCircuit:
        if n == 0:
            return circuit
        n -= 1
        circuit.h(n)
        for qubit in range(n):
            circuit.cp(np.pi / 2 ** (n - qubit), qubit, n)
        return _qft_rotations(circuit, n)
    
    def _swap_registers(circuit: QuantumCircuit, n: int) -> QuantumCircuit:
        for qubit in range(n // 2):
            circuit.swap(qubit, n - qubit - 1)
        return circuit
    
    _qft_rotations(qc, num_qubits)
    _swap_registers(qc, num_qubits)
    
    if inverse:
        qc = qc.inverse()
        qc.name = f"Inverse QFT-{num_qubits}"
    
    return qc


def create_variational_ansatz(
    num_qubits: int,
    num_layers: int = 2,
    entanglement: str = "linear",
    parameter_prefix: str = "θ"
) -> QuantumCircuit:
    """
    Create a hardware-efficient variational ansatz for VQE/QAOA.
    
    This ansatz is designed for near-term quantum devices and is
    commonly used in quantum optimization for telecom applications.
    
    Parameters
    ----------
    num_qubits : int
        Number of qubits in the ansatz
    num_layers : int
        Number of variational layers (default: 2)
    entanglement : str
        Entanglement pattern: 'linear', 'full', or 'circular' (default: 'linear')
    parameter_prefix : str
        Prefix for parameter names (default: 'θ')
    
    Returns
    -------
    QuantumCircuit
        Variational ansatz circuit with parameters
    """
    from qiskit.circuit import Parameter
    
    qc = QuantumCircuit(num_qubits, name=f"VarAnsatz-{num_qubits}x{num_layers}")
    
    param_idx = 0
    
    for layer in range(num_layers):
        # Rotation layer
        for qubit in range(num_qubits):
            theta_y = Parameter(f"{parameter_prefix}_{param_idx}")
            theta_z = Parameter(f"{parameter_prefix}_{param_idx + 1}")
            qc.ry(theta_y, qubit)
            qc.rz(theta_z, qubit)
            param_idx += 2
        
        # Entanglement layer
        if entanglement == "linear":
            for i in range(num_qubits - 1):
                qc.cx(i, i + 1)
        elif entanglement == "circular":
            for i in range(num_qubits - 1):
                qc.cx(i, i + 1)
            if num_qubits > 2:
                qc.cx(num_qubits - 1, 0)
        elif entanglement == "full":
            for i in range(num_qubits):
                for j in range(i + 1, num_qubits):
                    qc.cx(i, j)
        
        qc.barrier()
    
    return qc


def create_teleportation_circuit() -> QuantumCircuit:
    """
    Create a quantum teleportation protocol circuit.
    
    This circuit demonstrates the foundation of quantum communication,
    enabling the transfer of quantum information between network nodes.
    
    Returns
    -------
    QuantumCircuit
        Teleportation protocol circuit with:
        - q0: Message qubit (to be teleported)
        - q1: Alice's entangled qubit
        - q2: Bob's entangled qubit (receives teleported state)
    """
    qr = QuantumRegister(3, "q")
    cr = ClassicalRegister(2, "c")
    qc = QuantumCircuit(qr, cr, name="Teleportation")
    
    # Create entangled pair between Alice (q1) and Bob (q2)
    qc.h(qr[1])
    qc.cx(qr[1], qr[2])
    qc.barrier()
    
    # Alice's operations
    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    qc.barrier()
    
    # Measure Alice's qubits
    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])
    qc.barrier()
    
    # Bob's corrections (classically controlled)
    qc.x(qr[2]).c_if(cr, 1)
    qc.z(qr[2]).c_if(cr, 2)
    qc.x(qr[2]).c_if(cr, 3)
    qc.z(qr[2]).c_if(cr, 3)
    
    return qc
