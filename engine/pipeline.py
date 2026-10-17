"""Uçtan uca analiz: kural katmanı + parçalama + Gemma + doğrulama + tekilleştirme.

Arayüz (main.py) yalnızca `analiz_et` ve `pseudonymize.maskele` / `sizinti_kontrol`
/ `rapor` fonksiyonlarını çağırır; dönen bulgular `Bulgu.to_dict()` ile JSON olur.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from recognizers import tr_iban, tr_license_plate, tr_national_id

from . import llm
from .chunking import parcala
from .pseudonymize import tekillestir
from .schema import Bulgu, satir_no
from .verify import dogrula

# Melike'nin tr_phone / tr_api_key tanıyıcıları gelince bunlar onlarla değişir.
_EPOSTA = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_TELEFON = re.compile(r"(?<!\d)(?:\+?90[\s-]?)?\(?0?[2-5]\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)")
_API = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})\b")


def _modul_bul(modul, ad: str):
    """recognizers/ içinde varsa tanıyıcıyı kullan, yoksa None."""
    try:
        return __import__(f"recognizers.{modul}", fromlist=["find"]).find
    except ImportError:
        return None


def kural_bulgulari(metin: str) -> list[Bulgu]:
    kaynaklar = [
        ("tc_kimlik", tr_national_id.find, "T.C. Kimlik No (sağlama doğrulandı)", "yuksek"),
        ("iban", tr_iban.find, "TR IBAN (mod-97 doğrulandı)", "yuksek"),
        ("plaka", tr_license_plate.find, "Araç plakası (il kodu doğrulandı)", "dusuk"),
        ("eposta", _EPOSTA.finditer, "E-posta adresi", "orta"),
        ("telefon", _modul_bul("tr_phone", "find") or _TELEFON.finditer, "Telefon numarası", "orta"),
        ("api_anahtari", _modul_bul("tr_api_key", "find") or _API.finditer, "API anahtarı kalıbı", "yuksek"),
    ]
    out = []
    for kategori, bul, neden, risk in kaynaklar:
        for m in bul(metin):
            out.append(
                Bulgu(
                    kaynak="kural", kategori=kategori, kanit=m.group(), neden=neden, risk=risk,
                    guven=1.0, satir=satir_no(metin, m.start()), baslangic=m.start(), bitis=m.end(),
                )
            )
    return out


@dataclass
class Analiz:
    bulgular: list[Bulgu]
    model_kullanildi: bool
    model_durumu: str
    sure_sn: float
    elenen: int = 0  # doğrulanamadı sayısı (ölçüm tablosu için)
    hatalar: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bulgular": [b.to_dict() for b in self.bulgular],
            "model_kullanildi": self.model_kullanildi,
            "model_durumu": self.model_durumu,
            "sure_sn": round(self.sure_sn, 2),
            "dogrulanamadi": self.elenen,
            "hatalar": self.hatalar,
        }


def analiz_et(metin: str, model_kullan: bool = True, model: str = llm.MODEL) -> Analiz:
    t0 = time.perf_counter()
    bulgular = kural_bulgulari(metin)
    durum, kullanildi, hatalar = "Kapalı (yalnızca kural katmanı)", False, []

    if model_kullan:
        hazir, durum = llm.hazir_mi(model)
        if hazir:
            kullanildi = True
            ham: dict[tuple[str, str], dict] = {}
            for parca in parcala(metin):
                try:
                    for b in llm.parca_tara(parca, model=model):
                        anahtar = (b.get("kategori", "diger"), " ".join(str(b["kanit"]).split()))
                        ham.setdefault(anahtar, b)
                except llm.ModelHatasi as e:
                    hatalar.append(f"L{parca.ilk_satir}-L{parca.son_satir}: {e}")
            for b in ham.values():
                bulgu = Bulgu(
                    kaynak="model", kategori=b.get("kategori", "diger"), kanit=str(b["kanit"]),
                    neden=str(b.get("neden", ""))[:300], risk=b.get("risk", "orta"),
                    guven=b.get("guven", 0.7), satir=b.get("satir") if isinstance(b.get("satir"), int) else None,
                )
                bulgular.append(dogrula(metin, bulgu))

    bulgular = tekillestir(bulgular)
    elenen = sum(b.durum == "dogrulanamadi" for b in bulgular)
    return Analiz(bulgular, kullanildi, durum, time.perf_counter() - t0, elenen, hatalar)
