---
kapsam: MARpc wire protokolü — TCP çerçevesi, orders.fbs / orders_response.fbs tabloları ve alanları (tip, birim), enum'lar, istek ↔ yanıt eşlemesi, C struct dönüşümü ve pointer ömrü, versiyonlama
kaynak:
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
dogrulama: 2026-10-22
durum: taslak
---

# MARpc wire protokolü

İndeks: [README.md](README.md). Bağlantı, thread ve heartbeat zamanlaması: [baglanti-ve-threadler.md](baglanti-ve-threadler.md). Alanların order-service'teki anlamı (hangi alan doldurulur, ret kodları, yönlendirme): [order-service/arayuzler § 3](../order-service/arayuzler.md#3-marpc-sunucusu-orderserver). Bu dosya wire biçimini ve SDK dönüşümünü anlatır.

## 1. Çerçeve

```
+-------------------------+---------------------------------------+
| LEN: uint32, big-endian | PAYLOAD: LEN bayt FlatBuffers         |
| (payload uzunluğu)      | kök: RequestHolder / ResponseHolder   |
+-------------------------+---------------------------------------+
```

- `LEN` = `htonl(payloadSize)` (`MAHelper::copyPacketLength` → `copyInt`). Okuma `MAHelper::parseToInt`: `memcpy` + `ntohl`. Uzunluk **yalnız payload'u** sayar, kendi 4 baytını saymaz. Çerçevenin toplam boyu `LEN + 4` bayttır.
- Payload FlatBuffers ikili biçimindedir, içi **little-endian**. Aynı çerçevede iki farklı bayt düzeni bulunur.
- Yön: istemci → sunucu kökü `meeapps.orders.fb.RequestHolder`, sunucu → istemci kökü `meeapps.orders.rp.ResponseHolder`. Kök tipi çerçevede yazmaz; yöne göre bilinir.
- **Yok:** sürüm alanı, `file_identifier`, sıra numarası, checksum, azami boyut. FlatBuffers `Verifier` hiç çağrılmaz (`GetRequestHolder` / `GetResponseHolder` doğrudan). Bozuk veya kötü niyetli payload tanımsız davranıştır. Büyük `LEN` gelirse alıcı o kadar baytı bekleyerek sınırsız tampon biriktirir.
- `LENGTH_SHORT = 2` yalnız kullanılmayan `MAHelper::copyShort`'ta geçer.
- Gönderim: her çerçeve için `new char[4 + len]` ayrılır, `send(..., MSG_NOSIGNAL)` tamamı gidene kadar döngüde çağrılır; `EAGAIN` gelirse aynı yerde döner (`MATCPClient::sendMessage(int,…)`, `MATCPServer::sendMessage`).
- Alım ve ayrıştırma: `recv` 4096 baytlık parçalar okur (`RECV_BUF_SIZE`). Parçalar kuyruğa konur. Ayrı bir thread önceki artığı (`remainingBuf`) ve yeni parçayı birleştirip içinden tam çerçeveleri çıkarır: `MATCPClient::processCallback` ve `MATCPServer::processCallback`. İki kopya aynı mantıktadır; tek fark, sunucu kopyasında `CLOSE_MSG` kontrolü olması. Her çerçeve `substr` ile ayrı bir `std::string` (`fbData`) olur.

## 2. Özel çerçeveler

### 2.1 `CLOSE_MSG`

