"""Rebuild corpus/ from the URLs in corpus/SOURCES.md.

Usage: python corpus/download.py [--force]
"""
import re
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader

CORPUS = Path(__file__).parent
ROW = re.compile(r"^\| (\S+\.pdf) \|.*?\| (https://\S+) \|.*?\| (\d+) \|")


def sources():
    for line in (CORPUS / "SOURCES.md").read_text().splitlines():
        if m := ROW.match(line):
            yield m.group(1), m.group(2), int(m.group(3))


def main():
    force = "--force" in sys.argv
    problems = 0
    for filename, url, expected_pages in sources():
        path = CORPUS / filename
        if force or not path.exists():
            print(f"downloading {filename}")
            urllib.request.urlretrieve(url, path)
        pages = len(PdfReader(path).pages)
        if pages != expected_pages:
            # The IRS replaces files in place; a new revision can move every gold page.
            print(f"WARNING {filename}: {pages} pages, SOURCES.md says {expected_pages}")
            problems += 1
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
