import pandas as pd
import re

from vax.manual.twitter.base import TwitterCollectorBase
from vax.utils.dates import clean_date


class Ethiopia(TwitterCollectorBase):
    def __init__(self, api, paths=None):
        super().__init__(
            api=api,
            username="FMoHealth",
            location="Ethiopia",
            add_metrics_nan=["total_vaccinations"],
            paths=paths,
        )

    def _propose_df(self):
        regex = r"ባለፉት 24 .*"
        data = []
        for tweet in self.tweets:
            if re.search(regex, tweet.full_text):
                dt = tweet.created_at.strftime("%Y-%m-%d")
                if self.stop_search(dt):
                    break
                data.append(
                    {
                        "date": dt,
                        "text": tweet.full_text,
                        "source_url": self.build_post_url(tweet.id),
                        "media_url": tweet.extended_entities["media"][1][
                            "media_url_https"
                        ],
                    }
                )
        return pd.DataFrame(data)


def main(api, paths):
    Ethiopia(api, paths).to_csv()
