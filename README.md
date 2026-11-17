# Projekt 22 — Ukrywanie kodu wykonywalnego w plikach PNG/JPG

## Struktura projektu

```
methods/
  base.py              <- kontrakt (interfejs) - NIE edytowac
  append_method.py      <- gotowe
  metadata_method.py    <- gotowe
metrics.py               <- gotowe: ocena wynikow wg kryteriow a-f
generate_test_images.py  <- gotowe: generuje 3 obrazy bazowe (PNG+JPG)
runner.py                <- gotowe: odpala caly pipeline, zapisuje results.csv
data/
  images/                <- 3 obrazy bazowe x 2 formaty (juz wygenerowane)
  exe_samples/           <- TUTAJ wstawcie testowy .exe (patrz nizej)
results/
  results.csv            <- tu laduja wyniki po uruchomieniu runner.py
```

## Co dokladnie macie zaimplementowac

Otwórzcie swój plik (`append_method.py` albo `metadata_method.py`) —
w srodku jest już docstring z dokładnymi wskazówkami technicznymi
(co zrobić dla PNG, co dla JPG). Trzymajcie się **dokładnie** sygnatur
funkcji z `methods/base.py`:

```python
def hide(image_path: str, exe_path: str, output_path: str) -> str: ...
def extract(stego_path: str, output_path: str) -> str: ...
```

Nie zmieniajcie nazw parametrów ani liczby argumentów — `runner.py`
wywołuje te funkcje po nazwie modułu, więc jeśli sygnatura się nie
zgadza, nic nie zadziała.

**Obie osoby obsługują OBA formaty (PNG i JPG)** w ramach swojej
metody — to jedna funkcja `hide()`/`extract()`, która sama
rozpoznaje format po rozszerzeniu pliku i robi to, co trzeba.

## Jak testować swoją implementację

1. Wstawcie jakiś mały testowy plik `.exe` do `data/exe_samples/`
   (patrz sekcja niżej — na razie folder jest pusty).
2. Uruchomcie **tylko swoją** metodę:
   ```
   python runner.py --method append
   ```
   albo
   ```
   python runner.py --method metadata
   ```
3. Sprawdźcie `results/results.csv` — jeśli `sha256_match` wychodzi
   `True` dla wszystkich wierszy, a `displays_correctly` też `True`,
   to działa poprawnie.
4. Dopóki nie skończycie, `runner.py` i tak się odpali (nie wywali
   błędu) — po prostu zaloguje `SKIPPED: ...` w kolumnie
   `detectability_notes`, bo `base.py` domyślnie rzuca
   `NotImplementedError`.

## Pliki EXE testowe

Folder `data/exe_samples/` jest celowo pusty — potrzebny jest
**prawdziwy, mały, nieszkodliwy plik .exe** (np. prosty "Hello World"
skompilowany w C, albo cokolwiek przez PyInstaller na Windowsie).
Nie da się tego sensownie wygenerować z tego środowiska (Linux, bez
kompilatora Windows) — ktoś z zespołu z dostępem do Windows/VS
powinien dorzucić 1-2 małe pliki `.exe` do tego folderu przed
pierwszym pełnym uruchomieniem `runner.py`.

## Punkt III.d (uruchomienie EXE) — już działa, ale tylko na Windows

`metrics.runs_correctly()` faktycznie odpala odzyskany plik przez
`subprocess.run(...)` i sprawdza kod wyjścia. Na Linuksie (ten
sandbox, w którym to pisałem) zawsze zwróci `None`, bo `.exe` to
format PE, którego Linux nie uruchomi natywnie — stąd w
`results.csv` kolumna `runs_correctly` jest pusta. **Odpalcie
`python runner.py --method append metadata` jeszcze raz na
Windowsie** (ten sam kod, bez zmian) — wtedy `runs_correctly`
wypełni się `True`/`False` dla każdego wiersza.

Dla bardziej rygorystycznej wersji "kontrolowanego środowiska" (pełna
izolacja, nie tylko subprocess na własnym systemie) jest
`run_in_sandbox.py` — generuje plik `.wsb` (Windows Sandbox) i
odpala w nim EXE w odizolowanym, tymczasowym systemie:

```
python run_in_sandbox.py results\extracted\photo_like_append_test_program.exe
```

Wymaga Windows 10/11 **Pro/Enterprise/Education** (nie Home) i
jednorazowego włączenia funkcji "Windows Sandbox" w Panelu sterowania
(Programy → Włącz lub wyłącz funkcje systemu Windows), z restartem
po włączeniu. To dobry do wspomnienia w dokumentacji jako
"zweryfikowano też w izolowanym środowisku Windows Sandbox", nawet
jeśli do masowego przetestowania wszystkich 12 kombinacji
wystarczy zwykłe `runs_correctly()`.

