import csv
import requests
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from config import MAX_HISTORY_ROWS
from cusTypes import DailyRecord, Version
from platforms import Platform

README_TEMPLATE = """# Positron Daily Builds

This repository tracks available [Positron daily builds](https://github.com/posit-dev/positron/tags).

## Latest Available Dailies

Last updated: {current_time}

| Version |        |       |       | Download | Links |       |       |       |
|---------|--------|-------|-------|----------|-------|-------|-------|-------|
"""


def is_platform_available(
    checksums: dict, version: Version, platform: Platform
) -> bool:
    """Check if a specific platform build is available in the checksums.

    Args:
        checksums: Dictionary containing checksum data.
        version: Version to check.
        platform: Platform to check availability for.

    Returns:
        True if the platform build is available, False otherwise.
    """
    filename = platform.get_file_name(version)
    return filename in checksums


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


def url(version: Version, platform: Platform = Platform.WINDOWS_SYS) -> str:
    link: str | None = None
    match platform:
        case Platform.WINDOWS_SYS:
            link = f"https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{str(version)}-Setup-x64.exe"
        case Platform.WINDOWS_USER:
            link = f"https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{str(version)}-UserSetup-x64.exe"
        case Platform.MACOS_ARM:
            link = f"https://cdn.posit.co/positron/dailies/mac/arm64/Positron-{str(version)}-arm64.dmg"
        case Platform.MACOS_X64:
            link = f"https://cdn.posit.co/positron/dailies/mac/x64/Positron-{str(version)}-x64.dmg"
        case Platform.DEBIAN_X64:
            link = f"https://cdn.posit.co/positron/dailies/deb/x86_64/Positron-{str(version)}-x64.deb"
        case Platform.DEBIAN_ARM:
            link = f"https://cdn.posit.co/positron/dailies/deb/arm64/Positron-{str(version)}-arm64.deb"
        case Platform.REDHAT_X64:
            link = f"https://cdn.posit.co/positron/dailies/rpm/x86_64/Positron-{str(version)}-x64.rpm"
        case Platform.REDHAT_ARM:
            link = f"https://cdn.posit.co/positron/dailies/rpm/arm64/Positron-{str(version)}-arm64.rpm"
    if link:
        return link
    else:
        raise ValueError(f"unsupported platform: {platform}")


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
