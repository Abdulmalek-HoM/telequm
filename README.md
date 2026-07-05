# TELEQUM v3.0

<div align="center">

**Post-Quantum Cryptography & Quantum-Safe 6G Digital Twin Platform**

*Industrial-grade hybrid quantum-classical optimization and quantum-safe network migration for next-generation telecommunications infrastructure*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Qiskit](https://img.shields.io/badge/Qiskit-1.0+-purple.svg)](https://qiskit.org/)
[![Tests](https://img.shields.io/badge/tests-41%20passing-brightgreen.svg)]()

[Quick Start](#-quick-start) • [Dashboard](#-dashboard) • [PQC & Security Suite](#-pqc--quantum-safe-security-suite) • [Problem Library](#-telecom-problem-library) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 🎯 What is TELEQUM?

TELEQUM is the world's first open-source **quantum-telecom digital twin and post-quantum migration engineering platform** that lets you:

- 🛡️ **Migrate & Protect**: Model **NIST FIPS 203 (ML-KEM / Kyber)**, **FIPS 204 (ML-DSA / Dilithium)**, **FIPS 205 (SLH-DSA / SPHINCS+)**, and **FALCON** across telecom infrastructure tiers.
- ⚡ **Simulate Protocol Overhead & Crypto-Agility**: Evaluate cryptographic handshake latency, MTU packet fragmentation (1500B vs 9000B Jumbo frames), and X.509 dual-signature hybrid certificate chains across **TLS 1.3, IPSec/IKEv2, MACsec, 5G AKA, and DNSSEC/BGP**.
- 🚨 **Evaluate Quantum Threats**: Assess Harvest Now, Decrypt Later (**HNDL**) interception risks using **Mosca's Inequality ($X + Y > Z$)** and Shor vs. Grover logical qubit scaling estimators.
- 🪜 **Assess Operator Readiness**: Grade infrastructure maturity across the **AQC 5-Pillar Ladder (Levels 0–4)**, evaluate Sector Risk Profiles, and simulate **10-year network migration timelines (2025–2035)**.
- 🔬 **Formulate Telecom Optimization Problems**: Build 5 core 3GPP problems as QUBOs — PRB allocation, routing, beam selection, energy efficiency, and handover.
- ⚛️ **Solve with Quantum & Classical Engines**: Execute QAOA, VQE, Quantum Machine Learning (QSVC), simulated annealing, greedy, or hybrid ensemble strategies.
- 🌐 **Visualize Live Network Evolution**: Explore interactive 3GPP UMa topologies, SINR/coverage heatmaps, algorithm byte-expansion bar charts, and protocol handshake timing Gantt charts in Streamlit.
- 🔗 **Ingest External Channels & Traces**: Connect directly with MATLAB (CDL/TDL fading channels) and ns-3 (packet trace ingestion) via the source-agnostic `UniversalNetworkSnapshot`.

**Target Users**: Telecom operators, security architects, quantum researchers, 6G standards bodies (3GPP/IETF), and graduate engineering students.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/Abdulmalek-HoM/telequm.git
cd telequm/notebooks

# Create and activate virtual environment
python -m venv ../.venv
source ../.venv/bin/activate  # On Windows: ..\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch interactive engineering dashboard
streamlit run dashboard/app.py
```

### Run Automated Unit Tests (CLI)

```bash
python -m pytest tests/ -v
```

### Run Optimization Benchmarks

```bash
python run_benchmarks.py --category resource_allocation --seeds 5
```

---

## 🖥️ Dashboard

Four-tab interactive Streamlit application engineered with a sleek dark-mode aesthetic and dedicated domain switchers:

| Tab | Domain Modes & Engineering Capabilities |
| :--- | :--- |
| 🎓 **Education Hub** | **4 Quantum Optimization Tracks**: Bloch sphere, QUBO matrix builder, 3GPP path loss explorer, algorithm deep-dives.<br>**4 PQC & Security Tracks**: Lattice Theory (LWE/SIS), HNDL Threat Matrix & Mosca Calculator, Crypto-Agility Protocol Lab, AQC 5-Pillar Migration Framework (Levels 0–4). |
| 🧪 **Use-Case Lab** | **Network Optimization Lab**: Pick problem + solver $\to$ single-shot QUBO comparison & QAOA/VQE benchmarking.<br>**Quantum-Safe Protocol & Crypto-Agility Lab**: Simulate TLS 1.3, IPSec, MACsec, 5G AKA handshakes under Pure PQC and Hybrid suites; evaluate MTU fragmentation and latency over Fiber, 5G RAN, and LEO Satellite links. |
| 🖥️ **Hardware Hub** | **Quantum Processing Units (QPUs)**: Compare IBM, IonQ, Quantinuum physical/logical qubit roadmaps and radar charts.<br>**FTQC Roadmap & Telecom Hardware Benchmarks**: Track Shor's RSA-2048 threshold timeline (2026–2035+) and benchmark PQC cycle counts/memory across 5G Baseband (AVX-512), IoT Edge (ARM Cortex-A53), Core HSMs, and 400G Optical DWDM line cards. |
| 🌐 **Digital Twin** | **Live Network Optimization Twin**: Multi-timestep time-series simulation watching SINR, throughput, and fairness evolve.<br>**Quantum-Safe Migration & HNDL Risk Twin**: Simulate a 10-year operator transition timeline (2025–2035), tracking annual PQC rollout percentage, cumulative HNDL harvested data volume (TB/PB), and maturity progression. |

---

## 🛡️ PQC & Quantum-Safe Security Suite

TELEQUM v3.0 introduces a standalone, industrial-grade backend package (`telequm.pqc`) for modeling post-quantum telecommunications security:

```python
from telequm.pqc import (
    get_algorithm,
    list_algorithms,
    ProtocolSimulator,
    HNDLCalculator,
    MaturityLadder,
)

# 1. Retrieve NIST FIPS 203 (ML-KEM-768) specifications
kem = get_algorithm("ML-KEM-768")
print(f"Algorithm: {kem.name} | Standard: {kem.standard} | NIST Level: {kem.security_level}")
print(f"Public Key: {kem.public_key_bytes} B | Ciphertext: {kem.ciphertext_bytes} B | Total: {kem.total_handshake_bytes} B")

# 2. Simulate TLS 1.3 Handshake over 5G RAN using Hybrid Suite (X25519 + ML-KEM-768)
sim = ProtocolSimulator()
result = sim.simulate_handshake(
    protocol="TLS_1_3",
    link="5G_UMa_RAN",
    suite="HYBRID_RECOMMENDED",
    custom_mtu=1500,
)
print(f"Handshake Latency: {result.total_latency_ms:.2f} ms | Total Bytes: {result.total_bytes_transmitted} B")
print(f"MTU Fragmentation: {'YES (Risk Detected)' if result.fragmentation_occurred else 'NO (Clean Transmission)'}")

# 3. Evaluate Harvest Now, Decrypt Later (HNDL) Risk Score
score = HNDLCalculator.calculate(
    data_sensitivity_years=10,  # Shelf life of sensitive CDR / LI data
    crqc_years=8,               # Estimated arrival of Cryptographically Relevant Quantum Computer
    interception_prob=0.85,     # Nation-state passive fiber tapping probability
)
print(f"HNDL Urgency Level: {score.urgency_level} | Mosca Threshold Breached: {score.mosca_breached}")

# 4. Audit Operator Readiness across 5-Pillar Maturity Ladder
maturity = MaturityLadder.evaluate(gov_level=2, disc_level=3, arch_level=1, ops_level=2, proc_level=1)
print(f"Overall Operator Maturity Score: Level {maturity.overall_level} ({maturity.level_name})")
```

---

## 📡 Telecom Problem Library

All 5 core network optimization problems extend `BaseProblem` with a unified QUBO API:

```python
from telequm.core.network_snapshot import UniversalNetworkSnapshot
from telequm.problems import PRBAllocationProblem
from telequm.algorithms.hybrid import hybrid_solve

# Build a 3GPP network snapshot
snap = UniversalNetworkSnapshot(source="standalone")
snap.add_cells(7).add_users(50, seed=42).initialize_links()

# Formulate as QUBO and solve using Hybrid Ensemble strategy
problem = PRBAllocationProblem(snap)
result = hybrid_solve(problem, strategy="ensemble")
print("Best Solver:", result["best_method"], "| Cost:", result["best_solution"]["cost"])
```

| Problem | QUBO Variables | Description |
| :--- | :--- | :--- |
| `PRBAllocationProblem` | UE × Cell | Assign users to base stations, maximizing SINR-weighted throughput |
| `RoutingOptimization` | Cell² | Optimal minimum-cost path routing through cell backhaul graph |
| `BeamSelection` | UE × Beams | Discrete codebook beamforming assignment minimizing interference |
| `EnergyEfficiency` | Cell + UE × Cell | Dynamic base station sleep-mode switching + user handover |
| `HandoverOptimization` | UE × Cell | Ping-pong handover mitigation across user trajectory |

---

## 🏗️ Architecture

```
notebooks/
├── telequm/                       # Core Python Package
│   ├── pqc/                       # [NEW] Post-Quantum Cryptography & Security Suite
│   │   ├── algorithms.py          # NIST FIPS 203/204/205, FALCON, code-based, hybrid suites
│   │   ├── protocols.py           # Handshake simulators (TLS 1.3, IPSec, MACsec, 5G AKA, BGP)
│   │   ├── threat_models.py       # HNDL risk scoring engine & Shor/Grover qubit scaling
│   │   └── migration.py           # AQC Whitepaper 5-Pillar Maturity Ladder & sector risk
│   ├── core/                      # UniversalNetworkSnapshot, circuits, hamiltonians
│   ├── algorithms/                # QAOA, VQE, QML (QSVC), HybridSolver (3 strategies)
│   ├── bridges/                   # MATLAB CDL/TDL bridge & ns-3 trace socket ingestion
│   ├── problems/                  # 5 QUBO telecom problem formulations
│   ├── scenarios/                 # Small, Medium, Large, and MobilityStress presets
│   ├── simulator/                 # Discrete time-step engine, traffic, and mobility models
│   └── telecom/                   # 3GPP beamforming and resource allocation math
│
├── dashboard/                     # Interactive Streamlit Application
│   ├── app.py                     # Main navigation and branding
│   ├── components/                # education_hub, use_case_lab, hardware_hub, digital_twin
│   └── utils/                     # plot_helpers (Plotly Gantt, MTU bars, HNDL heatmaps)
│
├── experiments/                   # YAML experiment configs and automated metric logging
├── benchmarks/                    # Reference topologies (Hexagonal, NSFNET, Mesh)
├── tests/                         # 41 comprehensive pytest unit tests
└── .github/workflows/ci.yml       # Automated CI/CD pipeline (Ruff Lint -> Pytest -> Benchmark)
```

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Quantum SDK** | Qiskit 1.x, `qiskit-aer`, `qiskit-algorithms`, `qiskit-optimization` |
| **PQC & Security Modeling** | Pure Python mathematical models for NIST FIPS 203/204/205, IETF RFCs, and 3GPP specs |
| **Classical Optimization** | SciPy, NumPy, Simulated Annealing, Greedy heuristics |
| **Telecom Simulation** | 3GPP TR 38.901 Urban Macro (UMa) models, Poisson/Video/IoT traffic, Vehicular mobility |
| **Dashboard & Visualization** | Streamlit, Plotly (Gantt timing charts, MTU fragmentation bars, 4×4 risk heatmaps) |
| **External Bridges** | MATLAB Engine API for Python (optional), ns-3 TCP socket ingestion (optional) |
| **Quality Assurance** | Pytest (41 tests), Ruff linter, GitHub Actions CI/CD matrix (Python 3.10 / 3.11 / 3.12) |

---

## 🧪 Testing & Verification

We maintain a rigorous automated test suite covering 100% of both core telecom physics and post-quantum cryptography modules:

```bash
# Run full test suite across all modules
python -m pytest tests/ -v

# Run with code coverage reporting
python -m pytest tests/ -v --cov=telequm
```

**41 Automated Tests Passing**:
- **PQC & Security (`tests/test_pqc.py`)**: Verifies algorithm database retrieval, byte sizing, NIST security levels, TLS 1.3 / IPSec / 5G AKA handshake transmission latency, MTU packet fragmentation, HNDL risk scores, Shor/Grover qubit estimation, 5-Pillar maturity evaluation, and Plotly helper rendering.
- **Telecom & Simulation (`tests/test_simulator.py`)**: Verifies `UniversalNetworkSnapshot` immutability, channel matrix shapes, SINR calculations, Poisson/Video/IoT traffic generation, pedestrian/vehicular mobility trajectories, event queue ordering, QUBO translation, QAOA/VQE solver convergence, and benchmark topologies (Hexagonal, NSFNET, Mesh).

---

## 👤 Author

**Abdulmalek Baitulmal**  
*Quantum Strategy Lead (MENA Region)*

- [LinkedIn Profile](https://www.linkedin.com/in/abdulmalek-baitulmal-543753140/)
- Specializing in VQE/QAOA optimization for 6G networks, QEM-Former (Graph Transformer for Quantum Error Mitigation), and IET-published frameworks for national quantum technology adoption.

---

## 📜 License & Contributing

- **License**: MIT License — see [LICENSE](LICENSE) for details.
- **Contributing**: We welcome pull requests! See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflows and code formatting standards.

---

<div align="center">

**TELEQUM v3.0** — *Bridging Raw Radio Physics, Network Logic, and Quantum-Safe Security.*

</div>