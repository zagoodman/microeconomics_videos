version 17
do "scripts/stata/_setup.do"

load_analysis_data
add_microb_exams

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str99 ctrls str32 model

foreach exam of global itt_exams {
    local outcomes ${outcomes_`exam'}
    foreach y of local outcomes {
        quietly pds_itt `y' `exam'
    }
}

frame results: export delimited "data/generated/pds_coeffs.csv", replace
