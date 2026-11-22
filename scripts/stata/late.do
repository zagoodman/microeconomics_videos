version 17
do "scripts/stata/_setup.do"

load_analysis_data

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str32 model

foreach exam in mid2 final {
    quietly late_2sls `exam'scorestd `exam'
    quietly neyman_late `exam'scorestd `exam'
}

frame results: export delimited "data/generated/lates_coeffs.csv", replace
