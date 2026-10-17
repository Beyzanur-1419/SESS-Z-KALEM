"""Hızlı deneme: python -m engine.cli eval/fixtures/ornek_sozlesme_01.txt

Tüm doğrulanmış bulguları kabul edip maskeler; arayüz hazır olmadan motoru
uçtan uca test etmek içindir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import llm
from .pipeline import analiz_et
from .pseudonymize import maskele, rapor, sizinti_kontrol


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="engine.cli")
    p.add_argument("dosya", type=Path)
    p.add_argument("--model-yok", action="store_true", help="Yalnızca kural katmanı")
    p.add_argument("--model", default=llm.MODEL)
    p.add_argument("--json", action="store_true", help="Bulguları JSON olarak yazdır")
    a = p.parse_args(argv)

    metin = a.dosya.read_text(encoding="utf-8")
    sonuc = analiz_et(metin, model_kullan=not a.model_yok, model=a.model)
    if a.json:
        print(json.dumps(sonuc.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(f"Model: {sonuc.model_durumu} · süre {sonuc.sure_sn:.1f} sn · doğrulanamadı {sonuc.elenen}")
    for h in sonuc.hatalar:
        print("  HATA:", h)
    for b in sonuc.bulgular:
        konum = f"L{b.satir}" if b.konumlu else "  ? "
        print(f"[{b.kaynak:5}] {b.durum[:6]} {konum:>5} {b.kategori:<15} {b.kanit!r}  — {b.neden}")
        if b.durum == "dogrulandi":
            b.karar = "kabul"

    maskeli, _ = maskele(metin, sonuc.bulgular)
    sizinti = sizinti_kontrol(maskeli, sonuc.bulgular)
    print("\n--- Maskeli metin ---\n" + maskeli)
    print("\n" + rapor(sonuc.bulgular, sizinti, a.model if sonuc.model_kullanildi else "", sonuc.sure_sn))
    return 1 if sizinti else 0


if __name__ == "__main__":
    sys.exit(main())
