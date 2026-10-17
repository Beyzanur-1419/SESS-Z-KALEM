"""Türkiye telefon numarası tanıyıcı: `phonenumbers` kütüphanesi ile.

Kendi regex'imizi yazmak yerine `phonenumbers` kullanılır — Presidio'nun
`PhoneRecognizer`'ı da aynı kütüphaneye dayanıyor (bkz.
docs/rakip-analizi-ve-reuse.md); alan kodu, GSM öneki, +90/0 gibi
varyasyonları kendi regex'imizden çok daha güvenilir ayırt eder.

`find()` arayüzü diğer recognizers/*.py modülleriyle aynı: `match.group()`,
`match.start()`, `match.end()` sağlayan nesneler döndürür (engine/pipeline.py
tüm tanıyıcıları bu arayüzle çağırıyor).
"""

from dataclasses import dataclass

import phonenumbers


@dataclass(frozen=True)
class _Eslesme:
    _metin: str
    _baslangic: int
    _bitis: int

    def group(self) -> str:
        return self._metin

    def start(self) -> int:
        return self._baslangic

    def end(self) -> int:
        return self._bitis


def find(text: str):
    return [
        _Eslesme(text[m.start : m.end], m.start, m.end)
        for m in phonenumbers.PhoneNumberMatcher(text, "TR")
    ]
