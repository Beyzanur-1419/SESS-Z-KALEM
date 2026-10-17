from pathlib import Path

import pytest

from engine import chunking, llm, pipeline
from engine.pseudonymize import maskele, rapor, sizinti_kontrol, tekillestir
from engine.schema import Bulgu
from engine.verify import dogrula

FIXTURE = Path(__file__).resolve().parents[2] / "eval" / "fixtures" / "ornek_sozlesme_01.txt"
METIN = FIXTURE.read_text(encoding="utf-8")


# ---------- chunking ----------
def test_kisa_metin_tek_parca_ve_numarali():
    p = chunking.parcala("a\nb")
    assert len(p) == 1 and p[0].metin == "L001| a\nL002| b"


def test_uzun_metin_ortusen_parcalar_ve_satir_kaybi_yok():
    metin = "\n".join(f"satır {i} " + "x" * 80 for i in range(1, 101))
    parcalar = chunking.parcala(metin, boyut=1500, ortusme=200)
    assert len(parcalar) > 1
    assert parcalar[0].ilk_satir == 1 and parcalar[-1].son_satir == 100
    for a, b in zip(parcalar, parcalar[1:]):
        assert b.ilk_satir <= a.son_satir  # örtüşme var
    assert all(len(p.metin) < 1500 + 100 * 7 for p in parcalar)


def test_bos_metin():
    assert chunking.parcala("   ") == []


# ---------- verify (§3 kademeli arama) ----------
def _model(kanit, satir=None, kat="kod_adi"):
    return Bulgu(kaynak="model", kategori=kat, kanit=kanit, satir=satir)


def test_adim1_tam_eslesme_kesin_konum():
    b = dogrula(METIN, _model("Proje Kartal", 3))
    assert b.durum == "dogrulandi" and METIN[b.baslangic : b.bitis] == "Proje Kartal"


def test_adim1_bosluk_esnek():
    b = dogrula(METIN, _model("850.000   TL", kat="teklif_bedeli"))
    assert b.durum == "dogrulandi" and b.kanit == "850.000 TL"


def test_adim2_satir_sonuna_bolunmus():
    metin = "gizli Proje\nKartal kapsamında"
    b = dogrula(metin, _model("Proje Kartal"))
    assert b.durum == "dogrulandi" and b.kanit == "Proje\nKartal"


def test_adim3_harf_duyarsiz_turkce():
    metin = "İSTANBUL ŞUBESİ IRMAK"
    b = dogrula(metin, _model("istanbul şubesi ırmak"))
    assert b.durum == "dogrulandi" and b.kanit == "İSTANBUL ŞUBESİ IRMAK"


def test_adim4_turkce_ek_onarimi():
    b = dogrula(METIN, _model("Ada Yılmaz'ın", kat="musteri_bilgisi"))
    assert b.durum == "dogrulandi" and b.kanit == "Ada Yılmaz"


def test_satir_ipucuna_en_yakin_gecis_secilir():
    metin = "Kartal\nx\nx\nx\nKartal"
    b = dogrula(metin, _model("Kartal", satir=5))
    assert b.satir == 5


def test_bulunamayan_silinmez_dogrulanamadi_olur():
    b = dogrula(METIN, _model("Hayali Kişi", kat="musteri_bilgisi"))
    assert b.durum == "dogrulanamadi" and b.to_dict()["konum"] is None


# ---------- kural katmanı ----------
def test_kural_katmani_fixture():
    kats = {b.kategori for b in pipeline.kural_bulgulari(METIN)}
    assert {"tc_kimlik", "iban", "plaka", "telefon"} <= kats


# ---------- maskeleme ----------
def _hepsini_kabul(bulgular):
    for b in bulgular:
        b.karar = "kabul"
    return bulgular


def test_ayni_deger_ayni_etiket_tum_gecisler_maskelenir():
    metin = "Ada Yılmaz geldi. Ada Yılmaz'ın dosyası. Can Demir de geldi."
    b1 = dogrula(metin, _model("Ada Yılmaz", kat="musteri_bilgisi"))
    b2 = dogrula(metin, _model("Can Demir", kat="musteri_bilgisi"))
    maskeli, esleme = maskele(metin, _hepsini_kabul([b1, b2]))
    assert maskeli == "[MUSTERI_1] geldi. [MUSTERI_1]'ın dosyası. [MUSTERI_2] de geldi."
    assert esleme == {"MUSTERI_1": "Ada Yılmaz", "MUSTERI_2": "Can Demir"}
    assert sizinti_kontrol(maskeli, [b1, b2]) == []


def test_reddedilen_maskelenmez():
    b = dogrula(METIN, _model("Proje Kartal"))
    b.karar = "red"
    maskeli, _ = maskele(METIN, [b])
    assert "Proje Kartal" in maskeli


def test_tekillestirme_en_uzun_kalir():
    a = Bulgu(kaynak="model", kategori="musteri_bilgisi", kanit="Ada Yılmaz Danışmanlık", baslangic=0, bitis=22)
    b = Bulgu(kaynak="model", kategori="musteri_bilgisi", kanit="Ada Yılmaz", baslangic=0, bitis=10)
    assert tekillestir([b, a]) == [a]


def test_rapor_degerleri_icermez():
    bulgular = _hepsini_kabul(pipeline.kural_bulgulari(METIN))
    maskeli, _ = maskele(METIN, bulgular)
    r = rapor(bulgular, sizinti_kontrol(maskeli, bulgular))
    assert all(b.kanit not in r for b in bulgular)


# ---------- uçtan uca, sahte model ile (ağ yok) ----------
def test_uctan_uca_sahte_model(monkeypatch):
    sahte = [
        {"kategori": "kod_adi", "kanit": "Proje Kartal", "satir": 3, "neden": "kod adı", "risk": "yuksek", "guven": 0.9},
        {"kategori": "musteri_bilgisi", "kanit": "Ada Yılmaz Danışmanlık", "satir": 4, "neden": "müşteri", "risk": "orta", "guven": 0.9},
        {"kategori": "teklif_bedeli", "kanit": "850.000 TL", "satir": 11, "neden": "bedel", "risk": "yuksek", "guven": 0.9},
        {"kategori": "musteri_bilgisi", "kanit": "Uydurma Şirket", "satir": 2, "neden": "x", "risk": "orta", "guven": 0.3},
    ]
    monkeypatch.setattr(llm, "hazir_mi", lambda *a, **k: (True, "sahte"))
    monkeypatch.setattr(llm, "parca_tara", lambda *a, **k: sahte)
    sonuc = pipeline.analiz_et(METIN)
    d = sonuc.to_dict()
    assert sonuc.model_kullanildi and d["dogrulanamadi"] == 1
    for b in sonuc.bulgular:
        if b.durum == "dogrulandi":
            b.karar = "kabul"
    maskeli, _ = maskele(METIN, sonuc.bulgular)
    assert "Proje Kartal" not in maskeli and "850.000 TL" not in maskeli
    assert sizinti_kontrol(maskeli, sonuc.bulgular) == []


# ---------- gizlilik ----------
@pytest.mark.parametrize("host", ["http://8.8.8.8:11434", "https://ollama.com"])
def test_uzak_model_reddedilir(host):
    with pytest.raises(llm.YerelDegilHatasi):
        llm.yerel_mi(host)


def test_yerel_kabul():
    llm.yerel_mi("http://127.0.0.1:11434")
    llm.yerel_mi("http://localhost:11434")
