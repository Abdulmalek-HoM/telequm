"""
TELEQUM Simulator Module
========================

Discrete time-step simulation engine for quantum-telecom optimization.
Provides 3GPP-compliant network models, stochastic traffic, mobility,
and an optimization bridge connecting network state to solvers.
"""

from telequm.simulator.network_env import NetworkEnvironment
from telequm.simulator.engine import SimulationEngine
from telequm.simulator.traffic_models import PoissonTraffic, VideoStreamTraffic, IoTBurstTraffic
from telequm.simulator.mobility_models import RandomWaypointMobility, VehicularMobility, PedestrianMobility
from telequm.simulator.event_queue import EventQueue
from telequm.simulator.optimization_bridge import OptimizationBridge

__all__ = [
    "NetworkEnvironment",
    "SimulationEngine",
    "PoissonTraffic", "VideoStreamTraffic", "IoTBurstTraffic",
    "RandomWaypointMobility", "VehicularMobility", "PedestrianMobility",
    "EventQueue",
    "OptimizationBridge",
]
