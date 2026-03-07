"""
Education Hub — Interactive Quantum-Telecom Learning
=====================================================

Dashboard tab providing:
- Quantum computing fundamentals for telecom engineers
- Interactive QUBO formulation walkthroughs
- Circuit visualization and Bloch sphere demos
- 3GPP model explanations
"""

from __future__ import annotations

import numpy as np
import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from dashboard.utils.plot_helpers import PALETTE


def render():
    """Render the Education Hub tab."""
    st.header("🎓 Education Hub")
    st.caption("Interactive quantum-telecom learning for ICT engineers")

    subtab = st.selectbox(
        "Choose a topic",
        ["Quantum Computing 101", "QUBO Formulations", "3GPP Models", "Algorithm Deep Dives"],
        key="edu_subtab",
    )

    if subtab == "Quantum Computing 101":
        _render_quantum_101()
    elif subtab == "QUBO Formulations":
        _render_qubo_guide()
    elif subtab == "3GPP Models":
        _render_3gpp_models()
    elif subtab == "Algorithm Deep Dives":
        _render_algorithm_deep_dives()


# ─── Quantum 101 ─────────────────────────────────────────────────

def _render_quantum_101():
    st.subheader("Quantum Computing Basics for Telecom")

    with st.expander("🔵 Qubits & Superposition", expanded=True):
        st.markdown("""
        A **qubit** is the quantum analogue of a classical bit.
        Unlike a bit (0 or 1), a qubit exists in a **superposition**:

        $$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$

        where $|\\alpha|^2 + |\\beta|^2 = 1$.

        **Telecom analogy:** Think of superposition as a signal that
        simultaneously explores all frequency channels — upon measurement,
        it collapses to one.
        """)

    with st.expander("🔗 Entanglement"):
        st.markdown("""
        **Entanglement** creates correlations stronger than classical.
        For two qubits: $|\\Phi^+\\rangle = \\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)$

        **Telecom application:** Quantum key distribution (QKD)
        leverages entanglement for unconditionally secure communication.
        """)

    with st.expander("⚡ Quantum Gates"):
        st.markdown("""
        | Gate | Matrix | Telecom Use |
        |------|--------|-------------|
        | **H** (Hadamard) | Creates superposition | Initialize search space |
        | **CNOT** | Entangles qubits | Correlation structures |
        | **Rz(θ)** | Phase rotation | Encode problem parameters |
        | **RZZ(γ)** | Two-qubit interaction | QAOA cost layer |
        """)

    # Interactive Bloch sphere
    if HAS_PLOTLY:
        st.subheader("Interactive Bloch Sphere")
        col1, col2 = st.columns(2)
        with col1:
            theta = st.slider("θ (polar angle)", 0.0, np.pi, np.pi / 4, key="theta_bloch")
        with col2:
            phi = st.slider("φ (azimuthal angle)", 0.0, 2 * np.pi, 0.0, key="phi_bloch")

        fig = _plot_bloch_sphere(theta, phi)
        st.plotly_chart(fig, use_container_width=True)


