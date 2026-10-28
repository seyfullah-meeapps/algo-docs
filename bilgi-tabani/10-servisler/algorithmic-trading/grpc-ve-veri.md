---
kapsam: AlgoProd gRPC katmanı (StrategyService sunucusu, komut parse, wire alanları, GUI'ye dönen aktivite/özet akışı, proto farkları) ve trade-data-app AlgoService istemcisi (çağrılar, token, kalıcılık, restart)
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading          # prod
    branch: master
    commit: aa150ee
  - repo: HftSrvProd                  # proto diff
    branch: development
    commit: 4275ccc
  - repo: trade-data-app              # istemci tarafı doğrulaması
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# gRPC ve veri (AlgoProd)

İndeks: [README.md](README.md). Bu dosya HFT karşılığı [hftsrvprod/komutlar-ve-grpc.md](../hftsrvprod/komutlar-ve-grpc.md) ile **farkları** yazar; ortak kavramlar (Any + `clientmodels.*Value` sarmalayıcıları, protobuf `Map::insert`'ün üzerine yazmaması, eksik alanın varsayılana düşmesi) orada. İstemci tarafı: [trade-data-app/api.md](../trade-data-app/api.md) § 5 ve § 9, [veri-akisi.md](../trade-data-app/veri-akisi.md) § 4.4 ve § 5.3. UI zarfı: [mtrader-trade-ui/backend-sozlesmesi.md](../mtrader-trade-ui/backend-sozlesmesi.md). Strateji parametrelerinin anlamı: [arbitraj.md](../../20-stratejiler/arbitraj.md), [vwap.md](../../20-stratejiler/vwap.md), [fon-takibi.md](../../20-stratejiler/fon-takibi.md). Strateji döngüsü, emir yolu ve thread modeli bu dosyada yok.

Kod: `algoSrc/Managers/GUIManager.*`, `algoSrc/Managers/StrategyServiceImpl.*`, `algoSrc/Managers/StrategyManager.*`, `algoSrc/Commands/*`, `algoSrc/Utilities/GuiConstants.h`, `algoSrc/Utilities/ParserUtility.h`, `algoSrc/Strategy/StrategyActivities.h`, `algoSrc/Strategy/StrategySummary.h`, `algoSrc/Data/DatabaseServiceClient.*`, `algoSrc/*.proto`.

## 1. Sunucu ve kimlik doğrulama

- `GUIManager::startProperly` `grpcWorker` thread'inde `startGrpcServer` çalıştırır: senkron gRPC, `0.0.0.0:<clientPort>` ([config.md](config.md)), insecure. Default health servisi açık, `""` SERVING. Yani trade-data-app'in health `Watch`'ı AlgoProd'da çalışır (veri-akisi.md § 5.1'deki ❓ AlgoProd için kapanır). Açılışta `ma::build::PrintAll()` bağlı bileşen sürümlerini stdout'a basar ⚠ master'da yok (2026-10-22).
- Her RPC gRPC'nin senkron havuz thread'inde çalışır. Açık `FetchCommands` stream'i bir thread'i sürekli tutar (1 ms uyuyan döngü).
- **`StrategyLogin`**: `DatabaseServiceClient::LoginAsGuiUser` → trade-data-app `AlgoLogin`, `application=AlgoTrading` (HFT'de `HFT`). Token `userTokenMap`'e yazılır ve **stdout'a basılır**. Boş token → `CANCELLED` (gövdesiz status). İstisna yakalanmaz.
- **`checkAuthorization`**: HFT ile aynı (`authorization` metadata, `Bearer ` öneki atılır, süresiz bellek içi token). Restart sonrası istemci yeniden login olmalı. **Yetki kontrolü yapmayan RPC'ler:** `UpdateExtSettings`, `SubscribeToOrderbook`, `FetchOrders` (HFT'de hepsi kontrol ediyor ya da unimplemented).

## 2. RPC'ler

| RPC | AlgoProd'da ne yapar | Yanıt / hata |
|-----|----------------------|--------------|
| `StrategyLogin` | §1 | `token` / `CANCELLED` |
| `SetCommandRequest` | `message_type`'a göre dispatch (§3). Senkron. | `success` + status |
| `FetchCommands` (server stream) | Anahtar başına kuyrukları boşaltır (§5.1). İstek alanları okunmaz. | stream; döngü yalnızca AlgoProd kapanınca biter |
| `SubscribeToCommands` | `StrategyRequest` (1) ve `SummaryRequest` (5) işlenir, diğerleri (3 Balance, 8 MaxPriceState…) **sessizce atlanır** (§5.3) | her zaman `success=true` |
| `UnsubscribeFromCommands` | **Hiçbir şey yapmaz.** | `success=true` (HFT'de `NOT_FOUND`) |
| `FetchAllUniqueKeys` | `strategyMap`'te `Exchange_Info`'su istekteki hesaplardan biri olan stratejilerin unique key'leri, hesap başına gruplu | `success=true` |
| `SubscribeToFuture` | Tek arbitraj satırı: türev ve dayanak için order-service'e `insertStrategyInfo`, strateji yoksa `createArbitrageStrategy` (§3.2), yanıtta pozisyonlar (`drvPos`, `undPos`, lot) ve `remaining_days` | `NOT_FOUND` (enstrüman/strateji yok) |
| `SubscribeToFutures` | Listeyi `SubscribeToFuture` ile tek tek işler; **ilk hatada döner**, öncekiler yaratılmış kalır | ilk hatanın status'ü |
| `SubscribeToAllFutures` | `GetUnderlyingInstrumentsWithFuture` listesindeki her dayanak için (XU030 hariç) `expiry_month` (0–2) vadesiyle arbitraj stratejisi yaratır. İki vadeli tiplerde `other_expiry_month` zorunlu ve farklı olmalı. | `INVALID_ARGUMENT "Invalid (Other) Expiry Month"` |
| `AlgoSetAccountStrategy` | Yalnız order-service'e `insertStrategyInfo(..., overall_value)`. **Strateji yaratmaz.** Zaten varsa `success=false` + `OK`. | |
| `UpdateExtSettings` | Excel import bildirimi: istekteki her satır için arbitraj strategy key'i (§3.1) kurar, stratejileri **durdurur**; `is_finish_updating=true` ise ayarları DB'den yeniden okur (`updateStrategies`) ve paket durumunu DB'den tazeler (`updateStrategyStates`) | her zaman `OK` |
| `SubscribeToOrderbook` | **Gövdesi boş, `return` yok** (yalnız log). C++'ta tanımsız davranış. | ❓ doğrulanmadı: pratikte ne döndüğü / çöküp çökmediği |
| `FetchOrders` | Hemen `OK` ile kapanır. AlgoProd emirleri GUI'ye order-service feed'inden gider. | — |

Arbitraj `unique_key` üretimi (`generateUniqueKey`): `<istek unique_key>_<türevId>_<tipChar>`; iki vadeli tiplerde (`T`, `R`) `<istek unique_key>_<türevId>_<diğerTürevId>_<tipChar>`. trade-data-app istek key'ini `<hesap>_<strategyIdentifier>` olarak yollar (veri-akisi.md § 5.3). Proto `ArbitrageType` → iç tip: INTEREST→`I`, SPREAD→`F`, AUTO_SPREAD→`D`, TWO_FUTURES→`T`, TWO_FUTURES_INTEREST→`R`; tanımsız → `I` (log'la). Dayanak hesabı türev hesabındaki ilk `-`'den sonrası (iki vadelide türev hesabının kendisi).

## 3. `SetCommandRequest` dispatch

`StrategyServiceImpl::SetCommandRequest` → `checkAuthorization` → `message_type`:

| `CommandTypeRequest` | İşleyen | Not |
|----------------------|---------|-----|
| 1 `StrategyRequest` | `checkParams` → `StrategyManager::commandReceived(map, unique_key)` | §3.1 |
| 2 `PackageRequest` | `GUIManager::dispatchPackages` | yalnız arbitraj (§3.2) |
| 3 `BalanceRequest` | `getStrategy(unique_key)` → `strategy->setBalance(SetBalanceCommand)` | strateji yoksa `NOT_FOUND "Strategy Not Found"` |
| 4 `OrderRequest` | `GUIManager::dispatchOrders` | manuel emir (§3.3) |
| 6 `ExecuteUnderlyingRequest` | `strategy->executeUnderlying(PassiveUnderlyingCommand)` | arbitraj pasif dayanak emri |
| 5, 7, 8, 9, diğer | — | `INVALID_ARGUMENT "Invalid Message Type"` (CancelAll/ClosePosition AlgoProd'da yok) |

HFT'den fark: Balance/ExecuteUnderlying stratejiyi **`CommandRequest.unique_key`** ile bulur (HFT map'teki `Strategy_Unique_Key`'i okur). `getStrategy` `strategyMap`'i doğrusal tarar.

### 3.1 Strateji komutu (başlat / durdur / ayar güncelle)

Başlat, durdur ve ayar güncelleme aynı yoldur; fark `Strategy_Start` (Bool) değeridir.

1. **`checkParams`** (`StrategyServiceImpl.cpp`). HFT'de ölü olan bu kontrol AlgoProd'da **çağrılır**. `Command_Type` (Int) yoksa veya tanınmıyorsa `INVALID_ARGUMENT "Missing or invalid parameters"`. Komuta göre:
   - `ArbitrageTracker` (`'3'`): `Strategy_Unique_Key`, `Strategy_Id`, `Exchange_Info` boş olmamalı; `Arb_Strategy_Type`, `Channel_Enum`, `Is_Spot_Sell_Allowed`, `Derivative_Type`, `Sell_Type` Int > 0; `Orderbook_Id`, `Underlying_Instrument_Id` (farklı olmalı), `Start_Time`, `Stop_Time`, `Underlying_Multiplier` Long > 0; ayrıca `Contract_Limit(_Closing)`, `Package_Limit(_Closing)`, `Stop_Loss_Second`, `Stop_Loss_Level`, `Open_Tick`, `Close_Tick`, dört `*_By_*_Rate`, `Dividend_Prc`, `Current_Interest_Rate` **var** olmalı (değer kontrolü yok). Ret sebebi yalnız log'a yazılır.
   - `TradeByVolume` (`'6'`): `Vwap_Side`, `Vwap_Mode`, `Vwap_Price_Limit`, `Ratio` (Long > 0), `Strategy_Unique_Key`.
   - `FundTracker` (`'d'`): `Byf_Start_Time`, `Byf_Stop_Time`, `Byf_Spread_Buy/Sell`, `Byf_Lot_Count_Buy/Sell`, `Strategy_Unique_Key` var olmalı.
   - `TradeByVolumeOverall`, `BasketArbitrageTracker`, `ArbitrageOverallTracker`, Warrant/MA: kontrol yok.
2. **`CommandFactory::createStrategyCommand`**: sınıf **`Command_Type`** ile seçilir (HFT `Strategy_Type` ile seçer). `Command_Type` yoksa `BaseException` → `INTERNAL`. Tanımsız tip (`'X'` dahil) → `INTERNAL "…unknown/unimplemented command type"`. Arbitrajda `Underlying_Instrument_Id`=0 → `nullptr` → `INVALID_ARGUMENT "strategyCommandPtr is null"`.
3. **`commandReceived(cmd)`**: `strategyMap` anahtarı **strategy key**'dir (§3.4). Yoksa `StrategyFactory::createStrategy`; fabrika istisnası **yutulur** (log) ve akış devam eder. Varsa `strategy->setCommand(cmd)`: command tamamen değişir (merge yok), `isStarted()`'a göre `start()`/`stop()`.
   - `setCommand` istisna atarsa ve strateji bu komutla yeni yaratıldıysa `strategyMap`'ten silinir; `StrategyStartException` (ör. tutarsız arbitraj paketleri) → `FAILED_PRECONDITION <sebep>`, diğerleri → `INTERNAL`. ⚠ master'da yok (2026-10-22): master'da her istisna `INTERNAL` ve strateji map'te kalır.
   - `runsOnWorkerPool()` ve çalışıyorsa `AlgoWorkerManager`'a atanır ⚠ master'da yok.
4. `WarrantTracker` + `Orderbook_Id`=3 (XU030) ise en yakın vadeli için ikinci bir command (kullanılmayan strateji).
5. **`saveStrategySettings(map)`**: `Strategy_Start` hariç **gelen map** senkron `SetStrategySettings`'e yazılır (§7.2). Sonuç kontrol edilmez.
6. **`setStrategyNotifier(request.unique_key, cmd)`**: anahtar için GUI kuyruğu yoksa açılır, aktivite kuyrukları açılır (`HandleStrategySubscribers`) ve command snapshot'ı (`StrategyResponse`) kuyruğa konur. Bu "echo" UI'daki çalışıyor göstergesini besler.
7. `OK`, `success=true`.

### 3.2 Paket ve pozisyon komutları (arbitraj)

- **`dispatchPackages`**: `Arb_Pack_Token` (String) ve `Arb_Package_Type` (Int: 1 Update, 2 Delete) zorunlu, yoksa `INVALID_ARGUMENT`. Strateji `CommandRequest.unique_key` ile bulunur ve tipi `ARBITRAGE` olmalı, yoksa `INVALID_ARGUMENT "Strategy not found!"`.
  - Update → `ArbitrageTracker::updatePackage`: strateji **çalışıyorsa sessizce reddedilir** (yanıt yine `OK`); token bulunamazsa strateji durdurulur.
  - Delete → önce `DeleteArbitragePackage` (DB), sonra stratejide `deletePackage(token, dbSonucu)`. Strateji bulunamasa da DB silmesi yapılmış olur.
- **`setBalance`** (`SetBalanceCommand`): strateji çalışıyorsa `UNAVAILABLE "Strategy is running…"`. `Set_Balance_Type` (Int, char kodu: 83 `'S'` → Above paketi, 66 `'B'` → Below paketi; başka → `INVALID_ARGUMENT "Side is not valid!"`). Fiyat 0 ise o anki best fiyat alınır. Sonra DB'ye yazılır.
- **`createArbitrageStrategy`** (SubscribeToFuture/AllFutures): yalnız `Underlying_Instrument_Id`, `Orderbook_Id`, `Exchange_Info`, `Strategy_Id`, `Strategy_Type`=6, `Arb_Strategy_Type`, `Command_Type`=`'3'`, `Strategy_Unique_Key`, `Strategy_Type_Name`=`"ARBITRAGE"` içeren bir map ile `commandReceived(map)` çağrılır: `checkParams` atlanır, strateji **durmuş** hâlde yaratılır, DB'ye yalnız bu alanlar yazılır.

### 3.3 Manuel emir (`OrderRequest`)

`Order_Event_Type` (Int) zorunlu: 1 Enter, 2 Cancel, 3 Replace; başka → `INVALID_ARGUMENT`. HFT'deki Theoretical (4) yok. Strateji aranmaz; `EnterOrder` stratejiden bağımsız kurulur (TIF DAY, passthrough = yeni token) ve `OuchManager::send` ile order-service'e gider. Emir yolunun ayrıntısı bu dosyanın kapsamı dışında.

| Komut | Zorunlu alanlar (wrapper) | Not |
|-------|---------------------------|-----|
| Enter | `Orderbook_Id` (Long), `Exchange_Info` (String), `Order_Side` (Int 1/2/3 → `'B'/'S'/'T'`; başka → side 0, hata dönmez), `Order_Quantity` (Long, lot), `Order_Price` (Long, **raw**), `Strategy_Id` (String), `Strategy_Type` (Int, `common.proto` numarası), `Order_Lvl_Count` (Int) | `Order_Channel` (Int) yoksa OUCH. Eksik alan → `INVALID_ARGUMENT "…missing fields!"`. Enstrüman tradable değilse `INVALID_ARGUMENT`. Strategy info yoksa order-service'e eklenir. `Order_Lvl_Count` > 1 ise **en çok 10** kademe; BUY'da aşağı, diğerlerinde yukarı `getPriceStep(fiyat)` adımıyla. |
| Cancel | `Order_Token` (String), `Order_Channel` (Int) | |
| Replace | `Orderbook_Id`, `Order_Quantity`, `Order_Price` (Long, raw), `Order_Token`, `Order_Channel` | HFT'deki "fiyat ve miktar birlikte değişemez" kontrolü yok |

`OK` yalnız "gönderim denendi" demektir; emir sonucu GUI'ye order-service feed'inden gelir.

### 3.4 Strategy key ve unique key

- **Strategy key** (`BaseCommand::getStrategyKey`, `strategyMap` anahtarı): `std::to_string((char)Command_Type) + obid + Exchange_Info + Strategy_Id + std::to_string(Strategy_Type)`, ayraçsız. `std::to_string(char)` karakterin **sayısal kodunu** yazar: arbitraj `'3'` → `"51"`, örnek `51<obid><hesap><sid>6`. `PackageCommand`, `SetBalanceCommand`, `PassiveUnderlyingCommand` ve `generateStrategyKey` bunu arbitraj için sabit `'3'`/6 ile kurar.
- **Unique key** (`Strategy_Unique_Key`): GUI'nin verdiği string; AlgoProd kurmaz (arbitraj Subscribe RPC'leri hariç, §2). Snapshot ve aktiviteler bu anahtarla yönlenir. `getUniqueKey()` baştaki boşluk/form-feed'i kırpar.

## 4. Wire biçimi

### 4.1 Parse

- Alanlar `ParserUtility::extract{Int,Long,ULong,ULongLong,LongLong,Double,Bool,String,CharFromInt}` ile okunur. Bütün tamsayı varyantları **`clientmodels.LongValue`** açar (`extractULongLong` dahil); `extractInt`/`extractCharFromInt` **`IntValue`** açar. `GuiConstants.h` yorumundaki "uLongLong", "Long Long" yalnız C++ tipini anlatır; wire'da `LongValue`'dur.
- HFT'deki gibi: yanlış wrapper → `UnpackTo` başarısız → sessizce 0/false/"". Eksik alan → aynı varsayılan.
- **char alanlar**: `IntValue` içinde ASCII kodu (`Arb_Strategy_Type` `'D'`=68, `Vwap_Mode` `'P'`=80, `Set_Balance_Type` `'B'`=66…).
- `BaseCommand` ctor `Command_Type`, `Orderbook_Id`, `Exchange_Info`, `Strategy_Id`, `Strategy_Type` sırasıyla okur; biri eksikse log'lar ve **kalanları okumadan döner** (üye alanlar ilklenmemiş kalır). `Exchange_Info`'ya `Account` fallback'i yok (HFT'de var).

### 4.2 Ortak alanlar (strateji komutu)

| Anahtar | Wrapper | Anlam |
|---------|---------|-------|
| `Command_Type` | Int | **İç komut kodu** (`Globals/Enumarations.h` `Commands`, char → ASCII). Sınıf seçimi bununla yapılır (§4.4). |
| `Strategy_Type` | Int | `common.proto` `StrategyType` (= `ouchSDK::enums::StrategyType`, `ouch-sdk/include/models/Enums.h` ile aynı numaralar) |
| `Orderbook_Id` | Long | Arbitrajda **türev**, diğerlerinde işlem gören enstrüman |
| `Exchange_Info` | String | Hesap (arbitrajda türev hesabı) |
| `Strategy_Id` | String | strategy identifier |
| `Strategy_Unique_Key` | String | §3.4 |
| `Strategy_Start` | Bool | Başlat/durdur. DB'ye yazılmaz. |
| `Strategy_Type_Name` | String | Bilgi amaçlı; parse edilmez |
| `Order_Command_Type` | Int | Yalnız `CommandFactory::createOrderCommand` (CancelAll `'7'`) — gRPC yolundan çağrılmıyor |

Snapshot'ta (`BaseCommand::toClientMessage`) taban alanlar: `Command_Type`, `Orderbook_Id`, `Exchange_Info`, `Strategy_Id`, `Strategy_Type`, `Strategy_Start` + `unique_key`. HFT'den fark: `Account` ve `Is_Running` **yok**; `Strategy_Start` command'ın `started` değeridir, çalışma durumu özetteki `Is_Strategy_Running`'den okunur.

### 4.3 İç komut ↔ wire `StrategyType`

| `Commands` (char = `Command_Type`) | Command sınıfı | Wire `Strategy_Type` | `MyOrderType` (emir sınıfı) | Durum |
|-----|-----|-----|-----|-----|
| `'3'` (51) `ArbitrageTracker` | `ArbitrageTrackerCommand` | 6 Arbitrage | 18 `ArbitrageTracker` | aktif |
| `'E'` (69) `BasketArbitrageTracker` | `BasketArbitrageTrackerCommand` | 6 | 18 | kodda, kullanılmıyor (arbitraj.md) |
| `'6'` (54) `TradeByVolume` | `TradeByVolumeCommand` | 7 VWAP | command'dan (`getOrderType`) | aktif |
| `'V'` (86) `TradeByVolumeOverall` | `TradeByVolumeOverallCommand` | 7 | 14 `VolumeStrategy` | yeni GUI'de yok |
| `'d'` (100) `FundTracker` | `FundTrackerCommand` | 10 FundTracker | 27 `FundTracker` | aktif |
| `'9'` (57) `WarrantTracker`, `'T'` (84) `WarrantOverallTracker` | Warrant* | 2 | 19 | kullanılmıyor |
| `'8'` (56) `TradeByBSRatio` | `TradeByBSRatioCommand` | 3 AKD | 15 `BSRatioStrategy1` | kullanılmıyor |
| `'4'` (52) `MovingAverageTracker` | `MovingAverageTrackerCommand` | 5 | 20 | kullanılmıyor |
| `'X'` (88) `ArbitrageOverallTracker` | — | — | — | `checkParams` geçer, fabrika `INTERNAL` |

`OrderUtility::convertMyOrderStrategy` **`MyOrderType` → `StrategyType`** çevirir (iç `Commands` char'ını değil): User→1, WarrantTracker→2, BSRatioStrategy1→3, MovingAverageTracker→5, ArbitrageTracker→6, VolumeStrategy→7, FundTracker→27→10, Unknown→0, **diğer her şey → 1 (USER)**. Kullanım: emir defteri istatistiği ve iptal için hesap+identifier+tip anahtarı (`BaseStrategy::getPosition`, `OrderbookManager` cancel). Ters yön (wire tip → command) yoktur; `Command_Type` ile `Strategy_Type`'ın tutarlı gönderilmesi istemcinin işidir.

### 4.4 Alan grubu → strateji

| `GuiConstants.h` grubu | Strateji | Anlam/birim |
|------------------------|----------|-------------|
| `ARB_*` "Arbitrage Parameters" | Arbitraj (`'3'`) ve Sepet (`'E'`) | [arbitraj.md § Wire alanları](../../20-stratejiler/arbitraj.md) |
| `BYF_*` "FUND TRACKER PARAMETERS" | Fon Takibi | [fon-takibi.md § Wire alanları](../../20-stratejiler/fon-takibi.md) |
| `VWAP_*`, `TRADE_*`, `RATIO`, `BASE_INTEREST`, `BROKER_*`, `CHILD_ACCOUNT_*` | VWAP / VWAP Overall | [vwap.md § Wire alanları](../../20-stratejiler/vwap.md) |
| `MAX_POSITION_QTY` … `RSI_` "AKD Constants", `BUY_MA`…, `WARR_*` | AKD, MA, Warrant | kullanılmayan kod |
| `ARB_PKG_*`, `ARB_CONTRACT_QTY`, `ARB_DRV_*`, `ARB_UND_*`, `SET_BALANCE_TYPE`, `ARB_PACKAGE_TYPE`, `ARB_STRATEGY_SIDE` | Paket/bakiye komutları (§3.2) ve paket aktivitesi (§5.2) | aşağıda |
| `ORDER_*` | Manuel emir (§3.3), pasif emir aktivitesi | |

Paket/bakiye/pasif dayanak komut alanları:

| Alan | Wrapper | Kullanan | Birim |
|------|---------|----------|-------|
| `Arb_Pack_Token` | String | Package | paket token'ı |
| `Arb_Package_Type` | Int | Package | 1 Update, 2 Delete |
| `Arb_Contract_Qty` | Long | Package, SetBalance | kontrat (lot) |
| `Arb_Und_Exc_Qty` | Long | Package, SetBalance | dayanak adedi (lot) |
| `Arb_Drv_Price`, `Arb_Und_Price` | Long | Package, SetBalance | raw fiyat (❓ doğrulanmadı: türevde ölçek; [arbitraj.md § Fiyat birimleri](../../20-stratejiler/arbitraj.md)) |
| `Arb_Strategy_Side` | Int (char) | Package (parse edilir, `updatePackage` kullanmaz) | `'A'`/`'B'` |
| `Arb_Drv_SendOrder`, `Arb_Und_SendOrder` | Bool | Package, SetBalance | parse edilir, `setBalance` kullanmaz |
| `Set_Balance_Type` | Int (char) | SetBalance, PassiveUnderlying (`BaseOrderCommand`) | 66/83 |
| `Arb_Package_Id` | Int | PassiveUnderlying | paket id |
| `Arb_Und_Cmd_Type` | Int | PassiveUnderlying | 1 Execute, 2 Increase, 3 Decrease (`UnderlyingCommandTypes`) |

## 5. GUI'ye dönen akış

### 5.1 Boru hattı

```
Strateji Notifier ─► GUIManager tip-başı Subscriber ─► GUIManager::workAsyncron ─► StrategyServiceImpl anahtar-başı Subscriber ─► FetchCommands
(strategyActivity, package, passive,      (tek kuyruk/tip)         (userListMtx altında,         (unique_key → tbb kuyruğu)        (1 ms döngü)
 byfPackage, byfUnderlyingPrice, command)                           uyumadan döner)
```

- Anahtar-başı kuyruklar (`strategySubscriberMap`, `activitySubscriberMap`, `arbitragePackageSubscriberMap`, `passiveOrderSubscriberMap`, `byfPackage…`, `byfUnderlyingPrice…`, `strategySummarySubscriberMap`) **GUI aboneliğinden bağımsız** açılır: strateji GUI komutuyla geldiğinde (`setStrategyNotifier` → `HandleStrategySubscribers`) veya `SubscribeToCommands` ile. Aktivite kuyrukları yalnız ARBITRAGE (aktivite, paket, pasif emir) ve FUND_TRACKER (paket, teorik fiyat) için açılır. VWAP ve diğerleri için aktivite kuyruğu yok.
- GUIManager kuyruğunda anahtar karşılığı yoksa mesaj **atılır** (ör. restart sonrası DB'den yüklenmiş ama GUI'nin henüz dokunmadığı strateji).
- `FetchCommands` her turda bütün anahtar kuyruklarını sırayla boşaltır ve `Write` eder. `Write` dönüşü ve `context->IsCancelled()` **kontrol edilmez**; döngü AlgoProd kapanana kadar sürer. HFT development'taki iptal/yeniden kuyruklama düzeltmeleri burada yok.
- Kuyruklar `tbb::concurrent_bounded_queue`, kapasite verilmemiş (sınırsız). Stream yokken birikir; birden fazla stream varsa mesajlar aralarında bölünür.
- Snapshot (`StrategyResponse`) üreten yerler: `setStrategyNotifier` (her GUI komutunda), `SubscribeToCommands` (anlık), `BaseStrategy::exitProperly` (strateji kendini durdurunca, `strategyCommandNotifier` → GUIManager).

### 5.2 Giden mesajlar

| `message_type` | Üreten | `ACTIVITY_MESSAGE_TYPE` (`"StrategyActivity"` alanı) | Ne zaman |
|----------------|---------|-----|----------|
| 1 `StrategyResponse` | `<X>Command::toClientMessage` | — | §5.1 |
| 2 `ActivitiesResponse` | `ArbitrageStrategyActivity` | `ArbitrageStrategyActivity` | Arbitraj durumu değişince: oluşturma, kapama kârı, DB güncellemesi, snapshot (`notifyStrategyActivityAndSummary`). Periyodik değil. |
| 2 | `BasketArbitrageStrategyActivity` | `BasketArbitrageStrategyActivity` | kullanılmıyor; aktivite kuyruğu açılmadığı için zaten GUI'ye ulaşmaz |
| 3 `PackageActivityResponse` | `ArbitragePackageActivity` | `ArbitragePackageActivity` | Paket ekleme/güncelleme/silme, snapshot (`updatePackageState`) |
| 3 | `BYFPackageActivity` | **`FundTrackerStrategyActivity`** | Fon paketi değişince ve snapshot'ta |
| 4 `PassiveOrderResponse` | `PassiveOrderActivity` | `PassiveOrderActivity` | Arbitraj pasif dayanak emri değişince; snapshot'ta yalnız aktif olanlar |
| 6 `SummaryResponse` | `ArbitrageSummary`, `VWAPSummary` | — | §5.3 |
| 7 `BYFTheoreticalPriceResponse` | `BYFUnderlyingPriceActivity` | `FundTrackerUnderlyingPriceActivity` | Teorik alış fiyatı değişince ve fon işlemi gelince |

`BalanceResponse`, `StatisticsResponse`, `MaxPriceStateResponse` AlgoProd'da üretilmez. (fon-takibi.md'deki "`FundTrackerStrategyActivity` + ayrıca paket aktivitesi" ifadesi: ikisi aynı mesajdır.)

Bütün aktivitelerin ortak alanları (`StrategyActivity::toMessage`): `Orderbook_Id` (Long), `Exchange_Info`, `Strategy_Id`, `Strategy_Type` (Int), `StrategyActivity` (String, yukarıdaki etiket) + `unique_key`. Arbitraj aktivitesinde `Orderbook_Id` türev, hesap türev hesabıdır; pasif emirde dayanak ve (iki vadeli değilse) dayanak hesabı.

| Mesaj | Alanlar (wrapper, birim) |
|-------|--------------------------|
| `ArbitrageStrategyActivity` | `First_Open_Date`, `Last_Up_Date` (Long, epoch **saniye**); `Drv_Pos`, `Und_Pos` (Long, lot); `Drv_Avg_Price`, `Und_Avg_Price` (Long, ❓ ölçek); `Theo_Price` (Long, **TL×1000**); `Avg_Calc_Int_Rate`, `Int_By_Buy`, `Int_By_Sell` (Long, oran×1000); `Total_Profit` (Long, `state.totalProfit`×1000); `Closed_Position_Qty` (Long) |
| `ArbitragePackageActivity` | `Package_Activity_Is_Update`, `Package_Activity_Is_Delete` (Bool); `Arb_Package_Activity_Status` (Int; silmede DB silme sonucu); `Arb_Package_Activity_Current_Package` (Map: `Arb_Package_Id` Int, `Arb_Pack_Token` String, `Arb_Init_Contract_Qty`/`Arb_Contract_Qty`/`Arb_Und_Exc_Qty` Long, `Arb_Drv_Price`/`Arb_Und_Price` Long raw, `Arb_Int_Rate` Double, `Arb_Is_Active`/`Arb_Is_Completed` Bool, `Timestamp` **String** (epoch saniye), `Arb_Strategy_Side` Int char, `Arb_Expected/Real_Margin_Opening/Closing` Double, `Arb_Basket_Package` List) |
| `PassiveOrderActivity` | `Arb_Package_Id` (Int), `Order_Side` (Int, char kodu 66/83/84), `Order_Sent_Qty`, `Order_Exc_Qty` (Long, lot), `Order_Price` (Long, raw), `Order_Sent_Time` (Long, epoch ms ❓ dayanak emri için doğrulanmadı), `Arb_Spot_Instr_Name` (String), `Order_Is_Active` (Bool) |
| `BYFPackageActivity` | `Byf_Package_Id` (Int), `Byf_Package_Timestamp` (Long, epoch **ms**), `Byf_Package_Total_Price` (Long, **kuruş**), `Byf_Package_Is_Completed` (Bool), `Byf_Package_Order_Side` (Int, char kodu), `Byf_Package_Fund_Position` (Int), `Byf_Package_Instrument_Name`, `Byf_Package_Token` (String), `Byf_Package_Executed_Fund_Qty` (Long), `Byf_Package_Underlying_Orders` (List<Map>: `Byf_Order_Instrument_Name`, `Byf_Order_Sent_Qty`, `Byf_Order_Executed_Qty`, `Byf_Order_Mean_Price` (Long, ❓ ölçek), `Byf_Order_Is_Completed`, `Byf_Order_Weight` (Long, ağırlık×1000)) |
| `BYFUnderlyingPriceActivity` | `Byf_Underlying_Price` (Long, teorik **alış** fiyatı, kuruş), `Byf_Fund_Id` (Int), `Byf_Total_Fund_Sold_Qty`, `Byf_Total_Fund_Bought_Qty` (Long) |

### 5.3 `SubscribeToCommands` ve özetler

- `StrategyRequest` (1): strateji `getStrategy(unique_key)` ile bulunur; yoksa log + atlanır. Anahtar kuyruğu yoksa açılır ve `HandleStrategySubscribers` çağrılır. Command snapshot'ı kuyruğa konur, ardından `strategy->sendSnapshotOfStrategy()` (arbitraj: aktivite + özet + bütün paketler + aktif pasif emirler; fon: bütün paketler; diğerleri: ❓ taban sürüm).
- `SummaryRequest` (5): metadata `userid` ve `strategytype` zorunlu (trade-data-app ekler, veri-akisi.md § 4.4); yoksa log + atlanır. Abonelik anahtarı isteğin `unique_key`'idir (UI arbitrajda `""`, VWAP'ta `vwap-summary:<client_id>`; backend-sozlesmesi.md). `GUIManager::sendAndSubscribeToSummary`:
  - `GetUserAccounts(userid)` (DB) boşsa hiçbir şey yapılmaz.
  - **ARBITRAGE (6)**: `DatabaseServiceClient`'in bellek önbelleğindeki (`arbitrageDataMap`) kayıtlardan **spot ve türev hesabının ikisi de** kullanıcıya ait olanların stratejileri bulunur; her birinin `summaryNotifier`'ına abone olunur ve o anki özet bir kez gönderilir. Sonra arbitraj durumu her değiştiğinde özet gider.
  - **VWAP (7)**: kullanıcı hesabındaki her VWAP stratejisine abone olunur ve özet bir kez gider. `TradeByVolume::notifyStrategyActivityAndSummary` hiçbir yerden çağrılmadığı için **sonraki güncellemeler gelmez**; özet yalnız abonelik anında tazelenir.
  - Diğer tipler: log.
  - Abonelik tek seferliktir; sonradan yaratılan stratejiler özete eklenmez. `UnsubscribeFromCommands` boş olduğu için abonelikler process ömrü boyunca kalır.
- Özet alanları (`StrategySummary::toMessage`): `Total_Profit` (Long, **×1000'siz** `state.totalProfit`; aktivitedekiyle aynı ölçekte değil), `Timestamp` (**String**, epoch saniye), `Strategy_Type` (Int), `Strategy_Id`, `Is_Strategy_Running` (Bool, gerçek `isRunning`), `Strategy_Unique_Key` (String, stratejinin key'i). `FetchCommands` yanıtın `unique_key`'ini abonelik anahtarıyla **değiştirir**.
  - Arbitraj ek: `Arb_Spot_Ob_Id`, `Arb_Drv_Ob_Id` (Long), `Arb_Spot_Instr_Name`, `Arb_Drv_Instr_Name`, `Arb_Spot_Account`, `Arb_Derivative_Account` (String), `Arb_Strategy_Type` (Int char), `Arb_Und_Pos`, `Arb_Drv_Pos` (Long, lot), `Arb_Margin_Diff_Opening/Closing` (Double, paket ortalaması).
  - VWAP ek: `Orderbook_Id` (Long), `Instrument_Name`, `Vwap_Account` (String, ctor'da verilen hesap), `Vwap_Side` (Int char), `Vwap_Pos` (Long, lot), `Vwap_Mode` (**Long**; komutta Int), `Vwap_Buy/Sell_Position` (Long, lot), `Vwap_Buy/Sell_Volume` (Long, ❓ ölçek).

## 6. Proto farkları

`algoSrc/*.proto` ↔ `HftSrvProd/src/*.proto` ↔ trade-data-app `api/{client,protobuf}-spec/` (aynı paketler: `clientmodels`, `servicemodels`). AlgoProd'un kopyası development ile master arasında **aynı**.

| Dosya | AlgoProd'da HFT'ye göre eksik | AlgoProd'da fazla | trade-data-app'e göre |
|-------|------------------------------|-------------------|----------------------|
| `common.proto` | `StrategyType` 13 HFT_Warrant, 14 MinPrice, 15 HFT_WarrantAdvanced | `OrderEventType` 4 `ORDER_EVENT_THEORETICAL` | 13–15 eksik |
| `strategies.proto` | `Command_Type_MinPriceStateRequest`=10, `HftWarrantDerivativeResponse`=10, `MinPriceStateResponse`=11, `StrType` 7–9 | — (RPC listesi aynı, sıra farklı) | `HftWarrantDerivativeResponse`, `StrType` 7–9 eksik |
| `algo.proto` | — | — | aynı |
| `ouch-data.proto` | `Application` `HFT_MUSTERI`=4 | Login yanıtında `status`, `isOtpEnabled`, `errorMessage`; OUCH kullanıcısında `onlyMorningOrderUser`, `applicationUserName`; enstrümanda `underlying_instrument`, `tick_size`; emirde `is_main_order`, `main_order_id`, `level_count`, `latency_*_ns`, `internal_ouch`; strateji bilgisinde `overall_value`, `optional_*`, `arbitrage_type` | trade-data-app'te `orderRepeatCount`/`isDedicated` `reserved`, ek `orderUserPendingPassword`, `ouchRepeatCount`, `ouchCoreToPin`, `is_yip`, `UpdateOrderUserPassword` |

Pratik etki: AlgoProd yalnız `servicemodels.Application` enum'u için `ouch-data.proto`'yu kullanır; eksik enum değerleri bilinmeyen sayı olarak geçer. Eksik `StrategyType`'lar HFT tiplerine ait ve AlgoProd'a yönlenmez.

## 7. trade-data-app istemcisi (`DatabaseServiceClient`)

### 7.1 Bağlantı, token, hata

- Singleton; ilk `instance()` çağrısında ctor: config `dbIp:dbPort`, `dbUsername`/`dbPassword` ([config.md](config.md)). Kanal insecure, mesaj boyu sınırsız. `AlgoLogin(application=AlgoTrading)` → servis token'ı. Token boşsa ctor `BaseException` fırlatır (açılışta process düşer; K-187). Ctor ayrıca `pullArbitrageData` thread'ini başlatır (§7.3).
- Token **bir kez** alınır; yenileme, yeniden login, yeniden bağlanma mantığı yok. gRPC kanalı TCP kopmasında kendi yeniden bağlanır. ❓ doğrulanmadı: trade-data-app restart'ında eski token'ın geçerli kalıp kalmadığı (geçersizse AlgoProd restart edilene kadar bütün DB çağrıları başarısız olur).
- Her çağrı `authorization: <token>` metadata'sı ile gider (**`Bearer ` öneki yok**; trade-data-app `util/helper.go` öneki `TrimPrefix` ile isteğe bağlı atıyor, sorun değil). Hiçbir çağrıda **deadline yok**; trade-data-app yanıt vermezse çağıran thread bekler (gRPC handler, strateji thread'i).
- Hata davranışı çağrı başına değişir: çoğu log'lar ve boş/varsayılan döner; `getStrategySettings`, `setStrategySettings` gRPC status'ünü hiç okumaz.

### 7.2 Çağrılar

| `AlgoService` RPC | Metot | Çağıran / ne zaman | Durum |
|-------------------|-------|--------------------|-------|
| `AlgoLogin` | `Login` / `LoginAsGuiUser` | ctor; her `StrategyLogin` | aktif |
| `GetAllInstruments` | `getInstruments` | `SettingsManager` açılış | aktif |
| `GetFictiveInstrumentSettings`, `GetFictiveItemSettings` | aynı adlı | `SettingsManager`, `OrderbookManager` açılış (fiktif endeksler) | aktif |
| `GetUnderlyingInstrumentsWithFuture` | `getAllInstrumentsWithFuture` | `SubscribeToAllFutures`; sonuç süreç ömrü boyunca önbellekte | aktif |
| `GetUserAccounts` | `getUserAccounts` | Özet aboneliği (§5.3) | aktif |
| `GetStrategySettings` | `getStrategySettings` | `StrategyManager::readAlgoSettings` (açılış), `updateStrategies` (`UpdateExtSettings`) | aktif |
| `SetStrategySettings` | `setStrategySettings` | Her strateji komutu (§3.1 adım 5). `strategy_name`: `Arbitrage`, `VWAP`, `Fund_Tracker`, `AKD`; diğerleri boş | aktif |
| `GetArbitrageData` | `getArbitrageData` (önbellekli), `getArbitrageDataForced` | `ArbitrageTracker` ctor, her DB güncellemesinden sonra, `updateStateFromDatabase` | aktif |
| `SetArbitrageData` | `setArbitrageData` (senkron) / `setArbitrageDataAsync` | İlk kayıt senkron (ctor); sonraki her durum değişikliği async (§7.3) | aktif |
| `DeleteArbitragePackage` | `deleteArbitragePackage` | Paket silme komutu. Sonuç `resp.status()==1`; gRPC status okunmaz. | aktif |
| `GetFundData`, `SetFundData` | `getBYFData(inst,…)`, `setBYFPackageData` | `FundTracker` ctor (yoksa ilk kayıt), paket tamamlanınca; senkron | aktif |
| `GetByfSettings` | `getBYFData()` | `FundTracker::readPcfFile` (strateji başlangıcı) | aktif |
| `SubscribeBrokarageResults` (bidi) | `subscribeToVWAPData` → `startVWAPAKDStream` | VWAP, AKD broker listesi doluysa (ilk abonede stream açılır) | aktif ama bozuk olabilir (Şüpheli) |
| `UnsubscribeBrokerageResults` | `unsubscribeToVWAPData` | çağrısı `TradeByVolume`'da yorum satırı | çağrılmıyor |
| `UnsubscribeBrokerageSide` | `unsubscribeToVWAPDataSide` | RPC satırı yorumda | çağrılmıyor |
| `GetBrokerageFirmList` | `getBrokerInfos` | hiçbir yerden | çağrılmıyor |
| `FetchAkd` (stream) | `subscribeToAkd` → `fetchAkd` | yalnız `TradeByBSRatio` | kullanılmayan strateji |
| `GetTimeBasedData`, `FetchHistoricalData` | `getTimeBasedData`, `getHistoricalData` | `TradeByBSRatioData`, `HistoryManager` (← `MovingAverageCalculator`, `TradeByBSRatio`, `WarrantTracker`, `WarrantUnderlyingTracker`) | kullanılmayan stratejiler |
| `GetInstrumentScores`, `GetIndice`, `GetAllInstrumentsInIndice` | aynı adlı | `TradeByBSRatio`, `WarrantUnderlyingTracker`, `WarrantOverallTracker` | kullanılmayan stratejiler |
| `SetInstrumentScore`, `GetAllArbitrageData`, `GetIndiceOpeningPrice` | aynı adlı | hiçbir yerden | çağrılmıyor |
| `UpdateArbitragePackage`, `GetAllFundsData` | — | AlgoProd'da istemci metodu yok | — |

### 7.3 Kalıcılık ve restart

| Veri | Ne yazılır | Ne zaman | Restart'ta |
|------|-----------|----------|-----------|
| Strateji ayarı (`StrategySettings`) | Gelen komut map'i, `Strategy_Start` hariç; wrapper `clientmodels.X` → `servicemodels.AlgoX` (Map/List atlanır) | Her `StrategyRequest`; Subscribe*Future ile yaratılan arbitrajda yalnız taban alanlar | `readAlgoSettings`: `application_user = dbUsername` ile hepsi okunur, `convertAlgoSettings` geri çevirir, `commandReceived(cmd)` ile stratejiler **durmuş** yaratılır. Hata log'lanıp atlanır. GUI kuyrukları açılmaz (§5.1). |
| Arbitraj durumu (`ArbitrageData.h` `ArbitrageStruct`: pozisyonlar, `totalProfit`, `arbStrategyType`, paket listesi; paket: kontrat, raw fiyatlar, faiz, marjlar, aktif/tamamlandı) | Bütün struct (paketler dahil) | İlk kayıt senkron; sonra `setArbitrageDataAsync`: yerel önbellek (`arbitrageDataMap`, anahtar `<türevId>_<hesap>_<sid>`) hemen güncellenir, DB yazımı `pullArbitrageData` thread'inde **100 ms**'de bir kuyruk boşaltılarak | `ArbitrageTracker` ctor `getArbitrageData` ile pozisyon ve paketleri geri alır |
| Fon durumu (`BYFState`: fon/spot pozisyonu, paketler, alt emirler) | Bütün struct | Senkron `SetFundData`; yanıt yeni durum olarak alınır | `FundTracker` ctor `GetFundData` |
| PCF (`BYFData`) | — (salt okunur) | — | Strateji başlarken `GetByfSettings` |
| VWAP | DB'de durum yok | — | ❓ doğrulanmadı: pozisyon emir defteri istatistiğinden (önceki pozisyon order-service'ten) |

