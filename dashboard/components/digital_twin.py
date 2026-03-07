"""
Digital Twin — Live Network Simulation Viewer
===============================================

DIFFERENT from Use-Case Lab:
- Use-Case Lab = single-shot problem solving (QUBO comparison)
- Digital Twin = time-series simulation with live metrics evolution

Shows: topology, coverage map, throughput/SINR over time,
allocation heatmaps, and per-timestep exploration.
"""

from __future__ import annotations

import time

import numpy as np
import streamlit as st

from dashboard.utils.scenario_loader import build_config_from_sliders
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
    st.header("🌐 Digital Twin — Live Simulation")
    st.caption("Run a full time-series simulation and visualise network evolution")

    st.markdown("""
    > **How is this different from Use-Case Lab?**
    >
    > - **Use-Case Lab** = single-shot QUBO solve (compare problem formulations & solvers)
    > - **Digital Twin** = multi-timestep simulation (watch network metrics evolve over time)
    """)

    # ── Config (sidebar) ─────────────────────────────────────────
    with st.sidebar:
        st.subheader("🌐 Twin Config")
        num_bs = st.slider("Base Stations", 2, 8, 4, key="dt_bs")
        num_ue = st.slider("Users", 4, 30, 12, key="dt_ue")
        area = st.slider("Area (m)", 200, 3000, 1000, 100, key="dt_area")
        seed = st.number_input("Seed", 0, 9999, 42, key="dt_seed")

        st.divider()
        st.subheader("⏱️ Simulation")
        timesteps = st.slider("Timesteps", 10, 200, 50, key="dt_ts")
        traffic = st.selectbox("Traffic", ["poisson", "video", "iot"], key="dt_traffic")
        mobility = st.selectbox("Mobility", ["pedestrian", "random_waypoint", "vehicular"],
                                key="dt_mob")

        st.divider()
        st.subheader("🔧 Solver")
        solver = st.selectbox("Classical Method", ["greedy", "simulated_annealing"], key="dt_solver")
        opt_interval = st.slider("Optimize every N steps", 5, 50, 10, key="dt_opt_int")

    config = build_config_from_sliders(
        num_bs=num_bs, num_ue=num_ue,
        area_width=float(area), area_height=float(area),
        num_timesteps=timesteps,
        traffic_model=traffic, mobility_model=mobility,
        seed=int(seed), solver_method=solver,
    )
    config["simulation"]["optimization_interval"] = opt_interval

    # ── Run ───────────────────────────────────────────────────────
    if st.button("▶️ Run Simulation", type="primary", use_container_width=True, key="dt_run"):
        _run_twin(config)


