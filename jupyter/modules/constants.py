from datetime import datetime

MERGE_KEYS = ["id", "year"]

# Maps raw column names (lowercased) to canonical names used throughout the pipeline.
# Covers all variants seen across the different raw Excel files.
COLUMN_RENAME_MAP = {
    # id variants
    "de id": "id",
    "deid": "id",
    # year variants
    "year_econ": "year",
    "year - econ 100a": "year",
    "year - econ100a": "year",
    "year-econ100a": "year",
    "year-zack": "year",
    # term variants
    "term_code_econ": "term",
    "term-econ100a": "term",
    # other fields
    "term code courses": "term_courses",
    "term_precoursegpa": "term_pregpa",
    "term code econ 100a": "termecon",
    "previous_cum_gpa": "prev_cumgpa",
    "apct_type_desc": "apptype",
    "ethnicity_grouped": "ethnicity",
    "gender": "gender",
    "measure names": "measure",
    "measure values": "values",
    # GPA/units columns (from pivot table)
    "class units - letter grade": "units_letter",
    "class units - p/np": "units_pnp",
    "class units - withdrawn": "units_w",
    "gpa - classes letter grade": "gpa_letter",
    "gpa - classes letter grade - no econ": "gpa_letter_sansecon",
    "gpa - classes letter grade - no econ 100a": "gpa_letter_sans100a",
    "gpa - classes letter grade - only econ - no econ 100a": "gpa_econ_sans100a",
    "n classes - letter grade": "nclass_letter",
    "n classes - not passed": "nclass_np",
    "n classes - p/np": "nclass_pnp",
    "n classes - passed": "nclass_p",
    "n classes - withdrawn": "nclass_w",
}

EXAM_DATES = {
    2018: {
        "mid1": datetime(2018, 10, 19, 19, 20),
        "mid2": datetime(2018, 11, 19, 19, 20),
        "final": datetime(2018, 12, 8, 18, 0),
    },
    2019: {
        "mid1": datetime(2019, 10, 23, 21, 20),
        "mid2": datetime(2019, 11, 13, 21, 20),
        "final": datetime(2019, 12, 7, 14, 30),
    },
}

ZERO_FILL_COLS_CONCURRENT = ["units_pnp", "units_w"]

ZERO_FILL_COLS_FOLLOWING = [
    "units_letter",
    "units_pnp",
    "units_w",
    "nclass_letter",
    "nclass_np",
    "nclass_pnp",
    "nclass_p",
    "nclass_w",
]
