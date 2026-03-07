#!/usr/bin/env python3
"""
run_benchmarks.py — TELEQUM Benchmark Suite Runner
====================================================

Executes predefined benchmark scenarios across problem categories:
- Resource Allocation
- Interference Coordination
- Network Slicing
- Energy Optimization
- Routing

Compares classical baselines (greedy, SA) with quantum solvers
across multiple random seeds for statistical rigour.

Usage:
    python run_benchmarks.py --category resource_allocation --seeds 5
    python run_benchmarks.py --all
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from telequm.simulator.engine import SimulationEngine
from telequm.simulator.optimization_bridge import (
    OptimizationBridge, ResourceAllocationQUBO, ClassicalBaselines,
)
from experiments.metrics import compute_aggregate_metrics, compare_solvers

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(name)s  %(message)s")
logger = logging.getLogger("telequm.benchmarks")

BENCHMARK_DIR = Path(__file__).parent / "benchmarks"


# ─── Predefined Benchmark Instances ──────────────────────────────

def generate_small_network(n_bs: int = 2, n_ue: int = 4, seed: int = 42) -> dict:
    """Small instance for exact solver comparison."""
    rng = np.random.default_rng(seed)
    return {
        "experiment": {"name": f"bench_small_{n_bs}bs_{n_ue}ue", "description": "Small benchmark"},
        "network": {
            "area_size": [500, 500],
            "random_seed": seed,
            "base_stations": [
                {"id": i, "position": rng.uniform(50, 450, 2).tolist(),
                 "tx_power_dbm": 43.0, "frequency_ghz": 3.5,
                 "num_antennas": 32, "bandwidth_mhz": 40.0,
                 "num_prbs": 106, "height_m": 25.0}
                for i in range(n_bs)
            ],
            "users": [
                {"id": j, "position": rng.uniform(0, 500, 2).tolist(),
                 "traffic_demand_mbps": float(rng.uniform(1, 20))}
                for j in range(n_ue)
            ],
        },
        "simulation": {"num_timesteps": 20, "dt": 1.0, "random_seed": seed,
                        "channel_update_interval": 5, "optimization_interval": 5},
        "traffic": {"model": "poisson", "arrival_rate": 1.0, "session_rate_mbps": 5.0},
        "mobility": {"model": "pedestrian", "speed_mean": 1.0},
        "solver": {"classical_method": "greedy", "run_quantum": False},
    }


def generate_medium_network(n_bs: int = 4, n_ue: int = 16, seed: int = 42) -> dict:
    """Medium instance — practical size for QAOA."""
    rng = np.random.default_rng(seed)
    return {
        "experiment": {"name": f"bench_medium_{n_bs}bs_{n_ue}ue", "description": "Medium benchmark"},
        "network": {
            "area_size": [1000, 1000],
            "random_seed": seed,
            "base_stations": [
                {"id": i,
                 "position": [(i % 2) * 500 + 250, (i // 2) * 500 + 250],
                 "tx_power_dbm": 46.0, "frequency_ghz": 3.5,
                 "num_antennas": 64, "bandwidth_mhz": 100.0,
                 "num_prbs": 273, "height_m": 25.0}
                for i in range(n_bs)
            ],
            "users": [
                {"id": j, "position": rng.uniform(0, 1000, 2).tolist(),
                 "traffic_demand_mbps": float(rng.uniform(5, 30))}
                for j in range(n_ue)
            ],
        },
        "simulation": {"num_timesteps": 30, "dt": 1.0, "random_seed": seed,
                        "channel_update_interval": 5, "optimization_interval": 10},
        "traffic": {"model": "poisson"},
        "mobility": {"model": "random_waypoint"},
        "solver": {"classical_method": "greedy", "run_quantum": False},
    }


def generate_large_network(n_bs: int = 7, n_ue: int = 50, seed: int = 42) -> dict:
    """Large instance — scalability test (classical only)."""
    rng = np.random.default_rng(seed)
    return {
        "experiment": {"name": f"bench_large_{n_bs}bs_{n_ue}ue", "description": "Large benchmark"},
        "network": {
            "area_size": [2000, 2000],
            "random_seed": seed,
            "base_stations": [
                {"id": i, "position": rng.uniform(100, 1900, 2).tolist(),
                 "tx_power_dbm": 46.0, "frequency_ghz": 3.5,
                 "num_antennas": 64, "bandwidth_mhz": 100.0,
                 "num_prbs": 273, "height_m": 25.0}
                for i in range(n_bs)
            ],
            "users": [
                {"id": j, "position": rng.uniform(0, 2000, 2).tolist(),
                 "traffic_demand_mbps": float(rng.uniform(2, 40))}
                for j in range(n_ue)
            ],
        },
        "simulation": {"num_timesteps": 50, "dt": 1.0, "random_seed": seed,
                        "channel_update_interval": 10, "optimization_interval": 10},
        "traffic": {"model": "poisson"},
        "mobility": {"model": "vehicular"},
        "solver": {"classical_method": "simulated_annealing", "run_quantum": False},
    }


# ─── Benchmark Runner ───────────────────────────────────────────

def run_resource_allocation_benchmark(seeds: int = 3, verbose: bool = True) -> dict:
    """Run resource allocation benchmark across sizes and seeds."""
    results = {}
    configs = {
        "small": lambda s: generate_small_network(2, 4, s),
        "medium": lambda s: generate_medium_network(4, 8, s),
        "large": lambda s: generate_large_network(7, 20, s),
    }

    for size, config_fn in configs.items():
        size_results = []
        for seed in range(seeds):
            config = config_fn(seed)
            engine = SimulationEngine(config)
            problem = ResourceAllocationQUBO()
            bridge = OptimizationBridge(problem)
            engine.set_bridge(bridge)

            result = engine.run(verbose=False)
            agg = compute_aggregate_metrics(result["metrics"])
            comp = compare_solvers(result)
            size_results.append({
                "seed": seed,
                "agg_metrics": agg,
                "solver_comparison": comp,
                "runtime_s": result["total_runtime_s"],
            })

            if verbose:
                logger.info(
                    "%s/seed=%d → throughput=%.1f Mbps, runtime=%.2fs",
                    size, seed,
                    agg.get("avg_throughput_mbps", {}).get("mean", 0),
                    result["total_runtime_s"],
                )

        results[size] = size_results

    return results


def main():
    parser = argparse.ArgumentParser(description="TELEQUM Benchmark Suite")
    parser.add_argument("--category", type=str, default="resource_allocation",
                        choices=["resource_allocation", "all"])
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--output", "-o", type=str, default=None)
    args = parser.parse_args()

    t0 = time.time()

    if args.category in ("resource_allocation", "all"):
        results = run_resource_allocation_benchmark(seeds=args.seeds)

        out_path = args.output or str(
            BENCHMARK_DIR / "resource_allocation" / "results" / "benchmark_results.json"
        )
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("Benchmark results saved to %s", out_path)

    logger.info("Total benchmark time: %.1f s", time.time() - t0)


if __name__ == "__main__":
    main()
