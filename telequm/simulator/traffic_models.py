"""
Traffic Models — Stochastic Traffic Generation
===============================================

Implements realistic traffic models for telecom simulation:
- **Poisson**:        Classic voice/data arrival model
- **Video Streaming**: Bursty high-bandwidth sessions
- **IoT Burst**:      Periodic sensor-like traffic

Each model implements ``generate(rng, num_users, timestep)``
returning an ``np.ndarray`` of per-user demands (Mbps).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class TrafficModel(ABC):
    """Abstract base for all traffic generators."""

    @abstractmethod
    def generate(
        self,
        rng: np.random.Generator,
        num_users: int,
        timestep: int,
    ) -> np.ndarray:
        """
        Generate per-user traffic demand.

        Parameters
        ----------
        rng : np.random.Generator
        num_users : int
        timestep : int

        Returns
        -------
        np.ndarray  shape (num_users,), units Mbps
        """
        ...


class PoissonTraffic(TrafficModel):
    """
    Poisson arrival traffic model.

    Each user independently has a Poisson-distributed number
    of active sessions, each consuming ``session_rate_mbps``.

    Parameters
    ----------
    arrival_rate : float
        Mean arrivals per timestep per user (λ).
    session_rate_mbps : float
        Data rate per active session.
    """

    def __init__(self, arrival_rate: float = 1.0, session_rate_mbps: float = 5.0):
        self.arrival_rate = arrival_rate
        self.session_rate_mbps = session_rate_mbps

    def generate(self, rng: np.random.Generator, num_users: int, timestep: int) -> np.ndarray:
        sessions = rng.poisson(self.arrival_rate, size=num_users)
        return sessions.astype(float) * self.session_rate_mbps


class VideoStreamTraffic(TrafficModel):
    """
    Video streaming traffic — ON/OFF bursty model.

    Users alternate between high-rate ON periods and
    zero-rate OFF periods, modelling adaptive bitrate streaming.

    Parameters
    ----------
    on_rate_mbps : float
        Rate during ON period (e.g., 4K = 25 Mbps).
    on_prob : float
        Probability of being in ON state.
    off_rate_mbps : float
        Residual rate in OFF state (buffering ACKs, etc.).
    """

    def __init__(
        self,
        on_rate_mbps: float = 25.0,
        on_prob: float = 0.6,
        off_rate_mbps: float = 0.5,
    ):
        self.on_rate_mbps = on_rate_mbps
        self.on_prob = on_prob
        self.off_rate_mbps = off_rate_mbps

    def generate(self, rng: np.random.Generator, num_users: int, timestep: int) -> np.ndarray:
        on_mask = rng.random(num_users) < self.on_prob
        demands = np.where(on_mask, self.on_rate_mbps, self.off_rate_mbps)
        # Add jitter ±10 %
        jitter = rng.uniform(0.9, 1.1, size=num_users)
        return demands * jitter


class IoTBurstTraffic(TrafficModel):
    """
    IoT burst traffic — periodic low-rate transmissions
    with occasional bursts (alarm, firmware update).

    Parameters
    ----------
    base_rate_mbps : float
        Sensor heartbeat rate.
    burst_rate_mbps : float
        Burst peak rate.
    burst_prob : float
        Per-user probability of burst in a timestep.
    period : int
        Transmission period (active every *period* timesteps).
    """

    def __init__(
        self,
        base_rate_mbps: float = 0.01,
        burst_rate_mbps: float = 2.0,
        burst_prob: float = 0.05,
        period: int = 10,
    ):
        self.base_rate_mbps = base_rate_mbps
        self.burst_rate_mbps = burst_rate_mbps
        self.burst_prob = burst_prob
        self.period = period

    def generate(self, rng: np.random.Generator, num_users: int, timestep: int) -> np.ndarray:
        # Only transmit on period boundaries (else zero)
        active = (timestep % self.period == 0)
        if not active:
            return np.zeros(num_users)

        burst_mask = rng.random(num_users) < self.burst_prob
        return np.where(burst_mask, self.burst_rate_mbps, self.base_rate_mbps)


class MixedTraffic(TrafficModel):
    """
    Mix multiple traffic models with per-user type assignment.

    Parameters
    ----------
    models : list of (TrafficModel, float)
        Each tuple is (model, fraction_of_users).
        Fractions should sum to 1.0.
    """

    def __init__(self, models: list):
        self.models = models  # [(model, fraction), ...]

    def generate(self, rng: np.random.Generator, num_users: int, timestep: int) -> np.ndarray:
        demands = np.zeros(num_users)
        idx = 0
        for model, frac in self.models:
            count = int(np.round(frac * num_users))
            end = min(idx + count, num_users)
            demands[idx:end] = model.generate(rng, end - idx, timestep)
            idx = end
        # Handle rounding remainder
        if idx < num_users:
            m, _ = self.models[-1]
            demands[idx:] = m.generate(rng, num_users - idx, timestep)
        return demands
