# src/mtest/ks.py
from __future__ import annotations
import numpy as np
import pandas as pd
from itertools import combinations
from typing import Literal, Dict, Any
from scipy.stats import ks_2samp

# Texto estilo R para la alternativa
_ALT_TEXT = {
    "two-sided": "two-sided (distributions differ)",
    "less":      "alternative hypothesis: the CDF of x lies below that of y.",
    "greater":   "alternative hypothesis: the CDF of x lies above that of y.",
}

def _names_from_X(X) -> list[str]:
    if hasattr(X, "columns"):
        return [str(c) for c in X.columns]
    return [f"x{j+1}" for j in range(np.asarray(X).shape[1])]

def pairwise_ks_test(
    X,
    alternative: Literal["two-sided", "less", "greater"] = "two-sided",
) -> Dict[str, Any]:
    """
    Compute pairwise Kolmogorov–Smirnov tests for all predictor pairs.
    
    This function evaluates every ordered pair (x, y) of columns in X using
    `scipy.stats.ks_2samp(x, y, alternative=...)` and returns both a tidy
    long-form table and a square p-value matrix (rows = x, cols = y).
    
    Parameters
    ----------
    X : array-like or pandas.DataFrame, shape (n, p)
        Predictor matrix. If a DataFrame is provided, column names are
        propagated to the outputs.
    alternative : {"two-sided", "less", "greater"}, default="two-sided"
        Hypothesis as in R and SciPy:
          - "greater": the CDF of x lies above that of y.
          - "less"   : the CDF of x lies below that of y.
          - "two-sided": the distributions differ.
    
    Returns
    -------
    dict
        Dictionary with:
        - "tidy" : pandas.DataFrame
            Long-form results with columns:
            ["var1", "var2", "ks_stat", "p_value", "alternative"] for both
            directions (x vs y, y vs x).
        - "p_matrix" : pandas.DataFrame
            Square matrix of p-values with rows = x and cols = y; the diagonal is 1.0.
        - "alternative" : str
            Echo of the selected alternative.
        - "n_columns" : int
            Number of columns p in X.
        - "names" : list[str]
            Column names used for labeling outputs.
    
    Notes
    -----
    - The matrix is directional: p(x, y) is computed separately from p(y, x).
    - When X is a NumPy array, generic names "x1", "x2", ... are used.
    
    Examples
    --------
    >>> import pandas as pd
    >>> from mtest import pairwise_ks_test
    >>> X = pd.DataFrame({"a":[1,2,3], "b":[1,1,5], "c":[9,9,9]})
    >>> ks_res = pairwise_ks_test(X, alternative="greater")
    >>> ks_res["p_matrix"].shape
    (3, 3)
    """
    names = _names_from_X(X)
    X = np.asarray(X, float)
    p = X.shape[1]

    rows = []
    mat = pd.DataFrame(np.ones((p, p), float), index=names, columns=names)

    for i, j in combinations(range(p), 2):
        # x (fila=i) vs y (col=j)
        stat_ij, pval_ij = ks_2samp(X[:, i], X[:, j], alternative=alternative)
        rows.append({
            "var1": names[i], "var2": names[j],
            "ks_stat": float(stat_ij), "p_value": float(pval_ij),
            "alternative": alternative
        })
        mat.loc[names[i], names[j]] = float(pval_ij)

        # y (fila=j) vs x (col=i)
        stat_ji, pval_ji = ks_2samp(X[:, j], X[:, i], alternative=alternative)
        rows.append({
            "var1": names[j], "var2": names[i],
            "ks_stat": float(stat_ji), "p_value": float(pval_ji),
            "alternative": alternative
        })
        mat.loc[names[j], names[i]] = float(pval_ji)

    np.fill_diagonal(mat.values, 1.0)
    tidy = pd.DataFrame(rows).sort_values(["var1", "var2"]).reset_index(drop=True)

    return {
        "tidy": tidy,
        "p_matrix": mat,
        "alternative": alternative,
        "n_columns": p,
        "names": names,
    }




