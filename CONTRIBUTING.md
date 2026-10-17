# Katkı Rehberi

## Yeni bir kural tanıyıcı eklemek

`recognizers/` altına yeni bir dosya ekleyin (örnek: `recognizers/tr_vergi_no.py`),
mevcut `tr_national_id.py`/`tr_iban.py` ile aynı kalıbı izleyin:

- Modül başında kaynak/atıf notu (varsa, hangi emsal projeden/algoritmadan
  esinlenildi)
- `PATTERN`/`PATTERNS`: regex
- `validate(...)` ya da `validate_checksum(...)`: doğrulama mantığı
- `find(text)`: metindeki geçerli eşleşmeleri döndürür

`recognizers/tests/` altına aynı isimle bir test dosyası ekleyin; en az şunları
test edin: geçerli değer, geçersiz checksum/format, metin içinde bulma.

## Testleri çalıştırma

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Yeni sentetik test belgesi eklemek

`eval/fixtures/` altına bir `.txt` belge ve yanında aynı isimli `_beklenen.csv`
dosyası ekleyin (format: `kategori,kanit,risk` — bkz. mevcut örnek). Gerçek
sözleşme/kişi bilgisi kullanmayın (bkz. Proje Özeti, Güvenlik Tasarımı §4).

## Katkı alanları

Proje Özeti'ndeki tablo hâlâ geçerli: yeni tanıyıcı, sektör profili (YAML), yeni
test belgesi, farklı açık modellerle ölçüm, dil desteği, dosya biçimi desteği
(.odt/.rtf/OCR).
