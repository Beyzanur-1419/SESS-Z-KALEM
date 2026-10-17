# SırKalkan (çalışma adı)

Gizli bir belgeyi bir yapay zekâ servisiyle ya da şirket dışındaki biriyle paylaşmadan
önce hangi bilgilerin gizlenmesi gerektiğini cihazdan çıkmadan bulan, kullanıcı
onayıyla maskeleyen açık kaynaklı bir araç. Model ve kod tamamen cihazda çalışır.

Proje özeti ve 10 saatlik plan için bkz. ekip dokümanı. Bu repo için:

- [`docs/api-contract.md`](docs/api-contract.md) — bulgu şeması ve kanıt doğrulama algoritması (sabit sözleşme)
- [`docs/rakip-analizi-ve-reuse.md`](docs/rakip-analizi-ve-reuse.md) — emsal projeler ve yeniden kullanılan açık kaynak kod
- [`docs/hazir-versiyon-kapsam.md`](docs/hazir-versiyon-kapsam.md) — demo kapsamının ötesinde eklenebilecekler
- [`docs/model-ve-ortam-notu.md`](docs/model-ve-ortam-notu.md) — model kararı (gemma3:4b) ve ortam gereksinimleri
- [`recognizers/`](recognizers/) — kural tabanlı tanıyıcılar (T.C. Kimlik No, plaka, IBAN)

## Credits

T.C. Kimlik No, plaka ve IBAN tanıyıcılarındaki regex ve sağlama (checksum) mantığı
[Microsoft Presidio](https://github.com/data-privacy-stack/presidio) (MIT Lisansı)
projesinden uyarlanmıştır; ayrıntı için ilgili dosyaların başındaki not ve
`docs/rakip-analizi-ve-reuse.md`'ye bakın.

## Lisans

MIT — bkz. [`LICENSE`](LICENSE).
