"""
Merges all COVID-19 data into a 'megafile';
- Follows a long format of 1 row per country & date, and variables as columns;
- Published in CSV, XLSX, and JSON formats;
- Includes derived variables that can't be easily calculated, such as X per capita;
- Includes country ISO codes in a column next to country names.
"""

import json
import os
from datetime import datetime, date, timedelta
from functools import reduce
import yaml

import numpy as np
import pandas as pd

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "input"))
GRAPHER_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "grapher"))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "public", "data"))
TIMESTAMP_DIR = os.path.abspath(os.path.join(DATA_DIR, "internal", "timestamp"))
ANNOTATIONS_PATH = os.path.abspath(
    os.path.join(CURRENT_DIR, "annotations_internal.yaml")
)


def get_jhu():
    """
    Reads each COVID-19 JHU dataset located in /public/data/jhu/
    Melts the dataframe to vertical format (1 row per country and date)
    Merges all JHU dataframes into one with outer joins

    Returns:
        jhu {dataframe}
    """

    jhu_variables = [
        "total_cases",
        "new_cases",
        "weekly_cases",
        "total_deaths",
        "new_deaths",
        "weekly_deaths",
        "total_cases_per_million",
        "new_cases_per_million",
        "weekly_cases_per_million",
        "total_deaths_per_million",
        "new_deaths_per_million",
        "weekly_deaths_per_million",
    ]

    data_frames = []

    # Process each file and melt it to vertical format
    for jhu_var in jhu_variables:
        tmp = pd.read_csv(
            os.path.join(DATA_DIR, f"../../public/data/jhu/{jhu_var}.csv")
        )
        country_cols = list(tmp.columns)
        country_cols.remove("date")

        # Carrying last observation forward for International totals to avoid discrepancies
        if jhu_var[:5] == "total":
            tmp = tmp.sort_values("date")
            tmp["International"] = tmp["International"].ffill()

        tmp = (
            pd.melt(tmp, id_vars="date", value_vars=country_cols)
            .rename(columns={"value": jhu_var, "variable": "location"})
            .dropna()
        )

        # Exclude entities from megafile
        tmp = tmp[tmp.location != "2020 Summer Olympics athletes & staff"]

        if jhu_var[:7] == "weekly_":
            tmp[jhu_var] = tmp[jhu_var].div(7).round(3)
            tmp = tmp.rename(
                errors="ignore",
                columns={
                    "weekly_cases": "new_cases_smoothed",
                    "weekly_deaths": "new_deaths_smoothed",
                    "weekly_cases_per_million": "new_cases_smoothed_per_million",
                    "weekly_deaths_per_million": "new_deaths_smoothed_per_million",
                },
            )
        else:
            tmp[jhu_var] = tmp[jhu_var].round(3)
        data_frames.append(tmp)
    print()

    # Outer join between all files
    jhu = reduce(
        lambda left, right: pd.merge(left, right, on=["date", "location"], how="outer"),
        data_frames,
    )

    return jhu


def get_reprod():
    reprod = pd.read_csv(
        "https://github.com/crondonm/TrackingR/raw/main/Estimates-Database/database.csv",
        usecols=["Country/Region", "Date", "R", "days_infectious"],
    )
    reprod = (
        reprod[reprod["days_infectious"] == 7]
        .drop(columns=["days_infectious"])
        .rename(
            columns={
                "Country/Region": "location",
                "Date": "date",
                "R": "reproduction_rate",
            }
        )
        .round(2)
    )
    mapping = pd.read_csv(
        os.path.join(INPUT_DIR, "reproduction/reprod_country_standardized.csv")
    )
    reprod = reprod.replace(dict(zip(mapping.reprod, mapping.owid)))
    return reprod


def get_hosp():
    hosp = pd.read_csv(os.path.join(GRAPHER_DIR, "COVID-2019 - Hospital & ICU.csv"))
    hosp = hosp.rename(
        columns={
            "Country": "location",
            "Year": "date",
            "Daily ICU occupancy": "icu_patients",
            "Daily ICU occupancy per million": "icu_patients_per_million",
            "Daily hospital occupancy": "hosp_patients",
            "Daily hospital occupancy per million": "hosp_patients_per_million",
            "Weekly new ICU admissions": "weekly_icu_admissions",
            "Weekly new ICU admissions per million": "weekly_icu_admissions_per_million",
            "Weekly new hospital admissions": "weekly_hosp_admissions",
            "Weekly new hospital admissions per million": "weekly_hosp_admissions_per_million",
        }
    ).round(3)
    hosp.loc[:, "date"] = (
        ([pd.to_datetime("2020-01-21")] * hosp.shape[0])
        + hosp["date"].apply(pd.offsets.Day)
    ).astype(str)
    return hosp


