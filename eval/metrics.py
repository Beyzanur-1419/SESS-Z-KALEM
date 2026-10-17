"""Ölçüm betiği: `docs/api-contract.md`'deki birleşik bulgu listesini bilinen
(CSV) gizli bilgi listesiyle karşılaştırıp sunum tablosundaki metrikleri üretir.

Bu modül, tespit motorundan (Dilara) ve arayüzden (Beyza) bağımsız çalışır:
girdi olarak sade Python sözlükleri (bulgu listesi) alır, pipeline'a bağımlı
değildir. Pipeline hazır olduğunda gerçek çıktısı buraya verilir.
"""

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Beklenen:
    """Bir sentetik belgede bilinen, bulunması gereken gizli bilgi."""

    kategori: str
    kanit: str
    risk: str = "orta"


@dataclass(frozen=True)
class Sonuc:
    yakalama_orani: float
    yanlis_alarm: int
    elenen_bulgu: int
    kacirilanlar: list
    toplam_beklenen: int
    toplam_bulunan: int


def _anahtar(kategori: str, kanit: str) -> tuple:
    """Eşleştirme anahtarı: kategori + normalize edilmiş kanıt metni.

    Tam birebir eşleşme yerine normalize edilmiş karşılaştırma kullanılır
    (tüm boşluklar atılır, küçük harfe çevrilir), çünkü model ya da kural
    katmanı aynı değeri farklı boşluklamayla döndürebilir (örn. IBAN'ın
    boşluklu/boşluksuz hali).
    """
    return (kategori, "".join(kanit.split()).lower())


def degerlendir(
    bulgular: Sequence[dict],
    beklenenler: Iterable[Beklenen],
) -> Sonuc:
    """`bulgular`: docs/api-contract.md §2'deki birleşik bulgu nesneleri (dict).

    Yalnızca `karar: "kabul"` olan ya da henüz karar verilmemiş ama
    `durum: "dogrulandi"` olan bulgular "bulunan" sayılır; `durum:
    "dogrulanamadi"` olanlar yakalama oranına dahil edilmez ama elenen
    bulgu sayısına girer (kanıt doğrulamasının ne kadar iş yaptığını gösterir).
    """
    beklenenler = list(beklenenler)
    beklenen_anahtarlar = {_anahtar(b.kategori, b.kanit) for b in beklenenler}

    dogrulanan = [b for b in bulgular if b.get("durum") == "dogrulandi"]
    elenen = [b for b in bulgular if b.get("durum") == "dogrulanamadi"]
    bulunan_anahtarlar = {_anahtar(b["kategori"], b["kanit"]) for b in dogrulanan}

    dogru_bulunan = beklenen_anahtarlar & bulunan_anahtarlar
    yanlis_alarm = bulunan_anahtarlar - beklenen_anahtarlar
    kacirilan = beklenen_anahtarlar - bulunan_anahtarlar

    toplam_beklenen = len(beklenen_anahtarlar)
    oran = (len(dogru_bulunan) / toplam_beklenen) if toplam_beklenen else 0.0

    return Sonuc(
        yakalama_orani=round(oran, 3),
        yanlis_alarm=len(yanlis_alarm),
        elenen_bulgu=len(elenen),
        kacirilanlar=sorted(kacirilan),
        toplam_beklenen=toplam_beklenen,
        toplam_bulunan=len(bulunan_anahtarlar),
    )
