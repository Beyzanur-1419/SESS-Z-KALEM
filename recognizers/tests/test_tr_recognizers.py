from recognizers import tr_iban, tr_license_plate, tr_national_id


def test_tckn_valid():
    assert tr_national_id.validate_checksum("10000000146")


def test_tckn_invalid():
    assert not tr_national_id.validate_checksum("12345678901")


def test_tckn_cannot_start_with_zero():
    assert not tr_national_id.validate_checksum("01234567890")


def test_plate_valid_province():
    assert tr_license_plate.validate("34ABC1234")


def test_plate_invalid_province():
    assert not tr_license_plate.validate("99ABC1234")


def test_plate_found_in_text():
    found = tr_license_plate.find("Araç plakası 06 A 123 olarak kayıtlı.")
    assert [m.group() for m in found] == ["06 A 123"]


def test_iban_valid():
    assert tr_iban.validate("TR330006100519786457841326")


def test_iban_invalid_checksum():
    assert not tr_iban.validate("TR330006100519786457841327")


def test_iban_found_with_spaces():
    found = tr_iban.find("IBAN: TR33 0006 1005 1978 6457 8413 26.")
    assert [m.group() for m in found] == ["TR33 0006 1005 1978 6457 8413 26"]
