#!/usr/bin/env python
# coding: utf-8

# # Referee-requested analyses (JEE revision)
# 
# Python kernel. Produces the inputs for the new appendix tables/figures requested by Referee 1:
# 
# 1. **Point 1** — sample size, treatment assignment, and attrition by year (Figure A1 and Table A1 by year).
# 2. **Point 2** — exam score mean, median, and standard deviation by year and exam.
# 3. **Point 3** — Micro B enrollment (Table 8, "Took Micro B") and Micro B video watching (Table 9,
#    Panel A) by year. The enrollment gap is entirely in 2019, so 2018 is a persistence test without
#    differential selection into Micro B.
# 4. **Point 4** — first-stage and second-stage estimates (Tables 4 and 5) with video counts restricted to
#    credit-eligible opens (no other video opened before the video could be watched in full).
# 
# Stata was unavailable for this revision (expired license), so estimators are ported to Python in
# `modules/estimators.py`. Section 0 validates the ports by reproducing the existing Stata output files
# before anything new is computed. Outputs go to `data/generated/`; `assemble_tables.ipynb` turns them into
# LaTeX.

import sys

import numpy as np
import pandas as pd
from scipy.stats import norm, ttest_ind

sys.path.insert(0, ".")

from modules.analysis_data import CTRL_VARS, get_std_units, load_analysis_frame
from modules.estimators import (
    iv_robust,
    logit_prob,
    neyman,
    neyman_late,
    ols_robust,
    pds,
    pds_iv,
    wls_robust,
)

DATA_GEN = "../data/generated"
YEARS = [2018, 2019]

df = load_analysis_frame(DATA_GEN)
print(df.groupby(["year", "arm"]).size().unstack())


# ## 0. Validate Python ports against existing Stata output
# 
# Model (1) OLS, model (2) Neyman, the 2SLS LATEs, and all post-double-selection (PDS) ITT
# estimates are checked against `itt_coeffs.csv`, `lates_coeffs.csv`, `pds_coeffs.csv`, and
# `pds_iv_coeffs.csv`. Known residual differences from Stata's `lassopack` are printed rather than asserted.

itt_st = pd.read_csv(f"{DATA_GEN}/itt_coeffs.csv")
late_st = pd.read_csv(f"{DATA_GEN}/lates_coeffs.csv")
pds_st = pd.read_csv(f"{DATA_GEN}/pds_coeffs.csv")
pdsiv_st = pd.read_csv(f"{DATA_GEN}/pds_iv_coeffs.csv")


def samples(data, exam):
    """Model (1)/(3) sample and matched-pair model (2)/(4) sample, as in analyze_data.ipynb."""
    s = data[(data.arm > 0) & data[f"{exam}scorestd"].notnull()].copy()
    sp = data[(data.arm > 0) & (data[f"bothpairs_{exam}"] == 1)].copy()
    return s, sp


def st(frame, depvar, model):
    return frame[(frame.depvar == depvar) & (frame.model == model)].iloc[0]


