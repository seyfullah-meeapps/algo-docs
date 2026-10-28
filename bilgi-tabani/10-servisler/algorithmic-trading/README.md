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

## Alt dosyalar

| Soru | Dosya |
|------|-------|
| Açılış/kapanış sırası, sinyaller, manager'lar, thread ve worker modeli, kuyruklar ve sıra garantisi, kilitler, `StrategyManager` (restore, yaşam döngüsü), ITCH köprüsü, kendi emir defteri modeli, enstrüman hiyerarşisi, logger | [uygulama-ve-threadler.md](uygulama-ve-threadler.md) |
| Emir order-service'e nasıl gider (ouch-sdk/MARpc), kimlikler (token, passthrough), kanal seçimi, olayların stratejiye dönüşü, userbook'lar, pozisyon, fiyat ölçeği, ret ve PTRM, manuel emir, kopma, 🚧 `add-order-sdk` | [emir-yolu.md](emir-yolu.md) |
| gRPC `StrategyService` uçları ve HFT'den farkları, `SetCommandRequest` dispatch, wire alan biçimi, GUI'ye dönen akış, proto farkları, trade-data-app çağrıları ve kalıcılık | [grpc-ve-veri.md](grpc-ve-veri.md) |
| Config anahtarları | [config.md](config.md) |
| Log satırları | [40-operasyon/log-imzalari § 4](../../40-operasyon/log-imzalari.md#4-algoprod-algorithmictrading) |

## Önce bil

- **Prod `master`'dır ve development'tan belirgin geridir** (aa150ee, 2026-09-01; development 0dc32a7 31 commit önde, master'da 12 ayrı commit). master'da worker havuzu yok (Arbitraj kendi thread'inde), ITCH SDK v2 API'si kullanılıyor, `StrategyStartException` yok. Fon Takibi lot düzeltmesinin branch kapsamı ilgili strateji dosyasındadır; kurulu prod binary bu karşılaştırmayla doğrulanmaz.
- **Açılış:** Sentry → config → `SettingsManager` (DB'den enstrüman ve fiktif ayarlar) → PerfSDK → Logger → OrderbookManager → ITCH (Glimpse'i `itchsdk_start` bloklar; ardından snapshot-end için en çok 600 s) → OuchManager (3 s sabit bekleme; login hatasında açılış sürer) → gRPC → worker havuzu → `StrategyManager` restore. gRPC restore'dan önce açılır ([§ 1](uygulama-ve-threadler.md#1-açılış-sırası)).
- **Kapanış:** Yalnız SIGINT/SIGHUP/SIGUSR1/SIGUSR2 düzenli kapatır. SIGTERM handler'ı yorumda; gün sonu `EndOfMessages` kapanışı **ölü kod** (olayı yayınlayan yok). `docker stop` → SIGKILL ([§ 2](uygulama-ve-threadler.md#2-kapanış-sinyal-gün-sonu-hata)).
- **Bütün emirler order-service üzerinden** gider (ouch-sdk → MARpc). Yeni emirde bekleme/timeout **yoktur**; 10 sn timeout yalnız `send(Replace/Cancel)` yolundadır ve GUI/VWAP iptalleri bu yolu kullanmaz ([emir-yolu § 4](emir-yolu.md#4-gönderim-ouchmanagerh)).
- **Kanal:** `Channel_Enum` yalnız Arbitraj ve VWAP'ta okunur; kanal değerleri 1 OUCH, 2 FIX olarak aktarılır ([emir-yolu § 4.2](emir-yolu.md#42-kanal-seçimi-channel_enum)). Fon Takibi sabit OUCH.
- **gRPC sözleşmesi HFT ile aynı `.proto`, davranışı farklı:** komut sınıfı `Command_Type` (char) ile seçilir; bazı uçlar boş/işlevsiz ([grpc-ve-veri § 2](grpc-ve-veri.md#2-rpcler)).

## Config (`Configuration.ini`)

Anahtar referansı, parser tuzakları ve müşteri farkları: [config.md](config.md).

## Build

CMake, binary adı `AlgoProd`. Bağımlılıklar: `libouchSDK` (MARpc'yi içermez; `libMARpc.so`'ya dinamik bağlı, çalışma anında ayrıca gerekir), `libMAItchSDK`, (opsiyonel) `libMAPerfSDK`, gRPC/protobuf, TBB, sentry. Onload/Mellanox bulunursa hızlandırma derlenir. CI `algo.yml` binary'yi Algo-Setup'a (AlgoProd) yazar.
