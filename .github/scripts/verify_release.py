#!/usr/bin/env python3
"""Check that WindowSmith's update feed matches the builds in the repository.

For every <enclosure> in the appcast this verifies that:

  * the URL is HTTPS and points inside the site's own downloads directory,
  * the file it names actually exists in the repo,
  * the advertised `length` equals the real byte count,
  * an EdDSA signature is attached,
  * the file's SHA-256 matches the line for it in SHA256SUMS.txt,

and that the checksum printed on the download page is the current build's, so the
page can never show a hash for a different file than its buttons hand out.

Run it by hand with: python3 .github/scripts/verify_release.py
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

REPO = pathlib.Path(__file__).resolve().parents[2]
APPCAST = REPO / "WindowSmith" / "appcast.xml"
DOWNLOADS = REPO / "WindowSmith" / "downloads"
SUMS = DOWNLOADS / "SHA256SUMS.txt"
PAGE = REPO / "WindowSmith" / "index.html"

SPARKLE_NS = "http://www.andymatuschak.org/xml-namespaces/sparkle"
ALLOWED_HOSTS = {"bauerhaus.io", "www.bauerhaus.io"}
DOWNLOAD_PREFIX = "/WindowSmith/downloads/"

problems: list[str] = []


def fail(message: str) -> None:
    problems.append(message)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_checksums() -> dict[str, str]:
    if not SUMS.is_file():
        fail(f"{SUMS.relative_to(REPO)} is missing")
        return {}
    sums: dict[str, str] = {}
    for line in SUMS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            fail(f"SHA256SUMS.txt: cannot parse {line!r}")
            continue
        digest, name = parts[0], parts[1].lstrip("*")
        sums[name] = digest.lower()
    return sums


def check_download_page(checksums: dict[str, str], current: set[str]) -> None:
    """The page prints one build's checksum beside its download buttons. Each release
    moves the buttons to the new DMG; if the printed checksum is left behind, anyone who
    checks it sees a mismatch and concludes the download was tampered with."""
    if not PAGE.is_file():
        return
    html = PAGE.read_text()
    shown = re.search(r"SHA-256 &middot; (WindowSmith-[\d.]+\.dmg)<br>\s*<span[^>]*>([0-9a-f]{64})</span>", html)
    if not shown:
        fail("WindowSmith/index.html: no checksum line found beside the download buttons")
        return
    name, digest = shown.group(1), shown.group(2)
    before = len(problems)
    linked = set(re.findall(r'href="downloads/(WindowSmith-[\d.]+\.dmg)"', html))
    if linked != {name}:
        fail(f"WindowSmith/index.html: shows the checksum for {name} but its download links point at {sorted(linked)}")
    if current and name not in current:
        fail(f"WindowSmith/index.html: shows the checksum for {name}, but the appcast ships {sorted(current)}")
    if checksums.get(name) != digest:
        fail(f"WindowSmith/index.html: checksum shown for {name} does not match SHA256SUMS.txt")
    if len(problems) == before:
        print(f"ok  download page shows {name}  sha256={digest}")


def main() -> int:
    if not APPCAST.is_file():
        print(f"error: {APPCAST} not found", file=sys.stderr)
        return 1

    checksums = load_checksums()
    root = ET.parse(APPCAST).getroot()
    enclosures = root.findall(".//item/enclosure")

    if not enclosures:
        fail("appcast.xml contains no <enclosure> — no update would ever install")

    seen: set[str] = set()

    for enclosure in enclosures:
        url = enclosure.get("url", "")
        parts = urlsplit(url)
        name = pathlib.PurePosixPath(parts.path).name
        label = name or url or "<enclosure with no url>"

        if parts.scheme != "https":
            fail(f"{label}: enclosure URL is not HTTPS ({url!r})")
        if parts.hostname not in ALLOWED_HOSTS:
            fail(f"{label}: enclosure host {parts.hostname!r} is not a bauerhaus.io host")
        if not parts.path.startswith(DOWNLOAD_PREFIX):
            fail(f"{label}: enclosure path {parts.path!r} is outside {DOWNLOAD_PREFIX}")

        if not enclosure.get(f"{{{SPARKLE_NS}}}edSignature"):
            fail(f"{label}: no sparkle:edSignature — Sparkle would refuse this update")

        build = DOWNLOADS / name
        if not name or not build.is_file():
            fail(f"{label}: referenced by the appcast but not present in WindowSmith/downloads/")
            continue

        seen.add(name)

        actual_size = build.stat().st_size
        declared = enclosure.get("length")
        if declared is None:
            fail(f"{label}: enclosure has no length attribute (real size is {actual_size})")
        elif not declared.isdigit():
            fail(f"{label}: length {declared!r} is not a number")
        elif int(declared) != actual_size:
            fail(f"{label}: appcast says length={declared} but the file is {actual_size} bytes")

        digest = sha256(build)
        expected = checksums.get(name)
        if expected is None:
            fail(f"{label}: no entry in SHA256SUMS.txt (actual SHA-256 is {digest})")
        elif expected != digest:
            fail(f"{label}: SHA256SUMS.txt says {expected} but the file hashes to {digest}")
        else:
            print(f"ok  {name}  {actual_size} bytes  sha256={digest}")

    check_download_page(checksums, seen)

    # A checksum line for a build that is no longer shipped is stale, not fatal.
    for name in sorted(set(checksums) - seen):
        if not (DOWNLOADS / name).is_file():
            fail(f"{name}: listed in SHA256SUMS.txt but not present in WindowSmith/downloads/")

    if problems:
        print("\nRelease integrity check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("\nAppcast, builds and checksums all agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
