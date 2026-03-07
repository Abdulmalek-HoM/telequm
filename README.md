# TELEQUM v2.1

<div align="center">

**Quantum-Native 6G Digital Twin Platform**

*Industrial-grade hybrid quantum-classical optimization for next-generation telecom networks*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Qiskit](https://img.shields.io/badge/Qiskit-1.0+-purple.svg)](https://qiskit.org/)
[![Tests](https://img.shields.io/badge/tests-29%20passing-brightgreen.svg)]()

[Quick Start](#-quick-start) • [Dashboard](#-dashboard) • [Problem Library](#-telecom-problem-library) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 🎯 What is TELEQUM?

TELEQUM is the **first open-source quantum-telecom digital twin** that lets you:

- 🔬 **Formulate** 5 telecom problems as QUBOs — PRB allocation, routing, beam selection, energy efficiency, handover
- ⚛️ **Solve** with QAOA, VQE, simulated annealing, greedy, or hybrid strategies
- 📡 **Simulate** realistic 3GPP UMa networks with traffic, mobility, and channel fading
- 🌐 **Visualize** live network topology, SINR heatmaps, and solver comparisons in a Streamlit dashboard
- � **Integrate** with MATLAB (CDL/TDL channels) and ns-3 (trace ingestion) via source-agnostic `UniversalNetworkSnapshot`

**Target Users**: Telecom engineers, quantum researchers, 6G standards bodies, and graduate students.

---

## � Quick Start

```bash
# Clone
git clone https://github.com/Abdulmalek-HoM/telequm.git
cd telequm/notebooks

# Virtual environment
python -m venv ../.venv
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch dashboard
streamlit run dashboard/app.py
```

### Run a Simulation (CLI)

```bash
python run_experiment.py --config experiments/resource_allocation/config.yaml
```

### Run Benchmarks

```bash
python run_benchmarks.py --category resource_allocation --seeds 5
```

---

## 🖥️ Dashboard

Four-tab Streamlit app with TELEQUM dark theme:

| Tab | What it does |
|-----|-------------|
| 🎓 **Education Hub** | Interactive Bloch sphere, QUBO matrix builder, 3GPP path loss explorer, algorithm deep-dives |
| 🧪 **Use-Case Lab** | Pick a problem + solver → single-shot QUBO comparison *or* full simulation with time-series plots |
| 🖥️ **Hardware Hub** | Compare IBM / IonQ / Quantinuum specs, radar chart, workload projections |
| 🌐 **Digital Twin** | Multi-timestep simulation with live topology, throughput/SINR evolution, solver cost timeline |

### Use-Case Lab: 5 Problems × 5 Solvers

**Problems**: PRB Allocation · Routing · Beam Selection · Energy Efficiency · Handover  
**Solvers**: Greedy · Simulated Annealing · Exact · Hybrid Quantum-First · Hybrid Ensemble

Toggle ⚛️ Quantum (QAOA) for side-by-side classical vs quantum comparison.

---

## � Telecom Problem Library

```python
from telequm.core.network_snapshot import UniversalNetworkSnapshot
from telequm.problems import PRBAllocationProblem
from telequm.algorithms.hybrid import hybrid_solve

# Build a network
snap = UniversalNetworkSnapshot(source="standalone")
snap.add_cells(7).add_users(50, seed=42).initialize_links()

# Formulate as QUBO and solve
problem = PRBAllocationProblem(snap)
result = hybrid_solve(problem, strategy="ensemble")
print(result["best_method"], result["best_solution"]["cost"])
```

All 5 problems extend `BaseProblem` with a unified API:

| Problem | QUBO Variables | Description |
|---------|---------------|-------------|
| `PRBAllocationProblem` | UE × Cell | Assign users to cells, maximise SINR-weighted throughput |
| `RoutingOptimization` | Cell² | Optimal path through cell graph |
| `BeamSelection` | UE × Beams | Discrete codebook beam assignment |
| `EnergyEfficiency` | Cell + UE × Cell | Cell on/off + user reassignment |
| `HandoverOptimization` | UE × Cell | Minimise unnecessary handovers |

---

## 🏗️ Architecture

```
notebooks/
├── telequm/                       # Core package
│   ├── core/
│   │   └── network_snapshot.py    # UniversalNetworkSnapshot
│   ├── algorithms/
│   │   ├── hybrid/                # HybridSolver (3 strategies)
│   │   └── ...                    # QAOA, VQE, QML
│   ├── bridges/
│   │   ├── matlab_bridge.py       # CDL/TDL channel import
│   │   └── ns3_bridge.py          # Socket + file trace ingestion
│   ├── problems/                  # 5 QUBO problem formulations
│   ├── scenarios/                 # Small/Medium/Large/MobilityStress
│   ├── simulator/                 # Engine, NetworkEnv, traffic, mobility
│   └── telecom/                   # Beamforming, resource allocation
│
├── dashboard/                     # Streamlit (4 tabs)
│   ├── app.py
│   ├── components/                # education, use_case, hardware, digital_twin
│   └── utils/                     # scenario_loader, snapshot_manager, plot_helpers
│
├── experiments/                   # YAML configs, metrics, visualization
├── benchmarks/                    # Topologies (hex, NSFNET, mesh)
├── tests/                         # 29 pytest tests
├── v1_legacy/                     # Original workshop content
└── .github/workflows/ci.yml      # Lint → Test (3.10–3.12) → Benchmark
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Quantum SDK | Qiskit 1.x, qiskit-aer, qiskit-algorithms |
| Optimization | qiskit-optimization, scipy, numpy |
| Simulation | 3GPP TR 38.901 UMa models, discrete time-step engine |
| Dashboard | Streamlit, Plotly |
| External Bridges | MATLAB Engine (optional), ns-3 socket (optional) |
| Testing | pytest, pytest-cov, GitHub Actions CI |

---

## 🧪 Testing

```bash
# Run all tests
../.venv/bin/python -m pytest tests/ -v

# With coverage
../.venv/bin/python -m pytest tests/ -v --cov=telequm
```

**29 tests** covering: NetworkEnvironment, traffic models, mobility models, event queue, QUBO bridge, simulation engine reproducibility, and benchmark topologies.

---

## 👤 Author

**Abdulmalek Baitulmal**  
*Quantum Strategy Lead (MENA Region)*

- [LinkedIn](https://www.linkedin.com/in/abdulmalek-baitulmal-543753140/)
- VQE/QAOA optimization for 6G, QEM-Former (Graph Transformer for Error Mitigation), IET-published framework for national quantum adoption

---

## 📜 License

MIT License — see [LICENSE](LICENSE).

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

<div align="center">

**TELEQUM v2.1** — *Quantum-Native 6G Digital Twin*

Bridging raw radio physics, network logic, and quantum optimization.

</div>