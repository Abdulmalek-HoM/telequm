"""
Resource Allocation for Telecommunications
==========================================

Quantum-enhanced resource allocation for spectrum, channels,
and network resources in telecom networks.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

from telequm.algorithms.vqe import ResourceVQE
from telequm.core.hamiltonians import create_resource_allocation_hamiltonian


class ResourceAllocator:
    """
    Quantum resource allocator for telecom networks.
    
    Handles spectrum allocation, channel assignment, and 
    compute resource distribution using VQE optimization.
    
    Parameters
    ----------
    num_resources : int
        Number of resources (channels, spectrum blocks, etc.)
    num_users : int
        Number of users/devices to allocate to
    
    Example
    -------
    >>> from telequm.telecom import ResourceAllocator
    >>> allocator = ResourceAllocator(num_resources=8, num_users=4)
    >>> demand = np.random.rand(4, 8)
    >>> allocation = allocator.allocate(demand)
    """
    
    def __init__(self, num_resources: int, num_users: int):
        self.num_resources = num_resources
        self.num_users = num_users
        self.last_result = None
    
    def allocate(
        self,
        demand_matrix: np.ndarray,
        capacity_vector: Optional[np.ndarray] = None,
        method: str = "quantum",
        shots: int = 1024,
        maxiter: int = 100
    ) -> Dict:
        """
        Allocate resources to users.
        
        Parameters
        ----------
        demand_matrix : np.ndarray
            Benefit matrix (num_users x num_resources)
        capacity_vector : np.ndarray, optional
            Capacity constraints per resource
        method : str
            'quantum' (VQE) or 'classical' (greedy)
        shots : int
            Measurement shots for quantum method
        maxiter : int
            Maximum optimization iterations
        
        Returns
        -------
        Dict
            Allocation result with assignment matrix and metrics
        """
        if capacity_vector is None:
            capacity_vector = np.ones(self.num_resources) * 2  # Default: 2 users per resource
        
        if method == "quantum":
            return self._quantum_allocate(demand_matrix, capacity_vector, shots, maxiter)
        else:
            return self._classical_allocate(demand_matrix, capacity_vector)
    
    def _quantum_allocate(
        self,
        demand_matrix: np.ndarray,
        capacity_vector: np.ndarray,
        shots: int,
        maxiter: int
    ) -> Dict:
        """Quantum allocation using VQE."""
        # Create Hamiltonian
        hamiltonian, metadata = create_resource_allocation_hamiltonian(
            self.num_resources,
            self.num_users,
            demand_matrix,
            capacity_vector
        )
        
        # Run VQE
        vqe = ResourceVQE(
            num_qubits=metadata["num_qubits"],
            hamiltonian=hamiltonian,
            num_layers=2
        )
        
        result = vqe.optimize(shots=shots, maxiter=maxiter)
        
        # Decode allocation
        bitstring = result["optimal_bitstring"]
        allocation = self._decode_allocation(bitstring)
        
        self.last_result = {
            "allocation": allocation,
            "energy": result["optimal_energy"],
            "bitstring": bitstring,
            "total_benefit": self._compute_benefit(allocation, demand_matrix),
            "method": "quantum_vqe"
        }
        
        return self.last_result
    
    def _classical_allocate(
        self,
        demand_matrix: np.ndarray,
        capacity_vector: np.ndarray
    ) -> Dict:
        """Classical greedy allocation."""
        allocation = np.zeros((self.num_users, self.num_resources), dtype=int)
        resource_load = np.zeros(self.num_resources)
        
        # Sort by maximum demand
        flat_demands = []
        for u in range(self.num_users):
            for r in range(self.num_resources):
                flat_demands.append((demand_matrix[u, r], u, r))
        
        flat_demands.sort(reverse=True)
        user_assigned = np.zeros(self.num_users, dtype=bool)
        
        for demand, u, r in flat_demands:
            if not user_assigned[u] and resource_load[r] < capacity_vector[r]:
                allocation[u, r] = 1
                resource_load[r] += 1
                user_assigned[u] = True
        
        self.last_result = {
            "allocation": allocation,
            "total_benefit": self._compute_benefit(allocation, demand_matrix),
            "method": "classical_greedy"
        }
        
        return self.last_result
    
    def _decode_allocation(self, bitstring: str) -> np.ndarray:
        """Decode bitstring to allocation matrix."""
        allocation = np.zeros((self.num_users, self.num_resources), dtype=int)
        
        for u in range(self.num_users):
            for r in range(self.num_resources):
                idx = u * self.num_resources + r
                if idx < len(bitstring):
                    allocation[u, r] = int(bitstring[-(idx + 1)])
        
        return allocation
    
    def _compute_benefit(
        self,
        allocation: np.ndarray,
        demand_matrix: np.ndarray
    ) -> float:
        """Compute total benefit of allocation."""
        return float(np.sum(allocation * demand_matrix))


def optimize_spectrum_allocation(
    num_channels: int,
    num_users: int,
    interference_matrix: np.ndarray,
    demand_vector: np.ndarray,
    method: str = "quantum"
) -> Dict:
    """
    Optimize spectrum/frequency allocation.
    
    Parameters
    ----------
    num_channels : int
        Number of frequency channels
    num_users : int
        Number of users
    interference_matrix : np.ndarray
        Interference between channel-user pairs
    demand_vector : np.ndarray
        Bandwidth demand per user
    method : str
        'quantum' or 'classical'
    
    Returns
    -------
    Dict
        Optimization result
    """
    # Convert to demand matrix format
    demand_matrix = np.outer(demand_vector, np.ones(num_channels))
    demand_matrix *= (1 - interference_matrix)  # Penalize interference
    
    allocator = ResourceAllocator(num_channels, num_users)
    return allocator.allocate(demand_matrix, method=method)


def optimize_channel_assignment(
    base_stations: List[Dict],
    mobile_users: List[Dict],
    max_load_per_bs: int = 10
) -> Dict:
    """
    Assign mobile users to base stations.
    
    Parameters
    ----------
    base_stations : list of dict
        Base station configs with 'id', 'position', 'capacity'
    mobile_users : list of dict
        User configs with 'id', 'position', 'demand'
    max_load_per_bs : int
        Maximum users per base station
    
    Returns
    -------
    Dict
        Assignment result
    """
    num_bs = len(base_stations)
    num_users = len(mobile_users)
    
    # Compute signal quality matrix (inverse of distance)
    demand_matrix = np.zeros((num_users, num_bs))
    for u, user in enumerate(mobile_users):
        for b, bs in enumerate(base_stations):
            # Simple distance-based quality
            dist = np.sqrt(
                (user["position"][0] - bs["position"][0]) ** 2 +
                (user["position"][1] - bs["position"][1]) ** 2
            )
            demand_matrix[u, b] = user.get("demand", 1.0) / (dist + 0.1)
    
    capacity_vector = np.array([
        bs.get("capacity", max_load_per_bs) for bs in base_stations
    ])
    
    allocator = ResourceAllocator(num_bs, num_users)
    result = allocator.allocate(demand_matrix, capacity_vector)
    
    # Format result
    assignments = {}
    for u in range(num_users):
        for b in range(num_bs):
            if result["allocation"][u, b] == 1:
                assignments[mobile_users[u]["id"]] = base_stations[b]["id"]
    
    result["assignments"] = assignments
    return result
