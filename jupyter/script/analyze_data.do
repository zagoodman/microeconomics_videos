* Set working directory to base directory
* cd "C:\Users\Zack\Documents\GitHub\microeconomics_videos"
cd "/Users/zack/github/microeconomics_videos"

* set more off to show all output
set more off

* check that everything is up to date and installed
* run 'ssc install {package_name}' for any missing packages

*ado update, update // run this if you need to update packages

version
which avar
which binsreg // net install binsreg, from(https://raw.githubusercontent.com/nppackages/binsreg/master/stata)
which binscatter2 // net install binscatter2, from("https://raw.githubusercontent.com/mdroste/stata-binscatter2/master/")
which ereplace
which estout
which ftools
which grqreg
which gtools
which ivreg2
which lpdensity // net install lpdensity, from(https://raw.githubusercontent.com/nppackages/lpdensity/master/stata)
which mhtreg
// which moremata // not checkable but necessary
which pdslasso
which ranktest
which rddensity // net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata)
which rdrobust
which ritest
which rlasso // ssc install lassopack
which unique
which weakiv
which weakivtest


global ctrl_vars mathquizstd mathquiz_unobs videos_mid1_u duration_mid1_u pset_pre ///
    transfer prev_cumgpa prev_cumgpa_unobs female ///
    asian latx white

// sum $ctrl_vars

* Data prep functions

foreach v in clean_data get_idyearlevel merge_winter_gpa ///
    merge_dem clean_dem get_std_units {
    capture program drop `v'
}

* define data clean function common to all dfs
program clean_data
    capture drop arm
    gen arm = treated + toberandomized
    drop toberandomized
    drop if mi(mid1score) // did not start experiment
    label define arm 0 "Above median" 1 "Control" 2 "Treated"
    label values arm arm
    capture drop y2019
    gen y2019 = year == 2019
    capture drop bothpairs
    gen pairyear = year * 1000 + pair
    sort pair year
    foreach v in assigned_grade mid2score finalscore {
        gen bothpairs_`v' = !mi(`v')
        by pair year: ereplace bothpairs_`v' = sum(bothpairs_`v')
        replace bothpairs_`v' = bothpairs_`v' >= 2
    }
    rename (bothpairs_mid2 bothpairs_final) (bothpairs_mid2 bothpairs_final)
    gen mathquiz_unobs = mi(mathquiz)
    replace mathquiz = 0 if mi(mathquiz)
    end

* define function that loads student-year level data
program get_idyearlevel
    import delimited ./data/generated/student_analysis_sample.csv, clear varnames(1)
    clean_data
    end

* merge gpa/units/class data from subsequent quarter
program merge_winter_gpa
    preserve
    import delimited ./data/generated/student_demographics_winter.csv, clear varnames(1)
    local renamevars units_letter units_pnp units_w ///
        gpa_letter gpa_letter_sansecon gpa_letter_sans100a gpa_econ_sans100a ///
        nclass_letter nclass_np nclass_pnp nclass_p nclass_w
    keep id year `renamevars' 
    foreach v in `renamevars' {
        rename `v' winter_`v'
    }
    tempfile temp
    save `temp'
    restore
    merge 1:1 id year using `temp', nogen
    end

* merge demographic data
program merge_dem
    preserve
    import delimited ./data/generated/student_demographics_fall.csv, clear varnames(1)
    tempfile temp
    save `temp'
    restore
    merge 1:1 id year using `temp', nogen
    end

* get demographic vars into binary form
program clean_dem
    capture drop male female othergen ///
        chinese latx oasian viet white othereth 
    * gender
    gen male = gender == "m"
    gen female = gender == "f"
    gen othergen = gender == "u"
    * ethnicity
    gen chinese = ethnicity == "Chinese/Chinese-American"
    gen latx = ethnicity == "Chicanx/Latinx"
    gen oasian = ethnicity == "All Other Asian/Asian-American"
    gen viet = ethnicity == "Vietnamese"
    gen white = ethnicity == "White/Caucasian"
    gen othereth = !mi(ethnicity) & !(chinese | latx | oasian | viet | white)
    gen asian = chinese + oasian + viet
    * prev cumulative gpa
    gen prev_cumgpa_unobs = mi(prev_cumgpa)
    replace prev_cumgpa = 0 if mi(prev_cumgpa) // prev_cumgpa is interaction of obs * gpa
    * whether pass 100A
    capture drop pass
    gen pass = inlist(substr(assigned_grade, 1, 1), "A", "B", "C", "P")
    replace pass = . if mi(finalscore)
    * whether pass 100B
    capture drop pass100b
    gen pass100b = inlist(substr(lettergrade_100b, 1, 1), "A", "B", "C") if !mi(lettergrade_100b)
    * whether take 100A for letter
    capture drop letter_option
    gen letter_option = inlist(substr(assigned_grade, 1, 1), "A", "B", "C", "D", "F")
    replace letter_option = . if mi(finalscore)
    * sum of attendance
    capture drop attendance
    gen attendance = attend1 + attend2 + attend3 + attend4 + attend5 + attend6 + attend7
    * nclass_np
    foreach p in "winter_" "" {
        capture drop `p'nclass_np
        gen `p'tot_class = `p'nclass_letter + `p'nclass_pnp + `p'nclass_w
        gen `p'nclass_np = `p'tot_class - `p'nclass_p - `p'nclass_w // where are incompletes counted?
        gen `p'pclass_letter = `p'nclass_letter / (`p'nclass_letter + `p'nclass_pnp)
        gen `p'pclass_pnp = `p'nclass_pnp / (`p'nclass_letter + `p'nclass_pnp)
    }
    end

* get score variables into standard deviation units
* normalize by the median score in each year
program get_std_units
    *** return std units for 100A vars
    capture drop mid1scorestd
    gen mid1scorestd = .
    forvalues y = 2018/2019 {
        qui sum mid1score if year == `y' & arm >= 1
        local maxscore = r(max)
        qui sum mid1score if year == `y' & arm == 1
        replace mid1scorestd = (mid1score - `maxscore') / r(sd) if year == `y'
    }
    
    local oldvars "mathquiz mid2score finalscore"
    foreach v in `oldvars' {
        capture drop `v'std
        gen `v'std = .
        forvalues y = 2018/2019 {
            qui sum `v' if year == `y' & arm == 1
            replace `v'std = (`v' - r(mean)) / r(sd) if year == `y'
        }
    }

    *** return std units for 100B vars if they exist
    capture confirm variable mid1_100b
    if !_rc {
        local oldvars "mid1_100b mid2_100b final_100b"
        foreach v in `oldvars' {
            capture drop `v'std
            gen `v'std = .
            forvalues y = 2018/2019 {
            qui sum `v' if year == `y' & arm == 1
            replace `v'std = (`v' - r(mean)) / r(sd) if year == `y'
            }
        }
    }
    end

* Label variables

capture program drop label_vars

* label vars

program label_vars
    capture label var mathquizstd "Math Quiz score"
    capture label var mid1scorestd "Midterm 1 score"
    capture label var mid2scorestd "Midterm 2 score"
    capture label var finalscorestd "Final exam score"
    capture label var treated "Treated"
    capture label var mid1_100bstd "100B Midterm 1 score"
    capture label var mid2_100bstd "100B Midterm 2 score"
    capture label var final_100bstd "100B Final score"
    capture label var duration_mid1 "Duration, videos before mid1"
    capture label var duration_mid2 "Duration, videos before mid2"
    capture label var duration_final "Duration, videos before final"
    capture label var duration_mid1_u "Duration, unique videos before mid1"
    capture label var duration_mid2_u "Duration, unique videos before mid2"
    capture label var duration_final_u "Duration, unique videos before final"
    capture label var videos_mid1 "Num. videos before mid1"
    capture label var videos_mid2 "Num. videos before mid2"
    capture label var videos_final "Num. videos before final"
    capture label var videos_mid1_u "Num. unique videos before mid1"
    capture label var videos_mid2_u "Num. unique videos before mid2"
    capture label var videos_final_u "Num. unique videos before final"
    capture label var pset_pre "PSET"
    capture label var transfer "Transfer Student"
    capture label var prev_cumgpa "Prev. GPA"
    capture label var male "Male"
    capture label var female "Female"
    capture label var othergen "Other gender/not spec."
    capture label var asian "Asian"
    capture label var chinese "Chinese"
    capture label var latx "Latinx"
    capture label var viet "Vietnamese"
    capture label var oasian "Other Asian"
    capture label var latx "Latinx"
    capture label var white "White"
    capture label var othereth "Other ethnicity/not spec."
    end

* set scheme to one with white background

set scheme s1color


* plotting and export functions

capture program drop export_img

