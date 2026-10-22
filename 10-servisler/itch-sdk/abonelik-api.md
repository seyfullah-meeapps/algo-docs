---
kapsam: itch-sdk public API sözleşmesi — C/C++ yüzeyi, yaşam döngüsü, ItchSdkConfigurations, handle modeli, callback'lerin tetiklenme/thread/birim kuralları, level eşik semantiği, momentum (max-size), tiering, referans veri fonksiyonları ve dört tüketicinin bu API'yi nasıl kullandığı
kaynak:
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# itch-sdk — abonelik API'si ve callback sözleşmesi

Özet, sınıf tablosu, build: [README.md](README.md). Bu dosyada olmayanlar:
- UDP alım, demux, SPSC ring, Glimpse, Rewinder, birincil/ikincil hat → [alim-yolu.md](alim-yolu.md)
- ITCH mesaj kataloğu, `OrderDepth` / emir defteri iç yapısı, snapshot'taki emir sırası → [mesajlar-ve-emir-defteri.md](mesajlar-ve-emir-defteri.md)
- HFT'nin olayları stratejilere dağıtması (handle→strateji dizisi, kuyruklar) → [hftsrvprod/itch-entegrasyonu.md](../hftsrvprod/itch-entegrasyonu.md)
- Combiner'ın durum makinesi → [maordersdk/emir-akisi.md § 9](../maordersdk/emir-akisi.md)

Kod: `Public/itch_sdk.h` (C API), `Public/ItchSdk.h` (C++), `Public/config.h`, `Public/enums.h`, `Public/MAItchSDK.h` (şemsiye header), `Clients/SDKItchManager.*` (singleton + `extern "C"` gövdeleri), `OrderBook/OrderbookInfo.*` (orderbook başına callback dizileri ve tetikleme).

**Birim kuralları (bütün dosya için):** fiyatlar **raw `int32`** (TL = raw / 10^`decimalPrice`, bkz. [sozluk.md](../../00-genel/sozluk.md)); miktarlar **lot** (`uint64`); `ts`/`timestamp` adlı `uint32` alanlar **ITCH mesaj damgası = saniye içi ns** (saniye `T` mesajından gelir); `packetTs` **paket alım damgası, ns** (`SO_TIMESTAMPING` HW/SW; XLIO yolunda 0 olabilir, `OrderbookInfo.h` yorumu).

## 1. Yaşam döngüsü

- `SDKItchManager::instance()` süreç başına tek örnek (function-local static). C API'nin her fonksiyonu bu örneğe forward eder. `itch::getItchSdk()` aynı örneği `itch::ItchSdk*` olarak verir.
- Çağrı sırası:

| Adım | Fonksiyon | Ne yapar | Hata |
|------|-----------|----------|------|
| 0 | `itchsdk_set_arguments(argc, argv)` | `argv`'yi **kopyalamadan** saklar. Onload/XLIO build'inde `start()` `LD_PRELOAD` yoksa bununla `execvp` yapar. | Hep `SUCCESS`. Onload/XLIO build'inde çağrılmazsa ve preload yoksa `start()` `NOT_INITIALIZED` (-4) döner. |
| 1 | `itchsdk_initialize(&cfg)` | Config'i **sığ kopyalar** (struct + `MulticastConfiguration` dizisi; `const char*`'lar kopyalanmaz). Onload/XLIO `EF_*`/`XLIO_*` env'lerini `overwrite=0` ile set eder. Logger'ı (`logDirectory`, `logLevel`) açar. | `INVALID_CONFIG` (-1): `cfg` null veya `multicastConfigurationsCount <= 0`. `ALREADY_INITIALIZED` (-3). |
| 2 | `itchsdk_subscribe_snapshot_end(...)` | Pazar düzeyindeki tek abonelik; orderbook'lar henüz yokken açılabilen tek tür (§3.2). | — |
| 3 | `itchsdk_start()` | Ring'ler, receiver'lar, `ItchClient`'lar kurulur ve başlar. **Bütün `ItchClient`'lar Glimpse'i bitirene kadar bloklar** (10 ms poll, `glimpseStartTimeoutMs`). Snapshot-end callback'leri bu çağrı sürerken SDK thread'lerinden gelir. | `CONNECTION_FAILED` (-2): kurulum hatası, bir partition'ın Glimpse'i ölü, veya timeout (`cleanup()` yapılır). `ALREADY_INITIALIZED` (-3): zaten çalışıyor. `NOT_INITIALIZED` (-4). |
| 4 | per-orderbook abonelikler | Snapshot-end'den sonra (§3.2). | — |
| 5 | `itchsdk_stop()` | Client'ları sonra receiver'ları durdurur. Çalışmıyorsa no-op. | Hep `SUCCESS`. |
| 6 | `itchsdk_shutdown()` | `stop` + `cleanup` (ring, client, abonelik haritası, config silinir) + logger kapanır. | Hep `SUCCESS`. |

