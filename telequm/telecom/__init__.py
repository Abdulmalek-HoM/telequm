"""
TELEQUM Telecom Module
======================

Industry-specific implementations for telecommunications applications.
"""

from telequm.telecom.resource_allocation import (
    ResourceAllocator,
    optimize_spectrum_allocation,
    optimize_channel_assignment,
)
from telequm.telecom.beamforming import (
    BeamformingOptimizer,
    compute_beam_weights,
    optimize_mimo_configuration,
)
from telequm.telecom.network_optimization import (
    NetworkOptimizer,
    optimize_network_topology,
    optimize_load_balancing,
)

__all__ = [
    # Resource Allocation
    "ResourceAllocator",
    "optimize_spectrum_allocation",
    "optimize_channel_assignment",
    # Beamforming
    "BeamformingOptimizer",
    "compute_beam_weights",
    "optimize_mimo_configuration",
    # Network Optimization
    "NetworkOptimizer",
    "optimize_network_topology",
    "optimize_load_balancing",
]
