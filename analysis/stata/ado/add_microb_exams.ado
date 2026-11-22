program add_microb_exams
    version 17
    foreach exam in final mid1 mid2 {
        generate `exam'bscorestd = `exam'_100bstd
        mark_complete_pairs `exam'bscorestd bothpairs_`exam'b
    }
end
