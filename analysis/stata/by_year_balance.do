* Attrition, balance, and exam score summary statistics by year.
version 17
do "analysis/stata/_setup.do"

load_analysis_data

* ---------------------------------------------------------------------------
* 1. Attrition by year (pooled, 2018, 2019)
* ---------------------------------------------------------------------------
capture frame drop attr_results
frame create attr_results str8 sample str8 arm assigned consented observed_status ///
    took_mid2 took_final took_100b

* Pre-anonymization assigned counts for randomized arms = sum of max(pair) per year.
local pooled_assigned_1 = 0
local pooled_assigned_2 = 0
foreach yr in 2018 2019 {
    forvalues a = 1/2 {
        quietly summarize pair if year == `yr' & arm == `a', meanonly
        local pooled_assigned_`a' = `pooled_assigned_`a'' + r(max)
    }
}

foreach sample in pooled 2018 2019 {
    preserve
    if "`sample'" != "pooled" keep if year == `sample'

    forvalues a = 0/2 {
        if `a' == 0 {
            local assigned = .
        }
        else if "`sample'" == "pooled" {
            local assigned = `pooled_assigned_`a''
        }
        else {
            quietly summarize pair if arm == `a', meanonly
            local assigned = r(max)
        }
        quietly count if arm == `a'
        local consented = r(N)
        quietly count if arm == `a' & !missing(assigned_grade)
        local observed = r(N)
        quietly count if arm == `a' & !missing(assigned_grade) & !missing(mid2score)
        local took_mid2 = r(N)
        quietly count if arm == `a' & !missing(assigned_grade) & !missing(finalscore)
        local took_final = r(N)
        quietly count if arm == `a' & !missing(assigned_grade) & took100b == 1
        local took_100b = r(N)
        frame post attr_results ("`sample'") ("`a'") (`assigned') (`consented') ///
            (`observed') (`took_mid2') (`took_final') (`took_100b')
    }

    keep if !missing(assigned_grade) & arm > 0
    generate byte attrit_mid2 = missing(mid2score)
    generate byte attrit_final = missing(finalscore)
    generate byte attrit_100b = took100b == 0
    foreach k in mid2 final 100b {
        quietly ttest attrit_`k', by(arm) unequal
        local p_`k' = r(p)
    }
    frame post attr_results ("`sample'") ("pvalue") (.) (.) (.) (`p_mid2') (`p_final') (`p_100b')
    restore
}

frame attr_results: export delimited "data/generated/attrition_by_year.csv", replace

* ---------------------------------------------------------------------------
* 2. Balance by year
* ---------------------------------------------------------------------------
replace prev_cumgpa = . if prev_cumgpa_unobs

local balance_vars mid1scorestd y2019 ///
    prev_cumgpa prev_cumgpa_unobs mathquizstd pset_pre ///
    videos_mid1 videos_mid1_u duration_mid1 duration_mid1_u ///
    asian latx white othereth female male transfer

capture frame drop bal_results
frame create bal_results str32 depvar arm str32 exam bothpairs mean stderr N pvalue year

foreach yr in 2018 2019 {
    foreach exam in mid2 final {
        preserve
        keep if year == `yr' & !missing(assigned_grade)
        post_balance `balance_vars', exam(`exam') sample(-1) arms(0/2) frame(bal_results) year(`yr')
        keep if !missing(`exam'score)
        post_balance `balance_vars', exam(`exam') sample(0) arms(0/2) frame(bal_results) year(`yr')
        keep if bothpairs_`exam'
        post_balance `balance_vars', exam(`exam') sample(1) arms(1/2) frame(bal_results) year(`yr')
        restore
    }
}

frame bal_results: export delimited "data/generated/balance_table_data_by_year.csv", replace

* ---------------------------------------------------------------------------
* 3. Exam score summary statistics by year (percent of points possible)
* ---------------------------------------------------------------------------
capture frame drop exam_results
frame create exam_results year str16 group str16 exam N mean median sd

foreach yr in 2018 2019 {
    foreach gspec in `"All students|1"' `"Above median|arm == 0"' `"Control|arm == 1"' `"Incentive|arm == 2"' {
        gettoken gname gcond : gspec, parse("|")
        local gcond = substr("`gcond'", 2, .)
        foreach espec in `"mid1score|Midterm 1"' `"mid2score|Midterm 2"' `"finalscore|Final exam"' {
            gettoken col ename : espec, parse("|")
            local ename = substr("`ename'", 2, .)
            quietly summarize `col' if year == `yr' & (`gcond'), detail
            frame post exam_results (`yr') ("`gname'") ("`ename'") ///
                (r(N)) (r(mean) * 100) (r(p50) * 100) (r(sd) * 100)
        }
    }
}

frame exam_results: export delimited "data/generated/exam_stats_by_year.csv", replace