def get_vax():
    vax = pd.read_csv(
        os.path.join(DATA_DIR, "vaccinations/vaccinations.csv"),
        usecols=[
            "location",
            "date",
            "total_vaccinations",
            "total_vaccinations_per_hundred",
            "daily_vaccinations_raw",
            "daily_vaccinations",
            "daily_vaccinations_per_million",
            "people_vaccinated",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated",
            "people_fully_vaccinated_per_hundred",
        ],
    )
    vax = vax.rename(
        columns={
            "daily_vaccinations_raw": "new_vaccinations",
            "daily_vaccinations": "new_vaccinations_smoothed",
            "daily_vaccinations_per_million": "new_vaccinations_smoothed_per_million",
        }
    )
    vax["total_vaccinations_per_hundred"] = vax["total_vaccinations_per_hundred"].round(
        3
    )
    vax["people_vaccinated_per_hundred"] = vax["people_vaccinated_per_hundred"].round(3)
    vax["people_fully_vaccinated_per_hundred"] = vax[
        "people_fully_vaccinated_per_hundred"
    ].round(3)
    return vax


def get_testing():
    """
    Reads the main COVID-19 testing dataset located in /public/data/testing/
    Rearranges the Entity column to separate location from testing units
    Checks for duplicated location/date couples, as we can have more than 1 time series per country

    Returns:
        testing {dataframe}
    """

    testing = pd.read_csv(
        os.path.join(DATA_DIR, "testing/covid-testing-all-observations.csv"),
        usecols=[
            "Entity",
            "Date",
            "Cumulative total",
            "Daily change in cumulative total",
            "7-day smoothed daily change",
            "Cumulative total per thousand",
            "Daily change in cumulative total per thousand",
            "7-day smoothed daily change per thousand",
            "Short-term positive rate",
            "Short-term tests per case",
        ],
    )

    testing = testing.rename(
        columns={
            "Entity": "location",
            "Date": "date",
            "Cumulative total": "total_tests",
            "Daily change in cumulative total": "new_tests",
            "7-day smoothed daily change": "new_tests_smoothed",
            "Cumulative total per thousand": "total_tests_per_thousand",
            "Daily change in cumulative total per thousand": "new_tests_per_thousand",
            "7-day smoothed daily change per thousand": "new_tests_smoothed_per_thousand",
            "Short-term positive rate": "positive_rate",
            "Short-term tests per case": "tests_per_case",
        }
    )

    testing[
        [
            "total_tests_per_thousand",
            "new_tests_per_thousand",
            "new_tests_smoothed_per_thousand",
            "tests_per_case",
            "positive_rate",
        ]
    ] = testing[
        [
            "total_tests_per_thousand",
            "new_tests_per_thousand",
            "new_tests_smoothed_per_thousand",
            "tests_per_case",
            "positive_rate",
        ]
    ].round(
        3
    )

    # Split the original entity into location and testing units
    testing[["location", "tests_units"]] = testing.location.str.split(
        " - ", expand=True
    )

    # For locations with >1 series, choose a series
    to_remove = pd.read_csv(
        os.path.join(INPUT_DIR, "owid/secondary_testing_series.csv")
    )
    for loc, unit in to_remove.itertuples(index=False, name=None):
        testing = testing[
            -((testing["location"] == loc) & (testing["tests_units"] == unit))
        ]

    # Check for remaining duplicates of location/date
    duplicates = testing.groupby(["location", "date"]).size().to_frame("n")
    duplicates = duplicates[duplicates["n"] > 1]
    if duplicates.shape[0] > 0:
        print(duplicates)
        raise Exception("Multiple rows for the same location and date")

    # Remove observations for current day to avoid rows with testing data but no case/deaths
    testing = testing[testing["date"] < str(date.today())]

    return testing


