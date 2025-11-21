import os
from pathlib import Path

OWNER = "posit-dev"
REPO = "positron"
TOKEN = os.environ.get("GITHUB_TOKEN")  # optional, higher rate limit if set

# SCAN_WINDOW can still be controlled by env if desired (0 = no network checks)
SCAN_WINDOW: int = max(0, int(os.getenv("SCAN_WINDOW", "50")))
MAX_HISTORY_ROWS: int = 30
CSV_PATH: Path = Path("data/dailies.csv")
