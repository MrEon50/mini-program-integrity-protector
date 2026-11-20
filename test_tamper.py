"""
Skrypt demonstracyjny ataku i sabotażu (Tamper Simulator)
Kopiuje zabezpieczony plik, zmienia w nim losowo 1 bajt (symulacja hakera)
i uruchamia weryfikację, aby pokazać, jak system natychmiast wyłapuje ingerencję.
"""

import os
import sys
import subprocess
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def run_cmd(cmd):
    # Wymuszamy UTF-8 w komunikacji subprocess na Windowsie
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=my_env)
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 70)
    print(" 🧪 MINI-PIP: TEST ZABEZPIECZENIA PRZED MODYFIKACJĄ (TAMPER TEST)")
    print("=" * 70)

    demo_app = "demo_app.py"
    clean_package = "demo_app.pip"
    tampered_package = "tampered_app.pip"
    key_file = "secret.key"

    # 1. Pakowanie czystego programu
    print("\n[KROK 1] Pakowanie i szyfrowanie czystego programu demo_app.py...")
    code, out, _ = run_cmd(["pack.py", demo_app, "-o", clean_package, "-k", key_file, "-c", "256"])
    print(out)

    # 2. Uruchomienie czystego programu (test sukcesu)
    print("\n[KROK 2] Sprawdzanie normalnego uruchomienia czystej paczki...")
    code, out, err = run_cmd(["run.py", clean_package, "-k", key_file, "Tester"])
    print(out)
    if code != 0:
        print(f"[!] Błąd podczas czystego uruchomienia: {err}")
        return

    # 3. Sabotaż: Tworzenie zmanipulowanej kopii (zmiana 1 znaku w danych bloku #2)
    print("\n[KROK 3] Symulacja ataku hakera: zmiana danych wewnątrz Bloku #2...")
    shutil.copyfile(clean_package, tampered_package)
    
    with open(tampered_package, "r", encoding="utf-8") as f:
        import json
        data = json.load(f)
    
    # Podmieniamy ostatnie 4 znaki w zaszyfrowanych danych bloku #2
    old_b64 = data["blocks"][2]["data_b64"]
    data["blocks"][2]["data_b64"] = old_b64[:-4] + "AAAA"
    
    with open(tampered_package, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[*] W pliku '{tampered_package}' podmieniono dane w Bloku #2 bez naruszania struktury JSON.")

    # 4. Sprawdzenie reakcji Launchera na zmodyfikowany plik
    print("\n[KROK 4] Próba uruchomienia zmanipulowanego programu...")
    code, out, err = run_cmd(["run.py", tampered_package, "-k", key_file, "Tester"])
    print(out)

    if code != 0:
        print("🎯 SUKCES TESTU! Launcher natychmiast zablokował uruchomienie i wyświetlił alarm!")
    else:
        print("❌ BŁĄD TESTU: Zmanipulowany program uruchomił się bez ostrzeżenia!")

    print("=" * 70)

if __name__ == "__main__":
    main()
