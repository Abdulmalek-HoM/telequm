"""
Digital Twin — Real-Time Network Visualization
================================================

Dashboard tab providing digital twin visualizations:
- Live network topology with BS and UE positions
- SINR heatmap across the area
- Traffic demand distribution
- Classical vs quantum allocation comparison
- Per-timestep animation controls
"""

from __future__ import annotations

import json
import time

import numpy as np
import streamlit as st

from dashboard.utils.scenario_loader import build_config_from_sliders, list_presets, load_preset
from dashboard.utils.snapshot_manager import run_scenario
from dashboard.utils.plot_helpers import (
    plot_network_topology, plot_sinr_heatmap, plot_throughput_series,
    plot_fairness_sinr, plot_allocation_matrix, PALETTE,
)

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render():
    """Render the Digital Twin tab."""
    st.header("🌐 Digital Twin")
    st.caption("Real-time network visualization and scenario comparison")

    # ── Scenario Quick Setup ─────────────────────────────────────
    with st.sidebar:
        st.subheader("🎛️ Twin Config")
        num_bs = st.slider("Base Stations", 2, 8, 4, key="dt_bs")
        num_ue = st.slider("Users", 4, 30, 12, key="dt_ue")
        area = st.slider("Area (m)", 200, 3000, 1000, 100, key="dt_area")
        seed = st.number_input("Seed", 0, 9999, 42, key="dt_seed")
        timesteps = st.slider("Timesteps", 10, 100, 30, key="dt_ts")
        traffic = st.selectbox("Traffic", ["poisson", "video", "iot"],
                               key="dt_traffic")
        mobility = st.selectbox("Mobility",
                                ["pedestrian", "random_waypoint", "vehicular"],
                                key="dt_mob")
        solver = st.selectbox("Solver", ["greedy", "simulated_annealing"],
                              key="dt_solver")
        run_quantum = st.checkbox("Quantum (QAOA)", key="dt_quantum")

    config = build_config_from_sliders(
        num_bs=num_bs, num_ue=num_ue,
        area_width=float(area), area_height=float(area),
        num_timesteps=timesteps,
        traffic_model=traffic, mobility_model=mobility,
        seed=int(seed), solver_method=solver, run_quantum=run_quantum,
    )

    if st.button("🔄 Run Digital Twin", type="primary", use_container_width=True,
                 key="dt_run"):
        _run_twin(config)


def _run_twin(config: dict):
    """Execute scenario and render digital twin views."""
    progress = st.progress(0, text="Initializing simulation...")
    t0 = time.time()

    # Run full simulation
    results = run_scenario(config, verbose=False)
    runtime = time.time() - t0

    progress.progress(100, text=f"Complete in {runtime:.2f}s")

    metrics = results["metrics"]
    env_final = results.get("environment_final", {})
    classical = results.get("classical_solutions", [])
    quantum = results.get("quantum_solutions", [])

    # ── KPI Banner ───────────────────────────────────────────────
    st.divider()
    if metrics:
        last = metrics[-1]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📶 Throughput", f"{last['avg_throughput_mbps']:.1f} Mbps")
        c2.metric("📡 SINR", f"{last['avg_sinr_db']:.1f} dB")
        c3.metric("⚖️ Fairness", f"{last['fairness_jain']:.3f}")
        c4.metric("👥 Active UEs", last["num_active_ues"])
        c5.metric("⏱️ Runtime", f"{runtime:.2f}s")

    # ── Twin Layout ──────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Network Topology")
        bs_pos = np.array([bs["position"] for bs in env_final.get("base_stations", [])])
        ue_pos = np.array([ue["position"] for ue in env_final.get("users", [])])
        ue_serving = np.array([ue.get("serving_bs", -1) for ue in env_final.get("users", [])])
        area_size = tuple(env_final.get("area_size", [1000, 1000]))

        if len(bs_pos) > 0 and len(ue_pos) > 0:
            bs_ids = [bs["id"] for bs in env_final.get("base_stations", [])]
            serving_idx = np.array(
                [bs_ids.index(s) if s in bs_ids else -1 for s in ue_serving]
            )
            st.plotly_chart(
                plot_network_topology(bs_pos, ue_pos, serving_idx, area_size),
                use_container_width=True,
            )

    with col_right:
        st.subheader("SINR Heatmap")
        from telequm.simulator.network_env import NetworkEnvironment
        try:
            net_cfg = config.get("network", {})
            temp_env = NetworkEnvironment(net_cfg)
            st.plotly_chart(
                plot_sinr_heatmap(temp_env.sinr_matrix),
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"SINR heatmap error: {e}")

    # ── Coverage Map ─────────────────────────────────────────────
    st.subheader("📡 Coverage Heatmap")
    if HAS_PLOTLY and len(bs_pos) > 0:
        fig = _coverage_heatmap(bs_pos, area_size, config)
        st.plotly_chart(fig, use_container_width=True)

    # ── Time Series ──────────────────────────────────────────────
    st.subheader("📈 Performance Over Time")
    t1, t2 = st.columns(2)
    with t1:
        if metrics:
            st.plotly_chart(plot_throughput_series(metrics), use_container_width=True)
    with t2:
        if metrics:
            st.plotly_chart(plot_fairness_sinr(metrics), use_container_width=True)

    # ── Solver Comparison ────────────────────────────────────────
    if classical or quantum:
        st.subheader("⚔️ Classical vs Quantum")
        _solver_detail(classical, quantum)

    # ── Timestep Explorer ────────────────────────────────────────
    if metrics:
        st.subheader("🔍 Timestep Explorer")
        ts = st.slider("Select timestep", 0, len(metrics) - 1, len(metrics) - 1,
                        key="dt_ts_explore")
        m = metrics[ts]
        st.json(m)


