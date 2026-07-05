"""
Scenario Generators — Standard Network Scenarios
==================================================

Produce reproducible ``UniversalNetworkSnapshot`` instances
for benchmarks, experiments, and dashboard demos.
"""

from __future__ import annotations

import numpy as np

from telequm.core.network_snapshot import UniversalNetworkSnapshot


def generate_small_network(seed: int = 42) -> UniversalNetworkSnapshot:
    """
    Small network: 7 hexagonal cells, 50 users.

    Suitable for exact QUBO solving and rapid prototyping.
    """
    snap = UniversalNetworkSnapshot(source="standalone", metadata={"scenario": "small", "seed": seed})
    snap.area_size = (800.0, 800.0)

    # Hexagonal-ish layout
    positions = np.array([
        [400, 400], [200, 200], [600, 200], [200, 600],
        [600, 600], [400, 150], [400, 650],
    ])
    snap.add_cells(7, positions=positions, seed=seed)
    snap.add_users(50, mobility_model="RandomWaypoint", seed=seed)
    snap.initialize_links()
    return snap


def generate_medium_network(seed: int = 42) -> UniversalNetworkSnapshot:
    """
    Medium network: 19 cells, 200 users.

    Standard 3GPP evaluation: 2 rings of hexagonal cells.
    """
    snap = UniversalNetworkSnapshot(source="standalone", metadata={"scenario": "medium", "seed": seed})
    snap.area_size = (2000.0, 2000.0)

    # 19-cell hex layout (approximate)
    np.random.default_rng(seed)
    isd = 500.0
    center = np.array([1000, 1000])
    positions = [center]
    for ring in range(1, 3):
        for angle_idx in range(6 * ring):
            angle = 2 * np.pi * angle_idx / (6 * ring)
            r = ring * isd * 0.7
            pos = center + r * np.array([np.cos(angle), np.sin(angle)])
            if len(positions) < 19:
                positions.append(pos)

    positions = np.array(positions[:19])
    snap.add_cells(19, positions=positions, seed=seed)
    snap.add_users(200, mobility_model="RandomWaypoint", seed=seed, min_demand=5, max_demand=40)
    snap.initialize_links()
    return snap


def generate_large_network(seed: int = 42) -> UniversalNetworkSnapshot:
    """
    Large network: 37 cells, 500 users.

    Scalability stress test — classical solvers only.
    """
    snap = UniversalNetworkSnapshot(source="standalone", metadata={"scenario": "large", "seed": seed})
    snap.area_size = (3000.0, 3000.0)
    snap.add_cells(37, seed=seed)
    snap.add_users(500, mobility_model="Vehicular", seed=seed, min_demand=2, max_demand=50)
    snap.initialize_links()
    return snap


def generate_mobility_stress(seed: int = 42) -> UniversalNetworkSnapshot:
    """
    Mobility stress test: 7 cells, 100 high-speed vehicular users.

    Tests handover and re-association under rapid mobility.
    User velocities set to 30–120 km/h.
    """
    snap = UniversalNetworkSnapshot(
        source="standalone",
        metadata={"scenario": "mobility_stress", "seed": seed, "mobility_model": "Vehicular"},
    )
    snap.area_size = (1000.0, 1000.0)
    snap.add_cells(7, seed=seed)

    rng = np.random.default_rng(seed)
    for j in range(100):
        speed = rng.uniform(8.3, 33.3)  # 30–120 km/h
        angle = rng.uniform(0, 2 * np.pi)
        snap.users.append(
            __import__("telequm.core.network_snapshot", fromlist=["UserInfo"]).UserInfo(
                user_id=j,
                position=rng.uniform(0, snap.area_size),
                velocity=np.array([speed * np.cos(angle), speed * np.sin(angle)]),
                traffic_demand_mbps=float(rng.uniform(10, 30)),
            )
        )

    snap.initialize_links()
    return snap
