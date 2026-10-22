---
kapsam: order-service'in MAOrderSDK adaptörü (MAOSdkManager) ve oturum yönetimi (SdkSessionManager) — boot, kullanıcı yükleme, emir gönderme ve alan dönüşümleri, callback'ler, OUCH handoff'un order-service tarafı, FIX yolu ve şifre yenileme, yeniden bağlanma, thread modeli
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
dogrulama: 2026-10-22
durum: taslak
---

# MAOrderSDK adaptörü ve oturumlar (order-service)

Kod: `Managers/Sdk/MAOSdkManager.*`, `Managers/Sdk/SdkSessionManager.*`. Başka yerde anlatılanlar burada tekrar edilmez:
- SDK API'si, bölme, yerel retler, combiner: [maordersdk](../maordersdk/README.md)
- Handoff'un genel akışı: [sistem-haritasi § OUCH handoff](../../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri); HFT tarafı: [hftsrvprod/emir-yasam-dongusu § 4](../hftsrvprod/emir-yasam-dongusu.md)
- MARpc/gRPC sunucuları, `OrderDispatcher`, açılış sırası: [arayuzler.md](arayuzler.md)
- Sabah/açılış/YİP/teorik akışları (`SendRepeatableOrders`, `SendOpeningOrders`): [toplu-emirler.md](toplu-emirler.md)
- `RiskManager`: [risk.md](risk.md). DB kalıcılığı ve `config.yaml` referansı: [kalicilik-ve-config.md](kalicilik-ve-config.md)

`MAOSdkManager`, `OrderManager`'dan türer ve `Protocol::kOuch` ile kaydedilir. FIX ayrı bir manager değildir (issue #402): FIX kullanıcıları aynı `maordersdk::MAOrderSDK` örneğinde yaşar.

## 1. Boot sırası (`MAOSdkManager::StartProperly`)

1. `session_.start()`: reconnect ve şifre worker bayrakları açılır.
2. **OUCH kullanıcıları:** `UserService::GetUsers(kOuch)` (trade-data-app `DataService.GetOuchUsers`). Mode filtresi uygulanır (§2). Kullanıcı `users` haritasına ve `users_with_markets[market][partition]`'a eklenir. Pazar veya partition bulunamazsa `LOG_CRIT` + atlanır.
3. `accMarPart_to_clients`: hesap + pazar anahtarıyla kullanıcı listesi (host tarafı round-robin; yalnız çift pazarlı hesaplarda kullanılır, §4).
4. **FIX kullanıcıları:** `GetUsers(kFix)`, aynı mode filtresi. `fix_users_`, `fix_usernames_`, `market_parts_to_fix_users_["<market int><partition>"]`.
5. `user_accounts = user_service->GetAccounts()`: hesap → client category, AFK (agency fund code). `GetUsers` en az bir kez çağrılmadan boştur.
6. `maordersdk::OuchConfig` kurulur (§3). OUCH kullanıcıları `OrderUser::Sdk()` struct'ı olduğu gibi verilir; `session_.registerOuchUser`. Aynı hesap iki OUCH pazarında varsa `dual_market_accounts_`'a eklenir (`LOG_WARN`).
7. FIX kullanıcıları: `seedFixPassword`, `armFromConfig` (config `fixSession.newPasswords`), `sdk_user.fix_new_password`. `fix_session.*` alanları `fixSession` config'inden kopyalanır.
8. `sdk_ = make_unique<MAOrderSDK>()`, `session_.attach`, `setOuchConfig`, `setSdkConfig`, `setInstrumentLimits`, `ConfigureSdkCallbacks`.
9. `RetrieveSentOrders()` (§4.5): DB'deki günün OUCH+FIX emirleri `entered_orders`'a; FIX emirleri ayrıca `adoptFixOrders` ile SDK'ya.
10. `sdk_->start()`. Başarısızsa `runtime_error` (servis kalkmaz).
11. `parseBistLoopStart = şimdi (s)`. Pozisyon yazma penceresi bunu kullanır (§5).
12. **OUCH login:** her OUCH kullanıcısı için **sırayla** `sdk_->connectUser(username)`. Senkron: TCP (önce birincil, olmazsa ikincil IP) + SoupBinTCP login (2 s timeout). Replay recv thread'inde asenkron akar. `Ok`/`AlreadyConnected` dışı sonuçta `session_.scheduleReconnect`.
13. **FIX:** önce bütün FIX kullanıcıları `fix_replay_pending_`'e konur, sonra `connectUser` (QuickFIX `Session::logon`, asenkron). Başarısızsa `LOG_CRIT` ve pending'den çıkarılır.
14. Toplu akış thread'leri (detached): `repeatableOrders.ouch[]`, `repeatableOrders.fix[]`, açılış grupları, YİP → [toplu-emirler.md](toplu-emirler.md).

**Login sırasında `onlyMorningOrderUser` ayrımı yoktur:** handoff'a girecek kullanıcılara da order-service login olur. Gün içi restart'ta bunun sonucu için §9.

## 2. Kullanıcı modeli (`Data/Models/OrderUser.*`, `Service/Network/UserService.cpp`)

`OrderUser`, wire alanlarını gömülü `maordersdk::OuchUser sdk_` içinde tutar, host alanları yanında durur.

