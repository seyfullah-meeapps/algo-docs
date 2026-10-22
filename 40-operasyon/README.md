---
kapsam: Kurulum, dağıtım, günlük çalışma takvimi, container'lar, açılış log imzaları, sunucu ayarları, Algo-Setup ve algo-configs repoları
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

Sunucu adresleri, kullanıcılar ve şifreler bu dokümanda **yer almaz**.

## Repolar

| Repo | Ne içerir |
|------|-----------|
| **Algo-Setup** | Müşteri sunucusuna kurulan her şey: servis klasörleri (`HFT/`, `OrderService/`, `MADatabaseService/`, `MAAlgoProd/`, `MAAdminUI/`), her birinde Dockerfile, `docker-compose{,-onload,-mlx}.yml` ve `scripts/run*.sh`. Ayrıca derlenmiş binary'ler (CI commit'ler), `MAProdEnv/` (SDK `.so` ve header'ları, Onload ve Mellanox kütüphaneleri), müşteri bazlı `Configs/<Müşteri>/` (order-service config, MySQL compose, DB scriptleri, nginx, tuning), kurulum ve tuning scriptleri. **Branch = ortam.** |
| **algo-configs** | İsmine rağmen çalışma config'i değildir. İçinde: container imajları (`container-images/`: `MAProdEnvironment` build imajı, `HftTest`, `OrderServiceTest`, `AlgoProdOnload`, dev ortamları), lisans uygulaması (`License-Setup/`), test senaryoları, web sitesi, **dokümanlar** (`doc/`). Canlı branch `master`. |

### algo-configs `doc/` (insan için yazılmış kaynaklar)

- **`BIST-Dökümanlar/`**: BISTECH ITCH, Glimpse, MoldUDP64 ve SoupBinTCP protokol spesifikasyonları (PDF), bağlantı bilgisi, test ortamı.
- **`Business/`**: HFT, Tavan, Warrant ve Arbitraj iş dokümanları; risk kontrol; mTrader admin; AKD.
- **`Development/`**: onboarding, dev ortamı, config'ler, sabah kontrolleri (`Sabah_Kontrolleri.docx`), temel terimler, DataStore API, AKD, mTrader test rehberi. CI tarafından üretilen Doxygen dokümanları (ouch-sdk, HFT, AlgorithmicTrading).
- **`Network/`**: ağ topolojisi. Hassas bilgi içerir.

Bu bilgi tabanı kodu esas alır. İş tanımıyla çelişki görürsen ikisini de belirt.

## Kurulum paketi

1. Algo-Setup CI (`algosetup.yml`) `main`, `development` ve `preprod` push'larında **müşteri başına kurulum zip'i** üretir ve S3'e yükler.
   - Matris: Piramit, A1, Alnus, Alnus Algo, Marbas, Global.
   - Her müşteri için `setup_mode` ve ağ hızlandırma seçimi (`onload` / `mlx` / normal) ayrıca tanımlıdır.
2. Müşteri sunucusunda kurulum: zip açılır, `install.sh` içinde `setup_mode` ayarlanır, `./install.sh` çalıştırılır. Script şunları yapar:
   - Docker ve docker-compose kurulumu
   - Onload/Mellanox kurulumu (varsa)
   - `setup_<servis>.sh` → `docker-compose up -d --build`
   - crontab ayarı
3. Doğrulama:
   - `crontab -l`
   - `sysctl -a | grep net.core` (kuyruk boyutları)
   - `docker ps`
   - `docker logs --tail 100 -f <container>`
   - `chronyc tracking` (BIST zaman sunucusuna senkron)

`setup_mode` değerleri: `hft_order`, `hft_order_db`, `order_db`, `db`, `hft`, `order`, `algo_order`, `order_algo_db`.

## Günlük takvim (crontab, hafta içi)

`hft_order_db` örneği:

| Saat | İş |
|------|----|
| 07:43 | `docker start MADatabaseService` |
| 07:44 | `docker start MAOrderService` |
| 07:45 | `docker start MAHft` |
| 23:29–23:30 | HFT ve order-service durdurulur |
| 23:45 | DB servisi durdurulur |

Sıra [sistem haritası → başlatma sırası](../00-genel/sistem-haritasi.md#başlatma-sırası) ile aynıdır.

Durdurma sırasında `run.sh` SIGTERM'i yakalar: servisi kapatır, log dosyalarını zip'ler ve S3'e yükler (`s3://…/<MODE>/<COMPANY_NAME>/<servis>/logs/`).

## Container'lar

- Hepsi `network_mode: host`.
- HFT container'ı:
  - `cpuset` ile izole çekirdeklere bağlıdır.
  - `NET_ADMIN`, `IPC_LOCK`, `SYS_NICE` yetkileri vardır.
  - `memlock` sınırsızdır, `rtprio` 99.
  - Loglar `$HOME/workingDirectory/container-logs/<servis>/`'a bağlanır.
- **Container adları branch'e göre değişir.** Örneğin development compose'larında `MAHftTest`, `MAOrderServiceTest`, `MADatabaseServiceTest`; prod'da `MAHft`, `MAOrderService`, `MADatabaseService`, `MAAlgoProd`.

## Sunucu ayarları (`setup_tunning.sh`)

`tunning/` scriptleri: CPU (güç profili), kernel/sysctl, NIC, IRQ taşıma, THP kapatma, GRUB `isolcpus`, kalıcı `hft-tuning.service`. Müşteriye özel ayarlar `Configs/<Müşteri>/tunning/`'dedir.

Prod'da yaşanmış sorunlar nedeniyle bilerek kapalı tutulan ayarlar:
- `mlockall` / `sdkLockMemory`: host kilitlenmesi.
- Main thread pinleme: ping ve ssh ölüyordu, iLO reset gerekti.
- `SCHED_FIFO` env kapısı: `stalld` yoksa kworker aç kalıyor.

Ayrıntılar HftSrvProd `Configuration.toml` yorumlarında.

## Açılış log imzaları

Her adımda bir önceki servisin "hazır" imzasını gördükten sonra sıradakini başlat. Port numaraları ortama göre değişir.

**1. trade-data-app** (`docker logs <db container>`):
```
[AdminAPI] listening on :<adminApiPort>
[RestAPI] listening on <restPort>
[SNAPSHOT] Market 1 snapshot end received with N total instruments
```
- Listener satırları instrument snapshot'ından **önce** basılabilir.
- Bu aralıkta başlayan order-service ve HFT eksik enstrüman listesi çeker. MAOrderSDK limit tablosunda olmayan hisseler `1001 unknown instrument (no limit entry)` ile reddedilir.
- Bu yüzden Pay için `Market 1` snapshot-end satırını bekle; VİOP kullanılıyorsa `Market 2`'yi de.

**2. order-service:**
```
Instruments were fetched successfully. Count: N        ← trade-data-app bağlantısı tamam
Client connected …                                      ← BIST oturumu
[Server] Started Listening                              ← MARpc (HFT/AlgoProd buraya bağlanır)
Grpc Server listening on 0.0.0.0:<grpcPort>             ← HAZIR
```

**3. HftSrvProd:**
```
Restarting with Onload                                  ← çalışma anında Onload'un gerçekten açıldığını gösterir
DatabaseServiceClient::Connect - Login successful
MAOrderSDK: N active OUCH user(s) loaded …
HFT INITIALIZATION COMPLETE / Status: LIVE              ← nihai hazır sinyali
```
- Banner'daki `Network: Onload Enabled` derleme bayrağıdır, çalışma anı kanıtı değildir.
- OUCH kullanıcıları handoff ile gelir. Sabah handoff'u yoksa replay gate 20 sn sonra kendiliğinden açılır (`zero-handoff` CRIT log'u).
- Handoff sırasında: `orderUserDisconnected: handoff for OUCH user … i/N` ve `HFT took over OUCH user …`.

## Sabah kontrolleri

İnsan için hazırlanmış kontrol listesi: algo-configs `doc/Development/Sabah_Kontrolleri.docx`. ❓ Bu bilgi tabanına aktarılmadı.
