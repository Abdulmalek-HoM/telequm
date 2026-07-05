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
simulator
    Discrete time-step simulation engine with 3GPP models, traffic, mobility,
    optimization bridge, and classical/quantum solver integration

Example
-------
>>> from telequm.simulator import SimulationEngine, NetworkEnvironment
>>> from telequm.algorithms import qaoa
>>> engine = SimulationEngine(config)
>>> results = engine.run()
"""

__version__ = "2.1.0"
__author__ = "Abdulmalek Baitulmal"
__email__ = "abdulmalek@telequm.dev"

from telequm.algorithms import qaoa, qml, vqe
from telequm.core import circuits, hamiltonians, visualizations
from telequm.telecom import beamforming, network_optimization, resource_allocation

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
    # Simulator module (lazy import — heavy deps)
    "simulator",
    # Version info
    "__version__",
    "__author__",
]
