# 1 Günlük Demo → "Mühendislik Ürünü" İçin Ek Kapsam

Orijinal 10 saatlik plan ve kapsam (Proje Özeti) zaten doğru; buradaki liste onu
**değiştirmiyor**, üstüne binen ve maliyeti düşük ama jüri/izlenim açısından etkisi
yüksek eklemeler. Hepsi bugün (gün başlamadan) veya gün içinde "ortak" bloklarda
yapılabilir.

## Bugünden hazır olabilecekler (kod günü zamanını yemez)

- [x] `LICENSE` (MIT) — repoya eklendi.
- [x] `docs/api-contract.md` — bulgu şeması sabitlendi.
- [x] `docs/rakip-analizi-ve-reuse.md` — hangi kodun nereden geldiği, lisans atfı.
- [x] `recognizers/tr_national_id.py`, `tr_license_plate.py`, `tr_iban.py` — Presidio'dan
      porte edilmiş, test edilmiş checksum/regex mantığı (kural katmanının en riskli/
      en çok zaman alacak kısmı artık hazır; Kişi 3 bugün `tr_phone.py` ve
      `tr_api_key.py`'yi aynı kalıpla tamamlayabilir).
- [x] `recognizers/tests/test_tr_recognizers.py` — 9 test, geçiyor.
- [ ] `recognizers/tr_phone.py` — `phonenumbers` kütüphanesiyle (Presidio'nun yaptığı gibi),
      kendi regex'imizi yazmaktan daha güvenilir.
- [ ] `recognizers/tr_api_key.py` — yaygın API anahtarı kalıpları (örn. `sk-`, `AIza`,
      `ghp_` önekleri + uzunluk); bu tamamen bize ait, emsal yok.
- [ ] README iskeleti: ne yapar / nasıl kurulur / hangi model / bilinen sınırlar /
      "hukuki danışmanlık değildir" uyarısı + **Credits** bölümü (Presidio atfı).
- [ ] Sentetik test belgeleri + beklenen etiket CSV'si (ölçüm planı için) — en mekanik iş,
      bugünden yazılırsa gün içi 1-2 saat kazanılır.

## Gün içinde ekstra maliyeti düşük, güveni yüksek eklemeler

- **Run-cache / replay modu** (DataVeil'den esinlenilen fikir): her Gemma çağrısının ham
  cevabını `runs/<belge_hash>.json` olarak diske yaz. Faydası iki yönlü:
  1. Canlı demo sırasında model yavaş/kararsızsa, önceden kaydedilmiş gerçek bir
     çalıştırmayı "replay" ederek gösterebilirsin — yedek ekran kaydından daha iyi,
     çünkü hâlâ gerçek arayüz + gerçek etkileşim.
  2. Prompt iyileştirme (6-8. saat) sırasında modeli tekrar tekrar çağırmadan
     geliştirme yapılabilir.
  Maliyet: ~20-30 dakika, Kişi 1'in işine eklenir.
- **CI workflow** (`.github/workflows/test.yml`): push'ta `pytest` çalıştır. DataVeil'de
  de var, maliyeti 10 dakika, "bu ekip ciddi mühendislik yapıyor" izlenimini güçlendirir.
- **`requirements.txt` sabitlenmiş sürümlerle**: kurulum komutundaki paket listesini
  (`fastapi uvicorn ...`) sürüm pinleyerek dosyaya geçir — "paket adları zamanla
  değişebilir" riskini azaltır, jüri/organizatör kurulumu tekrarlamak isterse sorun
  çıkarmaz.
- **`CONTRIBUTING.md` + 5-6 "good first issue"**: doküman zaten planlıyor, sadece
  bugünden taslağı hazırlanabilir, gün içinde doldurulur.

## Bilinçli olarak YAPILMAYACAKLAR (kapsam dışı kalmalı)

Doküman bunları zaten doğru elemiş, değiştirmiyoruz: OCR, toplu işlem, UYAP formatları,
presidio-analyzer'ı bağımlılık olarak ekleme (spaCy nedeniyle), eşleşme dosyası/geri
çevirme (zaman kalırsa).

## Sonraki adım

Kural katmanının en riskli kısmı artık test edilmiş durumda. Sıradaki en yüksek riskli
parça **Gemma3:4b'nin JSON+kanıt+satır formatını tutarlı döndürmesi** — bunu gerçek
`ollama` ile bugün erken test etmenizi öneririm (gün planındaki 0,5-3. saat bloğundan
önce, mümkünse bugün), çünkü format tutmazsa prompt'u değiştirmek zaman alır ve bu
tüm pipeline'ın üzerine oturduğu varsayım.
