"""
Plot Helpers — Dashboard Visualization Functions
=================================================

Generates interactive Plotly charts and Matplotlib figures
for the dashboard using the TELEQUM brand palette.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import plotly.express as px  # noqa: F401
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: F401
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ─── TELEQUM Brand Palette ──────────────────────────────────────

PALETTE = {
    "primary": "#2D5BFF",
    "secondary": "#6C3AED",
    "accent": "#00D4AA",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "dark": "#1E293B",
    "light": "#F8FAFC",
    "bg": "#0F172A",
    "card": "#1E293B",
    "text": "#E2E8F0",
    "grid": "#334155",
}

SOLVER_COLORS = {
    "classical_greedy": PALETTE["primary"],
    "classical_simulated_annealing": PALETTE["warning"],
    "classical_exact": PALETTE["accent"],
    "quantum_qaoa": PALETTE["secondary"],
    "quantum_vqe": PALETTE["danger"],
}


# ─── Network Topology Plot ──────────────────────────────────────

def plot_network_topology(
    bs_positions: np.ndarray,
    ue_positions: np.ndarray,
    ue_serving: np.ndarray | None = None,
    area_size: tuple[float, float] = (1000, 1000),
    title: str = "Network Topology",
) -> go.Figure:
    """
    Interactive Plotly scatter of BS and UE positions with
    association lines.
    """
    fig = go.Figure()

    # Association lines
    if ue_serving is not None:
        for u in range(len(ue_positions)):
            bs_id = int(ue_serving[u])
            if 0 <= bs_id < len(bs_positions):
                fig.add_trace(go.Scatter(
                    x=[ue_positions[u, 0], bs_positions[bs_id, 0]],
                    y=[ue_positions[u, 1], bs_positions[bs_id, 1]],
                    mode="lines",
                    line={"color": PALETTE["grid"], "width": 0.5},
                    showlegend=False,
                    hoverinfo="skip",
                ))

    # Base stations
    fig.add_trace(go.Scatter(
        x=bs_positions[:, 0], y=bs_positions[:, 1],
        mode="markers+text",
        marker={"size": 16, "color": PALETTE["danger"], "symbol": "triangle-up",
                    "line": {"width": 2, "color": "white"}},
        text=[f"BS{i}" for i in range(len(bs_positions))],
        textposition="top center",
        name="Base Stations",
    ))

    # UEs
    fig.add_trace(go.Scatter(
        x=ue_positions[:, 0], y=ue_positions[:, 1],
        mode="markers",
        marker={"size": 8, "color": PALETTE["accent"],
                    "line": {"width": 1, "color": "white"}},
        text=[f"UE{i}" for i in range(len(ue_positions))],
        name="Users",
    ))

    fig.update_layout(
        title=title,
        xaxis={"range": [0, area_size[0]], "title": "X (m)",
                    "gridcolor": PALETTE["grid"]},
        yaxis={"range": [0, area_size[1]], "title": "Y (m)",
                    "gridcolor": PALETTE["grid"], "scaleanchor": "x"},
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        legend={"bgcolor": PALETTE["card"]},
        height=500,
    )
    return fig


# ─── SINR Heatmap ───────────────────────────────────────────────

def plot_sinr_heatmap(
    sinr_matrix: np.ndarray,
    title: str = "SINR Matrix (dB)",
) -> go.Figure:
    """SINR heatmap: UEs × BSs."""
    fig = go.Figure(data=go.Heatmap(
        z=sinr_matrix,
        x=[f"BS{b}" for b in range(sinr_matrix.shape[1])],
        y=[f"UE{u}" for u in range(sinr_matrix.shape[0])],
        colorscale="Viridis",
        colorbar={"title": "SINR (dB)"},
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Base Station",
        yaxis_title="User Equipment",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=400,
    )
    return fig


# ─── Throughput Time Series ──────────────────────────────────────

def plot_throughput_series(
    metrics: list[dict],
    title: str = "Throughput Over Time",
) -> go.Figure:
    """Line chart of avg and sum throughput."""
    ts = [m["timestep"] for m in metrics]
    avg = [m["avg_throughput_mbps"] for m in metrics]
    total = [m["sum_throughput_mbps"] for m in metrics]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Average Throughput", "Total Throughput"])

    fig.add_trace(go.Scatter(
        x=ts, y=avg, mode="lines",
        line={"color": PALETTE["primary"], "width": 2},
        fill="tozeroy", fillcolor="rgba(45,91,255,0.1)",
        name="Avg (Mbps)",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=ts, y=total, mode="lines",
        line={"color": PALETTE["accent"], "width": 2},
        fill="tozeroy", fillcolor="rgba(0,212,170,0.1)",
        name="Sum (Mbps)",
    ), row=2, col=1)

    fig.update_layout(
        title=title,
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=500,
    )
    fig.update_xaxes(gridcolor=PALETTE["grid"])
    fig.update_yaxes(gridcolor=PALETTE["grid"])
    return fig


# ─── Fairness & SINR ────────────────────────────────────────────

def plot_fairness_sinr(metrics: list[dict]) -> go.Figure:
    """Dual-axis: Jain's fairness + avg SINR."""
    ts = [m["timestep"] for m in metrics]
    fair = [m["fairness_jain"] for m in metrics]
    sinr = [m["avg_sinr_db"] for m in metrics]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=ts, y=fair, mode="lines",
        line={"color": PALETTE["warning"], "width": 2},
        name="Jain's Fairness",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=ts, y=sinr, mode="lines",
        line={"color": PALETTE["secondary"], "width": 2},
        name="Avg SINR (dB)",
    ), secondary_y=True)

    fig.update_layout(
        title="Fairness & SINR Over Time",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=400,
    )
    fig.update_yaxes(title_text="Fairness", secondary_y=False,
                     gridcolor=PALETTE["grid"])
    fig.update_yaxes(title_text="SINR (dB)", secondary_y=True,
                     gridcolor=PALETTE["grid"])
    fig.update_xaxes(title_text="Timestep", gridcolor=PALETTE["grid"])
    return fig


