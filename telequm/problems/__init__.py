"""
Telecom Problem Library
========================

Standardized problems with quantum-classical interface.
"""

from telequm.problems.base_problem import BaseProblem
from telequm.problems.prb_allocation import PRBAllocationProblem
from telequm.problems.telecom_problems import (
    BeamSelection,
    BSPlacementProblem,
    EnergyEfficiency,
    HandoverOptimization,
    QuantumNetworkRouting,
    RoutingOptimization,
)

__all__ = [
    "BaseProblem",
    "PRBAllocationProblem",
    "RoutingOptimization",
    "BeamSelection",
    "EnergyEfficiency",
    "HandoverOptimization",
    "BSPlacementProblem",
    "QuantumNetworkRouting",
]
