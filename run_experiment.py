#!/usr/bin/env python3
"""
run_experiment.py — Execute a TELEQUM simulation experiment
============================================================

Usage:
    python run_experiment.py experiments/resource_allocation/config.yaml

Loads config, builds the simulation engine, runs the loop,
and saves results + metrics to the results/ sub-directory.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

# Ensure package is importable when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from telequm.simulator.engine import SimulationEngine
from telequm.simulator.optimization_bridge import (
    OptimizationBridge,
    ResourceAllocationQUBO,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
)
logger = logging.getLogger("telequm.run_experiment")


def main():
    parser = argparse.ArgumentParser(description="Run a TELEQUM experiment")
    parser.add_argument("config", type=str, help="Path to experiment config.yaml")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Override output path for results JSON")
    args = parser.parse_args()

    # ── Load config ──────────────────────────────────────────────
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Config not found: %s", config_path)
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)
    logger.info("Loaded config: %s", config["experiment"]["name"])

    # ── Build engine ─────────────────────────────────────────────
    engine = SimulationEngine(config)

    # ── Attach optimization bridge ───────────────────────────────
    problem = ResourceAllocationQUBO(penalty=10.0)
    bridge = OptimizationBridge(problem)
    engine.set_bridge(bridge)

    # ── Run simulation ───────────────────────────────────────────
    results = engine.run(verbose=True)

    # ── Save results ─────────────────────────────────────────────
    if args.output:
        out_path = args.output
    else:
        out_dir = config_path.parent / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        exp_name = config["experiment"]["name"]
        seed = config["simulation"]["random_seed"]
        out_path = str(out_dir / f"{exp_name}_seed{seed}.json")

    engine.save_results(out_path)
    logger.info("Experiment complete. Results: %s", out_path)

    # ── Summary ──────────────────────────────────────────────────
    metrics = results["metrics"]
    if metrics:
        last = metrics[-1]
        logger.info(
            "Final metrics → throughput=%.1f Mbps | SINR=%.1f dB | fairness=%.3f",
            last["avg_throughput_mbps"],
            last["avg_sinr_db"],
            last["fairness_jain"],
        )
    logger.info(
        "Classical solutions: %d | Quantum solutions: %d",
        len(results["classical_solutions"]),
        len(results["quantum_solutions"]),
    )


if __name__ == "__main__":
    main()
