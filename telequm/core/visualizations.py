"""
Visualization Utilities for TELEQUM
====================================

Standardized plotting functions for quantum circuits, results,
and network topology visualizations.
"""

import numpy as np

try:
    import matplotlib.colors as mcolors  # noqa: F401
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


# TELEQUM color palette
TELEQUM_COLORS = {
    "primary": "#0082B4",      # Ericsson Blue
    "secondary": "#663399",     # Quantum Purple
    "accent": "#2E7D32",        # Success Green
    "warning": "#E67E22",       # Warning Orange
    "danger": "#C0392B",        # Danger Red
    "neutral": "#464646",       # Telecom Gray
    "light": "#F8F9FA",         # Light Background
}


def plot_circuit(
    circuit,
    output: str = "mpl",
    style: dict | None = None,
    figsize: tuple = (12, 6),
    title: str | None = None
):
    """
    Plot a quantum circuit with TELEQUM styling.

    Parameters
    ----------
    circuit : QuantumCircuit
        Qiskit quantum circuit to plot
    output : str
        Output format: 'mpl' (matplotlib), 'latex', 'text' (default: 'mpl')
    style : dict, optional
        Custom style dictionary
    figsize : tuple
        Figure size (default: (12, 6))
    title : str, optional
        Custom title for the plot

    Returns
    -------
    Figure or str
        Matplotlib figure or text representation
    """
    if not MATPLOTLIB_AVAILABLE and output == "mpl":
        return circuit.draw("text")

    default_style = {
        "backgroundcolor": TELEQUM_COLORS["light"],
        "linecolor": TELEQUM_COLORS["neutral"],
        "textcolor": TELEQUM_COLORS["neutral"],
        "gatetextcolor": "white",
        "gatefacecolor": TELEQUM_COLORS["primary"],
        "barrierfacecolor": TELEQUM_COLORS["warning"],
    }

    if style:
        default_style.update(style)

    fig = circuit.draw(output=output, style=default_style)

    if output == "mpl" and title:
        fig.suptitle(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["primary"])

    return fig


