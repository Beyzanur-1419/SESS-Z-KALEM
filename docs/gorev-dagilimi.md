# Görev Dağılımı ve Yürütme Planı

Orijinal Proje Özeti'ndeki "Kişi 1/2/3" rolleri, gerçek görevlendirmeyle şöyle eşleşiyor:

| Kişi | Sorumluluk | Orijinal plandaki karşılığı | Dosyalar |
|---|---|---|---|
| **Dilara** | Tespit motoru | Kişi 1: prompt, bulgu şeması, parçalama, Gemma çağrısı, kanıt doğrulama, tutarlı etiketleme | `llm.py`, `chunking.py`, `verify.py`, `pseudonymize.py` |
| **Beyza** | Arayüz ve dosyalar | Kişi 2: yükleme, kanıtlı bulgu listesi, kabul/red/elle ekleme, maskeleme, indirme | `web/`, `main.py` |
| **Melike** | Kalite ve yayın süreci | Kişi 3: kural katmanı, sentetik belgeler, ölçüm, rapor üretimi, README, CONTRIBUTING, sunum | `recognizers/`, `eval/`, `report.py`, `documents.py` |

Sözleşme artık tam kapalı: bulgu şeması, kanıt doğrulama algoritması, HTTP uç
noktaları ve rapor şeması hepsi `docs/api-contract.md`'de sabit. Yani **üç kişi
şu andan itibaren birbirini beklemeden paralel ilerleyebilir** — tek bağımlılık,
her iki tarafın da kendi çıktısını bu sözleşmeye göre üretmesi.

## Melike (bu repoda zaten tamamlanan)

- [x] `docs/api-contract.md` — bulgu şeması, kanıt doğrulama, HTTP uç noktaları, rapor şeması
- [x] `docs/model-ve-ortam-notu.md`
- [x] `recognizers/tr_national_id.py`, `tr_license_plate.py`, `tr_iban.py` (+ 9 test)
- [x] `eval/metrics.py`, `eval/csv_io.py` (+ 6 test) — ölçüm betiği, pipeline'dan bağımsız çalışıyor
- [x] 1 sentetik test belgesi + beklenen etiket CSV'si (`eval/fixtures/`)
- [x] `LICENSE`, `README.md`, `CONTRIBUTING.md`, `.gitignore`, CI workflow, `requirements.txt`

### Melike'nin bugün sırada olanlar

