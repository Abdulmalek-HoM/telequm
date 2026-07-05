"""
Resource Monitor — CPU / RAM / Time Tracking
=============================================

Context manager and utilities for tracking compute resources
during solver execution. Shows real-time feedback on:
- Peak RAM usage (MB)
- CPU time (s)
- Wall-clock time (s)
- Qubit count, gate count, circuit depth (for quantum solvers)
"""

from __future__ import annotations

import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np


@dataclass
class ResourceReport:
    """Report of resources consumed during a computation."""
    wall_time_s: float = 0.0
    peak_ram_mb: float = 0.0
    ram_delta_mb: float = 0.0
    cpu_time_s: float = 0.0

    # Quantum-specific
    num_qubits: int = 0
    gate_count: int = 0
    circuit_depth: int = 0
    num_parameters: int = 0
    circuit_text: str = ""

    # Problem-specific
    num_vars: int = 0
    qubo_density: float = 0.0   # fraction of non-zero Q entries


@contextmanager
def track_resources():
    """
    Context manager for tracking compute resources.

    Usage
    -----
    >>> with track_resources() as report:
    ...     result = some_heavy_computation()
    >>> print(report.peak_ram_mb, report.wall_time_s)
    """
    report = ResourceReport()

    # Start trackers
    tracemalloc.start()
    t_wall_start = time.perf_counter()
    t_cpu_start = time.process_time()

    try:
        yield report
    finally:
        # Capture results
        report.wall_time_s = time.perf_counter() - t_wall_start
        report.cpu_time_s = time.process_time() - t_cpu_start

        current, peak = tracemalloc.get_traced_memory()
        report.peak_ram_mb = peak / (1024 * 1024)
        report.ram_delta_mb = current / (1024 * 1024)

        tracemalloc.stop()


def estimate_statevector_ram(num_qubits: int) -> dict:
    """
    Estimate RAM for statevector simulation.

    Statevector: 2^n complex128 entries → 2^n × 16 bytes

    Parameters
    ----------
    num_qubits : int

    Returns
    -------
    dict with ram_bytes, ram_mb, ram_gb, feasible
    """
    entries = 2 ** num_qubits
    ram_bytes = entries * 16  # complex128
    ram_mb = ram_bytes / (1024 ** 2)
    ram_gb = ram_bytes / (1024 ** 3)

    return {
        "num_qubits": num_qubits,
        "statevector_entries": entries,
        "ram_bytes": ram_bytes,
        "ram_mb": round(ram_mb, 2),
        "ram_gb": round(ram_gb, 4),
        "feasible_laptop": ram_gb < 16,   # 16 GB typical
        "feasible_server": ram_gb < 256,  # 256 GB workstation
    }


def estimate_qaoa_resources(num_qubits: int, p: int, edge_count: int) -> dict:
    """
    Estimate QAOA circuit resources.

    - Gate count: O(p × (|E| + n)) per layer
    - Circuit depth: O(p × max_degree)
    - Parameters: 2p (gamma + beta per layer)
    - RAM: statevector of n qubits

    Parameters
    ----------
    num_qubits : int
    p : int  QAOA depth
    edge_count : int  number of edges in problem graph

    Returns
    -------
    dict
    """
    # Cost layer: 1 RZZ per edge = 2 CNOTs + 1 Rz per edge → 3 gates/edge
    # Mixer layer: 1 Rx per qubit
    gates_per_layer = 3 * edge_count + num_qubits
    total_gates = p * gates_per_layer + num_qubits  # +n for initial H gates
    depth = p * (edge_count + 1)  # approximate
    parameters = 2 * p

    ram = estimate_statevector_ram(num_qubits)

    return {
        "algorithm": "QAOA",
        "num_qubits": num_qubits,
        "p_layers": p,
        "edge_count": edge_count,
        "total_gates": total_gates,
        "circuit_depth": depth,
        "num_parameters": parameters,
        "time_complexity": f"O({p} × {edge_count} × shots × optimizer_iters)",
        **ram,
    }


def estimate_vqe_resources(num_qubits: int, layers: int) -> dict:
    """
    Estimate VQE (RealAmplitudes ansatz) circuit resources.

    - Ry gates: n per layer
    - CNOT ladder: n-1 per layer
    - Parameters: n × layers + n (initial Ry)

    Parameters
    ----------
    num_qubits : int
    layers : int

    Returns
    -------
    dict
    """
    ry_gates = num_qubits * (layers + 1)
    cnot_gates = (num_qubits - 1) * layers
    total_gates = ry_gates + cnot_gates
    depth = 2 * layers + 1  # alternating Ry-CNOT blocks
    parameters = ry_gates

    ram = estimate_statevector_ram(num_qubits)

    return {
        "algorithm": "VQE",
        "num_qubits": num_qubits,
        "ansatz_layers": layers,
        "total_gates": total_gates,
        "circuit_depth": depth,
        "num_parameters": parameters,
        "time_complexity": f"O({parameters} × shots × optimizer_iters × {num_qubits})",
        **ram,
    }


