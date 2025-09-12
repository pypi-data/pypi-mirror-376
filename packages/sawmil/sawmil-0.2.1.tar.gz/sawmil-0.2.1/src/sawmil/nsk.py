# sparse_mil/nsk.py
from __future__ import annotations
from typing import Optional, Sequence, List, Literal, Any, Mapping
import numpy as np
import numpy.typing as npt

from .svm import SVM
from .bag import Bag, BagDataset
from .kernels import get_kernel, KernelType, Linear
from .bag_kernels import BaseBagKernel, make_bag_kernel, WeightedMeanBagKernel
from .quadprog import quadprog


class NSK(SVM):
    """
    Normalized Set Kernel SVM on bags of instances.
    Builds a bag-level Gram matrix with a bag kernel, then solves the standard SVM dual.
    """

    def __init__(
        self,
        C: float = 1.0,
        # If bag_kernel is None, we'll build one from this instance-kernel spec:
        kernel: KernelType = "linear",
        solver: str = 'gurobi',
        *,
        # Bag kernel settings:
        normalizer: Literal["none", "average", "featurespace"] = "none",
        p: float = 1.0,
        # Solver / SVM settings:
        scale_C: bool = True,
        tol: float = 1e-8,
        verbose: bool = False,
        solver_params: Optional[Mapping[str, Any]] = None
    ) -> "NSK":
        """
        Initialize the NSK model.

        Args:
            C: Regularization parameter.
            kernel: Kernel type (default: "linear").
            solver: Solver to use (default: "gurobi").
            normalizer: Bag kernel normalization method (default: "none").
            p: Parameter for bag kernel (default: 1.0).
            scale_C: Whether to scale C (default: True).
            tol: Tolerance for stopping criteria (default: 1e-8).
            verbose: Whether to print verbose output (default: False).
            solver_params: Additional parameters for the solver (default: None).

        Returns:
            NSK: Initialized NSK model.
        """
        # parent SVM stores common attrs; kernel arg unused here
        super().__init__(C=C, kernel=kernel, tol=tol, verbose=verbose, solver=solver)
        self.scale_C = scale_C

        # How to build the bag kernel (if not provided)
        self.kernel = kernel
        # Bag Kernel
        self.normalizer = normalizer
        self.p = p
        self.bag_kernel = make_bag_kernel(inst_kernel=self.kernel, normalizer=self.normalizer,
                                          p=self.p)
        self.solver_params = dict(solver_params or {})

        # Fitted state
        # training bags (ordering does not matter)
        self.bags_: Optional[List[Bag]] = None

    # ---------- helpers ----------
    @staticmethod
    def _coerce_bags_and_labels(
        bags: Sequence[Bag] | BagDataset | Sequence[np.ndarray],
        y: Optional[npt.NDArray[np.float64]] = None
    ) -> tuple[List[Bag], npt.NDArray[np.float64]]:
        # BagDataset
        if isinstance(bags, BagDataset):
            blist = list(bags.bags)
            y_arr = np.asarray([b.y for b in blist], dtype=float)
            return blist, y_arr
        # List[Bag]
        if len(bags) > 0 and isinstance(bags[0], Bag):  # type: ignore[index]
            blist = list(bags)  # type: ignore[assignment]
            y_arr = np.asarray([b.y for b in blist], dtype=float) if y is None else np.asarray(
                y, dtype=float).ravel()
            if y is not None and y_arr.shape[0] != len(blist):
                raise ValueError("Length of y must equal number of bags.")
            return blist, y_arr
        if y is None:
            raise ValueError(
                "When passing raw arrays for bags, you must also pass y.")
        blist = [Bag(X=np.asarray(b, dtype=float), y=float(lbl))
                 for b, lbl in zip(bags, y)]
        return blist, np.asarray(y, dtype=float).ravel()

    def _ensure_bag_kernel(self) -> BaseBagKernel:
        if self.bag_kernel is not None:
            return self.bag_kernel
        # Build instance kernel, then lift to a bag kernel
        inst_k = get_kernel(self.base_kernel, gamma=self.gamma,
                            degree=self.degree, coef0=self.coef0)
        # Note: bag_kernels make normalized weights (means) in the numerator,
        # so to avoid double normalization we default to normalizer="none".
        self.bag_kernel = make_bag_kernel(
            inst_kernel=inst_k,
            normalizer=self.normalizer,
            p=self.p
        )
        # Fit once to allow instance kernel to set defaults (e.g., gamma)
        # (bag_k.fit looks at the first non-empty bag for dimensionality)
        return self.bag_kernel

    def _can_linearize(self, bk) -> bool:
        # recover w only for linear instance kernel + WeightedMeanBagKernel + p=1
        return (
            isinstance(bk, WeightedMeanBagKernel)
            and isinstance(bk.inst_kernel, Linear)
            and abs(bk.p - 1.0) < 1e-12
        )

    # ---------- sklearn-style API ----------
    def fit(self, bags: Sequence[Bag] | BagDataset | Sequence[np.ndarray],
            y: Optional[npt.NDArray[np.float64]] = None) -> "NSK":
        '''
        Fit the model to the training data.
        Returns:
            NSK: Fitted estimator.
        '''
        bag_list, y_arr = self._coerce_bags_and_labels(bags, y)
        if len(bag_list) == 0:
            raise ValueError("No bags provided.")
        self.bags_ = bag_list

        # Map labels to {-1, +1} (store original classes)
        classes = np.unique(y_arr)
        if classes.size != 2:
            raise ValueError(
                "Binary classification only—y must have exactly two classes.")
        self.classes_ = classes.astype(float)
        Y = np.where(y_arr == classes[0], -1.0, 1.0)
        self.y_ = Y

        # Bag kernel -> Gram
        bk = self._ensure_bag_kernel()
        bk.fit(bag_list)
        K = bk(bag_list, bag_list)  # (n_bags, n_bags)

        # Build dual QP (same as SVM)
        H = (Y[:, None] * Y[None, :]) * K
        n = len(bag_list)
        f = -np.ones(n, dtype=float)
        Aeq = Y.reshape(1, -1)
        beq = np.array([0.0], dtype=float)
        C_eff = (float(self.C) / n) if self.scale_C else float(self.C)
        lb = np.zeros(n, dtype=float)
        ub = np.full(n, C_eff, dtype=float)

        # Solve (reuse your quadprog function from SVM)
        alpha, _ = quadprog(H, f, Aeq, beq, lb, ub, verbose=self.verbose,
                            solver=self.solver, solver_params=self.solver_params)
        self.alpha_ = alpha

        # Identify support “vectors” (bags)
        sv_mask = alpha > self.tol
        self.support_ = np.flatnonzero(sv_mask).astype(int)
        self.support_vectors_ = [bag_list[i]
                                 # store the Bag objects
                                 for i in self.support_]
        self.dual_coef_ = (alpha[sv_mask] * Y[sv_mask]).reshape(1, -1)

        # Intercept from margin SVs (0 < α_i < C_eff)
        on_margin = (alpha > self.tol) & (alpha < C_eff - self.tol)
        if not np.any(on_margin):
            on_margin = sv_mask
        b_vals = Y[on_margin] - (alpha * Y) @ K[:, on_margin]
        self.intercept_ = float(np.mean(b_vals)) if b_vals.size else 0.0

        # Linearization (recover w and recompute b from primal if possible)
        if self._can_linearize(bk):
            Z = np.stack(
                [self._phi(b, normalizer=bk.normalizer) for b in bag_list],
                axis=0
            )  # (n_bags, d)

            w = (self.alpha_ * self.y_) @ Z
            self._train_embeddings_ = Z
            self.coef_ = w

            # Recompute b using margin SVs (or all SVs if none on-margin)
            on_margin = (self.alpha_ > self.tol) & (
                self.alpha_ < C_eff - self.tol)
            use = on_margin if np.any(on_margin) else (self.alpha_ > self.tol)
            if np.any(use):
                b_vals = self.y_[use] - Z[use] @ w
                self.intercept_ = float(np.mean(b_vals))
        else:
            self.coef_ = None

        self.X_ = None
        return self

    def _phi(self, bag: Bag, *, normalizer: str) -> np.ndarray:
        """
        Bag embedding φ(B) in ℝ^d matching the bag kernel:
          - weights: uniform
          - normalizer:
              "none"         -> φ = mean
              "average"      -> φ = mean / count   (count = n or sum(mask))
              "featurespace" -> φ = mean / ||mean|| (for Linear instance kernel)
        """
        n, X = bag.n, bag.X
        if n == 0:
            # d from any train bag
            return np.zeros((self.support_vectors_[0].d,), dtype=float)

        w = np.full(n, 1.0 / n, dtype=float)

        mean = (w[None, :] @ X).ravel()        # (d,)

        if normalizer == "none":
            return mean
        elif normalizer == "average":
            count = float(bag.n)
            return mean / max(count, 1e-12)
        elif normalizer == "featurespace":
            # For Linear instance kernel, FS-norm == ||mean||
            denom = float(np.linalg.norm(mean))
            return mean / max(denom, 1e-12)
        else:
            return mean  # fallback (shouldn't happen)

    def decision_function(self, bags) -> npt.NDArray[np.float64]:
        '''Compute the decision function for the given bags.'''
        if self.bags_ is None or self.alpha_ is None or self.y_ is None or self.intercept_ is None:
            raise RuntimeError("Model is not fitted yet.")

        # Coerce to list of Bag
        if isinstance(bags, BagDataset):
            test_bags = list(bags.bags)
        elif len(bags) > 0 and isinstance(bags[0], Bag):  # type: ignore[index]
            test_bags = list(bags)  # type: ignore[assignment]
        else:
            test_bags = [Bag(X=np.asarray(b, dtype=float), y=0.0)
                         for b in bags]

        bk = self._ensure_bag_kernel()

        # ---- if the coef_ exists (then fallback here)
        if self.coef_ is not None and self._can_linearize(bk):
            Zt = np.stack(
                [self._phi(b, normalizer=bk.normalizer) for b in test_bags],
                axis=0
            )
            return (Zt @ self.coef_ + self.intercept_).ravel()

        # fallback: kernel path
        Ktest = bk(self.bags_, test_bags)  # (n_train, n_test)
        return ((self.alpha_ * self.y_) @ Ktest + self.intercept_).ravel()

    def predict(self, bags: Sequence[Bag] | BagDataset | Sequence[np.ndarray]) -> npt.NDArray[np.float64]:
        """
        Predict the labels for the given bags.
        """
        scores = self.decision_function(bags)
        return (scores >= 0.0).astype(float)

    def score(self, bags, y_true) -> float:
        """
        Compute the accuracy of the model on the given bags.
        """
        y_pred = self.predict(bags)
        y_true = np.asarray(y_true, dtype=float).ravel()
        return float((y_pred == y_true).mean())
