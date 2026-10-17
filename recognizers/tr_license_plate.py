"""Türkiye araç plakası tanıyıcı: regex + il kodu (01-81) doğrulaması.

Presidio'nun `TrLicensePlateRecognizer` sınıfından (MIT) uyarlanmıştır; aynı
gerekçeyle (bkz. tr_national_id.py) sınıf hiyerarşisi değil yalnızca
regex/doğrulama mantığı taşınmıştır.
Kaynak: https://github.com/data-privacy-stack/presidio (MIT)
"""

import re

PATTERNS = [
    re.compile(r"\b(0[1-9]|[1-7][0-9]|8[0-1])\s?[A-PR-VY-Z]{1,3}\s?\d{2,4}\b"),
    re.compile(r"\b(0[1-9]|[1-7][0-9]|8[0-1])-[A-PR-VY-Z]{1,3}-\d{2,4}\b"),
]


def validate(plate_text: str) -> bool:
    sanitized = plate_text.replace("-", "").replace(" ", "")
    if len(sanitized) < 3 or not sanitized[:2].isdigit():
        return False
    return 1 <= int(sanitized[:2]) <= 81


def find(text: str):
    matches = []
    for pattern in PATTERNS:
        matches.extend(m for m in pattern.finditer(text) if validate(m.group()))
    return matches
