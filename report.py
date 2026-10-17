"""Değişiklik raporu üretimi — docs/api-contract.md §4.

`olustur()` birleşik bulgu listesinden (docs/api-contract.md §2 şeması) JSON
Rapor nesnesini üretir; `markdown()` bu JSON'dan okunabilir bir Markdown
raporu türetir (GET /indir?tip=rapor için). İki format da TEK kaynaktan
(JSON'dan) üretilir — ayrı ayrı hesaplanmaz, böylece ikisi asla birbirinden
sapmaz.

KRİTİK KURAL: Hiçbir fonksiyon `kanit` (gerçek değer) alanını rapora yazmaz.
Reddedilen ya da doğrulanamayan bir bulgu bile potansiyel olarak hassas bir
değer taşıyabilir; yalnızca kategori, konum.satir ve risk (seviye etiketi,
gerçek değer değil) tutulur.

pipeline'dan bağımsızdır (eval/metrics.py gibi): girdi sade sözlük listesi.
"""

from collections import Counter
from typing import Optional, Sequence


def _konum_ozet(bulgu: dict) -> Optional[dict]:
    konum = bulgu.get("konum")
    if not konum:
        return None
    return {"satir": konum.get("satir")}


def olustur(bulgular: Sequence[dict], sizinti_sayisi: int = 0) -> dict:
    """docs/api-contract.md §4'teki Rapor JSON'unu üretir.

    `sizinti_sayisi`: Dilara'nın sizinti_kontrol'ünün bulduğu, kabul edilip
    maskelendiği halde maskeli metinde hâlâ geçen değer SAYISI — gerçek
    değerlerin kendisi asla buraya girmez.
    """
    kabul_edilenler = [b for b in bulgular if b.get("karar") == "kabul"]
    kategori_sayi = Counter(b["kategori"] for b in kabul_edilenler)

    reddedilenler = [
        {"kategori": b["kategori"], "konum": _konum_ozet(b), "risk": b.get("risk")}
        for b in bulgular
        if b.get("karar") == "red"
    ]
    elle_eklenenler = [
        {"kategori": b["kategori"], "konum": _konum_ozet(b)}
        for b in bulgular
        if b.get("kaynak") == "elle"
    ]
    dogrulanamayanlar = [
        {
            "kategori": b["kategori"],
            "konum": _konum_ozet(b),
            "risk": b.get("risk"),
            "not": "elle kontrol edilmeli",
        }
        for b in bulgular
        if b.get("durum") == "dogrulanamadi"
    ]

    return {
        "ozet": {
            "kategori_basina_sayi": dict(kategori_sayi),
            "toplam_maskelenen": len(kabul_edilenler),
        },
        "reddedilenler": reddedilenler,
        "elle_eklenenler": elle_eklenenler,
        "dogrulanamayanlar": dogrulanamayanlar,
        "sizinti": {"bulundu": sizinti_sayisi > 0, "sayi": sizinti_sayisi},
    }


def markdown(rapor: dict, model: str = "", sure_sn: Optional[float] = None) -> str:
    """`olustur()`'un döndürdüğü JSON'dan okunabilir bir Markdown raporu üretir.

    Biçim Dilara'nın engine/pseudonymize.py'deki rapor() sunumundan esinlendi
    (bkz. docs/rakip-analizi-ve-reuse.md) — burada JSON'dan türetilir ki iki
    format da aynı sayıları göstersin.
    """
    satirlar = ["# Sessiz Kalem — Maskeleme Raporu", ""]
    if model:
        satirlar.append(f"- Analiz: kural katmanı + yerel {model}")
    else:
        satirlar.append("- Analiz: kural katmanı")
    if sure_sn is not None:
        satirlar.append(f"- Süre: {sure_sn:.1f} sn")

    sizinti = rapor["sizinti"]
    sizinti_satiri = (
        "✅ kabul edilen değerlerin hiçbiri çıktıda yok"
        if not sizinti["bulundu"]
        else f"❌ {sizinti['sayi']} değer çıktıda kaldı"
    )
    satirlar += [f"- Sızıntı kontrolü: {sizinti_satiri}", ""]

    kategoriler = sorted(
        set(rapor["ozet"]["kategori_basina_sayi"])
        | {r["kategori"] for r in rapor["reddedilenler"]}
        | {r["kategori"] for r in rapor["dogrulanamayanlar"]}
        | {r["kategori"] for r in rapor["elle_eklenenler"]}
    )
    satirlar += [
        "| Kategori | Kabul | Red | Elle eklenen | Doğrulanamadı |",
        "|---|---|---|---|---|",
    ]
    for kat in kategoriler:
        kabul = rapor["ozet"]["kategori_basina_sayi"].get(kat, 0)
        red = sum(1 for r in rapor["reddedilenler"] if r["kategori"] == kat)
        elle = sum(1 for r in rapor["elle_eklenenler"] if r["kategori"] == kat)
        dogrulanamadi = sum(1 for r in rapor["dogrulanamayanlar"] if r["kategori"] == kat)
        satirlar.append(f"| {kat} | {kabul} | {red} | {elle} | {dogrulanamadi} |")

    elle_kontrol = len(rapor["dogrulanamayanlar"]) + sum(
        1 for r in rapor["reddedilenler"] if r.get("risk") == "yuksek"
    )
    if elle_kontrol:
        satirlar += [
            "",
            f"**Elle kontrol edilmeli:** {elle_kontrol} bulgu "
            "(doğrulanamayan veya reddedilen yüksek riskli).",
        ]

    satirlar += [
        "",
        "> Maskeleme belgeyi tek başına anonim yapmaz; kalan bağlam kişiyi ele verebilir.",
        "> Hukuki danışmanlık değildir.",
    ]
    return "\n".join(satirlar)
