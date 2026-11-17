"""
Punkt III.e - wykrywalnosc ukrytych danych przez analize struktury
pliku PNG/JPG (bez odwolywania sie do konkretnej metody - tak jakby
ktos dostal "podejrzany" plik i nie wiedzial, czy i jak cos w nim
ukryto).

Idea: parsujemy plik zgodnie ze specyfikacja formatu (chunki PNG /
segmenty markerowe JPG) i szukamy anomalii:
  - dane PO oficjalnym koncu obrazu (IEND / EOI)        -> sygnatura metody "append"
  - nietypowe/niestandardowe chunki lub segmenty         -> sygnatura metody "metadata"
  - segment COM w nietypowym miejscu (zaraz po SOI)      -> sygnatura metody "metadata" w JPG

To NIE wymaga znajomosci naszego MAGIC/klucza - wlasnie to ma
pokazac, jak bardzo (nie)dyskretne sa obie metody wobec kogos, kto
robi tylko analize strukturalna, bez znajomosci szczegolow
implementacji.
"""

from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Chunki, ktorych obecnosc jest zupelnie normalna w typowym PNG
STANDARD_PNG_CHUNKS = {
    "IHDR", "PLTE", "IDAT", "IEND", "tRNS", "cHRM", "gAMA", "iCCP",
    "sBIT", "sRGB", "bKGD", "hIST", "pHYs", "sPLT", "tIME",
}
# tEXt/zTXt/iTXt sa tez "standardowe" strukturalnie, ale ich OBECNOSC
# z nietypowym kluczem (keyword) jest podejrzana - prawdziwy atakujacy
# uzylby pospolitego klucza (np. "Comment", "Software"), zeby sie wtopic
COMMON_TEXT_KEYWORDS = {
    "title", "author", "description", "copyright", "creation time",
    "software", "disclaimer", "warning", "source", "comment",
}


def analyze_png(path: str) -> dict:
    data = Path(path).read_bytes()
    findings = {
        "format": "png",
        "chunks_seen": [],
        "unusual_chunks": [],
        "trailing_bytes_after_iend": 0,
        "looks_like_pe_trailer": False,
        "verdict": [],
    }

    if data[:8] != PNG_SIGNATURE:
        findings["verdict"].append("Plik nie ma poprawnej sygnatury PNG - nie jest to standardowy PNG.")
        return findings

    pos = 8
    iend_end = None
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos : pos + 4], "big")
        ctype = data[pos + 4 : pos + 8].decode("ascii", errors="replace")
        findings["chunks_seen"].append(ctype)

        if ctype not in STANDARD_PNG_CHUNKS and ctype not in ("tEXt", "zTXt", "iTXt"):
            findings["unusual_chunks"].append(ctype)

        if ctype in ("tEXt", "zTXt", "iTXt"):
            chunk_data = data[pos + 8 : pos + 8 + length]
            keyword = chunk_data.split(b"\x00", 1)[0].decode("latin-1", errors="replace")
            if keyword.lower() not in COMMON_TEXT_KEYWORDS:
                findings["unusual_chunks"].append(f"{ctype} (keyword='{keyword}')")

        chunk_total_len = 8 + length + 4  # len + type + data + crc
        pos += chunk_total_len

        if ctype == "IEND":
            iend_end = pos
            break

    if iend_end is not None and iend_end < len(data):
        trailing = data[iend_end:]
        findings["trailing_bytes_after_iend"] = len(trailing)
        findings["looks_like_pe_trailer"] = _contains_pe_signature(trailing)

    if findings["trailing_bytes_after_iend"] > 0:
        msg = f"{findings['trailing_bytes_after_iend']} B danych PO chunku IEND - niestandardowe, silna sygnatura metody 'append'."
        if findings["looks_like_pe_trailer"]:
            msg += " Znaleziono sygnature 'MZ' (naglowek PE) w tych danych - to prawie na pewno ukryty EXE."
        findings["verdict"].append(msg)

    if findings["unusual_chunks"]:
        findings["verdict"].append(
            f"Nietypowe chunki/klucze tekstowe: {findings['unusual_chunks']} - sygnatura metody 'metadata'."
        )

    if not findings["verdict"]:
        findings["verdict"].append("Brak wykrytych anomalii strukturalnych.")

    return findings


def _contains_pe_signature(data: bytes) -> bool:
    # "MZ" to pierwsze 2 bajty kazdego pliku PE (EXE/DLL) - szukamy go
    # gdziekolwiek w danych koncowych, bo nasz MAGIC/naglowek dlugosci
    # poprzedza faktyczne bajty EXE (wiec nie zawsze jest to offset 0).
    return b"MZ" in data


def analyze_jpg(path: str) -> dict:
    data = Path(path).read_bytes()
    findings = {
        "format": "jpg",
        "segments_seen": [],
        "com_right_after_soi": False,
        "trailing_bytes_after_eoi": 0,
        "looks_like_pe_trailer": False,
        "verdict": [],
    }

    if data[:2] != b"\xff\xd8":
        findings["verdict"].append("Plik nie zaczyna sie od SOI - nie jest to standardowy JPG.")
        return findings

    if data[2:4] == b"\xff\xfe":
        findings["com_right_after_soi"] = True

    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            break
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xDA:  # SOS - start skompresowanych danych, koniec parsowania segmentow
            findings["segments_seen"].append("SOS")
            break
        seg_len = int.from_bytes(data[pos + 2 : pos + 4], "big")
        findings["segments_seen"].append(f"0xFF{marker:02X}")
        pos += 2 + seg_len

    eoi_idx = data.rfind(b"\xff\xd9")
    if eoi_idx != -1:
        trailing = data[eoi_idx + 2 :]
        findings["trailing_bytes_after_eoi"] = len(trailing)
        findings["looks_like_pe_trailer"] = _contains_pe_signature(trailing)

    if findings["com_right_after_soi"]:
        findings["verdict"].append(
            "Segment COM wystepuje natychmiast po SOI, przed APP0/JFIF - nietypowa kolejnosc, sygnatura metody 'metadata'."
        )

    if findings["trailing_bytes_after_eoi"] > 0:
        msg = f"{findings['trailing_bytes_after_eoi']} B danych PO markerze EOI - niestandardowe, silna sygnatura metody 'append'."
        if findings["looks_like_pe_trailer"]:
            msg += " Znaleziono sygnature 'MZ' (naglowek PE) w tych danych - to prawie na pewno ukryty EXE."
        findings["verdict"].append(msg)

    if not findings["verdict"]:
        findings["verdict"].append("Brak wykrytych anomalii strukturalnych.")

    return findings


def detect(path: str) -> dict:
    suffix = Path(path).suffix.lower()
    if suffix == ".png":
        return analyze_png(path)
    elif suffix in (".jpg", ".jpeg"):
        return analyze_jpg(path)
    raise ValueError(f"Nieobslugiwany format: {suffix}")


def summarize(path: str) -> str:
    """Krotkie podsumowanie tekstowe do wpisania w results.csv."""
    result = detect(path)
    return " ".join(result["verdict"])


if __name__ == "__main__":
    import sys

    for p in sys.argv[1:]:
        print(f"\n=== {p} ===")
        r = detect(p)
        for k, v in r.items():
            if k != "verdict":
                print(f"  {k}: {v}")
        print("  VERDICT:")
        for line in r["verdict"]:
            print(f"    - {line}")
