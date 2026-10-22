---
kapsam: Itch-Replayer — ITCH yakalama ve offline tekrar oynatma aracı (recap)
kaynak:
  - repo: Itch-Replayer
    branch: main
    commit: c4b6029
dogrulama: 2026-10-22
durum: taslak
---

# Itch-Replayer (`recap`)

Bağımsız araç; stack'e bağlı değildir. BIST ITCH beslemesini pcap olarak yakalar ve interaktif terminal aracı `recap` ile **tek bir sembolün emir defterini mesaj mesaj** gezdirir:
- Belirli bir zamana atlanabilir.
- 1 / 10 / 100 / 1000 mesaj ileri veya geri gidilebilir.
- Her konumda çözülmüş ITCH mesajı ve yeniden kurulmuş ilk N kademe görülür.

Strateji davranışını geçmiş veriyle incelemek ve "o anda emir defteri neydi" sorusunu cevaplamak için kullanılır.

## Yapı

| Yer | İçerik |
|-----|--------|
| `capture/` | Yakalama: multicast (`tcpdump` / `AF_PACKET`, `mcast_capture.c`, `mcast_daemon.c`, supervisor scriptleri) ve Glimpse snapshot (`glimpse_snapshot.c`) |
| `src/` | Replay (C++): pcap → Eth/VLAN/IPv4/UDP soyma → MoldUDP64 → ITCH decode (A/F/E/C/D/R/O/Z/Y) → emir defteri |
| `vendor/itch-sdk/` | itch-sdk'nın kopyası; yalnızca `OrderBook/OrderDepth.cpp` derlenir |
| `data/` | `instruments.csv`, `xutum.csv` |
| `docs/` | Tasarım ve uygulama planları (sürekli yakalama, istek üzerine sembol sunucusu) |
| `CLAUDE.md` | Agent kuralları (aşağıda) |

## Ortam kuralları (repo `CLAUDE.md`'sinden)

- **Yalnızca test sunucusunda** derlenir ve çalıştırılır. Linux ve libpcap gerekir. Replay kısmı Homebrew libpcap ile macOS'ta da derlenir.
- **Prod sunucusuna kesinlikle dokunulmaz**, yakalama yalnızca test sunucusunda yapılır.
- Test sunucusunun GitHub erişimi yoktur, bu yüzden itch-sdk `vendor/` altına kopyalanmıştır.
- Sunucu adresleri bu dokümanda yer almaz; repo `CLAUDE.md`'sine bakın.

Docker: `Dockerfile` (replay), `Dockerfile.capture` (yakalama).
