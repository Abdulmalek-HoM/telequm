"""Data provenance and credibility reporting for the TELEQUM dashboard.

The dashboard combines live host measurements, model-derived simulations,
literature-backed reference material, and manually maintained scenario data.
This module makes that distinction visible instead of presenting every number
with the same implied level of certainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CredibilityType = Literal["live", "estimated", "literature", "manual"]

STATUS = {
    "live": {"label": "🟢 Live", "score": 100},
    "estimated": {"label": "🟡 Estimated", "score": 65},
    "literature": {"label": "🔵 Literature", "score": 85},
    "manual": {"label": "⚪ Manual", "score": 35},
}


@dataclass(frozen=True)
class CredibilityItem:
    """One dashboard data source or quantitative output family."""

    feature: str
    category: CredibilityType
    weight: int
    source: str
    validation: str
    scope: str

    @property
    def score(self) -> int:
        return STATUS[self.category]["score"]

    @property
    def status(self) -> str:
        return STATUS[self.category]["label"]


# We score output families rather than each individual rendered number.  This
# keeps the assessment stable and makes provenance actionable at the feature
# level: a source owner can upgrade a whole family by adding citations, live
# ingestion, or reproducible validation.
CREDIBILITY_CATALOG: tuple[CredibilityItem, ...] = (
    CredibilityItem(
        "Quantum computing concepts and research reference library", "literature", 2,
        "Curated papers and standards listed in the Education Hub.",
        "Bibliographic links are displayed in the UI; no automated link or claim verification.",
        "Education Hub: Quantum 101, problem statements, research references.",
    ),
    CredibilityItem(
        "PQC algorithm catalogue and standards comparison", "literature", 3,
        "NIST FIPS 203/204/205-oriented algorithm metadata maintained in telequm.pqc.",
        "Unit-tested lookup and comparison behaviour; values are maintained in source, not fetched live.",
        "Education Hub PQC 101 and protocol tooling.",
    ),
    CredibilityItem(
        "HNDL risk and AQC maturity calculators", "estimated", 3,
        "Explicit Mosca-style inputs and an in-project maturity model.",
        "Formula execution is test-covered; risk thresholds and maturity interpretation are modelling assumptions.",
        "Education Hub threat matrix and migration framework.",
    ),
    CredibilityItem(
        "Memory, complexity, and solver-time projections", "estimated", 2,
        "Big-O formulae and local benchmark scaling rules.",
        "Deterministic calculations; not calibrated against a benchmark corpus or production workload traces.",
        "Education Hub calculators and resource panels.",
    ),
    CredibilityItem(
        "PQC protocol, latency, CPU, and fragmentation results", "estimated", 4,
        "ProtocolSimulator with embedded link, algorithm, and CPU-cycle assumptions.",
        "Simulator behaviour is unit-tested; results are not packet captures or measured device benchmarks.",
        "Use-Case Lab crypto-agility tools.",
    ),
    CredibilityItem(
        "Single-shot telecom QUBO solver results", "estimated", 5,
        "Synthetic topology, channel, traffic, and solver models in TELEQUM.",
        "All supported problem/solver paths are smoke-testable; validity depends on the selected model assumptions.",
        "Use-Case Lab optimisation experiments.",
    ),
    CredibilityItem(
        "Time-series network digital twin metrics", "estimated", 5,
        "Synthetic 3GPP-inspired propagation, traffic, mobility, and PRB-allocation simulation.",
        "Automated simulator tests cover execution and reproducibility; no live RAN telemetry is ingested.",
        "Digital Twin live network optimisation view.",
    ),
    CredibilityItem(
        "Quantum-backend specifications and FTQC roadmap", "manual", 4,
        "Hand-maintained constants in dashboard.components.hardware_hub.BACKENDS.",
        "No provider API, timestamp, or source citation is attached to each value.",
        "Hardware Hub quantum computer comparison.",
    ),
    CredibilityItem(
        "Telecom infrastructure PQC performance benchmark table", "manual", 4,
        "Hand-maintained latency, TPS, and memory figures in hardware_hub.py.",
        "No linked benchmark methodology, hardware run log, or external source per figure.",
        "Hardware Hub PQC infrastructure comparison.",
    ),
    CredibilityItem(
        "Host device benchmark", "live", 2,
        "Runtime CPU/RAM/platform inspection and a local NumPy matrix-multiply sample.",
        "Measured at button press on the Streamlit host; it is a quick indicator, not a controlled benchmark suite.",
        "Education Hub hardware benchmark.",
    ),
    CredibilityItem(
        "PQC migration and HNDL timeline", "estimated", 4,
        "User-selected rollout, CRQC horizon, and sensitive-traffic assumptions.",
        "Deterministic and reproducible; it is a scenario calculator rather than an operator inventory model.",
        "Digital Twin migration and HNDL view.",
    ),
    CredibilityItem(
        "Previously saved experiment and benchmark files", "manual", 2,
        "Local JSON files when supplied by the project user.",
        "File presence is checked, but provenance, schema version, and integrity are not currently verified.",
        "Data-loader utility for future dashboard integrations.",
    ),
)


def overall_score(items: tuple[CredibilityItem, ...] = CREDIBILITY_CATALOG) -> int:
    """Return the impact-weighted platform credibility score on a 0–100 scale."""
    total_weight = sum(item.weight for item in items)
    if not total_weight:
        return 0
    return round(sum(item.score * item.weight for item in items) / total_weight)


def score_by_category(items: tuple[CredibilityItem, ...] = CREDIBILITY_CATALOG) -> dict[str, int]:
    """Return the number of assessed output families in each provenance class."""
    return {category: sum(item.category == category for item in items) for category in STATUS}


def catalog_rows(items: tuple[CredibilityItem, ...] = CREDIBILITY_CATALOG) -> list[dict[str, object]]:
    """Convert the registry to rows suitable for Streamlit tables and downloads."""
    return [
        {
            "Feature / output family": item.feature,
            "Status": item.status,
            "Score": item.score,
            "Impact weight": item.weight,
            "Source": item.source,
            "Validation": item.validation,
            "Dashboard scope": item.scope,
        }
        for item in items
    ]
