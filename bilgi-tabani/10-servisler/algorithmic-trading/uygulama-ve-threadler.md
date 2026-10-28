---
kapsam: AlgoProd uygulama iskeleti — açılış/kapanış sırası, sinyaller, hata yolu, manager'lar ve singleton'lar, thread modeli (ITCH, ouch-sdk, gRPC, AlgoWorker, strateji thread'leri), kuyruklar ve sıra garantisi, StrategyManager yaşam döngüsü, ITCH entegrasyonu ve kendi emir defteri, enstrüman hiyerarşisi, logger/PerfSDK/Sentry
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading        # prod binary'si; farklar ⚠ ile işaretli
    branch: master
    commit: aa150ee
  - repo: AlgorithmicTrading        # yalnız sınır notu
    branch: add-order-sdk
    commit: 7d7f705
dogrulama: 2026-10-22
durum: taslak
---

# AlgoProd — uygulama, manager'lar ve thread'ler

Servisin genel haritası [README.md](README.md)'de, config anahtarları [config.md](config.md)'de, açılış log satırları [log-imzalari.md § 4](../../40-operasyon/log-imzalari.md#4-algoprod-algorithmictrading)'te. Bu dosya **sınırları** gösterir. Şunlar başka dosyalarda anlatılır: emir yolu (`OuchManager::send*`, takip, reject), gRPC uçları (`StrategyServiceImpl`) ve DB çağrıları (`DatabaseServiceClient`). Strateji mantığı [`20-stratejiler/`](../../20-stratejiler/README.md)'de.

Bütün yollar `algoSrc/`'ye görelidir.

## 1. Açılış sırası

`SourceFiles/Main.cpp` `main`:

1. **Onload/VMA re-exec** (derleme bayrağına bağlı): `HAS_ONLOAD` ile derlenmişse ve `LD_PRELOAD` boşsa `LD_PRELOAD=libonload.so` set edilir ve `execvp` ile proses kendini yeniden başlatır. Ardından `onload_set_stackname(ONLOAD_ALL_THREADS, ONLOAD_SCOPE_GLOBAL, ONLOAD_DONT_ACCELERATE)` çağrılır: varsayılan olarak **hiçbir thread hızlandırılmaz**. ITCH SDK kendi stack'ini (`itchOnloadStackName`) kullanır. `HAS_MLX` ile derlenmişse aynı işlem `libvma.so` ile yapılır.
2. **Sentry**: kullanıcı = hostname, release `mtrader-algoprod@1.5`, `debug=1`, veritabanı `.sentry-native`. DSN koda gömülüdür (`<REDACTED>`, K-15).
3. `loadConfiguration`: argüman yoksa `Configuration/Configuration.ini`, bir argüman varsa o dosya kullanılır. İkiden fazla argüman `BaseException` fırlatır, bu `try` dışında olduğu için `terminate` olur.
4. `Application::startApplication` (`SourceFiles/Application.cpp`):
   1. Sinyal handler'ları: `SIGINT`, `SIGHUP`, `SIGUSR1`, `SIGUSR2` → `terminationSignalReceived = 1`. `SIGPIPE` yok sayılır. **`SIGTERM` ve `SIGABRT` satırları yorumdadır**, bu yüzden SIGTERM varsayılan davranışla prosesi hemen öldürür ve kapanış sırası çalışmaz (bkz. K-183).
   2. `SettingsManager::loadAllSettingsFiles()`: trade-data-app'ten `GetAllInstruments` (`orderbookSettingsMap`) ve fiktif enstrüman tanımları (`fictiveInstrumentsSettingsMap`) okunur. **`try` dışında ve Logger'dan önce** çalışır: DB hatası `terminate` ile biter, bu adımın `logInfo` çağrıları da log dosyasına düşmez (yalnız stdout).
   3. `try { runTests(); waitCloseSignalEitherFromUserOrSystem(); }`. Üretim yolu `runTests`'tir. `runProduction`, `runUnitTests` ve `runPriceChanger` çağrılmayan eski yollardır.
5. `runTests` sırası:

| # | Adım | Bloklar mı | Not |
|---|------|-----------|-----|
| 1 | PerfSDK `PerformanceClient::start("algo_prod", monitoringPort, 0, 2000, false)` | — | Yalnız `HAS_MAPERFSDK` ve `monitoringEnabled=true` ise |
| 2 | `Logger::start()` | — | NanoLog başlar (§ 8) |
| 3 | `OrderbookManager::start()` | — | Tüketici thread'i başlar (§ 3) |
| 4 | `ItchSdkManager::startItchSdkManager` | **Evet**: `itchsdk_start()` bütün partition'ların Glimpse'i bitene kadar döner | Snapshot-end callback'leri bu çağrı sürerken SDK thread'lerinden gelir (§ 6) |
| 5 | `waitForInitialization(OrderbookManager, 600)` | Evet, 1 s aralıkla en çok 600 kez kontrol eder | `OrderbookManager::isInitialized()` ancak `ItchSnapshotEnd` olayı tüketici thread'inde işlenince true olur. Süre **4. adım bittikten sonra** başlar. Dolarsa `BaseException` fırlar |
| 6 | `OuchManager::start()` | Evet | Önce **3 s sabit uyku**, sonra `startOuchStreaming` (MARpc connect) ve `login(AlgoTrading)`. Login başarılıysa `createUserbooks()` (strateji bilgileri → kullanıcı defterleri) ve `ouchSDK::getAllOrders()` (replay; tamamlanana kadar bloklar) çağrılır. Login başarısızsa yalnız log dosyasına yazılır, açılış **devam eder**. Connect hiç kurulamazsa `login` sonsuza kadar bekler (K-151) |
| 7 | `GUIManager::start()` | — | Aboneliklerini kurar, gRPC sunucusunu ayrı thread'de açar. Bu adımdan sonra **gRPC komutları kabul edilir** |
| 8 | `AlgoWorkerManager::start()` | — | `workerCount` adet thread açar. ⚠ master'da yok |
| 9 | `StrategyManager::start()` → `readAlgoSettings()` | Evet (DB) | Kayıtlı stratejileri yeniden kurar (§ 5) |

Sıra notları:
- 7. adım 8–9'dan önce gelir. Bu yüzden GUI'den gelen bir komut, DB restore'u bitmeden `StrategyManager`'a ulaşabilir. `strategyMap`'in kilidi yoktur (Şüpheli).
- ⚠ master'da farklı: 8. adım yoktur. ITCH tarafı SDK v2'dir (`setItchConfig` + `startItch(true, …)` + `subscribeToGlimpseEndMessage`). master'da `workerCount` ve `triggerWorkerCount` ITCH SDK'nın worker sayılarıdır. development'ta `workerCount` AlgoWorker sayısına dönüşmüştür, `triggerWorkerCount` ise etkisizdir ([config.md](config.md)).
- 🚧 `add-order-sdk`: 6. adımdan önce `MAOrderSdkManager::start(ARGC, ARGV)` gelir; kapanışta `MAOrderSdkManager` ve `OrderEventDispatcher` durdurulur. Bu branch henüz development'ta değil (K-13).

## 2. Kapanış, sinyal, gün sonu, hata

`waitCloseSignalEitherFromUserOrSystem`: 5 s'de bir uyanır ve `OrderbookManager::eventNotifier`'a abone bir `Subscriber<EventCode>`'u boşaltır. Döngü iki koşulda biter: `EventCode::EndOfMessages` gelmesi veya `terminationSignalReceived` olması. Döngüden çıkınca `ouchSDK::stopOuchStreaming()` çağrılır.

- **Gün sonu ITCH ile tetiklenmez.** `eventNotifier`'a hiçbir yerden `notifyAllUsers` çağrılmaz (development ve master'da aynı). ITCH SDK v3 köprüsünde system-event aboneliği de yoktur. Pratikte uygulama yalnız `SIGINT`/`SIGHUP`/`SIGUSR1`/`SIGUSR2` ile düzenli kapanır. `docker stop` ise SIGTERM gönderir: handler olmadığı için proses hemen ölür, `stopApplication` çalışmaz.
- **`stopApplication` sırası:** `AlgoWorkerManager.stop` (worker'ları `join` eder) → `StrategyManager.stop` (her strateji `stop()`) → `OuchManager.stop` → `ItchSdkManager.stopItchSdkManager` (`itchsdk_stop` + `itchsdk_shutdown`) → `OrderbookManager.stop` → `GUIManager.stop` (`server->Shutdown()`) → `Logger.stop`.
- `Manager::stop` thread'leri **join etmez, detach eder** (`Managers/Manager.h`). Strateji, OrderbookManager ve GUIManager thread'leri kapanış sırasında hâlâ koşuyor olabilir. `indexCalculator` OrderbookManager thread'inin sonunda `join` edilir. `grpcWorker` hiç join edilmez.
- `stopApplication` **iki kez** çalışır: önce `startApplication`'ın sonunda, sonra `main`'de (1 s uykudan sonra). Manager'lar `running` bayrağıyla korunur, ama `stopItchSdkManager` korunmaz: `itchsdk_stop`/`itchsdk_shutdown` ikinci kez çağrılır. Ardından `sentry_close()` gelir ve `main` 0 döner.
- **Hata yolu:** `runTests` içindeki herhangi bir `std::exception` için `Application::startApplication failed: …` loglanır ve stdout'a basılır, ardından `stopApplication` çalışır ve proses **0 koduyla** çıkar. Örnekler: 600 s dolması, `itchsdk_initialize`/`itchsdk_start` hatası, snapshot-end aboneliğinin başarısız olması. `try` dışında kalan hatalar (`loadConfiguration`, `SettingsManager`, `std::stoi` ile okunan zorunlu anahtarlar) `terminate` ile biter. Bunlar SIGABRT üretir; SIGABRT handler'ı yorumda olduğundan Sentry'nin crash yakalaması devrededir. ❓ doğrulanmadı: sentry-native backend'inin (crashpad/breakpad) derlemede açık olup olmadığı.

## 3. Manager'lar, singleton'lar ve sahiplik

Hepsi Meyers singleton'dır (`static X& instance()`). Sahiplik zinciri yoktur; bileşenler birbirine `instance()` ile ulaşır.

| Singleton | Dosya | Kendi thread'i | Görev |
|-----------|-------|----------------|-------|
| `Application` | `SourceFiles/Application.*` | main | Açılış/kapanış |
| `ConfigurationManager` | `Configuration/` | — | [config.md](config.md) |
| `Logger` | `Logger/Logger.h` | (Manager thread'i boş döner) | NanoLog sarmalayıcı |
| `SettingsManager` | `Managers/SettingsManager.*` | — | DB'den enstrüman ayarları ve fiktif enstrümanlar; `InstrumentSettings*` ham `new`, hiç silinmez |
| `ItchSdkManager` | `Managers/ItchSdkManager.*` | — (SDK thread'lerinde çalışır) | ITCH SDK v3 köprüsü, `Notifier<Event>` |
| `OrderbookManager` | `Managers/OrderbookManager.*` | 1 tüketici + `indexCalculator` | Enstrümanlar, piyasa ve kullanıcı defterleri |
| `OuchManager` | `Managers/OuchManager.*` | Manager thread'i boş (`workAsyncron(){}`), callback'ler ouch-sdk thread'inde | Emir yolu (başka dosya) |
| `GUIManager` | `Managers/GUIManager.*` | `worker` (yayın döngüsü) + `grpcWorker` (`server->Wait()`) | gRPC sunucusu ve GUI akışlarının pompası |
| `StrategyServiceImpl` | `Managers/StrategyServiceImpl.*` | gRPC sync sunucusunun thread havuzu | gRPC uçları (başka dosya) |
| `StrategyManager` | `Managers/StrategyManager.*` | — | Strateji kayıt defteri (§ 5) |
| `AlgoWorkerManager` | `Workers/AlgoWorkerManager.*` | `workerCount` × `AlgoWorker` | Havuz (§ 4.2). ⚠ master'da yok |
| `DatabaseServiceClient` | `Data/` | (stream'ler için ek thread'ler) | trade-data-app istemcisi (başka dosya) |
| `StrategyLoggerManager` | `Logger/StrategyLoggerManager.*` | — | Strateji logger'ları (§ 8) |
| `OrderUtility` | `Utilities/OrderUtility.h` | `thread_pool` (5 thread, `WARRANT_THREAD_COUNT`) | Yardımcılar; havuzu yalnız `WarrantUnderlyingTracker` kullanır |

**`Manager` taban sınıfı** (`Managers/Manager.h`): `start()` `mutexStartStop` alır, `markedForDeletion=false` yapar, `startProperly()` çağırır, **ardından** `running=true` yapar ve havuz stratejisi değilse `std::thread(workAsyncron)` açar. `stop()` `running=false` yapar, thread'i detach eder ve `exitProperly()` çağırır. `IStrategy` de `Manager`'dan türer, yani her strateji bir `Manager`'dır. ⚠ master'da farklı: `running=true` `startProperly`'den önce set edilir ve havuz dalı yoktur.

## 4. Thread modeli

### 4.1 Thread listesi

| Thread | Kim açar | Ne yapar | Pin / öncelik |
|--------|----------|----------|---------------|
| main | — | Açılış, sonra `waitClose…` (5 s uyku döngüsü) | — |
| ITCH SDK receive/decode thread'leri | ITCH SDK | `ItchSdkManager::on*` callback'leri. Aynı orderbook'un callback'leri tek partition thread'inde sırayla gelir | Yalnız SDK config'i: `itchReceiverCpuCore1..4`, `clientCpuCore` ([config.md](config.md), [itch-sdk](../itch-sdk/abonelik-api.md)) |
| OrderbookManager tüketicisi | `Manager::start` | `messageList.try_dequeue` → `parseEvent`. **Uykusuz busy-spin** (bir çekirdeği %100 kullanır) | Yok |
| `indexCalculator` | `orderbookInitialized` | Fiktif endeksleri 150 ms'de bir hesaplar (§ 7) | Yok |
| ouch-sdk callback thread'i | network-sdk | `ouchSDK::orderAccepted/…` → `OuchManager::algoOrder*` → kullanıcı defteri + notifier'lar. Tek thread, order-service sırasıyla gelir ([ouch-sdk](../ouch-sdk/README.md)) | Yok |
| GUIManager `worker` | `Manager::start` | `userListMtx` altında `send*` fonksiyonları strateji/paket aktivite kuyruklarını gRPC akış kuyruklarına taşır. **Uykusuz busy-spin** | Yok |
| `grpcWorker` + gRPC havuzu | `GUIManager::startProperly` | RPC'ler. Strateji komutları `StrategyManager::commandReceived`'i **gRPC thread'inde** çalıştırır | Yok |
| `AlgoWorker-0..N-1` | `AlgoWorkerManager::start` | Havuzdaki stratejilerin `doPeriodicChecks`'i (§ 4.2) | **Yok** (koddaki yorumdaki "pinned" bir stratejinin tek worker'a bağlı kalması demektir, CPU pinlemesi değil) |
| Strateji thread'i (strateji başına 1) | `Manager::start` (havuz dışı stratejiler) | `BaseStrategy::workAsyncron` (§ 4.3) | Yok |
| `StrategyLogger` thread'i (logger başına 1, detached) | `StrategyLogger::start` | CSV'ye yazar (§ 8) | — |
| NanoLog arka plan thread'i | `nanolog::initialize` | Log dosyası | — |
| PerfSDK | `PerformanceClient::start` | Metrik gönderimi. ❓ doğrulanmadı: thread sayısı | — |

AlgoProd kodunda `pthread_setaffinity`/`sched_*` çağrısı **yoktur**. Pinleme yalnız ITCH SDK'nın kendi thread'leri için, config üzerinden yapılır.

### 4.2 Worker havuzu (`Workers/AlgoWorker*.cpp`) — ⚠ master'da yok

- **Kim:** `runsOnWorkerPool()==true` olanlar. development'ta yalnız `ArbitrageTracker` (`Strategy/Arbitrage/ArbitrageTracker.h`). `MovingAverageTracker` bunu açıkça `false` yapar; diğerleri varsayılan `false`'tur.
- **Atama:** `StrategyManager::commandReceived` sonunda, strateji havuz stratejisiyse ve `isRunning()` ise `AlgoWorkerManager::assignStrategy` çağrılır. `assignStrategy` `mapMutex_` altında `strategyToWorkerMap_`'e bakar. Anahtar (`getUniqueKey()`) daha önce atanmışsa hiçbir şey yapmaz. Atanmamışsa worker'ı round-robin seçer (`nextWorkerIndex_ % workerCount`). Ardından **çağıranın thread'inde** `onPoolAssigned()` (`beforePeriodicChecks`) çalışır ve `AlgoWorker::addStrategy` ile stratejiyi `pendingAdds_`'e (moodycamel) koyar. `onPoolAssigned` istisna atarsa map kaydı silinir ve strateji havuza girmez.
- **Kalıcılık:** Bir strateji ömrü boyunca aynı worker'da kalır. Stop/start döngüsünde yeniden eklenmez; worker zaten `!isRunning()` olanı atlar. `removeStrategy` (soft-delete) **hiç çağrılmaz**.
- **Döngü** (`AlgoWorker::workerLoop`): `drainPending()` → `strategies` vektörü (yalnız worker thread'i yazar ve okur, kilitsiz; 2000 kapasite ayrılmıştır) → `markedForDeletion` veya `!isRunning()` olanları atla → `processInWorker()` (`doPeriodicChecks`). Canlı strateji yoksa 500 µs uyur, varsa **uykusuz spin** eder.
- **İstisna:** `processInWorker` istisna atarsa strateji `markedForDeletion=true` olur ve log'a `AlgoWorker: strategy [<key>] threw, removed from pool` yazılır. Yeniden `start()` bu bayrağı sıfırlar; strateji hâlâ vektörde olduğu için kaldığı yerden devam eder.
- **Sözleşme:** `doPeriodicChecks` bloklamamalıdır, çünkü aynı worker'daki bütün stratejileri durdurur. Arbitraj beklemeyi `retryAfterNs_` ile yapar: seans kapalıyken 200 µs, bir başka durumda 5 ms (`ArbitrageTracker::doPeriodicChecks`). `afterPeriodicChecks` havuz stratejileri için **hiç çağrılmaz**.
- ⚠ master'da farklı: Arbitraj da kendi thread'inde `while(isRunning()) doPeriodicChecks();` koşar.

### 4.3 Strateji kendi thread'i (`Strategy/BaseStrategy.h`)

`workAsyncron`: `beforePeriodicChecks()` → `while(isRunning()) doPeriodicChecks();` → `afterPeriodicChecks()`. İstisna yakalanır ve `logInfo` ile yazılır, thread biter, **ama `running` true kalır** (Şüpheli). Bekleme stratejinin kendi `sleep`'iyle yapılır. Kodda görülen değerler: FundTracker 5 ms, BasketArbitrage 5 ms, TradeByVolume (VWAP) 20–100 ms, MovingAverage/WarrantOverall 1 s. Strateji özelindeki ayrıntılar strateji dosyalarındadır.

### 4.4 Kuyruklar (`Observer/`)

- `Subscriber<T, L>`: `L` varsayılan olarak `moodycamel::ConcurrentQueue<T>` (`Containers/concurrentqueue.h`), alternatifi `tbb::concurrent_bounded_queue<T>`. API: `add` (enqueue/push), `tryPop` (bloklamaz). `clear()` boştur.
- `Notifier<T, L>`: `shared_mutex` korumalı `unordered_map<id, Subscriber*>`. `notifyAllUsers` paylaşımlı kilitle her aboneye `add` yapar (**fan-out kopyası**, sınırsız kuyruk, geri basınç yok).
- Kullanım ayrımı: piyasa/emir olayları ve strateji içi kuyruklar **moodycamel**'dir. GUI'ye giden akışlar (`GUIManager` notifier'ları, `StrategyManager::strategyNotifierMap`, özet aboneleri) **TBB `concurrent_bounded_queue`**'dur.
- `Subscriber` kimliği `IdGenerator`'dan gelir: `static unsigned short` sayaç, atomik değil, `short` olarak saklanır (Şüpheli).

### 4.5 Olay yolları ve sıra garantisi

```
ITCH SDK partition thread ─┬─ add/execute/delete/state ─► Notifier<Event> ─► OrderbookManager kuyruğu (moodycamel)
                           │                                                   └─► Marketbook güncelle ─► OrderDepth notifier'ları ─► strateji Subscriber'ları
                           └─ header_changed ─► (doğrudan, aynı thread) strateji Subscriber<ItchHeaderChangedDataPtr>
ouch-sdk callback thread ──► OuchManager ─► Userbook (AccountDepth) ─► notifier'lar ─► strateji Subscriber'ları; GUIManager
gRPC thread ──► StrategyManager::commandReceived ─► setCommand (stratejinin start/stop'u bu thread'de)
```

- **Aynı orderbook'un ITCH olayları sıralıdır.** Callback'ler tek partition thread'inden gelir, moodycamel aynı üretici için FIFO'dur ve tek tüketici vardır.
- **Farklı partition'lar arasında global sıra yoktur.** moodycamel üreticiler arası sıra vermez.
- **Header yolu ile defter yolu ayrıdır.** Header-changed tetiği stratejiye OrderbookManager'ı beklemeden ulaşır. Strateji tetiği aldığında `Marketbook` henüz o olayı işlememiş olabilir, ya da tersi. Aradaki tek ortak nokta saattir.
- **OUCH ve ITCH arasında sıra yoktur.** Kendi emrimizin execute'u OUCH'tan ve ITCH'ten farklı thread'lerden gelir.
- Strateji `Subscriber`'ına birden çok üretici yazar (OrderbookManager thread'i, ouch thread'i, ITCH thread'i). Kuyruk başına FIFO yalnız üretici başınadır.

### 4.6 Kilitler

| Kilit | Korur | Not |
|-------|-------|-----|
| `Manager::mutexStartStop` | start/stop | Strateji başına |
| `BaseStrategy::commandPtrMutex` | `setCommand` | `doPeriodicChecks` bu kilidi almaz |
| `ArbitrageTracker::ArbitragePackageMtx` | paket durumu, `setCommand` doğrulaması | Ayrıntı [arbitraj.md](../../20-stratejiler/arbitraj.md) |
| `ItchSdkManager::itchHeaderSubsMtx` (`shared_mutex`) | tetik aboneleri, `headerStates` | Callback'ler paylaşımlı, subscribe/unsubscribe ve `onHeaderSnapshot` özel kilit alır |
| `Notifier::mutex_` | abone listesi | |
| `AccountDepth::levelMutex` | kullanıcı defterinde add/execute | Yalnız defter yazımının bir kısmını kapsar |
| `AlgoWorkerManager::mapMutex_` | `strategyToWorkerMap_` | |
| `GUIManager::userListMtx` | yayın döngüsü / kullanıcı listesi | |
| **Yok** | `StrategyManager::strategyMap`, `strategyNotifierMap`; `Marketbook` (`OrderDepth::orderLevels` `std::map`); `TradableInstrument::accountbooks`, `stateName`; `OrderbookManager::instrumentMap` | Şüpheli |

## 5. `StrategyManager` ve strateji arayüzü

**Kayıt defteri:** `strategyMap: unordered_map<string, IStrategyPtr>`, **kilitsiz**. Anahtar `BaseCommand::getStrategyKey()` = `to_string((char)commandType)` + `orderbookId` + `exchangeInfo` + `strategyId` + `to_string(strategyType)`, **ayraçsız**. `(char)` dönüşümü `to_string`'te sayıya döner: Arbitraj `'3'` → `"51"`. Bu anahtar UI'nin `unique_key`'inden farklı bir uzaydır. `getStrategy(uniqueKey)` map'i lineer tarar ve `getSettings()->getUniqueKey()` ile karşılaştırır. `StrategyServiceImpl::generateStrategyKey` yalnız arbitraj için aynı formatı yeniden üretir.

**Oluşturma** (`commandReceived(BaseStrategyCommandPtr)`, gRPC veya main thread'i):
1. Anahtar yoksa `StrategyFactory::createStrategy(cmd)`. Fabrika istisna atarsa (enstrüman yok, arbitrajda dayanak ile türev aynı, BYF'de vadeli/endeks yok, bilinmeyen tip) hata loglanır ve **sessizce dönülür**: gRPC'ye yine `OK` gider.
2. `setCommand(cmd)`. İstisna atarsa ve strateji yeni eklenmişse `cmd->stop()` çağrılır, map'ten silinir ve istisna yeniden fırlatılır. `StrategyStartException` gRPC'de `FAILED_PRECONDITION`, diğerleri `INTERNAL` olur. ⚠ master'da yok: bu geri alma ve `StrategyStartException` yoktur.
3. Havuz stratejisi ve çalışıyorsa `assignStrategy` (§ 4.2).

Stratejiler map'ten **hiç silinmez** (2. adımdaki geri alma dışında). Stop edilen strateji nesnesi, abonelikleri ve logger'ı süreç boyunca yaşar.

**GUI yolu** (`commandReceived(map, uniqueKey)`): `CommandFactory::createStrategyCommand` → yukarıdaki akış. Endeks varantında (`WarrantTracker`, obid `XU30_INSTRUMENT_ID`=3) en yakın `F_XU030` vadelisi için ikinci bir strateji de açılır. Ardından `saveStrategySettings(message)` (DB'ye yazar) ve `setStrategyNotifier` (GUI akışı) çağrılır.

**DB'den restore** (`readAlgoSettings`, açılışın 9. adımı): `DatabaseServiceClient::getStrategySettings()` bütün kayıtları getirir. Her kayıt için `convertAlgoSettings` `Algo*Value` tiplerini `clientmodels::*Value` tiplerine çevirir (Int/Long/String/Double/Bool; diğer tipler **düşer**), sonra `CommandFactory` → `commandReceived(cmd)` çağrılır. `STRATEGY_STARTED` true ise strateji başlatılır. Kayıt başına hata loglanır ve sonraki kayda geçilir. Restore yolu `setStrategyNotifier` çağırmaz.

**Toplu güncelleme** (`StrategyServiceImpl::UpdateExtSettings`): `stopStrategies(keys)` çağrılır. `is_finish_updating` ise DB'den yeniden okunur: `updateStrategies` (eşleşen kayıtlar için `commandReceived` + `setStrategyNotifier`) ve `updateStrategyStates` (`updateStateFromDatabase`). Anahtarlar arbitraj formatındadır.

**`stop()`**: map'teki bütün stratejiler için `stop()`.

**Arayüz:**
- `IStrategy` (`Strategy/IStrategy.h`, `Manager`'dan türer). Saf metodlar: `setCommand`, `getSettings`. Boş varsayılanlı metodlar: `setBalance`/`executeUnderlying` (`UNIMPLEMENTED`), `deletePackage`, `updatePackage`, `sendAllPackages`, `updateStateFromDatabase`, `sendSnapshotOfStrategy`, `trackerStopped`, `notifiedForSummaryChanges`.
- `BaseStrategy<InstrumentType, CommandType>`: `setCommand` `commandPtrMutex` alır, komutu `dynamic_pointer_cast` ile değiştirir ve `isStarted()`'a göre `start()`/`stop()` çağırır, ardından durum aboneleri bilgilendirilir. `startProperly` = `commandPtr->start()` + bildirim; `exitProperly` = `commandPtr->stop()` + bildirim + `strategyCommandNotifier`. Kancalar: `doPeriodicChecks` (saf), `beforePeriodicChecks`, `afterPeriodicChecks`. Yardımcılar: `getPosition` (Userbook istatistiklerinden alış−satış lot), `cancelAll*`/`cancelSingleOrder` (OrderbookManager üzerinden). Yıkıcı `stop()` çağırır ve stderr'e `STRATEGY DESTRUCTOR CALLED` basar.
- `StrategyFactory` (`Strategy/StrategyFactory.h`): `Commands` → sınıf eşlemesi. `'6'` TradeByVolume (VWAP), `'V'` TradeByVolumeOverall, `'8'` TradeByBSRatio, `'9'` WarrantTracker (varantsa) veya WarrantUnderlyingTracker, `'T'` WarrantOverallTracker, `'4'` MovingAverageTracker, `'d'` FundTracker, `'3'` ArbitrageTracker (türev `DerivedInstrument`, dayanak `TradableInstrument`), `'E'` BasketArbitrageTracker (vadeli + `Index` dayanak). obid `ALL_INSTRUMENTS`=99000000 ise enstrüman aranmaz. Hangilerinin kullanıldığı: [katalog](../../20-stratejiler/README.md).

## 6. ITCH entegrasyonu (`ItchSdkManager`, `OrderbookManager`)

**Başlatma:** `itchsdk_set_arguments` → config'ten `ItchSdkConfigurations` (multicast listesi, log dizini/seviyesi, `itchOnloadStackName`, ring boyutları, receiver çekirdekleri, Glimpse/Rewinder zaman aşımları) → `itchsdk_initialize` → config'teki **her pazar** için `itchsdk_subscribe_snapshot_end(market, onSnapshotEnd)` → `itchsdk_start()` (bloklar). SDK'ya verilen işaretçiler üye alanlarda tutulur.

**Snapshot-end** (`onSnapshotEnd`, SDK thread'i): Her orderbook için önce `ItchSnapshot` olayı yayınlanır. Bu olay `internString`/`internOrders` ile kalıcı belleğe kopyalanır, çünkü SDK snapshot'ı callback dönünce serbest bırakır. Snapshot emirleri `OrderAddEvent` dizisine çevrilir (`rankingSequenceNumber` = kademe içi sıra, `ts=0`). Sonra o orderbook için 4 canlı abonelik açılır: add, executed, delete, state. `completedMarkets ≥ expectedMarkets` olunca bir kez global `ItchSnapshotEnd` yayınlanır.

**K-126 ile ilişkisi:** SDK snapshot-end'de `market`'i saklamıyor ([itch-sdk Şüpheli](../itch-sdk/abonelik-api.md#şüpheli)). İki pazar açıksa her snapshot `onSnapshotEnd`'e iki kez gelir:
- `completedMarkets` ilk pazardan sonra 2 olur ve `ItchSnapshotEnd` **ikinci pazarın snapshot'ından önce** kuyruğa girer.
- `orderbookInitialized` (endeksler, `findNearestFutureInstrument`, dayanak ilişkileri) ikinci pazarın enstrümanları yokken çalışır.
- İkinci `ItchSnapshot` `Instrument already exists` hatasıyla reddedilir, ama canlı abonelikler iki kez açılır ve her olay iki kez işlenir.
- ❓ doğrulanmadı: prod config'inde iki pazar da açık mı; bu etkiler sahada görüldü mü.

**Hazır olma:** `OrderbookManager` tüketicisi `ItchSnapshotEnd`'i işleyince `orderbookInitialized()` çalışır:
1. `createIndices` (fiktif ayarlar + DB'den `getFictiveItemSettings`, **tüketici thread'inde senkron gRPC**)
2. `findNearestFutureInstrument` (adı `F_XU030` ile başlayan en yakın vade)
3. `createUnderlyingRelations` (`underlyingId` eşleşmesi; vadeli dayanak yalnız varantlar için, en yakın endeks vadelisi yalnız `setNearestIndexFuture` true dönen türevler için)
4. Her enstrümanın `orderbookInitialized`'ı
5. `initialized=true`, ardından `indexCalculator` başlar

Uygulama bunu 600 s bekler (§ 1).

**Olay işleme** (`OrderbookManager::parseEvent`):
- `ItchAddOrder`/`ExecuteOrder`/`DeleteOrder` → `TradableInstrument` → `Marketbook`.
- `ItchSnapshot` → `SettingsManager` ayarı + `OrderbookDirectory` ile `InstrumentFactory::createTradableInstrument`, snapshot emirleri ve durum.
- `ItchStateChanged` → `addState` (`stateName` + `stateChangeNotifier`).
- `ItchHeaderChanged` dalı **ölüdür**: SDK v3 köprüsü bu olayı `Notifier<Event>`'e koymaz.
- `ItchEquilibriumPriceUpdate` boştur.
- Bilinmeyen orderbook'un olayları `getTradableInstrument` içinde loglanıp atılır.

**Header tetikleri** (strateji yolu): `subscribeToItchHeaderChangeEvents[WithoutSnapshot](subscriber%2C%20obid%2C%20key)`. obid başına tek bir SDK `header_changed` aboneliği açılır, anahtar başına abone tutulur. v3 iki tarafı birlikte bildirir; `HeaderState` farkıyla v2 tarzı **tek taraflı** `ItchHeaderChangedData` olaylarına bölünür (fiyat raw, miktar lot, `timestamp` SDK'dan). "Snapshot'lı" abonelik ayrıca tek seferlik `header_snapshot` açar: orderbook'un bir sonraki hareketinde iki taraf bekleyen anahtarlara gönderilir ve abonelik kendini kapatır. Arbitraj `WithoutSnapshot` kullanır.

**Zaman damgası:** add ve state olaylarında `timestamp` = callback anı (v3 add'de `packetTs` yoktur), execute ve delete olaylarında `packetTs`.

⚠ master'da farklı: ITCH SDK v2. Tek bir `itchEventReceived` callback'i bütün olayları alır; `"g…"` ön ekli GUI aboneleri için ham BIST byte'ları üretilir (çağıranı yok, ölü). Glimpse-end ayrı bir abonelikle gelir, tetikler `subscribeOnlyTrigger` ile kurulur. Tick size `getTickSize` ile okunur.

## 7. Emir defteri modeli ve enstrümanlar

**Defterler** (`Orderbook/`):
- `Orderbook<OD>`: alış ve satış `OD` + `lastPrice`.
- `Marketbook` = `Orderbook<OrderDepth<MarketOrder, OrderLevel>>`: piyasanın **emir bazlı** tam defteri. Bütün enstrümanlar için tutulur (HFT'den farkı budur). Strateji tipi `USER`.
- `Userbook` = `Orderbook<AccountDepth<UserOrder, AccountLevel>>`: (hesap, strategyId, strategyType) başına kendi emirlerimiz. `TradableInstrument::accountbooks`, anahtar `<account>_<strategyId>_<strategyType>`. `addUserbook` ile açılır: açılışta `createUserbooks` (ouch-sdk strateji bilgileri), sonra komutlarla.
- `OrderDepth`: `orderLevels` `std::map<fiyat, Level*>` (`LevelComparator`: alışta büyükten küçüğe, satışta küçükten büyüğe; `begin()` = header), `orderMap` (MarketBook'ta ITCH orderId, UserBook'ta borsa token'ı → `Order*`), `totalQuantity`, `lastPrice`, `Statistics`. Notifier'lar: `notifierMap` (olay tipi veya emir tipi char'ı), `notifierMapNew`, `addOrderNotifierMap`, `cancelOrderNotifierMap`, `headerChangeNotifier`. Stratejiler `TradeDataPtr` aboneliklerini buradan kurar.
- Davranış: duplicate add → eski emir silinip yeniden eklenir. Add karşı tarafta aynı fiyatta bir seviye bulursa o seviyeyi siler (`removeLevelIfExists`, WARN). Execute miktar düşer, miktar 0 olursa emir silinir; `lastPrice` = execute fiyatı. Seviye miktarı < 1 olunca seviye silinir ve header yeniden hesaplanır. `Level*` nesneleri map'ten silinirken `delete` edilmez.
- `AccountDepth` OUCH olaylarını `levelMutex` ile yazar ve `ouchHistory` tutar. Emir tarafı ayrıntısı emir-yolu dokümanındadır.

**Enstrüman hiyerarşisi** (`Instruments/`):
```
Instrument (soyut)
├── TradableInstrument ── Equity (+UnderlyingInstrument)
│                       └ DerivedInstrument ── Future (+UnderlyingInstrument)
│                                            └ Option ── Warrant
└── FictiveInstrument ── Index (+UnderlyingInstrument)
```
`InstrumentFactory` `financialProduct`'a göre sınıf seçer: Option, Future, Cash → Equity, EquityWarrant → Warrant, diğerleri → düz `TradableInstrument`; Index → `Index`. `TradableInstrument` = ITCH snapshot (`OrderbookDirectory`) + DB ayarı (`prevClosePrice`, `minPrice`, `maxPrice`, `maximumValue`). DB'de olmayan enstrüman boş ayarla oluşur.

**Fiyat ölçeği:**
- `Marketbook`/`Userbook` fiyatları, `Instrument::lastPrice`, `getPriceStep` **raw tamsayı fiyattır** (ITCH `prx`).
- `decimalPrice` ITCH snapshot'ından gelir. `priceDivider = 10^decimalPrice`; `getLastPriceDouble() = lastPrice / priceDivider` TL verir. Spot için tipik değer `decimalPrice=3` (TL × 1000). ❓ doğrulanmadı: VİOP enstrümanlarının değeri.
- `getPriceStep(price)` = `itchsdk_get_tick_size(obid, raw)`. 0 dönebilir; `isValidPrice` 0'da false döner, deprecated `getValidPrice` ve `get*PriceLimit` ise 0'a bölebilir.
- `priceRange` = DB `last_price` ±%10. `getMinPrice`/`getMaxPrice` DB'den gelir. ❓ doğrulanmadı: DB `last_price`/`min_price`/`max_price`'ın raw mı TL mi olduğu (trade-data-app tarafına bakılmalı).
- `getTradeVolume()` = istatistik hacmi / 10^decimalPrice.

**Fiktif endeks** (`Index.h`): Bileşenler DB'deki fiktif kalemlerden gelir (endeks adı + hisse adı). Fiyat = Σ(bileşen `lastPrice` raw / `indexCurrencyRate` × `totalNumberOfShares` × `freeFloatRatio` × `weightingFactor` / `priceDivider`) / `indexDivisor`. Sonuç **raw değil TL tabanlıdır**; `getLastPriceDouble` doğrudan `lastPrice` döner. Hesap `indexCalculator`'da 150 ms'de bir yapılır, ancak bütün bileşenlerin `lastPrice > 0` olması ve en az birinin sürekli işlemde olması gerekir. Değer değişince `priceChangeNotifier` ve `tradeNotifier` yayınlanır. BYF (Sepet Arbitraj) bunu dayanak olarak kullanır.

**Seans:** `isContinuousSession` `stateName`'i Spot'ta `SurekliMuzayede`, VİOP'ta `ViopSurekliMuzayede` ile karşılaştırır (`OrderUtility` sabitleri).

## 8. Logger, PerfSDK, Sentry

- **Logger** (`Logger/Logger.h`): `nanolog::GuaranteedLogger`. Dosya `logDirectory/<logFile>_<tarih>` ve 1000 MB'ta döner (`log_file_roll_size_mb`). Seviye `logLevel`'dan gelir ([config.md](config.md)). `logError` → `LOG_CRIT`, `logWarning` → `LOG_WARN`, `logInfo`/`logDebug` → `LOG_INFO`. `start()` öncesindeki çağrılar **sessizce düşer** (`isStarted`). Kodun bir kısmı `LOG_INFO <<` makrolarını doğrudan kullanır.
- **Strateji logger'ı** (`Logger/StrategyLogger*.cpp`): `StrategyLoggerManager::createStrategyLogger(key, obid, exchangeInfo, command)` anahtar başına tek logger tutar. Dosya `strategyLogPath/<komut adı>/<exchangeInfo>/<enstrüman adı>.csv`; dizinler yoksa `mkdir` ile açılır. Her logger'ın detached bir thread'i vardır: `std::queue` + `mutex` + `condition_variable`. WarrantTracker, TradeByBSRatio ve TradeByVolume için CSV başlığı yazılır, dosya append modunda açılır. `log()` yalnız `running` iken kuyruğa ekler.
- **PerfSDK** (`HAS_MAPERFSDK` + `monitoringEnabled`): servis adı `algo_prod`. Metrikler: `itchEventReceived` (execute callback'inde şimdi − `packetTs`), `orderbookEventReceived` (kuyruk gecikmesi; add ve state'te callback anına göre), arbitraj `arb_rplc`, `arb_spot`, `arb_hdr`, `arb_loop`, `TIME_MEASUREMENT` makrosu. ⚠ master'da farklı: string adla eski API (`BenchmarkElapsedTime("…")`), `registerMetric` yok.
- **Sentry**: § 1. `debug=1` olduğu için stderr'de `[sentry]` satırları görülür.

## Şüpheli

- **bug? Gün sonu kapanışı hiç tetiklenmiyor.** `OrderbookManager::eventNotifier`'a yayın yapan kod yok (development ve master). README "EndOfMessages gelince kapanır" diyor, [log-imzalari § 5](../../40-operasyon/log-imzalari.md#5-kapanış) de AlgoProd'un kendiliğinden kapandığını yazıyor. Kodda bu yol ölü; SIGTERM handler'ı da yorumda. Düzenli kapanış yalnız SIGINT/SIGHUP/SIGUSR1/2 ile olur.
- **bug? K-126 erken `ItchSnapshotEnd` (doğrula).** İki pazar açıksa `orderbookInitialized` ikinci pazarın enstrümanları gelmeden çalışır. Sonuç: VİOP vadelileri için dayanak ilişkisi, `nearestFutureInstrument` ve fiktif endeks bileşenleri eksik kalabilir; canlı olaylar çift işlenir (§ 6).
- **doğrula: snapshot ile canlı olay arasında üreticiler arası sıra yok.** `ItchSnapshot` snapshot-end thread'inden, aynı orderbook'un canlı olayları partition thread'inden kuyruğa girer. moodycamel üreticiler arası sıra vermez. İlk canlı olay instrument oluşmadan tüketilirse sessizce atılır.
- **bug? Kilitsiz paylaşılan yapılar.** `Marketbook` (`std::map`) OrderbookManager thread'inde yazılırken strateji ve gRPC thread'leri `getHeader`/`headerValues`/`getLevel` ile okuyor. `strategyMap`'e gRPC thread'leri ve açılış (restore) aynı anda yazabiliyor (7. adım 9'dan önce). `accountbooks`, `stateName` (std::string) ve `strategyNotifierMap` de korumasız.
- **bug? `getUniqueKey()` her çağrıda `uniqueKey`'i yerinde değiştiriyor** (`erase`). Çok thread'den çağrıldığında `std::string` üzerinde veri yarışı oluşur.
- **bug? `readAlgoSettings`/`updateStrategies` anahtar kırpması bir karakter fazla siliyor**: `erase(0, find_first_not_of(ws)+1)`. Restore'da yalnız log'u etkiler. `updateStrategies`'te `setStrategyNotifier(uniqueKey)` bu kırpık anahtarla çağrılıyor, GUI akışı yanlış anahtara bağlanabilir (doğrula).
- **bug? Strateji thread'i istisnayla biterse `running` true kalıyor.** Strateji GUI'de çalışıyor görünür ama döngüsü yoktur. Stop/start ile kurtulur.
- **bug? `Manager::stop` detach ediyor.** Stop sonrası hızlı bir start eski thread hâlâ `doPeriodicChecks` içindeyken yenisini açabilir: aynı strateji iki thread'de koşar. Havuz stratejisinde `exitProperly` çağıranın thread'inde, worker `doPeriodicChecks` içindeyken çalışır.
- **bug? Fabrika hatası gRPC'ye `OK` dönüyor.** `commandReceived(BaseStrategyCommandPtr)` istisnayı yutup `return` ediyor. Ardından `saveStrategySettings` DB'ye yine yazıyor.
- **bug? `Subscriber` kimliği `unsigned short`, atomik değil.** 65535 aboneden sonra sarar; aynı id'li ikinci abone `Notifier::subscribe`'da sessizce eklenmez. Her strateji birden çok `Subscriber` açıyor ve stratejiler hiç silinmiyor.
- **bug? Busy-spin thread'ler.** OrderbookManager tüketicisi ve GUIManager `worker`'ı uykusuz döner; canlı strateji varken AlgoWorker'lar da öyle. Pinleme yok, bu yüzden ITCH SDK'nın pinli çekirdekleriyle çakışabilir. Bu durum `workerCount` + 2 çekirdeği sürekli meşgul eder.
- **bug? `stopItchSdkManager` iki kez çağrılıyor** (§ 2). `itchsdk_shutdown` sonrası ikinci `itchsdk_stop` davranışı ❓.
- **bug? `StrategyLogger::stop` `cv.notify` yapmıyor.** Thread `cv.wait`'te sonsuza kadar kalır. Kuyrukta `nullptr` mesaj olursa iç döngü `pop` etmeden `continue` eder ve sonsuz döngüye girer.
- **doğrula: `getStrategyKey` ayraçsız.** `obid` + `exchangeInfo` + `strategyId` birleşimi farklı üçlüler için aynı diziyi üretebilir. Pratikte hesap kodu harfle başlıyorsa çakışmaz.
- **ölü kod:** `runProduction`/`runUnitTests`/`runPriceChanger`, `parseEvent` içindeki `ItchHeaderChanged` dalı, `TradableInstrument::headerChanged`/`headerChangeNotifier`, `OuchManager::replay_completed` (set ediliyor, okunmuyor), `AlgoWorkerManager::removeStrategy`, `DatabaseServiceClient::startVWAPAKDStream` (çağıranı yok), `triggerWorkerCount`.
