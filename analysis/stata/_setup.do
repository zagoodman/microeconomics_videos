version 17
set more off
set varabbrev off

capture confirm file "data/generated/student_analysis_sample.csv"
if _rc {
    display as error "Run from the repository root with data/generated/ populated."
    exit 601
}

adopath ++ "analysis/stata/ado"

foreach cmd in ivreg2 ranktest weakiv weakivtest avar pdslasso ivlasso rlasso mhtreg ritest {
    quietly which `cmd'
}
mata: mata which mm_quantile()

* PDS control candidates (missing mathquiz scores are imputed to 0, matching 2019).
global ctrl_vars mathquizstd videos_mid1_u duration_mid1_u pset_pre ///
    transfer prev_cumgpa prev_cumgpa_unobs female asian latx white

global outcomes_mid2 videos_mid2_u videos_mid2 duration_mid2_u duration_mid2 mid2scorestd
global outcomes_final videos_final_u videos_final duration_final_u duration_final ///
    finalscorestd letter_option attendance pset_post ///
    piazza_questions piazza_answers piazza_views piazza_daysonline ///
    gpa_letter gpa_letter_sans100a gpa_letter_sansecon gpa_econ_sans100a ///
    units_letter units_pnp units_w ///
    nclass_p nclass_np nclass_w nclass_letter nclass_pnp pclass_letter pclass_pnp ///
    took100b ///
    winter_gpa_letter winter_gpa_letter_sans100a winter_gpa_letter_sansecon winter_gpa_econ_sans100a ///
    winter_units_letter winter_units_pnp winter_units_w ///
    winter_nclass_p winter_nclass_np winter_nclass_w ///
    winter_nclass_letter winter_nclass_pnp winter_pclass_letter winter_pclass_pnp
global outcomes_finalb videos_b videos_b_u duration_b duration_b_u finalbscorestd pass100b
global outcomes_mid1b mid1bscorestd
global outcomes_mid2b mid2bscorestd
global itt_exams mid2 final finalb mid1b mid2b