program export_img
    args name
    graph export "./tex/plots/`name'.pdf", name(`name') replace
    end

* get data

qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

* examine attrition between experiment start and end
* (for those who did not opt of sharing their data)

* Before anonymization:
// T, C, I: 425, 218, 218

di "Consented to data sharing:"
tab treated arm

di "In experiment & saw treatment assignment:"
tab treated arm if !mi(assigned_grade)

di "Took midterm 2:"
tab treated arm if !mi(mid2score) & !mi(assigned_grade)

di "Took final (and completed experiment):"
tab treated arm if !mi(finalscore) & !mi(assigned_grade)

di "Took Micro B:"
tab treated arm if took100b & !mi(assigned_grade)

tab assigned_grade arm if mi(mid2score), mi
tab assigned_grade arm if mi(finalscore) & !mi(mid2score), mi

capture restore
preserve

* keep only those who observed their treatment statuses (i.e. received a grade including W)
keep if !mi(assigned_grade) & arm > 0

foreach v in mid2score finalscore {
    capture drop miss
    qui gen miss = mi(`v')
    di "`v'"
    tab miss arm, col
    ttest miss, by(arm) unequal
}

capture drop miss
qui gen miss = took100b == 0
di "took100b"
tab miss arm, col
ttest miss, by(arm) unequal

* what if we condition on mid1 scores and year?
reg took100b treated mid1scorestd y2019 if arm > 0

restore

* get data and merge demographic vars

qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

** Generate balance tables

* create frame 'results' to store coefficients

capture frame drop results
frame create results str32 depvar arm str32 exam bothpairs mean stderr N

frames dir

* vars to check balance
local balance_vars mid1scorestd y2019 ///
    prev_cumgpa prev_cumgpa_unobs mathquizstd pset_pre ///
    videos_mid1 videos_mid1_u duration_mid1 duration_mid1_u ///
    asian latx white othereth female male transfer
replace prev_cumgpa = . if prev_cumgpa_unobs
order `balance_vars'
sum `balance_vars'


* Get balance table data
* Loop over exams for those seeing treatment assignment
foreach exam in mid2 final {
    
    * loop through all variables and post info to `results'
    
    capture restore
    preserve
    
    * first, anyone who saw their treatment status
    keep if !mi(assigned_grade)
    foreach v in `balance_vars' {
        forvalues i = 0/2 {
            qui sum `v' if arm == `i'
            frame post results ("`v'") (`i') ("`exam'") (-1) (r(mean)) (r(sd) / sqrt(r(N))) (r(N))
        }
    }
    
    * second, anyone who completed the `exam'
    keep if !mi(`exam'score)

    foreach v in `balance_vars' {
        forvalues i = 0/2 {
            qui sum `v' if arm == `i'
            frame post results ("`v'") (`i') ("`exam'") (0) (r(mean)) (r(sd) / sqrt(r(N))) (r(N))
        }
    }

    * third, matching pairs only
    keep if bothpairs_`exam'
    foreach v in `balance_vars' {
        forvalues i = 1/2 {
            qui sum `v' if arm == `i'
            frame post results ("`v'") (`i') ("`exam'") (1) (r(mean)) (r(sd) / sqrt(r(N))) (r(N))
        }
    }
    restore
}

frame results: li depvar arm bothpairs mean stderr N


* Export the results data for publication
frame results: export delimited "./data/generated/balance_table_data.csv", replace

capture restore

qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

preserve

import delimited "./data/raw/DeID_fa19_attendance_checks.csv", clear
keep v15 v16
rename (v15 v16) (qTreat id)
gen year = 2019
drop in 1
tempfile tempf
save `tempf'

import delimited "./data/raw/DeID_fa18_attendance_checks.csv", clear
keep v9 v16
rename (v9 v16) (qTreat id)
gen year = 2018
drop in 1

append using `tempf'

* clean response
gen qtreat = .
replace qtreat = 1 if qTreat == "True" | qTreat == "1"
replace qtreat = 0 if qTreat == "False" | qTreat == "0"
drop qTreat

save `tempf', replace

restore
merge 1:1 id year using `tempf'

tab qtreat arm

frames dir

set more off, perm

tab qtreat arm
di (10 + 23 + 11) / 704

* get Montiel-Pflueger F-stats

ivreg2 mid2scorestd mid1scorestd y2019 (videos_mid2_u = treated) if arm > 0, robust
weakivtest

ivreg2 finalscorestd mid1scorestd y2019 (videos_final_u = treated) if arm > 0, robust
weakivtest

* Anderson-Rubin confidence intervals

capture restore
preserve

* change units to 10s of videos
replace videos_mid2_u = videos_mid2_u / 10
replace videos_final_u = videos_final_u / 10

weakiv ivreg2 mid2scorestd mid1scorestd y2019 (videos_mid2_u = treated) if arm > 0, robust gridpoints(2500)
weakiv ivreg2 mid2scorestd mid1scorestd y2019 (duration_mid2_u = treated) if arm > 0, robust gridpoints(2500)

weakiv ivreg2 finalscorestd mid1scorestd y2019 (videos_final_u = treated) if arm > 0, robust gridpoints(2500)
weakiv ivreg2 finalscorestd mid1scorestd y2019 (duration_final_u = treated) if arm > 0, robust gridpoints(2500)

restore

/* Outcomes of interest:

- First stage
videos_b4_mid2_relu
duration_b4_mid2_relu
videos_rel_u
duration_rel_u

- Second stage
midterm2 score
final exam score

- Tests of exclusion restriction/spillovers to other studying
letter_option (did treatment affect decision to take 100A for letter grade?)
attendance
piazza questions
piazza answers
piazza views
pset visits (post)

- Spillover outcomes, concurrent quarter
gpa in all gpa-affecting courses
gpa, excluding 100A
gpa, non-econ courses
gpa, only econ courses excluding 100A
units taken for letter grade
units taken p/np
units withdrawn
n classes passed
n classes not passed
n class withdrawn
n classes taken p/np
n classes taken letter

- Spillovers, following quarter
took100b
videos_rel_u_100b
duration_rel_u_100b
midterm1 100B
midterm2 100B
final exam 100B
winter gpa all, excluding 100b, excluding all econ, econ excluding 100b
winter units taken letter, p/np, w
winter n classes pass, not passed, w
winter n classes taken letter, p/np
*/

* get data
qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars
//sum

* heteroskedasticity? 

capture restore
preserve
keep if arm > 0

qui reg mid2scorestd treated mid1scorestd y2019
predict resid, resid
twoway (scatter resid mid1scorestd if arm == 1, mcolor(navy%75) msymbol(Oh)) ///
    (scatter resid mid1scorestd if arm == 2, mcolor(cranberry%75) msymbol(Dh)), ///
    legend(order(2 "Incentive" 1 "Control" ) pos(11) ring(0) col(1) region(lstyle(none))) /// 
    title("a) Midterm 2 model residuals") ///
    ylabel(-3(1)3) ///
    name(resid_mid2, replace)

drop resid

qui reg finalscorestd treated mid1scorestd y2019
predict resid, resid
twoway (scatter resid mid1scorestd if arm == 1, mcolor(navy%75) msymbol(Oh)) ///
    (scatter resid mid1scorestd if arm == 2, mcolor(cranberry%75) msymbol(Dh)), ///
    legend(order(2 "Incentive" 1 "Control" ) pos(11) ring(0) col(1) region(lstyle(none))) /// 
    title("b) Final exam model residuals") ///
    ylabel(-3(1)3) ///
    name(resid_final, replace)

graph combine resid_mid2 resid_final, name(combo_resid, replace) ysize(3) xsize(6)
export_img combo_resid

restore

* Demonstrating that imputing missings as the mean or as zeros doesn't affect 
*  estimates of the coefficients of interest.

capture restore
preserve

keep if arm > 0

qui sum prev_cumgpa if prev_cumgpa_unobs == 0
gen prev_cumgpa2 = prev_cumgpa
replace prev_cumgpa2 = r(mean) if prev_cumgpa_unobs

reg finalscorestd treated mid1scorestd y2019
reg finalscorestd treated mid1scorestd y2019 prev_cumgpa prev_cumgpa_unobs
reg finalscorestd treated mid1scorestd y2019 prev_cumgpa2

restore

* create frame 'results' to store coefficients

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str32 model

frames dir

* define function to calculate difference in means and Neyman SEs

