from __future__ import annotations
import pandas as pd

def mtest_summary(
    res: dict,
    sort_by: str = "VIF",         # "VIF", "p_VIF_rule", "p_Klein_rule"
    ascending: bool = False,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Build a tabular summary of MTest results.
    
    Parameters
    ----------
    res : dict
        Output of mtest(...). Must contain the keys: "VIF_named", "p_vif", "p_klein".
    sort_by : {"VIF", "p_VIF_rule", "p_Klein_rule"}
        Column to use for sorting the summary.
    ascending : bool
        Sort order (ascending or descending).
    alpha : float
        Threshold to flag significance (p < alpha).
    
    Returns
    -------
    pandas.DataFrame
        Index: predictor. Columns:
        - ``VIF``
        - ``p_VIF_rule`` (ASL for VIF rule)
        - ``p_Klein_rule`` (ASL for Klein rule)
        - ``flag_VIF_rule`` (True if ``p_VIF_rule < alpha``)
        - ``flag_Klein_rule`` (True if ``p_Klein_rule < alpha``)
        - ``flag_any`` (True if any rule flags the predictor)
    """
    # Validaciones mínimas
    for k in ("VIF_named", "p_vif", "p_klein"):
        if k not in res:
            raise ValueError(f"Resultado MTest incompleto: falta clave '{k}'")

    rows = []
    # Recorre por nombres (usa intersección por seguridad)
    preds = sorted(set(res["VIF_named"].keys()) & set(res["p_vif"].keys()) & set(res["p_klein"].keys()))
    for pred in preds:
        vif = float(res["VIF_named"][pred])
        pv  = float(res["p_vif"][pred])
        pk  = float(res["p_klein"][pred])
        rows.append({
            "predictor": pred,
            "VIF": vif,
            "p_VIF_rule": pv,
            "p_Klein_rule": pk,
        })

    df = pd.DataFrame(rows).set_index("predictor")
    df["flag_VIF_rule"]   = df["p_VIF_rule"]   < alpha
    df["flag_Klein_rule"] = df["p_Klein_rule"] < alpha
    df["flag_any"]        = df["flag_VIF_rule"] | df["flag_Klein_rule"]

    # Orden
    if sort_by not in df.columns:
        raise ValueError(f"sort_by invalid: '{sort_by}'. Use 'VIF', 'p_VIF_rule' or 'p_Klein_rule'.")
    df = df.sort_values(sort_by, ascending=ascending)
    return df