checks, notes = [], []
for exam in ["mid2", "final"]:
    s, sp = samples(df, exam)
    for v in [
        f"videos_{exam}_u",
        f"videos_{exam}",
        f"duration_{exam}_u",
        f"duration_{exam}",
        f"{exam}scorestd",
    ]:
        b, se = ols_robust(s[v], s[["treated", "mid1scorestd", "y2019"]])
        r = st(itt_st, v, "itt")
        checks.append((f"OLS {v}", b[0], r.treatbeta, se[0], r.stderr))
        nb, nse = neyman(sp, v)
        r = st(itt_st, v, "Neyman")
        checks.append((f"Neyman {v}", nb, r.treatbeta, nse, r.stderr))
        for mod, data, part, fe in [
            ("noFEs", s, ["y2019", "mid1scorestd"], None),
            ("FEs", sp, ["mid1scorestd"], "pairyear"),
        ]:
            p = pds(data, v, "treated", CTRL_VARS, part, fe=fe)
            r = st(pds_st, v, mod)
            st_sel = sorted(str(r.ctrls).split()) if isinstance(r.ctrls, str) else []
            if sorted(p["selected"]) == st_sel:
                # Stata SEs lack the FE dof adjustment (ivlasso 1.1.02 bug); add it before comparing
                checks.append(
                    (f"PDS {mod} {v}", p["beta"], r.treatbeta, p["se"], r.stderr * np.sqrt(p["fe_dof"]))
                )
            else:
                notes.append(
                    f"PDS {mod} {v}: python selects {p['selected']}, Stata {st_sel}; "
                    f"beta {p['beta']:.4f} vs {r.treatbeta:.4f}"
                )
    y = f"{exam}scorestd"
    s10, sp10 = s.copy(), sp.copy()
    s10[f"videos_{exam}_u"] /= 10
    sp10[f"videos_{exam}_u"] /= 10
    for d, m in [(f"videos_{exam}_u", "v"), (f"duration_{exam}_u", "d")]:
        b, se = iv_robust(s10[y], s10[d], s10[["mid1scorestd", "y2019"]], s10["treated"])
        r = st(late_st, y, f"late_{m}")
        checks.append((f"2SLS {y} {m}", b, r.treatbeta, se, r.stderr))
        b, se = neyman_late(sp10, y, d)
        r = st(late_st, y, f"N_late_{m}")
        checks.append((f"Neyman LATE {y} {m}", b, r.treatbeta, se, r.stderr))
        for mod, data, part, fe in [
            (f"PDS_IV_{m}", s10, ["y2019", "mid1scorestd"], None),
            (f"PDS_IVFE_{m}", sp10, ["mid1scorestd"], "pairyear"),
        ]:
            p = pds_iv(data, y, d, "treated", CTRL_VARS, part, fe=fe)
            r = st(pdsiv_st, y, mod)
            st_sel = sorted(str(r.ctrls).split())
            if sorted(p["selected"]) == st_sel:
                checks.append(
                    (f"{mod} {y}", p["beta"], r.treatbeta, p["se"], r.stderr * np.sqrt(p["fe_dof"]))
                )
            else:
                notes.append(
                    f"{mod} {y}: python selects {p['selected']}, Stata {st_sel}; "
                    f"beta {p['beta']:.4f} vs {r.treatbeta:.4f}"
                )

chk = pd.DataFrame(checks, columns=["estimate", "beta_py", "beta_stata", "se_py", "se_stata"])
chk["max_abs_diff"] = np.maximum(abs(chk.beta_py - chk.beta_stata), abs(chk.se_py - chk.se_stata))
print(chk.to_string())
assert (chk.max_abs_diff < 1e-4).all(), "Python port does not reproduce Stata"
print(f"\n{len(chk)} estimates reproduce Stata to < 1e-4.")
print("\nSelection differences (not asserted):")
print("\n".join(notes))


# ## 1. Sample size, treatment assignment, and attrition by year (Referee point 1)
# 
# Pre-anonymization assignment counts for the randomized arms are recovered from the matched-pair
# identifiers (pairs are numbered consecutively within year, so assigned *Control* = assigned
# *Incentive* = number of pairs). The pre-anonymization count of *Above median* students by year
# is not recoverable from the anonymized data (five were removed across both years).

def attrition_counts(data):
    """Counts at each stage of Figure A1 for one sample (Stata block 'examine attrition')."""
    out = {}
    for a in [0, 1, 2]:
        g = data[data.arm == a]
        obs = g[g.assigned_grade.notnull()]
        out[a] = {
            "assigned": np.nan if a == 0 else g.pair.max() if len(g) else np.nan,
            "consented": len(g),
            "observed_status": len(obs),
            "took_mid2": int(obs.mid2score.notnull().sum()),
            "took_final": int(obs.finalscore.notnull().sum()),
            "took_100b": int((obs.took100b == 1).sum()),
        }
    return pd.DataFrame(out).T


