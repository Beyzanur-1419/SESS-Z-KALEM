"""T.C. Kimlik No tanıyıcı: regex + NVİ sağlama (checksum) algoritması.

Doğrulama mantığı Microsoft Presidio'nun `TrNationalIdRecognizer` sınıfından
(presidio-analyzer, MIT lisans, data-privacy-stack/presidio) uyarlanmıştır.
Burada presidio-analyzer paketine (spaCy bağımlılığı getirir, ~100+ MB ve
model indirmesi gerektirir) ihtiyaç duymamak için yalnızca regex + checksum
mantığı sade Python'a taşınmıştır; sınıf hiyerarşisi alınmamıştır.
Kaynak: https://github.com/data-privacy-stack/presidio (MIT)
"""

import re

PATTERN = re.compile(r"\b[1-9][0-9]{10}\b")


def validate_checksum(tckn: str) -> bool:
    if len(tckn) != 11 or not tckn.isdigit() or tckn[0] == "0":
        return False
    digits = [int(d) for d in tckn]
    odd_sum = sum(digits[i] for i in range(0, 9, 2))
    even_sum = sum(digits[i] for i in range(1, 8, 2))
    tenth = (odd_sum * 7 - even_sum) % 10
    if tenth != digits[9]:
        return False
    eleventh = sum(digits[:10]) % 10
    return eleventh == digits[10]


def find(text: str):
    """Metindeki geçerli T.C. Kimlik No eşleşmelerini (match objesi) döndürür."""
    return [m for m in PATTERN.finditer(text) if validate_checksum(m.group())]
