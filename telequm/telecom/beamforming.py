"""
Beamforming Optimization for 6G Networks
=========================================

Quantum-enhanced beamforming for MIMO systems with
intelligent weight computation and optimization.
"""

import numpy as np

from telequm.algorithms.qml import QuantumBeamformer


class BeamformingOptimizer:
    """
    Optimizer for MIMO beamforming in 6G networks.

    Combines quantum and classical methods for computing
    optimal beamforming weights in dynamic environments.

    Parameters
    ----------
    num_antennas : int
        Number of antenna elements
    num_users : int
        Number of users to serve
    method : str
        'quantum' or 'classical'
    """

    def __init__(
        self,
        num_antennas: int,
        num_users: int,
        method: str = "quantum"
    ):
        self.num_antennas = num_antennas
        self.num_users = num_users
        self.method = method

        if method == "quantum":
            self.qbeamformer = QuantumBeamformer(num_antennas, num_users)
        else:
            self.qbeamformer = None

    def compute_weights(
        self,
        channel_matrix: np.ndarray,
        noise_power: float = 0.01
    ) -> np.ndarray:
        """
        Compute beamforming weights for given channel state.

        Parameters
        ----------
        channel_matrix : np.ndarray
            Channel matrix (num_users x num_antennas)
        noise_power : float
            Noise power level

        Returns
        -------
        np.ndarray
            Beamforming weight matrix (num_antennas x num_users)
        """
        if self.method == "quantum":
            return self._quantum_weights(channel_matrix, noise_power)
        else:
            return self._classical_weights(channel_matrix, noise_power)

    def _quantum_weights(
        self,
        channel_matrix: np.ndarray,
        noise_power: float
    ) -> np.ndarray:
        """Compute weights using quantum circuit."""
        weights = np.zeros((self.num_antennas, self.num_users), dtype=complex)

        for user in range(self.num_users):
            user_channel = channel_matrix[user:user+1, :]
            w = self.qbeamformer.compute_weights(user_channel)
            weights[:len(w), user] = w

        return weights

    def _classical_weights(
        self,
        channel_matrix: np.ndarray,
        noise_power: float
    ) -> np.ndarray:
        """Compute weights using MMSE (classical)."""
        H = channel_matrix.T  # (num_antennas x num_users)

        # MMSE precoding
        HH = H @ H.conj().T
        regularizer = noise_power * np.eye(self.num_antennas)

        try:
            W = np.linalg.inv(HH + regularizer) @ H
        except np.linalg.LinAlgError:
            W = np.linalg.pinv(HH + regularizer) @ H

        # Normalize columns
        for i in range(W.shape[1]):
            W[:, i] /= np.linalg.norm(W[:, i]) + 1e-8

        return W

    def compute_sinr(
        self,
        weights: np.ndarray,
        channel_matrix: np.ndarray,
        noise_power: float = 0.01
    ) -> np.ndarray:
        """
        Compute Signal-to-Interference-plus-Noise Ratio.

        Parameters
        ----------
        weights : np.ndarray
            Beamforming weights
        channel_matrix : np.ndarray
            Channel matrix
        noise_power : float
            Noise power

        Returns
        -------
        np.ndarray
            SINR per user
        """
        sinr = np.zeros(self.num_users)

        for k in range(self.num_users):
            h_k = channel_matrix[k, :]
            w_k = weights[:, k]

            # Signal power
            signal = np.abs(h_k @ w_k) ** 2

            # Interference from other users
            interference = 0
            for j in range(self.num_users):
                if j != k:
                    w_j = weights[:, j]
                    interference += np.abs(h_k @ w_j) ** 2

            sinr[k] = signal / (interference + noise_power)

        return sinr

    def compute_capacity(
        self,
        sinr: np.ndarray
    ) -> float:
        """
        Compute sum capacity from SINR values.

        Parameters
        ----------
        sinr : np.ndarray
            SINR per user

        Returns
        -------
        float
            Sum capacity (bits/Hz)
        """
        return float(np.sum(np.log2(1 + sinr)))


def compute_beam_weights(
    channel_matrix: np.ndarray,
    method: str = "mmse",
    noise_power: float = 0.01
) -> np.ndarray:
    """
    Compute beamforming weights.

    Parameters
    ----------
    channel_matrix : np.ndarray
        Channel matrix
    method : str
        'mmse', 'zf' (zero-forcing), or 'mrt' (maximum ratio)
    noise_power : float
        Noise power

    Returns
    -------
    np.ndarray
        Beamforming weights
    """
    H = channel_matrix.T
    num_antennas, num_users = H.shape

    if method == "mmse":
        HH = H @ H.conj().T
        reg = noise_power * np.eye(num_antennas)
        W = np.linalg.inv(HH + reg) @ H

    elif method == "zf":
        # Zero-forcing: H^H (H H^H)^-1
        HH = H @ H.conj().T
        W = np.linalg.inv(HH) @ H

    elif method == "mrt":
        # Maximum ratio transmission: conjugate of channel
        W = H.conj()

    else:
        raise ValueError(f"Unknown method: {method}")

    # Normalize
    for i in range(W.shape[1]):
        W[:, i] /= np.linalg.norm(W[:, i]) + 1e-8

    return W


def optimize_mimo_configuration(
    num_antennas_options: list[int],
    num_users: int,
    channel_samples: list[np.ndarray],
    target_capacity: float
) -> dict:
    """
    Find optimal MIMO configuration.

    Parameters
    ----------
    num_antennas_options : list of int
        Antenna count options to evaluate
    num_users : int
        Number of users
    channel_samples : list of np.ndarray
        Sample channel matrices for evaluation
    target_capacity : float
        Target sum capacity

    Returns
    -------
    Dict
        Optimal configuration and metrics
    """
    results = []

    for num_antennas in num_antennas_options:
        optimizer = BeamformingOptimizer(num_antennas, num_users, method="classical")

        capacities = []
        for channel in channel_samples:
            # Resize channel if needed
            if channel.shape != (num_users, num_antennas):
                channel_resized = np.zeros((num_users, num_antennas), dtype=complex)
                min_u = min(channel.shape[0], num_users)
                min_a = min(channel.shape[1], num_antennas)
                channel_resized[:min_u, :min_a] = channel[:min_u, :min_a]
                channel = channel_resized

            weights = optimizer.compute_weights(channel)
            sinr = optimizer.compute_sinr(weights, channel)
            capacity = optimizer.compute_capacity(sinr)
            capacities.append(capacity)

        avg_capacity = np.mean(capacities)
        results.append({
            "num_antennas": num_antennas,
            "avg_capacity": avg_capacity,
            "meets_target": avg_capacity >= target_capacity
        })

    # Find optimal
    valid = [r for r in results if r["meets_target"]]
    if valid:
        optimal = min(valid, key=lambda x: x["num_antennas"])
    else:
        optimal = max(results, key=lambda x: x["avg_capacity"])

    return {
        "optimal_antennas": optimal["num_antennas"],
        "optimal_capacity": optimal["avg_capacity"],
        "all_results": results
    }
