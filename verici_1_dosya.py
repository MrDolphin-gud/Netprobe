from dataclasses import dataclass
from pathlib import Path
from typing import List

from ortak_1_yardimci import parcalara_ayir, sha256_dosya


@dataclass
class DosyaHazirligi:
    dosya_yolu: Path
    dosya_adi: str
    dosya_hash: str
    toplam_parca: int
    parcalar: List[bytes]
    dosya_boyutu: int


def dosya_hazirla(dosya_yolu: Path, payload_boyutu: int) -> DosyaHazirligi:
    ham = dosya_yolu.read_bytes()
    parcalar = parcalara_ayir(ham, payload_boyutu)
    return DosyaHazirligi(
        dosya_yolu=dosya_yolu,
        dosya_adi=dosya_yolu.name,
        dosya_hash=sha256_dosya(dosya_yolu),
        toplam_parca=len(parcalar),
        parcalar=parcalar,
        dosya_boyutu=len(ham),
    )
