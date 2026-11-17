"""
Wspolny interfejs (kontrakt) dla obu metod ukrywania EXE w obrazach.

KAZDA metoda (append / metadata) implementuje moduł z dokladnie tymi
dwiema funkcjami, o tej samej sygnaturze. Dzieki temu runner.py (i
metrics.py) nie musza wiedziec NIC o szczegolach implementacji - po
prostu importuja modul po nazwie i wolaja hide()/extract().

Obie osoby implementujace metody MUSZA obsluzyc:
  - pliki wejsciowe .png ORAZ .jpg (parametr image_path moze wskazywac
    na dowolny z tych dwoch formatow - funkcja ma sama rozpoznac po
    rozszerzeniu / zawartosci, jak postapic)
  - zwrocenie sciezki do faktycznie zapisanego pliku wyjsciowego
    (output_path powinien byc uzyty jako docelowa sciezka zapisu)

Jesli metoda dla danego formatu (np. JPG + metadata) jest technicznie
niemozliwa/inna w implementacji - to i tak MUSI zwrocic jakis wynik
(choc osiagniety innym mechanizmem, np. przez segmenty COM/EXIF w
JPG zamiast chunkow jak w PNG) - to jest czesc eksperymentu (patrz
punkt III.e opisu projektu: wykrywalnosc moze sie roznic miedzy
formatami).
"""

from pathlib import Path


def hide(image_path: str, exe_path: str, output_path: str) -> str:
    """
    Ukrywa plik EXE (exe_path) w obrazie (image_path), zapisuje wynik
    do output_path.

    Args:
        image_path: sciezka do obrazu nosnika (.png lub .jpg)
        exe_path: sciezka do pliku EXE, ktory ma zostac ukryty
        output_path: docelowa sciezka pliku wynikowego (ten sam
            format co image_path - nie zmieniamy formatu podczas
            ukrywania)

    Returns:
        Sciezka do zapisanego pliku wynikowego (powinna byc rowna
        output_path - zwracana dla wygody w pipeline).

    Raises:
        NotImplementedError: dopoki metoda nie jest zaimplementowana.
    """
    raise NotImplementedError("hide() nie zostalo jeszcze zaimplementowane")


def extract(stego_path: str, output_path: str) -> str:
    """
    Odzyskuje ukryty plik EXE z obrazu zawierajacego ukryte dane.

    Args:
        stego_path: sciezka do obrazu z ukrytymi danymi (wynik hide())
        output_path: docelowa sciezka, gdzie zapisac odzyskany EXE

    Returns:
        Sciezka do odzyskanego pliku EXE (powinna byc rowna
        output_path).

    Raises:
        NotImplementedError: dopoki metoda nie jest zaimplementowana.
        ValueError: jesli w stego_path nie znaleziono ukrytych danych.
    """
    raise NotImplementedError("extract() nie zostalo jeszcze zaimplementowane")


def _ensure_parent_dir(path: str) -> None:
    """Pomocnicze: tworzy folder nadrzedny dla output_path, jesli brak."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
