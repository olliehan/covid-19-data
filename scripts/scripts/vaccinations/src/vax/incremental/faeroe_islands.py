import requests

import pandas as pd

from vax.utils.utils import clean_count
from vax.utils.incremental import enrich_data, increment
from vax.utils.dates import localdate


class FaeroeIslands:
    def __init__(self, source_url: str, location: str, source_url_ref: str):
        self.source_url = source_url
        self.source_url_ref = source_url_ref
        self.location = location

    def read(self) -> pd.Series:
        data = requests.get(self.source_url).json()["stats"]
        return pd.DataFrame.from_records(data).iloc[0]

    def pipe_metrics(self, ds: pd.Series) -> pd.Series:
        ds = enrich_data(
            ds, "people_vaccinated", clean_count(ds["first_vaccine_number"])
        )
        ds = enrich_data(
            ds, "people_fully_vaccinated", clean_count(ds["second_vaccine_number"])
        )
        total_vaccinations = ds["people_vaccinated"] + ds["people_fully_vaccinated"]
        return enrich_data(ds, "total_vaccinations", total_vaccinations)

    def pipe_format_date(self, ds: pd.Series) -> pd.Series:
        date = localdate("Atlantic/Faeroe")
        return enrich_data(ds, "date", date)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Moderna, Pfizer/BioNTech")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url_ref)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return (
            ds.pipe(self.pipe_metrics)
            .pipe(self.pipe_format_date)
            .pipe(self.pipe_location)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_source)
        )

    def to_csv(self, paths):
        data = self.read().pipe(self.pipeline)
        increment(
            paths=paths,
            location=str(data["location"]),
            total_vaccinations=int(data["total_vaccinations"]),
            people_vaccinated=int(data["people_vaccinated"]),
            people_fully_vaccinated=int(data["people_fully_vaccinated"]),
            date=str(data["date"]),
            source_url=str(data["source_url"]),
            vaccine=str(data["vaccine"]),
        )


def main(paths):
    FaeroeIslands(
        location="Faeroe Islands",
        source_url="https://corona.fo/json/stats",
        source_url_ref="https://corona.fo/api",
    ).to_csv(paths)


if __name__ == "__main__":
    main()
