"""
Unit Tests for TELEQUM PQC & Security Module
============================================

Verifies cryptographic sizing models, protocol handshake simulators,
HNDL/Shor threat calculators, and AQC Whitepaper migration frameworks.
"""

import pytest
from telequm.pqc import (
    PQCAlgorithm,
    AlgorithmDatabase,
    get_algorithm,
    list_algorithms,
    compare_algorithms,
    ProtocolSimulator,
    HandshakeResult,
    HNDLCalculator,
    ShorGroverEstimator,
    MaturityLadder,
    MigrationExecutionChain,
    MigrationKPIs,
    SectorRiskMatrix,
)


def test_algorithm_database_and_retrieval():
    """Test retrieval and properties of NIST PQC standards and legacy schemes."""
    kem = get_algorithm("ML-KEM-768")
    assert kem.family == "Lattice-Based"
    assert kem.security_level == 3
    assert kem.public_key_bytes == 1184
    assert kem.ciphertext_bytes == 1088
    assert kem.total_handshake_bytes == 1184 + 1088

    sig = get_algorithm("ML-DSA-65")
    assert sig.type == "Signature"
    assert sig.signature_bytes == 3309

    hash_sig = get_algorithm("SLH-DSA-SHA2-128s")
    assert hash_sig.family == "Hash-Based"
    assert hash_sig.public_key_bytes == 32
    assert hash_sig.signature_bytes == 7856

    hybrid = get_algorithm("X25519+ML-KEM-768")
    assert hybrid.family == "Hybrid"
    assert hybrid.public_key_bytes == 32 + 1184

    with pytest.raises(KeyError):
        get_algorithm("NonExistent-Algo-999")


def test_list_and_compare_algorithms():
    """Test filtering and comparison tables."""
    lattice_kems = list_algorithms(family="Lattice-Based", type_filter="KEM")
    assert len(lattice_kems) >= 3
    assert all(a.family == "Lattice-Based" and a.type == "KEM" for a in lattice_kems)

    high_sec = list_algorithms(min_level=5)
    assert all(a.security_level == 5 for a in high_sec)

    comp = compare_algorithms(["ML-KEM-768", "RSA-2048"])
    assert len(comp) == 2
    assert comp[0]["name"] == "ML-KEM-768"
    assert comp[1]["security_level"] == 0


def test_protocol_simulator_tls():
    """Test TLS 1.3 handshake simulation over 5G RAN."""
    res = ProtocolSimulator.simulate_handshake(
        protocol="TLS_1_3",
        link_type="5G_UMa_RAN",
        crypto_suite="Hybrid",
        target_hw="x86_server",
    )
    assert isinstance(res, HandshakeResult)
    assert res.protocol == "TLS_1_3"
    assert res.crypto_suite == "Hybrid"
    assert res.cert_chain_bytes == 10000
    assert len(res.steps) == 3
    assert res.total_handshake_bytes == res.client_to_server_bytes + res.server_to_client_bytes
    assert res.total_latency_ms > res.network_transmission_ms
    assert isinstance(res.to_dict(), dict)


def test_protocol_simulator_ipsec_fragmentation():
    """Test IPSec IKEv2 fragmentation detection over standard Ethernet MTU."""
    res_ran = ProtocolSimulator.simulate_handshake(
        protocol="IPSec_IKEv2",
        link_type="5G_UMa_RAN",  # MTU 1500
        crypto_suite="Pure_PQC", # ML-KEM-768 + ML-DSA-65 + 11KB certs
    )
    assert res_ran.fragmentation_risk is True
    assert res_ran.total_fragments > len(res_ran.steps)

    res_jumbo = ProtocolSimulator.simulate_handshake(
        protocol="IPSec_IKEv2",
        link_type="Optical_Fiber_Core", # MTU 9000
        crypto_suite="Classical",
    )
    assert res_jumbo.fragmentation_risk is False


def test_protocol_simulator_5g_aka_and_macsec():
    """Test 5G AKA and MACsec protocol simulations."""
    res_aka = ProtocolSimulator.simulate_handshake("5G_AKA", "5G_UMa_RAN", "Hybrid", "arm_cortex_m4")
    assert res_aka.crypto_processing_ms > 0
    assert len(res_aka.steps) == 3

    res_macsec = ProtocolSimulator.simulate_handshake("MACsec", "Optical_Fiber_Core", "Pure_PQC")
    assert len(res_macsec.steps) == 2