def attrition_pvalues(data):
    """Welch t-test of attrition rates, Control vs Incentive, among students who observed status."""
    obs = data[(data.assigned_grade.notnull()) & (data.arm > 0)]
    res = {}
    for k, miss in [
        ("took_mid2", obs.mid2score.isnull()),
        ("took_final", obs.finalscore.isnull()),
        ("took_100b", obs.took100b == 0),
    ]:
        miss = miss.astype(float)
        res[k] = ttest_ind(miss[obs.arm == 1], miss[obs.arm == 2], equal_var=False).pvalue
    return res


rows = []
for label, data in [("pooled", df)] + [(str(y), df[df.year == y]) for y in YEARS]:
    c = attrition_counts(data)
    if label == "pooled":
        # pairs are numbered within year, so sum the per-year maxima
        for a in [1, 2]:
            c.loc[a, "assigned"] = sum(
                df[(df.year == y) & (df.arm == a)].pair.max() for y in YEARS
            )
    p = attrition_pvalues(data)
    for a in [0, 1, 2]:
        rows.append({"sample": label, "arm": a, **c.loc[a].to_dict()})
    rows.append({"sample": label, "arm": "pvalue", **p})
attr = pd.DataFrame(rows)
print(attr.to_string())

# validate the pooled numbers against the hand-entered Figure A1 (attrite_chart.tex)
pooled = attr[attr["sample"] == "pooled"].set_index("arm")
assert pooled.loc[1, "assigned"] == 218 and pooled.loc[2, "assigned"] == 218
assert list(pooled.loc[[0, 1, 2], "consented"]) == [420, 215, 215]
assert list(pooled.loc[[0, 1, 2], "observed_status"]) == [418, 196, 206]
assert list(pooled.loc[[0, 1, 2], "took_final"]) == [415, 184, 190]
assert list(pooled.loc[[0, 1, 2], "took_100b"]) == [284, 114, 100]
assert [round(pooled.loc["pvalue", k], 2) for k in ["took_mid2", "took_final", "took_100b"]] == [
    0.75,
    0.52,
    0.05,
]

attr.to_csv(f"{DATA_GEN}/attrition_by_year.csv", index=False)


# ### Balance by year (Table A1 by year)
# 
# Same statistics as the Stata balance block (`balance_table_data.csv`), computed separately by year.
# The pooled computation is validated against the Stata output first.

BALANCE_VARS = [
    "mid1scorestd",
    "y2019",
    "prev_cumgpa",
    "prev_cumgpa_unobs",
    "mathquizstd",
    "pset_pre",
    "videos_mid1",
    "videos_mid1_u",
    "duration_mid1",
    "duration_mid1_u",
    "asian",
    "latx",
    "white",
    "othereth",
    "female",
    "male",
    "transfer",
]

dfb = df.copy()
eth = dfb["ethnicity"]
known = [
    "Chicanx/Latinx",
    "White/Caucasian",
    "Chinese/Chinese-American",
    "All Other Asian/Asian-American",
    "Vietnamese",
]
dfb["othereth"] = (eth.notnull() & ~eth.isin(known)).astype(int)
dfb.loc[dfb.prev_cumgpa_unobs == 1, "prev_cumgpa"] = np.nan  # as in Stata balance block


def balance_rows(data):
    out = []
    for exam in ["mid2", "final"]:
        base = data[data.assigned_grade.notnull()]
        for bp, sub, arms in [
            (-1, base, [0, 1, 2]),
            (0, base[base[f"{exam}score"].notnull()], [0, 1, 2]),
        ]:
            for v in BALANCE_VARS:
                for a in arms:
                    x = sub.loc[sub.arm == a, v].dropna()
                    out.append(
                        {
                            "depvar": v,
                            "arm": a,
                            "exam": exam,
                            "bothpairs": bp,
                            "mean": x.mean(),
                            "stderr": x.std() / np.sqrt(len(x)),
                            "N": len(x),
                        }
                    )
        sub = base[base[f"{exam}score"].notnull() & (base[f"bothpairs_{exam}"] == 1)]
        for v in BALANCE_VARS:
            for a in [1, 2]:
                x = sub.loc[sub.arm == a, v].dropna()
                out.append(
                    {
                        "depvar": v,
                        "arm": a,
                        "exam": exam,
                        "bothpairs": 1,
                        "mean": x.mean(),
                        "stderr": x.std() / np.sqrt(len(x)),
                        "N": len(x),
                    }
                )
    return pd.DataFrame(out)


