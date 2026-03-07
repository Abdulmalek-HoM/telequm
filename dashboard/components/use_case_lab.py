"""
Use-Case Lab — Scenario-Driven Experiments
============================================

Dashboard tab for running interactive experiments:
- Select preset or upload custom YAML config
- Configure via sliders
- Run simulation on isolated snapshot
- View metrics and solver comparison
- Export results as CSV/PNG
"""

from __future__ import annotations

import json
import time

import numpy as np
import streamlit as st

from dashboard.utils.scenario_loader import (
    list_presets, load_preset, parse_uploaded_yaml, build_config_from_sliders,
)
from dashboard.utils.snapshot_manager import run_scenario, get_env_summary
from dashboard.utils.plot_helpers import (
    plot_network_topology, plot_sinr_heatmap, plot_throughput_series,
    plot_fairness_sinr, plot_solver_comparison, plot_allocation_matrix,
    metrics_to_csv, PALETTE,
)


def render():
    """Render the Use-Case Lab tab."""
    st.header("🧪 Use-Case Lab")
    st.caption("Run scenario-driven experiments on isolated network snapshots")

    # ── Scenario Selection ───────────────────────────────────────
    source = st.radio(
        "Scenario source",
        ["🎛️ Interactive Sliders", "📁 Preset Config", "📤 Upload YAML"],
        horizontal=True,
        key="scenario_source",
    )

    config = None

    if source == "🎛️ Interactive Sliders":
        config = _slider_config()
    elif source == "📁 Preset Config":
        config = _preset_config()
    elif source == "📤 Upload YAML":
        config = _upload_config()

    if config is None:
        st.info("Configure a scenario above to begin.")
        return

    # ── Config Summary ───────────────────────────────────────────
    with st.expander("📋 Scenario Config", expanded=False):
        st.json(config)

    # ── Run Simulation ───────────────────────────────────────────
    if st.button("🚀 Run Experiment", type="primary", use_container_width=True):
        _run_and_display(config)


# ─── Config Builders ─────────────────────────────────────────────

def _slider_config() -> dict:
    st.subheader("Configure Network")
    c1, c2, c3 = st.columns(3)
    with c1:
        num_bs = st.slider("Base Stations", 2, 8, 4, key="lab_bs")
        tx_power = st.slider("Tx Power (dBm)", 30.0, 50.0, 46.0, key="lab_txp")
    with c2:
        num_ue = st.slider("Users", 4, 30, 10, key="lab_ue")
        freq = st.slider("Frequency (GHz)", 0.7, 6.0, 3.5, 0.1, key="lab_freq")
    with c3:
        area = st.slider("Area (m)", 200, 3000, 1000, 100, key="lab_area")
        seed = st.number_input("Random Seed", 0, 9999, 42, key="lab_seed")

    st.subheader("Simulation Parameters")
    c4, c5 = st.columns(2)
    with c4:
        timesteps = st.slider("Timesteps", 10, 200, 50, key="lab_ts")
        traffic = st.selectbox("Traffic Model", ["poisson", "video", "iot"], key="lab_traffic")
    with c5:
        mobility = st.selectbox("Mobility Model",
                                ["pedestrian", "random_waypoint", "vehicular"],
                                key="lab_mobility")
        solver = st.selectbox("Classical Solver",
                              ["greedy", "simulated_annealing"],
                              key="lab_solver")

    run_quantum = st.checkbox("Enable Quantum Solver (QAOA)", value=False, key="lab_quantum")

    return build_config_from_sliders(
        num_bs=num_bs, num_ue=num_ue,
        area_width=float(area), area_height=float(area),
        tx_power_dbm=tx_power, frequency_ghz=freq,
        num_timesteps=timesteps,
        traffic_model=traffic, mobility_model=mobility,
        seed=int(seed), solver_method=solver, run_quantum=run_quantum,
    )


