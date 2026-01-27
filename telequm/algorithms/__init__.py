"""
TELEQUM Algorithms Module
=========================

Quantum optimization and machine learning algorithms for telecommunications.
"""

from telequm.algorithms.qaoa import (
    NetworkQAOA,
    create_qaoa_circuit,
    run_qaoa_optimization,
)
from telequm.algorithms.vqe import (
    ResourceVQE,
    create_vqe_circuit,
    run_vqe_optimization,
)
from telequm.algorithms.qml import (
    QuantumBeamformer,
    create_qml_feature_map,
    train_quantum_classifier,
)

__all__ = [
    # QAOA
    "NetworkQAOA",
    "create_qaoa_circuit",
    "run_qaoa_optimization",
    # VQE
    "ResourceVQE",
    "create_vqe_circuit", 
    "run_vqe_optimization",
    # QML
    "QuantumBeamformer",
    "create_qml_feature_map",
    "train_quantum_classifier",
]
