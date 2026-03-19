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

We are unable to post the data used because of privacy restrictions. However, the repository contains the output from our Jupyter Notebooks:
* [Data prep](https://nbviewer.jupyter.org/github/zagoodman/microeconomics_videos/blob/master/jupyter/assemble_data.ipynb)
* [Data analysis](https://nbviewer.jupyter.org/github/zagoodman/microeconomics_videos/blob/master/jupyter/assemble_data.ipynb)

## More information

* [Description of IMVH](https://economics.ucsd.edu/undergraduate-program/video-handbooks/index.html)
* [CAMSEE Research Plan](https://camsee.ucsd.edu/_files/170886_2019_07_08_Revised_Research_Plan_clean.pdf)

## Environment setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
1. Install dependencies: `uv sync`
1. Register the Stata kernel: `uv run python -m stata_kernel.install`
1. Verify `stata_path` in `~/.stata_kernel.conf` points to your Stata executable (e.g. `/Applications/Stata/StataSE.app/Contents/MacOS/stata-se`)
1. Download data (from Drive folder) and add to /data directory
1. Run notebooks: `uv run jupyter lab`

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
