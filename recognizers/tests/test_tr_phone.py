from recognizers import tr_phone


def test_gsm_numarasi_bulunur():
    found = tr_phone.find("Telefon: 0532 123 45 67 numarasından ulaşabilirsiniz.")
    assert len(found) == 1
    assert found[0].group().replace(" ", "") in {"05321234567", "5321234567"}


def test_sabit_hat_bulunur():
    found = tr_phone.find("Ofis hattı: 0212 345 67 89.")
    assert len(found) == 1


def test_gecersiz_numara_bulunmaz():
    found = tr_phone.find("Sipariş no: 123 456.")
    assert found == []


def test_start_end_dogru():
    metin = "Ara: 0532 123 45 67 lütfen."
    found = tr_phone.find(metin)
    assert len(found) == 1
    m = found[0]
    assert metin[m.start():m.end()] == m.group()
