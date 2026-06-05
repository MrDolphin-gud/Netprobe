# NetProbe

UDP üzerinde güvenilir dosya aktarımı, trafik izleme ve ağ performans analizi platformu.

## Hakkında

NetProbe, UDP'nin doğasında bulunmayan güvenilirlik mekanizmalarını uygulama katmanında gerçekleştiren bir istemci-sunucu sistemidir. Dosya aktarımı sırasında ağ olaylarını JSONL formatında kaydeder ve toplanan verilerden throughput, goodput, retransmission rate gibi performans metriklerini hesaplar.

Temel özellikler:

- Stop-and-wait tabanlı güvenilir aktarım (sequence number, ACK, timeout, retransmission)
- Paket başına SHA-256 checksum ve aktarım sonu dosya hash doğrulaması
- Yapılandırılabilir yapay paket kaybı simülasyonu (verici ve alıcı tarafı)
- Otomatik karşılaştırmalı deney çalıştırıcı ve grafik üretici

## Kullanım

**1) Alıcıyı başlat:**

```bash
python alici_2_main.py --host 127.0.0.1 --port 9000
```

**2) Vericiyi başlat:**

```bash
python verici_3_main.py dosya.bin --host 127.0.0.1 --port 9000
```

**3) Metrikleri görüntüle:**

```bash
python analiz_0_metrik.py --log logs/verici_olaylar.jsonl
```

**4) Karşılaştırmalı deneyleri çalıştır:**

```bash
python analiz_1_deney.py
```

Grafikler `deney_sonuclari/` klasörüne, özet JSON `deney_sonuclari/deney_ozet.json` dosyasına kaydedilir.

### Uzak bilgisayara aktarım

Alıcı tarafında tüm arayüzlerden dinlemek için `--host 0.0.0.0` kullanılır. Verici tarafında alıcının IP adresi belirtilir:

```bash
# Alıcı (uzak makine)
python alici_2_main.py --host 0.0.0.0 --port 9000

# Verici (yerel makine)
python verici_3_main.py dosya.bin --host 192.168.1.42 --port 9000
```

Windows Firewall'da UDP portuna izin gerekebilir:

```powershell
New-NetFirewallRule -DisplayName "NetProbe UDP" -Direction Inbound -Protocol UDP -LocalPort 9000 -Action Allow
```

## Komut Satırı Parametreleri

### alici_2_main.py

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| `--host` | `127.0.0.1` | Dinlenecek IP adresi |
| `--port` | `9000` | UDP port numarası |
| `--loss` | `0.0` | Yapay paket kayıp oranı (0.0–1.0) |

### verici_3_main.py

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| `dosya` | — | Gönderilecek dosya yolu (zorunlu) |
| `--host` | `127.0.0.1` | Alıcının IP adresi |
| `--port` | `9000` | Alıcının port numarası |
| `--timeout` | `0.4` | ACK bekleme süresi (saniye) |
| `--max-retry` | `5` | Paket başına maks. yeniden gönderim |
| `--chunk` | `1024` | Payload boyutu (byte) |
| `--loss` | `0.0` | Yapay paket kayıp oranı (0.0–1.0) |

## Protokol Tasarımı

### Paket Formatı

Tüm paketler JSON olarak kodlanır ve UTF-8 byte dizisi şeklinde gönderilir.

| Tür | Alanlar | Yön |
|-----|---------|-----|
| `START` | type, seq, filename, file_hash, total_packets, file_size, checksum | Verici → Alıcı |
| `START_ACK` | type, seq, checksum | Alıcı → Verici |
| `DATA` | type, seq, payload_b64, checksum | Verici → Alıcı |
| `ACK` | type, seq, checksum | Alıcı → Verici |
| `FIN` | type, seq, checksum | Verici → Alıcı |
| `FIN_ACK` | type, seq, checksum | Alıcı → Verici |

### Aktarım Akışı

```
  Verici                             Alıcı
    │                                  │
    │──── START (dosya bilgisi) ──────>│
    │<─── START_ACK ──────────────────│
    │                                  │
    │──── DATA seq=0 ────────────────>│
    │<─── ACK  seq=0 ────────────────│
    │                                  │
    │──── DATA seq=1 ────────────────>│
    │         × (paket kayboldu)       │
    │         (timeout)                │
    │──── DATA seq=1 ────────────────>│  ← yeniden gönderim
    │<─── ACK  seq=1 ────────────────│
    │              ...                 │
    │──── FIN ───────────────────────>│
    │<─── FIN_ACK ───────────────────│
    │                                  │
```

### Güvenilirlik Mekanizmaları

| Mekanizma | Açıklama |
|-----------|----------|
| Sequence Number | Her veri paketi sıralı numaralandırılır |
| ACK | Alıcı, aldığı her paketi onaylar |
| Timeout | Belirli sürede ACK gelmezse paket yeniden gönderilir |
| Max Retry | Paket başına en fazla 5 yeniden deneme (yapılandırılabilir) |
| Duplicate Handling | Aynı seq tekrar gelirse dosyaya yazılmaz, ACK tekrar gönderilir |
| Paket Checksum | SHA-256 ile her paketin bütünlüğü doğrulanır |
| Dosya Hash | Aktarım sonunda tüm dosyanın SHA-256 hash'i karşılaştırılır |

## Karşılaştırmalı Deneyler

`analiz_1_deney.py` aşağıdaki 4 senaryoyu otomatik olarak çalıştırır:

| # | Senaryo | Değişken | Test Değerleri |
|---|---------|----------|----------------|
| 1 | Dosya boyutunun etkisi | Dosya boyutu | 1 KB, 10 KB, 100 KB, 500 KB |
| 2 | Paket boyutunun etkisi | Chunk boyutu | 256 B, 512 B, 1024 B, 4096 B, 8192 B |
| 3 | Timeout değerinin etkisi | Timeout süresi | 0.05 s, 0.1 s, 0.2 s, 0.4 s, 1.0 s |
| 4 | Kayıp oranının etkisi | Yapay kayıp | %0, %5, %10, %20, %30 |

Her senaryo için throughput, goodput, tamamlanma süresi ve retransmission rate grafikleri üretilir.

## Olay Kayıtları

Aktarım sırasında tüm olaylar `logs/` dizininde JSONL formatında kaydedilir:

- `verici_olaylar.jsonl` — paket gönderimi, ACK alımı, timeout, retransmission
- `alici_olaylar.jsonl` — paket alımı, duplicate tespiti, checksum hataları, oturum durumu

## Proje Yapısı

```
├── ortak_0_protokol.py     Paket formatı, encode/decode, checksum
├── ortak_1_yardimci.py     Dosya hash ve parçalama
├── ortak_2_log.py          JSONL olay logger
├── alici_0_ayar.py         Alıcı yapılandırması
├── alici_1_oturum.py       Alıcı protokol işleyici
├── alici_2_main.py         Alıcı giriş noktası
├── verici_0_ayar.py        Verici yapılandırması
├── verici_1_dosya.py       Dosya hazırlama / parçalama
├── verici_2_gonderici.py   Stop-and-wait gönderim motoru
├── verici_3_main.py        Verici giriş noktası
├── analiz_0_metrik.py      Performans metrikleri (konsol)
├── analiz_1_deney.py       Otomatik deney + grafik üretici
└── README.md
```