`Strategy_Start` yazılmadığı için **restart sonrası hiçbir strateji kendiliğinden başlamaz** (HFT ile aynı).

## Şüpheli

- `SubscribeToOrderbook` gövdesinde `return` yok → tanımsız davranış (çöküş veya çöp status). trade-data-app `GuiSubscribeToOrderbook` AlgoProd tiplerinde (Arbitrage, VWAP; `ConvertStrategyType` sonrası) bunu çağırıyor. backend-sozlesmesi.md'deki "motor strateji yoksa yaratır ve DB'ye yazar" AlgoProd için geçerli değil.
- `FetchCommands` `Write` hatasını ve `IsCancelled`'ı kontrol etmiyor: trade-data-app yeniden bağlandığında eski handler sonsuza dek çalışır, bir gRPC thread'i tutar ve aynı kuyruklardan **mesaj çalar** (ölü stream'e yazılan mesajlar kaybolur). Her yeniden bağlanmada bir tane daha birikir.
- `GUIManager::workAsyncron` uyumadan dönen meşgul döngü (`userListMtx` altında) → bir CPU çekirdeği sürekli %100. ❓ doğrulanmadı: prod'da çekirdek pinlemesi.
- `startVWAPAKDStream` iç döngüsü uyumadan döner (ilk VWAP AKD aboneliğinden sonra bir çekirdek %100). `isVWAPStreamOK` stream bitince -1 olur (truthy) veya hatada 1 kalır; döngü ölü stream'e yazmaya devam eder, stream yeniden açılmaz. Okuyucu thread'e yerel `rpc` referansla geçiyor.
- `getBrokerInfos` hiç çağrılmadığı için `brokerMap` boş; `getBrokerShortName` her kurum için `""` döner → `SubscribeBrokarageResults` isteğindeki `brokarage_codes` boş string'lerden oluşur. VWAP AKD filtresi muhtemelen hiç eşleşmiyor (vwap.md "AKD filtresi" bölümüyle çelişir). ❓ doğrulanmadı: trade-data-app'in boş kodu nasıl ele aldığı.
- `StrategyFactory::createStrategy` istisnası `commandReceived(cmd)` içinde yutuluyor; dış akış ayarı DB'ye yazıp `OK` dönüyor. GUI başarı görür ama strateji yoktur; restart'ta aynı ayar yine yüklenmeye çalışılır.
- `setArbitrageDataAsync` her zaman `true` döner; `updateDatabaseWithCurrentState`'teki "insert error → stop" dalı ölü. DB yazım hatası yalnız `pullArbitrageData` log'unda görünür, strateji çalışmaya devam eder; önbellek DB'den ayrışabilir.
- `checkParams`: `TradeByBSRatio` case'i `break`'siz, VWAP kontrollerine düşüyor (kullanılmayan tip). `Is_Spot_Sell_Allowed`, `Derivative_Type`, `Sell_Type` Int>0 olarak zorunlu; UI char kodu yollamazsa komut `INVALID_ARGUMENT` alır, sebep yalnız log'da.
- `readAlgoSettings`/`updateStrategies` unique key'i `Any::value()` (serileştirilmiş `AlgoStringValue` baytları) üzerinden "ilk boşluk-olmayan + 1" kırparak çıkarıyor: protobuf tag (0x0A) ve uzunluk baytını atmak için hack. Key uzunluğu 9, 10, 11, 13, 32 veya ≥128 ise yanlış kırpılır; `updateStrategies`'te bu key `setStrategyNotifier`'a gidiyor.
- `sendAndSubscribeToSummary` VWAP case'i `break`'siz, `default`'a düşüp "strategy type is unknown!" hata log'u basıyor (işlev etkilenmiyor). Arbitraj özeti `arbitrageDataMap` önbelleğine dayanıyor; DB'de olup bu süreçte hiç okunmamış kayıtlar özete girmez.
- `Total_Profit` aktivitede ×1000, özette ×1000'siz gidiyor; UI iki kaynağı karıştırırsa 1000 kat hata. ❓ doğrulanmadı: UI'ın hangi alanı nasıl böldüğü.
- `userTokenMap` birden çok gRPC thread'inden kilitsiz yazılıp okunuyor (HFT ile aynı data race). `StrategyLogin` token'ı stdout'a basıyor.
- `UpdateExtSettings` ve `SubscribeToOrderbook` yetki kontrolü yapmıyor: :9098'e erişen herkes arbitraj stratejilerini durdurabilir.
- `dispatchPackages` Delete'te DB silme strateji doğrulamasından **önce** yapılıyor; Update çalışan stratejide sessizce reddediliyor ama yanıt `OK`.
- `BaseCommand` ctor bir alan eksikse erken dönüyor; sonraki üyeler (`strategyType` vb.) ilklenmemiş kalıyor ve strategy key'e çöp girebilir.
- DB istemcisinde token yenileme ve deadline yok; trade-data-app takılırsa GUI komutu (senkron `SetStrategySettings`) ve fon stratejisi (`SetFundData`) bloklanır.
