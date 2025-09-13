# mtest: a nonparametric bootstrap to assess multicollinearity via two rules:

- **Klein's rule**: compares global R² vs auxiliary R² for each predictor.
- **VIF rule**: flags when the auxiliary R² of a predictor exceeds a threshold.

## Install (local)

```bash
pip install -e .
```

## Quickstart

```python
import numpy as np
from mtest import mtest

rng = np.random.default_rng(0)
n, p = 500, 4
X = rng.normal(size=(n, p))
beta = np.array([1, 0.5, 0.0, 0.0])
y = X @ beta + rng.normal(scale=1.0, size=n)

res = mtest(X, y, n_boot=500, r2_threshold=0.9, seed=2025)
print(res["p_vif"])      # dict per predictor
print(res["p_klein"])    # dict per predictor
```

## API

```python
mtest(X, y, n_boot=1000, nsam=None, r2_threshold=0.9, seed=None, return_distributions=True)
```
- `X`: array-like `(n, p)` predictors. Intercept is **not** added automatically.
- `y`: array-like `(n,)` response.
- `n_boot`: bootstrap replicates.
- `nsam`: bootstrap sample size (default: `n`).
- `r2_threshold`: threshold **on auxiliary R²** used for VIF rule.
- `seed`: RNG seed.
- `return_distributions`: if `True`, returns bootstrap arrays.

**Return**: dict with keys
- `R2_global`, `R2_aux` (original sample),
- `VIF` (original sample),
- `B_R2_global` `(n_boot,)`,
- `B_R2_aux` `(n_boot, p)`, columns aligned with predictors,
- `p_vif` (dict), `p_klein` (dict).

## Notes

- For the VIF rule we use `Pr(R²_j > r2_threshold)` — pass `r2_threshold` accordingly.
- Klein's rule p-value is `Pr(R²_global < R²_j)` across bootstrap replicates.
- Numerical stability: we use least squares and guard divisions-by-zero.

MIT License.
