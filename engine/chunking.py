"""Belgeyi satır numaralı, örtüşen parçalara böler (docs/api-contract.md §1).

Satır numaraları BELGE geneline göredir: 3. parçadaki "L042|" belgenin 42.
satırıdır. Böylece modelin döndürdüğü `satir` ipucu doğrudan doğrulamada
kullanılabilir. Fikir: JoaoPeixoto003/DataVeil `number_lines()` (MIT).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Parca:
    ilk_satir: int  # 1 tabanlı, dahil
    son_satir: int  # 1 tabanlı, dahil
    metin: str  # "L001| ..." biçiminde numaralı


def numarala(satirlar: list[str], ilk: int = 1) -> str:
    return "\n".join(f"L{ilk + i:03d}| {s}" for i, s in enumerate(satirlar))


def _uzun_satiri_bol(satir: str, boyut: int) -> list[str]:
    return [satir[i : i + boyut] for i in range(0, len(satir), boyut)] or [""]


def parcala(metin: str, boyut: int = 1500, ortusme: int = 200) -> list[Parca]:
    """Satırları en fazla `boyut` karakterlik parçalara toplar; ardışık
    parçalar en az `ortusme` karakterlik tam satırla örtüşür.

    `boyut`tan uzun tek satır varsa o satır parçalarına ayrılır ama hepsi aynı
    satır numarasını taşır (doğrulama satır ipucunu yine doğru kullanır).
    """
    if not metin.strip():
        return []
    # (satir_no, icerik) — uzun satırlar bölünmüş halde
    birimler: list[tuple[int, str]] = []
    for no, satir in enumerate(metin.split("\n"), start=1):
        for p in _uzun_satiri_bol(satir, boyut):
            birimler.append((no, p))

    parcalar: list[Parca] = []
    i = 0
    while i < len(birimler):
        uzunluk, j = 0, i
        while j < len(birimler) and (j == i or uzunluk + len(birimler[j][1]) + 1 <= boyut):
            uzunluk += len(birimler[j][1]) + 1
            j += 1
        dilim = birimler[i:j]
        govde = "\n".join(f"L{no:03d}| {s}" for no, s in dilim)
        parcalar.append(Parca(dilim[0][0], dilim[-1][0], govde))
        if j >= len(birimler):
            break
        # örtüşme: sondan geriye doğru `ortusme` karakter kadar birimi tekrar al
        geri, k = 0, j
        while k - 1 > i and geri < ortusme:
            k -= 1
            geri += len(birimler[k][1]) + 1
        i = k if k > i else j
    return parcalar
