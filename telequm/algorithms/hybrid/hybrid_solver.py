"""
Hybrid Quantum-Classical Solver
================================

Implements hybrid AI-assisted optimization pipelines:

```
Traffic prediction → Problem formulation → QAOA/VQE → Network policy
```

Supports optional ML traffic prediction to modify
problem weights before quantum optimization.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from telequm.problems.base_problem import BaseProblem

logger = logging.getLogger("telequm.algorithms.hybrid")


class HybridSolver:
    """
    Hybrid quantum-classical optimization pipeline.

    Pipeline:
    1. (Optional) AI traffic prediction modifies demand weights
    2. Build QUBO from problem
    3. Solve with QAOA/VQE (quantum) or classical baseline
    4. Decode and evaluate solution

    Parameters
    ----------
    strategy : str
        'quantum_first' — try quantum, fall back to classical
        'classical_first' — classical baseline, compare with quantum
        'ensemble' — run both, pick best
    """

    def __init__(self, strategy: str = "quantum_first"):
        self.strategy = strategy
        self._predictor = None

    def set_traffic_predictor(self, predictor) -> None:
        """
        Attach an AI traffic prediction model.

        Parameters
        ----------
        predictor : callable
            Function that takes snapshot and returns predicted demands.
        """
        self._predictor = predictor

    def solve(
        self,
        problem: BaseProblem,
        prediction: np.ndarray | None = None,
        quantum_kwargs: dict | None = None,
        classical_method: str = "greedy",
    ) -> dict:
        """
        Execute hybrid optimization pipeline.

        Parameters
        ----------
        problem : BaseProblem
        prediction : np.ndarray, optional
            Predicted traffic demands to modify problem weights.
        quantum_kwargs : dict
            Passed to quantum solver (algorithm, shots, p, etc.).
        classical_method : str

        Returns
        -------
        dict with solution, metrics, method, runtime
        """
        t0 = time.time()
        quantum_kwargs = quantum_kwargs or {}

        # Step 1: Traffic prediction
        if prediction is not None:
            self._apply_prediction(problem, prediction)
        elif self._predictor is not None:
            pred = self._predictor(problem.snapshot)
            self._apply_prediction(problem, pred)

        # Step 2: Solve based on strategy
        if self.strategy == "quantum_first":
            result = self._quantum_first(problem, quantum_kwargs, classical_method)
        elif self.strategy == "classical_first":
            result = self._classical_first(problem, quantum_kwargs, classical_method)
        elif self.strategy == "ensemble":
            result = self._ensemble(problem, quantum_kwargs, classical_method)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        result["total_runtime_s"] = time.time() - t0
        result["strategy"] = self.strategy
        return result

    def _apply_prediction(self, problem: BaseProblem, prediction: np.ndarray):
        """Modify user demands in snapshot based on prediction."""
        for i, user in enumerate(problem.snapshot.users):
            if i < len(prediction):
                user.traffic_demand_mbps = float(prediction[i])

    def _quantum_first(self, problem, quantum_kwargs, classical_method):
        """Try quantum, fall back to classical on failure."""
        try:
            q_result = problem.solve_quantum(**quantum_kwargs)
            q_metrics = problem.compute_metrics(q_result)
            return {
                "solution": q_result, "metrics": q_metrics,
                "method": "quantum", "fallback": False,
            }
        except Exception as e:
            logger.warning("Quantum solver failed, falling back: %s", e)
            c_result = problem.solve_classical(classical_method)
            c_metrics = problem.compute_metrics(c_result)
            return {
                "solution": c_result, "metrics": c_metrics,
                "method": "classical_fallback", "fallback": True,
            }

    def _classical_first(self, problem, quantum_kwargs, classical_method):
        """Run classical, then compare with quantum."""
        c_result = problem.solve_classical(classical_method)
        c_metrics = problem.compute_metrics(c_result)
        result = {
            "classical": {"solution": c_result, "metrics": c_metrics},
            "method": "classical",
        }

        try:
            q_result = problem.solve_quantum(**quantum_kwargs)
            q_metrics = problem.compute_metrics(q_result)
            result["quantum"] = {"solution": q_result, "metrics": q_metrics}

            # Pick best
            c_cost = c_result.get("cost", float("inf"))
            q_cost = q_result.get("cost", float("inf"))
            result["best"] = "quantum" if q_cost < c_cost else "classical"
            result["improvement_pct"] = ((c_cost - q_cost) / abs(c_cost) * 100) if c_cost != 0 else 0
        except Exception as e:
            logger.info("Quantum comparison skipped: %s", e)

        return result

    def _ensemble(self, problem, quantum_kwargs, classical_method):
        """Run both solvers and return best."""
        results = {}

        # Classical
        c_result = problem.solve_classical(classical_method)
        results["classical"] = {
            "solution": c_result,
            "metrics": problem.compute_metrics(c_result),
            "cost": c_result.get("cost", float("inf")),
        }

        # SA
        sa_result = problem.solve_classical("simulated_annealing")
        results["simulated_annealing"] = {
            "solution": sa_result,
            "metrics": problem.compute_metrics(sa_result),
            "cost": sa_result.get("cost", float("inf")),
        }

        # Quantum (if feasible)
        try:
            q_result = problem.solve_quantum(**quantum_kwargs)
            results["quantum"] = {
                "solution": q_result,
                "metrics": problem.compute_metrics(q_result),
                "cost": q_result.get("cost", float("inf")),
            }
        except Exception as e:
            logger.info("Quantum skipped in ensemble: %s", e)

        # Pick winner
        best_key = min(results, key=lambda k: results[k]["cost"])
        return {
            "all_results": results,
            "best_method": best_key,
            "best_solution": results[best_key],
            "method": "ensemble",
        }


def hybrid_solve(
    problem: BaseProblem,
    prediction: np.ndarray | None = None,
    strategy: str = "quantum_first",
    **kwargs,
) -> dict:
    """
    Convenience function for hybrid solving.

    Parameters
    ----------
    problem : BaseProblem
    prediction : np.ndarray, optional
    strategy : str

    Returns
    -------
    dict
    """
    solver = HybridSolver(strategy=strategy)
    return solver.solve(problem, prediction=prediction, **kwargs)
