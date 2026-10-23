---
kapsam: HftSrvProd gRPC katmanı — GUI komutunun (trade-data-app → StrategyService) HFT içindeki yolu, command pattern ve wire biçimi, GUI'ye dönen mesajlar (FetchCommands / FetchOrders), yeni wire alanı ekleme
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# Komutlar ve gRPC (`StrategyService`)

İndeks: [README.md](README.md). Karşı taraf (istemci) trade-data-app'tir. Onun RPC kullanımı [`trade-data-app/api.md` § 9](../trade-data-app/api.md), stream tüketimi [`trade-data-app/veri-akisi.md` § 5.2](../trade-data-app/veri-akisi.md) dosyasında anlatılır, burada tekrar edilmez.
Bu dosyada olmayan konular: strateji çekirdeği ve thread modeli → [strateji-cekirdegi.md](strateji-cekirdegi.md), emir yaşam döngüsü → [emir-yasam-dongusu.md](emir-yasam-dongusu.md), ITCH → [itch-entegrasyonu.md](itch-entegrasyonu.md), config → [config.md](config.md). Strateji başına wire alanları → [`20-stratejiler/`](../../20-stratejiler/README.md).

Kod: `src/GUI/GUIManager.*`, `src/Strategy/Service/StrategyServiceImpl.*`, `src/Commands/*`, `src/Globals/GuiConstants.h`, `src/Globals/Enumarations.h`, `src/Globals/Parser.h` (`Parser::extractValue`), `src/strategies.proto`, `src/common.proto`.

## 1. Sunucu ve kimlik doğrulama

- `GUIManager::start` ayrı bir thread açar ve bu thread'de `startGrpcServer` çalışır. Sunucu senkron gRPC'dir (`ServerBuilder`, `0.0.0.0:<grpcPort>`, insecure). Default health check servisi açılır ve `""` servisi SERVING olarak işaretlenir. trade-data-app yeniden bağlanma kararını bu health `Watch`'a göre verir.
- Her RPC, gRPC'nin kendi senkron thread havuzundaki bir thread'de çalışır. ❓ doğrulanmadı: havuz boyutu ayarlanmıyor, gRPC varsayılanı kullanılıyor. Her açık stream (`FetchCommands`, `FetchOrders`) bir thread'i sürekli meşgul eder (1 ms uyuyan polling döngüsü).
- **`StrategyLogin`**: `DatabaseServiceClient::LoginAsGuiUser` çağrılır. Bu, trade-data-app `AlgoService.AlgoLogin`'e `application=HFT` ile bir istek atar. Dönen token `userTokenMap[token] = username` olarak bellekte saklanır ve istemciye aynı token döner. Token boşsa yanıt `CANCELLED` olur (UNAUTHENTICATED değil). İstisna durumunda `INTERNAL` döner.
- **`checkAuthorization`**: metadata'daki `authorization` okunur, `Bearer ` öneki varsa atılır ve token `userTokenMap`'te aranır. `StrategyLogin` dışındaki her RPC bunu çağırır. Başarısızsa `UNAUTHENTICATED "Unauthorized"` döner.
  - Token'ların süresi dolmaz, silinmez ve diske yazılmaz. HFT yeniden başlarsa bütün token'lar geçersiz olur ve istemcinin yeniden login olması gerekir.

## 2. RPC'ler

| RPC | HFT'de ne yapar | Yanıt / hata |
|-----|-----------------|--------------|
| `StrategyLogin` | Bkz. §1 | `token` |
| `SetCommandRequest` | `message_type`'a göre `GUIManager::dispatch*` çağrılır (§3). İşlem senkrondur; RPC, dispatch bitince döner. | `success` + gRPC status (§3.5) |
| `FetchCommands` (server stream) | Global komut kuyruğunu boşaltır (§5.1) | `stream FetchCommandResponse` |
| `FetchOrders` (server stream) | Emir olay kuyruğunu 50'lik paketlerle gönderir (§5.2) | `stream FetchOrdersResponse` |
| `SubscribeToCommands` | **Abonelik kaydı tutmaz.** İstenen her `unique_key` için o anki durumu bir kez kuyruğa koyar (§5.3). | Her zaman `success=true`. Bulunamayan key log'a yazılıp atlanır. |
| `UnsubscribeFromCommands` | `userConnectionsMap`'ten siler. Bu map hiçbir yerde doldurulmaz. | Pratikte her zaman `NOT_FOUND "Connection Not Found"` |
| `SubscribeToOrderbook` | Key `<obid>_<account>_<strategy_identifier>_<tip>` biçimindedir. Strateji bellekte yoksa boş bir `BaseStrategyCommand` ile oluşturulur (`createStrategy(..., false)`), ardından `OuchManager::insertStrategy` ile order-service'e kaydedilir. | `position` (= `strategy->balance`), `instrument_id`, `instrument_symbol`, `unique_key` |
| `AlgoSetAccountStrategy` | Aynı işi yapar, sıra terstir: önce `insertStrategy`, sonra `createStrategy`. | `success` |
| `FetchAllUniqueKeys`, `UpdateExtSettings`, `SubscribeToFuture*` | **HFT'de override edilmemiş.** gRPC varsayılanı döner. | `UNIMPLEMENTED` |

