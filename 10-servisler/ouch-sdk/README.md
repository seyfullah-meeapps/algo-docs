---
kapsam: ouch-sdk (libouchSDK) — order-service'in MARpc istemci SDK'sı; public API, model sınıfları ve wire eşlemesi, callback thread'i ve sahiplik, bağlantı yaşam döngüsü, enum farkları, build/CI
kaynak:
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: order-service
    branch: development
    commit: b86c0cf
dogrulama: 2026-10-22
durum: taslak
---

# ouch-sdk (`libouchSDK`)

Kod: `include/OrderStreamClient.h` (public API), `OrderStreamClient.cpp` (tek translation unit), `include/models/*.h` (domain sınıfları), `convertors/*.h` (domain ⇄ MARpc struct, kurulmaz/private). Namespace'ler: `ouchSDK`, `ouchSDK::models`, `ouchSDK::enums`, `ouchSDK::convertors`.

## 1. Görev ve isim karışıklığı

- İsim yanıltıcıdır: ouch-sdk **BIST OUCH'a bağlanmaz**. network-sdk (`libMARpc`) üzerinden **order-service'in MARpc portuna** (tipik 8000) bağlanan ince bir adaptördür. Kendi TCP/FlatBuffers kodu yoktur.
- BIST'e doğrudan bağlanan kütüphane [MAOrderSDK](../maordersdk/README.md)'dır.
- Sunucu tarafı order-service `OrderServer.*`: istek tipleri, wire alanları, olay yönlendirmesi → [order-service/arayuzler.md § 3](../order-service/arayuzler.md#3-marpc-sunucusu-orderserver). Burada tekrar edilmez.
- Taşıma katmanı (framing, heartbeat, thread'ler) → [network-sdk/README.md](../network-sdk/README.md). Bu dosya yalnız ouch-sdk'nın gördüğü yüzünü anlatır (§3.2, §5).

| Kullanan | Kod | Ne için |
|----------|-----|---------|
| HftSrvProd | `src/Clients/OuchManager.*` | Handoff öncesi yedek emir yolu ("OS yolu"), strateji kaydı (`insertStrategy`), restart sonrası `getAllOrders`, handoff bildirimi (`orderUserDisconnected`). Ayrıntı: [hftsrvprod/emir-yasam-dongusu.md](../hftsrvprod/emir-yasam-dongusu.md#os-yolu-eşdeğerleri-ouchmanagercpp-ouchsdkorder-serbest-fonksiyonları), [§ 4 Handoff](../hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı). |
| AlgorithmicTrading (AlgoProd) | `algoSrc/Managers/OuchManager.*` | **Bütün emirler**, strateji kaydı/okuma, açılışta `getAllOrders`. `orderUserDisconnected` boş (yalnız `cout`). Ayrıntı: [algorithmic-trading/emir-yolu.md](../algorithmic-trading/emir-yolu.md). |

Ek kullanım: HftSrvProd `ouchSDK::models::Order*` sınıflarını **MAOrderSDK yolunda da** iç olay tipi olarak kullanır (`src/Messages/OngoingMessages/Transaction/MsgConvert.*`, `HftConvert::fromSdk` → `shared_ptr<ouchSDK::models::OrderAccepted>` vb.). Model sınıflarındaki bir değişiklik HFT'nin iki yolunu da etkiler.

## 2. Katmanlar

| Katman | Yer | İş |
|--------|-----|----|
| Public API | `include/OrderStreamClient.h` | Serbest fonksiyonlar (sınıf yok). Process başına tek oturum: bütün durum `OrderStreamClient.cpp`'deki `static` değişkenlerde. |
| Durum | `OrderStreamClient.cpp` | `authToken` (string), `loginPromise`, `allOrdersPromise`, `getStrategiesPromise`, `addStrategyPromise`, `addStrategyPromiseMtx`, `getStrategyPromiseMtx`, `networkMap` + `networkMapMtx` |
| Dağıtıcı | `OrderStreamClient.cpp` `handleIncomingMessage` | network-sdk response delegate'i; `responseType`'a göre convertor + kullanıcı callback'i ya da promise |
| Convertor | `convertors/*Convertor.h` | Giden: domain → `new *Request{}` + `malloc`'lu C string'ler. Gelen: MARpc struct → `new ouchSDK::models::*` |
| Taşıma | network-sdk `Public/MAOrderClient.h` | `startOrderClient`, `setResponseDelegate`, `sendOrderRequest`, `closeClientConnection` (`extern "C"`, tek global `MATCPClient`) |

`networkMap`: her gelen yanıtın struct kopyası `ResponseTypes` anahtarıyla saklanır (tip başına son yanıt). Hiçbir yerde **okunmaz**; yalnız `insertStrategyInfo` `TYPE_AccountStrategyResponse` kaydını siler. Kopya sığdır (`char*`'lar FlatBuffers tamponunu gösterir, tampon sonra serbest kalır).

## 3. Public API (`include/OrderStreamClient.h`)

### 3.1 Fonksiyonlar

| İmza | Ne yapar | Senkron mu | Dönüş | network-sdk çağrısı |
|------|----------|------------|-------|---------------------|
| `void startOuchStreaming(std::string& ip, std::string& port)` | `startOrderClient(ip.c_str(), stoi(port))`, ardından `setResponseDelegate(&handleIncomingMessage)` | Connect çağıran thread'de bloklar; hata **sessiz** (§5.1) | — | `startOrderClient`, `setResponseDelegate` |
| `bool login(std::string& userName, std::string& password, enums::Application app)` | `LoginRequest` gönderir, `loginPromise`'ı bekler. 200 → `authToken` saklanır, `true`. 401/403/diğer → `false`. | **Bloklar, timeout yok** | `true` = token alındı | `sendOrderRequest` |
| `std::vector<models::StrategyInfo> getStrategyInfo()` | `AccountStrategyRequest{OPERATION_GET}`; `getStrategyPromiseMtx` altında bekler; yanıtı `StrategyInfoConvertor` ile vektöre çevirir | **Bloklar, timeout yok** | Kullanıcının bütün hesap-strateji kayıtları. 401'de boş vektör. | `sendOrderRequest` |
| `bool insertStrategyInfo(models::StrategyInfo&)` | `AccountStrategyRequest{OPERATION_SET, accountStrategy}`; `addStrategyPromiseMtx` altında bekler | **Bloklar, timeout yok** | `baseResponse.status`. order-service SET'te DB sonucundan bağımsız **hep `true`** döner; yalnız geçersiz token'da `false` ([arayuzler § 3.5](../order-service/arayuzler.md#35-strateji-kaydı-accountstrategyrequest)). | `sendOrderRequest` |
| `void enterOrder(models::EnterOrder&)` | `toString()`'i `std::cout`'a basar, `EnterOrderConvertor` → `authToken` eklenir → gönderilir | Asenkron (kuyruğa koyar) | — (sonuç callback ile) | `sendOrderRequest` |
| `void replaceOrder(models::ReplaceOrder&)` | `ReplaceOrderConvertor` → gönderir | Asenkron | — | `sendOrderRequest` |
| `void cancelOrder(models::CancelOrder&)` | `CancelOrderConvertor` → gönderir | Asenkron | — | `sendOrderRequest` |
| `void getAllOrders()` | `AllOrdersRequest{OPERATION_GET}`; `allOrdersPromise`'ı bekler. Yanıttaki her olay **callback thread'inde** ilgili `order*` callback'inden geçirilir, sonra promise set edilir. | **Bloklar, timeout yok**. Dönünce replay callback'lerinin hepsi çalışmış olur. | — | `sendOrderRequest` |
| `void stopOuchStreaming()` | `closeClientConnection()` | Asenkron (`"C"` çerçevesini kuyruğa koyar) | — | `closeClientConnection` |
| `order*` callback'leri (6 adet) | Uygulama tanımlar (§4) | — | — | — |

Header'daki yorumlar `Username`/`Password`'ün "MeeApps tarafından verildiğini" söyler: bu kullanıcı order-service/trade-data-app uygulama kullanıcısıdır, OUCH kullanıcısı değildir.

### 3.2 Giden yolun ayrıntısı

1. Convertor `new XRequest{}` (value-init, bütün alanlar 0) kurar, string alanlar için `malloc` + `strcpy` yapar.
2. `setMetadata` → `baseRequest.authToken = authToken.c_str()` (static string'in pointer'ı). `login`'den önce boş string.
3. `sendOrderRequest` → `MATCPClient::sendMessage`: `builderMutex` (spin `try_lock`) altında FlatBuffers'a **senkron** serileştirir, bayt dizisini `sendingMessageList` (moodycamel `ConcurrentQueue`) kuyruğuna koyar. Request struct'ı bu noktadan sonra okunmaz.
4. Asıl `send()`, network-sdk recv thread'inin döngüsünde yapılır: her iterasyonda kuyruktan **bir** mesaj.
5. Request struct'ları ve `malloc`'lu string'ler **hiç serbest bırakılmaz** (her istekte sızıntı; bug?). `login` dahil.

Sonuç: `enterOrder`/`replaceOrder`/`cancelOrder` dönüşü yalnız "kuyruğa kondu" demektir. Bağlantı kopuksa da sessizce döner (§5.3).

### 3.3 Thread-safety

| Çağrı | Durum |
|-------|-------|
| `enterOrder` / `replaceOrder` / `cancelOrder` | Çok thread'den çağrılabilir (serileştirme `builderMutex` ile). Farklı thread'lerden gelen istekler arasında gönderim sırası garanti değil: moodycamel kuyruğu yalnız **aynı üretici thread** içinde FIFO'dur. ❓ doğrulanmadı: pratikte yeniden sıralanma görülüp görülmediği. |
| `getStrategyInfo`, `insertStrategyInfo` | Kendi mutex'leriyle kendi aralarında serileşir. GET ve SET aynı anda bekleyebilir (yanıt `operationType` ile ayrılır). |
| `login`, `getAllOrders` | **Mutex yok.** İki thread aynı anda çağırırsa ikinci çağrı promise'i yeniden atar; ilk bekleyen `std::future_error (broken_promise)` alır. Çağıran serileştirmeli. HFT bunu `OuchManager::ouchSDKCallMutex` ile yapar. |
| `login` ↔ emir çağrıları | `authToken` yazımı kilitsiz; login bitmeden emir gönderilmemeli. |
| Herhangi bir bloklayan çağrı **callback içinden** | **Deadlock**: promise'i set edecek thread çağıranın kendisidir (§4.1). |

## 4. Callback'ler

### 4.1 Tanım, thread, sıra

- Header'da altı serbest fonksiyon **bildirilir, tanımlanmaz**: `orderAccepted`, `orderRejected`, `orderExecuted`, `orderCanceled`, `orderReplaced`, `orderUserDisconnected`. Uygulama `void ouchSDK::orderAccepted(ouchSDK::models::OrderAccepted*) {...}` şeklinde **link zamanında** sağlar (HFT: `src/Clients/OuchManager.cpp`, Algo: `algoSrc/Managers/OuchManager.cpp`). Kullanılmayan callback'e de boş gövde gerekir; yoksa link hatası.
- **Thread:** network-sdk `MATCPClient::processCallback` thread'i (`callbackTask`). Recv thread'i (`receiveTask`) yalnız bayt toplar ve gönderim yapar; ayrıştırma ve delegate çağrısı bu ayrı thread'dedir. Bütün callback'ler, `getAllOrders` replay'i ve login/strateji yanıtları **aynı tek thread**'de sırayla çalışır.
- **Sıra:** tek bağlantı + tek callback thread → olaylar order-service'in gönderdiği sırayla gelir. Callback dönmeden bir sonraki çerçeve işlenmez.
- **Bloklamanın etkisi:** callback içinde geçen süre boyunca diğer bütün olaylar ve `LoginResponse` / `AccountStrategyResponse` / `AllOrdersResponse` bekler. Diğer thread'lerde `insertStrategyInfo` / `getStrategyInfo` / `getAllOrders` bekleyenler de uzar. Örnek: HFT `orderUserDisconnected` içinde `connectUser` + ≤10 s retry uykusu (HFT Şüpheli 5).
- Callback'ten çıkan istisna `std::thread` sınırında yakalanmaz → `std::terminate`.
- `processCallback` `while(true)` + `try_dequeue` busy-spin döngüsüdür (yield yok): process ömrü boyunca bir çekirdeği tüketir. ❓ doğrulanmadı: prod'da çekirdek etkisinin ölçüldüğü.

### 4.2 Sahiplik

- Her olay için convertor `new ouchSDK::models::X{...}` üretir ve ham pointer'ı geçirir. ouch-sdk bu nesneyi **saklamaz ve silmez**. Pointer callback'ten sonra da geçerlidir; silmek uygulamanın işidir.
- HFT ve AlgoProd nesneyi kendi tiplerine kopyalayıp **silmez** → olay başına sızıntı (bug?, küçük nesneler).
- Domain nesnesi string'leri `std::string` olarak kopyalar; MARpc struct'ının `char*`'ları callback'ten sonra geçersizdir (FlatBuffers tamponu `processCallback` iterasyonu sonunda yok olur).

### 4.3 `getAllOrders` replay'i

`AllOrdersResponse.orders[]` (≤100000 slot, order-service en çok 99980 doldurur) içindeki her olay tipine göre aynı callback çağrılır. Replay ile canlı olay ayırt edilemez: modelde bayrak yoktur. Uygulama tekrarları kendisi eler (HFT: `addAcceptedOrder` `try_emplace`, `claimGlobalAcceptedToken`).

## 5. Bağlantı yaşam döngüsü

### 5.1 Açılış

Sıra: `startOuchStreaming` → `login` → (`getStrategyInfo` / `insertStrategyInfo`) → `getAllOrders` → emirler.

- `ip == "localhost"` (network-sdk `UNIX_SOCKET_ADDR`) ise TCP yerine Unix soket `/workingDirectory/sock/mysocket` açılır. Diğer değerler `inet_pton(AF_INET)` ile çözülür: **yalnız IPv4 literal**, hostname çözülmez.
- `port` `stoi` ile çevrilir: boş/sayısal olmayan değer `std::invalid_argument` fırlatır.
- TCP: `connect` (bloklayan), sonra `O_NONBLOCK` + `TCP_NODELAY`; recv, callback ve heartbeat (3 s) thread'leri başlar (detached).
- **Connect başarısızsa** `connectToServer` sessizce döner: log yok, thread yok, uygulamaya hata yok. Ardından `login` isteği kuyrukta kalır ve `login` **sonsuza kadar bloklar**. HFT'de bu `OuchManager` yapıcısında olur (açılış asılı kalır); `"Failed at ouch server login!"` yalnız 401'de fırlar.
- `setResponseDelegate`, thread'ler başladıktan **sonra** çağrılır. `MATCPClient::callback` üyesi yapıcıda ilklenmez. Login'den önce sunucu bir şey göndermediği için pratikte sorun çıkmaz (❓ doğrulanmadı: hiçbir sürümde sunucunun login öncesi mesaj göndermediği).

### 5.2 Login ve `Application`

| `ouchSDK::enums::Application` | Değer | order-service'te |
|-------------------------------|-------|------------------|
| `APP_UNKNOWN` | 0 | `APP_UNKNOWN` |
| `APP_HFT` | 1 | `HFT` (HftSrvProd kullanır) |
| `AlgoTrading` | 2 | `AlgoTrading` (AlgoProd kullanır) |
| `OUCH` | 3 | **`APP_UNKNOWN`'a düşer** (`OrderServer::RequestReceived`). ❓ doğrulanmadı: trade-data-app'in bu login'i kabul edip etmediği. |

- Değer `(Application)` cast ile network-sdk enum'una geçer (sayılar aynı).
- order-service yalnız 200/401 üretir. 403 dalı ölü koddur.
- Token'ın süresi yoktur. Aynı uygulama kullanıcısıyla bağlı **bütün** bağlantılar o kullanıcının olaylarını alır ([arayuzler § 3.7](../order-service/arayuzler.md#37-olayların-istemciye-dönüşü)).
- Handoff bildirimi `applicationUsername` ile yönlendirilir: HFT'nin `ouchUserName` config'i order-service'te OUCH kullanıcısına bağlı uygulama kullanıcısı olmalıdır ([hftsrvprod/config.md](../hftsrvprod/config.md)).

### 5.3 Kopma ve yeniden bağlanma

- **Otomatik yeniden bağlanma yok.** ouch-sdk'da da network-sdk istemcisinde de reconnect kodu yoktur.
- **Uygulamaya bildirim yok.** Kopma callback'i yoktur. `orderUserDisconnected` bir kopma bildirimi **değildir** (§6.8).
- Recv döngüsü yalnız `errno` EAGAIN/EWOULDBLOCK/0 dışına çıkınca biter (`" [Client] Socket closed because of state:"` + `" [Client] Connection Closed With Server"` log'u). Karşı taraf düzgün kapatırsa (`recv` → 0) `errno` değişmez ve döngü dönmeye devam eder; kopma algılanmaz. Gönderimler `" Sending Failed"` basar. Ayrıntı: [network-sdk](../network-sdk/README.md).
- Kopukken: emir çağrıları sessizce kuyruğa yazar, bloklayan çağrılar sonsuza kadar bekler. order-service tarafında açık emirler iptal edilmez, kopukken gelen olaylar atılır ([arayuzler § 3.9](../order-service/arayuzler.md)).
- Süreç içinde ikinci `startOuchStreaming`: global `tcpClient` `shared_ptr`'ı değişir, eski `MATCPClient` yok edilir. Ama detached thread'leri hâlâ eski `this`'i kullanır → UB (bug?). Pratikte yeniden bağlanma = **process restart** + `login` + `getAllOrders`. HftSrvProd ve AlgoProd da böyle yapar.
- order-service 15 s heartbeat görmezse bağlantıyı düşürür (istemci 3 s'de bir gönderir).

### 5.4 Kapanış

- `stopOuchStreaming` → `"C"` gövdeli çerçeveyi gönderim kuyruğuna koyar ve döner. Sunucu bunu görünce bağlantıyı kapatır. İstemci thread'leri durmaz.
- Gönderim recv thread'inde olduğundan process hemen çıkarsa `"C"` gitmeyebilir. Sunucu 15 s sonra heartbeat timeout ile temizler.
- `startOuchStreaming` hiç çağrılmadıysa `closeClientConnection` null `tcpClient`'ı kullanır (çökme). AlgoProd iki kez çağırır (`~OuchManager` + `Application`), HFT bir kez (`src/Main/HftMain.cpp`).
- `authToken` temizlenmez.

## 6. Model sınıfları (`include/models/`)

Getter/setter'lı düz sınıflar. Kopyalanabilir. Varsayılan yapıcılar sayısal alanları **ilklemez** (`= default`).

Ölçekler (bütün modellerde):
- **Fiyat:** raw tam sayı = TL × 10^`decimalCount` ([sözlük](../../00-genel/sozluk.md)). Dönüştürme yapılmaz. `Order.h` yorumundaki "14.98 → 1498" örneği 2 ondalıklı enstrüman içindir.
- **Miktar:** lot.
- **`orderbookId`:** ITCH orderbook id.
- **Timestamp:** order-service'ten aynen gelir. MAOrderSDK'da epoch **ns**'dir ([maordersdk/api-ve-yasam-dongusu.md](../maordersdk/api-ve-yasam-dongusu.md)). ❓ doğrulanmadı: order-service'in değeri dönüştürmeden ilettiği. Risk retlerinde `system_clock` ns'dir.

### 6.1 `EnterOrder` → `EnterOrderRequest`

Yapıcı: `EnterOrder(orderbookId, account, side, qty, prx, strategyIdentifier, timeInForce, strategyType, passThrough, ordType = REGULAR_ORDER_LIMIT, protocol = PROTOCOL_OUCH, expireDate = 0, isActive = false)`.

| Alan | Tip | MARpc alanı | Not |
|------|-----|-------------|-----|
| `orderbookId` | uint32 | `orderbookId` | |
| `account` | string | `account` | Hesap adı |
| `side` | `enums::Side` (`'B'/'S'/'T'`) | `side` (1/2/3) | `EnumsConvertor`, §7 |
| `quantity` | uint64 | `quantity` (ulong) | lot |
| `price` | uint32 (yapıcı `int32_t` alır) | `price` (int) | raw |
| `strategyIdentifier` | string | `strategyIdentifier` | Header yorumu: en çok 3 karakter. ❓ doğrulanmadı: sınırın sunucuda uygulandığı. |
| `timeInForce` | `enums::TimeInForce` | `timeInForce` | `static_cast`. order-service GTC(4)/AT_CROSSING(6)/0'ı DAY yapar ([arayuzler § 3.3](../order-service/arayuzler.md#33-enterorderrequest-alanları)). |
| `strategyType` | `enums::StrategyType` | `strategyType` | `static_cast`; sunucu bunu DB strateji id'si sayar |
| `passThrough` | string | `passThrough` | Olaylarda geri döner; istemcinin tek korelasyon alanı (wire'da istemci token'ı yok) |
| `ordType` | `enums::OrdType` | `regularOrderType` | `static_cast` |
| `protocol` | `enums::Protocol` | `protocolType` | 0 → sunucu emri **sessizce düşürür** |
| `expireDate` | uint64 | `timeToSent` | Sunucuda `SetExpireDate` → FIX GTD. ❓ doğrulanmadı: biçim. |
| `isActive` | bool | `isActive` | Sunucuda yalnız loglanır (eski toplu emir alanı) |

Emir token'ı wire'da **yoktur**. İstemci token'ı ilk kez `OrderAccepted.orderToken` ile öğrenir.

### 6.2 `ReplaceOrder`, `CancelOrder`

| Sınıf | Alanlar | MARpc'ye giden | Gitmeyen |
|-------|---------|----------------|----------|
| `ReplaceOrder(orderToken, qty, prx)` | `orderToken`, `quantity` (uint64, lot), `price` (uint32, raw), `passThrough` (`setPassThrough`, varsayılan `""`), `protocol` | `orderToken`, `quantity`, `price`, `passThrough` | **`protocol`**: convertor kopyalamaz, wire'a hep 0 gider. Üye ilklenmez. Sunucu protokolü token'dan bulur ([arayuzler § 6.3](../order-service/arayuzler.md#63-cancel--replace)). |
| `CancelOrder(orderToken)` | `orderToken` | `orderToken` | Protokol alanı yok; wire'da 0. AlgoProd'da `// FIXME: remove channel` bunu yansıtır. |

Getter adı tutarsız: `ReplaceOrder::getPassthrough()` (küçük t), setter `setPassThrough`.

### 6.3 `StrategyInfo` ⇄ `AccountStrategy`

Yapıcı: `StrategyInfo(orderbookId, account, strategyIdentifier, strategyType, overallValue = 0, position = 0, lastPrice = 0)`. Setter yok.

| Alan | Tip | SET'te wire'a gider mi | GET'te dolar mı |
|------|-----|------------------------|-----------------|
| `orderbookId` | uint32 | Evet | Evet |
| `account` | string | Evet | Evet |
| `strategyIdentifier` | string | Evet | Evet |
| `strategyType` | `enums::StrategyType` | Evet | Evet (= DB strateji id'si, cast) |
| `overallValue` | int32 | Evet | Evet. ❓ doğrulanmadı: birim. |
| `position` | int32 (lot) | **Hayır**: network-sdk `MAHelper::getRequest` serileştirmez | Evet |
| `lastPrice` | int32 (raw) | **Hayır** | Evet |

`getStrategyKey()` = `account + strategyIdentifier + to_string(strategyType)`. HFT strateji anahtarı (`<obid>_<account>_<id>_<type>`) bundan farklıdır.

### 6.4 Gelen olaylar

Bütün alanlar `MAOrderStruct.h` struct'ından convertor ile 1:1 kopyalanır (aşağıda isim değişenler belirtilmiştir).

| Sınıf | Alanlar (tip) | Wire eşlemesi / dikkat |
|-------|---------------|------------------------|
| `OrderAccepted` | `timeStamp` u64, `orderToken`, `orderId` u64 (BIST order id), `orderbookId` u32, `side`, `quantity` u64, `price` i32, `strategyIdentifier`, `account`, `passThrough`, `initialQuantity` u64, `strategyType`, `isInternal` bool | `initialQuantity` ← `preTradeQuantity`. `isInternal` convertor'da set edilmez, hep `false` (yalnız uygulama setter'ı). Yardımcılar: `extractFromPassThrough(start, len)` (kısa passthrough'ta `len` boşluk döner), `getStrategyKey()`. |
| `OrderRejected` | `timeStamp`, `orderToken`, `passThrough`, `rejectCode` i32, `rejectReason`, `account`, `strategyIdentifier`, `orderbookId`, `strategyType`, `isInternal` | **`quantity`, `side` yok.** order-service risk retinde `orderToken` boş gelir; eşleme `passThrough` ile yapılmalı. Cancel'ın 401 retinde `strategy`/`orderBookId` doldurulmaz. |
| `OrderExecuted` | `timeStamp`, `orderToken`, `orderbookId`, `quantity` (bu dolumun lotu), `price` (işlem fiyatı, raw), `matchId` u64 | **`side`, `account`, `passThrough`, `orderId` yok.** Wire'daki `previousPosition`/`dailyPosition`/`totalPosition`/`lastPrice` modele alınmaz (sunucu zaten 0 gönderir). Uygulama token ile eşler. |
| `OrderCanceled` | `timeStamp`, `orderToken`, `orderId`, `orderbookId`, `side`, `reasonCode` i32 (wire `unsigned`), `reason`, `quantity` | `account`, `strategy`, `passThrough` yok |
| `OrderReplaced` | `timeStamp`, `orderToken` (yeni), `oldToken`, `orderbookId`, `side`, `orderId`, `quantity`, `price`, `passThrough`, `account`, `preQuantity`, `strategyIdentifier`, `strategyType` | `orderToken` ← `replacementOrderToken`, `oldToken` ← `previousOrderToken`, `preQuantity` ← `preTradeQuantity` |

`strategyType` gelen olaylarda doğrudan cast edilir: sunucu 2 veya 12 gönderirse ouch-sdk'da adı olmayan bir enum değeri oluşur (§7.1).

### 6.5 `OuchUserDisconnected` (handoff bildirimi)

`orderUserDisconnected` bir **kopma bildirimi değildir**. order-service'in sabah devrinde OUCH kullanıcısından logout olduğunu ve kullanıcıyı uygulamaya devrettiğini bildirir ([sistem haritası](../../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri), tetik: [order-service/sdk-ve-oturumlar.md](../order-service/sdk-ve-oturumlar.md)).

| Getter | Tip | Wire (`UserDisconnected`) | Anlam |
|--------|-----|---------------------------|-------|
| `getUsername()` | string | `username` | OUCH kullanıcı adı (`<OUCH_USER>`) |
| `getPassword()` | string | `password` | OUCH şifresi, **düz metin** (MARpc şifresiz) |
| `getIp()`, `getPort()` | string, uint32 | `ip`, `port` | BIST OUCH gateway (`<PROD_IP>`) |
| `getApplicationUsername()` | string | `applicationUsername` | Bildirimin yönlendirildiği uygulama kullanıcısı |
| `getAllowedAccounts()` | `vector<string>` | `allowedAccounts[]` + `allowedAccountsSize` | Null girişler atlanır |
| `getCallbackNumber()`, `getTotalNumberOfCallbacks()` | int | aynı | Bu devir turundaki sıra / toplam **OUCH kullanıcısı** bildirimi |

Convertor null struct'ta `nullptr` geçirir. HFT bu callback'te MAOrderSDK `connectUser` ile BIST'e login olur ([hftsrvprod/emir-yasam-dongusu.md § 4](../hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı)). AlgoProd'da implementasyon yok.

`OuchUserDisconnected.h` `<vector>` ve `<cstdint>`'i include etmez; tek başına include edilirse derlenmez (`OrderStreamClient.h` üzerinden sorun yok).

### 6.6 `Order`

Public API'de hiçbir fonksiyon kullanmaz. Eski sabah/açılış emri modelidir (`isActive` yorumu "morning and opening orders"). Alanlar `EnterOrder` + `orderIdentifier` (order-service iç id'si, BIST order id değil). Tek kullanıcı HftSrvProd `CollectiveOrder` sınıfıdır; o da yalnız `OuchManager.h`'ta include edilir.

## 7. Enum'lar (`include/models/Enums.h`)

### 7.1 `StrategyType` (dikkat)

ouch-sdk değeri `static_cast` ile network-sdk `StrategyType`'a geçer, sayılar korunur. Fark **isimlerde** ve eksik değerlerdedir:

| Değer | ouch-sdk | network-sdk `MAOrderEnums.h` / `orders.fbs` | HftSrvProd `src/common.proto` |
|-------|----------|----------------------------------------------|-------------------------------|
| 0 | `UNKNOWN_STRATEGY` | `TYPE_UNKNOWN` / `UNKNOWN_STRATEGY` | `StrategyType_Unknown` |
| 1 | `USER` | `TYPE_USER` | `StrategyType_Algo_User` |
| 2 | — (**yok**) | `TYPE_WARRANT` | `StrategyType_Warrant` |
| 3–11 | `AKD`, `HFT`, `MOVING_AVERAGE`, `ARBITRAGE`, `VWAP`, `THEORETICAL_PRICE`, `MAX_PRICE`, `FUND_TRACKER`, `ORDER_CHASE` | aynı isimler | `AKD`, `HFT`, `MovingAverage`, `Arbitrage`, `VWAP`, `TheoreticalPrice`, `MaxPrice`, `FundTracker`, `OrderChase` |
| 12 | — (**yok**) | `TYPE_HFT_USER` | `StrategyType_HFT_User` |
| 13 | **`WARRANT`** | `TYPE_HFT_WARRANT` | `StrategyType_HFT_Warrant` |
| 14 | `MIN_PRICE` | `TYPE_MIN_PRICE` | `StrategyType_MinPrice` |
| 15 | `WARRANT_ADVANCED` | `TYPE_HFT_WARRANT_ADVANCED` | `StrategyType_HFT_WarrantAdvanced` |

- ouch-sdk `WARRANT` = **13** (HFT varantı). Proto/network-sdk `Warrant = 2`'nin ouch-sdk'da adı yoktur.
- network-sdk `getStrategyType` 15'ten büyük ya da tanımsız değerleri `UNKNOWN_STRATEGY`'ye çevirir.
- Yeni tip ekleme sırası (aynı numara): `common.proto`, ouch-sdk `Enums.h`, network-sdk `MAOrderEnums.h` + `orders.fbs` + `MAHelper::getStrategyType`/`getStrategyTypeResult`, order-service DB `Strategies.id`, trade-data-app, UI ([hftsrvprod/README.md](../hftsrvprod/README.md)).

### 7.2 Diğer enum'lar

| Enum | ouch-sdk değerleri | network-sdk karşılığı | Çeviri |
|------|--------------------|-----------------------|--------|
| `Side` | `UNKNOWN_SIDE=0`, `BUY='B'`(66), `SELL='S'`(83), `SHORT_SELL='T'`(84) | `SIDE_UNKNOWN=0`, `SIDE_BUY=1`, `SIDE_SELL=2`, `SIDE_SHORT_SELL=3` | `EnumsConvertor` switch (iki yön). **Cast edilmez**; `int(side)` 66 verir. |
| `TimeInForce` | `TIF_UNKNOWN=0`, `TIF_DAY=1`, `TIF_IMMEDIATE_OR_CANCEL=2`, `TIF_FILL_OR_KILL=3`, `TIF_GOOD_TILL_CANCEL=4`, `TIF_GOOD_TILL_DATE=5`, `TIF_AT_CROSSING=6` | aynı sayılar | `static_cast` |
| `OrdType` | `REGULAR_ORDER_UNKNOWN=0`, `_STANDART=1`, `_MARKET=2`, `_LIMIT=3`, `_MARKET_WITH_LEFTOVER_LIMIT=4` | `RegularOrderType`, aynı sayılar | `static_cast` |
| `Protocol` | `PROTOCOL_UNKOWN=0` (yazım hatası koddadır), `PROTOCOL_OUCH=1`, `PROTOCOL_FIX=2` | `ProtocolType` 0/1/2 | `static_cast` |
| `Application` | §5.2 | `Application` 0..3 | `(Application)` cast |

Gelen olaylarda `TimeInForce`, `OrdType`, `Protocol` taşınmaz; yalnız `Side` ve `StrategyType` gelir.

## 8. Sabah / açılış emri API'leri

- `addMorningOrder`, `getMorningOrders`, `clearMorningOrders`, `addOpeningOrder`, `getOpeningOrders`, `clearOpeningOrders` yalnız repo `README.md`'sinde geçer. `include/OrderStreamClient.h` ve `OrderStreamClient.cpp`'de **yoktur**. network-sdk'da karşılık gelen istek tipi de yoktur.
- HftSrvProd ve AlgoProd'da çağıran **yok** (grep: yalnız ouch-sdk `README.md`). `ouchSDKApp/main.cpp`'deki `add_morning_orders` çağrısı yorum satırındadır.
- Kalıntılar: `models::Order` (§6.6), `EnterOrder::isActive`, `EnterOrder::expireDate` → `timeToSent`.
- Toplu emirler bugün GUI → trade-data-app → order-service **gRPC** `SendOrder` (MORNING/OPENING/EVENING) yolundan gelir ([order-service/toplu-emirler.md](../order-service/toplu-emirler.md), [arayuzler § 4.3](../order-service/arayuzler.md#43-sendorder-dalları)).

## 9. Build, CI, örnek uygulama

### 9.1 CMake (`CMakeLists.txt`)

- `add_library(ouchSDK SHARED ...)`, C++17, varsayılan `Release` (`-O2`), Debug'da `-g`. `target_link_libraries(ouchSDK pthread MARpc)`, `link_directories(/usr/local/lib/)`.
- `ma_add_git_version(ouchSDK COMPONENT ouchSDK REPO ouch-sdk)` (`cmake/MAGitVersion.cmake`): git sürüm bilgisi `.so`'ya gömülür, `ma::build::PrintAll()` ile basılır, `cmake/ma-build-info.sh` (`ma_show`, `ma_verify`) ile çalıştırmadan okunur. `INSTALL_HEADER` verilmediği için `MAVersion/MABuildInfo.h` bu repo tarafından kurulmaz.
- Kurulum: `/usr/local/lib/libouchSDK.so`, `/usr/local/include/ouchSDK/OrderStreamClient.h`, `/usr/local/include/ouchSDK/models/`. `convertors/` kurulmaz.
- Public header'lar MARpc'yi include etmez. Ama `libouchSDK.so` `libMARpc.so`'ya dinamik bağlıdır: çalışma zamanında ikisi de gerekir. AlgoProd yalnız `ouchSDK`'yı linkler, MARpc'yi transitif alır.
- `soname`/sürüm yok: ABI değişince HftSrvProd ve AlgoProd yeniden derlenmeli.

### 9.2 CI (`.github/workflows/ouch_actions.yml`, "OuchSDK-CI")

1. Tetik: `master`, `preprod`, `development` push. Container `meeapps/maprodenv:4.0`.
2. `BRANCH_NAME`: development → `development`, preprod → `preprod`, aksi hâlde (`master`) → **`main`**.
3. `MeeApps/Algo-Setup`'ın `BRANCH_NAME` dalından `MAProdEnv/lib/libMARpc.so` ve `include/MARpc/` kopyalanır. ouch-sdk, network-sdk'nın o daldaki **yayınlanmış** ikilisiyle derlenir.
4. `cmake . && make clean && make -j10 && make install`.
5. `out/include/ouchSDK` + `out/lib/libouchSDK.so` → Algo-Setup `MAProdEnv` (aynı dal), commit "Commiting OuchSDK Files".
6. `doxygen Doxyfile` (`INPUT = include`, recursive, HTML, `OUTPUT_DIRECTORY = docs`, logo `MeeApps_Logo_Small.png`) → `MeeApps/algo-configs` `doc/Development/Documentation/Ouch-SDK`, **her zaman `master` dalına**. Hangi daldan push edilirse edilsin son push dokümanı ezer.
7. Test adımı yok. `ouchSDKApp` derlenmez.

### 9.3 `ouchSDKApp/`

- Ayrı CMake projesi (`MAOuchSDKApp`), kurulu `libouchSDK`'yı `find_library` ile bulur. Kök `CMakeLists.txt`'teki `add_subdirectory(ouchSDKApp)` yorum satırındadır.
- `main.cpp`: `startOuchStreaming` → `login(APP_HFT)` → 500 kez 2 s arayla `send_0_qty_order` (0 lot → ret beklenir; her seferinde `insertStrategyInfo`). Gerçek emir döngüsü yorumda. Sonra `while(1) sleep`.
- IP, kullanıcı adı ve şifre koda **sabit yazılmıştır** (`<ORDER_SERVICE_IP>`, `<APP_USER>`, `<REDACTED>`).
- `orderUserDisconnected` tanımlanmaz. ❓ doğrulanmadı: bu hâliyle link edildiği (beklenen: tanımsız sembol hatası).
- `include/rapidjson/` yalnız yorumdaki sabah emri JSON okuması içindir.

### 9.4 Repo `README.md` güncel değil

- `OrderStreamClient::` sınıf sözdizimi ve `std::shared_ptr` imzaları kullanır. Gerçek API serbest fonksiyon + referans/ham pointer'dır.
- `login(user, password)` iki parametrelidir; gerçekte `Application` de vardır.
- Sabah/açılış API'leri (§8) ve `StrategyType` `HFT_BASIC` (yok) geçer. `orderUserDisconnected` hiç geçmez.

## 10. Eski bilgi tabanıyla farklar

- ⚠ Eski bilgi tabanı callback'lerin "MARpc RX thread"inde çalıştığını söylüyordu. development'ta ayrı `processCallback` thread'inde çalışırlar (§4.1).
- ⚠ Eski bilgi tabanı `UserDisconnected`'ı "BIST oturumu düştüğünde / başka client login olduğunda" gelen kopma olayı, `callbackNumber`'ı da `allowedAccounts` parçalaması diye anlatıyordu. development'ta bu kasıtlı handoff bildirimidir; sayaç OUCH kullanıcısı başınadır (§6.5).
- ⚠ Eski bilgi tabanı "reconnect/retry MARpc içinde" diyordu. Hiçbir katmanda reconnect yok (§5.3).
- ⚠ Eski bilgi tabanı `login`'deki `username.c_str()`'nin dangling olabileceğini söylüyordu. `sendOrderRequest` senkron serileştirir, sorun yok (§3.2). Asıl dangling okuma yanıt tarafındadır (Şüpheli 2).
- ⚠ Eski bilgi tabanı "callback'e gelen pointer'ı saklamak UB, SDK shared_ptr ile tutuyor" diyordu. Domain nesnesi `new` ile üretilir, SDK tutmaz ve silmez; saklamak güvenlidir, silmek uygulamanın işidir (§4.2).
- ⚠ Eski bilgi tabanı fiyatı "14.98 → 1498 (tick-based int)" diye veriyordu. Doğrusu raw = TL × 10^`decimalCount` (§6).

## Şüpheli

1. **bug?** Bloklayan çağrılarda timeout yok (`login`, `getAllOrders`, `getStrategyInfo`, `insertStrategyInfo`). Connect başarısızsa (§5.1), bağlantı koptuysa ya da sunucu hiç yanıt vermezse (`AllOrdersRequest`'te geçersiz token → order-service sessiz) çağıran sonsuza kadar bekler.
2. **bug?** Yanıt `char*`'ları callback thread'i döndükten sonra okunuyor. `login` `loginResponse->token`'ı, `getStrategyInfo` `accountStrategies[i].account/strategyIdentifier`'ı **çağıran thread'de**, `future.get()` sonrası okur. Bu pointer'lar network-sdk `processCallback`'teki yerel `fbData` tamponunu gösterir; tampon iterasyon sonunda yok olur (use-after-free yarışı). Ayrıca `token` FlatBuffers `[byte]` vektörüdür, sonunda `\0` garanti değildir.
3. **bug?** Callback içinden herhangi bir bloklayan ouch-sdk çağrısı deadlock yapar (§3.3). Bugün HFT/Algo callback'lerinde böyle bir çağrı yok (koddan).
4. **bug?** `ReplaceOrder::protocol` wire'a gitmiyor, `CancelOrder`'da alan yok; ikisi de `protocolType=0` gider. order-service `order_protocols[token]`'da bulamazsa (ör. restart sonrası geri yüklenmemiş token) cancel/replace düşer ([arayuzler § 6.3](../order-service/arayuzler.md#63-cancel--replace)).
5. **bug?** `StrategyInfo` `position`/`lastPrice` SET'te serileştirilmez (network-sdk `MAHelper::getRequest`). Yalnız GET yönünde anlamlıdır.
6. **bug?** Bellek sızıntıları: her istekte request struct + `malloc`'lu string'ler (§3.2), her olayda domain nesnesi (HFT/Algo silmez, §4.2), her `insertStrategyInfo`'da `new AccountStrategy`.
7. **kasıtlı?** Her `AccountStrategyResponse` (`accountStrategies[30000]`, yaklaşık 1.4 MB) ve `AllOrdersResponse` (`orders[100000]`, 800 KB) `networkMap` için kopyalanır, kopya kullanılmaz. Callback thread'inde gereksiz büyük `memcpy`.
8. **bug?** `login` / `getAllOrders` eşzamanlı çağrılırsa promise yeniden atanır (`broken_promise`). Sunucudan beklenmeyen ikinci bir yanıt gelirse `set_value` ikinci kez çağrılır (`promise_already_satisfied`). İkisi de callback thread'inde istisnadır → `std::terminate`.
9. **bug?** Kopma algılanmıyor ve bildirilmiyor (§5.3). Süreç içinde yeniden `startOuchStreaming` UB.
10. **doğrula** `enterOrder` her emirde `std::cout << toString()` yapar. `insertStrategyInfo` 3 debug satırı, OPERATION_SET yanıtı 2 satır basar. HFT OS yolu ve AlgoProd'un bütün emirleri çağıran thread'de senkron `cout`'tan geçer.
11. **doğrula** Farklı thread'lerden gönderilen istekler arasında sıra garantisi yok (moodycamel çok üreticili kuyruk, §3.3). Aynı emir için enter ve cancel farklı thread'lerden gelirse cancel önce gidebilir.
12. **eksik** `Application::OUCH` (3) order-service'te `APP_UNKNOWN`'a düşer. Kullanan yok; anlamı belirsiz.
13. **eksik** `ouchSDKApp/main.cpp`'de sabit IP/kullanıcı/şifre var (repo'da düz metin kimlik bilgisi). Uygulama `orderUserDisconnected`'ı tanımlamaz.