- İstemci `closeClientConnection()` → `MATCPClient::closeConnection`: payload'u tek bayt `'C'` olan çerçeveyi gönderim kuyruğuna koyar (`00 00 00 01 43`).
- Sunucu (`MATCPServer::processCallback`): `packageLength == 1` ise `networkData.substr(LENGTH_INT, 1) == "C"` kontrolü yapar. Eşleşirse `isRunning[conn] = false` olur ve ayrıştırma döngüsü kırılır. Kapanış akışı: [bağlantı § 7](baglanti-ve-threadler.md#7-kapanış).
- Geçerli bir FlatBuffers kökü en az 4 bayt olduğundan 1 baytlık payload başka bir mesajla çakışmaz. Bu kasıtlıdır ama şemaya bağlı değildir; uygulama ayrıntısıdır.
- Kontrol **sabit offset** (`LENGTH_INT`) ile yapılır, çerçevenin `totalReadBytes` konumuyla yapılmaz. Bu yüzden `'C'` yalnız alınan tamponun ilk çerçevesiyse tanınır. Değilse 1 baytlık veri `GetRequestHolder`'a verilir (§ Şüpheli 2).
- İstemci tarafında `CLOSE_MSG` kontrolü yoktur. Sunucu bu çerçeveyi göndermez.

### 2.2 Heartbeat

- `RequestHolder{request_type = HearthbeatRequest, request = HearthbeatRequest{hearthbeat_count: 1}}`. `authToken` alanı **yoktur** (vektör yazılmaz).
- Çerçeve bir kez üretilip önbelleğe alınır: `MAHelper::getHeartbeatRequest`. İlk çağrı `MATCPClient` constructor'ındadır, sonraki her heartbeat aynı `hbReq` baytlarıdır. `hearthbeat_count` her zaman 1'dir; global `heartBeatCount` artırılmaz, struct'a yazılan değer kullanılmaz.
- Sunucu heartbeat'i host callback'ine vermez, yalnız `heartbeatMap[conn]` zamanını günceller. Zamanlama: [bağlantı § 3](baglanti-ve-threadler.md#3-login-ve-heartbeat).

## 3. Şemalar

Namespace: istek `meeapps.orders.fb` (`orders.fbs`), yanıt `meeapps.orders.rp` (`orders_response.fbs`, `include "orders.fbs"`; enum'ları ve `AccountStrategy` tablosunu `fb`'den kullanır).

FlatBuffers tipleri: `int` = int32, `uint` = uint32, `long`/`ulong` = int64/uint64, `byte` = int8, `[byte]` = int8 vektörü, `string` = UTF-8 + `\0`. C tarafı LP64 Linux: `unsigned long` = 64 bit.

### 3.1 Union'lar ve tip numaraları

Wire'daki tip, union'ın **sıra indeksidir** (`NONE = 0`, ilk üye 1). C enum'ları (`RequestTypes`, `ResponseTypes`, `Public/MAOrderEnums.h`) farklı numaralanır ve wire'a çıkmaz. Eşlemeyi `MAHelper` yapar.

| `BaseRequest` indeksi | Tablo | C `RequestTypes` |
|-----|-------|------------------|
| 1 | `LoginRequest` | `TYPE_LoginRequest` = 4 |
| 2 | `EnterOrder` | `TYPE_EnterOrderRequest` = 1 |
| 3 | `CancelOrder` | `TYPE_CancelOrderRequest` = 3 |
| 4 | `ReplaceOrder` | `TYPE_ReplaceOrderRequest` = 2 |
| 5 | `AllOrdersRequest` | `TYPE_AllOrdersRequest` = 5 |
| 6 | `AccountStrategyRequest` | `TYPE_AccountStrategyRequest` = 6 |
| 7 | `HearthbeatRequest` | `TYPE_HeartbeatRequest` = 7 |

| `BaseResponse` indeksi | Tablo | C `ResponseTypes` |
|-----|-------|-------------------|
| 1 | `LoginResponse` | `TYPE_LoginResponse` = 6 |
| 2 | `OrderAccepted` | `TYPE_OrderAccepted` = 1 |
| 3 | `OrderReplaced` | `TYPE_OrderReplaced` = 5 |
| 4 | `OrderCanceled` | `TYPE_OrderCanceled` = 3 |
| 5 | `OrderExecuted` | `TYPE_OrderExecuted` = 2 |
| 6 | `OrderRejected` | `TYPE_OrderRejected` = 4 |
| 7 | `AccountStrategiesResponse` | `TYPE_AccountStrategyResponse` = 7 |
| 8 | `AllOrdersResponse` | `TYPE_AllOrdersResponse` = 8 |
| 9 | `UserDisconnectedResponse` | `TYPE_UserDisconnected` = 9 |

Şemada tanımlı ama hiçbir union'da olmayan, kullanılmayan tablolar: `RemoveOrder{orderId:uint}`, `Order{…}`. `MarketType` enum'u (FB ve C) hiçbir alanda kullanılmaz.

### 3.2 Kök tablolar

| Tablo | Alan | Tip | Not |
|-------|------|-----|-----|
| `RequestHolder` | `request` | union `BaseRequest` | |
| | `authToken` | `[byte]` | Login'in döndürdüğü token. C `BaseRequest.authToken` → `strlen` uzunluğunda kopyalanır. Login ve heartbeat'te yazılmaz. |
| `ResponseHolder` | `response` | union `BaseResponse` | |
| | `status` | bool, varsayılan false | İstemci yalnız AccountStrategies, AllOrders ve UserDisconnected'da okur (§ 6.3) |
| | `statusCode` | uint | Her yanıtta okunur. order-service: 200 / 401 |

C `BaseRequest{requestType, connectionId, authToken}`: `connectionId` wire'da yoktur, sunucu kendi fd'sini yazar.

### 3.3 İstek tabloları

Birim sütunu order-service'in kullandığı anlamdır ([arayuzler § 3.3](../order-service/arayuzler.md#33-enterorderrequest-alanları)). SDK hiçbir değeri ölçeklemez; değerler olduğu gibi kopyalanır.

| Tablo.alan | FB tipi | C alanı (tip) | Birim / not |
|------------|---------|---------------|-------------|
| `LoginRequest.username` | string | `userName` (const char*) | |
| `.password` | string | `password` | **Açık metin** |
| `.application` | `Application` | `applicationType` | Decode'da bug var (§ 4) |
| `EnterOrder.order_book_id` | uint | `orderbookId` (unsigned int) | ITCH orderbook id |
| `.quantity` | ulong | `quantity` (unsigned long) | lot |
| `.price` | int | `price` (int) | **raw** = TL × 10^decimalCount, int32 |
| `.account` | string | `account` | |
| `.strategy` | `StrategyType` | `strategyType` | |
| `.strategy_identifier` | **`[byte]`** | `strategyIdentifier` | string değil |
| `.side` | `Side` | `side` | |
| `.time_in_force` | `TimeInForce` | `timeInForce` | |
| `.pass_through` | string | `passThrough` | İstemcinin korelasyon alanı |
| `.regular_order_type` | `RegularOrderType` | `regularOrderType` | |
| `.protocol_type` | `ProtocolType` | `protocolType` | |
| `.timeToSent` | ulong | `timeToSent` (unsigned long) | order-service → `expire_date` (FIX GTD). ❓ doğrulanmadı: biçim |
| `.is_active` | bool | `isActive` | |
| `ReplaceOrder.order_token` | `[byte]` | `orderToken` | SDK token'ı (OrderAccepted'dan) |
| `.quantity` | ulong | `quantity` | lot |
| `.price` | int | `price` | raw |
| `.pass_through` | **`[byte]`** | `passThrough` | Enter'da string, burada byte vektörü |
| `.protocol_type` | `ProtocolType` | `protocolType` | |
| `CancelOrder.order_token` | `[byte]` | `orderToken` | |
| `.protocol_type` | `ProtocolType` | `protocolType` | |
| `AllOrdersRequest.operation` | `OperationType` | `operation` | Pratikte GET |
| `AccountStrategyRequest.operation` | `OperationType` | `operation` | GET / SET |
| `.accountStrategy` | `AccountStrategy` | `accountStrategy` (gömülü struct) | Encode: `account` ve `strategy_identifier` yalnız SET'te yazılır. `position`/`last_price` **hiç yazılmaz**. Decode yalnız SET'te `account`, `strategyIdentifier`, `orderBookId`, `overallValue` okur. `strategyType` her zaman okunur. |
| `HearthbeatRequest.hearthbeat_count` | int | `HeartBeatRequest.heartbeatCount` (iç struct) | Hep 1 |

`AccountStrategy` (ortak tablo, `fb`): `order_book_id:uint`, `account:string`, `strategy:StrategyType`, `strategy_identifier:`**`string`** (Enter'dakinin aksine), `overall_value:int`, `position:int` (lot), `last_price:int` (raw). C `AccountStrategy`: aynı alanlar, `int`.

### 3.4 Yanıt tabloları

Hangi alanı order-service'in doldurduğu ve olay anlamı: [arayuzler § 3.7](../order-service/arayuzler.md#37-olayların-istemciye-dönüşü).

| Tablo | Alanlar (FB tipi) | C struct farkları |
|-------|-------------------|-------------------|
| `LoginResponse` | `token:[byte]` | `token` const char* |
| `OrderAccepted` | `order_id:ulong`, `pass_through:string`, `order_token:string`, `order_book_id:uint`, `quantity:ulong` (lot), `price:int` (raw), `account:string`, `strategy`, `strategy_identifier:string`, `pre_trade_quantity:ulong` (lot), `side`, `timestamp:ulong` | `timestamp` unsigned long long. Token burada **string**, istekte `[byte]`. |
| `OrderReplaced` | `order_id:ulong`, `pass_through`, `replacement_order_token`, `previous_order_token` (string), `order_book_id:uint`, `quantity:ulong`, `price:int`, `account`, `strategy`, `strategy_identifier`, `pre_trade_quantity:ulong`, `side`, `timestamp:ulong` | |
| `OrderCanceled` | `order_token:string`, `order_book_id:`**`int32`**, `side`, `timestamp:ulong`, `order_id:ulong`, `reason_code:uint`, `reason:string`, `matchId:ulong`, `quantity:ulong`, `price:int` | C `orderBookId` unsigned int. **Encode `price`'ı hiç yazmaz, `matchId`'ye sabit 0 yazar** (`MAHelper::getOrderFBObj`). Host doldursa da istemcide 0 olurlar. |
| `OrderExecuted` | `previous_position:long`, `daily_position:long`, `total_position:long`, `last_price:`**`long`**, `order_token:string`, `order_book_id:int32`, `quantity:ulong` (bu dolumun lotu), `price:int32` (raw), `timestamp:ulong`, `match_id:ulong` | Wire'da `side`, `account`, `pass_through` yoktur. C `timestamp` unsigned long. |
| `OrderRejected` | `order_token:string`, `pass_through:string`, `order_book_id:uint`, `account`, `strategy`, `strategy_identifier`, `timestamp:ulong`, `reject_code:int`, `reject_reason:string` | |
| `UserDisconnectedResponse` | `user_name`, `password` (açık metin), `ip` (string), `port:int`, `application_user:string`, `allowed_accounts:[string]`, `callbackNumber:int`, `totalNumberOfCallbacks:int` | C: `username`, `applicationUsername`, `port` unsigned int, `allowedAccounts` (const char**) + `allowedAccountsSize` |
| `AccountStrategiesResponse` | `accountStrategies:[AccountStrategy]`, `operationType` | C `AccountStrategyResponse{strategySize, operationType, accountStrategies[30000]}`: sabit dizi, ~1,4 MB |
| `AllOrdersResponse` | `orders_size:int`, `orders:[SingleOrderResponse]` | `SingleOrderResponse{response: BaseResponse}`: iç içe union. C `AllOrdersResponse{ordersSize, orders[100000]}` (BaseResponse* dizisi, ~800 KB) |

`timestamp` alanlarının birimini SDK tanımlamaz. Kaynağı order-service/MAOrderSDK'dır (❓ [arayuzler § 3.7](../order-service/arayuzler.md#37-olayların-istemciye-dönüşü)).

## 4. Enum'lar

Hepsi `: byte`. Wire değeri = sayısal değer. C enum'ları aynı sayıları taşır, adları önekle farklıdır (`MAOrderEnums.h`).

| Enum | Değerler (FB adı = sayı) | C öneki |
|------|--------------------------|---------|
| `Application` | `APP_UNKNOWN` 0, `HFT` 1, `AlgoTrading` 2, `OUCH` 3 | `APPLICATION_` |
| `Side` | `UNKNOWN_SIDE` 0, `BUY` 1, `SELL` 2, `SHORT_SELL` 3 | `SIDE_` |
| `TimeInForce` | `UNKNOWN_TIME_IN_FORCE` 0, `DAY` 1, `IMMEDIATE_OR_CANCEL` 2, `FILL_OR_KILL` 3, `GOOD_TILL_CANCEL` 4, `GOOD_TILL_DATE` 5, `AT_CROSSING` 6 | `TIF_` |
| `RegularOrderType` | `UNKNOWN_REGULAR_ORDER_TYPE` 0, `STANDART` 1 (yazım hatası), `MARKET` 2, `LIMIT` 3, `MARKET_WITH_LEFTOVER_LIMIT` 4 | `REGULAR_ORDER_` |
| `StrategyType` | `UNKNOWN_STRATEGY` 0, `USER` 1, `WARRANT` 2, `AKD` 3, `HFT` 4, `MOVING_AVERAGE` 5, `ARBITRAGE` 6, `VWAP` 7, `THEORETICAL_PRICE` 8, `MAX_PRICE` 9, `FUND_TRACKER` 10, `ORDER_CHASE` 11, `HFT_USER` 12, `HFT_WARRANT` 13, `MIN_PRICE` 14, `HFT_WARRANT_ADVANCED` 15 | `TYPE_` (C'de `TYPE_UNKNOWN` = 0) |
| `OperationType` | `OPERATION_UNKNOWN` 0, `GET` 1, `SET` 2, `DELETE` 3 | `OPERATION_` |
| `ProtocolType` | `UNKNOWN` 0, `OUCH` 1, `FIX` 2 | `PROTOCOL_TYPE_` |
| `MarketType` | `UNKNOWN` 0, `EQUITY` 1, `DERIVATIVE` 2 | `MarketType_` (kullanılmaz) |

- `HFT_WARRANT_ADVANCED (15)`: ⚠ master'da yok (2026-10-22).
- ouch-sdk'nın kendi `StrategyType`'ı bu tablodan farklıdır ([ouch-sdk README](../ouch-sdk/README.md)). order-service `StrategyType` değerini DB strateji id'si olarak kullanır ([arayuzler § 3.6](../order-service/arayuzler.md#36-enum-ve-id-varsayımı)).
- Eşleme `MAHelper::get<X>` (C → FB) ve `get<X>Result` (FB → C) `switch`'leriyle yapılır. Listede olmayan değer **sessizce 0** olur (`default`).
- **bug:** `MAHelper::getApplicationResult` FB `OUCH` → `APPLICATION_AlgoTrading`, FB `AlgoTrading` → `APPLICATION_OUCH` eşler. Encode (`getApplication`) doğrudur. Etkisi: AlgoProd `AlgoTrading` (2) gönderir, order-service `APPLICATION_OUCH` görür. `OrderServer::RequestReceived` yalnız `APPLICATION_AlgoTrading`/`HFT`'yi eşlediği için AlgoProd login'i trade-data-app'e `APP_UNKNOWN` olarak gider. HFT (1) etkilenmez. ❓ doğrulanmadı: trade-data-app'in `application` değerine göre davranış değiştirip değiştirmediği.
- `getRegularOrderType` C değerini FB sabitleriyle karşılaştırır. Sayılar aynı olduğu için çalışır.

## 5. İstek ↔ yanıt eşlemesi

Protokolde **istek id'si yoktur**. Yanıtlar asenkrondur. İstemci yanıtı tipine (ouch-sdk: tip başına tek `std::promise`) veya emir olaylarında `orderToken`/`passThrough` değerine göre eşler.

| İstek | Doğrudan yanıt | Sonraki olaylar |
|-------|----------------|-----------------|
| `LoginRequest` | `LoginResponse{token}`, `statusCode` 200/401. `status` hep false. | — |
| `EnterOrder` | Yok | `OrderAccepted` / `OrderRejected` → `OrderExecuted`, `OrderCanceled`. İlk olaya kadar token bilinmez; eşleme `passThrough` ile yapılır. |
| `ReplaceOrder` | Yok. Token geçersizse yanıt da yoktur. | `OrderReplaced` / `OrderRejected` |
| `CancelOrder` | Token geçersizse `OrderRejected{401}` | `OrderCanceled` |
| `AllOrdersRequest` | Tek `AllOrdersResponse`. İçinde Accepted, Replaced, Canceled, Executed ve Rejected olayları bulunur. | — |
| `AccountStrategyRequest` | `AccountStrategiesResponse`. `operationType` isteği yansıtır, istemci GET/SET'i buna göre ayırır. | — |
| `HearthbeatRequest` | Yok | — |
| — | — | `UserDisconnectedResponse`: istek olmadan, handoff'ta |

Ayrıntı ve sessiz düşüşler: [arayuzler § 3.2](../order-service/arayuzler.md#32-istek-tipleri), [§ 8](../order-service/arayuzler.md#8-şüpheli) madde 5.

## 6. C struct ↔ FlatBuffers dönüşümü ve pointer ömrü

### 6.1 Encode (`MAHelper::getRequest`, `getResponse`, `getOrderFBObj`)

- Tek bir singleton `flatbuffers::FlatBufferBuilder builder{4096}` kullanılır. Her mesajda `Reset()` çağrılır, sonuç `std::string`'e kopyalanır. Koruma tarafa göre değişir: istemcide `MATCPClient::builderMutex` (spin `try_lock`), sunucuda `MATCPServer::responseMtx`. `MAHelper::requestMtx` tanımlıdır ama kullanılmaz.
- Encode senkrondur. `sendOrderRequest` / `setOrderResponse` döndüğünde host struct'ı serbest bırakabilir; SDK struct'ı sahiplenmez ve silmez.
- `string` alanlar `CreateString(const char*)`, `[byte]` alanlar `CreateVector(ptr, strlen(ptr))` ile yazılır. **Encode edilen her `const char*` alan NULL olmamalıdır** (`strlen(nullptr)` → çökme). Boş değer için `""` verilir. İstisna: AccountStrategy GET'te `account`/`strategyIdentifier` okunmaz.
- Bilinmeyen `requestType` gelirse `getRequest` `return nullptr;` ile `std::string` kurar. Bu, libstdc++'ta `logic_error` fırlatır ve hata `extern "C"` sınırından geçer.

### 6.2 Decode — istek (sunucu, `MAHelper::getRequestResult`)

- Her istek için `new` ile C struct oluşturulur. **SDK silmez**; host da silmezse sızıntı olur (order-service silmez, [arayuzler § 8](../order-service/arayuzler.md#8-şüpheli) madde 14).
- **Derin kopya değildir.** `const char*` alanlar (`c_str()` / `Data()`) alınan çerçevenin `fbData` `std::string`'ini gösterir. `fbData`, `MATCPServer::processCallback`'te çerçeve başına yereldir ve callback döndükten sonra yok olur. **Pointer'lar yalnız `request_protocol` callback'i süresince geçerlidir.** Host saklamak istiyorsa callback içinde kopyalamalıdır. order-service AccountStrategy GET'te bu kuralı çiğner ([arayuzler § 8](../order-service/arayuzler.md#8-şüpheli) madde 3).
- `[byte]` alanlar (`strategy_identifier`, `order_token`, Replace `pass_through`, `authToken`) `Data()` ile C string'e çevrilir. FlatBuffers vektörlerinde `\0` sonlandırıcı yoktur (§ Şüpheli 3).
- Alan yoksa (`authToken` login/heartbeat'te yazılmaz) erişimci `nullptr` döner. `->Data()` / `->c_str()` adres aritmetiğidir, okuma yapmaz; sonuç küçük, geçersiz bir pointer'dır. SDK'da çökme olmaz. Host bu alanı okursa çöker. ⚠ Eski bilgi tabanı `authToken()->Data()` için "segfault" diyordu; development'ta çökme SDK içinde değil, alan okunursa host'ta olur.
- Bilinmeyen union tipi → `nullptr` döner. Ardından `MATCPServer::processCallback` `baseRequest->connectionId = connection` yazar ve null deref ile çöker (§ 9).

### 6.3 Decode — yanıt (istemci, `MAHelper::getResponseResult`, `getOrderFromFB`)

- `std::make_shared<…>()` ile oluşturulur. `const char*` alanlar yine `fbData`'yı gösterir (`MATCPClient::processCallback` yereli). **Yalnız `response_protocol` callback'i süresince geçerlidir.** Callback dönünce shared_ptr da serbest kalır.
- `AllOrdersResponse.orders[i]`: her alt olay ayrı `shared_ptr` olarak `MAHelper::ownershipList`'te tutulur. Callback'ten sonra `clearOwnership()` listeyi temizler. Sayaç olarak vektör uzunluğu değil `orders_size` kullanılır. Sınır kontrolü yoktur: 100000'i aşan `orders_size` taşar. `AccountStrategyResponse` için 30000 sınırı da aynıdır.
- `UserDisconnected.allowedAccounts`: her hesap `new char[]` ile kopyalanır. Bu, yanıt decode'unda **tek derin kopyadır** ve hiç silinmez.
- `baseResponse.status` yalnız AccountStrategies, AllOrders ve UserDisconnected'da okunur. Login ve emir olaylarında istemcide hep `false` kalır. `statusCode` her yanıtta okunur. ouch-sdk login sonucunu `statusCode` ile değerlendirir, SET sonucunu `status` ile.
- Bilinmeyen yanıt tipinde `result` boş kalır, ardından `result->statusCode` yazımı null deref ile çöker. `SingleOrderResponse` içinde bilinmeyen tip olursa `orders[i] = nullptr` olur.
- ⚠ ouch-sdk `handleIncomingMessage` struct'ları **sığ** kopyalar (`new LoginResponse(*resp)` vb.) ve bazılarını callback'ten sonra okur. Örnek: `login()` promise'ten sonra `std::string(loginResponse->token)` yapar. Bu kopyalardaki pointer'lar serbest kalmış tamponu gösterir ([ouch-sdk](../ouch-sdk/README.md); § Şüpheli 4).

## 7. Boyutlar

- `FlatBufferBuilder` başlangıç kapasitesi 4096 bayttır, gerekirse büyür. Azami çerçeve boyu uint32 ile sınırlıdır. Büyük `AllOrdersResponse` (order-service en çok 99980 olay) çok MB'lık tek çerçeve olur ve 4096'lık `recv` parçalarıyla birleştirilir.
- Heartbeat çerçevesi birkaç on bayttır. ❓ doğrulanmadı: kesin boy.

## 8. Taşınan gizli bilgi

`LoginRequest.password` ve `UserDisconnectedResponse.password` (OUCH şifresi) açık metindir; TLS yoktur. `UserDisconnected` BIST gateway `ip`/`port` bilgisini de taşır. Şifreleme kasıtlı olarak yoktur (iç ağ varsayımı). Log sızıntıları: [arayuzler § 8](../order-service/arayuzler.md#8-şüpheli) madde 19.

## 9. Versiyonlama ve uyumluluk

Sürüm müzakeresi yoktur. İki taraf aynı şemayla derlenmiş `libMARpc` kullanmalıdır. Kurallar:

| Değişiklik | Wire | SDK davranışı |
|------------|------|---------------|
| Tabloya **sona** yeni alan | Uyumlu (FB) | Eski okuyucu yok sayar. Eski yazıcının yazmadığı string alanı yeni okuyucuda `c_str()` ile geçersiz pointer olur (§ 6.2) → host çöker. Yeni string alanlar için decode tarafında null kontrolü gerekir. |
| Alan sırasını değiştirmek / araya eklemek / silmek | **Kırar** (FB vtable sırası) | — |
| Union'a **sona** yeni üye | FB'de uyumlu | Eski MARpc bilinmeyen tipi **null deref ile çöker** (§ 6.2, § 6.3). İki taraf birlikte güncellenmelidir. |
| Union üye sırası | **Kırar** (indeks = tip) | — |
| Enum'a yeni değer | Uyumlu | `MAHelper` `switch`'ine eklenmezse 0'a düşer. Eski taraf yeni değeri 0 görür. Örnek: istemci `HFT_WARRANT_ADVANCED (15)` gönderir, order-service eski `libMARpc` ile çalışıyorsa `UNKNOWN (0)` görür, hesap-strateji bulunamaz ve emir sessizce düşer. |
| Tablo/alan/enum **adı** (`Hearthbeat`, `STANDART`) | Uyumlu (ikili biçimde isim yoktur) | Yalnız üretilen kodun API'si değişir. ⚠ Eski bilgi tabanı "düzeltmek wire compat'i bozar" diyordu; bozmaz, yalnız kaynak uyumluluğunu etkiler. |
| C struct (`MAOrderStruct.h`) yerleşimi | Wire'ı etkilemez | **ABI**: `libMARpc.so` ile host (ouch-sdk, order-service) aynı başlıkla derlenmelidir. |

Deploy sırası: şema veya enum değişikliğinde Algo-Setup `MAProdEnv`'deki `libMARpc.so` ile ona bağlı ouch-sdk, HftSrvProd, AlgoProd ve order-service aynı sürüme çekilir. ❓ doğrulanmadı: bunun deploy sürecinde zorlandığı.

## Şüpheli

"bug?" = koddan çıkarım, canlıda doğrulanmadı.

1. **bug** `getApplicationResult` OUCH ↔ AlgoTrading ters (§ 4). AlgoProd login'i order-service'te `APP_UNKNOWN`.
2. **bug?** `CLOSE_MSG` sabit offset'le kontrol edilir (`MATCPServer::processCallback`). Tamponda ilk çerçeve değilse 1 baytlık `"C"` `GetRequestHolder`'a gider. Sınır dışı okuma olur, sonuç tanımsızdır (büyük olasılıkla null union ve çökme).
3. **bug?** `[byte]` alanlarda sonlandırıcı yok. FlatBuffers vektörü, uzunluğu 4'ün katı değilse sıfır dolguyla biter; 4'ün katıysa veri bir önceki yazılan nesnenin 4 baytlık uzunluk önekine bitişiktir. `getRequest` sırası: Enter'da `strategyIdentifier` (tamponun sonu, `fbData`'nın `\0`'ı ile güvenli) → `passThrough` → `account` → `authToken`. Cancel/Replace'te `orderToken` → `authToken` (→ Replace `passThrough`). Bu düzende `authToken` ve Replace `passThrough` uzunlukları 4'ün katıysa C string olarak okununca sonuna çöp bayt eklenir (bir önceki string'in uzunluğunun düşük baytı). Bu, order-service'te `ValidateToken` başarısızlığına ve sessiz düşüşe ya da `passThrough` eşleşmemesine yol açabilir. doğrula: canlı token uzunlukları ([arayuzler § 8](../order-service/arayuzler.md#8-şüpheli) madde 15). `LoginResponse.token` ilk yazılan nesne olduğu için güvenlidir.
4. **bug?** Pointer ömrü sözleşmesi (§ 6.2, § 6.3) başlıklarda yazılı değildir. ouch-sdk sığ kopyaları callback'ten sonra okur (login token, `AccountStrategyResponse` alanları): use-after-free. Pratikte tampon belleği hemen üzerine yazılmadığı için çalışıyor olabilir.
5. **bug?** `OrderCanceled.price` encode edilmez, `matchId` hep 0 (`getOrderFBObj`). Host'un doldurduğu değer kaybolur. Kasıtlı olduğuna dair iz yok.
6. **bug?** Bilinmeyen union tipi her iki tarafta çöker (§ 6.2, § 6.3). Şema sürümleri karışırsa (yeni istemci + eski order-service) sunucu process'i düşer.
7. **bug?** `Verifier` yok, `LEN` için üst sınır yok. Bozuk veya yanlış porta gelen veri sunucuyu çökertebilir ya da sınırsız bellek tüketebilir.
8. Küçük: `getHeartbeatRequest` sayaç taşımaz, hep 1. `timeToSent` adı (`time_to_send` olmalı). `STANDART`, `Hearthbeat` yazım hataları. `MarketType`, `RemoveOrder` ve `Order` kullanılmaz. `OrderCanceled`/`OrderExecuted.order_book_id` int32, diğerleri uint32.