**Strateji tipi numaralandırması iki farklı enum kullanır:**
- `AlgoSetAccountStrategyRequest.strategy_type`, map içindeki `Strategy_Type` ve `unique_key`'in son parçası `common.proto` `StrategyType` / `ouchSDK::enums::StrategyType` numaralarını kullanır: HFT=4, MaxPrice=9, TheoreticalPrice=8, HFT_Warrant=13, MinPrice=14, HFT_WarrantAdvanced=15.
- `SubscribeToOrderbookRequest.strategy_type` ve `StrategyOrder.strategy_type` ise `strategies.proto` `StrType`'ı kullanır: HFT=3, MAX_PRICE=4, THEORIC_PRICE=5, HFT_WARRANT=7, MIN_PRICE=8, HFT_WARRANT_ADVANCED=9.
- Çevrim `getOuchSDKVersionEnum` ve `decodeStrTypeFromPassthrough` ile yapılır. Bu iki fonksiyonun tanımadığı tipler (OrderChase vb.) `UNKNOWN` olur.

## 3. `SetCommandRequest` dispatch

`StrategyServiceImpl::SetCommandRequest` → `checkAuthorization` → `switch (message_type)`:

| `CommandTypeRequest` | Dispatch | Fabrika |
|----------------------|----------|---------|
| `Command_Type_StrategyRequest` (1) | `dispatchStrategy` | `CommandFactory::createStrategyCommand` |
| `Command_Type_BalanceRequest` (3) | `dispatchBalance` | `createSetBalanceCommand` |
| `Command_Type_OrderRequest` (4) | `dispatchOrders` | `createOrderCommand` |
| `Command_Type_CancelAllOrdersRequest` (7) | `dispatchCancelAllOrders` | `createCancelAllOrderCommand` |
| `Command_Type_ClosePositionRequest` (9) | `dispatchClosePosition` | `createClosePositionCommand` |
| diğerleri (2, 5, 6, 8, 10) | — | `INVALID_ARGUMENT "Invalid Message Type"` |

- `CommandRequest.unique_key` yalnızca log'a yazılır. Dispatch'ler key'i map'teki `Strategy_Unique_Key` alanından okur.
- Balance, CancelAll ve ClosePosition fabrikaları map içinde ayrıca `Command_Type` (IntValue) alanını arar ve değerin `hft::enums::CommandType` ile eşleşmesini ister: Balance=3, CancelAll=7, ClosePosition=9. Alan yoksa ya da değer uyuşmuyorsa fabrika `nullptr` döner ve yanıt `INVALID_ARGUMENT` olur.
- `GUIManager::checkParams` tanımlı ama hiçbir yerden çağrılmıyor. Zorunlu alan kontrolünü her dispatch kendi içinde yapar.

### 3.1 Strateji komutu: "UI'da Başlat'a basınca HFT'de ne olur"

1. trade-data-app, stratejinin **bütün** ayar map'ini `Strategy_Start=true` ile `Command_Type_StrategyRequest` olarak gönderir (tip kontrolü trade-data-app'te yapılır: api.md `GuiStrategySetCommands`).
2. `createStrategyCommand` `Strategy_Type` değerini `IntValue` olarak okur ve bu değere göre bir command sınıfı seçer: MAX_PRICE→`MaxPriceCommand`, HFT→`HftClassicCommand`, ORDER_CHASE→`OrderChaseCommand`, THEORETICAL_PRICE→`TheoreticalPriceCommand`, WARRANT→`HftWarrantCommand`, WARRANT_ADVANCED→`HftWarrantAdvancedCommand`, MIN_PRICE→`MinPriceCommand`. Diğer tiplerde `nullptr` döner → `INVALID_ARGUMENT "Invalid strategy command"`.
3. `StrategyManager::getStrategy(uniqueKey)`. Strateji yoksa `createStrategy(cmd, false)` çağrılır (§4.4). `createStrategy`'de ORDER_CHASE case'i yoktur, bu yüzden OrderChase stratejisi oluşmaz → `INVALID_ARGUMENT "Failed to create strategy"`.
4. `strategy->setCommand(cmd)`. Command **tamamen değiştirilir**, eski command ile birleştirme (merge) yapılmaz. Mesajda olmayan alan varsayılan değerine döner. Başlat/durdur bilgisi `BaseStrategyCommand::isStarted()` (`Strategy_Start`) üzerinden stratejiye geçer. Stratejinin bunu nasıl uyguladığı [strateji-cekirdegi.md](strateji-cekirdegi.md) dosyasındadır. `false` dönerse (örneğin HftClassic kilidi 100 µs içinde alamadıysa) yanıt `RESOURCE_EXHAUSTED` olur.
5. `cmd->saveStrategySettings(message)`: `Strategy_Start` **hariç** bütün alanlar senkron gRPC çağrısıyla `AlgoService.SetStrategySettings`'e yazılır (`strategyName`: `HFT`, `MAX_PRICE`, `MIN_PRICE`, `THEORETICAL_PRICE`, `HFT_WARRANT`, `HFT_WARRANT_ADVANCED`). Dönüş değeri kontrol edilmez. DB yazımı başarısız olsa da komut başarılı sayılır (DB tarafındaki rollback kuralı: [sema.md](../trade-data-app/sema.md)). `Strategy_Start` kaydedilmediği için restart sonrasında DB'den yüklenen stratejiler (`ItchSdkClient::loadStrategiesFromDb`) **durmuş** hâlde başlar.
6. `enqueueCommand(cmd)`: yeni command `FetchCommands`'a snapshot olarak gönderilir. UI'daki "çalışıyor" göstergesi bu echo'dan gelir.
7. Yanıt `OK`, `success=true`.

