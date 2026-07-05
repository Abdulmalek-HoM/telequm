"""
Telecom-Specific Hamiltonians for Quantum Optimization
=======================================================

This module provides Hamiltonian formulations for common telecom
optimization problems, ready for use with VQE and QAOA algorithms.
"""

import networkx as nx
import numpy as np

try:
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.converters import QuadraticProgramToQubo
    QISKIT_OPT_AVAILABLE = True
except ImportError:
    QISKIT_OPT_AVAILABLE = False


def create_max_cut_hamiltonian(
    graph: nx.Graph,
    weight_key: str = "weight"
) -> "SparsePauliOp":
    """
    Create a Max-Cut Hamiltonian for network partitioning.

    Max-Cut is fundamental for network segmentation, load balancing,
    and resource partitioning in telecommunications.

    The Hamiltonian is: H = Σ_{(i,j)∈E} w_ij * (1 - Z_i Z_j) / 2

    Parameters
    ----------
    graph : nx.Graph
        NetworkX graph representing the network topology
    weight_key : str
        Edge attribute key for weights (default: 'weight')

    Returns
    -------
    SparsePauliOp
        Hamiltonian as a Qiskit SparsePauliOp

    Example
    -------
    >>> import networkx as nx
    >>> from telequm.core.hamiltonians import create_max_cut_hamiltonian
    >>> G = nx.petersen_graph()
    >>> H = create_max_cut_hamiltonian(G)
    """
    num_nodes = graph.number_of_nodes()
    pauli_list = []
    coeffs = []

    for i, j in graph.edges():
        weight = graph[i][j].get(weight_key, 1.0)

        # ZZ term
        pauli_str = ["I"] * num_nodes
        pauli_str[i] = "Z"
        pauli_str[j] = "Z"
        pauli_list.append("".join(reversed(pauli_str)))
        coeffs.append(-weight / 2)

        # Identity offset
        pauli_list.append("I" * num_nodes)
        coeffs.append(weight / 2)

    return SparsePauliOp.from_list(list(zip(pauli_list, coeffs, strict=False))).simplify()


def create_resource_allocation_hamiltonian(
    num_resources: int,
    num_users: int,
    demand_matrix: np.ndarray,
    capacity_vector: np.ndarray,
    penalty_strength: float = 10.0
) -> tuple["SparsePauliOp", dict]:
    """
    Create a Hamiltonian for resource allocation in telecom networks.

    This models the assignment of network resources (channels, spectrum,
    compute) to users with constraints on capacity and demand satisfaction.

    Parameters
    ----------
    num_resources : int
        Number of resources (e.g., frequency channels)
    num_users : int
        Number of users/devices to serve
    demand_matrix : np.ndarray
        Shape (num_users, num_resources): benefit of assigning resource r to user u
    capacity_vector : np.ndarray
        Shape (num_resources,): maximum capacity of each resource
    penalty_strength : float
        Penalty for constraint violations (default: 10.0)

    Returns
    -------
    Tuple[SparsePauliOp, Dict]
        Hamiltonian and metadata dict containing qubit mapping
    """
    if not QISKIT_OPT_AVAILABLE:
        raise ImportError("qiskit-optimization required for resource allocation Hamiltonian")

    # Create QUBO formulation
    qp = QuadraticProgram("Resource_Allocation")

    # Binary variables: x_{u,r} = 1 if user u uses resource r
    for u in range(num_users):
        for r in range(num_resources):
            qp.binary_var(f"x_{u}_{r}")

    # Objective: Maximize total benefit (minimize negative)
    linear = {}
    for u in range(num_users):
        for r in range(num_resources):
            linear[f"x_{u}_{r}"] = -demand_matrix[u, r]  # Negative for minimization
    qp.minimize(linear=linear)

    # Constraint: Each user gets at most one resource
    for u in range(num_users):
        constraint_vars = {f"x_{u}_{r}": 1 for r in range(num_resources)}
        qp.linear_constraint(linear=constraint_vars, sense="<=", rhs=1, name=f"user_{u}_limit")

    # Constraint: Each resource serves at most capacity_vector[r] users
    for r in range(num_resources):
        constraint_vars = {f"x_{u}_{r}": 1 for u in range(num_users)}
        qp.linear_constraint(
            linear=constraint_vars,
            sense="<=",
            rhs=int(capacity_vector[r]),
            name=f"resource_{r}_capacity"
        )

    # Convert to QUBO
    converter = QuadraticProgramToQubo(penalty=penalty_strength)
    qubo = converter.convert(qp)

    # Get Hamiltonian
    hamiltonian, offset = qubo.to_ising()

    metadata = {
        "num_qubits": num_users * num_resources,
        "qubit_mapping": {
            (u, r): u * num_resources + r
            for u in range(num_users)
            for r in range(num_resources)
        },
        "offset": offset,
        "original_qp": qp
    }

    return hamiltonian, metadata


