"""Tekilleştirme, tutarlı etiketleme, maskeleme, sızıntı kontrolü ve rapor.

Etiket kararı (docs/gorev-dagilimi.md açık karar #2): AYNI değer belgenin her
yerinde AYNI etiketi alır ([MUSTERI_1] her geçişte), farklı değerler numaralanır.

Maskeleme, kabul edilen her değerin belgedeki TÜM geçişlerini kapatır (model
tek konum döndürse bile). Ardından `sizinti_kontrol` çıktıda kabul edilen hiçbir
değerin kalmadığını doğrular; kalırsa arayüz indirmeyi kapatmalı.

Eşleme tablosu ({etiket: değer}) yalnızca bellekte döner; diske yazılmaz.
"""
from __future__ import annotations

from collections import Counter

from .schema import ETIKET_ONEKI, Bulgu
from .verify import tr_kucuk, tum_gecisler


def _norm(s: str) -> str:
    return " ".join(tr_kucuk(s).split())


def tekillestir(bulgular: list[Bulgu]) -> list[Bulgu]:
    """§2: konumlu bulgularda çakışan aralıklardan EN UZUN olan kalır;
    konumsuzlarda (kategori, normalize kanıt) anahtarı tekildir."""
    konumlu = sorted(
        (b for b in bulgular if b.konumlu),
        key=lambda b: (-(b.bitis - b.baslangic), b.baslangic),
    )
    kalan: list[Bulgu] = []
    for b in konumlu:
        if any(b.baslangic < k.bitis and k.baslangic < b.bitis for k in kalan):
            continue
        kalan.append(b)
    goruldu = set()
    konumsuz = []
    for b in bulgular:
        if b.konumlu:
            continue
        anahtar = (b.kategori, _norm(b.kanit))
        if anahtar not in goruldu:
            goruldu.add(anahtar)
            konumsuz.append(b)
    return sorted(kalan, key=lambda b: b.baslangic) + konumsuz


def maskele(metin: str, bulgular: list[Bulgu]) -> tuple[str, dict[str, str]]:
    """Kabul edilen bulguları etiketle değiştirir. Döner: (maskeli metin, {etiket: değer})."""
    kabul = [b for b in bulgular if b.karar == "kabul" and b.kanit.strip()]

    # 1) Etiket ata: belgedeki ilk görünme sırasına göre, kategori içinde numara
    sira = sorted(kabul, key=lambda b: b.baslangic if b.konumlu else len(metin))
    etiket_of: dict[tuple[str, str], str] = {}
    sayac: Counter = Counter()
    for b in sira:
        onek = ETIKET_ONEKI[b.kategori]
        anahtar = (onek, _norm(b.kanit))
        if anahtar not in etiket_of:
            sayac[onek] += 1
            etiket_of[anahtar] = f"{onek}_{sayac[onek]}"
        b.etiket = etiket_of[anahtar]

    # 2) Her kabul edilen değerin TÜM geçişlerini topla
    araliklar: list[tuple[int, int, str]] = []
    for b in kabul:
        gecisler = tum_gecisler(metin, b.kanit)
        if b.konumlu and (b.baslangic, b.bitis) not in gecisler:
            gecisler.append((b.baslangic, b.bitis))
        araliklar += [(s, e, b.etiket) for s, e in gecisler]

    # 3) Çakışmada uzun aralık kazanır, sonra soldan sağa değiştir
    araliklar.sort(key=lambda a: (-(a[1] - a[0]), a[0]))
    secilen: list[tuple[int, int, str]] = []
    for a in araliklar:
        if any(a[0] < s[1] and s[0] < a[1] for s in secilen):
            continue
        secilen.append(a)
    secilen.sort()
    parcalar, imlec = [], 0
    for s, e, etiket in secilen:
        parcalar += [metin[imlec:s], f"[{etiket}]"]
        imlec = e
    parcalar.append(metin[imlec:])

    esleme = {}
    for b in kabul:
        esleme.setdefault(b.etiket, b.kanit)
    return "".join(parcalar), esleme


def sizinti_kontrol(maskeli: str, bulgular: list[Bulgu]) -> list[str]:
    """Kabul edilip de maskeli metinde hâlâ geçen değerler. BOŞ olmalı."""
    hedef = _norm(maskeli)
    return sorted(
        {b.kanit for b in bulgular if b.karar == "kabul" and b.kanit.strip() and _norm(b.kanit) in hedef}
    )


def rapor(bulgular: list[Bulgu], sizintilar: list[str], model: str = "", sure_sn: float | None = None) -> str:
    """Paylaşılabilir rapor. GERÇEK DEĞERLERİ İÇERMEZ (yalnızca kategori ve sayılar)."""
    satirlar = [
        "# Sessiz Kalem — Maskeleme Raporu",
        "",
        f"- Analiz: kural katmanı{' + yerel ' + model if model else ''}",
    ]
    if sure_sn is not None:
        satirlar.append(f"- Süre: {sure_sn:.1f} sn")
    satirlar += [
        f"- Sızıntı kontrolü: {'✅ kabul edilen değerlerin hiçbiri çıktıda yok' if not sizintilar else f'❌ {len(sizintilar)} değer çıktıda kaldı'}",
        "",
        "| Kategori | Kabul | Red | Beklemede | Doğrulanamadı |",
        "|---|---|---|---|---|",
    ]
    for kat in sorted({b.kategori for b in bulgular}):
        grup = [b for b in bulgular if b.kategori == kat]
        satirlar.append(
            f"| {kat} | {sum(b.karar == 'kabul' for b in grup)} | {sum(b.karar == 'red' for b in grup)} "
            f"| {sum(b.karar == 'beklemede' for b in grup)} | {sum(b.durum == 'dogrulanamadi' for b in grup)} |"
        )
    elle = [b for b in bulgular if b.durum == "dogrulanamadi" or (b.risk == "yuksek" and b.karar == "red")]
    if elle:
        satirlar += ["", f"**Elle kontrol edilmeli:** {len(elle)} bulgu (doğrulanamayan veya reddedilen yüksek riskli)."]
    satirlar += [
        "",
        "> Maskeleme belgeyi tek başına anonim yapmaz; kalan bağlam kişiyi ele verebilir.",
        "> Hukuki danışmanlık değildir.",
    ]
    return "\n".join(satirlar)
