"""
Mini-PIP - Pakowarka Projektu (Packer)
Dzieli kod na porcje, szyfruje każdy blok i łączy je w nienaruszalny łańcuch Blockchain.
"""

import os
import sys
import argparse
from core import (
    ProjectBlockchain,
    encrypt_payload,
    generate_key_file,
    load_key_file
)


def pack_script(input_file: str, output_file: str, key_file: str, chunk_size: int = 1024):
    if not os.path.exists(input_file):
        print(f"[!] BŁĄD: Nie znaleziono pliku wejściowego: {input_file}")
        sys.exit(1)

    print("=" * 65)
    print(" 🛡️  MINI-PIP: PAKOWANIE I ZABEZPIECZANIE PROJEKTU")
    print("=" * 65)

    # 1. Zarządzanie kluczem
    if os.path.exists(key_file):
        print(f"[*] Wczytywanie istniejącego klucza: {key_file}")
        key = load_key_file(key_file)
    else:
        print(f"[+] Generowanie nowego 256-bitowego klucza: {key_file}")
        key = generate_key_file(key_file)

    # 2. Odczyt kodu źródłowego
    with open(input_file, "rb") as f:
        code_bytes = f.read()

    total_size = len(code_bytes)
    print(f"[*] Plik źródłowy: {input_file} ({total_size} bajtów)")

    # 3. Inicjalizacja Blockchaina
    project_name = os.path.basename(input_file)
    blockchain = ProjectBlockchain(project_name=project_name)

    # 4. Tworzenie Bloku Genesis
    genesis_meta = {
        "project": project_name,
        "original_size": total_size,
        "chunk_size": chunk_size,
        "security": "ChaCha20-Poly1305/HMAC-SHA256 + Blockchain",
    }
    genesis_block = blockchain.create_genesis_block(genesis_meta)
    print(f"[+] Blok #0 [Genesis] -> Hash: {genesis_block.hash[:24]}...")

    # 5. Podział kodu na bloki i szyfrowanie
    chunks = [code_bytes[i : i + chunk_size] for i in range(0, total_size, chunk_size)]
    if not chunks:
        chunks = [b""]  # Pusty plik

    for idx, chunk in enumerate(chunks, start=1):
        # Szyfrowanie bloku
        encrypted_chunk = encrypt_payload(key, chunk)
        
        # Dodanie do łańcucha
        block = blockchain.add_block(block_type="CODE_CHUNK", encrypted_bytes=encrypted_chunk)
        print(f"[+] Blok #{block.index} [Kod {len(chunk)} B] -> Hash: {block.hash[:24]}...")

    # 6. Zapisanie gotowej paczki
    blockchain.save_to_file(output_file)
    
    print("-" * 65)
    print(f"[OK] Sukces! Zabezpieczona paczka zapisana w: {output_file}")
    print(f"[OK] Główny Hash Projektu (Root Hash): {blockchain.get_root_hash()}")
    print(f"[!] WAŻNE: Zachowaj plik klucza '{key_file}' – bez niego nikt nie uruchomi programu!")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Mini-PIP Packer - Pakuj i zabezpieczaj kod w łańcuchu blockchain.")
    parser.add_argument("input", help="Ścieżka do skryptu .py, który chcesz zabezpieczyć")
    parser.add_argument("-o", "--output", default=None, help="Ścieżka wyjściowa paczki (domyślnie: <nazwa>.pip)")
    parser.add_argument("-k", "--key", default="secret.key", help="Ścieżka do pliku klucza (domyślnie: secret.key)")
    parser.add_argument("-c", "--chunk-size", type=int, default=1024, help="Rozmiar pojedynczego bloku w bajtach (domyślnie: 1024)")

    args = parser.parse_args()

    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(args.input)
        output_path = base + ".pip"

    pack_script(args.input, output_path, args.key, args.chunk_size)


if __name__ == "__main__":
    main()