bal_st = pd.read_csv(f"{DATA_GEN}/balance_table_data.csv")
bal_py = balance_rows(dfb)
m = bal_st.merge(bal_py, on=["depvar", "arm", "exam", "bothpairs"], suffixes=("_st", "_py"))
assert len(m) == len(bal_st)
assert np.allclose(m.mean_st, m.mean_py, atol=1e-6, equal_nan=True)
assert np.allclose(m.stderr_st, m.stderr_py, atol=1e-6, equal_nan=True)
assert (m.N_st == m.N_py).all()
print("Pooled balance statistics reproduce balance_table_data.csv.")

bal_year = pd.concat(
    [balance_rows(dfb[dfb.year == y]).assign(year=y) for y in YEARS], ignore_index=True
)
bal_year.to_csv(f"{DATA_GEN}/balance_table_data_by_year.csv", index=False)
bal_year.query("exam == 'final' and bothpairs == 0 and depvar == 'mid1scorestd'")


# ## 2. Exam score summary statistics by year (Referee point 2)
# 
# Raw exam scores (percent of points possible) for every student in the analysis sample who sat
# the exam, by year and arm.

exam_cols = {"mid1score": "Midterm 1", "mid2score": "Midterm 2", "finalscore": "Final exam"}
groups = {"All students": [0, 1, 2], "Above median": [0], "Control": [1], "Incentive": [2]}
rows = []
for y in YEARS:
    for gname, arms in groups.items():
        for col, ename in exam_cols.items():
            x = df.loc[(df.year == y) & df.arm.isin(arms), col].dropna() * 100
            rows.append(
                {
                    "year": y,
                    "group": gname,
                    "exam": ename,
                    "N": len(x),
                    "mean": x.mean(),
                    "median": x.median(),
                    "sd": x.std(),
                }
            )
exam_stats = pd.DataFrame(rows)
exam_stats.to_csv(f"{DATA_GEN}/exam_stats_by_year.csv", index=False)
exam_stats.round(1)


# ## 3. Tables 4 and 5 with credit-eligible video counts (Referee point 4)
# 
# `*_cr` measures (built in `assemble_data.ipynb`, `modules.video_agg.add_credit_flag`) count only
# video opens that could have been watched in full at 2x speed before the student's next open. The same four models
# as Tables 4 and 5 are estimated with these measures; the reduced form is unchanged by construction.
# For comparison, the same Python code is also run on the original measures.

def first_stage(data, measures):
    """Rows of Table 4 for the given {label: column} measures."""
    out = []
    for exam in ["mid2", "final"]:
        s, sp = samples(data, exam)
        for label, tmpl in measures.items():
            v = tmpl.format(exam=exam)
            mean_ctrl = s.loc[s.arm == 1, v].mean()
            b, se = ols_robust(s[v], s[["treated", "mid1scorestd", "y2019"]])
            out.append((exam, label, 1, b[0], se[0], len(s), mean_ctrl, ""))
            nb, nse = neyman(sp, v)
            out.append((exam, label, 2, nb, nse, len(sp), mean_ctrl, ""))
            p = pds(s, v, "treated", CTRL_VARS, ["y2019", "mid1scorestd"])
            out.append(
                (exam, label, 3, p["beta"], p["se"], p["N"], mean_ctrl, " ".join(p["selected"]))
            )
            p = pds(sp, v, "treated", CTRL_VARS, ["mid1scorestd"], fe="pairyear")
            out.append(
                (exam, label, 4, p["beta"], p["se"], p["N"], mean_ctrl, " ".join(p["selected"]))
            )
    return pd.DataFrame(
        out, columns=["exam", "measure", "model", "beta", "se", "N", "meanctrl", "ctrls"]
    )


