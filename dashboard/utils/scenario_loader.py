"""
Scenario Loader — Load and Parse Experiment Configs
====================================================

Handles predefined YAML configs, custom YAML uploads,
and interactive slider-based scenario creation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "experiments"
BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent / "benchmarks"


def list_presets() -> list[dict]:
    """
    List available preset experiment configs.

    Returns
    -------
    list of dict
        Each dict has 'name', 'path', and 'description'.
    """
    presets = []
    for yaml_path in sorted(PRESETS_DIR.rglob("config.yaml")):
        try:
            with open(yaml_path) as f:
                cfg = yaml.safe_load(f)
            presets.append({
                "name": cfg.get("experiment", {}).get("name", yaml_path.parent.name),
                "path": str(yaml_path),
                "description": cfg.get("experiment", {}).get("description", ""),
            })
        except Exception:
            continue
    return presets


def load_preset(path: str) -> dict:
    """Load a preset config from a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def parse_uploaded_yaml(content: str) -> dict:
    """
    Parse a user-uploaded YAML string.

    Parameters
    ----------
    content : str
        Raw YAML text from Streamlit file uploader.

    Returns
    -------
    dict  parsed config

    Raises
    ------
    ValueError  if YAML is invalid or missing required keys
    """
    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}") from e

    required = ["network", "simulation"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")
    return config


def build_config_from_sliders(
    num_bs: int = 4,
    num_ue: int = 10,
    area_width: float = 1000.0,
    area_height: float = 1000.0,
    tx_power_dbm: float = 46.0,
    frequency_ghz: float = 3.5,
    num_timesteps: int = 50,
    traffic_model: str = "poisson",
    mobility_model: str = "pedestrian",
    seed: int = 42,
    solver_method: str = "greedy",
    run_quantum: bool = False,
) -> dict:
    """
    Build a config dict from dashboard slider values.

    Returns
    -------
    dict  ready to pass to SimulationEngine
    """
    rng = np.random.default_rng(seed)

    # Place BS on a grid
    cols = int(np.ceil(np.sqrt(num_bs)))
    rows = int(np.ceil(num_bs / cols))
    bs_list = []
    for i in range(num_bs):
        r, c = divmod(i, cols)
        x = (c + 0.5) * area_width / cols
        y = (r + 0.5) * area_height / rows
        bs_list.append({
            "id": i,
            "position": [float(x), float(y)],
            "tx_power_dbm": tx_power_dbm,
            "frequency_ghz": frequency_ghz,
            "num_antennas": 64,
            "bandwidth_mhz": 100.0,
            "num_prbs": 273,
            "height_m": 25.0,
        })

    ue_list = []
    for j in range(num_ue):
        ue_list.append({
            "id": j,
            "position": rng.uniform(0, [area_width, area_height]).tolist(),
            "traffic_demand_mbps": float(rng.uniform(5, 30)),
        })

    return {
        "experiment": {
            "name": f"interactive_{num_bs}bs_{num_ue}ue",
            "description": "Interactive dashboard scenario",
        },
        "network": {
            "area_size": [area_width, area_height],
            "random_seed": seed,
            "base_stations": bs_list,
            "users": ue_list,
        },
        "simulation": {
            "num_timesteps": num_timesteps,
            "dt": 1.0,
            "random_seed": seed,
            "channel_update_interval": 5,
            "optimization_interval": 10,
        },
        "traffic": {"model": traffic_model},
        "mobility": {"model": mobility_model},
        "solver": {
            "classical_method": solver_method,
            "run_quantum": run_quantum,
            "max_quantum_vars": 16,
            "shots": 1024,
            "p": 2,
        },
    }
