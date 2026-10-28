---
kapsam: order-service'in dış arayüzleri (MARpc sunucusu OrderServer, gRPC sunucusu OrderServiceImpl), wire alanları ve ölçekleri, OrderDispatcher ile emrin girişten BIST'e ve olayın geri dönüşüne kadar yolu, açılış sırası, thread/kilit modeli
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
dogrulama: 2026-10-22
durum: taslak
---

# order-service — arayüzler ve emir yönlendirme

İndeks: [README.md](README.md). Bu dosyada olmayanlar:
- MAOrderSDK oturumları, OUCH/FIX kullanıcıları, SDK callback ayrıntısı, handoff → [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md)
- Toplu emir zamanlaması (sabah/açılış/YİP/teorik/akşam) → [toplu-emirler.md](toplu-emirler.md)
- Risk kuralları → [risk.md](risk.md)
- `DatabaseClient`, `Service/Network/*`, emir kalıcılığı, config → [kalicilik-ve-config.md](kalicilik-ve-config.md)
- Karşı taraflar: [ouch-sdk](../ouch-sdk/README.md), [network-sdk](../network-sdk/README.md), trade-data-app istemcisi [api.md § 9](../trade-data-app/api.md) ve [veri-akisi.md § 5.4](../trade-data-app/veri-akisi.md)

Kod: `main.cpp`, `OrderServiceApplication.*`, `OrderServer.*`, `Managers/OrderDispatcher.*`, `Managers/OrderManager.*` (`Bind`, `OrderResponseCallBack`, `sendOrderRejectedToApplication`), `Managers/Sdk/MAOSdkManager.cpp` (`SendOrderAsync`, `ConfigureSdkCallbacks`, `FetchUserOrders`), `Service/Network/AuthenticationService.*`, `Service/servicemodel/*`, `Service/clientmodel/ouch-data.proto`. `Managers/OrderManagerFactory.h` **boş bir sınıftır**, hiçbir yerde kullanılmaz.

## 1. Arayüz özeti

| Arayüz | Taşıma | Bind | İstemci | Kod |
|--------|--------|------|---------|-----|
| MARpc | TCP, 4 bayt uzunluk + FlatBuffers (`orders.fbs` / `orders_response.fbs`) | `server.port` (örnek 8000), **tüm arayüzler** (`getaddrinfo(nullptr, AI_PASSIVE)`; `server.address` kullanılmaz) + Unix soket `/workingDirectory/sock/mysocket` | ouch-sdk: HFT, AlgoProd | `OrderServer` + network-sdk `Server/MATCPServer.cpp` |
| gRPC `clientmodels.OrderService` | HTTP/2, insecure, mesaj boyu sınırsız (`-1`) | `server.address:server.grpcPort` (örnek `0.0.0.0:9035`) | trade-data-app (`orderservice.go`) | `Service/servicemodel/OrderServiceImpl.*` |
| gRPC health | Default health service, `""` = SERVING | aynı port | trade-data-app `monitorConnection` | `OrderServer::StartServiceWithGRPC` |
| gRPC istemci `servicemodels.DataService` | — | — | order-service → trade-data-app | `Service/clientmodel/ouch-data.proto` (§5) |

İki sunucu **aynı token tablosunu** kullanır (`AuthenticationService::token_username`). MARpc login'iyle alınan token gRPC'de de geçerlidir, tersi de.

## 2. Açılış sırası

`main`: config yolu argümanı zorunlu → (derleme bayrağına göre) `LD_PRELOAD` ile Onload/VMA'yı yükleyip kendini `execvp` ile yeniden başlatır → `ma::build::PrintAll` → sinyal handler'ları (SIGINT, SIGABRT, SIGTERM, SIGHUP, SIGUSR1, SIGUSR2 → `app.Stop()`; SIGPIPE yok sayılır) → `ConfigurationManager` → log dizini/log init → lisans kontrolü **yorum satırında** → `app.Start()`.