def second_stage(data, vid_tmpl, dur_tmpl):
    """Rows of Table 5: RF, 2SLS per 10 videos, 2SLS per hour."""
    out = []
    for exam in ["mid2", "final"]:
        y = f"{exam}scorestd"
        s, sp = samples(data, exam)
        vid, dur = vid_tmpl.format(exam=exam), dur_tmpl.format(exam=exam)
        for frame in (s, sp):
            frame[vid] = frame[vid] / 10
        b, se = ols_robust(s[y], s[["treated", "mid1scorestd", "y2019"]])
        out.append((exam, "RF", 1, b[0], se[0], len(s), ""))
        nb, nse = neyman(sp, y)
        out.append((exam, "RF", 2, nb, nse, len(sp), ""))
        p = pds(s, y, "treated", CTRL_VARS, ["y2019", "mid1scorestd"])
        out.append((exam, "RF", 3, p["beta"], p["se"], p["N"], " ".join(p["selected"])))
        p = pds(sp, y, "treated", CTRL_VARS, ["mid1scorestd"], fe="pairyear")
        out.append((exam, "RF", 4, p["beta"], p["se"], p["N"], " ".join(p["selected"])))
        for label, d in [("2SLS_videos10", vid), ("2SLS_hours", dur)]:
            b, se = iv_robust(s[y], s[d], s[["mid1scorestd", "y2019"]], s["treated"])
            out.append((exam, label, 1, b, se, len(s), ""))
            b, se = neyman_late(sp, y, d)
            out.append((exam, label, 2, b, se, len(sp), ""))
            p = pds_iv(s, y, d, "treated", CTRL_VARS, ["y2019", "mid1scorestd"])
            out.append((exam, label, 3, p["beta"], p["se"], p["N"], " ".join(p["selected"])))
            p = pds_iv(sp, y, d, "treated", CTRL_VARS, ["mid1scorestd"], fe="pairyear")
            out.append((exam, label, 4, p["beta"], p["se"], p["N"], " ".join(p["selected"])))
    return pd.DataFrame(out, columns=["exam", "row", "model", "beta", "se", "N", "ctrls"])


credit_measures = {
    "Videos": "videos_{exam}_cr",
    "Unique videos": "videos_{exam}_cr_u",
    "Hours of videos": "duration_{exam}_cr",
    "Hours of unique videos": "duration_{exam}_cr_u",
}
orig_measures = {
    "Videos": "videos_{exam}",
    "Unique videos": "videos_{exam}_u",
    "Hours of videos": "duration_{exam}",
    "Hours of unique videos": "duration_{exam}_u",
}

fs_cr = first_stage(df, credit_measures)
ss_cr = second_stage(df, "videos_{exam}_cr_u", "duration_{exam}_cr_u")
fs_cr.to_csv(f"{DATA_GEN}/credit_firststage_coeffs.csv", index=False)
ss_cr.to_csv(f"{DATA_GEN}/credit_secondstage_coeffs.csv", index=False)

# side-by-side with the Python estimates on the original (all-opens) measures
fs_og = first_stage(df, orig_measures)
ss_og = second_stage(df, "videos_{exam}_u", "duration_{exam}_u")
cmp_fs = fs_og.merge(fs_cr, on=["exam", "measure", "model"], suffixes=("_all", "_credit"))
cmp_ss = ss_og.merge(ss_cr, on=["exam", "row", "model"], suffixes=("_all", "_credit"))
print(
    cmp_fs[
        [
            "exam",
            "measure",
            "model",
            "meanctrl_all",
            "beta_all",
            "se_all",
            "meanctrl_credit",
            "beta_credit",
            "se_credit",
        ]
    ]
    .round(3)
    .to_string()
)
print(
    cmp_ss[["exam", "row", "model", "beta_all", "se_all", "beta_credit", "se_credit"]]
    .round(3)
    .to_string()
)


