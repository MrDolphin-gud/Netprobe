import json
import time
from pathlib import Path
from typing import Any


class OlayLogger:
    def __init__(self, dosya_yolu: Path):
        self.dosya_yolu = dosya_yolu
        self.dosya_yolu.parent.mkdir(parents=True, exist_ok=True)

    def log(self, olay: str, **alanlar: Any) -> None:
        kayit = {"ts": time.time(), "event": olay}
        kayit.update(alanlar)
        with self.dosya_yolu.open("a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=True) + "\n")
