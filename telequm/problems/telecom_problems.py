"""
Additional Telecom Problem Formulations
========================================

- RoutingOptimization: shortest weighted path
- BeamSelection: discrete beam selection from codebook
- EnergyEfficiency: cell on/off + user reassignment
- HandoverOptimization: minimise unnecessary handovers
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from telequm.problems.base_problem import BaseProblem
from telequm.core.network_snapshot import UniversalNetworkSnapshot


class RoutingOptimization(BaseProblem):
    """
    Shortest-path routing QUBO.

    Variables: x_{i,j} ∈ {0,1} — edge (i,j) included in path.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0):
        super().__init__(snapshot)
        self.penalty = penalty

    def to_qubo(self) -> Tuple[np.ndarray, float, dict]:
        n = self.snapshot.num_cells
        Q = np.zeros((n * n, n * n))
        offset = 0.0
        sinr = self.snapshot.sinr_matrix if self.snapshot.num_users > 0 else np.zeros((1, n))

        # Edge cost: inverse of max SINR on that link
        for i in range(n):
            for j in range(n):
                if i != j:
                    idx = i * n + j
                    avg_sinr = np.mean(sinr[:, j]) if sinr.shape[0] > 0 else 0
                    Q[idx, idx] = -max(avg_sinr, 0.1)

        metadata = {"num_nodes": n, "num_vars": n * n}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n = metadata["num_nodes"]
        edges = []
        for i in range(n):
            for j in range(n):
                if x[i * n + j] == 1:
                    edges.append((i, j))
        return {"edges": edges}

    def compute_metrics(self, solution: dict) -> dict:
        return {"num_edges": len(solution.get("decoded", {}).get("edges", []))}


class BeamSelection(BaseProblem):
    """
    Discrete beam selection from codebook QUBO.

    Variables: x_{u,b} ∈ {0,1} — user u uses beam b.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, num_beams: int = 8, penalty: float = 10.0):
        super().__init__(snapshot)
        self.num_beams = num_beams
        self.penalty = penalty

    def to_qubo(self) -> Tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n = n_ue * self.num_beams
        Q = np.zeros((n, n))
        offset = 0.0
        rng = np.random.default_rng(42)
        beam_gains = rng.uniform(0, 1, (n_ue, self.num_beams))

        for u in range(n_ue):
            for b in range(self.num_beams):
                idx = u * self.num_beams + b
                Q[idx, idx] -= beam_gains[u, b]

        # One beam per user
        for u in range(n_ue):
            indices = [u * self.num_beams + b for b in range(self.num_beams)]
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    r, c = min(indices[i], indices[j]), max(indices[i], indices[j])
                    Q[r, c] += 2 * self.penalty

        metadata = {"num_ue": n_ue, "num_beams": self.num_beams, "num_vars": n}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        assignments = {}
        for u in range(metadata["num_ue"]):
            for b in range(metadata["num_beams"]):
                if x[u * metadata["num_beams"] + b] == 1:
                    assignments[u] = b
        return {"beam_assignments": assignments}

    def compute_metrics(self, solution: dict) -> dict:
        return {"num_assigned": len(solution.get("decoded", {}).get("beam_assignments", {}))}


class EnergyEfficiency(BaseProblem):
    """
    Cell on/off + user reassignment for energy savings.

    Variables: y_c ∈ {0,1} — cell c is ON; x_{u,c} — user assignment.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0,
                 power_per_cell_w: float = 500.0):
        super().__init__(snapshot)
        self.penalty = penalty
        self.power_per_cell = power_per_cell_w

    def to_qubo(self) -> Tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n_cell = self.snapshot.num_cells
        n_y = n_cell
        n_x = n_ue * n_cell
        n = n_y + n_x
        Q = np.zeros((n, n))
        offset = 0.0

        # Energy cost: penalise active cells
        for c in range(n_cell):
            Q[c, c] += self.power_per_cell / 1000  # normalised

        # SINR reward for assignments
        sinr = self.snapshot.sinr_matrix
        for u in range(n_ue):
            for c in range(n_cell):
                idx = n_y + u * n_cell + c
                Q[idx, idx] -= max(sinr[u, c], 0)

        metadata = {"num_ue": n_ue, "num_cells": n_cell, "num_vars": n, "n_y": n_y}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n_cell = metadata["num_cells"]
        n_y = metadata["n_y"]
        active_cells = [c for c in range(n_cell) if x[c] == 1]
        return {"active_cells": active_cells, "energy_saved_pct": (1 - len(active_cells) / n_cell) * 100}

    def compute_metrics(self, solution: dict) -> dict:
        decoded = solution.get("decoded", {})
        return {
            "active_cells": len(decoded.get("active_cells", [])),
            "energy_saved_pct": decoded.get("energy_saved_pct", 0),
        }


class HandoverOptimization(BaseProblem):
    """
    Handover minimisation QUBO.

    Variables: x_{u,c} — user u assigned to cell c.
    Penalises assignments that differ from current serving cell.
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0,
                 handover_cost: float = 5.0):
        super().__init__(snapshot)
        self.penalty = penalty
        self.handover_cost = handover_cost

    def to_qubo(self) -> Tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n_cell = self.snapshot.num_cells
        n = n_ue * n_cell
        Q = np.zeros((n, n))
        offset = 0.0
        sinr = self.snapshot.sinr_matrix
        serving = self.snapshot.user_serving_cells

        for u in range(n_ue):
            for c in range(n_cell):
                idx = u * n_cell + c
                # SINR reward
                Q[idx, idx] -= max(sinr[u, c], 0)
                # Handover penalty
                if serving[u] >= 0 and c != serving[u]:
                    Q[idx, idx] += self.handover_cost

        metadata = {"num_ue": n_ue, "num_cells": n_cell, "num_vars": n}
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n_cell = metadata["num_cells"]
        serving = self.snapshot.user_serving_cells
        handovers = 0
        for u in range(metadata["num_ue"]):
            for c in range(n_cell):
                if x[u * n_cell + c] == 1 and serving[u] >= 0 and c != serving[u]:
                    handovers += 1
        return {"num_handovers": handovers, "allocation_matrix": x}

    def compute_metrics(self, solution: dict) -> dict:
        return {"num_handovers": solution.get("decoded", {}).get("num_handovers", 0)}