def estimate_classical_resources(num_vars: int, method: str) -> dict:
    """
    Estimate classical solver resources.

    Parameters
    ----------
    num_vars : int  number of binary decision variables
    method : str  'greedy', 'simulated_annealing', 'exact'

    Returns
    -------
    dict
    """
    if method == "greedy":
        return {
            "algorithm": "Greedy",
            "num_vars": num_vars,
            "time_complexity": f"O(n²) = O({num_vars}²) = O({num_vars**2})",
            "space_complexity": f"O(n²) = O({num_vars**2})",
            "ram_mb": round(num_vars ** 2 * 8 / (1024 ** 2), 4),  # Q matrix
            "feasible": True,
        }
    elif method == "simulated_annealing":
        T_max = 1000
        return {
            "algorithm": "Simulated Annealing",
            "num_vars": num_vars,
            "time_complexity": f"O(n × T_max) = O({num_vars} × {T_max}) = O({num_vars * T_max})",
            "space_complexity": f"O(n²) = O({num_vars**2})",
            "ram_mb": round(num_vars ** 2 * 8 / (1024 ** 2), 4),
            "num_iterations": T_max,
            "feasible": True,
        }
    elif method == "exact":
        feasible = num_vars <= 25
        return {
            "algorithm": "Exact Brute-Force",
            "num_vars": num_vars,
            "time_complexity": f"O(2^n) = O(2^{num_vars}) = O({2**min(num_vars, 40):.0e})",
            "space_complexity": f"O(n) = O({num_vars})",
            "ram_mb": round(num_vars * 8 / (1024 ** 2), 6),
            "feasible": feasible,
            "warning": None if feasible else f"INFEASIBLE: 2^{num_vars} evaluations",
        }
    return {}


def get_qubo_stats(Q: np.ndarray) -> dict:
    """Get statistics about a QUBO matrix."""
    n = Q.shape[0]
    nonzero = np.count_nonzero(Q)
    total = n * n
    return {
        "matrix_size": f"{n}×{n}",
        "num_vars": n,
        "nonzero_entries": nonzero,
        "density": round(nonzero / total, 4) if total > 0 else 0,
        "q_range": [float(Q.min()), float(Q.max())],
        "ram_mb": round(Q.nbytes / (1024 ** 2), 4),
    }


# ─── Hardware Benchmark ─────────────────────────────────────────

def benchmark_device() -> dict:
    """
    Read hardware specs of the current machine.

    Returns dict with CPU, RAM, GPU info and a quick
    single-core benchmark (matrix multiply speed).
    """
    import multiprocessing
    import platform

    try:
        import psutil
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        available_ram_gb = psutil.virtual_memory().available / (1024 ** 3)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_ghz = cpu_freq.max / 1000 if cpu_freq else 0
    except ImportError:
        total_ram_gb = 0
        available_ram_gb = 0
        cpu_freq_ghz = 0

    # GPU detection
    gpu_name = "None detected"
    gpu_memory_gb = 0
    try:
        import subprocess
        # Try Apple Silicon GPU (Metal)
        if platform.machine() == "arm64" and platform.system() == "Darwin":
            gpu_name = "Apple Silicon (Metal)"
            # Unified memory — GPU shares system RAM
            gpu_memory_gb = total_ram_gb
    except Exception:
        pass

    try:
        # Try NVIDIA GPU
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            gpu_name = parts[0].strip()
            gpu_memory_gb = float(parts[1].strip()) / 1024
    except Exception:
        pass

    # Quick single-core benchmark: time a 500×500 matmul
    bench_size = 500
    A = np.random.randn(bench_size, bench_size)
    t0 = time.perf_counter()
    _ = A @ A.T
    matmul_time = time.perf_counter() - t0
    # GFLOPS estimate: 2 * N^3 / time
    gflops = 2 * bench_size ** 3 / matmul_time / 1e9

    return {
        "cpu_name": platform.processor() or platform.machine(),
        "cpu_cores_physical": multiprocessing.cpu_count(),
        "cpu_freq_ghz": round(cpu_freq_ghz, 2),
        "total_ram_gb": round(total_ram_gb, 1),
        "available_ram_gb": round(available_ram_gb, 1),
        "gpu_name": gpu_name,
        "gpu_memory_gb": round(gpu_memory_gb, 1),
        "os": f"{platform.system()} {platform.release()}",
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
        "bench_gflops": round(gflops, 1),
        "bench_matmul_ms": round(matmul_time * 1000, 2),
    }


