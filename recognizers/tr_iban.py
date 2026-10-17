"""TR IBAN tanıyıcı: genel IBAN regex + mod-97 sağlama + TR'ye özel format.

Mod-97 checksum ve TR format regex'i Presidio'nun `IbanRecognizer` /
`iban_patterns.py` dosyalarından (MIT) uyarlanmıştır; presidio-analyzer
paketinin tamamını (spaCy bağımlılığı) eklemek yerine yalnızca gerekli
regex/checksum mantığı taşınmıştır.
Kaynak: https://github.com/data-privacy-stack/presidio (MIT)
"""

import re
import string

GENERIC_PATTERN = re.compile(
    r"(?<![A-Z0-9])TR[0-9]{2}(?:[ -]?[A-Z0-9]{4}){5}[ -]?[A-Z0-9]{2}(?![A-Z0-9])"
)
# TR IBAN: TRkk bbbb bxcc cccc cccc cccc cc  (toplam 26 karakter)
TR_FORMAT = re.compile(r"^TR[0-9]{2}[0-9]{5}[A-Z0-9]{17}$")

LETTERS = {ord(d): str(i) for i, d in enumerate(string.digits + string.ascii_uppercase)}


def _checksum_ok(iban: str) -> bool:
    rearranged = (iban[4:] + iban[:4]).upper().translate(LETTERS)
    try:
        return int(rearranged) % 97 == 1
    except ValueError:
        return False


def validate(iban_text: str) -> bool:
    sanitized = iban_text.replace(" ", "").replace("-", "").upper()
    if not TR_FORMAT.match(sanitized):
        return False
    return _checksum_ok(sanitized)


def find(text: str):
    return [m for m in GENERIC_PATTERN.finditer(text) if validate(m.group())]
