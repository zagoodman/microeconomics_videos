* Student-level sample for the paper figures (read by analysis/python/make_figures.py).
version 17
do "analysis/stata/_setup.do"

load_analysis_data

keep id year arm mid1scorestd mid2score finalscore mid2scorestd finalscorestd ///
    videos_mid2_u videos_final_u videos_incent_counts_u bothpairs_mid2 bothpairs_final
export delimited using "data/generated/figure_sample.csv", nolabel replace