- Config'teki string pointer'ları SDK ömrü boyunca geçerli kalmalı. HFT (`ConfigurationManager` singleton string'leri), AlgoProd (`internConfigString`, üye `std::string`'ler) ve trade-data-app (`C.CString`, hiç free edilmez) bunu sağlıyor.
- ❓ doğrulanmadı: `stop()` → `start()` (shutdown'suz) yeniden başlatma. `start()` `receiverGroups`'u temizlemeden ekleme yapıyor; desteklendiğini gösteren kod yok.

**`extern "C"` yüzeyi ve cgo:**
- `itch_sdk.h`, `config.h`, `enums.h` saf C'dir (`stdbool.h`, `stdint.h`, `netinet/in.h`). `MAItchSDK.h` C++ arayüzünü (`ItchSdk.h`) yalnız `__cplusplus` altında include eder; bu sayede cgo şemsiye header'ı doğrudan include edebilir (trade-data-app `pkg/itch/itch.c`).
- Callback'ler C fonksiyon pointer'ıdır; userdata parametresi yalnız `itch_on_specific_order_event_fn`'de var. Diğer türlerde çağıran, olayı `subscriptionId` (handle) ile ayırt etmek zorundadır. cgo tarafı bu yüzden `itch.c`'de static C trampoline'ları tanımlar ve onlar `//export`lu Go fonksiyonlarını çağırır.
- Callback'ler SDK'nın kendi C++ thread'lerinden gelir; cgo bu Go'ya geçişleri "yabancı thread"ten callback olarak işler. Go tarafı callback içinde bir channel'a (`itchChan`) yazar; channel doluysa **ITCH decode thread'i bloklanır** (§9).
- Ek export: `itch_subscribe_header_snapshot` (`itchsdk_` önekisiz), header'da yok, `itchsdk_subscribe_header_snapshot` ile aynı. Kullanan bulunmadı.

## 2. `ItchSdkConfigurations` (`Public/config.h`)

Üst düzey alanlar. "SDK varsayılanı" = alan 0/NULL bırakılırsa SDK'nın kullandığı değer (kod). Header yorumundaki "default" değerleri SDK'nın değil tüketicilerin verdiği değerlerdir; fark olan yerde belirtildi.

| Alan | Tip / birim | Anlam | SDK varsayılanı (0/NULL) | Kod |
|------|-------------|-------|---------------------------|-----|
| `multicastConfigurations`, `multicastConfigurationsCount` | dizi, adet | (pazar, partition) başına bir kayıt (aşağı) | zorunlu; 0 → `INVALID_CONFIG` | `initialize` |
| `logDirectory` | yol | Quill dosya sink dizini | `"./logs"` | `Logger/ItchLogger.cpp` `createFileSink` |
| `logLevel` | `ItchSDKLogLevel` | `None/Debug/Info/Error`. **`Error` → Quill `Warning`** (kasıtlı mı belirsiz) | `None` (0) | `ItchLogger.cpp` `mapLevel` |
| `onloadStackName` | string | Onload stack adı (yalnız Onload build) | `"hft-itch"` | `initialize` |
| `mainRingBufferSize` | slot | Partition başına ana SPSC ring | 16384 (`MAIN_RING_SIZE`) | `createSPSCQueues` |
| `rewinderRingBufferSize` | slot | Partition başına rewinder ring | 1024 (`REWINDER_RING_SIZE`) | aynı |
| `receiverCpuCores[4]` | CPU id | Receiver (RX thread) pin'i; receiver'lar (iface, port) çiftinin config'teki **ilk görülme sırasıyla** indekslenir. 5. receiver ve sonrası pinlenmez. | `<= 0` → pin yok | `createReceiversAndClients`, `ItchReceiver::pinToCore` |
| `busyPollUsec` | µs | `SO_BUSY_POLL` | 50 | `ItchReceiver.cpp` |
| `socketRcvBufBytes` | byte | `SO_RCVBUF`/`SO_RCVBUFFORCE` | 64 MiB | aynı |
| `glimpseRetryCount` | adet | Glimpse ek deneme sayısı (toplam = N+1) | **0 = tek deneme** (header "default 3" der; o tüketici değeridir) | `ItchClient::runGlimpsePhase` |
| `glimpseRetryBackoffMs` | ms | Denemeler arası sabit bekleme | 0 = beklemesiz | aynı |
| `glimpseStartTimeoutMs` | ms | `start()` Glimpse bekleme kapısı | 30000 | `SDKItchManager::start` |
| `rewinderRequestTimeoutMs` | ms | Cevap gelmezse aynı isteği yeniden gönderme aralığı (sınırsız tekrar) | 5000 | `ItchClient::initialize` |

`MulticastConfiguration` (kayıt başına):

| Alan | Anlam |
|------|-------|
| `market` | `Spot=1`, `Viop=2` |
| `partition` | `Partition1..`; SDK `partId` = Spot 1–4, VİOP partition+4 ([alim-yolu § 8](alim-yolu.md#8-partition-varsayımları-ve-partid-k-01--ertelendi); yalnız log etiketi) |
| `itchConfiguration.clientConfiguration` | `name`, `ip`/`port` (multicast grubu, **port string**), `secondaryIp`/`secondaryPort` |
| `itchConfiguration.broadcastLocalInterface` | Yerel arayüz IP'si. **Boşsa veya `port` boşsa `start()` başarısız** (`LOG_ERROR` "missing iface or port") |
| `itchConfiguration.sourceIp`, `secondarySourceIp`, `rewinderSourceIp`, `secondaryRewinderSourceIp` | Demux kaynak IP filtresi (`setMarketSourceIps`); eşleşmeyen paket `packetsUnknownSrc`'a sayılır, log yok |
| `rewinderConfiguration` | `clientConfiguration` + `rewinderLocalPort` (string) |
| `glimpseConfiguration` | `clientConfiguration` + `userName`/`password` (`<GLIMPSE_USER>`, `<REDACTED>`) |
| `clientCpuCore` | Decode (`ItchClient`) thread pin'i; `<= 0` → pin yok |

Aynı (iface, port) için aynı pazardan iki kayıt → `start()` başarısız ("duplicate market for receiver"). Ring boyutunun 2'nin kuvveti olduğu **doğrulanmaz** (`spsc_ring_create` `mask = size-1` kullanır).

**Tüketicilerin doldurduğu değerler:**

| Alan | HFT (`ItchSdkClient::startItchSdkClient`) | AlgoProd (`ItchSdkManager::startItchSdkManager`) | trade-data-app (`itch.c` `receiveItch`) |
|------|------------------------------------------|--------------------------------------------------|------------------------------------------|
| Multicast kayıtları | `[[markets]]`, yalnız `on` partition'lar; SDK partition = pazar içindeki `on` sırası ([config.md](../hftsrvprod/config.md#markets)) | `Configuration.ini` `$Equity`/`$Derivative` bölümleri (`marketMap`), partition = bölümdeki sıra; `rewinderLocalPort` yoksa 28000+i (Spot) / 28100+i (VİOP) | JSON `itchConfigurations[]` ([config.md](../trade-data-app/config.md)); `part` yalnız 1–4, diğerleri `Partition1` |
| `rewinderSourceIp` | `sourceIp` ile aynı | `srcIp` ile aynı | **set edilmiyor** (NULL) |
| `clientCpuCore` | `partitions[].clientCore` | `itchClient.clientCpuCore` | 0 |
| log | `path/log`, `logLevel` (`debug`/`info`, diğer → Error) | `logDirectory/`, aynı eşleme | `"."`, `Info` |
| Onload stack | `itchOnloadStackName` | `itchOnloadStackName`, yoksa `"algo-itch"` | `onloadStackName` |
| Ring (ana/rewinder) | 65536 / 16384 (kod sabiti) | `itchMainRingBufferSize`/`itchRewinderRingBufferSize`, vars. 65536/16384 | 65536 / 16384 sabit |
| `receiverCpuCores` | `receiverCpuCores` (vars. -1) | `itchReceiverCpuCore1..4` (vars. -1) | -1 |
| busy poll / rcvbuf | 0 / 0 | `itchBusyPollUsec` / `itchSocketRcvBufBytes` (vars. 0) | 0 / 0 |
| Glimpse retry / backoff / start timeout | 3 / 500 / 30000 | `itchGlimpse*` (vars. 3 / 500 / **60000**) | 3 / 500 / 30000 |
| Rewinder timeout | 5000 | `itchRewinderRequestTimeoutMs` (vars. 5000) | 5000 |
| `set_arguments` | çağırmıyor (HFT `main()` kendi preload'unu yapar) | çağırıyor | çağırıyor |

trade-data-app'in `itchWorkerCount`/`itchTriggerWorkerCount` ayarları SDK'ya geçmez (`receiveItch` `(void)` ile atar; config struct'ında worker alanı yok). [README](README.md) § Config'teki "worker ve trigger worker sayıları" maddesi bu yüzden kodla uyuşmuyor.

## 3. C API

### 3.1 Handle modeli

- `SubscriptionHandle` = `void*`'a cast edilmiş, **1'den başlayan, süreç genelinde monoton artan sayaç** (`nextSubscriptionId`). Bütün abonelik türleri aynı sayacı paylaşır, değer yeniden kullanılmaz. `nullptr` = başarısız.
- SDK tarafında handle havuzu yoktur; sınır orderbook başına **callback slotlarıdır**: tür başına `MAX_CALLBACKS_PER_TYPE = 32` slot (`OrderbookInfo.h`). Header-snapshot dizisi 512 tanımlı ama yalnız ilk 32'si kullanılıyor. Snapshot-end için süreç genelinde 32 slot (`SNAPSHOT_CALLBACK_COUNT`).
- Slotların geri kazanımı türe göre farklı:

| Tür | Unsubscribe sonrası slot | Slot dolunca subscribe |
|-----|--------------------------|------------------------|
| level changed | Geri kazanılır (`occupied`), ama ancak o orderbook'ta en az 2 level-tetikleme geçişi (`LEVEL_RECLAIM_EPOCHS`) olduktan sonra | `nullptr` + `LOG_ERROR` |
| specific order events (combiner) | Hemen geri kazanılır (seqlock) | `nullptr` |
| price threshold | **Geri kazanılmaz** (yalnız `active=false`) | `nullptr` |
| header changed, add, executed, delete, state, equilibrium, specific order executed | **Geri kazanılmaz** | **Geçerli handle döner ama callback hiç gelmez** (dönüş değeri yok sayılıyor) |
| header snapshot | **Geri kazanılmaz**; `removeCallback` bu diziyi hiç taramaz | Geçerli handle, callback yok |
| snapshot end | `unsubscribe` slotu **kapatmaz** (callback gelmeye devam eder) | Geçerli handle, callback yok |

Yani "32" bir eşzamanlılık sınırı değil, çoğu tür için **orderbook başına gün boyu (süreç ömrü) toplam abonelik sınırıdır**. Bkz. Şüpheli.

### 3.2 Ortak kurallar

- **Orderbook önce var olmalı.** Per-orderbook subscribe'lar `getOrderbookInfo(obId)` ile kitabı arar. Kitaplar Glimpse sırasında `OrderBookDirectory` mesajıyla oluşur. Kitap yoksa:
  - `price_threshold_crossing`, `specific_order_events` → `nullptr`.
  - Diğer bütün türler (level dahil) → **geçerli handle döner, hiçbir zaman callback gelmez**. Bu yüzden tüketiciler per-orderbook abonelikleri snapshot-end'den sonra açar.
- Subscribe/update/unsubscribe herhangi bir thread'den çağrılabilir (`subscriptionMutex`). SDK `initialized` kontrolü yapmaz; init'ten önce çağrılırsa kitap bulunamaz (yukarıdaki kural).
- **Callback thread'i:** orderbook'un partition'ının `ItchClient` (decode) thread'i. Aynı orderbook'un bütün callback'leri tek thread'de, sırayla gelir. İstisnalar: snapshot-end (son biten partition'ın `ItchClient` thread'i, `glimpseMutex` altında) ve `itchsdk_seed_price_threshold` (çağıranın thread'i, §6).
- Callback içinde ağır iş yapılmamalı: decode thread'i bloklanır, ring dolar, paket düşer (`packetsDroppedFull`). Callback içinden subscribe/unsubscribe yapılabiliyor (AlgoProd `onHeaderSnapshot` kendini unsubscribe ediyor; snapshot-end içinde subscribe yaygın).
- **Tek olayda tetikleme sırası** (`OrderbookInfo::addOrderDirect` / `executeOrderDirect` / `deleteOrderDirect`): kitap güncellenir → bekleyen header snapshot'ları → order add/executed/delete → specific-order → (header **fiyatı** değiştiyse) price threshold → header changed → level changed.
- `itchsdk_unsubscribe` senkron değildir: o anda başka thread'de çalışan bir tetikleme geçişi callback'i bir kez daha çağırabilir (`fireSpecificOrderEventCallbacks` yorumu).

### 3.3 Abonelik fonksiyonları ve callback argümanları

| Fonksiyon → callback | Ne zaman tetiklenir | Callback argümanları |
|----------------------|---------------------|----------------------|
| `itchsdk_subscribe_snapshot_end(market, cb)` → `itch_on_snapshot_end_fn` | Bir pazarın **Partition1–4'ünün hepsi** Glimpse'i bitirince (`isMarketGlimpseComplete`). Callback dönünce snapshot belleği serbest bırakılır; tüketici kopyalamalı. Ardından o pazarın canlı akışı serbest bırakılır (`marketLiveReleased`), yani callback içinde açılan abonelikler ilk canlı delta'yı kaçırmaz. **`market` parametresi saklanmaz**: her snapshot bütün snapshot-end abonelerine gider (Şüpheli). | `const ItchFullSnapshot*`: `market`, `orderbookCount`, `orderbooks[]`. `isComplete` ve `timestamp` hiç doldurulmuyor (0). `ItchOrderbookSnapshot`: kimlik, `symbol`, `state`, `buyLevels[]`/`sellLevels[]` (`ItchLevelInfo`: `price` raw, `totalQuantity` lot, `side`, `orderCount`, `orders[]` = `orderId`, `quantity`, `price`), header'lar, referans alanları (`longName`, `isinCode`, `currency`, `decimalPrice`, lot boyları, `underlyingId`, `strikePrice`, `expirationDate`, `putCall`, `financialProduct` = `Product` enum). `tickSize` = `getTickSize(0)`'ın `uint16`'ya kesilmiş hali, güvenilmez (§8). |
| `itchsdk_subscribe_header_changed(obId, cb)` → `itch_on_header_changed_fn` | Best bid **veya** best ask **fiyatı** değişince. Yalnız miktar değişimi bu callback'i **tetiklemez** (bkz. §4: miktar için level aboneliği). Flush'ta (0,0) ile. | `newBuyHeader`, `newSellHeader` (raw; taraf boşsa 0), `newBuyHeaderQuantity`, `newSellHeaderQuantity` (lot), `timestamp`: **add kaynaklıysa ITCH saniye-içi ns, execute/delete kaynaklıysa `packetTs`, flush'ta 0** (Şüpheli). |
| `itchsdk_subscribe_header_snapshot(obId, cb)` → `itch_on_header_snapshot_fn` | Tek seferlik. Abone olunduğu andaki header (`atomic_*Header*`) yakalanır, **o orderbook'taki bir sonraki add/execute/delete'te** teslim edilir. Hareketsiz kitapta hiç gelmez. Sonra otomatik silinmez; slot dolu kalır. | Fiyat/miktar subscribe anındaki değer; `timestamp_ns` = subscribe anındaki `system_clock` ns (epoch). |
| `itchsdk_subscribe_order_level_changed(obId, side, qtyThreshold, isBelow, levelCount, maxOrderQty, cb)` → `itch_on_order_level_changed_fn` | §4 | `side`, `changedLevelIndex` (**0 tabanlı**), `changedPrice` (raw), `oldQuantity`/`newQuantity` (lot), `timestamp` (header ile aynı kural), `isMaxSizeExecution`, `couldSweep`, `sideTotalQuantity` (lot) |
| `itchsdk_subscribe_add_order(obId, cb)` → `itch_on_order_add_fn` | Her `A`/`F` mesajı | `side`, `addedQty`, `prx`, `orderId`, `rankingSequenceNumber`, `rankingSequenceTime`, `ts` (ITCH). `packetTs` yok. |
| `itchsdk_subscribe_order_executed(obId, cb)` → `itch_on_order_executed_fn` | Her `E`/`C` mesajı | `side` = **kitaptaki (dinlenen) emrin tarafı**, `executedQty`, `prevHeaderQty` (o tarafın execute öncesi en iyi kademe miktarı), `prx` = dinlenen emrin fiyatı (emir bilinmiyorsa 0; `C`'de gerçek işlem fiyatı okunmaz), `orderId`, `ts`, `packetTs` |
| `itchsdk_subscribe_order_delete(obId, cb)` → `itch_on_order_delete_fn` | Her `D` mesajı; flush'ta kitaptaki her emir için bir tane | `side`, `isHeaderOrder` (emir fiyatı eski best bid'e **veya** best ask'e eşitse 1, taraf ayrımı yok), `prevHeaderQty`, `deletedQty`, `prx`, `orderId`, `ts`, `packetTs`. Bilinmeyen emirde qty/fiyat 0. Flush'ta `prevHeaderQty=0`, `ts=0`, `packetTs=0`. |
| `itchsdk_subscribe_orderbook_state_changed(obId, cb)` → `itch_on_orderbook_state_changed_fn` | `O` mesajı (SDK değişim kontrolü yapmaz; her mesajda gelir). Abonelikte mevcut durum **replay edilmez**. | `newState`, `prevState` (`OrderbookStateType`) |
| `itchsdk_subscribe_equilibrium_price_update(obId, cb)` → `itch_on_equilibrium_price_update_fn` | `Z` mesajı | `availableBid/AskQuantity` (lot), `equilibriumPrice`, `bestBid/AskPrice` (raw), `bestBid/AskQuantity`, son argüman adı `packetTs` ama değeri **ITCH saniye-içi ns** (`parseEquilibriumPriceUpdateDirect`) |
| `itchsdk_subscribe_specific_order_executed(obId, orderId, cb)` → `itch_on_specific_order_executed_fn` | Bu `orderId` execute edilince | `orderbookId`, `orderId`, `side` |
| `itchsdk_subscribe_specific_order_events(obId, orderId, side, cb, userdata)` → `itch_on_specific_order_event_fn` | (`orderId`, `side`) execute veya delete edilince | `userdata` (geri yansıtılır), `eventType` (`EXECUTED=1`, `DELETED=2`; delete cancel mi replace mi ayırt edilemez), `quantity`, `price` (dinlenen emir fiyatı), `priceReliable` (`C` mesajında 0), `timestamp` (ITCH), `packetTs`. Flush delete'lerinde `timestamp=0`. |
| `itchsdk_subscribe_price_threshold_crossing(obId, side, promote, demote, cb)` → `itch_on_price_threshold_crossing_fn` | §6 | `side`, `currentPrice` (raw), `isHot`, `timestamp`; **`bool` döner** |

### 3.4 Güncelleme, kontrol ve dönüş kodları

| Fonksiyon | Etki | Dönüş |
|-----------|------|-------|
| `itchsdk_unsubscribe(h)` | Haritadan siler, slotu §3.1'e göre bırakır | `SUCCESS`; bilinmeyen handle → **`SUBSCRIPTION_FAILED` (-5)** (`NOT_FOUND` değil) |
| `itchsdk_set_callback_enabled(h, enabled)` | Slotu silmeden aç/kapa. Kapalı callback tetikleme döngüsünde atlanır; tür sayacı 0'a inerse döngüye hiç girilmez ("cold strateji maliyetsiz"). Level'da yeniden açma: kademe takibi **o anki kitaba** yeniden tohumlanır (sahte olay üretmez), momentum toplamı ve sweep/max-size kenarları sıfırlanır; zaten açıksa hiçbir şey yapmaz. Threshold'da yeniden açma `isHot`'u yeniden hesaplamaz. | `NOT_FOUND` (-7); snapshot-end → `INVALID_SUBSCRIPTION_TYPE` (-8); kitap/slot yok → `CALLBACK_UPDATE_FAILED` (-9) |
| `itchsdk_update_level_subscription(h, qty, isBelow, levelCount, side)` | Eşik, yön, kademe sayısı, taraf. Kademe takibi **sıfırlanır** (sonraki olayda izlenen her kademe yeniden raporlanır), momentum toplamı ve kenarlar sıfırlanır. `maxOrderQty`/window/arm'a dokunmaz. | -7 / -8 / -9 |
| `itchsdk_update_level_max_order_qty(h, lot)` | Yalnız `maxOrderQty` (atomic) | -7 / -8 / -9 |
| `itchsdk_update_level_exec_window(h, ns)` | Yalnız pencere; **100 ms'ye kırpılır** (`MAX_EXEC_WINDOW_NS`); toplam sıfırlanmaz | -7 / -8 / -9 |
| `itchsdk_update_level_exec_arm_price(h, raw)` | Yalnız fiyat kapısı | -7 / -8 / -9 |
| `itchsdk_seed_price_threshold(h)` | §6 | -7 / -8 / -9 |
| `itchsdk_update_specific_order_subscription(h, orderId)` | `specific_order_executed` aboneliğini başka orderId'ye taşır | -7 / -8 / -9 |
| `itchsdk_update_specific_order_events_subscription(h, orderId, side)` | Combiner replace akışı; callback/userdata korunur | Tür yanlış veya handle yok → -7; slot yok → -9 |

Update'ler `subscriptionMutex` altında ama besleme thread'iyle senkron değildir; atomic olmayan alanlar için bkz. Şüpheli.

## 4. Level aboneliği eşik semantiği (`OrderbookInfo::fireLevelChangedCallbacks`)

Her add/execute/delete/flush sonrası, abonelik başına:

1. **İzlenen kademeler:** abone olunan taraftaki ilk `levelCount` kademe (1 = yalnız best). Her kademe için son teslim edilen (fiyat, miktar) saklanır. Kademe "değişti" = fiyatı veya miktarı saklanandan farklı. İlk olayda saklanan değerler 0 olduğu için dolu her kademe değişmiş sayılır.
2. **Eşik koşulu** (yalnız değişen kademe için): `isBelow=true` → `newQty < quantityThreshold`; `isBelow=false` → `newQty >= quantityThreshold`. Aynı test eski miktara da uygulanır; **yeni veya eski** koşulu sağlıyorsa teslim edilir (eşikten çıkış kenarı da bir kez raporlanır).
   - Sonuç: `isBelow=true` aboneliği "kademe miktarı eşiğin altındayken her değişimi ve eşiğin üstüne çıktığı anı" verir; eşiğin üstünde kalan değişimler gelmez.
   - Kademe 0 olduğunda (taraf boş) fiyat 0, miktar 0 gelir.
3. **Zorla teslim:** değişen bir kademede `isMaxSizeExecution=1` ise eşikten bağımsız teslim edilir (derin kitapta da görülsün diye). `couldSweep` 0→1 geçişinde de değişen kademeler eşiksiz teslim edilir.
4. **Hiç kademe değişmediyse** ama `couldSweep` 0→1 veya `isMaxSizeExecution` 0→1 kenarı varsa: tek bir ek callback, `changedLevelIndex=0`, best kademenin mevcut değeri, `oldQuantity == newQuantity`.

Alanlar:
- `sideTotalQuantity`: abone tarafındaki **bütün** kademelerin toplamı (lot), güncelleme sonrası (`OrderDepth` tutulan toplam, O(1)).
- `couldSweep = (quantityThreshold > 0 && sideTotalQuantity < quantityThreshold)`. Ayrı parametresi yok, `quantityThreshold`'u kullanır. Seviye bazlıdır: koşul sürdükçe her teslimde 1 gelir; yalnız ek (zorla) teslim kenara bağlıdır. Header yorumu buna "falling edge" der (toplamın eşik altına düşmesi); bayrak açısından 0→1 kenarıdır.
- `isMaxSizeExecution`: §5.
- Kademe takip vektörleri `levelCount`'tan büyütülür ama küçültülmez. `levelCount <= 0` geçilmemeli (❓ `LevelCallbackEntry` kurucusu `resize(levels)` yapıyor, negatif değer tanımsız).

## 5. Momentum / max-size (`isMaxSizeExecution`)

Parametreler (abonelik başına): `maxOrderQty` (lot; 0 = kapalı; subscribe'da verilir, `itchsdk_update_level_max_order_qty` ile değişir), `execWindowNs` (ns; vars. 0), `execArmPrice` (mutlak raw fiyat; vars. 0 = kapı yok). SDK limiti feed'den türetemez; tüketici TL tavanını lot'a çevirip verir (HFT `HftClassic::maxOrderQtyAt`, bkz. [itch-entegrasyonu.md §7](../hftsrvprod/itch-entegrasyonu.md)).

**Birikim** (yalnız execute olaylarında ve `execSide == subscribedSide` iken; `execSide` = **execute edilen dinlenen emrin tarafı**, yani satıcı saldırganı ölçmek için `Buy`, alıcı saldırganı için `Sell` tarafına abone olunur):
1. `execAbsNs = currentFeedSecond_ × 1e9 + ITCH saniye-içi ns` (`ItchClient::parseOrderExecutedDirect`; saniye `T` mesajından). Gruplama **yalnız** bununla yapılır, `packetTs` ile değil.
2. `gap = execAbsNs − accumTs` (önceki fill daha yeniyse 0; aboneliğin ilk fill'inde sonsuz).
3. `gap > execWindowNs` → `accumQty = 0` (yeni grup). Sonra `accumTs = execAbsNs`, `accumQty += executedQty`.
   - `execWindowNs = 0`: yalnız **aynı damgalı** fill'ler toplanır (tek saldırgan emrin kitapta birden çok emri yemesi).
   - `> 0`: kayan pencere; aralarındaki boşluk pencereyi aşmayan ardışık fill'ler zincirlenir (SOR'un parçaladığı tek mantıksal emir).
4. **Saniye sınırı:** mutlak ns kullanıldığı için saniyeyi aşan boşluk doğru hesaplanır. ⚠ `itch_sdk.h` (`itchsdk_update_level_exec_window`) ve `OrderbookInfo` içindeki bazı yorumlar hâlâ "uint32 modüler aritmetik" der; bu yorumlar eskidir, kod mutlak ns kullanır.

**Bayrak:** `isMaxSizeExecution = 1` ⇔ bu olay abone tarafında bir execute **ve** `maxOrderQty > 0` **ve** `accumQty >= maxOrderQty` **ve** (`execArmPrice == 0` **veya** abone tarafının güncelleme sonrası best fiyatı `>= execArmPrice`).
- **Seviye bazlıdır, yükselen kenarda bir kez değil:** toplam eşiği geçtikten sonra aynı gruptaki **her** sonraki fill'de 1 gelir. Add/delete olaylarında her zaman 0. Yalnız "hiç kademe değişmediyse ek teslim" kenara bağlıdır (§4 madde 4).
- Arm kapısı yalnız bayrağı kapar, birikimi değil: fiyat kapıya ulaşmadan önceki fill'ler toplamda kalır.
- Kapı yalnız "`>=`" yönündedir (tavan yönü). Taban yönünde "fiyat şu değerin altındayken" ifade edilemez (kasıtlı tasarım, header yorumu "ask tavana N kademe yaklaşınca").
- Sıfırlayan olaylar: `update_level_subscription`, `set_callback_enabled(true)` (kapalıyken), slot yeniden kullanımı (`reinit`: window ve arm da 0'a döner; yeni abone kendi değerlerini yeniden göndermeli). `update_level_exec_window` toplamı sıfırlamaz. Kapalı (`active=false`) abonelik birikim yapmaz.

## 6. Tiering — fiyat eşiği geçişi (`OrderbookInfo::evaluatePriceThresholdCallbacks`)

`itchsdk_subscribe_price_threshold_crossing(obId, side, promotePrice, demotePrice, cb)`; fiyatlar mutlak raw. İzlenen fiyat = `side` tarafının header'ı.

| Bant | Koşul | Hot olur (promote) | Cold olur (demote) |
|------|-------|--------------------|--------------------|
| Tavan yönlü | `promote >= demote` | `price >= promote` | `price < demote` |
| Taban yönlü | `promote < demote` | `0 < price <= promote` | `price <= 0` veya `price > demote` |

`price = 0` (taraf boş) iki yönde de bant dışıdır. `promote` ile `demote` arası histerezis bölgesidir.

- **Değerlendirme anı:** yalnız header **fiyatı** değiştiğinde (add/execute/delete) ve flush'ta (0,0). Yalnız miktar değişimi değerlendirmez. Header-changed callback'inden önce çalışır.
- Durum değişecekse callback çağrılır (`isHot` = yeni durum). **`true` → geçiş kabul**, `isHot` güncellenir. **`false` → reddedilir**, SDK eski durumda kalır ve bir **sonraki header fiyat değişiminde** aynı geçişi yeniden dener (her olayda değil).
- Callback senkron ve decode thread'indedir (HFT doğrudan stratejiye iletir; [itch-entegrasyonu.md §4](../hftsrvprod/itch-entegrasyonu.md)).
- Subscribe anında `isHot` mevcut fiyattan **sessizce** hesaplanır; callback çağrılmaz. Başlangıçta hot olan aboneliğin haberdar olması için:
- `itchsdk_seed_price_threshold(h)`: mevcut fiyat promote bölgesindeyse callback'i `isHot=true`, `timestamp=0` ile **çağıranın thread'inde** çağırır; reddedilirse `isHot=false` kalır, sonraki header değişiminde tekrar tetiklenir. Bölge dışındaysa `isHot=false` yapar, callback yok. Kapalı (`set_callback_enabled(false)`) abonelikte bulunamaz → -9.
- Slot geri kazanılmaz (§3.1): orderbook başına ömür boyu 32 threshold aboneliği; 33.'sü `nullptr`.

## 7. C++ arayüzü (`Public/ItchSdk.h`)

```cpp
namespace itch {
class ItchSdk {               // SDKItchManager bunu uygular
  virtual SubscriptionHandle subscribeSpecificOrderEvents(uint32_t obId, uint64_t orderId, Side side,
                                 itch_on_specific_order_event_fn cb, void* userdata) = 0;
  virtual ItchSdkError updateSpecificOrderEventsSubscription(SubscriptionHandle, uint64_t orderId, Side) = 0;
  virtual ItchSdkError unsubscribe(SubscriptionHandle) = 0;
};
ItchSdk* getItchSdk();        // singleton; init'ten önce de geçerli pointer
}
```

- Yalnız combiner içindir: bu üç metot C'deki `itchsdk_subscribe_specific_order_events`, `itchsdk_update_specific_order_events_subscription`, `itchsdk_unsubscribe` ile aynı koddur.
- MAOrderSDK'ya `setItchSdk(itch::getItchSdk())` ile verilir (HFT `HftMain`, ITCH start'tan sonra). Combiner subscribe/update/unsubscribe'ı **OUCH recv thread'inden** yapar; olaylar `ItchClient` thread'inden gelir ([emir-akisi.md § 9](../maordersdk/emir-akisi.md)).
- Slot modeli: orderbook başına 32 **eşzamanlı** izlenen emir; unsubscribe slotu hemen geri verir. Fire yolu seqlock ile tutarlı anlık görüntü alır; geç gelen olay `orderId`/side kontrolüyle elenir (combiner de ayrıca kontrol eder).
- `T` (açığa satış) tarafı ITCH'te `S` olarak görünür; combiner `side`'ı buna göre verir.

## 8. Referans veri ve durum fonksiyonları

| Fonksiyon | Dönüş | Not |
|-----------|-------|-----|
| `itchsdk_get_tick_size(obId, price)` | `int64` fiyat adımı (raw) | ITCH `L` tablosu (`OrderbookInfo::getTickSize`): `prxFrom <= price <= prxTo` ilk eşleşme. **Orderbook bilinmiyorsa 0**, biliniyor ama fiyat tabloda yoksa **1**. |
| `itchsdk_get_orderbook_symbol(obId)` | `const char*` | `OrderbookInfo` içindeki `std::string`'in `c_str()`'ı; kopyalanmalı, kitap ömrüyle sınırlı. Bilinmeyen → `NULL`. |
| `itchsdk_get_all_orderbook_ids(buf, max)` | yazılan adet | Bütün client'ların `orderbookInfos` anahtarları (sırasız, Spot ve VİOP karışık). `buf` null kontrolü yok. |
| `itchsdk_get_processed_orderbook_count()` / `..._attached_...` | adet | İkisi aynı değeri döner. |
| `itchsdk_is_glimpse_finished(market, partition)` | `bool` | O partition'ın client'ı yoksa `false`. |
| `itch_sdk_get_receiver_metrics(i, &m)` / `..._histogram` | `ItchSdkError` | Receiver indeksi 0..N-1 (§2 sırası). `packetsDroppedFull`, `packetsUnknownSrc` vb. Ayrıntı `alim-yolu.md`. |

- **Varant tipi, dayanak, lot boyları, ondalık** için ayrı getter yoktur; yalnız snapshot-end'deki `ItchOrderbookSnapshot` alanlarından okunur. HFT varant C/P'yi `financialProduct == 14` (`EquityWarrant`) ve `longName`'in sondan 26. karakterinden çıkarır (`ItchSdkClient::cacheWarrantTypes`). Snapshot'taki `putCall` alanı da var ama HFT onu kullanmıyor. ❓ doğrulanmadı: `putCall`'ın varantlarda doğru dolup dolmadığı.
- Snapshot'taki `tickSize` = fiyat 0'daki adım, `uint16`'ya kesilmiş: çok-kademeli tablolarda anlamsız. Gerçek adım için `itchsdk_get_tick_size` kullanılmalı (AlgoProd bu alanı `SnapshotEvent.tickSize`'a kopyalıyor; ❓ AlgoProd'da nerede kullanıldığı incelenmedi).

## 9. Tüketiciler

| Fonksiyon | HFT | AlgoProd | trade-data-app | Combiner |
|-----------|-----|----------|----------------|----------|
| `set_arguments` | — | ✓ | ✓ | — |
| `initialize` / `start` | ✓ | ✓ | ✓ | — |
| `stop` / `shutdown` | var, kapanışta çağrılmıyor | ✓ | — (sonsuz döngü) | — |
| `snapshot_end` | yalnız Spot | config'teki her pazar | Spot ve VİOP (aynı callback) | — |
| `header_changed` | ✓ | ✓ (orderbook başına tek SDK aboneliği, içeride çoğaltılır) | ✓ (her orderbook) | — |
| `header_snapshot` | ✓ | ✓ (tek seferlik, kendini unsubscribe eder) | — | — |
| `order_level_changed` + `update_level_*` (4 fonksiyon) | ✓ | — | — | — |
| `price_threshold_crossing` + `seed` | ✓ (Tavan/Taban) | — | — | — |
| `set_callback_enabled` | ✓ | — | — | — |
| `add_order` / `order_executed` / `order_delete` | yalnız `executed` kullanılıyor (Varant Toplu) | ✓ (her orderbook) | ✓ (her orderbook) | — |
| `orderbook_state_changed` | ✓ (her orderbook) | ✓ (her orderbook) | ✓ | — |
| `equilibrium_price_update` | ✓ (Teorik) | — | ✓ | — |
| `specific_order_executed` (+update) | wrapper var, kullanan yok | — | — | — |
| `specific_order_events` (+update) | — | — | — | ✓ (C++ arayüzü) |
| `get_tick_size` | ✓ | — | ✓ | — |
| `get_orderbook_symbol`, `get_all_orderbook_ids`, `get_processed_orderbook_count` | ✓ | — | — | — |

Farklı kullanımlar / varsayımlar:
- **HFT** ([itch-entegrasyonu.md](../hftsrvprod/itch-entegrasyonu.md)): handle'ı 65536 elemanlı dizide indeks olarak kullanır (SDK sayacının yeniden kullanılmadığına güvenir). Level/threshold API'sinin tek kullanıcısı. Snapshot-end callback'inde yalnız varant cache'i doldurur, strateji yüklemesini ayrı thread'e verir; snapshot pointer'ını kopyalamadan saklayan `ItchSnapshotEndEvent` vardır (hiçbir stratejiye gitmiyor).
- **AlgoProd** (`algoSrc/Managers/ItchSdkManager.cpp`): snapshot'ı derin kopyalar (`internString`, `internOrders`), her orderbook için `ItchSnapshot` olayını yayınlar, sonra 4 canlı aboneliği açar. Snapshot emirlerini kendi `OrderAddEvent` dizisine çevirir (`rankingSequenceNumber` = kademe içi sıra). Header-changed'i iki taraflı v3 olayından tek taraflı v2 olaylarına kendi `HeaderState` farkıyla böler. `expectedMarkets` kadar snapshot-end sayınca tek bir global `ItchSnapshotEnd` yayınlar. Add callback'inde `packetTs` olmadığı için callback anındaki saati kullanır.
- **trade-data-app** (`pkg/itch/itch.c`, `cgo_calls.go`): snapshot-end callback'inde her orderbook için 6 abonelik açar (`is_already_subscribed` ile tekrarsız), `OnSnapshot` ile directory'yi Go'ya verir, snapshot emirlerini `OnAddOrder` olarak **replay eder** (ranking alanları 0). Header-changed'i iki Go çağrısına böler. Executed/delete callback'lerinde fiyat ve `packetTs`'yi atar. Bütün Go çağrıları `itchChan`'a bloklayan yazmadır; Go tüketicisi yavaşlarsa SDK decode thread'i durur.
- **Combiner**: §7. ITCH'in `priceReliable=0` (`C` cross fill) ve `price <= 0` olaylarını atlar; DELETED'i yalnız bilgi olarak alır.

## Şüpheli

1. **Snapshot-end `market` parametresini yok sayıyor (bug).** `SDKItchManager::subscribeSnapshotEnd` `market`'i saklamaz, `fireSnapshotEndToAllSubscribers` her pazarın snapshot'ını bütün abonelere verir. Etki:
   - AlgoProd iki pazar için iki kez abone → her snapshot `onSnapshotEnd`'e iki kez gelir. `completedMarkets` iki kez artar (ilk pazardan sonra global snapshot-end erken yayınlanır), orderbook'lar iki kez yayınlanır, **canlı abonelikler iki kez açılır → her add/execute/delete/state olayı iki kez teslim edilir**. ❓ doğrulanmadı: prod AlgoProd config'inde iki pazarın da açık olup olmadığı.
   - trade-data-app Spot+VİOP açıkken her snapshot iki kez işlenir. Abonelikler tekrarsız ama `OnSnapshot` ve `replay_snapshot_orders` iki kez → aynı emirler iki kez add edilir. ❓ Go tarafının orderId'ye göre tekilleştirip tekilleştirmediği incelenmedi.
   - HFT yalnız Spot'a abone ama callback `snapshot->market`'e bakmıyor; VİOP açılırsa VİOP snapshot'ı da strateji yüklemesini tetikler.
2. **Snapshot-end "Partition1–4'ün hepsi" kuralı (bug?).** `isMarketGlimpseComplete` her iki pazar için sabit {P1..P4} bekler. Bir pazarda 4'ten az partition yapılandırılırsa snapshot-end **hiç gelmez** ve o pazarın client'ları `bufferLiveUntilRelease`'te sonsuza kadar bekler (tampon dolunca paket düşer). `start()` yine başarılı döner (Glimpse bitti). 4'ten fazla partition (HFT VİOP 6 tanımlı) varsa snapshot P1–4 bitince alınır; P5+ hâlâ Glimpse yaparken onların kitapları başka thread'den okunur (veri yarışı). trade-data-app `part > 4`'ü `Partition1` yapar → aynı (receiver, pazar) için ikinci kayıt → `start()` "duplicate market" ile düşebilir.
3. **Sessiz ölü abonelikler.** Kitap yokken veya slot doluyken çoğu subscribe geçerli handle döner ama callback hiç gelmez (§3.1, §3.2). Header, add/exec/delete, state, equilibrium, header-snapshot slotları **geri kazanılmaz**: aynı orderbook'ta gün içinde 32 kez başlatılan bir HFT stratejisi (her start'ta HeaderChanged + HeaderSnapshot) 33. seferde header olaylarını hiç almaz ve "hazır" olmaz; log yok. AlgoProd her `withSnapshot` trigger aboneliğinde header-snapshot slotu tüketir.
4. **Level slot geri kazanımı hareketsiz kitapta durur.** Epoch yalnız o orderbook'ta olay oldukça ilerler; işlem görmeyen kitapta unsubscribe edilen level slotu geri dönmez, 32 dolunca subscribe `nullptr` döner.
5. **Besleme thread'iyle yarışan güncellemeler.** `updateLevelCallback` atomic olmayan alanları (`quantityThreshold`, `isBelow`, `levelCount`, `subscribedSide`) ve `lastPrices`/`lastQuantities` vektörlerini (gerekirse `resize`) çağıranın thread'inde yazar; decode thread aynı anda bu vektörleri geziyor olabilir → tanımsız davranış / olası çökme. `activateLevelEntry`→`reseedLevelCallback` ve `seedPriceThresholdCallback` çağıranın thread'inde `OrderDepth`'i okur. Seed, threshold callback'ini decode thread'iyle **eşzamanlı** çalıştırabilir ve `isHot`'u kilitsiz yazar.
6. **`findClientForOrderbook` static cache.** Fonksiyon içi `static unordered_map`, kilitsiz; HFT komut/loader thread'leri, combiner (OUCH recv thread) ve AlgoProd/trade-data-app snapshot callback'leri aynı anda subscribe edebilir → yarış. `shutdown()` cache'i temizlemez; yeniden `initialize`/`start` sonrası silinmiş `ItchClient*`'lara işaret eder.
7. **Zaman damgası tutarsızlığı.** Header-changed, level-changed ve threshold `timestamp`'i add kaynaklıysa ITCH saniye-içi ns, execute/delete kaynaklıysa `packetTs` (epoch ns), flush'ta 0. HFT bunu "> 2020-01-01 ns ise kullan" ile ayıklıyor; ham değeri kullanan tüketici iki farklı saat alanını karıştırır. Equilibrium'un `packetTs` adlı argümanı aslında ITCH damgası.
8. **`headerSnapshotCallbacks[512]` ilklendirilmiyor.** `initializeCallbackArrays` bu diziye dokunmaz; C++17'de (`CMAKE_CXX_STANDARD 17`) `std::atomic<T*>` dizisi `make_unique<OrderbookInfo>` ile varsayılan ilklendirilir, değeri belirsizdir. Taze heap sayfaları sıfır geldiği için pratikte çalışıyor olabilir. ❓ doğrulanmadı.
9. **Header-changed yalnız fiyata bakıyor.** Eski bug listesindeki #1 hâlâ geçerli: aynı fiyatta miktar değişimi header-changed üretmez. Tasarım kararı gibi duruyor (miktar için level aboneliği var), ama header yorumunda "fiyat veya miktar" beklentisi olan tüketiciler (AlgoProd v2 uyumu, trade-data-app) aynı fiyatta miktar erimesini görmez. ❓ kasıtlı mı doğrulanmadı.
10. **`OrderBookDirectory` tekrarı callback'leri siler.** `parseOrderBookDirectoryDirect` her mesajda yeni `OrderbookInfo` kurup map'e yazar; aynı orderbook için ikinci directory (ör. Glimpse tekrarı) eski nesneyi ve bütün callback slotlarını yok eder, handle'lar sessizce ölür, `getOrderbookSymbol`'den alınmış pointer dangling olur. ❓ doğrulanmadı: canlı akışta veya gün içi Glimpse tekrarında directory gelip gelmediği.
11. **Dönüş kodu tutarsızlığı.** `itchsdk_unsubscribe` bilinmeyen handle'da -5 (`SUBSCRIPTION_FAILED`), diğerleri -7 döner. Unsubscribe slot bulunamasa da `SUCCESS` döner.
12. **Config yorumları koddan farklı.** `config.h`: `glimpseRetryCount` "default 3" (SDK 0'da tek deneme yapar), trade-data-app yorumu `glimpseStartTimeoutMs` "0 = instant timeout" (SDK 0'da 30000 kullanır). Ring boyutunun 2'nin kuvveti olduğu kontrol edilmez.
13. **trade-data-app rewinder kaynak IP'si boş.** `rewinderSourceIp`/`secondaryRewinderSourceIp` set edilmiyor. Rewinder cevaplarının demux'ta tanınıp tanınmadığı `alim-yolu.md` kapsamında. ❓ doğrulanmadı.
14. **`isHeaderOrder` taraf ayrımı yapmıyor.** Delete'te emir fiyatı karşı tarafın best fiyatına eşitse de 1 olur (kitap kesişik değilken pratikte nadir).
