"""
NetworkEnvironment — Centralized Simulation State
==================================================

Single source of truth for all network state during simulation.
Implements 3GPP-compliant path loss models, SINR calculation,
and interference management.

**Design rule**: Optimizers never modify this object directly.
Only the ``SimulationEngine`` mutates state via explicit methods.

References
----------
- 3GPP TR 38.901: Channel model for 0.5–100 GHz
- 3GPP TS 38.214: Physical layer procedures for NR
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


# ─── Data classes ───────────────────────────────────────────────────

@dataclass
class BaseStation:
    """A gNB or small cell base station."""
    id: int
    position: np.ndarray            # (x, y) metres
    tx_power_dbm: float = 46.0      # 3GPP macro-cell typical
    frequency_ghz: float = 3.5      # n78 band
    num_antennas: int = 64
    bandwidth_mhz: float = 100.0
    num_prbs: int = 273             # for 100 MHz @ 30 kHz SCS
    height_m: float = 25.0
    active: bool = True

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=float)


@dataclass
class UserEquipment:
    """A mobile user / UE."""
    id: int
    position: np.ndarray            # (x, y) metres
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2))
    noise_figure_db: float = 7.0
    height_m: float = 1.5
    serving_bs: Optional[int] = None
    traffic_demand_mbps: float = 10.0
    slice_id: Optional[int] = None
    active: bool = True

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=float)
        self.velocity = np.asarray(self.velocity, dtype=float)


@dataclass
class NetworkSlice:
    """5G network slice definition."""
    id: int
    name: str                        # e.g. "eMBB", "URLLC", "mMTC"
    priority: int = 1
    min_rate_mbps: float = 0.0
    max_latency_ms: float = 100.0
    guaranteed_prbs: int = 0


# ─── Path-loss models (3GPP TR 38.901) ────────────────────────────

def _urban_macro_los(d_3d: float, f_ghz: float, h_bs: float, h_ue: float) -> float:
    """
    3GPP UMa LOS path loss (TR 38.901, Table 7.4.1-1).
    
    Parameters
    ----------
    d_3d : float   3D distance in metres
    f_ghz : float  carrier frequency in GHz
    h_bs : float   BS height in metres
    h_ue : float   UE height in metres
    
    Returns
    -------
    float  path loss in dB
    """
    d_2d = max(np.sqrt(d_3d**2 - (h_bs - h_ue)**2), 1.0)
    d_bp = 4 * (h_bs - 1) * (h_ue - 1) * f_ghz * 1e9 / 3e8
    fc = f_ghz * 1e3  # MHz for formula

    if d_2d <= d_bp:
        pl = 28.0 + 22.0 * np.log10(d_3d) + 20.0 * np.log10(f_ghz)
    else:
        pl = (28.0 + 40.0 * np.log10(d_3d) + 20.0 * np.log10(f_ghz)
              - 9.0 * np.log10(d_bp**2 + (h_bs - h_ue)**2))
    return pl


def _urban_macro_nlos(d_3d: float, f_ghz: float, h_bs: float, h_ue: float) -> float:
    """3GPP UMa NLOS path loss (simplified)."""
    pl_los = _urban_macro_los(d_3d, f_ghz, h_bs, h_ue)
    d_2d = max(np.sqrt(d_3d**2 - (h_bs - h_ue)**2), 1.0)
    pl_nlos = (13.54 + 39.08 * np.log10(d_3d) + 20.0 * np.log10(f_ghz)
               - 0.6 * (h_ue - 1.5))
    return max(pl_los, pl_nlos)


# ─── Network Environment ──────────────────────────────────────────

class NetworkEnvironment:
    """
    Centralized, mutable network state.
    
    This object is the **single source of truth** during a simulation
    run.  Only ``SimulationEngine`` should call mutation methods;
    optimizers receive read-only snapshots via ``get_snapshot()``.
    
    Parameters
    ----------
    config : dict
        Network configuration containing:
        - ``base_stations`` : list of BS configs
        - ``users``         : list of UE configs
        - ``slices``        : list of slice configs (optional)
        - ``area_size``     : (width, height) in metres
        - ``random_seed``   : int
    
    Attributes
    ----------
    timestep : int
        Current simulation timestep.
    channel_matrix : np.ndarray
        (num_ues × num_bs)  large-scale channel gain in linear scale.
    sinr_matrix : np.ndarray
        (num_ues × num_bs)  SINR in dB.
    allocation_matrix : np.ndarray
        (num_ues × num_bs)  PRB allocation (0 or fraction).
    """

    # ── Construction ───────────────────────────────────────────────

    def __init__(self, config: dict):
        self._rng = np.random.default_rng(config.get("random_seed", 42))
        self.timestep: int = 0
        self.area_size: Tuple[float, float] = tuple(config.get("area_size", (1000.0, 1000.0)))

        # Entities
        self.base_stations: List[BaseStation] = [
            BaseStation(**bs) for bs in config.get("base_stations", [])
        ]
        self.users: List[UserEquipment] = [
            UserEquipment(**ue) for ue in config.get("users", [])
        ]
        self.slices: List[NetworkSlice] = [
            NetworkSlice(**s) for s in config.get("slices", [])
        ]

        # State matrices
        n_ue, n_bs = len(self.users), len(self.base_stations)
        self.channel_matrix = np.zeros((n_ue, n_bs))
        self.sinr_matrix = np.zeros((n_ue, n_bs))
        self.allocation_matrix = np.zeros((n_ue, n_bs))

        # Metrics history (per-timestep)
        self.metrics_history: List[dict] = []

        # Initial channel update
        self.update_channels()

    # ── Factory helpers ────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, path: str) -> "NetworkEnvironment":
        """Load environment from a YAML config file."""
        import yaml
        with open(path) as f:
            config = yaml.safe_load(f)
        return cls(config)

    @classmethod
    def from_json(cls, path: str) -> "NetworkEnvironment":
        """Load environment from a JSON config file."""
        with open(path) as f:
            config = json.load(f)
        return cls(config)

    # ── Read-only snapshot ─────────────────────────────────────────

    def get_snapshot(self) -> dict:
        """
        Return an immutable snapshot of current state for optimizers.
        
        Returns
        -------
        dict
            Contains copies of channel_matrix, sinr_matrix,
            allocation_matrix, user positions, BS positions, etc.
        """
        return {
            "timestep": self.timestep,
            "num_bs": len(self.base_stations),
            "num_ue": len(self.users),
            "channel_matrix": self.channel_matrix.copy(),
            "sinr_matrix": self.sinr_matrix.copy(),
            "allocation_matrix": self.allocation_matrix.copy(),
            "bs_positions": np.array([bs.position for bs in self.base_stations]),
            "ue_positions": np.array([ue.position for ue in self.users]),
            "ue_demands": np.array([ue.traffic_demand_mbps for ue in self.users]),
            "bs_num_prbs": np.array([bs.num_prbs for bs in self.base_stations]),
            "ue_serving_bs": np.array([ue.serving_bs if ue.serving_bs is not None else -1
                                       for ue in self.users]),
        }

    # ── Channel / SINR updates ─────────────────────────────────────

    def update_channels(self) -> None:
        """
        Recompute large-scale channel gains and SINR for every
        UE–BS pair using 3GPP UMa path-loss model.
        """
        n_ue = len(self.users)
        n_bs = len(self.base_stations)
        self.channel_matrix = np.zeros((n_ue, n_bs))
        self.sinr_matrix = np.full((n_ue, n_bs), -np.inf)

        for u, ue in enumerate(self.users):
            if not ue.active:
                continue
            for b, bs in enumerate(self.base_stations):
                if not bs.active:
                    continue
                d_2d = np.linalg.norm(ue.position - bs.position)
                d_3d = np.sqrt(d_2d**2 + (bs.height_m - ue.height_m)**2)
                d_3d = max(d_3d, 1.0)

                # LOS probability (simplified 3GPP UMa)
                p_los = min(18.0 / d_2d, 1.0) * (1 - np.exp(-d_2d / 63.0)) + np.exp(-d_2d / 63.0)
                is_los = self._rng.random() < p_los

                if is_los:
                    pl_db = _urban_macro_los(d_3d, bs.frequency_ghz, bs.height_m, ue.height_m)
                else:
                    pl_db = _urban_macro_nlos(d_3d, bs.frequency_ghz, bs.height_m, ue.height_m)

                # Shadow fading
                shadow_std = 4.0 if is_los else 6.0
                shadow_db = self._rng.normal(0, shadow_std)
                total_pl_db = pl_db + shadow_db

                # Channel gain (linear)
                self.channel_matrix[u, b] = 10 ** (-total_pl_db / 10)

        self._compute_sinr()

    def _compute_sinr(self) -> None:
        """Compute downlink SINR for each UE from its serving BS."""
        n_ue = len(self.users)
        n_bs = len(self.base_stations)
        thermal_noise_dbm = -174 + 10 * np.log10(self.base_stations[0].bandwidth_mhz * 1e6) if n_bs > 0 else -100
        noise_linear = 10 ** ((thermal_noise_dbm) / 10)

        for u, ue in enumerate(self.users):
            if not ue.active:
                continue
            for b, bs in enumerate(self.base_stations):
                if not bs.active:
                    continue
                tx_linear = 10 ** (bs.tx_power_dbm / 10)
                signal = tx_linear * self.channel_matrix[u, b]
                # Interference from other BS
                interference = 0.0
                for b2, bs2 in enumerate(self.base_stations):
                    if b2 != b and bs2.active:
                        tx2 = 10 ** (bs2.tx_power_dbm / 10)
                        interference += tx2 * self.channel_matrix[u, b2]
                nf_linear = 10 ** (ue.noise_figure_db / 10)
                sinr_linear = signal / (interference + noise_linear * nf_linear)
                self.sinr_matrix[u, b] = 10 * np.log10(max(sinr_linear, 1e-20))

    # ── Association ────────────────────────────────────────────────

    def associate_users_max_sinr(self) -> None:
        """Assign each UE to the BS with highest SINR."""
        for u, ue in enumerate(self.users):
            if not ue.active:
                continue
            best_bs = int(np.argmax(self.sinr_matrix[u, :]))
            ue.serving_bs = self.base_stations[best_bs].id

    # ── Mutation helpers (called only by Engine) ───────────────────

    def apply_allocation(self, allocation: np.ndarray) -> None:
        """
        Apply a resource allocation decision.
        
        Parameters
        ----------
        allocation : np.ndarray
            (num_ue × num_bs) fractional PRB assignment.
        """
        self.allocation_matrix = allocation.copy()

    def update_user_positions(self, new_positions: np.ndarray) -> None:
        """
        Update user positions (called by mobility model).
        
        Parameters
        ----------
        new_positions : np.ndarray
            (num_ue × 2) new (x, y) positions.
        """
        for i, ue in enumerate(self.users):
            ue.position = new_positions[i].copy()

    def update_user_demands(self, new_demands: np.ndarray) -> None:
        """
        Update user traffic demands (called by traffic model).
        
        Parameters
        ----------
        new_demands : np.ndarray
            (num_ue,) new demand values in Mbps.
        """
        for i, ue in enumerate(self.users):
            ue.traffic_demand_mbps = float(new_demands[i])

    # ── Metrics ────────────────────────────────────────────────────

    def collect_metrics(self) -> dict:
        """
        Compute and store per-timestep metrics.
        
        Returns
        -------
        dict
            Metrics including throughput, fairness, avg SINR, etc.
        """
        serving = self.get_snapshot()["ue_serving_bs"]
        sinr_served = []
        throughputs = []

        for u, ue in enumerate(self.users):
            if not ue.active or serving[u] < 0:
                continue
            b = int(serving[u])
            # find BS index
            b_idx = next((i for i, bs in enumerate(self.base_stations) if bs.id == b), None)
            if b_idx is None:
                continue
            sinr_db = self.sinr_matrix[u, b_idx]
            sinr_served.append(sinr_db)
            # Shannon capacity (simplified)
            bw = self.base_stations[b_idx].bandwidth_mhz * 1e6
            alloc_frac = self.allocation_matrix[u, b_idx] if self.allocation_matrix[u, b_idx] > 0 else 1.0 / max(len(self.users), 1)
            sinr_lin = 10 ** (sinr_db / 10)
            tp = alloc_frac * bw * np.log2(1 + sinr_lin) / 1e6  # Mbps
            throughputs.append(tp)

        throughputs_arr = np.array(throughputs) if throughputs else np.array([0.0])
        sinr_arr = np.array(sinr_served) if sinr_served else np.array([-np.inf])

        metrics = {
            "timestep": self.timestep,
            "avg_throughput_mbps": float(np.mean(throughputs_arr)),
            "sum_throughput_mbps": float(np.sum(throughputs_arr)),
            "min_throughput_mbps": float(np.min(throughputs_arr)),
            "avg_sinr_db": float(np.mean(sinr_arr)),
            "fairness_jain": float(
                np.sum(throughputs_arr) ** 2 /
                (len(throughputs_arr) * np.sum(throughputs_arr ** 2))
            ) if np.sum(throughputs_arr ** 2) > 0 else 0.0,
            "num_active_ues": int(np.sum([ue.active for ue in self.users])),
            "num_active_bs": int(np.sum([bs.active for bs in self.base_stations])),
        }

        self.metrics_history.append(metrics)
        return metrics

    # ── Serialization ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize state to dict (for JSON export)."""
        return {
            "timestep": self.timestep,
            "area_size": list(self.area_size),
            "base_stations": [
                {"id": bs.id, "position": bs.position.tolist(),
                 "tx_power_dbm": bs.tx_power_dbm, "frequency_ghz": bs.frequency_ghz,
                 "num_antennas": bs.num_antennas, "bandwidth_mhz": bs.bandwidth_mhz,
                 "num_prbs": bs.num_prbs, "height_m": bs.height_m}
                for bs in self.base_stations
            ],
            "users": [
                {"id": ue.id, "position": ue.position.tolist(),
                 "serving_bs": ue.serving_bs, "traffic_demand_mbps": ue.traffic_demand_mbps}
                for ue in self.users
            ],
            "metrics_history": self.metrics_history,
        }
