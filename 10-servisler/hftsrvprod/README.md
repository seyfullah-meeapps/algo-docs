---
kapsam: HftSrvProd (HFT strateji motoru) — dizin haritası, açılış, thread modeli, ITCH dağıtımı, emir yolu, gRPC katmanı, config, build, yeni strateji ekleme
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# HftSrvProd

HFT strateji motoru (C++20). Stratejiler için: [`20-stratejiler/`](../../20-stratejiler/README.md). Sistem içindeki yeri: [`00-genel/sistem-haritasi.md`](../../00-genel/sistem-haritasi.md).

## Dizin haritası (`src/`)

| Klasör | İçerik |
|--------|--------|
| `Main/HftMain.cpp` | `main()`: config, CPU pin, logger, PerfSDK, ITCH SDK, MAOrderSDK boot ve callback'leri, servislerin başlatılması, kapanış |
| `Strategy/` | `Strategy` taban sınıfı, strateji sınıfları, `StrategyDepth` / `StrategyLevel` (kendi emir derinliğimiz), `Service/StrategyServiceImpl` (gRPC stream'leri) |
| `Commands/` | GUI'den gelen komutlar. Strateji başına bir command, emir komutları (`EnterOrder`, `Cancel`, `Replace`, `CancelAll`, `SetBalance`, `ClosePosition`), durum/özet komutları. Fabrika: `CommandFactory.h`. |
| `Managers/StrategyManager` | Strateji kayıt defteri (`unique_key` → strateji), oluşturma, periyodik işler (second rule timer'ları), durum push'ları, replay gate |
| `Workers/` | `AlgoWorker` / `AlgoWorkerManager`: stratejileri işleyen thread'ler. `OuchWorker*` eski internal-OUCH kalıntısı. |
| `Clients/ItchSdkClient` | `libMAItchSDK` sarmalayıcısı. Abonelikler (header, level, execute, denge fiyatı, fiyat eşiği) ve olayların stratejilere dağıtımı. |
| `Clients/OuchManager` | ouch-sdk istemcisi (order-service'e): handoff öncesi yedek emir yolu, strateji kaydı, `orderUserDisconnected` (handoff), enstrüman cache'i |
| `Clients/OrderRegistry` | MAOrderSDK yolunun accept edilmiş emirleri (`client_order_id` → emir). Token-only execute/cancel olaylarını çözmek için kullanılır. |
| `Clients/DatabaseServiceClient` | trade-data-app gRPC `AlgoService` istemcisi (enstrümanlar, hesaplar, ayarlar) |
| `GUI/GUIManager` | gRPC sunucusu (:`grpcPort`, varsayılan 9050). GUI komutlarını dağıtır, manuel emirleri işler. |
| `Messages/` | OUCH/ITCH mesaj modelleri, `MsgConvert` (HFT ↔ MAOrderSDK dönüşümleri) |
| `Configuration/` | `Configuration.toml` (örnek), `ConfigurationManager` |
| `Globals/` | `GuiConstants.h` (**wire alan adları, tek otorite**), `Enumarations.h`, `GlobalConstants.h` (ret kodları vb.) |
| `License/` | Lisans kontrolü. `HftMain`'de yorum satırında, **çalışmıyor**. |
| `*.proto` | `strategies.proto` (StrategyService), `algo.proto` (AlgoService istemcisi), `ouch-data.proto`, `common.proto`. `buf generate` ile üretilir. |

## Açılış sırası (`HftMain.cpp`)

1. Argüman olarak config dosyası verilir. Onload derlemesinde `LD_PRELOAD=libonload.so` ile kendini yeniden başlatır.
2. Config yüklenir. Main thread `mainCpuCores`'a pinlenir (boşsa pin yok). Strateji ITCH kuyruk sınırı (`strategyQueueMaxEvents`) uygulanır. `sdkLockMemory` açıksa `mlockall`.
3. Logger başlar (Quill, `<logFile>/hft.txt`, 1 GB'ta döner, 30 dosya). PerfSDK başlar (`monitoringEnabled`).
4. **ITCH SDK** başlar (`ItchSdkClient::startItchSdkClient`), orderbook durum abonelikleri kurulur. MAOrderSDK combiner ITCH'e ihtiyaç duyduğu için önce bu yapılır.
5. **MAOrderSDK boot**, adımların sırası zorunludur:
   1. `OuchConfig`
   2. `OrderSdkConfig` (combiner, onload, recv pin, replay quiet window, hard cap)
   3. `setInstrumentLimits` (DB'den max emir değeri, ondalık, brüt takas)
   4. `setStartArguments` + `bootstrapOnloadIfRequested`
   5. callback'ler (`onAccepted`, `onRejected`, `onExecuted`, `onWireExecuted`, `onReplaced`, `onCanceled`, `onReplayCompleted`)
   6. `start`
   - **Login yapılmaz**; OUCH kullanıcıları handoff ile gelir (bkz. sistem haritası → OUCH handoff).
6. `AlgoWorkerManager`, `GUIManager` (gRPC), `ItchManager`, `StrategyManager` periyodik işleri ve durum worker'ı başlar.
7. Konsola durum kutusu basılır: Onload, DB, bağlı OUCH kullanıcı sayısı, worker sayısı, uptick, monitoring, combiner, log seviyesi. Linklenen bütün MeeApps kütüphanelerinin git sürümü de basılır (`ma::build::PrintAll`).
8. Ana döngü sinyal bekler. Kapanış main thread'de yapılır; sinyal handler yalnızca bayrak çevirir.

## Thread modeli

| Thread | Ne yapar |
|--------|----------|
| ITCH SDK thread'leri (`libMAItchSDK` içi) | Multicast alımı, emir defteri, abonelik callback'leri → `ItchSdkClient` olayı stratejinin kuyruğuna koyar |
| **AlgoWorker** (`workerCount`) | Stratejiler worker'lara round-robin dağıtılır. Her worker döngüde kendi stratejilerinin `processSingleEvent()`'ini çağırır (busy-loop). Strateji kararları burada verilir. |
| MAOrderSDK OUCH recv thread'leri (kullanıcı başına) | `onAccepted` / `onRejected` / `onReplaced` / `onCanceled` / `onWireExecuted` → `strategy->addOrder/rejectOrder/...` |
| Combiner (açıksa) | `onExecuted` **ITCH client thread'inden** gelebilir (ITCH'te görülen fill OUCH'tan önce uygulanır). GUI'ye giden fill ise `onWireExecuted` ile OUCH thread'inden gider; sıra korunur. |
| gRPC (GUIManager) | GUI komutları. `setCommand` buradan çağrılır. |
| StrategyManager periodic jobs | Second rule / reClose timer'ları. Karar vermez, olay kuyruğa atar veya `sendSecondRuleOrder` çağırır. |
| StrategyStatesWorker | Dirty işaretli stratejilerin durum/özet push'u |

**Hot/cold öncelik:**
- `hotWorkerCount > 0` ise worker'lar önce `isHot` stratejileri, sonra soğukları işler.
- `realHotReadyQueue` (veya env `HFT_REAL_HOT_READY_QUEUE=1`) açıksa hot stratejinin olayı worker'ın hazır kuyruğuna doğrudan konur.
- Tavan/Taban fiyat eşiğine göre hot/cold geçer. Ayrıntı [tavan.md](../../20-stratejiler/tavan.md).

**Kuyruk sınırı:** Strateji başına ITCH kuyruğu `strategyQueueMaxEvents` (örnekte 50000). Aşılırsa eski olaylar düşürülür (`getDroppedItchEvents`).

**Kilitler:** Her strateji kendi `buySellInfoMutex`'ini kullanır (`recursive_timed_mutex`). HFT Classic ITCH yolunda kilidi 100 µs dener ve alamazsa olayı düşürür. Stratejiye özel kilitler (`warrantMutex`, `derivativeMutex`) ilgili strateji dokümanlarında.

## Emir gönderme deseni

Bütün stratejiler aynı deseni kullanır:

```cpp
if (!maosdk || !maosdk->enterOrder(HftConvert::toSdkMsg(order, account, fatherRef))) {
    if (!maosdk || !maosdk->ownsAccount(account))
        OuchManager::instance().enterOrder(order, account, fatherRef);   // order-service yedek yolu
}
```

- SDK hesabın sahibiyse (handoff sonrası) emir doğrudan BIST'e gider.
- SDK hesabın sahibi değilse (handoff öncesi) emir ouch-sdk üzerinden order-service'e gider.
- SDK sahip olduğu halde `false` dönerse (bağlantı yok vb.) emir **gönderilmez**. Strateji kendi kurtarma mantığına güvenir.
- Replace/cancel için `ownsOrder(token)` kullanılır.
- **Father order ref:** Büyük emirler parçalanabilir. Aynı father ref'i taşıyan parçaların accept'leri toplanarak "ailenin tamamı kabul edildi" bilgisi çıkarılır (Tavan/Taban `orderCompletelyAccepted`).
- **Replay gate:** Handoff sonrası OUCH replay bitene kadar (`ouchReplayComplete()`) stratejiler emir göndermez, çoğu ITCH olayı da işlemez.
- **Çift accept koruması:** Handoff replay'i order-service yolunda işlenmiş bir accept'i tekrar getirebilir. `OrderRegistry::addAcceptedOrder` + `OuchManager::claimGlobalAcceptedToken` stratejiye yalnızca ilk kaydın ulaşmasını sağlar.

## gRPC (`StrategyService`, :9050)

İstemci trade-data-app'tir.

| RPC | Ne |
|-----|----|
| `StrategyLogin` | trade-data-app login |
| `SetCommandRequest` | Strateji komutu (başlat/durdur/ayar), emir komutu (`Command_Type_OrderRequest`), cancel-all, set balance… → `GUIManager` dispatch |
| `FetchCommands` (stream) | Strateji snapshot'ları, durum ve özet mesajları, Varant Toplu olayları → GUI |
| `FetchOrders` (stream) | Emir olayları (accepted / executed / replaced / canceled / rejected, latency alanlarıyla) → GUI |
| `SubscribeToCommands` / `UnsubscribeFromCommands` | GUI istemcisinin hangi stratejileri dinlediği |
| `SubscribeToOrderbook` | Strateji emir defteri işaretleri |
| `AlgoSetAccountStrategy` | Hesap–strateji eşlemesi (toplu emirlerde kullanılır) |
| `FetchAllUniqueKeys` | Var olan stratejiler |
| `UpdateExtSettings` | Ek ayar güncellemesi |

Wire biçimi: `map<string, google.protobuf.Any>`. Alan adları ve tipleri `src/Globals/GuiConstants.h`'ta tanımlıdır. Yeni bir alan için trade-data-app'te proto değişikliği **gerekmez**, alan generic map'te taşınır. DB'ye kalıcı olması için `StrategyAttributes` satırı eklenmelidir.

## Config (`Configuration.toml`)

Önemli anahtarlar. Değerler ortama göre `algo-configs` / `Algo-Setup`'tadır; gizli bilgiler burada yer almaz.

| Anahtar | Anlam |
|---------|-------|
| `workerCount`, `algoWorkerCores` | AlgoWorker sayısı ve CPU pinleri (boş = pin yok) |
| `hotWorkerCount`, `realHotReadyQueue` | Hot öncelik |
| `activationPctFromPreviousClose` (6.5), `demoteBandTicks` (2), `minTierBandTicks` (1), `minHotDwellMs` (250), `coldReentryCooldownMs` (250), `emergencyReentryTicks` (2) | Tavan tiering eşikleri (parantez içi varsayılanlar) |
| `mainCpuCores` | Main ve yardımcı thread'lerin pini. ⚠ 2026-06'da host'u kilitlediği için kapalı tutuluyor. |
| `strategyQueueMaxEvents` | Strateji ITCH kuyruk sınırı |
| `sdk*` | MAOrderSDK: `sdkLockMemory` (kapalı, host hang), `sdkUseOnload`, `sdkRecvPinCore`, `sdkReplayQuietWindowMs` (10000, prod doğrulaması olmadan kısaltmayın), `sdkOrderHardCapTry` (tek emir notional sınırı, tam TL), `sdkHeartbeatIntervalMs`, `sdkTokenPoolSize` |
| `[[ouch_users]]` | Yalnızca recv-thread ayar tablosu. Kullanıcılar handoff'tan öğrenilir. |
| `dbIp`/`dbPort` | **trade-data-app gRPC** (MySQL değil) |
| `ouchIp`/`ouchPort` | **order-service MARpc** (BIST değil) |
| `grpcPort` | StrategyService portu |
| `combinerEnabled` | MAOrderSDK ITCH+OUCH execute combiner |
| `uptickEnabled` / `uptickRule` | Uptick kuralı |
| `monitoringEnabled`, `monitoringPort`, `perf*` | PerfSDK → ClickHouse (`perfDb*`). `monitoringPort` artık kullanılmıyor; kod yorumlarındaki "Prometheus" eski. Bkz. [performance-sdk](../performance-sdk/README.md). |
| `[[markets]]` | Spot (4 partition) ve Future (6 partition): ITCH multicast, Glimpse, Rewinder adresleri, birincil/ikincil hat |
| `onloadStackName`, `itchOnloadStackName` | Onload stack adları |
| `logLevel` | `debug` ITCH yükünde log seli yaratır |

## Build

- CMake + `buf generate` (`src/`). Bağımlılıklar `/usr/local/lib`'den alınır: `libouchSDK`, `libMAItchSDK`, `libMAOrderSDK`, `libMAPerfSDK`, cpprest, gRPC/protobuf, OpenSSL, OpenMP. Onload (`onload_ext`) veya Mellanox (`vma`) bulunursa hızlandırma derlenir.
- CI: [`00-genel/branch-ve-ortamlar.md`](../../00-genel/branch-ve-ortamlar.md). Regular ve Onload binary'leri Algo-Setup `HFT/HftSrvProd/` altına yazılır.

## Yeni strateji eklemek (kontrol listesi)

1. `common.proto` `StrategyType` enum'una değer ekle. **Bütün repolarda aynı numarayla**: HftSrvProd, order-service, trade-data-app, ouch-sdk enum'u, UI `app/types/index.ts`.
2. `Commands/<X>Command.{h,cpp}`: alanları `GuiConstants.h`'a ekle; `toClientMessage` ve `getDefaultSettings` yaz.
3. `Strategy/<X>.{h,cpp}`: `Strategy`'den türet; `setCommand`, `processSingleEvent`, OUCH callback'leri.
4. `CommandFactory::createStrategyCommand` ve `StrategyManager::createStrategy`'ye case ekle. İkisinden biri eksikse strateji oluşmaz (OrderChase örneği).
5. trade-data-app: `getApplicationFromStrategyType` (gui_api.go), WS `getApplicationFromStrategyType` / `ConvertStrategyType`, `StrategyAttributes` SQL satırları.
6. UI: `STRATEGY_WORKSPACE_CONFIGS`, route, paneller.
