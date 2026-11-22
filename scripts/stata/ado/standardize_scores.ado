* Midterm 1 is centered at the assignment cutoff (top randomized score in each year);
* other scores at the Control mean. All are scaled by the Control SD in each year.
program standardize_scores
    version 17
    quietly levelsof year, local(years)
    capture drop mid1scorestd
    generate mid1scorestd = .
    foreach y of local years {
        quietly summarize mid1score if year == `y' & arm >= 1
        local cutoff = r(max)
        quietly summarize mid1score if year == `y' & arm == 1
        replace mid1scorestd = (mid1score - `cutoff') / r(sd) if year == `y'
    }

    local scores mathquiz mid2score finalscore
    capture confirm variable mid1_100b, exact
    if !_rc local scores `scores' mid1_100b mid2_100b final_100b
    foreach v of local scores {
        capture drop `v'std
        generate `v'std = .
        foreach y of local years {
            quietly summarize `v' if year == `y' & arm == 1
            replace `v'std = (`v' - r(mean)) / r(sd) if year == `y'
        }
    }
end
