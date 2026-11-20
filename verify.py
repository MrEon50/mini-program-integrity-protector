"""
Mini-PIP - Narzędzie Inspekcji i Weryfikacji (Verify)
Pozwala podejrzeć strukturę bloków i zweryfikować stan łańcucha bez uruchamiania kodu.
"""

import sys
import json
import base64
import argparse
from core import ProjectBlockchain


def inspect_and_verify(package_file: str):
    print("=" * 70)
    print(" 🔍 MINI-PIP: INSPEKCJA I WERYFIKACJA ŁAŃCUCHA BLOKÓW")
    print("=" * 70)

    try:
        blockchain = ProjectBlockchain.load_from_file(package_file)
    except Exception as e:
        print(f"[!] Błąd odczytu pliku: {e}")
        sys.exit(1)

    print(f"[*] Projekt: {blockchain.project_name}")
    print(f"[*] Liczba bloków w łańcuchu: {len(blockchain.blocks)}")
    print(f"[*] Root Hash (Główny Hash): {blockchain.get_root_hash()}")
    print("-" * 70)

    # Wyświetlanie bloków
    for block in blockchain.blocks:
        calc_hash = block.calculate_hash()
        is_hash_ok = (block.hash == calc_hash)
        status_icon = "🟢" if is_hash_ok else "🔴"

        print(f"{status_icon} Blok #{block.index:02d} [{block.block_type:10s}]")
        print(f"   ├─ Hash:      {block.hash}")
        print(f"   ├─ Prev Hash: {block.prev_hash}")
        
        if block.block_type == "GENESIS":
            try:
                meta = json.loads(base64.b64decode(block.data_b64).decode("utf-8"))
                print(f"   └─ Metadane:  {meta}")
            except Exception:
                pass
        else:
            payload_len = len(base64.b64decode(block.data_b64))
            print(f"   └─ Rozmiar zaszyfrowanego bloku: {payload_len} bajtów")
        print()

    print("-" * 70)
    # Weryfikacja powiązań łańcucha
    is_valid, msg, bad_block = blockchain.verify_chain()

    if is_valid:
        print("✅ WYNIK AUDYTU: Łańcuch jest w 100% poprawny!")
        print("   Żaden blok ani powiązanie nie zostały zmodyfikowane.")
    else:
        print("❌ WYNIK AUDYTU: ZNALEZIONO NARUSZENIE INTEGRALNOŚCI!")
        print(f"   Problem w bloku #{bad_block}: {msg}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Weryfikuj i sprawdzaj stan bloków paczki .pip")
    parser.add_argument("package", help="Ścieżka do pliku .pip")
    args = parser.parse_args()

    inspect_and_verify(args.package)


if __name__ == "__main__":
    main()
