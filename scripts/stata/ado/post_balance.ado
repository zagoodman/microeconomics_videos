program post_balance
    version 17
    syntax varlist, exam(name) sample(integer) arms(numlist)
    foreach v of local varlist {
        foreach arm of local arms {
            quietly summarize `v' if arm == `arm'
            frame post results ("`v'") (`arm') ("`exam'") (`sample') (r(mean)) (r(sd) / sqrt(r(N))) (r(N))
        }
    }
end
