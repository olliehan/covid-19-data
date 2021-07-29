import requests

from PIL import Image
import numpy as np
import pandas as pd

from vax.manual.twitter.base import TwitterCollectorBase


class Malawi(TwitterCollectorBase):
    def __init__(self, api, paths=None, **kwargs):
        super().__init__(
            api=api,
            username="health_malawi",
            location="Malawi",
            add_metrics_nan=True,
            paths=paths,
            **kwargs
        )

    def _propose_df(self):
        max_iter = 30
        dist_th = 8.7
        col_dominant = [160, 194, 195]
        records = []
        for tweet in self.tweets[:max_iter]:
            cond = "media" in tweet.entities  # and len(tweet.full_text) < 30
            if cond:
                url = tweet.extended_entities["media"][0]["media_url_https"]
                im = Image.open(requests.get(url, stream=True).raw, formats=["jpeg"])
                pixel_values = [x for i, x in enumerate(im.getdata()) if i < 100000]
                h = pd.value_counts(pixel_values, normalize=True).index[0]
                dist = np.linalg.norm(np.array(h) - np.array(col_dominant))
                if dist < dist_th:
                    dt = tweet.created_at.strftime("%Y-%m-%d")
                    if self.stop_search(dt):
                        break
                    records.append(
                        {
                            "date": dt,
                            "text": tweet.full_text,
                            "source_url": self.build_post_url(tweet.id),
                            "media_url": url,
                        }
                    )
        df = pd.DataFrame(records)
        return df


def main(api, paths):
    Malawi(api, paths).to_csv()