capture program drop neyman
program define neyman
    args y exam
    preserve

    * restrict sample
    keep if bothpairs_`exam' & arm > 0

    * get N and mean ctrl group
    qui sum `y'
    local N = r(N)
    qui sum `y' if arm == 1
    local meanctrl = r(mean)

    * reshape wide
    keep pairyear `y' treated
    reshape wide `y', i(pairyear) j(treated)

    * take difference in means
    gen diff = `y'1 - `y'0

    * get point estimate
    qui sum diff
    local meandiff = r(mean)
    
    * calc standard error estimate
    * SE_hat = [1/(J(J-1)) * sum(diff_j - diff_bar) ^ 2] ^ 0.5
    gen diff2 = (diff - `meandiff') ^ 2
    qui sum diff2
    local sumdiff2 = r(sum)
    local J = `N' / 2
    local se_hat = (1 / `J' / (`J' - 1) * `sumdiff2') ^ 0.5

    * post to frame
    frame post results ("`y'") (`meanctrl') (`meandiff') (`se_hat') (`N') ("Neyman")

    restore
    end

* test cases
// neyman mid2scorestd mid2
// neyman finalscorestd final
// frame results: li

* Write function to estimate linear model only controlling for treatment assignment method

capture program drop get_itt
program define get_itt
    args y exam
    preserve

    * restrict sample
    keep if !mi(`exam'scorestd)
    
    keep if !mi(`y') & arm > 0

    * mean control group
    qui sum `y' if arm == 1
    local meanctrl = r(mean)

    * fit model
    reg `y' treated mid1scorestd y2019, robust
    
    * post to frame
    frame post results ("`y'") (`meanctrl') (_b[treated]) (_se[treated]) (e(N)) ("itt")

    restore
    end

* test cases
// get_itt mid2scorestd mid2
// get_itt finalscorestd final
// frame results: li

* Write function to estimate linear model only controlling for treatment assignment method
* and imputing zeros for missing outcomes

capture program drop get_itt_with_zeros
program define get_itt_with_zeros
    args y exam
    preserve

    * restrict sample to those seeing treatment status
    keep if !mi(assigned_grade) & arm > 0
    
    * replace `exam'scorestd with new one imputing zeros for missings,
    * then replace outcome with zero if missing. This is so stddev outcomes get correct
    * stddev units instead of zero, which would be a relatively high score.
    replace `exam'score = 0 if mi(`exam'score)
    get_std_units
    replace `y' = 0 if mi(`y')

    * mean control group
    qui sum `y' if arm == 1
    local meanctrl = r(mean)

    * fit model
    reg `y' treated mid1scorestd y2019, robust
    
    * post to frame
    frame post results ("`y'") (`meanctrl') (_b[treated]) (_se[treated]) (e(N)) ("itt_zeros")

    restore
    end

* test cases
// get_itt_with_zeros mid2scorestd mid2
// get_itt_with_zeros finalscorestd final
// frame results: li

* Loop through all dependent vars

local mid2vars videos_mid2_u ///
    videos_mid2 duration_mid2_u duration_mid2 mid2scorestd

local finalvars videos_final_u videos_final duration_final_u duration_final /// 
    finalscorestd ///
    letter_option attendance pset_post ///
    piazza_questions piazza_answers piazza_views piazza_daysonline ///
    gpa_letter gpa_letter_sans100a gpa_letter_sansecon gpa_econ_sans100a ///
    units_letter units_pnp units_w ///
    nclass_p nclass_np nclass_w nclass_letter nclass_pnp pclass_letter pclass_pnp ///
    took100b ///
    winter_gpa_letter winter_gpa_letter_sans100a winter_gpa_letter_sansecon winter_gpa_econ_sans100a ///
    winter_units_letter winter_units_pnp winter_units_w ///
    winter_nclass_p winter_nclass_np winter_nclass_w ///
    winter_nclass_letter winter_nclass_pnp winter_pclass_letter winter_pclass_pnp

local finalvarsb videos_b videos_b_u duration_b duration_b_u finalbscorestd pass100b


* Dependent vars observed after second midterm
foreach v in `mid2vars' {
    qui neyman `v' mid2
    qui get_itt `v' mid2
    qui get_itt_with_zeros `v' mid2
}


* Dependent vars observed after final
foreach v in `finalvars' {
    qui neyman `v' final
    qui get_itt `v' final
    qui get_itt_with_zeros `v' final
}


* Dependent vars observed at the end of 100B
capture drop bothpairs_finalb
rename final_100bstd finalbscorestd
gen bothpairs_finalb = !mi(finalbscorestd)
bys pair year: ereplace bothpairs_finalb = sum(bothpairs_finalb)
replace bothpairs_finalb = bothpairs_finalb >= 2
foreach v in `finalvarsb' {
    qui neyman `v' finalb
    qui get_itt `v' finalb
    qui get_itt_with_zeros `v' finalb
}
rename finalbscorestd final_100bstd


* Dependent vars observed in the middle of 100B
capture drop bothpairs_mid1b bothpairs_mid2b
forvalues i = 1/2 {
    di "`i'"
    rename mid`i'_100bstd mid`i'bscorestd
    gen bothpairs_mid`i'b = !mi(mid`i'bscorestd)
    bys pair year: ereplace bothpairs_mid`i'b = sum(bothpairs_mid`i'b)
    replace bothpairs_mid`i'b = bothpairs_mid`i'b >= 2
    qui neyman mid`i'bscorestd mid`i'b
    qui get_itt mid`i'bscorestd mid`i'b
    qui get_itt_with_zeros mid`i'bscorestd mid`i'b
    rename mid`i'bscorestd mid`i'_100bstd
}


* see results
frame results: li

* Export the results data for publication

frame results: export delimited "./data/generated/itt_coeffs.csv", replace


* Export sample for Semenova (2025) generalized Lee Bounds (computed in R)
* and IPW estimation
* Sample: all randomized students who completed Micro A (saw treatment assignment)
* Selection indicator: took100b (enrolled in Micro B)
preserve
keep if !mi(assigned_grade) & arm > 0
export delimited treated took100b y2019 ///
    videos_b videos_b_u duration_b duration_b_u ///
    mid1_100bstd mid2_100bstd final_100bstd ///
    mid1scorestd mathquizstd mathquiz_unobs ///
    transfer prev_cumgpa prev_cumgpa_unobs ///
    female asian latx white ///
    using "./data/generated/semenova_sample.csv", replace
restore


* IPW estimates for Micro B outcomes
* Reweight Micro B takers to look like the full experimental sample

capture frame drop ipw_results
frame create ipw_results str32 depvar meanctrl treatbeta stderr N str32 model

capture program drop est_ipw
program define est_ipw
    args y
    preserve

    * full sample: all randomized who completed Micro A
    keep if !mi(assigned_grade) & arm > 0

    * estimate propensity score: P(took100b=1 | X)
    logit took100b treated mid1scorestd mathquizstd mathquiz_unobs ///
        transfer prev_cumgpa prev_cumgpa_unobs ///
        female asian latx white y2019
    predict phat, pr

    * restrict to Micro B takers, generate IPW weights
    keep if took100b == 1
    gen ipw = 1 / phat

    * trim extreme weights at 1st/99th percentiles
    _pctile ipw, p(1 99)
    replace ipw = r(r1) if ipw < r(r1)
    replace ipw = r(r2) if ipw > r(r2)

    * control mean (unweighted, among Micro B takers)
    qui sum `y' if arm == 1
    local meanctrl = r(mean)

    * IPW-weighted regression
    reg `y' treated mid1scorestd y2019 [pweight=ipw], robust

    * post results
    frame post ipw_results ("`y'") (`meanctrl') (_b[treated]) (_se[treated]) (e(N)) ("ipw")

    restore
end

* Run IPW for each Micro B outcome
foreach v in videos_b videos_b_u duration_b duration_b_u mid1_100bstd mid2_100bstd final_100bstd {
    qui est_ipw `v'
}

frame ipw_results: li
frame ipw_results: export delimited "./data/generated/ipw_100b.csv", replace


* We'll use ivregress for the base model and a custom function for the Neyman model

* create frame 'results' to store coefficients

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str32 model

frames dir

* define function for ivregress

capture program drop est_late
program define est_late
    args y exam

    capture restore
    preserve

    * restrict sample
    qui keep if !mi(`y') & arm > 0

    * adjust units of videos
    replace videos_`exam'_u = videos_`exam'_u / 10 // 10s of videos

    * get N and mean ctrl group
    qui sum `y'
    local N = r(N)
    qui sum `y' if arm == 1
    local ctrlmean = r(mean)

    * estimate iv, twice
    qui ivregress 2sls `y' mid1scorestd y2019 (videos_`exam'_u = treated), vce(robust)
    local late_v = _b[videos_`exam'_u]
    local se_v = _se[videos_`exam'_u]
    qui ivregress 2sls `y' mid1scorestd y2019 (duration_`exam'_u = treated), vce(robust)
    local late_d = _b[duration_`exam'_u]
    local se_d = _se[duration_`exam'_u]

    * post to frame, twice
    frame post results ("`y'") (`ctrlmean') (`late_v') (`se_v') (`N') ("late_v")
    frame post results ("`y'") (`ctrlmean') (`late_d') (`se_d') (`N') ("late_d")

    restore
    end

* test cases
// est_late mid2scorestd mid2
// est_late finalscorestd final
// frame results: li

* define function for ivregress

capture program drop est_late_with_zeros
program define est_late_with_zeros
    args y exam

    capture restore
    preserve

    * restrict sample to those seeing treatment assignment
    keep if !mi(assigned_grade) & arm > 0    
    
    * replace `exam'scorestd with new one imputing zeros for missings,
    * then replace outcome with zero if missing. This is so stddev outcomes get correct
    * stddev units instead of zero, which would be a relatively high score.
    replace `exam'score = 0 if mi(`exam'score)
    get_std_units
    replace `y' = 0 if mi(`y')

    * adjust units of videos
    replace videos_`exam'_u = 0 if mi(videos_`exam'_u)
    replace duration_`exam'_u = 0 if mi(duration_`exam'_u)
    replace videos_`exam'_u = videos_`exam'_u / 10 // 10s of videos

    * get N and mean ctrl group
    qui sum `y'
    local N = r(N)
    qui sum `y' if arm == 1
    local ctrlmean = r(mean)

    * estimate iv, twice
    qui ivregress 2sls `y' mid1scorestd y2019 (videos_`exam'_u = treated), vce(robust)
    local late_v = _b[videos_`exam'_u]
    local se_v = _se[videos_`exam'_u]
    qui ivregress 2sls `y' mid1scorestd y2019 (duration_`exam'_u = treated), vce(robust)
    local late_d = _b[duration_`exam'_u]
    local se_d = _se[duration_`exam'_u]

    * post to frame, twice
    frame post results ("`y'") (`ctrlmean') (`late_v') (`se_v') (`N') ("late_v_with_zeros")
    frame post results ("`y'") (`ctrlmean') (`late_d') (`se_d') (`N') ("late_d_with_zeros")

    restore
    end

* test cases
// est_late_with_zeros mid2scorestd mid2
// est_late_with_zeros finalscorestd final
// frame results: li

* define function to calculate difference in means and Neyman SEs


capture program drop neyman_late
program define neyman_late
    args y exam
    preserve

    * restrict sample
    qui keep if bothpairs_`exam' & arm > 0

    * adjust units of videos
    replace videos_`exam'_u = videos_`exam'_u / 10 // 10s of videos

    * get N and mean ctrl group
    qui sum `y'
    local N = r(N)
    qui sum `y' if arm == 1
    local ctrlmean = r(mean)

    * reshape wide
    qui keep pairyear `y' treated videos_`exam'_u duration_`exam'_u
    qui reshape wide `y' videos_`exam'_u duration_`exam'_u, i(pairyear) j(treated)

    * take difference in means for itt and first stages
    gen itt = `y'1 - `y'0
    gen fs_v = videos_`exam'_u1 - videos_`exam'_u0
    gen fs_d = duration_`exam'_u1 - duration_`exam'_u0

    * get point estimate
    foreach v in itt fs_v fs_d {
        qui sum `v'
        local meandiff_`v' = r(mean)
    }
    local late_v = `meandiff_itt' / `meandiff_fs_v'
    local late_d = `meandiff_itt' / `meandiff_fs_d'
    
    * calc standard error estimates
    * SE_hat = [1/(J(J-1)) * sum(diff_j - diff_bar) ^ 2] ^ 0.5
    local J = `N' / 2
    foreach v in itt fs_v fs_d {
        capture drop diff2
        gen diff2 = (`v' - `meandiff_`v'') ^ 2
        qui sum diff2
        local se_hat_`v' = (1 / `J' / (`J' - 1) * r(sum)) ^ 0.5
    }

    * SE for LATE approx b1/b2 sqrt( V(b1)/b1^2 + V(b2)/b2^2 - 2 * cov(b1, b2) / (b1 * b2) )
    * do this calc twice for each meandiff_fs

    foreach x in "v" "d" {
        * calculate covariance between itt estimate and first stage estimate
        capture drop diff2
        gen diff2 = (itt - `meandiff_itt') * (fs_`x' - `meandiff_fs_`x'')
        qui sum diff2
        local cov_`x' = 1 / `J' / (`J' - 1) * r(sum)
        * get variance terms
        local term0 = (`meandiff_itt' / `meandiff_fs_`x'')
        local term1 = (`se_hat_itt' ^ 2) / (`meandiff_itt' ^ 2)
        local term2 = (`se_hat_fs_`x'' ^ 2) / (`meandiff_fs_`x'' ^ 2)
        local term3 = 2 * `cov_`x'' / (`meandiff_itt' * `meandiff_fs_`x'')
        * check terms
//         forvalues i = 0/3 {
//             di `term`i''
//         }
        * calc standard error
        local se_`x' = `term0' * sqrt( `term1' + `term2' - `term3' )
//         di `se_`x''
    }

    * post to frame, twice
    frame post results ("`y'") (`ctrlmean') (`late_v') (`se_v') (`N') ("N_late_v")
    frame post results ("`y'") (`ctrlmean') (`late_d') (`se_d') (`N') ("N_late_d")

    restore
    end

* test cases
// neyman_late mid2scorestd mid2
// neyman_late finalscorestd final
// frame results: li

* Loop through all dependent vars for which we estimate LATEs
// TODO: add 100b video vars

local mid2vars mid2scorestd

local finalvars finalscorestd 


* 100B outcomes
local finalvarsb final_100bstd


* Dependent vars observed after second midterm
foreach v in `mid2vars' {
    qui est_late `v' mid2
    qui est_late_with_zeros `v' mid2
    qui neyman_late `v' mid2
}


* Dependent vars observed after final
foreach v in `finalvars' {
    qui est_late `v' final
    qui est_late_with_zeros `v' final
    qui neyman_late `v' final
}

* see results
frame results: li

* Export the results data for publication

frame results: export delimited "./data/generated/lates_coeffs.csv", replace

* Bootstrap standard errors

* Not using this becuase dist variance may not be finite
* TODO: look into altenative options, perhaps parametric bootstrap, using
* percentiles, etc.

capture program drop neyman_boot
program define neyman_boot 
    args y exam iters
    capture frame change default
    capture restore
    preserve

    * restrict sample
    keep if bothpairs_`exam' & arm > 0

    * get N and mean ctrl group
    qui sum `y'
    local N = r(N)
    local J = `N' / 2

    * reshape wide
    qui keep pairyear `y' treated videos_`exam'_u duration_`exam'_u
    qui reshape wide `y' videos_`exam'_u duration_`exam'_u, i(pairyear) j(treated)

    * take difference in means for itt and first stages
    gen itt = `y'1 - `y'0
    gen fs_v = videos_`exam'_u1 - videos_`exam'_u0
    gen fs_d = duration_`exam'_u1 - duration_`exam'_u0

    * get point estimate
    foreach v in itt fs_v fs_d {
        qui sum `v'
        local meandiff_`v' = r(mean)
    }
    local late_v = `meandiff_itt' / `meandiff_fs_v'
    local late_d = `meandiff_itt' / `meandiff_fs_d'

    * now resample `iters' times and store "LATE" estimates each round
    * store in frame `sim'. Each draw in draws
    capture frame drop sim
    frame create sim iter late_v late_d
    keep itt fs_v fs_d
    forvalue i = 1/`iters' {
        capture frame drop copyf
        frame copy default copyf
        frame change copyf
        bsample
        foreach v in itt fs_v fs_d {
            qui sum `v'
            local meandiff_`v' = r(mean)
        }
        local late_v_s = `meandiff_itt' / `meandiff_fs_v'
        local late_d_s = `meandiff_itt' / `meandiff_fs_d'
        frame post sim (`i') (`late_v_s') (`late_d_s')
        frame change default
    }
    frame sim: sum
    frame change sim
    histogram late_d, bin(50)
    frame change default
    
    frame sim: qui sum late_v
    local se_v = r(sd)
    frame sim: qui sum late_d
    local se_d = r(sd)

    * post to frame, twice
    frame post results ("`y'") (`late_v') (`se_v') (`N') ("N_boot_v")
    frame post results ("`y'") (`late_d') (`se_d') (`N') ("N_boot_d")

    frame change default
    restore
    end

