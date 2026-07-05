"""
PRB Allocation Problem — Physical Resource Block Assignment
===========================================================

Assigns PRBs to users across cells to maximise throughput
while respecting per-cell capacity constraints.
"""

from __future__ import annotations

import numpy as np

from telequm.core.network_snapshot import UniversalNetworkSnapshot
from telequm.problems.base_problem import BaseProblem


class PRBAllocationProblem(BaseProblem):
    """
    PRB allocation QUBO formulation.

    Variables: x_{u,c} ∈ {0,1} — user u served by cell c.

    Objective: maximize SINR-weighted throughput.
    Constraints: each user served by exactly one cell;
                 per-cell capacity limit.

    Parameters
    ----------
    snapshot : UniversalNetworkSnapshot
    penalty : float  constraint violation weight
    """

    def __init__(self, snapshot: UniversalNetworkSnapshot, penalty: float = 10.0):
        super().__init__(snapshot)
        self.penalty = penalty

    def to_qubo(self) -> tuple[np.ndarray, float, dict]:
        n_ue = self.snapshot.num_users
        n_cell = self.snapshot.num_cells
        n = n_ue * n_cell
        sinr = self.snapshot.sinr_matrix
        prbs = self.snapshot.cell_num_prbs
        max_users = np.maximum(prbs // 10, 1)

        Q = np.zeros((n, n))
        offset = 0.0

        # Objective: maximise SINR
        for u in range(n_ue):
            for c in range(n_cell):
                idx = u * n_cell + c
                Q[idx, idx] -= max(sinr[u, c], 0)

        # Constraint: each user → exactly one cell
        for u in range(n_ue):
            indices = [u * n_cell + c for c in range(n_cell)]
            for idx in indices:
                Q[idx, idx] += self.penalty - 2 * self.penalty
            for i in range(len(indices)):
                Q[indices[i], indices[i]] += self.penalty
                for j in range(i + 1, len(indices)):
                    r, c_idx = min(indices[i], indices[j]), max(indices[i], indices[j])
                    Q[r, c_idx] += 2 * self.penalty
            for idx in indices:
                Q[idx, idx] -= 2 * self.penalty
            offset += self.penalty

        # Constraint: cell capacity
        for c in range(n_cell):
            cap = int(max_users[c])
            indices = [u * n_cell + c for u in range(n_ue)]
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    r, col = min(indices[i], indices[j]), max(indices[i], indices[j])
                    Q[r, col] += (self.penalty / cap) * 0.5

        metadata = {
            "num_ue": n_ue, "num_cells": n_cell, "num_vars": n,
            "var_map": {(u, c): u * n_cell + c for u in range(n_ue) for c in range(n_cell)},
        }
        return Q, offset, metadata

    def to_hamiltonian(self):
        from telequm.simulator.optimization_bridge import OptimizationBridge
        Q, offset, _ = self.to_qubo()
        return OptimizationBridge._qubo_to_ising(Q, offset)

    def decode_solution(self, x: np.ndarray, metadata: dict) -> dict:
        n_ue = metadata["num_ue"]
        n_cell = metadata["num_cells"]
        alloc = np.zeros((n_ue, n_cell), dtype=int)
        for u in range(n_ue):
            for c in range(n_cell):
                idx = u * n_cell + c
                if idx < len(x):
                    alloc[u, c] = int(x[idx])
        return {"allocation_matrix": alloc}

    def compute_metrics(self, solution: dict) -> dict:
        alloc = solution.get("decoded", {}).get("allocation_matrix", np.zeros((1, 1)))
        sinr = self.snapshot.sinr_matrix
        bw = self.snapshot.cells[0].bandwidth_mhz * 1e6 if self.snapshot.cells else 1e8
        throughputs = []
        for u in range(self.snapshot.num_users):
            served = np.where(alloc[u] == 1)[0]
            if len(served) > 0:
                c = served[0]
                sinr_lin = 10 ** (sinr[u, c] / 10)
                tp = bw * np.log2(1 + sinr_lin) / 1e6
                throughputs.append(tp)
            else:
                throughputs.append(0.0)
        tp_arr = np.array(throughputs)
        return {
            "avg_throughput_mbps": float(np.mean(tp_arr)),
            "sum_throughput_mbps": float(np.sum(tp_arr)),
            "fairness_jain": float(np.sum(tp_arr)**2 / (len(tp_arr) * np.sum(tp_arr**2)))
            if np.sum(tp_arr**2) > 0 else 0.0,
            "cost": solution.get("cost", 0),
        }
