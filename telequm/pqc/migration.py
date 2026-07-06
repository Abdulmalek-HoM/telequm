"""
AQC Whitepaper Operational Migration & Sector Risk Frameworks
=============================================================

Implements operational governance models derived from the AQC Whitepaper feedback:
- Operational Maturity Ladder (Levels 0 to 4)
- Migration Execution Chain (7-stage workflow)
- Migration KPIs (real-time tracking metrics)
- Infrastructure Lifecycle Categories (A, B, C, D)
- Sector-Specific Migration Profiles (Telecom, Banking, Mobile Money, SCADA/OT, Identity)

References & Standardization Sources:
- GSMA: "Post-Quantum Computing Telco Network Guidelines" (GSMA Whitepaper, 2023/2024).
- Applied Quantum Computing (AQC): Telecom Operational Maturity Frameworks.
- ETSI TR 103 619: Migration strategies and recommendations to Quantum-Safe schemes.
- ICAO / CISA / EBA: Sector data sensitivity shelf-life mandates (50 yr identity, 35 yr SCADA, 15 yr banking).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

MaturityLevel = Literal[0, 1, 2, 3, 4]


# ─── 1. Operational Maturity Ladder ──────────────────────────────────────

@dataclass
class MaturityScore:
    """Evaluation score across the 5 pillars of cryptographic maturity."""
    governance: int      # 0-100: Policy, executive sponsorship, PQC task force
    discovery: int       # 0-100: Automated inventory, SBOM/CBOM, visibility
    architecture: int    # 0-100: Crypto-agility, hybrid support, modular design
    operations: int      # 0-100: Certificate lifecycle automation, monitoring
    procurement: int     # 0-100: Vendor mandates, RFP requirements, SLA tracking
    overall_score: float # Average score
    level: int           # 0 to 4
    level_name: str
    next_steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "governance": self.governance,
            "discovery": self.discovery,
            "architecture": self.architecture,
            "operations": self.operations,
            "procurement": self.procurement,
            "overall_score": round(self.overall_score, 1),
            "level": self.level,
            "level_name": self.level_name,
            "name": self.level_name,
            "next_steps": self.next_steps,
            "next_step": self.next_step,
            "description": self.description,
        }

    @property
    def name(self) -> str:
        return self.level_name

    @property
    def next_step(self) -> str:
        return self.next_steps[0] if self.next_steps else "Maintain continuous monitoring."

    @property
    def description(self) -> str:
        return MaturityLadder.LEVEL_NAMES.get(self.level, f"Level {self.level} Maturity")


class MaturityLadder:
    """Evaluates an organization's post-quantum operational readiness."""

    LEVEL_NAMES = {
        0: "Level 0: Unaware & Vulnerable",
        1: "Level 1: Discovery & Assessment",
        2: "Level 2: Crypto-Agility & Hybrid Ready",
        3: "Level 3: Default PQC Enforcement",
        4: "Level 4: Quantum-Native Defense-in-Depth",
    }

    @classmethod
    def evaluate(
        cls,
        governance: int | dict[str, int] | list[int] | tuple[int, ...],
        discovery: int = 0,
        architecture: int = 0,
        operations: int = 0,
        procurement: int = 0,
    ) -> MaturityScore:
        """Compute maturity level and actionable recommendations."""
        if isinstance(governance, dict):
            discovery = governance.get("Discovery", governance.get("discovery", 0))
            architecture = governance.get("Architecture", governance.get("architecture", 0))
            operations = governance.get("Operations", governance.get("operations", 0))
            procurement = governance.get("Procurement", governance.get("procurement", 0))
            governance = governance.get("Governance", governance.get("governance", 0))
        elif isinstance(governance, (list, tuple)) and len(governance) >= 5:
            governance, discovery, architecture, operations, procurement = governance[:5]

        avg = (governance + discovery + architecture + operations + procurement) / 5.0

        if avg < 20.0:
            lvl = 0
            steps = [
                "Establish an executive-sponsored Quantum-Safe Task Force.",
                "Initiate automated cryptographic discovery across external-facing gateways.",
                "Update vendor procurement guidelines to mandate PQC disclosure.",
            ]
        elif avg < 45.0:
            lvl = 1
            steps = [
                "Deploy automated CBOM (Cryptographic Bill of Materials) scanning across all 5G Core nodes.",
                "Classify inventory by Infrastructure Lifecycle Categories (A, B, C, D).",
                "Begin lab testing of hybrid TLS 1.3 (X25519 + ML-KEM-768) in testbeds.",
            ]
        elif avg < 70.0:
            lvl = 2
            steps = [
                "Enforce hybrid key exchange on all external VPNs and cloud interconnects.",
                "Eliminate hardcoded classical primitives from proprietary applications.",
                "Automate X.509 certificate renewal cycles to support rapid agility.",
            ]
        elif avg < 90.0:
            lvl = 3
            steps = [
                "Mandate pure NIST PQC standards (ML-KEM, ML-DSA) as default across internal networks.",
                "Decommission legacy RSA/ECC fallback cipher suites.",
                "Integrate continuous HNDL vulnerability scoring into SOC monitoring.",
            ]
        else:
            lvl = 4
            steps = [
                "Integrate Quantum Key Distribution (QKD) across high-security optical transport backbones.",
                "Deploy continuous quantum random number generators (QRNG) in SIM/eSIM provisioning.",
                "Maintain ongoing leadership in 6G quantum security standards.",
            ]

        return MaturityScore(
            governance=governance,
            discovery=discovery,
            architecture=architecture,
            operations=operations,
            procurement=procurement,
            overall_score=avg,
            level=lvl,
            level_name=cls.LEVEL_NAMES[lvl],
            next_steps=steps,
        )


