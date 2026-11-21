"""Paper figures in the Journal of Economic Education print style.

JEE style sheet: black and white, arms distinguished by line pattern or weight (not color),
Times New Roman bold at 8-10 pt for axis and line labels, no larger than 5 x 5 inches,
EPS/TIFF/JPEG at 600 dpi or more.

Every figure is drawn with opaque grays only (no alpha): EPS has no transparency.
`save` writes a vector PDF for the LaTeX build (tex/plots/) plus EPS and a 600 dpi grayscale
TIFF for submission (tex/plots/jee/).

Replaces the Stata figures in analyze_data.ipynb (Stata license expired). Data definitions
follow the Stata code; deviations are noted in each function's docstring.
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from .estimators import ols_robust

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

MAX_IN = 5.0  # JEE: no larger than 5 x 5 inches

RC = {
    "font.family": "Times New Roman",
    "font.weight": "bold",
    "axes.labelweight": "bold",
    "axes.titleweight": "bold",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman:bold",
    "mathtext.it": "Times New Roman:bold:italic",
    "mathtext.bf": "Times New Roman:bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "axes.edgecolor": "black",
    "axes.titlelocation": "left",
    "axes.titlepad": 4,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "legend.handlelength": 1.5,
    "legend.handletextpad": 0.4,
    "lines.solid_capstyle": "butt",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 600,
    "savefig.bbox": "standard",
}

INK = "black"
GRID = "0.88"
BAND = "0.82"  # confidence band fill
SHADE = "0.94"  # background shading (alternate weeks)
REF = dict(color="0.6", lw=0.6, ls="-")  # reference lines (exams, thresholds, zero)
HIST_CONTROL = "0.72"  # Control histogram fill

# Arm encodings: weight + pattern, never color.
ARM_STYLE = {
    "Incentive": dict(color=INK, lw=1.7, ls="-"),
    "Control": dict(color=INK, lw=1.0, ls=(0, (4.5, 2))),
    "Above median": dict(color="0.45", lw=1.0, ls=(0, (1, 1.6))),
}
ARM_NAME = {0: "Above median", 1: "Control", 2: "Incentive"}

# Dot encodings for per-video rates: filled = Incentive, open = Control.
DOT = {
    "Incentive": dict(marker="o", ms=3.4, mfc=INK, mec=INK, mew=0.6, ls="none"),
    "Control": dict(marker="o", ms=3.4, mfc="white", mec=INK, mew=0.7, ls="none"),
}


def use_style():
    mpl.rcParams.update(RC)


def _grid(ax, axis="y"):
    ax.grid(axis=axis, color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)


def save(fig, name: str, plots_dir: str | Path):
    """Write <name>.pdf (LaTeX), jee/<name>.eps and jee/<name>.tif (600 dpi grayscale)."""
    w, h = fig.get_size_inches()
    assert w <= MAX_IN + 1e-9 and h <= MAX_IN + 1e-9, f"{name}: {w}x{h} in exceeds 5x5"
    plots_dir = Path(plots_dir)
    jee = plots_dir / "jee"
    jee.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / f"{name}.pdf")
    fig.savefig(jee / f"{name}.eps")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=600)
    buf.seek(0)
    Image.open(buf).convert("L").save(
        jee / f"{name}.tif", dpi=(600, 600), compression="tiff_lzw"
    )


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _survival(v: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Share of observations with v >= x for each x in grid."""
    v = np.sort(np.asarray(v, float))
    return 1 - np.searchsorted(v, grid, side="left") / len(v)


def survival_effects(df: pd.DataFrame, var: str, xmax: int) -> pd.DataFrame:
    """Port of the Stata loop behind combo_cdf: for X = 0..xmax, arm means of 1{var >= X} and the
    HC1-robust OLS coefficient on Incentive (Incentive vs Control only) with a 95% CI."""
    d = df.loc[df["arm"].isin([1, 2]), [var, "arm"]].dropna()
    t = (d["arm"] == 2).to_numpy(float)
    rows = []
    for x in range(xmax + 1):
        y = (d[var] >= x).to_numpy(float)
        if y.std() == 0:
            b, se = np.array([0.0]), np.array([0.0])
        else:
            with np.errstate(invalid="ignore"):
                b, se = ols_robust(y, t[:, None])
            se = np.nan_to_num(se)  # 1-2 nonzero obs: HC1 variance can round below zero
        rows.append(
            dict(
                x=x,
                control=y[t == 0].mean(),
                incentive=y[t == 1].mean(),
                effect=b[0],
                lo=b[0] - 1.96 * se[0],
                hi=b[0] + 1.96 * se[0],
            )
        )
    return pd.DataFrame(rows)


