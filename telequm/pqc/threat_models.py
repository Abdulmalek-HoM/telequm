"""
Quantum Threat & Harvest Now Decrypt Later (HNDL) Estimators
============================================================

Provides risk scoring models for Harvest Now Decrypt Later (HNDL) attacks
across telecom data types, and computes physical/logical qubit requirements
and execution times for Shor's and Grover's algorithms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class HNDLRiskScore:
    """Risk assessment for Harvest Now Decrypt Later exposure."""
    data_type: str
    data_sensitivity_years: int
    estimated_crqc_arrival_years: int
    interception_probability: float
    exposure_gap_years: int
    risk_score: float  # 0 to 100 scale
    urgency_level: str # "CRITICAL", "HIGH", "MODERATE", "LOW"
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_type": self.data_type,
            "data_sensitivity_years": self.data_sensitivity_years,
            "estimated_crqc_arrival_years": self.estimated_crqc_arrival_years,
            "interception_probability": self.interception_probability,
            "exposure_gap_years": self.exposure_gap_years,
            "risk_score": round(self.risk_score, 1),
            "urgency_level": self.urgency_level,
            "recommendation": self.recommendation,
        }


class HNDLCalculator:
    """Calculates Harvest Now Decrypt Later risk based on Mosca's Theorem."""

    # Typical telecom migration lead time in years (procurement, lab testing, rollout)
    DEFAULT_MIGRATION_LEAD_YEARS = 3

    @classmethod
    def calculate_score(
        cls,
        data_sensitivity_years: int,
        crqc_years: int,
        interception_prob: float,
        data_type: str = "Telecom Transport Backbone",
        migration_lead_years: int = DEFAULT_MIGRATION_LEAD_YEARS,
    ) -> HNDLRiskScore:
        """
        Evaluate HNDL risk using Mosca's Theorem:
        If X (sensitivity lifespan) + Y (migration lead time) > Z (time to CRQC),
        then systems are already vulnerable to retroactive decryption.
        """
        # Exposure gap = (X + Y) - Z
        total_required_years = data_sensitivity_years + migration_lead_years
        exposure_gap = total_required_years - crqc_years

        # Calculate normalized score (0 to 100)
        # 50% weighted on exposure time gap, 50% on interception probability
        time_factor = min(50.0, max(0.0, (exposure_gap / 15.0) * 50.0)) if exposure_gap > 0 else 0.0
        prob_factor = interception_prob * 50.0
        score = min(100.0, time_factor + prob_factor)

        if exposure_gap > 5 or score >= 75.0:
            urgency = "CRITICAL"
            rec = (
                "IMMEDIATE ACTION REQUIRED: Data lifespan exceeds quantum safety horizon. "
                "Deploy hybrid key exchange (e.g., X25519 + ML-KEM-768) immediately across all tunnels."
            )
        elif exposure_gap > 0 or score >= 50.0:
            urgency = "HIGH"
            rec = (
                "HIGH RISK: Begin migration pilots and vendor procurement mandates within 6 months. "
                "Prioritize long-lived VPN and optical transport links."
            )
        elif exposure_gap > -3 or score >= 25.0:
            urgency = "MODERATE"
            rec = (
                "MODERATE RISK: Inventory existing cryptographic assets and enforce crypto-agility "
                "requirements in upcoming hardware/software lifecycles."
            )
        else:
            urgency = "LOW"
            rec = (
                "LOW RISK: Continue monitoring NIST/ETSI standards and maintain automated "
                "cryptographic inventory."
            )

        return HNDLRiskScore(
            data_type=data_type,
            data_sensitivity_years=data_sensitivity_years,
            estimated_crqc_arrival_years=crqc_years,
            interception_probability=interception_prob,
            exposure_gap_years=exposure_gap,
            risk_score=score,
            urgency_level=urgency,
            recommendation=rec,
        )


@dataclass
class QuantumResourceEstimate:
    """Estimated quantum computer resources required to break a cryptographic scheme."""
    target_algorithm: str
    attack_algorithm: str
    logical_qubits_required: int
    physical_qubits_required: int
    surface_code_distance: int
    estimated_runtime_hours: float
    t_gates_count: float
    quantum_safe_status: str # "VULNERABLE", "SAFE", "WEAKENED"
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_algorithm": self.target_algorithm,
            "attack_algorithm": self.attack_algorithm,
            "logical_qubits_required": f"{self.logical_qubits_required:,}",
            "physical_qubits_required": f"{self.physical_qubits_required:,}",
            "surface_code_distance": self.surface_code_distance,
            "estimated_runtime_hours": round(self.estimated_runtime_hours, 2),
            "t_gates_count": f"{self.t_gates_count:.2e}",
            "quantum_safe_status": self.quantum_safe_status,
            "explanation": self.explanation,
        }