* test cases
// neyman_boot mid2scorestd mid2 10000
// neyman_late finalscorestd final
// frame results: li

* Distribution (perhaps) does not have finite variance, std err does not converge

// ivregress 2sls mid2scorestd mid1scorestd y2019 (duration_mid2_u = treated) if arm > 0, vce(bootstrap, rep(10000)) nodots

* get data
qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

* non linear controls?

/*
* add squares of nonbinary controls
capture drop mathquizstd2 pset_pre2 videos_b4_mid1_rel2
gen mathquizstd2 = mathquizstd * mathquizstd
gen pset_pre2 = pset_pre * pset_pre
gen videos_b4_mid1_rel2 = videos_b4_mid1_rel * videos_b4_mid1_rel
*/

* create frame 'results' to store coefficients

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str99 ctrls str32 model

frames dir

* Model without Fixed Effects

capture program drop pds_itt
program pds_itt, eclass
    args y
    // display 
    di "`=char(10)'`=char(13)'" ///
        "****************" "`=char(10)'`=char(13)'" "PDS for `y'..." ///
        "`=char(10)'`=char(13)'" "****************" "`=char(10)'`=char(13)'"
    // run PDS
    pdslasso `y' treated (y2019 mid1scorestd $ctrl_vars) if arm > 0, ///
        partial(y2019 mid1scorestd) robust noisily
    end


* Fixed Effect models

capture program drop pds_itt_fe
program pds_itt_fe, eclass
    args y bothpairs

    di "`=char(10)'`=char(13)'" ///
        "****************" "`=char(10)'`=char(13)'" "PDS for `y' with FEs..." ///
        "`=char(10)'`=char(13)'" "****************" "`=char(10)'`=char(13)'"

    
    pdslasso `y' treated (mid1scorestd $ctrl_vars) if arm > 0 & `bothpairs', ///
        partial(mid1scorestd) fe robust noisily
    end


* define function to get coefficient and ctrls for each outcome

