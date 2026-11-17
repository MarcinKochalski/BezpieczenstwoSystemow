"""
METODA A: dopisanie zawartosci pliku EXE na koncu pliku obrazu.

Dziala identycznie dla PNG i JPG, bo oba formaty maja jednoznaczny
"koniec danych obrazu", po ktorym dekodery przestaja czytac:
  - PNG: chunk IEND (dekoder konczy czytac zaraz po nim)
  - JPG: marker EOI = bajty 0xFF 0xD9

Format danych dopisywanych na koncu pliku:
    [MAGIC: 8 bajtow]  [DLUGOSC EXE: 8 bajtow, big-endian]  [DANE EXE]

MAGIC pozwala extract() odroznic "prawdziwy" doklejony payload od
przypadkowych smieci, ktore mogly juz byc za IEND/EOI w oryginalnym
pliku (rzadkie, ale mozliwe - niektore edytory zostawiaja np. bajty
zerowe).
"""

from pathlib import Path

from methods.base import _ensure_parent_dir

MAGIC = b"P22APPND"  # 8 bajtow - sygnatura naszego formatu
LEN_BYTES = 8  # dlugosc EXE zapisana jako 8-bajtowa liczba big-endian


def hide(image_path: str, exe_path: str, output_path: str) -> str:
    _ensure_parent_dir(output_path)

    image_bytes = Path(image_path).read_bytes()
    exe_bytes = Path(exe_path).read_bytes()

    payload = MAGIC + len(exe_bytes).to_bytes(LEN_BYTES, "big") + exe_bytes

    Path(output_path).write_bytes(image_bytes + payload)
    return output_path


def extract(stego_path: str, output_path: str) -> str:
    _ensure_parent_dir(output_path)

    data = Path(stego_path).read_bytes()

    idx = data.rfind(MAGIC)
    if idx == -1:
        raise ValueError(f"Nie znaleziono ukrytych danych (brak sygnatury {MAGIC!r}) w {stego_path}")

    header_start = idx + len(MAGIC)
    length_bytes = data[header_start : header_start + LEN_BYTES]
    if len(length_bytes) != LEN_BYTES:
        raise ValueError(f"Uszkodzony naglowek payloadu w {stego_path}")

    exe_len = int.from_bytes(length_bytes, "big")
    exe_start = header_start + LEN_BYTES
    exe_bytes = data[exe_start : exe_start + exe_len]

    if len(exe_bytes) != exe_len:
        raise ValueError(
            f"Niekompletne dane EXE w {stego_path}: oczekiwano {exe_len} B, "
            f"znaleziono {len(exe_bytes)} B"
        )

    Path(output_path).write_bytes(exe_bytes)
    return output_path
