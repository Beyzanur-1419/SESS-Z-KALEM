"""Sessiz Kalem - FastAPI Uygulaması ve Mock API Servisi.

docs/api-contract.md §2 ve §4 sözleşmesine birebir uyar.
Issue #5 ve #7 gereksinimlerini karşılar.
"""

from __future__ import annotations

import io
import json
import uuid
from typing import Any, Dict, List, Literal, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pseudonymize import etiketle, maskele_metin

app = FastAPI(
    title="Sessiz Kalem API",
    description="Hassas Bilgi Tespiti ve Belge Maskeleme API (docs/api-contract.md v1)",
    version="0.1.0",
)

# CORS yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Veri Modelleri (docs/api-contract.md §2 ve §4)
# ============================================================================

class Konum(BaseModel):
    satir: int
    baslangic: Optional[int] = None
    bitis: Optional[int] = None


class Bulgu(BaseModel):
    id: str
    kaynak: Literal["kural", "model", "elle"]
    kategori: str
    kanit: str
    konum: Optional[Konum] = None
    neden: str
    risk: Literal["yuksek", "orta", "dusuk"]
    guven: float
    durum: Literal["dogrulandi", "dogrulanamadi"]
    karar: Literal["beklemede", "kabul", "red"] = "beklemede"
    etiket: Optional[str] = None


class KararGirdisi(BaseModel):
    karar: Literal["kabul", "red"]


class ElleBulguGirdisi(BaseModel):
    kategori: str
    kanit: str
    konum: Optional[Konum] = None
    neden: Optional[str] = "Kullanıcı tarafından elle eklendi"
    risk: Optional[Literal["yuksek", "orta", "dusuk"]] = "orta"


class Ozet(BaseModel):
    kategori_basina_sayi: Dict[str, int]
    toplam_maskelenen: int


class RaporKonum(BaseModel):
    satir: Optional[int] = None


class Reddedilen(BaseModel):
    kategori: str
    konum: RaporKonum


class ElleEklenen(BaseModel):
    kategori: str
    konum: RaporKonum


class Dogrulanamayan(BaseModel):
    kategori: str
    konum: RaporKonum
    not_: str = Field(default="elle kontrol edilmeli", serialization_alias="not")


class Rapor(BaseModel):
    ozet: Ozet
    reddedilenler: List[Reddedilen]
    elle_eklenenler: List[ElleEklenen]
    dogrulanamayanlar: List[Dogrulanamayan]

    model_config = {
        "populate_by_name": True
    }


class MaskeleCiktisi(BaseModel):
    temiz_metin: str
    rapor: Rapor


# ============================================================================
# Bellek İçi Saklama (In-Memory Mock Depolama)
# ============================================================================

# Belge verisi: belge_id -> {"dosya_adi": str, "metin": str, "bulgular": List[dict], "temiz_metin": str, "rapor": dict}
BELGELER: Dict[str, Dict[str, Any]] = {}
# Global bulgu indexi: bulgu_id -> (belge_id, index)
BULGU_INDEX: Dict[str, tuple[str, int]] = {}

# Test / simülasyon bayrağı (Ollama çevrimdışı simülasyonu için)
MOCK_OLLAMA_OFFLINE = False


def _varsayilan_ornek_metin() -> str:
    return (
        "MADDE 4.2 - TARAFLAR VE TİCARİ YÜKÜMLÜLÜKLER\n\n"
        "İşbu sözleşme kapsamında danışman Ayşe Yılmaz, şirket bünyesinde gizli olarak yürütülen "
        "Atlas Projesi veri tabanı mimarisi üzerinde tam yetkiyle çalışacaktır.\n"
        "İlk faz tamamlanma bedeli olan 450.000 TL hak ediş, yüklenicinin QNB Finansbank nezdindeki "
        "TR44 0011 1000 0000 0456 7890 12 nolu hesabına en geç 5 iş günü içinde transfer edilecektir.\n"
        "Proje yöneticisi ile irtibat için dahili e-posta: ayse.yilmaz@sirket.internal adresi kullanılabilir.\n"
        "Gizli anlaşma şartı: Proje tesliminde belirtilen gizli protokol hükmü saklıdır."
    )


