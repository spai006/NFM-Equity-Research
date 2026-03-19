# load and track the universe of NSE tickets
# Responsibilities: Establish a stable ticker_to_id mapping dictionary 
# so that RELIANCE consistently maps to stock_id = 0 across runs. \
# This is critical for C++ to know which row belongs to which company.


import csv
from pathlib import Path

UNIVERSE_FILE = Path("data/universe_master.csv")

class Universe:

    def __init__(self):
        self.ticker_to_id = {}
        self.id_to_ticker = {}
        self._load()

    def _load(self):

        if not UNIVERSE_FILE.exists():
            raise FileNotFoundError("Universe file missing")

        with open(UNIVERSE_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = int(row["stock_id"])
                ticker = row["ticker"].strip().upper()

                self.ticker_to_id[ticker] = sid
                self.id_to_ticker[sid] = ticker

        # deterministic ordering check
        if len(self.ticker_to_id) != len(self.id_to_ticker):
            raise RuntimeError("Duplicate ids in universe")

    def get_id(self, ticker):
        return self.ticker_to_id[ticker.upper()]

    def get_ticker(self, stock_id):
        return self.id_to_ticker[stock_id]

    def all_tickers(self):
        # return sorted by stock_id
        return [
            self.id_to_ticker[i]
            for i in sorted(self.id_to_ticker.keys())
        ]

    def size(self):
        return len(self.ticker_to_id)