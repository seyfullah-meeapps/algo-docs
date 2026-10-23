---
kapsam: trade-data-app içindeki canlı veri akışları — açılış, ITCH → emir defteri → WS, WebSocket feed'lerinin wire formatı, HFT/AlgoProd/order-service stream'leri, goroutine/kilit modeli ve kopma davranışı
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app — canlı veri akışları

Genel paket haritası ve port listesi: [`README.md`](README.md). REST/gRPC uçları: [`api.md`](api.md). DB: [`sema.md`](sema.md). VERDA/AKD vb.: [`entegrasyonlar.md`](entegrasyonlar.md). Config anahtarları: [`config.md`](config.md). ITCH protokolü ve SDK içi: [`../itch-sdk/README.md`](../itch-sdk/README.md).

Özet akış:

```
BIST ITCH ─► libMAItchSDK (C thread'leri) ─► itch.c callback ─► Go export (cgo_calls.go)
   ─► itchChan (tek kanal) ─► processItchData (tek goroutine) ─► TradableInstrument/OrderBook
   ─► pubsub publisher'ları ─► WSListener.transmit* goroutine'leri ─► WS istemcileri

order-service SubscribeToOrders ─┐
HFT FetchOrders ─────────────────┼─► OrderService (bellekte emir geçmişi + "benim emrim" haritası) ─► /orders, /passive-orders, /itch işaretleri
HFT/AlgoProd FetchCommands ──────┴─► /strategy
```

## 1. Açılış sırası (`cmd/dataapp/main.go` `main`)

1. Config, log dosyası (`data_<tarih>.log`, stdout'a da yazar), request log, MySQL.
2. Sekiz `pubsub.Subscriber` oluşturulur (her WS feed için bir tane; kanal kapasitesi 100 000). `itch.NewManager`; ITCH subscriber'ı ve denge fiyatı subscriber'ı manager'a verilir.
3. `itchManager.Start()`:
   - `getInstruments`: DB'deki `isActive=1` enstrümanlar belleğe (`instruments` map'i) yüklenir. Henüz tradable değildirler (emir defteri yok).
   - `itchEnabled` ise `UpdateAllInstrumentsAsInactive`, sonra iki goroutine: `processItchData` ve `receiveItch` (C fonksiyonu; SDK'yı başlatır, sonra sonsuza kadar 100 ms `usleep` döngüsünde bekler — bu goroutine process ömrü boyunca bir OS thread'i tutar).
4. `itchEnabled` ise `<-snapshotEndChan` ile **bloklanır**. Kanal yalnızca config'deki **tüm** pazarlar (`spot` → equity, diğer her şey → derivative) `SnapshotEnd` verdiğinde ve tek seferlik bootstrap (`createIndices`, `createUnderlyingRelations`, `setNearestIndexFuture`, `setInstrumentBazaars`, `insertInstruments`, `setInstrumentsWithFuture`, `createInstrumentIndices`, `go calculateIndicePrices`) bittiğinde tetiklenir (`itch.Manager.configuredSnapshotsReady`).
   - `receiveItch` hata dönerse (`itchsdk_initialize`/`itchsdk_start` başarısız) yalnızca log basılır; `main` sonsuza kadar bekler. gRPC/REST hiç açılmaz.
   - Config'teki bir pazar hiç snapshot vermezse aynı şekilde sonsuz bekleme.
   - `main.go`'daki yorum ("ilk biten pazarda serbest kalır") koddan eskidir; kod tüm pazarları bekliyor.
