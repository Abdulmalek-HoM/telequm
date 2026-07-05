"""
SimulationEngine — Discrete Time-Step Orchestrator
===================================================

Central engine that orchestrates the simulation loop:
1. Update traffic demands
2. Update user mobility
3. Recompute channels / SINR
4. Run optimization (classical & quantum via bridge)
5. Apply allocation decisions
6. Collect metrics

Implements Rule #6 (time-driven simulation) and Rule #10
(reproducibility via random seeds and config).
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np

from telequm.simulator.event_queue import EventQueue
from telequm.simulator.mobility_models import MobilityModel, PedestrianMobility
from telequm.simulator.network_env import NetworkEnvironment
from telequm.simulator.optimization_bridge import OptimizationBridge
from telequm.simulator.traffic_models import PoissonTraffic, TrafficModel

logger = logging.getLogger("telequm.simulator.engine")


class SimulationEngine:
    """
    Orchestrates a discrete-time telecom network simulation.

    Parameters
    ----------
    config : dict
        Full experiment configuration including:
        - ``network``    : passed to ``NetworkEnvironment``
        - ``simulation`` : timesteps, dt, random_seed
        - ``traffic``    : traffic model config
        - ``mobility``   : mobility model config
        - ``solver``     : optimization bridge config

    Example
    -------
    >>> from telequm.simulator import SimulationEngine
    >>> engine = SimulationEngine(config)
    >>> results = engine.run()
    """

    def __init__(self, config: dict):
        self.config = config
        self.seed = config.get("simulation", {}).get("random_seed", 42)
        self._rng = np.random.default_rng(self.seed)

        # ── Timestep parameters ──────────────────────────────────
        sim_cfg = config.get("simulation", {})
        self.num_timesteps: int = sim_cfg.get("num_timesteps", 100)
        self.dt: float = sim_cfg.get("dt", 1.0)  # seconds per step
        self.channel_update_interval: int = sim_cfg.get("channel_update_interval", 5)
        self.optimization_interval: int = sim_cfg.get("optimization_interval", 10)

        # ── Network environment ──────────────────────────────────
        net_cfg = config.get("network", {})
        net_cfg["random_seed"] = self.seed
        self.env = NetworkEnvironment(net_cfg)

        # ── Traffic model ────────────────────────────────────────
        self.traffic_model: TrafficModel = self._build_traffic_model(
            config.get("traffic", {})
        )

        # ── Mobility model ───────────────────────────────────────
        self.mobility_model: MobilityModel = self._build_mobility_model(
            config.get("mobility", {})
        )

        # ── Optimization bridge (optional) ───────────────────────
        self.bridge: OptimizationBridge | None = None
        self.solver_config: dict = config.get("solver", {})

        # ── Event queue ──────────────────────────────────────────
        self.event_queue = EventQueue()

        # ── Results ──────────────────────────────────────────────
        self.results: dict[str, list] = {
            "metrics": [],
            "classical_solutions": [],
            "quantum_solutions": [],
        }

    # ── Model factories ──────────────────────────────────────────

    def _build_traffic_model(self, cfg: dict) -> TrafficModel:
        name = cfg.get("model", "poisson")
        if name == "poisson":
            return PoissonTraffic(
                arrival_rate=cfg.get("arrival_rate", 1.0),
                session_rate_mbps=cfg.get("session_rate_mbps", 5.0),
            )
        from telequm.simulator.traffic_models import IoTBurstTraffic, VideoStreamTraffic
        if name == "video":
            return VideoStreamTraffic(
                on_rate_mbps=cfg.get("on_rate_mbps", 25.0),
                on_prob=cfg.get("on_prob", 0.6),
            )
        if name == "iot":
            return IoTBurstTraffic(
                base_rate_mbps=cfg.get("base_rate_mbps", 0.01),
                burst_rate_mbps=cfg.get("burst_rate_mbps", 2.0),
                burst_prob=cfg.get("burst_prob", 0.05),
                period=cfg.get("period", 10),
            )
        return PoissonTraffic()

    def _build_mobility_model(self, cfg: dict) -> MobilityModel:
        name = cfg.get("model", "pedestrian")
        if name == "pedestrian":
            return PedestrianMobility(
                speed_mean=cfg.get("speed_mean", 1.2),
                dt=self.dt,
            )
        from telequm.simulator.mobility_models import RandomWaypointMobility, VehicularMobility
        if name == "random_waypoint":
            return RandomWaypointMobility(
                v_min=cfg.get("v_min", 0.5),
                v_max=cfg.get("v_max", 2.0),
                dt=self.dt,
            )
        if name == "vehicular":
            return VehicularMobility(
                v_min=cfg.get("v_min", 8.3),
                v_max=cfg.get("v_max", 33.3),
                dt=self.dt,
            )
        return PedestrianMobility(dt=self.dt)

    # ── Attach optimization bridge ────────────────────────────────

    def set_bridge(self, bridge: OptimizationBridge) -> None:
        """Attach an optimization bridge for solver integration."""
        self.bridge = bridge

    # ── Main simulation loop ──────────────────────────────────────

    def run(self, verbose: bool = True) -> dict:
        """
        Execute the full simulation.

        Returns
        -------
        dict
            Complete experiment results including metrics,
            solver outputs, config, and runtime.
        """
        t_start = time.time()
        logger.info("Starting simulation: %d timesteps, seed=%d", self.num_timesteps, self.seed)

        for t in range(self.num_timesteps):
            self.env.timestep = t
            self._step(t, verbose)

        total_time = time.time() - t_start
        logger.info("Simulation complete in %.2f s", total_time)

        return {
            "config": self.config,
            "metrics": self.results["metrics"],
            "classical_solutions": self.results["classical_solutions"],
            "quantum_solutions": self.results["quantum_solutions"],
            "total_runtime_s": total_time,
            "environment_final": self.env.to_dict(),
        }

    def _step(self, t: int, verbose: bool) -> None:
        """Execute a single timestep."""
        n_ue = len(self.env.users)

        # 1. Traffic update
        demands = self.traffic_model.generate(self._rng, n_ue, t)
        self.env.update_user_demands(demands)

        # 2. Mobility update
        positions = np.array([ue.position for ue in self.env.users])
        velocities = np.array([ue.velocity for ue in self.env.users])
        new_pos, new_vel = self.mobility_model.update(
            self._rng, positions, velocities, self.env.area_size, t
        )
        self.env.update_user_positions(new_pos)
        for i, ue in enumerate(self.env.users):
            ue.velocity = new_vel[i]

        # 3. Channel update (periodic — computationally expensive)
        if t % self.channel_update_interval == 0:
            self.env.update_channels()

        # 4. User association
        self.env.associate_users_max_sinr()

        # 5. Optimization (periodic)
        if self.bridge is not None and t % self.optimization_interval == 0:
            snapshot = self.env.get_snapshot()

            # Classical baseline
            try:
                classical = self.bridge.solve_classical(
                    snapshot,
                    method=self.solver_config.get("classical_method", "greedy"),
                )
                classical["timestep"] = t
                self.results["classical_solutions"].append(classical)

                # Apply classical allocation
                if "allocation_matrix" in classical["decoded"]:
                    self.env.apply_allocation(classical["decoded"]["allocation_matrix"])
            except Exception as e:
                logger.warning("Classical solver failed at t=%d: %s", t, e)

            # Quantum solver (only if configured and problem small enough)
            if self.solver_config.get("run_quantum", False):
                try:
                    num_vars = snapshot["num_ue"] * snapshot["num_bs"]
                    max_quantum = self.solver_config.get("max_quantum_vars", 16)
                    if num_vars <= max_quantum:
                        quantum = self.bridge.solve_quantum(
                            snapshot,
                            algorithm=self.solver_config.get("quantum_algorithm", "qaoa"),
                            shots=self.solver_config.get("shots", 1024),
                            p=self.solver_config.get("p", 2),
                        )
                        quantum["timestep"] = t
                        self.results["quantum_solutions"].append(quantum)
                    else:
                        logger.info(
                            "Skipping quantum at t=%d: %d vars > max %d",
                            t, num_vars, max_quantum,
                        )
                except Exception as e:
                    logger.warning("Quantum solver failed at t=%d: %s", t, e)

        # 6. Collect metrics
        metrics = self.env.collect_metrics()
        self.results["metrics"].append(metrics)

        if verbose and t % max(self.num_timesteps // 10, 1) == 0:
            logger.info(
                "t=%d | throughput=%.1f Mbps | SINR=%.1f dB | fairness=%.3f",
                t,
                metrics["avg_throughput_mbps"],
                metrics["avg_sinr_db"],
                metrics["fairness_jain"],
            )

    # ── Export ────────────────────────────────────────────────────

    def save_results(self, path: str) -> None:
        """Save simulation results to JSON."""
        results = {
            "config": self.config,
            "metrics": self.results["metrics"],
            "classical_solutions": [
                {k: v.tolist() if isinstance(v, np.ndarray) else v
                 for k, v in sol.items()}
                for sol in self.results["classical_solutions"]
            ],
            "quantum_solutions": [
                {k: v.tolist() if isinstance(v, np.ndarray) else v
                 for k, v in sol.items()}
                for sol in self.results["quantum_solutions"]
            ],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("Results saved to %s", path)
