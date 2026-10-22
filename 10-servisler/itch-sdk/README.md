---
kapsam: itch-sdk (libMAItchSDK, v3) — ITCH piyasa verisi SDK'sı; sınıflar, thread modeli, alım yolu, Glimpse/Rewinder, abonelik API'si, momentum/tiering yetenekleri, kullanıcılar
kaynak:
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
dogrulama: 2026-10-22
durum: taslak
---

# itch-sdk (`libMAItchSDK`)

BIST ITCH piyasa verisi SDK'sı (C++, namespace `itch`, tek paylaşımlı kütüphane). Development'taki kod, eski bilgi tabanında "v3 rewrite" diye anlatılan sürümdür.

**Kullananlar:**
- HftSrvProd (`ItchSdkClient`)
- AlgorithmicTrading (`ItchSdkManager`)
- trade-data-app (cgo, `pkg/itch`)
- MAOrderSDK combiner (`itch::getItchSdk()`)

## Sınıflar

| Sınıf | Dosya | Rol |
|-------|-------|-----|
| `SDKItchManager` | `Clients/SDKItchManager.*` | Singleton. Yaşam döngüsü, abonelik kayıt defteri, snapshot oluşturma. Alttaki `extern "C"` C API'si de burada. |
| `ItchReceiver` | `Clients/ItchReceiver.*` | UDP RX thread'i: recv (POSIX `recvmmsg` / Onload ZC / XLIO), demux, SPSC kuyruğa koyma, PerfSDK metrikleri |
| `ItchClient` | `Clients/ItchClient.*` | (port, pazar) başına decoder thread'i: mesaj parse, Rewinder durum makinesi |
| `GlimpseClient` | `Clients/GlimpseClient.*` | TCP snapshot (login → sıralı veri → EndOfGlimpse) |
| `OrderbookInfo` | `OrderBook/OrderbookInfo.*` | Orderbook başına durum ve callback yönetimi (header, level, execute, eşik, momentum) |
| `OrderDepth` | `OrderBook/OrderDepth.*` | Taraf başına fiyat→miktar ve orderId→emir haritası |
| `SPSCRingBuffer` | `Public/spsc_ring_buffer.h` | Cache-line hizalı, 2'nin kuvveti boyutlu ring |
| `TscClock` | `Globals/TscClock.h` | `rdtsc` ile ns zaman damgası (hot path'te `clock_gettime` yok) |

## Thread modeli ve alım yolu

```
NIC ─► ItchReceiver (RX thread, pinli, SCHED_FIFO) ─► SPSC ring (port×pazar) ─► ItchClient (decode thread) ─► OrderbookInfo ─► abone callback'i
```

- RX thread yalnızca recv + memcpy + kuyruğa koyma yapar. Decode yavaşlarsa paket düşer (`packetsDroppedFull`), RX etkilenmez.
- Callback'ler **ItchClient thread'inde** çalışır. Tüketici (HFT `ItchSdkClient`) olayı kendi strateji kuyruğuna koyar; ağır iş callback içinde yapılmaz.
- Onload derlemesinde `LD_PRELOAD` yoksa `start()` kendini `execvp` ile yeniden başlatır.

## Glimpse ve Rewinder

- **Glimpse** (TCP): gün içinde açılışta partition başına snapshot alır, baseline sequence'i belirler. `itchsdk_is_glimpse_finished(market, partition)`.
  - ⚠ Yeni davranış (2026-10): Canlı ITCH paketleri Glimpse snapshot'ı bitene kadar **tamponlanır**, bitince sırayla işlenir. Snapshot emirleri sıralanır, flush'ta emir başına delete üretilir.
- **Rewinder** (UDP): sequence boşluğu görülünce eksik paketler istenir. Kurtarma bitince normal akışa dönülür.
- **Birincil/ikincil hat** (`ip`/`secondaryIp`) config'tedir. Seçim **açılışta ve process genelinde** yapılır, çalışma sırasında failover yoktur (`ItchClient.cpp` yorumu: "start-time only").
  - Varsayılan birincildir. Glimpse TCP bağlantısı birincilde başarısız olursa ya da zaman aşımına uğrarsa global seçim ikincile döner (`ITCHTCPConnection::Connect`). Bu Rewinder dahil sonraki bütün bağlantıları etkiler ve geri dönmez.
  - Multicast alımında demux iki hattın kaynak IP'lerini de tanır (`setMarketSourceIps`).
- **Partition kimliği:** `partId` Spot 1–4, VİOP 5–8 (`partition + 4`). Bu kural VİOP'ta 4'ten fazla partition'ı öngörmüyor, oysa HFT config'leri 6 tanımlıyor. ❓ 5–6. VİOP partition'larında `partId` çakışması olup olmadığı incelenmedi; [trade-data-app](../trade-data-app/README.md) partition farkıyla birlikte ertelenen konu.

## Abonelik API'si (`Public/itch_sdk.h`, C)

| Fonksiyon | Olay |
|-----------|------|
| `itchsdk_subscribe_header_changed` | Best bid/ask fiyat veya miktar değişti |
| `itchsdk_subscribe_header_snapshot` | İlk header durumu |
| `itchsdk_subscribe_order_level_changed` | Bir taraftaki kademe değişimi, **eşikli**: miktar eşiğin altında/üstünde, kaç kademe. Olayda `sideTotalQuantity`, `couldSweep`, `isMaxSizeExecution` alanları da gelir. |
| `itchsdk_update_level_subscription` | Eşik veya kademe güncelle |
| `itchsdk_update_level_max_order_qty` | Momentum: azami emir lot eşiği (0 = kapalı) |
| `itchsdk_update_level_exec_window` | Momentum: bu kadar ns içindeki fill'ler tek emir sayılır (0 = yalnız aynı borsa damgası) |
| `itchsdk_update_level_exec_arm_price` | Momentum: mutlak fiyat kapısı (ask bu fiyatın altındayken bayrak kalkmaz) |
| `itchsdk_subscribe_order_executed` / `add_order` / `order_delete` | Emir olayları (`ORDER_EXECUTED`'da kitaptaki emrin tarafı ve `prevHeaderQty`) |
| `itchsdk_subscribe_specific_order_executed` / `specific_order_events` | Belirli bir orderId (combiner) |
| `itchsdk_subscribe_equilibrium_price_update` | Denge fiyatı (müzayede) |
| `itchsdk_subscribe_orderbook_state_changed` | Seans durumu |
| `itchsdk_subscribe_snapshot_end` | Glimpse bitti |
| `itchsdk_subscribe_price_threshold_crossing` + `itchsdk_seed_price_threshold` | **Tiering**: promote/demote fiyat geçişi. Callback `false` dönerse geçiş reddedilir ve sonraki güncellemede yeniden tetiklenir. |
| `itchsdk_set_callback_enabled` | Aboneliği geçici aç/kapa (cold strateji maliyetsiz kalır) |
| `itchsdk_unsubscribe` | |
| `itchsdk_get_tick_size(obId, price)`, `itchsdk_get_orderbook_symbol`, `itchsdk_get_all_orderbook_ids` | Referans veri (fiyat adımı tablosu ITCH'ten gelir) |

C++ arayüzü (`Public/ItchSdk.h`, `itch::getItchSdk()`) yalnızca belirli emir olayları için dar bir yüzeydir; combiner bunu kullanır.

**Momentum (max-size) mantığı:**
- Bir saldırganın (aggressor) fill'leri, aynı borsa zaman damgasıyla veya pencere içinde toplanır.
- Toplam `maxOrderQty`'ye ulaştığı anda `isMaxSizeExecution` **yükselen kenarda** bir kez kalkar. Saniye sınırını geçen boşluklar da doğru hesaplanır.
- Tüketiciler: HFT Classic follow-max, Tavan max-size giriş/çıkış, Taban momentum girişi.

## Config (`ItchSdkConfigurations`, `Public/config.h`)

- Pazar: Spot / Derivative.
- Partition başına: ITCH multicast IP/port (birincil/ikincil), Glimpse IP/port ve kullanıcı, Rewinder IP/port ve yerel port, `localInterface`, kaynak IP.
- Worker ve trigger worker sayıları, CPU core ataması, Onload stack adı.

Değerler tüketici servisin config'inden gelir (HFT `[[markets]]`, AlgoProd `$Equity`/`$Derivative`, trade-data-app `itchConfigurations`).

## Build

CMake. Varyantlar: normal, **Onload** (`libMAItchSDK_Onload.so`), Mellanox. CI `itchsdk.yml` kütüphaneleri Algo-Setup `MAProdEnv/lib`'e yazar. Kütüphane, sürüm bilgisini (`MAItchSDK_BuildInfo`) gömülü taşır.

## Bilinen notlar

Eski bilgi tabanındaki ayrıntılı notlar (performans, pcap gözlemleri, mesaj kataloğu) büyük ölçüde geçerli. Bu doküman yalnızca güncel yapıyı ve API'yi özetler. ❓ Eski "bilinen buglar" listesinin hangilerinin düzeltildiği tek tek doğrulanmadı.
