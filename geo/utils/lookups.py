GEO_TYPES = {
    "state_city_name": "City Name + State Name",
    "state_name": "State Name",
    "state_city_postal": "City + State Postal Code",
    "state_fips": "State FIPS Code",
    "state_county_fips": "State + County FIPS Codes",
    "zip_5": "5-digit ZIP Code",
    "zip_9": "ZIP+4 Code",
    "state_postal": "State Postal Code",
    "state_county_postal": "State Postal Code + County Name",
    "state_county_name": "Full State Name + County Name",
    "state_school_postal": "State Postal Code + School District Name",
    "state_congress_postal": "State Postal Code + Congressional District Number",
    "census_tract": "State FIPS + County FIPS + Census Tract",
    "census_blockgroup": "State FIPS + County FIPS + Census Block Group",
    "census_block": "State FIPS + County FIPS + Census Block",
}

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