def _run_twin(config: dict):
    """Execute scenario and render digital twin views."""
    progress = st.progress(0, text="Initializing...")

    t0 = time.time()
    results = run_scenario(config, verbose=False)
    runtime = time.time() - t0

    progress.progress(100, text=f"✅ Done in {runtime:.2f}s")

    metrics = results["metrics"]
    env_final = results.get("environment_final", {})
    classical = results.get("classical_solutions", [])

    # ── KPI Banner ───────────────────────────────────────────────
    if metrics:
        last = metrics[-1]
        first = metrics[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📶 Throughput", f"{last['avg_throughput_mbps']:.1f}",
                  delta=f"{last['avg_throughput_mbps'] - first['avg_throughput_mbps']:+.1f}")
        c2.metric("📡 SINR", f"{last['avg_sinr_db']:.1f} dB")
        c3.metric("⚖️ Fairness", f"{last['fairness_jain']:.3f}",
                  delta=f"{last['fairness_jain'] - first['fairness_jain']:+.3f}")
        c4.metric("👥 Active UEs", last["num_active_ues"])
        c5.metric("⏱️ Steps", f"{len(metrics)}")

    # ── Main Layout: Topology + Coverage ─────────────────────────
    st.subheader("📍 Network State")
    col_left, col_right = st.columns(2)

    bs_pos = np.array([bs["position"] for bs in env_final.get("base_stations", [])])
    ue_pos = np.array([ue["position"] for ue in env_final.get("users", [])])
    ue_serving = np.array([ue.get("serving_bs", -1) for ue in env_final.get("users", [])])
    area_size = tuple(env_final.get("area_size", [1000, 1000]))

    with col_left:
        if len(bs_pos) > 0 and len(ue_pos) > 0:
            bs_ids = [bs["id"] for bs in env_final.get("base_stations", [])]
            serving_idx = np.array(
                [bs_ids.index(s) if s in bs_ids else -1 for s in ue_serving]
            )
            st.plotly_chart(
                plot_network_topology(bs_pos, ue_pos, serving_idx, area_size,
                                      title="Final Topology"),
                use_container_width=True,
            )

    with col_right:
        if HAS_PLOTLY and len(bs_pos) > 0:
            st.plotly_chart(_coverage_heatmap(bs_pos, area_size, config),
                           use_container_width=True)

    # ── Time Series ──────────────────────────────────────────────
    st.subheader("📈 Performance Over Time")
    if metrics:
        t1, t2 = st.columns(2)
        with t1:
            st.plotly_chart(plot_throughput_series(metrics), use_container_width=True)
        with t2:
            st.plotly_chart(plot_fairness_sinr(metrics), use_container_width=True)

    # ── Solver Timeline ──────────────────────────────────────────
    if classical:
        st.subheader("🔧 Solver Costs Over Time")
        costs = [s["cost"] for s in classical]
        times = [s["timestep"] for s in classical]
        if HAS_PLOTLY:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=times, y=costs, mode="lines+markers",
                line=dict(color=PALETTE["primary"], width=2),
                marker=dict(size=6), name="Classical Cost",
            ))
            fig.update_layout(
                title="QUBO Cost at Optimization Steps",
                xaxis_title="Timestep", yaxis_title="Cost",
                plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
                font=dict(color=PALETTE["text"]), height=350,
            )
            fig.update_xaxes(gridcolor=PALETTE["grid"])
            fig.update_yaxes(gridcolor=PALETTE["grid"])
            st.plotly_chart(fig, use_container_width=True)

    # ── Timestep Explorer ────────────────────────────────────────
    if metrics:
        st.subheader("🔍 Timestep Explorer")
        ts = st.slider("Select timestep", 0, len(metrics) - 1, len(metrics) - 1,
                        key="dt_ts_explore")
        m = metrics[ts]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Step", m["timestep"])
        c2.metric("Throughput", f"{m['avg_throughput_mbps']:.1f}")
        c3.metric("SINR", f"{m['avg_sinr_db']:.1f}")
        c4.metric("Fairness", f"{m['fairness_jain']:.3f}")


def _coverage_heatmap(bs_positions, area_size, config):
    """Coverage strength heatmap."""
    resolution = 50
    x = np.linspace(0, area_size[0], resolution)
    y = np.linspace(0, area_size[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = np.full_like(X, -200.0)
    bs_list = config.get("network", {}).get("base_stations", [])
    for i, bs in enumerate(bs_positions):
        d = np.maximum(np.sqrt((X - bs[0])**2 + (Y - bs[1])**2), 1.0)
        freq = bs_list[0].get("frequency_ghz", 3.5) if bs_list else 3.5
        tx = bs_list[0].get("tx_power_dbm", 46) if bs_list else 46
        pl = 28 + 22 * np.log10(d) + 20 * np.log10(freq)
        Z = np.maximum(Z, tx - pl)

    fig = go.Figure(data=go.Heatmap(x=x, y=y, z=Z, colorscale="Viridis",
                                     colorbar=dict(title="Rx (dBm)")))
    fig.add_trace(go.Scatter(
        x=bs_positions[:, 0], y=bs_positions[:, 1], mode="markers",
        marker=dict(size=14, color=PALETTE["danger"], symbol="triangle-up",
                    line=dict(width=2, color="white")),
        name="BS",
    ))
    fig.update_layout(
        title="Coverage Map", xaxis_title="X (m)", yaxis_title="Y (m)",
        plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]), height=450,
    )
    return fig
