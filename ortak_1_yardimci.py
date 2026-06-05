import hashlib
from pathlib import Path
from typing import List


def sha256_bytes(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


def sha256_dosya(dosya_yolu: Path) -> str:
    hasher = hashlib.sha256()
    with dosya_yolu.open("rb") as f:
        for blok in iter(lambda: f.read(1024 * 64), b""):
            hasher.update(blok)
    return hasher.hexdigest()


def parcalara_ayir(veri: bytes, parca_boyutu: int) -> List[bytes]:
    if parca_boyutu <= 0:
        raise ValueError("parca_boyutu pozitif olmalidir")
    return [veri[i : i + parca_boyutu] for i in range(0, len(veri), parca_boyutu)]
