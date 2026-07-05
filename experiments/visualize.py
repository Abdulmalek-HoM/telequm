"""
Experiment Visualization — Plotting Utilities
=============================================

Generate publication-quality plots from experiment results
using the TELEQUM colour palette.
"""

from __future__ import annotations

from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# TELEQUM colour palette
TELEQUM_COLORS = {
    "primary": "#2D5BFF",
    "secondary": "#6C3AED",
    "accent": "#00D4AA",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "dark": "#1E293B",
    "light": "#F8FAFC",
}


def plot_throughput_timeseries(
    metrics: list,
    title: str = "Network Throughput Over Time",
    save_path: str | None = None,
) -> None:
    """Plot average and sum throughput over simulation timesteps."""
    if not HAS_MPL:
        return

    ts = [m["timestep"] for m in metrics]
    avg = [m["avg_throughput_mbps"] for m in metrics]
    total = [m["sum_throughput_mbps"] for m in metrics]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["dark"])

    ax1.plot(ts, avg, color=TELEQUM_COLORS["primary"], linewidth=1.5, label="Avg Throughput")
    ax1.fill_between(ts, 0, avg, alpha=0.15, color=TELEQUM_COLORS["primary"])
    ax1.set_ylabel("Avg Throughput (Mbps)")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2.plot(ts, total, color=TELEQUM_COLORS["accent"], linewidth=1.5, label="Sum Throughput")
    ax2.fill_between(ts, 0, total, alpha=0.15, color=TELEQUM_COLORS["accent"])
    ax2.set_xlabel("Timestep")
    ax2.set_ylabel("Sum Throughput (Mbps)")
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sinr_fairness(
    metrics: list,
    title: str = "SINR & Jain's Fairness",
    save_path: str | None = None,
) -> None:
    """Plot SINR and fairness index over time."""
    if not HAS_MPL:
        return

    ts = [m["timestep"] for m in metrics]
    sinr = [m["avg_sinr_db"] for m in metrics]
    fair = [m["fairness_jain"] for m in metrics]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["dark"])

    ax1.plot(ts, sinr, color=TELEQUM_COLORS["secondary"], linewidth=1.5)
    ax1.set_ylabel("Avg SINR (dB)")
    ax1.grid(alpha=0.3)

    ax2.plot(ts, fair, color=TELEQUM_COLORS["warning"], linewidth=1.5)
    ax2.set_ylabel("Jain's Fairness Index")
    ax2.set_xlabel("Timestep")
    ax2.set_ylim([0, 1.05])
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_solver_comparison(
    classical_costs: list,
    quantum_costs: list,
    labels: tuple = ("Classical (Greedy)", "Quantum (QAOA)"),
    title: str = "Solver Cost Comparison",
    save_path: str | None = None,
) -> None:
    """Bar / box plot comparing classical vs quantum costs."""
    if not HAS_MPL:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    data = [classical_costs, quantum_costs]
    colors = [TELEQUM_COLORS["primary"], TELEQUM_COLORS["secondary"]]

    bp = ax.boxplot(data, labels=labels, patch_artist=True, widths=0.5)
    for patch, color in zip(bp["boxes"], colors, strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel("QUBO Cost")
    ax.set_title(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["dark"])
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
