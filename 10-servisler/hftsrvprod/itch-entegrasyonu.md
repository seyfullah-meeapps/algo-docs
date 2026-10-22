---
kapsam: HftSrvProd'un ITCH SDK'yı nasıl kullandığı — başlatma, abonelik tipleri ve strateji eşlemesi, olay dağıtımı (kuyruk/filtre), fiyat ölçeği ve tick size, seans durumu, uptick, hazır olma koşulu, enstrüman bilgisinin kaynağı, kopma davranışı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# HftSrvProd — ITCH entegrasyonu

SDK'nın kendi iç yapısı (thread'ler, Glimpse/Rewinder, momentum mantığı, C API listesi) [itch-sdk/README.md](../itch-sdk/README.md)'dedir; burada tekrar edilmez. Bu dosya HFT tarafını anlatır: `src/Clients/ItchSdkClient.*`, `src/EventDriven/ItchEvents.h`, `src/OrderBook/OrderBookInfo.*`, `src/Clients/ItchManager.*`, `src/Main/HftMain.cpp`.

İlgili başka dosyalar: config anahtarları [config.md](config.md), strateji taban sınıfı ve `processSingleEvent` [strateji-cekirdegi.md](strateji-cekirdegi.md), emirler [emir-yasam-dongusu.md](emir-yasam-dongusu.md), GUI komutları [komutlar-ve-grpc.md](komutlar-ve-grpc.md).

## 1. Başlatma (`ItchSdkClient::startItchSdkClient`)

`HftMain` bunu MAOrderSDK boot'undan **önce** çağırır, çünkü combiner açıksa MAOrderSDK canlı `itch::getItchSdk()` ister. Hata olursa `LOG_CRIT` basılır ve `exit(1)` çağrılır.

