"""
Snapshot Manager — Isolated Environment Copies
================================================

Creates temporary, isolated copies of NetworkEnvironment
for safe scenario execution. Dashboard NEVER modifies the
original environment (Rule #11: read-only dashboard).
"""

from __future__ import annotations

import copy
from typing import Dict, Optional

from telequm.simulator.network_env import NetworkEnvironment
from telequm.simulator.engine import SimulationEngine
from telequm.simulator.optimization_bridge import (
    OptimizationBridge,
    ResourceAllocationQUBO,
)


def create_snapshot_env(config: dict) -> NetworkEnvironment:
    """
    Create a fresh, isolated NetworkEnvironment from config.

    Parameters
    ----------
    config : dict
        Network config (the 'network' key from experiment config).

    Returns
    -------
    NetworkEnvironment  new isolated instance
    """
    net_cfg = config.get("network", config)
    return NetworkEnvironment(net_cfg)


def run_scenario(config: dict, verbose: bool = False) -> dict:
    """
    Execute a complete scenario on an isolated environment.

    This is the main entry point for dashboard scenario execution.
    It creates a fresh engine, attaches the optimization bridge,
    runs the simulation, and returns results.

    Parameters
    ----------
    config : dict
        Full experiment config.
    verbose : bool
        Whether to log progress.

    Returns
    -------
    dict with keys: metrics, classical_solutions, quantum_solutions,
         total_runtime_s, environment_final
    """
    engine = SimulationEngine(config)
    problem = ResourceAllocationQUBO(penalty=10.0)
    bridge = OptimizationBridge(problem)
    engine.set_bridge(bridge)
    return engine.run(verbose=verbose)


def get_env_summary(env: NetworkEnvironment) -> dict:
    """
    Get a human-readable summary of a NetworkEnvironment.

    Returns
    -------
    dict  summary stats for dashboard display
    """
    snap = env.get_snapshot()
    return {
        "num_base_stations": snap["num_bs"],
        "num_users": snap["num_ue"],
        "area_size": list(env.area_size),
        "avg_sinr_db": float(snap["sinr_matrix"][snap["sinr_matrix"] > -999].mean())
        if snap["sinr_matrix"].size > 0 else 0.0,
        "sinr_range": [
            float(snap["sinr_matrix"][snap["sinr_matrix"] > -999].min()),
            float(snap["sinr_matrix"][snap["sinr_matrix"] > -999].max()),
        ] if snap["sinr_matrix"].size > 0 else [0, 0],
        "total_demand_mbps": float(snap["ue_demands"].sum()),
    }
