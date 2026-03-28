#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime
import json
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_DATA_PATH   = Path("niai_data/kanjis.json")
DEFAULT_TMP_DIR     = Path("tmp")
DEFAULT_OUT_DIR     = Path("out")
DEFAULT_MAX_SIMILAR = 20    # similar kanji to include per character
BANK_SIZE           = 10_000  # max entries per Yomitan bank file
DICT_FORMAT         = 3       # Yomitan dictionary schema version

# Shared metadata written into every index.json
_DICT_META: dict[str, Any] = {
    "author":      "mrahhal",
    "url":         "https://github.com/mrahhal/niai",
    "description": (
        "Kanji visual-similarity data from the niai project. "
        "Similar kanji are ranked by a structural-similarity score (0–1)."
    ),
    "attribution": "https://github.com/mrahhal/niai",
}




def load_niai_data(path: Path) -> list[dict]:
    """Load and return the raw niai kanjis.json as a list of entry dicts."""
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def build_kanji_bank(entries: list[dict], max_similar: int) -> list[list]:
    """
    Transform niai entries into Yomitan kanji-bank rows.

    Only the similarity stats are populated; readings, meanings, and tags
    are left empty so they do not conflict with dedicated kanji dictionaries.

    Yomitan kanji-bank row format:
        [character, onyomi, kunyomi, tags, [meanings], {stats}]
    """
    rows: list[list] = []
    for entry in entries:
        similar = (entry.get("Similar") or [])[:max_similar]
        if not similar:
            continue
        # Compact representation: "了 (1.00)  亅 (0.95)  …"
        stats = {
            "similar": "  ".join(
                f"{s['Kanji']} ({s['Score']:.2f})" for s in similar
            )
        }
        rows.append([entry["Character"], "", "", "", [], stats])
    return rows


def build_index(revision: str) -> dict:
    """Build the Yomitan index.json manifest."""
    return {
        "title":     "Niai – Visual Similarity",
        "format":    DICT_FORMAT,
        "revision":  revision,
        "sequenced": False,
        **_DICT_META,
    }


def _write_json(path: Path, data: Any) -> None:
    """Write *data* as compact UTF-8 JSON to *path*, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)


def _chunks(lst: list, size: int):
    """Yield successive *size*-length slices of *lst*."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def write_banks(rows: list[list], prefix: str, directory: Path) -> None:
    """
    Write *rows* to numbered Yomitan bank files (max BANK_SIZE each)
    inside *directory*.  File names follow the pattern ``prefix_N.json``.
    """
    for idx, bank in enumerate(_chunks(rows, BANK_SIZE), start=1):
        path = directory / f"{prefix}_{idx}.json"
        _write_json(path, bank)
        print(f"    {path.name}  ({len(bank):,} entries)")


def package_zip(source_dir: Path, out_path: Path) -> None:
    """
    Collect all .json files from *source_dir* and compress them into the
    Yomitan dictionary archive at *out_path*.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for json_file in sorted(source_dir.glob("*.json")):
            zf.write(json_file, arcname=json_file.name)
    size_kb = out_path.stat().st_size / 1024
    print(f"\n  → {out_path}  ({size_kb:.1f} kB)")


def clean_tmp(directory: Path) -> None:
    """Remove leftover .json bank files from a previous run."""
    if directory.exists():
        for f in directory.glob("*.json"):
            f.unlink()
    directory.mkdir(parents=True, exist_ok=True)


def build(
    entries: list[dict],
    max_similar: int,
) -> None:
    """Build and package the Yomitan kanji dictionary from *entries*."""
    revision = datetime.date.today().strftime("%Y-%m-%d")
    print(f"\n{len(entries):,} kanji entries  (revision: {revision})")

    _write_json(DEFAULT_TMP_DIR / "index.json", build_index(revision))

    print("  kanji_bank:")
    write_banks(build_kanji_bank(entries, max_similar), "kanji_bank", DEFAULT_TMP_DIR)

    print("\n  Packaging …")
    package_zip(DEFAULT_TMP_DIR, DEFAULT_OUT_DIR / "niai.zip")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-similar",
        type=int,
        default=DEFAULT_MAX_SIMILAR,
        dest="max_similar",
        metavar="N",
        help=f"Max similar kanji per character  (default: {DEFAULT_MAX_SIMILAR})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    print(f"Loading niai data from {DEFAULT_DATA_PATH} …")
    entries = load_niai_data(DEFAULT_DATA_PATH)
    print(f"Loaded {len(entries):,} kanji entries.")

    print(f"Cleaning tmp directory: {DEFAULT_TMP_DIR}")
    clean_tmp(DEFAULT_TMP_DIR)

    build(entries, args.max_similar)


if __name__ == "__main__":
    main()