"""
Generuje wykresy do prezentacji na podstawie results/results.csv i
results/resave_results.csv. Zapisuje PNG-i do results/charts/ -
gotowe do wklejenia w slajdy.

Uruchomienie (po runner.py i resave_test.py):
    python generate_charts.py
"""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS_CSV = Path("results/results.csv")
RESAVE_CSV = Path("results/resave_results.csv")
CHARTS_DIR = Path("results/charts")


def load_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def chart_size_overhead(rows: list[dict]) -> None:
    """Narzut rozmiaru (B) per metoda x format - usredniony po obrazach."""
    groups = defaultdict(list)
    for r in rows:
        key = (r["method"], r["format"])
        groups[key].append(int(r["size_delta_bytes"]))

    methods = sorted({m for m, _ in groups})
    formats = sorted({f for _, f in groups})

    x = np.arange(len(formats))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    for i, method in enumerate(methods):
        values = [np.mean(groups[(method, fmt)]) for fmt in formats]
        ax.bar(x + i * width, values, width, label=method)

    ax.set_xlabel("Format obrazu")
    ax.set_ylabel("Narzut rozmiaru (bajty)")
    ax.set_title("Zmiana rozmiaru pliku po ukryciu EXE\n(III.b, usrednione po 3 obrazach bazowych)")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(formats)
    ax.legend(title="Metoda")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "size_overhead.png", dpi=150)
    plt.close(fig)


def chart_correctness_summary(rows: list[dict]) -> None:
    """Procent sukcesu dla displays_correctly i sha256_match, per metoda."""
    methods = sorted({r["method"] for r in rows})
    criteria = ["displays_correctly", "sha256_match"]
    labels_pl = {"displays_correctly": "Poprawne wyswietlanie (III.a)", "sha256_match": "Integralnosc SHA-256 (III.c)"}

    x = np.arange(len(methods))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    for i, crit in enumerate(criteria):
        values = []
        for method in methods:
            subset = [r for r in rows if r["method"] == method]
            successes = sum(1 for r in subset if r[crit] == "True")
            values.append(100 * successes / len(subset) if subset else 0)
        ax.bar(x + i * width, values, width, label=labels_pl[crit])

    ax.set_xlabel("Metoda")
    ax.set_ylabel("% przypadkow spelnionych")
    ax.set_ylim(0, 110)
    ax.set_title("Poprawnosc wyswietlania i integralnosc danych")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(methods)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "correctness_summary.png", dpi=150)
    plt.close(fig)


def chart_resave_survival(rows: list[dict]) -> None:
    """Czy dane przetrwaly ponowny zapis - per metoda x format."""
    methods = sorted({r["method"] for r in rows})
    formats = sorted({r["format"] for r in rows})

    x = np.arange(len(formats))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    for i, method in enumerate(methods):
        values = []
        for fmt in formats:
            subset = [r for r in rows if r["method"] == method and r["format"] == fmt]
            successes = sum(1 for r in subset if r["survives_resave"] == "True")
            values.append(100 * successes / len(subset) if subset else 0)
        ax.bar(x + i * width, values, width, label=method)

    ax.set_xlabel("Format obrazu")
    ax.set_ylabel("% przypadkow, gdzie dane przetrwaly (III.f)")
    ax.set_ylim(0, 110)
    ax.set_title("Przetrwanie ukrytych danych po ponownym zapisie obrazu\n(zwykly Image.open().save() bez dodatkowych opcji)")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(formats)
    ax.legend(title="Metoda")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "resave_survival.png", dpi=150)
    plt.close(fig)


def main() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    results_rows = load_rows(RESULTS_CSV)
    chart_size_overhead(results_rows)
    chart_correctness_summary(results_rows)

    if RESAVE_CSV.exists():
        resave_rows = load_rows(RESAVE_CSV)
        chart_resave_survival(resave_rows)
    else:
        print(f"Brak {RESAVE_CSV} - pomijam wykres przetrwania zapisu (odpal najpierw resave_test.py)")

    print(f"Zapisano wykresy do {CHARTS_DIR}/")


if __name__ == "__main__":
    main()
