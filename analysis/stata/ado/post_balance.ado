program post_balance
    version 17
    syntax varlist, exam(name) sample(integer) arms(numlist) [frame(name) year(integer 0)]
    if "`frame'" == "" local frame results
    foreach v of local varlist {
        capture quietly ttest `v' if arm > 0, by(arm) unequal
        local p = cond(_rc == 0, r(p), .)
        foreach arm of local arms {
            quietly summarize `v' if arm == `arm'
            if `year' > 0 {
                frame post `frame' ("`v'") (`arm') ("`exam'") (`sample') ///
                    (r(mean)) (r(sd) / sqrt(r(N))) (r(N)) (`p') (`year')
            }
            else {
                frame post `frame' ("`v'") (`arm') ("`exam'") (`sample') ///
                    (r(mean)) (r(sd) / sqrt(r(N))) (r(N)) (`p')
            }
        }
    }
end
