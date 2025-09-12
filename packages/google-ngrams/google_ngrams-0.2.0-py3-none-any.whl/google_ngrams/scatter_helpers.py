from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class SmoothResult:
    x: np.ndarray
    y_fit: np.ndarray
    y_lower: Optional[np.ndarray]
    y_upper: Optional[np.ndarray]


def _df_from_ui(n: int, smoothing: int) -> int:
    """Map UI smoothing (1..9) to an effective df like original code.

    Original mapping: df = (10 - smoothing) * 10.
    Clamp to a feasible range given the sample size and cubic degree.
    """
    s_param = int(smoothing)
    if s_param < 1:
        s_param = 1
    elif s_param > 9:
        s_param = 9
    df = (10 - s_param) * 10  # 1->90 (flexible), 9->10 (smooth)
    # For cubic regression spline, basis dimension = 4 + t (t=interior knots).
    max_t = max(0, n - 5)
    max_df = max_t + 4
    df = max(6, min(df, max_df))
    return df


def _crs_design(x: np.ndarray, knots: np.ndarray) -> np.ndarray:
    """Cubic regression spline design matrix using truncated power basis.

    Columns: [1, x, x^2, x^3, (x - t1)_+^3, ..., (x - tm)_+^3]
    Where (a)_+ = max(a, 0).
    """
    x = np.asarray(x, dtype=float)
    X = [
        np.ones_like(x),
        x,
        x * x,
        x * x * x,
    ]
    for t in knots:
        z = x - float(t)
        z[z < 0.0] = 0.0
        X.append(z * z * z)
    return np.column_stack(X)


def _fit_ridge(X: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    """Solve ridge regression (X^T X + lam I) beta = X^T y."""
    XtX = X.T @ X
    n_feat = XtX.shape[0]
    A = XtX + lam * np.eye(n_feat)
    Xty = X.T @ y
    try:
        beta = np.linalg.solve(A, Xty)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(A, Xty, rcond=None)[0]
    return beta


def gam_smoother(
    x: np.ndarray,
    y: np.ndarray,
    *,
    smoothing: int = 7,
    ci: bool = True,
    ci_level: float = 0.95,
    n_boot: int = 200,
    random_state: Optional[int] = None,
) -> SmoothResult:
    """Cubic regression spline (NumPy only) with optional bootstrap CIs.

    Uses a truncated power basis with interior knots chosen at quantiles and
    ridge regularization mapped from the UI smoothing parameter. Returns
    predictions at the original x order and clips negatives to zero.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("x and y must be 1D arrays of the same length")

    order = np.argsort(x)
    x_sorted = x[order]
    y_sorted = y[order]

    # Handle duplicate x by adding tiny jitter
    dx = np.diff(x_sorted)
    if np.any(dx == 0):
        eps = 1e-9 * max(1.0, (x_sorted.max() - x_sorted.min()))
        counts = {}
        x_use = x_sorted.copy()
        for i, val in enumerate(x_sorted):
            c = counts.get(val, 0)
            if c > 0:
                x_use[i] = val + c * eps
            counts[val] = c + 1
    else:
        x_use = x_sorted

    # Normalize x to [0,1] for numerical stability
    xmin = float(x_use.min())
    xmax = float(x_use.max())
    span = xmax - xmin
    if span <= 0:
        span = 1.0
    x0 = (x_use - xmin) / span

    # Determine number of interior knots from df mapping
    n = len(x0)
    df = _df_from_ui(n, smoothing)
    k = 3  # cubic
    t_count = max(0, min(df - (k + 1), n - (k + 2)))
    if t_count > 0:
        qs = np.linspace(0, 1, t_count + 2)[1:-1]
        knots = np.quantile(x0, qs)
    else:
        knots = np.array([], dtype=float)

    # Build design
    X = _crs_design(x0, knots)
    # Standardize columns except intercept for stable ridge behavior
    Xs = X.copy()
    means = np.zeros(X.shape[1])
    scales = np.ones(X.shape[1])
    # skip intercept at col 0
    for j in range(1, X.shape[1]):
        col = X[:, j]
        m = float(np.mean(col))
        s = float(np.std(col))
        if s <= 0.0:
            s = 1.0
        means[j] = m
        scales[j] = s
        Xs[:, j] = (col - m) / s

    # Map smoothing (1..9) -> ridge lambda on a small scale
    # smoothing=1 -> ~1e-9 (very flexible), smoothing=9 -> ~1e-4 (smoother)
    s_param = int(np.clip(smoothing, 1, 9))
    exp_min, exp_max = -9.0, -4.0
    exponent = exp_min + (s_param - 1) * (exp_max - exp_min) / 8.0
    lam = 10.0 ** exponent

    beta = _fit_ridge(Xs, y_sorted, lam)
    y_fit_sorted = Xs @ beta

    inv = np.argsort(order)
    y_fit = np.asarray(y_fit_sorted[inv], dtype=float)
    y_fit[y_fit < 0] = 0.0

    y_lower = None
    y_upper = None
    if ci:
        rng = np.random.default_rng(random_state)
        alpha = 1.0 - float(ci_level)
        hi_q = 100.0 * (1.0 - alpha / 2.0)
        resid_sorted = y_sorted - y_fit_sorted
        boot_preds = np.empty((n_boot, len(x0)), dtype=float)
        for b in range(n_boot):
            resampled = rng.choice(
                resid_sorted, size=len(resid_sorted), replace=True
            )
            y_b = y_fit_sorted + resampled
            # Refit with the same design and penalty
            beta_b = _fit_ridge(Xs, y_b, lam)
            boot_preds[b, :] = Xs @ beta_b
        # Symmetric, fit-centered half-width from absolute deviations
        hw_sorted = np.percentile(
            np.abs(boot_preds - y_fit_sorted), hi_q, axis=0
        )
        y_lower_sorted = y_fit_sorted - hw_sorted
        y_upper_sorted = y_fit_sorted + hw_sorted
        # Map back to original x order
        y_lower = y_lower_sorted[inv]
        y_upper = y_upper_sorted[inv]
        # Clip to non-negative domain
        y_lower[y_lower < 0] = 0.0
        y_upper[y_upper < 0] = 0.0

    return SmoothResult(x=x, y_fit=y_fit, y_lower=y_lower, y_upper=y_upper)
