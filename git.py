from cusTypes import Version
from config import OWNER, REPO, TOKEN
import requests

def convert_tag_to_version(tag: dict) -> Version | None:
    try:
        return Version.from_string(tag["name"])
    except ValueError:
        return None

def fetch_latest_versions(n: int = 30) -> list[Version]:
    session = requests.Session()
    if TOKEN:
        session.headers.update({"Authorization": f"token {TOKEN}"})

    tags = []
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/tags?per_page=100"
    while url:
        resp = session.get(url)
        resp.raise_for_status()  # pyrefly: ignore
        tags.extend(resp.json())
        # follow Link header for pagination
        link = resp.headers.get("Link", "")
        url = None
        if 'rel="next"' in link:
            # find next URL
            parts = [p.split(";") for p in link.split(",")]
            for part in parts:
                if 'rel="next"' in part[1]:
                    url = part[0].strip().strip("<>")
                    break

    versions_raw: list[Version | None] = [convert_tag_to_version(t) for t in tags]
    versions: list[Version] = [v for v in versions_raw if v is not None]
    versions.sort(reverse=True)
    versions = versions[:30]  # keep only the latest 30 versions

    return versions