| Alan | Kaynak (proto `OrderUsersResponse`) | Kullanım |
|------|------------------------------------|----------|
| ip/port, secondary ip/port | `ouchIp`, `ouchPort`, `ouchSecondaryIp/Port` | SDK endpoint. Handoff mesajına yalnız birincil gider. |
| username, password | `orderUsername`, `orderUserPassword` | SDK credentials |
| `pendingPassword` | `orderUserPendingPassword` (yalnız FIX) | Şifre yenileme (§8) |
| market | `ouchMarket`: `EQUITY` → kEquity, `VIOP` → kDerivative | Routing, hesap alanları (§4.2) |
| **partition** | **DB'den okunmaz.** `OrderUser` ctor'u `sdk_.partition = 1` yapar; `GetUsers` `SetPartition` çağırmaz, proto'da alan yok | Her kullanıcı partition 1'dir. |
| allowed accounts | `ouchAccounts[].accountName` | SDK `allowed_accounts`; hesap nesneleri (`isCancelAllowed`, `orderCapacity`, `orderRepeatRemaining`, `client_type`, `agency_fund_code`…) `UserService::accounts`'a |
| `capacity`, `repeatCount`, `coreToPin` | `ouchCapacity`, `ouchRepeatCount`, `ouchCoreToPin` | Yalnız host; sabah akışları ([toplu-emirler.md](toplu-emirler.md)). SDK'ya gitmez. |
| `onlyMorningOrderUser` | `onlyMorningOrderUser` → `sdk_.morning_only` | Handoff (§7) |
| `applicationUsername` | `applicationUsername` | Handoff hedefi (ör. HFT'nin MARpc kullanıcısı) |
| `isProduction` | `isProduction` | Mode filtresi |
| FIX `subId`, `senderCompId`, `targetCompId` | `orderUserSubId/SenderCompId/TargetCompId` | QuickFIX session kimliği |

**Mode filtresi:** `IsTestEnvironment()` → yalnız `!IsProduction()`; `IsProductionEnvironment()` → yalnız `IsProduction()`. İkisi de değilse hiçbir kullanıcı yüklenmez.

## 3. SDK config (kodda sabit)

| Alan | Değer | Not |
|------|-------|-----|
| `heartbeat_interval_ms` | 3000 | OUCH client heartbeat |
| `heartbeat_timeout_ms` | 15000 | Recv watchdog; yalnız `onHeartbeatTimeout` tetikler (§9) |
| `token_pool_size` | 100000 | Önceden üretilmiş token havuzu; bitince kilit altında üretim |
| `use_onload`, `lock_memory` | false | |
| `order_hard_cap_try` | `maordersdk.orderHardCapTry` (tam TL) | 0 ise `LOG_CRIT` ve SDK varsayılanı korunur |
| `replay_quiet_window_ms`, `recv_pin_core`, combiner | set edilmez | SDK varsayılanları. `setItchSdk` çağrılmaz; combiner yok. |
| `InstrumentLimit` | `MaxOrderVal()` (tam TL, `uint32`'ye cast), `decimal_count` = `DecimalPrx()`'in sondaki sıfır sayısı (1000 → 3), `IsBrutTakas()` | `InstrumentService::GetInstruments()`'tan, açılışta bir kez |

## 4. Emir gönderme

### 4.1 Giriş noktaları

| Fonksiyon | Çağıran | Routing | Bölme | DB |
|-----------|---------|---------|-------|----|
| `SendOrderAsync(EnterOrder)` | `OrderDispatcher` (MARpc/gRPC emirleri) | FIX → `getNextFixClient`; çift pazarlı hesap → `NextClientForAccount`; diğer → SDK hesap round-robin | Evet (strateji Arbitraj/VWAP/Fon Takibi hariç) | `InsertOrderToDatabaseAsync`, yalnız SDK'nın sahiplendiği parçalar |
| `SendOrderWithUsername` | Toplu akışlar | Verilen kullanıcıya exact-route (OUCH ya da FIX) | **Hayır** (`preserve_single_order=true`) | `insert_to_db` parametresine bağlı |
| `SendPackagedOrderWithUsername` | Toplu akışlar (`packOrders`) | Aynı kullanıcıya döngüyle tek tek `enterOrder` | Hayır | Yazmaz (çağıran yazar) |
| `SendOrderAsync(CancelOrder)` | Dispatcher | SDK token'dan bulur | — | — |
| `SendOrderAsync(ReplaceOrder)` | Dispatcher | SDK, eski token'ın connection'ı | — | Yeni token'lı kopya yazılır |

- `getNextFixClient(market, partition, account)`: `market_parts_to_fix_users_`'ta hesabı izinli **ilk** FIX kullanıcısı (round-robin yok). Bulamazsa `FixUserNotFoundException` → `LOG_CRIT`, emir gönderilmez. Partition enstrümandan gelir; kullanıcı partition'ı hep 1 olduğundan (§2) partition'ı 1 olmayan enstrümanda FIX kullanıcısı bulunamaz. ❓ doğrulanmadı: DB'de partition 2 enstrüman olup olmadığı.
- `NextClientForAccount(accMarPart)`: host round-robin; bağlantı durumuna bakmaz.
- Instrument veya hesap bulunamazsa `LOG_CRIT` + return. Uygulamaya ret dönmez.
- `this->offhours` (19:00 sonrası `kOffHourOrders`, `OrderManager` `offhours_invertor`) yalnız `SendOrderAsync(EnterOrder)` yolunda set edilir.

### 4.2 Alan dönüşümleri (`ToSdkOrder` + hesap hazırlığı)

| SDK alanı (`EnterOrderMsg`) | Kaynak | Birim / not |
|-----------------------------|--------|-------------|
| `client_order_id` | **boş** | SDK token sahibi; 14 karakter `[0-9A-Za-z]` OUCH token'ı public id olur (HFT ile aynı model) |
| `orderbook_id` | `OrderBookId()` | |
| `side`, `tif`, `ord_type`, `open_close` | enum'lar `static_cast` ile birebir | Değer uyumu varsayılır |
| `quantity` | `Quantity()` | **lot** |
| `price` | `Price()` (`int32`) | **raw** = TL × `DecimalPrx` (= 10^`decimal_count`). TL değildir. Ölçek enstrüman başına. |
| `client_category` | `ClientCategory()` | `kUnknown` → `Unknown`; tanımsız değer → `Client` |
| `client_account`, `exchange_info` | Pay piyasası: fon hesabıysa `client_account` = AFK; `exchange_info` = hesap adı; category = hesap `ClientType`. VİOP: `client_account` = hesap adı, category `kUnknown`. | `SendOrderAsync` `user_accounts`'tan, username yolları `PrepareAccountFields` ile (orada pay piyasasında category yalnız fon için set edilir) |
| `routing_account` | hesap adı | SDK route anahtarı (wire'a gitmez) |
| `off_hours` | `kOffHourOrders` → `OffHours` | |
| `display_quantity`, `passthrough`, `smp_*`, `expire_date` | aynı adlı alanlar | `expire_date` epoch s, yalnız FIX GTD (tag 432) |
| `preferred_ouch_username` | §4.1 routing | Boşsa SDK hesap round-robin'i |
| `no_split` | `preserve_single_order` veya strateji Arbitraj/VWAP/Fon Takibi | Hard cap ve enstrüman kontrolü yine uygulanır |

### 4.3 Token ve kayıt (`SubmitEnterOrder`)

1. Host tarafında kilit tutulmadan `sdk_->enterOrder(msg, on_token_assigned)` çağrılır.
2. SDK token atadığında (wire'a yazmadan **önce**, çağıran thread'de) callback çalışır:
   - `EnterOrder` kopyasına token, (parça) miktar, gönderen kullanıcı ve protokol yazılır (`fix_usernames_`'ta varsa kFix).
   - `register_order` ise `entered_orders[token]`'a konur.
   - Böylece recv thread'inden gelen accept her zaman kaydı bulur.
3. Dönüşten sonra `ownsOrder(token)` false olan (yerel ret almış) kayıtlar `entered_orders`'tan silinir ve DB'ye yazılmaz.
4. Kısmi bölme başarısında yalnız gönderilen parçalar kalıcı olur (`LOG_WARN`).

**SDK `false` döndüğünde uygulamaya ne gider:**

| Durum | SDK davranışı | order-service sonucu |
|-------|---------------|----------------------|
| Yerel validasyon (1001–1006); split'te route var ama bağlı bağlantı yok (1) | Token atanır + senkron `onRejected` | `OrderRejected` uygulamaya ve GUI'ye gider (§5) |
| Split'te hesabın `account_routes_` kaydı hiç yok (1) | `onRejected` `client_order_id = ""` ile, token atanmaz | `context_for("")` kayıt bulamaz, olay atılır ([maordersdk/emir-akisi](../maordersdk/emir-akisi.md)) |
| Encode / soket / duplicate (4/5/6/15) | `notify_send_failure` → `onRejected` | Aynı |
| Bölünmeyen emir, hesabın **bağlı** connection'ı yok (handoff sonrası, kopma, exact-route kullanıcısı düşük) | `onSdkError(1)`, token yok, ret yok | Yalnız `LOG_CRIT "MAOrderSDK error code=1"`. **Uygulamaya cevap gitmez** (Şüpheli #3) |

### 4.4 Cancel / replace

- **Cancel:** `sdk_->cancelOrder(token)`; `false` ise yalnız `LOG_CRIT "MAOrderSDK cancel failed"`. SDK: bilinmeyen token → `onSdkError(9)`, emrin connection'ı bağlı değil → `onSdkError(10)`. Emir, gönderildiği connection'a bağlıdır; aynı hesabın başka bağlı kullanıcısına düşmez.
- **Replace:**
  - `entered_orders`'tan eski emir alınır; yoksa `LOG_CRIT` + return.
  - `risk_manager->checkEnterOrder(orderedDifference(...))` ret verirse `sendOrderRejectedToApplication` çağrılır.
  - `ReplaceOrderMsg`: `client_order_id` = eski token, `new_client_order_id` boş (SDK atar), `quantity`/`price` istekteki gibi. 0 = koru; host kopyasında 0 olan alan eski değerle doldurulur.
  - Token callback'inde yeni token'lı kopya `entered_orders`'a girer, `OrderID` 0'lanır (replay dedup'ı yanlış tetiklenmesin).
  - `false` dönerse yeni kayıt silinir; uygulamaya ret gitmez (SDK `onRejected` ürettiyse o gider).

### 4.5 Restart sonrası kayıt (`RetrieveSentOrders`)

- `order_service->GetStrategyOrders(kOuch)` + `(kFix)` → `entered_orders[token]` (`OrderID` = 0).
- FIX emirleri ayrıca `AdoptedFixOrder` olarak SDK'ya verilir (`adoptFixOrders`), FIX kullanıcısı `getNextFixClient` ile yeniden seçilir. Amaç cancel/replace'in restart sonrası çalışması. 141=Y reset'ten önce gönderilen emirlere replay ulaşmaz; seed tek güvencedir.
- OUCH emirleri SDK'ya seed edilmez. Login'deki replay (§9) SDK'da adopt eder; `client_order_id` = wire token = DB `Token` olduğu için host kaydıyla eşleşir.

## 5. Callback'ler (`ConfigureSdkCallbacks`)

Her emir callback'i `sdk_callback_mutex_` altında çalışır, `context_for(token)` ile `entered_orders` kopyasını alır. Kayıt yoksa (`OrderBookId()==0`) `LOG_WARN` + **olay atılır**.

| Callback | Dedup (aynı proses içi reconnect replay'i) | Yan etkiler |
|----------|--------------------------------------------|-------------|
| `onAccepted` | `entered.OrderID() != 0 && == msg.order_id` → atla | `entered_orders` güncellenir (`OrderID`, miktar, fiyat). `OrderAccepted` (protokol, TIF, tip, ana emir, passthrough, gecikmeler ns) → `OrderResponseCallBack`, `risk_manager->OnOrderAccepted`, `accepted_orders` |
| `onRejected` | `rejected_orders`'ta aynı timestamp + kod → atla | 1001–1003 için `LOG_CRIT "LOCAL REJECT"`. Açıklama SDK'dan, boşsa `kRejectCodes`. Miktar/obid 0 ise kayıttan. → `OrderResponseCallBack`, `rejected_orders`. Risk'e çağrı yok. |
| `onExecuted` | `processed_execution_keys_` (`token:match_id:timestamp`) | `OrderExecuted` (fiyat raw, `LastPrice` = fill fiyatı). `risk->OnOrderExecuted(apply_balance = !is_replay)`. Pozisyon: `is_replay` ise yazılmaz; FIX ise yazılır; OUCH ise yalnız `şimdi − parseBistLoopStart > 10 s` ise yazılır (`PARSE_LOOP_START_TIMEOUT`). `executed_orders` |
| `onCanceled` | `canceled_orders`'ta aynı token + `order_id` → atla | Sebep `kCancelReasonCodes` (1 kullanıcı, 3 deal, 4 inaktif, 9 sistem). `risk->OnOrderCanceled(..., entered.Price(), entered.Quantity())`. `canceled_orders` |
| `onReplaced` | `entered.OrderID() != 0 && == msg.order_id` → atla | Yeni token kaydı güncellenir; `PreviousPrice` eski kayıttan. `risk->OnOrderReplaced(old, new)`. `replaced_orders` |

- **`is_replay`** yalnız FIX'te set edilir (`FixEngine`, PossDupFlag). OUCH decoder'ı set etmez; OUCH replay'i SDK'da canlı olaylardan ayırt edilemez.
- **Yayılım:** `OrderResponseCallBack` senkron olarak `OrderDispatcher` üzerinden bağlı fonksiyonları çağırır:
  - `OrderServer` (MARpc): `SenderApplication`'ın bağlantılarına gönderir.
  - `OrderServiceImpl`: gRPC `order_queue`'ya koyar → trade-data-app.
  - Ayrıntı: [arayuzler.md](arayuzler.md).
- **Session callback'leri:**
  - `onUserConnected`: OUCH'ta yalnız log. FIX'te replay gate'e eklenir + `session_.onUserConnected`.
  - `onUserDisconnected`: FIX'te gate temizlenir; OUCH'ta `session_.onUserDisconnected`.
  - `onReplayCompleted`: log + FIX gate'inden çıkarma.
  - `onLoginFailed`, `onHeartbeatTimeout`: yalnız `LOG_CRIT` (`session_`).
  - `onSdkError`: yalnız `LOG_CRIT`.
- **`kRejectCodes`** (BIST negatif kodları, yalnız açıklama için): `-110023` iki kez tanımlı ("Illegal transaction at this time" kalır, "orderbook not available" düşer); `-420029` iki kez. Ret davranışı (ör. `-110023` döngüsü) toplu akışlarda: [toplu-emirler.md](toplu-emirler.md).

### `FetchUserOrders` (HFT `getAllOrders`)

- Önce `WaitForFixReplay(10 s)`: `fix_replay_pending_` boşalana kadar bekler. Süre dolarsa logon olmamış kullanıcılar pending'den atılır, replay'i süren kalır.
- Sonra `accepted/rejected/executed/replaced/canceled` haritalarından `SenderApplication == username` olanlar toplanır, `Timestamp` + `SendPriority`'ye göre sıralanır.
- Döndürülen ham pointer'lar. Haritalar gün boyu büyür, silinmez.

## 6. Ölçek özeti

| Değer | Birim |
|-------|-------|
| Fiyat (`price`, `LastPrice`, `PreviousPrice`) | raw `int32` = TL × `DecimalPrx`; SDK `int64` |
| Miktar | lot |
| `max_order_value`, `orderHardCapTry` | tam TL |
| Timestamp'ler | SDK'dan geldiği gibi (`SentTime` host'ta ns epoch) |
| Gecikmeler (`latency_*_ns`) | ns |

## 7. OUCH handoff — order-service tarafı

### 7.1 Tetikler

Üç yol var. Hepsi `DisconnectMorningOrderUsers`'a çıkar.

| Yol | Ne zaman | Kapsam |
|-----|----------|--------|
| **A. Akış sonu** (`OrderManager::SendRepeatableOrders` sonu) | Bir `repeatableOrders` satırı emirlerini gönderip 2 s sonra fazla kopyaları iptal edip `WorkAfterSendRepeatableOrders`'ı bitirince | O satırın `GetUsers(protocol, part, mode)` döndürdüğü **bütün** kullanıcılar için `DisconnectMorningOrderUsers(username)`. Pazar filtresi yok. FIX satırlarında kullanıcı `users`'ta olmadığı için no-op. Satırda hiç emir yoksa ya da geç kalındıysa (`IsLateToSend(5)`) bu yol çalışmaz. |
| **B. Zamanlayıcı** (`OrderServiceApplication::shouldTriggerOuchDisconnectOnStartup`) | Açılış saat:dk:sn'den (ms yok) önceyse, `repeatableOrders.ouch[]`'taki her `type: morning` satırı için detached thread `config + 30 s`'de `TriggerOuchDisconnect()` | Bütün kullanıcılar (`username` boş). `morning_viop` satırı için zamanlayıcı yok. |
| **C. Geç başlatma** | Açılış bir `morning` satırının saatinden sonraysa | Hemen detached thread'de `TriggerOuchDisconnect()`; `break` |

`TriggerOuchDisconnect` = `DisconnectMorningOrderUsers()` + exception yutma (`LOG_WARN`). `OrderDispatcher::TriggerOuchDisconnect` kOuch manager'ını `dynamic_cast` ile bulur.

### 7.2 `DisconnectMorningOrderUsers`

- **Tek kullanıcı (yol A):**
  - `disconnect_mutex_` alınır.
  - Kullanıcı `users`'ta ve `disconnected_users_`'ta değilse, o uygulama kullanıcısı için toplam ilk kez hesaplanır (`CalculateDisconnectNumberOfCallbacks(appUsername)`).
  - `OnlyMorningOrderUser` değilse çıkılır.
  - Kullanıcı `disconnected_users_`'a eklenir, sayaç `fetch_add` ile artırılır, `TryDisconnectUser` çağrılır.
- **Hepsi (yol B/C):**
  - `applicationUserTotalCounts_` **boşsa** bütün uygulama kullanıcıları için toplamlar hesaplanır.
  - Sonra her kullanıcı için `disconnect_mutex_` altında: zaten devredilmişse veya morning-only değilse atlanır; değilse sayaç artırılır, set'e eklenir, `TryDisconnectUser` çağrılır.
- **Toplam** (`callbackTotal`): o `applicationUsername`'e bağlı, henüz devredilmemiş morning-only kullanıcı sayısı. Bütün pazar ve partition'lar dahil, hesaplandığı anda sabitlenir.
- **Sıra** (`callbackNumber`): o uygulama kullanıcısı için 1'den başlayan atomik sayaç.

### 7.3 `TryDisconnectUser`

1. Morning-only değilse ya da `applicationUsername` boşsa `false` (log).
2. `auth_service->GetUserConnections(appUser)`:
   - Bağlantı varsa 1 s uyunur.
   - Yoksa `IsRunning()` sürdükçe 500 ms aralıkla **süresiz** beklenir, sonra 20 ms uyunur.
   - Bekleme `disconnect_mutex_` tutulurken yapılır (Şüpheli #5).
3. `session_.markIntendedDown(user)`: reconnect shim'i bu kullanıcı için **kalıcı** kapanır. Bayrak hiç geri alınmaz.
4. `sdk_->disconnectUser(user)` → `OuchConnection::disconnect()`:
   - `connected_ = false`, recv thread join, soket `close`.
   - **SoupBinTCP LogoutRequest gönderilmez.** `OuchConnection::logout()` tanımlı ama hiçbir yerden çağrılmıyor. BIST oturumu TCP kapanışıyla düşer.
   - `onUserDisconnected` çağıran thread'de tetiklenir; `intended` true olduğundan reconnect planlanmaz.
5. `UserDisconnected` kurulur ve `OrderResponseCallBack(OnUserDisconnected)` çağrılır:
   - `OrderServer::OnUserDisconnected`: `applicationUsername`'in **bütün** MARpc bağlantılarına gönderir.
   - `OrderServiceImpl::OnUserDisconnected`: gRPC `order_queue`'ya koyar. ❓ doğrulanmadı: trade-data-app stream'inde bu olayın filtrelenip filtrelenmediği ve şifrenin oraya gidip gitmediği ([arayuzler.md](arayuzler.md)).
6. `true` döner. Dönüş değerini kimse kullanmaz.

**`UserDisconnected` wire içeriği** (`OrderServer::CreateResponse`, `TYPE_UserDisconnected`):

| Alan | Değer |
|------|-------|
| `username` | OUCH kullanıcı adı |
| `password` | **açık metin** OUCH şifresi (`<REDACTED>`) |
| `ip`, `port` | yalnız birincil endpoint. İkincil IP ve pazar gönderilmez (HFT `market = Equity` sabitler). |
| `applicationUsername` | hedef uygulama kullanıcısı |
| `allowedAccounts[]` | izinli hesaplar |
| `callbackNumber`, `totalNumberOfCallbacks` | §7.2. HFT ilk callback'te `registerExpectedReplays(total)` yapar ([emir-yasam-dongusu § 4](../hftsrvprod/emir-yasam-dongusu.md)). |

### 7.4 Hata ve zaman aşımı

| Durum | Davranış |
|-------|----------|
| Uygulama kullanıcısı hiç bağlanmaz | Thread süresiz bekler. Kullanıcı order-service'te kalır, emirler OS yolundan gider. Diğer handoff çağrıları `disconnect_mutex_`'te bloklanır. |
| HFT `connectUser`'ı başarısız | order-service bunu bilmez; geri bildirim yoktur. Kullanıcı ne order-service'te (intended down) ne HFT'de bağlıdır. Gün boyu OUCH yoktur (2026-08-03 olayı). |
| `UserDisconnected` gönderimi exception | `OrderServer` `LOG_CRIT`; tekrar denenmez. Kullanıcı yine devredilmiş sayılır. |
| HFT handoff'tan sonra yeniden başlar | `disconnected_users_` dolu; tekrar `UserDisconnected` gönderilmez. ❓ doğrulanmadı: order-service yeniden başlatılmadan kullanıcının geri alınmasının bir yolu olup olmadığı (kodda yok). |
| Uygulama kullanıcısı AlgoProd ise | ❓ doğrulanmadı: AlgoProd `development`'ın `UserDisconnected`'ı işlediği. MAOrderSDK'lı devir `add-order-sdk` branch'inde. |

### 7.5 Handoff sonrası o kullanıcıyla ilgili order-service davranışı

- **Olaylar:** order-service'in bağlantısı kapalıdır, o kullanıcının emirlerine (sabah emirleri dahil) ait yeni accept/execute/cancel olayları order-service'e **gelmez**. Bu olaylar yalnız HFT'nin SDK'sına (replay + canlı) düşer. order-service'in GUI stream'i ve DB'si o andan sonra bu emirleri güncellemez. ❓ doğrulanmadı: GUI'nin bunları HFT `FetchOrders` yolundan gördüğü.
- **Yeni emir:** Hesabın bağlı başka bir OUCH kullanıcısı varsa SDK round-robin onu kullanır. Yoksa `onSdkError(1)` + `false`; uygulamaya ret gitmez (§4.3). HFT'nin OS yoluna düşen emirleri (OUCH kopması vb.) böyle sessizce kaybolur.
- **Cancel/replace:** Emir kapalı connection'a bağlıdır → `onSdkError(10)` (cancel) / replace hatası; yalnız `LOG_CRIT`, uygulamaya cevap yok. Bu, [emir-yasam-dongusu § 4](../hftsrvprod/emir-yasam-dongusu.md)'deki "replay'den önce OS yoluna giden cancel" ❓'ının cevabıdır.
- **Reconnect:** Shim çalışmaz (`intended_down_`).

## 8. FIX yolu

- **Motor:** MAOrderSDK içindeki `FixEngine` (QuickFIX `SocketInitiator`, statik). FIX kullanıcıları `protocol=Fix` ile aynı `OuchConfig.ouch_users` listesine girer. Emirler exact-route (`preferred_ouch_username` = FIX kullanıcısı) ile FIX havuzuna gider; OUCH ve FIX round-robin'i karışmaz.
- **Config eşlemesi** (`fixSession.*` → `sdk_config.fix_session.*`): `beginString`, `defaultApplVerID`, `connectionType`, `fileStorePath`, `fileLogPath`, `allowUnknownMsgFields`, `validateUserDefined*`, `resetOnLogon/Logout/Disconnect`, `useDataDictionary`/`dataDictionary`, `useTransportDataDictionary`/`transportDataDictionary`, `reconnectInterval` (QuickFIX, **s**), `heartBtInt` (s), `replayFromSeq`.
- **`resetOnLogon: false` + `replayFromSeq: 1`:** `FixEngine::start` her `.seqnums` dosyasında beklenen gelen seq'i 1'e yazar. BIST gerçek seq ile cevap verir, QuickFIX gap görüp ResendRequest atar ve günün ExecutionReport'ları PossDupFlag=Y ile gelir (`is_replay=true`). Bu yalnız proses başlangıcında olur. Proses içi yeniden bağlanmada QuickFIX store'u devam eder.
- **FIX replay gate:** `fix_replay_pending_` (§5 `FetchUserOrders`). `onUserConnected` ekler; `onReplayCompleted`, `onUserDisconnected` ve `onFixLogonRejected` çıkarır.
- **Kopma:** order-service shim'i FIX için devreye girmez; QuickFIX `reconnectInterval` ile yeniden dener. `sdk_->disconnectUser(fix)` = `Session::logout()` ve oturum **devre dışı** kalır (retry yok).

### FIX şifre yaşam döngüsü (`SdkSessionManager`)

Değişmez kural: BIST'in kabul ettiği şifre her zaman {DB `password`, DB `pendingPassword`} kümesindedir. Aday wire'a, DB'ye pending olarak yazılmadan gitmez.

| Tetik | Akış |
|-------|------|
| Açılış, config `fixSession.newPasswords[user]` | `armFromConfig`: DB şifresine eşitse yok sayılır (eski blok). DB'de pending varsa reddedilir. Değilse aday `UpdateOrderUserPassword(user, db_pw, candidate)` ile pending yazılır (başarısızsa yine arm edilir, `LOG_CRIT` elle düzelt), `fix_new_password` olarak arm edilir. |
| Logon reject **1409=8** (süresi doldu) | `autoRenewExpiredPasswords` false ise yalnız log. Değilse worker'da `RenewExpiredFixPassword`: aday = DB pending varsa o (crash-safe), yoksa `generateBistFixPassword()`. Önce DB pending yazılır (başarısızsa arm yok, deneme sayılmaz), sonra `armFixPasswordChange`. Relogon QuickFIX'in sonraki reconnect penceresinde. 5 denemeden sonra `disconnectUser` (oturum kapalı). Eşzamanlı ikinci renew engellenir (`renew_inflight`). |
| Logon reject **1409=5** (hatalı şifre) | DB pending varsa ve daha önce denenmediyse **bir kez** `setFixPassword(pending)` (BIST adayı kabul etmiş olabilir). Değilse `disconnectUser`: kilitlenme riski nedeniyle otomatik tekrar yok. |
| Diğer 1409 (6 kilitli, 9 CompID, 100/101) | Yalnız log |
| `onFixPasswordChangeResult` 0/1 | `live = armed`. DB'ye yazma logon-connected'da yapılır. |
| 〃 −1 (1409'suz logout) | Sonuç bilinmiyor; pending DB'de kalır, sonraki logon çözer. |
| 〃 3 (politika reddi) | Otomatik akışsa pending temizlenir, yeni aday üretilir. Config akışıysa log (oturum kapalı). |
| `onUserConnected` (FIX) | `db_pending` doluysa veya `db_pw != live` ise worker'da `PromoteFixPasswordIfNeeded`: `UpdateOrderUserPassword(user, live, "")`, sayaçlar sıfırlanır. |

- Worker'lar `SpawnFixPwWorker` ile açılır, QuickFIX thread'inde RPC yapılmaz. `stop()`'ta join edilir.
- DB RPC'si: trade-data-app `DataService.UpdateOrderUserPassword` (eski db-service bilmeyebilir).

## 9. Oturumlar, yeniden bağlanma ve kopma senaryoları

**Reconnect shim** (`SdkSessionManager::scheduleReconnect` / `ReconnectUser`, yalnız OUCH):
- Tetik: açılışta login başarısız, ya da `onUserDisconnected` gelir ve `intended_down` false'tur.
- Kullanıcı başına tek thread vardır (`reconnect_in_progress_` CAS). Döngü sırasında gelen yeni istekler `reconnect_requested_` ile birleştirilir.
- Döngü: 1 s uyku → `connectUser(username)`. Sınırsız denenir, backoff yok, her 10 denemede bir `LOG_CRIT`. `intended_down`, `stop()` veya `!IsRunning()` ile durur.
- Her başarılı OUCH login'i sequence **1** ister (`OuchCodec::encode_login`). Günün bütün mesajları yeniden gelir; dedup §5 tablosundadır.

| Senaryo | Ne olur (koddan) |
|---------|------------------|
| **OUCH TCP koptu** (handoff dışı kullanıcı) | Recv loop biter → `onUserDisconnected` → shim 1 s aralıkla yeniden bağlanır. End of Session (`Z`) paketinde `onUserDisconnected` gelmez, shim tetiklenmez ([maordersdk/ouch-protokolu](../maordersdk/ouch-protokolu.md)). Arada o kullanıcıya route edilen emirler: hesabın başka bağlı kullanıcısı varsa ona gider. Yoksa `onSdkError(1)`, sessiz kayıp (§4.3). Açık emirlerin cancel'ı `onSdkError(10)`. Bağlanınca replay; accept/replace/cancel/execute dedup'ı proses içi state ile çalışır, pozisyon tekrar yazılmaz. |
| **OUCH heartbeat timeout** (veri yok, TCP açık) | SDK yalnız `onHeartbeatTimeout` çağırır, soketi kapatmaz. order-service yalnız log basar; reconnect **yok** (Şüpheli #6). |
| **Handoff edilmiş kullanıcı koptu** | order-service etkilenmez (zaten bağlı değil). HFT tarafı: [emir-yasam-dongusu § 6](../hftsrvprod/emir-yasam-dongusu.md). |
| **FIX koptu** | QuickFIX `reconnectInterval` (örnek config 3600 s) sonra yeniden dener. Açılıştaki ilk bağlanma ≤30 s içinde olur (QuickFIX varsayılanı), sonrakiler bu pencerede ([maordersdk/fix](../maordersdk/fix.md)). Gate temizlenir. Şifre akışları bu pencereye bağlıdır. |
| **trade-data-app yok** (açılışta) | `GetUsers` boş döner (`LOG_CRIT`); hiç kullanıcı yüklenmez. ❓ doğrulanmadı: `DatabaseClient::Connect`'in bunu önceden bloklayıp bloklamadığı ([kalicilik-ve-config.md](kalicilik-ve-config.md)). |
| **Gün içi restart, sabah saatinden sonra** | (1) DB'den emirler `entered_orders`'a (OrderID=0). (2) **Bütün** OUCH kullanıcılarına login denenir; morning-only kullanıcı HFT'deyse ikinci login'in sonucu BIST'e bağlıdır (❓ doğrulanmadı: reddedilir mi). Reddedilirse shim 1 s aralıkla denemeye başlar. (3) Yol C: HFT order-service'e bağlıyken `markIntendedDown` shim'i durdurur. Bağlı olmayan connection'a `disconnectUser` callback üretmez. `UserDisconnected` HFT'ye yeniden gider; HFT connection'ı zaten bağlıysa `connectUser` → `AlreadyConnected`. (4) Login olan kullanıcılarda replay: accept'ler yeniden işlenir, risk'e ve uygulamalara yeniden yayılır (`OrderID` 0 olduğundan dedup yok). Execute'larda pozisyon yazımı yalnız `parseBistLoopStart`'tan sonraki 10 s içinde bastırılır (Şüpheli #4). Rejected/canceled haritaları boş olduğu için bunlar da yeniden yayılır. |
| **Gün içi restart, sabah saatinden önce** | Normal açılış; yol B zamanlayıcıları kurulur. |

## 10. Thread modeli ve kilitler

| Thread | Ne çalıştırır |
|--------|---------------|
| OUCH recv thread (connection başına, SDK) | `onAccepted/Rejected/Executed/Canceled/Replaced`, `onUserDisconnected` (kopma), `onReplayCompleted`, `onHeartbeatTimeout`; shim spawn'ı |
| QuickFIX initiator thread'i | FIX emir callback'leri, `onUserConnected`, `onFixLogonRejected`, `onFixPasswordChangeResult` |
| Çağıran thread (MARpc/gRPC handler, toplu akış thread'leri) | `enterOrder` + token callback; yerel retlerde **senkron** `onRejected` |
| Reconnect thread (kullanıcı başına) | `connectUser` (bloklayan login) |
| FIX şifre worker'ları | DB RPC + arm |
| Handoff thread'leri (zamanlayıcı, geç başlatma, akış sonu) | `TryDisconnectUser` (bekleme + disconnect + MARpc gönderimi) |
| `OrderManager` DB thread'leri | `insert_order_queue`, `insert_position_queue` (asenkron) |

| Kilit | Korur |
|-------|-------|
| `sdk_callback_mutex_` | Bütün emir callback'leri. **Tüm connection'lar arasında** serileştirir. Yayılım (MARpc gönderimi, risk) bu kilit altında senkron çalışır; yavaş bir tüketici bütün recv thread'lerini bekletir. |
| `enter_order_mtx` | `entered_orders`, `accepted/canceled_orders`, `executed_orders` |
| `reject_order_mtx`, `replace_order_mtx` | `rejected_orders`, `replaced_orders` |
| `disconnect_mutex_`, `calculation_mutex_` | Handoff state'i (§7) |
| `fix_replay_mtx_` + `fix_replay_cv_` | FIX replay gate |
| `fix_pw_mutex_`, `fix_pw_workers_mutex_`, `reconnect_threads_mutex_` | `SdkSessionManager` |

- Gönderimde host kilidi yoktur. SDK haritaları kendi kilitlidir; soket yazımı connection başına mutex'le korunur.
- `processed_execution_keys_` `sdk_callback_mutex_` altında kullanılır.
- `accMarPart_to_clientId` (host round-robin) kilitsiz güncellenir.

## Şüpheli

1. **bug? `morning_viop` akışı pay piyasası morning-only kullanıcılarını da devrediyor.** `OrderManager::SendRepeatableOrders` sonunda `GetUsers(protocol, part, mode)` döndürdüğü bütün partition kullanıcıları için `DisconnectMorningOrderUsers` çağırır; pazar filtresi yoktur (`is_morning_viop` bu fonksiyonda kullanılmıyor). Örnek config'te `morning_viop` 09:20, `morning` 09:40. VİOP sabah emri olan bir günde, HFT bağlıysa pay piyasası kullanıcıları da ~09:21'de devredilir. 09:40 akışı bu kullanıcılarla `SendOrderWithUsername` yapar → SDK `pick_connection` null → `onSdkError(1)`, emirler gitmez. Doğrula.
2. **doğrula: Zamanlayıcı ile sabah akışı yarışı.** Yol B, `morning` saati (ms'siz) + 30 s'de bütün kullanıcıları devreder. `disconnected_users_` yalnız devirde dolduğu için akış hâlâ sürüyorsa (gönderim `duration` + `-110023` tekrarları + 2 s iptal beklemesi) kullanıcı akışın ortasında kapanır. Fazla kopya iptali (`CancelRepeatedOrders`) `onSdkError(10)` ile düşer. ❓ `duration` biriminin ve gerçek akış süresinin 30 s'yi aşıp aşmadığı.
3. **bug? Bağlı connection yokken emir sessizce düşüyor.** Bölünmeyen emirde SDK `onSdkError(1)` + `false` döner, ret üretmez. `SendOrderAsync` uygulamaya `OrderRejected` göndermez; HFT/AlgoProd emri beklemede kalır. Aynısı cancel (`onSdkError(9/10)`) ve replace için geçerli (`MAOSdkManager::SendOrderAsync`). Instrument/hesap bulunamadığında da ret yok.
4. **doğrula: Restart sonrası OUCH replay fill'leri.** OUCH'ta `is_replay` hiç set edilmez.
   - Pozisyon tekrarını yalnız `parseBistLoopStart` + 10 s penceresi önler. Pencere `sdk_->start()` sonrası, **sıralı ve bloklayan** login döngüsünden önce başlar. Kullanıcı sayısı × login süresi + replay 10 s'yi aşarsa replay fill'leri `InsertPositionToDatabase`'e tekrar yazılır.
   - `risk->OnOrderExecuted(apply_balance=true)` her OUCH replay fill'inde bakiyeyi yeniden uygular. README'nin risk bölümündeki "Replay edilen fill bakiyeye ikinci kez yazılmaz" ifadesi yalnız FIX için doğrudur ([risk.md](risk.md)).
5. **doğrula: Handoff bekleme kilidi.** `TryDisconnectUser`, uygulama kullanıcısını `disconnect_mutex_` tutarken süresiz bekler. Sabah akış thread'i (yol A) bu kilitte bloklanır; yol B/C thread'leri birbirini bekler. Bekleme `IsRunning()` false olana kadar sürer.
6. **bug? OUCH heartbeat timeout'u reconnect üretmiyor.** `SdkSessionManager::onHeartbeatTimeout` yalnız log basar, SDK soketi kapatmaz. Yarı açık TCP'de (FIN gelmeyen kopma) kullanıcı `is_connected()==true` görünür; emirler yazılır ama cevap gelmez, shim tetiklenmez.
7. **doğrula: Handoff'ta LogoutRequest yok.** `OuchConnection::disconnect` yalnız soketi kapatır; `logout()` ölü kod. BIST'in oturumu bırakması TCP kapanışına bağlıdır. Bu, HFT'deki 4 denemeli `connectUser` retry'ının nedeni olabilir.
8. **bug? Toplam sayısı 0 gidebilir.** Yol A bir uygulama kullanıcısı için `applicationUserTotalCounts_`'ı doldurduysa, yol B/C toplamları yeniden hesaplamaz (`empty()` kontrolü). Haritada olmayan başka bir uygulama kullanıcısının kullanıcıları `totalNumberOfCallbacks = 0` ile gider. HFT `registerExpectedReplays(0)` ile gate'i hemen açık sayar (`DisconnectMorningOrderUsers`).
9. **doğrula: Kullanıcı partition'ı DB'den gelmiyor.** `OrderUser` ctor'u 1 yapar, proto'da alan yok. `repeatableOrders[].part: 2` satırı hiç kullanıcı bulamaz. `getNextFixClient` partition'ı 2 olan enstrümanda FIX kullanıcısı bulamaz.
10. **doğrula: FIX `reconnectInterval: 3600`.** Örnek config'te FIX kopması ve otomatik şifre yenilemesi sonrası relogon 1 saate kadar gecikebilir. ❓ Müşteri config'lerindeki değer.
11. **doğrula: Çift pazarlı hesapta düşük kullanıcı.** `NextClientForAccount` bağlantı durumuna bakmaz. Seçilen kullanıcı kopuksa exact-route emir düşer (#3), diğer pazar kullanıcısına geçilmez.
12. **Açık metin şifre.** `UserDisconnected` OUCH şifresini MARpc'den ve (❓) gRPC kuyruğundan taşır. Kasıtlı (HFT login'i için gerekli); trade-data-app tarafı doğrulanmalı.
