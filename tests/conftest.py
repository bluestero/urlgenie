import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

#-The reference sheet at the repo root; it is the spec these tests assert
# against. Read directly rather than from a copy, so there is only one file
# to edit and no risk of the two drifting apart.-#
SAMPLE_CSV = pathlib.Path(__file__).resolve().parents[1] / "sample.csv"


def load_sample_rows():
    """Yield (section, url, generalized, handles) from the reference sample sheet."""
    rows = []
    section = ""
    with SAMPLE_CSV.open(encoding="utf-8") as handle:
        for row in list(csv.reader(handle))[1:]:
            if not row or not row[0].strip():
                continue
            url, expected = row[0].strip(), row[1].strip()
            handles = row[2].strip() if len(row) > 2 else ""
            if not expected:
                section = url
                continue
            rows.append((section, url, expected, handles))
    return rows
