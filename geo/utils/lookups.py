GEO_TYPES = [
    {
        "name": "city",
        "description": "city",
        "acs_sumlev": "160,170,060",
    },
    {
        "name": "state", 
        "description": "State",
        "acs_sumlev": "040",
    },
    {
        "name": "postal",
        "description": "Postal Code",
        "acs_sumlev": "160,170,060",
    },
    {
        "name": "state_fips",
        "description": "FIPS Code - State",
        "acs_sumlev": "040",
    },
    {
        "name": "state_county_fips",
        "description": "FIPS Code - State + County",
        "acs_sumlev": "050"
    },
    {
        "name": "zip_5",
        "description": "ZIP Code (5 digit)",
        "acs_sumlev": "850,860",
    },
    {
        "name": "zip_9",
        "description": "ZIP Code (5+4 digit",
        "acs_sumlev": "850,860",
    },
    # what is state postal code?
    #{
    #    "name": "state_postal",
    #    "description": "State Postal Code",
    #    "acs_sumlev": "040",
    #},
    {
        "name": "county",
        "description": "County",
        "acs_sumlev": "050"
    },
    {
        "name": "school_district",
        "description": "School District",
        "acs_sumlev": "950,960,970",
    },
    {
        "name": "congress_district",
        "description": "Congressional District Number",
        "acs_sumlev": "500", # Assuming US Congressional District
    },
    {
        "name": "census_tract",
        "description": "Census Tract",
        "acs_sumlev": "140",
    },
    {
        "name": "census_blockgroup",
        "description": "Census Block Group",
        "acs_sumlev": "150",
    },
    {
        "name": "census_block",
        "description": "Census Block",
        "acs_sumlev": "101",
    },
]

ACS_DATA_TYPES = {
    "total_pop": {
        "human_name": "Total population",
        "table_id": "B01003",
    },
    "median_hh_income": {
        "human_name": "Median household income",
        "table_id": "B19013",
    },
    "per_capita_income": {
        "human_name": "Per capita income",
        "table_id": "B19301",
    },
    "pop_percent_by_race": {
        "human_name": "Population percentage by race",
        "table_id": "B02001", 
    },
    # This is going to need to be derived from something else
    # "percent_minority": "",
    "median_age": {
        "human_name": "Median age",
        "table_id": "B01002",
    },
    "education": {
        "human_name": "Educational attainment",
        "table_id": "B15002",
    },
    "median_val_oo_housing": {
        "human_name": "Median value owner occupied housing",
        "table_id": "B25077",
    },
    "group_quarters_pop": {
        "human_name": "Group quarters population",
        "table_id": "B26001",
    },
    "unmarried_hh_by_sex": {
        "human_name": "Unmarried-partner households by sex of partner",
        "table_id": "B11009",
    },
    "place_of_birth": {
        "human_name": "Place of birth (foreign-born population)",
        "table_id": "B05006",
    },
}

# There are certain things that seem to be
# counted better in 10-year census

TEN_YEAR_DATA_TYPES = {
    "Average family size": "",
}
