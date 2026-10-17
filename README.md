# Sessiz Kalem

Gizli bir belgeyi bir yapay zekâ servisiyle ya da şirket dışındaki biriyle paylaşmadan
önce hangi bilgilerin gizlenmesi gerektiğini cihazdan çıkmadan bulan, kullanıcı
onayıyla maskeleyen açık kaynaklı bir araç. Model ve kod tamamen cihazda çalışır —
belge hiçbir bulut servisine yüklenmez.

## Kurulum

```bash
git clone https://github.com/Beyzanur-1419/SESS-Z-KALEM.git
cd SESS-Z-KALEM
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

ollama pull gemma4:e4b
```

Kurulumdan sonra **Wi-Fi'yi kapatıp** şunu deneyin — aracın internetsiz
çalıştığının en basit kanıtı budur:

```bash
ollama run gemma4:e4b "test"
```

Model/ortam gereksinimleri (RAM, disk, GPU) için bkz.
[`docs/model-ve-ortam-notu.md`](docs/model-ve-ortam-notu.md).

## Çalıştırma

```bash
uvicorn main:app --reload
```

Tarayıcıda `http://127.0.0.1:8000` adresini açın.

## Kullanım akışı

1. Belgeyi yükleyin (pdf, docx ya da txt).
2. Bulunan bulguları kanıt metinleriyle birlikte inceleyin.
3. Her bulguyu kabul edin, reddedin ya da kaçırılmış bir bilgiyi elle ekleyin.
4. Maskeleyin; temiz belgeyi ve değişiklik raporunu indirin.

Şema ve API ayrıntıları için bkz. [`docs/api-contract.md`](docs/api-contract.md).

## Bilinen sınırlar

- **Bağlamsal tespitte kaçırma kaçınılmazdır.** Model bazı gizli bilgileri
  gözden kaçırabilir; bu yüzden inceleme ekranı ve insan onayı zorunludur,
  araç hiçbir şeyi sizin yerinize otomatik maskelemez.
- **Maskeleme tek başına yeterli olmayabilir.** "2019'da ihaleyi kazanan tek
  firma" gibi bir ayrıntı, maskelenmiş bir adı yine de ele verebilir —
  maskeleme, bağlamdan bağımsız anonimleştirme garantisi vermez.
- **`.docx` çıktısında yalnızca paragraflar taranır ve maskelenir** — tablo
  hücreleri içindeki metin kapsam dışıdır (bkz.
  [`docs/maskeleme-notu.md`](docs/maskeleme-notu.md)).
- **Türkçe ekler** ("Ahmet'e", "Ahmet'in") yalın ad + ek kalıbıyla eşleştirilir;
  bu her durumda mükemmel çalışmayabilir.
- **Eşleşme tablosu saklanırsa** (ileri düzey, isteğe bağlı özellik) bu takma
  adlandırmadır (pseudonymization), geri döndürülemez anonimleştirme değildir.

## Hukuki uyarı

Bu araç **hukuki danışmanlık ya da uyumluluk garantisi vermez**. KVKK ya da
başka bir mevzuata atıf yapmanız gerekiyorsa, kullanmadan önce bir hukukçuya
danışın. Şu ifadelerden kaçının: "tamamen güvenli", "KVKK'ya tam uyumlu",
"hiç kaçırmaz" — bunların hiçbiri doğru değildir ve araç bunu iddia etmez.

## Depo içeriği

- [`docs/api-contract.md`](docs/api-contract.md) — bulgu şeması ve kanıt doğrulama algoritması (sabit sözleşme)
- [`docs/rakip-analizi-ve-reuse.md`](docs/rakip-analizi-ve-reuse.md) — emsal projeler ve yeniden kullanılan açık kaynak kod
- [`docs/hazir-versiyon-kapsam.md`](docs/hazir-versiyon-kapsam.md) — demo kapsamının ötesinde eklenebilecekler
- [`docs/model-ve-ortam-notu.md`](docs/model-ve-ortam-notu.md) — model kararı (gemma4:e4b) ve ortam gereksinimleri
- [`docs/maskeleme-notu.md`](docs/maskeleme-notu.md) — maskeleme sırasında metin düzeyinde ne değişir (.txt vs .docx riski)
- [`docs/gorev-dagilimi.md`](docs/gorev-dagilimi.md) — görev dağılımı ve yürütme planı
- [`recognizers/`](recognizers/) — kural tabanlı tanıyıcılar (T.C. Kimlik No, plaka, IBAN, telefon, API anahtarı)
- [`eval/`](eval/) — ölçüm betiği ve sentetik test belgeleri

Yeni bir kural tanıyıcı veya sentetik test belgesi eklemek için bkz.
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Credits

T.C. Kimlik No, plaka ve IBAN tanıyıcılarındaki regex ve sağlama (checksum) mantığı
[Microsoft Presidio](https://github.com/data-privacy-stack/presidio) (MIT Lisansı)
projesinden uyarlanmıştır; ayrıntı için ilgili dosyaların başındaki not ve
`docs/rakip-analizi-ve-reuse.md`'ye bakın.

## Lisans

MIT — bkz. [`LICENSE`](LICENSE).
