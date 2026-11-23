"""Paper figures (JEE print style).

The nine figures in the paper. Style and data definitions live in ``modules/figures.py``.

Inputs (``data/generated/``): ``figure_sample.csv`` (student-level sample exported by
``analysis/stata/figure_data.do``), plus ``weekly_video_panel.csv`` and ``video_watch_rates.csv``
(from ``construction/assemble_data.py``).

JEE style sheet: black and white with arms distinguished by line pattern/weight, Times New Roman
bold 8-10 pt, at most 5 x 5 in, EPS/TIFF/JPEG at 600 dpi or more.

Outputs:
- ``tex/plots/<name>.pdf`` -- vector PDF used by the LaTeX build
- ``tex/plots/jee/<name>.eps``, ``tex/plots/jee/<name>.tif`` -- submission files (TIFF is 600 dpi grayscale)

Encoding used throughout: Incentive = thick solid line / filled circle; Control = thin
dashed line / open circle; Above median = gray dotted line. 95% CIs are gray bands.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from modules import figures as F

ROOT = Path(__file__).resolve().parents[2]
DATA_GEN = str(ROOT / "data" / "generated")
PLOTS = str(ROOT / "tex" / "plots")

F.use_style()

# Data

df = pd.read_csv(f"{DATA_GEN}/figure_sample.csv", dtype={"id": str})
weekly = pd.read_csv(f"{DATA_GEN}/weekly_video_panel.csv", dtype={"id": str})
vids = pd.read_csv(f"{DATA_GEN}/video_watch_rates.csv")
print(df.groupby("arm").size().rename(F.ARM_NAME))
print(f"{len(vids)} videos ({vids.incent.sum()} incentivized)")


def _save(fig, name):
    F.save(fig, name, PLOTS)
    plt.close(fig)


# Effect of the incentive on videos watched (combo_cdf)
_save(F.fig_videos_survival(df), "combo_cdf")

# Weekly video watching by arm (tscombo)
_save(F.fig_weekly(weekly), "tscombo")

# Videos counted toward the incentive (hist_v_incent)
_save(F.fig_incentive_hist(df), "hist_v_incent")

# Per-video watch rates (bar_uviews, bar_uviews_week, bar_uviews_duration)
_save(F.fig_watch_rates_by_incentive(vids), "bar_uviews")
_save(F.fig_watch_rates_by_week(vids), "bar_uviews_week")
_save(F.fig_watch_rates_by_duration(vids), "bar_uviews_duration")

# Effects along midterm 1 score (lpolymid2, lpolyfinal)
_save(F.fig_local_linear(df, "mid2"), "lpolymid2")
_save(F.fig_local_linear(df, "final"), "lpolyfinal")

# Most videos watched in one week (hist_maxweek)
_save(F.fig_max_week(weekly), "hist_maxweek")