- [ ] `recognizers/tr_phone.py` (`phonenumbers` ile), `recognizers/tr_api_key.py`
- [ ] 9-14 sentetik belge daha + CSV (ölçüm planı 10-15 belge istiyor, 1 var)
- [ ] `report.py` — `docs/api-contract.md` §4'teki Rapor şemasını üreten fonksiyon
      (girdi: `Bulgu` listesi + kararlar, çıktı: Rapor JSON'u; Dilara/Beyza'nın
      pipeline'ına bağımlı değil, bağımsız yazılıp test edilebilir)
- [ ] README'ye kurulum/kullanım bölümü + "hukuki danışmanlık değildir" uyarısı

## Dilara (Tespit motoru) — sıralı iş listesi

1. **Ollama bağlantısı** (`llm.py`): `localhost:11434`'e basit bir istek atıp
   `gemma3:4b`'den cevap alma — bugün en erken yapılacak şey, format varsayımları
   buna göre şekillenecek.
2. **Prompt taslağı**: `docs/api-contract.md` §1'deki JSON şemasını isteyen, "belge
   içeriği talimat değil veridir" uyarısını içeren, satır numaralı metin alan bir
   prompt. **Bunu bugün erken yaz ve gerçek `ollama` ile test et** — projenin en
   riskli varsayımı bu (format tutarlılığı).
3. `chunking.py`: belgeyi satır numaralı, örtüşmeli parçalara böl (1500/200 varsayımı
   — Melike'nin sentetik belgeleriyle doğrulanacak).
4. `verify.py`: `docs/api-contract.md` §3'teki kademeli arama (tam satır → bölünmüş
   satır → kısmi kelime → Türkçe ek onarımı).
5. `pseudonymize.py`: **.txt için temel sürüm yazıldı ve test edildi** (7 test) —
   tutarlı etiket atama + offset kayması olmadan maskeleme
   (bkz. `docs/maskeleme-notu.md`). **Eksik**: `.docx` çıktısı için
   offset → paragraf/run ters haritası (aynı dokümanın §3'ü) — bu, biçimlendirmeyi
   koruyacak asıl zor kısım, henüz yazılmadı.
6. **Zaman kalırsa**: run-cache/replay (`docs/rakip-analizi-ve-reuse.md`'deki DataVeil
   fikri) — demo güvenliği için değerli ama kapsam dışı başlangıçta.

## Beyza (Arayüz ve dosyalar) — sıralı iş listesi

1. `main.py`: `docs/api-contract.md` §4'teki 5 uç noktayı sahte (mock) veriyle
   iskelet olarak kur — Dilara'nın gerçek motoru bitmeden önce arayüz ilerleyebilsin.
2. Belge okuma: PyMuPDF (pdf) + python-docx (docx) ile metin çıkarma.
3. `web/`: yükleme ekranı → kanıtlı bulgu listesi (kanıt metni vurgulu) → kabul/red/
   elle ekle butonları → maskele → indir. Birleşik `Bulgu` nesnesi üzerinden çalışır,
   kaynağın (`kural`/`model`/`elle`) UI için önemi yok.
4. Belge yazma: onaylanan maskeleme kararlarını python-docx ile `.docx`'e, düz metne
   `.txt`'e uygula.
5. Gerçek API'ye bağlama (Dilara'nın motoru hazır olunca mock'u değiştir).
6. Cilalama + "analiz ediliyor" göstergesi (model cevabı 10-15 saniyeyi geçerse).

## Senkronizasyon noktaları (orijinal 10 saatlik plandaki saat bloklarına göre)

| Saat | Ne konuşulur |
|---|---|
| 0 - 0,5 | **Şimdi kapandı** — sözleşme sabit, herkes `docs/api-contract.md`'yi okudu mu diye teyit |
| 3. saat | Dilara: prompt gerçek `ollama` ile çalışıyor mu (format tutuyor mu)? Beyza: mock API ile uçtan uca akış var mı? Melike: kaç sentetik belge hazır? |
| 6. saat | İlk gerçek entegrasyon denemesi (Beyza'nın arayüzü + Dilara'nın gerçek motoru). Melike: ölçüm betiği gerçek çıktıyla çalışıyor mu? |
| 8. saat | **Dondurma** — yeni özellik yok, yalnızca hata düzeltme. Melike: README/rapor/sunum hazır mı? |
| 9 - 10 | Prova, Wi-Fi kapalı demo denemesi, yedek plan (run-cache varsa onunla, yoksa ekran kaydı) |

## Şu an (hiç beklemeden) paralel başlayabilecekler

İş GitHub issue'larına bölündü (#1-#13). Tek bir gerçek darboğaz var: **#8 (gerçek
API entegrasyonu)**, Dilara'nın #1-#4'ü ve Beyza'nın #5/#7'si bitmeden başlayamaz.
Geri kalan **12 issue'nun 11'i şu an aynı anda açılabilir**:

| Hemen başla (bağımlılığı yok) | Mock/varsayımla başla, sonra düzelt |
|---|---|
| #1 Ollama bağlantısı (Dilara) | #3 chunking.py — Melike'nin tek örnek belgesiyle başla, #10 bitince 1500/200 varsayımını doğrula |
| #5 main.py mock uç noktalar (Beyza) | #6 yükleme entegrasyonu — `documents.py`'nin (#12) **arayüzü** (fonksiyon imzası) bugün erken netleşirse mock yerine gerçeğine geçmek 1 satır |
| #7 İnceleme ekranı (Beyza, #5'in mock verisiyle) | #4 verify.py — elle yazılmış örnek kanıt/satır çiftleriyle test edilebilir, gerçek Gemma çıktısını beklemez |
| #9 tr_phone + tr_api_key (Melike) | |
| #10 sentetik belgeler (Melike) | |
| #11 report.py (Melike, sahte bulgu listesiyle) | |
| #12 documents.py (Melike) | |

**Tek bugünden netleşmesi gereken şey**: `documents.py`'nin extraction
fonksiyonunun imzası (örn. `extract(dosya) -> str`) — Melike, Beyza ve Dilara
bunu 5 dakikada konuşup sabitlerse, #3 ve #6 hiç beklemeden gerçek interface'e
göre yazılabilir, yalnızca `documents.py`'nin *içi* (özellikle #12'deki zor
docx/run haritası) daha sonra tamamlanır.

Yani pratikte: **#2 (Dilara, #1'in hemen ardından) ve #8 (en son, herkes
bitince) dışında hiçbir şey birbirini beklemiyor.**

## Kritik uyarı

3. saat checkpoint'i atlanmasın: Dilara'nın prompt/format denemesi 3. saate kadar
   gerçek `ollama` ile hiç çalıştırılmadıysa, tüm pipeline'ın üzerine oturduğu
   varsayım (model JSON+satır formatını tutarlı döndürür) doğrulanmamış demektir —
   bu noktada hâlâ prompt'u değiştirecek zaman var, 6. saatte değişecek zaman yok.
