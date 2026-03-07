"""
UniversalNetworkSnapshot — Source-Agnostic Network State
========================================================

Central data class that unifies network state from:
- **Standalone simulator** (TELEQUM engine)
- **MATLAB** (CDL/TDL channel models)
- **ns-3** (PDCP/RLC/MAC telemetry traces)

Any TELEQUM module that consumes network state (problems, solvers,
dashboard) operates on this universal snapshot — never on raw source
data. This guarantees source-agnostic portability.

Design Principles
-----------------
- Immutable after creation (optimizers/dashboard never mutate)
- Serializable to JSON for experiment storage
- Contains all KPIs needed by any problem formulation
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class CellInfo:
    """Single cell / base station state."""
    cell_id: int
    position: np.ndarray                # (x, y) metres
    tx_power_dbm: float = 46.0
    frequency_ghz: float = 3.5
    num_antennas: int = 64
    bandwidth_mhz: float = 100.0
    num_prbs: int = 273
    height_m: float = 25.0
    active: bool = True
    load_fraction: float = 0.0         # current load [0, 1]
    energy_consumption_w: float = 0.0  # watts

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=float)


@dataclass
class UserInfo:
    """Single UE state."""
    user_id: int
    position: np.ndarray
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2))
    serving_cell: Optional[int] = None
    traffic_demand_mbps: float = 10.0
    achieved_throughput_mbps: float = 0.0
    latency_ms: float = 0.0
    slice_id: Optional[int] = None
    cqi: int = 15                       # channel quality indicator [0–15]
    active: bool = True

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=float)
        self.velocity = np.asarray(self.velocity, dtype=float)


class UniversalNetworkSnapshot:
    """
    Source-agnostic, immutable network state.

    This is the **single data contract** consumed by all TELEQUM
    problems, solvers, and visualizations.

    Parameters
    ----------
    source : str
        Origin identifier: 'standalone', 'matlab', 'ns3'.
    metadata : dict, optional
        Arbitrary experiment metadata (seed, scenario name, etc.).

    Example
    -------
    >>> snap = UniversalNetworkSnapshot(source='standalone')
    >>> snap.add_cells(7)
    >>> snap.add_users(50, mobility_model='RandomWaypoint', seed=42)
    >>> snap.initialize_links()
    >>> problem = PRBAllocationProblem(snap)
    """

    def __init__(self, source: str = "standalone", metadata: Optional[dict] = None):
        self.source: str = source
        self.metadata: dict = metadata or {}
        self.cells: List[CellInfo] = []
        self.users: List[UserInfo] = []
        self.area_size: Tuple[float, float] = (1000.0, 1000.0)

        # Matrices (populated by initialize_links or external source)
        self._channel_matrix: Optional[np.ndarray] = None   # (n_ue, n_cell) linear gain
        self._sinr_matrix: Optional[np.ndarray] = None      # (n_ue, n_cell) dB
        self._h_matrix: Optional[np.ndarray] = None          # MIMO channel (from MATLAB)
        self._allocation_matrix: Optional[np.ndarray] = None # (n_ue, n_cell) PRB alloc

        self._frozen: bool = False

    # ── Builder methods (before freeze) ──────────────────────────

    def add_cells(
        self,
        count: int,
        positions: Optional[np.ndarray] = None,
        **kwargs,
    ) -> "UniversalNetworkSnapshot":
        """Add cells to the snapshot."""
        self._check_mutable()
        rng = np.random.default_rng(kwargs.get("seed", 42))

        if positions is not None:
            for i in range(count):
                self.cells.append(CellInfo(
                    cell_id=len(self.cells),
                    position=positions[i],
                    **{k: v for k, v in kwargs.items() if k != "seed"},
                ))
        else:
            # Grid layout
            cols = int(np.ceil(np.sqrt(count)))
            for i in range(count):
                r, c = divmod(i, cols)
                x = (c + 0.5) * self.area_size[0] / cols
                y = (r + 0.5) * self.area_size[1] / max(int(np.ceil(count / cols)), 1)
                self.cells.append(CellInfo(
                    cell_id=len(self.cells),
                    position=np.array([x, y]),
                    **{k: v for k, v in kwargs.items() if k != "seed"},
                ))
        return self

    def add_users(
        self,
        count: int,
        mobility_model: str = "static",
        seed: int = 42,
        **kwargs,
    ) -> "UniversalNetworkSnapshot":
        """Add randomly placed users."""
        self._check_mutable()
        rng = np.random.default_rng(seed)

        for j in range(count):
            pos = rng.uniform(0, self.area_size)
            demand = float(rng.uniform(kwargs.get("min_demand", 5),
                                       kwargs.get("max_demand", 30)))
            self.users.append(UserInfo(
                user_id=len(self.users),
                position=pos,
                traffic_demand_mbps=demand,
            ))
        self.metadata["mobility_model"] = mobility_model
        return self

    def initialize_links(self) -> "UniversalNetworkSnapshot":
        """
        Compute channel and SINR matrices from cell/user positions
        using 3GPP UMa path loss.
        """
        self._check_mutable()
        from telequm.simulator.network_env import _urban_macro_los, _urban_macro_nlos

        n_ue = len(self.users)
        n_cell = len(self.cells)
        rng = np.random.default_rng(self.metadata.get("seed", 42))

        self._channel_matrix = np.zeros((n_ue, n_cell))
        self._sinr_matrix = np.full((n_ue, n_cell), -np.inf)

        for u, ue in enumerate(self.users):
            for c, cell in enumerate(self.cells):
                d_2d = np.linalg.norm(ue.position - cell.position)
                d_3d = max(np.sqrt(d_2d**2 + (cell.height_m - 1.5)**2), 1.0)

                p_los = min(18 / max(d_2d, 1), 1) * (1 - np.exp(-d_2d / 63)) + np.exp(-d_2d / 63)
                is_los = rng.random() < p_los
                pl = (_urban_macro_los if is_los else _urban_macro_nlos)(
                    d_3d, cell.frequency_ghz, cell.height_m, 1.5
                )
                shadow = rng.normal(0, 4 if is_los else 6)
                self._channel_matrix[u, c] = 10 ** (-(pl + shadow) / 10)

        # SINR
        noise_dbm = -174 + 10 * np.log10(self.cells[0].bandwidth_mhz * 1e6) if n_cell > 0 else -100
        noise_lin = 10 ** (noise_dbm / 10)

        for u in range(n_ue):
            for c in range(n_cell):
                tx = 10 ** (self.cells[c].tx_power_dbm / 10)
                sig = tx * self._channel_matrix[u, c]
                intf = sum(
                    10 ** (self.cells[c2].tx_power_dbm / 10) * self._channel_matrix[u, c2]
                    for c2 in range(n_cell) if c2 != c
                )
                nf = 10 ** (7 / 10)  # 7 dB noise figure
                self._sinr_matrix[u, c] = 10 * np.log10(max(sig / (intf + noise_lin * nf), 1e-20))

        # Association — best SINR
        for u, ue in enumerate(self.users):
            ue.serving_cell = int(self.cells[np.argmax(self._sinr_matrix[u])].cell_id)

        return self

    def store_channel_matrix(self, H: np.ndarray) -> "UniversalNetworkSnapshot":
        """Store a MIMO H-matrix (from MATLAB CDL/TDL)."""
        self._check_mutable()
        self._h_matrix = np.asarray(H)
        return self

    def freeze(self) -> "UniversalNetworkSnapshot":
        """
        Freeze snapshot — no further mutation allowed.
        All downstream consumers get an immutable view.
        """
        self._frozen = True
        return self

    def _check_mutable(self):
        if self._frozen:
            raise RuntimeError("Snapshot is frozen — cannot mutate")

    # ── Read-only accessors ──────────────────────────────────────

    @property
    def num_cells(self) -> int:
        return len(self.cells)

    @property
    def num_users(self) -> int:
        return len(self.users)

    @property
    def channel_matrix(self) -> np.ndarray:
        if self._channel_matrix is None:
            raise ValueError("Links not initialized. Call initialize_links() first.")
        return self._channel_matrix.copy()

    @property
    def sinr_matrix(self) -> np.ndarray:
        if self._sinr_matrix is None:
            raise ValueError("Links not initialized.")
        return self._sinr_matrix.copy()

    @property
    def h_matrix(self) -> Optional[np.ndarray]:
        return self._h_matrix.copy() if self._h_matrix is not None else None

    @property
    def allocation_matrix(self) -> Optional[np.ndarray]:
        return self._allocation_matrix.copy() if self._allocation_matrix is not None else None

    @property
    def cell_positions(self) -> np.ndarray:
        return np.array([c.position for c in self.cells])

    @property
    def user_positions(self) -> np.ndarray:
        return np.array([u.position for u in self.users])

    @property
    def user_demands(self) -> np.ndarray:
        return np.array([u.traffic_demand_mbps for u in self.users])

    @property
    def user_serving_cells(self) -> np.ndarray:
        return np.array([u.serving_cell if u.serving_cell is not None else -1
                         for u in self.users])

    @property
    def cell_num_prbs(self) -> np.ndarray:
        return np.array([c.num_prbs for c in self.cells])

    def to_legacy_snapshot(self) -> dict:
        """Convert to the dict snapshot format used by optimization bridge."""
        return {
            "timestep": 0,
            "num_bs": self.num_cells,
            "num_ue": self.num_users,
            "channel_matrix": self.channel_matrix,
            "sinr_matrix": self.sinr_matrix,
            "allocation_matrix": self.allocation_matrix if self._allocation_matrix is not None
                                 else np.zeros((self.num_users, self.num_cells)),
            "bs_positions": self.cell_positions,
            "ue_positions": self.user_positions,
            "ue_demands": self.user_demands,
            "bs_num_prbs": self.cell_num_prbs,
            "ue_serving_bs": self.user_serving_cells,
        }

    # ── Factory: from NetworkEnvironment ─────────────────────────

    @classmethod
    def from_network_env(cls, env) -> "UniversalNetworkSnapshot":
        """Create snapshot from a NetworkEnvironment instance."""
        snap = cls(source="standalone")
        snap.area_size = env.area_size

        for bs in env.base_stations:
            snap.cells.append(CellInfo(
                cell_id=bs.id, position=bs.position,
                tx_power_dbm=bs.tx_power_dbm, frequency_ghz=bs.frequency_ghz,
                num_antennas=bs.num_antennas, bandwidth_mhz=bs.bandwidth_mhz,
                num_prbs=bs.num_prbs, height_m=bs.height_m, active=bs.active,
            ))

        for ue in env.users:
            snap.users.append(UserInfo(
                user_id=ue.id, position=ue.position,
                velocity=ue.velocity, serving_cell=ue.serving_bs,
                traffic_demand_mbps=ue.traffic_demand_mbps, active=ue.active,
            ))

        snap._channel_matrix = env.channel_matrix.copy()
        snap._sinr_matrix = env.sinr_matrix.copy()
        snap._allocation_matrix = env.allocation_matrix.copy()
        return snap

    # ── Serialization ────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "metadata": self.metadata,
            "area_size": list(self.area_size),
            "num_cells": self.num_cells,
            "num_users": self.num_users,
            "cells": [
                {"cell_id": c.cell_id, "position": c.position.tolist(),
                 "tx_power_dbm": c.tx_power_dbm, "frequency_ghz": c.frequency_ghz,
                 "num_prbs": c.num_prbs, "load_fraction": c.load_fraction}
                for c in self.cells
            ],
            "users": [
                {"user_id": u.user_id, "position": u.position.tolist(),
                 "serving_cell": u.serving_cell,
                 "demand_mbps": u.traffic_demand_mbps,
                 "throughput_mbps": u.achieved_throughput_mbps}
                for u in self.users
            ],
        }

    def to_json(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