Durdurma da aynı yoldan gider; fark `Strategy_Start=false` olmasıdır. Ayar güncellemesi de aynı yoldur, ayrı bir RPC yoktur.

### 3.2 Manuel emir komutları (`Command_Type_OrderRequest`)

`createOrderCommand`, `Order_Event_Type` (`hft::enums::OrderEventType`) değerine bakar: 1 Enter, 2 Cancel, 3 Replace, 4 TheoreticalOrder. 5 (`HftWarrantOrder`) ve bilinmeyen değerler `nullptr` → `INVALID_ARGUMENT`. Alanların ortak kısmı `OrderCommand` ctor'unda parse edilir: `Command_Type`, `Strategy_Type` (Int), `Orderbook_Id` (Long), `Strategy_Id`, `Exchange_Info` (**yalnızca bu alan okunur, `Account`'a fallback yoktur**), `Strategy_Unique_Key`, `Order_Channel` (Int), `Order_Event_Type`.

**EnterOrder** (`GUIManager::handleEnterOrder`):
- Strateji key'i `<Orderbook_Id>_<Exchange_Info>_<Strategy_Id>_<Strategy_Type>` olarak kurulur. Bulunamazsa `getStrategyByDerivative` ile varant/türev üzerinden aranır. O da bulunamazsa `OuchManager::insertStrategy` çağrılır, ama bu çağrı yalnızca order-service'e kayıt yapar ve `StrategyManager`'a strateji eklemez. Sonuç `INTERNAL "Strategy creation failed"` olur (koddan çıkarım). Pratikte manuel emirden önce stratejinin `SubscribeToOrderbook` ile bellekte açılmış olması gerekir.
- Alanlar ve varsayılanlar:

| Alan | Wrapper | Varsayılan | Not |
|------|---------|-----------|-----|
| `Order_Side` | Int | 0 | **1=BUY, 2=SELL, 3=SHORT** (proto `Side`), `ouchSDK` `'B'/'S'/'T'`'ye çevrilir |
| `Order_Quantity` | Long | 0 | lot; 0 → `INVALID_ARGUMENT` |
| `Order_Price` | Long | 0 | **raw fiyat** (`10^decimalCount` ölçeği, [sözlük](../../00-genel/sozluk.md)). Market değilse >0 olmalı |
| `Time_In_Force` | Int | 1 (DAY) | `ouchSDK::enums::TimeInForce` |
| `Order_Type` | Int | 3 (LIMIT) | 2=MARKET yalnız `Order_Channel=2` (FIX) ile kabul edilir ⚠ master'da yok (2026-10-22) |
| `Order_Channel` | Int | 1 (OUCH) | 2=FIX → her zaman order-service (`OuchManager::enterOrder`) ⚠ master'da yok |
| `Order_Lvl_Count` | Int | **0** | ≥1 olmalı; gönderilmezse `INVALID_ARGUMENT "Invalid order level count"`. Market ile >1 yasak. |
| `Is_Active` | Bool | false | parse edilir, kullanılmaz |

- `strategy->userOrderBlockReason(obid, side)` boş değilse yanıt `FAILED_PRECONDITION <sebep>` olur. Örnek: Varant Toplu çalışırken yapılan elle satış ([varant-toplu.md](../../20-stratejiler/varant-toplu.md)). ⚠ master'da yok.
- Emir `Hft::EnterOrder` ile kurulur, `MessageType::UserOrder` (`'1'`) kullanılır. `StrategyInfo` komuttaki `Orderbook_Id` ile kurulur, yani türev enstrüman olabilir. Gönderim README'deki desene uyar: SDK → `ownsAccount` değilse order-service ([README § Emir gönderme deseni](README.md#emir-gönderme-deseni)).
- `Order_Lvl_Count = N > 1` ise N emir gider. İlk emir verilen fiyattandır. Sonraki emirler BUY'da `i×tick` aşağıda, SELL/SHORT'ta `i×tick` yukarıdadır. Tick, **stratejinin kendi orderbook'u** ve baz fiyat ile `ItchSdkClient::getTickSize`'dan alınır.
- `OK` yanıtı yalnızca "gönderim denendi" anlamına gelir. Emrin kabulü `FetchOrders` ile gelir. SDK hesabın sahibi olduğu halde `enterOrder` `false` dönerse emir gitmez, yanıt yine `OK` olur.

**CancelOrder**: `Order_Token` (String) zorunludur. `maosdk->ownsOrder(token)` doğruysa SDK, değilse order-service kullanılır. Yanıt her zaman `OK`. ⚠ master'da yok: sahiplik önce kontrol ediliyor (master'da önce SDK deneniyordu).

**ReplaceOrder**: `Order_Token`, `Order_Quantity` (Long), `Order_Price` (Long, raw). Fiyat ve miktarın **ikisi birden pozitif olamaz** (`INVALID_ARGUMENT`); replace ya fiyat ya miktar değiştirir. Yeni token `UtilityClass::generateToken()` ile üretilir. Yönlendirme Cancel ile aynıdır. `Order_Channel` burada `LongValue` olarak okunur ama kullanılmaz.

**TheoreticalOrder** (`Order_Event_Type=4`): Enter'a benzer, farkları şunlar: `Expected_Price` (Long, raw) >0 olmalı, `MessageType::TheoreticalOrder` (`'5'`) kullanılır ve emir `HftTheoreticalPrice::addTheoreticalOrder`'a kaydedilir. Side 1/2/3 olarak gelir. Ayrıntı [teorik-fiyat.md](../../20-stratejiler/teorik-fiyat.md).

