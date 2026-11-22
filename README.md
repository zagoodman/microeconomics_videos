# microeconomics_videos

This repository contains replication materials for *The Effect of Supplementary Videos on University Educational Outcomes* by [M. Famulari](https://econweb.ucsd.edu/~mfamular/index.html) and [Z. Goodman](http://zagoodman.com).

## Experiment Overview

The purpose of the experiment is to estimate the effectiveness of the Intermediate Microeconomics Video Handbook (IMVH) on learning outcomes in the first intermediate microeconomics course at UC San Diego. The course is taken by about 400 students per fall quarter. 

Of note, the design of the experiment includes randomizing students who scored below a sharp cutoff into treatment and control, allowing us to estimate two local average treatment effects (LATE):
1. The LATE for students who scored below the cutoff
2. The LATE for students who scored at the cutoff

## Preview of findings

1. The incentive (requiring the videos as part of the students' grade) induced substantial takeup of the videos.
2. Treatment significantly increased student test scores on both exams following the start of the experiment.
3. Treated students continue to watch videos more frequently than their control peers during the second course in the sequence.

## Repository details

We are unable to post the data used because of privacy restrictions. The replication pipeline is split into two stages:

* `construction/` — builds the analysis datasets in `data/generated/` from raw registrar and video logs in `data/raw/`:
  * `construction/assemble_data.py`
* `analysis/` — reads only `data/generated/` and produces all estimates, tables, and figures:
  * `analysis/stata/run_all.do` — statistical analysis (Stata 17)
  * `analysis/r/semenova_bounds.R` — generalized Lee bounds (R)
  * `analysis/python/make_tables.py` — LaTeX table generation (main and referee tables)
  * `analysis/python/make_figures.py` — JEE print-style figures

## More information

* [Description of IMVH](https://economics.ucsd.edu/undergraduate-program/video-handbooks/index.html)
* [CAMSEE Research Plan](https://camsee.ucsd.edu/_files/170886_2019_07_08_Revised_Research_Plan_clean.pdf)

## Environment setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
1. Install Python dependencies: `uv sync`
1. Install Stata 17 (for `analysis/stata/`) and R (for `analysis/r/semenova_bounds.R`)
1. Download raw data into `data/raw/` (or place the assembled datasets in `data/generated/` to start at `analysis/`)
1. Run the replication scripts:
   - `uv run python construction/assemble_data.py`
   - `stata -b do analysis/stata/run_all.do`
   - `uv run python analysis/python/make_tables.py`
   - `uv run python analysis/python/make_figures.py`

## LaTeX setup

Install BasicTeX (macOS):

```bash
brew install --cask basictex
```

Restart your terminal, then install required packages:

```bash
sudo tlmgr update --self
sudo tlmgr install scalerel doublestroke cmathbb placeins preprint threeparttable threeparttablex multirow csquotes epigraph biblatex biber biblatex-apa environ nextpage xstring
```

## Compiling the paper

```bash
./tex/build.sh
```
