"""
Use-Case Lab — Scenario-Driven Experiments
============================================

Dashboard tab for running interactive experiments with:
- Multiple telecom problems (PRB, Routing, Beam, Energy, Handover)
- Multiple solvers (Greedy, SA, Exact, Hybrid, Quantum QAOA)
- Network topology and SINR visualizations
- Full simulation mode with time-series plots
"""

from __future__ import annotations

import json
import time

import numpy as np
import streamlit as st

from dashboard.utils.scenario_loader import (
    list_presets, load_preset, parse_uploaded_yaml, build_config_from_sliders,
)
from dashboard.utils.snapshot_manager import run_problem_direct, run_scenario
from dashboard.utils.plot_helpers import (
    plot_network_topology, plot_sinr_heatmap, plot_throughput_series,
    plot_fairness_sinr, plot_solver_comparison, plot_allocation_matrix,
    metrics_to_csv, PALETTE,
)
from dashboard.utils.resource_monitor import (
    track_resources, estimate_qaoa_resources, estimate_vqe_resources,
    estimate_classical_resources, estimate_statevector_ram,
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

SOLVER_METHODS = {
    "🟢 Greedy (fast)": "greedy",
    "🔵 Simulated Annealing": "simulated_annealing",
    "🟡 Exact Brute-Force (small only)": "exact",
    "🟣 Hybrid — Quantum First": "hybrid_quantum_first",
    "🟠 Hybrid — Ensemble (best of all)": "hybrid_ensemble",
}


def render():
    """Render the Use-Case Lab tab."""
    st.header("🧪 Use-Case Lab")
    st.caption("Select a problem, choose a solver, and compare classical vs quantum solutions")

    # ── 1. Network Setup ─────────────────────────────────────────
    st.subheader("1️⃣ Network Configuration")
    config = _network_config()

    # ── 2. Problem Selection ─────────────────────────────────────
    st.subheader("2️⃣ Problem Formulation")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        problem_label = st.selectbox("Telecom Problem", list(PROBLEM_TYPES.keys()), key="lab_problem")
    problem_type = PROBLEM_TYPES[problem_label]
    with col_p2:
        n_bs = len(config.get("network", {}).get("base_stations", []))
        n_ue = len(config.get("network", {}).get("users", []))
        var_est = _estimate_vars(problem_type, n_ue, n_bs)
        st.metric("QUBO Variables", f"{var_est}", help="Number of binary variables in the QUBO")

    _problem_description(problem_type)

    # ── 3. Solver Selection ──────────────────────────────────────
    st.subheader("3️⃣ Solver Selection")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        solver_label = st.selectbox("Classical / Hybrid Solver", list(SOLVER_METHODS.keys()), key="lab_solver")
    solver_method = SOLVER_METHODS[solver_label]

    with col_s2:
        run_quantum = st.toggle("⚛️ Compare with Quantum (QAOA)", value=False, key="lab_quantum")
        if run_quantum:
            max_q = st.slider("Max quantum variables", 4, 100, 20, key="lab_max_q")
            config.setdefault("solver", {})["max_quantum_vars"] = max_q
            if max_q > 50:
                st.warning(
                    "🔴 **>50 qubits** — Statevector simulation requires **multi-CPU or GPU** "
                    "architecture. RAM: ~{:.0f} GB. Expect long runtimes on standard hardware.".format(
                        2**max_q * 16 / (1024**3)
                    )
                )
            elif max_q > 30:
                st.info(
                    "🟡 **>30 qubits** — Simulation will be slow on a single CPU. "
                    "RAM estimate: ~{:.2f} GB statevector.".format(
                        2**max_q * 16 / (1024**3)
                    )
                )
            if var_est > max_q:
                st.warning(f"⚠️ Problem has **{var_est}** vars but quantum limit is **{max_q}**. "
                           f"Reduce network size or increase limit.")

    # ── 4. Simulation Mode ───────────────────────────────────────
    st.subheader("4️⃣ Experiment Mode")
    mode = st.radio(
        "Mode",
        ["⚡ Single-Shot QUBO", "📈 Full Simulation (with time-series)"],
        horizontal=True, key="lab_mode",
    )

    if mode == "📈 Full Simulation (with time-series)":
        c1, c2, c3 = st.columns(3)
        with c1:
            timesteps = st.slider("Timesteps", 10, 100, 30, key="lab_ts")
        with c2:
            traffic = st.selectbox("Traffic Model", ["poisson", "video", "iot"], key="lab_traffic")
        with c3:
            mobility = st.selectbox("Mobility Model", ["pedestrian", "random_waypoint", "vehicular"],
                                    key="lab_mobility")
        config["simulation"] = {
            "num_timesteps": timesteps, "dt": 1.0,
            "random_seed": config.get("network", {}).get("random_seed", 42),
            "channel_update_interval": 5, "optimization_interval": 5,
        }
        config["traffic"] = {"model": traffic, "arrival_rate": 1.0, "session_rate_mbps": 5.0}
        config["mobility"] = {"model": mobility, "speed_mean": 1.2}
        config["solver"] = {"classical_method": solver_method.split("hybrid_")[0] if "hybrid" in solver_method else solver_method,
                            "run_quantum": False}

    # ── 5. Run ───────────────────────────────────────────────────
    st.divider()
    if st.button("🚀 Run Experiment", type="primary", use_container_width=True):
        if mode == "⚡ Single-Shot QUBO":
            _run_single_shot(config, problem_type, solver_method, run_quantum)
        else:
            _run_full_simulation(config, problem_type, solver_method)


# ─── Network Config Builder ──────────────────────────────────────

def _network_config() -> dict:
    source = st.radio("Source", ["🎛️ Sliders", "📁 Preset", "📤 Upload YAML"],
                      horizontal=True, key="lab_source")

    if source == "📁 Preset":
        presets = list_presets()
        if presets:
            idx = st.selectbox("Preset", range(len(presets)),
                               format_func=lambda i: presets[i]["name"], key="lab_preset")
            return load_preset(presets[idx]["path"])
        st.warning("No presets found")

    if source == "📤 Upload YAML":
        up = st.file_uploader("YAML config", type=["yaml", "yml"], key="lab_upload")
        if up:
            try:
                return parse_uploaded_yaml(up.read().decode())
            except ValueError as e:
                st.error(str(e))

    # Default: sliders
    c1, c2, c3 = st.columns(3)
    with c1:
        num_bs = st.slider("Base Stations", 2, 8, 3, key="lab_bs")
        tx_power = st.slider("Tx Power (dBm)", 30.0, 50.0, 46.0, key="lab_txp")
    with c2:
        num_ue = st.slider("Users", 2, 20, 6, key="lab_ue")
        freq = st.slider("Frequency (GHz)", 0.7, 6.0, 3.5, 0.1, key="lab_freq")
    with c3:
        area = st.slider("Area (m)", 200, 3000, 1000, 100, key="lab_area")
        seed = st.number_input("Seed", 0, 9999, 42, key="lab_seed")

    return build_config_from_sliders(
        num_bs=num_bs, num_ue=num_ue,
        area_width=float(area), area_height=float(area),
        tx_power_dbm=tx_power, frequency_ghz=freq,
        num_timesteps=1, seed=int(seed),
    )


# ─── Problem Info ─────────────────────────────────────────────────

def _problem_description(problem_type: str):
    descriptions = {
        "prb_allocation": (
            "**PRB Allocation** — Assign users to base stations maximising SINR-weighted throughput. "
            "Constraints: each user → one BS, per-BS capacity."
        ),
        "routing": (
            "**Routing** — Find optimal routing paths through cell graph, "
            "weighted by aggregate SINR strength."
        ),
        "beam_selection": (
            "**Beam Selection** — Select discrete beams from a codebook for each user. "
            "One beam per user constraint."
        ),
        "energy_efficiency": (
            "**Energy Efficiency** — Decide which cells to keep active (cell on/off) "
            "while maintaining coverage. Trade-off: SINR vs energy."
        ),
        "handover": (
            "**Handover Optimization** — Reassign users to cells while minimising "
            "unnecessary handovers. Penalises deviations from current serving cell."
        ),
        "bs_placement": (
            "**BS Placement** — Facility location: select which candidate sites to build "
            "base stations on, maximising coverage under a budget constraint."
        ),
        "quantum_routing": (
            "**Quantum Network Routing** — Route entanglement / QKD keys through a "
            "network of quantum repeaters, maximising end-to-end fidelity."
        ),
    }
    st.info(descriptions.get(problem_type, ""))


def _estimate_vars(problem_type: str, n_ue: int, n_bs: int) -> int:
    if problem_type == "prb_allocation":
        return n_ue * n_bs
    elif problem_type == "routing":
        return n_bs * n_bs
    elif problem_type == "beam_selection":
        return n_ue * 8
    elif problem_type == "energy_efficiency":
        return n_bs + n_ue * n_bs
    elif problem_type == "handover":
        return n_ue * n_bs
    elif problem_type == "bs_placement":
        return n_bs
    elif problem_type == "quantum_routing":
        return n_bs * n_bs
    return n_ue * n_bs


# ─── Single-Shot QUBO Execution ──────────────────────────────────

def _run_single_shot(config: dict, problem_type: str, solver_method: str, run_quantum: bool):
    with st.spinner(f"Solving {problem_type} with {solver_method}..."):
        with track_resources() as res_report:
            results = run_problem_direct(
                config, problem_type=problem_type,
                solver_method=solver_method, run_quantum=run_quantum,
            )
        total = res_report.wall_time_s

    st.success(f"✅ Complete in **{total:.2f}s** — {results['num_vars']} QUBO variables")

    # ── KPI Cards ────────────────────────────────────────────────
    info = results["snapshot_info"]
    c_met = results.get("classical_metrics") or {}

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🏗️ Cells", info["num_cells"])
    k2.metric("👥 Users", info["num_users"])
    k3.metric("📊 QUBO Vars", results["num_vars"])
    k4.metric("⏱️ Runtime", f"{total:.3f}s")

    # ── 📍 Network State ─────────────────────────────────────────
    st.subheader("📍 Network State")
    bs_pos = results.get("bs_positions")
    ue_pos = results.get("ue_positions")
    sinr_mat = results.get("sinr_matrix")
    serving = results.get("serving_cells")

    if bs_pos is not None and ue_pos is not None:
        col_topo, col_sinr = st.columns(2)

        with col_topo:
            fig = plot_network_topology(
                bs_pos, ue_pos, serving,
                tuple(info["area_size"]),
                title="Network Topology + Association",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_sinr:
            if sinr_mat is not None:
                fig = plot_sinr_heatmap(
                    sinr_mat, title="SINR Matrix (UE × Cell)"
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Allocation Matrix ────────────────────────────────────────
    alloc = results.get("allocation_matrix")
    if alloc is not None and isinstance(alloc, np.ndarray) and alloc.ndim == 2:
        st.subheader("🗺️ Allocation Heatmap")
        fig = plot_allocation_matrix(alloc)
        st.plotly_chart(fig, use_container_width=True)

    # ── Classical Result ─────────────────────────────────────────
    st.subheader("📊 Classical Result")
    c_res = results["classical_result"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Method", c_res.get("method", solver_method).replace("_", " ").title())
    col2.metric("QUBO Cost", f"{c_res.get('cost', 'N/A')}")
    col3.metric("Runtime", f"{c_res.get('runtime_s', 0) * 1000:.1f} ms")

    if c_met:
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Avg Throughput", f"{c_met.get('avg_throughput_mbps', 0):.1f} Mbps")
        mc2.metric("Sum Throughput", f"{c_met.get('sum_throughput_mbps', 0):.1f} Mbps")
        mc3.metric("Jain Fairness", f"{c_met.get('fairness_jain', 0):.3f}")

    # ── Quantum Result ───────────────────────────────────────────
    st.subheader("⚛️ Quantum Result")
    q_res = results.get("quantum_result")
    q_met = results.get("quantum_metrics") or {}

    if q_res is None:
        st.info("Quantum comparison not enabled. Toggle the ⚛️ switch above to compare.")
    elif "error" in q_res:
        st.warning(f"**Quantum could not run:** {q_res['error']}")
        if "num_vars" in q_res:
            st.caption(f"💡 Tip: Reduce to ≤ {q_res.get('max_quantum_vars', 20)} vars "
                       f"(current: {q_res['num_vars']} vars)")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Method", q_res.get("method", "QAOA").replace("_", " ").title())
        col2.metric("QUBO Cost", f"{q_res.get('cost', 'N/A')}")
        col3.metric("Runtime", f"{q_res.get('runtime_s', 0) * 1000:.1f} ms")

        if c_res.get("cost") and q_res.get("cost"):
            c_cost, q_cost = float(c_res["cost"]), float(q_res["cost"])
            if c_cost != 0:
                improvement = (c_cost - q_cost) / abs(c_cost) * 100
                st.metric("⚡ Quantum vs Classical",
                          f"{improvement:+.1f}%",
                          delta="Better" if improvement > 0 else "Worse")

        if q_met:
            mc1, mc2 = st.columns(2)
            mc1.metric("Q Throughput", f"{q_met.get('avg_throughput_mbps', 0):.1f} Mbps")
            mc2.metric("Q Fairness", f"{q_met.get('fairness_jain', 0):.3f}")

        # ── 🔬 Quantum Circuit Execution Details ─────────────────
        st.subheader("🔬 Quantum Circuit Execution")

        # Circuit stats
        cs1, cs2, cs3, cs4 = st.columns(4)
        cs1.metric("🔲 Qubits", q_res.get("num_qubits", q_res.get("num_vars", "?")))
        cs2.metric("📏 Depth", q_res.get("circuit_depth", "?"))
        cs3.metric("🧩 Gates", q_res.get("gate_count", "?"))
        cs4.metric("🎯 Shots", q_res.get("shots", 1024))

        # Circuit diagram
        circuit_text = q_res.get("circuit_text", "")
        if circuit_text:
            with st.expander("📐 Circuit Diagram", expanded=True):
                st.code(circuit_text, language=None)

        # Optimal parameters
        opt_params = q_res.get("optimal_params")
        if opt_params:
            with st.expander("🎛️ Optimal QAOA/VQE Parameters"):
                p = len(opt_params) // 2
                gamma = opt_params[:p]
                beta = opt_params[p:]
                param_rows = ""
                for i in range(p):
                    param_rows += f"| Layer {i+1} | {gamma[i]:.6f} | {beta[i]:.6f} |\n"
                st.markdown(f"""
| Layer | γ (cost) | β (mixer) |
|-------|----------|-----------|
{param_rows}
                """)

        # Convergence info
        conv = q_res.get("convergence_info", {})
        if conv:
            with st.expander("📊 Convergence Info"):
                ci1, ci2, ci3 = st.columns(3)
                ci1.metric("Func Evals", conv.get("nfev", "?"))
                ci2.metric("Converged", "✅" if conv.get("success") else "❌")
                ci3.metric("Final Cost", f"{conv.get('final_cost', 0):.4f}")
                if conv.get("message"):
                    st.caption(f"Optimizer: {conv['message']}")

        # Optimization history (convergence plot)
        history = q_res.get("optimization_history", [])
        if history and HAS_PLOTLY:
            with st.expander("📈 Convergence Plot", expanded=True):
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(len(history))), y=history,
                    mode="lines+markers",
                    line=dict(color=PALETTE["primary"], width=2),
                    marker=dict(size=4),
                    name="Cost per Iteration",
                ))
                fig.update_layout(
                    title="QAOA/VQE Optimization Convergence",
                    xaxis_title="Iteration", yaxis_title="Expectation Value",
                    plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
                    font=dict(color=PALETTE["text"]), height=350,
                )
                fig.update_xaxes(gridcolor=PALETTE["grid"])
                fig.update_yaxes(gridcolor=PALETTE["grid"])
                st.plotly_chart(fig, use_container_width=True)

        # Measurement distribution
        counts = q_res.get("measurement_counts", {})
        if counts and HAS_PLOTLY:
            with st.expander("🎲 Measurement Distribution (Top 15)"):
                sorted_counts = sorted(counts.items(), key=lambda x: -x[1])[:15]
                labels = [c[0] for c in sorted_counts]
                values = [c[1] for c in sorted_counts]
                fig = go.Figure(data=[go.Bar(
                    x=labels, y=values,
                    marker_color=PALETTE["primary"],
                )])
                fig.update_layout(
                    title="Measurement Counts (Top Bitstrings)",
                    xaxis_title="Bitstring", yaxis_title="Count",
                    plot_bgcolor=PALETTE["bg"], paper_bgcolor=PALETTE["card"],
                    font=dict(color=PALETTE["text"]), height=350,
                    xaxis=dict(tickangle=45),
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── 📋 Problem-Specific Evaluation ────────────────────────────
    st.subheader("📋 Solution Evaluation")
    _show_evaluation_metrics(problem_type, c_res, c_met, q_res, q_met)

    # ── 🖥️ Resource Usage ─────────────────────────────────────────
    st.subheader("🖥️ Compute Resources Used")
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("⏱️ Wall Time", f"{res_report.wall_time_s * 1000:.1f} ms")
    rc2.metric("🧠 Peak RAM", f"{res_report.peak_ram_mb:.2f} MB")
    rc3.metric("🔧 CPU Time", f"{res_report.cpu_time_s * 1000:.1f} ms")
    rc4.metric("📊 QUBO Vars", results["num_vars"])

    # Show estimated resources for the algorithm
    n_vars = results["num_vars"]
    if "hybrid" in solver_method or solver_method == "greedy":
        est = estimate_classical_resources(n_vars, "greedy")
    elif solver_method == "simulated_annealing":
        est = estimate_classical_resources(n_vars, "simulated_annealing")
    elif solver_method == "exact":
        est = estimate_classical_resources(n_vars, "exact")
    else:
        est = estimate_classical_resources(n_vars, "greedy")

    with st.expander("📐 Algorithm Complexity Estimate"):
        st.markdown(f"""
        | Property | Value |
        |----------|-------|
        | **Algorithm** | {est.get('algorithm', solver_method)} |
        | **Time Complexity** | {est.get('time_complexity', 'N/A')} |
        | **Space Complexity** | {est.get('space_complexity', 'N/A')} |
        | **Estimated RAM** | {est.get('ram_mb', 0):.4f} MB |
        | **Actual Peak RAM** | {res_report.peak_ram_mb:.2f} MB |
        """)
        if run_quantum:
            q_est = estimate_qaoa_resources(n_vars, 2, n_vars * (n_vars - 1) // 2)
            st.markdown(f"""
        | **QAOA Qubits** | {q_est['num_qubits']} |
        | **QAOA Gates** | {q_est['total_gates']} |
        | **QAOA Depth** | {q_est['circuit_depth']} |
        | **Statevector RAM** | {q_est['ram_mb']:,.2f} MB |
            """)

    # ── Export ────────────────────────────────────────────────────
    st.divider()
    _export_section(results, c_res, q_res, c_met, q_met)


# ─── Full Simulation Mode ────────────────────────────────────────

def _run_full_simulation(config: dict, problem_type: str, solver_method: str):
    with st.spinner("Running full simulation..."):
        t0 = time.time()
        results = run_scenario(config, verbose=False)
        total = time.time() - t0

    metrics = results.get("metrics", [])
    classical = results.get("classical_solutions", [])
    env_final = results.get("environment_final", {})

    st.success(f"✅ Simulation complete in **{total:.2f}s** — {len(metrics)} timesteps")

    if not metrics:
        st.warning("No metrics collected.")
        return

    # ── KPI Banner ───────────────────────────────────────────────
    last, first = metrics[-1], metrics[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📶 Throughput", f"{last['avg_throughput_mbps']:.1f}",
              delta=f"{last['avg_throughput_mbps'] - first['avg_throughput_mbps']:+.1f}")
    k2.metric("📡 SINR", f"{last['avg_sinr_db']:.1f} dB")
    k3.metric("⚖️ Fairness", f"{last['fairness_jain']:.3f}",
              delta=f"{last['fairness_jain'] - first['fairness_jain']:+.3f}")
    k4.metric("👥 Active UEs", last["num_active_ues"])

    # ── 📍 Network State ─────────────────────────────────────────
    st.subheader("📍 Network State")
    bs_pos = np.array([bs["position"] for bs in env_final.get("base_stations", [])])
    ue_pos = np.array([ue["position"] for ue in env_final.get("users", [])])
    serving = np.array([ue.get("serving_bs", -1) for ue in env_final.get("users", [])])
    area_size = tuple(env_final.get("area_size", [1000, 1000]))

    if len(bs_pos) > 0 and len(ue_pos) > 0:
        bs_ids = [bs["id"] for bs in env_final.get("base_stations", [])]
        serving_idx = np.array([bs_ids.index(s) if s in bs_ids else -1 for s in serving])
        st.plotly_chart(
            plot_network_topology(bs_pos, ue_pos, serving_idx, area_size,
                                  title="Final Network Topology"),
            use_container_width=True,
        )

    # ── 📈 Performance Over Time ─────────────────────────────────
    st.subheader("📈 Performance Over Time")
    t1, t2 = st.columns(2)
    with t1:
        st.plotly_chart(plot_throughput_series(metrics), use_container_width=True)
    with t2:
        st.plotly_chart(plot_fairness_sinr(metrics), use_container_width=True)

    # ── 🔧 Solver Costs Over Time ────────────────────────────────
    if classical and HAS_PLOTLY:
        st.subheader("🔧 Solver Costs Over Time")
        costs = [s["cost"] for s in classical]
        times = [s["timestep"] for s in classical]
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

    # ── Export ────────────────────────────────────────────────────
    st.divider()
    csv_data = metrics_to_csv(metrics)
    st.download_button("⬇️ Download Metrics CSV", csv_data,
                       "telequm_metrics.csv", "text/csv")


# ─── Export Section ───────────────────────────────────────────────

def _export_section(results, c_res, q_res, c_met, q_met):
    st.subheader("📥 Export")
    export = {
        "problem_type": results["problem_type"],
        "solver_method": results["solver_method"],
        "num_vars": results["num_vars"],
        "classical_cost": c_res.get("cost"),
        "quantum_cost": q_res.get("cost") if q_res and "cost" in q_res else None,
        "classical_metrics": c_met,
        "quantum_metrics": q_met,
    }
    st.download_button("⬇️ Download Results JSON",
                       json.dumps(export, indent=2, default=str),
                       "telequm_results.json", "application/json")


# ─── Problem-Specific Evaluation ─────────────────────────────────

def _show_evaluation_metrics(problem_type, c_res, c_met, q_res, q_met):
    """Display problem-specific evaluation metrics side-by-side."""

    def _fmt(v, fmt=".2f"):
        if v is None or v == 0:
            return "—"
        return f"{v:{fmt}}"

    if problem_type == "prb_allocation":
        st.markdown("**PRB Allocation Evaluation**")
        cols = st.columns(4)
        cols[0].metric("C: Throughput", f"{c_met.get('avg_throughput_mbps', 0):.1f} Mbps")
        cols[1].metric("C: Fairness", _fmt(c_met.get('fairness_jain')))
        if q_met:
            cols[2].metric("Q: Throughput", f"{q_met.get('avg_throughput_mbps', 0):.1f} Mbps")
            cols[3].metric("Q: Fairness", _fmt(q_met.get('fairness_jain')))

    elif problem_type == "routing":
        st.markdown("**Routing Evaluation**")
        cols = st.columns(3)
        cols[0].metric("C: Edges Used", c_met.get("num_edges", "—"))
        cols[1].metric("C: Cost", _fmt(c_res.get("cost")))
        if q_res and "cost" in q_res:
            cols[2].metric("Q: Cost", _fmt(q_res.get("cost")))

    elif problem_type == "beam_selection":
        st.markdown("**Beam Selection Evaluation**")
        cols = st.columns(3)
        cols[0].metric("C: Assigned", c_met.get("num_assigned", "—"))
        cols[1].metric("C: Cost", _fmt(c_res.get("cost")))
        if q_res and "cost" in q_res:
            cols[2].metric("Q: Cost", _fmt(q_res.get("cost")))

    elif problem_type == "energy_efficiency":
        st.markdown("**Energy Efficiency Evaluation**")
        cols = st.columns(4)
        cols[0].metric("C: Active Cells", c_met.get("active_cells", "—"))
        cols[1].metric("C: Energy Saved", f"{c_met.get('energy_saved_pct', 0):.1f}%")
        if q_met:
            cols[2].metric("Q: Active Cells", q_met.get("active_cells", "—"))
            cols[3].metric("Q: Energy Saved", f"{q_met.get('energy_saved_pct', 0):.1f}%")

    elif problem_type == "handover":
        st.markdown("**Handover Evaluation**")
        cols = st.columns(3)
        cols[0].metric("C: Handovers", c_met.get("num_handovers", "—"))
        cols[1].metric("C: Cost", _fmt(c_res.get("cost")))
        if q_res and "cost" in q_res:
            cols[2].metric("Q: Handovers", q_met.get("num_handovers", "—") if q_met else "—")

    elif problem_type == "bs_placement":
        st.markdown("**BS Placement Evaluation**")
        cols = st.columns(4)
        cols[0].metric("C: Sites Selected", c_met.get("sites_selected", "—"))
        cols[1].metric("C: Budget Used", f"{c_met.get('utilisation_pct', 0):.0f}%")
        cols[2].metric("C: Cost", _fmt(c_res.get("cost")))
        if q_met:
            cols[3].metric("Q: Sites Selected", q_met.get("sites_selected", "—"))

    elif problem_type == "quantum_routing":
        st.markdown("**Quantum Network Routing Evaluation**")
        cols = st.columns(4)
        cols[0].metric("C: Hops", c_met.get("num_hops", "—"))
        cols[1].metric("C: Fidelity", _fmt(c_met.get("end_to_end_fidelity"), ".4f"))
        if q_met:
            cols[2].metric("Q: Hops", q_met.get("num_hops", "—"))
            cols[3].metric("Q: Fidelity", _fmt(q_met.get("end_to_end_fidelity"), ".4f"))

    else:
        st.caption("No specific evaluation metrics for this problem type.")

