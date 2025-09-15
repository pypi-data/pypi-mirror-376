import json

from py_alpaca_api.http.requests import Requests
from py_alpaca_api.models.quote_model import QuoteModel, quote_class_from_dict


class LatestQuote:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers

    def get(
        self,
        symbol: list[str] | str | None,
        feed: str = "iex",
        currency: str = "USD",
    ) -> list[QuoteModel] | QuoteModel:
        if symbol is None or symbol == "":
            raise ValueError("Symbol is required. Must be a string or list of strings.")

        valid_feeds = ["iex", "sip", "otc"]
        if feed not in valid_feeds:
            raise ValueError("Invalid feed, must be one of: 'iex', 'sip', 'otc'")

        if isinstance(symbol, list):
            symbol = ",".join(symbol).replace(" ", "").upper()
        else:
            symbol = symbol.replace(" ", "").upper()

        url = "https://data.alpaca.markets/v2/stocks/quotes/latest"

        params: dict[str, str | bool | float | int] = {
            "symbols": symbol,
            "feed": feed,
            "currency": currency,
        }

        response = json.loads(
            Requests()
            .request(method="GET", url=url, headers=self.headers, params=params)
            .text
        )

        quotes = []

        for key, value in response["quotes"].items():
            quotes.append(
                quote_class_from_dict(
                    {
                        "symbol": key,
                        "timestamp": value["t"],
                        "ask": value["ap"],
                        "ask_size": value["as"],
                        "bid": value["bp"],
                        "bid_size": value["bs"],
                    }
                )
            )

        return quotes if len(quotes) > 1 else quotes[0]
