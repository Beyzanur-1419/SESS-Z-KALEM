# Bulgu Şeması ve API Sözleşmesi (v1)

İlk 30 dakikada sabitlenen sözleşme budur. Üç kişi de bu dosyaya göre paralel çalışır;
değişiklik gerekirse önce burada güncellenir.

## 1. Model (Gemma) ham çıktısı — chunk başına

Gemma'dan yalnızca bunu isteriz. Karakter konumu **istemeyiz** (küçük modeller
sayılarda hata yapar) ama DataVeil'in yaklaşımını referans alıp bir **satır ipucu**
isteriz — bu, kanıt doğrulamayı çok daha sağlam hale getirir (bkz. bölüm 3).

```json
{
  "bulgular": [
    {
      "kategori": "teklif_bedeli | kod_adi | ozel_anlasma | musteri_bilgisi | strateji | diger",
      "kanit": "belgeden birebir alıntı",
      "satir": 12,
      "neden": "neden gizli olabilir (kısa)",
      "risk": "yuksek | orta | dusuk",
      "guven": 0.0
    }
  ]
}
```

- `satir`: modele verilen chunk'ın satır numarası (chunk'ı Gemma'ya göndermeden önce
  `L001| ...` biçiminde numaralandırıyoruz — DataVeil'in `number_lines()` yöntemi).
  Model yanlış satır verirse arama ±N satır içinde genişler, tamamen başarısız olursa
  bulgu `dogrulanamadi` olarak işaretlenir, elenmez.
- `kanit` birebir tutmuyorsa (model parafraz/typo yaptıysa) bkz. bölüm 3'teki kademeli arama.

## 2. Birleşik (kural + model) bulgu nesnesi — review ekranının ve API'nin gördüğü şey

Kural katmanı ve model katmanı farklı kaynaklardan gelir ama review ekranı, maskeleme ve
rapor **tek bir tip** üzerinden çalışır. Bu, Kişi 2'nin işini kaynaktan bağımsız hale getirir.

```json
{
  "id": "f-0007",
  "kaynak": "kural | model | elle",
  "kategori": "tc_kimlik | iban | telefon | plaka | api_anahtari | eposta | teklif_bedeli | kod_adi | ozel_anlasma | musteri_bilgisi | strateji | diger",
  "kanit": "belgeden birebir alıntı",
  "konum": { "satir": 12, "baslangic": 134, "bitis": 151 },
  "neden": "kısa açıklama",
  "risk": "yuksek | orta | dusuk",
  "guven": 0.9,
  "durum": "dogrulandi | dogrulanamadi",
  "karar": "beklemede | kabul | red",
  "etiket": null
}
```

- `konum`: kural bulgularında recognizer'dan direkt gelir (kesin). Model bulgularında
  kanıt doğrulama adımının bulduğu kesin aralıktır; bulunamazsa `null` ve
  `durum: "dogrulanamadi"`.
- `etiket`: yalnızca `karar: "kabul"` olduğunda maskeleme sırasında atanır
  (`KOD_ADI_1`, `TUTAR_1` gibi); önceden boş kalır.
- Tekilleştirme anahtarı: `konum` doluysa `(satir, baslangic, bitis)`; değilse
  `(kategori, kanit)`. Çakışan aralıklarda en uzun olan tutulur (DataVeil `entities.py`
  ile aynı kural).

## 3. Kanıt doğrulama: kademeli arama (naif substring aramasından daha sağlam)

Orijinal plan "alıntıyı belgede ara, yoksa ele" diyordu. Bu, gemma4:e4b gibi küçük bir
modelin ufak bir boşluk/satır sonu/aksan hatası yapması durumunda bulguyu gereksiz yere
eler. DataVeil'in `detector.py`/`_pieces()` mantığını Türkçe'ye uyarlayıp şu sırayla
deniyoruz (ilk eşleşen kazanır, `satir` ipucuna en yakın olan seçilir):