def _plot_bloch_sphere(theta: float, phi: float) -> go.Figure:
    """Render a Bloch sphere with state vector."""
    # Sphere wireframe
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 20)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        opacity=0.1, colorscale=[[0, PALETTE["primary"]], [1, PALETTE["secondary"]]],
        showscale=False,
    ))

    # State vector
    sx = np.sin(theta) * np.cos(phi)
    sy = np.sin(theta) * np.sin(phi)
    sz = np.cos(theta)

    fig.add_trace(go.Scatter3d(
        x=[0, sx], y=[0, sy], z=[0, sz],
        mode="lines+markers",
        marker=dict(size=[3, 8], color=[PALETTE["dark"], PALETTE["accent"]]),
        line=dict(color=PALETTE["accent"], width=4),
        name=f"|ψ⟩ = {np.cos(theta/2):.2f}|0⟩ + {np.sin(theta/2)*np.exp(1j*phi):.2f}|1⟩",
    ))

    # Axes
    for ax, label, color in [
        ([1.3, 0, 0], "X", PALETTE["danger"]),
        ([0, 1.3, 0], "Y", PALETTE["warning"]),
        ([0, 0, 1.3], "|0⟩", PALETTE["accent"]),
    ]:
        fig.add_trace(go.Scatter3d(
            x=[0, ax[0]], y=[0, ax[1]], z=[0, ax[2]],
            mode="lines+text",
            line=dict(color=color, width=2),
            text=["", label], textposition="top center",
            showlegend=False,
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="cube",
        ),
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
        height=450,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig


# ─── QUBO Guide ──────────────────────────────────────────────────

def _render_qubo_guide():
    st.subheader("QUBO Formulations for Telecom")

    st.markdown("""
    Every quantum optimization in TELEQUM follows:

    ```
    1. build_qubo(snapshot)    → Q matrix, offset, metadata
    2. Solve (classical/quantum)
    3. decode_solution(x, meta) → actionable allocation
    4. evaluate_cost(x, Q)     → scalar objective
    ```
    """)

    with st.expander("📡 Resource Allocation QUBO", expanded=True):
        st.markdown("""
        **Problem:** Assign users to base stations maximising throughput.

        **Variables:** $x_{u,b} \\in \\{0,1\\}$ — user $u$ served by BS $b$

        **Objective:**
        $$\\min \\sum_{u,b} -\\text{SINR}_{u,b} \\cdot x_{u,b}$$

        **Constraint 1** (one BS per user):
        $$\\sum_b x_{u,b} = 1 \\quad \\forall u$$

        **Constraint 2** (BS capacity):
        $$\\sum_u x_{u,b} \\leq C_b \\quad \\forall b$$

        Constraints converted to penalty terms with weight $P$:
        $$Q_{\\text{total}} = Q_{\\text{obj}} + P \\cdot Q_{\\text{c1}} + P \\cdot Q_{\\text{c2}}$$
        """)

    # Interactive QUBO matrix visualization
    st.subheader("Interactive QUBO Builder")
    col1, col2 = st.columns(2)
    with col1:
        n_ue_demo = st.slider("Users", 2, 6, 3, key="qubo_ue")
    with col2:
        n_bs_demo = st.slider("Base Stations", 2, 4, 2, key="qubo_bs")

    n = n_ue_demo * n_bs_demo
    rng = np.random.default_rng(42)
    Q_demo = rng.uniform(-5, 5, (n, n))
    Q_demo = np.triu(Q_demo + Q_demo.T)

    if HAS_PLOTLY:
        labels = [f"x({u},{b})" for u in range(n_ue_demo) for b in range(n_bs_demo)]
        fig = go.Figure(data=go.Heatmap(
            z=Q_demo, x=labels, y=labels,
            colorscale="RdBu_r",
            colorbar=dict(title="Q value"),
        ))
        fig.update_layout(
            title=f"QUBO Matrix ({n}×{n})",
            plot_bgcolor=PALETTE["bg"],
            paper_bgcolor=PALETTE["card"],
            font=dict(color=PALETTE["text"]),
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.info(f"💡 This {n_ue_demo}×{n_bs_demo} problem has **{n} binary variables** → "
            f"QAOA needs **{n} qubits**")


# ─── 3GPP Models ─────────────────────────────────────────────────

def _render_3gpp_models():
    st.subheader("3GPP Channel Models in TELEQUM")

    st.markdown("""
    TELEQUM implements **3GPP TR 38.901** Urban Macro (UMa) path loss:
    """)

    with st.expander("📐 UMa LOS Path Loss"):
        st.latex(r"PL_{\text{LOS}} = 28 + 22 \log_{10}(d_{3D}) + 20 \log_{10}(f_c)")
        st.markdown("Valid for $10\\text{m} \\leq d_{2D} \\leq d_{BP}$, $f_c$ in GHz")

    with st.expander("🏙️ UMa NLOS Path Loss"):
        st.latex(r"PL_{\text{NLOS}} = 13.54 + 39.08 \log_{10}(d_{3D}) + 20 \log_{10}(f_c) - 0.6(h_{UE} - 1.5)")

    # Interactive path loss plot
    st.subheader("Path Loss vs Distance")
    freq = st.slider("Frequency (GHz)", 0.5, 6.0, 3.5, 0.1, key="freq_3gpp")

    distances = np.linspace(10, 500, 200)
    pl_los = 28 + 22 * np.log10(distances) + 20 * np.log10(freq)
    pl_nlos = 13.54 + 39.08 * np.log10(distances) + 20 * np.log10(freq) - 0.6 * (1.5 - 1.5)

    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=distances, y=pl_los, name="LOS",
                                  line=dict(color=PALETTE["accent"], width=2)))
        fig.add_trace(go.Scatter(x=distances, y=pl_nlos, name="NLOS",
                                  line=dict(color=PALETTE["danger"], width=2, dash="dash")))
        fig.update_layout(
            title=f"3GPP UMa Path Loss @ {freq} GHz",
            xaxis_title="Distance (m)", yaxis_title="Path Loss (dB)",
            plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
            font=dict(color=PALETTE["text"]), height=400,
        )
        fig.update_xaxes(gridcolor=PALETTE["grid"])
        fig.update_yaxes(gridcolor=PALETTE["grid"])
        st.plotly_chart(fig, use_container_width=True)


