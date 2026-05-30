import argparse
import socket

from alici_0_ayar import AliciAyar
from alici_1_oturum import AliciOturumu
from ortak_0_protokol import paket_coz
from ortak_2_log import OlayLogger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP tabanli dosya alici")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--loss", type=float, default=0.0, help="Yapay paket kayip orani [0.0-1.0]")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ayar = AliciAyar(host=args.host, port=args.port, yapay_kayip_orani=args.loss)
    logger = OlayLogger(ayar.log_dosyasi)
    oturum = AliciOturumu(ayar.cikti_klasoru, logger)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((ayar.host, ayar.port))
        logger.log("receiver_started", host=ayar.host, port=ayar.port, loss=ayar.yapay_kayip_orani)
        print(f"[Alici] Dinleniyor: {ayar.host}:{ayar.port}")

        while True:
            veri, adres = sock.recvfrom(ayar.buffer_size)
            try:
                paket = paket_coz(veri)
            except Exception as exc:  # noqa: BLE001
                logger.log("packet_decode_error", error=str(exc))
                continue

            tamamlandi = oturum.handle(sock, paket, adres, yapay_kayip_orani=ayar.yapay_kayip_orani)
            if tamamlandi:
                print("[Alici] Aktarim basariyla tamamlandi.")


if __name__ == "__main__":
    main()
