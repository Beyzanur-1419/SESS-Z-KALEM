from report import markdown, olustur


def _bulgu(kategori, karar="kabul", kaynak="kural", durum="dogrulandi",
           risk="orta", satir=1, kanit="gercek-deger-sizda-kalmali"):
    return {
        "kategori": kategori,
        "kanit": kanit,
        "konum": {"satir": satir},
        "risk": risk,
        "durum": durum,
        "karar": karar,
        "kaynak": kaynak,
    }


def test_kabul_edilenler_ozette_sayilir():
    bulgular = [
        _bulgu("kod_adi"),
        _bulgu("kod_adi"),
        _bulgu("iban"),
    ]
    rapor = olustur(bulgular)
    assert rapor["ozet"]["kategori_basina_sayi"] == {"kod_adi": 2, "iban": 1}
    assert rapor["ozet"]["toplam_maskelenen"] == 3


def test_kanit_hicbir_yerde_yok():
    bulgular = [
        _bulgu("kod_adi", karar="red", kanit="GIZLI_DEGER_1"),
        _bulgu("tc_kimlik", durum="dogrulanamadi", kanit="GIZLI_DEGER_2"),
        _bulgu("iban", kaynak="elle", kanit="GIZLI_DEGER_3"),
    ]
    rapor = olustur(bulgular)
    rapor_str = str(rapor)
    assert "GIZLI_DEGER_1" not in rapor_str
    assert "GIZLI_DEGER_2" not in rapor_str
    assert "GIZLI_DEGER_3" not in rapor_str


def test_reddedilen_kategori_ve_konum_ve_risk_tutulur():
    bulgular = [_bulgu("kod_adi", karar="red", risk="yuksek", satir=7)]
    rapor = olustur(bulgular)
    assert rapor["reddedilenler"] == [{"kategori": "kod_adi", "konum": {"satir": 7}, "risk": "yuksek"}]


def test_dogrulanamayan_not_icerir():
    bulgular = [_bulgu("teklif_bedeli", durum="dogrulanamadi", karar="beklemede")]
    rapor = olustur(bulgular)
    assert rapor["dogrulanamayanlar"][0]["not"] == "elle kontrol edilmeli"


def test_elle_eklenen_ayri_listelenir():
    bulgular = [_bulgu("plaka", kaynak="elle")]
    rapor = olustur(bulgular)
    assert len(rapor["elle_eklenenler"]) == 1
    assert rapor["elle_eklenenler"][0]["kategori"] == "plaka"


def test_sizinti_sayisi_gercek_deger_icermeden_tasinir():
    rapor = olustur([], sizinti_sayisi=2)
    assert rapor["sizinti"] == {"bulundu": True, "sayi": 2}


def test_sizinti_yoksa_bulundu_false():
    rapor = olustur([], sizinti_sayisi=0)
    assert rapor["sizinti"] == {"bulundu": False, "sayi": 0}


def test_markdown_kanit_icermez():
    bulgular = [
        _bulgu("kod_adi", kanit="SIZMAMALI_DEGER"),
        _bulgu("kod_adi", karar="red", kanit="SIZMAMALI_DEGER_2"),
    ]
    rapor = olustur(bulgular)
    md = markdown(rapor, model="gemma4:e4b", sure_sn=3.2)
    assert "SIZMAMALI_DEGER" not in md
    assert "SIZMAMALI_DEGER_2" not in md
    assert "gemma4:e4b" in md
    assert "kod_adi" in md


def test_markdown_sizinti_satiri_degisir():
    rapor_temiz = olustur([], sizinti_sayisi=0)
    rapor_sizinti = olustur([], sizinti_sayisi=1)
    assert "✅" in markdown(rapor_temiz)
    assert "❌" in markdown(rapor_sizinti)


def test_markdown_elle_kontrol_satiri():
    bulgular = [_bulgu("tc_kimlik", durum="dogrulanamadi", karar="beklemede")]
    rapor = olustur(bulgular)
    md = markdown(rapor)
    assert "Elle kontrol edilmeli" in md