def add_macro_variables(complete_dataset, macro_variables):
    """
    Appends a list of 'macro' (non-directly COVID related) variables to the dataset
    The data is denormalized, i.e. each yearly value (for example GDP per capita)
    is added to each row of the complete dataset. This is meant to facilitate the use
    of our dataset by non-experts.
    """
    original_shape = complete_dataset.shape

    for var, file in macro_variables.items():
        var_df = pd.read_csv(os.path.join(INPUT_DIR, file), usecols=["iso_code", var])
        var_df = var_df[-var_df["iso_code"].isnull()]
        var_df[var] = var_df[var].round(3)
        complete_dataset = complete_dataset.merge(var_df, on="iso_code", how="left")

    assert complete_dataset.shape[0] == original_shape[0]
    assert complete_dataset.shape[1] == original_shape[1] + len(macro_variables)

    return complete_dataset


def get_cgrt():
    """
    Downloads the latest OxCGRT dataset from BSG's GitHub repository
    Remaps BSG country names to OWID country names

    Returns:
        cgrt {dataframe}
    """

    cgrt = pd.read_csv(os.path.join(INPUT_DIR, "bsg/latest.csv"), low_memory=False)

    if "RegionCode" in cgrt.columns:
        cgrt = cgrt[cgrt.RegionCode.isnull()]

    cgrt = cgrt[["CountryName", "Date", "StringencyIndex"]]

    cgrt.loc[:, "Date"] = pd.to_datetime(cgrt["Date"], format="%Y%m%d").dt.date.astype(
        str
    )

    country_mapping = pd.read_csv(
        os.path.join(INPUT_DIR, "bsg/bsg_country_standardised.csv")
    )

    cgrt = country_mapping.merge(cgrt, on="CountryName", how="right")

    missing_from_mapping = cgrt[cgrt["Country"].isna()]["CountryName"].unique()
    if len(missing_from_mapping) > 0:
        raise Exception(f"Missing countries in OxCGRT mapping: {missing_from_mapping}")

    cgrt = cgrt.drop(columns=["CountryName"])

    rename_dict = {
        "Country": "location",
        "Date": "date",
        "StringencyIndex": "stringency_index",
    }

    cgrt = cgrt.rename(columns=rename_dict)

    return cgrt


def add_excess_mortality(df: pd.DataFrame) -> pd.DataFrame:
    xm = pd.read_csv(
        os.path.join(DATA_DIR, "excess_mortality/excess_mortality.csv"),
        usecols=["location", "date", "p_scores_all_ages"],
    )
    df = df.merge(xm, how="left", on=["location", "date"]).rename(
        columns={"p_scores_all_ages": "excess_mortality"}
    )
    return df


def dict_to_compact_json(d: dict):
    """
    Encodes a Python dict into valid, minified JSON.
    """
    return json.dumps(
        d,
        # Use separators without any trailing whitespace to minimize file size.
        # The defaults (", ", ": ") contain a trailing space.
        separators=(",", ":"),
        # The json library by default encodes NaNs in JSON, but this is invalid JSON.
        # By having this False, an error will be thrown if a NaN exists in the data.
        allow_nan=False,
    )


def df_to_json(complete_dataset, output_path, static_columns):
    """
    Writes a JSON version of the complete dataset, with the ISO code at the root.
    NA values are dropped from the output.
    Macro variables are normalized by appearing only once, at the root of each ISO code.
    """
    megajson = {}

    static_columns = ["continent", "location"] + list(static_columns)

    complete_dataset = complete_dataset.dropna(axis="rows", subset=["iso_code"])

    for iso in complete_dataset.iso_code.unique():
        country_df = complete_dataset[complete_dataset.iso_code == iso].drop(
            columns=["iso_code"]
        )
        static_data = country_df.head(1)[static_columns].to_dict("records")[0]
        megajson[iso] = {k: v for k, v in static_data.items() if pd.notnull(v)}
        megajson[iso]["data"] = [
            {k: v for k, v in r.items() if pd.notnull(v)}
            for r in country_df.drop(columns=static_columns).to_dict("records")
        ]

    with open(output_path, "w") as file:
        file.write(dict_to_compact_json(megajson))


