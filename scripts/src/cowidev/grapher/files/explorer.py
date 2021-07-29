import json

import pandas as pd
import numpy as np


class Exploriser:
    def __init__(
        self, location: str = "location", date: str = "date", pivot_column: str = None, pivot_values: str = None
    ) -> None:
        self.location = location
        self.date = date
        self.pivot_column = pivot_column
        self.pivot_values = pivot_values

    def pipe_pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.pivot_column is not None and self.pivot_values is not None:
            return (
                df
                .pivot(
                    index=[self.location, self.date],
                    columns=self.pivot_column,
                    values=self.pivot_values,
                )
                .reset_index()
            )
        return df

    def pipe_nan_to_none(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.replace({np.nan: None})

    def pipe_to_dict(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.to_dict(orient="list")

    def pipeline(self, input_path: str) -> dict:
        df = pd.read_csv(input_path)
        df = (
            df
            .pipe(self.pipe_pivot)
            .pipe(self.pipe_nan_to_none)
            .pipe(self.pipe_to_dict)
        )
        return df

    def to_json(self, obj):
        return json.dumps(
            obj,
            # Use separators without any trailing whitespace to minimize file size.
            # The defaults (", ", ": ") contain a trailing space.
            separators=(",", ":"),
            # The json library by default encodes NaNs in JSON, but this is invalid JSON.
            # By having this False, an error will be thrown if a NaN exists in the data.
            allow_nan=False
        )

    def run(self, input_path: str, output_path: str):
        data = self.pipeline(input_path)
        with open(output_path, "w") as f:
            f.write(self.to_json(data))