# ─── 2. Migration Execution Chain ────────────────────────────────────────

@dataclass
class MigrationStage:
    """A stage in the 7-step telecom PQC migration workflow."""
    stage_id: int
    name: str
    duration_months: str
    key_activities: list[str]
    telecom_bottlenecks: list[str]
    deliverables: list[str]

    @property
    def stage_number(self) -> int:
        return self.stage_id

    @property
    def timeline(self) -> str:
        return self.duration_months

    @property
    def objective(self) -> str:
        return self.key_activities[0] if self.key_activities else "Execute migration activities."

    @property
    def key_milestones(self) -> list[str]:
        return self.key_activities + self.telecom_bottlenecks



class MigrationExecutionChain:
    """Models the end-to-end migration execution roadmap for telecom operators."""

    STAGES: list[MigrationStage] = [
        MigrationStage(
            1, "Discovery & Automated Inventory", "6 – 12 Months",
            ["Scan network gateways, routers, and 5G Core nodes for cryptographic algorithms.", "Generate real-time Cryptographic Bill of Materials (CBOM).", "Identify undocumented or shadow PKI hierarchies."],
            ["Proprietary baseband firmware lacking introspection APIs.", "Deeply embedded smart card (SIM/eSIM) cryptographic profiles.", "Legacy 2G/3G/4G signaling nodes."],
            ["Comprehensive Operator CBOM Database", "Risk-ranked asset inventory by HNDL exposure"],
        ),
        MigrationStage(
            2, "Risk Prioritization & HNDL Triage", "3 – 6 Months",
            ["Map inventory against Infrastructure Lifecycle Categories (A, B, C, D).", "Prioritize long-lived archival data (Category C) and embedded hardware (Category D).", "Perform Harvest Now Decrypt Later threat modeling across optical transport."],
            ["Quantifying data lifespan for complex multi-service subscriber data.", "Aligning cybersecurity triage with network engineering maintenance schedules."],
            ["HNDL Risk Heatmap", "Executive Migration Priority Matrix"],
        ),
        MigrationStage(
            3, "Vendor Assessment & Procurement Mandates", "6 – 12 Months",
            ["Audit RAN, Core, and Optical hardware vendors for PQC upgrade roadmaps.", "Update RFPs and SLAs to mandate NIST FIPS 203/204/205 compliance.", "Assess vendor lock-in risks and hardware ASIC replacement timelines."],
            ["Long vendor development cycles for custom telecom ASICs and FPGAs.", "Disparity between cloud software agility and physical radio hardware lifecycles."],
            ["Quantum-Safe Procurement Policy", "Vendor Readiness Scorecards"],
        ),
        MigrationStage(
            4, "Lab Testing & Interoperability Pilots", "6 – 12 Months",
            ["Benchmark hybrid TLS 1.3 and IKEv2/IPSec in operator testbeds.", "Evaluate packet fragmentation over Ethernet MTU (1500 B) and Jumbo frames.", "Measure latency impact on 3GPP Ultra-Reliable Low-Latency (URLLC) slices."],
            ["Packet loss and jitter spikes caused by ML-KEM/ML-DSA packet expansion.", "Incompatible vendor interpretations of hybrid IETF drafts."],
            ["Lab Benchmark Report", "URLLC & RAN Impact Analysis"],
        ),
        MigrationStage(
            5, "Hybrid Suite Deployment", "12 – 24 Months",
            ["Deploy hybrid key exchange (X25519 + ML-KEM-768) across transport backbone.", "Roll out dual-signed X.509 certificate chains in 5G Core SBA.", "Enable hybrid VPNs for remote access and enterprise cloud interconnects."],
            ["Managing doubled certificate sizes (~10 KB) during massive IoT signaling storms.", "Coordinating simultaneous upgrades across dual-vendor RAN interfaces."],
            ["Hybrid Backbone Operational Release", "Dual-Root PKI Infrastructure"],
        ),
        MigrationStage(
            6, "Default PQC Production Rollout", "12 – 36 Months",
            ["Enforce pure NIST PQC suites as default across all subscriber and core traffic.", "Phase out legacy classical fallbacks (RSA-2048, ECDH P-256).", "Update eSIM provisioning profiles with ML-KEM / ML-DSA primitives."],
            ["Legacy subscriber devices (older smartphones, 10-year IoT meters) unable to upgrade.", "Managing backwards compatibility without opening downgrade attack vectors."],
            ["Full PQC Network Enforcement", "Decommissioned Legacy Crypto Report"],
        ),
        MigrationStage(
            7, "Continuous Monitoring & Crypto-Agility Governance", "Ongoing",
            ["Integrate automated cryptographic posture monitoring into SOC / NOC dashboards.", "Conduct annual red-team audits against emerging cryptanalysis.", "Maintain modular crypto-agility to swap algorithms if future flaws are found."],
            ["Maintaining organizational vigilance over a multi-decade technology evolution.", "Preventing configuration drift and unauthorized classical deployments."],
            ["Real-Time Crypto-Agility Dashboard", "Annual Quantum Security Audit"],
        ),
    ]

    @classmethod
    def get_chain(cls) -> list[MigrationStage]:
        return cls.STAGES


