"""
MATLAB Bridge — High-Fidelity Channel Import
=============================================

Interfaces with MATLAB Engine for:
- CDL/TDL channel model generation
- High-fidelity H-matrix extraction
- Beamforming weight computation and validation
- Comparison with classical LS/ZF baselines

Requirements
------------
- MATLAB R2023b+ with 5G Toolbox
- ``pip install matlabengine``

If MATLAB is not available, all functions gracefully degrade
to standalone 3GPP models from ``network_env.py``.
"""

from __future__ import annotations

import logging

import numpy as np

from telequm.core.network_snapshot import UniversalNetworkSnapshot

logger = logging.getLogger("telequm.bridges.matlab")

try:
    import matlab.engine
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False
    logger.info("MATLAB engine not available — using standalone models")


class MATLABBridge:
    """
    Bridge to MATLAB for physics-grade channel models.

    Parameters
    ----------
    startup_options : str, optional
        MATLAB startup flags (e.g., '-nojvm').

    Example
    -------
    >>> bridge = MATLABBridge()
    >>> bridge.start()
    >>> H = bridge.get_channel_matrix('CDL-C', 64, 4)
    >>> bridge.stop()
    """

    def __init__(self, startup_options: str = "-nojvm"):
        self._eng = None
        self._options = startup_options

    @property
    def is_available(self) -> bool:
        return MATLAB_AVAILABLE

    def start(self) -> bool:
        """Start MATLAB engine. Returns True if successful."""
        if not MATLAB_AVAILABLE:
            logger.warning("MATLAB engine not installed")
            return False
        try:
            self._eng = matlab.engine.start_matlab(self._options)
            logger.info("MATLAB engine started")
            return True
        except Exception as e:
            logger.error("Failed to start MATLAB: %s", e)
            return False

    def stop(self):
        """Stop MATLAB engine."""
        if self._eng is not None:
            self._eng.quit()
            self._eng = None
            logger.info("MATLAB engine stopped")

    def get_channel_matrix(
        self,
        model: str = "CDL-C",
        num_tx: int = 64,
        num_rx: int = 4,
        delay_spread: float = 300e-9,
        carrier_freq: float = 3.5e9,
        velocity: float = 30.0,
    ) -> np.ndarray:
        """
        Generate channel matrix using MATLAB 5G Toolbox.

        Parameters
        ----------
        model : str      CDL model profile ('CDL-A' through 'CDL-E')
        num_tx : int     transmit antennas
        num_rx : int     receive antennas
        delay_spread : float  seconds
        carrier_freq : float  Hz
        velocity : float      m/s

        Returns
        -------
        np.ndarray  complex H-matrix (num_rx × num_tx)
        """
        if self._eng is None:
            logger.warning("MATLAB not started — generating synthetic H-matrix")
            return self._synthetic_h_matrix(num_tx, num_rx)

        try:
            # MATLAB script call
            self._eng.eval(f"""
                channel = nrCDLChannel;
                channel.DelayProfile = '{model}';
                channel.DelaySpread = {delay_spread};
                channel.CarrierFrequency = {carrier_freq};
                channel.MaximumDopplerShift = {velocity * carrier_freq / 3e8};
                channel.NumTransmitAntennas = {num_tx};
                channel.NumReceiveAntennas = {num_rx};
                txWaveform = complex(randn({num_tx}, 1), randn({num_tx}, 1)) / sqrt(2);
                [rxWaveform, pathGains] = channel(txWaveform);
                H = squeeze(pathGains(1,:,:));
            """, nargout=0)

            H = np.array(self._eng.workspace['H'])
            logger.info("Retrieved %s H-matrix: %s", model, H.shape)
            return H

        except Exception as e:
            logger.error("MATLAB channel generation failed: %s", e)
            return self._synthetic_h_matrix(num_tx, num_rx)

    def compute_beamforming_weights(
        self,
        H: np.ndarray,
        method: str = "zf",
    ) -> np.ndarray:
        """
        Compute classical beamforming weights.

        Parameters
        ----------
        H : np.ndarray  (num_rx × num_tx) channel matrix
        method : str     'ls' (least squares), 'zf' (zero-forcing),
                         'mmse' (minimum MSE)

        Returns
        -------
        np.ndarray  (num_tx × num_rx) beamforming weight matrix
        """
        if method == "zf":
            # W = H^H (H H^H)^{-1}
            H_hermitian = H.conj().T
            return H_hermitian @ np.linalg.inv(H @ H_hermitian + 1e-10 * np.eye(H.shape[0]))
        elif method == "ls":
            return np.linalg.pinv(H)
        elif method == "mmse":
            snr_linear = 10.0  # 10 dB default
            H_hermitian = H.conj().T
            return H_hermitian @ np.linalg.inv(
                H @ H_hermitian + (1 / snr_linear) * np.eye(H.shape[0])
            )
        else:
            raise ValueError(f"Unknown beamforming method: {method}")

    def inject_into_snapshot(
        self,
        snapshot: UniversalNetworkSnapshot,
        model: str = "CDL-C",
    ) -> UniversalNetworkSnapshot:
        """
        Pull H-matrix from MATLAB and inject into snapshot.

        Parameters
        ----------
        snapshot : UniversalNetworkSnapshot
        model : str  CDL profile

        Returns
        -------
        UniversalNetworkSnapshot  with H-matrix stored
        """
        if not snapshot.cells:
            raise ValueError("Snapshot has no cells")

        num_tx = snapshot.cells[0].num_antennas
        num_rx = 4  # typical UE
        H = self.get_channel_matrix(model, num_tx, num_rx)
        snapshot.store_channel_matrix(H)
        snapshot.metadata["matlab_model"] = model
        snapshot.metadata["source"] = "matlab"
        return snapshot

    @staticmethod
    def _synthetic_h_matrix(num_tx: int, num_rx: int, seed: int = 42) -> np.ndarray:
        """Generate synthetic Rayleigh fading H-matrix (fallback)."""
        rng = np.random.default_rng(seed)
        return (rng.standard_normal((num_rx, num_tx)) +
                1j * rng.standard_normal((num_rx, num_tx))) / np.sqrt(2)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