capture program drop get_pds
program define get_pds
    args y exam

    * no fixed effects
    preserve
    keep if !mi(`exam'scorestd)
    qui sum `y' if arm == 1
    local meany = r(mean)
    qui pds_itt `y'
    restore
    frame post results ("`y'") (`meany') (_b[treated]) (_se[treated]) (e(N)) ("`e(xselected)'") ("noFEs")

    * fixed effects
    preserve
    xtset pairyear
    keep if bothpairs_`exam'
    qui sum `y' if arm == 1
    local meany = r(mean)
    qui pds_itt_fe `y' bothpairs_`exam'
    restore
    frame post results ("`y'") (`meany') (_b[treated]) (_se[treated]) (e(N)) ("`e(xselected)'") ("FEs")
    end

* test cases
// get_pds mid2scorestd mid2
// get_pds finalscorestd final
// frame results: li

* Loop through all dependent vars
// TODO: add duration_rel_u for three times: before mid2, at final, and at 100b final

local mid2vars videos_mid2_u ///
    videos_mid2 duration_mid2_u duration_mid2 mid2scorestd

local finalvars videos_final_u videos_final duration_final_u duration_final /// 
    finalscorestd ///
    letter_option attendance pset_post ///
    piazza_questions piazza_answers piazza_views piazza_daysonline ///
    gpa_letter gpa_letter_sans100a gpa_letter_sansecon gpa_econ_sans100a ///
    units_letter units_pnp units_w ///
    nclass_p nclass_np nclass_w nclass_letter nclass_pnp pclass_letter pclass_pnp ///
    took100b ///
    winter_gpa_letter winter_gpa_letter_sans100a winter_gpa_letter_sansecon winter_gpa_econ_sans100a ///
    winter_units_letter winter_units_pnp winter_units_w ///
    winter_nclass_p winter_nclass_np winter_nclass_w ///
    winter_nclass_letter winter_nclass_pnp winter_pclass_letter winter_pclass_pnp

local finalvarsb videos_b videos_b_u duration_b duration_b_u finalbscorestd pass100b


* Dependent vars observed after second midterm
foreach v in `mid2vars' {
    qui get_pds `v' mid2
}


* Dependent vars observed after final
foreach v in `finalvars' {
    qui get_pds `v' final
}


* Dependent vars observed at the end of 100B
capture drop bothpairs_finalb
rename final_100bstd finalbscorestd
gen bothpairs_finalb = !mi(finalbscorestd)
bys pair year: ereplace bothpairs_finalb = sum(bothpairs_finalb)
replace bothpairs_finalb = bothpairs_finalb >= 2
foreach v in `finalvarsb' {
    qui get_pds `v' finalb
}
rename finalbscorestd final_100bstd


* Dependent vars observed in the middle of 100B
capture drop bothpairs_mid1b bothpairs_mid2b
forvalues i = 1/2 {
    di "`i'"
    rename mid`i'_100bstd mid`i'bscorestd
    gen bothpairs_mid`i'b = !mi(mid`i'bscorestd)
    bys pair year: ereplace bothpairs_mid`i'b = sum(bothpairs_mid`i'b)
    replace bothpairs_mid`i'b = bothpairs_mid`i'b >= 2
    qui get_pds mid`i'bscorestd mid`i'b
    rename mid`i'bscorestd mid`i'_100bstd
}


* see results
frame results: li

* Export the results data for publication

frame results: export delimited "./data/generated/pds_coeffs.csv", replace

* create frame 'results' to store coefficients

capture frame drop results
frame create results str32 depvar meanctrl treatbeta stderr N str99 ctrls str32 model

frames dir

* Model without Fixed Effects

capture program drop pds_iv
program pds_iv
    args y exam

    ** no Fixed Effects

    * restrict sample
    preserve
    keep if !mi(`y') & arm > 0

    * adjust units of videos_
    replace videos_`exam'_u = videos_`exam'_u / 10 // 10s of videos

    * control mean
    qui sum `y' if arm == 1
    local meany = r(mean)

    * estimate IV using PDS, video counts
    ivlasso `y' (y2019 mid1scorestd $ctrl_vars) (videos_`exam'_u=treated), ///
        partial(y2019 mid1scorestd treated) robust noisily
    frame post results ("`y'") (`meany') (_b[videos_`exam'_u]) (_se[videos_`exam'_u]) ///
        (e(N)) ("`e(xselected)'") ("PDS_IV_v")

    * estimate IV using PDS, video duration
    ivlasso `y' (y2019 mid1scorestd $ctrl_vars) (duration_`exam'_u=treated), ///
        partial(y2019 mid1scorestd treated) robust noisily
    frame post results ("`y'") (`meany') (_b[duration_`exam'_u]) (_se[duration_`exam'_u]) ///
        (e(N)) ("`e(xselected)'") ("PDS_IV_d")


    ** Fixed Effects

    * further restrict sample and xtset
    keep if bothpairs_`exam'
    xtset pairyear

    * get control mean
    qui sum `y' if arm == 1
    local meany = r(mean)

    * estimate IV using PDS with FEs, video counts
    ivlasso `y' (mid1scorestd $ctrl_vars) (videos_`exam'_u=treated), ///
        partial(mid1scorestd treated) fe robust noisily
    frame post results ("`y'") (`meany') (_b[videos_`exam'_u]) (_se[videos_`exam'_u]) ///
        (e(N)) ("`e(xselected)'") ("PDS_IVFE_v")

    * estimate IV using PDS with FEs, video duration
    ivlasso `y' (mid1scorestd $ctrl_vars) (duration_`exam'_u=treated), ///
        partial(mid1scorestd treated) fe robust noisily
    frame post results ("`y'") (`meany') (_b[duration_`exam'_u]) (_se[duration_`exam'_u]) ///
        (e(N)) ("`e(xselected)'") ("PDS_IVFE_d")

    restore
    end

* test cases
// qui pds_iv mid2scorestd mid2
// qui pds_iv finalscorestd final
// frame results: li

* Loop through all dependent vars for which we estimate LATEs
// TODO: add 100b video vars

local mid2vars mid2scorestd

local finalvars finalscorestd 

* 100B outcomes
local finalvarsb final_100bstd


* Dependent vars observed after second midterm
foreach v in `mid2vars' {
    qui pds_iv `v' mid2
}

* Dependent vars observed after final
foreach v in `finalvars' {
    qui pds_iv `v' final
}

* TODO: 100B LATEs

* see results
frame results: li

* Export the results data for publication

frame results: export delimited "./data/generated/pds_iv_coeffs.csv", replace

* get data
qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

* results frame for storing output

capture frame drop results
frame create results str32 depvar str32 interactvar meanctrl interactbeta stderr N

frames dir

* Look at heterogeneity by:
* - blocking variables: mid1score and year
* - pre treatment videos, total and unique
* - demographics: transfer, ethnicity, gender

* why pretreatment videos?
* Hypothesis: those with high pretreatment videos are more likely to have watched
*  videos anyways, so potentially lower treatment effects.
* On the other hand, those who intended to watch videos may have done so for the 
*  very reason they knew they'd high have treatment effects.

capture restore
preserve

local interact_vars mid1scorestd y2019 ///
    videos_mid1 videos_mid1_u ///
    transfer female white asian latx othereth
    
