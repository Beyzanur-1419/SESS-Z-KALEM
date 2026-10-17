"""Kanıt doğrulama — docs/api-contract.md §3 kademeli arama.

Model `kanit` metnini ve bir `satir` ipucu döndürür. Bu modül metni belgede
arar ve KESİN konumu bulur. Sıra (ilk bulan kazanır, aynı adımda birden çok
eşleşme varsa `satir` ipucuna en yakın olan seçilir):

  1. Aynı satırda tam eşleşme (boşluklar esnek)
  2. Satır sonuna bölünmüş eşleşme ("Proje\\nKartal")
  3. Büyük/küçük harf duyarsız, kelime içi eşleşme (Türkçe I/ı, İ/i doğru)
  4. Türkçe ek onarımı: "Kartal'a" -> "Kartal" (kök önce denenir, bkz. dogrula)

Hiçbiri bulamazsa bulgu SİLİNMEZ: durum="dogrulanamadi", konum=None.
Bulunursa `kanit` belgedeki gerçek metinle değiştirilir (maskeleme bunu kullanır).
"""
from __future__ import annotations

import re
from typing import Optional

from .schema import Bulgu, satir_no

# Uzunluğu koruyan Türkçe küçük harf dönüşümü (ofsetler kaymasın)
_TR_KUCUK = str.maketrans({"I": "ı", "İ": "i"})
_KESME = re.compile(r"[’'`´]\w*$")


def tr_kucuk(s: str) -> str:
    out = s.translate(_TR_KUCUK).lower()
    # .lower() bazı harflerde uzunluk değiştirebilir; o durumda orijinali kullan
    return out if len(out) == len(s) else s


def _desen(kanit: str, satir_ici: bool) -> Optional[re.Pattern]:
    parcalar = kanit.split()
    if not parcalar:
        return None
    ayrac = r"[ \t]+" if satir_ici else r"\s+"
    return re.compile(ayrac.join(re.escape(p) for p in parcalar))


def _en_yakin(metin: str, eslesmeler: list[re.Match], ipucu: Optional[int]) -> Optional[re.Match]:
    if not eslesmeler:
        return None
    if ipucu is None:
        return eslesmeler[0]
    return min(eslesmeler, key=lambda m: abs(satir_no(metin, m.start()) - ipucu))


def _ara(metin: str, kanit: str, ipucu: Optional[int]) -> Optional[tuple[int, int]]:
    # Adım 1: tek satırda
    d = _desen(kanit, satir_ici=True)
    if d is None:
        return None
    m = _en_yakin(metin, list(d.finditer(metin)), ipucu)
    if m:
        return m.start(), m.end()
    # Adım 2: satır sonuna bölünmüş
    d = _desen(kanit, satir_ici=False)
    m = _en_yakin(metin, list(d.finditer(metin)), ipucu)
    if m:
        return m.start(), m.end()
    # Adım 3: harf duyarsız (uzunluk koruyan dönüşümle aynı ofsetler)
    d = _desen(tr_kucuk(kanit), satir_ici=False)
    m = _en_yakin(metin, list(d.finditer(tr_kucuk(metin))), ipucu)
    if m:
        return m.start(), m.end()
    return None


def dogrula(metin: str, bulgu: Bulgu, min_uzunluk: int = 2) -> Bulgu:
    kanit = bulgu.kanit.strip()
    # Adım 4: kesmeli eki at ("Kartal'a" -> "Kartal"). Kök ÖNCE denenir: böylece
    # maskeleme kökü belgenin her yerinde kapatır ("Kartal", "Kartal'ın", ...)
    # ve aynı kişi tek etiket alır. Kök bulunamazsa ekli hali denenir.
    kok = _KESME.sub("", kanit)
    aday = [kok, kanit] if kok != kanit else [kanit]

    for k in aday:
        if len(k) < min_uzunluk:
            continue
        konum = _ara(metin, k, bulgu.satir)
        if konum:
            bas, bit = konum
            bulgu.baslangic, bulgu.bitis = bas, bit
            bulgu.satir = satir_no(metin, bas)
            bulgu.kanit = metin[bas:bit]
            bulgu.durum = "dogrulandi"
            return bulgu

    bulgu.baslangic = bulgu.bitis = None
    bulgu.durum = "dogrulanamadi"
    return bulgu


def tum_gecisler(metin: str, deger: str) -> list[tuple[int, int]]:
    """Bir değerin belgedeki TÜM geçişleri (boşluk esnek, harf duyarsız).

    Maskeleme bunu kullanır: model bir adı tek konumla döndürse bile adın
    geçtiği her yer maskelenmeli, yoksa çıktıda sızıntı kalır.
    """
    d = _desen(tr_kucuk(deger), satir_ici=False)
    if d is None:
        return []
    return [(m.start(), m.end()) for m in d.finditer(tr_kucuk(metin))]
