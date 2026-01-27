"""
TELEQUM - The Applied Quantum Testbed for Telecommunications
=============================================================

TELEQUM bridges the gap between quantum research and practical telecom engineering,
providing tools, education, and industrial simulators for quantum-powered networks.

Modules
-------
core
    Reusable quantum circuits, Hamiltonians, and visualization utilities
algorithms
    QAOA, VQE, and Quantum Machine Learning implementations
telecom
    Industry-specific modules for resource allocation, beamforming, and optimization

Example
-------
>>> from telequm.algorithms import qaoa
>>> from telequm.telecom import network_optimization
>>> optimizer = qaoa.NetworkQAOA(num_nodes=5)
>>> result = optimizer.optimize()
"""

__version__ = "2.0.0"
__author__ = "Abdulmalek Baitulmal"
__email__ = "abdulmalek@telequm.dev"

from telequm.core import circuits, hamiltonians, visualizations
from telequm.algorithms import qaoa, vqe, qml
from telequm.telecom import resource_allocation, beamforming, network_optimization

__all__ = [
    # Core modules
    "circuits",
    "hamiltonians", 
    "visualizations",
    # Algorithm modules
    "qaoa",
    "vqe",
    "qml",
    # Telecom modules
    "resource_allocation",
    "beamforming",
    "network_optimization",
    # Version info
    "__version__",
    "__author__",
]