def _coverage_heatmap(
    bs_positions: np.ndarray,
    area_size: tuple,
    config: dict,
) -> go.Figure:
    """Generate a coverage strength heatmap across the area."""
    resolution = 50
    x = np.linspace(0, area_size[0], resolution)
    y = np.linspace(0, area_size[1], resolution)
    X, Y = np.meshgrid(x, y)

    # Compute max received power at each grid point
    Z = np.full_like(X, -200.0)
    for bs in bs_positions:
        d = np.sqrt((X - bs[0]) ** 2 + (Y - bs[1]) ** 2)
        d = np.maximum(d, 1.0)
        freq = config.get("network", {}).get("base_stations", [{}])[0].get("frequency_ghz", 3.5)
        tx_power = config.get("network", {}).get("base_stations", [{}])[0].get("tx_power_dbm", 46)
        pl = 28 + 22 * np.log10(d) + 20 * np.log10(freq)
        rx = tx_power - pl
        Z = np.maximum(Z, rx)

    fig = go.Figure(data=go.Heatmap(
        x=x, y=y, z=Z,
        colorscale="Viridis",
        colorbar=dict(title="Rx Power (dBm)"),
    ))

    # Overlay BS markers
    fig.add_trace(go.Scatter(
        x=bs_positions[:, 0], y=bs_positions[:, 1],
        mode="markers",
        marker=dict(size=14, color=PALETTE["danger"], symbol="triangle-up",
                    line=dict(width=2, color="white")),
        name="Base Stations",
    ))

    fig.update_layout(
        title="Downlink Coverage Map",
        xaxis_title="X (m)", yaxis_title="Y (m)",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
        height=450,
    )
    return fig


def _solver_detail(classical: list, quantum: list):
    """Show detailed solver comparison."""
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Classical Solver**")
        if classical:
            last_c = classical[-1]
            st.metric("Cost", f"{last_c['cost']:.2f}")
            st.metric("Runtime", f"{last_c['runtime_s'] * 1000:.1f} ms")
            st.metric("Method", last_c.get("method", "N/A"))
        else:
            st.info("No classical solutions")

    with c2:
        st.markdown("**Quantum Solver**")
        if quantum:
            last_q = quantum[-1]
            st.metric("Cost", f"{last_q['cost']:.2f}")
            st.metric("Runtime", f"{last_q['runtime_s'] * 1000:.1f} ms")
            st.metric("Method", last_q.get("method", "N/A"))
        else:
            st.info("Quantum solver not enabled")

    # Cost improvement
    if classical and quantum:
        c_cost = classical[-1]["cost"]
        q_cost = quantum[-1]["cost"]
        if c_cost != 0:
            improvement = (c_cost - q_cost) / abs(c_cost) * 100
            delta_color = "normal" if improvement > 0 else "inverse"
            st.metric("Quantum Improvement", f"{improvement:+.1f}%",
                      delta=f"{'Better' if improvement > 0 else 'Worse'} than classical",
                      delta_color=delta_color)