def _preset_config() -> dict | None:
    presets = list_presets()
    if not presets:
        st.warning("No preset configs found in `experiments/`.")
        return None

    names = [p["name"] for p in presets]
    idx = st.selectbox("Select preset", range(len(names)),
                       format_func=lambda i: f"{names[i]} — {presets[i]['description']}",
                       key="lab_preset")
    return load_preset(presets[idx]["path"])


def _upload_config() -> dict | None:
    uploaded = st.file_uploader("Upload YAML config", type=["yaml", "yml"],
                                key="lab_upload")
    if uploaded is None:
        return None
    try:
        content = uploaded.read().decode("utf-8")
        config = parse_uploaded_yaml(content)
        st.success("✅ Config parsed successfully")
        return config
    except ValueError as e:
        st.error(f"❌ {e}")
        return None


# ─── Execution & Display ─────────────────────────────────────────

def _run_and_display(config: dict):
    with st.spinner("Running simulation..."):
        t0 = time.time()
        results = run_scenario(config, verbose=False)
        runtime = time.time() - t0

    metrics = results["metrics"]
    classical = results.get("classical_solutions", [])
    quantum = results.get("quantum_solutions", [])
    env_final = results.get("environment_final", {})

    st.success(f"✅ Simulation complete in **{runtime:.2f}s** — "
               f"{len(metrics)} timesteps")

    # ── KPI Cards ────────────────────────────────────────────────
    if metrics:
        last = metrics[-1]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Avg Throughput", f"{last['avg_throughput_mbps']:.1f} Mbps")
        k2.metric("Avg SINR", f"{last['avg_sinr_db']:.1f} dB")
        k3.metric("Jain Fairness", f"{last['fairness_jain']:.3f}")
        k4.metric("Active UEs", f"{last['num_active_ues']}")

    # ── Plots ────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Throughput", "📡 SINR & Fairness", "🗺️ Topology",
        "🔥 SINR Heatmap", "⚔️ Solver Comparison",
    ])

    with tab1:
        if metrics:
            st.plotly_chart(plot_throughput_series(metrics), use_container_width=True)

    with tab2:
        if metrics:
            st.plotly_chart(plot_fairness_sinr(metrics), use_container_width=True)

    with tab3:
        snap = results.get("environment_final", {})
        bs_pos = np.array([bs["position"] for bs in snap.get("base_stations", [])])
        ue_pos = np.array([ue["position"] for ue in snap.get("users", [])])
        ue_serving = np.array([ue.get("serving_bs", -1) for ue in snap.get("users", [])])
        area = tuple(snap.get("area_size", [1000, 1000]))
        if len(bs_pos) > 0 and len(ue_pos) > 0:
            # Map serving BS IDs to indices
            bs_ids = [bs["id"] for bs in snap.get("base_stations", [])]
            serving_idx = np.array([bs_ids.index(s) if s in bs_ids else -1 for s in ue_serving])
            st.plotly_chart(
                plot_network_topology(bs_pos, ue_pos, serving_idx, area),
                use_container_width=True,
            )

    with tab4:
        # Reconstruct SINR from final env
        from telequm.simulator.network_env import NetworkEnvironment
        try:
            net_cfg = config.get("network", {})
            temp_env = NetworkEnvironment(net_cfg)
            st.plotly_chart(
                plot_sinr_heatmap(temp_env.sinr_matrix),
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Could not compute SINR heatmap: {e}")

    with tab5:
        if classical or quantum:
            st.plotly_chart(
                plot_solver_comparison(classical, quantum),
                use_container_width=True,
            )
        else:
            st.info("No solver solutions to compare.")

    # ── Export ────────────────────────────────────────────────────
    st.divider()
    st.subheader("📥 Export Results")
    c1, c2 = st.columns(2)
    with c1:
        csv = metrics_to_csv(metrics)
        st.download_button("⬇️ Download Metrics CSV", csv,
                           "telequm_metrics.csv", "text/csv")
    with c2:
        json_str = json.dumps({
            "config": config,
            "metrics": metrics,
            "classical_count": len(classical),
            "quantum_count": len(quantum),
        }, indent=2, default=str)
        st.download_button("⬇️ Download Full JSON", json_str,
                           "telequm_results.json", "application/json")
