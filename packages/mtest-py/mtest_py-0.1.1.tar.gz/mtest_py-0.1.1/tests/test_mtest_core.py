import numpy as np
import pandas as pd
import pytest
from mtest import mtest

def test_mtest_smoke_and_shapes():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 4))
    beta = np.array([1.0, 0.5, 0.0, 0.0])
    y = X @ beta + rng.normal(size=200, scale=1.0)

    res = mtest(X, y, n_boot=128, r2_threshold=0.9, seed=123, add_intercept=True)
    assert "R2_global" in res and np.isfinite(res["R2_global"])
    assert res["B_R2_global"].shape == (128,)
    assert res["B_R2_aux"].shape == (128, 4)
    assert len(res["VIF"]) == 4
    assert set(res["p_vif"]).issuperset({"x1", "x2", "x3", "x4"})

def test_mtest_dataframe_names_propagated():
    rng = np.random.default_rng(1)
    X = pd.DataFrame(rng.normal(size=(150, 3)), columns=["a", "b", "c"])
    y = (X["a"] * 0.8 + rng.normal(size=150)).to_numpy()

    res = mtest(X, y, n_boot=64, seed=7)
    # Debe usar nombres reales
    for k in ["VIF_named", "p_vif", "p_klein"]:
        assert set(res[k].keys()) == {"a", "b", "c"}

def test_mtest_add_intercept_toggle_consistency():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(120, 2))
    y = X[:, 0] - 0.5 * X[:, 1] + rng.normal(size=120, scale=0.5)

    # Caso A: agregando intercepto dentro de mtest
    res_A = mtest(X, y, n_boot=50, seed=3, add_intercept=True)

    # Caso B: sin intercepto interno, pero agregándolo manualmente a X
    X_manual = np.c_[np.ones((X.shape[0], 1)), X]
    # mtest asume add_intercept=False si ya lo agregaste
    # para probar coherencia, hacemos una llamada equivalente:
    from mtest.mtest import _r2_fit  # sólo para comparar R2_global (prueba interna)
    R2_A = res_A["R2_global"]
    R2_B = _r2_fit(X_manual, y)
    assert np.isfinite(R2_A) and np.isfinite(R2_B)
    assert abs(R2_A - R2_B) < 1e-9

def test_mtest_nsam_subsampling_effect():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(300, 3))
    y = X @ np.array([1.0, 0.0, 0.0]) + rng.normal(size=300)

    res_full = mtest(X, y, n_boot=40, nsam=300, seed=5)
    res_half = mtest(X, y, n_boot=40, nsam=150, seed=5)
    # No deben ser idénticos porque el bootstrap muestrea distinto tamaño
    assert not np.allclose(res_full["B_R2_global"], res_half["B_R2_global"])
