"""
Mobility Models — User Movement Patterns
=========================================

Realistic mobility models for telecom simulation:
- **Random Waypoint**: Standard MANET model (pedestrian / indoor)
- **Vehicular**:       Highway / urban road grid movement
- **Pedestrian**:      Low-speed random walk with direction persistence

Each model implements ``update(rng, positions, velocities, area_size, timestep)``
returning new ``(positions, velocities)`` arrays.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class MobilityModel(ABC):
    """Abstract base for mobility models."""

    @abstractmethod
    def update(
        self,
        rng: np.random.Generator,
        positions: np.ndarray,
        velocities: np.ndarray,
        area_size: tuple[float, float],
        timestep: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute new positions and velocities.

        Parameters
        ----------
        rng : np.random.Generator
        positions : np.ndarray  shape (num_users, 2)
        velocities : np.ndarray shape (num_users, 2)
        area_size : (width, height) in metres
        timestep : int  current simulation step

        Returns
        -------
        (new_positions, new_velocities)  both shape (num_users, 2)
        """
        ...


class RandomWaypointMobility(MobilityModel):
    """
    Random Waypoint mobility (Camp et al., 2002).

    Users choose a random destination within the area,
    travel at a random speed, pause, then choose again.

    Parameters
    ----------
    v_min : float   minimum speed m/s (default 0.5)
    v_max : float   maximum speed m/s (default 2.0)
    pause_prob : float  probability of pausing at each step
    dt : float      timestep duration in seconds
    """

    def __init__(
        self,
        v_min: float = 0.5,
        v_max: float = 2.0,
        pause_prob: float = 0.1,
        dt: float = 1.0,
    ):
        self.v_min = v_min
        self.v_max = v_max
        self.pause_prob = pause_prob
        self.dt = dt
        self._destinations: np.ndarray | None = None

    def update(
        self,
        rng: np.random.Generator,
        positions: np.ndarray,
        velocities: np.ndarray,
        area_size: tuple[float, float],
        timestep: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        n = len(positions)

        # Initialise destinations on first call
        if self._destinations is None or len(self._destinations) != n:
            self._destinations = np.column_stack([
                rng.uniform(0, area_size[0], n),
                rng.uniform(0, area_size[1], n),
            ])

        new_pos = positions.copy()
        new_vel = velocities.copy()

        for i in range(n):
            # Check if user pauses
            if rng.random() < self.pause_prob:
                new_vel[i] = 0.0
                continue

            # Direction to destination
            diff = self._destinations[i] - positions[i]
            dist = np.linalg.norm(diff)

            if dist < 1.0:
                # Arrived — choose new destination
                self._destinations[i] = [
                    rng.uniform(0, area_size[0]),
                    rng.uniform(0, area_size[1]),
                ]
                diff = self._destinations[i] - positions[i]
                dist = np.linalg.norm(diff)

            speed = rng.uniform(self.v_min, self.v_max)
            direction = diff / max(dist, 1e-6)
            new_vel[i] = direction * speed
            new_pos[i] = positions[i] + new_vel[i] * self.dt

        # Clamp to area
        new_pos[:, 0] = np.clip(new_pos[:, 0], 0, area_size[0])
        new_pos[:, 1] = np.clip(new_pos[:, 1], 0, area_size[1])

        return new_pos, new_vel


class VehicularMobility(MobilityModel):
    """
    Vehicular mobility — high-speed movement along roads.

    Users move in straight lines at vehicular speed
    with occasional lane changes (direction perturbation).

    Parameters
    ----------
    v_min : float   min speed m/s (default 8.3 ≈ 30 km/h)
    v_max : float   max speed m/s (default 33.3 ≈ 120 km/h)
    lane_change_prob : float  probability of direction change
    dt : float      timestep duration in seconds
    """

    def __init__(
        self,
        v_min: float = 8.3,
        v_max: float = 33.3,
        lane_change_prob: float = 0.05,
        dt: float = 1.0,
    ):
        self.v_min = v_min
        self.v_max = v_max
        self.lane_change_prob = lane_change_prob
        self.dt = dt

    def update(
        self,
        rng: np.random.Generator,
        positions: np.ndarray,
        velocities: np.ndarray,
        area_size: tuple[float, float],
        timestep: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        n = len(positions)
        new_vel = velocities.copy()

        # Initialise velocities if zero
        zero_mask = np.linalg.norm(velocities, axis=1) < 0.1
        if np.any(zero_mask):
            angles = rng.uniform(0, 2 * np.pi, np.sum(zero_mask))
            speeds = rng.uniform(self.v_min, self.v_max, np.sum(zero_mask))
            new_vel[zero_mask, 0] = speeds * np.cos(angles)
            new_vel[zero_mask, 1] = speeds * np.sin(angles)

        # Lane changes
        change_mask = rng.random(n) < self.lane_change_prob
        if np.any(change_mask):
            perturbation = rng.normal(0, 0.3, np.sum(change_mask))
            angles = np.arctan2(new_vel[change_mask, 1], new_vel[change_mask, 0]) + perturbation
            speeds = np.linalg.norm(new_vel[change_mask], axis=1)
            new_vel[change_mask, 0] = speeds * np.cos(angles)
            new_vel[change_mask, 1] = speeds * np.sin(angles)

        new_pos = positions + new_vel * self.dt

        # Reflect at boundaries (bounce)
        for dim, limit in enumerate(area_size):
            under = new_pos[:, dim] < 0
            over = new_pos[:, dim] > limit
            new_pos[under, dim] = -new_pos[under, dim]
            new_vel[under, dim] = -new_vel[under, dim]
            new_pos[over, dim] = 2 * limit - new_pos[over, dim]
            new_vel[over, dim] = -new_vel[over, dim]

        return new_pos, new_vel


class PedestrianMobility(MobilityModel):
    """
    Pedestrian random walk with directional persistence.

    Parameters
    ----------
    speed_mean : float  mean speed m/s (default 1.2)
    speed_std : float   speed std  m/s (default 0.3)
    turn_std : float    angular std per step (radians)
    dt : float          timestep duration in seconds
    """

    def __init__(
        self,
        speed_mean: float = 1.2,
        speed_std: float = 0.3,
        turn_std: float = 0.3,
        dt: float = 1.0,
    ):
        self.speed_mean = speed_mean
        self.speed_std = speed_std
        self.turn_std = turn_std
        self.dt = dt
        self._angles: np.ndarray | None = None

    def update(
        self,
        rng: np.random.Generator,
        positions: np.ndarray,
        velocities: np.ndarray,
        area_size: tuple[float, float],
        timestep: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        n = len(positions)

        if self._angles is None or len(self._angles) != n:
            self._angles = rng.uniform(0, 2 * np.pi, n)

        # Perturb direction
        self._angles += rng.normal(0, self.turn_std, n)
        speeds = np.clip(rng.normal(self.speed_mean, self.speed_std, n), 0, 3.0)

        new_vel = np.column_stack([
            speeds * np.cos(self._angles),
            speeds * np.sin(self._angles),
        ])

        new_pos = positions + new_vel * self.dt

        # Clamp
        new_pos[:, 0] = np.clip(new_pos[:, 0], 0, area_size[0])
        new_pos[:, 1] = np.clip(new_pos[:, 1], 0, area_size[1])

        return new_pos, new_vel
