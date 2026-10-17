"""Beklenen (ground-truth) gizli bilgi listesini CSV'den okur.

CSV biçimi (bkz. eval/fixtures/*.csv):
    kategori,kanit,risk
    kod_adi,Proje Kartal,yuksek
    tc_kimlik,10000000146,yuksek
"""

import csv
from pathlib import Path
from typing import List

from eval.metrics import Beklenen


def oku(yol: Path) -> List[Beklenen]:
    with open(yol, encoding="utf-8", newline="") as f:
        return [
            Beklenen(kategori=row["kategori"], kanit=row["kanit"], risk=row.get("risk", "orta"))
            for row in csv.DictReader(f)
        ]
