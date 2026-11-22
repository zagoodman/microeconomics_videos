version 17
do "analysis/stata/_setup.do"

load_analysis_data
replace prev_cumgpa = . if prev_cumgpa_unobs

local balance_vars mid1scorestd y2019 ///
    prev_cumgpa prev_cumgpa_unobs mathquizstd pset_pre ///
    videos_mid1 videos_mid1_u duration_mid1 duration_mid1_u ///
    asian latx white othereth female male transfer

capture frame drop results
frame create results str32 depvar arm str32 exam bothpairs mean stderr N

foreach exam in mid2 final {
    preserve
    keep if !missing(assigned_grade)
    post_balance `balance_vars', exam(`exam') sample(-1) arms(0/2)
    keep if !missing(`exam'score)
    post_balance `balance_vars', exam(`exam') sample(0) arms(0/2)
    keep if bothpairs_`exam'
    post_balance `balance_vars', exam(`exam') sample(1) arms(1/2)
    restore
}

frame results: export delimited "data/generated/balance_table_data.csv", replace
