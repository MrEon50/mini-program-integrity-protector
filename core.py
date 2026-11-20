"""
Mini-PIP (Program Integrity Protector) - Core Engine
Łączy silne szyfrowanie (ChaCha20 + HMAC-SHA256) z niezmiennym łańcuchem bloków (Blockchain).
Działa w 100% na czystej bibliotece standardowej Pythona (zero zewnętrznych zależności).
"""

import os
import sys
import json
import time
import struct
import base64
import hashlib
import hmac
from typing import List, Dict, Tuple, Optional


# ==============================================================================
# 1. WARSTWA KRYPTOGRAFICZNA (RFC 8439 ChaCha20 + HMAC-SHA256 Authenticated Encryption)
# ==============================================================================

def _quarter_round(x: List[int], a: int, b: int, c: int, d: int):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = (((x[d] ^ x[a]) << 16) | ((x[d] ^ x[a]) >> 16)) & 0xFFFFFFFF
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = (((x[b] ^ x[c]) << 12) | ((x[b] ^ x[c]) >> 20)) & 0xFFFFFFFF
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = (((x[d] ^ x[a]) << 8) | ((x[d] ^ x[a]) >> 24)) & 0xFFFFFFFF
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = (((x[b] ^ x[c]) << 7) | ((x[b] ^ x[c]) >> 25)) & 0xFFFFFFFF


def _chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    key_words = list(struct.unpack("<8I", key))
    nonce_words = list(struct.unpack("<3I", nonce))
    state = constants + key_words + [counter & 0xFFFFFFFF] + nonce_words
    initial_state = list(state)

    for _ in range(10):  # 20 rounds
        _quarter_round(state, 0, 4, 8, 12)
        _quarter_round(state, 1, 5, 9, 13)
        _quarter_round(state, 2, 6, 10, 14)
        _quarter_round(state, 3, 7, 11, 15)
        _quarter_round(state, 0, 5, 10, 15)
        _quarter_round(state, 1, 6, 11, 12)
        _quarter_round(state, 2, 7, 8, 13)
        _quarter_round(state, 3, 4, 9, 14)

    out = [(state[i] + initial_state[i]) & 0xFFFFFFFF for i in range(16)]
    return struct.pack("<16I", *out)


