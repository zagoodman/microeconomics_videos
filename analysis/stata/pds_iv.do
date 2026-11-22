version 17
do "analysis/stata/_setup.do"

load_analysis_data

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str99 ctrls str32 model

foreach exam in mid2 final {
    quietly pds_iv `exam'scorestd `exam'
}

frame results: export delimited "data/generated/pds_iv_coeffs.csv", replace
