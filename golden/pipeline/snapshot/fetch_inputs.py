"""Download the batch inputs of the pipeline family into a raw folder.

    python fetch_inputs.py --out ../data/raw

Sources (public, no key):
- USAspending.gov Award Data Archive: FY2024 prime award transactions ("Full" files), one zip per
  agency and award type. The archive is regenerated monthly and old dates are removed, so a later run
  fetches a newer file with a different checksum. ARCHIVE_DATE pins the one frozen here.
- Census Bureau county population estimates, vintage 2024 (2020-2024) and vintage 2021 (2020-2021).
- The Wikimedia site matrix (meta.wikimedia.org API).

The files are stored byte for byte as served. data/MANIFEST.json records each file's sha256, size and
source URL (written by manifest.py). The benchmark itself runs offline from the frozen copy.
Stdlib only.
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

ARCHIVE = "https://files.usaspending.gov/award_data_archive"
ARCHIVE_DATE = "20261006"
# Toptier agency code -> name, as in the archive's file names and the awarding_agency_* columns.
AGENCIES = {
    "417": "National Endowment for the Arts",
    "418": "National Endowment for the Humanities",
    "474": "Institute of Museum and Library Services",
    "485": "Corporation for National and Community Service",
}
CENSUS = {
    "co-est2024-alldata.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
    "co-est2021-alldata.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2021/counties/totals/co-est2021-alldata.csv",
}
SITEMATRIX = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json&formatversion=2"
USER_AGENT = "harness-benchmark-snapshot/0.1 (https://github.com/jtouley/harness-benchmark)"


def sources() -> dict[str, str]:
    """Relative path under the raw folder -> source URL."""
    out = {}
    for code in AGENCIES:
        for kind in ("Assistance", "Contracts"):
            name = f"FY2024_{code}_{kind}_Full_{ARCHIVE_DATE}.zip"
            out[f"usaspending/{name}"] = f"{ARCHIVE}/{name}"
    for name, url in CENSUS.items():
        out[f"census/{name}"] = url
    out["sitematrix.json"] = SITEMATRIX
    return out


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    for rel, url in sources().items():
        fetch(url, args.out / rel)
        print(f"fetched {rel}")


if __name__ == "__main__":
    main()
