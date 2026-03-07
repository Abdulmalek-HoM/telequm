"""
Data Loader — Load Benchmark & Experiment Results
===================================================

Utility for loading previously-run experiment and benchmark
results for dashboard display.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


RESULTS_BASE = Path(__file__).resolve().parent.parent.parent


def load_experiment_results(experiment_name: str) -> Optional[dict]:
    """
    Load results JSON for a named experiment.

    Parameters
    ----------
    experiment_name : str
        e.g., 'resource_allocation'

    Returns
    -------
    dict or None
    """
    results_dir = RESULTS_BASE / "experiments" / experiment_name / "results"
    if not results_dir.exists():
        return None
    json_files = sorted(results_dir.glob("*.json"))
    if not json_files:
        return None
    with open(json_files[-1]) as f:
        return json.load(f)


def load_benchmark_results(category: str = "resource_allocation") -> Optional[dict]:
    """
    Load benchmark results for a category.

    Parameters
    ----------
    category : str
        e.g., 'resource_allocation'

    Returns
    -------
    dict or None
    """
    path = RESULTS_BASE / "benchmarks" / category / "results" / "benchmark_results.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_experiment_results() -> List[dict]:
    """List all available experiment result files."""
    results = []
    exp_dir = RESULTS_BASE / "experiments"
    if not exp_dir.exists():
        return results
    for json_file in sorted(exp_dir.rglob("results/*.json")):
        try:
            with open(json_file) as f:
                data = json.load(f)
            results.append({
                "path": str(json_file),
                "name": json_file.stem,
                "num_metrics": len(data.get("metrics", [])),
            })
        except Exception:
            continue
    return results


def list_benchmark_results() -> List[dict]:
    """List all available benchmark result files."""
    results = []
    bench_dir = RESULTS_BASE / "benchmarks"
    if not bench_dir.exists():
        return results
    for json_file in sorted(bench_dir.rglob("results/*.json")):
        results.append({
            "path": str(json_file),
            "category": json_file.parent.parent.name,
            "name": json_file.stem,
        })
    return results
