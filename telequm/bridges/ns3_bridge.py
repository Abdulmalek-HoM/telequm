"""
ns-3 Bridge — Network Simulator Trace Ingestion
================================================

Socket-based telemetry bridge for real-time ns-3 integration.
Ingests traces from:
- RadioBearerStatsCalculator
- PDCP E2E traces
- RLC E2E traces
- DL MAC Scheduler traces

Converts all input into ``UniversalNetworkSnapshot`` for
source-agnostic consumption by TELEQUM problems and solvers.

Requirements
------------
- ns-3 with 5G-LENA or mmWave module
- Traces exported via socket or CSV

If ns-3 is not available, synthetic trace generation
is provided for development and testing.
"""

from __future__ import annotations

import csv
import json
import logging
import socket

import numpy as np

from telequm.core.network_snapshot import CellInfo, UniversalNetworkSnapshot, UserInfo

logger = logging.getLogger("telequm.bridges.ns3")


class NS3Bridge:
    """
    Bridge to ns-3 network simulator via socket or file traces.

    Parameters
    ----------
    host : str
        Hostname for socket connection (default 'localhost').
    port : int
        Port number (default 5555).
    """

    def __init__(self, host: str = "localhost", port: int = 5555):
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None

    # ── Socket Mode ──────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect to ns-3 telemetry socket."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self.host, self.port))
            logger.info("Connected to ns-3 at %s:%d", self.host, self.port)
            return True
        except Exception as e:
            logger.warning("ns-3 connection failed: %s", e)
            self._socket = None
            return False

    def disconnect(self):
        """Close socket connection."""
        if self._socket:
            self._socket.close()
            self._socket = None

    def ingest_trace(self, buffer_size: int = 65536) -> dict | None:
        """
        Receive a single trace snapshot from ns-3 via socket.

        Returns
        -------
        dict or None  raw trace data (JSON parsed)
        """
        if self._socket is None:
            logger.error("Not connected to ns-3")
            return None
        try:
            data = self._socket.recv(buffer_size)
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error("Trace ingestion failed: %s", e)
            return None

    def ingest_to_snapshot(self) -> UniversalNetworkSnapshot | None:
        """
        Receive trace and convert to UniversalNetworkSnapshot.

        Returns
        -------
        UniversalNetworkSnapshot or None
        """
        raw = self.ingest_trace()
        if raw is None:
            return None
        return self.trace_to_snapshot(raw)

    # ── File Mode ────────────────────────────────────────────────

    @staticmethod
    def load_pdcp_trace(path: str) -> list[dict]:
        """
        Load PDCP E2E trace CSV from ns-3.

        Expected columns: time, imsi, rnti, lcid, size, delay
        """
        records = []
        with open(path) as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                records.append({
                    "time_s": float(row.get("time", 0)),
                    "imsi": int(row.get("IMSI", row.get("imsi", 0))),
                    "rnti": int(row.get("RNTI", row.get("rnti", 0))),
                    "size_bytes": int(row.get("size", row.get("TxBytes", 0))),
                    "delay_s": float(row.get("delay", row.get("Delay", 0))),
                })
        return records

    @staticmethod
    def load_mac_sched_trace(path: str) -> list[dict]:
        """
        Load DL MAC Scheduler trace from ns-3.

        Expected columns: time, cellId, rnti, mcsTb1, sizeTb1, nrb
        """
        records = []
        with open(path) as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                records.append({
                    "time_s": float(row.get("time", 0)),
                    "cell_id": int(row.get("cellId", row.get("CellId", 0))),
                    "rnti": int(row.get("RNTI", row.get("rnti", 0))),
                    "mcs": int(row.get("mcsTb1", row.get("MCS", 0))),
                    "tb_size": int(row.get("sizeTb1", row.get("TbSize", 0))),
                    "num_prbs": int(row.get("nRB", row.get("nrb", 0))),
                })
        return records

    # ── Conversion ───────────────────────────────────────────────

    @staticmethod
    def trace_to_snapshot(
        trace: dict,
        area_size: tuple = (1000.0, 1000.0),
    ) -> UniversalNetworkSnapshot:
        """
        Convert raw ns-3 trace to UniversalNetworkSnapshot.

        Parameters
        ----------
        trace : dict
            Must contain 'cells' and 'users' lists.

        Returns
        -------
        UniversalNetworkSnapshot
        """
        snap = UniversalNetworkSnapshot(source="ns3", metadata=trace.get("metadata", {}))
        snap.area_size = tuple(trace.get("area_size", area_size))

        for c in trace.get("cells", []):
            snap.cells.append(CellInfo(
                cell_id=c.get("cell_id", c.get("cellId", 0)),
                position=np.array(c.get("position", [0, 0])),
                tx_power_dbm=c.get("tx_power_dbm", 46.0),
                num_prbs=c.get("num_prbs", 273),
            ))

        for u in trace.get("users", []):
            snap.users.append(UserInfo(
                user_id=u.get("user_id", u.get("imsi", 0)),
                position=np.array(u.get("position", [0, 0])),
                serving_cell=u.get("serving_cell", u.get("cellId")),
                traffic_demand_mbps=u.get("demand_mbps", 10.0),
                achieved_throughput_mbps=u.get("throughput_mbps", 0.0),
                latency_ms=u.get("latency_ms", 0.0),
            ))

        # If SINR data present
        if "sinr_matrix" in trace:
            snap._sinr_matrix = np.array(trace["sinr_matrix"])
        if "channel_matrix" in trace:
            snap._channel_matrix = np.array(trace["channel_matrix"])

        return snap

    @staticmethod
    def traces_to_snapshot(
        pdcp_records: list[dict],
        mac_records: list[dict],
        area_size: tuple = (1000.0, 1000.0),
    ) -> UniversalNetworkSnapshot:
        """
        Convert PDCP + MAC file traces to snapshot.

        Aggregates per-user throughput and per-cell load.
        """
        snap = UniversalNetworkSnapshot(source="ns3")
        snap.area_size = area_size
        rng = np.random.default_rng(42)

        # Discover cells and users from MAC trace
        cell_ids = sorted({r["cell_id"] for r in mac_records})
        user_rntis = sorted({r["rnti"] for r in mac_records})

        for cid in cell_ids:
            snap.cells.append(CellInfo(
                cell_id=cid,
                position=rng.uniform(0, area_size),
            ))

        for rnti in user_rntis:
            # Compute throughput from PDCP
            user_pdcp = [r for r in pdcp_records if r["rnti"] == rnti]
            total_bytes = sum(r["size_bytes"] for r in user_pdcp)
            if user_pdcp:
                duration = max(r["time_s"] for r in user_pdcp) - min(r["time_s"] for r in user_pdcp)
                tp_mbps = (total_bytes * 8 / 1e6) / max(duration, 0.001)
            else:
                tp_mbps = 0.0

            # Find serving cell
            user_mac = [r for r in mac_records if r["rnti"] == rnti]
            serving = user_mac[0]["cell_id"] if user_mac else -1

            snap.users.append(UserInfo(
                user_id=rnti,
                position=rng.uniform(0, area_size),
                serving_cell=serving,
                achieved_throughput_mbps=tp_mbps,
            ))

        return snap

    # ── Synthetic Trace (Dev/Test) ───────────────────────────────

    @staticmethod
    def generate_synthetic_trace(
        num_cells: int = 4,
        num_users: int = 20,
        seed: int = 42,
    ) -> dict:
        """Generate synthetic ns-3-like trace for development."""
        rng = np.random.default_rng(seed)
        cells = [
            {"cell_id": i, "position": rng.uniform(0, 1000, 2).tolist(),
             "tx_power_dbm": 46.0, "num_prbs": 273}
            for i in range(num_cells)
        ]
        users = [
            {"user_id": j, "position": rng.uniform(0, 1000, 2).tolist(),
             "serving_cell": int(rng.integers(0, num_cells)),
             "demand_mbps": float(rng.uniform(5, 30)),
             "throughput_mbps": float(rng.uniform(2, 25)),
             "latency_ms": float(rng.exponential(5))}
            for j in range(num_users)
        ]
        return {"cells": cells, "users": users, "metadata": {"source": "synthetic"}}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
