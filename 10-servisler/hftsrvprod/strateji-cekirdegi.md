---
kapsam: HftSrvProd strateji çekirdeği — Strategy taban sınıfı, StrategyManager (registry, yaşam döngüsü, replay gate, periyodik işler, durum push), AlgoWorker thread modeli, hot/cold, kuyruklar, kilitler, açılış/durdurma/restart senaryoları
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# Strateji çekirdeği

Bu dosya bütün HFT stratejilerinin üzerinde koştuğu ortak altyapıyı anlatır. Servisin genel özeti [README.md](README.md)'de, strateji mantığı [`20-stratejiler/`](../../20-stratejiler/README.md)'de. Komut/gRPC ayrıntısı için [komutlar-ve-grpc.md](komutlar-ve-grpc.md), emir yaşam döngüsü ve handoff için [emir-yasam-dongusu.md](emir-yasam-dongusu.md), ITCH abonelikleri için [itch-entegrasyonu.md](itch-entegrasyonu.md), config anahtarları için [config.md](config.md).

Kod: `src/Strategy/Strategy.{h,cpp}`, `src/Strategy/StrategyDepth.*`, `src/Strategy/StrategyLevel.*`, `src/Managers/StrategyManager.*`, `src/Workers/AlgoWorker*.*`, `src/EventDriven/ItchEvents.h`, `src/Globals/Enumarations.h`.

## 1. `Strategy` taban sınıfı

Soyut sınıftır. Somut sınıflar: `HftClassic`, `HftMaxPrice` (Tavan), `HftMinPrice` (Taban), `HftTheoreticalPrice`, `HftWarrant`, `HftWarrantAdvanced`. Hepsi `std::shared_ptr<Strategy>` (`StrategyPtr`) olarak tutulur. `StrategyFactory.h` boş bir singleton'dır; fabrika görevini `StrategyManager::createStrategy` üstlenir.

### Üyeler

| Grup | Üye | Not |
|------|-----|-----|
| Kimlik | `uniqueKey`, `account`, `strategyIdentifier`, `strategyType` (`ouchSDK::enums::StrategyType`), `hftType` (`hft::enums::HftType`), `strategyInfo` (obid + hesap + id + tip), `summaryKey` = `"SUMMARY_" + account` | `uniqueKey` komuttan gelir (bkz. §2) |
| Komut | `command` (`BaseStrategyCommandPtr`) | Son uygulanan parametre seti. `setCommand` bunu değiştirir. |
| Durum bayrakları | `isRunning`, `isHot`, `markedForDeletion`, `sent`, `chaseSent`, `autoCloseWaitingAccept` (hepsi `std::atomic_bool`) | §1 "Durum" |
| Pozisyon | `balance` (lot, işaretli), `profit` (nakit akışı: Σ satış qty×fiyat − Σ alış qty×fiyat), `net` (balance 0 olduğunda `profit`'e eşitlenir), `openLots` (FIFO lot kuyruğu), `realizedProfit` | Fiyatlar raw tamsayı fiyat, TL değil. `getOpenCost()` = Σ lot qty×fiyat. |
| Fiyat bilgisi | `tavanPrice`, `tabanPrice`, `lastPrice`, `buyHeaderLevel`, `sellHeaderLevel`, `orderbookInfo`, `symbol` | `updateLastDayVariables` doldurur (aşağıda) |
| Yerel defter | `localOrderbook` (`LocalOrderbook`: header fiyat/miktarı + `std::map` fiyat→miktar seviyeleri) | ITCH header/level olaylarıyla güncellenir. `isConsistent()` header ile seviyelerin uyumunu kontrol eder. |
| Emirlerimiz | `orderMap` (`token → Hft::OrderAccepted*`), `buyDepth` / `sellDepth` (`StrategyDepth`), `replacedPriceMap` | Pointer'ların sahibi strateji değildir; `OrderRegistry` sahiplenir (bkz. [emir-yasam-dongusu.md](emir-yasam-dongusu.md)). |
| Hazır emir şablonları | `buyInfoOrder`, `sellInfoOrder` (`Hft::EnterOrder`) | `closePosition` bunları kullanır |
| Kilit | `buySellInfoMutex` (`std::recursive_timed_mutex`) | Tek strateji kilidi. Strateji-özel ek kilitler strateji dokümanlarında. |
| Worker | `algoWorker` (raw `AlgoWorker*`) | `AlgoWorker::addStrategy` set eder |
| Pozisyon kapatma | `pendingCancelTokens`, `waitingForCancelCompletion`, `closePositionInProgress` | §1 "Ortak yardımcılar" |
| ITCH kuyruğu | `itchEventQueue_` (`moodycamel::ConcurrentQueue<unique_ptr<ItchEventBase>>`), `queuedItchEvents_`, `droppedItchEvents_`, `eventGeneration_`, statik `s_itchEventQueueMaxEvents` (varsayılan 50000) | §3 |
| ITCH abonelikleri | `itchClient_` ve `*Handle_` alanları (`levelChangeHandle_`, `headerChangeHandle_`, …, `orderbookStateHandle_`) | Çoğu alt sınıf kendi handle alanlarını kullanır. Ayrıntı [itch-entegrasyonu.md](itch-entegrasyonu.md). |

`StrategyDepth` fiyat → `StrategyLevel` eşlemesi tutar (`unordered_map`). `StrategyLevel` ise o fiyattaki `OrderAccepted*` listesini ve `totalQuantity` değerini tutar. Execute geldiğinde `totalQuantity` düşer, emir listeden **çıkarılmaz**; çıkarma `deleteOrder(order, executed=true)` ile yapılır. Seviyenin miktarı 0'a inince seviye silinir. Yardımcılar: `getTotalQuantity(level)` (−1 = bütün seviyeler), `getUpperQuantity` / `getLowerQuantity` (sınır dahil), `hasSecOrder` (seviyede `SecondRule` emri var mı), `updateCumulativeOrders(baseLot, headerLevel)`. Sonuncusu header seviyesi dışındaki seviyelerde base lot'u aşan algo emirlerini replace veya cancel ile kırpar. **Kendi kilidi yoktur**; çağıran stratejinin kilidi tutması beklenir.

### Sanal metodlar ve alt sınıf sözleşmesi

| Metod | Saf mı | Kim çağırır / hangi thread | Beklenen davranış |
|-------|--------|----------------------------|-------------------|
| `setCommand(cmd)` | evet | gRPC (`GUIManager::dispatchStrategy`) | Parametreleri uygula, `isStarted()`'a göre başlat/durdur, `StrategyManager::setStrategyRunningState` çağır. Kilit alınamazsa `false` dön → gRPC `RESOURCE_EXHAUSTED`. HftClassic 100 µs, HftMaxPrice/HftMinPrice 500 ms dener. |
| `processSingleEvent()` | evet | AlgoWorker | `isRunning` ve `ouchReplayComplete()` kontrolü, ardından kuyruktan **tek** olay al ve işle. İşlediyse `true` dön. |
| `processItchEvent(ev)` | evet | (doğrudan işleme yolu) | Alt sınıflar `processItchEventTimed`'a yönlendirir |
| `processReadyEvent(ev)` | hayır | AlgoWorker (hot-ready yolu) | Varsayılan: olayı kendi kuyruğuna geri koy, `false` dön. Yalnız `HftMaxPrice` ve `HftMinPrice` override eder ve olayı doğrudan işler. |
| `onPriceThresholdCrossing(...)` | hayır (varsayılan `true`) | ITCH SDK thread'i | Tavan/Taban hot↔cold geçişi. `false` dönerse SDK geçişi reddeder ve sonraki güncellemede yeniden tetikler. |
| `addOrder` / `rejectOrder` / `updateOrder` / `executeOrder(ev, side)` / `deleteOrder(ev, side)` / `deleteBaseOrder(acc, executed)` | evet | OUCH recv thread'i (combiner açıkken `executeOrder` ITCH thread'inden de gelebilir) | `orderMap` ve depth'i güncelle, pozisyonu `updatePosition` ile işle. HftClassic bunları **bloklayan** `lock_guard` ile kilitler. |
| `addSecondRuleOrder(acc)` / `sendSecondRuleOrder(acc)` | hayır (boş) | `addSecondRuleOrder`: OUCH thread'i, `addOrder`'dan hemen sonra. `sendSecondRuleOrder`: periodic jobs thread'i | §2 "Periyodik işler" |
| `initializeItchSubscriptions` / `cleanupItchSubscriptions` | hayır (boş) | `StrategyManager::startStrategy` / `stopStrategy` | Çoğu strateji abonelikleri `setCommand` içinde kendisi kurar (ör. `HftClassic::setupInitialSubscriptions`). |
| `stop()` | hayır (boş) | Stratejinin kendisi (tolerans aşımı vb. öz-durdurma) | Alt sınıfa özgü |
| `cancelAllOrders(side, notify)` | hayır | gRPC (cancel-all, close position) | §1 "Ortak yardımcılar" |
| `hasCancelableOrders()` | hayır | `StrategyManager::cancelAllStrategyOrders` | Varsayılan: depth'te miktar var mı. Depth tutmayan strateji override eder. |
| `userOrderBlockReason(obid, side)` | hayır (boş string) | Manuel emir yolu | Boş olmayan dönüş GUI emrini engeller |
| `setBidInfoQuantity` / `setAskInfoQuantity`, `updateBuySellQuantities` | hayır | strateji içi | HftClassic miktar hesabı ([hft-classic.md](../../20-stratejiler/hft-classic.md)) |
| `updatePosition`, `setBalance`, `sendBalanceUpdate`, `continuousSession`, `updateLastDayVariables`, `updateCumulativeOrders` | hayır | çeşitli | aşağıda |

