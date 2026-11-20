"""
Mini-PIP - Bezpieczny Starter (Launcher)
Weryfikuje integralność łańcucha Blockchain, deszyfruje kod w pamięci RAM i odpala program.
W przypadku jakiejkolwiek modyfikacji natychmiast blokuje uruchomienie i generuje alarm.
"""

import os
import sys
import base64
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core import (
    ProjectBlockchain,
    decrypt_payload,
    load_key_file,
    log_security_event
)


def run_protected_package(package_file: str, key_file: str, script_args: list):
    if not os.path.exists(package_file):
        print(f"[!] BŁĄD: Nie znaleziono paczki: {package_file}")
        sys.exit(1)

    if not os.path.exists(key_file):
        print(f"[!] BŁĄD: Nie znaleziono klucza deszyfrującego: {key_file}")
        print("    Bez klucza program nie może zostać autoryzowany ani uruchomiony.")
        sys.exit(1)

    # 1. Wczytanie paczki
    try:
        blockchain = ProjectBlockchain.load_from_file(package_file)
    except Exception as e:
        print(f"[!] BŁĄD KRYTYCZNY: Uszkodzony format pliku paczki: {e}")
        log_security_event("CORRUPTED_FILE_FORMAT", str(e))
        sys.exit(1)

    # 2. Weryfikacja łańcucha bloków (Integralność)
    is_valid, msg, bad_block_idx = blockchain.verify_chain()

    if not is_valid:
        print("\n" + "=" * 70)
        print("🚨 ALARM BEZPIECZEŃSTWA: WYKRYTO ZMANIPULOWANIE PROGRAMU!")
        print("=" * 70)
        print(f"[!] Wykryto naruszenie w bloku #{bad_block_idx}")
        print(f"[!] Szczegóły błędu: {msg}")
        print("\n[X] Status: ŁAŃCUCH BLOCKCHAIN ZOSTAŁ PRZERWANY.")
        print("[X] Dostęp zablokowany. Program NIE zostanie uruchomiony.")
        print("[X] Odszyfrowanie wstrzymane w celu ochrony Twoich danych i systemu.")
        print("=" * 70)
        print(f"[*] Zdarzenie naruszenia zapisano w: security_audit.log\n")

        log_security_event("TAMPER_DETECTED", f"Plik {package_file}: blok #{bad_block_idx} - {msg}")
        sys.exit(2)

    # 3. Wczytanie klucza i deszyfracja w RAM
    try:
        key = load_key_file(key_file)
    except Exception as e:
        print(f"[!] Błąd wczytywania klucza: {e}")
        sys.exit(1)

    code_chunks = []
    for block in blockchain.blocks:
        if block.block_type == "GENESIS":
            continue
        
        raw_encrypted = base64.b64decode(block.data_b64)
        try:
            decrypted_chunk = decrypt_payload(key, raw_encrypted)
            code_chunks.append(decrypted_chunk)
        except ValueError as e:
            print("\n" + "=" * 70)
            print("🚨 ALARM KRYPTOGRAFICZNY: BŁĄD DESZYFROWANIA / NIEPRAWIDŁOWY KLUCZ!")
            print("=" * 70)
            print(f"[!] Błąd w bloku #{block.index}: {e}")
            print("[X] Podany klucz jest nieprawidłowy lub dane zostały podmienione.")
            print("=" * 70)
            log_security_event("CRYPTO_AUTH_FAIL", f"Błąd w bloku #{block.index}: {e}")
            sys.exit(3)

    full_code = b"".join(code_chunks).decode("utf-8")

    # 4. Wykonanie kodu w locie (In-Memory Execution)
    # Zastępujemy sys.argv argumentami przekazanymi do chronionego programu
    sys.argv = [blockchain.project_name] + script_args

    # Środowisko zmiennych dla chronionego skryptu
    global_env = {
        "__name__": "__main__",
        "__file__": blockchain.project_name,
        "__doc__": None,
    }

    try:
        exec(full_code, global_env)
    except SystemExit as se:
        sys.exit(se.code)
    except Exception as e:
        import traceback
        print(f"[!] Wystąpił błąd w trakcie działania chronionego programu:")
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Mini-PIP Runner - Uruchamiaj chroniony program po weryfikacji blockchaina.")
    parser.add_argument("package", help="Ścieżka do zabezpieczonej paczki (.pip)")
    parser.add_argument("-k", "--key", default="secret.key", help="Ścieżka do pliku klucza (domyślnie: secret.key)")

    args, app_args = parser.parse_known_args()
    run_protected_package(args.package, args.key, app_args)


if __name__ == "__main__":
    main()
