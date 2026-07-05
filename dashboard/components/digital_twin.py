"""
Digital Twin — Live Network Simulation Viewer
===============================================

DIFFERENT from Use-Case Lab:
- Use-Case Lab = single-shot problem solving (QUBO comparison)
- Digital Twin = time-series simulation with live metrics evolution

Shows: topology, coverage map, throughput/SINR over time,
allocation heatmaps, per-timestep exploration, and quantum
circuit execution details when quantum solver is enabled.
"""

from __future__ import annotations

import time

import numpy as np
import streamlit as st

from dashboard.utils.scenario_loader import build_config_from_sliders
from dashboard.utils.snapshot_manager import run_scenario, run_problem_direct
from dashboard.utils.plot_helpers import (
    plot_network_topology, plot_sinr_heatmap, plot_throughput_series,
    plot_fairness_sinr, plot_allocation_matrix, PALETTE,
)
from dashboard.utils.resource_monitor import (
    track_resources, estimate_qaoa_resources,
    estimate_classical_resources,
)

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


PROBLEM_TYPES = {
    "📡 PRB Allocation": "prb_allocation",
    "🔀 Routing Optimization": "routing",
    "📶 Beam Selection": "beam_selection",
    "⚡ Energy Efficiency": "energy_efficiency",
    "🔄 Handover Optimization": "handover",
    "🏗️ BS Placement": "bs_placement",
    "🌐 Quantum Network Routing": "quantum_routing",
}


def render():
    """Render the Digital Twin tab."""
    st.header("🌐 Digital Twin — Live Simulation")
    st.caption("Time-series simulation across network optimization and quantum-safe migration")

    twin_mode = st.radio(
        "Select Digital Twin Domain",
        ["📡 Live Network Optimization Twin (Timestep Evolution)", "🛡️ Quantum-Safe Migration & HNDL Risk Twin"],
        horizontal=True,
        key="twin_domain_sel",
    )
    st.divider()

    if twin_mode == "📡 Live Network Optimization Twin (Timestep Evolution)":
        _render_optimization_twin()
    else:
        _render_pqc_migration_twin()


