"""Birleşik bulgu nesnesi — docs/api-contract.md §2'nin Python karşılığı.

Kural, model ve elle eklenen bulgular aynı tipe dönüşür; arayüz (Beyza) ve
ölçüm (Melike) yalnızca `Bulgu.to_dict()` çıktısını görür.

Konum notu: `baslangic` / `bitis` BELGE düzeyinde karakter ofsetleridir
(recognizer `match.start()` / `match.end()` ile aynı). `satir` 1'den başlar.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Optional

# Modelden istenen kategoriler (§1)
MODEL_KATEGORILERI = [
    "teklif_bedeli",
    "kod_adi",
    "ozel_anlasma",
    "musteri_bilgisi",
    "strateji",
    "diger",
]
# Kural katmanının kategorileri (§2)
KURAL_KATEGORILERI = ["tc_kimlik", "iban", "telefon", "plaka", "api_anahtari", "eposta"]

# Maskeleme etiketi önekleri: [KOD_ADI_1], [TUTAR_1] ...
ETIKET_ONEKI = {
    "teklif_bedeli": "TUTAR",
    "kod_adi": "KOD_ADI",
    "ozel_anlasma": "OZEL_ANLASMA",
    "musteri_bilgisi": "MUSTERI",
    "strateji": "STRATEJI",
    "diger": "GIZLI",
    "tc_kimlik": "TCKN",
    "iban": "IBAN",
    "telefon": "TELEFON",
    "plaka": "PLAKA",
    "api_anahtari": "API_ANAHTARI",
    "eposta": "EPOSTA",
}

_sayac = itertools.count(1)


def yeni_id() -> str:
    return f"f-{next(_sayac):04d}"


@dataclass
class Bulgu:
    kaynak: str  # kural | model | elle
    kategori: str
    kanit: str
    neden: str = ""
    risk: str = "orta"  # yuksek | orta | dusuk
    guven: float = 1.0
    satir: Optional[int] = None
    baslangic: Optional[int] = None
    bitis: Optional[int] = None
    durum: str = "dogrulandi"  # dogrulandi | dogrulanamadi
    karar: str = "beklemede"  # beklemede | kabul | red
    etiket: Optional[str] = None
    id: str = field(default_factory=yeni_id)

    def __post_init__(self) -> None:
        if self.kategori not in ETIKET_ONEKI:
            self.kategori = "diger"
        if self.risk not in ("yuksek", "orta", "dusuk"):
            self.risk = "orta"
        try:
            self.guven = max(0.0, min(1.0, float(self.guven)))
        except (TypeError, ValueError):
            self.guven = 0.5

    @property
    def konumlu(self) -> bool:
        return self.baslangic is not None and self.bitis is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kaynak": self.kaynak,
            "kategori": self.kategori,
            "kanit": self.kanit,
            "konum": (
                {"satir": self.satir, "baslangic": self.baslangic, "bitis": self.bitis}
                if self.konumlu
                else None
            ),
            "neden": self.neden,
            "risk": self.risk,
            "guven": self.guven,
            "durum": self.durum,
            "karar": self.karar,
            "etiket": self.etiket,
        }


def satir_no(metin: str, ofset: int) -> int:
    """Belge ofsetinin 1 tabanlı satır numarası."""
    return metin.count("\n", 0, ofset) + 1
