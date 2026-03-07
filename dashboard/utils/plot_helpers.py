"""
Plot Helpers — Dashboard Visualization Functions
=================================================

Generates interactive Plotly charts and Matplotlib figures
for the dashboard using the TELEQUM brand palette.
"""

from __future__ import annotations

import io
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
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
    ue_serving: Optional[np.ndarray] = None,
    area_size: Tuple[float, float] = (1000, 1000),
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
                    line=dict(color=PALETTE["grid"], width=0.5),
                    showlegend=False,
                    hoverinfo="skip",
                ))

    # Base stations
    fig.add_trace(go.Scatter(
        x=bs_positions[:, 0], y=bs_positions[:, 1],
        mode="markers+text",
        marker=dict(size=16, color=PALETTE["danger"], symbol="triangle-up",
                    line=dict(width=2, color="white")),
        text=[f"BS{i}" for i in range(len(bs_positions))],
        textposition="top center",
        name="Base Stations",
    ))

    # UEs
    fig.add_trace(go.Scatter(
        x=ue_positions[:, 0], y=ue_positions[:, 1],
        mode="markers",
        marker=dict(size=8, color=PALETTE["accent"],
                    line=dict(width=1, color="white")),
        text=[f"UE{i}" for i in range(len(ue_positions))],
        name="Users",
    ))

    fig.update_layout(
        title=title,
        xaxis=dict(range=[0, area_size[0]], title="X (m)",
                    gridcolor=PALETTE["grid"]),
        yaxis=dict(range=[0, area_size[1]], title="Y (m)",
                    gridcolor=PALETTE["grid"], scaleanchor="x"),
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
        legend=dict(bgcolor=PALETTE["card"]),
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
        colorbar=dict(title="SINR (dB)"),
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Base Station",
        yaxis_title="User Equipment",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
        height=400,
    )
    return fig


# ─── Throughput Time Series ──────────────────────────────────────

def plot_throughput_series(
    metrics: List[dict],
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
        line=dict(color=PALETTE["primary"], width=2),
        fill="tozeroy", fillcolor="rgba(45,91,255,0.1)",
        name="Avg (Mbps)",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=ts, y=total, mode="lines",
        line=dict(color=PALETTE["accent"], width=2),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.1)",
        name="Sum (Mbps)",
    ), row=2, col=1)

    fig.update_layout(
        title=title,
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
        height=500,
    )
    fig.update_xaxes(gridcolor=PALETTE["grid"])
    fig.update_yaxes(gridcolor=PALETTE["grid"])
    return fig


# ─── Fairness & SINR ────────────────────────────────────────────

def plot_fairness_sinr(metrics: List[dict]) -> go.Figure:
    """Dual-axis: Jain's fairness + avg SINR."""
    ts = [m["timestep"] for m in metrics]
    fair = [m["fairness_jain"] for m in metrics]
    sinr = [m["avg_sinr_db"] for m in metrics]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=ts, y=fair, mode="lines",
        line=dict(color=PALETTE["warning"], width=2),
        name="Jain's Fairness",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=ts, y=sinr, mode="lines",
        line=dict(color=PALETTE["secondary"], width=2),
        name="Avg SINR (dB)",
    ), secondary_y=True)

    fig.update_layout(
        title="Fairness & SINR Over Time",
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
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
    classical_solutions: List[dict],
    quantum_solutions: List[dict],
) -> go.Figure:
    """Box plot comparing solver costs."""
    fig = go.Figure()

    if classical_solutions:
        costs = [s["cost"] for s in classical_solutions if "cost" in s]
        methods = list(set(s.get("method", "classical") for s in classical_solutions))
        label = methods[0] if methods else "Classical"
        fig.add_trace(go.Box(
            y=costs, name=label.replace("_", " ").title(),
            marker_color=PALETTE["primary"],
            boxmean=True,
        ))

    if quantum_solutions:
        costs = [s["cost"] for s in quantum_solutions if "cost" in s]
        methods = list(set(s.get("method", "quantum") for s in quantum_solutions))
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
        font=dict(color=PALETTE["text"]),
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
        colorbar=dict(title="Allocation"),
    ))
    fig.update_layout(
        title=title,
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["card"],
        font=dict(color=PALETTE["text"]),
        height=400,
    )
    return fig


# ─── Metric Export Helpers ───────────────────────────────────────

def metrics_to_csv(metrics: List[dict]) -> str:
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
