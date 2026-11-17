"""
Punkt III.f - sprawdza, czy ukryte dane przetrwaja PONOWNY ZAPIS
obrazu (symulacja: ktos otwiera stego-plik w zwyklej bibliotece/
edytorze i zapisuje go od nowa, nie wiedzac o ukrytych danych).

Dla kazdego pliku w results/stego/ (wygenerowanego wczesniej przez
runner.py):
  1. Otwiera go przez Pillow (Image.open) i zapisuje ponownie do
     results/resaved/ (PNG bez zadnych dodatkowych opcji, JPG z tym
     samym quality=85 co oryginalne testowe obrazy).
  2. Probuje odzyskac EXE z PONOWNIE ZAPISANEGO pliku, uzywajac
     extract() wlasciwej metody (append/metadata - rozpoznawanej
     z nazwy pliku).
  3. Zapisuje wynik (True/False + ewentualny powod) do
     results/resave_results.csv.

Uruchomienie (po wczesniejszym "python runner.py --method append metadata"):
    python resave_test.py
"""

import csv
import importlib
import re
from pathlib import Path

from PIL import Image

import metrics

STEGO_DIR = Path("results/stego")
RESAVED_DIR = Path("results/resaved")
TMP_EXTRACT_DIR = Path("results/resave_extracted")
EXE_DIR = Path("data/exe_samples")
OUT_CSV = Path("results/resave_results.csv")

METHOD_MODULES = {
    "append": "methods.append_method",
    "metadata": "methods.metadata_method",
}

# Nazwy plikow w results/stego/ maja postac:
#   {image_name}_{method}_{exe_name}{suffix}
NAME_PATTERN = re.compile(r"^(?P<image>.+)_(?P<method>append|metadata)_(?P<exe>.+)$")


def parse_stego_filename(path: Path) -> dict:
    stem = path.stem
    match = NAME_PATTERN.match(stem)
    if not match:
        raise ValueError(f"Nie udalo sie sparsowac nazwy pliku: {path.name}")
    return match.groupdict()


def resave(stego_path: Path, resaved_path: Path) -> None:
    resaved_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(stego_path)
    if stego_path.suffix.lower() in (".jpg", ".jpeg"):
        img.convert("RGB").save(resaved_path, format="JPEG", quality=85)
    else:
        img.save(resaved_path, format="PNG")


def main() -> None:
    TMP_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for stego_path in sorted(STEGO_DIR.iterdir()):
        info = parse_stego_filename(stego_path)
        method_module = importlib.import_module(METHOD_MODULES[info["method"]])
        original_exe_path = EXE_DIR / f"{info['exe']}.exe"

        resaved_path = RESAVED_DIR / stego_path.name
        resave(stego_path, resaved_path)

        tmp_extract_path = TMP_EXTRACT_DIR / f"{stego_path.stem}.exe"
        survived = metrics.survives_resave(
            method_module, str(resaved_path), str(original_exe_path), str(tmp_extract_path)
        )

        rows.append(
            {
                "image_name": info["image"],
                "format": stego_path.suffix.lstrip("."),
                "method": info["method"],
                "exe_name": info["exe"],
                "survives_resave": survived,
            }
        )
        print(f"{stego_path.name}: survives_resave={survived}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "format", "method", "exe_name", "survives_resave"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nZapisano {len(rows)} wierszy do {OUT_CSV}")


if __name__ == "__main__":
    main()
