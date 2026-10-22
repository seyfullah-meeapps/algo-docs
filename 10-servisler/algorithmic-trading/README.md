---
kapsam: AlgorithmicTrading (AlgoProd) — dizin haritası, açılış, strateji çalıştırma modeli, emir yolu, gRPC, config, build
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
dogrulama: 2026-10-22
durum: taslak
---

# AlgorithmicTrading (AlgoProd)

İkinci strateji motoru (C++). Arbitraj, VWAP, Fon Takibi ve Sepet Arbitraj burada çalışır. Binary adı ve log/metrik adı **AlgoProd** (`algo_prod`); trade-data-app config'inde `algotrading`.

Stratejiler: [arbitraj.md](../../20-stratejiler/arbitraj.md), [vwap.md](../../20-stratejiler/vwap.md), [fon-takibi.md](../../20-stratejiler/fon-takibi.md). Kodda duran ama kullanılmayanlar: [katalog](../../20-stratejiler/README.md#kullanılmayan-kod).

⚠ Eski bilgi tabanında bu repo hiç anlatılmıyordu.

## Dizin haritası (`algoSrc/`)

| Klasör | İçerik |
|--------|--------|
| `SourceFiles/` | `Main.cpp`, `Application.cpp` (başlatma ve kapatma sırası) |
| `Managers/` | `OrderbookManager` (enstrümanlar + emir defterleri), `ItchSdkManager` (ITCH SDK), `OuchManager` (ouch-sdk istemcisi → order-service), `GUIManager` + `StrategyServiceImpl` (gRPC), `StrategyManager` (strateji kayıt defteri), `SettingsManager` |
| `Strategy/` | Strateji sınıfları, `BaseStrategy` / `IStrategy`, `StrategyFactory`, `StrategySummary`, `StrategyActivities` |
| `Commands/` | Komutlar; iç komut kodları `Globals/Enumarations.h` `Commands` enum'u (char) |
| `Instruments/` | Enstrüman hiyerarşisi: `Equity`, `Future`, `Option`, `Warrant`, `Index` (fiktif), `DerivedInstrument` (vade, dayanak) |
| `Orderbook/` | Kendi emir defteri modeli (`OrderDepth`, `OrderLevel`, `AccountDepth`) |
| `ItchMessages/`, `OuchMessages/`, `Transactions/` | Mesaj modelleri |
| `Data/` | trade-data-app istemcisi (`DatabaseServiceClient`), `ArbitrageData`, `BYFData` |
| `Workers/` | `AlgoWorker` / `AlgoWorkerManager` (worker havuzu) |
| `Logger/` | NanoLog + strateji başına logger (`StrategyLogger`) |
| `Utilities/GuiConstants.h` | **Wire alan adları** (`ARB_*`, `VWAP_*`, `BYF_*`…) |
| `Configuration/Configuration.ini` | Örnek config (özel `$Bölüm … &Bölüm` sözdizimi) |
| `holidays.csv` | BIST tatil günleri (vadeye kalan süre hesabı) |
| `*.proto` | HftSrvProd ile aynı servis sözleşmeleri, AlgoProd'un kendi kopyası |

## Açılış sırası (`Application::runTests`)

Kodda üretim yolu `runTests()` adını taşıyor.

1. PerfSDK (`monitoringEnabled`)
2. Logger
3. `OrderbookManager.start()`
4. `ItchSdkManager.startItchSdkManager()`: Spot + VİOP ITCH (Glimpse snapshot, multicast, Rewinder). Emir defteri hazır olana kadar en fazla 600 sn beklenir; dolarsa uygulama exception ile başlamaz.
5. `OuchManager.start()`: order-service'e MARpc ile bağlan (`ouchIp:ouchPort`, kullanıcı `algoUser`).
6. `GUIManager.start()`: gRPC sunucusu (`clientPort`, örnek 9098).
7. `AlgoWorkerManager.start()`
8. `StrategyManager.start()`: DB'deki strateji ayarlarını okur (`readAlgoSettings`) ve stratejileri yeniden oluşturur.

ITCH `EndOfMessages` (gün sonu) gelince veya sinyal gelince kapanır.

## Strateji çalıştırma modeli

İki model vardır:

| Model | Kim | Nasıl |
|-------|-----|-------|
| **Kendi thread'i** | VWAP, Fon Takibi, diğerleri | `BaseStrategy::workAsyncron`: `while(isRunning()) doPeriodicChecks();`. Strateji kendi `sleep`'ini yapar (VWAP ~100 ms, Fon ~5 ms). |
| **Worker havuzu** (`runsOnWorkerPool() == true`) | Arbitraj | `AlgoWorkerManager`'a atanır. `doPeriodicChecks()` **bloklamamalıdır**; bekleme `sleep` yerine `retryAfterNs_` ile yapılır. |

Piyasa ve emir olayları stratejiye `Subscriber`/`Notifier` kuyrukları ile gelir (`moodycamel::ConcurrentQueue`, TBB kuyrukları). Strateji bunları her döngüde `tryPop` ile boşaltır.

## Emir yolu

- **Bütün emirler** `OuchManager::send` → ouch-sdk → MARpc → **order-service** → BIST.
- Protokol strateji başına seçilir: `Channel_Enum` OUCH veya FIX.
- Gönderim 10 sn içinde dönmezse strateji durur (VWAP `sendTransaction`).
- 🚧 `add-order-sdk` branch'i (12 commit, son 2026-10-15) MAOrderSDK'yı ve OUCH handoff'u getiriyor: `MAOrderSdkManager`, `MAOrderSdkRouter`, `OrderEventDispatcher`, replay beklemesi. Henüz development'ta değil. Daha eski `feature/maorder-sdk-integration` (2026-05) da merge edilmemiş.

## gRPC (`StrategyService`, :9098)

HftSrvProd ile aynı sözleşmedir (`strategies.proto`); istemci trade-data-app'tir. Ek olarak AlgoProd'a özgü uçlar vardır:
- Vadeli abonelikleri: `SubscribeToFuture(s)`, `SubscribeToAllFutures`
- Paket işlemleri
- Strateji aktiviteleri: `ArbitrageStrategyActivity`, `ArbitragePackageActivity`, `FundTracker*Activity`, özetler

## trade-data-app'e (`AlgoService`, :6620) yaptığı çağrılar

`AlgoLogin`, `GetUserAccounts`, `GetAllInstruments`, `GetFictiveInstrumentSettings` / `GetFictiveItemSettings` (endeks tanımları), `Get/SetArbitrageData`, `UpdateArbitragePackage`, `DeleteArbitragePackage`, `Get/SetFundData`, `GetByfSettings`, `Get/SetStrategySettings`, `FetchAkd` (stream), `SubscribeBrokarageResults`, `GetTimeBasedData`, `FetchHistoricalData`.

## Config (`Configuration.ini`)

Anahtar referansı, parser tuzakları ve müşteri farkları: [config.md](config.md).

## Build

CMake, binary adı `AlgoProd`. Bağımlılıklar: `libouchSDK` (MARpc'yi içermez; `libMARpc.so`'ya dinamik bağlı, çalışma anında ayrıca gerekir), `libMAItchSDK`, (opsiyonel) `libMAPerfSDK`, gRPC/protobuf, TBB, sentry. Onload/Mellanox bulunursa hızlandırma derlenir. CI `algo.yml` binary'yi Algo-Setup'a (AlgoProd) yazar.
