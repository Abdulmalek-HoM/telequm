"""
Education Hub — Comprehensive Quantum-Telecom Learning Platform
================================================================

7 interactive subtabs:
1. Quantum 101          — Bloch sphere, gates, entanglement
2. Memory & Complexity  — Big-O calculator, RAM estimation per algorithm
3. Algorithm Deep Dives — Math → QUBO → Circuit → Code for each solver
4. Quantum Circuits     — Gate-by-gate QAOA/VQE breakdown, circuit rendering
5. Problem Statements   — 5 telecom problems: math model, bottleneck, quantum approach
6. Solver Architecture  — Mermaid mindmap, file table, pipeline flow
7. References           — Curated research papers indexed by problem domain
"""

from __future__ import annotations

import numpy as np
import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from dashboard.utils.plot_helpers import (
    PALETTE,
    plot_hndl_risk_heatmap,
    plot_maturity_radar,
    plot_packet_fragmentation,
    plot_protocol_handshake_sequence,
    plot_qubit_scaling_curve,
)
from dashboard.utils.resource_monitor import (
    estimate_classical_resources,
    estimate_qaoa_resources,
    estimate_statevector_ram,
    estimate_vqe_resources,
)
from telequm.pqc.algorithms import compare_algorithms, list_algorithms
from telequm.pqc.migration import (
    MaturityLadder,
    MigrationExecutionChain,
    SectorRiskMatrix,
)
from telequm.pqc.protocols import ProtocolSimulator
from telequm.pqc.threat_models import HNDLCalculator

# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════

def render():
    st.header("🎓 Education Hub")
    st.caption("Comprehensive quantum-telecom learning — from theory to code")

    subtab = st.selectbox(
        "Choose a topic",
        [
            "⚛️ Quantum Computing 101",
            "🛡️ PQC 101: Lattice Theory & NIST Standards",
            "🚨 Threat Matrix: HNDL & Telecom Vulnerabilities",
            "⚡ Crypto-Agility & Protocol Overhead Lab",
            "🪜 AQC Migration Framework (Levels 0-4)",
            "🧮 Memory & Complexity Calculator",
            "🔬 Algorithm Deep Dives",
            "🔌 Quantum Circuits Explained",
            "📡 Problem Statements & Modeling",
            "🏗️ Solver Architecture & File Map",
            "📚 Research References",
            "🖥️ Hardware Benchmark",
        ],
        key="edu_subtab",
    )

    if subtab == "⚛️ Quantum Computing 101":
        _render_quantum_101()
    elif subtab == "🛡️ PQC 101: Lattice Theory & NIST Standards":
        _render_pqc_101()
    elif subtab == "🚨 Threat Matrix: HNDL & Telecom Vulnerabilities":
        _render_hndl_threats()
    elif subtab == "⚡ Crypto-Agility & Protocol Overhead Lab":
        _render_crypto_agility()
    elif subtab == "🪜 AQC Migration Framework (Levels 0-4)":
        _render_aqc_migration()
    elif subtab == "🧮 Memory & Complexity Calculator":
        _render_memory_calculator()
    elif subtab == "🔬 Algorithm Deep Dives":
        _render_algorithm_deep_dives()
    elif subtab == "🔌 Quantum Circuits Explained":
        _render_quantum_circuits()
    elif subtab == "📡 Problem Statements & Modeling":
        _render_problem_statements()
    elif subtab == "🏗️ Solver Architecture & File Map":
        _render_solver_architecture()
    elif subtab == "📚 Research References":
        _render_references()
    elif subtab == "🖥️ Hardware Benchmark":
        _render_hardware_benchmark()


# ═══════════════════════════════════════════════════════════════════
# 1. QUANTUM 101
# ═══════════════════════════════════════════════════════════════════

