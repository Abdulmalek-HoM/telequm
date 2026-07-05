 """
TELEQUM vNext — Post-Quantum Cryptography & Quantum-Safe Telecom Package
========================================================================

This package provides industrial-grade mathematical models, protocol handshake
simulators, threat estimators, and operational migration frameworks for
transitioning telecommunications infrastructure to Quantum-Safe Networks.

Modules:
    - algorithms: NIST FIPS 203/204/205, legacy classical, code-based, and hybrid suites.
    - protocols: Handshake simulators for TLS 1.3, IPSec/IKEv2, MACsec, 5G AKA, DNSSEC, BGP.
    - threat_models: Harvest Now Decrypt Later (HNDL) risk engine and Shor/Grover calculators.
    - migration: AQC Whitepaper frameworks (Maturity Ladder, Execution Chain, KPIs, Sector risk).
"""

from __future__ import annotations

from telequm.pqc.algorithms import (
    PQCAlgorithm,
    AlgorithmDatabase,
    get_algorithm,
    list_algorithms,
    compare_algorithms,
)
from telequm.pqc.protocols import (
    ProtocolSimulator,
    HandshakeResult,
    HandshakeStep,
    ProtocolType,
    LinkType,
    CryptoSuite,
)
from telequm.pqc.threat_models import (
    HNDLCalculator,
    HNDLRiskScore,
    ShorGroverEstimator,
    QuantumResourceEstimate,
)
from telequm.pqc.migration import (
    MaturityScore,
    MaturityLadder,
    MaturityLevel,
    MigrationExecutionChain,
    MigrationStage,
    MigrationKPIs,
    SectorRiskMatrix,
    SectorType,
)

__all__ = [
    "PQCAlgorithm",
    "AlgorithmDatabase",
    "get_algorithm",
    "list_algorithms",
    "compare_algorithms",
    "ProtocolSimulator",
    "HandshakeResult",
    "HandshakeStep",
    "ProtocolType",
    "LinkType",
    "CryptoSuite",
    "HNDLCalculator",
    "HNDLRiskScore",
    "ShorGroverEstimator",
    "QuantumResourceEstimate",
    "MaturityScore",
    "MaturityLadder",
    "MaturityLevel",
    "MigrationExecutionChain",
    "MigrationStage",
    "MigrationKPIs",
    "SectorRiskMatrix",