def _chacha20_crypt(key: bytes, nonce: bytes, data: bytes, counter: int = 1) -> bytes:
    result = bytearray()
    for i in range(0, len(data), 64):
        block = _chacha20_block(key, counter + (i // 64), nonce)
        chunk = data[i : i + 64]
        for b1, b2 in zip(chunk, block):
            result.append(b1 ^ b2)
    return bytes(result)


def derive_keys(master_key: bytes) -> Tuple[bytes, bytes]:
    """Wyprowadza klucz szyfrowania (enc_key) i klucz podpisu (mac_key) z master_key."""
    enc_key = hashlib.sha256(master_key + b"mini_pip_encryption_key_v1").digest()
    mac_key = hashlib.sha256(master_key + b"mini_pip_authentication_key_v1").digest()
    return enc_key, mac_key


def encrypt_payload(master_key: bytes, plaintext: bytes) -> bytes:
    """
    Szyfruje dane algorytmem ChaCha20 i podpisuje HMAC-SHA256 (Encrypt-then-MAC).
    Format wyjściowy: [HMAC 32 bajty] + [NONCE 12 bajtów] + [CIPHERTEXT]
    """
    enc_key, mac_key = derive_keys(master_key)
    nonce = os.urandom(12)
    ciphertext = _chacha20_crypt(enc_key, nonce, plaintext)
    
    # HMAC liczymy nad: nonce + ciphertext
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    return tag + nonce + ciphertext


def decrypt_payload(master_key: bytes, package: bytes) -> bytes:
    """
    Weryfikuje podpis HMAC i deszyfruje dane.
    Zwraca odszyfrowane bajty lub rzuca ValueError jeśli wykryto ingerencję.
    """
    if len(package) < 32 + 12:
        raise ValueError("Uszkodzony pakiet danych: zbyt mały rozmiar.")

    tag = package[:32]
    nonce = package[32:44]
    ciphertext = package[44:]

    enc_key, mac_key = derive_keys(master_key)
    expected_tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Błąd weryfikacji kryptograficznej (HMAC mismatch) - dane zostały zmodyfikowane!")

    return _chacha20_crypt(enc_key, nonce, ciphertext)


# ==============================================================================
# 2. WARSTWA BLOCKCHAIN (Niezmienny łańcuch bloków integralności)
# ==============================================================================

class Block:
    def __init__(self, index: int, block_type: str, timestamp: float, data_b64: str, prev_hash: str, block_hash: Optional[str] = None):
        self.index = index
        self.block_type = block_type  # "GENESIS" | "CODE_CHUNK"
        self.timestamp = timestamp
        self.data_b64 = data_b64
        self.prev_hash = prev_hash
        self.hash = block_hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        """Kryptograficzny hash SHA-256 wiążący wszystkie metadane i zawartość bloku."""
        hasher = hashlib.sha256()
        hasher.update(str(self.index).encode("utf-8"))
        hasher.update(self.block_type.encode("utf-8"))
        hasher.update(f"{self.timestamp:.6f}".encode("utf-8"))
        hasher.update(self.prev_hash.encode("utf-8"))
        hasher.update(self.data_b64.encode("utf-8"))
        return hasher.hexdigest()

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "block_type": self.block_type,
            "timestamp": self.timestamp,
            "data_b64": self.data_b64,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'Block':
        return cls(
            index=d["index"],
            block_type=d["block_type"],
            timestamp=d["timestamp"],
            data_b64=d["data_b64"],
            prev_hash=d["prev_hash"],
            block_hash=d.get("hash")
        )


class ProjectBlockchain:
    def __init__(self, project_name: str = "MiniPIP-App"):
        self.project_name = project_name
        self.blocks: List[Block] = []

    def create_genesis_block(self, metadata: Dict) -> Block:
        """Tworzy pierwszy blok łańcucha (Genesis) zawierający metadane projektu."""
        meta_json = json.dumps(metadata, sort_keys=True).encode("utf-8")
        genesis_data_b64 = base64.b64encode(meta_json).decode("utf-8")
        
        genesis = Block(
            index=0,
            block_type="GENESIS",
            timestamp=time.time(),
            data_b64=genesis_data_b64,
            prev_hash="0" * 64
        )
        self.blocks.append(genesis)
        return genesis

    def add_block(self, block_type: str, encrypted_bytes: bytes) -> Block:
        """Dołącza nowy blok powiązany kryptograficznie z poprzednim."""
        if not self.blocks:
            raise ValueError("Brak bloku Genesis! Najpierw stwórz Genesis.")

        prev_block = self.blocks[-1]
        data_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")

        new_block = Block(
            index=len(self.blocks),
            block_type=block_type,
            timestamp=time.time(),
            data_b64=data_b64,
            prev_hash=prev_block.hash
        )
        self.blocks.append(new_block)
        return new_block

    def get_root_hash(self) -> str:
        """Zwraca hash ostatniego bloku (Root Hash całego projektu)."""
        if not self.blocks:
            return ""
        return self.blocks[-1].hash

    def verify_chain(self) -> Tuple[bool, str, Optional[int]]:
        """
        Weryfikuje cały łańcuch bloków od Genesis do końca.
        Zwraca: (czy_poprawny, komunikat, indeks_błędnego_bloku)
        """
        if not self.blocks:
            return False, "Pusty łańcuch bloków.", None

        # 1. Weryfikacja Genesis
        genesis = self.blocks[0]
        if genesis.index != 0 or genesis.prev_hash != "0" * 64:
            return False, "Blok Genesis został naruszony!", 0
        if genesis.hash != genesis.calculate_hash():
            return False, "Niezgodność hasha w Bloku Genesis!", 0

        # 2. Weryfikacja kolejnych bloków w łańcuchu
        for i in range(1, len(self.blocks)):
            current = self.blocks[i]
            previous = self.blocks[i - 1]

            # Sprawdzenie wskaźnika wstecz (Backlink)
            if current.prev_hash != previous.hash:
                return False, (
                    f"Przerwany łańcuch w Bloku #{current.index}! "
                    f"Oczekiwano poprzedniego hasha {previous.hash[:16]}..., "
                    f"a odczytano {current.prev_hash[:16]}..."
                ), current.index

            # Sprawdzenie spójności zawartości bloku
            expected_hash = current.calculate_hash()
            if current.hash != expected_hash:
                return False, (
                    f"Zmodyfikowano zawartość Bloku #{current.index}! "
                    f"Zapisany hash {current.hash[:16]}... != obliczony {expected_hash[:16]}..."
                ), current.index

        return True, "Łańcuch blockchain jest w 100% spójny i nienaruszony.", None

    def save_to_file(self, file_path: str):
        """Zapisuje chronioną paczkę do pliku JSON."""
        data = {
            "format": "MINI-PIP-v1",
            "project_name": self.project_name,
            "root_hash": self.get_root_hash(),
            "total_blocks": len(self.blocks),
            "blocks": [b.to_dict() for b in self.blocks]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'ProjectBlockchain':
        """Wczytuje chronioną paczkę z pliku."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chain = cls(project_name=data.get("project_name", "MiniPIP-App"))
        for b_dict in data.get("blocks", []):
            chain.blocks.append(Block.from_dict(b_dict))
        return chain


# ==============================================================================
# 3. ZARZĄDZANIE KLUCZAMI I LOGAMI
# ==============================================================================

def generate_key_file(key_path: str) -> bytes:
    """Generuje nowy 256-bitowy klucz szyfrujący i zapisuje go w formacie base64."""
    key = os.urandom(32)
    b64_key = base64.b64encode(key).decode("utf-8")
    with open(key_path, "w", encoding="utf-8") as f:
        f.write(b64_key.strip())
    return key


def load_key_file(key_path: str) -> bytes:
    """Wczytuje klucz szyfrujący z pliku."""
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Nie znaleziono pliku klucza: {key_path}")
    with open(key_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return base64.b64decode(content)


def log_security_event(event_type: str, details: str, log_file: str = "security_audit.log"):
    """Zapisuje zdarzenie naruszenia integralności do lokalnego dziennika audytu."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    entry = f"[{timestamp}] [{event_type}] {details}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
