import os
from pathlib import Path
from datetime import date

OWNER = "posit-dev"
REPO = "positron"
TOKEN = os.environ.get("GITHUB_TOKEN")  # optional, higher rate limit if set

today: date = date.today()

default_month: int = today.month + 1 if today.month < 12 else 1
# We no longer read CURRENT_MONTH/CURRENT_VERSION from .env. Instead we derive
# the current month and start build from the latest CSV record. Keep a sensible
# fallback for an empty CSV.
FALLBACK_YEAR: int = today.year
FALLBACK_MONTH: int = default_month
FALLBACK_START_VERSION: int = 0
# SCAN_WINDOW can still be controlled by env if desired (0 = no network checks)
SCAN_WINDOW: int = max(0, int(os.getenv("SCAN_WINDOW", "50")))
MAX_HISTORY_ROWS: int = 30
CSV_PATH: Path = Path("data/dailies.csv")