# ─── Solver Cost Comparison ─────────────────────────────────────

def plot_solver_comparison(
    classical_solutions: list[dict],
    quantum_solutions: list[dict],
) -> go.Figure:
    """Box plot comparing solver costs."""
    fig = go.Figure()

    if classical_solutions:
        costs = [s["cost"] for s in classical_solutions if "cost" in s]
        methods = list({s.get("method", "classical") for s in classical_solutions})
        label = methods[0] if methods else "Classical"
        fig.add_trace(go.Box(
            y=costs, name=label.replace("_", " ").title(),
            marker_color=PALETTE["primary"],
            boxmean=True,
        ))

    if quantum_solutions:
        costs = [s["cost"] for s in quantum_solutions if "cost" in s]
        methods = list({s.get("method", "quantum") for s in quantum_solutions})
        label = methods[0] if methods else "Quantum"
        fig.add_trace(go.Box(
            y=costs, name=label.replace("_", " ").title(),
            marker_color=PALETTE["secondary"],
            boxmean=True,
        ))

    fig.update_layout(
        title="Classical vs Quantum — Cost Distribution",
        yaxis_title="QUBO Cost",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=400,
    )
    fig.update_yaxes(gridcolor=PALETTE["grid"])
    return fig


# ─── Allocation Heatmap ─────────────────────────────────────────

def plot_allocation_matrix(
    allocation: np.ndarray,
    title: str = "Resource Allocation",
) -> go.Figure:
    """Heatmap of UE-to-BS allocation."""
    fig = go.Figure(data=go.Heatmap(
        z=allocation,
        x=[f"BS{b}" for b in range(allocation.shape[1])],
        y=[f"UE{u}" for u in range(allocation.shape[0])],
        colorscale=[[0, PALETTE["bg"]], [1, PALETTE["accent"]]],
        colorbar={"title": "Allocation"},
    ))
    fig.update_layout(
        title=title,
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=400,
    )
    return fig


