"""
Experiment Metrics — Post-Hoc Analysis Utilities
=================================================

Load simulation results and compute aggregate metrics
for comparison across solver methods and seeds.
"""

from __future__ import annotations

import json

import numpy as np


def load_results(path: str) -> dict:
    """Load a results JSON file."""
    with open(path) as f:
        return json.load(f)


def compute_aggregate_metrics(metrics: list[dict]) -> dict:
    """
    Compute aggregate statistics from per-timestep metrics.

    Returns
    -------
    dict  with mean, std, min, max for each numeric metric.
    """
    if not metrics:
        return {}

    keys = [k for k in metrics[0] if k != "timestep"]
    agg = {}
    for key in keys:
        vals = np.array([m.get(key, 0.0) for m in metrics])
        agg[key] = {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "p5": float(np.percentile(vals, 5)),
            "p95": float(np.percentile(vals, 95)),
        }
    return agg


def compare_solvers(results: dict) -> dict:
    """
    Compare classical vs. quantum solver performance.

    Returns
    -------
    dict  with per-solver cost and runtime statistics.
    """
    comparison = {}
    for key in ["classical_solutions", "quantum_solutions"]:
        sols = results.get(key, [])
        if not sols:
            comparison[key] = {"count": 0}
            continue
        costs = [s["cost"] for s in sols if "cost" in s]
        runtimes = [s["runtime_s"] for s in sols if "runtime_s" in s]
        comparison[key] = {
            "count": len(sols),
            "mean_cost": float(np.mean(costs)) if costs else None,
            "std_cost": float(np.std(costs)) if costs else None,
            "mean_runtime_s": float(np.mean(runtimes)) if runtimes else None,
            "methods": list({s.get("method", "unknown") for s in sols}),
        }
    return comparison


def convergence_series(solutions: list[dict]) -> dict[str, list]:
    """
    Extract timestep–cost pairs for convergence plotting.
    """
    return {
        "timesteps": [s["timestep"] for s in solutions if "timestep" in s],
        "costs": [s["cost"] for s in solutions if "cost" in s],
        "runtimes": [s["runtime_s"] for s in solutions if "runtime_s" in s],
    }
