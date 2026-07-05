"""
Benchmark Instances — Standardized Network Topologies
======================================================

Predefined network configurations for reproducible
benchmark evaluations.
"""

from __future__ import annotations

import numpy as np


def hexagonal_topology(
    num_rings: int = 1,
    isd: float = 500.0,
    ues_per_cell: int = 5,
    seed: int = 42,
) -> dict:
    """
    3GPP-style hexagonal BS layout.

    Parameters
    ----------
    num_rings : int  number of hex rings (1 = 7 cells, 2 = 19 cells)
    isd : float      inter-site distance in metres
    ues_per_cell : int
    seed : int

    Returns
    -------
    dict  network config
    """
    rng = np.random.default_rng(seed)

    # Generate hex BS positions
    bs_positions = [(0.0, 0.0)]
    for ring in range(1, num_rings + 1):
        for side in range(6):
            for step in range(ring):
                angle = np.pi / 3 * side + np.pi / 6
                x = ring * isd * np.cos(angle) - step * isd * np.cos(angle + np.pi / 3)
                y = ring * isd * np.sin(angle) - step * isd * np.sin(angle + np.pi / 3)
                if (round(x, 1), round(y, 1)) not in [(round(p[0], 1), round(p[1], 1)) for p in bs_positions]:
                    bs_positions.append((x, y))

    n_bs = len(bs_positions)
    n_ue = n_bs * ues_per_cell

    # Center positions so all are positive
    min_x = min(p[0] for p in bs_positions) - isd
    min_y = min(p[1] for p in bs_positions) - isd
    bs_positions = [(p[0] - min_x, p[1] - min_y) for p in bs_positions]
    max_x = max(p[0] for p in bs_positions) + isd
    max_y = max(p[1] for p in bs_positions) + isd

    bs_list = [
        {"id": i, "position": list(pos), "tx_power_dbm": 46.0,
         "frequency_ghz": 3.5, "num_antennas": 64,
         "bandwidth_mhz": 100.0, "num_prbs": 273, "height_m": 25.0}
        for i, pos in enumerate(bs_positions)
    ]

    ue_list = [
        {"id": j, "position": rng.uniform(0, [max_x, max_y]).tolist(),
         "traffic_demand_mbps": float(rng.uniform(5, 30))}
        for j in range(n_ue)
    ]

    return {
        "area_size": [max_x, max_y],
        "random_seed": seed,
        "base_stations": bs_list,
        "users": ue_list,
    }


def nsfnet_topology(ues_per_node: int = 3, seed: int = 42) -> dict:
    """
    NSFNET 14-node topology (classic network benchmark).

    Returns
    -------
    dict  network config
    """
    rng = np.random.default_rng(seed)

    # Approximate NSFNET node positions (normalised to 2000×1000m)
    nodes = [
        (200, 800), (400, 900), (300, 600), (600, 700),
        (800, 800), (700, 500), (500, 400), (900, 600),
        (1100, 700), (1300, 800), (1000, 400), (1200, 500),
        (1500, 600), (1700, 700),
    ]

    bs_list = [
        {"id": i, "position": list(pos), "tx_power_dbm": 43.0,
         "frequency_ghz": 3.5, "num_antennas": 32,
         "bandwidth_mhz": 40.0, "num_prbs": 106, "height_m": 20.0}
        for i, pos in enumerate(nodes)
    ]

    n_ue = len(nodes) * ues_per_node
    ue_list = [
        {"id": j, "position": rng.uniform(0, [1800, 1000]).tolist(),
         "traffic_demand_mbps": float(rng.uniform(2, 25))}
        for j in range(n_ue)
    ]

    return {
        "area_size": [1800, 1000],
        "random_seed": seed,
        "base_stations": bs_list,
        "users": ue_list,
    }


def mesh_topology(
    rows: int = 3,
    cols: int = 3,
    spacing: float = 300.0,
    ues_per_node: int = 4,
    seed: int = 42,
) -> dict:
    """
    Regular mesh/grid BS topology.

    Returns
    -------
    dict  network config
    """
    rng = np.random.default_rng(seed)

    bs_list = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            bs_list.append({
                "id": idx,
                "position": [(c + 0.5) * spacing, (r + 0.5) * spacing],
                "tx_power_dbm": 46.0, "frequency_ghz": 3.5,
                "num_antennas": 64, "bandwidth_mhz": 100.0,
                "num_prbs": 273, "height_m": 25.0,
            })
            idx += 1

    n_ue = rows * cols * ues_per_node
    area = [cols * spacing, rows * spacing]
    ue_list = [
        {"id": j, "position": rng.uniform(0, area).tolist(),
         "traffic_demand_mbps": float(rng.uniform(5, 30))}
        for j in range(n_ue)
    ]

    return {
        "area_size": area,
        "random_seed": seed,
        "base_stations": bs_list,
        "users": ue_list,
    }