def _ornek_mock_bulgular(metin: str) -> List[dict]:
    """docs/api-contract.md §2'ye tam uyumlu mock bulgular üretir."""
    bulgular: List[dict] = []

    # 1. Kural tabanlı bulgu: IBAN
    iban_val = "TR44 0011 1000 0000 0456 7890 12"
    if iban_val in metin:
        b_idx = metin.index(iban_val)
        bulgular.append({
            "id": f"f-{uuid.uuid4().hex[:4]}",
            "kaynak": "kural",
            "kategori": "iban",
            "kanit": iban_val,
            "konum": {"satir": 4, "baslangic": b_idx, "bitis": b_idx + len(iban_val)},
            "neden": "Kural tabanlı TR IBAN sağlama kontrolü doğrulandı.",
            "risk": "yuksek",
            "guven": 0.99,
            "durum": "dogrulandi",
            "karar": "beklemede",
            "etiket": None,
        })

    # 2. Model bulgusu: Kişi Adı (Ayşe Yılmaz)
    kisi_val = "Ayşe Yılmaz"
    if kisi_val in metin:
        b_idx = metin.index(kisi_val)
        bulgular.append({
            "id": f"f-{uuid.uuid4().hex[:4]}",
            "kaynak": "model",
            "kategori": "musteri_bilgisi",
            "kanit": kisi_val,
            "konum": {"satir": 3, "baslangic": b_idx, "bitis": b_idx + len(kisi_val)},
            "neden": "Kişisel veri / sözleşme tarafı kimlik bilgisi.",
            "risk": "orta",
            "guven": 0.95,
            "durum": "dogrulandi",
            "karar": "beklemede",
            "etiket": None,
        })

    # 3. Model bulgusu: Kod Adı (Atlas Projesi)
    proje_val = "Atlas Projesi"
    if proje_val in metin:
        b_idx = metin.index(proje_val)
        bulgular.append({
            "id": f"f-{uuid.uuid4().hex[:4]}",
            "kaynak": "model",
            "kategori": "kod_adi",
            "kanit": proje_val,
            "konum": {"satir": 3, "baslangic": b_idx, "bitis": b_idx + len(proje_val)},
            "neden": "Şirket içi gizli ticari proje kod adı.",
            "risk": "yuksek",
            "guven": 0.92,
            "durum": "dogrulandi",
            "karar": "beklemede",
            "etiket": None,
        })

    # 4. Model bulgusu: Teklif Bedeli (450.000 TL)
    tutar_val = "450.000 TL"
    if tutar_val in metin:
        b_idx = metin.index(tutar_val)
        bulgular.append({
            "id": f"f-{uuid.uuid4().hex[:4]}",
            "kaynak": "model",
            "kategori": "teklif_bedeli",
            "kanit": tutar_val,
            "konum": {"satir": 4, "baslangic": b_idx, "bitis": b_idx + len(tutar_val)},
            "neden": "Hassas finansal sözleşme bedeli.",
            "risk": "orta",
            "guven": 0.90,
            "durum": "dogrulandi",
            "karar": "beklemede",
            "etiket": None,
        })

    # 5. Doğrulanamayan bulgu örneği (Issue #7 gereksinimi: "elle kontrol edilmeli" rozeti için)
    bulgular.append({
        "id": f"f-{uuid.uuid4().hex[:4]}",
        "kaynak": "model",
        "kategori": "ozel_anlasma",
        "kanit": "gizli protokol hükmü",
        "konum": None,
        "neden": "Model alıntıyı tespit etti fakat kesin satır/karakter konumu doğrulanamadı.",
        "risk": "orta",
        "guven": 0.65,
        "durum": "dogrulanamadi",
        "karar": "beklemede",
        "etiket": None,
    })

    return bulgular


# ============================================================================
# API Uç Noktaları (docs/api-contract.md §4)
# ============================================================================