def estimate_solver_times(num_vars: int, hw: dict | None = None) -> list:
    """
    Estimate wall-clock time for each solver at a given QUBO size.

    Uses hardware benchmark results to scale estimates.
    Returns a list of dicts (one per solver).

    Parameters
    ----------
    num_vars : int   number of binary variables
    hw : dict        from benchmark_device(), or None for defaults
    """
    if hw is None:
        hw = {"bench_gflops": 5.0, "total_ram_gb": 8.0}

    gflops = max(hw.get("bench_gflops", 5.0), 0.1)
    ram_gb = hw.get("total_ram_gb", 8.0)

    # Base operation counts per algorithm
    # Greedy: O(n^2) evaluations, each is O(n) matmul → O(n^3) total ops
    greedy_ops = num_vars ** 3
    greedy_time_s = greedy_ops / (gflops * 1e9)

    # SA: O(100 × n) iterations, each O(n) → O(100 × n^2) ops
    sa_iters = 100 * num_vars
    sa_ops = sa_iters * num_vars
    sa_time_s = sa_ops / (gflops * 1e9)

    # Exact: O(2^n × n) ops
    if num_vars <= 40:
        exact_ops = (2 ** num_vars) * num_vars
        exact_time_s = exact_ops / (gflops * 1e9)
    else:
        exact_time_s = float("inf")

    # QAOA (p=2, COBYLA 100 iters, statevector):
    # Each iter: O(2^n × gates) ops
    qaoa_edges = num_vars * (num_vars - 1) // 2
    qaoa_gates = 2 * (3 * qaoa_edges + num_vars) + num_vars
    qaoa_iters = 100
    if num_vars <= 30:
        qaoa_ops = qaoa_iters * (2 ** num_vars) * qaoa_gates
        qaoa_time_s = qaoa_ops / (gflops * 1e9)
    elif num_vars <= 50:
        qaoa_ops = qaoa_iters * (2 ** num_vars) * qaoa_gates
        qaoa_time_s = qaoa_ops / (gflops * 1e9)
    else:
        qaoa_time_s = float("inf")

    # Statevector RAM for QAOA
    sv_ram_gb = (2 ** num_vars) * 16 / (1024 ** 3)

    def _fmt_time(t):
        if t == float("inf"):
            return "∞ (intractable)"
        if t < 0.001:
            return f"{t * 1e6:.0f} μs"
        if t < 1:
            return f"{t * 1000:.1f} ms"
        if t < 60:
            return f"{t:.2f} s"
        if t < 3600:
            return f"{t / 60:.1f} min"
        if t < 86400:
            return f"{t / 3600:.1f} hrs"
        if t < 86400 * 365:
            return f"{t / 86400:.0f} days"
        return f"{t / (86400 * 365):.1e} years"

    return [
        {
            "solver": "Greedy",
            "big_o": f"O(n³) = O({num_vars}³)",
            "ops": f"{greedy_ops:,.0f}",
            "est_time": _fmt_time(greedy_time_s),
            "est_time_s": greedy_time_s,
            "ram_mb": round(num_vars ** 2 * 8 / (1024 ** 2), 4),
            "feasible": True,
        },
        {
            "solver": "Simulated Annealing",
            "big_o": f"O(n² × T) = O({num_vars}² × {100})",
            "ops": f"{sa_ops:,.0f}",
            "est_time": _fmt_time(sa_time_s),
            "est_time_s": sa_time_s,
            "ram_mb": round(num_vars ** 2 * 8 / (1024 ** 2), 4),
            "feasible": True,
        },
        {
            "solver": "Exact Brute-Force",
            "big_o": f"O(2ⁿ × n) = O(2^{num_vars} × {num_vars})",
            "ops": f"{exact_ops:,.0f}" if num_vars <= 40 else "∞",
            "est_time": _fmt_time(exact_time_s),
            "est_time_s": exact_time_s,
            "ram_mb": round(num_vars * 8 / (1024 ** 2), 6),
            "feasible": num_vars <= 25,
        },
        {
            "solver": "QAOA (p=2, statevector)",
            "big_o": f"O(iters × 2ⁿ × gates) = O(100 × 2^{num_vars} × {qaoa_gates})",
            "ops": f"{qaoa_ops:,.0f}" if num_vars <= 50 else "∞",
            "est_time": _fmt_time(qaoa_time_s),
            "est_time_s": qaoa_time_s,
            "ram_mb": round(sv_ram_gb * 1024, 2),
            "feasible": sv_ram_gb < ram_gb,
            "note": f"Statevector: {sv_ram_gb:.2f} GB" if sv_ram_gb < 1000 else f"Statevector: {sv_ram_gb:.0f} GB — EXCEEDS RAM",
        },
    ]

