"""
Metryki oceny zgodnie z punktem III (a-f) opisu projektu.

evaluate() przyjmuje sciezki do: oryginalnego obrazu, oryginalnego
EXE, obrazu z ukrytymi danymi (stego) i odzyskanego EXE - i zwraca
slownik z wynikami wszystkich kryteriow. Ten slownik trafia potem
jako jeden wiersz do results.csv (patrz runner.py).

Punkt III.d (uruchomienie EXE) i III.e (wykrywalnosc) sa tu na razie
uproszczone / oznaczone jako TODO - patrz komentarze ponizej.
"""

import hashlib
from pathlib import Path

from PIL import Image


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def displays_correctly(image_path: str) -> bool:
    """Punkt III.a - czy obraz nadal otwiera sie i renderuje poprawnie."""
    try:
        with Image.open(image_path) as img:
            img.verify()
        # verify() "zuzywa" obiekt, wiec otwieramy ponownie zeby
        # sprawdzic faktyczne zaladowanie danych pikseli
        with Image.open(image_path) as img:
            img.load()
        return True
    except Exception:
        return False


def size_delta_bytes(original_image_path: str, stego_image_path: str) -> int:
    """Punkt III.b - zmiana rozmiaru pliku PNG/JPG po ukryciu EXE."""
    return Path(stego_image_path).stat().st_size - Path(original_image_path).stat().st_size


def integrity_matches(original_exe_path: str, extracted_exe_path: str) -> bool:
    """Punkt III.c - czy odzyskany EXE jest identyczny (SHA-256) z oryginalem."""
    try:
        return sha256_of_file(original_exe_path) == sha256_of_file(extracted_exe_path)
    except FileNotFoundError:
        return False


def runs_correctly(extracted_exe_path: str, timeout_seconds: float = 5.0) -> bool | None:
    """
    Punkt III.d - czy odzyskany EXE da sie uruchomic poprawnie
    (kod wyjscia 0, bez wywalenia timeoutu).

    Dziala "na prawdziwie" tylko na Windows (bo .exe to PE, ktorego
    Linux nie uruchomi natywnie) - jesli funkcja jest wywolana na
    innym systemie, zwraca None ("nie dotyczy / nie sprawdzono tutaj"),
    zamiast falszywie raportowac porazke.

    Uwaga bezpieczenstwa: to uruchamia PRAWDZIWY plik wykonywalny.
    Uzywajcie tego wylacznie z plikami testowymi, ktorych zawartosc
    sami skompilowaliscie/znacie (tak jak data/exe_samples/test_program.exe)
    - NIGDY z plikami EXE nieznanego pochodzenia. Dla dodatkowej izolacji
    mozna to odpalac w Windows Sandbox (patrz run_in_sandbox.py).
    """
    import platform
    import subprocess

    if platform.system() != "Windows":
        return None

    try:
        result = subprocess.run(
            [extracted_exe_path],
            timeout=timeout_seconds,
            capture_output=True,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        return False


def detectability_notes(stego_image_path: str) -> str:
    """
    Punkt III.e - wykrywalnosc ukrytych danych przez analize struktury
    pliku / danych obrazu. Patrz detect.py po pelna implementacje
    (parsowanie chunkow PNG / segmentow JPG, wykrywanie anomalii).
    """
    import detect

    return detect.summarize(stego_image_path)


def survives_resave(method_module, resaved_image_path: str, original_exe_path: str, tmp_extract_path: str) -> bool:
    """
    Punkt III.f - czy ukryte dane przetrwaly ponowny zapis obrazu
    (np. ktos otworzyl i zapisal plik w jakims edytorze/bibliotece).

    Probuje wywolac extract() DANEJ METODY na juz-ponownie-zapisanym
    obrazie (resaved_image_path) i porownuje SHA-256 z oryginalnym
    EXE. Zwraca False zarowno gdy extract() rzuci wyjatek (dane
    zniknely calkowicie), jak i gdy "cos" sie wyciagnie, ale nie
    zgadza sie z oryginalem (dane uszkodzone).

    Patrz resave_test.py - tam jest pelny pipeline generujacy
    resaved_image_path i wolajacy te funkcje dla wszystkich
    kombinacji z results/stego/.
    """
    try:
        method_module.extract(resaved_image_path, tmp_extract_path)
        return integrity_matches(original_exe_path, tmp_extract_path)
    except Exception:
        return False


def evaluate(
    original_image_path: str,
    exe_path: str,
    stego_image_path: str,
    extracted_exe_path: str,
) -> dict:
    """Zbiera wszystkie kryteria a-f w jeden wiersz wynikow."""
    return {
        "displays_correctly": displays_correctly(stego_image_path),
        "size_delta_bytes": size_delta_bytes(original_image_path, stego_image_path),
        "sha256_match": integrity_matches(exe_path, extracted_exe_path),
        "runs_correctly": runs_correctly(extracted_exe_path),
        "detectability_notes": detectability_notes(stego_image_path),
    }