@app.post("/belgeler", status_code=status.HTTP_201_CREATED)
async def belge_yukle(dosya: UploadFile = File(...)):
    """Dosya yükleme (pdf/docx/txt, multipart).

    Çıktı: { "belge_id": "...", "bulgular": [Bulgu, ...] }
    Hata durumu: desteklenmeyen dosya tipi veya boş belge -> 400 + { "hata": "..." }
    Model erişilemezse -> 503 + { "hata": "model_erisilemez" }
    """
    global MOCK_OLLAMA_OFFLINE
    if MOCK_OLLAMA_OFFLINE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"hata": "model_erisilemez"},
        )

    dosya_adi = dosya.filename or ""
    uzanti = dosya_adi.lower().split(".")[-1] if "." in dosya_adi else ""

    if uzanti not in ["txt", "pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"hata": "desteklenmeyen_dosya_tipi"},
        )

    icerik_bayt = await dosya.read()
    if len(icerik_bayt) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"hata": "bos_belge"},
        )

    # Issue #6 gelene kadar metin çıkarma mock / utf-8 decode
    if uzanti == "txt":
        try:
            metin = icerik_bayt.decode("utf-8")
        except UnicodeDecodeError:
            metin = icerik_bayt.decode("latin-1", errors="ignore")
    else:
        # PDF/DOCX için Melike'nin documents.py modülü bağlanana kadar örnek şablon metin
        metin = _varsayilan_ornek_metin()

    belge_id = f"doc-{uuid.uuid4().hex[:8]}"
    bulgular = _ornek_mock_bulgular(metin)

    # Kaydet
    BELGELER[belge_id] = {
        "dosya_adi": dosya_adi,
        "metin": metin,
        "bulgular": bulgular,
        "temiz_metin": None,
        "rapor": None,
    }

    # Bulgu indexini güncelle
    for idx, b in enumerate(bulgular):
        BULGU_INDEX[b["id"]] = (belge_id, idx)

    return {
        "belge_id": belge_id,
        "bulgular": bulgular,
    }


@app.post("/bulgular/{id}/karar")
async def bulgu_karar(id: str, girdi: KararGirdisi):
    """Bulgu için karar güncelleme (kabul | red).

    Çıktı: güncellenmiş Bulgu
    """
    if id not in BULGU_INDEX:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"hata": "bulgu_bulunamadi"},
        )

    belge_id, idx = BULGU_INDEX[id]
    bulgu = BELGELER[belge_id]["bulgular"][idx]
    bulgu["karar"] = girdi.karar

    return bulgu


@app.post("/belgeler/{belge_id}/bulgular", status_code=status.HTTP_201_CREATED)
async def elle_bulgu_ekle(belge_id: str, girdi: ElleBulguGirdisi):
    """Elle eklenen bulgu.

    Çıktı: yeni Bulgu (kaynak: 'elle', durum: 'dogrulandi')
    """
    if belge_id not in BELGELER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"hata": "belge_bulunamadi"},
        )

    belge = BELGELER[belge_id]
    yeni_id = f"f-{uuid.uuid4().hex[:4]}"

    konum_dict = None
    if girdi.konum is not None:
        konum_dict = girdi.konum.model_dump()
    else:
        # Metinde alıntıyı bulmaya çalışalım
        if girdi.kanit in belge["metin"]:
            baslangic = belge["metin"].index(girdi.kanit)
            bitis = baslangic + len(girdi.kanit)
            satir_no = belge["metin"][:baslangic].count("\n") + 1
            konum_dict = {"satir": satir_no, "baslangic": baslangic, "bitis": bitis}
        else:
            konum_dict = {"satir": 1, "baslangic": None, "bitis": None}

    yeni_bulgu = {
        "id": yeni_id,
        "kaynak": "elle",
        "kategori": girdi.kategori,
        "kanit": girdi.kanit,
        "konum": konum_dict,
        "neden": girdi.neden or "Kullanıcı tarafından elle eklendi",
        "risk": girdi.risk or "orta",
        "guven": 1.0,
        "durum": "dogrulandi",
        "karar": "beklemede",
        "etiket": None,
    }

    belge["bulgular"].append(yeni_bulgu)
    BULGU_INDEX[yeni_id] = (belge_id, len(belge["bulgular"]) - 1)

    return yeni_bulgu


