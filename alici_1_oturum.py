from __future__ import annotations

import random
import socket
from pathlib import Path
from typing import Dict, Tuple

from ortak_0_protokol import (
    PAKET_ACK,
    PAKET_DATA,
    PAKET_FIN,
    PAKET_FIN_ACK,
    PAKET_START,
    PAKET_START_ACK,
    paket_dogrula,
    paket_kodla,
    paket_uret,
    payload_al,
)
from ortak_1_yardimci import sha256_bytes
from ortak_2_log import OlayLogger


class AliciOturumu:
    def __init__(self, cikti_klasoru: Path, logger: OlayLogger):
        self.cikti_klasoru = cikti_klasoru
        self.logger = logger
        self.dosya_adi: str | None = None
        self.hedef_hash: str | None = None
        self.beklenen_toplam = 0
        self.gelen_parcalar: Dict[int, bytes] = {}

    def _ack_yolla(self, sock: socket.socket, adres: Tuple[str, int], ack_no: int, ack_tipi: str = PAKET_ACK) -> None:
        ack = paket_uret(ack_tipi, seq=ack_no)
        sock.sendto(paket_kodla(ack), adres)
        self.logger.log("ack_sent", ack_no=ack_no, ack_type=ack_tipi, target=f"{adres[0]}:{adres[1]}")

    def handle(self, sock: socket.socket, paket: dict, adres: Tuple[str, int], yapay_kayip_orani: float = 0.0) -> bool:
        if yapay_kayip_orani > 0 and random.random() < yapay_kayip_orani:
            self.logger.log("packet_dropped_simulated", packet_type=paket.get("type"), seq=paket.get("seq"))
            return False

        if not paket_dogrula(paket):
            self.logger.log("packet_invalid_checksum", packet_type=paket.get("type"), seq=paket.get("seq"))
            return False

        paket_tipi = paket.get("type")
        seq = int(paket.get("seq", -1))

        if paket_tipi == PAKET_START:
            self.dosya_adi = str(paket["filename"])
            self.hedef_hash = str(paket["file_hash"])
            self.beklenen_toplam = int(paket["total_packets"])
            self.gelen_parcalar.clear()
            self.logger.log(
                "session_started",
                filename=self.dosya_adi,
                total_packets=self.beklenen_toplam,
                source=f"{adres[0]}:{adres[1]}",
            )
            self._ack_yolla(sock, adres, ack_no=-1, ack_tipi=PAKET_START_ACK)
            return False

        if paket_tipi == PAKET_DATA:
            if seq not in self.gelen_parcalar:
                self.gelen_parcalar[seq] = payload_al(paket)
                self.logger.log("data_received", seq=seq, size=len(self.gelen_parcalar[seq]))
            else:
                self.logger.log("data_duplicate", seq=seq)

            self._ack_yolla(sock, adres, ack_no=seq, ack_tipi=PAKET_ACK)
            return False

        if paket_tipi == PAKET_FIN:
            self._ack_yolla(sock, adres, ack_no=seq, ack_tipi=PAKET_FIN_ACK)
            return self._oturumu_kapat()

        self.logger.log("packet_unknown_type", packet_type=paket_tipi, seq=seq)
        return False

    def _oturumu_kapat(self) -> bool:
        if self.dosya_adi is None or self.hedef_hash is None:
            self.logger.log("session_finish_error", reason="missing_start_packet")
            return False

        eksikler = [i for i in range(self.beklenen_toplam) if i not in self.gelen_parcalar]
        if eksikler:
            self.logger.log("session_finish_error", reason="missing_packets", missing_count=len(eksikler))
            return False

        birlesik = b"".join(self.gelen_parcalar[i] for i in range(self.beklenen_toplam))
        hesaplanan_hash = sha256_bytes(birlesik)

        if hesaplanan_hash != self.hedef_hash:
            self.logger.log("session_finish_error", reason="hash_mismatch")
            return False

        self.cikti_klasoru.mkdir(parents=True, exist_ok=True)
        hedef = self.cikti_klasoru / self.dosya_adi
        hedef.write_bytes(birlesik)
        self.logger.log("session_completed", filename=self.dosya_adi, bytes=len(birlesik), output=str(hedef))
        return True
