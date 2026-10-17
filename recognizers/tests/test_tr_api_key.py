from recognizers import tr_api_key


def test_openai_anahtari_bulunur():
    found = tr_api_key.find("API_KEY=sk-ABCDEFGHIJ1234567890abcdefgh")
    assert len(found) == 1
    assert found[0].group().startswith("sk-")


def test_github_token_bulunur():
    token = "ghp_" + "a" * 36
    found = tr_api_key.find(f"token: {token}")
    assert [m.group() for m in found] == [token]


def test_aws_key_bulunur():
    found = tr_api_key.find("AKIAABCDEFGHIJKLMNOP kullan.")
    assert len(found) == 1


def test_google_key_bulunur():
    key = "AIza" + "a" * 35
    found = tr_api_key.find(f"key={key}")
    assert [m.group() for m in found] == [key]


def test_kisa_metin_eslesmez():
    found = tr_api_key.find("sk-kisa")
    assert found == []


def test_normal_metinde_yanlis_alarm_yok():
    found = tr_api_key.find("Bu belgede hiçbir anahtar yok, sadece düz metin.")
    assert found == []