# ─── 3. Migration KPIs ───────────────────────────────────────────────────

@dataclass
class MigrationKPIs:
    """Real-time operational tracking metrics for quantum-safe migration."""
    inventory_discovered_pct: float   # % of network nodes with verified CBOM
    hybrid_readiness_index: float     # % of endpoints supporting hybrid PQC
    cert_replacement_hours: float     # Time required to rotate root/intermediate CAs
    pqc_latency_overhead_ms: float  # Average latency added by PQC handshakes
    hndl_exposure_score: float        # 0-100 aggregate HNDL vulnerability
    overall_health: str               # "EXCELLENT", "ON_TRACK", "AT_RISK", "CRITICAL"
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_discovered_pct": round(self.inventory_discovered_pct, 1),
            "hybrid_readiness_index": round(self.hybrid_readiness_index, 1),
            "cert_replacement_hours": round(self.cert_replacement_hours, 1),
            "pqc_latency_overhead_ms": round(self.pqc_latency_overhead_ms, 2),
            "hndl_exposure_score": round(self.hndl_exposure_score, 1),
            "overall_health": self.overall_health,
            "summary": self.summary,
        }

    @classmethod
    def evaluate(
        cls,
        discovered_pct: float,
        hybrid_pct: float,
        cert_hours: float,
        latency_ms: float,
        hndl_score: float,
    ) -> MigrationKPIs:
        if discovered_pct > 80 and hybrid_pct > 70 and hndl_score < 30:
            health = "EXCELLENT"
            sum_text = "Network migration is ahead of schedule with robust crypto-agility and low HNDL risk."
        elif discovered_pct > 50 and hybrid_pct > 40 and hndl_score < 60:
            health = "ON_TRACK"
            sum_text = "Migration is progressing steadily. Focus on expanding hybrid readiness in RAN."
        elif discovered_pct > 25 or hndl_score < 80:
            health = "AT_RISK"
            sum_text = "Migration bottlenecks detected. High HNDL exposure in archival transport links."
        else:
            health = "CRITICAL"
            sum_text = "CRITICAL VULNERABILITY: Severe HNDL risk and minimal visibility into cryptographic assets."

        return MigrationKPIs(
            inventory_discovered_pct=discovered_pct,
            hybrid_readiness_index=hybrid_pct,
            cert_replacement_hours=cert_hours,
            pqc_latency_overhead_ms=latency_ms,
            hndl_exposure_score=hndl_score,
            overall_health=health,
            summary=sum_text,
        )


