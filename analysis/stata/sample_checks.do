* Attrition, treatment-awareness quiz and incentive take-up. Log output only.
version 17
do "analysis/stata/_setup.do"

load_analysis_data

tabulate treated arm
tabulate treated arm if !missing(assigned_grade)
tabulate treated arm if !missing(assigned_grade) & !missing(mid2score)
tabulate treated arm if !missing(assigned_grade) & !missing(finalscore)
tabulate treated arm if !missing(assigned_grade) & took100b
tabulate assigned_grade arm if missing(mid2score), missing
tabulate assigned_grade arm if missing(finalscore) & !missing(mid2score), missing

preserve
keep if !missing(assigned_grade) & arm > 0
generate attrit_mid2 = missing(mid2score)
generate attrit_final = missing(finalscore)
generate attrit_microb = took100b == 0
foreach v of varlist attrit_* {
    tabulate `v' arm, column
    ttest `v', by(arm) unequal
}
regress took100b treated mid1scorestd y2019
restore

* In-class quiz: which grading scheme are you on? (assembled by construction/assemble_data.py)
preserve
import delimited "data/generated/treatment_awareness_quiz.csv", clear varnames(1) stringcols(1)
tempfile quiz
save `quiz', replace
restore

merge 1:1 id year using `quiz', keep(master match) nogenerate
tabulate quiz_treated arm
generate quiz_correct = quiz_treated == treated if !missing(quiz_treated)
summarize quiz_correct

generate met_incentive = videos_incent_counts_u >= 40 if !missing(videos_incent_counts_u)
tabstat met_incentive if !missing(finalscore), by(arm)
