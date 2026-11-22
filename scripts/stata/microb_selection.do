* Inputs for the Micro B selection corrections: the sample for the generalized Lee
* bounds (scripts/r/semenova_bounds.R) and IPW estimates.
version 17
do "scripts/stata/_setup.do"

local outcomes videos_b videos_b_u duration_b duration_b_u mid1_100bstd mid2_100bstd final_100bstd
local selection_x mid1scorestd mathquizstd mathquiz_unobs transfer ///
    prev_cumgpa prev_cumgpa_unobs female asian latx white

load_analysis_data
keep if !missing(assigned_grade) & arm > 0

export delimited treated took100b y2019 `outcomes' `selection_x' ///
    using "data/generated/semenova_sample.csv", replace

* Logit propensity score, 1st/99th-percentile winsorized IPW, and weighted OLS
* wrapped in one program so bootstrap accounts for propensity-score estimation
* and winsorization.
capture program drop _ipw_microb
program define _ipw_microb, rclass
    version 17
    syntax, outcomes(namelist) selection_x(namelist)
    tempvar phat ipw
    quietly logit took100b treated `selection_x' y2019
    quietly predict double `phat', pr
    quietly generate double `ipw' = 1 / `phat' if took100b == 1
    quietly _pctile `ipw' if took100b == 1, p(1 99)
    local lo = r(r1)
    local hi = r(r2)
    quietly replace `ipw' = `lo' if took100b == 1 & `ipw' < `lo'
    quietly replace `ipw' = `hi' if took100b == 1 & !missing(`ipw') & `ipw' > `hi'
    foreach y of local outcomes {
        quietly regress `y' treated mid1scorestd y2019 [pweight = `ipw'] if took100b == 1
        return scalar b_`y' = _b[treated]
    }
    ereturn clear
end

local boot_exp
foreach y of local outcomes {
    local boot_exp `boot_exp' b_`y'=r(b_`y')
}
bootstrap `boot_exp', reps(1000) seed(20192): ///
    _ipw_microb, outcomes(`outcomes') selection_x(`selection_x')

capture frame drop ipw_results
frame create ipw_results str32 depvar meanctrl treatbeta stderr N str32 model

foreach y of local outcomes {
    quietly summarize `y' if took100b == 1 & arm == 1
    local meanctrl = r(mean)
    quietly count if took100b == 1 & !missing(`y')
    local N = r(N)
    frame post ipw_results ("`y'") (`meanctrl') (_b[b_`y']) (_se[b_`y']) (`N') ("ipw")
}

frame ipw_results: export delimited "data/generated/ipw_100b.csv", replace