def ks_summary(
    ks_res: Dict[str, Any],
    digits: int = 4,
) -> Dict[str, Any]:
    """
    Pairwise Kolmogorov–Smirnov tests between all columns of X.

    Computes K–S tests for every ordered pair (x, y) of columns. For
    one-sided alternatives the test is directional; for ``two-sided`` it is
    symmetric.

    Parameters
    ----------
    X : pandas.DataFrame or array-like, shape (n, p)
        Data matrix whose columns will be compared pairwise.
        Column names are used in outputs when available.
    alternative : {"two-sided", "less", "greater"}, default="two-sided"
        The alternative hypothesis passed to SciPy's ``ks_2samp``:
        - ``less``   : CDF(x) below CDF(y).
        - ``greater``: CDF(x) above CDF(y).
        - ``two-sided``: two-sided difference.

    Returns
    -------
    dict
        - ``tidy`` : DataFrame with columns (``x``, ``y``, ``ks_stat``, ``p_value``).
        - ``p_matrix`` : DataFrame p-value matrix (rows=x, cols=y; diagonal=1).
        - ``alternative`` : str
        - ``n_columns`` : int
        - ``names`` : list[str]

    Notes
    -----
    • ``two-sided`` ⇒ ``p(x, y) == p(y, x)`` (symmetric).
    • ``less``/``greater`` ⇒ directional p-values (generally ``p(x,y) != p(y,x)``).
    
    References
    ----------
    Morales-Oñate, V., & Morales-Oñate, B. (2023). *MTest: a Bootstrap Test for
    Multicollinearity*, Revista Politécnica, 51(2), 53–62. doi:10.33333/rp.vol51n2.05

    See Also
    --------
    ks_summary : Pretty, R-like text summary with Suggestion and minima by row.

    Examples
    --------
    >>> import pandas as pd
    >>> from mtest import pairwise_ks_test, ks_summary
    >>> X = pd.read_csv("https://raw.githubusercontent.com/selva86/datasets/master/mtcars.csv", index_col=0)[["disp","hp","wt","qsec"]]
    >>> res = pairwise_ks_test(X, alternative="less")
    >>> print(ks_summary(res)["summary_text"])
    """

    mat: pd.DataFrame = ks_res["p_matrix"].copy()
    alt: str = ks_res["alternative"]
    p = mat.shape[1]

    # Row-wise minima (excluye diagonal)
    rw_rows = []
    for rname in mat.index:
        row_no_diag = mat.loc[rname].drop(index=rname)
        y_name = row_no_diag.idxmin()
        p_min = float(row_no_diag.min())
        rw_rows.append({"x": rname, "y": y_name, "p": p_min})
    rowwise_minima = pd.DataFrame(rw_rows)

    # Texto de alternativa estilo R
    _ALT_TEXT = {
        "two-sided": "alternative hypothesis: two-sided",
        "less":      "alternative hypothesis: the CDF of x lies below that of y. Rows are x and Columns are y",
        "greater":   "alternative hypothesis: the CDF of x lies above that of y. Rows are x and Columns are y",
    }
    alt_text = _ALT_TEXT.get(alt, alt)

    # --- Suggestion según alternativa (igual a R) ---
    # less    -> colSums(P)
    # greater -> rowSums(P)
    # two-sided -> "No suggestions"
    if alt == "less":
        suggestion = mat.sum(axis=0)        # columnas
    elif alt == "greater":
        suggestion = mat.sum(axis=1)        # filas
    else:
        suggestion = None

    # Armado del texto (sin FutureWarning en formateo)
    header = []
    header.append("=" * 60)
    header.append("pairwiseKStest summary")
    header.append("-" * 60)
    header.append(f"Columns compared     : {p}")
    header.append(f"Alternative (as text): {alt_text}")
    header.append("Note: rows are 'x' and columns are 'y' in ks.test(x, y).")
    header.append("-" * 60)
    header.append("P-value matrix (rows = x, cols = y):")

    mat_fmt = mat.copy().apply(lambda s: s.map(lambda v: f"{v:.{digits}g}"))
    col_line = "     " + "  ".join(f"{c:>8s}" for c in mat_fmt.columns)
    header.append(col_line)
    for idx, row in mat_fmt.iterrows():
        header.append(f"{idx:<5s} " + "  ".join(f"{val:>8s}" for val in row.values))
    header.append("-" * 60)

    header.append("Suggestion:")
    if suggestion is None:
        header.append("No suggestions")
    else:
        sugg_sorted = suggestion.sort_values(ascending=False)  # descendente
        sugg_line = " ".join(f"{k} = {v:.3f}" for k, v in sugg_sorted.items())
        header.append(sugg_line)
    header.append("-" * 60)

    header.append("Row-wise minima (for each x, the y with smallest p):")
    header.append("    x        y            p")
    for _, r in rowwise_minima.iterrows():
        header.append(f"{r['x']:<8s}{r['y']:<10s}{r['p']:.{digits}g}")
    header.append("=" * 60)

    summary_text = "\n".join(header)

    return {
        "summary_text": summary_text,
        "p_matrix": mat,
        "suggestion": suggestion,       # Series o None
        "rowwise_minima": rowwise_minima,
    }
