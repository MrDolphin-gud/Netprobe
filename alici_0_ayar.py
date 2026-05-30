from dataclasses import dataclass
from pathlib import Path


@dataclass
class AliciAyar:
    host: str = "127.0.0.1"
    port: int = 9000
    buffer_size: int = 65535
    cikti_klasoru: Path = Path("alinan_dosyalar")
    log_dosyasi: Path = Path("logs/alici_olaylar.jsonl")
    yapay_kayip_orani: float = 0.0