def _render_quantum_101():
    st.subheader("Quantum Computing Basics for Telecom")

    with st.expander("🔵 Qubits & Superposition", expanded=True):
        st.markdown(r"""
        A **qubit** is the quantum analogue of a classical bit.
        Unlike a bit (0 or 1), a qubit exists in a **superposition**:

        $$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$$

        where $|\alpha|^2 + |\beta|^2 = 1$.

        **Telecom analogy:** Think of superposition as a signal simultaneously
        exploring all frequency channels — upon measurement, it collapses to one.
        """)

    with st.expander("🔗 Entanglement"):
        st.markdown(r"""
        **Entanglement** creates correlations stronger than classical.
        For two qubits:

        $$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

        **Telecom application:** Quantum key distribution (QKD) leverages
        entanglement for unconditionally secure communication.
        """)

    with st.expander("⚡ Quantum Gates"):
        st.markdown("""
        | Gate | Matrix | TELEQUM Use |
        |------|--------|-------------|
        | **H** (Hadamard) | Creates superposition | Initialize QAOA search space |
        | **CNOT** | Entangles qubits | VQE entanglement layers |
        | **Rz(θ)** | Phase rotation | Encode QUBO cost coefficients |
        | **RZZ(γ)** | Two-qubit interaction | QAOA cost layer |
        | **Rx(β)** | X-rotation | QAOA mixer layer |
        | **Ry(θ)** | Y-rotation | VQE ansatz parameterization |
        """)

    # Interactive Bloch sphere
    if HAS_PLOTLY:
        st.subheader("Interactive Bloch Sphere")
        col1, col2 = st.columns(2)
        with col1:
            theta = st.slider("θ (polar)", 0.0, np.pi, np.pi / 4, key="theta_bloch")
        with col2:
            phi = st.slider("φ (azimuthal)", 0.0, 2 * np.pi, 0.0, key="phi_bloch")
        st.plotly_chart(_plot_bloch_sphere(theta, phi), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 1B. PQC 101: LATTICE THEORY & NIST STANDARDS
# ═══════════════════════════════════════════════════════════════════

def _render_pqc_101():
    st.subheader("🛡️ Post-Quantum Cryptography (PQC) 101")
    st.markdown("""
    While Shor's algorithm on a Fault-Tolerant Quantum Computer (FTQC) breaks classical public-key cryptography (RSA, ECC, Diffie-Hellman), **Post-Quantum Cryptography (PQC)** relies on mathematical problems that are hard for both classical and quantum computers.
    """)

    with st.expander("🌐 Why Lattices? (Learning With Errors & Shortest Vector Problem)", expanded=True):
        st.markdown(r"""
        Modern NIST standards rely on **Lattice-Based Cryptography**, specifically **Module-LWE (Learning With Errors)** and **Module-SIS (Shortest Integer Solution)** over polynomial rings.

        - **Shortest Vector Problem (SVP):** Given a multi-dimensional grid (lattice) generated by basis vectors, find the shortest non-zero vector in the grid.
        - **Learning With Errors (LWE):** Given linear equations with small random noise $e$:
          $$\mathbf{b} = \mathbf{A}\mathbf{s} + \mathbf{e} \pmod q$$
          It is exponentially hard for both classical lattice reduction (BKZ) and quantum algorithms (Grover/Shor) to recover the secret vector $\mathbf{s}$.

        **Why Module Lattices?** Ring-LWE offers compact keys by using polynomial multiplication, while Module-LWE allows seamless security scaling by simply increasing the module dimension $k$ (e.g., $k=2, 3, 4$ for Kyber-512, 768, 1024) without redefining the underlying algebraic field!
        """)

    with st.expander("📜 NIST FIPS Standards Breakdown"):
        st.markdown("""
        | Standard | Algorithm Name | Type | Key Mathematics | Primary Telecom Use Case |
        |----------|----------------|------|-----------------|--------------------------|
        | **FIPS 203** | ML-KEM (Kyber) | Key Encapsulation (KEM) | Module-LWE | TLS 1.3 / IKEv2 Session Key Exchange |
        | **FIPS 204** | ML-DSA (Dilithium) | Digital Signature | Module-LWE / Module-SIS | X.509 Certs, BGP Route Signing, 5G AKA |
        | **FIPS 205** | SLH-DSA (SPHINCS+) | Stateless Hash Signature | Hash Trees (SHA-2/SHAKE) | Root CA Signing, Firmware Updates (Ultra-Conservative) |
        | **FIPS 206** | FN-DSA (FALCON) | Digital Signature | NTRU Lattices + Fast Fourier Sampling | Constrained Hardware / Low-Latency MACsec |
        """)

    st.subheader("📊 NIST & Legacy Algorithm Comparison Table")
    algos = list_algorithms()
    sel_algos = st.multiselect(
        "Select algorithms to compare:",
        algos,
        default=["RSA-3072", "ECDH-256", "ML-KEM-768", "ML-DSA-65", "SLH-DSA-SHA2-128s"],
        key="pqc_101_comp",
    )
    if sel_algos:
        comp_data = compare_algorithms(sel_algos)
        header = "| Algorithm | Family | NIST Level | Public Key (B) | Secret Key (B) | Ciphertext/Sig (B) | Quantum Safe? |\n"
        header += "|-----------|--------|------------|----------------|----------------|--------------------|---------------|\n"
        rows = ""
        for a in comp_data:
            q_safe = "✅ Yes" if a["quantum_safe"] else "❌ Broken by Shor"
            rows += f"| **{a['name']}** | {a['family']} | {a['nist_level']} | {a['public_key_bytes']:,} | {a['secret_key_bytes']:,} | {a['ciphertext_bytes']:,} | {q_safe} |\n"
        st.markdown(header + rows)

    if HAS_PLOTLY:
        st.subheader("📈 Quantum Resource Scaling: Shor's vs Grover's Algorithm")
        st.plotly_chart(plot_qubit_scaling_curve(), use_container_width=True)
        st.caption("Notice how RSA and ECC require logical qubits linear in key size (Shor's polynomial speedup), whereas AES requires Grover's quadratic speedup—meaning AES-256 remains completely safe against quantum attacks!")


# ═══════════════════════════════════════════════════════════════════
# 1C. THREAT MATRIX: HNDL & TELECOM VULNERABILITIES
# ═══════════════════════════════════════════════════════════════════

def _render_hndl_threats():
    st.subheader("🚨 Threat Matrix: Harvest Now, Decrypt Later (HNDL)")
    st.markdown("""
    In telecommunications, adversaries do **not** need to wait for a Fault-Tolerant Quantum Computer (FTQC) to begin attacking networks. Under the **Harvest Now, Decrypt Later (HNDL)** threat model, nation-state adversaries passively record encrypted telecom traffic today and store it until an FTQC comes online.
    """)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 🧮 MOSQUE Theorem (Mosca's Inequality)")
        st.latex(r"X + Y > Z \implies \text{CRITICAL RISK}")
        st.markdown("""
        - **$X$ (Security Shelf-Life):** How long must the data remain confidential?
        - **$Y$ (Migration Time):** How many years to upgrade systems to PQC?
        - **$Z$ (Quantum Horizon):** Years until a cryptographically relevant quantum computer (CRQC) exists?

        *If $X + Y > Z$, your data is already being compromised today!*
        """)
    with col2:
        st.markdown("### 🔬 Shor's vs Grover's Impact")
        st.markdown("""
        - **Shor's Algorithm (Public-Key / Asymmetric):**
          - Solves integer factorization and discrete logarithms in **polynomial time** $O(\\log^3 N)$.
          - **Impact:** RSA, ECDH, ECDSA, DSA are **100% broken**. All session key exchanges and certificates collapse.
        - **Grover's Algorithm (Symmetric / Hashing):**
          - Provides a **quadratic speedup** $O(\\sqrt{N})$ for unstructured search.
          - **Impact:** Halves effective key length (AES-128 $\to$ 64-bit security).
          - **Remedy:** Simply double key lengths! **AES-256 and SHA-384/512 are quantum-safe.**
        """)

    st.divider()
    st.subheader("🎛️ Interactive HNDL Risk Calculator")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox("Telecom Data Category", [
            "Customer PII & CDRs",
            "Core Routing & Signaling (BGP/MPLS)",
            "Lawful Intercept & Gov Communications",
            "5G RAN MACsec & Over-the-Air",
            "Billing & Financial Transactions",
        ], key="hndl_cat")
        x_val = st.slider("Shelf-Life X (Years data must stay secret)", 1, 50, 15, key="hndl_x")
    with c2:
        y_val = st.slider("Migration Time Y (Years to deploy PQC)", 1, 20, 7, key="hndl_y")
        z_val = st.slider("Quantum Horizon Z (Years until CRQC)", 5, 30, 15, key="hndl_z")
    with c3:
        score_obj = HNDLCalculator.calculate(x_val, y_val, z_val)
        st.metric("HNDL Risk Score", f"{score_obj.score}/100", delta=score_obj.risk_level, delta_color="inverse")
        st.markdown(f"**Action Required:** `{score_obj.action_required}`")
        st.caption(f"Margin: {score_obj.margin_years:+d} years | {score_obj.description}")

    if HAS_PLOTLY:
        st.subheader("🔥 Telecom Layer vs Infrastructure Lifecycle Heatmap")
        layers = ["L1 Radio / Optical", "L2 MACsec / RLC", "L3 IPsec / RRC", "L4-7 Core / TLS / NAS"]
        cats = ["Cat A (Device/SIM)", "Cat B (RAN/Edge)", "Cat C (Core/Transport)", "Cat D (Cloud/OSS)"]

        mat = np.zeros((4, 4))
        for i, _l in enumerate(layers):
            for j, _c in enumerate(cats):
                shelf = 5 + j * 10 - i * 2
                mig = 3 + j * 3
                mat[i, j] = HNDLCalculator.calculate(max(1, shelf), mig, z_val).score

        st.plotly_chart(plot_hndl_risk_heatmap(mat, cats, layers), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 1D. CRYPTO-AGILITY & PROTOCOL OVERHEAD LAB
# ═══════════════════════════════════════════════════════════════════

def _render_crypto_agility():
    st.subheader("⚡ Crypto-Agility & Protocol Overhead Lab")
    st.markdown("""
    **Crypto-Agility** is the architectural capability of a telecommunications network to rapidly switch cryptographic algorithms, protocols, and certificates without upgrading hardware or causing network outages.

    Why is this critical for telecom? Because PQC algorithms have **much larger public keys and signatures** than classical ECC/RSA, which can cause severe **packet fragmentation over network MTUs**, increased handshake latency, and buffer overflows on constrained IoT/RAN devices!
    """)

    with st.expander("🔗 Hybrid Certificates (X.509 Dual-Signature Paradigm)", expanded=True):
        st.markdown("""
        During the 2025–2035 transition decade, telecom operators cannot rely solely on PQC (due to compliance and software maturity) nor solely on ECC (due to HNDL risk).

        The solution is **Hybrid Certificates (ITU-T X.509 / IETF RFC 9385)**:
        - Each certificate contains **both** a classical key (ECDSA-P256 or RSA-3072) and a PQC key (ML-DSA-44 or ML-DSA-65).
        - **Rule:** Both signatures must be verified! If an attacker breaks ECC with a quantum computer, the ML-DSA signature still protects the session.
        - **Trade-off:** Certificate size jumps from ~1.5 KB to **>6 KB**, requiring multi-packet transmission during TLS 1.3 / IKEv2 handshakes!
        """)

    st.subheader("🧪 Interactive Protocol Handshake & Fragmentation Simulator")

    c1, c2, c3 = st.columns(3)
    with c1:
        proto_sel = st.selectbox("Protocol", ["TLS_1_3", "IPSec_IKEv2", "MACsec", "5G_AKA", "DNSSEC_BGP"], key="ca_proto")
    with c2:
        link_sel = st.selectbox("Telecom Link Type", ["5G_UMa_RAN", "Optical_Backhaul", "Satellite_LEO", "Core_Mesh"], key="ca_link")
    with c3:
        suite_sel = st.selectbox("Cryptographic Suite", ["Classical", "PQC_Pure", "Hybrid"], key="ca_suite")

    res = ProtocolSimulator.simulate_handshake(proto_sel, link_sel, suite_sel)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Latency", f"{res.total_latency_ms:.2f} ms")
    m2.metric("Total Bytes Transferred", f"{res.total_bytes:,} B")
    m3.metric("Packet Fragmentation", f"{res.fragmentation_count} pkts", delta="MTU Exceeded!" if res.mtu_exceeded else "No Fragmentation", delta_color="inverse" if res.mtu_exceeded else "normal")
    m4.metric("Crypto CPU Load", f"{res.cpu_processing_ms:.2f} ms")

    if HAS_PLOTLY:
        st.plotly_chart(plot_protocol_handshake_sequence(res.steps, f"{proto_sel} Handshake Timing ({suite_sel} on {link_sel})"), use_container_width=True)

        st.subheader("📦 MTU Fragmentation Comparison Across Suites")
        suites_dict = {
            "Classical (ECDH+ECDSA)": ProtocolSimulator.simulate_handshake(proto_sel, link_sel, "Classical").to_dict(),
            "PQC Pure (ML-KEM+ML-DSA)": ProtocolSimulator.simulate_handshake(proto_sel, link_sel, "PQC_Pure").to_dict(),
            "Hybrid (Dual Suite)": ProtocolSimulator.simulate_handshake(proto_sel, link_sel, "Hybrid").to_dict(),
        }
        st.plotly_chart(plot_packet_fragmentation(suites_dict, mtu_bytes=1500), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# 1E. AQC MIGRATION FRAMEWORK (LEVELS 0-4)
# ═══════════════════════════════════════════════════════════════════

def _render_aqc_migration():
    st.subheader("🪜 AQC Operational Migration Framework")
    st.markdown("""
    Based on the **Applied Quantum Computing (AQC) Telecom Whitepaper** and GSMA Post-Quantum guidelines, telecommunications operators migrate to quantum-safe networks across a **5-Pillar Operational Maturity Ladder** ranging from Level 0 to Level 4.
    """)

    with st.expander("🏆 The 5 Pillars of Telecom PQC Maturity", expanded=True):
        st.markdown("""
        1. **Governance & Strategy:** Executive sponsorship, PQC policy mandates, quantum risk tracking, regulatory compliance (ETSI, GSMA, NIST).
        2. **Cryptographic Discovery:** Automated cryptographic inventory, continuous scanning of cipher suites, certificates, and algorithms across OSS/BSS and RAN.
        3. **Architecture & Agility:** Abstraction of cryptography from application logic, hybrid certificate support, protocol adaptability without hardcoding.
        4. **Operational Deployment:** Lab testing, pilot trials, staged rollout across transport, core, and radio networks with automated key rotation.
        5. **Procurement & Supply Chain:** Vendor RFP requirements mandating FIPS 203/204 compliance, hardware security module (HSM) upgrades, and SLA guarantees.
        """)

    st.subheader("🎚️ Interactive Maturity Ladder Assessment")
    st.markdown("Adjust your organization's score (0-100) across the 5 pillars to evaluate your **Maturity Level**:")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        gov = st.slider("1. Governance", 0, 100, 45, key="mat_gov")
    with c2:
        disc = st.slider("2. Discovery", 0, 100, 30, key="mat_disc")
    with c3:
        arch = st.slider("3. Architecture", 0, 100, 25, key="mat_arch")
    with c4:
        ops = st.slider("4. Operations", 0, 100, 15, key="mat_ops")
    with c5:
        proc = st.slider("5. Procurement", 0, 100, 40, key="mat_proc")

    scores = {
        "Governance": gov,
        "Discovery": disc,
        "Architecture": arch,
        "Operations": ops,
        "Procurement": proc,
    }
    mat_res = MaturityLadder.evaluate(scores)

    col_res1, col_res2 = st.columns([1, 2])
    with col_res1:
        st.metric("Overall Maturity Level", f"Level {mat_res.level}: {mat_res.name}")
        st.markdown(f"**Average Score:** `{mat_res.overall_score:.1f}/100`")
        st.info(f"💡 **Next Step:** {mat_res.next_step}")
        st.caption(f"**Description:** {mat_res.description}")
    with col_res2:
        if HAS_PLOTLY:
            st.plotly_chart(plot_maturity_radar(scores), use_container_width=True)

    st.divider()
    st.subheader("🏭 Sector Risk Profiles & Execution Chain")

    sec_sel = st.selectbox("Select Industry Sector Profile", [
        "Telecommunications",
        "Banking_Finance",
        "Government_Defense",
        "Healthcare_MedTech",
        "Critical_Infrastructure",
    ], key="sec_prof")

    sec_data = SectorRiskMatrix.get_profile(sec_sel)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Max Allowable Latency", f"{sec_data.max_allowable_latency_ms} ms")
    sc2.metric("Hardware Replacement Cycle", f"{sec_data.hardware_replacement_cycle_years} Years")
    sc3.metric("Data Sensitivity Shelf-Life", f"{sec_data.data_sensitivity_shelf_life_years} Years")

    st.markdown(f"**Regulatory Mandates:** {', '.join(sec_data.regulatory_mandates)}")
    st.markdown(f"**Recommended Crypto Suite:** `{sec_data.recommended_suite}`")

    with st.expander("🔄 4-Phase Migration Execution Chain & KPIs"):
        chain = MigrationExecutionChain.get_chain()
        for idx, stage in enumerate(chain):
            st.markdown(f"#### Phase {stage.stage_number}: {stage.name} (`{stage.timeline}`)")
            st.markdown(f"**Objective:** {stage.objective}")
            st.markdown(f"**Deliverables:** {', '.join(stage.deliverables)}")
            st.markdown(f"**Key Milestones:** {', '.join(stage.key_milestones)}")
            if idx < len(chain) - 1:
                st.markdown("---")


# ═══════════════════════════════════════════════════════════════════
# 2. MEMORY & COMPLEXITY CALCULATOR
# ═══════════════════════════════════════════════════════════════════

def _render_memory_calculator():
    st.subheader("🧮 Memory & Complexity Calculator")
    st.markdown("""
    Estimate the **RAM, gate count, and time complexity** for any algorithm
    based on your problem size. This uses Big-O analysis tied to the actual
    implementations in the TELEQUM codebase.
    """)

    # ── Input sliders ────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        n_qubits = st.slider("Qubits / Variables (n)", 2, 40, 10, key="mem_nq")
    with c2:
        p_layers = st.slider("QAOA depth (p)", 1, 10, 2, key="mem_p")
    with c3:
        edge_count = st.slider("Problem edges (|E|)", 1, 200, n_qubits * 2, key="mem_edges")

    # ── Statevector RAM ──────────────────────────────────────────
    st.subheader("💾 Statevector Simulation RAM")
    st.latex(r"\text{RAM} = 2^n \times 16 \text{ bytes (complex128)}")

    ram = estimate_statevector_ram(n_qubits)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Qubits", ram["num_qubits"])
    c2.metric("State Vector Size", f"{ram['statevector_entries']:,}")
    c3.metric("RAM (MB)", f"{ram['ram_mb']:,.2f}")
    c4.metric("RAM (GB)", f"{ram['ram_gb']:,.4f}")

    if ram["feasible_laptop"]:
        st.success("✅ Feasible on a laptop (< 16 GB)")
    elif ram["feasible_server"]:
        st.warning("⚠️ Requires a workstation (< 256 GB)")
    else:
        st.error(f"❌ Infeasible: {ram['ram_gb']:.0f} GB needed")

    # ── RAM scaling chart ────────────────────────────────────────
    if HAS_PLOTLY:
        qubits_range = list(range(2, min(n_qubits + 15, 41)))
        ram_vals = [estimate_statevector_ram(q)["ram_mb"] for q in qubits_range]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=qubits_range, y=ram_vals, mode="lines+markers",
            line={"color": PALETTE["primary"], "width": 2},
            name="RAM (MB)"
        ))
        fig.add_hline(y=16000, line_dash="dash", line_color=PALETTE["danger"],
                      annotation_text="16 GB laptop limit")
        fig.update_layout(
            title="Statevector RAM vs Qubit Count (log scale)",
            xaxis_title="Qubits", yaxis_title="RAM (MB)",
            yaxis_type="log",
            plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
            font={"color": PALETTE["text"]}, height=350,
        )
        fig.update_xaxes(gridcolor=PALETTE["grid"])
        fig.update_yaxes(gridcolor=PALETTE["grid"])
        st.plotly_chart(fig, use_container_width=True)

    # ── Algorithm comparison table ───────────────────────────────
    st.subheader("📊 Algorithm Resource Comparison")

    qaoa = estimate_qaoa_resources(n_qubits, p_layers, edge_count)
    vqe = estimate_vqe_resources(n_qubits, p_layers)
    greedy = estimate_classical_resources(n_qubits, "greedy")
    sa = estimate_classical_resources(n_qubits, "simulated_annealing")
    exact = estimate_classical_resources(n_qubits, "exact")

    st.markdown(f"""
    | Algorithm | Time Complexity | Gates | Depth | RAM (MB) | Feasible? |
    |-----------|----------------|-------|-------|----------|-----------|
    | **QAOA** (p={p_layers}) | {qaoa['time_complexity']} | {qaoa['total_gates']} | {qaoa['circuit_depth']} | {qaoa['ram_mb']:,.2f} | {'✅' if qaoa['feasible_laptop'] else '⚠️'} |
    | **VQE** ({p_layers} layers) | {vqe['time_complexity']} | {vqe['total_gates']} | {vqe['circuit_depth']} | {vqe['ram_mb']:,.2f} | {'✅' if vqe['feasible_laptop'] else '⚠️'} |
    | **Greedy** | {greedy['time_complexity']} | — | — | {greedy['ram_mb']:,.4f} | ✅ |
    | **Simulated Annealing** | {sa['time_complexity']} | — | — | {sa['ram_mb']:,.4f} | ✅ |
    | **Exact Brute-Force** | {exact['time_complexity']} | — | — | {exact['ram_mb']:,.6f} | {'✅' if exact['feasible'] else '❌'} |
    """)


# ═══════════════════════════════════════════════════════════════════
# 3. ALGORITHM DEEP DIVES
# ═══════════════════════════════════════════════════════════════════

def _render_algorithm_deep_dives():
    st.subheader("🔬 Algorithm Deep Dives")
    st.markdown("From **mathematical equation → QUBO modeling → code implementation**")

    algo = st.selectbox("Select algorithm",
                        ["QAOA", "VQE", "Greedy Baseline", "Simulated Annealing", "Exact Brute-Force"],
                        key="algo_dive")

    if algo == "QAOA":
        _dive_qaoa()
    elif algo == "VQE":
        _dive_vqe()
    elif algo == "Greedy Baseline":
        _dive_greedy()
    elif algo == "Simulated Annealing":
        _dive_sa()
    elif algo == "Exact Brute-Force":
        _dive_exact()


def _dive_qaoa():
    st.markdown(r"""
    ### Quantum Approximate Optimization Algorithm (QAOA)

    **Origin:** Farhi, Goldstone, Gutmann (2014) — MIT

    #### Step 1: Mathematical Formulation
    Given a cost function $C(x) = x^T Q x$ (the QUBO), construct cost Hamiltonian:

    $$H_C = \sum_{(i,j)} Q_{ij} \frac{(1-Z_i)(1-Z_j)}{4}$$

    and mixer Hamiltonian:

    $$H_M = \sum_i X_i$$

    #### Step 2: QAOA Circuit
    The parameterized state after $p$ layers:

    $$|\gamma, \beta\rangle = \prod_{l=1}^{p} e^{-i\beta_l H_M} \cdot e^{-i\gamma_l H_C} \cdot |+\rangle^{\otimes n}$$

    #### Step 3: Classical Optimization Loop
    A classical optimizer (COBYLA / SPSA) minimizes:

    $$\langle\gamma,\beta|H_C|\gamma,\beta\rangle$$

    by tuning $\gamma_1,...,\gamma_p,\beta_1,...,\beta_p$.

    #### Step 4: Code Mapping in TELEQUM

    | Step | File | Function / Class |
    |------|------|-----------------|
    | Build QUBO | `problems/prb_allocation.py` | `PRBAllocationProblem.to_qubo()` |
    | QUBO → Ising | `simulator/optimization_bridge.py` | `OptimizationBridge._qubo_to_ising()` |
    | Run QAOA | `simulator/optimization_bridge.py` | `OptimizationBridge.solve_quantum()` |
    | Decode | `problems/base_problem.py` | `BaseProblem.decode_solution()` |
    | Metrics | `problems/prb_allocation.py` | `PRBAllocationProblem.compute_metrics()` |

    #### Complexity
    - **Qubits:** $n$ (number of QUBO variables)
    - **Gates per layer:** $O(|E| + n)$ where $|E|$ = edges in problem graph
    - **Parameters:** $2p$ (gamma + beta per layer)
    - **RAM:** $O(2^n)$ for statevector, $O(n^2)$ for shot-based
    """)


def _dive_vqe():
    st.markdown(r"""
    ### Variational Quantum Eigensolver (VQE)

    **Origin:** Peruzzo et al. (2014) — Nature

    #### Step 1: Mathematical Formulation
    Find the ground state energy of Hamiltonian $H$:

    $$E(\theta) = \min_\theta \langle\psi(\theta)|H|\psi(\theta)\rangle$$

    where $|\psi(\theta)\rangle = U(\theta)|0\rangle^{\otimes n}$ is a parameterized ansatz.

    #### Step 2: Ansatz (Circuit Template)
    TELEQUM uses **RealAmplitudes** ansatz:
    - **Layer structure:** $[R_y(\theta)] \rightarrow [\text{CNOT ladder}]$ repeated $L$ times
    - Each layer: $n$ Ry gates + $(n-1)$ CNOTs
    - Total parameters: $n \times (L+1)$

    #### Step 3: Measurement + Classical Update
    1. Prepare $|\psi(\theta)\rangle$
    2. Measure $\langle H \rangle$ via Pauli decomposition
    3. Update $\theta$ via COBYLA / L-BFGS-B

    #### Step 4: Code Mapping

    | Step | File | Function |
    |------|------|----------|
    | Build Hamiltonian | `simulator/optimization_bridge.py` | `_qubo_to_ising()` |
    | VQE execution | `simulator/optimization_bridge.py` | `solve_quantum(algorithm='vqe')` |
    | Ansatz | Qiskit `RealAmplitudes` | Built-in |
    | Optimizer | Qiskit `COBYLA` | Built-in |

    #### Complexity
    - **Qubits:** $n$
    - **Parameters:** $n \times (L+1)$, each requiring gradient estimation
    - **VQE vs QAOA:** VQE has more parameters but may find better ground states
    """)


def _dive_greedy():
    st.markdown(r"""
    ### Greedy Solver

    #### Algorithm
    ```
    for each variable i = 0..n-1:
        set x[i] = 0, compute cost_0
        set x[i] = 1, compute cost_1
        keep x[i] = argmin(cost_0, cost_1)
    ```

    #### Complexity
    - **Time:** $O(n^2)$ — for each of $n$ variables, evaluate cost over $n$-dim Q
    - **Space:** $O(n^2)$ — storing the Q matrix
    - **Quality:** Local optimum only, no global guarantee

    #### Code Mapping

    | Step | File | Function |
    |------|------|----------|
    | Greedy solve | `simulator/optimization_bridge.py` | `ClassicalBaselines.greedy()` |

    #### Bottleneck for Telcos
    Greedy is the **most common** solver in production telecom RAN schedulers
    (e.g., proportional-fair schedulers). It runs in real-time but:
    - Gets stuck in local optima for dense interference scenarios
    - Cannot handle multi-objective constraints (SINR + fairness + energy)
    - Performance degrades with network density
    """)


def _dive_sa():
    st.markdown(r"""
    ### Simulated Annealing (SA)

    #### Algorithm
    ```
    T = T_max
    x = random initial solution
    while T > T_min:
        x_new = flip random bit in x
        ΔE = cost(x_new) - cost(x)
        if ΔE < 0 or random() < exp(-ΔE/T):
            x = x_new
        T = T × cooling_rate
    ```

    #### Mathematical Foundation
    Accept probability: $P(\Delta E, T) = e^{-\Delta E / T}$

    At high $T$: accepts almost everything (exploration).
    At low $T$: only accepts improvements (exploitation).

    #### Complexity
    - **Time:** $O(n \times T_{max} / \text{cooling\_step})$ ≈ $O(n \times 1000)$
    - **Space:** $O(n^2)$ — Q matrix
    - **Quality:** Good — escapes local optima via temperature schedule

    #### Code Mapping

    | Step | File | Function |
    |------|------|----------|
    | SA solve | `simulator/optimization_bridge.py` | `ClassicalBaselines.simulated_annealing()` |
    """)


def _dive_exact():
    st.markdown(r"""
    ### Exact Brute-Force

    #### Algorithm
    ```
    best_cost = +∞
    for x in all 2^n binary strings:
        cost = x^T Q x
        if cost < best_cost:
            best_cost = cost
            best_x = x
    ```

    #### Complexity
    - **Time:** $O(2^n \times n^2)$ — exponential in problem size
    - **Space:** $O(n)$
    - **Quality:** Globally optimal — guaranteed best solution

    #### Feasibility
    | n | 2^n | Time @ 1M eval/s |
    |---|-----|------------------|
    | 10 | 1,024 | 1 ms |
    | 20 | 1,048,576 | 1 s |
    | 25 | 33,554,432 | 34 s |
    | 30 | 1,073,741,824 | 18 min |
    | 40 | 1.1 × 10¹² | 13 days |

    #### Code Mapping

    | Step | File | Function |
    |------|------|----------|
    | Exact solve | `simulator/optimization_bridge.py` | `ClassicalBaselines.exact_brute_force()` |
    """)


# ═══════════════════════════════════════════════════════════════════
# 4. QUANTUM CIRCUITS EXPLAINED
# ═══════════════════════════════════════════════════════════════════

def _render_quantum_circuits():
    st.subheader("🔌 Quantum Circuits in TELEQUM")
    st.markdown("""
    Every quantum solver in TELEQUM constructs a **parameterized quantum circuit**.
    Here's exactly how each circuit is built, gate by gate.
    """)

    circuit = st.selectbox("Circuit type", ["QAOA Circuit", "VQE Circuit"], key="circ_type")

    if circuit == "QAOA Circuit":
        st.markdown(r"""
        ### QAOA Circuit Construction

        **Input:** QUBO matrix $Q$ (from `problem.to_qubo()`)

        ```
        Step 1: Convert Q → Ising Hamiltonian (Z operators)
                H_C = Σ_{i<j} J_{ij} Z_i Z_j + Σ_i h_i Z_i

        Step 2: Build circuit for p layers:
        ┌──────────────────────────────────────────────────────────┐
        │  |0⟩ ─── H ─┬─ Rz(γ₁·h₁) ─── RZZ(γ₁·J₁₂) ─── Rx(β₁) ─ ...  │
        │  |0⟩ ─── H ─┴─ Rz(γ₁·h₂) ─── RZZ(γ₁·J₁₃) ─── Rx(β₁) ─ ...  │
        │  |0⟩ ─── H ─── Rz(γ₁·h₃) ─── ...            ─── Rx(β₁) ─ ...  │
        └──────────────────────────────────────────────────────────┘
                              ↑ Cost Layer (γ)         ↑ Mixer Layer (β)

        Step 3: Measure all qubits → binary string x
        Step 4: Evaluate C(x) = x^T Q x
        Step 5: Classical optimizer updates γ, β
        Step 6: Repeat for k iterations
        ```

        #### Gate Breakdown
        | Gate | Count per layer | Purpose |
        |------|----------------|---------|
        | **H** | $n$ (first layer only) | Create uniform superposition |
        | **Rz(γ·h)** | $n$ | Single-qubit cost terms |
        | **RZZ(γ·J)** | $|E|$ (edges) | Two-qubit interaction terms |
        | **Rx(β)** | $n$ | Mixer — explore solution space |

        #### RZZ Gate Decomposition
        The RZZ(θ) gate is implemented as:
        ```
        q1 ───●─── Rz(θ) ───●───
              │              │
        q2 ───⊕─────────────⊕───
        ```
        This is: CNOT → Rz(θ) → CNOT = 2 CNOTs + 1 Rz per edge.

        #### Which TELEQUM files build this circuit?

        | Component | File | What it does |
        |-----------|------|-------------|
        | QUBO → Ising | `optimization_bridge.py` | Converts Q matrix to Pauli Z operators |
        | QAOA circuit | Qiskit `QAOA` class | Builds parameterized layers automatically |
        | Optimizer | Qiskit `COBYLA` | Classical loop to tune γ, β |
        | Sampler | `qiskit_aer.AerSimulator` | Statevector or shot-based simulation |
        """)

    elif circuit == "VQE Circuit":
        st.markdown(r"""
        ### VQE Circuit Construction (RealAmplitudes Ansatz)

        **Input:** Ising Hamiltonian $H$ (from QUBO conversion)

        ```
        ┌──────────────────────────────────────────────────────────┐
        │  |0⟩ ─── Ry(θ₁) ───●─── Ry(θ₄) ───●─── Ry(θ₇) ─── M  │
        │  |0⟩ ─── Ry(θ₂) ───⊕───●── Ry(θ₅) ───⊕── Ry(θ₈) ─── M  │
        │  |0⟩ ─── Ry(θ₃) ───────⊕── Ry(θ₆) ─────── Ry(θ₉) ─── M  │
        └──────────────────────────────────────────────────────────┘
              ↑ Parameter layer    ↑ Entangle   ↑ Param   ↑ Entangle  ↑ Param
                 Layer 0                          Layer 1               Layer 2
        ```

        #### Gate Breakdown
        | Gate | Count per layer | Purpose |
        |------|----------------|---------|
        | **Ry(θ)** | $n$ | Parameterized rotation (variational freedom) |
        | **CNOT** | $n-1$ | Linear entanglement — creates correlations |

        #### Key Differences vs QAOA
        | Property | QAOA | VQE |
        |----------|------|-----|
        | Circuit structure | Problem-specific (cost+mixer) | Generic ansatz |
        | Parameters | 2p (few) | n×(L+1) (many) |
        | Best for | Combinatorial optimization | Ground state finding |
        | Expressibility | Limited by p | Highly expressive |
        """)

    # ── Interactive circuit preview ──────────────────────────────
    st.subheader("🔍 Circuit Size Preview")
    n = st.slider("Qubits", 2, 20, 6, key="circ_preview_n")
    p = st.slider("Layers", 1, 5, 2, key="circ_preview_p")

    if circuit == "QAOA Circuit":
        res = estimate_qaoa_resources(n, p, n * (n - 1) // 2)
    else:
        res = estimate_vqe_resources(n, p)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Qubits", res["num_qubits"])
    c2.metric("Total Gates", res["total_gates"])
    c3.metric("Circuit Depth", res["circuit_depth"])
    c4.metric("Parameters", res["num_parameters"])


# ═══════════════════════════════════════════════════════════════════
# 5. PROBLEM STATEMENTS & MODELING
# ═══════════════════════════════════════════════════════════════════

def _render_problem_statements():
    st.subheader("📡 Telecom Optimization Problems")
    st.markdown("""
    Each problem represents a **core research target for TELEQUM**.
    Described with:
    1. **Problem description** — what operators face in real networks
    2. **Mathematical formulation** — objective, variables, constraints
    3. **Classical techniques** — what Ericsson, Nokia, Huawei actually use
    4. **Scalability bottlenecks** — why classical solvers break down
    5. **Quantum approach** — QUBO formulation and solver pipeline
    6. **References** — IEEE, 3GPP, and recent arXiv papers
    """)

    prob = st.selectbox("Problem", [
        "📡 1. PRB Allocation (Resource Scheduling)",
        "🔀 2. Network Routing Optimization",
        "🏗️ 3. Base Station Placement",
        "📶 4. Beamforming Optimization",
        "⚡ 5. Energy Efficiency (Cell On/Off)",
        "🔄 6. Handover Optimization",
        "🔮 7. Quantum Network Routing (Future Internet)",
    ], key="prob_stmt")

    if "PRB" in prob:
        _prob_prb()
    elif "Routing" in prob and "Quantum" not in prob:
        _prob_routing()
    elif "Base Station" in prob:
        _prob_bs_placement()
    elif "Beam" in prob:
        _prob_beamforming()
    elif "Energy" in prob:
        _prob_energy()
    elif "Handover" in prob:
        _prob_handover()
    elif "Quantum Network" in prob:
        _prob_quantum_routing()


def _prob_prb():
    st.markdown(r"""
    ### 📡 1. Radio Resource Allocation (PRB Scheduling)

    #### Problem Description
    In cellular networks (4G/5G/6G), the base station must allocate **Physical
    Resource Blocks (PRBs)** to users every **1 millisecond** (TTI). Each user has
    different channel conditions, QoS requirements, and interference from
    neighboring cells. The goal: **maximize throughput while maintaining fairness
    and minimizing inter-cell interference**.

    #### Mathematical Formulation

    **Sets:** $U$ = users, $R$ = resource blocks

    **Decision variables:** $x_{u,r} \in \{0,1\}$ — user $u$ gets PRB $r$

    **Objective — maximize weighted throughput:**

    $$\max \sum_{u \in U} \sum_{r \in R} w_u \cdot c_{u,r} \cdot x_{u,r}$$

    where $c_{u,r}$ = achievable rate, $w_u$ = fairness weight.

    **Constraint — each PRB to at most one user:**

    $$\sum_{u \in U} x_{u,r} \leq 1 \quad \forall r \in R$$

    #### Classical Techniques Used by Telecom Vendors

    | Algorithm | Used By | How It Works | Limitation |
    |-----------|---------|-------------|------------|
    | **Proportional Fair (PF)** | Ericsson, Nokia | $\text{priority}_u = \frac{\text{inst\_rate}}{\text{avg\_rate}}$ | Greedy — local optima |
    | **Round Robin (RR)** | 3GPP baseline | Equal time slices per user | Ignores channel quality |
    | **Weighted Fair Queuing** | QoS-aware networks | Priority weights per class | No joint power/beam opt |
    | **Max-Rate** | High-throughput cells | Always picks best user | Starves edge users |
    | **Hungarian Algorithm** | Academic | Optimal in $O(n^3)$ | Too slow for >1000 UEs |
    | **ILP (Gurobi/CPLEX)** | R&D labs | Integer programming | Exponential worst-case |

    #### Scalability Bottlenecks

    1. **NP-hard** — search space: $|R|^{|U|}$ (exponential in users)
    2. **Interference coupling** — interacts with power control, beamforming, cell coordination
    3. **Real-time** — scheduler runs every **1 ms** in LTE/5G → vendors forced to use heuristics
    4. **Network density** — 5G small cells: 10–100× more sites, heuristic-optimal gap grows

    #### Quantum Approach (QUBO)

    $$\min\ x^T Q x = -\sum_{u,r} w_u c_{u,r}\,x_{u,r} + P\sum_r\!\left(\sum_u x_{u,r} - 1\right)^{\!2}$$

    **Pipeline:** `PRB allocation → QUBO matrix → Ising Hamiltonian → QAOA/VQE → Decode`

    #### TELEQUM Files
    - `telequm/problems/prb_allocation.py` → `PRBAllocationProblem`
    - Methods: `to_qubo()`, `decode_solution()`, `compute_metrics()`

    #### References
    - Choi et al., *"Quantum Approximation for Wireless Scheduling"*,
      Applied Sciences, 2020. [DOI: 10.3390/app10207116](https://doi.org/10.3390/app10207116)
    - 3GPP TS 38.214, *"NR; Physical layer procedures for data"*
    - 3GPP TS 36.213, *"E-UTRA; Physical layer procedures"*
    """)


def _prob_routing():
    st.markdown(r"""
    ### 🔀 2. Network Routing Optimization

    #### Problem Description
    Routing determines **how packets travel through the network**. Must minimize
    latency, congestion, and maximize throughput/reliability. Becomes extremely
    difficult in **large, dynamic 6G mesh networks** with 10,000+ nodes.

    #### Mathematical Formulation

    **Network:** $G = (V, E)$ — $|V|$ nodes, $|E|$ links

    **Decision variables:** $x_{i,j} \in \{0,1\}$ — link $(i,j)$ in path

    **Objective — minimize path cost:**

    $$\min \sum_{(i,j) \in E} c_{i,j} \cdot x_{i,j}$$

    **Flow conservation:**

    $$\sum_j x_{i,j} - \sum_j x_{j,i} = b_i$$

    where $b_{\text{src}}=+1$, $b_{\text{dst}}=-1$, $b_{\text{transit}}=0$.

    #### Classical Techniques

    | Algorithm | Protocol | Limitation |
    |-----------|----------|------------|
    | **Dijkstra** | OSPF, IS-IS | Single-objective, no QoS constraints |
    | **Bellman-Ford** | BGP, RIP | Slow convergence, negative cycle issues |
    | **Multi-Commodity Flow** | SDN (ONOS, ODL) | MILP — NP-hard for multi-constrained |
    | **Segment Routing** | SR-MPLS, SRv6 | Pre-computed, no real-time adaptation |

    #### Scalability Bottlenecks

    1. **Multi-objective** — jointly optimize latency, loss, jitter, energy
    2. **Scale** — 10,000+ nodes, recomputation exceeds network coherence time
    3. **Dynamic topology** — link failures require instant re-routing

    #### Quantum Approach

    $$H = \sum_{(i,j)} c_{i,j}\, x_{i,j} + P \cdot \text{flow\_conservation\_penalties}$$

    QAOA complexity does **not grow** with node count for fixed sparsity (Urgelles 2022).

    #### TELEQUM Files
    - `telequm/problems/telecom_problems.py` → `RoutingOptimization`

    #### References
    - Urgelles et al., *"Multi-Objective Routing for 6G Using QAOA"*,
      Sensors, 2022. [DOI: 10.3390/s22197570](https://doi.org/10.3390/s22197570)
    - Lin et al., *"Routing Using Coherent Ising Machines"*, arXiv:2503.07924, 2025.
    - Chen et al., *"Distributed Quantum Circuits for Wireless Networks"*, arXiv:2501.10242, 2025.
    - Dash et al., *"Hierarchical Quantum Routing"*, arXiv:2511.00506, 2025.
    """)


def _prob_bs_placement():
    st.markdown(r"""
    ### 🏗️ 3. Base Station Placement

    #### Problem Description
    Operators must decide **where to deploy base stations** to maximize
    coverage while minimizing deployment cost — a classic **facility location** problem.

    #### Mathematical Formulation

    **Sets:** $S$ = candidate sites, $U$ = user locations

    **Decision variables:** $y_s \in \{0,1\}$ — BS placed at site $s$

    **Objective — minimize cost with coverage:**

    $$\min \sum_{s \in S} \text{cost}_s \cdot y_s$$

    **Coverage constraint:**

    $$\sum_{s \in S} a_{u,s} \cdot y_s \geq 1 \quad \forall u \in U$$

    where $a_{u,s} = 1$ if site $s$ covers user $u$.

    #### Classical Techniques

    | Method | Used In | Limitation |
    |--------|---------|------------|
    | **MILP** | Radio planning (Atoll, Planet) | NP-hard for >1000 candidates |
    | **Genetic Algorithms** | Evolutionary optimization | Slow convergence |
    | **Greedy** | Quick estimation | Locally optimal only |
    | **SA** | Research prototypes | No optimality guarantee |

    #### Bottlenecks

    1. Search space: $2^{|S|}$ (thousands of candidates)
    2. Complex 3D propagation models for mmWave
    3. Multi-layer: jointly place macro + small cells + mmWave

    #### Quantum Approach

    $$H = \sum_s \text{cost}_s\, y_s + P \sum_u \left(1 - \sum_s a_{u,s}\, y_s\right)^2$$

    #### TELEQUM Files
    - **Status:** Research target — extensible via `telequm/problems/`
    - `benchmarks/topologies.py` provides test topologies

    #### References
    - Daskin & Maass, *"Facility Location Problems"*, Wiley, 2015.
    - 3GPP TR 38.901, *"Channel model for 0.5–100 GHz"*
    """)


def _prob_beamforming():
    st.markdown(r"""
    ### 📶 4. Beamforming Optimization

    #### Problem Description
    Massive MIMO (64–256 antennas) must compute **optimal beamforming vectors**
    for each user. Includes **analog beam selection** (from codebook) and
    **digital beamforming** (precoding weights).

    #### Mathematical Formulation

    **Channel:** $\mathbf{H} \in \mathbb{C}^{K \times N}$ ($K$ users, $N$ antennas)

    **Beamforming:** $\mathbf{W} \in \mathbb{C}^{N \times K}$

    **Objective:**

    $$\max_\mathbf{W} \sum_{k=1}^K |\mathbf{h}_k^H \mathbf{w}_k|^2 \quad \text{s.t. } \|\mathbf{W}\|_F^2 \leq P_{\max}$$

    **Discrete variant:** $x_{u,k} \in \{0,1\}$, one beam per user ($\sum_k x_{u,k} = 1$).

    #### Classical Techniques

    | Method | Complexity | Limitation |
    |--------|-----------|------------|
    | **Zero-Forcing (ZF)** | $O(N^3)$ | Noise amplification |
    | **MMSE** | $O(N^3)$ | Cubic scaling for large arrays |
    | **Exhaustive sweep** | $O(|B| \times K)$ | Too slow for 256 beams × 32 users |
    | **Hierarchical search** | $O(\log|B| \times K)$ | Misses multi-path beams |
    | **ML prediction** | Inference cost | Poor generalization |

    #### Bottlenecks

    1. **$O(N^3)$ matrix inversion** for $N=256$ antennas in real-time
    2. Beam search: 256 antennas × 64 beams — prohibitive per-slot
    3. Channel changes every ~0.5 ms at 120 kHz SCS

    #### Quantum Approach

    - **Discrete selection** → one-hot QUBO for QAOA
    - **Continuous precoding** → HHL algorithm: $O(\log N)$ vs $O(N^3)$
    - **Hybrid:** quantum gradient descent for weight optimization

    #### TELEQUM Files
    - Discrete: `telequm/problems/telecom_problems.py` → `BeamSelection`
    - Continuous: `telequm/bridges/matlab_bridge.py` → ZF/MMSE

    #### References
    - Ericsson, *"Quantum Neural Networks for Antenna Optimization"*, 2024.
    - Harrow et al., *"Quantum Algorithm for Linear Systems (HHL)"*, PRL, 2009.
    - 3GPP TS 38.214, *"Beam management procedures"*
    """)


def _prob_energy():
    st.markdown(r"""
    ### ⚡ 5. Energy Efficiency (Cell On/Off)

    #### Problem Description
    Telcos spend **5–10% of OPEX on energy** (GSMA, 2024). With 5G densification
    (10–100× more sites), **switch off underutilized cells** while maintaining coverage.

    #### Mathematical Formulation

    **Decision variables:** $y_c \in \{0,1\}$ (cell active), $x_{u,c} \in \{0,1\}$ (user→cell)

    $$\min \sum_c P_c\, y_c - \lambda \sum_{u,c} \text{SINR}_{u,c}\, x_{u,c}$$

    **Constraints:** $x_{u,c} \leq y_c$ (only active cells), $\sum_c x_{u,c} \geq 1$ (all served)

    #### Classical Techniques

    | Method | Limitation |
    |--------|------------|
    | **Rule-based sleep modes** | No global optimization |
    | **Reinforcement Learning** | Slow training, unstable |
    | **MILP (Gurobi/CPLEX)** | NP-hard for >50 cells |
    | **Column generation** | Complex, slow convergence |

    #### Bottlenecks

    1. Joint cell+user = coupled binary problem
    2. Traffic varies hourly
    3. GSMA net-zero 2050 → need 50% energy reduction

    #### Quantum Approach (set-cover QUBO)

    $$H = \sum_c P_c\, y_c - \lambda\sum_{u,c} \text{SINR}_{u,c}\, x_{u,c} + P\cdot\text{constraints}$$

    #### TELEQUM Files
    - `telequm/problems/telecom_problems.py` → `EnergyEfficiency`

    #### References
    - GSMA, *"Mobile Net Zero: State of the Industry"*, 2024.
    - Orange Research Labs, *"Quantum Network Optimization"*, 2024.
    """)


def _prob_handover():
    st.markdown(r"""
    ### 🔄 6. Handover Optimization

    #### Problem Description
    In 6G dense small cells (ISD < 200m), handover rates exceed **10/minute**
    at vehicular speeds — each disruption ~50ms.

    #### Mathematical Formulation

    **Decision variables:** $x_{u,c} \in \{0,1\}$ — user $u$ served by cell $c$

    $$\min \sum_{u,c} \left[-\text{SINR}_{u,c}\, x_{u,c} + \delta_{u,c}\, H_{\text{cost}}\right]$$

    where $\delta_{u,c}=1$ if cell change (handover penalty).

    #### Classical Techniques

    | Method | Limitation |
    |--------|------------|
    | **A3/A5 event triggers** | Reactive, ping-pong |
    | **Hysteresis + TTT** | Static thresholds |
    | **ML predictive** | Per-cell training, doesn't scale |
    | **Conditional HO (Rel-16)** | Still reactive |

    #### Bottlenecks

    1. Ping-pong between cells
    2. Failure rate ↑ with speed + density
    3. Must consider future trajectory

    #### Quantum Approach

    $$H = -\sum_{u,c} \text{SINR}_{u,c}\, x_{u,c} + H_{\text{pen}} \sum \delta_{u,c}\, x_{u,c} + P\cdot\text{one-per-user}$$

    #### TELEQUM Files
    - `telequm/problems/telecom_problems.py` → `HandoverOptimization`

    #### References
    - 3GPP TS 38.331, *"RRC"*; 3GPP TS 38.300, *"NR Overall Description"*
    """)


def _prob_quantum_routing():
    st.markdown(r"""
    ### 🔮 7. Quantum Network Routing (Future Quantum Internet)

    #### Problem Description
    Future networks must route **entanglement and quantum keys** — not classical
    packets. Quantum repeaters, entanglement swapping, and decoherence create
    fundamentally different constraints.

    #### Mathematical Formulation

    **Graph:** $G = (V, E)$, edge weight = fidelity $F_{i,j}$

    **Objective — maximize end-to-end fidelity:**

    $$\max \prod_{(i,j) \in \text{path}} F_{i,j} \equiv \max \sum_{(i,j)} \log F_{i,j}\, x_{i,j}$$

    **Constraints:**
    - Flow conservation
    - Path latency $\leq$ decoherence time
    - Repeater capacity limits

    #### Classical Techniques

    | Method | Limitation |
    |--------|------------|
    | **Dijkstra + fidelity** | Single-objective |
    | **Dynamic programming** | Exponential in constraints |
    | **Heuristic routing** | No fidelity optimization |

    #### Bottlenecks

    1. **Decoherence** — time-sensitive, classical solvers too slow
    2. **Probabilistic links** — success probability < 1
    3. **Memory limits** — quantum memories hold state for limited time

    #### Quantum Approach

    - Variational quantum optimization for fidelity paths
    - Quantum annealing for QKD key routing
    - Hybrid: classical graph theory + quantum optimization

    #### TELEQUM Files
    - **Status:** Research target — extends `RoutingOptimization`
    - Future integration with QKD simulators (SimulaQron, NetSquid)

    #### References
    - Caleffi et al., *"Quantum Internet: Networking Challenges"*, IEEE Network, 2020.
    - Kozlowski & Wehner, *"Designing a Quantum Network Protocol"*, arXiv, 2019.
    """)


# ═══════════════════════════════════════════════════════════════════
# 6. SOLVER ARCHITECTURE & FILE MAP
# ═══════════════════════════════════════════════════════════════════

def _render_solver_architecture():
    st.subheader("🏗️ Solver Architecture & File Map")

    st.markdown("""
    ### Pipeline Flow

    ```mermaid
    graph LR
        A["NetworkEnvironment<br>network_env.py"] -->|get_snapshot| B["UniversalNetworkSnapshot<br>core/network_snapshot.py"]
        B --> C["Problem Library<br>problems/*.py"]
        C -->|to_qubo| D["QUBO Matrix Q"]
        D --> E{"Solver Selection"}
        E -->|Classical| F["ClassicalBaselines<br>optimization_bridge.py"]
        E -->|Quantum| G["Qiskit QAOA/VQE<br>optimization_bridge.py"]
        E -->|Hybrid| H["HybridSolver<br>algorithms/hybrid/"]
        F --> I["decode_solution"]
        G --> I
        H --> I
        I --> J["compute_metrics"]
    ```

    > ⚠️ *Mermaid diagrams render as text in Streamlit. View in a Markdown viewer for the graph.*

    ### TELEQUM File Map

    | Module | File | Purpose |
    |--------|------|---------|
    | **Core** | `core/network_snapshot.py` | `UniversalNetworkSnapshot` — source-agnostic state |
    | **Simulator** | `simulator/network_env.py` | Network state, 3GPP UMa, SINR computation |
    | | `simulator/engine.py` | Time-step orchestrator |
    | | `simulator/optimization_bridge.py` | QUBO↔Ising, ClassicalBaselines, quantum solving |
    | | `simulator/traffic_models.py` | Poisson, Video, IoT traffic generators |
    | | `simulator/mobility_models.py` | Pedestrian, Vehicular, Random Waypoint |
    | **Problems** | `problems/base_problem.py` | `BaseProblem` ABC: to_qubo, to_hamiltonian |
    | | `problems/prb_allocation.py` | PRB QUBO formulation |
    | | `problems/telecom_problems.py` | Routing, Beam, Energy, Handover QUBOs |
    | **Solvers** | `algorithms/hybrid/hybrid_solver.py` | 3-strategy hybrid pipeline |
    | **Bridges** | `bridges/matlab_bridge.py` | MATLAB CDL/TDL H-matrix import |
    | | `bridges/ns3_bridge.py` | ns-3 trace ingestion |
    | **Scenarios** | `scenarios/__init__.py` | small/medium/large/mobility_stress generators |
    | **Dashboard** | `dashboard/app.py` | Streamlit entry point |
    | | `dashboard/utils/resource_monitor.py` | RAM/CPU/time tracking |

    ### Which Solver Uses Which Circuit?

    | Solver | Circuit Type | Qiskit Class | File |
    |--------|-------------|--------------|------|
    | QAOA | Cost (RZZ) + Mixer (Rx) layers | `qiskit_algorithms.QAOA` | `optimization_bridge.py` |
    | VQE | RealAmplitudes ansatz (Ry + CNOT) | `qiskit_algorithms.VQE` | `optimization_bridge.py` |
    | Greedy | No circuit | — | `optimization_bridge.py` |
    | Simulated Annealing | No circuit | — | `optimization_bridge.py` |
    | Exact | No circuit | — | `optimization_bridge.py` |
    | HybridSolver | Delegates to QAOA or VQE | `HybridSolver` | `hybrid_solver.py` |
    """)


# ═══════════════════════════════════════════════════════════════════
# 7. RESEARCH REFERENCES
# ═══════════════════════════════════════════════════════════════════

def _render_references():
    st.subheader("📚 Research References Database")
    st.markdown("""
    Curated papers forming the **scientific foundation** of TELEQUM.
    Organized by problem domain.
    """)

    domain = st.selectbox("Filter by domain", [
        "All References",
        "1. Wireless Resource Scheduling",
        "2. Network Routing",
        "3. Multi-Hop & Sensor Networks",
        "4. Large-Scale Routing",
        "5. Circuit Optimization",
        "6. General Quantum-Telecom",
    ], key="ref_domain")

    refs = _get_references()
    if domain != "All References":
        idx = int(domain[0])
        refs = [r for r in refs if r["domain_id"] == idx]

    for r in refs:
        with st.expander(f"📄 {r['short_title']}", expanded=False):
            st.markdown(f"""
**Authors:** {r['authors']}

**Title:** *{r['title']}*

**Journal:** {r['journal']}, {r['year']}

**DOI/Link:** [{r['doi']}]({r['doi']})

**Summary:** {r['summary']}

**TELEQUM Mapping:**
```
{r['mapping']}
```

**Tags:** {', '.join(f'`{t}`' for t in r['tags'])}
            """)

    st.divider()
    st.markdown("""
    ### Why These Papers Matter

    The existing literature typically studies **one telecom problem at a time**
    (scheduling OR routing OR beamforming). TELEQUM is different — it provides
    a **unified platform** to test QAOA, VQE, quantum annealing, Ising machines,
    and classical heuristics across **multiple telecom problems in the same simulator**.
    """)


def _get_references():
    return [
        {
            "domain_id": 1,
            "short_title": "Choi et al. 2020 — QAOA for Wireless Scheduling",
            "authors": "Choi, J., Oh, S., & Kim, J.",
            "title": "Quantum Approximation for Wireless Scheduling",
            "journal": "Applied Sciences (MDPI)",
            "year": 2020,
            "doi": "https://doi.org/10.3390/app10207116",
            "summary": "Applies QAOA to wireless scheduling as Maximum Weight Independent Set (MWIS). "
                       "Designs Hamiltonians for interference constraints. QAOA outperforms greedy and "
                       "random heuristics in simulation.",
            "mapping": "prb_allocation.py — interference-aware scheduling\nspectrum_scheduling — MWIS formulation",
            "tags": ["quantum_optimization", "wireless_scheduling", "QAOA", "MWIS", "QUBO"],
        },
        {
            "domain_id": 2,
            "short_title": "Urgelles et al. 2022 — QAOA Routing for 6G",
            "authors": "Urgelles, H., Picazo-Martinez, P., Garcia-Roger, D., Monserrat, J.",
            "title": "Multi-Objective Routing Optimization for 6G Communication Networks Using QAOA",
            "journal": "Sensors (MDPI)",
            "year": 2022,
            "doi": "https://doi.org/10.3390/s22197570",
            "summary": "Explores single- and multi-objective routing for 6G networks using QAOA. "
                       "Routing formulated as QUBO, mapped to Ising Hamiltonian. Shows QAOA circuit "
                       "complexity doesn't grow with node count for fixed sparsity.",
            "mapping": "routing_optimization.py — QUBO routing\nmulti-objective experiments\n6G network optimization",
            "tags": ["quantum_optimization", "routing", "QAOA", "6G", "QUBO"],
        },
        {
            "domain_id": 3,
            "short_title": "Lin et al. 2025 — Coherent Ising Machines for Multi-Hop Routing",
            "authors": "Lin, Y., Xu, C., Wang, C.",
            "title": "Multi-Objective Routing Using Coherent Ising Machines in Wireless Multihop Networks",
            "journal": "arXiv preprint",
            "year": 2025,
            "doi": "https://arxiv.org/abs/2503.07924",
            "summary": "Formulates multi-hop routing as QUBO→Ising, solved via Coherent Ising Machines (CIM). "
                       "Scales to hundreds of nodes. Avoids topology-specific heuristics.",
            "mapping": "routing_optimization.py\nbenchmark comparison: QAOA vs VQE vs CIM vs classical",
            "tags": ["routing", "Ising_machines", "multi_hop", "wireless_networks"],
        },
        {
            "domain_id": 3,
            "short_title": "Chen et al. 2025 — Distributed Quantum Circuits for WSN",
            "authors": "Chen, K., Burt, F., Yu, S., Liu, C., Hsieh, M., Leung, K.",
            "title": "Resource-Efficient Compilation of Distributed Quantum Circuits for Wireless Network Problems",
            "journal": "arXiv preprint",
            "year": 2025,
            "doi": "https://arxiv.org/abs/2501.10242",
            "summary": "Hybrid classical-quantum framework for WSN routing. Uses spectral clustering for "
                       "network partitioning + QAOA for routing optimization.",
            "mapping": "large_network routing benchmarks\ndistributed optimization\nhybrid quantum-classical",
            "tags": ["distributed_quantum", "WSN", "routing", "QAOA", "hybrid"],
        },
        {
            "domain_id": 4,
            "short_title": "Dash et al. 2025 — Hierarchical Quantum Routing",
            "authors": "Dash, S., Banerjee, S., Panigrahi, P.",
            "title": "Hierarchical Quantum Optimization for Large-Scale Vehicle Routing",
            "journal": "arXiv preprint",
            "year": 2025,
            "doi": "https://arxiv.org/abs/2511.00506",
            "summary": "Hierarchical framework using Multi-Angle QAOA (MA-QAOA). Clustering-based "
                       "decomposition enables quantum optimization of larger routing instances.",
            "mapping": "scalable routing experiments\nclustered network optimization\nlarge topology simulations",
            "tags": ["routing", "MA_QAOA", "hierarchical", "large_scale"],
        },
        {
            "domain_id": 5,
            "short_title": "Kotil et al. 2023 — QAOA Circuit Qubit Routing",
            "authors": "Kotil, A., Simkovic, F., Leib, M.",
            "title": "Improved Qubit Routing for QAOA Circuits",
            "journal": "arXiv preprint",
            "year": 2023,
            "doi": "https://arxiv.org/abs/2312.15982",
            "summary": "Polynomial-time algorithm for qubit routing in QAOA circuits, minimizing "
                       "circuit depth and swap gates. Critical for hardware-aware optimization.",
            "mapping": "hardware-aware QAOA compilation\ncircuit optimization\nscalability experiments",
            "tags": ["QAOA", "circuit_optimization", "qubit_routing", "hardware"],
        },
        {
            "domain_id": 6,
            "short_title": "Ericsson 2024 — Quantum AI for Telecom",
            "authors": "Ericsson Research",
            "title": "Quantum AI Will Become Competitive Necessity for CSPs",
            "journal": "Telecoms.com / Ericsson Blog",
            "year": 2024,
            "doi": "https://www.ericsson.com/en/blog/2024",
            "summary": "Ericsson validates quantum neural networks for antenna optimization with "
                       "fewer parameters than classical models. Projects quantum-enhanced features "
                       "standard in 6G by 2030.",
            "mapping": "beam_selection.py — antenna optimization\nhardware_hub.py — vendor comparison",
            "tags": ["quantum_AI", "telecom_industry", "6G", "Ericsson"],
        },
        {
            "domain_id": 6,
            "short_title": "Orange 2024 — Quantum Network Optimization",
            "authors": "Orange Research Labs",
            "title": "Quantum Computing to Optimize Network Operations",
            "journal": "Orange Innovation Blog",
            "year": 2024,
            "doi": "https://hellofuture.orange.com/en/quantum-computing/",
            "summary": "Orange initiates research into hybrid classical-quantum models for dynamic "
                       "network management. Focus on reducing compute time and energy consumption.",
            "mapping": "energy_efficiency.py — cell on/off optimization\nhybrid_solver.py — hybrid pipeline",
            "tags": ["quantum_optimization", "energy_efficiency", "Orange", "hybrid"],
        },
        {
            "domain_id": 6,
            "short_title": "3GPP TR 38.901 — Channel Models",
            "authors": "3GPP",
            "title": "Study on Channel Model for Frequencies from 0.5 to 100 GHz",
            "journal": "3GPP Technical Report",
            "year": 2023,
            "doi": "https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3173",
            "summary": "Standardized channel models (UMa/UMi/InH) used by TELEQUM for path loss, "
                       "shadow fading, and SINR computation. The foundation of all network simulations.",
            "mapping": "simulator/network_env.py — _urban_macro_los(), _urban_macro_nlos()\nAll SINR computations",
            "tags": ["3GPP", "channel_model", "path_loss", "SINR", "UMa"],
        },
    ]


# ═══════════════════════════════════════════════════════════════════
# BLOCH SPHERE HELPER
# ═══════════════════════════════════════════════════════════════════

def _plot_bloch_sphere(theta: float, phi: float) -> go.Figure:
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 20)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=x, y=y, z=z, opacity=0.1,
        colorscale=[[0, PALETTE["primary"]], [1, PALETTE["secondary"]]],
        showscale=False,
    ))

    sx = np.sin(theta) * np.cos(phi)
    sy = np.sin(theta) * np.sin(phi)
    sz = np.cos(theta)

    fig.add_trace(go.Scatter3d(
        x=[0, sx], y=[0, sy], z=[0, sz],
        mode="lines+markers",
        marker={"size": [3, 8], "color": [PALETTE["dark"], PALETTE["accent"]]},
        line={"color": PALETTE["accent"], "width": 4},
        name="|ψ⟩",
    ))

    for ax, label, color in [
        ([1.3, 0, 0], "X", PALETTE["danger"]),
        ([0, 1.3, 0], "Y", PALETTE["warning"]),
        ([0, 0, 1.3], "|0⟩", PALETTE["accent"]),
    ]:
        fig.add_trace(go.Scatter3d(
            x=[0, ax[0]], y=[0, ax[1]], z=[0, ax[2]],
            mode="lines+text", line={"color": color, "width": 2},
            text=["", label], textposition="top center", showlegend=False,
        ))

    fig.update_layout(
        scene={"xaxis": {"visible": False}, "yaxis": {"visible": False},
                   "zaxis": {"visible": False}, "aspectmode": "cube"},
        paper_bgcolor=PALETTE["card"], font={"color": PALETTE["text"]},
        height=450, margin={"l": 0, "r": 0, "t": 30, "b": 0},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════
# 8. HARDWARE BENCHMARK
# ═══════════════════════════════════════════════════════════════════

def _render_hardware_benchmark():
    """Hardware benchmark subtab: detect specs, estimate solver times."""
    from dashboard.utils.resource_monitor import benchmark_device, estimate_solver_times

    st.subheader("🖥️ Hardware Benchmark")
    st.markdown("""
    Detect your device's hardware specs, run a quick performance benchmark,
    and see **estimated solver runtimes** for any QUBO problem size.
    """)

    # ── Run Benchmark ─────────────────────────────────────────
    if st.button("🚀 Run Device Benchmark", type="primary"):
        with st.spinner("Benchmarking hardware..."):
            hw = benchmark_device()
        st.session_state["hw_benchmark"] = hw

    hw = st.session_state.get("hw_benchmark")

    if hw:
        # ── Device Specs Card ────────────────────────────────────
        st.subheader("⚙️ Device Specifications")
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("🖥️ CPU", hw["cpu_name"])
        h2.metric("🧵 Cores", hw["cpu_cores_physical"])
        h3.metric("🧠 Total RAM", f"{hw['total_ram_gb']} GB")
        h4.metric("🟢 Available RAM", f"{hw['available_ram_gb']} GB")

        h5, h6, h7, h8 = st.columns(4)
        h5.metric("🎮 GPU", hw["gpu_name"])
        h6.metric("💾 GPU Memory", f"{hw['gpu_memory_gb']} GB" if hw["gpu_memory_gb"] else "N/A")
        h7.metric("💻 OS", hw["os"])
        h8.metric("🐍 Python", hw["python_version"])

        st.divider()

        # ── Benchmark Results ────────────────────────────────────
        st.subheader("⚡ Benchmark Score")
        b1, b2, b3 = st.columns(3)
        b1.metric("🚀 GFLOPS", f"{hw['bench_gflops']}",
                  help="Single-core matrix multiply throughput")
        b2.metric("⏱ 500×500 MatMul", f"{hw['bench_matmul_ms']} ms")
        b3.metric("🏗️ Architecture", hw["architecture"])

        if hw["bench_gflops"] > 20:
            st.success("🟢 High-performance hardware — suitable for medium QAOA (up to ~25 qubits).")
        elif hw["bench_gflops"] > 5:
            st.info("🟡 Standard hardware — classical solvers run well, QAOA limited to ~15–20 qubits.")
        else:
            st.warning("🟠 Low-performance hardware — keep QUBO sizes small (<15 vars).")

        st.divider()

        # ── Solver Time Estimation ───────────────────────────────
        st.subheader("📊 Solver Time Estimation")
        st.markdown("""
        Adjust the QUBO size below to see **estimated wall-clock time**
        for each solver on **your hardware**. These are theoretical estimates
        based on Big-O complexity scaled by your benchmark score.
        """)

        n_vars = st.slider("QUBO Variables (n)", 2, 100, 20, key="bench_nvars")
        estimates = estimate_solver_times(n_vars, hw)

        # Build table
        header = "| Solver | Big-O | Operations | Est. Time | RAM | Feasible |\n"
        header += "|--------|-------|------------|-----------|-----|----------|\n"
        rows = ""
        for e in estimates:
            feasible_icon = "✅" if e["feasible"] else "❌"
            rows += (f"| **{e['solver']}** | `{e['big_o']}` | {e['ops']} | "
                     f"**{e['est_time']}** | {e['ram_mb']} MB | {feasible_icon} |\n")
        st.markdown(header + rows)

        # Notes per solver
        for e in estimates:
            if "note" in e:
                if "EXCEEDS" in e.get("note", ""):
                    st.error(f"🚨 **{e['solver']}**: {e['note']}")
                else:
                    st.caption(f"📌 {e['solver']}: {e['note']}")

        # ── Comparison at Multiple Scales ───────────────────────
        with st.expander("📈 Time Comparison at Multiple Scales"):
            st.markdown("Estimated runtimes for common QUBO sizes on your device:\n")
            scale_header = "| n | Greedy | SA | Exact | QAOA |\n"
            scale_header += "|---|--------|----|-------|------|\n"
            scale_rows = ""
            for n in [5, 10, 15, 20, 25, 30, 40, 50, 60]:
                est = estimate_solver_times(n, hw)
                scale_rows += f"| **{n}** "
                for e in est:
                    scale_rows += f"| {e['est_time']} "
                scale_rows += "|\n"
            st.markdown(scale_header + scale_rows)

            st.markdown("""
            ---
            **Key takeaways:**
            - **Greedy/SA** scale polynomially — fast even at 100+ variables
            - **Exact** hits a wall at ~25 variables (exponential)
            - **QAOA** statevector simulation requires RAM that doubles per qubit
            - Above ~30 qubits, QAOA needs shot-based (noisy) simulation or real quantum hardware
            """)
    else:
        st.info("👆 Click the button above to detect your hardware and run a benchmark.")
