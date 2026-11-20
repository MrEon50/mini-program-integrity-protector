# Mini-PIP: Program Integrity Protector (Python + Blockchain)

Lekkie, w 100% niezależne narzędzie (zero zewnętrznych bibliotek, czysty Python) do zabezpieczania własnych projektów przed nieautoryzowanymi modyfikacjami na niskim poziomie oraz kradzieżą kodu.

---

## 💡 Jak to działa?

1. **Szyfrowanie blokowe (Poufność):**
   * Twój kod źródłowy jest dzielony na porcje (bloki) i szyfrowany kryptograficznie algorytmem **ChaCha20** z uwierzytelnieniem **HMAC-SHA256** (zgodnie ze standardem RFC 8439).
   * Na dysku nikt nie podejrzy algorytmów ani logiki – plik to czysty, zaszyfrowany szum.

2. **Łańcuch bloków (Mikro-Blockchain):**
   * Każdy blok posiada swój unikalny Hash SHA-256 oraz nierozerwalny odnośnik do hasha poprzedniego bloku (`prev_hash`).
   * Zmiana choćby 1 bajtu w pliku (np. w hex-edytorze) powoduje natychmiastowe przerwanie łańcucha powiązań i odmowę uruchomienia.

3. **Uruchamianie w RAM (In-Memory Execution):**
   * Kod jest weryfikowany i odszyfrowywany **wyłącznie w pamięci operacyjnej**.
   * Na dysku nie pojawia się żaden plik tymczasowy, co uniemożliwia proste przechwycenie kodu z dysku.

---

## 📁 Struktura plików

| Plik | Rola |
|---|---|
| `core.py` | Silnik kryptograficzny (ChaCha20, HMAC, SHA-256) oraz struktury Blockchain (`Block`, `ProjectBlockchain`). |
| `pack.py` | Narzędzie dla Ciebie: pakuje Twój skrypt Python w zabezpieczoną paczkę `.pip`. |
| `run.py` | Starter (Launcher): weryfikuje integralność łańcucha, deszyfruje w RAM i uruchamia program. |
| `verify.py` | Narzędzie inspekcji: pozwala podejrzeć status każdego bloku i wykryć manipulacje. |
| `demo_app.py` | Przykładowy program do przetestowania. |
| `test_tamper.py` | Automatyczny symulator ataku: modyfikuje plik i sprawdza reakcję alarmową. |

---

## 🚀 Instrukcja obsługi (Szybki start)

### 1. Zabezpieczenie (Spakowanie) programu:
```bash
python pack.py demo_app.py
```
* Wygeneruje plik `demo_app.pip` (zabezpieczona paczka) oraz `secret.key` (klucz szyfrujący).

### 2. Uruchomienie zabezpieczonego programu:
```bash
python run.py demo_app.pip
```
* Program zweryfikuje łańcuch w ułamku sekundy i wystartuje z pamięci RAM.

### 3. Inspekcja stanu bloków:
```bash
python verify.py demo_app.pip
```
* Zobaczysz wizualny raport o stanie każdego bloku (zielone checkmarki lub czerwone alarmy).

### 4. Test sabotażowy (Symulacja ataku hakera):
```bash
python test_tamper.py
```
* Skrypt zmodyfikuje zawartość Bloku #2 i spróbuje go odpalić. Zobaczysz natychmiastową blokadę i alarm bezpieczeństwa!

---

## 📦 Kompilacja do pliku `.exe` (Dystrybucja bez Pythona)

Sam starter `run.py` można w prosty sposób skompilować do natywnego pliku wykonywalnego Windows (`.exe`) za pomocą narzędzi takich jak **PyInstaller** lub **Nuitka**.

### Sposób kompilacji launchera:
```bash
pyinstaller --onefile --name launcher run.py
```
Po kompilacji w folderze `dist/` powstanie samodzielny plik `launcher.exe`.

### Model dystrybucji z plikiem zewnętrznym:
Użytkownik końcowy **nie musi mieć zainstalowanego Pythona**. Wystarczy przekazać mu:
```text
launcher.exe
moj_program.pip      <-- zaszyfrowany program spięty blockchainem
secret.key           <-- plik klucza autoryzacyjnego
```
Uruchomienie:
```bash
launcher.exe moj_program.pip
```

### 🛡️ Przewaga nad standardowym PyInstallerem:
* **Standardowy plik .exe z PyInstallera:** Każdy początkujący może pobrać darmowe narzędzie (np. `pyinstxtractor`) i w kilka sekund wyciągnąć ze skompilowanego pliku `.exe` cały kod źródłowy w postaci plików `.pyc` / `.py`.
* **Rozwiązanie z Mini-PIP:** Wewnątrz pliku `.exe` znajduje się tylko mechanizm weryfikacji. Właściwy program leży w zaszyfrowanym pliku `.pip`. Nawet dekompilacja launchera nie ujawnia kodu Twojej aplikacji, a jakakolwiek próba ingerencji w plik `.pip` wywoła natychmiastowy alarm i blokadę wykonania.

### 🌟 Wariant All-In-One (Pojedynczy plik .exe):
Istnieje również możliwość zaszycia wygenerowanej paczki `.pip` oraz mechanizmu sprawdzającego wewnątrz jednego pliku `MojProgram.exe`. W tym wariancie:
1. Użytkownik otrzymuje tylko jeden plik `.exe`.
2. Przy starcie program bada swój własny łańcuch bloków zaszyty w zasobach binarki.
3. Jeśli ktoś spróbuje zmodyfikować kod maszynowy lub ominąć warunki licencyjne w hex-edytorze – suma kontrolna i łańcuch hashów pękają, a program odmawia uruchomienia.

---

## 🧠 Dlaczego kryptograficzna integralność przewyższa antywirusy?

W tradycyjnym podejściu polega się na programach antywirusowych (EDR / AV). Mają one jednak istotne ograniczenia:
* Antywirus szuka **znanych sygnatur złośliwego oprogramowania** lub opiera się na heurystyce. Jeśli ktoś zmodyfikuje Twój program w celu ominięcia licencji, usunięcia znaku wodnego lub kradzieży algorytmu, antywirus w ogóle na to nie zareaguje, bo taka modyfikacja nie jest wirusem.
* **Mini-PIP stosuje zasadę Zero-Trust (Samoobrona aplikacji):** 
  Program sam staje się swoim strażnikiem. Opiera się na czystej matematyce (SHA-256 i ChaCha20). Każdy blok kodu jest poświadczany przez poprzedni. Nawet zmiana 1 bitu w kodzie sprawia, że program samoczynnie odmówi działania, dając 100% gwarancji, że kod wykonujący się w pamięci jest dokładnie tym, co podpisał autor.
