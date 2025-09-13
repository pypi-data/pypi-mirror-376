from __future__ import annotations
import numpy as np
from typing import Optional, Dict, Any

def _add_intercept(X: np.ndarray) -> np.ndarray:
    ones = np.ones((X.shape[0], 1), dtype=float)
    return np.concatenate([ones, X], axis=1)

def _r2_fit(X: np.ndarray, y: np.ndarray) -> float:
    """
    R^2 from linear regression of y on columns of X (no intercept added here).
    Returns NaN if TSS == 0.
    """
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    rss = float(resid.T @ resid)
    y_mean = float(np.mean(y))
    tss = float(((y - y_mean) ** 2).sum())
    if not np.isfinite(rss) or tss <= 0:
        return np.nan
    return 1.0 - rss / tss

def _r2_aux_j(X_full: np.ndarray, j: int) -> float:
    """
    Auxiliary R^2 for predictor j (excluding the intercept column 0).
    We regress column j on all other columns (including intercept).
    """
    n, p = X_full.shape
    if p <= 2:  # intercept + one predictor -> no aux regression
        return np.nan
    mask = np.ones(p, dtype=bool)
    mask[j] = False
    Z = X_full[:, mask]
    xj = X_full[:, j]
    beta, *_ = np.linalg.lstsq(Z, xj, rcond=None)
    resid = xj - Z @ beta
    rss = float(resid.T @ resid)
    xj_mean = float(np.mean(xj))
    tss = float(((xj - xj_mean) ** 2).sum())
    if not np.isfinite(rss) or tss <= 0:
        return np.nan
    return 1.0 - rss / tss


def mtest(
    X,
    y,
    n_boot: int = 1000,
    nsam: Optional[int] = None,
    r2_threshold: float = 0.9,
    seed: Optional[int] = None,
    return_distributions: bool = True,
    add_intercept: bool = True,
) -> Dict[str, Any]:
    """
    Pure NumPy port of the MTest bootstrap for multicollinearity.

    Parameters
    ----------
    X : array-like or pandas.DataFrame, shape (n, p)
        Predictor matrix. If `add_intercept=True` (default), a leading column of ones is added.
        If a DataFrame is provided, column names are propagated to outputs.
    y : array-like, shape (n,)
        Response vector.
    n_boot : int
        Number of bootstrap replicates.
    nsam : int or None
        Sample size per bootstrap replicate (default: n).
    r2_threshold : float
        Threshold on auxiliary R^2 for the VIF rule (Pr(R^2_j > r2_threshold)).
    seed : int or None
        Random seed for reproducibility.
    return_distributions : bool
        If True, include bootstrap arrays in the result.
    add_intercept : bool
        If True, add a column of ones as intercept to X (aligns with R::model.matrix default).

    Returns
    -------
    dict
        Keys: "R2_global", "R2_aux", "VIF", "VIF_named", "p_vif", "p_klein",
              and optionally "B_R2_global", "B_R2_aux".
        When X is a DataFrame, p-value dicts and VIF_named use its column names.
    """
    # --- Detectar nombres de columnas si X es DataFrame ---
    col_names = None
    try:
        import pandas as pd  # noqa: F401
        if hasattr(X, "columns"):
            col_names = [str(c) for c in X.columns]
            X = np.asarray(X, dtype=float)
        else:
            X = np.asarray(X, dtype=float)
    except Exception:
        X = np.asarray(X, dtype=float)

    y = np.asarray(y, dtype=float).reshape(-1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0]:
        raise ValueError("Shapes must be X:(n,p), y:(n,) with same n.")
    n, p_no_int = X.shape
    if nsam is None:
        nsam = n
    if nsam <= 0:
        raise ValueError("nsam must be positive.")
    rng = np.random.default_rng(seed)

    # Add intercept if requested
    X_full = _add_intercept(X) if add_intercept else X
    n, p_full = X_full.shape  # p_full = 1 + p_no_int if add_intercept else p_no_int

    # --- Métricas muestra original ---
    R2_global = _r2_fit(X_full, y)
    # R^2 auxiliares para predictores (excluye intercepto -> j = 1..p_full-1)
    R2_aux = np.array([_r2_aux_j(X_full, j) for j in range(1, p_full)], dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        VIF = 1.0 / (1.0 - R2_aux)
    VIF[~np.isfinite(VIF)] = np.nan

    # --- Bootstrap ---
    B_R2_global = np.full((n_boot,), np.nan, dtype=float)
    B_R2_aux = np.full((n_boot, p_full - 1), np.nan, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=nsam)
        Xb = X_full[idx, :]
        yb = y[idx]
        B_R2_global[b] = _r2_fit(Xb, yb)
        for j in range(1, p_full):
            B_R2_aux[b, j - 1] = _r2_aux_j(Xb, j)

    # --- p-values ---
    with np.errstate(invalid="ignore"):
        p_vif_vals = np.nanmean(B_R2_aux > r2_threshold, axis=0)
    g = B_R2_global.reshape(-1, 1)
    with np.errstate(invalid="ignore"):
        p_klein_vals = np.nanmean(g < B_R2_aux, axis=0)

    # --- Nombres amigables (robusto) ---
    # Número de predictores SIN intercepto (independiente de add_intercept)
    n_pred = p_no_int

    if col_names is not None:
        # Usa exactamente los nombres de las columnas de X (sin intercepto)
        names = [str(c) for c in col_names[:n_pred]]
    else:
        # Fallback para ndarray
        names = [f"x{j}" for j in range(1, n_pred + 1)]

    p_vif = {nm: float(p_vif_vals[j]) for j, nm in enumerate(names)}
    p_klein = {nm: float(p_klein_vals[j]) for j, nm in enumerate(names)}
    VIF_named = {nm: float(VIF[j]) for j, nm in enumerate(names)}

    out = {
        "R2_global": float(R2_global),
        "R2_aux": R2_aux,
        "VIF": VIF,              # array (se mantiene por compatibilidad)
        "VIF_named": VIF_named,  # nuevo: dict con nombres reales
        "p_vif": p_vif,          # dict con nombres
        "p_klein": p_klein,      # dict con nombres
    }
    if return_distributions:
        out["B_R2_global"] = B_R2_global
        out["B_R2_aux"] = B_R2_aux
    return out