def test_hndl_calculator():
    """Test Harvest Now Decrypt Later risk scoring equations."""
    crit = HNDLCalculator.calculate_score(
        data_sensitivity_years=25,
        crqc_years=10,
        interception_prob=0.9,
    )
    assert crit.urgency_level == "CRITICAL"
    assert crit.risk_score > 70.0
    assert crit.exposure_gap_years > 0

    low = HNDLCalculator.calculate_score(
        data_sensitivity_years=2,
        crqc_years=30,
        interception_prob=0.1,
    )
    assert low.urgency_level == "LOW"
    assert low.risk_score < 30.0
    assert low.exposure_gap_years < 0


def test_shor_grover_estimator():
    """Test quantum resource estimation for Shor's and Grover's algorithms."""
    rsa_est = ShorGroverEstimator.estimate_resources("RSA-2048", 2048)
    assert rsa_est.quantum_safe_status == "VULNERABLE"
    assert rsa_est.logical_qubits_required > 4000
    assert rsa_est.physical_qubits_required > 1_000_000
    assert "Shor" in rsa_est.attack_algorithm

    ecc_est = ShorGroverEstimator.estimate_resources("ECDH-P256", 256)
    assert ecc_est.quantum_safe_status == "VULNERABLE"
    assert ecc_est.logical_qubits_required < rsa_est.logical_qubits_required # ECC takes fewer qubits than RSA!

    aes128 = ShorGroverEstimator.estimate_resources("AES-128", 128)
    assert aes128.quantum_safe_status == "WEAKENED"
    assert "Grover" in aes128.attack_algorithm

    aes256 = ShorGroverEstimator.estimate_resources("AES-256", 256)
    assert aes256.quantum_safe_status == "SAFE"

    ml_kem = ShorGroverEstimator.estimate_resources("ML-KEM-768", 768)
    assert ml_kem.quantum_safe_status == "SAFE"


def test_maturity_ladder():
    """Test operational maturity ladder evaluation."""
    low_mat = MaturityLadder.evaluate(10, 15, 10, 20, 10)
    assert low_mat.level == 0
    assert "Level 0" in low_mat.level_name
    assert len(low_mat.next_steps) > 0

    mid_mat = MaturityLadder.evaluate(50, 60, 55, 50, 50)
    assert mid_mat.level == 2

    high_mat = MaturityLadder.evaluate(95, 95, 95, 90, 95)
    assert high_mat.level == 4


def test_migration_execution_chain():
    """Test the 7-stage migration workflow."""
    chain = MigrationExecutionChain.get_chain()
    assert len(chain) == 7
    assert chain[0].stage_id == 1
    assert "Discovery" in chain[0].name
    assert chain[-1].stage_id == 7


def test_migration_kpis():
    """Test Migration KPIs evaluation."""
    kpi_exc = MigrationKPIs.evaluate(90.0, 85.0, 4.0, 8.5, 15.0)
    assert kpi_exc.overall_health == "EXCELLENT"

    kpi_crit = MigrationKPIs.evaluate(10.0, 10.0, 120.0, 50.0, 90.0)
    assert kpi_crit.overall_health == "CRITICAL"


def test_sector_risk_matrix():
    """Test sector risk profiles."""
    telecom = SectorRiskMatrix.get_profile("Telecommunications")
    assert telecom.max_allowable_latency_ms == 10.0
    assert len(telecom.regulatory_mandates) >= 3

    banking = SectorRiskMatrix.get_profile("Banking_Finance")
    assert banking.hardware_replacement_cycle_years == 5

    with pytest.raises(KeyError):
        SectorRiskMatrix.get_profile("NonExistentSector")


def test_plot_helpers():
    """Verify that all PQC visualization helpers generate valid Plotly figures."""
    from dashboard.utils.plot_helpers import (
        plot_protocol_handshake_sequence,
        plot_packet_fragmentation,
        plot_hndl_risk_heatmap,
        plot_maturity_radar,
        plot_qubit_scaling_curve,
    )
    import numpy as np

    res = ProtocolSimulator.simulate_handshake("TLS_1_3", "5G_UMa_RAN", "Hybrid")
    fig1 = plot_protocol_handshake_sequence(res.steps)
    assert fig1 is not None

    suite_dict = {
        "Classical": ProtocolSimulator.simulate_handshake("TLS_1_3", "5G_UMa_RAN", "Classical").to_dict(),
        "Hybrid": res.to_dict(),
    }
    fig2 = plot_packet_fragmentation(suite_dict)
    assert fig2 is not None

    mat = np.random.uniform(0, 100, (4, 4))
    fig3 = plot_hndl_risk_heatmap(mat, ["Cat A", "Cat B", "Cat C", "Cat D"], ["5 yr", "10 yr", "25 yr", "50 yr"])
    assert fig3 is not None

    fig4 = plot_maturity_radar({"Governance": 50, "Discovery": 60, "Architecture": 40, "Operations": 70, "Procurement": 30})
    assert fig4 is not None

    fig5 = plot_qubit_scaling_curve()
    assert fig5 is not None
