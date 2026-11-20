"""
Przykładowy skrypt testowy (Aplikacja demonstracyjna)
Ten plik zostanie spakowany, zaszyfrowany i zabezpieczony łańcuchem bloków.
"""

import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def super_secret_calculation(a, b):
    # Wyobraź sobie, że to Twój autorski algorytm lub mechanizm licencyjny
    return (a * 42) ^ (b + 1337)

def main():
    print("\n" + "*" * 50)
    print("[*] WITAJ W TWOIM PROGRAMIE!")
    print("   Ten program działa w 100% z pamięci RAM.")
    print("   Nigdy nie został zapisany na dysku w jawnej postaci.")
    print("*" * 50)
    
    user_name = input("Podaj swoje imię: ") if len(sys.argv) <= 1 else sys.argv[1]
    print(f"Miło Cię poznać, {user_name}!")
    
    print("\n[+] Wykonuję autorskie obliczenia...")
    wynik = super_secret_calculation(10, 20)
    print(f"[OK] Tajny wynik algorytmu: {wynik}")
    print("*" * 50 + "\n")

if __name__ == "__main__":
    main()
