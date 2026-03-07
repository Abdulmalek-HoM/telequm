"""
Snapshot Manager — Isolated Environment Copies
================================================

Creates temporary, isolated copies of NetworkEnvironment
for safe scenario execution. Dashboard NEVER modifies the
original environment (Rule #11: read-only dashboard).
"""

from __future__ import annotations

import time
from typing import Dict, Optional

import numpy as np

from telequm.simulator.network_env import NetworkEnvironment
from telequm.simulator.engine import SimulationEngine
from telequm.simulator.optimization_bridge import (
    OptimizationBridge,
    ResourceAllocationQUBO,
    ClassicalBaselines,
)
from telequm.core.network_snapshot import UniversalNetworkSnapshot


def create_snapshot_env(config: dict) -> NetworkEnvironment:
    """Create a fresh, isolated NetworkEnvironment from config."""
    net_cfg = config.get("network", config)
    return NetworkEnvironment(net_cfg)


def run_scenario(config: dict, verbose: bool = False) -> dict:
    """Execute a complete scenario using the SimulationEngine."""
    engine = SimulationEngine(config)
    problem = ResourceAllocationQUBO(penalty=10.0)
    bridge = OptimizationBridge(problem)
    engine.set_bridge(bridge)
    return engine.run(verbose=verbose)


def run_problem_direct(
    config: dict,
    problem_type: str = "prb_allocation",
    solver_method: str = "greedy",
    run_quantum: bool = False,
) -> dict:
    """
    Run a problem formulation directly on a snapshot — bypasses
    the engine loop for instant single-shot comparison.

    Parameters
    ----------
    config : dict
        Full experiment config.
    problem_type : str
        One of: prb_allocation, routing, beam_selection,
        energy_efficiency, handover
    solver_method : str
        Classical: greedy, simulated_annealing, exact
        Hybrid: hybrid_quantum_first, hybrid_ensemble
    run_quantum : bool
        Whether to also run quantum solver for comparison.

    Returns
    -------
    dict with classical_result, quantum_result, metrics, snapshot_info
    """
    # Build snapshot
    snap = UniversalNetworkSnapshot(source="standalone")
    net = config.get("network", {})
    snap.area_size = tuple(net.get("area_size", [1000, 1000]))

    for bs in net.get("base_stations", []):
        from telequm.core.network_snapshot import CellInfo
        snap.cells.append(CellInfo(
            cell_id=bs["id"],
            position=np.array(bs["position"]),
            tx_power_dbm=bs.get("tx_power_dbm", 46.0),
            frequency_ghz=bs.get("frequency_ghz", 3.5),
            num_antennas=bs.get("num_antennas", 64),
            bandwidth_mhz=bs.get("bandwidth_mhz", 100.0),
            num_prbs=bs.get("num_prbs", 273),
            height_m=bs.get("height_m", 25.0),
        ))

    for ue in net.get("users", []):
        from telequm.core.network_snapshot import UserInfo
        snap.users.append(UserInfo(
            user_id=ue["id"],
            position=np.array(ue["position"]),
            traffic_demand_mbps=ue.get("traffic_demand_mbps", 10.0),
        ))

    snap.initialize_links()

    # Build problem
    problem = _build_problem(problem_type, snap)

    # Solve classical
    t0 = time.time()
    if solver_method.startswith("hybrid_"):
        from telequm.algorithms.hybrid import HybridSolver
        strategy = solver_method.replace("hybrid_", "")
        solver = HybridSolver(strategy=strategy)
        hybrid_result = solver.solve(problem, classical_method="greedy")
        # Extract the usable solution from hybrid's nested structure
        if "classical" in hybrid_result and "solution" in hybrid_result["classical"]:
            classical_result = hybrid_result["classical"]["solution"]
        elif "best_solution" in hybrid_result and "solution" in hybrid_result["best_solution"]:
            classical_result = hybrid_result["best_solution"]["solution"]
        elif "solution" in hybrid_result:
            classical_result = hybrid_result["solution"]
        else:
            # Fallback: run classical directly
            classical_result = problem.solve_classical("greedy")

        classical_result["method"] = solver_method
        classical_result["hybrid_detail"] = {
            k: v for k, v in hybrid_result.items()
            if k not in ("solution", "classical")
        }
    else:
        classical_result = problem.solve_classical(solver_method)

    classical_result["runtime_s"] = time.time() - t0
    classical_metrics = problem.compute_metrics(classical_result)


    # Solve quantum (if enabled + small enough)
    quantum_result = None
    quantum_metrics = None
    num_vars = _get_num_vars(problem_type, snap)
    max_q = config.get("solver", {}).get("max_quantum_vars", 20)

    if run_quantum and num_vars <= max_q:
        try:
            t0 = time.time()
            quantum_result = problem.solve_quantum(algorithm="qaoa")
            quantum_result["runtime_s"] = time.time() - t0
            quantum_metrics = problem.compute_metrics(quantum_result)
        except Exception as e:
            quantum_result = {"error": str(e), "method": "quantum_qaoa"}
    elif run_quantum and num_vars > max_q:
        quantum_result = {
            "error": f"Problem too large for quantum: {num_vars} vars > max {max_q}",
            "method": "quantum_qaoa",
            "num_vars": num_vars,
            "max_quantum_vars": max_q,
        }

    return {
        "problem_type": problem_type,
        "solver_method": solver_method,
        "num_vars": num_vars,
        "classical_result": classical_result,
        "classical_metrics": classical_metrics,
        "quantum_result": quantum_result,
        "quantum_metrics": quantum_metrics,
        "snapshot_info": {
            "num_cells": snap.num_cells,
            "num_users": snap.num_users,
            "area_size": list(snap.area_size),
        },
        # Arrays for visualization
        "bs_positions": snap.cell_positions,
        "ue_positions": snap.user_positions,
        "sinr_matrix": snap.sinr_matrix,
        "serving_cells": snap.user_serving_cells,
        "allocation_matrix": classical_result.get("decoded", {}).get(
            "allocation_matrix", None
        ),
    }



