# microeconomics_videos

This repository contains replication materials for *The Effects of Incentivizing Video Watching: A Field Experiment in Intermediate Microeconomics* by [M. Famulari](https://econweb.ucsd.edu/~mfamular/index.html) and [Z. Goodman](https://zgoodman.com).

## Experiment Overview

The purpose of the experiment is to estimate the effect of a small grade incentive to watch the Intermediate Microeconomics Video Handbook (IMVH) on learning outcomes in the first intermediate microeconomics course at UC San Diego. The course is taken by about 400 students per fall quarter.

## Preview of findings

1. The incentive induced substantial take-up of the videos.
2. Treatment increased scores on the second midterm and final exam by about 0.18 standard deviations.
3. There is suggestive evidence that treated students continued watching videos more in the next course in the sequence.

## Repository details

We are unable to post the data used because of privacy restrictions. The replication pipeline is split into two stages:

* `construction/` — builds the analysis datasets in `data/generated/` from raw registrar and video logs in `data/raw/`:
  * `construction/assemble_data.py`
* `analysis/` — reads only `data/generated/` and produces all estimates, tables, and figures:
  * `analysis/stata/run_all.do` — all estimation (Stata 17); also exports the student-level figure sample
  * `analysis/r/semenova_bounds.R` — generalized Lee bounds (R)
  * `analysis/python/make_tables.py` — LaTeX table generation (main and referee tables)
  * `analysis/python/make_figures.py` — JEE print-style figures (plotting only; no estimation)

## More information

* [Description of IMVH](https://economics.ucsd.edu/undergraduate-program/resources/video-handbooks/index.html)
* The experiment was approved by the UC San Diego Human Research Protections Program (IRB #170886) for both the 2018 and 2019 cohorts.

## Environment setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
1. Install Python dependencies: `uv sync`
1. Install Stata 17 (for `analysis/stata/`) and R (for `analysis/r/semenova_bounds.R`)
1. Download raw data into `data/raw/` (or place the assembled datasets in `data/generated/` to start at `analysis/`)
1. Run the replication scripts:
   - `uv run python construction/assemble_data.py`
   - `stata -b do analysis/stata/run_all.do`
   - `Rscript analysis/r/semenova_bounds.R <path-to-leebounds-repo>`
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
