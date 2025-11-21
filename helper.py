import csv
import requests
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

from config import MAX_HISTORY_ROWS, FALLBACK_START_VERSION
from cusTypes import DailyRecord, Version


def url(version: Version) -> str:
    return f"https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{str(version)}-Setup-x64.exe"


class bcolors:
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"


def check_downloadable(url: str) -> int:
    try:
        # Send a HEAD request to the URL
        response = requests.head(url)

        # Check if the response status code is 200 (OK), indicating the file is available
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return -1


def load_history(path: Path) -> List[DailyRecord]:
    if not path.exists():
        return []

    history: List[DailyRecord] = []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                version: Version = Version.from_string(row.get("version", ""))
            except ValueError:
                continue

            history.append(
                DailyRecord(
                    version=version,
                    fetched_at=row.get("fetched_at", ""),
                )
            )

    return sort_history(history)


def save_history(history: List[DailyRecord], path: Path):
    if not history and not path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["version", "fetched_at"]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in history:
            writer.writerow(
                {
                    "version": str(record["version"]),
                    "fetched_at": record.get("fetched_at", ""),
                }
            )


def sort_history(history: List[DailyRecord]) -> List[DailyRecord]:
    def sort_key(record: DailyRecord) -> Version:
        return record.get("version")

    return sorted(history, key=sort_key)


def trim_history(history: List[DailyRecord], limit: int = MAX_HISTORY_ROWS) -> List[DailyRecord]:
    if len(history) <= limit:
        return history
    return history[-limit:]


def latest_for_month(history: List[DailyRecord], month: int) -> Optional[DailyRecord]:
    monthly = [record for record in history if record.get("version").month == month]
    if not monthly:
        return None
    return monthly[-1]


def build_record(year: int, month: int, build_number: int) -> DailyRecord:
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return DailyRecord(
        version=Version(year, month, build_number),
        fetched_at=timestamp,
    )


def determine_start_build(history: List[DailyRecord], month: int) -> int:
    monthly_latest = latest_for_month(history, month)
    if monthly_latest:
        return monthly_latest["version"].number + 1
    if history:
        return 0
    return FALLBACK_START_VERSION