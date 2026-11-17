"""
Pipeline: odpala hide()+extract() dla kazdej kombinacji
(obraz bazowy x format x metoda) i zapisuje wyniki metrics.evaluate()
do results/results.csv.

Zeby uruchomic po zaimplementowaniu metody append:
    python runner.py --method append

Zeby uruchomic po zaimplementowaniu metody metadata:
    python runner.py --method metadata

Zeby uruchomic obie (gdy obie juz gotowe):
    python runner.py --method append metadata
"""

import argparse
import csv
import importlib
from pathlib import Path

import metrics

IMAGES_DIR = Path("data/images")
EXE_DIR = Path("data/exe_samples")
STEGO_DIR = Path("results/stego")
EXTRACTED_DIR = Path("results/extracted")
RESULTS_CSV = Path("results/results.csv")

METHOD_MODULES = {
    "append": "methods.append_method",
    "metadata": "methods.metadata_method",
}

FIELDNAMES = [
    "image_name",
    "format",
    "method",
    "exe_name",
    "displays_correctly",
    "size_delta_bytes",
    "sha256_match",
    "runs_correctly",
    "detectability_notes",
]


def discover_images() -> list[Path]:
    return sorted(IMAGES_DIR.glob("*.png")) + sorted(IMAGES_DIR.glob("*.jpg"))


def discover_exe_samples() -> list[Path]:
    files = sorted(EXE_DIR.glob("*.exe"))
    if not files:
        raise FileNotFoundError(
            f"Brak plikow .exe w {EXE_DIR} - patrz README.md, sekcja 'Pliki EXE testowe'"
        )
    return files


def run_for_method(method_name: str) -> list[dict]:
    module = importlib.import_module(METHOD_MODULES[method_name])
    STEGO_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for image_path in discover_images():
        for exe_path in discover_exe_samples():
            fmt = image_path.suffix.lstrip(".")
            stego_path = STEGO_DIR / f"{image_path.stem}_{method_name}_{exe_path.stem}{image_path.suffix}"
            extracted_path = EXTRACTED_DIR / f"{image_path.stem}_{method_name}_{exe_path.stem}.exe"

            try:
                module.hide(str(image_path), str(exe_path), str(stego_path))
                module.extract(str(stego_path), str(extracted_path))
                result = metrics.evaluate(str(image_path), str(exe_path), str(stego_path), str(extracted_path))
            except NotImplementedError as e:
                result = {
                    "displays_correctly": None,
                    "size_delta_bytes": None,
                    "sha256_match": None,
                    "runs_correctly": None,
                    "detectability_notes": f"SKIPPED: {e}",
                }

            rows.append(
                {
                    "image_name": image_path.stem,
                    "format": fmt,
                    "method": method_name,
                    "exe_name": exe_path.stem,
                    **result,
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", nargs="+", choices=METHOD_MODULES.keys(), required=True)
    args = parser.parse_args()

    all_rows = []
    for method_name in args.method:
        print(f"Uruchamiam metode: {method_name}")
        all_rows.extend(run_for_method(method_name))

    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nZapisano {len(all_rows)} wierszy do {RESULTS_CSV}")


if __name__ == "__main__":
    main()
