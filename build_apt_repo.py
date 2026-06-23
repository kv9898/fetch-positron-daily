from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from cusTypes.version import Version


DEBIAN_SYSTEM_NAME = "Debian/Ubuntu Linux"
ARCHITECTURES = {
    "x64": "amd64",
    "ARM": "arm64",
}
PUBLIC_KEY_FILE = "positron-daily-archive-keyring.asc"


@dataclass(frozen=True)
class DebPackage:
    version: Version
    arch_label: str
    debian_arch: str
    url: str

    @property
    def filename(self) -> str:
        parsed = urlparse(self.url)
        return Path(parsed.path).name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a small APT repository for Positron daily .deb packages."
    )
    parser.add_argument("--data", type=Path, default=Path("dailies.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-path", default="apt")
    parser.add_argument("--suite", default="stable")
    parser.add_argument("--component", default="main")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--origin", default="Positron Daily Builds")
    parser.add_argument("--label", default="Positron Daily Builds")
    parser.add_argument("--public-key", type=Path, default=Path(PUBLIC_KEY_FILE))
    parser.add_argument("--signing-key", default=os.environ.get("APT_SIGNING_KEY_ID"))
    return parser.parse_args()


def load_versions(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    versions = data.get("versions", [])
    if not isinstance(versions, list):
        raise ValueError(f"{path} does not contain a versions list")

    return sorted(
        versions,
        key=lambda item: Version.from_string(str(item["version"])),
        reverse=True,
    )


def select_latest_debs(versions: list[dict[str, Any]]) -> list[DebPackage]:
    packages: list[DebPackage] = []

    for arch_label, debian_arch in ARCHITECTURES.items():
        for item in versions:
            version = Version.from_string(str(item["version"]))
            downloads = item.get("downloads", {})
            debian_downloads = downloads.get(DEBIAN_SYSTEM_NAME, {})
            url = debian_downloads.get(arch_label)
            if url:
                packages.append(DebPackage(version, arch_label, debian_arch, url))
                break
        else:
            raise ValueError(f"No Debian/Ubuntu package found for {arch_label}")

    return packages


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with temporary.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)

    os.replace(temporary, destination)


def package_field(stanza: str, field_name: str) -> str | None:
    prefix = f"{field_name}:"
    for line in stanza.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def filter_packages_by_arch(packages_text: str, arch: str) -> str:
    stanzas = [stanza.strip() for stanza in packages_text.split("\n\n") if stanza.strip()]
    matching_stanzas = [
        stanza
        for stanza in stanzas
        if package_field(stanza, "Architecture") in {arch, "all"}
    ]

    if not matching_stanzas:
        raise ValueError(f"No packages found for architecture {arch}")

    return "\n\n".join(matching_stanzas) + "\n"


def scan_packages(repo_dir: Path) -> str:
    result = subprocess.run(
        ["dpkg-scanpackages", "pool"],
        cwd=repo_dir,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def write_packages_index(
    repo_dir: Path, suite: str, component: str, arch: str, packages_text: str
) -> None:
    index_dir = repo_dir / "dists" / suite / component / f"binary-{arch}"
    index_dir.mkdir(parents=True, exist_ok=True)
    packages_file = index_dir / "Packages"

    packages_file.write_text(
        filter_packages_by_arch(packages_text, arch),
        encoding="utf-8",
    )

    with packages_file.open("rb") as raw_input:
        with (index_dir / "Packages.gz").open("wb") as raw_output:
            with gzip.GzipFile(
                filename="Packages",
                mode="wb",
                fileobj=raw_output,
                mtime=0,
            ) as compressed_output:
                shutil.copyfileobj(raw_input, compressed_output)


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_entries(release_dir: Path) -> list[Path]:
    ignored = {"Release", "InRelease", "Release.gpg"}
    return sorted(
        path
        for path in release_dir.rglob("*")
        if path.is_file() and path.name not in ignored
    )


def write_release_file(
    repo_dir: Path,
    suite: str,
    component: str,
    architectures: list[str],
    origin: str,
    label: str,
) -> None:
    release_dir = repo_dir / "dists" / suite
    release_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"Origin: {origin}",
        f"Label: {label}",
        f"Suite: {suite}",
        f"Codename: {suite}",
        f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')}",
        f"Architectures: {' '.join(architectures)}",
        f"Components: {component}",
        "Description: Positron daily builds for Debian and Ubuntu",
    ]

    files = release_entries(release_dir)
    for field_name, algorithm in (
        ("MD5Sum", "md5"),
        ("SHA1", "sha1"),
        ("SHA256", "sha256"),
    ):
        lines.append(f"{field_name}:")
        for path in files:
            relative = path.relative_to(release_dir).as_posix()
            lines.append(
                f" {hash_file(path, algorithm)} {path.stat().st_size:16d} {relative}"
            )

    (release_dir / "Release").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sign_release_file(repo_dir: Path, suite: str, signing_key: str | None) -> None:
    if not signing_key:
        print("No signing key configured; APT repository will be unsigned.")
        return

    release_dir = repo_dir / "dists" / suite
    release_file = release_dir / "Release"

    subprocess.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--local-user",
            signing_key,
            "--clearsign",
            "--output",
            str(release_dir / "InRelease"),
            str(release_file),
        ],
        check=True,
    )
    subprocess.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--local-user",
            signing_key,
            "--armor",
            "--detach-sign",
            "--output",
            str(release_dir / "Release.gpg"),
            str(release_file),
        ],
        check=True,
    )


