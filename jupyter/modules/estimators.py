"""
estimators.py — numpy ports of the Stata estimators used in analyze_data.ipynb.

Written because Stata was unavailable for the referee revisions. Every estimator here is
validated in referee_analysis.ipynb by reproducing the existing Stata outputs
(itt_coeffs.csv, lates_coeffs.csv, pds_coeffs.csv, pds_iv_coeffs.csv) before it is used for
anything new.

- ols_robust:  `reg y x, robust` (HC1)
- wls_robust:  `reg y x [pweight=w], robust` (HC1)
- logit_prob:  fitted probabilities from `logit y x` (Newton-Raphson MLE)
- iv_robust:   `ivregress 2sls y w (d = z), vce(robust)` (HC0)
- neyman / neyman_late: the paired difference-in-means programs
- rlasso / pds / pds_iv: rigorous (heteroskedastic) lasso and post-double-selection,
  following lassopack/pdslasso defaults (c = 1.1, gamma = 0.1/log(N), 5 initial
  correlates, post-lasso penalty-loading iterations).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

# ---------------------------------------------------------------------------
# OLS / 2SLS
# ---------------------------------------------------------------------------


def _add_const(X: np.ndarray) -> np.ndarray:
    return np.column_stack([X, np.ones(len(X))])


def ols_robust(y, X, hc: str = "HC1"):
    """OLS of y on X (constant appended). Returns (beta, se) arrays aligned with X columns."""
    y = np.asarray(y, float)
    X = _add_const(np.asarray(X, float))
    n, k = X.shape
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    meat = (X * e[:, None] ** 2).T @ X
    V = XtXi @ meat @ XtXi
    if hc == "HC1":
        V *= n / (n - k)
    return b[:-1], np.sqrt(np.diag(V))[:-1]


def wls_robust(y, X, w):
    """Weighted OLS with probability weights, `reg y X [pweight=w], robust` (HC1).

    Returns (beta, se) arrays aligned with X columns (constant appended and dropped).
    """
    y = np.asarray(y, float)
    w = np.asarray(w, float)
    X = _add_const(np.asarray(X, float))
    n, k = X.shape
    XtWXi = np.linalg.pinv((X * w[:, None]).T @ X)
    b = XtWXi @ (X * w[:, None]).T @ y
    e = y - X @ b
    meat = (X * (w * e)[:, None] ** 2).T @ X
    V = XtWXi @ meat @ XtWXi * n / (n - k)
    return b[:-1], np.sqrt(np.diag(V))[:-1]


def logit_prob(y, X, tol: float = 1e-12, max_iter: int = 100):
    """Fitted P(y=1|X) from a logit of y on X (constant appended), by Newton-Raphson."""
    y = np.asarray(y, float)
    X = _add_const(np.asarray(X, float))
    b = np.zeros(X.shape[1])
    for _ in range(max_iter):
        p = 1 / (1 + np.exp(-X @ b))
        step = np.linalg.solve((X * (p * (1 - p))[:, None]).T @ X, X.T @ (y - p))
        b += step
        if np.max(np.abs(step)) < tol:
            break
    return 1 / (1 + np.exp(-X @ b))


def iv_robust(y, d, W, z, small: bool = False):
    """Just-identified 2SLS of y on d (instrumented by z) and exogenous W (constant appended).

    Returns (beta_d, se_d). small=False matches `ivregress 2sls, vce(robust)` (no dof scaling).
    """
    y = np.asarray(y, float)
    W = np.asarray(W, float).reshape(len(y), -1)
    X = _add_const(np.column_stack([np.asarray(d, float), W]))
    Z = _add_const(np.column_stack([np.asarray(z, float), W]))
    n, k = X.shape
    ZX_i = np.linalg.inv(Z.T @ X)
    b = ZX_i @ Z.T @ y
    e = y - X @ b
    meat = (Z * e[:, None] ** 2).T @ Z
    V = ZX_i @ meat @ ZX_i.T
    if small:
        V *= n / (n - k)
    return b[0], np.sqrt(V[0, 0])


# ---------------------------------------------------------------------------
# Neyman paired estimators
# ---------------------------------------------------------------------------


def _pair_diffs(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    wide = df.pivot(index="pairyear", columns="treated", values=cols)
    return pd.DataFrame({c: wide[(c, 1)] - wide[(c, 0)] for c in cols})


def neyman(df: pd.DataFrame, y: str):
    """Paired difference in means and Neyman SE. df restricted to complete pairs."""
    diff = _pair_diffs(df, [y])[y]
    J = len(diff)
    return diff.mean(), np.sqrt(((diff - diff.mean()) ** 2).sum() / J / (J - 1))


def neyman_late(df: pd.DataFrame, y: str, d: str):
    """Paired Wald estimator with delta-method SE (Stata `neyman_late`)."""
    dd = _pair_diffs(df, [y, d])
    J = len(dd)
    m_y, m_d = dd[y].mean(), dd[d].mean()
    v_y = ((dd[y] - m_y) ** 2).sum() / J / (J - 1)
    v_d = ((dd[d] - m_d) ** 2).sum() / J / (J - 1)
    cov = ((dd[y] - m_y) * (dd[d] - m_d)).sum() / J / (J - 1)
    late = m_y / m_d
    se = late * np.sqrt(v_y / m_y**2 + v_d / m_d**2 - 2 * cov / (m_y * m_d))
    return late, abs(se)


# ---------------------------------------------------------------------------
# Rigorous lasso and post-double-selection
# ---------------------------------------------------------------------------


def _partial(A: np.ndarray, P: np.ndarray) -> np.ndarray:
    """Residualize columns of A on P."""
    if P.shape[1] == 0:
        return A
    coef = np.linalg.lstsq(P, A, rcond=None)[0]
    return A - P @ coef


def _within(A: np.ndarray, groups: np.ndarray) -> np.ndarray:
    df = pd.DataFrame(A)
    return (df - df.groupby(groups).transform("mean")).to_numpy()


def _lasso_cd(y, X, lam, psi, tol=1e-10, max_iter=100000):
    """Minimize (1/n)||y - Xb||^2 + (lam/n) sum psi_j |b_j| by coordinate descent."""
    p = X.shape[1]
    b = np.zeros(p)
    r = y.copy()
    xx = (X**2).sum(0)
    for _ in range(max_iter):
        bmax = 0.0
        for j in range(p):
            if xx[j] == 0:
                continue
            bj_old = b[j]
            rho = X[:, j] @ r + xx[j] * bj_old
            thr = lam * psi[j] / 2
            bj = np.sign(rho) * max(abs(rho) - thr, 0.0) / xx[j]
            if bj != bj_old:
                r -= X[:, j] * (bj - bj_old)
                b[j] = bj
                bmax = max(bmax, abs(bj - bj_old))
        if bmax < tol:
            break
    return b


def rlasso(
    y,
    X,
    c: float = 1.1,
    gamma: float | None = None,
    n_corr: int = 5,
    max_psi_iter: int = 2,
    tol_psi: float = 1e-4,
    n_eff: int | None = None,
):
    """Heteroskedastic rigorous lasso on already-partialled y, X. Returns selected column idx.

    n_eff: sample size used for lambda and loadings (defaults to len(y)).
    """
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, p = X.shape
    N = n if n_eff is None else n_eff
    if gamma is None:
        gamma = 0.1 / np.log(N)
    lam = 2 * c * np.sqrt(N) * norm.ppf(1 - gamma / (2 * p))

    # initial residuals: OLS on the n_corr regressors most correlated with y
    sd = X.std(0)
    corr = np.where(sd > 0, np.abs(X.T @ (y - y.mean())) / np.where(sd > 0, sd, 1), 0)
    top = np.argsort(-corr)[: min(n_corr, p)]
    e = y - X[:, top] @ np.linalg.lstsq(X[:, top], y, rcond=None)[0]

    psi = np.sqrt(((X**2) * (e[:, None] ** 2)).sum(0) / N)
    sel = np.array([], dtype=int)
    for _ in range(max_psi_iter + 1):
        b = _lasso_cd(y, X, lam, psi)
        sel = np.flatnonzero(b != 0)
        if len(sel):
            e = y - X[:, sel] @ np.linalg.lstsq(X[:, sel], y, rcond=None)[0]
        else:
            e = y.copy()
        psi_new = np.sqrt(((X**2) * (e[:, None] ** 2)).sum(0) / N)
        if np.max(np.abs(psi_new - psi) / np.where(psi > 0, psi, 1)) < tol_psi:
            psi = psi_new
            break
        psi = psi_new
    return sel


def _prep(df, cols_pen, cols_part, fe=None):
    """Return dict of partialled arrays: within-transform (if fe) then partial constant + cols_part."""

    def arr(cols):
        return df[cols].to_numpy(float) if cols else np.zeros((len(df), 0))

    if fe is not None:
        g = df[fe].to_numpy()
        tr = lambda A: _within(A, g)  # noqa: E731
        P = tr(arr(cols_part))
    else:
        tr = lambda A: A  # noqa: E731
        P = _add_const(arr(cols_part))
    return tr, P


def _fe_dof(df, fe):
    """Large-sample FE adjustment N/(N - number of groups) for the robust VCE.

    pdslasso/ivlasso compute this (dofminus) for the fe option, and the published tables
    include it. ivlasso 1.1.02 never passes it on to ivreg2, so current Stata output omits it
    (SEs too small by sqrt(2) with matched pairs). We keep the adjustment.
    """
    if fe is None:
        return 1.0
    n = len(df)
    return n / (n - df[fe].nunique())


def pds(
    df: pd.DataFrame,
    y: str,
    d: str,
    controls: list[str],
    partial: list[str],
    fe: str | None = None,
):
    """pdslasso y d (partial + controls), partial(partial) [fe] robust.

    Returns dict(beta, se, N, selected, fe_dof).
    """
    df = df.dropna(subset=[y, d, *controls, *partial])
    tr, P = _prep(df, controls, partial, fe)
    Y = _partial(tr(df[[y]].to_numpy(float)), P)[:, 0]
    D = _partial(tr(df[[d]].to_numpy(float)), P)[:, 0]
    X = _partial(tr(df[controls].to_numpy(float)), P)
    sel = sorted(set(rlasso(Y, X)) | set(rlasso(D, X)))
    selected = [controls[i] for i in sel]
    # final OLS on partialled data, robust (HC0, matching pdslasso's ivreg2 robust)
    R = np.column_stack([D, X[:, sel]]) if sel else D[:, None]
    n = len(Y)
    XtXi = np.linalg.pinv(R.T @ R)
    b = XtXi @ R.T @ Y
    e = Y - R @ b
    V = XtXi @ ((R * e[:, None] ** 2).T @ R) @ XtXi
    dof = _fe_dof(df, fe)
    V *= dof
    return {"beta": b[0], "se": np.sqrt(V[0, 0]), "N": n, "selected": selected, "fe_dof": dof}


def pds_iv(
    df: pd.DataFrame,
    y: str,
    d: str,
    z: str,
    controls: list[str],
    partial: list[str],
    fe: str | None = None,
    select_on: tuple[str, ...] = ("y", "d"),
):
    """ivlasso y (partial + controls) (d = z), partial(partial z) [fe] robust.

    Selection is the union of rigorous-lasso selections of the partialled controls for the
    equations listed in select_on (see comment below). Returns dict(beta, se, N, selected, fe_dof).
    """
    df = df.dropna(subset=[y, d, z, *controls, *partial])
    tr, P = _prep(df, controls, partial, fe)
    Y = _partial(tr(df[[y]].to_numpy(float)), P)[:, 0]
    D = _partial(tr(df[[d]].to_numpy(float)), P)[:, 0]
    Zz = _partial(tr(df[[z]].to_numpy(float)), P)[:, 0]
    X = _partial(tr(df[controls].to_numpy(float)), P)
    # Selection follows ivlasso's low-dimensional-instrument case: lasso of y on X, and lasso of
    # d on X with the (unpenalized) instrument partialled out. This choice reproduces 6 of the 8
    # existing Stata ivlasso selections exactly (all non-FE, and both FE duration models).
    eqs = {"y": Y, "d": _partial(D[:, None], Zz[:, None])[:, 0]}
    sel = sorted(set().union(*[set(rlasso(eqs[k], X)) for k in select_on]))
    selected = [controls[i] for i in sel]
    Xs = X[:, sel]
    RX = np.column_stack([D, Xs])
    RZ = np.column_stack([Zz, Xs])
    ZX_i = np.linalg.inv(RZ.T @ RX)
    b = ZX_i @ RZ.T @ Y
    e = Y - RX @ b
    V = ZX_i @ ((RZ * e[:, None] ** 2).T @ RZ) @ ZX_i.T
    dof = _fe_dof(df, fe)
    V *= dof
    return {"beta": b[0], "se": np.sqrt(V[0, 0]), "N": len(Y), "selected": selected, "fe_dof": dof}
