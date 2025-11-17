import requests
import os
from dotenv import load_dotenv, set_key
from typing import Optional
from datetime import date

load_dotenv()
# compute default as previous month (wrap to 12 if current month is January)
today: date = date.today()
default_month: int = today.month - 1 if today.month > 1 else 12
CURRENT_MONTH: str = os.getenv("CURRENT_MONTH", str(default_month))
CURRENT_VERSION: int = int(os.getenv("CURRENT_VERSION", "0")) # pyrefly: ignore


def url(number: int):
    return f"https://cdn.posit.co/positron/dailies/win/x86_64/Positron-2025.{CURRENT_MONTH}.0-{number}-Setup-x64.exe"


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


def main():
    latest_version: Optional[int] = None
    try:
        for i in range(CURRENT_VERSION, CURRENT_VERSION + 50):
            match check_downloadable(url(i)):
                case 200:
                    latest_version = i
                    print(bcolors.OKGREEN + f"{i}: downloadable!" + bcolors.ENDC)
                case 404 | 403:
                    print(f"{i}: not downloadable.")
                case _:
                    print(bcolors.WARNING + f"{i}: unknown response." + bcolors.ENDC)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
    if latest_version is not None:
        set_key(".env", "CURRENT_VERSION", str(latest_version))
        print(f"Latest downloadable: {url(latest_version)}")


if __name__ == "__main__":
    main()