def df_to_columnar_json(complete_dataset, output_path):
    """
    Writes a columnar JSON version of the complete dataset.
    NA values are dropped from the output.

    In columnar JSON, the table headers are keys, and the values are lists
    of all cells for a column.
    Example:
        {
            "iso_code": ["AFG", "AFG", ... ],
            "date": ["2020-03-01", "2020-03-02", ... ]
        }
    """
    # Replace NaNs with None in order to be serializable to JSON.
    # JSON doesn't support NaNs, but it does have null which is represented as None in Python.
    columnar_dict = complete_dataset.to_dict(orient="list")
    for k, v in columnar_dict.items():
        columnar_dict[k] = [x if pd.notnull(x) else None for x in v]
    with open(output_path, "w") as file:
        file.write(dict_to_compact_json(columnar_dict))


def create_latest(df):

    df = df[df.date >= str(date.today() - timedelta(weeks=2))]
    df = df.sort_values("date")

    latest = [
        df[df.location == loc].ffill().tail(1).round(3) for loc in set(df.location)
    ]
    latest = pd.concat(latest)
    latest = latest.sort_values("location").rename(
        columns={"date": "last_updated_date"}
    )

    print("Writing latest version…")
    latest.to_csv(os.path.join(DATA_DIR, "latest/owid-covid-latest.csv"), index=False)
    latest.to_excel(
        os.path.join(DATA_DIR, "latest/owid-covid-latest.xlsx"), index=False
    )
    latest.dropna(subset=["iso_code"]).set_index("iso_code").to_json(
        os.path.join(DATA_DIR, "latest/owid-covid-latest.json"), orient="index"
    )


internal_files_columns = {
    "cases-tests": [
        "location",
        "date",
        "total_cases",
        "new_cases",
        "new_cases_smoothed",
        "total_cases_per_million",
        "new_cases_per_million",
        "new_cases_smoothed_per_million",
        "reproduction_rate",
        "new_tests",
        "total_tests",
        "total_tests_per_thousand",
        "new_tests_per_thousand",
        "new_tests_smoothed",
        "new_tests_smoothed_per_thousand",
        "positive_rate",
        "tests_per_case",
        "tests_units",
        "stringency_index",
    ],
    "deaths": [
        "continent",
        "location",
        "date",
        "total_deaths",
        "new_deaths",
        "new_deaths_smoothed",
        "total_deaths_per_million",
        "new_deaths_per_million",
        "new_deaths_smoothed_per_million",
        "cfr",
        "cfr_short_term",
    ],
    "vaccinations": [
        "location",
        "date",
        "total_vaccinations",
        "people_vaccinated",
        "people_fully_vaccinated",
        "new_vaccinations",
        "new_vaccinations_smoothed",
        "total_vaccinations_per_hundred",
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "new_vaccinations_smoothed_per_million",
        "population",
        "people_partly_vaccinated",
        "people_partly_vaccinated_per_hundred",
    ],
    "hospital-admissions": [
        "location",
        "date",
        "icu_patients",
        "icu_patients_per_million",
        "hosp_patients",
        "hosp_patients_per_million",
        "weekly_icu_admissions",
        "weekly_icu_admissions_per_million",
        "weekly_hosp_admissions",
        "weekly_hosp_admissions_per_million",
    ],
    "excess-mortality": [
        "location",
        "date",
        "excess_mortality",
    ],
    "auxiliary": [
        "iso_code",
        "continent",
        "location",
        "date",
        "population_density",
        "median_age",
        "aged_65_older",
        "aged_70_older",
        "gdp_per_capita",
        "extreme_poverty",
        "cardiovasc_death_rate",
        "diabetes_prevalence",
        "female_smokers",
        "male_smokers",
        "handwashing_facilities",
        "hospital_beds_per_thousand",
        "life_expectancy",
        "human_development_index",
    ],
}