def copy_public_key(public_key: Path, repo_dir: Path, required: bool) -> None:
    if not public_key.exists():
        message = f"Public key file not found: {public_key}"
        if required:
            raise FileNotFoundError(message)
        print(message)
        return

    shutil.copyfile(public_key, repo_dir / PUBLIC_KEY_FILE)


def write_site_index(output_dir: Path, base_url: str, suite: str, component: str) -> None:
    repo_url = base_url.rstrip("/") or "https://OWNER.github.io/REPOSITORY/apt"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Positron Daily APT Repository</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 56rem; line-height: 1.5; }}
    code, pre {{ background: #f4f4f5; border-radius: 4px; }}
    code {{ padding: 0.1rem 0.25rem; }}
    pre {{ overflow-x: auto; padding: 1rem; }}
  </style>
</head>
<body>
  <h1>Positron Daily APT Repository</h1>
  <p>This repository mirrors the latest Positron daily Debian packages.</p>
  <pre><code>curl -fsSL {repo_url}/{PUBLIC_KEY_FILE} | sudo gpg --dearmor -o /usr/share/keyrings/positron-daily-archive-keyring.gpg
ARCH=$(dpkg --print-architecture)
echo "deb [arch=${{ARCH}} signed-by=/usr/share/keyrings/positron-daily-archive-keyring.gpg] {repo_url} {suite} {component}" | sudo tee /etc/apt/sources.list.d/positron-daily.list
sudo apt update
sudo apt install positron</code></pre>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def build_repo(args: argparse.Namespace) -> None:
    packages = select_latest_debs(load_versions(args.data))
    output_dir = args.output.resolve()
    repo_dir = output_dir / args.repo_path

    if output_dir.exists():
        shutil.rmtree(output_dir)

    pool_dir = repo_dir / "pool" / "main" / "p" / "positron"
    for package in packages:
        destination = pool_dir / package.filename
        print(f"Downloading {package.url}")
        download_file(package.url, destination)

    architectures = sorted({package.debian_arch for package in packages})
    packages_text = scan_packages(repo_dir)
    for architecture in architectures:
        write_packages_index(
            repo_dir, args.suite, args.component, architecture, packages_text
        )

    write_release_file(
        repo_dir,
        args.suite,
        args.component,
        architectures,
        args.origin,
        args.label,
    )
    sign_release_file(repo_dir, args.suite, args.signing_key)
    copy_public_key(args.public_key, repo_dir, required=bool(args.signing_key))
    write_site_index(output_dir, args.base_url, args.suite, args.component)

    print(f"APT repository written to {repo_dir}")


def main() -> int:
    build_repo(parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
