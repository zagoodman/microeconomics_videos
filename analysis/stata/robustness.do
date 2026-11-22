* Checks not reported in tables. Log output only.
version 17
do "analysis/stata/_setup.do"

load_analysis_data

* Missing prior GPA: zero plus indicator vs. mean imputation.
quietly summarize prev_cumgpa if !prev_cumgpa_unobs & arm > 0
generate prev_cumgpa_meanimp = cond(prev_cumgpa_unobs, r(mean), prev_cumgpa)
foreach gpa in "" "prev_cumgpa prev_cumgpa_unobs" "prev_cumgpa_meanimp" {
    regress finalscorestd treated mid1scorestd y2019 `gpa' if arm > 0
}

* Randomization inference within pairs, matching the design; seed from random.org.
preserve
keep if arm > 0
foreach exam in final mid2 {
    ritest treated _b[treated], reps(5000) seed(84784) strata(pairyear): ///
        regress `exam'scorestd treated mid1scorestd i.year, robust
}
restore

* Quantile treatment effects.
set seed 1887
foreach exam in final mid2 {
    sqreg `exam'scorestd treated mid1scorestd y2019 if arm > 0, quantile(.05 .25 .5 .75 .95) reps(500)
}
