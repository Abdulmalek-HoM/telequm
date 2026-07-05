"""
Hardware Intelligence Hub — Quantum Backend Comparison
=======================================================

Dashboard tab for comparing quantum hardware backends:
- IBM Quantum (superconducting)
- IonQ (trapped ion)
- Quantinuum (trapped ion)
- Simulator baselines

Displays specs, estimated capabilities, and benchmark
projections for telecom optimization workloads.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots  # noqa: F401
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from dashboard.utils.plot_helpers import PALETTE

# ─── Hardware Database ───────────────────────────────────────────

BACKENDS = {
    "IBM Eagle (127Q)": {
        "provider": "IBM Quantum",
        "type": "Superconducting",
        "qubits": 127,
        "gate_fidelity_1q": 0.9996,
        "gate_fidelity_2q": 0.99,
        "t1_us": 300,
        "t2_us": 200,
        "connectivity": "Heavy-hex",
        "max_circuit_depth": 300,
        "access": "Cloud (IBM Quantum Network)",
        "color": PALETTE["primary"],
    },
    "IBM Heron (156Q)": {
        "provider": "IBM Quantum",
        "type": "Superconducting",
        "qubits": 156,
        "gate_fidelity_1q": 0.9998,
        "gate_fidelity_2q": 0.995,
        "t1_us": 400,
        "t2_us": 300,
        "connectivity": "Heavy-hex",
        "max_circuit_depth": 500,
        "access": "Cloud (IBM Quantum Network)",
        "color": "#4F8BFF",
    },
    "IonQ Forte (36Q)": {
        "provider": "IonQ",
        "type": "Trapped Ion",
        "qubits": 36,
        "gate_fidelity_1q": 0.9998,
        "gate_fidelity_2q": 0.995,
        "t1_us": 1e7,  # seconds-scale
        "t2_us": 1e6,
        "connectivity": "All-to-all",
        "max_circuit_depth": 1000,
        "access": "Cloud (AWS Braket, Azure Quantum)",
        "color": PALETTE["accent"],
    },
    "Quantinuum H2 (56Q)": {
        "provider": "Quantinuum",
        "type": "Trapped Ion",
        "qubits": 56,
        "gate_fidelity_1q": 0.99998,
        "gate_fidelity_2q": 0.998,
        "t1_us": 1e7,
        "t2_us": 1e6,
        "connectivity": "All-to-all",
        "max_circuit_depth": 2000,
        "access": "Cloud (Azure Quantum)",
        "color": PALETTE["secondary"],
    },
    "Simulator (Qiskit Aer)": {
        "provider": "Local",
        "type": "Classical Simulation",
        "qubits": 32,
        "gate_fidelity_1q": 1.0,
        "gate_fidelity_2q": 1.0,
        "t1_us": float("inf"),
        "t2_us": float("inf"),
        "connectivity": "All-to-all",
        "max_circuit_depth": 10000,
        "access": "Local",
        "color": PALETTE["warning"],
    },
}


def render():
    """Render the Hardware Intelligence Hub tab."""
    st.header("🖥️ Hardware Intelligence Hub")
    st.caption("Compare quantum computers and analyze telecom infrastructure PQC performance")

    hw_mode = st.radio(
        "Select Hardware Analysis Domain",
        ["⚛️ Quantum Computers & FTQC Roadmap", "🛡️ Telecom Infrastructure PQC Benchmarks"],
        horizontal=True,
        key="hw_domain_sel",
    )
    st.divider()

    if hw_mode == "⚛️ Quantum Computers & FTQC Roadmap":
        _render_quantum_hardware()
    else:
        _render_pqc_telecom_hardware()


def _render_quantum_hardware():
    """Render quantum hardware backends and FTQC roadmap."""
    # ── Backend selector ─────────────────────────────────────────
    selected = st.multiselect(
        "Select backends to compare",
        list(BACKENDS.keys()),
        default=list(BACKENDS.keys())[:3],
        key="hw_backends",
    )

    if not selected:
        st.info("Select at least one backend to display.")
        return

    # ── Specs Table ──────────────────────────────────────────────
    st.subheader("Hardware Specifications")
    _render_specs_table(selected)

    # ── Radar Chart ──────────────────────────────────────────────
    if HAS_PLOTLY and len(selected) >= 2:
        st.subheader("Capability Radar")
        st.plotly_chart(_radar_chart(selected), use_container_width=True)

    # ── Telecom Workload Projection ──────────────────────────────
    st.subheader("Telecom Workload Projection")
    _render_workload_projection(selected)

    # ── Recommendations ──────────────────────────────────────────
    st.subheader("💡 TELEQUM Recommendations")
    _render_recommendations()

    # ── FTQC Roadmap ─────────────────────────────────────────────
    st.divider()
    st.subheader("🗺️ Fault-Tolerant Quantum Computing (FTQC) Roadmap (2026–2035+)")
    st.markdown("""
    The transition from Noisy Intermediate-Scale Quantum (NISQ) to Fault-Tolerant Quantum Computing (FTQC) determines exactly when Shor's algorithm becomes a viable threat to telecommunications networks.
    """)

    ftqc_data = [
        {"Year": "2026", "Phase": "NISQ Era", "Physical Qubits": "~1,000 - 3,000", "Logical Qubits": "0 - 10", "Telecom Impact": "No threat to RSA/ECC. Used for small QAOA/VQE radio resource optimization."},
        {"Year": "2028", "Phase": "Early Error Correction", "Physical Qubits": "~10,000", "Logical Qubits": "~50 - 100", "Telecom Impact": "Can simulate small molecules and complex network graphs. RSA-2048 still secure."},
        {"Year": "2030", "Phase": "Mid-Scale FTQC", "Physical Qubits": "~100,000", "Logical Qubits": "~500 - 1,000", "Telecom Impact": "RSA-1024 vulnerable. Operators must have completed Level 3 AQC PQC migration across Core and RAN."},
        {"Year": "2033+", "Phase": "Full FTQC / CRQC", "Physical Qubits": "~1,000,000+", "Logical Qubits": "~4,100+", "Telecom Impact": "🚨 **Shor's Threshold Reached.** RSA-2048 and ECC-256/384 completely broken in real-time."},
    ]
    import pandas as pd
    st.dataframe(pd.DataFrame(ftqc_data), use_container_width=True, hide_index=True)


def _render_pqc_telecom_hardware():
    """Render telecom infrastructure PQC performance benchmarks."""
    st.subheader("🛡️ Telecom Infrastructure PQC Performance Benchmarks")
    st.markdown("""
    Running Post-Quantum Cryptography (NIST FIPS 203/204) introduces different computational overheads across the telecommunications infrastructure tier. Explore how key encapsulation and digital signature verification impact baseband units, IoT edge devices, core HSMs, and optical encryptors.
    """)

    # Hardware tiers database
    tiers_data = {
        "5G RAN Baseband (Intel Xeon AVX-512)": {
            "role": "DU / CU Baseband Unit processing MACsec & RRC signaling",
            "kem_encap_ms": 0.03, "kem_decap_ms": 0.03,
            "dsa_sign_ms": 0.15, "dsa_verify_ms": 0.04,
            "tps_capacity": 32000, "memory_kb": 128,
            "notes": "AVX-512 vectorization provides 4x speedup for polynomial multiplication.",
        },
        "Edge / IoT UE Baseband (ARM Cortex-A53)": {
            "role": "Cellular IoT / Smart Meter / UE SIM processing AKA & NAS",
            "kem_encap_ms": 1.20, "kem_decap_ms": 1.45,
            "dsa_sign_ms": 12.50, "dsa_verify_ms": 3.10,
            "tps_capacity": 85, "memory_kb": 64,
            "notes": "Heavy signature generation overhead. Recommend FALCON or ML-KEM-512 for constrained devices.",
        },
        "Core HSM (Thales / Marvell PCIe ACC)": {
            "role": "Core Network Authentication Server (AUSF / UDM / CA)",
            "kem_encap_ms": 0.005, "kem_decap_ms": 0.005,
            "dsa_sign_ms": 0.02, "dsa_verify_ms": 0.008,
            "tps_capacity": 150000, "memory_kb": 4096,
            "notes": "Dedicated FPGA/PCIe hardware acceleration required to prevent core signaling bottlenecks.",
        },
        "Optical Transport (400G DWDM Line Card)": {
            "role": "Layer 1 Optical Encryptor processing MACsec / OTN",
            "kem_encap_ms": 0.01, "kem_decap_ms": 0.01,
            "dsa_sign_ms": 0.05, "dsa_verify_ms": 0.02,
            "tps_capacity": 80000, "memory_kb": 512,
            "notes": "Requires ultra-low latency (<0.1 ms) session key derivation at line rate.",
        },
    }

    c1, c2 = st.columns([1, 1])
    with c1:
        selected_tier = st.selectbox("Select Telecom Hardware Platform", list(tiers_data.keys()), key="pqc_hw_tier")
    with c2:
        selected_algo = st.selectbox("Select PQC Algorithm Profile", ["ML-KEM-768 (Key Exchange)", "ML-DSA-65 (Digital Signature)", "Hybrid (ML-KEM + ML-DSA)"], key="pqc_hw_algo")

    tier = tiers_data[selected_tier]
    st.markdown(f"**Role & Deployment:** `{tier['role']}`")
    st.info(f"📌 **Hardware Optimization Note:** {tier['notes']}")

    m1, m2, m3, m4 = st.columns(4)
    if "KEM" in selected_algo:
        m1.metric("Encap Latency", f"{tier['kem_encap_ms']} ms")
        m2.metric("Decap Latency", f"{tier['kem_decap_ms']} ms")
    elif "DSA" in selected_algo:
        m1.metric("Sign Latency", f"{tier['dsa_sign_ms']} ms")
        m2.metric("Verify Latency", f"{tier['dsa_verify_ms']} ms")
    else:
        m1.metric("Combined Latency", f"{tier['kem_encap_ms'] + tier['dsa_sign_ms']:.2f} ms")
        m2.metric("Verify + Decap", f"{tier['kem_decap_ms'] + tier['dsa_verify_ms']:.2f} ms")

    m3.metric("Max Throughput Capacity", f"{tier['tps_capacity']:,} TPS")
    m4.metric("Memory Footprint", f"{tier['memory_kb']} KB")

    if HAS_PLOTLY:
        st.subheader("📊 Cross-Platform PQC Latency Comparison")
        fig = go.Figure()
        tiers_names = list(tiers_data.keys())
        enc_times = [tiers_data[t]["kem_encap_ms"] for t in tiers_names]
        sig_times = [tiers_data[t]["dsa_sign_ms"] for t in tiers_names]

        fig.add_trace(go.Bar(name="ML-KEM-768 Encap (ms)", x=tiers_names, y=enc_times, marker_color=PALETTE["primary"]))
        fig.add_trace(go.Bar(name="ML-DSA-65 Sign (ms)", x=tiers_names, y=sig_times, marker_color=PALETTE["secondary"]))

        fig.update_layout(
            barmode="group",
            yaxis_type="log",
            yaxis_title="Latency (ms) [Log Scale]",
            xaxis_title="Telecom Hardware Tier",
            plot_bgcolor=PALETTE["bg"],
            paper_bgcolor=PALETTE["card"],
            font={"color": PALETTE["text"]},
            legend={"bgcolor": PALETTE["card"]},
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Comprehensive Hardware Tier Summary")
    import pandas as pd
    summary_rows = []
    for t_name, t_val in tiers_data.items():
        summary_rows.append({
            "Hardware Platform": t_name,
            "KEM Encap (ms)": t_val["kem_encap_ms"],
            "KEM Decap (ms)": t_val["kem_decap_ms"],
            "DSA Sign (ms)": t_val["dsa_sign_ms"],
            "DSA Verify (ms)": t_val["dsa_verify_ms"],
            "Max TPS": f"{t_val['tps_capacity']:,}",
            "RAM (KB)": t_val["memory_kb"],
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


def _render_specs_table(selected: list):
    import pandas as pd
    rows = []
    for name in selected:
        hw = BACKENDS[name]
        rows.append({
            "Backend": name,
            "Type": hw["type"],
            "Qubits": hw["qubits"],
            "1Q Fidelity": f"{hw['gate_fidelity_1q']:.4f}",
            "2Q Fidelity": f"{hw['gate_fidelity_2q']:.4f}",
            "Connectivity": hw["connectivity"],
            "Max Depth": hw["max_circuit_depth"],
            "Access": hw["access"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _radar_chart(selected: list) -> go.Figure:
    categories = ["Qubits", "2Q Fidelity", "Coherence", "Connectivity", "Max Depth"]

    fig = go.Figure()
    for name in selected:
        hw = BACKENDS[name]
        # Normalize to 0-1 scale
        vals = [
            min(hw["qubits"] / 200, 1.0),
            hw["gate_fidelity_2q"],
            min(hw["t2_us"] / 1e6, 1.0),
            1.0 if hw["connectivity"] == "All-to-all" else 0.5,
            min(hw["max_circuit_depth"] / 2000, 1.0),
        ]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=name,
            line={"color": hw["color"], "width": 2},
            opacity=0.7,
        ))

    fig.update_layout(
        polar={
            "radialaxis": {"visible": True, "range": [0, 1],
                            "gridcolor": PALETTE["grid"]},
            "angularaxis": {"gridcolor": PALETTE["grid"]},
            "bgcolor": PALETTE["bg"],
        },
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=450,
    )
    return fig


def _render_workload_projection(selected: list):
    st.markdown("""
    Estimated maximum problem size for QAOA ($p=2$) resource allocation:
    """)

    for name in selected:
        hw = BACKENDS[name]
        n_q = hw["qubits"]
        fid_2q = hw["gate_fidelity_2q"]
        max_depth = hw["max_circuit_depth"]

        # Estimate: QAOA p=2 needs ~4n gates, n = UEs × BSs
        max_vars = min(n_q, max_depth // 4)
        # Success probability ≈ fidelity^(num_2q_gates)
        est_gates = max_vars * 4
        success_prob = fid_2q ** est_gates

        max_ue = int(np.sqrt(max_vars))
        max_bs = max_ue

        col1, col2, col3 = st.columns(3)
        col1.metric(f"{name}", f"{max_vars} qubits")
        col2.metric("Max Problem", f"{max_ue} UE × {max_bs} BS")
        col3.metric("Est. Success", f"{success_prob:.2%}")


def _render_recommendations():
    st.markdown("""
    | Scenario | Recommended Backend | Reason |
    |----------|-------------------|--------|
    | **Research / prototyping** | Qiskit Aer Simulator | Fast iteration, perfect fidelity |
    | **Small problems (≤16 vars)** | IBM Eagle/Heron | Accessible, good fidelity |
    | **High-fidelity (≤36 vars)** | IonQ Forte | All-to-all, highest fidelity |
    | **Production pilot** | Quantinuum H2 | Best 2Q gates, mid-scale |
    | **Scaling study** | Hybrid: classical + IBM | Classical for large, quantum for sub-problems |
    """)
