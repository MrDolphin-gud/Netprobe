import argparse
import os
from pathlib import Path

from verici_0_ayar import VericiAyar
from verici_2_gonderici import Verici


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP tabanli guvenilir dosya verici")
    parser.add_argument("dosya", help="Gonderilecek dosya yolu")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--timeout", type=float, default=0.4)
    parser.add_argument("--max-retry", type=int, default=5)
    parser.add_argument("--chunk", type=int, default=1024)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ayar = VericiAyar(
        hedef_host=args.host,
        hedef_port=args.port,
        timeout_saniye=args.timeout,
        max_yeniden_gonderim=args.max_retry,
        payload_boyutu=args.chunk,
    )
    env_log = os.environ.get("NETPROBE_VERICI_LOG")
    if env_log:
        ayar.log_dosyasi = Path(env_log)
    verici = Verici(ayar)
    basarili = verici.dosya_gonder(Path(args.dosya))
    if basarili:
        print("[Verici] Aktarim tamamlandi.")
    else:
        print("[Verici] Aktarim basarisiz.")


if __name__ == "__main__":
    main()