# ─── PQC & Quantum-Safe Visualization Helpers ───────────────────

def plot_protocol_handshake_sequence(
    steps: list[Any],
    title: str = "Protocol Handshake Timing & Processing Breakdown",
) -> go.Figure:
    """
    Horizontal stacked bar / Gantt chart representing network transmission
    vs cryptographic processing latency for each step in a handshake.
    """
    fig = go.Figure()

    step_names = [f"Step {s['step_index']}: {s['name']}" if isinstance(s, dict) else f"Step {s.step_index}: {s.name}" for s in steps]
    net_times = [s["transmission_ms"] if isinstance(s, dict) else s.transmission_ms for s in steps]
    cpu_times = [s["crypto_cpu_ms"] if isinstance(s, dict) else s.crypto_cpu_ms for s in steps]

    fig.add_trace(go.Bar(
        y=step_names,
        x=net_times,
        name="Network Transmission (ms)",
        orientation="h",
        marker={"color": PALETTE["primary"]},
        text=[f"{val:.2f} ms" for val in net_times],
        textposition="inside",
    ))

    fig.add_trace(go.Bar(
        y=step_names,
        x=cpu_times,
        name="Crypto Processing CPU (ms)",
        orientation="h",
        marker={"color": PALETTE["secondary"]},
        text=[f"{val:.2f} ms" for val in cpu_times],
        textposition="inside",
    ))

    fig.update_layout(
        title=title,
        barmode="stack",
        xaxis_title="Latency (ms)",
        yaxis_title="Handshake Exchange Step",
        yaxis={"autorange": "reversed"},
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        legend={"bgcolor": PALETTE["card"], "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        height=350 + len(steps) * 50,
    )
    fig.update_xaxes(gridcolor=PALETTE["grid"])
    return fig


def plot_packet_fragmentation(
    suite_results: dict[str, dict],
    mtu_bytes: int = 1500,
    title: str = "Packet Expansion & MTU Fragmentation Comparison",
) -> go.Figure:
    """
    Bar chart comparing total handshake bytes and max packet size against link MTU.
    """
    suites = list(suite_results.keys())
    total_bytes = [suite_results[s]["total_handshake_bytes"] for s in suites]
    max_packet = [suite_results[s]["max_fragment_size"] for s in suites]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=suites,
        y=total_bytes,
        name="Total Exchange Bytes",
        marker_color=PALETTE["primary"],
        text=[f"{val:,} B" for val in total_bytes],
        textposition="auto",
    ))

    fig.add_trace(go.Bar(
        x=suites,
        y=max_packet,
        name="Max Single Packet Bytes",
        marker_color=PALETTE["accent"],
        text=[f"{val:,} B" for val in max_packet],
        textposition="auto",
    ))

    fig.add_hline(
        y=mtu_bytes,
        line_dash="dash",
        line_color=PALETTE["danger"],
        annotation_text=f"Link MTU ({mtu_bytes} B)",
        annotation_position="top left",
    )

    fig.update_layout(
        title=title,
        barmode="group",
        xaxis_title="Cryptographic Suite",
        yaxis_title="Payload Size (Bytes)",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        legend={"bgcolor": PALETTE["card"]},
        height=450,
    )
    fig.update_yaxes(gridcolor=PALETTE["grid"])
    return fig


def plot_hndl_risk_heatmap(
    risk_matrix: np.ndarray,
    x_labels: list[str],
    y_labels: list[str],
    title: str = "Harvest Now Decrypt Later (HNDL) Risk Exposure",
) -> go.Figure:
    """
    Heatmap of HNDL risk scores across telecom layers and data lifespans.
    """
    fig = go.Figure(data=go.Heatmap(
        z=risk_matrix,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0.0, PALETTE["accent"]],
            [0.4, PALETTE["warning"]],
            [0.7, PALETTE["danger"]],
            [1.0, "#7F1D1D"],
        ],
        zmin=0, zmax=100,
        colorbar={"title": "Risk Score (0-100)"},
        text=risk_matrix,
        texttemplate="%{text:.1f}",
        textfont={"size": 12},
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Infrastructure Lifecycle Category / Layer",
        yaxis_title="Data Sensitivity Lifespan",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        height=450,
    )
    return fig


