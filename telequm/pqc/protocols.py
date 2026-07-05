"""
Telecom Protocol Handshake & Fragmentation Simulators
=====================================================

Simulates cryptographic handshakes across real telecommunications protocols
(TLS 1.3, IPSec/IKEv2, MACsec, 5G AKA, DNSSEC, BGP) under Classical, Hybrid,
and Post-Quantum suites.

Evaluates packet expansion, MTU fragmentation, transmission latency over diverse
telecom links (Fiber, 5G RAN, Satellite, IoT), and CPU processing cycles across
target hardware architectures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from telequm.pqc.algorithms import PQCAlgorithm, get_algorithm

ProtocolType = Literal["TLS_1_3", "IPSec_IKEv2", "MACsec", "5G_AKA", "DNSSEC", "BGP_SEC"]
LinkType = Literal["5G_UMa_RAN", "Optical_Fiber_Core", "Submarine_Cable", "Satellite_LEO", "IoT_NB_Air"]
CryptoSuite = Literal["Classical", "Hybrid", "Pure_PQC"]


# ─── Telecom Network Link Specifications ─────────────────────────────────

@dataclass
class LinkSpec:
    """Physical network link characteristics."""
    name: str
    bandwidth_mbps: float
    rtt_ms: float
    mtu_bytes: int
    packet_loss_rate: float
    description: str


LINKS: dict[str, LinkSpec] = {
    "5G_UMa_RAN": LinkSpec(
        name="5G Urban Macro RAN",
        bandwidth_mbps=100.0,
        rtt_ms=8.0,
        mtu_bytes=1500,
        packet_loss_rate=0.001,
        description="Standard 3GPP 5G air interface between UE and gNB.",
    ),
    "Optical_Fiber_Core": LinkSpec(
        name="Optical Fiber Core Backbone",
        bandwidth_mbps=10000.0,  # 10 Gbps
        rtt_ms=2.0,
        mtu_bytes=9000,          # Jumbo frames
        packet_loss_rate=0.00001,
        description="High-speed terrestrial fiber transport between 5G Core data centers.",
    ),
    "Submarine_Cable": LinkSpec(
        name="Trans-Oceanic Submarine Cable",
        bandwidth_mbps=100000.0, # 100 Gbps
        rtt_ms=80.0,
        mtu_bytes=9000,
        packet_loss_rate=0.000001,
        description="Inter-continental submarine optical fiber link.",
    ),
    "Satellite_LEO": LinkSpec(
        name="LEO Satellite Link",
        bandwidth_mbps=50.0,
        rtt_ms=40.0,
        mtu_bytes=1400,
        packet_loss_rate=0.005,
        description="Low Earth Orbit satellite transport for remote cell towers and maritime.",
    ),
    "IoT_NB_Air": LinkSpec(
        name="NB-IoT / LPWAN Air Link",
        bandwidth_mbps=0.1,      # 100 kbps
        rtt_ms=500.0,
        mtu_bytes=1280,          # IPv6 minimum MTU
        packet_loss_rate=0.02,
        description="Constrained Narrowband IoT wireless sensor connection.",
    ),
}


# ─── Hardware Architecture Multipliers ───────────────────────────────────

HARDWARE_SPEED_MULTIPLIERS: dict[str, float] = {
    "x86_server": 1.0,         # Intel Xeon / AMD EPYC @ ~3.0 GHz (Reference)
    "edge_gnb": 1.5,           # Edge Base Station processor @ ~2.0 GHz
    "arm_cortex_m4": 30.0,     # Constrained IoT / SIM Smart Card @ ~100 MHz
    "baseband_fpga": 0.5,      # Hardware accelerated FPGA/ASIC baseband processing
}


@dataclass
class HandshakeStep:
    """A single packet transmission step in a protocol handshake."""
    step_index: int
    name: str
    sender: str
    payload_bytes: int
    num_fragments: int
    transmission_ms: float
    crypto_cpu_ms: float
    total_step_ms: float


@dataclass
class HandshakeResult:
    """Comprehensive simulation results for a protocol handshake."""
    protocol: str
    link_type: str
    crypto_suite: str
    kem_used: str
    sig_used: str
    total_handshake_bytes: int
    client_to_server_bytes: int
    server_to_client_bytes: int
    total_fragments: int
    max_fragment_size: int
    total_latency_ms: float
    network_transmission_ms: float
    crypto_processing_ms: float
    cert_chain_bytes: int
    fragmentation_risk: bool
    steps: list[HandshakeStep] = field(default_factory=list)
    summary_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "link_type": self.link_type,
            "crypto_suite": self.crypto_suite,
            "kem_used": self.kem_used,
            "sig_used": self.sig_used,
            "total_handshake_bytes": self.total_handshake_bytes,
            "client_to_server_bytes": self.client_to_server_bytes,
            "server_to_client_bytes": self.server_to_client_bytes,
            "total_fragments": self.total_fragments,
            "max_fragment_size": self.max_fragment_size,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "network_transmission_ms": round(self.network_transmission_ms, 2),
            "crypto_processing_ms": round(self.crypto_processing_ms, 2),
            "cert_chain_bytes": self.cert_chain_bytes,
            "fragmentation_risk": self.fragmentation_risk,
            "num_steps": len(self.steps),
            "summary_notes": self.summary_notes,
        }


class ProtocolSimulator:
    """Simulates telecom protocol handshakes and analyzes network impact."""

    @classmethod
    def get_suite_algorithms(cls, crypto_suite: str) -> tuple[PQCAlgorithm, PQCAlgorithm, int]:
        """Return (KEM, Signature, cert_chain_bytes) for a given suite."""
        if crypto_suite == "Classical":
            kem = get_algorithm("ECDH-P256")
            sig = get_algorithm("ECDSA-P256")
            cert_chain = 3000  # 3 x ~1 KB classical X.509 certs (Root, Inter, Leaf)
        elif crypto_suite == "Hybrid":
            kem = get_algorithm("X25519+ML-KEM-768")
            sig = get_algorithm("ECDSA-P256+ML-DSA-65")
            cert_chain = 10000 # 3 x dual-signed hybrid certs
        elif crypto_suite == "Pure_PQC":
            kem = get_algorithm("ML-KEM-768")
            sig = get_algorithm("ML-DSA-65")
            cert_chain = 11000 # 3 x ML-DSA-65 certs (~3.6 KB each)
        else:
            raise ValueError(f"Unknown crypto suite: {crypto_suite}")
        return kem, sig, cert_chain

    @classmethod
    def simulate_handshake(
        cls,
        protocol: str,
        link_type: str,
        crypto_suite: str,
        target_hw: str = "x86_server",
    ) -> HandshakeResult:
        """Simulate a full protocol handshake over a specific telecom link."""
        if link_type not in LINKS:
            raise KeyError(f"Link type '{link_type}' not found. Available: {list(LINKS.keys())}")
        link = LINKS[link_type]
        hw_mult = HARDWARE_SPEED_MULTIPLIERS.get(target_hw, 1.0)

        kem, sig, cert_chain_bytes = cls.get_suite_algorithms(crypto_suite)

        # Base cycle time in ms for reference x86 (assume 3 GHz => 1 cycle = 0.333 ns => 3,000,000 cycles = 1 ms)
        def cycles_to_ms(cycles: int) -> float:
            return (cycles / 3_000_000.0) * hw_mult

        steps: list[HandshakeStep] = []
        c2s_bytes = 0
        s2c_bytes = 0
        net_ms = 0.0
        cpu_ms = 0.0

        if protocol == "TLS_1_3":
            # Step 1: ClientHello + KeyShare (KEM PK)
            s1_bytes = 200 + kem.public_key_bytes
            s1_frags = math.ceil(s1_bytes / link.mtu_bytes)
            s1_net = (s1_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s1_cpu = cycles_to_ms(kem.est_encap_cycles // 2) # Keypair gen
            steps.append(HandshakeStep(1, "ClientHello + KeyShare (KEM PK)", "Client (UE/Browser)", s1_bytes, s1_frags, s1_net, s1_cpu, s1_net + s1_cpu))
            c2s_bytes += s1_bytes
            net_ms += s1_net
            cpu_ms += s1_cpu

            # Step 2: ServerHello + KeyShare (KEM CT) + EncryptedExtensions + Cert Chain + CertVerify (Sig) + Finished
            s2_bytes = 300 + kem.ciphertext_bytes + cert_chain_bytes + sig.signature_bytes
            s2_frags = math.ceil(s2_bytes / link.mtu_bytes)
            s2_net = (s2_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s2_cpu = cycles_to_ms(kem.est_encap_cycles + sig.est_encap_cycles) # KEM encap + Sign
            steps.append(HandshakeStep(2, "ServerHello + KEM CT + Cert Chain + Sig + Finished", "Server (5G Core/Web)", s2_bytes, s2_frags, s2_net, s2_cpu, s2_net + s2_cpu))
            s2c_bytes += s2_bytes
            net_ms += s2_net
            cpu_ms += s2_cpu

            # Step 3: Client Finished (Decap + Verify)
            s3_bytes = 80
            s3_frags = 1
            s3_net = (s3_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s3_cpu = cycles_to_ms(kem.est_decap_cycles + sig.est_decap_cycles) # Decap + Verify
            steps.append(HandshakeStep(3, "Client Finished + Verification", "Client (UE/Browser)", s3_bytes, s3_frags, s3_net, s3_cpu, s3_net + s3_cpu))
            c2s_bytes += s3_bytes
            net_ms += s3_net
            cpu_ms += s3_cpu

            summary = f"TLS 1.3 handshake over {link.name}. Total exchange: {c2s_bytes + s2c_bytes:,} B."

        elif protocol == "IPSec_IKEv2":
            # IKE_SA_INIT Request (KEM PK)
            s1_bytes = 250 + kem.public_key_bytes
            s1_frags = math.ceil(s1_bytes / link.mtu_bytes)
            s1_net = (s1_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s1_cpu = cycles_to_ms(kem.est_encap_cycles // 2)
            steps.append(HandshakeStep(1, "IKE_SA_INIT Req (KEM PK)", "Initiator (gNB/Router)", s1_bytes, s1_frags, s1_net, s1_cpu, s1_net + s1_cpu))
            c2s_bytes += s1_bytes
            net_ms += s1_net
            cpu_ms += s1_cpu

            # IKE_SA_INIT Response (KEM CT)
            s2_bytes = 250 + kem.ciphertext_bytes
            s2_frags = math.ceil(s2_bytes / link.mtu_bytes)
            s2_net = (s2_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s2_cpu = cycles_to_ms(kem.est_encap_cycles)
            steps.append(HandshakeStep(2, "IKE_SA_INIT Resp (KEM CT)", "Responder (Security Gateway)", s2_bytes, s2_frags, s2_net, s2_cpu, s2_net + s2_cpu))
            s2c_bytes += s2_bytes
            net_ms += s2_net
            cpu_ms += s2_cpu

            # IKE_AUTH Request (Cert Chain + Sig)
            s3_bytes = 300 + cert_chain_bytes + sig.signature_bytes
            s3_frags = math.ceil(s3_bytes / link.mtu_bytes)
            s3_net = (s3_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s3_cpu = cycles_to_ms(kem.est_decap_cycles + sig.est_encap_cycles)
            steps.append(HandshakeStep(3, "IKE_AUTH Req (Cert Chain + Sig)", "Initiator (gNB/Router)", s3_bytes, s3_frags, s3_net, s3_cpu, s3_net + s3_cpu))
            c2s_bytes += s3_bytes
            net_ms += s3_net
            cpu_ms += s3_cpu

            # IKE_AUTH Response (Cert Chain + Sig)
            s4_bytes = 300 + cert_chain_bytes + sig.signature_bytes
            s4_frags = math.ceil(s4_bytes / link.mtu_bytes)
            s4_net = (s4_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s4_cpu = cycles_to_ms(sig.est_decap_cycles + sig.est_encap_cycles)
            steps.append(HandshakeStep(4, "IKE_AUTH Resp (Cert Chain + Sig)", "Responder (Security Gateway)", s4_bytes, s4_frags, s4_net, s4_cpu, s4_net + s4_cpu))
            s2c_bytes += s4_bytes
            net_ms += s4_net
            cpu_ms += s4_cpu

            summary = f"IPSec / IKEv2 tunnel establishment over {link.name}. High fragmentation risk on standard Ethernet MTU."

        elif protocol == "5G_AKA":
            # 5G AKA Authentication Request (UE -> gNB -> AMF -> UDM)
            s1_bytes = 150 + (kem.public_key_bytes if crypto_suite != "Classical" else 64)
            s1_frags = math.ceil(s1_bytes / link.mtu_bytes)
            s1_net = (s1_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s1_cpu = cycles_to_ms(kem.est_encap_cycles // 2)
            steps.append(HandshakeStep(1, "5G AKA Auth Request + SUCI", "UE / SIM Smart Card", s1_bytes, s1_frags, s1_net, s1_cpu, s1_net + s1_cpu))
            c2s_bytes += s1_bytes
            net_ms += s1_net
            cpu_ms += s1_cpu

            # Authentication Vector (AV) Challenge (UDM/AMF -> UE)
            s2_bytes = 200 + (kem.ciphertext_bytes if crypto_suite != "Classical" else 64) + sig.signature_bytes
            s2_frags = math.ceil(s2_bytes / link.mtu_bytes)
            s2_net = (s2_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s2_cpu = cycles_to_ms(kem.est_encap_cycles + sig.est_encap_cycles)
            steps.append(HandshakeStep(2, "Auth Challenge (5G AV + KEM CT)", "AMF / UDM Core", s2_bytes, s2_frags, s2_net, s2_cpu, s2_net + s2_cpu))
            s2c_bytes += s2_bytes
            net_ms += s2_net
            cpu_ms += s2_cpu

            # Auth Response + Session Key Derivation (UE -> AMF)
            s3_bytes = 100
            s3_frags = 1
            s3_net = (s3_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s3_cpu = cycles_to_ms(kem.est_decap_cycles + sig.est_decap_cycles)
            steps.append(HandshakeStep(3, "Auth Response + RES* Verify", "UE / SIM Smart Card", s3_bytes, s3_frags, s3_net, s3_cpu, s3_net + s3_cpu))
            c2s_bytes += s3_bytes
            net_ms += s3_net
            cpu_ms += s3_cpu

            summary = f"5G AKA Authentication over {link.name}. Critical smart card APDU buffer constraints."

        elif protocol in ("MACsec", "DNSSEC", "BGP_SEC"):
            # Simplified 2-step exchange for link-layer / routing protocols
            s1_bytes = 120 + kem.public_key_bytes
            s1_frags = math.ceil(s1_bytes / link.mtu_bytes)
            s1_net = (s1_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s1_cpu = cycles_to_ms(kem.est_encap_cycles)
            steps.append(HandshakeStep(1, f"{protocol} Key Agreement Request", "Initiator Node", s1_bytes, s1_frags, s1_net, s1_cpu, s1_net + s1_cpu))
            c2s_bytes += s1_bytes
            net_ms += s1_net
            cpu_ms += s1_cpu

            s2_bytes = 150 + kem.ciphertext_bytes + sig.signature_bytes
            s2_frags = math.ceil(s2_bytes / link.mtu_bytes)
            s2_net = (s2_bytes * 8.0) / (link.bandwidth_mbps * 1e6) * 1000.0 + (link.rtt_ms / 2.0)
            s2_cpu = cycles_to_ms(kem.est_decap_cycles + sig.est_decap_cycles)
            steps.append(HandshakeStep(2, f"{protocol} Key Agreement Response", "Responder Node", s2_bytes, s2_frags, s2_net, s2_cpu, s2_net + s2_cpu))
            s2c_bytes += s2_bytes
            net_ms += s2_net
            cpu_ms += s2_cpu

            summary = f"{protocol} session establishment over {link.name}."
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

        total_bytes = c2s_bytes + s2c_bytes
        total_frags = sum(s.num_fragments for s in steps)
        max_frag_size = max(s.payload_bytes for s in steps)
        frag_risk = any(s.payload_bytes > link.mtu_bytes for s in steps) or (total_frags > len(steps) * 2)

        return HandshakeResult(
            protocol=protocol,
            link_type=link_type,
            crypto_suite=crypto_suite,
            kem_used=kem.name,
            sig_used=sig.name,
            total_handshake_bytes=total_bytes,
            client_to_server_bytes=c2s_bytes,
            server_to_client_bytes=s2c_bytes,
            total_fragments=total_frags,
            max_fragment_size=max_frag_size,
            total_latency_ms=net_ms + cpu_ms,
            network_transmission_ms=net_ms,
            crypto_processing_ms=cpu_ms,
            cert_chain_bytes=cert_chain_bytes,
            fragmentation_risk=frag_risk,
            steps=steps,
            summary_notes=summary,
        )
