from __future__ import annotations

import random
import socket
import time
from pathlib import Path

from ortak_0_protokol import (
    PAKET_ACK,
    PAKET_DATA,
    PAKET_FIN,
    PAKET_FIN_ACK,
    PAKET_START,
    PAKET_START_ACK,
    paket_coz,
    paket_kodla,
    paket_uret,
)
from ortak_2_log import OlayLogger
from verici_0_ayar import VericiAyar
from verici_1_dosya import dosya_hazirla


class Verici:
    def __init__(self, ayar: VericiAyar):
        self.ayar = ayar
        self.logger = OlayLogger(ayar.log_dosyasi)
        self.hedef = (ayar.hedef_host, ayar.hedef_port)

    def _gonder_ve_ack_bekle(
        self,
        sock: socket.socket,
        paket: dict,
        beklenen_ack_tipi: str,
        beklenen_ack_no: int,
    ) -> bool:
        deneme = 0
        while deneme <= self.ayar.max_yeniden_gonderim:
            deneme += 1
            if self.ayar.yapay_kayip_orani > 0 and random.random() < self.ayar.yapay_kayip_orani:
                self.logger.log(
                    "packet_dropped_simulated",
                    packet_type=paket["type"],
                    seq=paket["seq"],
                    attempt=deneme,
                )
            else:
                sock.sendto(paket_kodla(paket), self.hedef)
                self.logger.log(
                    "packet_sent",
                    packet_type=paket["type"],
                    seq=paket["seq"],
                    attempt=deneme,
                )

            try:
                ham_ack, _ = sock.recvfrom(65535)
                ack = paket_coz(ham_ack)
            except socket.timeout:
                self.logger.log("timeout", packet_type=paket["type"], seq=paket["seq"], attempt=deneme)
                continue

            if ack.get("type") == beklenen_ack_tipi and int(ack.get("seq", -999)) == beklenen_ack_no:
                self.logger.log("ack_received", ack_type=ack["type"], ack_no=ack["seq"])
                return True

            self.logger.log("ack_unexpected", ack=ack, expected_type=beklenen_ack_tipi, expected_no=beklenen_ack_no)

        self.logger.log("packet_failed", packet_type=paket["type"], seq=paket["seq"])
        return False

    def dosya_gonder(self, dosya_yolu: Path) -> bool:
        hazir = dosya_hazirla(dosya_yolu, self.ayar.payload_boyutu)
        baslangic = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self.ayar.timeout_saniye)

            start_paket = paket_uret(
                PAKET_START,
                seq=-1,
                extra={
                    "filename": hazir.dosya_adi,
                    "file_hash": hazir.dosya_hash,
                    "total_packets": hazir.toplam_parca,
                    "file_size": hazir.dosya_boyutu,
                },
            )
            if not self._gonder_ve_ack_bekle(sock, start_paket, PAKET_START_ACK, -1):
                return False

            for seq, parca in enumerate(hazir.parcalar):
                data_paket = paket_uret(PAKET_DATA, seq=seq, payload=parca)
                if not self._gonder_ve_ack_bekle(sock, data_paket, PAKET_ACK, seq):
                    return False

            fin_paket = paket_uret(PAKET_FIN, seq=hazir.toplam_parca)
            if not self._gonder_ve_ack_bekle(sock, fin_paket, PAKET_FIN_ACK, hazir.toplam_parca):
                return False

        bitis = time.time()
        self.logger.log(
            "transfer_completed",
            filename=hazir.dosya_adi,
            file_size=hazir.dosya_boyutu,
            duration_sec=bitis - baslangic,
            total_packets=hazir.toplam_parca,
        )
        return True
