# Maskeleme: Metin Düzeyinde Ne Değişir

`docs/api-contract.md` §2'deki `karar: "kabul"` olan bulgular elimizde olduğunda,
metin üzerinde iki farklı değişiklik türü var — biri kolay (.txt), biri gerçek
mühendislik riski taşıyor (.docx). İkisini ayrı ele almak gerekiyor.

## 1. Önce, tek seferlik: etiket atama

Maskelemeden önce, kabul edilen **tüm** bulgular üzerinde tek bir geçişle
normalize edilmiş değer → etiket eşlemesi kurulur (`eval/metrics.py`'deki
`_anahtar` ile aynı normalizasyon: boşluk atılır, küçük harfe çevrilir).
Aynı değer belgede kaç yerde geçerse geçsin aynı etiketi alır:

```
"Proje Kartal" (1. geçiş)  -> KOD_ADI_1
"Proje Kartal" (2. geçiş)  -> KOD_ADI_1   (aynı anahtar, yeni etiket yok)
"850.000 TL"               -> TEKLIF_BEDELI_1
```

Bu eşleme kurulmadan maskeleme yapılırsa aynı değer belgede farklı yerlerde
farklı etiketler alabilir — rapor okunamaz hale gelir.

## 2. Düz metin (.txt): offset kayması tuzağı

Bulguların `konum.baslangic`/`konum.bitis` alanları metindeki mutlak karakter
aralığıdır. **Tuzak**: etiketin uzunluğu orijinal değerden neredeyse her zaman
farklıdır —`"850.000 TL"` (10 karakter) → `"[TEKLIF_BEDELI_1]"` (17 karakter).
Bulguları soldan sağa sırayla, önceki değişiklikten etkilenen bir string
üzerinde `str.replace` ya da aynı offsetlerle art arda splice ederseniz, ilk
değişiklik sonraki bulgunun offsetini kaydırır ve yanlış yeri maskelersiniz.

**Doğru yöntem**: span'ları `baslangic`'e göre artan sırada işleyip, **orijinal
metinden** kopyalanan aralıkları ve etiketleri ardışık biriktirip tek seferde
birleştirmek — hiçbir offset üzerinde yerinde değişiklik yapılmaz, bu yüzden
uzunluk farkı hiç sorun olmaz:

```
imleç=0, sonuç=[]
her bulgu (baslangic artan sırada):
    sonuç.ekle( metin[imleç:baslangic] )   # aradaki orijinal parça
    sonuç.ekle( "[" + etiket + "]" )
    imleç = bitis
sonuç.ekle( metin[imleç:] )                # kalan kuyruk
döndür "".join(sonuç)
```

Bu mantık `pseudonymize.py`'de uygulandı ve test edildi (bkz. kod). **.txt için
risk burada biter** — biçimlendirme yok, yalnızca karakter dizisi var.

## 3. .docx: asıl risk — biçimlendirme kaybı

Tespit için metin, `python-docx` ile tüm paragrafların birleştirilmesiyle elde
edilir (`"\n".join(p.text for p in belge.paragraphs)`); bulgu offsetleri **bu
birleşik düz metne göredir**, orijinal `.docx`'in paragraf/run yapısına göre
değil.

Eğer maskeleme sonrası çıktı bu düz metinden sıfırdan yeni bir `Document()`
yazılarak üretilirse, **orijinal biçimlendirme (kalın, italik, başlık stili,
tablo) tamamen kaybolur**. Bu, "paylaşıma hazır temiz belge" vaadini zedeler —
jüri/kullanıcı orijinaline hiç benzemeyen, düz metne dönüşmüş bir belge görür.

**Doğru yöntem**: extraction aşamasında, düz metindeki her karakterin hangi
paragraf+run'dan geldiğini tutan bir **ters harita** kurulur:
`offset -> (paragraf_index, run_index, run_ici_offset)`. Maskeleme aşamasında
her onaylı span bu haritayla ilgili run'a geri eşlenir; span bir run'ın yalnızca
bir kısmını kapsıyorsa o run'ı bölüp (örn. `"Toplam "` + `"850.000 TL"` +
`" olarak"` üç ayrı run'a ayrılır) yalnızca ortadaki parça etiketle değiştirilir,
geri kalan biçimlendirme korunur.

**MVP kararı**: Bu harita olmadan docx çıktısı üretmeyin — "iyi niyetli ama
kırık" bir belge, hiç belge olmamasından daha kötü bir izlenim bırakır. Zaman
dar giderse önce `.txt` çıktısını sağlam yapın (risk yok), `.docx` biçimlendirme
korumasını ayrı bir görev olarak planlayın; en kötü ihtimalle `.docx` çıktısı da
düz metin olarak üretilsin ama bu, README'de açık bir bilinen sınır olarak
yazılsın ("karmaşık biçimlendirmeli belgelerde stil korunmaz").

## 4. Rapor üretimiyle ilişkisi

Aynı maskeleme geçişinden, `docs/api-contract.md` §4'teki Rapor için gereken
`ozet.kategori_basina_sayi` (kaç bulgu hangi kategoride maskelendi) ve
reddedilen/doğrulanamayan bulguların (yalnızca kategori+satır, kanıt metni
değil) listesi aynı anda üretilir.