Yeni strateji eklerken kontrol listesi: [README.md → Yeni strateji eklemek](README.md#yeni-strateji-eklemek-kontrol-listesi).

### Ortak yardımcılar

- **`updatePosition(side, price, qty)`**: BUY ise `balance += qty` ve `profit -= qty×price`; diğer bütün taraflar (SELL, SHORT_SELL) için tersi uygulanır. FIFO lot eşleştirmesi ters yöndeki lotları kapatır ve `realizedProfit`'i günceller, kalan miktar yeni lot olarak açılır. Lot toplamı `balance` ile tutmazsa WARN "lot base out of sync" yazılır. Metod kilit almaz.
- **`setBalance(side, price, qty)`**: Kilidi alır, `updatePosition` + `updateBuySellQuantities` çağırır. GUI'deki SetBalance komutu bunu kullanır (`GUIManager::dispatchBalance`). Bakiye **mutlak olarak set edilmez**, gelen değer fill gibi eklenir.
- **`sendBalanceUpdate()`**: `SetBalanceCommand` (balance, profit, realizedProfit, openCost) üretip `StrategyServiceImpl::enqueueCommand` ile GUI stream'ine koyar.
- **`cancelAllOrders(side, notifyWhenComplete)`**: Kilidi alır, `orderMap`'teki kalan miktarı > 0 olan emirleri iptal eder. Taraf eşleşmesi XOR ile yapılır: `side ^ orderSide` 17 (`B`/`S`) veya 22 (`B`/`T`) **değilse** iptal edilir; böylece `S` istendiğinde `T` (açığa satış) emirleri de iptal edilir. İptal, emir gönderme deseniyle MAOrderSDK'ya, olmazsa order-service'e gider. `notify` açıksa token'lar `pendingCancelTokens`'a yazılır. `onCancelResponse(token)` (OUCH thread'i, cancel veya reject geldiğinde) son token düşünce `cancelAllOrdersFinished` → `closePosition` çağırır.
- **`closePosition()`**: `balance > 0` ise **taban fiyatından** SELL, `< 0` ise **tavan fiyatından** BUY gönderir (`QtyBarrier` tipi, DAY, limit). Kilit almaz ve replay gate'e bakmaz.
- **`getOrderQuantity(side, level)`**: HftClassic pozisyonsuz miktar hesabı. `sent || chaseSent` ise 0 döner. Komutu `HftClassicCommand`'a cast eder; `getSecondRuleDuration()` da aynı cast'i yapar. İkisi de yalnız HftClassic için anlamlıdır.
- **`updateLastDayVariables()`** (constructor'da çağrılır): `lastPrice` OuchManager enstrüman cache'inden okunur. Tavan/taban trade-data-app'in `max_price`/`min_price` değerleridir. Bu değerler yoksa `lastPrice` ±%10 alınır ve tick'e yuvarlanır (taban bir tick yukarı). Enstrüman cache'te yoksa LOG_CRIT yazılır ve tavan/taban **set edilmez**.
- **`checkAndSetSent(customerInfo)`**: Reject sonrası "gönderildi" kilidini çözer. `customerInfo >= QtyBarrier` ise `sent = false`; `Chase` ise `chaseSent = false`.
- **`ouchReplayComplete()`** → `StrategyManager::isAllOuchReplayComplete()`. Emir gönderen bütün giriş noktaları bunu kontrol etmelidir (§2 "Replay gate").
- **Emir gönderme deseni** (SDK → order-service yedek yolu): [README.md → Emir gönderme deseni](README.md#emir-gönderme-deseni). HftClassic bunu `wrapEnterOrder` içinde PerfSDK zaman damgalarıyla sarar.

### Durum

Taban sınıfta tek bir durum enum'u **yoktur**. "Strateji durumu" şu bayrakların birleşimidir:

| Bayrak | Anlam | Yazan |
|--------|-------|-------|
| `isRunning` | Strateji başlatıldı. ITCH callback'leri yalnız `isRunning` iken olay üretir, worker yalnız `isRunning` iken işler. | `setCommand`, `StrategyManager::startStrategy/stopStrategy`, alt sınıf `stop()` |
| `isHot` | Tavan/Taban tiering'inde sıcak. Worker önceliği ve hot-ready yolu buna bakar. | `HftMaxPrice` / `HftMinPrice` |
| `markedForDeletion` | Worker bu stratejiyi atlar | `AlgoWorker::removeStrategy` (pratikte çağrılmıyor, §2) |
| `allUsersReplayDone` (global) | Replay gate açık | `StrategyManager` |
| `closePositionInProgress`, `waitingForCancelCompletion` | Pozisyon kapatma akışı sürüyor | `closeThePositionForSingleStock`, `cancelAllOrders`, `onCancelResponse` |
| `sent`, `chaseSent`, `autoCloseWaitingAccept` | Gönderilmiş, accept bekleyen emir kilidi | strateji |

⚠ `HftMaxPrice` ve `HftMinPrice` kendi `std::atomic_bool isRunning` üyesini tanımlar ve taban sınıftaki `Strategy::isRunning`'i gölgeler. Bu yüzden ikisini birlikte set ederler (`isRunning.store(..); Strategy::isRunning.store(..)`). Worker ve ITCH client taban sınıftakine bakar. Bu sınıflarda tek birini değiştiren kod hata üretir.

İlgili enum'lar (`src/Globals/Enumarations.h`):
- `hft::enums::strategy::MessageType`: emrin `customerInfo` alanı. `NoType '0'`, `UserOrder '1'`, `MorningOrder '2'`, `OpeningOrder '3'`, `EveningOrder '4'`, `TheoreticalOrder '5'`, `ChaseBait '6'`, `Chase '7'`, `QtyBarrier '8'`, `FastBarrier '9'`, `SecondRule 'B'`, `PassivePositionClose 'I'`, `Warrant 'W'`.
- `hft::enums::AutoClosePossitionStates`: `closeThePositionForSingleStock` dönüşü. `NotFound 1`, `AlreadyClosed 2`, `OnlyCancelled 3`, `OnlyClosed 4`, `CancelAndClosed 5`, `InProgress 6`.
- `hft::enums::HftType`: `notHft 0`, `HftClassic 1`, `HftNoPosition 2`, `HftMaxPrice 3`, `Warrant 4`, `HftMinPrice 5`, `WarrantAdvanced 6`.
- `hft::enums::StrategyType` (`NoPosition 1`, `OrderChase 2`, `Max_Price 3`, `TheoreticalPrice 4`) eski bir enum'dur. Registry ve wire'da kullanılan tip `ouchSDK::enums::StrategyType`'tır (`common.proto`).

Strateji-özel durum makineleri (Tavan/Taban `TavanState`, PTRM durdurması `ptrmStopped` / `Stopped_By_Ptrm`, `HftWarrant::DerivativeState`, `HftWarrantAdvanced::WarrantState`) ilgili dokümanlardadır: [tavan.md](../../20-stratejiler/tavan.md), [taban.md](../../20-stratejiler/taban.md), [varant.md](../../20-stratejiler/varant.md), [varant-toplu.md](../../20-stratejiler/varant-toplu.md).

## 2. `StrategyManager`

Singleton (`StrategyManager::instance()`).

### Registry ve `unique_key`

- `strategies`: `unordered_map<string, shared_ptr<Strategy>>`, `strManagerMutex` (`shared_mutex`) ile korunur.
- **Format:** `<orderbookId>_<account>_<strategyIdentifier>_<strategyType>`. `strategyType` sayısaldır (`ouchSDK::enums::StrategyType`).
- **Üretim:** HftSrvProd GUI komutlarında anahtarı **üretmez**; komuttaki `Strategy_Unique_Key` alanından okur (`BaseStrategyCommand` constructor'ı, baştaki boşluklar `getUniqueKey` içinde kırpılır). UI aynı formatta üretir (ör. mtrader-trade-ui `CancelAllOrdersModal`). HftSrvProd'un kendisi anahtarı yalnız şu yerlerde birleştirir: `SubscribeToOrderbook`, `AlgoSetAccountStrategy` (`StrategyServiceImpl`) ve OUCH olaylarından stratejiyi bulurken (`OuchManager::findStrategy`, `StrategyManager::findStrategy`, `Strategy::getStrategyKey`).
- **Sonuç:** Registry anahtarı bu formattan saparsa OUCH olayları stratejiye ulaşmaz ("strategy not found for token").
- `derivativeToStrategyKey` (`derivativeMapMutex`): varant stratejileri için türev obid → ana strateji anahtarı (`registerDerivative`, `getStrategyByDerivative`).
- `runningStrategies` ve `stateSubscriberStrategies` (`runningStrategiesMutex`): çalışan stratejiler ve orderbook-state abonesi stratejiler (yalnız `THEORETICAL_PRICE`).

### Oluşturma (`createStrategy(cmd, isItchSdkClient)`)

1. Anahtar zaten varsa **mevcut** strateji döner. Komut uygulanmaz.
2. `strategyType`'a göre `createStrategyImpl<Command, Strategy>` çağrılır: `MAX_PRICE`→`HftMaxPrice`, `MIN_PRICE`→`HftMinPrice`, `HFT`→`HftClassic`, `THEORETICAL_PRICE`, `WARRANT`, `WARRANT_ADVANCED`. Listede olmayan tip LOG_CRIT yazar ve `nullptr` döner.
3. `make_shared<StrategyT>(cmd, !isItchSdkClient)`, ardından `addStrategy`. `addStrategy` registry'ye ekler ve `AlgoWorkerManager::assignStrategy` çağırır.
4. `isItchSdkClient == false` (GUI/gRPC kaynaklı) ise `getDefaultSettings` + `saveStrategySettings` ile varsayılan ayarlar DB'ye (trade-data-app) yazılır.
5. Komut `StrategyServiceImpl::enqueueCommand` ile GUI stream'ine konur (snapshot).

`createStrategy` **`setCommand` çağırmaz**. Strateji `isRunning = false` doğar. Parametreler yalnız `command` alanında durur ve ilk `setCommand`'a kadar uygulanmaz.

Çağıranlar: `ItchSdkClient::loadStrategiesFromDb` (açılış), `GUIManager::dispatchStrategy` (önce oluşturur, sonra `setCommand`), `GUIManager::dispatchBalance`, `StrategyServiceImpl::AlgoSetAccountStrategy` / `SubscribeToOrderbook`. Son üçü çıplak bir `BaseStrategyCommand` ile oluşturur (bkz. Şüpheli davranışlar).

### Başlatma / durdurma

- `setStrategyRunningState(key, run)` → `startStrategy` / `stopStrategy`. Stratejinin `setCommand`'ı bunu kendisi çağırır.
- `startStrategy`: Strateji zaten `runningStrategies`'te ise `false` döner. `THEORETICAL_PRICE` için orderbook-state aboneliği kurar. `isRunning = true`, `initializeItchSubscriptions()`, `runningStrategies`'e ekleme.
- `stopStrategy`: `THEORETICAL_PRICE` için state aboneliğini kaldırır. `isRunning = false`, `cleanupItchSubscriptions()`, `runningStrategies`'ten çıkarma.
- Durdurma **emirleri iptal etmez ve pozisyonu kapatmaz**. Bu işler ayrı komutlardır: cancel-all (`cancelAllOrders`) ve close position (`closeThePositionForSingleStock`). Strateji-özel durdurma davranışı (ör. HftClassic kuyruğu boşaltır, Tavan/Taban `bumpEventGeneration`) strateji dokümanlarındadır.
- `stopAllStrategies()` tanımlıdır ama kodda çağıran yok.

### Silme

`removeStrategy(key)` stratejiyi registry'den çıkarır, `AlgoWorkerManager::removeStrategy` (→ `markedForDeletion = true`) çağırır ve periodic job'ını siler. **Kodda bunu çağıran yer yok.** Bu yüzden oluşturulan strateji süreç bitene kadar bellekte kalır. GUI'den "silme" komutu HftSrvProd'a ulaşmaz. ❓ doğrulanmadı: UI/trade-data-app silmeyi yalnız DB tarafında mı yapıyor.

### DB'den yükleme ve `restorePositionState`

- Tetik: ITCH Spot snapshot-end callback'i (`ItchSdkClient::onSnapshotEndCallback`). Callback önce varant tiplerini cache'ler, sonra `requestStrategyLoadAsync()` ile **`strat-loader`** thread'ini uyandırır. Yükleme SDK receiver thread'inde yapılmaz: 2026-08-03'te bu thread'de yapılan yükleme bir partition'ı dakikalarca durdurdu.
- `loadStrategiesFromDb`: `DatabaseServiceClient::getStrategySettings()` → her satır için `convertAlgoSettings` → `CommandFactory::createStrategyCommand` → `createStrategy(cmd, true)`. Bitince `strategiesLoadedFromDb = true`. Snapshot-end birden fazla gelirse yükleme tekrarlanır. Var olan anahtarlar atlandığı için tekrar zararsızdır.
- `Strategy_Started` DB'ye **yazılmaz**: `saveStrategySettings` bu alanı filtreler. Yüklenen stratejiler bu yüzden **durmuş** halde gelir (kasıtlı). Kullanıcı GUI'den yeniden başlatmalıdır.
- **Pozisyon DB'den yüklenmez.** `balance`/`profit` 0 ile başlar. Yeniden kurulmalarının iki yolu var: OUCH replay'inin getirdiği accept/execute olayları (`addOrder`/`executeOrder` → `updatePosition`) veya GUI'den SetBalance. ❓ doğrulanmadı: gün içi restart'ta order-service'in handoff + replay'i yeniden yapıp yapmadığı ([emir-yasam-dongusu.md](emir-yasam-dongusu.md)).
- `restorePositionState()` StrategyManager'da **değildir**. `HftMaxPrice` ve `HftMinPrice` üyesidir ve her `setCommand`'da çalışır. Tavan'da kural şudur: `balance > 0` veya tavan fiyatında bekleyen alış var **ve** yolda bir satış (çıkış) emri yok. Taban'da kural `balance > 0` veya herhangi bir bekleyen satış emri olmasıdır. Kural sağlanırsa `isPositionOpen` true, sağlanmazsa false yapılır. Sonra `mark{Max,Min}PriceStateDirty` çağırır. Ayrıntı: [tavan.md](../../20-stratejiler/tavan.md), [taban.md](../../20-stratejiler/taban.md).

### Replay gate

Amaç: OUCH handoff replay'i sürerken stratejilerin emir göndermemesi ve ITCH'e göre karar vermemesi.

- Durum: `pendingReplays` (atomic int) ve `allUsersReplayDone` (atomic bool). Okuma: `isAllOuchReplayComplete()`.
- **Kurulma:** İlk `ouchSDK::orderUserDisconnected` (handoff) callback'inde bir kez `registerExpectedReplays(total)` çağrılır (`OuchManager.cpp`, statik `replaysRegistered`). Bu çağrı `pendingReplays = total` ve `allUsersReplayDone = (total == 0)` yapar.
- **Açılma:** MAOrderSDK `onReplayCompleted(username)` → `notifyUserReplayCompleted`, sayaç 0'a inince gate açılır.
- **60 sn timeout:** `registerExpectedReplays` tek seferlik bir thread kurar. 60 sn sonra gate hâlâ kapalıysa LOG_CRIT "replay gate TIMEOUT … FORCING gate open" yazar ve gate'i zorla açar.
- **20 sn zero-handoff watchdog:** `startPeriodicJobs` içinde kurulur, tek seferliktir. 20 sn sonra `pendingReplays == 0` ve gate kapalıysa açar ve LOG_CRIT "no OUCH handoff within 20s — opening gate (zero-handoff)" yazar. Sabah OUCH kullanıcısı yoksa handoff hiç gelmez ve gate sonsuza kadar kapalı kalırdı.
- Watchdog açtıktan sonra handoff gelirse `registerExpectedReplays` gate'i **yeniden kapatır**. Header'daki "Never reverts" yorumu bu durumda doğru değil. Gate yalnız ilk handoff turunda kurulur; sonraki turlar `replaysRegistered` nedeniyle gate'i kurmaz.
- Gate kapalıyken: `processSingleEvent` erken döner (olay kuyrukta kalır), `addSecondRuleOrder` job kurmaz, HftClassic passive TP göndermez, `processReadyEvent` (Tavan/Taban) olayı kuyruğa geri koyar.

### Periyodik işler (`periodicJobsWorker`)

- `PeriodicJob { executeTime (steady_clock), shared_ptr<Strategy>, OrderAccepted* }`. `periodicJobsMap` **strateji anahtarıyla** tutulur, yani strateji başına **tek** bekleyen job olur ve yeni `scheduleJob` eskisinin üzerine yazar.
- Thread döngüsü: süresi gelen job'ları map'ten çıkarır ve `strategy->sendSecondRuleOrder(order)` çağırır. Döngüde sleep yok; `periodicJobAvailable` false iken de boş döner (busy-spin).
- Kullananlar:
  - **HftClassic second rule:** accept sonrası `Second_Rule_Duration` **saniye**. `sendSecondRuleOrder` bu thread'de stratejinin kilidini (bloklayarak) alır ve **emri doğrudan gönderir**. Karar burada verilir. Mantık: [hft-classic.md → Second rule](../../20-stratejiler/hft-classic.md).
  - **Tavan secondRule re-check / Taban reClose re-check:** süre **ms**, `order = nullptr`. `sendSecondRuleOrder` yalnız sentetik `TIMER_TRIGGER_CHECK` olayını stratejinin kuyruğuna koyar. Karar AlgoWorker'da verilir.

### Durum push worker'ı ve dirty bayrağı (`strategyStatesWorker`)

100 ms'de bir sırayla:
1. `processMaxPriceStateUpdates` / `processMinPriceStateUpdates`: `dirtyMaxPriceStates` / `dirtyMinPriceStates` kümelerindeki stratejiler için `sendMaxPriceStateUpdate` / `sendMinPriceStateUpdate`.
2. `processSummaryUpdates`: `dirtyStrategies` (`markStrategyDirty`) kümesindeki her anahtar için `updateSummaryMap` çalışır. Strateji, `balance > 0 || isRunning || profit != 0 || WARRANT_ADVANCED` ise hesabın özetine girer, değilse çıkar. Özet push'u **saniyede bir** yapılır: hesap başına `SummaryCommand` üretilir, anahtarı `SUMMARY_<account>`. İçeriği: obid, hesap, id, tip, sembol, isRunning, balance, hftType. `profit` yalnız `balance == 0` iken gönderilir, aksi halde 0 gider. Varant alanları da eklenir.
3. `processSetToOneUpdates`: `queueSetToOneUpdate` / `queueCommandPush` kuyruğu. Strateji kendi parametresini değiştirdiğinde komutu GUI'ye ve DB'ye geri iter. Anahtar başına son komut kalır.
4. `processGuiOrders`: `guiOrderQueue`'yu boşaltır. Bu kuyruğu yalnız `OuchWorker` dolduruyordu ve o artık çalışmıyor (§3). MAOrderSDK yolunda emir olayları doğrudan `StrategyServiceImpl::enqueue*OrderEvent` ile gider.

Dirty işareti yalnız özet **üyeliğini** günceller. Üyelikteki stratejilerin değerleri her saniye yeniden okunur.

### Hesap çapı işler

- `cancelAllOrders(cmd)`: anahtarla bulunan strateji için `side` 0 ise iki taraf, aksi halde `'B'`/`'S'` iptal edilir.
- `cancelAllStrategyOrders(account)`: hesabın `hasCancelableOrders()` olan bütün stratejilerinde iki taraf iptal edilir.
- `closeThePositionForSingleStock`: `closePositionInProgress` ise `InProgress` döner. Bakiye ve emir yoksa `AlreadyClosed`. Yalnız emir varsa iptal edilir (`OnlyCancelled`). Yalnız bakiye varsa `closePosition` (`OnlyClosed`). İkisi de varsa önce iptal, son cancel cevabında `closePosition` (`CancelAndClosed`).
- `closeAllPositions()`: bütün stratejiler için `closeThePositionForSingleStock` çağırır.

## 3. Thread modeli ayrıntısı

Özet tablo [README.md → Thread modeli](README.md#thread-modeli)'nde.

### AlgoWorker döngüsü (`AlgoWorker::eventDispatcherLoop`)

- `AlgoWorkerManager` `workerCount` kadar worker kurar. `algoWorkerCores` listesindeki ilk N worker'ı pinler, `HFT_RT_FIFO` env değişkeni varsa ayrıca `SCHED_FIFO@80` uygular. Liste dışındaki worker'lar pinsizdir.
- Her worker'ın `strategies` vektörü vardır (2000 kapasite ayrılmış) ve vektörden hiç eleman silinmez. Döngü uyumadan döner (busy-loop):
  1. `realHotReadyQueue` açıksa `drainHotReady(512)`.
  2. `strategiesBeingModified` false ise:
     - **Hot öncelik kapalıysa** (`hotWorkerCount == 0`): her çalışan ve silinmemiş strateji için `processSingleEvent()` çağrılır, yani her tur strateji başına en fazla **bir** olay işlenir.
     - **Hot öncelik açıksa** (`hotWorkerCount > 0`; sayının kendisi kullanılmaz, yalnız açık/kapalı anlamı taşır): çalışan stratejilerin `{ptr, isHot}` anlık görüntüsü alınır. Önce bütün hot'lar için `processSingleEvent`, sonra cold'lar için çağrılır. Hot-ready açıksa her 32 cold stratejide bir `drainHotReady(64)` yapılır.
  3. 5 sn'lik kuyruk derinliği raporu hesaplanır ama log satırı yorumdadır.
- **Atama:** `AlgoWorkerManager::assignStrategy` round-robin çalışır (`nextWorkerIndex_ % workerCount_`). Strateji worker'a ömür boyu bağlıdır. Hot/cold değişince worker değişmez, yalnız tur içindeki sıra değişir. `workerCount` 0 olursa modulo sıfıra bölme olur.

### Hot/cold ve `realHotReadyQueue`

- `isHot` bayrağını Tavan/Taban, fiyat eşiği geçişine göre set eder (`onPriceThresholdCrossing`). Tiering yalnız `hotWorkerCount > 0` iken açıktır (`tieringEnabled`). Eşikler: [tavan.md](../../20-stratejiler/tavan.md), [config.md](config.md).
- `realHotReadyQueue = Y` (veya env `HFT_REAL_HOT_READY_QUEUE` = `1`/`Y`/`y`/`true`/`TRUE`; env config'i ezer) iken:
  - `ItchSdkClient::enqueueStrategyEvent`: strateji hot ise olay stratejinin worker'ının `hotReadyQueue_`'suna `HotReadyItem{strategy, event, generation}` olarak konur. Kuyruk ≥ 65536 ise `hotReadyDropped_` artar ve olay normal strateji kuyruğuna düşer (kaybolmaz).
  - `processHotReadyItem` sırası:
    1. Strateji silinmiş, durmuş veya generation farklıysa olay **atılır** (`hotReadyStale_`).
    2. Strateji artık hot değilse veya kendi kuyruğunda bekleyen olay varsa olay stratejinin kuyruğuna eklenir. FIFO korunur.
    3. Diğer durumda `processReadyEvent` çağrılır ve olay doğrudan işlenir (Tavan/Taban).
  - `eventGeneration_`: Tavan/Taban start/stop sınırında `bumpEventGeneration()` çağırır. Önceki çalışma döneminden kalan hot-ready öğeleri böylece geçersiz olur.

### Strateji başına ITCH kuyruğu

- `Strategy::enqueueItchEvent`: `queuedItchEvents_` sınırı (`strategyQueueMaxEvents`, 0 → 50000) aşılırsa **yeni gelen olay** düşürülür ve `droppedItchEvents_` artar. Eski olaylar kuyrukta kalır. `enqueuedAt` PerfSDK için ns damgasıdır.
- ITCH callback'leri olayı yalnız `strategy->isRunning` iken üretir. Strateji, handle → `Strategy*` lock-free tablosundan (`handleToStrategy_`) bulunur.
- Olay tipleri (`ItchEventType`): `LEVEL_CHANGED`, `HEADER_CHANGED`, `HEADER_SNAPSHOT`, `SPECIFIC_ORDER_EXECUTED`, `ORDER_ADDED`, `ORDER_EXECUTED`, `ORDER_DELETED`, `ORDERBOOK_STATE_CHANGED`, `SNAPSHOT_END`, `EQUILIBRIUM_PRICE_UPDATE` ve sentetik `TIMER_TRIGGER_CHECK` (stratejinin kendi timer'ı). Alan ayrıntısı: [itch-entegrasyonu.md](itch-entegrasyonu.md).
- HftClassic, kilidi 100 µs içinde alamazsa olayı işlemeden düşürür ([hft-classic.md](../../20-stratejiler/hft-classic.md)).

### Hangi kod hangi thread'de çalışır

| Kod | Thread |
|-----|--------|
| `processSingleEvent`, `processReadyEvent`, `processItchEvent*` (strateji kararları) | AlgoWorker |
| `enqueueItchEvent` / `enqueueHotReady`, `onPriceThresholdCrossing` | ITCH SDK receiver thread'leri |
| `loadStrategiesFromDb` → `createStrategy` | `strat-loader` |
| `setCommand`, `createStrategy` (GUI), `cancelAllOrders`, `closeThePositionForSingleStock`, `setBalance` | gRPC (`GUIManager` / `StrategyServiceImpl`) |
| `addOrder` + `addSecondRuleOrder`, `rejectOrder`, `updateOrder`, `deleteOrder`, `onCancelResponse` | MAOrderSDK OUCH recv thread'i (handoff öncesi: ouch-sdk istemci thread'i, `OuchManager.cpp`) |
| `executeOrder` | OUCH recv; combiner açıkken ITCH thread'i de olabilir |
| `sendSecondRuleOrder` | periodic jobs thread'i |
| Özet / state push, `processSetToOneUpdates` | `strategyStatesWorker` |
| 20 sn / 60 sn gate thread'leri | detached tek seferlik thread'ler |

### Kilitler, sıra ve yarışlar

| Kilit | Tür | Korur |
|-------|-----|-------|
| `Strategy::buySellInfoMutex` | `recursive_timed_mutex` | Stratejinin bütün durumu: `orderMap`, depth, miktarlar |
| `strManagerMutex` | `shared_mutex` | `strategies` |
| `runningStrategiesMutex` | `shared_mutex` | `runningStrategies`, `stateSubscriberStrategies` |
| `derivativeMapMutex` | `shared_mutex` | `derivativeToStrategyKey` |
| `periodicJobsMutex`, `dirty*Mutex`, `setToOneUpdatesMutex`, `summaryMutex` | `mutex` / `shared_mutex` | ilgili kuyruk/küme |

Gözlenen kilit sıraları:
- `strManagerMutex` (shared) → `buySellInfoMutex`: `StrategyManager::cancelAllOrders`, `closeThePositionForSingleStock` ve `cancelAllStrategyOrders`, registry kilidini tutarken stratejinin kilidini alır.
- `buySellInfoMutex` → `strManagerMutex` (shared) → `runningStrategiesMutex` (unique): `setCommand` stratejinin kilidini tutarken `setStrategyRunningState` çağırır.
- İki sıra ters yöndedir ama iki uçta da `strManagerMutex` **shared** alındığı için doğrudan deadlock oluşmaz. ❓ doğrulanmadı: arada bir writer (`addStrategy`) beklerken shared-lock'un bloklanıp bloklanmayacağı. Bu, platformun `shared_mutex` writer önceliğine bağlıdır.
- OUCH callback'leri `buySellInfoMutex`'i **bloklayarak** alır. Worker kilidi uzun tutarsa OUCH recv thread'i bekler. Recursive kilit, SDK'nın `enterOrder` içinden senkron ateşlediği yerel reject'in aynı thread'de kilidi yeniden alabilmesi için gereklidir.
- Kilitsiz okunan/yazılan alanlar (veri yarışı):
  - `balance`/`profit` özet thread'inden ve `closeThePositionForSingleStock`'tan okunur.
  - `closePosition` ve `HftClassic::sendSecondRuleOrder`'ın başındaki `localOrderbook` okuması kilitsizdir.
  - `Strategy::updateCumulativeOrders` depth'i kilitsiz dolaşıp replace/cancel gönderir; kilidi ancak sonrasında alır.

### Kuyruklar (`src/Containers`)

| Kuyruk | Tip | Üretici → Tüketici |
|--------|-----|--------------------|
| `Strategy::itchEventQueue_` | `moodycamel::ConcurrentQueue` | ITCH thread'leri, timer'lar, hot-ready geri düşmesi → AlgoWorker |
| `AlgoWorker::hotReadyQueue_` | `moodycamel::ConcurrentQueue` (yumuşak sınır 65536) | ITCH thread'leri → aynı worker |
| `StrategyServiceImpl::globalCommandQueue` | `moodycamel::ConcurrentQueue` | herkes → gRPC `FetchCommands` stream'i ([komutlar-ve-grpc.md](komutlar-ve-grpc.md)) |
| `StrategyManager::guiOrderQueue` | `moodycamel::ConcurrentQueue` | yalnız `OuchWorker` (ölü) → `strategyStatesWorker` |
| `SPSCQueue`, `ParseBuffer` | özel | yalnız `OuchWorker` |

`BlockingQueue.h`, `Barrier.h`, `readerwriterqueue.h`, `readerwritercircularbuffer.h` kodda kullanılmıyor.

### `OuchWorker*` kalıntısı

`src/Workers/OuchWorker*.{h,cpp}` CMake'te derlenir ve `OuchManager.h` include eder (`ClientInfo::worker`). Ancak kodda `OuchWorker` veya `OuchWorkerManager` örneği **oluşturulmaz**. Eski internal-OUCH yolunda bu sınıf ham SoupTCP payload'ını parse edip `enqueueGuiOrder` ile GUI'ye taşıyordu. MAOrderSDK geçişinden sonra bu kod ölü. `getOuchWorkerCount` config anahtarı da kullanılmıyor.

## 4. Yaşam döngüsü senaryoları

### Açılış

1. `HftMain`: ITCH SDK başlar. `ItchSdkClient::initialize` önce `strat-loader` thread'ini, sonra Spot snapshot-end aboneliğini kurar.
2. MAOrderSDK boot olur (login yok). `AlgoWorkerManager.start()` → `GUIManager` (gRPC) → `ItchManager` → `startPeriodicJobs` (20 sn watchdog kurulur) → `startStrategyStatesWorker`.
3. Glimpse/snapshot bitince `strat-loader` DB'deki bütün strateji ayarlarını yükler. Her strateji oluşur, bir worker'a atanır ve GUI'ye snapshot'ı gider. Hepsi **durmuş**, `balance = 0` halde gelir.
4. order-service OUCH kullanıcılarını devreder (handoff) ve gate kapanır. MAOrderSDK günün emirlerini replay eder. Replay sırasında `onAccepted` → `addOrder`, `onExecuted` → `executeOrder` çalışır ve strateji varsa depth ile pozisyon yeniden kurulur. Strateji henüz yüklenmemişse WARN "strategy not found for token" yazılır ve o olay stratejiye ulaşmaz. ❓ doğrulanmadı: replay ile DB yüklemesinin pratikteki sırası.
5. Replay biter (veya 60 sn timeout, ya da handoff hiç yoksa 20 sn watchdog) ve gate açılır.
6. Kullanıcı GUI'den başlatır: `dispatchStrategy` → `setCommand` → abonelikler kurulur, `isRunning = true`, ITCH olayları akmaya başlar.

### Durdurma (GUI)

`setCommand(started=false)`: strateji abonelikleri kaldırır. HftClassic kuyruğu boşaltır, Tavan/Taban generation'ı artırır ve `isHot = false` yapar. Ardından `stopStrategy` ve `isRunning = false`. Bekleyen emirler **borsada kalır**. İptal için cancel-all, pozisyon için close position komutu gerekir. Stratejinin kendini durdurması (`stop()`) strateji dokümanlarındadır.

### Servis restart'ı

- `SIGINT`/`SIGTERM` gelince handler yalnız bayrak çevirir. Main thread'de `performShutdown` sırasıyla şunları yapar: `maosdk->stop()` (bütün OUCH kullanıcılarının bağlantısı kesilir), legacy `ouchSDK::stopOuchStreaming`, `ItchManager.stop`, `GUIManager.stop`, `stopPeriodicJobs`, `AlgoWorkerManager.stop`, `exit(1)`.
- Kapanışta stratejiler durdurulmaz, emirler iptal edilmez, pozisyon veya state diske ya da DB'ye yazılmaz. `stopStrategyStatesWorker` da açıkça çağrılmaz. ❓ doğrulanmadı: OUCH bağlantısı kopunca BIST tarafında cancel-on-disconnect uygulanıp uygulanmadığı.
- Yeniden açılışta "Açılış" senaryosu tekrarlanır. **Pozisyon ne olur:**
  - Bellekteki `balance`, `profit`, `openLots`, `realizedProfit` ve strateji-özel durum (ör. Tavan `isPositionOpen`) kaybolur.
  - Depth ve bakiye yalnız OUCH replay ile yeniden kurulabilir. Bunun için replay günün accept ve fill'lerini getirmeli ve strateji o anda registry'de olmalıdır. Aksi halde bakiye GUI'den SetBalance ile elle düzeltilmelidir.
  - Tavan/Taban bir sonraki `setCommand`'da `restorePositionState` ile `isPositionOpen`'ı kurulan bakiye ve depth'ten yeniden türetir.
  - `realizedProfit` ve FIFO lotlar yalnız replay edilen fill'lerden oluşur.
- Stratejiler restart sonrası **otomatik başlamaz** (`Strategy_Started` DB'ye kaydedilmez).

## Şüpheli davranışlar (koddan)

- **Kuyruk taşması yeni olayı düşürür.** `Strategy::enqueueItchEvent` sınır aşılınca gelen olayı atar. README "eski olaylar düşürülür" diyor. Ayrıca gate kapalıyken çalışan bir stratejinin `processSingleEvent`'i dequeue etmez. Gün içi bir handoff turunda olaylar birikir ve gate açılınca bayat olaylar işlenir. ❓ doğrulanmadı: pratikte oluşup oluşmadığı.
- **`checkAndSetSent`'te ölü dal.** `PassivePositionClose` (`'I'`) değeri `>= QtyBarrier` (`'8'`) koşulunu sağlar ve ilk dala girer. `autoCloseWaitingAccept = false` dalına hiç ulaşılmaz.
- **Strateji başına tek periodic job.** `periodicJobsMap` strateji anahtarıyla tutulur. Kısa aralıkla gelen iki accept'te ilk emrin HftClassic second rule job'ı ezilir. ❓ doğrulanmadı: kasıtlı mı.
- **Ömür sorunu olan raw pointer.** `PeriodicJob::order` raw `OrderAccepted*` taşır. Job çalıştığında emir tamamen dolmuş veya iptal olmuş olabilir. Pointer'ın geçerliliği `OrderRegistry`'nin nesneyi ne zaman sildiğine bağlıdır. ❓ doğrulanmadı.
- **`periodicJobsWorker` busy-spin.** Job yokken de sleep'siz döner ve pinsiz bir çekirdeği yakar.
- **Çıplak `BaseStrategyCommand` ile oluşturma.** `dispatchBalance`, `AlgoSetAccountStrategy` ve `SubscribeToOrderbook` stratejiyi bu komutla oluşturur. `createStrategyImpl` ise komutu `static_pointer_cast` ile `HftClassicCommand` vb. tipe çevirir: tanımsız davranış. HftClassic'in `getSecondRuleDuration` / `getOrderQuantity` içindeki `dynamic_pointer_cast` sonucu null olur ve `setCommand` gelmeden çağrılırsa null deref olur. Bu yol `isItchSdkClient = false` ile çalıştığından DB'ye yalnız taban alanlardan oluşan varsayılan ayar da yazılır.
- **Worker vektöründe yarış.** `AlgoWorker::addStrategy` worker döngüsü sürerken `push_back` yapar. `strategiesBeingModified` yalnız turun başında kontrol edilir. 2000'lik `reserve` aşılırsa yeniden tahsis worker'ın iterasyonunu bozabilir. `strategyToWorkerMap_` kilitsizdir.
- **Silme yolu yok.** `removeStrategy` ve `stopAllStrategies` çağrılmıyor. `markedForDeletion` pratikte hiç set edilmiyor.
- **Replay gate'i atlayan çağrılar.** `closePosition` ve `cancelAllOrders` gate'e bakmaz; replay sırasında GUI'den close position emir gönderebilir.
- **`isRunning` gölgeleme.** `HftMaxPrice`/`HftMinPrice` içindeki ikinci `isRunning` iki bayrağın ayrışma riskini taşır (§1).
- **Kayıt silinmeden abonelik kaldırma.** HftClassic `setCommand(stop)` içinde `unsubscribe` yapar ama `unregisterStrategyForHandle` çağırmaz; `handleToStrategy_` slotu dolu kalır. ❓ doğrulanmadı: SDK handle değerlerini yeniden kullanıyor mu ([itch-entegrasyonu.md](itch-entegrasyonu.md)).
- **Yanlış kilit.** `stopAllStrategies`, `runningStrategies`'i `strManagerMutex` altında okur; doğru kilit `runningStrategiesMutex`.