5. `historyManagerEnabled` ise price data + volatility + history manager. Sonra API nesneleri, AKD, BYF. BYF hatası veya fiktif enstrüman ayar hatası → `main` **return** eder (process çıkar).
6. TradeVerifier (açıksa): VERDA dosyaları bir kez çekilir, `applyBounds("startup")` DB'ye ve bellekteki `TradableInstrument`'lara `minPrice`/`maxPrice` yazar. Hata → `main` return. Ardından `reconcileChan`'i dinleyen goroutine kurulur. `NotifyOnSnapshotEnd` bildirimi yalnızca bootstrap anında bir kez gönderildiği için bu goroutine pratikte bir kez daha (`"snapshot"`) çalışır; sonraki snapshot'larda tetiklenmez. Ayrıntı: [`entegrasyonlar.md`](entegrasyonlar.md).
7. `srv.StartNonBlocking()` — gRPC, REST gateway, Admin REST.
8. `startGui := <-guiChan` ile bloklanır. `DataService.Login` başarılı olduğunda (`servicemodels/ouch_api.go` `API.Login`) kanala **non-blocking** `select` ile `true` yazılır. Kanal buffer'sız; `main` o anda beklemiyorsa bildirim düşer ("Already Loggedin" log'u). Pratikte bunu yapan order-service'tir.
9. `NewGuiExtServ` → `NewWsListener` → `SetWsSubscribers` → `guiApi/ouchApi.SetGuiExtServices` → `guiExtServices.Connect` (her dış servis için ayrı goroutine, bkz. §5) → `SetWsOrderService` → `Serve` (HTTP dinleyici + 7 transmit goroutine'i).
10. Sinyal beklenir. Kapanışta `itchManager.Stop` (`running=false`, enstrümanları DB'ye tekrar yazar) ve history manager durdurulur. WS veya dış bağlantılar için kapanış adımı yok.

Sonuç: order-service gelmeden UI WebSocket'i açılmaz; HFT/AlgoProd bağlantısı da kurulmaz. REST bu arada çalışır, ama komut uçları `guiExtServices == nil` hatası döner.

## 2. ITCH hattı (`pkg/itch`)

### 2.1 cgo köprüsü ve thread'ler

- `itch.go` `Manager.Start` config'deki her `itchConfigurations[]` elemanını `addItchConfiguration` ile C tarafındaki statik diziye ekler (en fazla 10). `Market == "spot"` → `Spot`; `"derivative"`/`"derivatives"` → `Viop`; bilinmeyen → uyarı + `Viop`.
- **Partition eşlemesi yalnızca 1–4'ü tanır.** `Part` 5 veya 6 ise `[WARNING] Unknown partition ... defaulting to Partition1` log'u basılır ve `Partition1` kullanılır (itch-sdk `enums.h` `Partition5..10`'u tanımlıyor). VİOP için 6 partition tanımlayan config'lerde 5. ve 6. partition'ın enstrümanları trade-data-app'e gelmez. Kasıtlı olduğuna dair bir işaret yok; bug adayı. README'deki VİOP partition notuyla ilişkili.
- `receiveItch` (`itch.c`): `itchsdk_initialize` → her pazar için bir kez `itchsdk_subscribe_snapshot_end` → `itchsdk_start`. Sabit ayarlar: `mainRingBufferSize = 1<<16`, `rewinderRingBufferSize = 1<<14`, CPU pin yok (`-1`), Glimpse 3 deneme / 500 ms backoff / 30 sn başlangıç timeout'u, Rewinder 5 sn timeout.
- `itchWorkerCount`, `itchTriggerWorkerCount`, `monitoring.*` C'ye geçirilir ama **kullanılmaz** (`(void)` ile susturulmuş; 4.x SDK'da worker sayısı yok).
- SDK callback'leri SDK'nın kendi thread'lerinde çalışır. Her biri bir Go export fonksiyonunu çağırır (`OnAddOrder`, `OnOrderExecute`, `OnOrderDelete`, `OnHeaderChanged`, `OnOrderBookState`, `OnEquilibriumPriceUpdate`, `OnSnapshot`, `OnSnapshotEnd`). Bunlar tek bir global kanala `itchChan` (kapasite 100 000 000 `Message`) yazar. Kanal dolarsa SDK thread'i bloklanır.
- `processItchData` tek goroutine'dir; `select` içinde `default: break` olduğu için kanal boşken **meşgul döngüde döner** (bir CPU çekirdeğini sürekli kullanır).

### 2.2 Snapshot ve enstrüman yükleme

`on_snapshot_end_cb` (`itch.c`), her emir defteri için sırayla:
1. `subscribe_to_orderbook_with_error_check`: add, executed, delete, header_changed, state_changed, equilibrium_price_update aboneliklerini açar (zaten abone ise atlar).
2. `OnSnapshot` → `OrderBookDir` mesajı. `processItchData` enstrüman yoksa `NewInstrumentFromOrderBookDirectory` ile yaratır, varsa (DB'den gelmişse) `AddOrderBookDirectory` ile alanlarını günceller. Sonra `SetActive(true)` + `createInstrument`. `createInstrument` `FinancialProduct`'a göre Equity / Future / Warrant / Option / düz `TradableInstrument` nesnesi yaratır ve ilgili map'lere koyar. **Tradable nesne ve emir defteri her snapshot'ta yeniden yaratılır.**
3. `replay_snapshot_orders`: snapshot'taki her emir `OnAddOrder` olarak yeniden oynatılır (`rankingSequence*` ve `ts` = 0). Taraf başına en fazla 1000 seviye işlenir.
4. Son olarak `OnSnapshotEnd(market)`.

Canlı abonelik snapshot replay'inden **önce** açıldığı için aynı emir defterine ait canlı olaylar replay mesajlarıyla `itchChan`'da karışabilir. ❓ doğrulanmadı: SDK'nın snapshot callback'i içindeyken o defter için canlı olay üretip üretmediği.

Zaman damgaları: `time.Unix(<şimdiki saniye>, ts)` — saniye kısmı yerel saat, nanosaniye kısmı ITCH'teki `ts`. ITCH zamanı değildir.

### 2.3 Fiyat ölçeği

- Tüm ITCH fiyatları (emir, seviye, header, denge fiyatı) **raw integer** olarak taşınır ve WS'e de raw gider.
- TL = raw / `priceDivider`. `priceDivider = 10^decimalPrice` (`instruments/instrument.go`). ITCH'ten yeni yaratılan enstrümanda `DecimalPrice`'tan; DB'den yüklenende `Instrument.decimalCount` kolonundan (bir önceki çalışmada ITCH'ten yazılmış değer).
- `AddOrderBookDirectory` `decimalPrice`'ı günceller ama `priceDivider`'ı **güncellemez**. DB'den gelen enstrümanın ondalık sayısı değişirse bellekteki bölücü eski kalır (bug adayı, nadir).
- `priceDivider` WS'e yalnızca şu mesajlarda gider: emir defteri snapshot'ı (`PriceDivider`), best bid/ask snapshot'ı, bounds mesajları (`priceDivider`). Seviye güncellemeleri, best güncellemeleri ve denge fiyatı mesajları bölücü taşımaz; UI snapshot'tan bilmelidir.
- Tavan/taban (`minPrice`/`maxPrice`): TradeVerifier VERDA'daki TL değerini **×1000** yazıyor (`tradeverifier/verda.go`, `math.Round(minPrice * 1000)`). Bu, `priceDivider`'dan bağımsız sabit bir ölçek; 3 ondalıklı pay senetlerinde raw ile örtüşür.
- `TickSize` (yalnızca snapshot seviyelerinde): `itchsdk_get_tick_size(orderbookId, price)`, raw birimde.

### 2.4 Emir defteri yapısı (`pkg/itch/orderbook`)

- `OrderBook` = `buyOrderDepth` + `sellOrderDepth` + `state`. Side `'T'` (açığa satış) satış derinliğine gider.
- `OrderDepth`: `orderMap` (ITCH order id string → `Order`), `levels` (raw fiyat → `OrderLevel`), `orderedLevelPrices` (alışta azalan, satışta artan; `[0]` = best). Yeni seviye eklendiğinde tüm dilim yeniden sıralanır.
- `OrderLevel`: `CurrentQuantity` (lot), `ExecutedQuantity`, `CancelledQuantity`, öncelik sırasına göre `orders` (`RankingSequenceTime`, sonra `RankingSequenceNumber`). Execute öndeki emirden düşer.
- Kilitler: `TradableInstrument.InstrumentMtx` (her ITCH olayında tutulur); paket seviyesinde **tek global** `depthMapMutex` (tüm enstrümanların tüm derinlikleri için ortak RWMutex); `OrderLevel.orderMutex`. `CurrentQuantity`, `lastPrice`, `header` gibi alanlar kilitsiz okunur.
- İki ayrı "header" kaynağı var: SDK'nın `header_changed` callback'i `depth.header`'ı doğrudan yazar; `OrderDepth.Header()` ise seviyelerden hesaplar. `Header().OrderBookId` ve bounds mesajlarının `orderbookId`'si `depth.header.OrderBookId`'den gelir — o defter için ilk SDK header callback'i gelene kadar 0'dır.

### 2.5 Yayıncılar (abonelik noktaları)

| Yayıncı | Nerede | Tetik | Yayınlanan tip | WS feed |
|---------|--------|-------|----------------|---------|
| `notifierMap[AddOrder/ExecuteOrder/DeleteOrder]` | `OrderDepth` | Her ITCH add/execute/delete (+ OrderService'in sahte add'i, §5.4) | `messages.AddOrder` / `OrderExecute` / `OrderDelete` (değer) | `/ws/v1/itch` |
| `headerChangePublisher` | `OrderDepth` (ilk abonelikte yaratılır) | SDK header callback'i (her callback'te alış ve satış için iki mesaj) + best seviyeye dokunan add/execute/delete | `*orderbook.Header` | `/ws/v1/best` |
| `boundsChangePublisher` | `OrderDepth` | Tavan (satış) / taban (alış) seviyesinin lotu değiştiğinde | `*orderbook.BoundsPriceLotUpdate` | `/ws/v1/bounds` |
| `equilibriumPricePublisher` | `TradableInstrument` | SDK `equilibrium_price_update` | `messages.EquilibriumPriceUpdate` | `/ws/v1/equilibrium` |
| `tradePublisher`, `priceChangePublisher` | `OrderDepth`, `Instrument` | Execute | `TradeData`, `PriceChange` | WS'e gitmez (history/pricedata/AKD kullanır) |

Bounds yayını yalnızca `SetBoundsPrices` çağrıldıktan sonra anlamlıdır; bu çağrı **yalnızca bir istemci `/ws/v1/bounds`'a abone olduğunda** `NewBoundsPriceLotUpdateFromItch` içinde, `minPrice > 0 && maxPrice > 0` ise yapılır. Snapshot yeniden geldiğinde emir defteri yeniden yaratıldığından bounds fiyatları ve header/bounds abonelikleri kaybolur. ❓ doğrulanmadı: gün içinde ikinci bir snapshot'ın (Glimpse yeniden bağlanması) gerçekte tetiklenip tetiklenmediği.

## 3. `pkg/pubsub`

- `Subscriber`: tek bir buffer'lı kanal (100 000). ID global sayaçtan, atomik değil.
- `Publisher.Publish`: mutex altında her aboneye **bloklayan** `sub.queue <- data`. Bir abonenin kanalı dolarsa yayıncı bloklanır. ITCH yayıncıları `InstrumentMtx` altında çağrıldığından, bir WS transmit goroutine'i yavaşlarsa (ör. bir istemciye yazma 10 sn bekliyorsa) **tüm ITCH işleme hattı durur** ve `itchChan` birikir.
- WS tarafında her feed için **tek bir paylaşılan subscriber** vardır; istemci başına kanal yoktur. Yönlendirme transmit goroutine'inde istemci listesinin taranmasıyla yapılır. Manager tarafındaki abonelikler hiç geri alınmaz (unsubscribe yalnızca istemcinin filtresini değiştirir).

## 4. WebSocket sunucusu (`pkg/gui/connections/ws_listener.go`, `client.go`)

### 4.1 Ortak kurallar

- `http.ListenAndServe(":" + gui.port)` — süreç içinde **TLS yok** (`GUIConfig` yalnızca `Port`, `Ip`, `Hostname` içerir). `CheckOrigin` her origin'i kabul eder. ❓ doğrulanmadı: wss sonlandırmasının reverse proxy'de yapıldığı.
- Her bağlantı için `Client` yaratılır, `clientId` = artan sayaç. Sunucu bağlanır bağlanmaz `{"client_id": <uint32>}` yollar.
- Wire: istemci → `{"Type": <RequestType>, "Body": {...}}`. Go `encoding/json` alan adlarında büyük/küçük harf duyarsızdır. Sunucu → Go `encoding/json`: `json` tag'i olmayan alanlar Go adlarıyla (PascalCase) gider; 64-bit sayılar number; `time.Time` RFC3339 string; `comvars.Side` **sayıdır** (`66`='B', `83`='S', `84`='T'); `map[int64]` anahtarları string olur.
- **Kimlik doğrulama:** ilk istek `{"Type":1,"Body":{"Token":"<JWT>"}}` olmalı. Token REST login'inden gelen JWT'dir; `util.Helper.Authorize` ile doğrulanır. Başarı: `{"Type":2,"Body":"Login successful"}`. Hata: `{"Type":1,"Body":{"Message":"Unauthorized"}}`. Doğrulanmadan gelen her istek aynı hatayı alır ve işlenmez. İkinci authenticate → `"Already authenticated"`. Bağlantı kapatılmaz.
- Bir feed'in yolunda başka feed'in isteği → `"Wrong address for ..."` hatası. Bilinmeyen tip → `"Unknown request type"`.
- İstekler okuma goroutine'inde **senkron** işlenir; snapshot yazılırken o istemciden başka istek okunmaz.

`RequestType`: 1 Authenticate, 2 SubscribeOrderbook, 3 SubscribeOuch, 4 SubscribeStrategyCommands, 5 SubscribeTopBidAsk, 6 SubscribeEquilibriumPrice, 7 SubscribeBoundsLot, 8 SubscribePassiveOrders, 9 UnsubscribeOrderbook, 10 UnsubscribeOrders, 11 UnsubscribeStrategyCommands, 12 UnsubscribeTopBidAsk, 13 UnsubscribeEquilibriumPrice, 14 UnsubscribeBoundsLot, 15 UnsubscribePassiveOrders.

`ResponseType`: 1 Error, 2 Authenticate, 3 AddOrder, 4 OrderExecute, 5 OrderDelete, 6 OrderReplace, 7 OrderReject, 8 OrderbookSnapshot, 9 OrderbookState (kullanılmıyor), 10 BulkOrderEnter, 11 BulkOrderDelete, 12 EquilibriumPriceUpdate, 13 BoundsPriceLotUpdate, 14 PassiveOrdersSnapshot.

### 4.2 `/ws/v1/itch/start` — emir defteri derinliği

Subscribe (2) / unsubscribe (9) gövdesi: `{"Account", "OrderBookId": uint32, "StrategyIdentifier", "StrategyType": uint8}`.

- Sunucu iki anahtar üretir: `orderBookKeys[0] = "<Account>_<OrderBookId>_<StrategyIdentifier>_<StrategyType>"` (strateji emirleri), `[1]` = aynısı `StrategyType=1` (User, manuel emirler). Bu, HFT'nin strateji `unique_key`'i ile **aynı değildir** (HFT: `<orderbookId>_<hesap>_...`, bkz. [sözlük](../../00-genel/sozluk.md)); trade-data-app'in emir takibi için kullandığı iç anahtardır (`messages.NewUniqueKeyFromOuch`).
- Snapshot, enstrümanın `InstrumentMtx`'i tutularak hesaplanır **ve istemciye yazılır** (yazma bitene kadar o enstrümanın ITCH olayları ve dolayısıyla tüm `processItchData` bekler). Enstrüman bulunamazsa hiçbir şey dönmez (sessiz).
- Snapshot mesajı `OrderBookSnapshot`: `{"Type":8, "OrderBook":{"OrderBookId", "OrderBookKey" (= anahtar[0]), "State" (0 Other, 1 AcilisEmirToplama, 2 SurekliMuzayede, 3 ViopSurekliMuzayede, 4 Eslestirme, 5 KapanisEmirToplama), "BuyOrderDepth"/"SellOrderDepth": {"Side", "Levels": {"<raw fiyat>": OrderLevelMessage}}, "PriceDivider"}}`.
- `OrderLevelMessage` alanları: `Orders` (o seviyedeki tüm ITCH emirleri: `Type`, `Timestamp`, `OrderBookID`, `OrderID` (string), `Side`, `RankingSequenceTime`, `RankingSequenceNumber`, `Quantity` (lot), `Price` (raw), `QuoteIndication`, `LotType`), `OrderBookId`, `CurrentQuantity` (lot), `Level` (raw fiyat), `Side`, `Index` (0 = best), `OrderBookKey`, `HasUserOrder`, `UserOrderQuantity` (lot), `HasStrategyOrder`, `StrategyOrderQuantity` (lot), `TickSize` (raw), `PreviousUserOrderCount`, `PreviousStrategyOrderCount`. Snapshot'ta seviye içindeki `OrderBookId`/`OrderBookKey` doldurulmaz.
  - `Previous*OrderCount` adına rağmen **lot**'tur: seviyedeki ITCH kuyruğunda benim ilk emrimden önceki emirlerin toplam miktarı. Eşleşme OUCH `OrderId` = ITCH `OrderID` varsayımıyla yapılır (`getPreviousOrdersCount`).
  - ITCH'te olmayan ama bende emri olan fiyatlar da sentetik seviye olarak eklenir (ITCH derinliği tamamen boşsa veya güncellemede seviye yoksa).
- Güncellemeler: her ITCH add/execute/delete için o fiyat seviyesinin **güncel** durumu tek bir `OrderLevelMessage` olarak gider (`Type` alanı yok, `Orders` boş, `TickSize` 0). Seviye silinmişse `CurrentQuantity: 0, Index: -1`. Yalnızca etkilenen seviye gönderilir; başka seviyelerin `Index`'i kaysa da onlar için mesaj gitmez. Durum, mesaj üretildiği anda (olay anında değil) okunur.
- Aynı istemci birden fazla defter/anahtar tutabilir (`subbedOrderBookIDs` `sync.Map`). Aynı defter iki farklı anahtarla tutulursa her olay iki kez gider.
- Unsubscribe yalnızca anahtarı siler; sunucudan yanıt dönmez.

### 4.3 `/ws/v1/orders/start` — emir olayları

Subscribe (3) / unsubscribe (10): `{"AccountName": [string], "Types": [StrategyType]}`.

- Subscribe istemcinin filtresini **değiştirir** (ekleme yapmaz), `OrderService`'e WS subscriber'ını bağlar, arka planda `SubscribeToStrategyOrders`'ı başlatır (HFT'nin `FetchOrders` akışını WS'e bağlar; §5.2) ve bellekteki geçmişten filtreye uyanları (REPLACED olayları hariç) **tek tek** ayrı mesajlar olarak yollar. Her subscribe tüm geçmişi yeniden yollar.
- Unsubscribe verilen hesap ve tipleri filtreden çıkarır.
- Canlı: order-service ve HFT olayları; `Account ∈ AccountName` **ve** `StrategyType ∈ Types` ise gönderilir. `/passive-orders`'a abone olan istemciye bu feed'in canlı mesajları gitmez.
- Mesajlar (`gui/messages/base_order.go`): ortak alanlar `MyOrderCommon` — `Type`, `Timestamp` (ns'den), `OrderBookID`, `OrderToken`, `Passthrough` (CustomData), `Side`, `Protocol` (1 OUCH, 2 FIX), `OrderId`, `Account`, `IsActive`, `RegularOrderType`, `TimeInForce`, `OrderType` (1 MORNING, 2 OPENING, 3 STRATEGY, 4 EVENING, 5 REGULAR), `Price`, `Quantity`, `StrategyIdentifier`, `ApplicationType`, `StrategyType`, `IsMainOrder`, `MainOrderId`, `LevelCount`, `IsYip`, `latencyWritingNs`/`latencyNetworkNs`/`latencyBistNs` (ns, boşsa yok), `internalOuch` (boşsa yok).
  - `Type 3` `MyOrderAdd`: + `PreTradeQty`, `Position`, `Price`, `LotType`.
  - `Type 4` `MyOrderExecute`: `Quantity` = `ExcQty`; + `ExcQty`, `InitQty`, `RemainingQty`, `Price`.
  - `Type 5` `MyOrderCancel`: `Quantity` = iptal anında bellekte kalan miktar (`GetCanceledOrderQuantity`); + `Price`, `Reason`, `ReasonCode`.
  - `Type 6` `MyOrderReplace`: + `PrevToken`, `Quantity`, `Price`, `PreTradeQty`.
  - `Type 7` `MyOrderReject`: + `Reason`, `ReasonCode`.
  - `Type 10/11/0` `MyOrderCommon` (order-service'in toplu emir `Common` olayı; ACCEPTED → 10, CANCELED → 11).
  - Alt tipteki `Price`/`Quantity` gölgelediği için JSON'da tek `Price`/`Quantity` görünür. Fiyat raw integer.
  - `Side`: HFT stratejilerinden gelen emirlerde proto enum (1/2/3) olarak gelebilir; `OrderService.normalizeSide` iki biçimi de kabul ediyor. order-service iki biçim yollar: strateji olaylarında iç enum doğrudan (66/83/84 = 'B'/'S'/'T'), toplu emir `OrdersCommon` mesajlarında 1/2/3 (`OrderServiceImpl::getOrderResponseItem`; [order-service/arayuzler](../order-service/arayuzler.md)).

### 4.4 `/ws/v1/strategy/start` — strateji komut/durum

Subscribe (4): `{"StrategyType": uint8, "Commands": [{"CommandType": uint8, "UniqueKey": string}]}`. `CommandType`: 1 Strategy, 2 Package, 3 Balance, 4 Order, 5 Summary, 6 ExecuteUnderlying (sunucu sabitleri 0–6). Yeni GUI ayrıca `8` (tavan/taban durumu) gönderir; değer uint8 olarak motora aynen geçer ([mtrader-trade-ui/backend-sozlesmesi § 4.2](../mtrader-trade-ui/backend-sozlesmesi.md#42-feed-tablosu)). Unsubscribe (11): `{"StrategyType", "UnsubscribeAll": bool, "Commands": [...]}`.

- Anahtarlar istemcinin `subbedKeys` listesine eklenir; ardından `getApplicationFromStrategyType` (WS kopyası, §5.5) ile motor seçilir. Motor tanımlı değil/bağlı değilse `"... service is not available/connected"` hatası döner — **anahtarlar yine de eklenmiş kalır**. Bilinmeyen tip için hiçbir şey yapılmaz, hata da dönmez.
- Motora `SubscribeToCommands` (unary) çağrısı ayrı goroutine'de yapılır. Metadata: `authorization`, `strategytype`; `SummaryRequest` varsa `userid` (JWT'den gelen kullanıcı). Hata yalnızca log'a yazılır, istemciye dönmez.
- Yanıtlar motorun **tek, adanmış** `FetchCommands` stream'inden (`ConnectionId: 0`) gelir ve `UniqueKey` istemcinin listesinde ise gönderilir. Mesaj `FetchCommandResponseJSON`: `{"message_type": "<CommandTypeResponse adı, örn. Command_Type_StrategyResponse>", "unique_key": string, "fields": {"<alan>": <değer>}}`. `fields` her `Any` alanın **protojson** çıktısıdır (`@type` silinir, `{"value": x}` → `x`, `"values"` içeriği yukarı alınır). Yani `fields` içinde 64-bit sayılar **string**, enum'lar isimdir — WS'in geri kalanından farklı. Çözülemeyen alan atlanır (`STRATEGY_TRACE: FIELD_SKIPPED`).
- `unique_key` biçimi istemciden geldiği gibi kullanılır; sunucu ayrıştırmaz.
- Unsubscribe: motora `UnsubscribeFromCommands{ConnectionId: clientId, UniqueKeys, UnsubscribeAll}`. **Bug:** yerel filtre `Contains(commands, key)` ile `[]*CommandsRequest` içinde `string` aradığı için hiç eşleşmez; seçici unsubscribe istemcinin `subbedKeys`'inden bir şey silmez, istemci o anahtarların mesajlarını almaya devam eder. Yalnızca `Commands == null && UnsubscribeAll == true` listeyi temizler.

### 4.5 `/ws/v1/best/start` — best bid/ask

Subscribe (5): `{"OrderBookIDs": [uint32]}`. Unsubscribe (12): `{"UnsubscribeAll": bool, "OrderBookIDs": [...]}`.

- Snapshot: tek mesaj, `{"<obId>": {"BestBid": Header, "BestAsk": Header, "PriceDivider"}}`. Bilinmeyen id → sıfır değerli nesne. `Header` = `{"OrderBookId", "Side", "Price" (raw), "Quantity" (lot), "Symbol" (genelde boş)}`, seviyelerden hesaplanır.
- Güncelleme: çıplak `Header` nesnesi (`Type` ve `PriceDivider` yok). §2.5'teki iki kaynaktan gelir; aynı değişiklik birden fazla kez gelebilir.

### 4.6 `/ws/v1/equilibrium/start` — denge fiyatı

Subscribe (6) / unsubscribe (13): `{"OrderBookIDs": [uint32]}` (+ `"UnsubscribeAll"`). **Snapshot yok, onay mesajı yok.** Güncelleme (`json` tag'li): `{"type":12, "orderbookId", "availableBidQuantity", "availableAskQuantity" (lot), "equilibriumPrice", "bestBidPrice", "bestAskPrice" (raw int32), "bestBidQuantity", "bestAskQuantity" (lot), "timestamp"}`.

Anahtar `"equilibrium_<obId>"` olarak `/itch` ile aynı `subbedOrderBookIDs` yapısında tutulur. `transmitItchMessages` anahtar önekine bakmadığı için, aynı defter başka bir istemcide `/itch` ile de açıksa equilibrium istemcisine `OrderLevelMessage`'lar da gider (bug adayı, koddan çıkarım).

### 4.7 `/ws/v1/bounds/start` — tavan/taban lotu

Subscribe (7): `{"OrderBookIDs": [uint32]}`. Unsubscribe (14): `{"UnsubscribeAll", "OrderBookIDs"}`.

- Snapshot: `{"<obId>": BoundsPriceLotUpdate}`; güncelleme: çıplak `BoundsPriceLotUpdate`. Alanlar: `{"type":13, "orderbookId", "maxAskPrice" (tavan, raw, ×1000 ölçeği §2.3), "maxAskLot" (satış tarafında tavan fiyattaki toplam lot), "minBidPrice" (taban, raw), "minBidLot" (alış tarafında taban fiyattaki toplam lot), "priceDivider", "timestamp"}`.
- Tavan/taban 0 ise (TradeVerifier kapalı/eşleşmedi) seviyeler bulunamaz; lotlar 0 gelir ve güncelleme hiç tetiklenmez. Bilinmeyen id → yalnızca `{"type":13}`.

### 4.8 `/ws/v1/passive-orders/start` — pasif emirler

Subscribe (8) / unsubscribe (15): `{"AccountName": [string], "Types": [StrategyType]}`.

- İstemci `subbedToPassiveOrders=true` olur; `/orders` canlı mesajlarını almaz. `SubscribeToStrategyOrders` başlatılır.
- Mesaj her zaman tam snapshot: `{"Type":14, "Orders": [MyOrderAdd]}` — bellekte miktarı > 0 olan aktif emirler; REPLACED olanlar güncel fiyat/miktarla Accepted biçimine çevrilir. Boşsa `Orders: []`.
- Her canlı emir olayında (`checkUserOrder`, geçmiş sonrası) `passiveOrderUpdateChan` tetiklenir ve **tüm** pasif istemcilere ayrı goroutine'lerde tam snapshot yeniden yollanır.

### 4.9 Yazma ve kopma

- `Client.sendMessage`: `writeMutex` altında 10 sn write deadline + `WriteJSON`. Hata → `running=false`, sonraki tüm gönderimler sessizce reddedilir. Bağlantı kapatılmaz, istemci listeden çıkmaz.
- İstemci yalnızca okuma hatasıyla (`ReadJSON`) temizlenir: `safeClose` + `removeClient`. Ping/pong ve okuma deadline'ı yok; yarı açık TCP bağlantısı tespit edilmez ve istemci listede kalır (her mesajda tekrar tekrar elenir).
- Yavaş istemci: yazma 10 sn'ye kadar bekleyebilir; bu sürede ilgili transmit goroutine'i (ve §3 nedeniyle ITCH hattı) bekler.
- `removeClient` `TryLock` ile meşgul döngüde istemci map kilidini bekler. Sonra `unsubscribeFromCommands(…, Unknown, nil, true)` çağırır: önce AlgoProd'a, sonra HFT'ye `UnsubscribeAll`. **AlgoProd config'de yoksa veya bağlı değilse fonksiyon erken döner ve HFT'ye unsubscribe hiç gitmez** (bug adayı).

## 5. Dış bağlantılar (`gui/connections`)

### 5.1 Bağlanma, yeniden bağlanma, bağlantı yokken

- `GuiExtServ.Connect`: `extServices[]` her eleman için goroutine. `application` değeri `hft`, `algotrading`, `orderserv` dışında ise `NewExternalService` `nil` döner; goroutine'deki `srv.Connect()` nil interface üzerinde çağrıldığından panic verir ve process çöker (koddan çıkarım).
- `Connect()` (üç servis için aynı kalıp): `token=""` → `grpc.Dial(WithBlock, insecure, maxint mesaj boyu)` başarılı olana kadar 2 sn arayla **sonsuz** dener → login (`StrategyLogin` / order-service `Login`, `Application_OUCH`) → `token` set → `monitorConnection` + stream goroutine'leri.
- Login hatası → `Connect` hata döner → ilk bağlantıda goroutine biter; yeniden bağlanmada "Quit trying to reconnect" ile **kalıcı olarak vazgeçilir**. Process yeniden başlatılana kadar o servis bağlantısız kalır.
- Kopma tespiti: `monitorConnection` gRPC Health `Watch` stream'i; `Recv` hatası → `isDisconnectedChan <- true` → yeniden `Connect`. `Watch` çağrısı hata dönerse yalnızca log basılır ve o bağlantı için izleme yapılmaz. order-service health servisini sunar (`""` SERVING, `OrderServer::StartServiceWithGRPC`). AlgoProd varsayılan health servisini sunar (`""` SERVING, [grpc-ve-veri § 1](../algorithmic-trading/grpc-ve-veri.md#1-sunucu-ve-kimlik-doğrulama)). ❓ doğrulanmadı: HFT'nin sunduğu; sunmuyorsa ilk `Recv` hatası kopma sayılır ve sürekli yeniden bağlanma döngüsü beklenir.
- `IsConnected()` = `len(token) > 0`. Token yalnızca yeniden `Connect` başlarken silinir; kopma ile health tespiti arasındaki sürede `true` kalır.
- **Bağlantı yokken komutlar:** kuyruk yok (`commandsQueue` alanı tanımlı, kullanılmıyor). REST `SetStrategyCommands` `IsConnected` false ise `"HFT service is not connected"` hatasıyla döner; true ama bağlantı ölü ise gRPC hatası döner. Komut kaybolur, yeniden denenmez. WS strategy subscribe'ı aynı şekilde hata mesajı döner; yeniden bağlantıda abonelikler motora **otomatik yenilenmez** — istemci yeniden subscribe etmelidir. ❓ doğrulanmadı: motorların abonelik durumunu kopma sonrası koruyup korumadığı.

### 5.2 HFT (`hft.go`)

- Login sonrası `NotifyConnection` (1 buffer'lı `connectedChan`'e `true`) + `getOrdersFromService` + `getCommandsFromService`.
- `FetchOrders{OrderTypes:[STRATEGY]}` stream'i: ilk mesaj = günün geçmişi, sonrakiler canlı. Her mesaja `IsOrderHistoryReceived` (ilk mesajda false) işlenir.
  - WS'te henüz `/orders` veya `/passive-orders` abonesi yoksa mesajlar **sınırsız** `orderBuffer`'da birikir; ilk abone geldiğinde 10 ms arayla yayınlanır.
  - Yeniden bağlanmada (`alreadyConnected`) ilk mesaj (geçmiş) atlanır; arada kaçan olaylar telafi edilmez.
  - Akış bitince sessizce döner; yeniden açılması `Connect`'e bağlıdır.
- `SubscribeToStrategyOrders` (`ws_listener.go`): yalnızca HFT için (AlgoProd yok). HFT bağlı değilse `connectedChan`'den sinyal bekler; her `/orders`/`/passive-orders` subscribe'ı yeni bir bekleyen goroutine açar, tek sinyali yalnızca biri alır (goroutine sızıntısı adayı).
- HFT emirleri `transmitOuchMessages`'da `convertStrategyOrderToOrder` ile order-service biçimine çevrilir; `convertStrategyGuiType` yalnızca MaxPrice, HFT, TheoreticalPrice, Arbitrage, HftWarrant, MinPrice, HftWarrantAdvanced'i tanır, diğerleri `Unknown` (0) olur ve `/orders` tip filtresine takılır. Ardından `OrderService.checkUserOrders` ile belleğe yazılır. Uygulama ömründe **ilk** geçmiş mesajı WS'e yayınlanmaz (`isFirstOrderSubscriber`), sadece belleğe alınır.
- `FetchCommands{ConnectionId:0}`: boş `Fields`'lı mesajlar atlanır, diğerleri `commandPublisher` → `/strategy`. Stream hatasında 1 sn bekler; o anda `IsConnected` false ise 30 dk'ya kadar saniyede bir kontrol edip kendini yeniden çağırır. Aynı anda `Connect` de yeni bir `getCommandsFromService` başlattığından bu durumda **iki stream** açılabilir ve her yanıt iki kez yayınlanır (yarış, koddan çıkarım). `IsConnected` hâlâ true ise fonksiyon biter; yeni stream'i `Connect` açar.
- Diğer RPC'ler (`SetCommandRequest`, `SubscribeToOrderbook`, `AlgoSetAccountStrategy`) REST yolundan çağrılır: [`api.md`](api.md).

### 5.3 AlgoProd (`algotrading.go`)

HFT ile aynı bağlanma/`FetchCommands` kalıbı; `FetchOrders` **açılmaz** (AlgoProd emirleri order-service akışından gelir). Ek RPC'ler: `FetchAllUniqueKeys`, `SubscribeToFuture(s)`, `SubscribeToAllFutures` (`unique_key` burada `<hesap>_<strategyIdentifier>`), `UpdateExtSettings`. `SetAccountStrategy` motor `Success=false` dönse de `true` döner (bug adayı).

### 5.4 order-service (`orderservice.go`) ve bellekteki emir durumu

- Login sonrası `StartWorker`: `SubscribeToOrders{RequesterKey: <kullanıcı>, ApplicationUsernames: <DB Application_Users>, OrderTypes:[MORNING, OPENING, STRATEGY, EVENING]}`. Ardından bellek **sıfırlanır** (`orders`, `canceledOrderQty`, `userOrdersMap`, `orderIdToPriceMap`, `orderIdToSideMap`) ve stream okunur. İlk mesaj = geçmiş.
- Her mesaj: önce `orderPublisher.Publish` (→ `/orders`), **sonra** `checkUserOrders`. Bu sıra yüzünden `/orders`'taki Cancel mesajının `Quantity`'si, `canceledOrderQty` henüz yazılmadan okunup 0 gelebilir (yarış, koddan çıkarım). HFT yolunda sıra terstir (önce `checkUserOrders`).
- `checkUserOrders` (iki goroutine'den çağrılır: order-service okuyucusu ve `transmitOuchMessages`):
  - Her olayı `orders` dilimine ekler — process ömrü boyunca büyür; yalnızca order-service yeniden bağlanınca sıfırlanır. **Sıfırlama HFT'den gelmiş emirleri de siler** ve HFT geçmişi yeniden istenmez; order-service kopup gelirse HFT strateji emirleri `/orders` geçmişinden ve emir defteri işaretlerinden kaybolur (bug adayı).
  - Olayları zaman damgasına göre sıralar (order-service geçmişi tipe göre gruplu gönderiyor) ve `userOrdersMap[orderBookKey][rawPrice][orderId] = kalanLot` haritasını günceller: Accepted ekler, Executed düşer, Canceled siler (kalanı `canceledOrderQty`'ye yazar), Replaced fiyat taşır.
  - Geçmiş sonrası her olayda: `generateItchTrigger` ilgili derinlikte o fiyat (ve replace'te eski fiyat) için **sahte bir AddOrder** yayınlar → `/itch` istemcileri "benim emrim" işaretli seviye güncellemesi alır. Ardından `passiveOrderUpdateChan <- true` (buffer'sız; `userOrdersMtx` tutulurken bloklar, `transmitPassiveOrdersMessages` alana kadar).
- `orderBookKey` = `<Account>_<OrderBookId>_<StrategyIdentifier>_<StrategyType>` (`NewUniqueKeyFromOuch`). `/itch` işaretleri, pasif emirler ve "önümdeki lot" hesapları bu anahtarla yapılır; UI'ın `/itch` subscribe'ında yolladığı `Account`/`StrategyIdentifier`/`StrategyType` emirdekiyle birebir aynı olmalıdır.
- `SetOrders` (Go sarmalayıcı) → `SendOrder` RPC; bağlantı yoksa `"connection is not established"`. Kuyruk yok.

### 5.5 `getApplicationFromStrategyType` — iki kopya

| StrategyType | REST: `servicemodels/gui_api.go` `API.getApplicationFromStrategyType` | WS: `connections/ws_listener.go` `getApplicationFromStrategyType` |
|---|---|---|
| 1 (User / Algo_User) | AlgoTrading | **HFT** |
| 2 Warrant, 3 AKD, 5 MovingAverage, 6 Arbitrage, 7 VWAP, 10 FundTracker | AlgoTrading | AlgoTrading |
| 4 HFT, 8 TheoreticalPrice, 9 MaxPrice, 11 OrderChase, 13 HftWarrant, 14 MinPrice, 15 HftWarrantAdvanced | HFT | HFT |
| 12 HFT_User | HFT | **yok → Unknown** (subscribe sessizce hiçbir şey yapmaz) |

Kullanım: REST kopyası komut/emir yönlendirme ve uygulama kullanıcısı seçimi; WS kopyası `/strategy` subscribe/unsubscribe. Yeni tip eklerken ikisi birden güncellenmeli.

## 6. Goroutine ve kilit modeli

| Goroutine | Sayı | Okur | Yazar / kilit |
|-----------|------|------|---------------|
| SDK thread'leri (C) | SDK'ya bağlı | multicast/Glimpse | `itchChan` |
| `receiveItch` | 1 | — | sonsuz `usleep` |
| `processItchData` | 1 | `itchChan` | `InstrumentMtx`, `depthMapMutex`, pubsub publish |
| `calculateIndicePrices` | 1 | endeksler (200 ms) | kilitsiz map okuma |
| `transmitItch/Ouch/Algo/BestBidAsk/EquilibriumPriceUpdate/BoundsLotUpdates/PassiveOrdersMessages` | 7 | ilgili subscriber | `guiClientsByClientIdMtx` (R), `Client.writeMutex` |
| WS bağlantı başına | 1 | `ReadJSON` | istek işleyicileri (snapshot'ta `InstrumentMtx`) |
| Pasif snapshot | olay × istemci | `ordersMtx`, `userOrdersMtx` (R) | `writeMutex` |
| Servis başına: reconnect döngüsü, `monitorConnection`, `FetchCommands`, (HFT) `FetchOrders`, (order-service) `SubscribeToOrders` | ~3–4 | gRPC stream | `commandMtx`, `ordersMtx`, `userOrdersMtx` |

Kilitsiz paylaşılan durum (data race adayları): `Client.running`, `subbedAccounts`, `subbedStrTypes`, `subbedBestBidAsks`, `subbedMaxAskLots`, `subbedToPassiveOrders` (okuma goroutine'i yazar, transmit goroutine'leri okur); `Manager.running`; `HftService.token`/`client`/`orderHistoryReceived`; `OrderDepth.header` (pointer olarak yayınlanır, ITCH goroutine'i yazmaya devam ederken JSON'a çevrilir); `SubscribeToAll`/`UnsubscribeFromAll` ve `processItchData`'daki `snapshotEquityReady` vb. map/alan erişimleri.

## 7. Bilinen riskler ve şüpheli davranışlar (koddan)

Hepsi 1cca9a8 itibarıyla koddan okunmuştur; prod'da gözlenip gözlenmediği doğrulanmadı.

1. **VİOP partition 5–6 → Partition1** (§2.1). 6 partition'lı config'lerde son iki partition'ın enstrümanları gelmez.
2. **Tek yavaş WS istemcisi ITCH hattını durdurabilir**: bloklayan `Publish` + `InstrumentMtx` altında yayın + 10 sn write deadline; `/itch` snapshot'ı da `InstrumentMtx` tutarak yazılır (§3, §4.2).
3. **`processItchData` meşgul döngü** — bir çekirdek sürekli %100 (§2.1).
4. Açılışta ITCH SDK başlatılamazsa veya bir pazar snapshot vermezse süreç sessizce takılı kalır (§1).
5. `guiChan` bildirimi `main` beklemiyorsa düşer → WS ve dış bağlantılar hiç açılmaz (§1 madde 8).
6. Ölü WS istemcileri temizlenmez; ping/pong yok (§4.9).
7. `/strategy` seçici unsubscribe yerel filtreyi temizlemiyor (§4.4).
8. İstemci koptuğunda AlgoProd yoksa HFT'ye `UnsubscribeFromCommands` gitmiyor (§4.9).
9. order-service yeniden bağlanınca HFT strateji emirleri bellekten siliniyor (§5.4).
10. order-service Cancel olayında `Quantity` 0 gelebilir (publish/check sırası, §5.4).
11. Equilibrium istemcilerine `/itch` seviye mesajı sızabilir (§4.6).
12. HFT/AlgoProd yeniden bağlanmasında çift `FetchCommands` stream'i → çift yanıt olasılığı (§5.2).
13. Login hatasında yeniden bağlanma kalıcı olarak durur (§5.1).
14. WS `getApplicationFromStrategyType`'ta 12 (HFT_User) yok; 1 iki kopyada farklı motora gidiyor (§5.5).
15. `DataService.Login` gelen şifreyi düz metin olarak log'a yazıyor (`ouch_api.go` `API.Login`) — güvenlik riski.
