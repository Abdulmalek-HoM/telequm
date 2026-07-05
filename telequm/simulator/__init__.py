"""
TELEQUM Simulator Module
========================

Discrete time-step simulation engine for quantum-telecom optimization.
Provides 3GPP-compliant network models, stochastic traffic, mobility,
and an optimization bridge connecting network state to solvers.
"""

from telequm.simulator.engine import SimulationEngine
from telequm.simulator.event_queue import EventQueue
from telequm.simulator.mobility_models import (
    PedestrianMobility,
    RandomWaypointMobility,
    VehicularMobility,
)
from telequm.simulator.network_env import NetworkEnvironment
from telequm.simulator.optimization_bridge import OptimizationBridge
from telequm.simulator.traffic_models import IoTBurstTraffic, PoissonTraffic, VideoStreamTraffic

__all__ = [
    "NetworkEnvironment",
    "SimulationEngine",
    "PoissonTraffic", "VideoStreamTraffic", "IoTBurstTraffic",
    "RandomWaypointMobility", "VehicularMobility", "PedestrianMobility",
    "EventQueue",
    "OptimizationBridge",
]
