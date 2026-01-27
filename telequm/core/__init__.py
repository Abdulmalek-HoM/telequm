"""
TELEQUM Core Module
===================

Reusable quantum circuits, Hamiltonians, and visualization utilities.
"""

from telequm.core.circuits import (
    create_bell_state,
    create_ghz_state,
    create_qft_circuit,
    create_variational_ansatz,
)
from telequm.core.hamiltonians import (
    create_max_cut_hamiltonian,
    create_resource_allocation_hamiltonian,
    create_network_optimization_hamiltonian,
)
from telequm.core.visualizations import (
    plot_circuit,
    plot_histogram,
    plot_network_graph,
    plot_optimization_landscape,
)

__all__ = [
    # Circuits
    "create_bell_state",
    "create_ghz_state",
    "create_qft_circuit",
    "create_variational_ansatz",
    # Hamiltonians
    "create_max_cut_hamiltonian",
    "create_resource_allocation_hamiltonian",
    "create_network_optimization_hamiltonian",
    # Visualizations
    "plot_circuit",
    "plot_histogram",
    "plot_network_graph",
    "plot_optimization_landscape",
]
