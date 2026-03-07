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
    from plotly.subplots import make_subplots
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
    st.caption("Compare quantum backends for telecom optimization workloads")

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
            line=dict(color=hw["color"], width=2),
            opacity=0.7,
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1],
                            gridcolor=PALETTE["grid"]),
            angularaxis=dict(gridcolor=PALETTE["grid"]),
            bgcolor=PALETTE["bg"],
        ),
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
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
    st.markdown(f"""
    | Scenario | Recommended Backend | Reason |
    |----------|-------------------|--------|
    | **Research / prototyping** | Qiskit Aer Simulator | Fast iteration, perfect fidelity |
    | **Small problems (≤16 vars)** | IBM Eagle/Heron | Accessible, good fidelity |
    | **High-fidelity (≤36 vars)** | IonQ Forte | All-to-all, highest fidelity |
    | **Production pilot** | Quantinuum H2 | Best 2Q gates, mid-scale |
    | **Scaling study** | Hybrid: classical + IBM | Classical for large, quantum for sub-problems |
    """)