def _build_problem(problem_type: str, snap: UniversalNetworkSnapshot):
    """Factory for problem instances."""
    from telequm.problems import (
        PRBAllocationProblem, RoutingOptimization,
        BeamSelection, EnergyEfficiency, HandoverOptimization,
    )
    if problem_type == "prb_allocation":
        return PRBAllocationProblem(snap)
    elif problem_type == "routing":
        return RoutingOptimization(snap)
    elif problem_type == "beam_selection":
        return BeamSelection(snap, num_beams=8)
    elif problem_type == "energy_efficiency":
        return EnergyEfficiency(snap)
    elif problem_type == "handover":
        return HandoverOptimization(snap)
    else:
        return PRBAllocationProblem(snap)


def _get_num_vars(problem_type: str, snap: UniversalNetworkSnapshot) -> int:
    """Estimate QUBO variable count for a problem."""
    n_ue, n_cell = snap.num_users, snap.num_cells
    if problem_type == "prb_allocation":
        return n_ue * n_cell
    elif problem_type == "routing":
        return n_cell * n_cell
    elif problem_type == "beam_selection":
        return n_ue * 8
    elif problem_type == "energy_efficiency":
        return n_cell + n_ue * n_cell
    elif problem_type == "handover":
        return n_ue * n_cell
    return n_ue * n_cell


def get_env_summary(env: NetworkEnvironment) -> dict:
    """Get a human-readable summary of a NetworkEnvironment."""
    snap = env.get_snapshot()
    valid = snap["sinr_matrix"][snap["sinr_matrix"] > -999]
    return {
        "num_base_stations": snap["num_bs"],
        "num_users": snap["num_ue"],
        "area_size": list(env.area_size),
        "avg_sinr_db": float(valid.mean()) if valid.size > 0 else 0.0,
        "sinr_range": [float(valid.min()), float(valid.max())] if valid.size > 0 else [0, 0],
        "total_demand_mbps": float(snap["ue_demands"].sum()),
    }
