import csv
import requests
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import re

from config import MAX_HISTORY_ROWS, FALLBACK_START_VERSION
from cusTypes import DailyRecord, Version, Platform


def scrape_github_tags(max_pages: int = 5) -> List[Version]:
    """
    Scrape version tags from the Positron GitHub tags page.
    Returns a list of Version objects parsed from the tag names.
    
    Args:
        max_pages: Maximum number of pages to scrape (default 5, which should get 50+ tags)
    """
    base_url = "https://github.com/posit-dev/positron/tags"
    versions: List[Version] = []
    current_url = base_url
    
    # Build regex pattern for finding tag links using Version's pattern
    tag_pattern = re.compile(f'/posit-dev/positron/releases/tag/{Version.VERSION_PATTERN}')
    
    try:
        for page in range(max_pages):
            response = requests.get(current_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all tag links that match the version pattern
            tag_links = soup.find_all('a', href=tag_pattern)
            
            page_versions = 0
            for link in tag_links:
                tag_name = link.get_text(strip=True)
                try:
                    version = Version.from_string(tag_name)
                    versions.append(version)
                    page_versions += 1
                except ValueError:
                    # Skip tags that don't match our version format
                    continue
            
            print(f"Page {page + 1}: Found {page_versions} version tags")
            
            # Look for next page link
            next_link = soup.find('a', string='Next')
            if next_link and next_link.get('href'):
                current_url = "https://github.com" + next_link['href']
            else:
                print("No more pages to scrape")
                break
        
        unique_versions = sorted(set(versions))
        print(f"Total: Scraped {len(unique_versions)} unique version tags from GitHub")
        return unique_versions
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping GitHub tags: {e}")
        return []


def url(version: Version, platform: Platform = Platform.WINDOWS_SYS) -> str:
    link: str|None = None
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