"""
Generuje 3 obrazy bazowe (rozne charakterystyki tresci) i zapisuje
kazdy w wersji PNG i JPG do data/images/.

Kategorie (uzasadnienie w dokumentacji - wplyw tresci obrazu na
steganografie/wykrywalnosc):
  1. photo_like   - wysoka entropia (szum + gradienty, jak zdjecie)
  2. flat_graphic - niska entropia (plaskie kolory, jak screenshot/ikona)
  3. high_res      - duza rozdzielczosc (sprawdza wplyw skali pliku)

Uruchomienie:
    python generate_test_images.py
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT_DIR = Path("data/images")
JPEG_QUALITY = 85  # ustalona jakosc kompresji - stala dla wszystkich testow


def make_photo_like(size=(800, 600)) -> Image.Image:
    """Wysoka entropia: losowy szum + plynne gradienty (symulacja zdjecia)."""
    rng = np.random.default_rng(42)
    w, h = size
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xv, yv = np.meshgrid(x, y)
    gradient = np.stack(
        [
            (np.sin(xv * 6) * 0.5 + 0.5),
            (np.cos(yv * 4) * 0.5 + 0.5),
            (np.sin((xv + yv) * 5) * 0.5 + 0.5),
        ],
        axis=-1,
    )
    noise = rng.normal(0, 0.08, size=(h, w, 3))
    arr = np.clip(gradient + noise, 0, 1)
    return Image.fromarray((arr * 255).astype(np.uint8), mode="RGB")


def make_flat_graphic(size=(800, 600)) -> Image.Image:
    """Niska entropia: plaskie kolory + proste ksztalty (jak screenshot/UI)."""
    img = Image.new("RGB", size, color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, size[0] - 40, 140], fill=(30, 90, 200))
    draw.rectangle([40, 180, 380, 420], fill=(220, 220, 220), outline=(30, 30, 30), width=3)
    draw.ellipse([440, 180, 760, 420], fill=(60, 180, 90))
    draw.line([40, 460, size[0] - 40, 460], fill=(10, 10, 10), width=4)
    return img


def make_high_res(size=(3840, 2160)) -> Image.Image:
    """Duza rozdzielczosc: powtarzalny wzor (checkerboard) w skali 4K."""
    tile = 40
    w, h = size
    xv, yv = np.meshgrid(np.arange(w) // tile, np.arange(h) // tile)
    pattern = ((xv + yv) % 2).astype(np.uint8) * 255
    arr = np.stack([pattern, 255 - pattern, np.full_like(pattern, 128)], axis=-1)
    return Image.fromarray(arr, mode="RGB")


def shannon_entropy(img: Image.Image) -> float:
    """Entropia Shannon w bitach/piksel (po splaszczeniu do grayscale)."""
    gray = np.array(img.convert("L"))
    hist, _ = np.histogram(gray, bins=256, range=(0, 255), density=True)
    hist = hist[hist > 0]
    return float(-np.sum(hist * np.log2(hist)))


def save_both_formats(img: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUT_DIR / f"{name}.png"
    jpg_path = OUT_DIR / f"{name}.jpg"
    img.save(png_path, format="PNG")
    img.convert("RGB").save(jpg_path, format="JPEG", quality=JPEG_QUALITY)

    entropy = shannon_entropy(img)
    print(f"{name}:")
    print(f"  rozdzielczosc: {img.size[0]}x{img.size[1]}")
    print(f"  entropia (bits/px): {entropy:.3f}")
    print(f"  PNG: {png_path}  ({png_path.stat().st_size:,} B)")
    print(f"  JPG: {jpg_path}  ({jpg_path.stat().st_size:,} B)")
    print()


if __name__ == "__main__":
    save_both_formats(make_photo_like(), "photo_like")
    save_both_formats(make_flat_graphic(), "flat_graphic")
    save_both_formats(make_high_res(), "high_res")