def _render_pqc_migration_twin():
    from telequm.pqc.threat_models import HNDLCalculator
    from telequm.pqc.migration import MaturityLadder, MigrationExecutionChain

    st.subheader("🛡️ Quantum-Safe Network Migration & HNDL Risk Twin")
    st.markdown("""
    Simulate a 10-year transition timeline (2025–2035) for a national telecommunications operator migrating to Post-Quantum Cryptography (NIST FIPS 203/204). Track year-by-year PQC adoption percentage, cumulative data volume exposed to Harvest Now, Decrypt Later (HNDL) interception, and operational maturity progression!
    """)

    # ── Sidebar / Top Controls ───────────────────────────────────
    st.subheader("1️⃣ Operator & Migration Strategy Configuration")
    c1, c2, c3 = st.columns(3)
    with c1:
        n_bs = st.number_input("Total RAN Base Stations (5G DUs/CUs)", 100, 100000, 5000, step=500, key="dt_pqc_bs")
        n_core = st.number_input("Core Network Signaling Nodes", 10, 1000, 50, step=10, key="dt_pqc_core")
    with c2:
        pace = st.selectbox("Migration Rollout Strategy", ["Aggressive (4-5 Years)", "Balanced (7-8 Years)", "Lagging / Reactive (10+ Years)"], index=1, key="dt_pqc_pace")
        start_year = st.number_input("PQC Deployment Start Year", 2024, 2030, 2025, key="dt_pqc_start")
    with c3:
        q_horizon = st.slider("Quantum Horizon Z (CRQC Arrival Year)", 2028, 2040, 2033, key="dt_pqc_horizon")
        daily_tb = st.slider("Sensitive Traffic (TB / Day)", 10, 1000, 150, key="dt_pqc_tb")

    # ── Run 10-Year Simulation ───────────────────────────────────
    years = np.arange(2025, 2036)
    n_years = len(years)
    
    if "Aggressive" in pace:
        mig_duration = 5
    elif "Balanced" in pace:
        mig_duration = 7
    else:
        mig_duration = 10

    pqc_pct = []
    hndl_exposed_tb = []
    cum_hndl_pb = 0.0
    maturity_levels = []
    
    for y in years:
        if y < start_year:
            pct = 0.0
        else:
            elapsed = y - start_year + 1
            pct = min(100.0, (elapsed / mig_duration) * 100.0)
        pqc_pct.append(pct)
        
        if y < q_horizon:
            unprotected_pct = max(0.0, 100.0 - pct)
            exposed_tb_year = (unprotected_pct / 100.0) * daily_tb * 365
        else:
            unprotected_pct = max(0.0, 100.0 - pct)
            exposed_tb_year = (unprotected_pct / 100.0) * daily_tb * 365 * 2
            
        hndl_exposed_tb.append(exposed_tb_year)
        cum_hndl_pb += exposed_tb_year / 1000.0
        
        if pct == 0:
            mat = 0
        elif pct < 25:
            mat = 1
        elif pct < 60:
            mat = 2
        elif pct < 90:
            mat = 3
        else:
            mat = 4
        maturity_levels.append(mat)

    st.subheader("2️⃣ 10-Year Migration Simulation Results (2025–2035)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final PQC Adoption (2035)", f"{pqc_pct[-1]:.0f}%")
    m2.metric("Total HNDL Harvested Data", f"{cum_hndl_pb:.2f} PB", delta="Critical Risk!" if cum_hndl_pb > 10 else "Controlled", delta_color="inverse" if cum_hndl_pb > 10 else "normal")
    m3.metric("CRQC Threat Year", f"{q_horizon}")
    m4.metric("2035 Operational Maturity", f"Level {maturity_levels[-1]}")

    if HAS_PLOTLY:
        st.subheader("📈 PQC Rollout Trajectory & HNDL Vulnerability Window")
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(go.Scatter(x=years, y=pqc_pct, name="PQC Adoption (%)", line=dict(color=PALETTE["primary"], width=3)), secondary_y=False)
        fig.add_trace(go.Bar(name="Annual HNDL Harvested Data (TB)", x=years, y=hndl_exposed_tb, marker_color=PALETTE["danger"], opacity=0.6), secondary_y=True)
        
        fig.add_vline(x=q_horizon, line_width=2, line_dash="dash", line_color=PALETTE["warning"], annotation_text="CRQC Arrival (Shor's Threshold)")
        
        fig.update_layout(
            plot_bgcolor=PALETTE["bg"],
            paper_bgcolor=PALETTE["card"],
            font=dict(color=PALETTE["text"]),
            legend=dict(bgcolor=PALETTE["card"], orientation="h", y=1.1),
            height=450,
            xaxis_title="Year",
        )
        fig.update_yaxes(title_text="PQC Adoption (%)", range=[0, 105], secondary_y=False)
        fig.update_yaxes(title_text="Harvested Data Volume (TB / Year)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Year-by-Year Operator Migration Audit Table")
    import pandas as pd
    df_audit = pd.DataFrame({
        "Year": years,
        "PQC Adoption (%)": [f"{p:.1f}%" for p in pqc_pct],
        "AQC Maturity Level": [f"Level {m}" for m in maturity_levels],
        "Annual Harvested Data (TB)": [f"{v:,.1f} TB" for v in hndl_exposed_tb],
        "Status": ["🟢 Safe / Agility Prep" if y < q_horizon and p > 80 else ("🟡 Vulnerable Window" if y < q_horizon else ("🚨 CRQC COMPROMISE" if p < 100 else "🟢 Quantum Safe")) for y, p in zip(years, pqc_pct)],
    })
    st.dataframe(df_audit, use_container_width=True, hide_index=True)