* get het. ATE estimate for each covariate
foreach v in `interact_vars' {
    
    * two outcome vars
    foreach y in mid2scorestd finalscorestd {
        
        * get mean for control
        qui sum `y' if arm == 1
        local meanctrl = r(mean)
        
        * get interaction term
        capture drop interact
        gen interact = treated * `v'

        qui reg `y' treated interact mid1scorestd y2019 `v' if arm > 0, robust
        
        * store in frame
        frame post results ("`y'") ("`v'") (`meanctrl') (_b[interact]) ///
            (_se[interact]) (e(N))
        
        /*
        qui reg `y' treated interact mid1scorestd y2019 transfer female white asian latx `v' if arm > 0, robust
        
        * store in frame
        frame post results ("`y'") ("`v'") (`meanctrl') (_b[interact]) ///
            (_se[interact]) (e(N))
        */
    }
}

restore

frame results: li

* Export results as CSV

frame results: export delimited "./data/generated/het_coeffs.csv", replace

* adjust for multiple hypotheses

capture restore
preserve

keep if arm > 0

gen inter1 = treated * transfer
gen inter2 = treated * female
gen inter3 = treated * asian
gen inter4 = treated * latx
gen inter5 = treated * white
gen inter6 = treated * othereth
gen inter7 = treated * mid1scorestd 
gen inter8 = treated * y2019
gen inter9 = treated * videos_mid1_u

mhtreg (mid2scorestd inter1 transfer treated mid1scorestd y2019) ///
    (finalscorestd inter1 transfer treated mid1scorestd y2019) ///
 (mid2scorestd inter2 female treated mid1scorestd y2019) ///
    (finalscorestd inter2 female treated mid1scorestd y2019) ///
 (mid2scorestd inter3 asian treated mid1scorestd y2019) ///
    (finalscorestd inter3 asian treated mid1scorestd y2019) ///
(mid2scorestd inter4 latx treated mid1scorestd y2019) ///
    (finalscorestd inter4 latx treated mid1scorestd y2019) ///
 (mid2scorestd inter5 white treated mid1scorestd y2019) ///
    (finalscorestd inter5 white treated mid1scorestd y2019) ///
 (mid2scorestd inter6 othereth treated mid1scorestd y2019) ///
    (finalscorestd inter6 othereth treated mid1scorestd y2019) ///
(mid2scorestd inter7 treated mid1scorestd y2019) ///
    (finalscorestd inter7 treated mid1scorestd y2019) ///
 (mid2scorestd inter8 treated mid1scorestd y2019) ///
    (finalscorestd inter8 treated mid1scorestd y2019) ///
 (mid2scorestd inter9 videos_mid1_u treated mid1scorestd y2019) ///
    (finalscorestd inter9 videos_mid1_u treated mid1scorestd y2019)

restore

* Plot local linear trends for mid2

capture restore
preserve

keep if !mi(finalscorestd)
replace arm = 1 if arm == 0

keep if mid1scorestd >= -3.0
keep if mid1scorestd <= 2

local videos videos_mid2_u
local outcome mid2scorestd
local n = 50
local bw = 0.9

twoway (lpolyci `videos' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `videos' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("") ///
    ytitle("Unique Videos") ///
    legend(order(4 "Incentive" 2 "Control") pos(1) ring(0) col(1) region(lstyle(none))) ///
    ylabel(0(10)60) ///
    name(lpolymid2v, replace)

twoway (lpolyci `outcome' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `outcome' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("Midterm 1 Score") ///
    ytitle("Midterm 2 Score") ///
    legend(order(4 "Incentive" 2 "Control") pos(11) ring(0) col(1) region(lstyle(none))) ///
    ylabel(-3(1)3) ///
    name(lpolymid2, replace)


* keep if matched pair or above median
keep if bothpairs_mid2 | (mid1scorestd > 0)

twoway (lpolyci `videos' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `videos' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("") ///
    ytitle("Unique videos") ///
    legend(order(4 "Incentive" 2 "Control") pos(1) ring(0) col(1) region(lstyle(none))) ///
    ylabel(0(10)60) ///
    name(lpolymid2vmatched, replace)

twoway (lpolyci `outcome' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `outcome' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("Midterm 1 Score") ///
    ytitle("Midterm 2 Score") ///
    legend(order(4 "Incentive" 2 "Control") pos(11) ring(0) col(1) region(lstyle(none))) ///
    ylabel(-3(1)3) ///
    name(lpolymid2matched, replace)

restore


* export combined plot

local filename lpolymid2

graph combine lpolymid2v lpolymid2vmatched lpolymid2 lpolymid2matched, ///
    name(`filename', replace) row(2) ///
    altshrink iscale(1.2) ysize(5) xsize(6)

export_img `filename'

* Plot local linear trends for final

capture restore
preserve

keep if !mi(finalscorestd)
replace arm = 1 if arm == 0

keep if mid1scorestd >= -3.0
keep if mid1scorestd <= 2

local videos videos_final_u
local outcome finalscorestd
local n = 100
local bw = 0.9

twoway (lpolyci `videos' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `videos' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("") ///
    ytitle("Unique Videos") ///
    legend(order(4 "Incentive" 2 "Control") pos(1) ring(0) col(1) region(lstyle(none))) ///
    ylabel(0(10)70) ///
    name(lpolyfinalv, replace)

twoway (lpolyci `outcome' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `outcome' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("Midterm 1 Score") ///
    ytitle("Final Exam Score") ///
    legend(order(4 "Incentive" 2 "Control") pos(11) ring(0) col(1) region(lstyle(none))) ///
    ylabel(-3(1)3) ///
    name(lpolyfinal, replace)


* keep if matched pair or above median
keep if bothpairs_final | (mid1scorestd > 0)

twoway (lpolyci `videos' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `videos' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("") ///
    ytitle("Unique videos") ///
    legend(order(4 "Incentive" 2 "Control") pos(1) ring(0) col(1) region(lstyle(none))) ///
    ylabel(0(10)70) ///
    name(lpolyfinalvmatched, replace)

twoway (lpolyci `outcome' mid1scorestd if arm == 1, kernel(tri) degree(1) bwidth(`bw') n(`n') ///
    ciplot(rarea) lcolor(navy) fcolor(gray*.5%60) alcolor(%0)) ///
    (lpolyci `outcome' mid1scorestd if arm == 2, degree(1) n(`n') ///
    ciplot(rarea) lcolor(cranberry) fcolor(gray*.5%60) alcolor(%0)), ///
    xtitle("Midterm 1 Score") ///
    ytitle("Final Exam Score") ///
    legend(order(4 "Incentive" 2 "Control") pos(11) ring(0) col(1) region(lstyle(none))) ///
    ylabel(-3(1)3) ///
    name(lpolyfinalmatched, replace)

restore


* export combined plot

local filename lpolyfinal

graph combine lpolyfinalv lpolyfinalvmatched lpolyfinal lpolyfinalmatched, ///
    name(`filename', replace) row(2) ///
    altshrink iscale(1.2) ysize(5) xsize(6)

export_img `filename'

* get data
qui get_idyearlevel
qui get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

* histogram of unique videos watched

capture restore
preserve
keep if !mi(finalscore) // only include experiment completers

// how many students completed incentive?
gen meet_incent = videos_incent_counts_u >= 40
sum meet_incent if arm == 1
sum meet_incent if arm == 2

local w = 1
local filename = "hist_v_incent"
local histvar videos_incent_counts_u
twoway (hist `histvar' if arm == 1, ///
        width(`w') color(navy%50) freq) ///
    (hist `histvar' if arm == 2, ///
        width(`w') col(cranberry%50) freq xline(40, lpattern("dash") lcolor("black"))), ///
    legend(order(1 "Control" 2 "Incentive") ring(0) pos(11) col(1) region(lstyle(none))) ///
    xtitle("Videos") ///
    ytitle("Number of students") ///
    name(`filename', replace)

export_img `filename'

restore

* regress treatment X indicator for watching at least N videos

* do this for mid2 and final


frame change default
capture frame drop results
frame create results N meanctrlm meanctrlf meantreatm meantreatf treatm lbm ubm treatf lbf ubf

capture restore
preserve

forvalues N = 0/74 {
    * number of people watching at least N vids
    capture drop vidsm vidsf
    local nvids = `N' * 1
    qui gen vidsm = videos_mid2_u >= `nvids'
    qui gen vidsf = videos_final_u >= `nvids'
    * mean in control arm
    qui sum vidsm if arm == 1
    local meanctrl_m = r(mean)
    qui sum vidsf if arm == 1
    local meanctrl_f = r(mean)
    * mean in treatment arm
    qui sum vidsm if arm == 2
    local meantreat_m = r(mean)
    qui sum vidsf if arm == 2
    local meantreat_f = r(mean)
    * regression for mid2
    qui reg vidsm ib1.arm if arm > 0, robust
    local treatm = _b[2.arm]
    local lbm = _b[2.arm] - 1.96*_se[2.arm]
    local ubm = _b[2.arm] + 1.96*_se[2.arm]
    * regression for final
    qui reg vidsf ib1.arm if arm > 0, robust
    local treatf = _b[2.arm]
    local lbf = _b[2.arm] - 1.96*_se[2.arm]
    local ubf = _b[2.arm] + 1.96*_se[2.arm]
    * post to frame
    frame post results (`nvids') (`meanctrl_m') (`meanctrl_f') (`meantreat_m') (`meantreat_f') ///
        (`treatm') (`lbm') (`ubm') (`treatf') (`lbf') (`ubf')
}

// frame results: li

frame change results

local c 71

twoway (line meanctrlm N if N <= `c', lcol("navy")) ///
    (line meantreatm N if N <= `c', lcol("cranberry")), ///
    ytitle("% watching {&ge}X unique videos") ///
    xtitle("") ///
    title("A: Midterm 2") ///
    xlabel(0(15)65) ///
    legend(order(2 "Incentive" 1 "Control" ) pos(2) ring(0) col(1) region(lstyle(none))) ///
    name(cdf_m, replace)

twoway (line meanctrlf N, lcol("navy")) ///
    (line meantreatf N, lcol("cranberry")), ///
    xtitle("") ///
    title("B: Final exam") ///
    xlabel(0(15)75) ///
    legend(order(2 "Incentive" 1 "Control" ) pos(2) ring(0) col(1) region(lstyle(none))) ///
    name(cdf_f, replace)

twoway (line treatm N if N <= `c', lcol("cranberry") yline(0, lcol("black") lpat("dash"))) ///
    (line lbm N if N <= `c', lcol("black") lpat("dash")) ///
    (line ubm N if N <= `c', lcol("black") lpat("dash")), ///
    ytitle("Effect of incentive on" "watching {&ge}X unique videos") ///
    xtitle("Unique videos") ///
    xlabel(0(15)65) ///
    ylabel(-0.15(.15)0.65) ///
    legend(off) ///
    name(treat_m, replace)

twoway (line treatf N, lcol("cranberry") yline(0, lcol("black") lpat("dash"))) ///
    (line lbf N, lcol("black") lpat("dash")) ///
    (line ubf N, lcol("black") lpat("dash")), ///
    xtitle("Unique videos") ///
    xlabel(0(15)75) ///
    ylabel(-0.15(.15)0.65) ///
    legend(off) ///
    name(treat_f, replace)

graph combine cdf_m cdf_f treat_m treat_f, name(combo_cdf, replace) row(2) ///
    altshrink iscale(1.2) ysize(5) xsize(6)
export_img combo_cdf


frame change default

restore

tab transfer arm
sum transfer if arm > 0

* binscatter unique relevant videos watched vs mid1 score

capture restore
preserve
keep if !mi(finalscore) // only include experiment completers

local bins = 16

local filename = "binscatter_videosu"
binscatter2 videos_final_u mid1scorestd, by(arm) n(`bins') absorb(year) ///
    colors(green navy cranberry)
graph display


local filename = "binscatter_final"
binscatter2 finalscorestd mid1scorestd, by(arm) n(`bins') absorb(year) ///
    colors(green navy cranberry)
graph display

//     legend(order(3 "Incentive" 2 "Control"  1 "Above Median") pos(2) ring(0) col(1) region(lstyle(none))) ///
//     legend(order(3 "Incentive" 2 "Control"  1 "Above Median") pos(11) ring(0) col(1) region(lstyle(none))) ///


restore

* binscatter, mid2 & final, videos and scores

capture restore
preserve
keep if !mi(mid2score)

local bins = 20
local options "by(arm) n(`bins') absorb(year) colors(navy cranberry) msymbols(Oh Dh)"
replace arm = 1 if arm == 0

local filename "binscatter_vmid2"
binscatter2 videos_mid2_u mid1scorestd, `options'
// ytitle("Unique videos by Midterm 2") name(`filename', replace) xtitle("")
// legend(order(2 "Incentive" 1 "Control") pos(2) ring(0) col(1) region(lstyle(none)))
graph display

local filename "binscatter_mid2"
binscatter2 mid2scorestd mid1scorestd, `options'
// ytitle("Midterm 2 score") name(`filename', replace) xtitle("Midterm 1 Score")
// legend(order(2 "Incentive" 1 "Control") pos(11) ring(0) col(1) region(lstyle(none)))
graph display


capture restore
preserve
keep if !mi(finalscore)

replace arm = 1 if arm == 0

local filename "binscatter_vfinal"
binscatter2 videos_final_u mid1scorestd, `options'
graph display
// ytitle("Unique videos by Final") name(`filename', replace) xtitle("") ///
// legend(order(2 "Incentive" 1 "Control") pos(2) ring(0) col(1) region(lstyle(none)))

local filename "binscatter_final"
binscatter2 finalscorestd mid1scorestd, `options'
graph display
// ytitle("Final exam score") name(`filename', replace) xtitle("Midterm 1 Score") ///
// legend(order(2 "Incentive" 1 "Control") pos(11) ring(0) col(1) region(lstyle(none)))

restore

// graph combine binscatter_vmid2 binscatter_mid2 binscatter_vfinal binscatter_final, ///
//    name(combo_binscatter, replace) row(2) ///
//    altshrink iscale(1.2) ysize(4) xsize(6) colfirst xcommon
// export_img combo_binscatter

* final 

local filename = "finalquantreg"
tempfile temp
sqreg finalscorestd treated mid1scorestd if arm > 0, ///
    quantile(.05 .25 .5 .75 .95) reps(100) 
grqreg treated, ci ols olsci seed(1887) save(`temp') 
preserve
use `temp', clear
tw (rarea treated_cihi treated_cilo qtile, col(gs13)) ///
    (line treated qtile) (line ols_treated qtile if qtile <= 0.06 | qtile >= 0.94, ///
        lpattern("dash")), ///
    title("Quantile effects of being assigned" "treatment on final exam scores") ///
    legend(col(1) ring(0) order(2 "QITE estimates" 3 "OLS estimate")) ///
    ytitle("Final exam std. deviations") ///
    xtitle("Quantile") ///
    name(`filename', replace)
export_img `filename'
restore

* midterm 2

local filename = "mid2quantreg"
tempfile temp2
sqreg mid2scorestd treated mid1scorestd if arm > 0, ///
    quantile(.05 .25 .5 .75 .95) reps(100) 
grqreg treated, ci ols olsci seed(1887) save(`temp2') 
preserve
use `temp2', clear
tw (rarea treated_cihi treated_cilo qtile, col(gs13)) ///
    (line treated qtile) (line ols_treated qtile if qtile <= 0.06 | qtile >= 0.94, ///
        lpattern("dash")), ///
    title("Quantile effects of being assigned" "treatment on midterm 2 scores") ///
    legend(col(1) ring(0) order(2 "QTE estimates" 3 "OLS estimate")) ///
    ytitle("Midterm 2 std. deviations") ///
    xtitle("Quantile") ///
    name(`filename', replace)
export_img `filename'
restore

import delimited "./data/generated/id-year-weekoy-arm_level.csv", clear varnames(1)

* keep only those who finish final
keep if !mi(finalscore)

* Hours units
replace duration = duration / 3600
replace durationu = durationu / 3600

unique year
unique id
unique id year
describe
// sum

* collapse to arm-weekoy level taking means

drop id year finalscore
collapse videos-videos_post_mid2u, by(weekoy arm)

sum

* define plot function

capture program drop plot_ts
program plot_ts
    args filename y title xtitle ytitle
    twoway (line `y' weekoy if arm == 0, lcol(green)) ///
        (line `y' weekoy if arm == 1, lcol(navy)) ///
        (line `y' weekoy if arm == 2, lcol(cranberry) ///
            xline(-1, lpattern(dash) lcolor(black)) ///
            xline(3, lpattern(dash) lcolor(black)) ///
            xline(6, lpattern(dash) lcolor(black))), ///
        legend(off) ///
        title(`title') ///
        xtitle("") ///
        ytitle(`ytitle') ///
        xscale(range(-4 7)) ///
        xlabel(-4(1)7) ///
        xsize(2.5) ///
        ysize(1.7) ///
        name(`filename', replace)
    // export_img `filename'
    end


capture program drop plot_ts_legend
program plot_ts_legend
    args filename y title xtitle ytitle
    twoway (line `y' weekoy if arm == 0, lcol(green)) ///
        (line `y' weekoy if arm == 1, lcol(navy)) ///
        (line `y' weekoy if arm == 2, lcol(cranberry) ///
            xline(-1, lpattern(dash) lcolor(black)) ///
            xline(3, lpattern(dash) lcolor(black)) ///
            xline(6, lpattern(dash) lcolor(black))), ///
        legend(order(3 "Treated" 2 "Control" 1 "Above cutoff" ) ///
            pos(11) ring(0) col(1) region(lstyle(none))) ///
        title(`title') ///
        xtitle(`xtitle') ///
        ytitle(`ytitle') ///
        xscale(range(-4 7)) ///
        xlabel(-4(1)7) ///
        xsize(2.5) ///
        ysize(2) ///
        name(`filename', replace)
    // export_img `filename'
    end

* Mean videos, all
plot_ts tsall videos ///
    "Videos watched per week" ///
    "Weeks since experiment began" ///
    "Videos"

* Mean videos, unique
plot_ts tsunique videosu ///
    "Unique videos watched per week" ///
    "Weeks since experiment began" ///
    "Unique videos"

* Mean duration
plot_ts_legend tsduration duration ///
    "Time spent watching per week" ///
    "Weeks since experiment began" ///
    "Hours"

* Videos before midterm 1
plot_ts tspremid1 videos_pre_mid1 ///
    "Videos relevant to first midterm watched per week" ///
    "Weeks since experiment began" ///
    "Videos"

* Videos between mid1 and mid2
plot_ts tsmid1mid2 videos_mid1_to_mid2 ///
    "Videos relevant to second midterm watched per week" ///
    "Weeks since experiment began" ///
    "Videos"

* Videos post midterm 2
plot_ts_legend tspostmid2 videos_post_mid2 ///
    "Videos relevant to final exam watched per week" ///
    "Weeks since experiment began" ///
    "Videos"



graph combine tsall tsunique tsduration, name(tscombo, replace) rows(3) ysize(6) xsize(5) ///
    altshrink iscale(1.5)

export_img tscombo

graph combine tspremid1 tsmid1mid2 tspostmid2, name(tscombo_exam, replace) rows(3) ysize(6) xsize(5) ///
    altshrink iscale(1.5)

export_img tscombo_exam

* Histogram of most videos watched in any week

capture restore
import delimited "./data/generated/id-year-weekoy-arm_level.csv", clear varnames(1)

* keep only those who finish final
keep if !mi(finalscore)

preserve
local filename = "histweek"
local w = 2
bys id year: egen max_videos_week = max(videos)
keep if weekoy == 1
twoway (hist max_videos_week if arm == 1, ///
        width(`w') color(navy%50) freq) ///
    (hist max_videos_week if arm == 2, ///
        width(`w') col(cranberry%50) freq), ///
    title("Most videos watched in one week by each student") ///
    legend(order(1 "Control" 2 "Treated") ring(0) pos(1) col(1)) ///
    xtitle("Videos") ///
    name(`filename', replace)

restore

preserve
local filename = "histweek_u"
local w = 2
bys id year: egen unique_videos_week = max(videosu) 
keep if weekoy == 1
twoway (hist unique_videos_week if arm == 1, ///
        width(`w') color(navy%50) freq) ///
    (hist unique_videos_week if arm == 2, ///
        width(`w') col(cranberry%50) freq), ///
    title("Most unique videos watched in one week by each student") ///
    legend(order(1 "Control" 2 "Treated") ring(0) pos(1) col(1)) ///
    xtitle("Videos") ///
    name(`filename', replace)

restore

* Histogram of most videos watched in any week before mid2
preserve
local filename = "histweekmid2"
keep if inrange(weekoy, 0, 3)
capture drop max_relevant_u_week
bys id year: egen max_relevant_u_week = max(videos)
keep if weekoy == 3
local w = 2
twoway (hist max_relevant_u_week if arm == 1, ///
        width(`w') color(navy%50) freq) ///
    (hist max_relevant_u_week if arm == 2, ///
        width(`w') col(cranberry%50) freq), ///
    title("Most videos watched in one week" "before Midterm 2") ///
    legend(order(1 "Control" 2 "Treated") ring(0) pos(1) col(1)) ///
    xtitle("Videos") ///
    name(`filename', replace)
restore

preserve
local filename = "histweekfinal"
keep if weekoy >= 4
capture drop max_relevant_u_week
bys id year: egen max_relevant_u_week = max(videos)
keep if weekoy == 4
local w = 2
twoway (hist max_relevant_u_week if arm == 1, ///
        width(`w') color(navy%50) freq) ///
    (hist max_relevant_u_week if arm == 2, ///
        width(`w') col(cranberry%50) freq), ///
    title("Most videos watched in one week" "between Midterm 2 and Final") ///
    legend(order(1 "Control" 2 "Treated") ring(0) pos(1) col(1)) ///
    xtitle("Videos") ///
    name(`filename', replace)
restore

preserve
keep if bothpairs_final

* final
local filename = "rdplotfinal"
qui sum mid1scorestd if arm == 2
local cutoff = r(max)
rdplot finalscorestd mid1scorestd i.year if arm != 1, ///
    c(`cutoff') p(2) kernel(tri) ci(95) shade nbins(10) ///
    graph_options(name(`filename', replace) ///
    title("Effect of Treatement (ITT) at the cutoff on Final exam scores") ///
    legend(off) xtitle("Normalized Midterm 1 score") ///
    ytitle("Normalized Final exam score"))
export_img `filename'
graph display

restore

preserve
keep if bothpairs_mid2

* midterm 2
local filename = "rdplotmid2"
qui sum mid1scorestd if arm == 2
local cutoff = r(max)
rdplot mid2scorestd mid1scorestd i.year if arm != 1, ///
    c(`cutoff') p(2) kernel(tri) ci(95) shade nbins(10) ///
    graph_options(name(`filename', replace) ///
    title("Effect of Treatement (ITT) at the cutoff on Midterm 2 scores") ///
    legend(off) xtitle("Normalized Midterm 1 score") ///
    ytitle("Normalized Midterm 2 score"))
export_img `filename'
graph display

restore

* Combine histograms

graph combine histweek histweek_u histweekmid2 histweekfinal, ///
    col(2) altshrink name(hist_maxweek)

export_img hist_maxweek



* Start with raw video data, collapse to arm-video level

* import and clean
import delimited ./data/raw/DeID_video-level_data.csv, clear varnames(1)
rename deid id
drop if length_mins == "NA"
drop if mi(id)
drop if syllabus_week == "NA"
destring visitid length_mins-syllabus_week, replace
gen video_duration_secs = 60 * minutes + seconds
keep id year videocode video_duration_secs incentivized-syllabus_week
gen views = 1

* collapse to student-video level
collapse (sum) views, by(id year videocode video_duration_secs incentivized-syllabus_week)

* merge arm
preserve
get_idyearlevel
// keep if complete experiment
keep if !mi(finalscore)
keep id year arm
tempfile temp
save `temp'
restore
// merge and drop videos watched by those not in sample
merge n:1 id year using `temp', nogen keep(2 3) 

* balance panel
bysort id year: gen idyear = 1 if _n == 1
replace idyear = sum(idyear)
drop id year
encode videocode, generate(vcode)
replace vcode = 1 if mi(vcode)
tsset idyear vcode
unique idyear vcode
unique idyear
unique vcode
local x = 789 * 73
di "Should have `x' observations after balancing."
tsfill, full
count
//tab vcode

* replace missings
drop videocode
bys idyear: ereplace arm = min(arm)
replace views = 0 if mi(views)
foreach v of varlist incentivized-video_duration_secs {
    bys vcode: ereplace `v' = min(`v')
}

sum

* collapse to arm-video level
drop idyear
gen conditional_views = views if views > 0
gen unique_views = views > 0
collapse (mean) unique_views views conditional_views, ///
    by(arm vcode incentivized-video_duration_secs)

label var unique_views "Perc. arm that saw video at least once"
label var views "Avg. views for that video by that arm"
label var conditional_views "Avg. views conditional on seeing the video at least once"

sum

help scheme files


*** Plot % of each arm viewing each video

* trim and reshape data for plotting
capture restore
preserve
keep if arm > 0
gen incent = incentivized > 0
label define incent 0 "Not incentivized" 1 "Incentivized"
label values incent incent
replace syllabus_week = syllabus_week + 1
reshape wide views unique_views conditional_views, i(vcode incentivized - video_duration_secs) j(arm)
order vcode video_duration_secs incent incentivized - syllabus_week unique_views* views* conditional_views*


* regression watch_rate = b0 + b1 * length + b2 * control_watch_rate
gen video_duration_mins = video_duration_secs / 60
sum video_duration_mins if incentivized
reg unique_views2 video_duration_mins unique_views1 if incentivized, robust
di -.0036438 * (19.93333 - 9.682639)

* ordered by incentives

capture drop ordering
sort unique_views1
bys incent: gen ordering = _n
local filename = "bar_uviews"
graph bar unique_views1 unique_views2, ///
    over(ordering, sort(1) lab(nolab)) over(incent) nofill ///
    bar(1, color(navy)) bar(2, color(cranberry)) ///
    legend(order(1 "Control" 2 "Treated") ring(0) ///
        col(1) pos(10) region(lstyle(none))) ///
    title("Fraction of arm viewing each video") ///
    ytitle("Fraction of arm") ///
    name(`filename', replace)
export_img `filename'


* ordered by syllabus_week

capture drop ordering
sort syllabus_week unique_views1
bys incent: gen ordering = _n
local filename = "bar_uviews_week"
graph bar unique_views1 unique_views2, ///
    over(ordering, sort(1) lab(nolab)) over(syllabus_week) nofill ///
    bar(1, color(navy)) bar(2, color(cranberry)) ///
    legend(order(1 "Control" 2 "Treated") ring(0) ///
        col(1) pos(10) region(lstyle(none))) ///
    title("Fraction of arm viewing each video") ///
    ytitle("Fraction of arm") ///
    b1title("Week of quarter") ///
    name(`filename', replace)
export_img `filename'


* ordered by video_duration

capture drop ordering
sort incent video_duration_secs
by incent: gen ordering = _n
local filename = "bar_uviews_duration"
graph bar unique_views1 unique_views2, ///
    over(ordering, lab(nolab)) over(incent) nofill ///
    bar(1, color(navy)) bar(2, color(cranberry)) ///
    legend(order(1 "Control" 2 "Treated") ring(0) ///
        col(1) pos(10) region(lstyle(none))) ///
    title("Fraction of arm viewing each video") ///
    ytitle("Fraction of arm") ///
    b1title("Week of quarter") ///
    name(`filename', replace)
export_img `filename'


* Total views per person

capture drop ordering
sort incent unique_views1
by incent: gen ordering = _n
local filename = "bar_views"
graph bar views1 views2, ///
    over(ordering, sort(1) lab(nolab)) over(incent) nofill ///
    bar(1, color(navy)) bar(2, color(cranberry)) ///
    legend(order(1 "Control" 2 "Treated") ring(0) ///
    col(1) pos(10) region(lstyle(none))) ///
    title("Views per person per video") ///
    ytitle("Views") ///
    name(`filename', replace)
export_img `filename'


* Conditional views per person

capture drop ordering
sort conditional_views1
bys incent: gen ordering = _n
local filename = "bar_cviews"
graph bar conditional_views1 conditional_views2, ///
    over(ordering, sort(1) lab(nolab)) over(incent) nofill ///
    bar(1, color(navy)) bar(2, color(cranberry)) ///
    legend(order(1 "Control" 2 "Treated") ring(0) ///
        col(1) pos(10) region(lstyle(none))) ///
    title("Views per person who watched at least once") ///
    ytitle("Views") ///
    name(`filename', replace)
export_img `filename'



restore

sum

* get data

get_idyearlevel
get_std_units
qui merge_winter_gpa
qui merge_dem
qui clean_dem
qui label_vars

* random number generated from random.org

ritest treated _b[treated], reps(5000) seed(84784) strata(year mid1scorestd): ///
    reg finalscorestd treated mid1scorestd i.year if arm > 0, robust

sum 

* repeat fixing pair assignments as strata

ritest treated _b[treated], reps(5000) seed(84784) strata(pairyear): ///
    reg finalscorestd treated mid1scorestd i.year if arm > 0, robust

* Randomization inference for midterm 2 as outcome

ritest treated _b[treated], reps(1000) seed(84784) strata(year mid1scorestd): ///
    reg mid2scorestd treated mid1scorestd i.year if arm > 0, robust

ritest treated _b[treated], reps(1000) seed(84784) strata(pairyear): ///
    reg mid2scorestd treated mid1scorestd i.year if arm > 0, robust