def plot_histogram(
    counts: dict[str, int],
    title: str = "Measurement Results",
    figsize: tuple = (10, 6),
    top_k: int | None = None,
    sort: bool = True,
    show_percentages: bool = True
):
    """
    Plot measurement histogram with TELEQUM styling.

    Parameters
    ----------
    counts : Dict[str, int]
        Measurement counts dictionary
    title : str
        Plot title (default: 'Measurement Results')
    figsize : tuple
        Figure size (default: (10, 6))
    top_k : int, optional
        Show only top k results
    sort : bool
        Sort by count descending (default: True)
    show_percentages : bool
        Show percentage labels (default: True)

    Returns
    -------
    Figure
        Matplotlib figure
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for histogram plotting")

    # Process counts
    if sort:
        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    else:
        sorted_counts = counts

    if top_k:
        sorted_counts = dict(list(sorted_counts.items())[:top_k])

    total = sum(counts.values())

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    states = list(sorted_counts.keys())
    values = list(sorted_counts.values())

    # Create gradient colors
    colors = [TELEQUM_COLORS["primary"]] * len(states)

    bars = ax.bar(states, values, color=colors, edgecolor=TELEQUM_COLORS["neutral"], linewidth=1)

    # Add percentage labels
    if show_percentages:
        for bar, value in zip(bars, values, strict=False):
            height = bar.get_height()
            percentage = 100 * value / total
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(values) * 0.02,
                f"{percentage:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
                color=TELEQUM_COLORS["neutral"]
            )

    ax.set_xlabel("Quantum State", fontsize=12, fontweight="bold")
    ax.set_ylabel("Counts", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["primary"])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    return fig


def plot_network_graph(
    graph,
    node_colors: list | None = None,
    node_labels: dict | None = None,
    edge_weights: bool = True,
    title: str = "Network Topology",
    figsize: tuple = (10, 8),
    layout: str = "spring",
    highlight_nodes: list | None = None
):
    """
    Plot network graph with TELEQUM styling.

    Parameters
    ----------
    graph : nx.Graph
        NetworkX graph to plot
    node_colors : list, optional
        Colors for each node
    node_labels : dict, optional
        Custom labels for nodes
    edge_weights : bool
        Show edge weights (default: True)
    title : str
        Plot title
    figsize : tuple
        Figure size
    layout : str
        Layout algorithm: 'spring', 'circular', 'kamada_kawai', 'shell'
    highlight_nodes : list, optional
        Nodes to highlight with accent color

    Returns
    -------
    Figure
        Matplotlib figure
    """
    if not MATPLOTLIB_AVAILABLE or not NETWORKX_AVAILABLE:
        raise ImportError("matplotlib and networkx required for graph plotting")

    fig, ax = plt.subplots(figsize=figsize)

    # Get layout
    layout_funcs = {
        "spring": nx.spring_layout,
        "circular": nx.circular_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
        "shell": nx.shell_layout,
    }
    pos = layout_funcs.get(layout, nx.spring_layout)(graph)

    # Node colors
    if node_colors is None:
        node_colors = [TELEQUM_COLORS["primary"]] * graph.number_of_nodes()

    if highlight_nodes:
        node_list = list(graph.nodes())
        node_colors = [
            TELEQUM_COLORS["accent"] if node in highlight_nodes else TELEQUM_COLORS["primary"]
            for node in node_list
        ]

    # Draw nodes
    nx.draw_networkx_nodes(
        graph, pos, ax=ax,
        node_color=node_colors,
        node_size=700,
        edgecolors=TELEQUM_COLORS["neutral"],
        linewidths=2
    )

    # Draw edges
    nx.draw_networkx_edges(
        graph, pos, ax=ax,
        edge_color=TELEQUM_COLORS["neutral"],
        width=2,
        alpha=0.7
    )

    # Draw labels
    labels = node_labels if node_labels else {n: str(n) for n in graph.nodes()}
    nx.draw_networkx_labels(
        graph, pos, ax=ax,
        labels=labels,
        font_size=12,
        font_weight="bold",
        font_color="white"
    )

    # Draw edge weights
    if edge_weights:
        edge_labels = nx.get_edge_attributes(graph, "weight")
        if edge_labels:
            nx.draw_networkx_edge_labels(
                graph, pos, ax=ax,
                edge_labels={k: f"{v:.2f}" for k, v in edge_labels.items()},
                font_size=9,
                font_color=TELEQUM_COLORS["secondary"]
            )

    ax.set_title(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["primary"])
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_optimization_landscape(
    params: np.ndarray,
    energies: np.ndarray,
    title: str = "Optimization Landscape",
    figsize: tuple = (10, 6),
    show_minimum: bool = True
):
    """
    Plot optimization convergence or energy landscape.

    Parameters
    ----------
    params : np.ndarray
        Parameter values (1D) or iteration numbers
    energies : np.ndarray
        Corresponding energy/cost values
    title : str
        Plot title
    figsize : tuple
        Figure size
    show_minimum : bool
        Highlight the minimum point (default: True)

    Returns
    -------
    Figure
        Matplotlib figure
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for landscape plotting")

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(
        params, energies,
        color=TELEQUM_COLORS["primary"],
        linewidth=2,
        label="Energy"
    )
    ax.fill_between(
        params, energies,
        alpha=0.2,
        color=TELEQUM_COLORS["primary"]
    )

    if show_minimum:
        min_idx = np.argmin(energies)
        ax.scatter(
            [params[min_idx]], [energies[min_idx]],
            color=TELEQUM_COLORS["accent"],
            s=150,
            zorder=5,
            label=f"Minimum: {energies[min_idx]:.4f}"
        )
        ax.axhline(
            y=energies[min_idx],
            color=TELEQUM_COLORS["accent"],
            linestyle="--",
            alpha=0.5
        )

    ax.set_xlabel("Iteration / Parameter", fontsize=12, fontweight="bold")
    ax.set_ylabel("Energy / Cost", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", color=TELEQUM_COLORS["primary"])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