`OrderServiceApplication::Start`:
1. Nesneler kurulur: `DatabaseClient`, `AuthenticationService`, `InstrumentService`, `UserService`, `AccountStrategyService`, `OrderService`, `RiskManager`, `OrderDispatcher` (içinde `MAOSdkManager` oluşur), `OrderServer` (constructor'da dispatcher'a MARpc olay callback'lerini bağlar, §6.4).
2. PerfSDK başlatılır (`monitoring.active` ise). `order_dispatcher->Start`'tan **önce** olmalı; yorumda gerekçe var (MAOrderSDK metrik kaydı).
3. `db_client->Connect()` → trade-data-app `DataService.Login` (`Application=OUCH`). **Dönüş değeri kontrol edilmez.** Bu login trade-data-app'te GUI WebSocket'ini açan tetiktir ([sistem-haritasi](../../00-genel/sistem-haritasi.md#başlatma-sırası)).
4. `FetchInstruments`, `FetchStrategies`, `FetchAccountStrategies`, `FetchAccountStrategyPositions`, `risk_manager->Start(riskControl)`.
5. `order_dispatcher->Start()` → `OrderManager::Start` (DB yazma thread'leri, `offhours_invertor`) → `MAOSdkManager::StartProperly` (OUCH/FIX login, toplu emir thread'leri).
6. Handoff zamanlayıcısı: `repeatableOrders.ouch[]` içindeki her `type == "morning"` girdisi için `shouldTriggerOuchDisconnectOnStartup`:
   - Saat geçmişse: detached thread hemen `order_dispatcher->TriggerOuchDisconnect()` çağırır (log "Waiting for HftService" der ama bu fonksiyonda bekleme yoktur; bekleme handoff tarafında, bkz. [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md)). Döngü `break` eder.
   - Saat gelmemişse: detached thread `sabah saati + 30 sn`'ye kadar uyur, sonra `TriggerOuchDisconnect()`. Döngü devam eder; birden çok `morning` girdisi varsa her biri için ayrı thread kurulur.
7. `srv->Start()`: önce MARpc (`startOrderServer`, delegate'ler), sonra gRPC `BuildAndStart` + `server->Wait()`. **Ana thread burada sonsuza kadar bloklanır**; arkasındaki `while(is_running){}` pratikte çalışmaz.

Sonuç: MARpc ve gRPC portları OUCH/FIX login'leri ve toplu emir thread'leri kurulduktan sonra açılır. Config anahtarları: [kalicilik-ve-config.md](kalicilik-ve-config.md).

## 3. MARpc sunucusu (`OrderServer`)

### 3.1 Taşıma ve bağlantı (network-sdk `MATCPServer`)

- Çerçeve: 4 bayt uzunluk + FlatBuffers `RequestHolder` (`request` union + `authToken:[byte]`). Yanıt: `ResponseHolder`.
- Bağlantı kimliği = socket fd (`connectionId`). Kapanan fd yeniden kullanılabilir.
- Üst sınır `MAX_ALLOWED_CONNECTION = 5` (TCP + Unix toplam). Aşan bağlantı `accept` edilir ama **kapatılmaz ve işlenmez**.
- Her bağlantıya 2 thread (listener başına 10'luk `ThreadPool`):
  - `receiveMessage`: non-blocking `recv` döngüsü (busy-spin). Gönderim kuyruğundan **iterasyon başına bir** mesaj yollar.
  - `processCallback`: çerçeveyi ayrıştırır, `OrderServer::RequestReceived`'ı **senkron** çağırır (busy-spin `try_dequeue`).
- Heartbeat: istemci (network-sdk `MATCPClient::sendHeartbeatMessage`, ouch-sdk üzerinden) 3 sn'de bir `HeartbeatRequest` gönderir. Sunucu `CONNECTION_TIMEOUT_MS = 15000` ms geçince bağlantıyı düşürür (`checkHeartbeatMessages`, `yield` ile dönen ayrı thread). Heartbeat `RequestReceived`'a ulaşmaz.
- İstemci `"C"` gövdeli çerçeve gönderirse sunucu bağlantıyı kapatır (`CLOSE_MSG`).
- Kapanışta `closeCallBack` → `OrderServer::ConnectionClosed` (§3.9).
- `setPerformanceSDK` order-service'te çağrılmaz; MARpc metrikleri kapalıdır.

### 3.2 İstek tipleri

`RequestReceived` `requestType`'a göre dallanır (`MAOrderEnums.h` `RequestTypes`):

| Tip | Değer | İşlem | Yanıt |
|-----|-------|-------|-------|
| `LoginRequest` | 4 | `AuthenticationService::Login` → trade-data-app `DataService.Login`. `applicationType`: 1 HFT, 2 AlgoTrading, diğerleri `APP_UNKNOWN`. ⚠ network-sdk decoder'ı 2 ile 3'ü yer değiştiriyor (`MAHelper::getApplicationResult`), bu yüzden AlgoProd'un login'i `APP_UNKNOWN` ile yapılıyor ([network-sdk/wire-protokolu § 4](../network-sdk/wire-protokolu.md#4-enumlar), K-149). Bağlantı, kullanıcı adının bağlantı listesine eklenir (`user_connections`). | `LoginResponse{token}`; `statusCode` 200 / 401. `status` alanı set edilmez (false). |
| `EnterOrderRequest` | 1 | §3.3 | Doğrudan yanıt yok; olaylar §3.7 |
| `CancelOrderRequest` | 3 | Token geçersizse `OrderRejected{401, "Unauthorized"}` döner. Geçerliyse `CancelOrder{orderToken, protocolType}` → `OrderDispatcher::SendOrder` | Olay |
| `ReplaceOrderRequest` | 2 | Token geçersizse **sessizce düşer** (yalnız log). Geçerliyse `ReplaceOrder{orderToken, price, quantity, passThrough, protocolType}` → dispatcher | Olay |
| `AllOrdersRequest` (`OPERATION_GET`) | 5 | Detached thread: `FetchUserOrders(kOuch, user)` + `FetchUserOrders(kFix, user)` (kFix manager yok, hep boş). FIX replay'i bitene kadar en çok 10 sn bekler (`MAOSdkManager::WaitForFixReplay`). | Tek `AllOrdersResponse`; içinde olay listesi (§3.7 tipleri). Kapasite 100000 slot, kodda en çok 99980 gönderilir, fazlası sessizce kesilir. |
| `AccountStrategyRequest` | 6 | §3.5 | `AccountStrategyResponse` |
| `HeartbeatRequest` | 7 | network-sdk içinde tüketilir | — |

`authToken` her istekte `RequestHolder.authToken`'dan okunur ve `AuthenticationService::ValidateToken` ile kullanıcı adına çevrilir. Bu kullanıcı adı emrin `SenderApplication`'ı olur ve olay yönlendirmesinin anahtarıdır (§3.7).

### 3.3 `EnterOrderRequest` alanları

`RequestReceived` → `models::EnterOrder` → `OrderDispatcher::SendOrder`.

| Wire alanı | Tip | Birim / ölçek | order-service'te |
|------------|-----|---------------|------------------|
| `orderbookId` | uint32 | ITCH orderbook id | `SetOrderBookId` |
| `quantity` | ulong | **lot** | `SetQuantity` |
| `price` | int32 | **raw** = TL × 10^`decimalCount` ([sözlük](../../00-genel/sozluk.md)) | Dönüştürülmez; `MAOSdkManager::ToSdkOrder` `msg.price`'a aynen koyar |
| `account` | string | Hesap adı | Hesap-strateji anahtarı ve OUCH/FIX yönlendirmesi |
| `strategyType` | enum `StrategyType` (1..15) | **DB strateji id'si olarak** kullanılır | `AccountStrategyService::GetAccountStrategy(strategyType, account, strategyIdentifier, orderbookId, username)`. Bulunamazsa exception yakalanır, log basılır, **istemciye yanıt gitmez**. |
| `strategyIdentifier` | `[byte]` | — | Anahtarın parçası |
| `side` | 1 BUY, 2 SELL, 3 SHORT_SELL | — | İç enum `'B'`/`'S'`/`'T'` |
| `timeInForce` | 1..6 | — | Yalnızca IOC(2), FOK(3), GTD(5) eşlenir; **GTC(4), AT_CROSSING(6) ve 0 → DAY** |
| `passThrough` | string | Serbest metin | Olaylarda geri döner. İstemcinin korelasyon alanıdır (wire'da istemci token'ı yoktur). |
| `regularOrderType` | 1 STANDART, 2 MARKET, 3 LIMIT, 4 MARKET_WITH_LEFTOVER_LIMIT | — | Aynı değerler |
| `protocolType` | 0/1 OUCH/2 FIX | — | `Protocol`; 0 → dispatcher "Unknown protocol type" loglar ve emri düşürür |
| `timeToSent` | ulong | ❓ doğrulanmadı: biçim | `SetExpireDate` → MAOrderSDK `msg.expire_date` (FIX GTD tag 432; 0 = yok) |
| `isActive` | bool | — | Yalnızca loglanır |

Sabit set edilenler: `OrderType=kEnterOrder`, `IsMainOrder=true`, `MainOrderId=0`. Emir token'ı istemciden **gelmez**: wire'da alan yoktur. Token'ı MAOrderSDK atar ve istemci onu ilk kez `OrderAccepted` ile öğrenir (HFT'nin kendi token havuzu wire'a çıkmaz).

### 3.4 Replace ve Cancel

- **Cancel:** dispatcher protokolü `order_protocols[token]`'dan bulur, yoksa istekteki `protocolType`'ı kullanır (§6.3). `MAOSdkManager::SendOrderAsync(CancelOrder)` → `sdk_->cancelOrder(token)`. SDK `false` dönerse **yalnızca log**, istemciye olay yok. Risk kontrolü yok.
- **Replace:** `price` raw int32, `quantity` lot. `MAOSdkManager::SendOrderAsync(ReplaceOrder)`:
  1. `entered_orders[token]` bulunamazsa log + **sessiz düşüş**.
  2. Risk: `checkEnterOrder(orderedDifference(entered, replace))` (ayrıntı [risk.md](risk.md)). Ret → `sendOrderRejectedToApplication(entered, desc)`.
  3. `ReplaceOrderMsg{client_order_id=eski token, new_client_order_id="" (SDK atar), quantity, price, passthrough}`. İç kayıt için 0 fiyat/miktar eski değerle doldurulur; SDK mesajına ise istekteki değer (0 olabilir) gider. ❓ doğrulanmadı: MAOrderSDK'nın 0'ı "değiştirme" diye yorumladığı.
  4. Yeni token `entered_orders`'a yazılır, `InsertOrderToDatabaseAsync`.

### 3.5 Strateji kaydı (`AccountStrategyRequest`)

ouch-sdk `insertStrategyInfo` / `getStrategyInfo` bunu kullanır.

- Token geçersiz → `AccountStrategyResponse{401, status=false, strategySize=0}`.
- **SET** (`OPERATION_SET`): `AccountStrategy{account, orderBookId, strategyIdentifier, overallValue}` + `GetStrategyById(strategyType)` → `AccountStrategyService::InsertAccountStrategy` → trade-data-app `DataService.SetAccountStrategy` (senkron, bu bağlantının `processCallback` thread'inde). Başarılıysa bellek haritasına (`account_strategies`) eklenir. Yanıt **her zaman** `200, status=true` (DB hatası istemciye yansımaz).
- **GET**: detached thread → `GetAccountStrategies(token)` (DB'den hepsi çekilir, uygulama kullanıcısına göre süzülür) → `AccountStrategyResponse` (en çok 30000 kayıt; alanlar: `orderBookId`, `account`, `strategyType` (= DB strateji id), `strategyIdentifier`, `position` (lot), `lastPrice` (raw), `overallValue`).

### 3.6 Enum ve id varsayımı

MARpc yolu `StrategyType` enum değerini doğrudan DB `Strategies.id` olarak kullanır (`GetAccountStrategy` anahtarı, `GetStrategyById`, yanıtlarda `(StrategyType) StrategyType().Id()`). gRPC yolu ise tipi isimle eşleyip id'yi bulur (`OrderServiceImpl::getStrategyId`). ❓ doğrulanmadı: her ortamda DB strateji id'leri enum değerleriyle (HFT=4, MaxPrice=9 …) birebir aynı. Enum farkları için [ouch-sdk README](../ouch-sdk/README.md).

### 3.7 Olayların istemciye dönüşü

Yönlendirme: `OrderServer::OnOrder*` → `auth_service->GetUserConnections(event.SenderApplication())` → her bağlantıya `CreateResponse` + `setOrderResponse`. `SenderApplication` = emri gönderen MARpc kullanıcı adı (gRPC STRATEGY emrinde `application_username`). Aynı kullanıcı adıyla bağlı **bütün** bağlantılar olayı alır. Bağlantı yoksa olay log'a "Client Count: 0" yazılır ve **atılır** (tampon yok). İstemci geçmişi `AllOrdersRequest` ile tekrar çeker.

| Olay (`ResponseTypes`) | Doldurulan alanlar | Doldurulmayan / dikkat |
|------------------------|--------------------|------------------------|
| `OrderAccepted` (1) | `orderToken` (SDK token), `orderId` (BIST order id), `passThrough`, `orderBookId`, `quantity` (lot), `price` (raw int32), `account`, `strategy`, `strategyIdentifier`, `preTradeQuantity` (lot), `side` (1/2/3), `timestamp` | `timestamp` = MAOrderSDK `msg.timestamp` (❓ doğrulanmadı: birim) |
| `OrderExecuted` (2) | `orderToken`, `orderBookId`, `timestamp`, `quantity` (**bu dolumun** lotu), `price` = `lastPrice` (işlem fiyatı, raw), `matchId` | Wire'da `side`, `account`, `passThrough` alanı yok. `previousPosition`/`dailyPosition`/`totalPosition` 0. İstemci token ile eşler. |
| `OrderCanceled` (3) | `orderToken`, `orderId`, `orderBookId`, `timestamp`, `reasonCode`, `reason`, `quantity` (lot), `side` | `price` ve `matchId` gönderilmez (0). Sebep network-sdk'da: `MAHelper::getOrderFBObj` `price`'ı yazmıyor, `matchId`'ye 0 yazıyor; order-service doldursa da kaybolur ([network-sdk/wire-protokolu § 6.1](../network-sdk/wire-protokolu.md#61-encode-mahelpergetrequest-getresponse-getorderfbobj)) |
| `OrderRejected` (4) | `orderToken`, `passThrough`, `orderBookId`, `account`, `strategy`, `strategyIdentifier`, `timestamp`, `rejectCode`, `rejectReason` | Risk reddinde (§6.2) `orderToken` **boş**, `rejectCode` model varsayılanı, `timestamp` ns (`system_clock`). İstemci `passThrough` ile eşlemelidir. |
| `OrderReplaced` (5) | `previousOrderToken`, `replacementOrderToken`, `passThrough`, `orderId`, `orderBookId`, `quantity` (lot), `price` (raw), `account`, `strategy`, `strategyIdentifier`, `preTradeQuantity`, `side`, `timestamp` | — |
| `UserDisconnected` (9) | §3.8 | — |

### 3.8 `UserDisconnected` (handoff bildirimi)

Kaynak: `MAOSdkManager::TryDisconnectUser` → `OrderResponseCallBack(OnUserDisconnected)` → `OrderServer::OnUserDisconnected`. Yönlendirme `SenderApplication` ile değil **`applicationUsername`** ile yapılır (OUCH kullanıcısına bağlı uygulama kullanıcısı, ör. HFT'nin kullanıcısı).

| Alan | Anlam |
|------|-------|
| `username`, `password` | OUCH kullanıcı adı ve **düz metin şifre** (MARpc şifrelenmemiş TCP) |
| `ip`, `port` | BIST OUCH gateway adresi (`<PROD_IP>`) |
| `applicationUsername` | Hedef uygulama kullanıcısı |
| `allowedAccounts[]`, `allowedAccountsSize` | İzinli hesaplar |
| `callbackNumber`, `totalNumberOfCallbacks` | Bu bildirimin sırası / toplam bildirim sayısı |

Tetik ve bekleme mantığı: [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md). HFT tarafı: [hftsrvprod/emir-yasam-dongusu.md](../hftsrvprod/emir-yasam-dongusu.md).

### 3.9 İstemci kopunca

- `OrderServer::ConnectionClosed` → `AuthenticationService::RemoveConnection(fd)`: bağlantı kullanıcı listesinden çıkar. **Token silinmez** (token'ların süresi yoktur, process ömrü boyunca geçerlidir).
- Açık emirler **iptal edilmez** (cancel-on-disconnect yok). BIST'te yaşamaya devam eder.
- Kopukken gelen olaylar atılır (§3.7). Yeniden bağlanan istemci login olur ve `getAllOrders` ile günün olaylarını alır.

## 4. gRPC sunucusu (`OrderServiceImpl`)

### 4.1 Kimlik doğrulama

- **`Login`**: kullanıcı adı/şifre/`application` trade-data-app `DataService.Login`'e **aynen iletilir** (`DatabaseClient::Login`). Dönen token'dan `Bearer ` öneki atılıp `SetAuthToken(username, token)` ile tabloya eklenir; yanıtta token önekli hâliyle döner. Boş token veya token tabloda zaten varsa → `CANCELLED` (UNAUTHENTICATED değil).
- **`checkAuthorization`**: metadata `authorization`, `Bearer ` öneki atılır, `ValidateToken`. Başarısızsa `UNAUTHENTICATED "Unauthorized"`. `Login` dışındaki her RPC çağırır.

### 4.2 RPC'ler

| RPC | Davranış | Yanıt |
|-----|----------|-------|
| `Login` | §4.1 | `token` |
| `SendOrder(SendOrdersRequest)` | §4.3 | `OK` / `NOT_FOUND "Strategy not found!"` / `INVALID_ARGUMENT "Order type is not valid!"`. `ResponseBase` doldurulmaz. |
| `SubscribeToOrders` (server stream) | §4.4 | `stream OrdersResponse` |
| `StopSubscription` | `stream_map[requester_key] = false`; o anahtardaki **bütün** stream döngüleri çıkar. Kayıt silinmez. trade-data-app bu RPC'yi çağırmaz. | `OK` |

### 4.3 `SendOrder` dalları

Her `SendOrderRequest` için:
1. `data::models::Order` doldurulur (side 1/2/3 → `'B'/'S'/'T'`, `price`, `quantity`, `custom_data` → passThrough, TIF, regular type, protocol, `is_active`, `is_main_order`, `main_order_id`, `level_count`, `is_yip`).
2. Hesap-strateji `GetAccountStrategy(getStrategyId(type), account, strategyIdentifier, orderbook_id, application_username)`. Yoksa `GetStrategyByType` + `InsertAccountStrategyToDb` ile oluşturulur. Strateji tipi DB'de yoksa → `NOT_FOUND` ve RPC döner.
3. `event_type` × `order_type`:

| `event_type` | `order_type` | İşlem |
|--------------|--------------|-------|
| ENTER | STRATEGY | `InsertRegularOrder` → `EnterOrder` → `OrderDispatcher::SendOrder` (risk + hemen gönderim, §6.2). `SenderApplication = application_username`. |
| ENTER | MORNING / OPENING / EVENING | Yeni DB satır token'ı (`OrderUtility::GenerateToken`; OUCH token'ı değildir) → `InsertCollectiveOrder` → tipe göre üye vektöre eklenir |
| CANCEL | MORNING/OPENING/EVENING, `is_main_order=true` | `RemoveCollectiveOrder` → `OrderService::RemoveOrder(order_id, ...)`. `false` → `INVALID_ARGUMENT`. |
| CANCEL | diğer (STRATEGY dahil, ana olmayan) | **Hiçbir şey yapılmaz** |
| REPLACE | toplu tip | `is_main_order` ise önce `RemoveCollectiveOrder`, sonra yeni token ile `InsertCollectiveOrder` (sil + yeniden ekle) |

4. Döngü sonunda boş olmayan her vektör: `BulkInsertMorningOrder` / `Opening` / `Evening` (DB) → `PublishCollectiveOrders` (yalnız ana emirler `order_queue`'ya `OrdersCommon` olarak) → vektör temizlenir.

Toplu emirlerin ne zaman gönderildiği: [toplu-emirler.md](toplu-emirler.md). trade-data-app pratikte yalnızca toplu tipleri buraya gönderir; STRATEGY emirlerini motorlara yollar ([api.md § 7](../trade-data-app/api.md)). STRATEGY dalı kodda vardır ama trade-data-app'ten kullanılmıyor.

### 4.4 `SubscribeToOrders` stream davranışı

1. Auth → `stream_map[requester_key] = true`.
2. İstenen her `order_types` için geçmiş toplanır:
   - `STRATEGY`: her `application_usernames` için `FetchUserOrders(kOuch)` + `FetchUserOrders(kFix)` (kullanıcı içinde zamana göre sıralı). Ardından `OrderServiceImpl::On*` callback'leri dispatcher'a **bağlanır** (`BindAccepted`, `Bind`×5). Canlı strateji olayları ancak bu bağlamadan sonra kuyruğa girer.
   - `MORNING` / `EVENING` / `OPENING`: `OrderService::Get*Orders(kOuch)` + `(kFix)` → `ConvertCollectiveOrder(..., kOrderAccepted, ...)`.
   - Geçmiş **tek** `OrdersResponse` olarak yazılır (boşsa yazılmaz).
3. Canlı döngü: `while(true)` içinde `stream_map[key]` true olduğu sürece `order_queue.tryPop` (bekleme yok, busy-spin). Olayın tipi (`RepeatableOrderType` → `OrderType`; SDK olayları `kNonRepeatable` → STRATEGY) istenen tiplerde değilse olay **atılır**. Değilse tek elemanlı `OrdersResponse` yazılır. `context->IsCancelled()` ve `Write` dönüşü kontrol edilmez.

`order_queue` **bütün stream'ler için tektir** (`ThreadSafeQueue`, sınırsız): her olay yalnızca onu ilk çeken stream'e gider.

### 4.5 gRPC wire alanları ve ölçek

| Alan | Tip | Birim / not |
|------|-----|-------------|
| `SendOrderRequest.price`, `expected_price` | uint64 | raw (TL × 10^decimalCount); trade-data-app ITCH ham tamsayısını gönderir. STRATEGY dalında `EnterOrder` int32'ye daraltılır. `expected_price` order-service'te okunmaz. |
| `SendOrderRequest.quantity` | uint64 | lot |
| `SendOrderRequest.order_id` | uint64 | DB emir id'si (yalnız CANCEL/REPLACE'te) |
| `Order.*.common.price/quantity` | uint64 | raw / lot |
| `OrderAccepted.price`, `OrderExecuted.price` | uint64 | raw. Executed'da işlem fiyatı; `excQty` = dolum lotu. `initialQty`/`remainingQty` doldurulmaz. |
| `OrderCanceled.price` | uint32 | raw (registry'deki emir fiyatı) |
| `OrderReplaced.price`, `previous_price` | int32 | raw |
| `common.timestamp` | uint64 | SDK olaylarında `msg.timestamp` (❓ birim); risk reddinde ns epoch |
| `common.side` | enum | **İki biçim:** toplu emir `common` mesajlarında 1/2/3 (`getSideInfoResponse`); strateji olaylarında (accepted/executed/canceled/rejected/replaced) iç enum doğrudan cast edilir → **66 ('B') / 83 ('S') / 84 ('T')**. trade-data-app `normalizeSide` ikisini de kabul ediyor. |
| `common.latency_*_ns` | uint64 | ns; MAOrderSDK gecikme ölçümleri |
| `common.internal_ouch` | string | Emri taşıyan OUCH/FIX kullanıcı adı (`SenderUsername`) |
| `common.application_type` | enum | Strateji adından türetilir (`ConvertStrategyToApplication`); tanınmayan → `OUCH` |
| `common.order_type` | enum | Strateji olaylarında sabit `STRATEGY` |

## 5. Proto dosyaları — isimler ters

| Dosya | `package` | Rol |
|-------|-----------|-----|
| `Service/servicemodel/order-service.proto` + `common.proto` | `clientmodels` (go_package `trade-data-app/pkg/gui/clientmodels`) | order-service'in **sunduğu** `OrderService` |
| `Service/clientmodel/ouch-data.proto` | `servicemodels` (go_package `trade-data-app/pkg/servicemodels`) | order-service'in **istemci** olduğu trade-data-app `DataService` (`Login`, `GetOuchUsers`, `GetFixUsers`, `UpdateOrderUserPassword`, `GetStrategies`, `GetInstruments`, `GetPositions`, `SetPosition`, `GetOrders`, `SetOrders`, `DeleteOrders`, `SetAccountStrategy`, `GetAccountStrategies`, `GetAllIndices`, `GetIndiceInstruments`). Kullanımı: [kalicilik-ve-config.md](kalicilik-ve-config.md). |
| `Service/limit/*.proto` | — | Risk servisi istemcisi ([risk.md](risk.md)). `buf.work.yaml` yalnızca `clientmodel` ve `servicemodel`'i listeler. |

Dizin adı ("clientmodel" / "servicemodel") ile proto paket adı birbirinin tersidir. İkisi de trade-data-app'teki kopyalarla aynı tutulmalıdır.

## 6. `OrderDispatcher` ve emrin yolu

### 6.1 Manager seçimi

- Constructor: `protocols` listesinde `ouch` veya `fix` varsa **tek** bir `MAOSdkManager` oluşturulur ve `order_managers[kOuch]`'a konur. Ayrı FIX manager yoktur (issue #402).
- `manager_for(protocol)`: `kFix` → `kOuch` manager'ına düşer. `kUnknown` → `nullptr`.
- `FetchUserOrders(kFix, ...)` bilerek fallback yapmaz ve boş döner. FIX emirleri zaten `kOuch` listesindedir.
- `TriggerOuchDisconnect` → `MAOSdkManager::TriggerOuchDisconnect` (dynamic_cast).

### 6.2 Enter: girişten BIST'e

1. Giriş: `OrderServer::RequestReceived` (MARpc, bağlantının `processCallback` thread'i) veya `OrderServiceImpl::InsertRegularOrder` (gRPC thread'i). Toplu emirler bu yoldan geçmez ([toplu-emirler.md](toplu-emirler.md)).
2. `OrderDispatcher::SendOrder(EnterOrder)` → `manager_for(protocol)`. `nullptr` → log, düşüş.
3. `risk_manager->checkEnterOrder(order, desc)` ([risk.md](risk.md)).
   - Ret → `OrderManager::sendOrderRejectedToApplication`: sentetik `OrderRejected` (token yok, ns timestamp, `passThrough`, hesap-strateji, fiyat, miktar) → `OrderResponseCallBack(OnOrderRejected)` → MARpc istemcisine ve (bağlıysa) gRPC kuyruğuna. Emir BIST'e gitmez; `rejected_orders`'a yazılmaz.
4. `MAOSdkManager::SendOrderAsync(EnterOrder)`. İsmine rağmen **senkron**, çağıran thread'de çalışır:
   - Token boşaltılır, `offhours` bayrağı ve gönderim zamanı set edilir.
   - Enstrüman `InstrumentService::GetInstrumentById`; yoksa log + düşüş.
   - Hesap `user_accounts`; yoksa log + düşüş. Pay piyasasında fon hesabı ise `ClientAccount = AgencyFundCode`, `ExchangeInfo = hesap adı`, `ClientCategory = hesap tipi`. VİOP'ta `ClientAccount = hesap adı`.
   - Kullanıcı tercihi: FIX ise `getNextFixClient(market, partition, account)` (bulunamazsa log + düşüş). İki pazarda tanımlı hesapta `NextClientForAccount(hesap+pazar)` round-robin. Diğer durumlarda seçimi MAOrderSDK yapar.
   - `SubmitEnterOrder` → `ToSdkOrder` (fiyat raw aynen; ARBITRAGE/VWAP/FUND_TRACKER için `no_split`) → `sdk_->enterOrder`. Token atama callback'i her (bölünmüş) çocuk için `entered_orders[token]`'a kayıt açar ve protokolü gerçek kullanıcıdan belirler.
   - SDK sahiplenmeyen çocuk (yerel ret) kayıttan silinir. Gönderilen her çocuk `InsertOrderToDatabaseAsync` ile DB kuyruğuna girer.
5. Bölme, token, OUCH/FIX gönderimi MAOrderSDK içindedir: [maordersdk](../maordersdk/README.md), [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md).

### 6.3 Cancel / Replace

`OrderDispatcher::SendOrder(Cancel|Replace)`: `order_protocols` haritasında (accept/replace olaylarında doldurulur, hiç silinmez) token aranır. Bulunamazsa istekteki `protocolType` kullanılır (restart sonrası geri yüklenen emirler haritada yoktur). İkisi de `kUnknown` ise log + düşüş. Her iki protokol aynı manager'a gittiği için bu harita pratikte yalnızca `kUnknown` ayrımı yapar. Risk kontrolü dispatcher'da yalnız Enter için yapılır. Replace'in risk kontrolü `MAOSdkManager` içindedir (§3.4), Cancel'da risk yoktur.

### 6.4 Olayın geri dönüşü

1. MAOrderSDK callback'i (`ConfigureSdkCallbacks` içindeki `onAccepted` / `onRejected` / `onExecuted` / `onCanceled` / `onReplaced`) `sdk_callback_mutex_` altında çalışır. Token'la `entered_orders`'tan bağlam alınır; kayıt yoksa olay **atılır** (WARN). Replay tekrarları burada elenir (ayrıntı [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md)).
2. `OrderManager::OrderResponseCallBack(type, resp)` → o tipe bağlı her callback sırayla:
   - `OrderDispatcher` lambda'sı (dynamic_cast; accepted/replaced'te `order_protocols`'a yazar) → `OrderServer::OnOrder*` (MARpc, §3.7).
   - SubscribeToOrders'ın bağladığı her set → `OrderServiceImpl::OnOrder*` → `order_queue.push` (gRPC, §4.4).
3. Ardından `risk_manager->OnOrder*` (rezervasyon güncellemesi), bellek kaydı (`accepted_orders` vb.), executed'da pozisyon yazımı ([kalicilik-ve-config.md](kalicilik-ve-config.md)).

Bağlama sırası: `OrderServer` constructor'ı (açılışta bir kez), sonra her STRATEGY içeren `SubscribeToOrders`. Callback vektörleri (`OnOrderAccepted` vb.) kilitsiz `std::vector`'dür.

## 7. Thread ve kilit modeli

| Thread | Ne çalıştırır | Not |
|--------|---------------|-----|
| main | `Start` → `server->Wait()` | Sonsuza kadar bloklu |
| MARpc accept ×2 (TCP, Unix) + heartbeat checker | network-sdk | Checker `yield` ile döner |
| MARpc bağlantı başına ×2 | `receiveMessage`, `processCallback` → `RequestReceived` | Busy-spin. Bir bağlantının istekleri **sırayla** işlenir; Enter'da risk + SDK gönderimi bu thread'de senkron. AccountStrategy SET'te trade-data-app gRPC çağrısı da bu thread'i bloklar. |
| MARpc detached | `AllOrdersRequest`, AccountStrategy GET | İstek başına bir thread |
| gRPC senkron havuz | `Login`, `SendOrder`, `StopSubscription`, `SubscribeToOrders` | Her açık stream bir thread'i sürekli meşgul eder (busy-spin) |
| MAOrderSDK callback thread(ler)i | Olaylar → `OrderServer::On*` + `OrderServiceImpl::On*` + risk | `sdk_callback_mutex_` altında. ❓ doğrulanmadı: SDK'nın kaç callback thread'i olduğu ([maordersdk](../maordersdk/README.md)). |
| Detached | Handoff zamanlayıcısı (§2 adım 6), `OrderManager` DB thread'leri, `offhours_invertor`, toplu emir thread'leri | [toplu-emirler.md](toplu-emirler.md) |

Kilitler:
- `AuthenticationService`: `user_connections` → `user_connections_mutex` (shared). `token_username` → **kilitsiz**.
- `OrderDispatcher::order_protocols` → `order_protocols_mtx`.
- `OrderServiceImpl`: `stream_map` → `stream_mtx` (shared). `morningOrders`/`openingOrders`/`eveningOrders` → **kilitsiz**.
- `MATCPServer::setResponse` → `responseMtx` (serileştirme global `MAHelper` FlatBuffers builder'ı ile yapılır). `sendingMessageList`/`isRunning` map'lerinin okuma tarafı kilitsiz.
- `MAOSdkManager`: `enter_order_mtx`, `reject_order_mtx`, `replace_order_mtx`, `sdk_callback_mutex_`. `FetchUserOrders` kilitler altında ham pointer listesi döner, pointer'lar kilit bırakıldıktan sonra kullanılır (nesneler `unique_ptr` ile tutulur ve silinmez).
- `AccountStrategyService::account_strategies`: `InsertAccountStrategyToDb` ekler, `GetAccountStrategy` okur; ikisi de kilitsiz (`strategiesMtx` yalnız `strategies` için).

## 8. Şüpheli

Kod referanslarıyla. "bug?" = koddan çıkarım, canlıda doğrulanmadı. "doğrula" = davranış belirsiz.

1. **bug?** Başarısız MARpc login boş token'ı tabloya yazar. `AuthenticationService::Login`, `db_client->Login` boş dönse de `token_username.insert({"", username})` yapar ve bağlantıyı kullanıcı listesine ekler. Sonrasında `authToken` boş gelen istek `ValidateToken("")` ile bu kullanıcı adına yetkili sayılır.
2. **bug?** `token_username` kilitsiz `std::map`; MARpc `Login` (bağlantı thread'leri), gRPC `Login` ve bütün `ValidateToken` çağrıları eşzamanlı erişir (`AuthenticationService`).
3. **bug** AccountStrategy GET thread'i `[&]` ile yakalar (`OrderServer::RequestReceived`, `TYPE_AccountStrategyRequest`): `strategyRequest` ve `connectionId` yerel değişkenlerine referans detached thread'de handler döndükten sonra kullanılır → dangling; yanıt yanlış bağlantıya gidebilir veya çökme. Aynı bloktaki `authToken` kopyası kullanılmıyor.
4. **bug** `OrderServer::CreateResponse` `OrderReplaced` dalı: `replacement_chr[prev_token.size()] = '\0'`. Yeni token eskisinden kısaysa taşma, uzunsa kesilme. ❓ SDK token'ları sabit uzunluktaysa pratikte zararsız.
5. **bug?** İstemciye hiç yanıt gitmeyen sessiz düşüşler: Enter'da geçersiz token, hesap-strateji bulunamaması, `protocolType=0`, enstrüman/hesap/FIX kullanıcısı bulunamaması (`MAOSdkManager::SendOrderAsync`). Replace'te geçersiz token ve `entered_orders`'ta olmayan token. Cancel'da SDK `false`. İstemci emri sonsuza kadar "gönderildi" sanabilir. doğrula: ouch-sdk/HFT/AlgoProd'da zaman aşımı var mı.
6. **bug?** MARpc `timeInForce` GTC(4) ve AT_CROSSING(6) sessizce DAY'e çevrilir (`RequestReceived` Enter dalı). gRPC STRATEGY dalı ise sayısal cast ile hepsini taşır.
7. **bug?** Her STRATEGY içeren `SubscribeToOrders` çağrısı callback'leri yeniden bağlar (`OrderServiceImpl::SubscribeToOrders`) ve bağlamayı hiç kaldırmaz. trade-data-app her yeniden bağlanmada abone olduğundan her olay `order_queue`'ya N kez girer. Bağlama, SDK thread'leri vektörü dolaşırken kilitsiz `push_back` yapar (`OrderManager::Bind`) → veri yarışı.
8. **bug?** Tek paylaşılan `order_queue` + `IsCancelled` kontrolü olmayan döngü: kopan istemcinin stream döngüsü sonlanmaz (trade-data-app `StopSubscription` çağırmaz) ve olayları tüketmeye devam eder. Yeni stream ile olaylar paylaşılır, bir kısmı GUI'ye hiç ulaşmaz. İstenmeyen tipteki olay da tüketilip atılır.
9. **doğrula** STRATEGY aboneliği olmadan strateji olayları gRPC kuyruğuna hiç girmez. Toplu emir yayınları (`PublishCollectiveOrders`) ise abone yokken de `order_queue`'ya birikir (sınırsız).
10. **bug?** `OrderServiceImpl::SendOrder` paylaşılan üye vektörleri (`morningOrders` vb.) kilitsiz kullanır; eşzamanlı iki `SendOrder` yarışır. Döngü ortasında `NOT_FOUND`/`INVALID_ARGUMENT` ile dönüşte önceki emirler vektörde kalır ve **sonraki** `SendOrder` çağrısında DB'ye yazılıp gönderilir.
11. **doğrula** gRPC strateji olaylarında `side` 66/83/84, toplu `common`'da 1/2/3 (§4.5). Tutarsız; trade-data-app tolere ediyor.
12. **bug?** `UserDisconnected` gRPC kuyruğuna da girer (`OrderServiceImpl::OnUserDisconnected`). `getOrderResponseItem` bu tipi tanımaz ve boş `Order` mesajı STRATEGY abonesine yazılır.
13. **bug?** Kapanış: sinyal handler'ı `app.Stop()` çağırır (async-signal-safe değil) ama ana thread `grpc::Server::Wait()`'te kalır, gRPC `Shutdown` çağrılmaz. doğrula: SIGTERM'de process'in kendiliğinden çıkıp çıkmadığı (systemd SIGKILL'e kadar bekleyebilir).
14. **bug?** Bellek sızıntısı: network-sdk `getRequestResult` her isteği `new` ile üretir, order-service silmez. `CreateResponse` her olayda `new` ile struct ve `char*` kopyaları üretir. `setResponse` serileştirir ama serbest bırakmaz.
15. **doğrula** (network-sdk) `[byte]` alanları (`strategy_identifier`, `order_token`, Replace `pass_through`, `authToken`) `Data()` ile C string olarak okunur. FlatBuffers byte vektörlerinde sonlandırıcı `\0` garanti değildir (`MAHelper::getRequestResult`).
16. **doğrula** (network-sdk) 5 bağlantı sınırını aşan bağlantı kapatılmaz. fd yeniden kullanıldığında eski bağlantının `sendingMessageList[fd]` kuyruğunda kalan mesajlar yeni bağlantıya gidebilir. Map'ler kilitsiz okunur (`MATCPServer`).
17. **bug?** AccountStrategy SET'te `GetStrategyById` bilinmeyen tipte `StrategyNotFoundException` atar ve yakalanmaz → MARpc thread'inde `std::terminate`. DB hatasında da yanıt 200 döner.
18. **doğrula** MARpc yolunda `StrategyType` enum değeri = DB strateji id'si varsayımı (§3.6).
19. **Gizli bilgi sızıntısı:** MARpc login'de şifre `printf` ile stdout'a basılır (`RequestReceived`). `DatabaseClient::Login` token'ı log'a ve stdout'a yazar. `UserDisconnected` OUCH şifresini düz metin taşır (bu kısmı tasarım gereği).
20. **doğrula** `db_client->Connect()` dönüşü yok sayılır (`OrderServiceApplication::Start`). trade-data-app kapalıyken açılış ne yapar: [kalicilik-ve-config.md](kalicilik-ve-config.md).
21. **doğrula** Birden çok `type: morning` girdisi varsa her biri için ayrı handoff zamanlayıcısı kurulur. Sabah akışının kendi tetiği de ayrıca çalışır. Tekrar tetiklemenin idempotent olup olmadığı: [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md).
22. Küçük: `order_protocols` sınırsız büyür. `OrderServiceImpl::Login` aynı token ikinci kez gelirse `CANCELLED` döner. MARpc `LoginResponse.status` hep false. `main`'deki versiyon sabit `"20210210.0850"` ve log satırı mod yerine `app_name` basar.
