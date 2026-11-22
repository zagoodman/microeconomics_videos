program load_analysis_data
    version 17
    quietly {
        import delimited "data/generated/student_analysis_sample.csv", clear varnames(1)
        _clean_sample
        standardize_scores
        _merge_student_file using "data/generated/student_demographics_winter.csv", ///
            prefix(winter_) keep(units_letter units_pnp units_w ///
            gpa_letter gpa_letter_sansecon gpa_letter_sans100a gpa_econ_sans100a ///
            nclass_letter nclass_np nclass_pnp nclass_p nclass_w)
        _merge_student_file using "data/generated/student_demographics_fall.csv"
        _derive_covariates
    }
end

program _clean_sample
    generate arm = treated + toberandomized
    drop toberandomized
    drop if missing(mid1score)
    label define arm 0 "Above median" 1 "Control" 2 "Treated"
    label values arm arm
    generate y2019 = year == 2019
    generate pairyear = year * 1000 + pair
    mark_complete_pairs mid2score bothpairs_mid2
    mark_complete_pairs finalscore bothpairs_final
    generate mathquiz_unobs = missing(mathquiz)
    replace mathquiz = 0 if mathquiz_unobs
end

program _merge_student_file
    syntax using/ [, prefix(name) keep(namelist)]
    preserve
    import delimited `"`using'"', clear varnames(1)
    if "`keep'" != "" {
        keep id year `keep'
        foreach v of local keep {
            rename `v' `prefix'`v'
        }
    }
    tempfile file
    save `file'
    restore
    merge 1:1 id year using `file', assert(match) nogenerate
end

program _derive_covariates
    generate male = gender == "m"
    generate female = gender == "f"
    generate othergen = gender == "u"

    generate chinese = ethnicity == "Chinese/Chinese-American"
    generate latx = ethnicity == "Chicanx/Latinx"
    generate oasian = ethnicity == "All Other Asian/Asian-American"
    generate viet = ethnicity == "Vietnamese"
    generate white = ethnicity == "White/Caucasian"
    generate othereth = !missing(ethnicity) & !(chinese | latx | oasian | viet | white)
    generate asian = chinese + oasian + viet

    generate prev_cumgpa_unobs = missing(prev_cumgpa)
    replace prev_cumgpa = 0 if prev_cumgpa_unobs // prev_cumgpa is interaction of obs * gpa

    generate pass = inlist(substr(assigned_grade, 1, 1), "A", "B", "C", "P") if !missing(finalscore)
    generate pass100b = inlist(substr(lettergrade_100b, 1, 1), "A", "B", "C") if !missing(lettergrade_100b)
    generate letter_option = inlist(substr(assigned_grade, 1, 1), "A", "B", "C", "D", "F") if !missing(finalscore)
    generate attendance = attend1 + attend2 + attend3 + attend4 + attend5 + attend6 + attend7

    * nclass_np (from registrar demographics CSVs) counts D, F, and NP grades only, excluding incompletes.
    foreach p in winter_ "" {
        generate `p'pclass_letter = `p'nclass_letter / (`p'nclass_letter + `p'nclass_pnp)
        generate `p'pclass_pnp = `p'nclass_pnp / (`p'nclass_letter + `p'nclass_pnp)
    }
end
