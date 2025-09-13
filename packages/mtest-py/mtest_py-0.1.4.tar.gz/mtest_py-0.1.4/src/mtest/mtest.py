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
    Bootstrap-based test for multicollinearity (Klein and VIF).

    This function implements a nonparametric *pairs bootstrap* to assess
    multicollinearity by computing achieved significance levels (ASL) for two
    classic diagnostics:
    (i) Klein's rule and (ii) the VIF rule. For each bootstrap sample it
    recomputes the global R^2 and the auxiliary R_j^2 (regressing each
    predictor X_j on X_{-j}), and derives p-values as tail probabilities over
    the bootstrap distribution.

    Parameters
    ----------
    X : array-like or pandas.DataFrame, shape (n, p)
        Predictor matrix. If ``add_intercept=True`` (default), a leading column
        of ones is appended. If a DataFrame is provided, its column names are
        propagated to the named outputs.
    y : array-like, shape (n,)
        Response vector.
    n_boot : int, default=100
        Number of bootstrap iterations (rows resampled with replacement).
        Corresponds to ``nboot`` in the R function.
    nsam : int or None, default=None
        Bootstrap sample size per iteration. Defaults to the original row count.
        Corresponds to ``nsam`` in R.
    r2_threshold : float, default=0.90
        Threshold ``c`` applied to the auxiliary R_j^2 for the VIF rule.
        We estimate ASL as ``P(R_j^2 > c)``. Since ``VIF_j = 1/(1 - R_j^2)``,
        the implied VIF threshold is ``VIF >= 1/(1 - c)`` (e.g. ``c=0.90`` → VIF≈10).
        Corresponds to ``valor_vif`` in R.
    seed : int or None, default=None
        RNG seed for reproducibility. Matches ``seed`` in R.
    return_distributions : bool, default=True
        If True, include bootstrap arrays in the result (global and auxiliary R^2).
    add_intercept : bool, default=True
        If True, append an intercept column to ``X`` (mimics R's ``model.matrix``
        default). Set to False if your ``X`` already contains an intercept.

    Returns
    -------
    dict
        A dictionary with:
        - ``R2_global`` : float
            Observed global R^2.
        - ``R2_aux`` : ndarray, shape (p,)
            Observed auxiliary R_j^2 for each predictor.
        - ``VIF`` : ndarray, shape (p,)
            Observed VIF per predictor, computed as ``1/(1 - R_j^2)``.
        - ``VIF_named`` : dict[str, float]
            VIF keyed by predictor name (DataFrame columns if available).
        - ``p_vif`` : dict[str, float]
            ASL for the VIF rule, ``P(R_j^2 > r2_threshold)``.
        - ``p_klein`` : dict[str, float]
            ASL for Klein's rule, ``P(R_g^2 < R_j^2)``.
        - ``B_R2_global`` : ndarray, shape (n_boot,), optional
            Bootstrap global R^2 (included if ``return_distributions=True``).
        - ``B_R2_aux`` : ndarray, shape (n_boot, p), optional
            Bootstrap auxiliary R_j^2 (included if ``return_distributions=True``).
        - ``n_boot`` : int
            Effective number of bootstrap iterations.
        - ``nsam`` : int
            Effective bootstrap sample size.

    Notes
    -----
    • **Bootstrap scheme**: resampling is done on *pairs* (rows of ``[X, y]``),
      recomputing global and auxiliary R^2 under a fixed design shape that matches
      the provided ``X`` (plus optional intercept).

    • **Design expansion**: unlike R, Python does not expand formulas; if you need
      transformed terms (e.g., interactions, polynomials, factors) pass an ``X``
      that already contains those columns.

    • **Mapping to R**:
      - R's ``MTest(object, nboot, nsam, seed, valor_vif)`` →
        Python's ``mtest(X, y, n_boot, nsam, seed, r2_threshold)``.
      - ``valor_vif`` ↔ ``r2_threshold`` with implied VIF cut at ``1/(1-c)``.

    Interpretation
    --------------
    • Larger ``p_klein[j]`` ⇒ stronger evidence that predictor ``j`` violates
      Klein's rule (``R_j^2`` often exceeds ``R_g^2``).

    • Larger ``p_vif[j]`` ⇒ ``R_j^2`` frequently exceeds ``r2_threshold``
      (equivalently, VIF exceeds the implied threshold).

    References
    ----------
    Morales-Oñate, V., & Morales-Oñate, B. (2023). *MTest: a Bootstrap Test for
    Multicollinearity*, Revista Politécnica, 51(2), 53–62. doi:10.33333/rp.vol51n2.05

    See Also
    --------
    mtest_summary : Tabular summary with flags for VIF and Klein rules.

    Examples
    --------
    >>> import pandas as pd
    >>> from mtest import mtest, mtest_summary
    >>> mtcars = pd.read_csv("https://raw.githubusercontent.com/selva86/datasets/master/mtcars.csv", index_col=0)
    >>> X = mtcars[["disp", "hp", "wt", "qsec"]]
    >>> y = mtcars["mpg"].to_numpy()
    >>> res = mtest(X, y, n_boot=200, seed=123, r2_threshold=0.90)
    >>> mtest_summary(res).head()
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
        names = [str(c) for c in col_names[:n_pred]]
    else:
        names = [f"x{j}" for j in range(1, n_pred + 1)]

    p_vif = {nm: float(p_vif_vals[j]) for j, nm in enumerate(names)}
    p_klein = {nm: float(p_klein_vals[j]) for j, nm in enumerate(names)}
    VIF_named = {nm: float(VIF[j]) for j, nm in enumerate(names)}

    out = {
        "R2_global": float(R2_global),
        "R2_aux": R2_aux,
        "VIF": VIF,
        "VIF_named": VIF_named,
        "p_vif": p_vif,
        "p_klein": p_klein,
    }
    if return_distributions:
        out["B_R2_global"] = B_R2_global
        out["B_R2_aux"] = B_R2_aux
    return out