def create_network_optimization_hamiltonian(
    adjacency_matrix: np.ndarray,
    node_weights: np.ndarray | None = None,
    problem_type: str = "min_vertex_cover"
) -> tuple["SparsePauliOp", dict]:
    """
    Create Hamiltonians for common network optimization problems.

    Parameters
    ----------
    adjacency_matrix : np.ndarray
        Square adjacency matrix of the network graph
    node_weights : np.ndarray, optional
        Weights for each node (default: uniform weight of 1)
    problem_type : str
        Type of optimization:
        - 'min_vertex_cover': Minimum nodes to cover all edges
        - 'max_independent_set': Maximum non-adjacent nodes
        - 'graph_coloring': Minimum colors for valid coloring

    Returns
    -------
    Tuple[SparsePauliOp, Dict]
        Hamiltonian and metadata
    """
    n = adjacency_matrix.shape[0]

    if node_weights is None:
        node_weights = np.ones(n)

    # Build graph
    G = nx.from_numpy_array(adjacency_matrix)

    if problem_type == "min_vertex_cover":
        return _min_vertex_cover_hamiltonian(G, node_weights)
    elif problem_type == "max_independent_set":
        return _max_independent_set_hamiltonian(G, node_weights)
    else:
        raise ValueError(f"Unknown problem type: {problem_type}")


def _min_vertex_cover_hamiltonian(
    graph: nx.Graph,
    node_weights: np.ndarray,
    penalty: float = 10.0
) -> tuple["SparsePauliOp", dict]:
    """Create Min Vertex Cover Hamiltonian."""
    n = graph.number_of_nodes()
    pauli_list = []
    coeffs = []

    # Objective: minimize sum of selected nodes
    for i in range(n):
        pauli_str = ["I"] * n
        pauli_str[i] = "Z"
        pauli_list.append("".join(reversed(pauli_str)))
        coeffs.append(-node_weights[i] / 2)

        pauli_list.append("I" * n)
        coeffs.append(node_weights[i] / 2)

    # Penalty for uncovered edges: each edge must have at least one endpoint selected
    for u, v in graph.edges():
        # Penalty = penalty * (1-x_u)(1-x_v) = penalty * (1 - x_u - x_v + x_u*x_v)
        # In Ising: x_i = (1 - Z_i)/2
        pauli_str = ["I"] * n
        pauli_str[u] = "Z"
        pauli_str[v] = "Z"
        pauli_list.append("".join(reversed(pauli_str)))
        coeffs.append(penalty / 4)

        for node in [u, v]:
            pauli_str = ["I"] * n
            pauli_str[node] = "Z"
            pauli_list.append("".join(reversed(pauli_str)))
            coeffs.append(penalty / 4)

        pauli_list.append("I" * n)
        coeffs.append(penalty / 4)

    hamiltonian = SparsePauliOp.from_list(list(zip(pauli_list, coeffs, strict=False))).simplify()

    metadata = {
        "num_qubits": n,
        "problem_type": "min_vertex_cover",
        "graph": graph
    }

    return hamiltonian, metadata


def _max_independent_set_hamiltonian(
    graph: nx.Graph,
    node_weights: np.ndarray,
    penalty: float = 10.0
) -> tuple["SparsePauliOp", dict]:
    """Create Max Independent Set Hamiltonian."""
    n = graph.number_of_nodes()
    pauli_list = []
    coeffs = []

    # Objective: maximize sum of selected nodes (minimize negative)
    for i in range(n):
        pauli_str = ["I"] * n
        pauli_str[i] = "Z"
        pauli_list.append("".join(reversed(pauli_str)))
        coeffs.append(node_weights[i] / 2)  # Positive because we want to maximize

        pauli_list.append("I" * n)
        coeffs.append(-node_weights[i] / 2)

    # Penalty for adjacent selected nodes
    for u, v in graph.edges():
        pauli_str = ["I"] * n
        pauli_str[u] = "Z"
        pauli_str[v] = "Z"
        pauli_list.append("".join(reversed(pauli_str)))
        coeffs.append(penalty / 4)

        for node in [u, v]:
            pauli_str = ["I"] * n
            pauli_str[node] = "Z"
            pauli_list.append("".join(reversed(pauli_str)))
            coeffs.append(-penalty / 4)

        pauli_list.append("I" * n)
        coeffs.append(penalty / 4)

    hamiltonian = SparsePauliOp.from_list(list(zip(pauli_list, coeffs, strict=False))).simplify()

    metadata = {
        "num_qubits": n,
        "problem_type": "max_independent_set",
        "graph": graph
    }

    return hamiltonian, metadata
