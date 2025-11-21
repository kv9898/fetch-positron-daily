import os
from pathlib import Path
from datetime import date

today: date = date.today()

default_month: int = today.month - 1 if today.month > 1 else 12
# We no longer read CURRENT_MONTH/CURRENT_VERSION from .env. Instead we derive
# the current month and start build from the latest CSV record. Keep a sensible
# fallback for an empty CSV.
FALLBACK_MONTH: str = str(default_month)
FALLBACK_START_VERSION: int = 0
# SCAN_WINDOW can still be controlled by env if desired (0 = no network checks)
SCAN_WINDOW: int = max(0, int(os.getenv("SCAN_WINDOW", "50")))
MAX_HISTORY_ROWS: int = 30
CSV_PATH: Path = Path("data/dailies.csv")