"""Run urlgenie v1 and urlgenie2 over the sample sheet and diff the results.

Both packages live side by side in the repo root, so both import from there.

    python tools/compare_v1_v2.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import urlgenie2
from conftest import load_sample_rows

try:
    from urlgenie import UrlGenie
except Exception as error:  # pragma: no cover - v1 may not be importable
    UrlGenie = None
    print(f"note: urlgenie v1 not importable ({error})")

#-Non-default v1 flags needed to reach v2's behaviour. Kept here and printed with
# the summary so the score is never read as "v1 does this out of the box".-#
V1_FLAGS = {"keep_periods": False}


def main() -> int:
    v1 = UrlGenie() if UrlGenie else None
    stats = {"v1": 0, "v2": 0, "total": 0}

    for section, url, expected, _ in load_sample_rows():
        comma = "," in url and ", " in expected
        got2 = ", ".join(urlgenie2.generalize_many(url)) if comma else urlgenie2.generalize(url)
        got1 = v1.generalize(url, comma_separated=comma, **V1_FLAGS) if v1 else None

        stats["total"] += 1
        stats["v1"] += got1 == expected
        stats["v2"] += got2 == expected

        if got1 != expected or got2 != expected:
            print(f"[{section}] {url}")
            print(f"   expected: {expected}")
            print(f"   v1:       {got1}{'' if got1 == expected else '   <-- MISMATCH'}")
            print(f"   v2:       {got2}{'' if got2 == expected else '   <-- MISMATCH'}\n")

    flags = ", ".join(f"{key}={value}" for key, value in V1_FLAGS.items()) or "defaults"
    print(f"v1: {stats['v1']}/{stats['total']}  (v1 flags: {flags})")
    print(f"v2: {stats['v2']}/{stats['total']}  (no flags -- this is the default behaviour)")
    return 0 if stats["v2"] == stats["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
