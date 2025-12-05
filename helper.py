from turtle import right
import csv
import requests
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from config import MAX_HISTORY_ROWS
from cusTypes.record import DailyRecord, DailyAvailability
from cusTypes.version import Version
from platforms import Platform, System

README_TEMPLATE = """# Positron Daily Builds

This repository tracks available [Positron daily builds](https://github.com/posit-dev/positron/tags).

## Latest Available Dailies

Last updated: {current_time}

| Version |        |       |       | Download | Links |       |       |       |
|---------|--------|-------|-------|----------|-------|-------|-------|-------|
"""


def table_header(num_systems: int = len(System)) -> str:
    start: str = "| Version |"

    half = num_systems // 2

    left_spaces: str = "       |" * (half - 1)
    right_spaces: str = "       |" * (num_systems - half - 1)
    first: str = start + left_spaces + " Download | Links |" + right_spaces

    second: str = "|---------|" + "--------|" * num_systems
    return first + "\n" + second + "\n"


def checksums_url(version: Version) -> str:
    """Return the URL for the checksums JSON file for a given version."""
    return f"https://cdn.posit.co/positron/dailies/checksums/positron-{str(version)}-checksums.json"


def fetch_checksums(version: Version) -> dict | None:
    """Fetch and parse the checksums JSON for a given version.

    Returns:
        dict: The parsed checksums JSON if successful, None otherwise.
    """
    checksum_url = checksums_url(version)
    try:
        response = requests.get(checksum_url, timeout=30)
        if response.status_code == 200:
            return response.json()
        # Non-200 status codes indicate the checksums file is not available yet
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching checksums for {version}: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing checksums JSON for {version}: {e}")
        return None


def fetch_availability(version: Version) -> DailyAvailability | None:
    checksums = fetch_checksums(version)
    if checksums is None:
        return None

    # Convert checksums dictionary to platform availability dictionary
    # Normalize: include all platforms from Platform enum, set missing to False
    platform_availability = {}

    for platform in Platform:
        filename = platform.get_file_name(version)
        # Check if this filename exists in the checksums
        is_available = filename in checksums
        platform_availability[platform] = is_available

    return DailyAvailability(version, platform_availability)


class bcolors:
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"


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


def trim_history(
    history: List[DailyRecord], limit: int = MAX_HISTORY_ROWS
) -> List[DailyRecord]:
    if len(history) <= limit:
        return history
    return history[-limit:]


def trim_availability(
    availability_list: List[DailyAvailability], limit: int = MAX_HISTORY_ROWS
) -> List[DailyAvailability]:
    sorted_list = sorted(availability_list)
    if len(sorted_list) <= limit:
        return sorted_list
    return sorted_list[-limit:]


def history_to_availability(history: List[DailyRecord]) -> List[DailyAvailability]:
    return [
        DailyAvailability(
            version=record["version"], available_platforms={p: True for p in Platform}
        )
        for record in history
    ]


def build_record(version: Version) -> DailyRecord:
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return DailyRecord(
        version=version,
        fetched_at=timestamp,
    )