1. **Aynı satırda tam eşleşme** (boşluk normalize edilmiş).
2. **Satır sonuna bölünmüş eşleşme** (`"...Proje\nKartal..."` gibi iki satıra yayılmış).
3. **Kısmi/alt-kelime eşleşme** (en az 2 karakter, örn. `"1500"` içinde `"500"`).
4. **Türkçe ek onarımı**: `"Kartal'a"`, `"Kartal'ın"` gibi ekleri ayırıp yalın kök ile
   eşleştir (doküman bunu zaten sorun olarak işaretlemişti — çözüm burada).

Hiçbiri bulamazsa: bulgu silinmez, `durum: "dogrulanamadi"` ile işaretlenir ve rapora
"elle kontrol edilmeli" listesine düşer. **Sessizce kaybolma yok** — bu DataVeil'in en
değerli tasarım kararı.

## 4. HTTP uç noktaları (Dilara ↔ Beyza sözleşmesi)

`docs/gorev-dagilimi.md`'de öneri olarak duruyordu, burada karara bağlanıyor —
Beyza'nın arayüzü ve Dilara'nın motoru bundan sonra bunu sabit kabul edip paralel
ilerleyebilir.

| Uç nokta | Girdi | Çıktı |
|---|---|---|
| `POST /belgeler` | dosya (pdf/docx/txt, multipart) | `{ "belge_id": "...", "bulgular": [Bulgu, ...] }` |
| `POST /bulgular/{id}/karar` | `{ "karar": "kabul" \| "red" }` | güncellenmiş `Bulgu` |
| `POST /belgeler/{belge_id}/bulgular` | elle eklenen `{ "kategori", "kanit", "konum" }` | yeni `Bulgu` (`kaynak: "elle"`, `durum: "dogrulandi"`) |
| `POST /belgeler/{belge_id}/maskele` | — (yalnızca `karar: "kabul"` olanlar işlenir) | `{ "temiz_metin": "...", "rapor": Rapor }` |
| `GET /belgeler/{belge_id}/indir?tip=docx\|txt\|rapor` | — | dosya |

`Bulgu` = bölüm 2'deki birleşik nesne. `Rapor` şeması:

```json
{
  "ozet": { "kategori_basina_sayi": { "kod_adi": 2, "iban": 1 }, "toplam_maskelenen": 5 },
  "reddedilenler": [ { "kategori": "...", "konum": { "satir": 12 } } ],
  "elle_eklenenler": [ { "kategori": "...", "konum": { "satir": 7 } } ],
  "dogrulanamayanlar": [ { "kategori": "...", "konum": { "satir": 20 }, "not": "elle kontrol edilmeli" } ]
}
```

Rapor **gerçek değer içermez** kuralı (Proje Özeti, Özellikler §7) burada sıkı
tutuluyor: `kanit` alanı rapora **hiçbir durumda girmez** — reddedilen ya da
doğrulanamayan bir bulgu bile potansiyel olarak hassas bir değer taşıyabilir,
bu yüzden yalnızca `kategori` ve `konum.satir` (kullanıcı belgeye dönüp kendi
gözüyle bakabilsin diye) tutulur. `kabul` edilip maskelenen değerler rapora hiç
girmez, yalnızca `ozet.kategori_basina_sayi` sayılarıyla görünür.

Hata durumu: desteklenmeyen dosya tipi veya boş belge → `400` + `{ "hata": "..." }`.
Model (Ollama) ayakta değilse → `503` + `{ "hata": "model_erisilemez" }`; arayüz bunu
"Ollama çalışıyor mu kontrol edin" mesajıyla göstermeli (demo günü en olası arıza budur).

## 5. Dayanak

- Satır numaralama + kademeli konum bulma: `JoaoPeixoto003/DataVeil`,
  `backend/anonymizer/detector.py` ve `entities.py` (MIT) — mantık port edildi, kod
  birebir kopyalanmadı (onlar Gemini'ye, biz Gemma/Ollama'ya gönderiyoruz).
- Kategori adları ve risk/guven alanları orijinal Sessiz Kalem planından (Proje Özeti, s.4).
