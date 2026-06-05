import base64
import hashlib
import json
from typing import Any, Dict


PAKET_DATA = "DATA"
PAKET_ACK = "ACK"
PAKET_START = "START"
PAKET_START_ACK = "START_ACK"
PAKET_FIN = "FIN"
PAKET_FIN_ACK = "FIN_ACK"


def _bytes_to_b64(veri: bytes) -> str:
    return base64.b64encode(veri).decode("ascii")


def _b64_to_bytes(veri: str) -> bytes:
    return base64.b64decode(veri.encode("ascii"))


def payload_checksum(seq: int, payload: bytes, paket_tipi: str) -> str:
    ham = f"{paket_tipi}:{seq}:".encode("utf-8") + payload
    return hashlib.sha256(ham).hexdigest()


def paket_uret(
    paket_tipi: str,
    seq: int,
    payload: bytes = b"",
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    paket = {
        "type": paket_tipi,
        "seq": seq,
        "payload_b64": _bytes_to_b64(payload),
        "checksum": payload_checksum(seq=seq, payload=payload, paket_tipi=paket_tipi),
    }
    if extra:
        paket.update(extra)
    return paket


def paket_kodla(paket: Dict[str, Any]) -> bytes:
    return json.dumps(paket, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def paket_coz(veri: bytes) -> Dict[str, Any]:
    return json.loads(veri.decode("utf-8"))


def paket_dogrula(paket: Dict[str, Any]) -> bool:
    payload = _b64_to_bytes(paket.get("payload_b64", ""))
    beklenen = payload_checksum(
        seq=int(paket.get("seq", -1)),
        payload=payload,
        paket_tipi=str(paket.get("type", "")),
    )
    return beklenen == paket.get("checksum")


def payload_al(paket: Dict[str, Any]) -> bytes:
    return _b64_to_bytes(paket.get("payload_b64", ""))
