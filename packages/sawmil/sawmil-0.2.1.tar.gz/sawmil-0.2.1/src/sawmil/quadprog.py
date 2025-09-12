from __future__ import annotations
import logging
import numpy as np
import numpy.typing as npt
from typing import Optional, Tuple, Union, Mapping, Any
from .solvers.objective import Objective

try:
    from .solvers._gurobi import quadprog_gurobi as _qp_gurobi
except Exception:  # Gurobi not installed
    _qp_gurobi = None
try:
    from .solvers._osqp import quadprog_osqp as _qp_osqp
except Exception:  # OSQP not installed
    _qp_osqp = None

try:
    from .solvers._daqp import quadprog_daqp as _qp_daqp
except Exception:  # DAQP not installed
    _qp_daqp = None

log = logging.getLogger("quadprog")

def _check_param(d, key):
    if key not in d:
        raise KeyError(f"Missing required parameter: '{key}'")
    return d[key]

def _nearest_psd(H: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    # assumes H is symmetric
    w, V = np.linalg.eigh(H)
    w_clipped = np.maximum(w, eps)
    return (V * w_clipped) @ V.T  # V @ diag(w_clipped) @ V.T

def _validate_and_stabilize(
    H: npt.NDArray[np.float64],
    f: npt.NDArray[np.float64],
    Aeq: Optional[npt.NDArray[np.float64]],
    beq: Optional[npt.NDArray[np.float64]],
    lb: npt.NDArray[np.float64],
    ub: npt.NDArray[np.float64],
    jitter: float = 1e-8,
    stabilize: bool = True
):
    """
    Validate and stabilize the quadratic program inputs.

    This function performs the following:
      • Ensures all inputs are converted to float64 NumPy arrays (with copies, 
        so originals are untouched).
      • Validates shapes and consistency of arguments.
      • Checks that bound constraints are valid (lb ≤ ub).
      • Symmetrizes the Hessian H to enforce numerical stability.
      • Adds a small diagonal jitter to H to guarantee positive semidefiniteness.

    Args:
        H: (n, n) Hessian matrix for the quadratic term in 0.5 * αᵀ H α.
           For SVM duals, this is typically (y yᵀ) ⊙ K where K is the kernel matrix.
        f: (n,) linear term vector in fᵀ α. For SVMs, usually -1 for each component.
        Aeq: (m, n) optional equality constraint matrix, e.g. yᵀ for SVM bias constraint.
        beq: (m,) optional right-hand side of equality constraint, usually 0.
        lb: (n,) lower bound vector, e.g. all zeros in standard SVM dual.
        ub: (n,) upper bound vector, e.g. all entries equal to C in soft-margin SVM.
        jitter: Small positive value added to the diagonal of H for numerical stability.
        stabilize: Whether to apply stabilization (symmetrization + jitter) to the problem.
        

    Returns:
        Tuple of (H, f, Aeq, beq, lb, ub), all coerced to float64 arrays, 
        with H symmetrized and regularized.

    Raises:
        ValueError: if input shapes are inconsistent or bounds are invalid.
    """

    # Coerce, copy and dtype
    H = np.asarray(H, dtype=np.float64).copy()
    f = np.asarray(f, dtype=np.float64).ravel().copy()
    lb = np.asarray(lb, dtype=np.float64).ravel().copy()
    ub = np.asarray(ub, dtype=np.float64).ravel().copy()

    # Shapes
    if H.ndim != 2 or H.shape[0] != H.shape[1]:
        raise ValueError(f"H must be square (n,n); got {H.shape}")
    n = H.shape[0]
    if f.shape != (n,):
        raise ValueError(f"f must be shape (n,); got {f.shape}")
    if lb.shape != (n,) or ub.shape != (n,):
        raise ValueError(
            f"lb and ub must be shape (n,); got {lb.shape}, {ub.shape}")
    if np.any(lb > ub):
        raise ValueError("Each component must satisfy lb[i] <= ub[i].")

    if (Aeq is None) ^ (beq is None):
        raise ValueError("Provide both Aeq and beq, or neither.")
    if Aeq is not None:
        Aeq = np.atleast_2d(np.asarray(Aeq, dtype=np.float64)).copy()
        beq = np.asarray(beq, dtype=np.float64)
        # Accept (m,), (m,1), or (1,m)
        if beq.ndim == 2 and 1 in beq.shape:
            beq = beq.ravel()
        beq = beq.copy()
        if Aeq.shape[1] != n:
            raise ValueError(f"Aeq must have {n} columns; got {Aeq.shape[1]}")
        if beq.shape != (Aeq.shape[0],):
            raise ValueError(f"beq must have shape (m,); got {beq.shape}")

    # Symmetrize + jitter (for numerical PSD)
    if stabilize:
        H = 0.5 * (H + H.T)
        H[np.diag_indices_from(H)] += jitter

    return H, f, Aeq, beq, lb, ub


def quadprog(
    H: npt.NDArray[np.float64],
    f: npt.NDArray[np.float64],
    Aeq: Optional[npt.NDArray[np.float64]],
    beq: Optional[npt.NDArray[np.float64]],
    lb: npt.NDArray[np.float64],
    ub: npt.NDArray[np.float64],
    solver: str = "gurobi",
    verbose: bool = False,
    solver_params: Optional[Mapping[str, Any]] = None,
) -> Union[Tuple[npt.NDArray[np.float64], "Objective"], None]:
    """
    Solve the quadratic program:

        minimize   0.5 * αᵀ H α + fᵀ α
        subject to Aeq α = beq
                   lb ≤ α ≤ ub

    Args:
        H: (n, n) quadratic term matrix in 0.5 * αᵀ H α
        f: (n,) linear term vector in fᵀ α , usually f = -1
        Aeq: (m, n) equality constraint matrix, usually yᵀ
        beq: (m,) equality constraint rhs, usually 0
        lb: (n,) lower bound vector, usually 0
        ub: (n,) upper bound vector, usually C
        verbose: If True, print solver logs
        solver_params: dict of backend-specific options. 
            Examples:
                - solver='gurobi': {'env': <gp.Env>, 'params': {'Method':2, 'Threads':1}}
                - solver='osqp'  : {'setup': {...}, 'solve': {...}} or flat keys for setup
                - solver='daqp'  : {'eps_abs': 1e-8, 'eps_rel': 1e-8, ...}

    Returns:
        α*: Optimal solution vector
        Objective: quadratic and linear parts of the optimum
    """
    H, f, Aeq, beq, lb, ub = _validate_and_stabilize(H, f, Aeq, beq, lb, ub)

    params = dict(solver_params or {})
    if params:
        print(f"Using solver '{solver}' with params: {params}")

    if solver == "gurobi":
        if _qp_gurobi is None:
            raise ImportError("gurobi path selected but 'gurobipy' is not installed or usable. "
                              "Install with: pip install sawmil[gurobi]")
        return _qp_gurobi(H, f, Aeq, beq, lb, ub, verbose=verbose, **params)

    elif solver == "osqp":
        if _qp_osqp is None:
            raise ImportError("osqp path selected but 'osqp' is not installed. "
                              "Install with: pip install sawmil[osqp]")
        return _qp_osqp(H, f, Aeq, beq, lb, ub, verbose=verbose, **params)
    elif solver == "daqp":
        if _qp_daqp is None:
            raise ImportError("daqp path selected but 'daqp' is not installed. "
                              "Install with: pip install sawmil[daqp]")
        return _qp_daqp(H, f, Aeq, beq, lb, ub, verbose=verbose, **params)

    raise ValueError(f"Unknown solver: {solver}")
