from pseudonymize import etiketle, maskele_metin


def _bulgu(id_, kategori, kanit, baslangic, bitis, karar="kabul"):
    return {
        "id": id_,
        "kategori": kategori,
        "kanit": kanit,
        "konum": {"satir": 1, "baslangic": baslangic, "bitis": bitis},
        "karar": karar,
    }


def test_tekrarlanan_deger_ayni_etiketi_alir():
    metin = "Proje Kartal başladı. Proje Kartal devam ediyor."
    bulgular = [
        _bulgu("f1", "kod_adi", "Proje Kartal", 0, 12),
        _bulgu("f2", "kod_adi", "Proje Kartal", 22, 34),
    ]
    etiketler = etiketle(bulgular)
    assert etiketler["f1"] == etiketler["f2"] == "KOD_ADI_1"


def test_farkli_kategoriler_ayri_sayilir():
    bulgular = [
        _bulgu("f1", "kod_adi", "Proje Kartal", 0, 12),
        _bulgu("f2", "teklif_bedeli", "850.000 TL", 20, 30),
    ]
    etiketler = etiketle(bulgular)
    assert etiketler["f1"] == "KOD_ADI_1"
    assert etiketler["f2"] == "TEKLIF_BEDELI_1"


def test_reddedilen_bulgu_etiket_almaz():
    bulgular = [_bulgu("f1", "kod_adi", "Proje Kartal", 0, 12, karar="red")]
    assert etiketle(bulgular) == {}


def test_offset_kaymasi_olmadan_maskeleme():
    # Etiket orijinal değerden daha uzun ("850.000 TL" = 10, "[TEKLIF_BEDELI_1]" = 18)
    metin = "Toplam bedel 850.000 TL olarak belirlenmiştir."
    baslangic = metin.index("850.000 TL")
    bitis = baslangic + len("850.000 TL")
    bulgular = [_bulgu("f1", "teklif_bedeli", "850.000 TL", baslangic, bitis)]

    sonuc = maskele_metin(metin, bulgular)

    assert sonuc == "Toplam bedel [TEKLIF_BEDELI_1] olarak belirlenmiştir."


def test_birden_fazla_bulgu_dogru_sirayla_maskelenir():
    metin = "Ada Yılmaz, IBAN TR33 0006 1005 1978 6457 8413 26 numaralı hesaba öder."
    ad_b, ad_e = metin.index("Ada Yılmaz"), metin.index("Ada Yılmaz") + len("Ada Yılmaz")
    iban_deger = "TR33 0006 1005 1978 6457 8413 26"
    iban_b, iban_e = metin.index(iban_deger), metin.index(iban_deger) + len(iban_deger)
    bulgular = [
        _bulgu("f1", "musteri_bilgisi", "Ada Yılmaz", ad_b, ad_e),
        _bulgu("f2", "iban", iban_deger, iban_b, iban_e),
    ]

    sonuc = maskele_metin(metin, bulgular)

    assert sonuc == "[MUSTERI_BILGISI_1], IBAN [IBAN_1] numaralı hesaba öder."


def test_karari_beklemede_olan_bulgu_maskelenmez():
    metin = "Proje Kartal devam ediyor."
    bulgular = [_bulgu("f1", "kod_adi", "Proje Kartal", 0, 12, karar="beklemede")]
    assert maskele_metin(metin, bulgular) == metin


def test_konumu_olmayan_bulgu_atlanir():
    bulgular = [{"id": "f1", "kategori": "kod_adi", "kanit": "x", "karar": "kabul", "konum": None}]
    assert maskele_metin("değişmeyen metin", bulgular) == "değişmeyen metin"
