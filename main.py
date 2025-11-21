import csv
import requests
import os
from pathlib import Path
from typing import Optional, List, TypedDict
from datetime import date, datetime, timezone

# compute default as previous month (wrap to 12 if current month is January)
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


def generate_readme(history: List[DailyRecord]):
    """Generate README.md with a table of available Positron dailies."""
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    readme_content = f"""# Positron Daily Builds

This repository tracks available Positron daily builds.

## Latest Available Dailies

Last updated: {current_time}

| Version | Month | Build Number | Download Link |
|---------|-------|--------------|---------------|
"""
    
    if not history:
        readme_content += "| No builds available | - | - | - |\n"
    else:
        for record in reversed(sort_history(history)):
            readme_content += (
                f"| {record['version']} | {record['month']} | {record['build_number']} | "
                f"[Download]({record['download_url']}) |\n"
            )
    
    readme_content += "\n## About\n\n"
    readme_content += "This list is automatically generated by scanning the Positron CDN for available daily builds.\n"
    readme_content += "\n## Data persistence\n\n"
    readme_content += (
        "Daily build metadata is cached in `data/dailies.csv`, allowing the script to resume from the "
        "last recorded build and limit the history to the 30 most recent dailies for quick reference.\n"
    )
    
    return readme_content


def write_readme(content: str):
    """Write content to README.md file."""
    with open("README.md", "w") as f:
        f.write(content)


def main():
    history = load_history(CSV_PATH)
    # determine the current month from the latest CSV record if present,
    # otherwise fall back to the configured default month
    if history:
        current_month: str = str(history[-1]["month"])
    else:
        current_month = FALLBACK_MONTH

    start_build = determine_start_build(history, current_month)
    latest_version: Optional[int] = None
    new_records: List[DailyRecord] = []

    try:
        for build_number in range(start_build, start_build + SCAN_WINDOW):
            build_url = url(build_number, current_month)
            match check_downloadable(build_url):
                case 200:
                    latest_version = build_number
                    record = build_record(current_month, build_number, build_url)
                    history.append(record)
                    new_records.append(record)
                    print(bcolors.OKGREEN + f"{build_number}: downloadable: {build_url}" + bcolors.ENDC)
                case 404 | 403:
                    print(f"{build_number}: not downloadable.")
                case _:
                    print(bcolors.WARNING + f"{build_number}: unknown response." + bcolors.ENDC)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")

    history = trim_history(sort_history(history))
    save_history(history, CSV_PATH)

    if latest_version is not None:
        print(f"Latest downloadable: {url(latest_version)}")

    readme_content = generate_readme(history)
    write_readme(readme_content)
    print(f"\nREADME.md generated with {len(history)} recorded version(s).")


if __name__ == "__main__":
    main()