**Bezpieczeństwo**: to uruchamia prawdziwy plik wykonywalny — róbcie
to wyłącznie z plikami, które sami skompilowaliście (jak
`data/exe_samples/test_program.exe`), nigdy z plikiem nieznanego
pochodzenia.

## Punkt III.e (wykrywalność) — zaimplementowane w `detect.py`

Parsuje plik zgodnie ze specyfikacją formatu (chunki PNG / segmenty
JPG) i szuka anomalii, **bez znajomości naszego konkretnego klucza/
sygnatury** — tak jakby ktoś dostał podejrzany plik bez wiedzy, co
w nim szukać:
- dane **po** `IEND`/`EOI` → sygnatura metody append (+ szuka bajtów
  `MZ`, czyli nagłówka PE, jako dowodu, że to prawdopodobnie EXE)
- nietypowy klucz chunku `tEXt` (nie z listy popularnych typu
  "Comment"/"Software") → sygnatura metody metadata w PNG
- segment `COM` od razu po `SOI` (przed `APP0`/JFIF — nietypowa
  kolejność) → sygnatura metody metadata w JPG

Uruchomienie dla pojedynczego pliku: `python detect.py sciezka.png`.
`runner.py` woła to automatycznie dla każdej kombinacji — wynik
trafia do kolumny `detectability_notes` w `results.csv`.

## Punkt III.f (przetrwanie po zapisie) — `resave_test.py`

Otwiera każdy stego-plik przez Pillow i zapisuje go ponownie "na
czysto" (bez żadnych dodatkowych opcji — symulacja kogoś, kto nie
wie o ukrytych danych), a potem próbuje `extract()` na nowo
zapisanym pliku. Wynik w `results/resave_results.csv`.

```
python resave_test.py
```

## Wykresy do prezentacji — `generate_charts.py`

Generuje 3 gotowe PNG-i do `results/charts/`: narzut rozmiaru (III.b),
poprawność wyświetlania + integralność (III.a/III.c), przetrwanie
zapisu (III.f). Wymaga wcześniejszego `runner.py` i `resave_test.py`.

```
python generate_charts.py
```

## Podsumowanie wyników (już policzone, do prezentacji)

Z 12 kombinacji (3 obrazy × 2 formaty × 2 metody), z Waszym testowym
`test_program.exe` (39 424 B):

| Kryterium | append | metadata |
|---|---|---|
| III.a wyświetlanie | ✅ 12/12 | ✅ 12/12 |
| III.c integralność SHA-256 | ✅ 12/12 | ✅ 12/12 |
| III.b narzut rozmiaru | +39 440 B (stały) | PNG: +52 592 B (Base64, +33%) / JPG: +39 444 B |
| III.e wykrywalność | **łatwo wykrywalne** — trailing bajty + sygnatura `MZ` znaleziona wprost | wykrywalne, ale subtelniej — nietypowy klucz/kolejność, bez widocznej sygnatury PE |
| III.f przetrwanie zapisu | ❌ 0/12 (Pillow przebudowuje plik od zera) | ❌ 0/12 (Pillow nie przenosi metadanych bez jawnego `pnginfo=`) |

**Kluczowy wniosek na jutro**: obie metody są w pełni niezawodne pod
względem integralności danych (a, c), ale **żadna nie przetrwała
zwykłego ponownego zapisu obrazu** — to pokazuje, że tego typu
steganografia jest krucha wobec najprostszej, przypadkowej "obróbki"
pliku (nie mówiąc już o celowym przeciwdziałaniu). Append jest
trywialny do wykrycia (wystarczy sprawdzić bajty po końcu pliku),
metadata wymaga nieco więcej pracy analitycznej, ale też nie jest
realnie "ukryta" dla kogoś, kto zna format pliku.

III.d (uruchomienie EXE) wymaga odpalenia na Windows — patrz sekcja
wyżej.

## Dane obrazów bazowych

`data/images/` zawiera już wygenerowane 3 kategorie (uzasadnienie w
dokumentacji projektu):

| Nazwa | Charakterystyka | Entropia (bits/px) |
|---|---|---|
| `photo_like` | wysoka entropia (szum+gradient, jak zdjęcie) | ~7.7 |
| `flat_graphic` | niska entropia (płaskie kolory, jak screenshot) | ~1.8 |
| `high_res` | duża rozdzielczość (3840×2160) | ~1.0 |

Każda jest zapisana jako `.png` i `.jpg` (quality=85) — 6 plików
łącznie. Jeśli chcecie je zregenerować (np. inne wymiary), odpalcie
`python generate_test_images.py`.
