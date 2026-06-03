from dataclasses import dataclass
from pathlib import Path


@dataclass
class VericiAyar:
    hedef_host: str = "127.0.0.1"
    hedef_port: int = 9000
    payload_boyutu: int = 1024
    timeout_saniye: float = 0.4
    max_yeniden_gonderim: int = 5
    log_dosyasi: Path = Path("logs/verici_olaylar.jsonl")
    yapay_kayip_orani: float = 0.0
