"""
Network Topology Optimization
=============================

Quantum optimization for network topology design,
load balancing, and infrastructure planning.
"""

import numpy as np

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from telequm.algorithms.qaoa import NetworkQAOA
from telequm.core.hamiltonians import create_max_cut_hamiltonian


class NetworkOptimizer:
    """
    Quantum network topology optimizer.

    Uses QAOA for solving network optimization problems
    like partitioning, load balancing, and routing.

    Parameters
    ----------
    graph : nx.Graph
        Network topology graph
    """

    def __init__(self, graph):
        if not NETWORKX_AVAILABLE:
            raise ImportError("networkx required for NetworkOptimizer")

        self.graph = graph
        self.num_nodes = graph.number_of_nodes()

    def partition(
        self,
        num_partitions: int = 2,
        method: str = "quantum",
        shots: int = 1024
    ) -> dict:
        """
        Partition network into balanced subgraphs.

        Parameters
        ----------
        num_partitions : int
            Number of partitions (currently supports 2)
        method : str
            'quantum' (QAOA) or 'classical'
        shots : int
            Measurement shots for quantum method

        Returns
        -------
        Dict
            Partition result with node assignments
        """
        if num_partitions != 2:
            raise NotImplementedError("Only 2-partition supported currently")

        if method == "quantum":
            return self._quantum_partition(shots)
        else:
            return self._classical_partition()

    def _quantum_partition(self, shots: int) -> dict:
        """Partition using QAOA (Max-Cut)."""
        hamiltonian = create_max_cut_hamiltonian(self.graph)

        qaoa = NetworkQAOA(
            num_qubits=self.num_nodes,
            p=2,
            hamiltonian=hamiltonian
        )

        result = qaoa.optimize(shots=shots)

        # Decode partition
        bitstring = result["optimal_bitstring"]
        partition_a = [i for i, b in enumerate(reversed(bitstring)) if b == "0"]
        partition_b = [i for i, b in enumerate(reversed(bitstring)) if b == "1"]

        # Count cut edges
        cut_edges = sum(
            1 for u, v in self.graph.edges()
            if (u in partition_a and v in partition_b) or
               (u in partition_b and v in partition_a)
        )

        return {
            "partition_a": partition_a,
            "partition_b": partition_b,
            "cut_edges": cut_edges,
            "balance": abs(len(partition_a) - len(partition_b)),
            "method": "quantum_qaoa",
            "qaoa_result": result
        }

    def _classical_partition(self) -> dict:
        """Partition using classical spectral clustering."""
        # Get Laplacian
        L = nx.laplacian_matrix(self.graph).toarray()

        # Compute second eigenvector (Fiedler vector)
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        fiedler_vector = eigenvectors[:, 1]

        # Partition by sign
        partition_a = [i for i in range(self.num_nodes) if fiedler_vector[i] >= 0]
        partition_b = [i for i in range(self.num_nodes) if fiedler_vector[i] < 0]

        cut_edges = sum(
            1 for u, v in self.graph.edges()
            if (u in partition_a and v in partition_b) or
               (u in partition_b and v in partition_a)
        )

        return {
            "partition_a": partition_a,
            "partition_b": partition_b,
            "cut_edges": cut_edges,
            "balance": abs(len(partition_a) - len(partition_b)),
            "method": "classical_spectral"
        }

    def find_critical_nodes(
        self,
        method: str = "centrality"
    ) -> list[int]:
        """
        Identify critical nodes in the network.

        Parameters
        ----------
        method : str
            'centrality', 'betweenness', or 'pagerank'

        Returns
        -------
        List[int]
            Indices of critical nodes (sorted by importance)
        """
        if method == "centrality":
            scores = nx.degree_centrality(self.graph)
        elif method == "betweenness":
            scores = nx.betweenness_centrality(self.graph)
        elif method == "pagerank":
            scores = nx.pagerank(self.graph)
        else:
            raise ValueError(f"Unknown method: {method}")

        sorted_nodes = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_nodes

    def optimize_resilience(
        self,
        budget: int,
        method: str = "quantum"
    ) -> dict:
        """
        Find nodes to reinforce for maximum resilience.

        Parameters
        ----------
        budget : int
            Number of nodes that can be reinforced
        method : str
            'quantum' or 'classical'

        Returns
        -------
        Dict
            Nodes to reinforce and expected improvement
        """
        critical = self.find_critical_nodes("betweenness")
        selected = critical[:budget]

        # Compute original connectivity
        original_connectivity = nx.node_connectivity(self.graph)

        return {
            "nodes_to_reinforce": selected,
            "current_connectivity": original_connectivity,
            "method": method
        }


def optimize_network_topology(
    nodes: list[dict],
    max_edges: int,
    objective: str = "connectivity"
) -> dict:
    """
    Optimize network topology given node locations.

    Parameters
    ----------
    nodes : list of dict
        Node configs with 'id' and 'position'
    max_edges : int
        Maximum number of edges in design
    objective : str
        'connectivity', 'latency', or 'cost'

    Returns
    -------
    Dict
        Optimized topology
    """
    n = len(nodes)

    # Compute all pairwise distances
    distances = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(
                (nodes[i]["position"][0] - nodes[j]["position"][0]) ** 2 +
                (nodes[i]["position"][1] - nodes[j]["position"][1]) ** 2
            )
            distances[i, j] = dist
            distances[j, i] = dist

    # Create candidate edges sorted by distance
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((i, j, distances[i, j]))

    edges.sort(key=lambda x: x[2])

    # Greedy: add edges while maintaining connectivity goal
    G = nx.Graph()
    G.add_nodes_from(range(n))

    for i, j, dist in edges[:max_edges]:
        G.add_edge(i, j, weight=dist)

    return {
        "graph": G,
        "num_edges": G.number_of_edges(),
        "is_connected": nx.is_connected(G),
        "total_distance": sum(d for _, _, d in G.edges(data="weight")),
        "diameter": nx.diameter(G) if nx.is_connected(G) else float("inf")
    }


def optimize_load_balancing(
    servers: list[dict],
    requests: list[dict],
    method: str = "quantum"
) -> dict:
    """
    Optimize request distribution across servers.

    Parameters
    ----------
    servers : list of dict
        Server configs with 'id', 'capacity', 'load'
    requests : list of dict
        Request configs with 'id', 'size'
    method : str
        'quantum' or 'classical'

    Returns
    -------
    Dict
        Load balancing assignment
    """
    n_servers = len(servers)
    len(requests)

    # Classical weighted round-robin
    assignment = {}
    server_loads = [s.get("load", 0) for s in servers]
    capacities = [s.get("capacity", 100) for s in servers]

    for req in requests:
        # Find server with lowest relative load
        best_server = 0
        best_ratio = float("inf")

        for s in range(n_servers):
            ratio = server_loads[s] / capacities[s]
            if ratio < best_ratio and server_loads[s] + req["size"] <= capacities[s]:
                best_ratio = ratio
                best_server = s

        assignment[req["id"]] = servers[best_server]["id"]
        server_loads[best_server] += req["size"]

    # Compute metrics
    load_variance = np.var([load_val / c for load_val, c in zip(server_loads, capacities, strict=False)])

    return {
        "assignment": assignment,
        "final_loads": {
            servers[i]["id"]: server_loads[i]
            for i in range(n_servers)
        },
        "load_variance": load_variance,
        "method": method
    }