# ## 4. Micro B enrollment and Micro B video watching by year (Referee point 3)
# 
# Figure A2 shows the Micro B enrollment gap is entirely in 2019. Here Table 8's *Took Micro B* row and
# Table 9's Panel A are re-estimated separately by year, with `y2019` dropped from every specification
# (and covariates that are constant within a year dropped, as Stata would: `mathquiz_unobs` is all zero in
# 2019). Because the two years are disjoint samples, the 2019 − 2018 difference of the by-year estimates has
# SE $\sqrt{se_{2018}^2 + se_{2019}^2}$; this is the year-interaction test.
# 
# Samples follow `analyze_data.ipynb`:
# 
# - *Took Micro B* models (1)–(4) use final-exam takers (as Table 8); model (5) uses all students who saw
#   their assignment, coding non-enrollment as zero (Stata `itt_zeros`), which is the Figure A2 population.
# - Panel A PDS uses Micro B final-exam takers; IPW reweights Micro B enrollees using a logit for enrollment
#   on baseline covariates fit on all students who saw their assignment, weights trimmed at the 1st/99th
#   percentiles. Generalized Lee bounds by year come from `modules/semenova_bounds.R <leebounds> <year>`.
# 
# Each estimator is first checked against the pooled Stata output.

IPW_X = [
    "mid1scorestd",
    "mathquizstd",
    "mathquiz_unobs",
    "transfer",
    "prev_cumgpa",
    "prev_cumgpa_unobs",
    "female",
    "asian",
    "latx",
    "white",
]
PANEL_A = ["videos_b", "videos_b_u", "duration_b", "duration_b_u"]
ipw_st = pd.read_csv(f"{DATA_GEN}/ipw_100b.csv")


def stata_pctile(x, p):
    """Stata `_pctile` default definition."""
    x = np.sort(np.asarray(x))
    nq = len(x) * p / 100
    return (x[int(nq) - 1] + x[int(nq)]) / 2 if nq == int(nq) else x[int(np.ceil(nq)) - 1]


def took_models(data, yr):
    """Table 8 'Took Micro B' row, models (1)-(4), plus (5) = Stata itt_zeros."""
    s = data[(data.arm > 0) & data.finalscorestd.notnull() & data.took100b.notnull()]
    sp = data[(data.arm > 0) & (data.bothpairs_final == 1)]
    m, mp = s.loc[s.arm == 1, "took100b"].mean(), sp.loc[sp.arm == 1, "took100b"].mean()
    out = []
    b, se = ols_robust(s.took100b, s[["treated", "mid1scorestd", *yr]])
    out.append((1, b[0], se[0], len(s), m, ""))
    nb_, nse = neyman(sp, "took100b")
    out.append((2, nb_, nse, len(sp), mp, ""))
    p = pds(s, "took100b", "treated", CTRL_VARS, [*yr, "mid1scorestd"])
    out.append((3, p["beta"], p["se"], p["N"], m, " ".join(p["selected"])))
    p = pds(sp, "took100b", "treated", CTRL_VARS, ["mid1scorestd"], fe="pairyear")
    out.append((4, p["beta"], p["se"], p["N"], mp, " ".join(p["selected"])))
    z = data[(data.arm > 0) & data.assigned_grade.notnull()].copy()
    z["took100b"] = z.took100b.fillna(0)
    z = get_std_units(z)  # Stata get_itt_with_zeros re-standardizes within this sample
    b, se = ols_robust(z.took100b, z[["treated", "mid1scorestd", *yr]])
    out.append((5, b[0], se[0], len(z), z.loc[z.arm == 1, "took100b"].mean(), ""))
    return pd.DataFrame(out, columns=["model", "beta", "se", "N", "meanctrl", "ctrls"])


def ipw(data, y, yr):
    """Stata est_ipw."""
    full = data[(data.arm > 0) & data.assigned_grade.notnull()].copy()
    xs = [c for c in ["treated", *IPW_X, *yr] if full[c].nunique() > 1]
    full["phat"] = logit_prob(full.took100b, full[xs])
    t = full[full.took100b == 1].copy()
    t["w"] = 1 / t.phat
    t["w"] = t.w.clip(stata_pctile(t.w, 1), stata_pctile(t.w, 99))
    t = t[t[y].notnull()]
    b, se = wls_robust(t[y], t[["treated", "mid1scorestd", *yr]], t.w)
    return b[0], se[0], len(t), t.loc[t.arm == 1, y].mean()


