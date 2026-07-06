"""
PQC Algorithms Database & Sizing Models
=======================================

Provides comprehensive specifications, byte sizing, CPU cycle estimates, and
telecommunications use cases for NIST PQC standards (FIPS 203, 204, 205),
legacy classical schemes, code-based cryptography, and hybrid transition suites.

References & Standardization Sources:
- NIST FIPS 203 (ML-KEM / Kyber): Module-Lattice-Based Key Encapsulation Mechanism Standard (Aug 2024).
- NIST FIPS 204 (ML-DSA / Dilithium): Module-Lattice-Based Digital Signature Standard (Aug 2024).
- NIST FIPS 205 (SLH-DSA / SPHINCS+): Stateless Hash-Based Digital Signature Standard (Aug 2024).
- SUPERCOP / eBACS: ECRYPT Benchmarking of Cryptographic Systems on Intel Xeon and Cortex-A53 testbeds.
- IETF RFC 8446 / NIST SP 800-56A: Classical ECDH P-256 and RSA-3072 sizing baselines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PQCAlgorithm:
    """Specification and engineering metrics for a cryptographic algorithm."""
    name: str
    family: str          # e.g., "Lattice-Based", "Hash-Based", "Code-Based", "Classical", "Hybrid"
    standard: str        # e.g., "NIST FIPS 203", "Legacy", "IETF RFC 9258"
    type: str            # "KEM", "Signature", "Hybrid-KEM", "Hybrid-Signature"
    security_level: int  # NIST Level 1-5 (0 for vulnerable legacy)
    public_key_bytes: int
    secret_key_bytes: int
    ciphertext_bytes: int  # 0 for signatures
    signature_bytes: int   # 0 for KEMs
    est_encap_cycles: int  # Reference x86_64 cycles (or sign cycles for signatures)
    est_decap_cycles: int  # Reference x86_64 cycles (or verify cycles for signatures)
    ram_footprint_bytes: int  # Peak working memory required
    description: str
    telecom_use_case: str

    @property
    def total_handshake_bytes(self) -> int:
        """Total payload bytes transmitted over the network for one operation."""
        return self.public_key_bytes + self.ciphertext_bytes + self.signature_bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "standard": self.standard,
            "type": self.type,
            "security_level": self.security_level,
            "nist_level": self.security_level,
            "quantum_safe": self.security_level > 0,
            "public_key_bytes": self.public_key_bytes,
            "secret_key_bytes": self.secret_key_bytes,
            "ciphertext_bytes": max(self.ciphertext_bytes, self.signature_bytes),
            "signature_bytes": self.signature_bytes,
            "total_handshake_bytes": self.total_handshake_bytes,
            "est_encap_cycles": self.est_encap_cycles,
            "est_decap_cycles": self.est_decap_cycles,
            "ram_footprint_bytes": self.ram_footprint_bytes,
            "description": self.description,
            "telecom_use_case": self.telecom_use_case,
        }


class AlgorithmDatabase:
    """Authoritative repository of cryptographic schemes and telecom benchmarks."""

    KEMS: dict[str, PQCAlgorithm] = {
        "ML-KEM-512": PQCAlgorithm(
            name="ML-KEM-512",
            family="Lattice-Based",
            standard="NIST FIPS 203",
            type="KEM",
            security_level=1,
            public_key_bytes=800,
            secret_key_bytes=1632,
            ciphertext_bytes=768,
            signature_bytes=0,
            est_encap_cycles=35000,
            est_decap_cycles=30000,
            ram_footprint_bytes=4096,
            description="Module-Lattice-Based Key Encapsulation Mechanism (Kyber-512). Fast, compact.",
            telecom_use_case="Constrained IoT sensors, NB-IoT SIM/eSIM key exchange, smart card APDUs.",
        ),
        "ML-KEM-768": PQCAlgorithm(
            name="ML-KEM-768",
            family="Lattice-Based",
            standard="NIST FIPS 203",
            type="KEM",
            security_level=3,
            public_key_bytes=1184,
            secret_key_bytes=2400,
            ciphertext_bytes=1088,
            signature_bytes=0,
            est_encap_cycles=50000,
            est_decap_cycles=45000,
            ram_footprint_bytes=6144,
            description="Primary NIST standard KEM (Kyber-768). Optimal balance of security and speed.",
            telecom_use_case="Default session key agreement for TLS 1.3, IPSec/IKEv2, and 5G Core SBA.",
        ),
        "ML-KEM-1024": PQCAlgorithm(
            name="ML-KEM-1024",
            family="Lattice-Based",
            standard="NIST FIPS 203",
            type="KEM",
            security_level=5,
            public_key_bytes=1568,
            secret_key_bytes=3168,
            ciphertext_bytes=1568,
            signature_bytes=0,
            est_encap_cycles=65000,
            est_decap_cycles=60000,
            ram_footprint_bytes=8192,
            description="High-security KEM (Kyber-1024) for critical government and defense tiers.",
            telecom_use_case="Core network backbone transport, lawful intercept, and defense communications.",
        ),
        "Classic-McEliece-348864": PQCAlgorithm(
            name="Classic-McEliece-348864",
            family="Code-Based",
            standard="NIST Round 4",
            type="KEM",
            security_level=1,
            public_key_bytes=261120,
            secret_key_bytes=6492,
            ciphertext_bytes=128,
            signature_bytes=0,
            est_encap_cycles=45000,
            est_decap_cycles=130000,
            ram_footprint_bytes=300000,
            description="Conservative code-based KEM. Extremely large public key, tiny ciphertext.",
            telecom_use_case="Long-lived submarine cable VPN tunnels and archival pre-shared key distribution.",
        ),
        "Classic-McEliece-6688128": PQCAlgorithm(
            name="Classic-McEliece-6688128",
            family="Code-Based",
            standard="NIST Round 4",
            type="KEM",
            security_level=5,
            public_key_bytes=1044992,
            secret_key_bytes=13932,
            ciphertext_bytes=240,
            signature_bytes=0,
            est_encap_cycles=80000,
            est_decap_cycles=280000,
            ram_footprint_bytes=1200000,
            description="Maximum assurance code-based KEM with 40+ year security track record.",
            telecom_use_case="Top-secret national telecom infrastructure and critical data center links.",
        ),
        "BIKE-L1": PQCAlgorithm(
            name="BIKE-L1",
            family="Code-Based",
            standard="NIST Round 4",
            type="KEM",
            security_level=1,
            public_key_bytes=1541,
            secret_key_bytes=3114,
            ciphertext_bytes=1541,
            signature_bytes=0,
            est_encap_cycles=150000,
            est_decap_cycles=1500000,
            ram_footprint_bytes=20480,
            description="Bit-Flipping Key Encapsulation. Compact alternative code-based KEM.",
            telecom_use_case="Backup code-based KEM for 5G Core control plane when lattice diversity is required.",
        ),
        "HQC-128": PQCAlgorithm(
            name="HQC-128",
            family="Code-Based",
            standard="NIST Round 4",
            type="KEM",
            security_level=1,
            public_key_bytes=2249,
            secret_key_bytes=2289,
            ciphertext_bytes=4481,
            signature_bytes=0,
            est_encap_cycles=180000,
            est_decap_cycles=300000,
            ram_footprint_bytes=16384,
            description="Hamming Quasi-Cyclic KEM. Rigorous reduction to coding theory problems.",
            telecom_use_case="Alternative KEM for Open RAN transport networks requiring non-lattice backup.",
        ),
    }

    SIGNATURES: dict[str, PQCAlgorithm] = {
        "ML-DSA-44": PQCAlgorithm(
            name="ML-DSA-44",
            family="Lattice-Based",
            standard="NIST FIPS 204",
            type="Signature",
            security_level=2,
            public_key_bytes=1312,
            secret_key_bytes=2560,
            ciphertext_bytes=0,
            signature_bytes=2420,
            est_encap_cycles=100000,
            est_decap_cycles=35000,
            ram_footprint_bytes=16384,
            description="Module-Lattice-Based Digital Signature Algorithm (Dilithium-2). Compact signatures.",
            telecom_use_case="Constrained device authentication, IoT signaling, and edge access points.",
        ),
        "ML-DSA-65": PQCAlgorithm(
            name="ML-DSA-65",
            family="Lattice-Based",
            standard="NIST FIPS 204",
            type="Signature",
            security_level=3,
            public_key_bytes=1952,
            secret_key_bytes=4032,
            ciphertext_bytes=0,
            signature_bytes=3309,
            est_encap_cycles=150000,
            est_decap_cycles=50000,
            ram_footprint_bytes=20480,
            description="Primary NIST standard signature (Dilithium-3). Optimal verification speed.",
            telecom_use_case="X.509 PKI certificates, 5G Core control plane (HTTP/2 SBA), and TLS server certs.",
        ),
        "ML-DSA-87": PQCAlgorithm(
            name="ML-DSA-87",
            family="Lattice-Based",
            standard="NIST FIPS 204",
            type="Signature",
            security_level=5,
            public_key_bytes=2592,
            secret_key_bytes=4896,
            ciphertext_bytes=0,
            signature_bytes=4627,
            est_encap_cycles=200000,
            est_decap_cycles=75000,
            ram_footprint_bytes=24576,
            description="High-security signature (Dilithium-5) for critical trust anchors.",
            telecom_use_case="Root and Intermediate Certificate Authorities (CAs), BGPsec routing trust anchors.",
        ),
        "SLH-DSA-SHA2-128s": PQCAlgorithm(
            name="SLH-DSA-SHA2-128s",
            family="Hash-Based",
            standard="NIST FIPS 205",
            type="Signature",
            security_level=1,
            public_key_bytes=32,
            secret_key_bytes=64,
            ciphertext_bytes=0,
            signature_bytes=7856,
            est_encap_cycles=45000000,
            est_decap_cycles=4500000,
            ram_footprint_bytes=12288,
            description="Stateless Hash-Based Digital Signature Algorithm (SPHINCS+). Small PK, slow signing.",
            telecom_use_case="Hardware Root-of-Trust, secure boot, eSIM firmware updates, offline root CAs.",
        ),
        "SLH-DSA-SHA2-256s": PQCAlgorithm(
            name="SLH-DSA-SHA2-256s",
            family="Hash-Based",
            standard="NIST FIPS 205",
            type="Signature",
            security_level=5,
            public_key_bytes=64,
            secret_key_bytes=128,
            ciphertext_bytes=0,
            signature_bytes=29792,
            est_encap_cycles=180000000,
            est_decap_cycles=15000000,
            ram_footprint_bytes=20480,
            description="Maximum security stateless hash signature. Conservative backup to lattice schemes.",
            telecom_use_case="Long-lived telecom infrastructure firmware signing and critical archival identity.",
        ),
        "Falcon-512": PQCAlgorithm(
            name="Falcon-512",
            family="Lattice-Based",
            standard="NIST Round 3",
            type="Signature",
            security_level=1,
            public_key_bytes=897,
            secret_key_bytes=1281,
            ciphertext_bytes=0,
            signature_bytes=666,
            est_encap_cycles=380000,
            est_decap_cycles=40000,
            ram_footprint_bytes=32768,
            description="Fast Fourier Lattice signature. Smallest combined PK and signature, complex FPU signing.",
            telecom_use_case="Bandwidth-constrained V2X communication, drone authentication, and satellite telemetry.",
        ),
    }

    LEGACY: dict[str, PQCAlgorithm] = {
        "RSA-2048": PQCAlgorithm(
            name="RSA-2048",
            family="Classical",
            standard="Legacy FIPS 186-4",
            type="Signature",
            security_level=0,
            public_key_bytes=256,
            secret_key_bytes=1200,
            ciphertext_bytes=256,
            signature_bytes=256,
            est_encap_cycles=1500000,
            est_decap_cycles=50000,
            ram_footprint_bytes=2048,
            description="Legacy integer factorization scheme. Vulnerable to Shor's algorithm in polynomial time.",
            telecom_use_case="Current legacy 3G/4G PKI, older TLS 1.2 server certificates, and enterprise VPNs.",
        ),
        "RSA-3072": PQCAlgorithm(
            name="RSA-3072",
            family="Classical",
            standard="Legacy FIPS 186-4",
            type="Signature",
            security_level=0,
            public_key_bytes=384,
            secret_key_bytes=1800,
            ciphertext_bytes=384,
            signature_bytes=384,
            est_encap_cycles=4500000,
            est_decap_cycles=100000,
            ram_footprint_bytes=3072,
            description="128-bit classical security RSA. Vulnerable to Shor's algorithm.",
            telecom_use_case="Current transitional enterprise PKI and government legacy systems.",
        ),
        "ECDH-P256": PQCAlgorithm(
            name="ECDH-P256",
            family="Classical",
            standard="Legacy SP 800-56A",
            type="KEM",
            security_level=0,
            public_key_bytes=64,
            secret_key_bytes=32,
            ciphertext_bytes=64,
            signature_bytes=0,
            est_encap_cycles=120000,
            est_decap_cycles=120000,
            ram_footprint_bytes=1024,
            description="Elliptic Curve Diffie-Hellman over NIST P-256. Vulnerable to Shor's algorithm.",
            telecom_use_case="Current 5G AKA authentication, TLS 1.3 key exchange, and eSIM profile provisioning.",
        ),
        "ECDSA-P256": PQCAlgorithm(
            name="ECDSA-P256",
            family="Classical",
            standard="Legacy FIPS 186-4",
            type="Signature",
            security_level=0,
            public_key_bytes=64,
            secret_key_bytes=32,
            ciphertext_bytes=0,
            signature_bytes=64,
            est_encap_cycles=150000,
            est_decap_cycles=180000,
            ram_footprint_bytes=1024,
            description="Elliptic Curve Digital Signature Algorithm. Compact, fast, but quantum-vulnerable.",
            telecom_use_case="Current 5G Core control plane authentication and smart card identity.",
        ),
        "X25519": PQCAlgorithm(
            name="X25519",
            family="Classical",
            standard="RFC 7748",
            type="KEM",
            security_level=0,
            public_key_bytes=32,
            secret_key_bytes=32,
            ciphertext_bytes=32,
            signature_bytes=0,
            est_encap_cycles=80000,
            est_decap_cycles=80000,
            ram_footprint_bytes=1024,
            description="Curve25519 Diffie-Hellman. Standard modern classical key exchange.",
            telecom_use_case="Modern classical VPNs, WireGuard tunnels, and cloud edge transport.",
        ),
    }

    HYBRID: dict[str, PQCAlgorithm] = {
        "X25519+ML-KEM-768": PQCAlgorithm(
            name="X25519+ML-KEM-768",
            family="Hybrid",
            standard="IETF Draft / ETSI TS 103 744",
            type="Hybrid-KEM",
            security_level=3,
            public_key_bytes=1216,  # 32 + 1184
            secret_key_bytes=2432,
            ciphertext_bytes=1120,  # 32 + 1088
            signature_bytes=0,
            est_encap_cycles=130000,
            est_decap_cycles=125000,
            ram_footprint_bytes=7168,
            description="Combined classical elliptic curve and lattice KEM. Ensures FIPS compliance and crypto-agility.",
            telecom_use_case="Recommended transition suite for TLS 1.3, IPSec/IKEv2, and 5G Core signaling.",
        ),
        "ECDH-P384+ML-KEM-1024": PQCAlgorithm(
            name="ECDH-P384+ML-KEM-1024",
            family="Hybrid",
            standard="IETF Draft / ETSI TS 103 744",
            type="Hybrid-KEM",
            security_level=5,
            public_key_bytes=1664,
            secret_key_bytes=3216,
            ciphertext_bytes=1664,
            signature_bytes=0,
            est_encap_cycles=250000,
            est_decap_cycles=240000,
            ram_footprint_bytes=10240,
            description="High-assurance hybrid KEM for defense-in-depth telecom backbone encryption.",
            telecom_use_case="Critical infrastructure transport, lawful intercept, and optical backbone links.",
        ),
        "ECDSA-P256+ML-DSA-65": PQCAlgorithm(
            name="ECDSA-P256+ML-DSA-65",
            family="Hybrid",
            standard="IETF X.509 Dual-Sig Draft",
            type="Hybrid-Signature",
            security_level=3,
            public_key_bytes=2016,  # 64 + 1952
            secret_key_bytes=4064,
            ciphertext_bytes=0,
            signature_bytes=3373,   # 64 + 3309
            est_encap_cycles=300000,
            est_decap_cycles=230000,
            ram_footprint_bytes=22528,
            description="Dual-signed X.509 certificate hierarchy combining classical ECDSA with Dilithium-3.",
            telecom_use_case="Transitional 5G Core PKI, operator CA cross-signing, and server authentication.",
        ),
    }

    @classmethod
    def get_all(cls) -> dict[str, PQCAlgorithm]:
        """Return a unified dictionary of all registered algorithms."""
        all_algos = {}
        all_algos.update(cls.KEMS)
        all_algos.update(cls.SIGNATURES)
        all_algos.update(cls.LEGACY)
        all_algos.update(cls.HYBRID)
        return all_algos


def get_algorithm(name: str) -> PQCAlgorithm:
    """Retrieve an algorithm by name."""
    db = AlgorithmDatabase.get_all()
    if name not in db:
        raise KeyError(f"Algorithm '{name}' not found in TELEQUM PQC database. Available: {list(db.keys())}")
    return db[name]


def list_algorithms(
    family: str | None = None,
    type_filter: str | None = None,
    min_level: int = 0,
) -> list[PQCAlgorithm]:
    """Filter and list algorithms by family, type, and minimum security level."""
    results = []
    for algo in AlgorithmDatabase.get_all().values():
        if family and algo.family != family:
            continue
        if type_filter and algo.type != type_filter:
            continue
        if algo.security_level < min_level:
            continue
        results.append(algo)
    return sorted(results, key=lambda x: (x.family, -x.security_level, x.name))


def compare_algorithms(names: list[str]) -> list[dict[str, Any]]:
    """Return a list of dictionaries for side-by-side comparison tables."""
    return [get_algorithm(name).to_dict() for name in names]
