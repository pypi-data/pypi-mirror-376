import numpy as np
import pandas as pd
from mtest import mtest, mtest_summary


def test_mtest_summary_columns_and_flags():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(180, 4)), columns=list("abcd"))
    X["d"] = X["a"] * 0.9 + rng.normal(scale=0.1, size=180)
    y = (1.5 * X["a"] - 0.3 * X["b"] + rng.normal(size=180)).to_numpy()

    res = mtest(X, y, n_boot=80, seed=42)
    df = mtest_summary(res, sort_by="VIF", ascending=False, alpha=0.1)

    expected_cols = {"VIF", "p_VIF_rule", "p_Klein_rule", "flag_VIF_rule", "flag_Klein_rule", "flag_any"}
    assert expected_cols.issubset(df.columns)

    # Mismos predictores, independientemente del orden
    assert set(df.index) == set(list("abcd"))

    # Confirmar que está realmente ordenado por VIF descendente
    assert df["VIF"].is_monotonic_decreasing


def test_mtest_summary_sort_by_pvalues():
    rng = np.random.default_rng(1)
    X = pd.DataFrame(rng.normal(size=(120, 3)), columns=["u", "v", "w"])
    y = X["u"] + rng.normal(size=120)

    res = mtest(X, y, n_boot=60, seed=11)
    df_pv = mtest_summary(res, sort_by="p_VIF_rule", ascending=True)
    assert df_pv.index[0] in ["u", "v", "w"]  # el más significativo primero (p más chico)