# ─── 4. Sector-Specific Migration Profiles ───────────────────────────────

@dataclass
class SectorType:
    """Domain-specific risk profile and migration requirements."""
    sector_name: str
    primary_threat: str
    critical_infrastructure_layer: str
    target_pqc_suite: str
    max_allowable_latency_ms: float
    hardware_replacement_cycle_years: int
    regulatory_mandates: list[str]
    description: str

    @property
    def recommended_suite(self) -> str:
        return self.target_pqc_suite

    @property
    def data_sensitivity_shelf_life_years(self) -> int:
        shelf_lives = {
            "Telecommunications & 6G Networks": 25,
            "Banking & Financial Markets": 15,
            "Mobile Money & Financial Inclusion (M-Pesa / UPI)": 15,
            "Digital Identity, e-Passports & Smart Cards": 50,
            "Industrial Control Systems (ICS) / SCADA / OT": 35,
        }
        return shelf_lives.get(self.sector_name, 25)



class SectorRiskMatrix:
    """Provides tailored migration guidelines across critical industry sectors."""

    SECTORS: dict[str, SectorType] = {
        "Telecommunications": SectorType(
            sector_name="Telecommunications & 6G Networks",
            primary_threat="Harvest Now Decrypt Later (HNDL) on backbone fiber and long-lived VPNs; Shor attacks on 5G AKA and PKI.",
            critical_infrastructure_layer="5G Core Service-Based Architecture (SBA), Open RAN transport, eSIM provisioning, optical backbone.",
            target_pqc_suite="Hybrid X25519 + ML-KEM-768 for session keys; ML-DSA-65 for X.509 PKI.",
            max_allowable_latency_ms=10.0, # URLLC slice constraint
            hardware_replacement_cycle_years=10,
            regulatory_mandates=["GSMA PQC Task Force Guidelines", "3GPP SA3 Rel-19/20 PQC Study", "ETSI TC CYBER ISG QSC", "NSA CNSA 2.0 (2025-2035)"],
            description="Core communication infrastructure supporting national economies and all other critical sectors.",
        ),
        "Banking_Finance": SectorType(
            sector_name="Banking & Financial Markets",
            primary_threat="Retroactive decryption of high-value interbank wire transfers (SWIFT), algorithmic trading logs, and customer ledgers.",
            critical_infrastructure_layer="Interbank payment gateways, ATM networks, TLS 1.3 web banking, hardware security modules (HSMs).",
            target_pqc_suite="Hybrid ECDH-P384 + ML-KEM-1024; ML-DSA-87 for root trust anchors.",
            max_allowable_latency_ms=5.0,  # High-frequency trading constraint
            hardware_replacement_cycle_years=5,
            regulatory_mandates=["PCI DSS v4.x PQC Roadmap", "ECB & Federal Reserve PQC Guidance", "ISO/IEC 27001 Quantum-Safe Annex"],
            description="High-velocity financial transaction networks requiring zero-downtime cryptographic rotation.",
        ),
        "Mobile_Money": SectorType(
            sector_name="Mobile Money & Financial Inclusion (M-Pesa / UPI)",
            primary_threat="Mass forgery of digital signatures on USSD/SMS/app transactions and compromise of central clearing ledgers.",
            critical_infrastructure_layer="SIM Toolkit (STK) smart card applets, USSD signaling gateways, merchant POS APIs.",
            target_pqc_suite="ML-KEM-512 for constrained SIM exchange; SLH-DSA-SHA2-128s for hardware root-of-trust.",
            max_allowable_latency_ms=500.0, # Cellular signaling constraint
            hardware_replacement_cycle_years=12,
            regulatory_mandates=["GSMA Mobile Money Security Standard", "National Central Bank Fintech Regulations"],
            description="Critical financial lifeline in emerging markets operating on constrained cellular handsets and 2G/3G/4G signaling.",
        ),
        "Digital_Identity_SmartCards": SectorType(
            sector_name="Digital Identity, e-Passports & Smart Cards",
            primary_threat="Cloning of national e-IDs, e-Passports, and cryptographic biometric credentials via Shor's algorithm.",
            critical_infrastructure_layer="ISO/IEC 7816 smart card chips, NFC contactless interfaces, national identity registries.",
            target_pqc_suite="ML-DSA-44 or Falcon-512 (due to severe APDU buffer and chip RAM limits).",
            max_allowable_latency_ms=250.0, # Contactless gate tap constraint
            hardware_replacement_cycle_years=15,
            regulatory_mandates=["ICAO Doc 9303 e-Passport PQC Roadmap", "eIDAS 2.0 Quantum-Safe Framework", "NIST SP 800-63 Digital Identity Guidelines"],
            description="Long-lived physical and digital identity credentials with extreme memory and processing constraints.",
        ),
        "ICS_SCADA_OT": SectorType(
            sector_name="Industrial Control Systems (ICS) / SCADA / OT",
            primary_threat="Quantum forgery of command authentication leading to unauthorized physical control of power grids, pipelines, and manufacturing.",
            critical_infrastructure_layer="Modbus/DNP3/IEC 61850 over IPSec gateways, PLC firmware updates, RTU telemetry.",
            target_pqc_suite="ML-KEM-512 for low-power sensors; SLH-DSA-SHA2-128s for immutable firmware signing.",
            max_allowable_latency_ms=20.0,  # Grid protection tripping time
            hardware_replacement_cycle_years=20,
            regulatory_mandates=["NERC CIP Quantum-Safe Guidelines", "IEC 62443 Industrial Cybersecurity", "ISA/IEC OT Security Standards"],
            description="Ultra-long lifecycle industrial hardware where downtime or latency spikes cause catastrophic physical damage.",
        ),
    }

    @classmethod
    def get_profile(cls, sector_key: str) -> SectorType:
        aliases = {
            "Government_Defense": "Digital_Identity_SmartCards",
            "Healthcare_MedTech": "Mobile_Money",
            "Critical_Infrastructure": "ICS_SCADA_OT",
        }
        sector_key = aliases.get(sector_key, sector_key)
        if sector_key not in cls.SECTORS:
            raise KeyError(f"Sector '{sector_key}' not found. Available: {list(cls.SECTORS.keys())}")
        return cls.SECTORS[sector_key]

    @classmethod
    def list_all(cls) -> dict[str, SectorType]:
        return cls.SECTORS