### 3.3 CancelAll, ClosePosition, SetBalance

| Komut | Zorunlu | Davranış |
|-------|---------|----------|
| CancelAll (`Command_Type=7`) | `Exchange_Info` veya `Account` | `Orderbook_Id=0` → `StrategyManager::stopAllStrategies()` (**hesaptan bağımsız, bütün çalışan stratejiler**) + `cancelAllStrategyOrders(account)`. `Orderbook_Id≠0` → `Strategy_Unique_Key` ile bulunan stratejide `cancelAllOrders`. `Order_Side`: 0=iki taraf, 66 (`'B'`)=alış, 83 (`'S'`)=satış. Strateji yoksa `NOT_FOUND`. |
| ClosePosition (`Command_Type=9`) | `Exchange_Info`/`Account` | `Orderbook_Id=0` → `stopAllStrategies()` + `closeAllPositions()` (hesap filtresi yok). Aksi halde `closeThePositionForSingleStock` çağrılır. Sonuç eşlemesi: `NotFound`→`NOT_FOUND`, `InProgress`→`ALREADY_EXISTS`, `AlreadyClosed`/`OnlyCancelled`/`OnlyClosed`/`CancelAndClosed`→`OK`. |
| SetBalance (`Command_Type=3`) | `Strategy_Unique_Key` | Strateji yoksa boş `BaseStrategyCommand` ile oluşturulur ve `insertStrategy` çağrılır. Sonra `strategy->setBalance(side, price, qty)` → `Strategy::updatePosition`. Bu bir **delta**'dır, dolum gibi uygulanır (BUY'da `balance += qty`, `profit -= qty×price`, FIFO lot eşleşmesi). Mutlak bir set değildir. `Order_Side`: 66=BUY, 83=SELL, 84 (`'T'`)=SHORT, başka değer UNKNOWN (SELL dalına düşer). `Order_Price` Long raw, `Order_Quantity` Long lot. |

`Order_Side` kodlaması komuta göre değişir: EnterOrder/Theoretical'da 1/2/3, CancelAll/SetBalance'ta ASCII kodu. `CancelAllOrderCommand` ctor'undaki yorumda satış `86 ('V')` yazıyor, ama kod 83 (`'S'`) ile karşılaştırıyor.

### 3.4 Hata ve yanıt biçimi

- Başarıda `CommandResponse{success=true}` + `Status::OK` döner. Hatada `success=false` ve gRPC status'ün `error_code` / `error_message` alanları dolar; mesajlar yukarıdaki tablolarda geçen İngilizce metinlerdir. trade-data-app bunları HTTP'ye çevirir (api.md).
- Asenkron sonuçlar (emir kabul/ret, strateji durumu) RPC yanıtında gelmez. Bunlar §5'teki stream'lerden gelir.

## 4. Command pattern ve wire biçimi

### 4.1 Sınıflar

| Sınıf | Rol |
|-------|-----|
| `BaseCommand` | Ortak alanlar (`Command_Type`, `Orderbook_Id`, `Exchange_Info`→fallback `Account`, `Strategy_Id`, `Strategy_Type`). Saf sanal `toClientMessage(FetchCommandResponse&)`. |
| `BaseStrategyCommand : BaseCommand` | Strateji komutlarının tabanı: `Strategy_Start`→`started`, `Strategy_Unique_Key`→`uniqueKey`, `start()`/`stop()`/`isStarted()`, sanal `toClientMessage`, `saveStrategySettings`, `getDefaultSettings`. |
| `<X>Command : BaseStrategyCommand` | Strateji başına alanlar. Ctor = parse. |
| `OrderCommand` (ayrı hiyerarşi) | `EnterOrderCommand`, `CancelOrderCommand`, `ReplaceOrderCommand`, `TheoreticalPriceOrderCommand`. `toClientMessage` boştur, bunlar GUI'ye geri gönderilmez. |
| `SetBalanceCommand`, `HftWarrantBalanceCommand`, `SummaryCommand`, `MaxPriceStateCommand`, `MinPriceStateCommand`, `WarrantAdvancedEventCommand` | Çoğunlukla **giden** mesajlar (§5.4). İkisi hem gelen hem giden yönde kullanılır: `SetBalanceCommand` ve `SummaryCommand` hem map'ten parse edilir hem de kendi ctor'larıyla üretilir. |
| `CancelAllOrderCommand`, `ClosePositionCommand` | Yalnızca gelen yönde. |

### 4.2 Sözleşme

- **Parse = ctor.** `<X>Command(const Map<string, Any>&)` önce taban ctor'u çağırır, sonra her alanı `Parser::extractValue<T, Wrapper>(msg, KEY, default)` ile okur.
- **`toClientMessage(resp)`**: önce `BaseStrategyCommand::toClientMessage` çağrılır. Bu `message_type=Command_Type_StrategyResponse` set eder, `Command_Type`, `Orderbook_Id`, `Account`, `Strategy_Id`, `Strategy_Type`, `Is_Running` ve `Strategy_Start` alanlarını ekler ve `resp.unique_key`'i doldurur. Çağrı sırası önemlidir: alanlar `mutable_fields()->insert` ile eklenir ve protobuf `Map::insert` **var olan anahtarın üzerine yazmaz**, ilk eklenen değer kalır. Taban alanları önce eklendiği için alt sınıf aynı anahtarı tekrar yazsa da taban değeri kalır.
  - Snapshot'ta `Is_Running` ve `Strategy_Start` alanlarının ikisi de `started` değerini taşır. Stratejinin gerçek `isRunning` durumunu göstermezler.