def panel_a(data, yr):
    """Table 9 Panel A: PDS (no FEs) on Micro B final takers, and IPW."""
    s = data[(data.arm > 0) & data.final_100bstd.notnull()]
    out = []
    for v in PANEL_A:
        p = pds(s, v, "treated", CTRL_VARS, [*yr, "mid1scorestd"])
        out.append((v, "pds", p["beta"], p["se"], p["N"], s.loc[s.arm == 1, v].mean(), " ".join(p["selected"])))
        out.append((v, "ipw", *ipw(data, v, yr), ""))
    return pd.DataFrame(out, columns=["depvar", "model", "beta", "se", "N", "meanctrl", "ctrls"])


# --- validate pooled estimates against Stata ---
chk = []
took_pool = took_models(df, ["y2019"])
sp_final = df[(df.arm > 0) & (df.bothpairs_final == 1)]
pair_dof = len(sp_final) / (len(sp_final) - sp_final.pairyear.nunique())
for mdl, (frame, name) in {
    1: (itt_st, "itt"),
    2: (itt_st, "Neyman"),
    3: (pds_st, "noFEs"),
    4: (pds_st, "FEs"),
    5: (itt_st, "itt_zeros"),
}.items():
    r, py = st(frame, "took100b", name), took_pool.set_index("model").loc[mdl]
    se_st = r.stderr * (np.sqrt(pair_dof) if mdl == 4 else 1)  # Stata FE SEs lack dof adj., see Section 0
    chk.append((f"took100b ({mdl})", py.beta, r.treatbeta, py.se, se_st))
pa_pool = panel_a(df, ["y2019"]).set_index(["depvar", "model"])
for v in PANEL_A:
    for mdl, frame, name in [("pds", pds_st, "noFEs"), ("ipw", ipw_st, "ipw")]:
        r, py = st(frame, v, name), pa_pool.loc[(v, mdl)]
        chk.append((f"{v} {mdl}", py.beta, r.treatbeta, py.se, r.stderr))
chk = pd.DataFrame(chk, columns=["estimate", "beta_py", "beta_stata", "se_py", "se_stata"])
chk["max_abs_diff"] = np.maximum(abs(chk.beta_py - chk.beta_stata), abs(chk.se_py - chk.se_stata))
print(chk.to_string())
assert (chk.max_abs_diff < 1e-4).all(), "Python port does not reproduce Stata"
assert list(took_pool.ctrls) == ["", "", "", "mathquizstd", ""]  # PDS selections match Stata


def add_diff(frame, keys):
    """Append 2019 - 2018 rows: difference of independent by-year estimates."""
    a = frame[frame["sample"] == "2018"].set_index(keys)
    b = frame[frame["sample"] == "2019"].set_index(keys)
    d = pd.DataFrame({"beta": b.beta - a.beta, "se": np.sqrt(a.se**2 + b.se**2)})
    d["pvalue"] = 2 * norm.sf(abs(d.beta / d.se))
    return pd.concat([frame, d.reset_index().assign(sample="diff")], ignore_index=True)


took = pd.concat(
    [took_pool.assign(sample="pooled")]
    + [took_models(df[df.year == y], []).assign(sample=str(y)) for y in YEARS],
    ignore_index=True,
)
took = add_diff(took, ["model"])
took.to_csv(f"{DATA_GEN}/microb_took_by_year.csv", index=False)
print(took.round(3).to_string())

vids = pd.concat(
    [pa_pool.reset_index().assign(sample="pooled")]
    + [panel_a(df[df.year == y], []).assign(sample=str(y)) for y in YEARS],
    ignore_index=True,
)
vids = add_diff(vids, ["depvar", "model"])
vids.to_csv(f"{DATA_GEN}/microb_videos_by_year.csv", index=False)
print(vids.round(3).to_string())

