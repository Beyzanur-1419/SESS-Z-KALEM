"""Onaylanan bulgulara tutarlı etiket atar ve düz metni maskeler.

Yalnızca düz metin (.txt) çıktısını kapsar — .docx çıktısı biçimlendirmeyi
korumak için farklı bir yaklaşım gerektirir (bkz. docs/maskeleme-notu.md §3),
bu dosya o kısmı KAPSAMAZ. Bu, Dilara'nın (tespit motoru) pseudonymize.py
sorumluluğu için başlangıç noktasıdır (bkz. docs/gorev-dagilimi.md).

Beklenen girdi: docs/api-contract.md §2'deki birleşik bulgu nesneleri (dict),
`konum.baslangic`/`konum.bitis` alanları `metin` üzerindeki MUTLAK karakter
aralığı olmalı (satır içi değil).
"""

from typing import Dict, Sequence


def _anahtar(kategori: str, kanit: str) -> tuple:
    """eval/metrics.py'deki ile aynı normalizasyon: boşluksuz, küçük harf."""
    return (kategori, "".join(kanit.split()).lower())


def etiketle(bulgular: Sequence[dict]) -> Dict[str, str]:
    """Kabul edilen bulgulara tutarlı etiket atar.

    Döner: bulgu id'si -> etiket (örn. "KOD_ADI_1"). Aynı (kategori,
    normalize edilmiş kanıt) ikilisi — belgede kaç yerde geçerse geçsin —
    her zaman aynı etiketi alır.
    """
    sayac: Dict[str, int] = {}
    anahtar_to_etiket: Dict[tuple, str] = {}
    id_to_etiket: Dict[str, str] = {}
    for b in bulgular:
        if b.get("karar") != "kabul":
            continue
        anahtar = _anahtar(b["kategori"], b["kanit"])
        if anahtar not in anahtar_to_etiket:
            sayac[b["kategori"]] = sayac.get(b["kategori"], 0) + 1
            anahtar_to_etiket[anahtar] = f"{b['kategori'].upper()}_{sayac[b['kategori']]}"
        id_to_etiket[b["id"]] = anahtar_to_etiket[anahtar]
    return id_to_etiket


def maskele_metin(metin: str, bulgular: Sequence[dict]) -> str:
    """Kabul edilen bulguları `metin` içinde `[ETIKET]` ile değiştirir.

    Span'lar başlangıca göre artan sırada işlenir; yeni metin, aralardaki
    orijinal parçalarla etiketler ardışık birleştirilerek kurulur (yerinde
    değişiklik yok) — bu yüzden etiket uzunluğu orijinal değerden farklı
    olsa bile offset kayması oluşmaz (bkz. docs/maskeleme-notu.md §2).

    Çakışan/tekilleştirilmemiş span'lar (önceki span'ın imlecinden önce
    başlayan) sessizce atlanır — tekilleştirme docs/api-contract.md §2'ye
    göre bu fonksiyona gelmeden önce yapılmış olmalı.
    """
    etiketler = etiketle(bulgular)
    kabul_edilenler = sorted(
        (
            b for b in bulgular
            if b.get("karar") == "kabul" and b.get("konum")
        ),
        key=lambda b: b["konum"]["baslangic"],
    )

    parcalar = []
    imlec = 0
    for b in kabul_edilenler:
        baslangic = b["konum"]["baslangic"]
        bitis = b["konum"]["bitis"]
        if baslangic < imlec:
            continue
        parcalar.append(metin[imlec:baslangic])
        parcalar.append(f"[{etiketler[b['id']]}]")
        imlec = bitis
    parcalar.append(metin[imlec:])
    return "".join(parcalar)
