program add_microb_exams
    version 17
    foreach exam in final mid1 mid2 {
        generate `exam'bscorestd = `exam'_100bstd
        mark_complete_pairs `exam'bscorestd bothpairs_`exam'b
    }
    * Pseudo-exam "enrollb" marks all Micro B enrollees, so Micro B video outcomes
    * (defined for every enrollee) are not restricted to Micro B final exam takers.
    generate enrollbscorestd = 0 if took100b == 1
    mark_complete_pairs enrollbscorestd bothpairs_enrollb
end