Adımlar:
1. `ConfigurationManager::getItchSdkConfigurations()` `[[markets]]` ağacından `MulticastConfiguration` dizisini üretir. Ayrıntı: [config.md → `[[markets]]`](config.md#markets).
2. `ItchSdkConfigurations` struct'ı doldurulur:

| SDK alanı | HFT kaynağı | Not |
|-----------|-------------|-----|
| multicast konfigürasyonları | `[[markets]]` (yalnız `on=true` partition'lar) | |
| log dizini | `path` + `/log` | HFT log'u ile aynı dizin |
| log seviyesi | `logLevel` → `getItchLogLevel()` | `debug`→Debug, `info`→Info, **diğer her şey → Error** |
| Onload stack | `itchOnloadStackName` | OUCH stack'inden (`onloadStackName`) ayrı |
| main / rewinder ring boyutu | sabit kod: 65536 / 16384 slot | config'ten okunmaz (bkz. config.md) |
| `receiverCpuCores[4]` | `receiverCpuCores` | SDK sırayla receiver başına bir core atar |
| busy poll, `SO_RCVBUF` | sabit kod: 0 / 0 | |
| Glimpse retry / backoff / start timeout | sabit kod: 3 / 500 ms / 30000 ms | |
| Rewinder istek timeout | sabit kod: 5000 ms | |

3. `initialize()` → `itchsdk_initialize`. Ardından:
   - `uptickRule` ve `realHotReadyQueue` (env öncelikli) okunur, üyeye yazılır.
   - Strateji yükleyici thread'i (`strat-loader`) açılır.
   - **Yalnızca Spot** için `subscribeSnapshotEnd(Spot)` kurulur. Yükleyici bu abonelikten önce açılır ki ilk istek kaçmasın.
4. `start()` → `itchsdk_start`. SDK, bütün partition'larda Glimpse bitene kadar **bloklar**. Timeout HFT'de sabit 30 s'dir. Bir partition ölürse veya süre dolarsa hata döner ve HFT çıkar.
   - Onload derlemesinde HFT `main()` zaten `LD_PRELOAD` ile kendini yeniden başlatmıştır, bu yüzden SDK'nın kendi re-exec'i devreye girmez.
5. `HftMain` → `initializeGlobalOrderBookStates()`: SDK'nın bildiği **her** orderbook için durum aboneliği açılır (bkz. §6).

`requestStrategyLoadAsync` / `loadStrategiesFromDb`: Spot snapshot-end callback'i, o pazarın son biten partition'ının `ItchClient` decode thread'inde (`glimpseMutex` altında) çalışır; RX thread'i değil ([itch-sdk/alim-yolu § 6.2](../itch-sdk/alim-yolu.md#62-partition-tamamlanması--snapshot-end)). HftSrvProd'daki kod yorumu "receiver thread" der, yanlış. Önce varant tiplerini cache'ler (§8), `glimpseEndProcessed=true` yapar, sonra DB yüklemesini `strat-loader` thread'ine devreder.
- Gerekçe kod yorumundadır: 2026-08-03'te bu iş callback içinde yapıldı, DB fetch'i ve `createStrategy` döngüsü bir partition'ı dakikalarca durdurdu.
- Yükleyici trade-data-app'ten `getStrategySettings` çeker. Her ayar için `CommandFactory::createStrategyCommand` + `StrategyManager::createStrategy(cmd, true)` çağrılır.
- Pas bitince `strategiesLoadedFromDb=true` olur.

## 2. Hazır olma koşulu ve açılış zinciri

| Aşama | Koşul / bekleme | Kod |
|-------|-----------------|-----|
| ITCH hazır | `itchsdk_start` dönene kadar (tüm partition'larda Glimpse bitti) | `ItchSdkClient::start` |
| Snapshot işlendi | `glimpseEndProcessed` (yalnız Spot snapshot-end) | `onSnapshotEndCallback` |
| `ItchManager::start` | `glimpseEndProcessed` true olana kadar 500 ms aralıkla **main thread'de** bekler | `ItchManager.cpp` |
| Strateji yükleme | `strat-loader` thread'i, snapshot-end'den sonra | `loadStrategiesFromDb` |
| OUCH all-orders isteği | Detached thread `strategiesLoadedFromDb`'yi en fazla 300 s bekler, sonra `OuchManager::getAllOrders()` çağırır (süre dolarsa uyarıyla yine çağırır) | `ItchManager::start` |

Gerekçe (kod yorumu): Restart sonrası replay boş strateji haritasıyla yarışırsa replay edilen bütün fill'ler düşer.

Sıra notları:
- GUI gRPC sunucusu (`guiManager.start`) `itchManager.start`'tan önce başlar. Periyodik işler ise ITCH hazır olduktan sonra başlar.
- Strateji başına "hazır" kavramı stratejidedir: header snapshot gelene kadar karar verilmez (`headerSnapshotReceived` / `headerSynced`). Ayrıntı [strateji-cekirdegi.md](strateji-cekirdegi.md).
- Handoff sonrası replay gate ayrıdır: [emir-yasam-dongusu.md](emir-yasam-dongusu.md).

## 3. Abonelik tipleri

Hepsi `ItchSdkClient` üzerinden açılır. SDK handle döner; strateji handle'ı `registerStrategyForHandle(handle, this)` ile kendine bağlar (§4).

| Wrapper | SDK | Kuyruğa giren olay (`ItchEventType`) | Parametreler |
|---------|-----|--------------------------------------|--------------|
| `subscribeHeaderSnapshot(obId)` | `itchsdk_subscribe_header_snapshot` | `HEADER_SNAPSHOT` | İlk best bid/ask fiyat+miktar |
| `subscribeHeaderChanged(obId)` | `itchsdk_subscribe_header_changed` | `HEADER_CHANGED` | |
| `subscribeLevelChanged(obId, side, qtyThreshold, isBelow, levelCount, maxOrderQty=0)` | `itchsdk_subscribe_order_level_changed` | `LEVEL_CHANGED` | Eşik **lot**, `levelCount` kademe sayısı, `maxOrderQty` lot (0 = momentum kapalı) |
| `updateLevelSubscription(h, qty, isBelow, levels, side)` | `itchsdk_update_level_subscription` | — | Eşik değişimi |
| `updateLevelMaxOrderQty(h, lot)` | `..._max_order_qty` | — | Momentum eşiği |
| `updateLevelExecWindow(h, ns)` | `..._exec_window` | — | ns; 0 = yalnız aynı ITCH damgası. ⚠ master'da yok (2026-10-22) |
| `updateLevelExecArmPrice(h, rawPrice)` | `..._exec_arm_price` | — | Raw fiyat; 0 = kapı yok. ⚠ master'da yok (2026-10-22) |
| `subscribePriceThresholdCrossing(obId, side, promote, demote)` + `seedPriceThreshold(h)` | `..._price_threshold_crossing` | **Kuyruğa girmez**, senkron callback (§4) | Raw fiyatlar |
| `setCallbackEnabled(h, bool)` | `itchsdk_set_callback_enabled` | — | Cold stratejinin aboneliklerini susturur |
| `subscribeOrderExecuted(obId)` | `itchsdk_subscribe_order_executed` | `ORDER_EXECUTED` | Taraf, miktar, `prevHeaderQty`, fiyat, orderId, `packetTs` |
| `subscribeEquilibriumPriceUpdate(obId)` | `..._equilibrium_price_update` | `EQUILIBRIUM_PRICE_UPDATE` | Denge fiyatı, eşleşebilir bid/ask miktarı, best bid/ask |
| `subscribeOrderbookStateChanged(obId)` | `..._orderbook_state_changed` | `ORDERBOOK_STATE_CHANGED` | + global durum haritası güncellenir (§6) |
| `subscribeSnapshotEnd(market)` | `..._snapshot_end` | `SNAPSHOT_END` (pratikte hiçbir stratejiye gitmez) | Yalnız `ItchSdkClient` kendisi, Spot |
| `subscribeOrderAdded`, `subscribeOrderDeleted`, `subscribeSpecificOrderExecuted` (+`update...`) | ilgili SDK fonksiyonu | `ORDER_ADDED`, `ORDER_DELETED`, `SPECIFIC_ORDER_EXECUTED` | **Hiçbir strateji kullanmıyor** (4275ccc) |

Ek olarak `TIMER_TRIGGER_CHECK`, ITCH'ten gelmeyen sentetik bir olaydır. Tavan/Taban kendi zamanlayıcısından kendi kuyruğuna koyar.

### Strateji × abonelik

| Strateji (sınıf) | Abonelikler | Doküman |
|------------------|-------------|---------|
| HFT Classic (`HftClassic`) | HeaderSnapshot (ilk snapshot gelince unsubscribe), HeaderChanged, LevelChanged Buy (`buyQtyBarrier`, isBelow, 1 kademe, follow-max-sell için `maxOrderQty`), LevelChanged Sell (`sellQtyBarrier`, follow-max-buy). Parametre değişince `updateLevelSubscription`; başarısız olursa unsubscribe + yeniden subscribe. Header hareket ettikçe `updateLevelMaxOrderQty`. | [hft-classic.md](../../20-stratejiler/hft-classic.md) |
| Tavan (`HftMaxPrice`) | HeaderSnapshot, HeaderChanged, Level Sell melt (`meltLot` veya `meltPercentage`, isBelow), Level Buy cancel (isBelow), Level Buy recover (isBelow=false, `shouldRecover && cancelLotNumber>0`). Momentum: exec window, arm price, maxOrderQty. Tiering: PriceThreshold **Buy** + `setCallbackEnabled`. | [tavan.md](../../20-stratejiler/tavan.md) |
| Taban (`HftMinPrice`) | HeaderSnapshot, HeaderChanged, Level Sell **koşulsuz** (eşik 1e12 → her ask-header değişimi), Level Buy escape (isBelow; gerekince çalışma sırasında açılır). Sell handle üzerinde exec window + maxOrderQty. Tiering: PriceThreshold **Sell** + `setCallbackEnabled`. | [taban.md](../../20-stratejiler/taban.md) |
| Teorik (`HftTheoreticalPrice`) | EquilibriumPriceUpdate (strateji kendisi açar), OrderbookStateChanged (`StrategyManager` start'ta açar, stop'ta kapatır) | [teorik-fiyat.md](../../20-stratejiler/teorik-fiyat.md) |
| Varant (`HftWarrant`) | **Dayanak** üzerinde HeaderChanged. `RemainingLots` kriterinde dayanakta LevelChanged (seçili taraf, eşik 1e8, isBelow → pratikte her değişim). | [varant.md](../../20-stratejiler/varant.md) |
| Varant Toplu (`HftWarrantAdvanced`) | Dayanakta HeaderSnapshot + HeaderChanged. Her aktif varant için OrderExecuted. `kItchDebug=false` olduğu için varant HeaderChanged'i kapalı. `getWarrantType` ile C/P tipi okunur. | [varant-toplu.md](../../20-stratejiler/varant-toplu.md) |

## 4. Olayların stratejilere dağıtımı

```
SDK ItchClient thread ─► ItchSdkClient::on*Callback (static)
   handle → handleToStrategy_[handle] (lock-free atomic dizi, 65536 slot)
   filtre: handle < 65536, strateji kayıtlı, strategy->isRunning
   ─► enqueueStrategyEvent
        realHotReadyQueue && strategy->isHot && worker  ─► AlgoWorker hot-ready kuyruğu
        aksi halde                                        ─► Strategy::enqueueItchEvent (strateji kuyruğu)
AlgoWorker busy-loop ─► strategy->processSingleEvent()  (bkz. strateji-cekirdegi.md)
```

- **Handle eşlemesi:** SDK handle'ı 1'den başlayan, monoton artan bir sayaçtır ve yeniden kullanılmaz. HFT bu sayıyı doğrudan dizi indeksi olarak kullanır.
  - `>= 65536` olan handle'ın olayları sessizce düşer; `register` da no-op olur (bkz. Şüpheli davranışlar).
- **Filtre:** Olay üretilmeden önce yalnızca `strategy->isRunning` kontrol edilir. Orderbook filtresi yoktur, çünkü abonelik zaten orderbook başınadır. Durmuş stratejinin olayı kuyruğa hiç girmez.
- **Strateji kuyruğu:** `moodycamel::ConcurrentQueue<unique_ptr<ItchEventBase>>`, strateji başına bir tane.
  - Yumuşak sınır `strategyQueueMaxEvents` (varsayılan 50000, statik, tüm stratejiler için ortak).
  - Sınır aşılırsa **gelen (yeni) olay düşer**, `droppedItchEvents_` artar. Eski olaylar kuyrukta kalır.
  - `enqueuedAt` PerfSDK için ns damgasıdır.
- **Hot-ready kuyruğu** (`AlgoWorker::enqueueHotReady`, worker başına, sınır 65536):
  - Doluysa olay strateji kuyruğuna döner.
  - Worker olayı `processReadyEvent` ile doğrudan işler. Yalnızca şu koşulların hepsi tutuyorsa: strateji hâlâ hot, çalışıyor, silinmek üzere değil, `eventGeneration` aynı ve **strateji kuyruğu boş** (FIFO bariyeri). Aksi halde olay strateji kuyruğuna konur.
  - `processReadyEvent`'i yalnız Tavan ve Taban override eder. `Strategy` taban sınıfındaki varsayılan uygulama olayı strateji kuyruğuna geri koyar ve `false` döner.
- **Fiyat eşiği (tiering) callback'i senkrondur:** `onPriceThresholdCrossingCallback` doğrudan `strategy->onPriceThresholdCrossing(...)` çağırır, ITCH thread'inde çalışır ve dönüş değeri SDK'ya gider (`false` = geçiş reddedildi, SDK tekrar dener).
  - Strateji yoksa veya durmuşsa `true` döner, böylece SDK durumu piyasayı izlemeye devam eder.
  - Promote/demote mantığı ve eşik hesabı [tavan.md](../../20-stratejiler/tavan.md) ve [taban.md](../../20-stratejiler/taban.md)'dedir.
- **Cold strateji:** `setCallbackEnabled(false)` SDK tarafında callback'i kapatır. Cold strateji ITCH thread'ine de worker'a da maliyet getirmez.
- **Stop:** HFT Classic durunca handle'larını unsubscribe eder ve kuyruğu boşaltır ("stale events"). Tavan, Taban ve Varant Toplu ayrıca `unregisterStrategyForHandle` çağırır.

## 5. Olay alanları, zaman damgası

`src/EventDriven/ItchEvents.h`. Temel alanlar: `eventType`, `orderbookId`, `timestamp` (ns), `enqueuedAt`.

- `timestamp` varsayılan olarak olayın kurulduğu andaki `system_clock` (ns epoch) değeridir.
- `LEVEL_CHANGED` ve `HEADER_CHANGED`: SDK'nın verdiği ITCH zaman damgası 2020-01-01'den (1577836800e9 ns) büyükse o kullanılır, değilse sistem saati kalır.
- `HEADER_SNAPSHOT`: SDK damgası koşulsuz kullanılır.
- `ORDER_ADDED/EXECUTED/DELETED`: `timestamp` sistem saatidir. ITCH damgası ayrı `ts` (uint32, ITCH mesaj damgası) ve `packetTs` (uint64) alanlarında taşınır. `ts` = son ITCH `T` saniyesi içindeki ns (uint32, her saniye sıfırlanır); `packetTs` = kernel SW RX zamanı, `CLOCK_REALTIME` epoch ns, Glimpse ve XLIO'da 0 ([itch-sdk/mesajlar § 3](../itch-sdk/mesajlar-ve-emir-defteri.md#3-timestamp-modeli)).
- `LEVEL_CHANGED` ek alanları: `changedLevelIndex`, `changedPrice` (raw), `oldQuantity`/`newQuantity` (lot), `isMaxSizeExecution` (momentum; seviye bazlı, eşik geçilince gruptaki her fill'de 1 — [itch-sdk/abonelik-api § 5](../itch-sdk/abonelik-api.md#5-momentum--max-size-ismaxsizeexecution)), `couldSweep` (taraf toplamı eşiğin altında), `sideTotalQuantity` (lot). Anlamları: [itch-sdk → Abonelik API'si](../itch-sdk/README.md).
- Stratejiler dwell/cooldown hesabında ITCH damgasını değil `hft::perf::nowNs()` (steady clock) kullanır, çünkü epoch'lar farklıdır (Tavan kod yorumu).

## 6. Orderbook durumu ve seans

İki ayrı yapı vardır.

1. **Global durum haritası** (`ItchSdkClient::globalOrderbookStates_`, `unordered_map<obId, atomic<OrderbookStateType>>`):
   - `initializeGlobalOrderBookStates` haritayı SDK'nın bildiği bütün orderbook'larla doldurur. **Başlangıç değeri `SurekliMuzayede`'dir** (kod yorumu "Other" diyor). Her orderbook için `subscribeOrderbookStateChanged` açılır. Bu handle'lar stratejiye bağlanmaz.
   - Her durum callback'i haritayı günceller. Bu, Teorik stratejinin kendi aboneliği için de geçerlidir.
   - `getOrderbookState(obId)`: haritada olmayan orderbook için `Other` döner.
   - `isOrderbookContinuousSession(obId)`: durum `SurekliMuzayede` veya `ViopSurekliMuzayede` ise true. `Strategy::continuousSession()` bunu çağırır. HFT Classic sürekli müzayede dışında bazı akışları atlar.
   - Durum değerleri (SDK `OrderbookStateType`): `Other`, `AcilisEmirToplama`, `SurekliMuzayede`, `ViopSurekliMuzayede`, `Eslestirme`, `KapanisEmirToplama`. Seans saatleri: [borsa-kurallari.md](../../00-genel/borsa-kurallari.md).
   - `morningGathering_` / `eveningGathering_` bayrakları callback'te set edilir ve sıfırlanır ama hiçbir yerde okunmaz. "cancelGatheringOrders / reverseGatheringOrders" yalnızca yorum olarak duruyor.
2. **Strateji başına `OrderBookInfo`** (`src/OrderBook/`, `Strategy::orderbookInfo`, `shared_ptr`):
   - Fiilen yalnızca `symbol` (ITCH'ten), `orderbookId`, `tavanPrice`/`tabanPrice` (`updateLastDayVariables`'tan) yazılır.
   - `updateHeaders`, `updateState`, `updateEquilibriumPrice`, `setUptickRule`, `updateLevel` **hiçbir yerden çağrılmaz**. Header, state ve equilibrium alanları hep 0 / `Other` kalır, `continuousSession` hep true kalır.
   - Header ve kademe durumu stratejinin kendi `localOrderbook`'undadır ([strateji-cekirdegi.md](strateji-cekirdegi.md)).

## 7. Fiyat ölçeği ve tick size

- ITCH'ten gelen bütün fiyatlar **raw int32**'dir: enstrümanın `decimalCount` ölçeğinde tam sayı, TL = raw / 10^decimalCount. Tanım: [sozluk.md → Raw fiyat](../../00-genel/sozluk.md). HFT ITCH fiyatlarını hiç dönüştürmez; strateji, emir ve eşik değerleri hep raw'dır.
- Miktarlar lot'tur (uint64).
- `getTickSize(obId, rawPrice)` → `itchsdk_get_tick_size`: verilen fiyattaki fiyat adımı (raw, int64). Tablo ITCH referans verisinden gelir. **Orderbook bilinmiyorsa 0 döner.** Çağıranların çoğu 0'ı kontrol etmez (HFT Classic fiyat ± tick hesapları, GUI manuel çok kademeli emir). Tiering `max(1, tick)` kullanır. Tavan/taban fallback'i 0'ı kontrol eder.
- `decimalPrx` = 10^`decimal_count`. trade-data-app'ten gelir (`OuchManager::getInstrumentDecimalPrice`), ITCH'ten gelmez.
  - `maxOrderValue` tam TL'dir. Lot'a çevirmek için: `maxOrderValue × decimalPrx [× %] / rawPrice` (`HftClassic::maxOrderQtyAt`).
- Tavan/taban (`Strategy::updateLastDayVariables`):
  - Önce trade-data-app `min_price`/`max_price` kullanılır (raw; trade-data-app bunları VERDA'dan ×1000 yazar, bkz. [trade-data-app/veri-akisi.md](../trade-data-app/veri-akisi.md)).
  - İkisinden biri 0 ise fallback: `lastPrice×1.10` / `×0.90`, ITCH tick'ine yuvarlanır (tavan aşağı yuvarlanır, taban yukarı bir tick eklenir).
  - Tick 0 ise tavan = taban = `lastPrice` olur.

## 8. Enstrüman bilgisinin kaynağı

| Bilgi | Kaynak | HFT erişimi |
|-------|--------|-------------|
| Orderbook id listesi, sembol | ITCH (Glimpse sonrası SDK) | `getAllOrderbookIds`, `getOrderbookSymbol` |
| Fiyat adımı tablosu | ITCH | `getTickSize` |
| Seans durumu | ITCH | §6 |
| Varant tipi C/P | ITCH Spot snapshot: `financialProduct==14` ve `longName`'in sondan 26. karakteri | `cacheWarrantTypes` / `getWarrantType` (0 = bilinmiyor). ⚠ master'da yok (2026-10-22) |
| Önceki kapanış (`last_price`), tavan/taban (`min_price`/`max_price`), `max_order_val` (TL), `decimal_count`, `is_brut_takas`, pazar, partition, `financial_product` | trade-data-app `AlgoService.GetAllInstruments` | `DatabaseServiceClient::getInstruments` |
| Varant dayanağı (`underlyingInstrumentId`) | GUI komutu | strateji command'ı |

- trade-data-app listesi açılışta iki kez çekilir:
  - `HftMain` → `maosdk->setInstrumentLimits` (max emir değeri, ondalık, brüt takas).
  - `OuchManager` yapıcısı → `fillAllInstruments` (`instrumentMap`, `obidToDecimalPrice`, `obidToMaxOrderValue`, `obidToBrutTakas`).
- Gün içinde **yenilenmez**.
- `isBrutTakas` bilinmeyen orderbook için `true` döner (güvenli taraf).
- `getInstrumentLastPrice` `operator[]` kullanır; bilinmeyen orderbook için haritaya boş kayıt ekler.

## 9. Uptick

- `ItchSdkClient::hasUptickRule(obId)` orderbook'a bakmaz, config'teki **global** `uptickRule`'u döner. `setUptickRuleEnabled` var ama çağıran yok.
- Kullanan yalnızca HFT Classic'tir (bait ve chase emirlerinde taraf/fiyat seçimi, `UtilityClass` yardımcısı). Davranış: [hft-classic.md](../../20-stratejiler/hft-classic.md).
- `uptickEnabled` ayrı bir anahtardır, yalnız konsol durum kutusunda "Uptick: ON/OFF" olarak görünür. Konsoldaki "Uptick" satırı **gerçek kuralı (`uptickRule`) göstermez**.
- BIST'te açığa satış kuralı enstrüman bazlıdır ([borsa-kurallari.md](../../00-genel/borsa-kurallari.md)). HFT bunu ITCH'ten okumaz.

## 10. Kopma, gap, hat değişimi (HFT'nin gördüğü kadarıyla)

- HFT'ye **gap, Rewinder kurtarma, Glimpse tekrarı veya hat değişimi bildiren bir callback yoktur**. Sequence takibi, Rewinder ve birincil/ikincil hat seçimi tamamen SDK içindedir ([itch-sdk → Glimpse ve Rewinder](../itch-sdk/alim-yolu.md#5-gap-ve-rewinder)). Hat seçimi yalnız açılışta yapılır.
- Kurtarma sırasında olaylar gecikir, stratejinin `localOrderbook`'u eski kalır. HFT tarafında bayatlık (staleness) kontrolü yoktur. ❓ doğrulanmadı: SDK Rewinder sırasında callback'leri tutuyor mu yoksa kurtarılan mesajları sırayla mı akıtıyor.
- Açılışta Glimpse 30 s içinde bitmezse ITCH başlatma başarısız olur ve process `exit(1)` ile çıkar. Gün içinde yeniden bağlanma HFT'nin kontrolünde değildir.
- SDK ring taşması (`packetsDroppedFull`) HFT'ye yansımaz; yalnız PerfSDK metriklerinde görünür ([performance-sdk](../performance-sdk/README.md)).
- Strateji kuyruğu taşması `droppedItchEvents_`'e yazılır. Bu sayacı okuyan tek yer `AlgoWorker`'ın 5 s'lik raporudur ve o `LOG_INFO` **yorum satırında**. Yani drop'lar log'da görünmez.
- Snapshot-end yeniden tetiklenirse (SDK market'in bütün partition'ları tekrar tamamlanınca yeniden yayınlıyor) DB'den strateji yükleme pası tekrar çalışır. ❓ doğrulanmadı: gün içinde tekrar Glimpse olup olmadığı ve `createStrategy`'nin var olan `unique_key` için ne yaptığı.

## 11. Kullanılmayan / ölü kod

- `src/Messages/IncomingMessages/Itch/**` (AddOrder, OrderExecuted, OrderBookState, TickSizeTable, OrderBookDirectory …) **CMake'e dahil değil**. Eski kendi-ITCH parser'ından kalmadır. Yalnız `EquilibriumPriceUpdate.h` header'ı `ItchSdkClient.cpp`'de include ediliyor, o da kullanılmıyor.
- `Hft::ItchManager`:
  - Partition başına `MulticastClient(nullptr)` oluşturur ama kullanmaz.
  - `addUnderlyingOrderbookInfo` / `getUnderlyingOrderbookInfo` için çağıran yok.
  - `stop()` boş.
- `ItchSdkClient::stop/shutdown` kapanışta çağrılmıyor (`performShutdown`'da "crashes program" yorumu). Process `exit(1)` ile bitiyor.
- `ItchSdkClient::setOn*` callback setter'ları ve `on*_` std::function üyeleri hiç set edilmiyor. Dağıtım static callback'lerden doğrudan yapılıyor.

## Şüpheli davranışlar / uyumsuzluklar (koddan)

- **Handle tavanı 65536:** SDK handle'ı monoton artan sayaçtır ve yeniden kullanılmaz.
  - Açılışta orderbook sayısı kadar durum aboneliği handle tüketir.
  - Her strateji start'ı ve HFT Classic'in her eşik-fallback resubscribe'ı yeni handle alır.
  - Sayaç 65536'yı geçerse yeni aboneliklerin olayları **sessizce** düşer (`registerStrategyForHandle` no-op, callback'te indeks kontrolü). Log yok. Uzun süre çalışan ve sık restart edilen stratejilerde risk. ❓ doğrulanmadı: günlük handle tüketimi.
- **Unregister eksikliği:** HFT Classic, Varant ve Teorik stop'ta `unsubscribe` yapıyor ama `unregisterStrategyForHandle` yapmıyor. Handle yeniden kullanılmadığı için yanlış stratejiye olay gitmez. Ancak slot strateji pointer'ını tutmaya devam eder; strateji silinirse dangling pointer kalır. Bu pointer, SDK geç bir callback teslim ederse okunur. ❓ doğrulanmadı.
- **Teorik restart:** `setCommand` her "started" komutunda yeni bir equilibrium aboneliği açıyor, eski handle'ı kapatmıyor. Stop'ta `unsubscribe` var, `unregister` ve handle sıfırlama yok.
- **README çelişkisi — kuyruk drop politikası:** [README](README.md) ve toml yorumu "eski/stale olaylar düşürülür" diyor. Kod (`Strategy::enqueueItchEvent`) **yeni gelen olayı** düşürüyor.
- **Başlangıç seans durumu:** Global harita `SurekliMuzayede` ile başlıyor ve durum abonelikleri Glimpse bittikten sonra açılıyor. Gün içi restart'ta ilk durum değişimine kadar her orderbook sürekli müzayedede sayılır; örneğin kapanış emir toplamada restart edilirse yanlış olur. ❓ doğrulanmadı: SDK abonelikte mevcut durumu replay ediyor mu.
- **Veri yarışı adayı:** `globalOrderbookStates_` (`unordered_map`) main thread'de abonelikler açılırken dolduruluyor. Aynı anda ITCH thread'i callback'te `find` yapabilir. Ekleme sırasında rehash olursa tanımsız davranış.
- **Yalnız Spot snapshot-end:** `glimpseEndProcessed` ve strateji yüklemesi yalnız Spot snapshot'ına bağlı. Spot'un kapalı olduğu (yalnız VİOP) bir kurulumda `ItchManager::start` sonsuza kadar bekler. Bütün mevcut config'lerde Spot açık, VİOP kapalı.
- **Snapshot pointer'ı:** `ItchSnapshotEndEvent` ham `ItchFullSnapshot*` saklıyor. SDK callback dönünce snapshot'ı serbest bırakıyor (`cleanupSnapshot`). Şu an bu olay hiçbir stratejiye gitmediği için zararsız, ama kullanılırsa use-after-free olur.
- **`OrderBookInfo` header'ı hiç güncellenmiyor:** Tavan `shouldCancelPositionViaVolume` içinde `tavanPrice != orderbookInfo->getBuyHeader()` (hep 0) kontrol ediyor. Bu dal her zaman true dönüyor. Ayrıca fonksiyonun son dalında `return` yok (tanımsız davranış). Ayrıntılı inceleme [tavan.md](../../20-stratejiler/tavan.md)'ye ait.
- **`getTickSize` 0 dönüşü:** Bilinmeyen orderbook'ta 0 döner. HFT Classic ve GUI çok kademeli emir hesaplarında kontrol yok; tick 0 olursa bütün kademeler aynı fiyata düşer. 0 kontrolü yalnız tavan/taban fallback'inde ve tiering'de (`max(1, tick)`) var.
- **Kod yorumu ile davranış farkı:** HFT Classic `setupInitialSubscriptions`'daki "MELT … üstü (isBelow = false)" yorumu, kodda `isBelow=true`. HftMain'deki "setItchSdk çağrısı kaldırıldı" yorumu ise hemen altında `maosdk->setItchSdk(...)` çağrısıyla çelişiyor.
- **ITCH log seviyesi:** `logLevel=warn` gibi bir değer Quill'de Warn olur ama ITCH SDK'da Error'a düşer. İki log aynı seviyede değildir.