# ─── Algorithm Deep Dives ───────────────────────────────────────

def _render_algorithm_deep_dives():
    st.subheader("Algorithm Deep Dives")

    algo = st.selectbox("Select algorithm", ["QAOA", "VQE", "Classical Baselines"],
                        key="algo_deep_dive")

    if algo == "QAOA":
        st.markdown("""
        ### Quantum Approximate Optimization Algorithm (QAOA)

        **Purpose:** Find approximate solutions to combinatorial optimization.

        **Circuit structure** ($p$ layers):
        $$|\\gamma, \\beta\\rangle = \\prod_{l=1}^{p} e^{-i \\beta_l H_M} e^{-i \\gamma_l H_C} |+\\rangle^{\\otimes n}$$

        | Component | Role | Telecom Mapping |
        |-----------|------|-----------------|
        | $H_C$ (cost) | Problem Hamiltonian | SINR-weighted allocation |
        | $H_M$ (mixer) | Explore solution space | X rotations on all qubits |
        | $\\gamma_l$ | Cost layer angles | Learned via classical optimizer |
        | $\\beta_l$ | Mixer layer angles | Learned via classical optimizer |

        **TELEQUM usage:** `OptimizationBridge.solve_quantum(snapshot, algorithm="qaoa")`
        """)
    elif algo == "VQE":
        st.markdown("""
        ### Variational Quantum Eigensolver (VQE)

        **Purpose:** Find ground state of a Hamiltonian.

        $$E(\\theta) = \\langle \\psi(\\theta) | H | \\psi(\\theta) \\rangle$$

        **Ansatz types in TELEQUM:**
        - Hardware-efficient: `RY-CNOT` layers
        - Alternating: `RY-RZ` blocks with entanglement

        **TELEQUM usage:** `OptimizationBridge.solve_quantum(snapshot, algorithm="vqe")`
        """)
    elif algo == "Classical Baselines":
        st.markdown("""
        ### Classical Baselines (Rule #5)

        Every quantum solver is benchmarked against:

        | Method | Complexity | Quality | Use Case |
        |--------|-----------|---------|----------|
        | **Greedy** | O(n²) | Good | Fast baseline |
        | **Simulated Annealing** | O(n·k) | Better | Medium instances |
        | **Exact Brute-Force** | O(2ⁿ) | Optimal | n ≤ 20 only |

        **TELEQUM usage:** `OptimizationBridge.solve_classical(snapshot, method="greedy")`
        """)
