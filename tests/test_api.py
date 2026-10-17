"""docs/api-contract.md §2 ve §4 sözleşmesine uygun API uç noktası testleri."""

import io
import pytest
from fastapi.testclient import TestClient

from main import app, BELGELER, BULGU_INDEX


@pytest.fixture
def client():
    # Testler arası state temizliği
    BELGELER.clear()
    BULGU_INDEX.clear()
    return TestClient(app)


def test_belge_yukleme_ve_bulgu_semasi(client):
    """POST /belgeler: mock bulgu listesi döner ve şemaya birebir uyar."""
    ornek_icerik = "MADDE 4.2 - Danışman Ayşe Yılmaz, Atlas Projesi için 450.000 TL alacaktır."
    dosya = io.BytesIO(ornek_icerik.encode("utf-8"))

    res = client.post(
        "/belgeler",
        files={"dosya": ("sozlesme.txt", dosya, "text/plain")}
    )

    assert res.status_code == 201
    veri = res.json()
    assert "belge_id" in veri
    assert "bulgular" in veri
    assert len(veri["bulgular"]) > 0

    # Bulgu şeması kontrolü (§2)
    bulgu = veri["bulgular"][0]
    zorunlu_alanlar = ["id", "kaynak", "kategori", "kanit", "konum", "neden", "risk", "guven", "durum", "karar", "etiket"]
    for alan in zorunlu_alanlar:
        assert alan in bulgu, f"Bulguda zorunlu alan eksik: {alan}"

    assert bulgu["kaynak"] in ["kural", "model", "elle"]
    assert bulgu["risk"] in ["yuksek", "orta", "dusuk"]
    assert bulgu["durum"] in ["dogrulandi", "dogrulanamadi"]
    assert bulgu["karar"] in ["beklemede", "kabul", "red"]


def test_desteklenmeyen_dosya_tipi_400(client):
    """Desteklenmeyen dosya uzantısında 400 dönmeli."""
    dosya = io.BytesIO(b"zararli kod")
    res = client.post(
        "/belgeler",
        files={"dosya": ("zararli.exe", dosya, "application/octet-stream")}
    )
    assert res.status_code == 400
    assert "desteklenmeyen_dosya_tipi" in res.json()["detail"]["hata"]


def test_bos_belge_400(client):
    """Boş belgede 400 dönmeli."""
    dosya = io.BytesIO(b"")
    res = client.post(
        "/belgeler",
        files={"dosya": ("bos.txt", dosya, "text/plain")}
    )
    assert res.status_code == 400
    assert "bos_belge" in res.json()["detail"]["hata"]


def test_model_erisilemez_503(client):
    """Ollama/model çevrimdışıyken 503 ve {hata: 'model_erisilemez'} dönmeli."""
    client.post("/simulasyon/model-durumu?cevrildisi=true")
    try:
        dosya = io.BytesIO(b"test icerik")
        res = client.post(
            "/belgeler",
            files={"dosya": ("test.txt", dosya, "text/plain")}
        )
        assert res.status_code == 503
        assert res.json()["detail"]["hata"] == "model_erisilemez"
    finally:
        client.post("/simulasyon/model-durumu?cevrildisi=false")


def test_bulgu_karar_guncelleme(client):
    """POST /bulgular/{id}/karar: kabul ve red durumları güncellenir."""
    # Önce belge yükle
    dosya = io.BytesIO(b"Metin icerigi")
    res = client.post("/belgeler", files={"dosya": ("test.txt", dosya, "text/plain")})
    bulgular = res.json()["bulgular"]
    bulgu_id = bulgular[0]["id"]

    # Kabul et
    res_kabul = client.post(f"/bulgular/{bulgu_id}/karar", json={"karar": "kabul"})
    assert res_kabul.status_code == 200
    assert res_kabul.json()["karar"] == "kabul"

    # Reddet
    res_red = client.post(f"/bulgular/{bulgu_id}/karar", json={"karar": "red"})
    assert res_red.status_code == 200
    assert res_red.json()["karar"] == "red"


def test_elle_bulgu_ekleme(client):
    """POST /belgeler/{belge_id}/bulgular: yeni elle eklenen bulgu döner."""
    dosya = io.BytesIO(b"Metin icerigi")
    res = client.post("/belgeler", files={"dosya": ("test.txt", dosya, "text/plain")})
    belge_id = res.json()["belge_id"]

    yeni_girdi = {
        "kategori": "ozel_anlasma",
        "kanit": "özel protokol",
        "konum": {"satir": 5, "baslangic": 10, "bitis": 23},
        "neden": "Kullanıcı özel ticari sır olarak ekledi",
        "risk": "yuksek"
    }

    res_elle = client.post(f"/belgeler/{belge_id}/bulgular", json=yeni_girdi)
    assert res_elle.status_code == 201
    yeni_bulgu = res_elle.json()
    assert yeni_bulgu["kaynak"] == "elle"
    assert yeni_bulgu["durum"] == "dogrulandi"
    assert yeni_bulgu["kanit"] == "özel protokol"
    assert yeni_bulgu["kategori"] == "ozel_anlasma"


def test_maskeleme_ve_rapor_semasi(client):
    """POST /belgeler/{belge_id}/maskele: temiz metin ve kanıt içermeyen rapor döner."""
    metin = "Ayşe Yılmaz, Atlas Projesi kapsamında çalışacaktır."
    dosya = io.BytesIO(metin.encode("utf-8"))
    res = client.post("/belgeler", files={"dosya": ("test.txt", dosya, "text/plain")})
    belge_id = res.json()["belge_id"]
    bulgular = res.json()["bulgular"]

    # Birinciyi kabul et, ikinciyi reddet
    if len(bulgular) >= 2:
        client.post(f"/bulgular/{bulgular[0]['id']}/karar", json={"karar": "kabul"})
        client.post(f"/bulgular/{bulgular[1]['id']}/karar", json={"karar": "red"})

    res_maskele = client.post(f"/belgeler/{belge_id}/maskele")
    assert res_maskele.status_code == 200
    cikti = res_maskele.json()
    assert "temiz_metin" in cikti
    assert "rapor" in cikti

    rapor = cikti["rapor"]
    # Rapor şema kontrolleri (§4)
    assert "ozet" in rapor
    assert "toplam_maskelenen" in rapor["ozet"]
    assert "kategori_basina_sayi" in rapor["ozet"]
    assert "reddedilenler" in rapor
    assert "elle_eklenenler" in rapor
    assert "dogrulanamayanlar" in rapor

    # GİZLİLİK KONTROLÜ: Kanıt metni raporda KESİNLİKLE yer almamalı!
    rapor_str = str(rapor)
    assert "Ayşe Yılmaz" not in rapor_str
    assert "Atlas Projesi" not in rapor_str


def test_belge_indir_txt_ve_rapor(client):
    """GET /belgeler/{belge_id}/indir?tip=txt|rapor."""
    dosya = io.BytesIO(b"Test metin")
    res = client.post("/belgeler", files={"dosya": ("test.txt", dosya, "text/plain")})
    belge_id = res.json()["belge_id"]

    # TXT indir
    res_txt = client.get(f"/belgeler/{belge_id}/indir?tip=txt")
    assert res_txt.status_code == 200
    assert "attachment" in res_txt.headers.get("content-disposition", "")

    # Rapor indir
    res_rapor = client.get(f"/belgeler/{belge_id}/indir?tip=rapor")
    assert res_rapor.status_code == 200
    assert "attachment" in res_rapor.headers.get("content-disposition", "")