def plot_maturity_radar(
    scores_dict: dict[str, int],
    title: str = "Operational Maturity Ladder — 5-Pillar Assessment",
) -> go.Figure:
    """
    Radar / spider chart displaying scores across the 5 PQC maturity pillars.
    """
    categories = list(scores_dict.keys())
    values = list(scores_dict.values())

    categories = categories + [categories[0]]
    values = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor="rgba(45,91,255,0.25)",
        line={"color": PALETTE["primary"], "width": 3},
        name="Current Maturity",
    ))

    target_vals = [80] * len(categories)
    fig.add_trace(go.Scatterpolar(
        r=target_vals,
        theta=categories,
        line={"color": PALETTE["accent"], "width": 2, "dash": "dash"},
        name="Target Level 3 (PQC Default)",
    ))

    fig.update_layout(
        title=title,
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "gridcolor": PALETTE["grid"],
                "linecolor": PALETTE["grid"],
            },
            "angularaxis": {
                "gridcolor": PALETTE["grid"],
                "linecolor": PALETTE["grid"],
            },
            "bgcolor": PALETTE["bg"],
        },
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        legend={"bgcolor": PALETTE["card"]},
        height=450,
    )
    return fig


def plot_qubit_scaling_curve(
    title: str = "Fault-Tolerant Quantum Resource Scaling (Shor's vs Grover's)",
) -> go.Figure:
    """
    Line chart comparing physical/logical qubit requirements against key sizes.
    """
    key_sizes = [128, 256, 384, 512, 1024, 2048, 3072, 4096]

    rsa_logical = [2 * k + 3 if k >= 1024 else np.nan for k in key_sizes]
    ecc_logical = [int(2.5 * k) if k <= 512 else np.nan for k in key_sizes]
    aes_logical = [2 * k + 100 if k in (128, 256) else np.nan for k in key_sizes]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=key_sizes, y=rsa_logical, mode="lines+markers",
        name="RSA (Shor's Algorithm)", line={"color": PALETTE["danger"], "width": 3},
    ))

    fig.add_trace(go.Scatter(
        x=key_sizes, y=ecc_logical, mode="lines+markers",
        name="ECC / ECDH (Shor's Algorithm)", line={"color": PALETTE["warning"], "width": 3},
    ))

    fig.add_trace(go.Scatter(
        x=key_sizes, y=aes_logical, mode="lines+markers",
        name="AES / Symmetric (Grover's Algorithm)", line={"color": PALETTE["accent"], "width": 3},
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Cryptographic Key Size (Bits)",
        yaxis_title="Required Logical Qubits",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font={"color": PALETTE["text"]},
        legend={"bgcolor": PALETTE["card"]},
        height=450,
    )
    fig.update_xaxes(gridcolor=PALETTE["grid"])
    fig.update_yaxes(gridcolor=PALETTE["grid"])
    return fig


# ─── Metric Export Helpers ───────────────────────────────────────

def metrics_to_csv(metrics: list[dict]) -> str:
    """Convert metrics list to CSV string."""
    if not metrics:
        return ""
    keys = list(metrics[0].keys())
    lines = [",".join(keys)]
    for m in metrics:
        lines.append(",".join(str(m.get(k, "")) for k in keys))
    return "\n".join(lines)


def fig_to_png_bytes(fig: go.Figure, width: int = 1200, height: int = 600) -> bytes:
    """Export Plotly figure to PNG bytes (requires kaleido)."""
    try:
        return fig.to_image(format="png", width=width, height=height)
    except Exception:
        return b""