class AnnotatorInternal:
    """Adds annotations column.

    Uses attribute `config` to add annotations. Its format should be as:
    ```
    {
        "vaccinations": [{
            'annotation_text': 'Data for China added on Jun 10',
            'location': ['World', 'Asia', 'Upper middle income'],
            'date': '2020-06-10'
        }],
        "case-tests": [{
            'annotation_text': 'something',
            'location': ['World', 'Asia', 'Upper middle income'],
            'date': '2020-06-11'
        }],
    }
    ```

    Keys in config should match those in `internal_files_columns`.
    """

    def __init__(self, config: dict):
        self.config = config

    @classmethod
    def from_yaml(cls, path):
        with open(path, "r") as f:
            dix = yaml.safe_load(f)
        return cls(dix)

    @property
    def streams(self):
        return list(self.config.keys())

    def add_annotations(self, df: pd.DataFrame, stream: str) -> pd.DataFrame:
        if stream in self.streams:
            print(f"Adding annotation for {stream}")
            return self._add_annotations(df, stream)
        return df

    def _add_annotations(self, df: pd.DataFrame, stream: str) -> pd.DataFrame:
        df = df.assign(annotations=pd.NA)
        conf = self.config[stream]
        for c in conf:
            if not ("location" in c and "annotation_text" in c):
                raise ValueError(
                    f"Missing field in {stream} (`location` and `annotation_text` are required)."
                )
            if isinstance(c["location"], str):
                mask = df.location == c["location"]
            elif isinstance(c["location"], list):
                mask = df.location.isin(c["location"])
            if "date" in c:
                mask = mask & (df.date >= c["date"])
            df.loc[mask, "annotations"] = c["annotation_text"]
        return df


def create_internal(df):

    dir_path = os.path.join(DATA_DIR, "internal")
    # Ensure internal/ dir is created
    os.makedirs(dir_path, exist_ok=True)

    # These are "key" or "attribute" columns.
    # These columns are ignored when dropping rows with dropna().
    non_value_columns = ["iso_code", "continent", "location", "date", "population"]

    # Load annotations
    annotator = AnnotatorInternal.from_yaml(ANNOTATIONS_PATH)

    # Copy df
    df = df.copy()
    # Insert CFR column to avoid calculating it on the client, and enable
    # splitting up into cases & deaths columns.
    df["cfr"] = (df["total_deaths"] * 100 / df["total_cases"]).round(3)

    # Insert short-term CFR
    cfr_day_shift = 10  # We compute number of deaths divided by number of cases `cfr_day_shift` days before.
    shifted_cases = (
        df.sort_values("date").groupby("location")["new_cases_smoothed"].shift(cfr_day_shift)
    )
    df["cfr_short_term"] = (
        df["new_deaths_smoothed"]
        .div(shifted_cases)
        .replace(np.inf, np.nan)
        .replace(-np.inf, np.nan)
        .mul(100)
        .round(4)
    )
    df.loc[
        (df.cfr_short_term < 0)
        | (df.cfr_short_term > 10)
        | (df.date.astype(str) < "2020-09-01"),
        "cfr_short_term",
    ] = pd.NA
    
    # Add partly vaccinated
    dfg = df.groupby("location")
    df["people_partly_vaccinated"] = (
        dfg.people_vaccinated.ffill() - dfg.people_fully_vaccinated.ffill().fillna(0)).apply(lambda x: max(x, 0)
    )
    df["people_partly_vaccinated_per_hundred"] = df["people_partly_vaccinated"]/df["population"] * 100

    # Export
    for name, columns in internal_files_columns.items():
        output_path = os.path.join(dir_path, f"megafile--{name}.json")
        value_columns = list(set(columns) - set(non_value_columns))
        df_output = df[columns].dropna(subset=value_columns, how="all")
        df_output = annotator.add_annotations(df_output, name)
        df_to_columnar_json(df_output, output_path)


