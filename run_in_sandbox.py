"""
Generuje plik .wsb (Windows Sandbox Configuration) do uruchomienia
odzyskanego EXE w pelnej izolacji - to jest "kontrolowane srodowisko"
z punktu III.d w bardziej rygorystycznej wersji niz zwykle
subprocess.run() w metrics.py (ktore odpala plik bezposrednio na
Waszym systemie - OK dla wlasnego, znanego pliku testowego, ale
.wsb daje dodatkowa warstwe izolacji, ktora latwo opisac w
dokumentacji jako "kontrolowane srodowisko").

Wymagania:
  - Windows 10/11 Pro, Enterprise lub Education (Sandbox NIE jest
    dostepny na Windows Home)
  - Wlaczona funkcja "Windows Sandbox" (Panel sterowania -> Programy
    -> Wlacz lub wylacz funkcje systemu Windows -> Windows Sandbox),
    wymaga restartu po wlaczeniu

Uzycie:
    python run_in_sandbox.py results\\extracted\\photo_like_append_test_program.exe

Otworzy sie plik .wsb w folderze %TEMP% - kliknij go dwukrotnie
(albo skrypt sam go odpali), zeby uruchomic Windows Sandbox,
ktory automatycznie odpali ten EXE w izolowanym, tymczasowym
systemie (znikajacym po zamknieciu okna sandboxa).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def build_wsb_config(exe_path: Path) -> str:
    exe_path = exe_path.resolve()
    folder = exe_path.parent
    # MappedFolders udostepnia folder z EXE wewnatrz sandboxa (read-only),
    # LogonCommand automatycznie odpala plik zaraz po starcie sandboxa.
    return f"""<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>{folder}</HostFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>cmd /c start "" "C:\\Users\\WDAGUtilityAccount\\Desktop\\{folder.name}\\{exe_path.name}"</Command>
  </LogonCommand>
</Configuration>
"""


def main() -> None:
    if len(sys.argv) != 2:
        print("Uzycie: python run_in_sandbox.py <sciezka_do_exe>")
        sys.exit(1)

    exe_path = Path(sys.argv[1])
    if not exe_path.exists():
        print(f"Nie znaleziono pliku: {exe_path}")
        sys.exit(1)

    wsb_content = build_wsb_config(exe_path)
    wsb_path = Path(tempfile.gettempdir()) / f"{exe_path.stem}_sandbox.wsb"
    wsb_path.write_text(wsb_content, encoding="utf-8")

    print(f"Utworzono konfiguracje: {wsb_path}")
    print("Otwieram Windows Sandbox...")

    if os.name == "nt":
        os.startfile(str(wsb_path))  # type: ignore[attr-defined]
    else:
        print("Ten skrypt dziala tylko na Windows (wymaga Windows Sandbox).")


if __name__ == "__main__":
    main()
