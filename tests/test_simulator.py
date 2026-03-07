"""
Tests — TELEQUM v2.1 Simulator Test Suite
==========================================

Comprehensive pytest suite covering:
- NetworkEnvironment
- SimulationEngine
- Traffic & Mobility models
- EventQueue
- Optimization Bridge (QUBO + baselines)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ─── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def small_config():
    return {
        "experiment": {"name": "test_small"},
        "network": {
            "area_size": [500, 500],
            "random_seed": 42,
            "base_stations": [
                {"id": 0, "position": [125, 125], "tx_power_dbm": 46,
                 "frequency_ghz": 3.5, "num_antennas": 64,
                 "bandwidth_mhz": 100, "num_prbs": 273, "height_m": 25},
                {"id": 1, "position": [375, 375], "tx_power_dbm": 46,
                 "frequency_ghz": 3.5, "num_antennas": 64,
                 "bandwidth_mhz": 100, "num_prbs": 273, "height_m": 25},
            ],
            "users": [
                {"id": 0, "position": [100, 100], "traffic_demand_mbps": 10},
                {"id": 1, "position": [300, 300], "traffic_demand_mbps": 15},
                {"id": 2, "position": [400, 100], "traffic_demand_mbps": 5},
            ],
        },
        "simulation": {
            "num_timesteps": 10, "dt": 1.0, "random_seed": 42,
            "channel_update_interval": 5, "optimization_interval": 5,
        },
        "traffic": {"model": "poisson", "arrival_rate": 1.0, "session_rate_mbps": 5},
        "mobility": {"model": "pedestrian", "speed_mean": 1.2},
        "solver": {"classical_method": "greedy", "run_quantum": False},
    }


@pytest.fixture
def network_env(small_config):
    from telequm.simulator.network_env import NetworkEnvironment
    return NetworkEnvironment(small_config["network"])


# ─── NetworkEnvironment Tests ────────────────────────────────────

class TestNetworkEnvironment:
    def test_creation(self, network_env):
        assert len(network_env.base_stations) == 2
        assert len(network_env.users) == 3
        assert network_env.timestep == 0

    def test_channel_matrix_shape(self, network_env):
        assert network_env.channel_matrix.shape == (3, 2)
        assert np.all(network_env.channel_matrix >= 0)

    def test_sinr_matrix_shape(self, network_env):
        assert network_env.sinr_matrix.shape == (3, 2)

    def test_snapshot_immutability(self, network_env):
        snap = network_env.get_snapshot()
        snap["channel_matrix"][0, 0] = 999
        assert network_env.channel_matrix[0, 0] != 999

    def test_user_association(self, network_env):
        network_env.associate_users_max_sinr()
        for ue in network_env.users:
            assert ue.serving_bs is not None

    def test_metrics_collection(self, network_env):
        network_env.associate_users_max_sinr()
        m = network_env.collect_metrics()
        assert "avg_throughput_mbps" in m
        assert "fairness_jain" in m
        assert m["num_active_ues"] == 3

    def test_apply_allocation(self, network_env):
        alloc = np.eye(3, 2)
        network_env.apply_allocation(alloc)
        assert np.array_equal(network_env.allocation_matrix, alloc)

    def test_update_positions(self, network_env):
        new_pos = np.array([[200, 200], [300, 300], [400, 400]], dtype=float)
        network_env.update_user_positions(new_pos)
        assert np.allclose(network_env.users[0].position, [200, 200])

    def test_to_dict(self, network_env):
        d = network_env.to_dict()
        assert "base_stations" in d
        assert "users" in d
        assert d["timestep"] == 0


# ─── Traffic Model Tests ────────────────────────────────────────

class TestTrafficModels:
    def test_poisson(self):
        from telequm.simulator.traffic_models import PoissonTraffic
        rng = np.random.default_rng(42)
        model = PoissonTraffic(arrival_rate=2.0, session_rate_mbps=5.0)
        demands = model.generate(rng, 10, 0)
        assert demands.shape == (10,)
        assert np.all(demands >= 0)

    def test_video(self):
        from telequm.simulator.traffic_models import VideoStreamTraffic
        rng = np.random.default_rng(42)
        model = VideoStreamTraffic()
        demands = model.generate(rng, 10, 0)
        assert demands.shape == (10,)
        assert np.all(demands > 0)

    def test_iot_burst(self):
        from telequm.simulator.traffic_models import IoTBurstTraffic
        rng = np.random.default_rng(42)
        model = IoTBurstTraffic(period=5)
        d0 = model.generate(rng, 10, 0)  # active
        d1 = model.generate(rng, 10, 1)  # inactive
        assert np.all(d0 >= 0)
        assert np.all(d1 == 0)

    def test_mixed(self):
        from telequm.simulator.traffic_models import PoissonTraffic, VideoStreamTraffic, MixedTraffic
        rng = np.random.default_rng(42)
        mixed = MixedTraffic([
            (PoissonTraffic(), 0.5),
            (VideoStreamTraffic(), 0.5),
        ])
        demands = mixed.generate(rng, 10, 0)
        assert demands.shape == (10,)


# ─── Mobility Model Tests ───────────────────────────────────────

class TestMobilityModels:
    def test_pedestrian(self):
        from telequm.simulator.mobility_models import PedestrianMobility
        rng = np.random.default_rng(42)
        model = PedestrianMobility()
        pos = np.array([[100, 100], [200, 200]], dtype=float)
        vel = np.zeros((2, 2))
        new_pos, new_vel = model.update(rng, pos, vel, (500, 500), 0)
        assert new_pos.shape == (2, 2)
        assert not np.array_equal(new_pos, pos)

    def test_random_waypoint(self):
        from telequm.simulator.mobility_models import RandomWaypointMobility
        rng = np.random.default_rng(42)
        model = RandomWaypointMobility()
        pos = np.array([[100, 100]], dtype=float)
        vel = np.zeros((1, 2))
        new_pos, _ = model.update(rng, pos, vel, (500, 500), 0)
        assert new_pos.shape == (1, 2)
        assert np.all(new_pos >= 0) and np.all(new_pos <= 500)

    def test_vehicular(self):
        from telequm.simulator.mobility_models import VehicularMobility
        rng = np.random.default_rng(42)
        model = VehicularMobility()
        pos = np.array([[250, 250]], dtype=float)
        vel = np.zeros((1, 2))
        new_pos, new_vel = model.update(rng, pos, vel, (500, 500), 0)
        assert np.linalg.norm(new_vel) > 0  # should be moving


# ─── EventQueue Tests ───────────────────────────────────────────

class TestEventQueue:
    def test_ordering(self):
        from telequm.simulator.event_queue import EventQueue, Event, EventType
        eq = EventQueue()
        eq.schedule(Event(time=10, event_type=EventType.TRAFFIC_UPDATE))
        eq.schedule(Event(time=5, event_type=EventType.CHANNEL_UPDATE))
        eq.schedule(Event(time=7, event_type=EventType.MOBILITY_UPDATE))
        assert eq.pop().time == 5
        assert eq.pop().time == 7
        assert eq.pop().time == 10

    def test_recurring(self):
        from telequm.simulator.event_queue import EventQueue, EventType
        eq = EventQueue()
        eq.schedule_recurring(EventType.METRIC_COLLECTION, start=0, interval=5, end=20)
        assert len(eq) == 5  # t=0, 5, 10, 15, 20


# ─── Optimization Bridge Tests ──────────────────────────────────

class TestOptimizationBridge:
    def test_qubo_build(self, network_env):
        from telequm.simulator.optimization_bridge import ResourceAllocationQUBO
        problem = ResourceAllocationQUBO(penalty=10.0)
        snap = network_env.get_snapshot()
        Q, offset, meta = problem.build_qubo(snap)
        assert Q.shape == (6, 6)  # 3 UE × 2 BS
        assert meta["num_vars"] == 6

    def test_greedy_solver(self, network_env):
        from telequm.simulator.optimization_bridge import ResourceAllocationQUBO, ClassicalBaselines
        problem = ResourceAllocationQUBO()
        snap = network_env.get_snapshot()
        Q, offset, meta = problem.build_qubo(snap)
        x, cost, rt = ClassicalBaselines.greedy(Q, offset)
        assert len(x) == 6
        assert rt >= 0

    def test_sa_solver(self, network_env):
        from telequm.simulator.optimization_bridge import ResourceAllocationQUBO, ClassicalBaselines
        problem = ResourceAllocationQUBO()
        snap = network_env.get_snapshot()
        Q, offset, meta = problem.build_qubo(snap)
        x, cost, rt = ClassicalBaselines.simulated_annealing(Q, offset, num_reads=20)
        assert len(x) == 6

    def test_exact_solver(self, network_env):
        from telequm.simulator.optimization_bridge import ResourceAllocationQUBO, ClassicalBaselines
        problem = ResourceAllocationQUBO()
        snap = network_env.get_snapshot()
        Q, offset, meta = problem.build_qubo(snap)
        x, cost, rt = ClassicalBaselines.exact_brute_force(Q, offset)
        assert len(x) == 6

    def test_decode(self, network_env):
        from telequm.simulator.optimization_bridge import ResourceAllocationQUBO
        problem = ResourceAllocationQUBO()
        snap = network_env.get_snapshot()
        Q, offset, meta = problem.build_qubo(snap)
        x = np.array([1, 0, 0, 1, 1, 0])
        decoded = problem.decode_solution(x, meta)
        assert "allocation_matrix" in decoded
        assert decoded["allocation_matrix"].shape == (3, 2)

    def test_bridge_classical(self, network_env):
        from telequm.simulator.optimization_bridge import OptimizationBridge, ResourceAllocationQUBO
        bridge = OptimizationBridge(ResourceAllocationQUBO())
        snap = network_env.get_snapshot()
        result = bridge.solve_classical(snap, method="greedy")
        assert "cost" in result
        assert "decoded" in result
        assert "runtime_s" in result


# ─── SimulationEngine Tests ─────────────────────────────────────

class TestSimulationEngine:
    def test_run(self, small_config):
        from telequm.simulator.engine import SimulationEngine
        from telequm.simulator.optimization_bridge import OptimizationBridge, ResourceAllocationQUBO
        engine = SimulationEngine(small_config)
        bridge = OptimizationBridge(ResourceAllocationQUBO())
        engine.set_bridge(bridge)
        results = engine.run(verbose=False)
        assert len(results["metrics"]) == 10
        assert results["total_runtime_s"] > 0

    def test_reproducibility(self, small_config):
        from telequm.simulator.engine import SimulationEngine
        from telequm.simulator.optimization_bridge import OptimizationBridge, ResourceAllocationQUBO
        # Run twice with same seed
        engine1 = SimulationEngine(small_config)
        engine1.set_bridge(OptimizationBridge(ResourceAllocationQUBO()))
        r1 = engine1.run(verbose=False)

        engine2 = SimulationEngine(small_config)
        engine2.set_bridge(OptimizationBridge(ResourceAllocationQUBO()))
        r2 = engine2.run(verbose=False)

        # Metrics should be identical
        for m1, m2 in zip(r1["metrics"], r2["metrics"]):
            assert m1["avg_throughput_mbps"] == m2["avg_throughput_mbps"]


# ─── Benchmark Topology Tests ───────────────────────────────────

class TestBenchmarkTopologies:
    def test_hexagonal(self):
        from benchmarks.topologies import hexagonal_topology
        config = hexagonal_topology(num_rings=1, ues_per_cell=3)
        assert len(config["base_stations"]) >= 7
        assert len(config["users"]) >= 21

    def test_nsfnet(self):
        from benchmarks.topologies import nsfnet_topology
        config = nsfnet_topology()
        assert len(config["base_stations"]) == 14

    def test_mesh(self):
        from benchmarks.topologies import mesh_topology
        config = mesh_topology(rows=2, cols=2)
        assert len(config["base_stations"]) == 4