def generate_megafile():

    print("\nFetching JHU dataset…")
    jhu = get_jhu()

    print("\nFetching reproduction rate…")
    reprod = get_reprod()

    location_mismatch = set(reprod.location).difference(set(jhu.location))
    for loc in location_mismatch:
        print(
            f"<!> Location '{loc}' has reproduction rates but is absent from JHU data"
        )

    print("\nFetching hospital dataset…")
    hosp = get_hosp()

    location_mismatch = set(hosp.location).difference(set(jhu.location))
    for loc in location_mismatch:
        print(f"<!> Location '{loc}' has hospital data but is absent from JHU data")

    print("\nFetching testing dataset…")
    testing = get_testing()

    location_mismatch = set(testing.location).difference(set(jhu.location))
    for loc in location_mismatch:
        print(f"<!> Location '{loc}' has testing data but is absent from JHU data")

    print("\nFetching vaccination dataset…")
    vax = get_vax()
    vax = vax[
        -vax.location.isin(
            [
                "England",
                "Northern Ireland",
                "Scotland",
                "Wales",
                "High income",
                "Upper middle income",
                "Lower middle income",
                "Low income",
            ]
        )
    ]

    print("\nFetching OxCGRT dataset…")
    cgrt = get_cgrt()

    all_covid = (
        jhu.merge(reprod, on=["date", "location"], how="left")
        .merge(hosp, on=["date", "location"], how="outer")
        .merge(testing, on=["date", "location"], how="outer")
        .merge(vax, on=["date", "location"], how="outer")
        .merge(cgrt, on=["date", "location"], how="left")
        .sort_values(["location", "date"])
    )

    # Add ISO codes
    print("Adding ISO codes…")
    iso_codes = pd.read_csv(os.path.join(INPUT_DIR, "iso/iso3166_1_alpha_3_codes.csv"))

    missing_iso = set(all_covid.location).difference(set(iso_codes.location))
    if len(missing_iso) > 0:
        print(missing_iso)
        raise Exception("Missing ISO code for some locations")

    all_covid = iso_codes.merge(all_covid, on="location")

    # Add continents
    print("Adding continents…")
    continents = pd.read_csv(
        os.path.join(INPUT_DIR, "owid/continents.csv"),
        names=["_1", "iso_code", "_2", "continent"],
        usecols=["iso_code", "continent"],
        header=0,
    )

    all_covid = continents.merge(all_covid, on="iso_code", how="right")

    # Add macro variables
    # - the key is the name of the variable of interest
    # - the value is the path to the corresponding file
    macro_variables = {
        "population": "un/population_2020.csv",
        "population_density": "wb/population_density.csv",
        "median_age": "un/median_age.csv",
        "aged_65_older": "wb/aged_65_older.csv",
        "aged_70_older": "un/aged_70_older.csv",
        "gdp_per_capita": "wb/gdp_per_capita.csv",
        "extreme_poverty": "wb/extreme_poverty.csv",
        "cardiovasc_death_rate": "gbd/cardiovasc_death_rate.csv",
        "diabetes_prevalence": "wb/diabetes_prevalence.csv",
        "female_smokers": "wb/female_smokers.csv",
        "male_smokers": "wb/male_smokers.csv",
        "handwashing_facilities": "un/handwashing_facilities.csv",
        "hospital_beds_per_thousand": "owid/hospital_beds.csv",
        "life_expectancy": "owid/life_expectancy.csv",
        "human_development_index": "un/human_development_index.csv",
    }
    all_covid = add_macro_variables(all_covid, macro_variables)

    # Add excess mortality
    all_covid = add_excess_mortality(all_covid)

    # Sort by location and date
    all_covid = all_covid.sort_values(["location", "date"])

    # Check that we only have 1 unique row for each location/date pair
    assert (
        all_covid.drop_duplicates(subset=["location", "date"]).shape == all_covid.shape
    )

    # Create light versions of complete dataset with only the latest data point
    create_latest(all_covid)

    print("Writing to CSV…")
    all_covid.to_csv(os.path.join(DATA_DIR, "owid-covid-data.csv"), index=False)

    print("Writing to XLSX…")
    all_covid.to_excel(
        os.path.join(DATA_DIR, "owid-covid-data.xlsx"), index=False, engine="xlsxwriter"
    )

    print("Writing to JSON…")
    df_to_json(
        all_covid,
        os.path.join(DATA_DIR, "owid-covid-data.json"),
        macro_variables.keys(),
    )

    print("Creating internal files…")
    create_internal(all_covid)

    # Store the last updated time
    timestamp_filename = os.path.join(
        DATA_DIR, "owid-covid-data-last-updated-timestamp.txt"
    )  # @deprecate
    export_timestamp(timestamp_filename)  # @deprecate
    timestamp_filename = os.path.join(
        TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-root.txt"
    )
    export_timestamp(timestamp_filename)

    print("All done!")


def export_timestamp(timestamp_filename):
    with open(timestamp_filename, "w") as timestamp_file:
        timestamp_file.write(datetime.utcnow().replace(microsecond=0).isoformat())


if __name__ == "__main__":
    generate_megafile()
