"""
Telecom Problem Library — Base Class & Implementations
======================================================

Standard interface for all telecom optimization problems:
- ``to_qubo()``        → QUBO matrix for quantum solvers
- ``to_hamiltonian()`` → Ising Hamiltonian (SparsePauliOp)
- ``solve_classical()`` → Classical baseline result
- ``compute_metrics()`` → KPI evaluation

All problems consume ``UniversalNetworkSnapshot`` —
never raw source data.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

import numpy as np

from telequm.core.network_snapshot import UniversalNetworkSnapshot


class BaseProblem(ABC):
    """
    Abstract base class for telecom optimization problems.

    Parameters
    ----------
    snapshot : UniversalNetworkSnapshot
        Network state to optimize over.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot):
        self.snapshot = snapshot

    @abstractmethod
    def to_qubo(self) -> Tuple[np.ndarray, float, dict]:
        """
        Build QUBO matrix from snapshot.

        Returns
        -------
        Q : np.ndarray  (n × n)
        offset : float
        metadata : dict
        """
        ...

    @abstractmethod
    def to_hamiltonian(self):
        """Convert QUBO to Ising Hamiltonian (SparsePauliOp)."""
        ...

    @abstractmethod
    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        """Decode binary vector to actionable allocation."""
        ...

    @abstractmethod
    def compute_metrics(self, solution: dict) -> dict:
        """Evaluate solution quality (KPIs)."""
        ...

    def solve_classical(self, method: str = "greedy") -> dict:
        """Solve with classical baseline."""
        from telequm.simulator.optimization_bridge import ClassicalBaselines
        Q, offset, meta = self.to_qubo()
        t0 = time.time()
        if method == "greedy":
            x, cost, rt = ClassicalBaselines.greedy(Q, offset)
        elif method == "simulated_annealing":
            x, cost, rt = ClassicalBaselines.simulated_annealing(Q, offset)
        elif method == "exact":
            x, cost, rt = ClassicalBaselines.exact_brute_force(Q, offset)
        else:
            raise ValueError(f"Unknown method: {method}")
        decoded = self.decode_solution(x, meta)
        return {"solution": x, "decoded": decoded, "cost": cost,
                "runtime_s": time.time() - t0, "method": f"classical_{method}"}

    def solve_quantum(self, algorithm: str = "qaoa", **kwargs) -> dict:
        """Solve with quantum algorithm."""
        from telequm.simulator.optimization_bridge import OptimizationBridge, ResourceAllocationQUBO
        legacy = self.snapshot.to_legacy_snapshot()
        bridge = OptimizationBridge(ResourceAllocationQUBO())
        return bridge.solve_quantum(legacy, algorithm=algorithm, **kwargs)
