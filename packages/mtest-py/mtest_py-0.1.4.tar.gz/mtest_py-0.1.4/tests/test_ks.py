import numpy as np
import pandas as pd
from mtest import pairwise_ks_test, ks_summary


def test_pairwise_ks_shapes_and_directionality():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({
        "x": rng.normal(size=100),
        "y": rng.normal(loc=1.0, size=100),
        "z": rng.normal(size=100),
    })

    # two-sided: p(x,y) == p(y,x)
    res_ts = pairwise_ks_test(X, alternative="two-sided")
    tidy = res_ts["tidy"]
    mat  = res_ts["p_matrix"]

    assert len(tidy) == 6
    assert mat.shape == (3, 3)
    assert np.allclose(np.diag(mat.values), 1.0)

    # Simetría en two-sided
    assert np.allclose(mat.loc["x", "y"], mat.loc["y", "x"])

    # one-sided (greater): típicamente p(x,y) != p(y,x)
    res_g = pairwise_ks_test(X, alternative="greater")
    mat_g = res_g["p_matrix"]
    assert not np.allclose(mat_g.loc["x", "y"], mat_g.loc["y", "x"])



def test_ks_summary_suggestion_logic_less_and_greater():
    # Construye data con diferencias claras
    rng = np.random.default_rng(1)
    A = rng.normal(loc=0.0, size=200)
    B = rng.normal(loc=1.0, size=200)
    C = rng.normal(loc=0.0, size=200)
    X = pd.DataFrame({"A": A, "B": B, "C": C})

    # alternative="less" -> Suggestion = colSums(P) descendente
    res_less = pairwise_ks_test(X, alternative="less")
    summ_less = ks_summary(res_less, digits=6)
    assert "Suggestion:" in summ_less["summary_text"]
    # Debe existir, no "No suggestions"
    assert summ_less["suggestion"] is not None

    # alternative="greater" -> Suggestion = rowSums(P) descendente
    res_great = pairwise_ks_test(X, alternative="greater")
    summ_great = ks_summary(res_great, digits=6)
    assert summ_great["suggestion"] is not None

def test_ks_summary_two_sided_no_suggestion():
    rng = np.random.default_rng(2)
    X = pd.DataFrame(rng.normal(size=(120, 4)), columns=list("abcd"))
    res = pairwise_ks_test(X, alternative="two-sided")
    summ = ks_summary(res)
    assert summ["suggestion"] is None
    assert "No suggestions" in summ["summary_text"]
