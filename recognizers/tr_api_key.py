"""Yaygın API anahtarı kalıpları: önek + minimum uzunluk.

Emsal yok — bu tamamen projeye özel bir tanıyıcı (Presidio'da karşılığı yok).
Kapsanan önekler: OpenAI (`sk-`), GitHub personal access token (`ghp_`),
AWS access key (`AKIA`), Google API key (`AIza`). Yanlış pozitifi azaltmak
için her önek için minimum uzunluk da aranıyor.

Not: engine/pipeline.py'de aynı desenle bir yer tutucu (`_API`) zaten vardı;
bu modül onun yerini alır (bkz. docs/gorev-dagilimi.md).
"""

import re

PATTERN = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})\b"
)


def find(text: str):
    return list(PATTERN.finditer(text))