def local_linear(x, y, grid, h: float):
    """Local linear regression with a triangle kernel and bandwidth h (Stata lpoly kernel(tri)
    degree(1)). Returns fit, lower and upper 95% pointwise bands. The variance uses the
    equivalent-kernel weights and squared residuals (heteroskedasticity-robust), so bands
    differ slightly from Stata's lpolyci, which assumes a constant residual variance."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    def weights(x0):
        u = (x - x0) / h
        k = np.clip(1 - np.abs(u), 0, None)
        X = np.column_stack([np.ones_like(x), x - x0])
        XtW = X.T * k
        A = np.linalg.pinv(XtW @ X)
        return (A @ XtW)[0]  # equivalent kernel: fit(x0) = l @ y

    resid = y - np.array([weights(xi) @ y for xi in x])
    fit, se = [], []
    for g in grid:
        l = weights(g)
        fit.append(l @ y)
        se.append(np.sqrt(np.sum(l**2 * resid**2)))
    fit, se = np.array(fit), np.array(se)
    return fit, fit - 1.96 * se, fit + 1.96 * se


def video_watch_rates(data_raw: str | Path, sample: pd.DataFrame) -> pd.DataFrame:
    """Per-video share of each arm that opened the video at least once (Stata block behind
    bar_uviews*). `sample` holds id, year, arm for students who took the final; only arms 1-2
    are kept. Videos are those in the IMVH log with a runtime and a syllabus week."""
    v = pd.read_csv(Path(data_raw) / "DeID_video-level_data.csv")
    v = v.dropna(subset=["length_mins", "DeID", "syllabus_week"])
    v["duration_min"] = (v["minutes"] * 60 + v["seconds"]) / 60
    vids = (
        v.groupby("videocode")
        .agg(
            incentivized=("incentivized", "min"),
            week=("syllabus_week", "min"),
            duration_min=("duration_min", "min"),
            title=("title", "first"),
        )
        .reset_index()
    )
    vids["incent"] = (vids["incentivized"] > 0).astype(int)
    vids["week"] = vids["week"].astype(int) + 1
    s = sample.loc[sample["arm"].isin([1, 2]), ["id", "year", "arm"]].copy()
    s["id"] = s["id"].astype(str)
    v = v.rename(columns={"DeID": "id"})
    v["id"] = v["id"].astype(str)
    seen = v[["id", "year", "videocode"]].drop_duplicates().merge(s, on=["id", "year"])
    n_arm = s.groupby("arm").size()
    rates = (
        seen.groupby(["videocode", "arm"]).size().unstack("arm").reindex(vids["videocode"])
        .fillna(0)
        .div(n_arm, axis=1)
    )
    vids["control"] = rates[1].to_numpy()
    vids["incentive"] = rates[2].to_numpy()
    return vids


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def fig_videos_survival(df: pd.DataFrame, exam_takers: bool = True):
    """`combo_cdf`. Top: % of each arm watching at least X unique videos before
    midterm 2 / before the final. Bottom: Incentive - Control difference with 95% CI.
    Sample (default exam_takers=True): students who took that panel's exam (midterm 2 /
    final), matching the other figures and the regression tables. exam_takers=False gives the
    Stata sample, all Incentive and Control students, including 28 who left before learning
    their assignment."""
    panels = [
        ("A. Before midterm 2", "videos_mid2_u", 70, 15, "mid2score"),
        ("B. Before final exam", "videos_final_u", 75, 15, "finalscore"),
    ]
    fig, axes = plt.subplots(
        2, 2, figsize=(5.0, 4.4), sharex="col", gridspec_kw=dict(height_ratios=[1.15, 1])
    )
    for j, (title, var, xmax, step, exam) in enumerate(panels):
        r = survival_effects(df.loc[df[exam].notnull()] if exam_takers else df, var, xmax)
        top, bot = axes[0, j], axes[1, j]
        top.plot(r.x, 100 * r.control, **ARM_STYLE["Control"])
        top.plot(r.x, 100 * r.incentive, **ARM_STYLE["Incentive"])
        top.set_title(title)
        top.set_ylim(0, 102)
        top.set_yticks(range(0, 101, 25))
        _grid(top)
        bot.fill_between(r.x, 100 * r.lo, 100 * r.hi, color=BAND, lw=0, zorder=1)
        bot.plot(r.x, 100 * r.effect, color=INK, lw=1.3, zorder=2)
        bot.axhline(0, **REF, zorder=2)
        bot.set_ylim(-15, 65)
        bot.set_yticks(range(0, 61, 20))
        bot.set_xlim(0, xmax)
        bot.set_xticks(range(0, xmax + 1, step))
        bot.set_xlabel("Unique videos")
        _grid(bot)
        if j == 0:
            top.set_ylabel("% watching " + r"$\geq$" + "X unique videos")
            bot.set_ylabel("Effect of incentive on\nwatching " + r"$\geq$" + "X unique videos")
        else:
            top.tick_params(labelleft=False)
            bot.tick_params(labelleft=False)
        if j == 0:
            handles = [mpl.lines.Line2D([], [], **ARM_STYLE[k]) for k in ("Incentive", "Control")]
            top.legend(handles, ["Incentive", "Control"], loc="upper right", borderaxespad=0.2)
    axes[1, 1].sharey(axes[1, 0])
    axes[0, 1].sharey(axes[0, 0])
    fig.align_ylabels(axes[:, 0])
    fig.tight_layout(pad=0.3, w_pad=0.8, h_pad=0.6)
    return fig


EXAMS = {-1: "Midterm 1", 3: "Midterm 2", 6: "Final"}


def fig_weekly(weekly: pd.DataFrame):
    """`tscombo`. Weekly means by arm; students who took the final (as in Stata)."""
    d = weekly.loc[weekly["finalscore"].notnull()].copy()
    d["hours"] = d["duration"] / 3600
    m = d.groupby(["arm", "weekoy"])[["videos", "videosu", "hours"]].mean().reset_index()
    rows = [
        ("A. Videos watched per week", "videos", "Videos"),
        ("B. Unique videos watched per week", "videosu", "Unique videos"),
        ("C. Time spent watching per week", "hours", "Hours"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(4.6, 5.0), sharex=True)
    for i, (ax, (title, var, ylab)) in enumerate(zip(axes, rows)):
        for wk in EXAMS:
            ax.axvline(wk, **REF, zorder=1)
        for arm in (0, 1, 2):
            g = m[m.arm == arm]
            ax.plot(g.weekoy, g[var], **ARM_STYLE[ARM_NAME[arm]], zorder=3)
        ax.set_title(title)
        ax.set_ylabel(ylab)
        ax.set_ylim(bottom=0)
        ax.margins(x=0.01)
        _grid(ax)
        if i == 0:
            top = ax.get_ylim()[1] * 1.02
            for wk, lab in EXAMS.items():
                ax.text(wk + 0.12, top, lab, fontsize=8, va="top", ha="left")
            handles = [
                mpl.lines.Line2D([], [], **ARM_STYLE[k])
                for k in ("Incentive", "Control", "Above median")
            ]
            ax.legend(
                handles,
                ["Incentive", "Control", "Above median"],
                loc="center left",
                bbox_to_anchor=(0.0, 0.70),
                borderaxespad=0.2,
            )
    axes[-1].set_xticks(range(-4, 8))
    axes[-1].set_xlabel("Weeks since experiment began")
    fig.align_ylabels(axes)
    fig.tight_layout(pad=0.3, h_pad=0.5)
    return fig


def fig_incentive_hist(df: pd.DataFrame):
    """`hist_v_incent`. Distribution of incentive-eligible unique videos by arm,
    students who took the final. Small multiples instead of overlaid translucent bars."""
    d = df.loc[df["finalscore"].notnull() & df["arm"].isin([1, 2])]
    fig, axes = plt.subplots(2, 1, figsize=(5.0, 3.6), sharex=True, sharey=True)
    bins = np.arange(-0.5, 49.5, 1)
    for ax, arm in zip(axes, (1, 2)):
        v = d.loc[d.arm == arm, "videos_incent_counts_u"]
        ax.hist(v, bins=bins, color="0.35", edgecolor="white", linewidth=0.4, zorder=2)
        ax.axvline(39.5, **REF, zorder=3)
        ax.set_title(f"{'AB'[arm - 1]}. {ARM_NAME[arm]}")
        ax.set_ylabel("Students")
        _grid(ax)
    axes[-1].set_xlim(-0.8, 48.8)
    axes[-1].set_xticks([0, 10, 20, 30, 40, 48])
    axes[-1].set_xlabel("Incentive-eligible unique videos watched")
    fig.tight_layout(pad=0.3, h_pad=0.6)
    return fig


def _dumbbells(ax, x, c, t):
    ax.vlines(x, c * 100, t * 100, color="0.55", lw=0.6, zorder=2)
    ax.plot(x, c * 100, **DOT["Control"], zorder=3)
    ax.plot(x, t * 100, **DOT["Incentive"], zorder=4)


def _dot_legend(ax, loc="upper left", **kw):
    h = [mpl.lines.Line2D([], [], **DOT[k]) for k in ("Incentive", "Control")]
    ax.legend(h, ["Incentive", "Control"], loc=loc, handlelength=1, **kw)


def fig_watch_rates_by_incentive(vids: pd.DataFrame):
    """`bar_uviews`. Share of each arm opening each video; videos sorted by the
    Control rate within incentivized / non-incentivized groups. Dumbbells replace paired bars."""
    groups = [(0, "A. Not incentivized"), (1, "B. Incentivized")]
    sizes = [int((vids.incent == g).sum()) for g, _ in groups]
    fig, axes = plt.subplots(
        1, 2, figsize=(5.0, 3.0), sharey=True, gridspec_kw=dict(width_ratios=sizes)
    )
    for ax, (g, title) in zip(axes, groups):
        s = vids[vids.incent == g].sort_values("control").reset_index(drop=True)
        x = np.arange(1, len(s) + 1)
        _dumbbells(ax, x, s.control, s.incentive)
        ax.set_title(title)
        ax.set_xlim(0, len(s) + 1)
        ax.set_xticks([])
        _grid(ax)
    axes[0].set_ylim(0, 102)
    axes[0].set_ylabel("Students who watched video")
    _dot_legend(axes[0])
    fig.supxlabel("Videos, by Control watch rate", fontsize=9, fontweight="bold")
    fig.tight_layout(pad=0.3, w_pad=0.6)
    return fig


def fig_watch_rates_by_week(vids: pd.DataFrame):
    """`bar_uviews_week`. As bar_uviews, grouped by syllabus week; videos within a week are
    sorted by Control rate. Alternate weeks are shaded."""
    s = vids.sort_values(["week", "control"]).reset_index(drop=True)
    gap = 1.5
    xs, centers, spans = [], {}, {}
    pos = 0.0
    for wk, g in s.groupby("week", sort=True):
        start = pos + 1
        idx = np.arange(len(g)) + start
        xs.extend(idx)
        centers[wk] = idx.mean()
        spans[wk] = (idx[0] - gap / 2, idx[-1] + gap / 2)
        pos = idx[-1] + gap
    s["x"] = xs
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    for k, (wk, (a, b)) in enumerate(spans.items()):
        if k % 2 == 1:
            ax.axvspan(a, b, color=SHADE, lw=0, zorder=0)
    _dumbbells(ax, s.x.to_numpy(), s.control, s.incentive)
    ax.set_xticks(list(centers.values()))
    ax.set_xticklabels(list(centers.keys()))
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(min(a for a, _ in spans.values()), max(b for _, b in spans.values()))
    ax.set_ylim(0, 102)
    ax.set_xlabel("Week of quarter (syllabus)")
    ax.set_ylabel("Students who watched video")
    ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    _dot_legend(ax, loc="upper left")
    fig.tight_layout(pad=0.3)
    return fig


def fig_watch_rates_by_duration(vids: pd.DataFrame):
    """`bar_uviews_duration`. Watch rate against video runtime. Replaces bars
    ordered by duration (whose x-axis was mislabeled "Week of quarter") with runtime on x."""
    groups = [(0, "A. Not incentivized"), (1, "B. Incentivized")]
    fig, axes = plt.subplots(1, 2, figsize=(5.0, 3.0), sharey=True, sharex=True)
    for ax, (g, title) in zip(axes, groups):
        s = vids[vids.incent == g]
        _dumbbells(ax, s.duration_min.to_numpy(), s.control, s.incentive)
        ax.set_title(title)
        ax.set_xlabel("Video runtime (minutes)")
        _grid(ax)
    axes[0].set_ylim(0, 102)
    axes[0].set_xlim(0, 30)
    axes[0].set_ylabel("Students who watched video")
    _dot_legend(axes[0], loc="upper left")
    fig.tight_layout(pad=0.3, w_pad=0.8)
    return fig


def fig_local_linear(df: pd.DataFrame, exam: str, h: float = 0.9):
    """`lpolymid2`, `lpolyfinal`. Local linear fits of unique videos (top) and exam
    score (bottom) on midterm 1 score, by arm. Left: all students who took the exam; right:
    drops students whose matched pair attrited (keeps all Above median students, who are
    pooled with Control as in Stata). Midterm 1 restricted to [-3, 2] Control SDs.

    Deviations from Stata: (i) both arms use the triangle kernel with h = 0.9 (Stata applied
    these only to Control; Incentive got lpoly defaults); (ii) the midterm 2 figure uses
    students who took midterm 2 (Stata conditioned on the final, contrary to the note);
    (iii) robust pointwise bands (see local_linear)."""
    vids_var = {"mid2": "videos_mid2_u", "final": "videos_final_u"}[exam]
    score = {"mid2": "mid2scorestd", "final": "finalscorestd"}[exam]
    score_lab = {"mid2": "Midterm 2 score", "final": "Final exam score"}[exam]
    pairs = {"mid2": "bothpairs_mid2", "final": "bothpairs_final"}[exam]
    d = df.loc[df[score].notnull() & df["mid1scorestd"].between(-3, 2)].copy()
    d["arm2"] = np.where(d["arm"] == 2, 2, 1)
    samples = [
        ("All students", d),
        ("Matched pairs", d[(d[pairs] == 1) | (d["mid1scorestd"] > 0)]),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.4), sharex=True, sharey="row")
    for j, (name, s) in enumerate(samples):
        for i, (yvar, ylab) in enumerate([(vids_var, "Unique videos"), (score, score_lab)]):
            ax = axes[i, j]
            fits = {}
            for arm in (2, 1):
                g = s[s.arm2 == arm]
                grid = np.linspace(g.mid1scorestd.min(), g.mid1scorestd.max(), 100)
                fits[arm] = (grid, *local_linear(g.mid1scorestd, g[yvar], grid, h))
            grid, f, lo, hi = fits[2]
            ax.fill_between(grid, lo, hi, color=BAND, lw=0, zorder=1)
            grid1, f1, lo1, hi1 = fits[1]
            for b in (lo1, hi1):
                ax.plot(grid1, b, color=INK, lw=0.5, ls=(0, (1, 1.2)), zorder=2)
            ax.plot(grid1, f1, **ARM_STYLE["Control"], zorder=3)
            ax.plot(grid, f, **ARM_STYLE["Incentive"], zorder=4)
            ax.axvline(0, **REF, zorder=0)
            _grid(ax)
            if i == 0:
                ax.set_title(f"{'AB'[j]}. {name}")
            if j == 0:
                ax.set_ylabel(ylab)
            if i == 1:
                ax.set_xlabel("Midterm 1 score")
    axes[0, 0].set_ylim(0, 65 if exam == "mid2" else 80)
    axes[1, 0].set_ylim(-2, 3)
    axes[1, 0].set_xticks(range(-3, 3))
    handles = [mpl.lines.Line2D([], [], **ARM_STYLE[k]) for k in ("Incentive", "Control")]
    axes[0, 0].legend(
        handles, ["Incentive", "Control"], loc="upper right", borderaxespad=0.2
    )
    fig.align_ylabels(axes[:, 0])
    fig.tight_layout(pad=0.3, w_pad=0.6, h_pad=0.6)
    return fig


def fig_max_week(weekly: pd.DataFrame):
    """`hist_maxweek`. Histograms (width-2 bins, as in Stata) of each student's most videos
    opened in one week: Control as light gray bars, Incentive as a black outline (EPS has no
    transparency, so the two are not drawn as translucent fills). Same four measures as Stata.
    Students who took the final, Incentive and Control only."""
    d = weekly.loc[weekly["finalscore"].notnull() & weekly["arm"].isin([1, 2])]
    keys = ["id", "year", "arm"]
    measures = [
        ("A. Videos, any week", d.groupby(keys)["videos"].max()),
        ("B. Unique videos, any week", d.groupby(keys)["videosu"].max()),
        ("C. Videos, before midterm 2", d[d.weekoy.between(0, 3)].groupby(keys)["videos"].max()),
        ("D. Videos, after midterm 2", d[d.weekoy >= 4].groupby(keys)["videos"].max()),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.2))
    for ax, (title, s) in zip(axes.flat, measures):
        s = s.reset_index()
        v = s.iloc[:, -1]
        bins = np.arange(0, v.max() + 3, 2)
        ax.hist(v[s.arm == 1], bins=bins, color=HIST_CONTROL, edgecolor="white", linewidth=0.3,
                zorder=2)
        ax.hist(v[s.arm == 2], bins=bins, histtype="step", color=INK, linewidth=1.1, zorder=3)
        ax.set_title(title)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
        _grid(ax)
    for ax in axes[:, 0]:
        ax.set_ylabel("Students")
    for ax in axes[1, :]:
        ax.set_xlabel("Most videos watched in one week")
    handles = [
        mpl.lines.Line2D([], [], color=INK, lw=1.1),
        mpl.patches.Patch(facecolor=HIST_CONTROL, edgecolor="none"),
    ]
    axes[0, 0].legend(handles, ["Incentive", "Control"], loc="upper right")
    fig.tight_layout(pad=0.3, w_pad=0.8, h_pad=0.8)
    return fig