@app.post("/belgeler/{belge_id}/maskele")
async def belge_maskele(belge_id: str):
    """Yalnızca karar: 'kabul' olan bulguları maskeler.

    Çıktı: { "temiz_metin": "...", "rapor": Rapor }
    Rapor gerçek kanıt değeri içermez (docs/api-contract.md §4).
    """
    if belge_id not in BELGELER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"hata": "belge_bulunamadi"},
        )

    belge = BELGELER[belge_id]
    bulgular = belge["bulgular"]
    metin = belge["metin"]

    # 1. Etiketleri ata ve metni maskele (pseudonymize.py ile)
    etiketler = etiketle(bulgular)
    for b in bulgular:
        if b["id"] in etiketler:
            b["etiket"] = etiketler[b["id"]]

    temiz_metin = maskele_metin(metin, bulgular)
    belge["temiz_metin"] = temiz_metin

    # 2. Rapor nesnesini oluştur
    # Özet sayımları
    kategori_sayilari: Dict[str, int] = {}
    toplam_maskelenen = 0
    reddedilenler: List[dict] = []
    elle_eklenenler: List[dict] = []
    dogrulanamayanlar: List[dict] = []

    for b in bulgular:
        satir_no = b["konum"]["satir"] if b.get("konum") and "satir" in b["konum"] else None

        if b.get("karar") == "kabul":
            toplam_maskelenen += 1
            kat = b["kategori"]
            kategori_sayilari[kat] = kategori_sayilari.get(kat, 0) + 1

        if b.get("karar") == "red":
            reddedilenler.append({
                "kategori": b["kategori"],
                "konum": {"satir": satir_no},
            })

        if b.get("kaynak") == "elle":
            elle_eklenenler.append({
                "kategori": b["kategori"],
                "konum": {"satir": satir_no},
            })

        if b.get("durum") == "dogrulanamadi":
            dogrulanamayanlar.append({
                "kategori": b["kategori"],
                "konum": {"satir": satir_no},
                "not": "elle kontrol edilmeli",
            })

    rapor = {
        "ozet": {
            "kategori_basina_sayi": kategori_sayilari,
            "toplam_maskelenen": toplam_maskelenen,
        },
        "reddedilenler": reddedilenler,
        "elle_eklenenler": elle_eklenenler,
        "dogrulanamayanlar": dogrulanamayanlar,
    }

    belge["rapor"] = rapor

    return {
        "temiz_metin": temiz_metin,
        "rapor": rapor,
    }


@app.get("/belgeler/{belge_id}/indir")
async def belge_indir(belge_id: str, tip: Literal["docx", "txt", "rapor"] = Query(...)):
    """Maskelenmiş belge veya rapor indirme."""
    if belge_id not in BELGELER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"hata": "belge_bulunamadi"},
        )

    belge = BELGELER[belge_id]
    temiz_metin = belge.get("temiz_metin") or belge["metin"]
    rapor = belge.get("rapor")

    if tip == "txt":
        icerik = temiz_metin.encode("utf-8")
        dosya_adi = f"maskelenmis_{belge['dosya_adi']}.txt"
        return Response(
            content=icerik,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{dosya_adi}"'},
        )

    elif tip == "rapor":
        if rapor is None:
            # Maskeleme henüz yapılmadıysa geçici rapor türet
            rapor = {
                "ozet": {"kategori_basina_sayi": {}, "toplam_maskelenen": 0},
                "reddedilenler": [],
                "elle_eklenenler": [],
                "dogrulanamayanlar": [],
            }
        rapor_json = json.dumps(rapor, ensure_ascii=False, indent=2).encode("utf-8")
        dosya_adi = f"denetim_raporu_{belge_id}.json"
        return Response(
            content=rapor_json,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{dosya_adi}"'},
        )

    elif tip == "docx":
        # python-docx ile basit docx oluştur
        try:
            import docx
            doc = docx.Document()
            doc.add_heading("Sessiz Kalem - Maskelenmiş Belge Çıktısı", level=1)
            for paragraf in temiz_metin.split("\n"):
                doc.add_paragraph(paragraf)
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            dosya_adi = f"maskelenmis_{belge['dosya_adi']}.docx"
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="{dosya_adi}"'},
            )
        except Exception:
            # Yedek: düz metin olarak stream et
            return Response(
                content=temiz_metin.encode("utf-8"),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="maskelenmis_{belge_id}.docx"'},
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"hata": "gecersiz_indirme_tipi"},
    )


# ============================================================================
# Simülasyon Yardımcı Uç Noktaları (Geliştirme / Test için)
# ============================================================================

@app.post("/simulasyon/model-durumu")
async def model_durumu_ayarla(cevrildisi: bool = Query(...)):
    """Ollama 503 simülasyonunu açıp kapamak için test yardımcısı."""
    global MOCK_OLLAMA_OFFLINE
    MOCK_OLLAMA_OFFLINE = cevrildisi
    return {"model_erisilebilir": not MOCK_OLLAMA_OFFLINE}


# ============================================================================
# Statik Dosyalar ve Web Arayüzü (web/ dizini)
# ============================================================================

import os

if os.path.isdir("web"):
    app.mount("/static", StaticFiles(directory="web"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_yolu = os.path.join("web", "index.html")
        if os.path.exists(index_yolu):
            with open(index_yolu, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h3>Sessiz Kalem Web Arayüzü Yükleniyor...</h3>")
