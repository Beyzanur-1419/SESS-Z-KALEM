from pathlib import Path

from eval import csv_io
from eval.metrics import Beklenen, degerlendir

FIXTURE_CSV = Path(__file__).resolve().parents[1] / "fixtures" / "ornek_sozlesme_01_beklenen.csv"


def test_csv_okunuyor():
    beklenenler = csv_io.oku(FIXTURE_CSV)
    assert len(beklenenler) == 8
    assert beklenenler[0] == Beklenen(kategori="kod_adi", kanit="Proje Kartal", risk="yuksek")


def test_tam_eslesme():
    beklenenler = [Beklenen(kategori="tc_kimlik", kanit="10000000146")]
    bulgular = [{"kategori": "tc_kimlik", "kanit": "10000000146", "durum": "dogrulandi"}]
    sonuc = degerlendir(bulgular, beklenenler)
    assert sonuc.yakalama_orani == 1.0
    assert sonuc.yanlis_alarm == 0
    assert sonuc.kacirilanlar == []


def test_kacirilan_bulgu():
    beklenenler = [
        Beklenen(kategori="kod_adi", kanit="Proje Kartal"),
        Beklenen(kategori="tc_kimlik", kanit="10000000146"),
    ]
    bulgular = [{"kategori": "kod_adi", "kanit": "Proje Kartal", "durum": "dogrulandi"}]
    sonuc = degerlendir(bulgular, beklenenler)
    assert sonuc.yakalama_orani == 0.5
    assert sonuc.kacirilanlar == [("tc_kimlik", "10000000146")]


def test_yanlis_alarm():
    beklenenler = [Beklenen(kategori="kod_adi", kanit="Proje Kartal")]
    bulgular = [
        {"kategori": "kod_adi", "kanit": "Proje Kartal", "durum": "dogrulandi"},
        {"kategori": "diger", "kanit": "uydurma bulgu", "durum": "dogrulandi"},
    ]
    sonuc = degerlendir(bulgular, beklenenler)
    assert sonuc.yakalama_orani == 1.0
    assert sonuc.yanlis_alarm == 1


def test_elenen_bulgu_sayilir_ama_yakalamaya_girmez():
    beklenenler = [Beklenen(kategori="kod_adi", kanit="Proje Kartal")]
    bulgular = [
        {"kategori": "kod_adi", "kanit": "Proje Kartal", "durum": "dogrulanamadi"},
    ]
    sonuc = degerlendir(bulgular, beklenenler)
    assert sonuc.yakalama_orani == 0.0
    assert sonuc.elenen_bulgu == 1


def test_normalize_edilmis_bosluk_eslesir():
    beklenenler = [Beklenen(kategori="iban", kanit="TR33 0006 1005 1978 6457 8413 26")]
    bulgular = [
        {"kategori": "iban", "kanit": "TR330006100519786457841326", "durum": "dogrulandi"},
    ]
    sonuc = degerlendir(bulgular, beklenenler)
    assert sonuc.yakalama_orani == 1.0