- **`getDefaultSettings(map)`**: `StrategyManager::createStrategy` strateji ilk kez GUI yoluyla (`isItchSdkClient=false`) oluşturulduğunda bunu çağırır ve sonucu `saveStrategySettings` ile DB'ye yazar. Taban sürüm şu alanları yazar: `Strategy_Start=false`, `Is_Running=false`, `Strategy_Type`, `Orderbook_Id`, `Strategy_Id`, `Strategy_Unique_Key`, `Account`. Strateji sürümü kendi alanlarını ekler.

### 4.3 Wire biçimi, tipler, eksik alan

- Bütün komutlar `map<string, google.protobuf.Any>` içinde taşınır. Any'nin içi `clientmodels.{Bool,Int,Long,Double,String,List,Map}Value` sarmalayıcılarından biridir (`strategies.proto`).
- **Tip katıdır.** `Any::UnpackTo` type URL'i kontrol eder. Bir alan `IntValue` olarak beklenip `LongValue` olarak gelirse unpack başarısız olur ve alan **sessizce varsayılan değerini** alır. Hata ya da log oluşmaz. Fabrikaların `Strategy_Type` / `Command_Type` / `Order_Event_Type` okumalarında `UnpackTo` dönüşü kontrol edilmez. Yanlış tip geldiğinde değer 0 olur ve sonuç `INVALID_ARGUMENT` olur.
- **Eksik alan** da varsayılan değerini alır (genelde 0/false/""). Önemli istisnalar:
  - HftClassic `Hft_Stop_Loss_Level`=-1, `Second_Rule_Duration`=1 (0 da 1'e çekilir).
  - EnterOrder `Time_In_Force`=1, `Order_Type`=3, `Order_Channel`=1, `Order_Lvl_Count`=0.
  - `Strategy_Unique_Key` yoksa `BaseStrategyCommand` ctor'u erken döner: `uniqueKey=""` olur ve sınıf içindeki `strategyType` HFT varsayılanında kalır.
- **Gerçek tip parse kodudur, `GuiConstants.h` yorumu değil.** Yorum ile kod birkaç yerde uyuşmuyor. Örnek: `Second_Rule_Duration` yorumda `IntValue`, HftClassic parse'ında `LongValue`, `toClientMessage`'da `IntValue`, `getDefaultSettings`'te `LongValue`. Yeni kod yazarken her alan için ilgili `<X>Command.cpp` ctor'una bakın.
- DB'ye giderken `DatabaseServiceClient::setStrategySettings` her wrapper'ı aynı tipte `servicemodels.Algo*Value`'ya çevirir. Tanımadığı wrapper'ı (`MapValue`) atlar, `ListValue`'yu olduğu gibi geçirir. Okurken `convertAlgoSettings` ters çevrimi yapar.
- **Ad çakışmaları** (`GuiConstants.h`): `STRATEGY_IDENTIFIER` ve `STRATEGY_SETTINGS_ID` aynı stringdir (`"Strategy_Id"`). `STRATEGY_COMMAND_TYPE` ve `COMMAND_TYPE` de öyle (`"Command_Type"`).
- **`GuiConstants.h` tek otorite değil.** Bazı giden mesajlar anahtarı string literal olarak yazar: `WarrantAdvancedEventCommand` (`instrumentId`, `symbol`, `event`, `state`, `reason`, `quantity`, `price`, `token`, `prevToken`, `underlying*`), `HftWarrantBalanceCommand` (`Underlying_Balance`, `Derivatives_Balance`, `Derivatives_Count`) ve özet satırları (`obid`, `account`, `strategyId`, `strategyType`, `orderbookName`, `isRunning`, `balance`, `hftType`, `profit`, varant alt alanları). Yeni alan **gelen** yöndeyse `GuiConstants.h`'a eklenir.

### 4.4 Ortak alanlar (bütün strateji komutları)

| Anahtar | Wrapper | Anlam |
|---------|---------|-------|
| `Strategy_Unique_Key` | String | `<obid>_<hesap>_<identifier>_<StrategyType>` ([katalog](../../20-stratejiler/README.md)). HFT bunu kendisi kurmaz, gelen değeri kullanır (baştaki boşluk/form-feed kırpılır). |
| `Strategy_Type` | Int | `common.proto` `StrategyType` (§2) |
| `Orderbook_Id` | Long | Dayanak enstrüman |
| `Exchange_Info` / `Account` | String | Hesap. Gelen yönde `Exchange_Info` önceliklidir, giden yönde her zaman `Account` yazılır. |
| `Strategy_Id` | String | strategy identifier |
| `Command_Type` | Int | Strateji mesajında bilgi amaçlıdır. Balance/CancelAll/ClosePosition'da zorunludur (§3). |
| `Strategy_Start` | Bool | Başlat/durdur. DB'ye kaydedilmez. |
| `Is_Running` | Bool | Snapshot'ta `Strategy_Start` ile aynı değeri taşır. Bazı stratejiler ayrıca parse eder (HftClassic `is_running`). |

**`createStrategy` uyarısı:** `createStrategyImpl<CommandType, StrategyType>` gelen command'ı `static_pointer_cast<CommandType>` ile çevirir. `SubscribeToOrderbook`, `AlgoSetAccountStrategy` ve `dispatchBalance` ise somut tipte olmayan, düz bir `BaseStrategyCommand` geçirir (bkz. Şüpheli davranışlar).

## 5. GUI'ye dönen akış

### 5.1 `FetchCommands`

- Tek bir **global** kuyruk vardır: `globalCommandQueue` (`moodycamel::ConcurrentQueue<BaseCommandPtr>`). Kuyruğun sınırı yoktur, dolayısıyla backpressure da yoktur: istemci yokken ya da yavaşken mesajlar bellekte birikir.
- Stream döngüsü şöyle çalışır: `context->IsCancelled()` kontrol edilir ⚠ master'da yok, kuyruk `try_dequeue` ile boşaltılır, her öğe için `toClientMessage` → `Write` yapılır, kuyruk boşsa 1 ms uyunur. Döngü `GUIManager::isRunning()` doğru olduğu sürece devam eder.
- **İstek alanları yok sayılır.** `connection_id` ve `commands` alanlarına bakılmaz, istemci başına bir filtre uygulanmaz. Birden fazla `FetchCommands` stream'i açıksa her mesaj **yalnızca birine** gider (aynı kuyruktan rekabetle okunur). trade-data-app'in yanlışlıkla iki stream açması da bu sınıfa girer (veri-akisi.md § 5.2).
- `Write` başarısız olursa mesaj kuyruğun **sonuna** geri konur ve stream `CANCELLED` ile kapanır ⚠ master'da yok (master'da mesaj kayboluyordu). Bu durumda o mesajın sırası bozulur. Yeniden bağlanan stream, birikmiş eski snapshot'ları da alır.
- ❓ doğrulanmadı: moodycamel kuyruğu üretici başına FIFO'dur, farklı thread'lerden gelen mesajlar arasında genel bir sıra garantisi vermez.

