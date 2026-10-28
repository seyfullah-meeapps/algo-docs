---
kapsam: itch-sdk (libMAItchSDK, v3) — giriş ve indeks; görev, kullananlar, sınıflar, alt dosyalar, kısa özetler, eski bug listesinin durumu, build
kaynak:
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
dogrulama: 2026-10-22
durum: taslak
---

# itch-sdk (`libMAItchSDK`)

Feature takibi: [extended execution/quote API ve build sınırı](quote-executed-feature.md) — referans development desteği değildir.

BIST ITCH piyasa verisi SDK'sı (C++, namespace `itch`, tek paylaşımlı kütüphane, `extern "C"` API). Development'taki kod, eski bilgi tabanında "v3 rewrite" diye anlatılan sürümdür.

**Kullananlar:**
- HftSrvProd (`ItchSdkClient`) → [hftsrvprod/itch-entegrasyonu](../hftsrvprod/itch-entegrasyonu.md)
- AlgorithmicTrading (`ItchSdkManager`)
- trade-data-app (cgo, `pkg/itch`)
- MAOrderSDK combiner (`itch::getItchSdk()`) → [maordersdk/emir-akisi § 9](../maordersdk/emir-akisi.md#9-combiner-srccombiner)

Tüketici bazında hangi fonksiyonların kullanıldığı: [abonelik-api § 9](abonelik-api.md#9-tüketiciler).

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`alim-yolu.md`](alim-yolu.md) | Thread'ler ve başlatma sırası, recv modları (POSIX/Onload ZC/XLIO), demux ve MoldUDP64, birincil/ikincil hat, gap ve Rewinder, Glimpse ve canlı tampon, kuyruk dolması, partition varsayımları, PerfSDK metrikleri, kopma senaryoları |
| [`mesajlar-ve-emir-defteri.md`](mesajlar-ve-emir-defteri.md) | ITCH mesaj kataloğu ve byte düzenleri, **timestamp modeli**, fiyat/miktar ölçeği ve tick tablosu, `OrderbookInfo`/`OrderDepth`, emir olaylarının kitaba etkisi, header hesabı, orderbook state, snapshot emir sırası, kilitler |
| [`abonelik-api.md`](abonelik-api.md) | Yaşam döngüsü, `ItchSdkConfigurations` alanları, C API ve callback argümanları, handle modeli, level eşik semantiği, momentum/max-size, tiering, C++ arayüzü, referans veri fonksiyonları, tüketiciler |

## Sınıflar

| Sınıf | Dosya | Rol |
|-------|-------|-----|
| `SDKItchManager` | `Clients/SDKItchManager.*` | Singleton. Yaşam döngüsü, abonelik kayıt defteri, snapshot oluşturma, `extern "C"` gövdeleri |
| `ItchReceiver` | `Clients/ItchReceiver.*` | UDP RX thread'i: recv, demux, SPSC kuyruğa koyma, metrikler |
| `ItchClient` | `Clients/ItchClient.*` | Partition başına decoder thread'i: MoldUDP64, mesaj parse, Rewinder durum makinesi |
| `GlimpseClient` | `Clients/GlimpseClient.*` | TCP snapshot (SoupBinTCP login → veri → EndOfSnapshot) |
| `OrderbookInfo` | `OrderBook/OrderbookInfo.*` | Orderbook başına durum ve callback dizileri (header, level, execute, eşik, momentum) |
| `OrderDepth` | `OrderBook/OrderDepth.*` | Taraf başına fiyat→miktar ve orderId→emir haritası |
| `SPSCRingBuffer` | `Public/spsc_ring_buffer.h` | Cache-line hizalı ring |
| `TscClock` | `Globals/TscClock.h` | `rdtsc` tabanlı ns; yalnız RX metriklerinde |

## Kısa özetler

Ayrıntı ve kod referansları alt dosyalarda; burada yalnız yön bulmak için.

- **Thread modeli:** `NIC → ItchReceiver (RX) → SPSC ring → ItchClient (decode) → OrderbookInfo → callback`. Callback'ler **decode thread'inde** çalışır. Pinleme yalnız core > 0 verilirse, SCHED_FIFO yalnız `ITCH_RT_FIFO` env'i varsa ([alim-yolu § 1](alim-yolu.md#1-bileşenler-threadler-başlatma-sırası)).
- **Birincil/ikincil hat:** Seçim açılışta ve process genelinde yapılır; çalışma sırasında failover yok. Glimpse TCP bağlantısı birincilde başarısız olursa global bayrak ikincile döner (geri dönmez). Multicast her zaman birincil hattan alınır; ikincil gruba join yok, A/B arbitraj yok ([alim-yolu § 3–4](alim-yolu.md#4-birincilikincil-seçimi)).
- **Glimpse ve canlı tampon:** Canlı paketler Glimpse snapshot'ı bitene kadar tamponlanır (2026-10). Snapshot-end, pazar başına **sabit Partition 1–4** tamamlanınca tetiklenir; partition sayısı config'ten okunmaz ([alim-yolu § 6, § 8](alim-yolu.md#6-glimpse-ve-canlıya-geçiş)).
- **Gap:** Rewinder ile kurtarılır. Kurtarılamazsa partition kalıcı donabilir ([alim-yolu § 5](alim-yolu.md#5-gap-ve-rewinder)).
- **Timestamp:** ITCH `timestamp` / callback `ts` = son `T` (saniye) mesajının içindeki **ns** (uint32, her saniye sıfırlanır). `packetTs` = kernel SW RX zamanı, `CLOCK_REALTIME` epoch ns; Glimpse ve XLIO'da 0. Header/level callback'lerinde alanın domeni olay kaynağına göre değişir ([mesajlar § 3](mesajlar-ve-emir-defteri.md#3-timestamp-modeli)).
- **`header_changed`:** Yalnız best bid/ask **fiyatı** değişince tetiklenir; miktar değişimi level aboneliğinden izlenir ([mesajlar § 7](mesajlar-ve-emir-defteri.md#7-header-ve-kademe-hesabı)).
- **`header_snapshot`:** Abone olunduğu andaki header, kitaptaki bir sonraki add/execute/delete'te teslim edilir; hareketsiz kitapta hiç gelmez ([abonelik-api § 3.3](abonelik-api.md#33-abonelik-fonksiyonları-ve-callback-argümanları)).
- **Momentum (max-size):** Aggressor fill'leri aynı borsa damgasıyla veya `exec_window` (ns) içinde toplanır. `isMaxSizeExecution` **seviye bazlıdır**: toplam eşiği geçince aynı gruptaki her sonraki fill'de 1 gelir, yalnız bir kez değil. `exec_arm_price` mutlak fiyat kapısıdır ([abonelik-api § 5](abonelik-api.md#5-momentum--max-size-ismaxsizeexecution)). Tüketiciler: HFT Classic follow-max, Tavan max-size, Taban momentum girişi.
- **Tiering:** `price_threshold_crossing` + `seed_price_threshold`; callback `false` dönerse geçiş reddedilir ([abonelik-api § 6](abonelik-api.md#6-tiering--fiyat-eşiği-geçişi-orderbookinfoevaluatepricethresholdcallbacks)).
- **Fiyat:** Raw, enstrümanın `DecimalCount`'u ile. Tick tablosu ITCH referans verisinden gelir; `itchsdk_get_tick_size` satır bulamazsa 1, orderbook bilinmiyorsa 0 döner ([mesajlar § 4](mesajlar-ve-emir-defteri.md#4-fiyat-ve-miktar-ölçeği)).
- **Config:** Değerler tüketici servisin config'inden gelir (HFT `[[markets]]`, AlgoProd `$Equity`/`$Derivative`, trade-data-app `itchConfigurations`). Alan tablosu: [abonelik-api § 2](abonelik-api.md#2-itchsdkconfigurations-publicconfigh).

Açık sorunlar: [`ACIK-KONULAR.md`](../../../issues/ACIK-KONULAR.md) § itch-sdk.

## Eski bilinen buglar (K-06, kapandı)

Eski `meeapps-ai` `context-itch-sdk/bugs-quirks.md` listesi 2026-10-22'de güncel koda karşı kontrol edildi. Ayrıntılar alt dosyaların `Şüpheli` bölümlerinde.

| Eski # | Konu | Durum |
|--------|------|-------|
| 1 | HeaderChanged yalnız fiyata bakıyor | Hâlâ var |
| 2 | p99 ingest tail | ❓ ölçüm gerekir |
| 3 | Rewinder sayaçlarında çift sayım | Hâlâ var |
| 4 | `setArguments` zorunlu (Onload/XLIO yeniden başlatma) | Hâlâ var; HFT çağırmıyor |
| 5 | Çalışma anında `EF_*`/`XLIO_*` `setenv` | Kısmen: `execvp` yolunda etkili, preload'la başlatılmış süreçte değil |
| 6 | Kaynak IP / iface uyuşmazlığı sessiz | Kısmen: boş iface/port artık `start` hatası; kaynak IP uyuşmazlığı hâlâ yalnız sayaç |
| 7 | `F` (AddOrderWithMPID) ve `C` (OrderExecutedWithPrice) aynı handler | Kısmen: `C` için specific-order olayında `priceReliable=0` (fiyat hâlâ kitap fiyatı, `order_executed`'da bayrak yok); `F` `len<45` şartıyla tamamen düşebilir ([mesajlar § 2.5](mesajlar-ve-emir-defteri.md#25-f-addorderwithmpid)) |
| 8 | `T`/`P`/`S` düşüyor | `T` düzeltildi; `P`, `S` hâlâ düşüyor (kasıtlı) |
| 9 | Birincil/ikincil yalnız açılışta | Hâlâ var; ek olarak ikincil multicast'e join yok |
| 10 | Snapshot'ta seviye emirleri boş | Düzeltildi (PR #152, sıralı); heap alloc yükü duruyor |
| 11 | `getMarketForPartition`/`getPortForPartition` | Hâlâ var, ölü kod |
| 12 | `findClientForOrderbook` static cache yarışı | Hâlâ var; `cleanup`'ta temizlenmiyor |
| 13 | 2048 bayt üstü paket taşması | POSIX güvenli; ZC ve XLIO yollarında hâlâ var |
| 14 | Client spin döngüsü, pin yok | Spin var; pin artık var (`clientCpuCore`) |
| 15 | `Error` log seviyesi `Warning` oluyor | Hâlâ var |
| 16 | ITCH ts "gün başından ns" | Eski bilgi yanlıştı: saniye içi ns |
| 17 | Bazı parçalar root namespace'te | Hâlâ var: `Globals/UtilityClass.h`, `Globals/Parser.h`, `Public/enums.h`, `Public/config.h`, `Public/spsc_ring_buffer.h` (`Public/itch_sdk.h` C API olduğu için kasıtlı) |

## Build

CMake. Varyantlar: normal, **Onload** (`libMAItchSDK_Onload.so`), Mellanox/XLIO ([alim-yolu § 2](alim-yolu.md#2-recv-modları-ve-derleme-varyantı)). CI `itchsdk.yml` kütüphaneleri Algo-Setup `MAProdEnv/lib`'e yazar. Kütüphane, sürüm bilgisini (`MAItchSDK_BuildInfo`) gömülü taşır. Örnek: `demoApp/smoke_main.cpp`.
