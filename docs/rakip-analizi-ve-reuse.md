# Rakip/Emsal Repo Analizi — Ne Kullanılabilir, Ne Kullanılamaz

## Microsoft Presidio (`data-privacy-stack/presidio`, MIT)

İncelendi: `presidio-analyzer/predefined_recognizers/country_specific/turkey/*`,
`generic/iban_recognizer.py`, `generic/iban_patterns.py`, `generic/phone_recognizer.py`.

**Doğrudan kullanılabilir (kod olarak taşındı → `recognizers/`):**
- T.C. Kimlik No regex + NVİ sağlama algoritması → `tr_national_id.py` (test edildi, geçti)
- Plaka regex + il kodu (01-81) doğrulaması → `tr_license_plate.py` (test edildi, geçti)
- TR IBAN regex + mod-97 checksum → `tr_iban.py` (test edildi, geçti)

**Kullanılmadı, kasıtlı karar:** `presidio-analyzer` paketinin tamamını bağımlılık olarak
eklemedik. `pyproject.toml`'a bakıldığında paket sert bağımlılık olarak **spaCy**,
**numpy**, **tldextract** istiyor — bizim "az bağımlılıklı, hızlı kurulan, tamamen
internetsiz" sözümüzle çelişir (spaCy dil modeli indirme gerektirebilir, kurulum
etkinlik günü risk). Bunun yerine yalnızca regex + checksum **mantığını** kendi sade
Python modüllerimize taşıdık, sınıf hiyerarşisini (`PatternRecognizer` vb.) almadık.
Atıf `recognizers/*.py` dosyalarının başında var.

**Kullanılabilir ama henüz taşınmadı (zaman kalırsa):**
- `phone_recognizer.py` → `phonenumbers` kütüphanesini kullanıyor (hafif, saf Python,
  spaCy gerektirmiyor). Telefon tanıyıcımız için `pip install phonenumbers` + birkaç
  satır sarmalayıcı yeterli; kendi regex'imizi yazmaktan daha güvenilir.
- `email_recognizer.py`, `credit_card_recognizer.py` → regex'leri küçük, doğrudan
  kopyalanabilir, bağımlılık getirmiyor.

## DataVeil (`JoaoPeixoto003/DataVeil`, MIT) — JunctionX Lisbon 2026

Bu, bizim akışımızla neredeyse birebir aynı bir hackathon ürünü ama **Gemini** (bulut)
kullanıyor — bizim ana itirazımızı (bulut = amaç çürür) tam olarak onlar için geçerli
kılıyor. Kod kalitesi beklenenin üzerinde: tip anotasyonlu, UTF-16 offset yönetimi,
9 test dosyası, CI workflow'u var.

**Mimari olarak alınan fikirler (kod kopyalanmadı, port edildi — bkz. `api-contract.md`):**
1. **Satır numaralama + kademeli konum bulma** (`detector.py` → `_pieces()`/`_search()`):
   modelden tam karakter konumu istemek yerine satırı numaralandırıp modelden satır
   ipucu + kanıt metni istemek, sonra tam satır → bölünmüş satır → kısmi kelime →
   onarılmış (typo/aksan) eşleşme sırasıyla aramak. Bizim orijinal planımızdaki "tüm
   belgede ara, yoksa ele" yaklaşımından çok daha sağlam — küçük model (gemma3:4b)
   büyük ihtimalle Gemini'den daha fazla küçük hata yapacağı için bize onlardan daha
   kritik.
2. **Run-cache / replay modu** (`_save_run`/`detect_from_run`): modelin ham cevabını
   içerik hash'iyle diske yazıp API'siz tekrar oynatabilme. Bizim için demo güvenliği:
   canlı model yavaş/bozuksa önceden kaydedilmiş bir çalıştırmayı gösterebiliriz —
   doküman zaten "yedek ekran kaydı" planlıyordu, bu daha iyisi: **yedek canlı demo**.
3. **Tekilleştirme/örtüşme kuralı** (`entities.py`): aynı konumda birden fazla bulgu
   varsa en uzununu tut, geri kalanı at. Basit ve doğru.
4. **`API_CONTRACT.md` dosyası**: FE/BE arasındaki sözleşmeyi dosyaya yazıp ikisi de ona
   göre ilerliyor. Biz de `docs/api-contract.md` olarak aynısını yaptık.

**Kullanılmadı:** Gemini istemcisi, PDF yeniden inşası (`pdf_reconstructor.py` — tek
`*` ile kelime maskeleme yaklaşımı bizim planımızdaki `[KOD_ADI_1]` etiketli, tutarlı
maskeleme ile çakışıyor, bizim yaklaşımımız jüri için daha okunur ve demoya daha uygun).

## CamoText / Anoni / PrivacyScrubber

Kapalı kaynak ürünler, kod incelenemedi — yalnızca konumlandırma/pazar referansı olarak
kullanıldı (önceki mesajda).

## Lisans notu

Tüm porte edilen kod MIT lisanslı Presidio'dan; MIT, türetilmiş çalışmada da MIT ile
uyumlu. README'ye bir "Credits / Attribution" bölümü eklenmeli (bugünkü yapılacaklar
listesine ekle).