def _render_optimization_twin():
    """Render the Digital Twin tab for network optimization."""
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
        st.subheader("📋 Problem")
        problem_label = st.selectbox(
            "Telecom Problem", list(PROBLEM_TYPES.keys()), key="dt_problem"
        )
        problem_type = PROBLEM_TYPES[problem_label]

        st.divider()
        st.subheader("⏱️ Simulation")
        timesteps = st.slider("Timesteps", 10, 200, 50, key="dt_ts")
        traffic = st.selectbox("Traffic", ["poisson", "video", "iot"], key="dt_traffic")
        mobility = st.selectbox("Mobility", ["pedestrian", "random_waypoint", "vehicular"],
                                key="dt_mob")

        st.divider()
        st.subheader("🔧 Solver")
        solver = st.selectbox("Classical Method",
                              ["greedy", "simulated_annealing", "exact"],
                              key="dt_solver")
        opt_interval = st.slider("Optimize every N steps", 5, 50, 10, key="dt_opt_int")

        st.divider()
        st.subheader("⚛️ Quantum")
        run_quantum = st.toggle("Compare with Quantum (QAOA)", value=False, key="dt_quantum")
        if run_quantum:
            max_q = st.slider("Max quantum variables", 4, 100, 20, key="dt_max_q")
            if max_q > 50:
                st.warning(
                    "🔴 **>50 qubits** — Requires **multi-CPU/GPU**. "
                    "RAM: ~{:.0f} GB.".format(2**max_q * 16 / (1024**3))
                )
            elif max_q > 30:
                st.info(
                    "🟡 **>30 qubits** — Slow on single CPU. "
                    "RAM: ~{:.2f} GB.".format(2**max_q * 16 / (1024**3))
                )

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
        _run_twin(config, problem_type, solver, run_quantum,
                  max_q if run_quantum else 20)


