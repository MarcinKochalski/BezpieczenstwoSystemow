"""
METODA B: zapis zakodowanej zawartosci EXE w metadanych obrazu.

PNG -> wykorzystuje chunk tEXt (przez Pillow PngInfo.add_text).
       Chunk tekstowy oczekuje danych "tekstowych", wiec EXE (dane
       binarne) kodujemy w Base64 przed zapisem.

JPG -> JPG nie ma chunkow jak PNG, ale ma segmenty markerowe.
       Uzywamy segmentu COM (marker 0xFF 0xFE) - segment ten moze
       zawierac DOWOLNE bajty (w przeciwienstwie do skompresowanych
       danych obrazu, segmenty markerowe nie wymagaja "bitstuffingu"),
       wiec zapisujemy tu dane EXE bezposrednio, bez kodowania.
       Segment COM wstawiamy od razu po markerze SOI (0xFF 0xD8) -
       dekodery JPG ignoruja nieznane/nieuzywane segmenty markerowe
       przy renderowaniu obrazu.

Jesli EXE jest wiekszy niz miesci sie w jednym segmencie COM
(limit: 65533 B danych na segment, bo dlugosc segmentu to pole
2-bajtowe), dzielimy dane na kilka kolejnych segmentow COM -
extract() skleja je z powrotem w kolejnosci wystapienia.
"""

import base64
from pathlib import Path

from PIL import Image, PngImagePlugin

from methods.base import _ensure_parent_dir

PNG_TEXT_KEY = "p22_payload"

MAGIC = b"P22META\x00"  # 8 bajtow
LEN_BYTES = 8  # dlugosc EXE jako 8-bajtowa liczba big-endian
MAX_COM_CHUNK = 65000  # bezpieczny margines ponizej limitu 65533 B


# ---------------------------------------------------------------- PNG ----

def _png_hide(image_path: str, exe_path: str, output_path: str) -> str:
    exe_bytes = Path(exe_path).read_bytes()
    encoded = base64.b64encode(exe_bytes).decode("ascii")

    img = Image.open(image_path)
    meta = PngImagePlugin.PngInfo()
    meta.add_text(PNG_TEXT_KEY, encoded)
    img.save(output_path, format="PNG", pnginfo=meta)
    return output_path


def _png_extract(stego_path: str, output_path: str) -> str:
    img = Image.open(stego_path)
    img.load()  # niezbedne, zeby Pillow wczytal chunki tekstowe po IDAT

    encoded = img.text.get(PNG_TEXT_KEY) if hasattr(img, "text") else None
    if encoded is None:
        raise ValueError(f"Nie znaleziono chunku '{PNG_TEXT_KEY}' w {stego_path}")

    exe_bytes = base64.b64decode(encoded)
    Path(output_path).write_bytes(exe_bytes)
    return output_path


# ---------------------------------------------------------------- JPG ----

def _build_com_segments(payload: bytes) -> bytes:
    segments = b""
    for i in range(0, len(payload), MAX_COM_CHUNK):
        chunk = payload[i : i + MAX_COM_CHUNK]
        seg_len = len(chunk) + 2  # pole dlugosci liczy sie samo w sobie
        segments += b"\xff\xfe" + seg_len.to_bytes(2, "big") + chunk
    return segments


def _jpg_hide(image_path: str, exe_path: str, output_path: str) -> str:
    image_bytes = Path(image_path).read_bytes()
    if image_bytes[:2] != b"\xff\xd8":
        raise ValueError(f"{image_path} nie zaczyna sie od markera SOI - to nie jest poprawny JPG")

    exe_bytes = Path(exe_path).read_bytes()
    payload = MAGIC + len(exe_bytes).to_bytes(LEN_BYTES, "big") + exe_bytes

    com_segments = _build_com_segments(payload)
    # wstawiamy segmenty COM zaraz po SOI (pierwsze 2 bajty pliku)
    result = image_bytes[:2] + com_segments + image_bytes[2:]
    Path(output_path).write_bytes(result)
    return output_path


def _jpg_extract(stego_path: str, output_path: str) -> str:
    data = Path(stego_path).read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"{stego_path} nie zaczyna sie od markera SOI - to nie jest poprawny JPG")

    pos = 2
    collected = b""
    while data[pos : pos + 2] == b"\xff\xfe":
        seg_len = int.from_bytes(data[pos + 2 : pos + 4], "big")
        chunk = data[pos + 4 : pos + 2 + seg_len]
        collected += chunk
        pos += 2 + seg_len

    if not collected.startswith(MAGIC):
        raise ValueError(f"Nie znaleziono ukrytych danych (brak sygnatury {MAGIC!r}) w {stego_path}")

    header_start = len(MAGIC)
    exe_len = int.from_bytes(collected[header_start : header_start + LEN_BYTES], "big")
    exe_start = header_start + LEN_BYTES
    exe_bytes = collected[exe_start : exe_start + exe_len]

    if len(exe_bytes) != exe_len:
        raise ValueError(
            f"Niekompletne dane EXE w {stego_path}: oczekiwano {exe_len} B, "
            f"znaleziono {len(exe_bytes)} B"
        )

    Path(output_path).write_bytes(exe_bytes)
    return output_path


# ------------------------------------------------------------ dispatch ----

def hide(image_path: str, exe_path: str, output_path: str) -> str:
    _ensure_parent_dir(output_path)
    suffix = Path(image_path).suffix.lower()
    if suffix == ".png":
        return _png_hide(image_path, exe_path, output_path)
    elif suffix in (".jpg", ".jpeg"):
        return _jpg_hide(image_path, exe_path, output_path)
    raise ValueError(f"Nieobslugiwany format: {suffix}")


def extract(stego_path: str, output_path: str) -> str:
    _ensure_parent_dir(output_path)
    suffix = Path(stego_path).suffix.lower()
    if suffix == ".png":
        return _png_extract(stego_path, output_path)
    elif suffix in (".jpg", ".jpeg"):
        return _jpg_extract(stego_path, output_path)
    raise ValueError(f"Nieobslugiwany format: {suffix}")
