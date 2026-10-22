---
kapsam: Operasyon giriş noktası — kurulum/dağıtım, config, log imzaları ve sabah kontrolleri dosyalarının indeksi; Algo-Setup ve algo-configs repolarının rolü
kaynak:
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
  - repo: algo-configs
    branch: master
    commit: ab35dde
dogrulama: 2026-10-22
durum: taslak
---

# Operasyon

Sunucu adresleri, kullanıcılar ve şifreler bu klasörde **yer almaz**.

## Hangi soru, hangi dosya

| Soru | Dosya |
|------|-------|
| Müşteri sunucusuna ne, nasıl kuruluyor? CI müşteri matrisi, `install.sh`, `setup_mode`, crontab saatleri, container adları, cpuset, volume'ler, `run.sh`, tuning, binary güncelleme | [kurulum-ve-dagitim.md](kurulum-ve-dagitim.md) |
| Bir servisin config'i nerede (repo şablonu, Algo-Setup müşteri dosyası, container yolu)? Hangi port, host ya da kullanıcı servisler arasında **aynı olmalı**? nginx-proxy yönlendirmesi | [config-referansi.md](config-referansi.md). Anahtarların anlamı servis dokümanlarında; oradan linkli |
| Servis ayağa kalktı mı? "HAZIR" satırı ne? Sabah toplu emir zamanlayıcı satırları, handoff, hata ve kapanış log'ları, log dosyalarının yeri | [log-imzalari.md](log-imzalari.md) |
| Her sabah 08:30'a kadar ne kontrol edilir? Seans öncesi canlı emir testi, yeniden başlatma sırası | [sabah-kontrolleri.md](sabah-kontrolleri.md) |
| Başlatma sırası ve servis bağımlılıkları | [sistem haritası § Başlatma sırası](../00-genel/sistem-haritasi.md#başlatma-sırası) |
| Prod'da bilerek kapalı tutulan ayarlar (`mlockall`, main thread pinleme, `SCHED_FIFO`) | [hftsrvprod/config.md § Prod'da kapalı tutulanlar](../10-servisler/hftsrvprod/config.md#prodda-kapalı-tutulanlar-toml-yorumlarından) |

## Repolar

| Repo | Ne içerir |
|------|-----------|
| **Algo-Setup** | Müşteri sunucusuna kurulan her şey. Servis klasörleri (`HFT/`, `OrderService/`, `MADatabaseService/`, `MAAlgoProd/`, `MAAdminUI/`), her birinde Dockerfile, compose ve `scripts/run*.sh`. Derlenmiş binary'ler (CI commit'leri), `MAProdEnv/` (SDK `.so` dosyaları, Onload ve Mellanox kütüphaneleri), müşteri bazlı `Configs/<Müşteri>/` (servis config'leri, MySQL, nginx-proxy, DB scriptleri). **Branch = ortam:** `development`, `preprod`, `main` (prod). |
| **algo-configs** | İsmine rağmen çalışma config'i **değildir**. Container imajları (`container-images/`: `MAProdEnvironment` build imajı, test imajları), lisans uygulaması (`License-Setup/`), test senaryoları, web sitesi ve insan için yazılmış dokümanlar (`doc/`). Canlı branch `master`. |

### algo-configs `doc/` (insan için yazılmış kaynaklar)

- **`BIST-Dökümanlar/`**: BISTECH ITCH, Glimpse, MoldUDP64 ve SoupBinTCP protokol spesifikasyonları (PDF), bağlantı bilgisi, test ortamı.
- **`Business/`**: HFT, Tavan, Warrant ve Arbitraj iş dokümanları; risk kontrol; mTrader admin; AKD.
- **`Development/`**: onboarding, dev ortamı, config'ler, sabah kontrolleri (`Sabah_Kontrolleri.docx` → [sabah-kontrolleri.md](sabah-kontrolleri.md)), temel terimler, DataStore API, AKD, mTrader test rehberi. CI'ın ürettiği Doxygen dokümanları (ouch-sdk, HFT, AlgorithmicTrading).
- **`Network/`**: ağ topolojisi. Hassas bilgi içerir.

Bu bilgi tabanı kodu esas alır. İş tanımıyla çelişki görürsen ikisini de belirt.

## Bilinmesi gereken beş şey

Ayrıntıları linkli dosyalardadır; burada yalnız uyarı olarak duruyor.

1. **Container adları branch'e göre değişir.** Cron her branch'te prod adlarını kullanır. Dev ve preprod'da günlük start/stop bu yüzden çalışmaz ([kurulum-ve-dagitim § Adlar](kurulum-ve-dagitim.md#adlar-compose-container_name), K-184).
2. **Gece 22:00 güncellemesi** (`setup_copy_binary.sh`) bozuk. Düzeltilirse prod'a development binary'si ve config'i kopyalar. Container içinde elle yapılan config değişikliği bu güncellemede ezilir (K-179).
3. **Ağ:** Servislerin çoğu `network_mode: host` ile çalışır. **İstisnalar** MySQL (`3306`) ve MAAdminUI (`81:80`); ikisi bridge ağında.
4. **Log arşivi:** S3'e yalnız HFT yükler. Diğer servisler kapanışta arşivi yerelde bırakır. trade-data-app'in log volume'u yoktur (K-185).
5. **HFT ve AlgoProd `docker stop`'ta temiz kapanmaz.** `run.sh`'taki `kill -15 <isim>` çalışmaz (K-183).
