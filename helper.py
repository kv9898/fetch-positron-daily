import csv
import requests
from pathlib import Path
from typing import Optional, List, TypedDict
from datetime import datetime, timezone

from config import FALLBACK_MONTH, MAX_HISTORY_ROWS, FALLBACK_START_VERSION

class DailyRecord(TypedDict):
    version: str
    month: str
    build_number: int
    download_url: str
    fetched_at: str


def url(number: int, month: Optional[str] = None):
    target_month = month if month is not None else FALLBACK_MONTH
    return f"https://cdn.posit.co/positron/dailies/win/x86_64/Positron-2025.{target_month}.0-{number}-Setup-x64.exe"


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
                build_number = int(row.get("build_number", "0"))
            except ValueError:
                continue

            month = row.get("month") or FALLBACK_MONTH
            history.append(
                DailyRecord(
                    version=row.get("version") or f"2025.{month}.0-{build_number}",
                    month=month,
                    build_number=build_number,
                    download_url=row.get("download_url") or url(build_number, month),
                    fetched_at=row.get("fetched_at", ""),
                )
            )

    return sort_history(history)


def save_history(history: List[DailyRecord], path: Path):
    if not history and not path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["version", "month", "build_number", "download_url", "fetched_at"]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in history:
            writer.writerow(
                {
                    "version": record["version"],
                    "month": record["month"],
                    "build_number": record["build_number"],
                    "download_url": record["download_url"],
                    "fetched_at": record.get("fetched_at", ""),
                }
            )


def sort_history(history: List[DailyRecord]) -> List[DailyRecord]:
    def sort_key(record: DailyRecord):
        fetched_at = record.get("fetched_at", "")
        return (fetched_at, record["month"], record["build_number"])

    return sorted(history, key=sort_key)


def trim_history(history: List[DailyRecord], limit: int = MAX_HISTORY_ROWS) -> List[DailyRecord]:
    if len(history) <= limit:
        return history
    return history[-limit:]


def latest_for_month(history: List[DailyRecord], month: str) -> Optional[DailyRecord]:
    monthly = [record for record in history if record["month"] == month]
    if not monthly:
        return None
    return monthly[-1]


def build_record(month: str, build_number: int, download_url: str) -> DailyRecord:
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return DailyRecord(
        version=f"2025.{month}.0-{build_number}",
        month=month,
        build_number=build_number,
        download_url=download_url,
        fetched_at=timestamp,
    )


def determine_start_build(history: List[DailyRecord], month: str) -> int:
    monthly_latest = latest_for_month(history, month)
    if monthly_latest:
        return monthly_latest["build_number"] + 1
    if history:
        return 0
    return FALLBACK_START_VERSION
