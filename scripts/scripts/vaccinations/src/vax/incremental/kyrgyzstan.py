import pandas as pd

from vax.utils.utils import get_soup
from vax.utils.incremental import clean_count, enrich_data, increment
from vax.utils.dates import localdate


class Kyrgyzstan:
    def __init__(self):
        self.source_url = "https://vc.emed.gov.kg/"
        self.location = "Kyrgyzstan"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        return pd.Series(data)

    def _parse_data(self, soup):
        metrics_raw = soup.find_all("h3", class_="ml-4")
        data = {}
        for h in metrics_raw:
            if h.parent.p.text == "Всего вакцинаций":
                data["total_vaccinations"] = clean_count(h.text)
            elif h.parent.p.text == "Количество вакцинированных 1 дозой":
                data["people_vaccinated"] = clean_count(h.text)
            elif h.parent.p.text == "Количество лиц, прошедших полный курс вакцинации":
                data["people_fully_vaccinated"] = clean_count(h.text)
        return data

    def pipe_date(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "date", localdate("Asia/Bishkek"))

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(
            ds,
            "vaccine",
            "Sinopharm/Beijing, Sputnik V"
        )

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return (
            ds
            .pipe(self.pipe_date)
            .pipe(self.pipe_source)
            .pipe(self.pipe_location)
            .pipe(self.pipe_vaccine)
        )

    def export(self, paths):
        """Generalized."""
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
    Kyrgyzstan().export(paths)


if __name__ == "__main__":
    main()
