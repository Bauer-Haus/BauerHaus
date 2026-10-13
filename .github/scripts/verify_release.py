#!/usr/bin/env python3
"""Check that each app's update feed matches the builds in the repository.

Apps: WindowSmith (WindowSmith/appcast.xml) and Nexa (nexa/appcast.xml).

For every <enclosure> in the appcast this verifies that:

  * the URL is HTTPS and points inside the site's own downloads directory,
  * the file it names actually exists in the repo,
  * the advertised `length` equals the real byte count,
  * an EdDSA signature is attached.

Run it by hand with: python3 .github/scripts/verify_release.py
"""

from __future__ import annotations

import pathlib
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

REPO = pathlib.Path(__file__).resolve().parents[2]
# Each app's folder on the site: its appcast.xml, and downloads/ with the builds it lists.
APPS = ["WindowSmith", "nexa"]

SPARKLE_NS = "http://www.andymatuschak.org/xml-namespaces/sparkle"
ALLOWED_HOSTS = {"bauerhaus.io", "www.bauerhaus.io"}

problems: list[str] = []


def fail(message: str) -> None:
    problems.append(message)


def main() -> int:
    for app in APPS:
        check(app)
    if problems:
        print("\nRelease integrity check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("\nAppcasts and builds agree.")
    return 0


def check(app: str) -> None:
    appcast = REPO / app / "appcast.xml"
    downloads = REPO / app / "downloads"
    download_prefix = f"/{app}/downloads/"
    if not appcast.is_file():
        fail(f"{app}: {appcast.relative_to(REPO)} not found")
        return

    root = ET.parse(appcast).getroot()
    enclosures = root.findall(".//item/enclosure")

    if not enclosures:
        fail(f"{app}: appcast.xml contains no <enclosure> — no update would ever install")

    for enclosure in enclosures:
        url = enclosure.get("url", "")
        parts = urlsplit(url)
        name = pathlib.PurePosixPath(parts.path).name
        label = name or url or "<enclosure with no url>"

        if parts.scheme != "https":
            fail(f"{label}: enclosure URL is not HTTPS ({url!r})")
        if parts.hostname not in ALLOWED_HOSTS:
            fail(f"{label}: enclosure host {parts.hostname!r} is not a bauerhaus.io host")
        if not parts.path.startswith(download_prefix):
            fail(f"{label}: enclosure path {parts.path!r} is outside {download_prefix}")

        if not enclosure.get(f"{{{SPARKLE_NS}}}edSignature"):
            fail(f"{label}: no sparkle:edSignature — Sparkle would refuse this update")

        build = downloads / name
        if not name or not build.is_file():
            fail(f"{label}: referenced by the appcast but not present in {app}/downloads/")
            continue

        actual_size = build.stat().st_size
        declared = enclosure.get("length")
        if declared is None:
            fail(f"{label}: enclosure has no length attribute (real size is {actual_size})")
        elif not declared.isdigit():
            fail(f"{label}: length {declared!r} is not a number")
        elif int(declared) != actual_size:
            fail(f"{label}: appcast says length={declared} but the file is {actual_size} bytes")
        else:
            print(f"ok  {app}/downloads/{name}  {actual_size} bytes")


if __name__ == "__main__":
    raise SystemExit(main())