### 5.2 `FetchOrders`

- Kaynak `internalOuchOrdersQueue`'dur (`OrderEvent` tutar: order ptr, tip, `preTradeQuantity`, üç latency, `prevPrice`). Bu kuyruğu dolduran yerler:
  - **MAOrderSDK callback'leri** (`HftMain.cpp`): `onAccepted` (duplicate değilse), `onRejected`, `onWireExecuted` (GUI'ye fill bu callback'ten gider, `onExecuted`'ten gitmez), `onReplaced` (eski fiyat, `updateOrder`'dan önce yakalanır), `onCanceled`.
  - Legacy `OuchWorker` → `StrategyManager::enqueueGuiOrder` → `processGuiOrders` yolu.
  - Handoff öncesi order-service yolundan (`ouchSDK::orderAccepted` vb.) giden emirler bu kuyruğa **girmez** (koddan). Bu emirleri GUI order-service feed'inden görür (api.md § 9).
- Stream açıldıktan sonra önce **3 sn** sabit beklenir ("replay timeout"). Sonra döngü başlar: önceki stream'in yazamadığı `unsentOrderEvents` (sırasıyla) ve ardından kuyruk, en fazla **50 olaylık** bir pakette `FetchOrdersResponse.orders` olarak gönderilir. `Write` başarısız olursa paket `unsentOrderEvents`'in **başına** geri konur ve sıra korunur ⚠ master'da yok. `order_types` filtresi ve `is_order_history_received` HFT'de kullanılmaz. Geçmiş replay'i de yoktur, yalnızca canlı olaylar gönderilir.
- **`StrategyOrder` alanları** (`buildStrategyOrderFromEvent`):

| Alan | Değer / birim |
|------|---------------|
| `operation` | `ORDER_OPERATION_ACCEPTED/EXECUTED/REPLACED/CANCELED/REJECTED` |
| `token`, `order_id` | client order token (replace'te **yeni** token), BIST order id |
| `price`, `prev_price` | **raw fiyat** (uint32). Executed'da işlem fiyatı. Replace'te `prev_price` = replace öncesi fiyat (yoksa registry'deki fiyat). |
| `quantity` | Accepted: `initialQuantity`. Executed: işlem miktarı (`exec_qty` ile aynı). Canceled: kabuldeki miktar. Replaced: yeni miktar. Lot. |
| `pre_trade_qty` | Accepted ve Replaced'da dolar |
| `side` | proto `Side` (1/2/3). Rejected'da her zaman `SIDE_UNKNOWN`. |
| `strategy_type` | **`StrType`** numarası (§2), passthrough'tan çözülür (`decodeStrTypeFromPassthrough`). Replace/cancel/execute'ta bu bilgi orijinal accept'ten alınır. |
| `strategy_identifier`, `account`, `orderbook_id` | identifier'ın sağındaki boşluk kırpılır |
| `custom_data`, `custom_data_size` | OUCH passthrough (`[cust:1]x[id:3]x[type:2][fatherRef:7]`) |
| `reason`, `reason_code` | Rejected/Canceled |
| `order_time` | OUCH mesaj timestamp'i (`getTimeStamp`). ❓ doğrulanmadı: epoch mu gün başı mı (ns) |
| `latency_writing_ns` | ns, socket `write()` süresi |
| `latency_network_ns` | ns, write sonrası → yanıtın yerelde alınması |
| `latency_bist_ns` | ns, write sonrası → BIST'in mesaja bastığı timestamp (MAOrderSDK `MAOrderStruct.h`) |
| `internal_ouch` | Emri taşıyan OUCH kullanıcı adı (`getOrderTokenToOuchClientUsernames`) |
| sabitler | `order_type=STRATEGY`, `application_type=HFT`, `protocol=OUCH`, `time_in_force=DAY`, `regular_order_type=LIMIT` (gerçek değerden bağımsız), `is_active` (Accepted/Executed/Replaced true) |

- Executed olaylarında latency alanları 0'dır (`enqueueExecutedOrderEvent` latency almaz).

### 5.3 `SubscribeToCommands` (anlık durum isteği)

Her `FetchCommandRequest` için:
- `StrategyRequest`: `strategy->getCommand()` kuyruğa konur (snapshot). Strateji MaxPrice/MinPrice ise ek olarak state mesajı gönderilir.
- `BalanceRequest`: `strategy->sendBalanceUpdate()` çağrılır (stratejiler override edebilir, örneğin varant).
- `SummaryRequest`: `unique_key` `SUMMARY_<hesap>` biçiminde olmalıdır. O hesabın özeti bir kez gönderilir.
- `MaxPriceStateRequest` (8): HftMaxPrice ya da HftMinPrice'a göre state gönderilir. Proto'da `Command_Type_MinPriceStateRequest` (10) tanımlı ama HFT'de işlenmiyor. Koddaki yorumda "proto'da ayrı MinPriceState yok" yazıyor, bu yanlış.

### 5.4 Giden mesaj tipleri (`FetchCommandResponse.message_type`)

| `CommandTypeResponse` | Üreten | İçerik |
|-----------------------|--------|--------|
| `StrategyResponse` (1) | `<X>Command::toClientMessage` | Stratejinin tam ayar snapshot'ı (§4.2) |
| `BalanceResponse` (8) | `SetBalanceCommand` (`Strategy::sendBalanceUpdate`), `HftWarrantBalanceCommand` | `Order_Side` (Int, ouchSDK char kodu, normalde 0), `Order_Price` (Long, 0), `Order_Quantity` (Long, **pozisyon lot**), `Profit`, `Realized_Profit`, `Open_Cost` (Long, **raw fiyat × lot**, TL'ye çevirmek için `10^decimalCount`'a bölünür), `Balance_Trigger_Timestamp` (Long, ns epoch, `system_clock`). Varant'ta ek olarak `Underlying_*`, `Derivatives_Balance` (JSON string), `Derivatives_Count`. |
| `SummaryResponse` (6) | `SummaryCommand` | `unique_key=SUMMARY_<hesap>`, `Account`, `Is_All_Accounts` (her zaman false), `Summary_Items` = `MapValue{ <uniqueKey> → MapValue{obid, account, strategyId, strategyType, orderbookName, isRunning, balance(Double), hftType, profit, …} }`. `profit` yalnızca `balance==0` iken gerçek değerdir, aksi halde 0. Varant ve Varant Toplu alt alanları için [varant.md](../../20-stratejiler/varant.md) ve [varant-toplu.md](../../20-stratejiler/varant-toplu.md). |
| `MaxPriceStateResponse` (9) | `MaxPriceStateCommand` **ve** `MinPriceStateCommand` | Tavan/Taban durum zarfı. `MinPriceStateResponse` (11) kullanılmıyor. Alanlar [tavan.md](../../20-stratejiler/tavan.md) ve [taban.md](../../20-stratejiler/taban.md) dosyalarında. |
| `HftWarrantDerivativeResponse` (10) | `WarrantAdvancedEventCommand` | Varant Toplu anlık olayı ⚠ master'da yok |

`ActivitiesResponse`, `PackageActivityResponse`, `PassiveOrderResponse`, `StatisticsResponse`, `BYFTheoreticalPriceResponse` HFT tarafından üretilmiyor.

### 5.5 Push zamanlaması (`StrategyStatesWorker`)

`StrategyManager::strategyStatesWorker` her **100 ms**'de bir şu adımları sırayla çalıştırır:
1. `processMaxPriceStateUpdates` ve `processMinPriceStateUpdates`: `markMaxPriceStateDirty` / `markMinPriceStateDirty` ile işaretlenmiş stratejiler için state mesajı gönderilir.
2. `processSummaryUpdates`: `markStrategyDirty` ile işaretlenmiş stratejilerin özet üyeliği güncellenir. Bir strateji özette yer alır eğer `balance>0`, çalışıyor, `profit≠0` ya da tipi WARRANT_ADVANCED ise. Ardından **en çok 1 sn'de bir**, özette stratejisi olan **her hesap** için, değişiklik olsun ya da olmasın, `SummaryResponse` gönderilir.
3. `processSetToOneUpdates`: stratejilerin `queueSetToOneUpdate` / `queueCommandPush` ile istediği snapshot'lar gönderilir (örnek: Tavan melt lot'un 1'e çekilmesi, Taban `Enter_Lot` güncellemesi). Aynı key için yalnızca son istek kalır.
4. `processGuiOrders`: legacy emir olayları (§5.2).

Doğrudan (worker beklemeden) kuyruğa yazanlar: `dispatchStrategy`, `createStrategy`, `SubscribeToCommands`, `Strategy::sendBalanceUpdate`, varant komutları ve `WarrantAdvancedEventCommand`.

## 6. Yeni wire alanı ekleme (kontrol listesi)

Yeni strateji tipi için: [README § Yeni strateji eklemek](README.md#yeni-strateji-eklemek-kontrol-listesi). Var olan bir stratejiye alan eklemek için:

1. **`GuiConstants.h`**: `#define` ekleyin. Anahtar adı birebir kullanılır, büyük/küçük harf duyarlıdır. Yorumda wrapper tipini yazın ve yazdığınız tipin kodla uyumlu olduğundan emin olun.
2. **`<X>Command` ctor**: alanı `Parser::extractValue<T, clientmodels::<W>Value>(msg, KEY, default)` ile okuyun. Varsayılan değeri, alan eksik geldiğinde güvenli olacak şekilde seçin (§4.3).
3. **`<X>Command::toClientMessage`**: aynı wrapper ile ekleyin. Taban anahtarlarıyla çakışan bir ad seçmeyin, `insert` üzerine yazmaz.
4. **`<X>Command::getDefaultSettings`**: aynı wrapper ile ekleyin. Eklemezseniz yeni oluşturulan stratejinin DB kaydında bu alan olmaz.
5. **Strateji**: `setCommand` içinde command'dan okuyun ([strateji-cekirdegi.md](strateji-cekirdegi.md)).
6. **trade-data-app**: `StrategyAttributes`'a satır ekleyin (`attribute_name` = anahtar, `value_type` = **aynı** `clientmodels.*` TypeUrl). Satır eksikse o stratejinin bütün ayar kaydı rollback olur. Tip uyuşmazsa GUI komutu 500 alır. Ayrıntı: [sema.md § Ayar saklama modeli](../trade-data-app/sema.md). Proto değişikliği gerekmez.
7. **UI**: alanı aynı wrapper tipiyle gönderin. UI tarafındaki wrapper `GuiXValue`'dur, trade-data-app bunu `ConvertFields` ile `clientmodels.XValue`'ya çevirir. Ardından snapshot'tan okuyun.
8. Strateji dokümanını güncelleyin (`20-stratejiler/<x>.md`, birim ve ölçek dahil).

## Şüpheli davranışlar (koddan)

- **Yanlış tipe `static_pointer_cast`:** `SubscribeToOrderbook`, `AlgoSetAccountStrategy` ve `dispatchBalance` düz bir `BaseStrategyCommand` oluşturup `createStrategy`'ye veriyor. `createStrategyImpl` bunu `static_pointer_cast<HftClassicCommand>` (vb.) ile çeviriyor. Bu tanımsız davranıştır: strateji, olmayan alt sınıf alanlarını okur. Sanal çağrılar ise taban sürüme gider, yani DB'ye yalnızca taban varsayılanları yazılır ve ilk snapshot taban snapshot'ı olur. ❓ doğrulanmadı: pratikteki etkisi.
- **`strategyType` gölgelenmesi:** `BaseCommand` ve `BaseStrategyCommand` ikisi de `strategyType` üyesi tanımlıyor. `setStrategyType` yalnızca alt sınıftakini set ediyor, `BaseCommand::toClientMessage` ise tabandakini yazıyor. Yukarıdaki yolla oluşan command'larda snapshot'taki `Strategy_Type` muhtemelen 0 olur. ❓ doğrulanmadı.
- `HftClassic::setCommand` kilidi almadan önce `command = ptr` atıyor. Kilit zaman aşımında `RESOURCE_EXHAUSTED` dönse bile command değişmiş oluyor. ❓ doğrulanmadı: diğer stratejiler de böyle mi.
- `handleTheoreticalOrder` `dynamic_pointer_cast<HftTheoreticalPrice>` sonucunu null kontrolü yapmadan kullanıyor. Key teorik tipte olmayan bir stratejiye denk gelirse çökme riski var.
- CancelAll ve ClosePosition `Orderbook_Id=0` ile çağrıldığında **bütün hesapların** çalışan stratejilerini durduruyor. CancelAll iptali hesapla sınırlı, ClosePosition `closeAllPositions` hesap filtresi kullanmıyor.
- Manuel emirde SDK hesabın sahibi olduğu halde `enterOrder` `false` dönerse emir gönderilmiyor ama yanıt `OK` dönüyor. Çok kademeli emirde tick stratejinin kendi orderbook'undan alınıyor; komuttaki orderbook türev olabilir.
- `buildStrategyOrderFromEvent` registry'de accept bulamazsa erken dönüyor, ama `FetchOrders` boş `StrategyOrder`'ı yine de pakete ekliyor. SDK enqueue anında kontrol eder; sonraki replace/rekey eski token'ı kaldırabilir ([K-230](emir-yasam-dongusu.md#ikinci-tur-gui-token-eşlemesi)). Legacy `processGuiOrders` yolu enqueue kontrolü de yapmaz. Legacy yol replace'te `prevPrice` da geçirmiyor.
- `userTokenMap` birden fazla gRPC thread'inden kilitsiz okunup yazılıyor (`StrategyLogin` yazıyor). Bu bir data race'tir.
- `UnsubscribeFromCommands` kısmi silmede `erase(it)` sonrasında geçersizleşmiş iterator'ı karşılaştırıyor. Map hiç dolmadığı için bu kod pratikte çalışmıyor.
- `globalCommandQueue` sınırsız ve tek tüketicili tasarlanmış. İki gateway ya da iki stream olduğunda mesajlar bölünüyor. Stream yokken kuyruk bellek büyütüyor.
- `FetchOrders` açılışındaki 3 sn'lik bekleme sabit ve koşulsuz. Bu süre içinde gelen olaylar kuyrukta bekliyor.