class ShorGroverEstimator:
    """Estimates physical and logical qubit requirements for quantum attacks."""

    @classmethod
    def estimate_resources(
        cls,
        target_algorithm: str,
        key_size_bits: int,
        error_rate: float = 0.001,
        cycle_time_us: float = 1.0,
    ) -> QuantumResourceEstimate:
        """
        Estimate fault-tolerant quantum computing (FTQC) resources required
        to attack a specific cryptographic scheme.
        """
        algo_upper = target_algorithm.upper()

        if "RSA" in algo_upper:
            # Shor's Algorithm for integer factorization
            # Logical qubits ≈ 2 * N + 3 (with Gidney-Ekera optimizations)
            log_q = 2 * key_size_bits + 3
            # Surface code distance d ≈ ceil(log10(1000 * N^3)) * 2 + 1
            d = max(17, int(math.ceil(math.log10(1000 * (key_size_bits ** 3)))) * 2 + 1)
            # Physical qubits ≈ 2 * d^2 * log_q (standard surface code patch)
            phys_q = int(2 * (d ** 2) * log_q)
            # T-gate count ≈ 0.3 * N^3
            t_gates = 0.3 * (key_size_bits ** 3)
            # Runtime in hours (assuming cycle_time_us per surface code cycle)
            runtime_hr = (t_gates * cycle_time_us * 1e-6) / 3600.0
            status = "VULNERABLE"
            expl = (
                f"Shor's algorithm factors {target_algorithm} in polynomial time. "
                f"Requires ~{log_q:,} logical qubits and ~{phys_q:,} physical qubits under surface code QEC."
            )
            attack = "Shor's Algorithm (Integer Factorization)"

        elif "ECC" in algo_upper or "ECDH" in algo_upper or "ECDSA" in algo_upper or "P-256" in algo_upper or "P-384" in algo_upper or "X25519" in algo_upper:
            # Shor's Algorithm for Discrete Logarithms over Elliptic Curves
            # Logical qubits ≈ 2.5 * N (e.g. ~640 for P-256)
            log_q = int(2.5 * key_size_bits)
            d = max(15, int(math.ceil(math.log10(500 * (key_size_bits ** 3)))) * 2 + 1)
            phys_q = int(2 * (d ** 2) * log_q)
            # ECC requires more complex arithmetic per step than RSA -> ~9 * N^3 T-gates
            t_gates = 9.0 * (key_size_bits ** 3)
            runtime_hr = (t_gates * cycle_time_us * 1e-6) / 3600.0
            status = "VULNERABLE"
            expl = (
                f"Shor's algorithm solves elliptic curve discrete logarithms in polynomial time. "
                f"Requires fewer qubits (~{log_q:,} logical) than RSA, making ECC easier to break!"
            )
            attack = "Shor's Algorithm (Discrete Logarithm)"

        elif "AES" in algo_upper or "SHA" in algo_upper or "SYMMETRIC" in algo_upper:
            # Grover's Algorithm for unstructured search
            # Quadratic speedup: effective security reduced from N bits to N/2 bits
            log_q = key_size_bits * 2 + 100
            d = 21
            phys_q = int(2 * (d ** 2) * log_q)
            # T-gates ≈ 2^(N/2) * gate_depth
            t_gates = float(2 ** (key_size_bits // 2)) * 1000.0

            if key_size_bits >= 256:
                runtime_hr = float("inf")
                status = "SAFE"
                expl = (
                    f"Grover's algorithm reduces {target_algorithm} effective security to {key_size_bits // 2} bits. "
                    f"However, 2^{key_size_bits // 2} operations remains physically infeasible even for quantum supercomputers."
                )
            else:
                runtime_hr = (t_gates * cycle_time_us * 1e-6) / 3600.0
                status = "WEAKENED"
                expl = (
                    f"Grover's algorithm halves effective key length to {key_size_bits // 2} bits. "
                    f"Transition to AES-256 / SHA-384 is required to restore full quantum resistance."
                )
            attack = "Grover's Algorithm (Quadratic Search Speedup)"

        else:
            # PQC Lattice or Code-Based schemes
            log_q = 50000  # Prohibitive
            d = 41
            phys_q = int(2 * (d ** 2) * log_q)
            t_gates = float(2 ** 128)
            runtime_hr = float("inf")
            status = "SAFE"
            expl = (
                f"{target_algorithm} is resistant to both Shor's and Grover's algorithms. "
                f"No known quantum algorithm provides exponential or prohibitive polynomial speedup."
            )
            attack = "No Known Efficient Quantum Attack"

        return QuantumResourceEstimate(
            target_algorithm=target_algorithm,
            attack_algorithm=attack,
            logical_qubits_required=log_q,
            physical_qubits_required=phys_q,
            surface_code_distance=d,
            estimated_runtime_hours=runtime_hr,
            t_gates_count=t_gates,
            quantum_safe_status=status,
            explanation=expl,
        )