def _run_twin(config: dict, problem_type: str, solver_method: str,
              run_quantum: bool, max_q: int):
    """Execute scenario and render digital twin views."""
    progress = st.progress(0, text="Initializing simulation...")

    # ── 1. Run time-series simulation ────────────────────────────
    with track_resources() as res_report:
        t0 = time.time()
        results = run_scenario(config, verbose=False)
        sim_runtime = time.time() - t0

    progress.progress(50, text="Simulation done. Running QUBO comparison...")

    metrics = results["metrics"]
    env_final = results.get("environment_final", {})
    classical = results.get("classical_solutions", [])

    # ── 2. Run problem-specific QUBO solve on final state ────────
    qubo_config = config.copy()
    if run_quantum:
        qubo_config.setdefault("solver", {})["max_quantum_vars"] = max_q

    qubo_results = None
    try:
        qubo_results = run_problem_direct(
            qubo_config, problem_type=problem_type,
            solver_method=solver_method, run_quantum=run_quantum,
        )
    except Exception as e:
        st.warning(f"QUBO solve failed: {e}")

    progress.progress(100, text=f"✅ Complete in {sim_runtime:.2f}s")

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

    # ── QUBO Results & Quantum Details ───────────────────────────
    if qubo_results:
        st.subheader(f"📊 QUBO Solve — {problem_type.replace('_', ' ').title()}")

        c_res = qubo_results["classical_result"]
        q_res = qubo_results.get("quantum_result")
        c_met = qubo_results.get("classical_metrics") or {}
        q_met = qubo_results.get("quantum_metrics") or {}

        kc1, kc2, kc3 = st.columns(3)
        kc1.metric("Classical Cost", f"{c_res.get('cost', 'N/A')}")
        kc2.metric("Solver", c_res.get("method", solver_method).replace("_", " ").title())
        kc3.metric("QUBO Vars", qubo_results["num_vars"])

        # ── Quantum result section ────────────────────────────────
        if q_res is None:
            st.info("Quantum not enabled. Toggle ⚛️ in sidebar to compare.")
        elif "error" in q_res:
            st.warning(f"**Quantum:** {q_res['error']}")
        else:
            st.subheader("⚛️ Quantum Result")
            qc1, qc2, qc3 = st.columns(3)
            qc1.metric("Q Cost", f"{q_res.get('cost', 'N/A')}")
            qc2.metric("Method", q_res.get("method", "QAOA").replace("_", " ").title())
            qc3.metric("Runtime", f"{q_res.get('runtime_s', 0) * 1000:.1f} ms")

            if c_res.get("cost") and q_res.get("cost"):
                c_cost, q_cost = float(c_res["cost"]), float(q_res["cost"])
                if c_cost != 0:
                    imp = (c_cost - q_cost) / abs(c_cost) * 100
                    st.metric("⚡ Quantum vs Classical", f"{imp:+.1f}%",
                              delta="Better" if imp > 0 else "Worse")

            # ── 🔬 Circuit Execution ──────────────────────────────
            st.subheader("🔬 Quantum Circuit Execution")

            cs1, cs2, cs3, cs4 = st.columns(4)
            cs1.metric("🔲 Qubits", q_res.get("num_qubits", "?"))
            cs2.metric("📏 Depth", q_res.get("circuit_depth", "?"))
            cs3.metric("🧩 Gates", q_res.get("gate_count", "?"))
            cs4.metric("🎯 Shots", q_res.get("shots", 1024))

            circuit_text = q_res.get("circuit_text", "")
            if circuit_text:
                with st.expander("📐 Circuit Diagram", expanded=True):
                    st.code(circuit_text, language=None)

            opt_params = q_res.get("optimal_params")
            if opt_params:
                with st.expander("🎛️ Optimal Parameters"):
                    p = len(opt_params) // 2
                    gamma = opt_params[:p]
                    beta = opt_params[p:]
                    rows = ""
                    for i in range(p):
                        rows += f"| Layer {i+1} | {gamma[i]:.6f} | {beta[i]:.6f} |\n"
                    st.markdown(f"""
| Layer | γ (cost) | β (mixer) |
|-------|----------|-----------|
{rows}
                    """)

            conv = q_res.get("convergence_info", {})
            if conv:
                with st.expander("📊 Convergence Info"):
                    ci1, ci2, ci3 = st.columns(3)
                    ci1.metric("Func Evals", conv.get("nfev", "?"))
                    ci2.metric("Converged", "✅" if conv.get("success") else "❌")
                    ci3.metric("Final Cost", f"{conv.get('final_cost', 0):.4f}")

            history = q_res.get("optimization_history", [])
            if history and HAS_PLOTLY:
                with st.expander("📈 Convergence Plot", expanded=True):
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(range(len(history))), y=history,
                        mode="lines+markers",
                        line=dict(color=PALETTE["primary"], width=2),
                        marker=dict(size=4), name="Cost",
                    ))
                    fig.update_layout(
                        title="QAOA Optimization Convergence",
                        xaxis_title="Iteration", yaxis_title="Cost",
                        plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
                        font=dict(color=PALETTE["text"]), height=300,
                    )
                    st.plotly_chart(fig, use_container_width=True)

            counts = q_res.get("measurement_counts", {})
            if counts and HAS_PLOTLY:
                with st.expander("🎲 Measurement Distribution (Top 15)"):
                    top = sorted(counts.items(), key=lambda x: -x[1])[:15]
                    fig = go.Figure(data=[go.Bar(
                        x=[c[0] for c in top], y=[c[1] for c in top],
                        marker_color=PALETTE["primary"],
                    )])
                    fig.update_layout(
                        title="Top Bitstrings", xaxis_title="Bitstring",
                        yaxis_title="Count",
                        plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
                        font=dict(color=PALETTE["text"]), height=300,
                        xaxis=dict(tickangle=45),
                    )
                    st.plotly_chart(fig, use_container_width=True)

    # ── 🖥️ Resource Usage ────────────────────────────────────────
    st.subheader("🖥️ Compute Resources")
    r1, r2, r3 = st.columns(3)
    r1.metric("⏱️ Total Time", f"{res_report.wall_time_s:.2f}s")
    r2.metric("🧠 Peak RAM", f"{res_report.peak_ram_mb:.2f} MB")
    r3.metric("🔧 CPU Time", f"{res_report.cpu_time_s:.3f}s")

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
