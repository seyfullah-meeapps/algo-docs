---
kapsam: HFT içinde bir emrin yaşam döngüsü — emir modeli, gönderim yolu seçimi, OUCH olaylarının stratejiye ve GUI'ye dönüşü, handoff/replay sırasında sahiplik ve çift kayıt koruması, ret kodları, kopma senaryoları
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: order-service
    branch: development
    commit: b86c0cf
dogrulama: 2026-10-22
durum: taslak
---

# Emir yaşam döngüsü (HFT)

Genel desen ve handoff özeti başka dosyalarda; burada tekrar edilmez:
- Gönderim deseni: [README § Emir gönderme deseni](README.md#emir-gönderme-deseni)
- Emir yolları ve handoff: [sistem-haritasi § Emir yolları](../../00-genel/sistem-haritasi.md#emir-yolları), [§ OUCH handoff](../../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri)
- SDK API'si, bölme, combiner: [maordersdk](../maordersdk/README.md)
- GUI komutları ve gRPC: [komutlar-ve-grpc.md](komutlar-ve-grpc.md). Strateji taban sınıfı ve depth: [strateji-cekirdegi.md](strateji-cekirdegi.md). Config anahtarları: [config.md](config.md).

İki emir yolu vardır. Bu dosyada şu adlarla geçerler:
- **SDK yolu:** HFT → MAOrderSDK → BIST OUCH.
- **OS yolu:** HFT → ouch-sdk (MARpc) → order-service → BIST. Yedek yoldur.

## 1. Emir modeli

### Giden emir: `Hft::EnterOrder`

`src/Messages/OngoingMessages/Transaction/EnterOrder.*`. İçinde `ouchSDK::models::EnterOrder sdkEnterOrder` taşır. SDK yoluna `HftConvert::toSdkMsg` ile `maordersdk::EnterOrderMsg`'e çevrilir.

| Alan | Tip / birim | Not |
|------|-------------|-----|
| `orderbookId` | `uint32` | BIST orderbook id. Varantta türev obid'i olabilir. |
| `side` | char: `B` / `S` / `T` (short sell) | `toSdkMsg` → `Side::Buy/Sell/ShortSell` |
| `quantity` | `uint64`, **lot** | |
| `price` | `int32`, **raw** = TL × 10^`decimal_count` | Ölçek enstrüman başına `OuchManager::getInstrumentDecimalPrice`. TL değildir. |
| `tif`, `ordType` | ouchSDK enum'ları | `mapTif` / `mapOrdType`. Strateji emirleri genelde `TIF_DAY` + `REGULAR_ORDER_LIMIT`. |
| hesap | string | `DE` ile başlıyorsa `client_account` (16 bayt), değilse `exchange_info` (32 bayt) (`toSdkMsg`). Accept dönüşünde SDK hesabı geri yazar (`on_wire_accepted`, decoder'ın Exchange-Info fallback'i). |
| `client_cat` | byte: 0 Client, 1 House, 7 Fund | `mapClientCategory`. Alan-alan ctor'un varsayılanı 1'dir. Mesaj-parse ctor'u `DE` hesabı için 0 yapar. |
| `passthrough` | 15 bayt (`CUST_INFO_LEN`) | Strateji kimliği ve father ref. Aşağıdaki tabloya bakın. |
| `parentOrderbookId`, `expectedPrice` | | Yalnızca HFT içinde kalır, wire'a çıkmaz. |

**Passthrough düzeni** (`EnterOrder::updateExtraData`, çözümü `MsgConvert.cpp` `decodeStrategy`):

```
[0]     customerInfo (MessageType, 1 bayt)
[1]     'x'
[2..4]  strategyIdentifier (3 bayt; boşlukla doldurulur / kesilir)
[5]     'x'
[6..7]  strategyType (2 hane, ondalık)
[8..14] fatherOrderRef (7 bayt, FATHER_ORDER_REF_LEN)
```

- `customerInfo` (`Enumarations.h` `hft::enums::strategy::MessageType`):
  - `'0'` NoType, `'1'` UserOrder, `'2'` Morning, `'3'` Opening, `'4'` Evening, `'5'` TheoreticalOrder
  - `'6'` ChaseBait, `'7'` Chase, `'8'` QtyBarrier, `'9'` FastBarrier, `'B'` SecondRule, `'I'` PassivePositionClose, `'W'` Warrant
  - `OrderAccepted::sentByAlgo` ve `Strategy::checkAndSetSent` bu bayta göre karar verir.
- **Kimlik yalnız passthrough'tadır.** OUCH accept ve reject strateji bilgisini başka hiçbir alanda taşımaz. `strategyIdentifier` 3 bayta kesildiği için 3 karakterden uzun bir id dönüşte eşleşmez. ❓ doğrulanmadı: Pratikte id'lerin hep ≤3 karakter olduğu.
- **Father ref:** Passthrough'un son 7 baytıdır. Tavan/Taban rejectte `passThrough.substr(len-7)` ile okur.
  - `toSdkMsg`'e `fatherRef` verilirse passthrough yeniden kurulur. Verilmezse ve passthrough boşsa `UtilityClass::generateFatherOrderRef()` üretilir.
  - Tavan, ref'i önceden üretilmiş 100 000'lik havuzdan alır (`OuchManager::getNewFatherOrderRef`).
  - SDK bir emri bölerse bütün çocuklar aynı passthrough'u, dolayısıyla aynı father ref'i taşır.

### Kimlik: token / `client_order_id`

- **SDK yolu:** `toSdkMsg` `client_order_id`'yi **bilerek boş** bırakır. SDK 14 baytlık OUCH token'ı üretir ve bütün callback'lerde onu `client_order_id` olarak döner ("SDK-owned token" modeli; bkz. [maordersdk § Callback'ler](../maordersdk/README.md#callbackler)).
  - Strateji token'ı gönderim anında öğrenmez, `onAccepted` ile öğrenir.
  - Replace'te yeni id'yi HFT kendisi üretir: `UtilityClass::generateToken()`, 14 karakter `[0-9a-zA-Z]`.
- **OS yolu:** `OuchManager::enterOrder` havuzdan bir token atar (`tokens[token_index++]`), ama bu token yalnız `hftEnterOrder` sarmalayıcısında kalır; MARpc `EnterOrder` (network-sdk `sdk/Models/orders.fbs`) ve ouch-sdk `EnterOrder`'da token alanı yoktur. order-service emri kendi MAOrderSDK'sıyla, SDK'nın ürettiği token'la gönderir (`MAOSdkManager.cpp`, `msg.client_order_id.clear()`; bkz. [order-service/arayuzler](../order-service/arayuzler.md)).
  - Dolayısıyla HFT'ye dönen accept token'ı her iki yolda da **BIST wire token'ıdır**. Çift kayıt koruması bu eşitliğe dayanır (§4).
- **Stratejiye eşleme anahtarı:** `OuchManager::findStrategy` anahtarı `"<orderbookId>_<account>_<strategyIdentifier>_<strategyType>"` olarak kurar.
  - Bu, `StrategyManager` kayıt defterinin `unique_key`'idir (`Strategy::getStrategyKey` aynı formatı üretir).
  - Anahtarla bulunamazsa türev fallback'ine düşer: `StrategyManager::getStrategyByDerivative` (varant emirleri).

### `MsgConvert` (`namespace HftConvert`)

| Fonksiyon | Yön | Not |
|-----------|-----|-----|
| `toSdkMsg(EnterOrder&, account, fatherRef)` | HFT → SDK | `src`'yi değiştirir (passthrough). `client_order_id` boş. SMP, `open_close`, `display_quantity` set edilmez (SDK varsayılanı). Header yorumundaki "generates client_order_id if unset" ifadesi koda uymuyor. |
| `toSdkMsg(ReplaceOrder&, newId)` | HFT → SDK | `client_order_id` = eski token, `new_client_order_id` = `newId`. Hesap boş bırakılır, SDK mevcut emirden bulur. |
| `fromSdk(OrderAcceptedMsg)` | SDK → ouchSDK model | `initialQuantity = pre_trade_quantity`, `quantity` = wire'daki kalan miktar. Strateji kimliği passthrough'tan çözülür. |
| `fromSdk(OrderRejectedMsg)` | | Kod, metin, obid, hesap, passthrough. Wire reject'te bunlar yoktur; SDK gönderim kaydından doldurur. |
| `fromSdk(OrderExecutedMsg)` | | Yalnızca token, obid, miktar (lot), fiyat (raw), `match_id`. Side, hesap ve passthrough **yoktur**; çağıran taraf `OrderRegistry`'den çözer. |
| `fromSdk(OrderCanceledMsg / OrderReplacedMsg)` | | Replace mesajı `oldToken` = `previous_client_order_id` taşır. |

Gelen modeller (`src/Messages/IncomingMessages/Ouch/`):
- `Hft::OrderAccepted`: `sdkOrderAccepted`, `customerInfo` (passthrough[0]), `executedQuantity`, `expectedPrice`, `parentOrderbookId`.
  - Passthrough >1 bayt ise `parentOrderbookId` = kendi obid'i olur.
  - `updateOrder` replace'i uygular, `executeOrder` kalan miktarı düşer.
- `Hft::OrderRejected`: `quantity` alanı father-ref muhasebesi içindir. SDK yolunda `m.quantity`'den set edilir.

## 2. Gönderim

### Yol seçimi

Bütün strateji gönderim noktaları aynı kalıbı kullanır:
- Örnekler: `HftClassic.cpp` `wrapEnterOrder`, `Strategy::closePosition`, `Strategy::cancelAllOrders`, `HftMaxPrice`/`HftMinPrice`/`HftWarrant*` içindeki satır içi kopyalar, `GUIManager::handleEnterOrder`.
- Kalıbın kendisi: [README](README.md#emir-gönderme-deseni).

| Koşul | `enterOrder` sonucu | Ne olur |
|-------|---------------------|---------|
| `maosdk` null | — | OS yolu |
| Yerel validasyon reddi (1001–1006) | `false` + **senkron `onRejected`** | `ownsAccount` false ise emir **ayrıca OS yoluna da gider** (Şüpheli #1) |
| Bağlı bir connection hesabın sahibi değil (handoff öncesi, OUCH koptu) | `false`, `onSdkError(1)` | `ownsAccount` false → OS yolu |
| Bölünmesi gereken emir, hesap için route yok | `false` + `onRejected(code 1, token "")` | OS yolu da (Şüpheli #1) |
| Connection var, encode/send/duplicate hatası | `false` + `onRejected(4/5/6/15)` | `ownsAccount` true → **gönderilmez** |
| Başarılı | `true` | Tamam |

- **`ownsAccount(account)`** (MAOrderSDK): `is_connected()` olan bir OUCH connection hesabı `allowed_accounts`'unda taşıyorsa (ya da FIX engine sahipse) true döner.
  - "Sahiplik" bağlantı canlılığına bağlıdır. Handoff sonrası OUCH koparsa hesap yeniden OS yoluna düşer (§6).
- **`ownsOrder(token)`:** Token SDK'nın `wire_by_client` haritasında ya da split parent tablosunda varsa true döner.
  - Replay ile öğrenilen (adopt edilen) emirler de bu haritaya girer (`on_wire_accepted` else dalı).
  - Bu yüzden handoff öncesi açılmış bir emir, replay'den sonra SDK'nın olur.
- **GUI manuel emri** (`GUIManager::handleEnterOrder` / `handleTheoreticalOrder`):
  - `channel == PROTOCOL_FIX` ise **her zaman** OS yolu; SDK yolu yalnızca OUCH içindir.
  - `levelCount > 1` ise ilk emirle birlikte `levelCount-1` ek emir gider. Her biri bir tick (`ItchSdkClient::getTickSize`) daha pasif fiyattadır.
  - GUI emirleri **replay gate'e takılmaz** (gRPC thread'inde, kontrol yok).

### Bölme (max emir değeri)

- Bölme SDK içindedir (`MAOrderSDK::enterOrder`, #15). HFT bölme yapmaz; eski `OuchManager` matematiği SDK'ya taşındı.
- Limitler açılışta DB'den yüklenir (`HftMain.cpp`, `setInstrumentLimits`):
  - `max_order_value`: tam TL
  - `decimal_count`
  - `is_brut_takas`
- Hesap, raw birimle yapılır:
  - `limit_raw = max_order_value × 10^decimal_count`
  - `quantity > limit_raw / price` ise çocuk başına `max_child_qty = limit_raw / price` lot olur, kalan miktar son çocuğa gider.
- Önce statik `order_hard_cap_try` (config `sdkOrderHardCapTry`, tam TL) kontrol edilir. Aşılırsa 1003 ile reddedilir. Kap 0 ise **her emir** 1003 alır.
- HFT parent id vermediği için (`client_order_id` boş) SDK `split_parents_` kaydı tutmaz:
  - Her çocuk ayrı token'la ayrı bir emir olarak `onAccepted`'e düşer.
  - Çocukları birbirine bağlayan şey yalnızca father ref'tir.
  - Cancel/replace çocuk token'ı ile, tek tek yapılır.
- OS yolunda bölmeyi order-service'in kendi MAOrderSDK'sı yapar (order-service de `setInstrumentLimits` çağırır, `MAOSdkManager.cpp`). ❓ doğrulanmadı: order-service'in HFT emrine aynı limit tablosunu uyguladığı.

### Replace / cancel

- **Strateji kalıbı:** `if (!maosdk->replaceOrder/cancelOrder(...)) { if (!maosdk->ownsOrder(token)) OuchManager::...; }`
- **GUI kalıbı** (`handleCancelOrder` / `handleReplaceOrder`): Önce `ownsOrder` sorulur, sahipse SDK, değilse OS yolu. Sebep: FIX emirleri SDK'da bilinmez.
- **Replace semantiği:**
  - Fiyat 0 = fiyat korunur, miktar 0 = miktar korunur. GUI ikisinin birden pozitif olmasını reddeder.
  - `OuchManager::replaceOrder` (OS yolu) no-op replace'i (aynı miktar veya aynı fiyat) göndermez ve passthrough boşsa `"10"` yazar. SDK yolunda bu no-op filtresi yoktur.
- **SDK yerel hataları** (`onSdkError`, **ret callback'i yok**):
  - 9: bilinmeyen token
  - 10: emrin connection'ı yok veya kopuk
  - 4: duplicate yeni id
  - 8: boş id
  - 12: bölünmüş emrin miktarı değiştirilemez
  - Bu durumda `false` döner. `ownsOrder` true olduğundan OS yoluna da gitmez; **cancel/replace sessizce düşer**.

### Cancel-all ve pozisyon kapatma

- **`Strategy::cancelAllOrders(side, notifyWhenComplete)`:** `orderMap`'teki, kalan miktarı > 0 olan her emre cancel gönderir.
  - Side seçimi XOR ile yapılır. `'B'` yalnız alışları, `'S'` hem `S` hem `T` (short) emirlerini iptal eder.
  - `notifyWhenComplete` ise token'lar `pendingCancelTokens`'a yazılır. Her cancel/reject dönüşü `onCancelResponse` ile düşülür. Boşalınca `cancelAllOrdersFinished` → `closePosition()` çalışır.
- **GUI CancelAll** (`GUIManager` dispatch):
  - `orderbookId == 0`: `stopAllStrategies()` (**hesap filtresi yok, bütün çalışan stratejiler durur**) + `cancelAllStrategyOrders(account)` (yalnız o hesabın stratejileri).
  - Aksi halde `StrategyManager::cancelAllOrders`: `unique_key` ile tek strateji, side 0 = iki taraf.
- **`Strategy::closePosition`:** Bakiyeyi kapatmak için `QtyBarrier` tipli emir gönderir. Fiyat:
  - satış (long kapatma): taban fiyatı
  - alış (short kapatma): tavan fiyatı

## 3. Dönüş (olaylar → strateji → GUI)

### SDK yolu callback'leri (`HftMain.cpp`, `cbs.*`)

| Callback | Thread | Registry | Strateji | GUI (`StrategyServiceImpl::enqueue*`) |
|----------|--------|----------|----------|----------------------------------------|
| `onAccepted` | Emrin OUCH recv thread'i | `OrderRegistry::addAcceptedOrder(token)`. İlk ekleyen sahip olur (`try_emplace`). | Sahipse ve `claimGlobalAcceptedToken` true ise `addOrder` + `addSecondRuleOrder` | Duplicate değilse `ACCEPTED` (pre-trade qty + latency ns) |
| `onRejected` | Wire reject: recv thread. **Yerel ret: `enterOrder`'ı çağıran thread** (AlgoWorker veya gRPC), senkron. | — | `findStrategy` (passthrough'tan) → `rejectOrder` + `onCancelResponse` | Her zaman `REJECTED` |
| `onExecuted` | Recv thread **veya combiner açıksa ITCH client thread'i** | `getAcceptedOrder(token)`; yoksa log + düşer | `executeOrder(exec, side)` | **Yok** (bilerek) |
| `onWireExecuted` | Her zaman emrin recv thread'i | Kayıt yoksa düşer | — | `EXECUTED` |
| `onReplaced` | Recv thread | `getAcceptedOrder(prev)`, sonra `rekeyAcceptedOrder(prev → new)` | `updateOrder` | `REPLACED`. `prevPrice` mutasyondan **önce** yakalanır; GUI replace'i bununla eşler. |
| `onCanceled` | Recv thread | `getAcceptedOrder(token)` | `deleteOrder(can, side)` + `onCancelResponse` | `CANCELED` |
| `onReplayCompleted` | Recv thread ❓ doğrulanmadı | — | `StrategyManager::notifyUserReplayCompleted` (§4) | — |

- **`OrderRegistry`** (`src/Clients/OrderRegistry.h`): `client_order_id` → `shared_ptr<Hft::OrderAccepted>` tutar, tek mutex'le korunur.
  - **Kayıtlar hiç silinmez.** Bu kasıtlıdır: strateji depth'leri bu nesnelere ham pointer tutar. Bellek gün boyu büyür.
  - Replace'te nesne aynı kalır, yalnızca anahtarı değişir.
- **Strateji kimliği:**
  - Accept ve reject'te passthrough'tan çözülür.
  - Execute, cancel ve replace'te registry'deki orijinal accept'ten alınır. Replace cevabının passthrough'u kimlik taşımaz (`StrategyServiceImpl.cpp` yorumu: `"I0"`).
- **`internal_ouch` kolonu:** `OuchManager::getOrderTokenToOuchClientUsernames()[token] = m.ouch_username` ile doldurulur (accept ve replace'te). GUI'deki "hangi OUCH kullanıcısı" bilgisi buradan gelir.
- **Strateji içi işlem:** Callback'ler strateji metotlarını doğrudan çağırır; kuyruğa atmaz. Stratejiler `buySellInfoMutex` (`recursive_timed_mutex`) ile korunur.
  - Yerel ret, stratejinin kendi gönderim kodunun **içinden** re-entrant olarak `rejectOrder`'ı tetikler. Mutex recursive olduğu için kilitlenmez.
  - Strateji özelindeki işleme: [strateji-cekirdegi.md](strateji-cekirdegi.md).

### Combiner etkisi

- **`combinerEnabled` açıkken:**
  - Kendi emrimizin ITCH'te görülen fill'i `onExecuted` ile ITCH client thread'inden, OUCH'tan önce gelebilir. OUCH tekrarı SDK içinde emilir.
  - Stratejiye fill bir kez ulaşır. GUI'ye giden `onWireExecuted` ise her zaman OUCH'tan, accept'le aynı thread'den gelir; emir başına sıra korunur.
- **Combiner'a girmeyen emirler:** Yalnızca bu oturumda `enterOrder` ile girilmiş emirler combiner'a alınır. Replay ile adopt edilenler girmez, onlar yalnız OUCH'tan dolar.
- **Bağlantı kopması:** İzlenen bütün emirler zehirlenir (`poison_all`).

### OS yolu eşdeğerleri (`OuchManager.cpp`, `ouchSDK::order*` serbest fonksiyonları)

- **Thread:** ouch-sdk'nın tek response delegate'i (`OrderStreamClient.cpp` `handleIncomingMessage`). ❓ doğrulanmadı: Bunun network-sdk istemci recv thread'i olduğu. `orderUserDisconnected` (handoff) da aynı thread'de çalışır.
- **Ayrı harita:** OS yolu `OuchManager::acceptedOrders` (`unique_ptr`, silinmez) kullanır; `OrderRegistry`'ye **yazmaz**.

| Olay | Davranış |
|------|----------|
| `orderAccepted` | `quantity = initialQuantity` yapılır. Strateji bulunursa `addAcceptedOrder`, sonra `claimGlobalAcceptedToken`; ikisini de geçerse `addOrder` + `addSecondRuleOrder`. Strateji yoksa yalnız haritaya eklenir, **claim edilmez**. |
| `orderRejected` | `rejectOrder` + `onCancelResponse` + `addGlobalRejectedToken`. **`quantity` set edilmez (0)**. |
| `orderExecuted` | Harita lookup → `executeOrder`, ardından `addGlobalExecutedMatch(matchId_token8)`. Bu set hiçbir yerde **okunmaz**; okuyan tek yer eski `OuchWorker`. |
| `orderReplaced` | `renameAcceptedOrder(old → new)` başarısızsa olay **stratejiye gitmez**. |
| `orderCanceled` | `deleteOrder` + `onCancelResponse` |

- OS yolu olayları HFT'nin GUI kuyruğuna (`enqueue*`) **konmaz**. ❓ doğrulanmadı: GUI'nin bu emirleri order-service → trade-data-app akışından gördüğü.
- **Restart sonrası doldurma:** `ItchManager::start` Glimpse bitince ayrı bir thread açar. Bu thread stratejiler DB'den yüklenene kadar (en çok 300 s) bekler, sonra `OuchManager::getAllOrders()` çağırır.
  - order-service günün emirlerini toplu döner (`AllOrdersResponse`), olaylar yukarıdaki fonksiyonlardan geçer.
  - `getAllOrders` cevap gelene kadar `ouchSDKCallMutex`'i tutar (Şüpheli #6).

### GUI'ye akış (`FetchOrders`)

- `enqueue*OrderEvent` olayları `internalOuchOrdersQueue`'ya koyar.
- `FetchOrders` stream'i ilk açılışta 3 s bekler. Sonra kuyruğu 50'lik batch'ler halinde `buildStrategyOrderFromEvent` ile `StrategyOrder` proto'suna çevirip yazar.
- Yazma başarısızsa batch `unsentOrderEvents`'te bir sonraki stream'e saklanır.
- Execute, cancel ve replace olayları build anında `OrderRegistry`'ye tekrar bakar. Bu yüzden OS yolu emirleri bu builder'dan geçemez.
- Wire alanları: [komutlar-ve-grpc.md](komutlar-ve-grpc.md).

## 4. Handoff — HFT tarafı

### Akış

1. **Açılış:** MAOrderSDK `start()` edilir, `connectUser` çağrılmaz (`HftMain.cpp` adım 8).
   - `[[ouch_users]]`'daki **`isActive=true`** girişler `OuchConfig`'e kullanıcı olarak yüklenir ve account route'larına yazılır, ama bağlanmaz.
   - `isActive=false` girişler yalnızca recv-thread ayar tablosudur.
2. **Bildirim:** order-service, MARpc ile `UserDisconnected` gönderir. HFT `ouchSDK::orderUserDisconnected`'ı çağırır.
   - Callback `disconnect_callback_mutex_` altında çalışır, kullanıcılar sırayla işlenir.
   - İlk callback'te (process ömründe **bir kez**, `static replaysRegistered`) `registerExpectedReplays(total)` çağrılır.
3. **Kullanıcı kaydı:** `maordersdk::OuchUser`, handoff verisinden kurulur:
   - ip/port, şifre, `allowed_accounts`
   - `market = Equity` sabit; mesaj pazar taşımaz
   - recv pin/policy/prio: önce global `sdkRecv*`, sonra `[[ouch_users]]`'taki aynı isimli girişten override
   - Secondary endpoint **yoktur**.
   - Onload derlemesinde socket, `onloadStackName` stack'inde açılır (`OnloadStackScope`).
4. **Login:** `maosdk->connectUser(u)` çağrılır. `Ok` ya da `AlreadyConnected` dışındaki sonuçta 4 kez daha denenir; denemeler arası 1, 2, 3, 4 s beklenir (toplam ≤10 s uyku).
   - Hepsi başarısızsa yalnızca WARN log basılır; o kullanıcı için OUCH yoktur.
   - Bu callback ouch-sdk thread'ini bloke eder (Şüpheli #5).
   - Kullanıcı adı `OuchConfig`'de zaten kayıtlıysa (`isActive=true`), `connectUser(OuchUser)` **mevcut connection'ı config'deki ip/şifreyle** kullanır; handoff verisi yok sayılır (MAOrderSDK `connectUser(const OuchUser&)`).
5. **Replay:** Login sonrası SDK günün mesajlarını replay eder.
   - Kendi gönderdiği kayıtta olmayan token'ları adopt eder: `orders_by_token`/`wire_by_client`'a yazar, `client_order_id` = wire token.
   - `replay_quiet_window_ms` (varsayılan 10 000 ms) boyunca yeni SequencedData gelmezse ve en az bir heartbeat görülmüşse `onReplayCompleted` tetiklenir.

### Replay gate (`StrategyManager`)

- **Durum:** `pendingReplays` (int) ve `allUsersReplayDone` (atomic bool). Stratejiler `Strategy::ouchReplayComplete()` ile bakar. Gate şunları kapatır:
  - HftClassic, Tavan, Taban, Teorik: ITCH olay işleme girişi
  - HftClassic: başlangıç emirleri, pasif TP, second-rule
  - Varant / Varant Toplu: gönderim noktaları
- **`registerExpectedReplays(n)`:** `pending = n`, `done = (n == 0)`. Gate açıksa **yeniden kapanır**. Header'daki "Never reverts" yorumu bu yüzden yanlış.
  - İlk çağrıda tek seferlik 60 s güvenlik zamanlayıcısı kurulur. Süre dolduğunda gate hâlâ kapalıysa zorla açılır (`LOG_CRIT ... TIMEOUT`).
- **`notifyUserReplayCompleted`:** `pending` 1 azalır, ≤0 olunca gate açılır.
  - Sonraki logon'lardaki replay'ler (yeniden bağlanma) sayacı negatife indirir; gate'i tekrar kapatmaz.
- **Zero-handoff watchdog** (`startPeriodicJobs`): Açılıştan 20 s sonra `pending == 0` ve gate kapalıysa gate açılır.
- **Tipik gün:** HFT 09:40'tan önce açılır, watchdog 20 s'de gate'i açar. Stratejiler OS yolundan çalışır. Handoff gelince gate kapanır. Replay'ler bitince (en az ~10 s quiet window) açılır ve yeni emirler SDK yolundan gider.
- **Gate globaldir:** Tek bir kullanıcının handoff'u, başka hesaplardaki stratejileri de durdurur.

### Çift kayıt koruması

Aynı accept iki kez gelebilir:
- OS yolundan (canlı veya `getAllOrders`)
- Handoff replay'inden (SDK yolu)

İki yolun haritaları ayrıdır (`OuchManager::acceptedOrders` ve `OrderRegistry`). Ortak tek kapı `OuchManager::globalAcceptedTokens`'tır:
- `claimGlobalAcceptedToken` insert eder ve yalnızca ilk çağırana `true` döner.
- has + add tek kilit altındadır; iki thread aynı anda "ilk" olamaz.

| Senaryo | Sonuç |
|---------|-------|
| OS accept önce, replay sonra | OS yolu claim eder ve stratejiye ekler. Replay accept registry'ye girer (owned), claim başarısız → `duplicate` → depth'e ve GUI'ye eklenmez. Execute/cancel lookup'ı registry'deki kopyadan yapılır; stratejide eşleme token iledir. |
| Replay önce, OS sonra | Tersi: SDK nesnesi stratejiye gider, OS nesnesi haritada kalır, stratejiye dokunmaz. |
| Aynı token registry'de zaten var | `addAcceptedOrder` false → `duplicate`. Yeni nesne atılır, eski korunur. |
| Strateji bulunamadı | Kayıt yapılır, claim **yapılmaz**. GUI'ye gider. |

**Kapsam dışı:** Bu koruma yalnızca accept içindir. Replay, handoff öncesi OS yolunda zaten işlenmiş **execute**'ları da yeniden getirir. SDK `onExecuted` bunları match_id kontrolü yapmadan stratejiye iletir (Şüpheli #2).

### Handoff öncesi açılmış emirlerin sahipliği

- **Replay'den önce:** Emir yalnız OS yolunda bilinir; `ownsOrder` false döner.
  - Bu aralıkta stratejinin cancel'ı OS yoluna gider. Ancak order-service o OUCH kullanıcısından logout olmuştur. order-service'in SDK'sı emrin kapalı connection'ını görür → `onSdkError(10)`; order-service yalnız log basar, HFT'ye cevap gitmez ([order-service/sdk-ve-oturumlar](../order-service/sdk-ve-oturumlar.md)).
- **Replay'den sonra:** Emir SDK'da adopt edilmiştir (`ownsOrder` true). Cancel ve replace SDK yolundan gider; dönüş olayları `OrderRegistry`'deki replay kopyasıyla çözülür ve aynı stratejiye eşlenir.
- **Combiner:** Adopt edilen emirler combiner'a girmez.

## 5. Ret ve hata kodları

### MAOrderSDK yerel retleri (`onRejected`, BIST'e gitmez)

| Kod | Sebep | Kaynak |
|-----|-------|--------|
| 1 | Bölünecek emir için hesabın route'u veya connection'ı yok (split yolu) | `enterOrder` |
| 4 | Duplicate `client_order_id` | `notify_send_failure` |
| 5 | Encode hatası | 〃 |
| 6 | Socket yazımı başarısız | 〃 |
| 15 | Token-assignment callback'i exception attı | 〃 |
| 1001 | Enstrüman limit tablosunda yok | `enterOrder` |
| 1002 | Brüt takas enstrümanı | 〃 |
| 1003 | `order_hard_cap_try` (tam TL) aşıldı | 〃 |
| 1004 | Tek lot bile `max_order_value`'nun üstünde | 〃 |
| 1005 | Fiyat 0 (market emri değil) | 〃 |
| 1006 | Miktar 0 | 〃 |

- `onSdkError` kodları (ret değil, yalnız WARN log): 1 hesap sahibi yok, 8–12 cancel/replace hataları (§2), 7 Onload, 13 combiner.
- Bölünmemiş emirde "connection yok" durumu **ret üretmez**, yalnızca `false` döner.

### BIST kodları (HFT'nin tanıdıkları, `src/Globals/GlobalConstants.h`)

| Kod | Sabit | HFT davranışı |
|-----|-------|---------------|
| `-420177` | `ME_MATCH_ORD_NOT_FOU` (emir bulunamadı; tipik olarak zaten gitmiş bir emre cancel/replace) | HftClassic `checkAndSetSent`'i atlar. Tavan ve Taban rejectte hemen döner (father-ref muhasebesine dokunmaz). |
| `-850002`, `-850004`, `-850044`, `-850064` | PTRM; `isPtrmRejectCode` | Taban (`HftMinPrice::rejectOrder`) ilk redde `stopOnPtrmReject` çağırır ve durur; father-ref muhasebesi önce yine çalışır. Varant Toplu bu kodlar için ret metni üretir. HftClassic ve Tavan `isPtrmRejectCode` kullanmaz (grep). Kod listesi ve AlgoProd farkı: [borsa-kurallari § PTRM](../../00-genel/borsa-kurallari.md#ön-işlem-risk-ptrm-ve-diğer-ret-kodları). |

MAOrderSDK `docs/reject-codes.txt` ek BIST kodlarını listeler: `-420131` fiyat limiti, `-800002` duplicate token, `-850008` geçersiz hesap, `-420579` emir değeri çok büyük vb. HFT bunlar için özel bir dal içermez; genel `rejectOrder` yolundan geçerler.

**Genel ret etkisi** (`Strategy::checkAndSetSent`):
- `customerInfo ≥ '8'` (QtyBarrier ve sonrası) → `sent = false`, strateji yeniden gönderebilir.
- Chase → `chaseSent = false`.
- PassivePositionClose → `autoCloseWaitingAccept = false`.
- Tavan/Taban father-ref'ten `getQuantity()` kadar beklenen miktarı serbest bırakır.

Strateji özelindeki ayrıntı: [taban](../../20-stratejiler/taban.md#tolerans-ve-durma), [tavan](../../20-stratejiler/tavan.md), [hft-classic](../../20-stratejiler/hft-classic.md), [varant-toplu](../../20-stratejiler/varant-toplu.md).

## 6. Kopma senaryoları

| Senaryo | Ne olur (koddan) |
|---------|------------------|
| **OUCH koptu** (handoff sonrası) | `is_connected` false olur, combiner `poison_all` yapar. HFT `onUserDisconnected`/`onHeartbeatTimeout` callback'lerini **set etmez**. SDK kendiliğinden yeniden bağlanmaz (heartbeat thread yalnızca bağlı olanlara heartbeat yollar). Hesabın başka canlı connection'ı varsa round-robin onu kullanır. Yoksa `ownsAccount` false olur ve **yeni emirler OS yoluna düşer**. Açık emirlerin cancel/replace'i `ownsOrder` true olduğu için OS'ye gitmez; `onSdkError(10)` ile düşer. order-service'te hesabın bağlı başka OUCH kullanıcısı yoksa SDK `onSdkError(1)` + `false` döner; ret gitmez, emir sessizce kaybolur ([order-service/sdk-ve-oturumlar](../order-service/sdk-ve-oturumlar.md)). Kullanıcıyı geri almanın tek yolu yeni bir `orderUserDisconnected`'dır. `replaysRegistered` statik olduğu için ikinci tur gate'i yeniden kurmaz. |
| **order-service koptu** | Handoff sonrası SDK yolu etkilenmez. OS yolu (handoff öncesi emirler, FIX kanallı GUI emirleri, OUCH kopmuş hesaplar) çalışmaz. ❓ doğrulanmadı: ouch-sdk/MARpc'nin yeniden bağlanma ve login davranışı. `OuchManager` constructor'ı login başarısızsa exception atar; açılışta order-service yoksa HFT kalkmaz. Handoff hiç gelmezse 20 s watchdog gate'i açar ve stratejiler OS yoluna emir dener. |
| **Replay sırasında** | Gate kapalıdır; stratejiler ITCH işlemez, emir göndermez. GUI manuel emirleri **geçer**. Replay'deki accept'ler §4 tablosuna göre ayıklanır; execute'lar ayıklanmaz. 60 s içinde bütün kullanıcılar `onReplayCompleted` vermezse gate zorla açılır. Login'i başarısız olan bir kullanıcı replay vermediği için gate 60 s'yi bekler. |
| **connectUser hepsi başarısız** | O kullanıcının hesapları OS yolunda kalır (`ownsAccount` false). order-service ise kullanıcıdan logout olmuştur (2026-08-03 olayında gün boyu OUCH yoktu; retry o olaydan sonra eklendi). |

## Şüpheli davranışlar (koddan)

1. **Handoff öncesi yerel ret + yedek yol.** Yerel validasyon (1001–1006) ve "split ama route yok" (kod 1) bağlantı kontrolünden önce koşar, `onRejected` üretir ve `false` döner. Çağıran taraf `ownsAccount` false gördüğü için aynı emri OS yoluna da gönderir. Sonuç:
   - Strateji ret alır (HftClassic `sent=false` yapar, Tavan/Taban father-ref miktarını serbest bırakır), emir ise order-service'ten gider.
   - Hard-cap (1003) handoff öncesi fiilen bypass edilir.
   - Split-route retinde token boş string'dir.
2. **Replay execute'ları dedup edilmiyor.** Handoff öncesi OS yolunda stratejiye işlenmiş fill'ler, replay'de SDK `onExecuted` ile tekrar `executeOrder`'a gelebilir. Stratejilerde match_id kontrolü yoktur (grep). `globalExecutedMatches` yazılır ama okunmaz. ❓ doğrulanmadı: SDK'nın replay'i hangi sequence'tan istediği; tekrarın fiilen oluşup oluşmadığı.
3. **OS yolu ret miktarı 0.** `ouchSDK::orderRejected` `OrderRejected::quantity`'yi set etmez; Tavan/Taban father-ref'ten 0 lot serbest bırakır.
4. **`isActive=true` kullanıcıda handoff verisi yok sayılır.** `MAOrderSDK::connectUser` aynı isimli kayıtlı bağlantıyı yeniden kullanır; config'deki ip/şifre geçerli olur. Müşteri config'lerinde (Algo-Setup `development`, 2026-10-22) `[[ouch_users]]` girişi yok; pratikte tetiklenmez.
5. **Handoff ouch-sdk thread'ini bloke ediyor.** `orderUserDisconnected` retry uykuları (≤10 s) ve blocking `connectUser` süresince aynı thread'deki OS yolu olayları bekler.
6. **`getAllOrders` mutex tutuyor.** `ouchSDKCallMutex`'i cevap gelene kadar tutar. Bu sürede `OuchManager::enterOrder/replaceOrder/cancelOrder` ve `getInstrument*` (strateji fiyat/limit okumaları) bloklanır.
7. **Senkronizasyonsuz harita.** `orderTokenToOuchClientUsername` (`unordered_map`) recv thread'lerinden yazılıp gRPC `FetchOrders` thread'inden okunur; kilit yok.
8. **Lock-free route okuması.** `account_routes_` SDK'da kilitsiz okunur. `connectUser(OuchUser)` ise insert eder. Watchdog gate'i açtıktan sonra gelen handoff'ta ya da gate'siz GUI emirlerinde eşzamanlı okuma ve yazma olabilir.
9. **Havuz taşması.** `OuchManager::tokens` ve `refs` havuzları (her biri 100 000) sarmadan `++` ile indekslenir; taşma tanımsız davranıştır. `refs` Tavan'ın her girişinde tüketilir.
10. **SMP gönderilmiyor.** SDK yolunda SMP alanları gönderilmez (`toSdkMsg`, Unknown). Eski `EnterOrder::toBISTBytes` SMP'yi `WithinaMember`/`CancelBoth` ile gönderiyordu. Kasıtlı mı, bilinmiyor.
11. **`client_cat` varsayılanı.** Alan-alan `EnterOrder` ctor'unun `client_cat` varsayılanı 1'dir (House). `DE` hesaplar için 0'a çeviren yalnızca mesaj-parse ctor'u. ❓ doğrulanmadı: Strateji emirlerinde `DE` hesabın House olarak gidip gitmediği.
12. **CancelAll(obid=0) bütün hesapları durduruyor.** `stopAllStrategies` hesap filtresi uygulamaz.
13. **Pozisyon kapatmada bekleme listesi siliniyor.** `closeThePositionForSingleStock` iki tarafta `cancelAllOrders(..., true)` çağırır. İkinci çağrı birincinin `pendingCancelTokens`'ını temizler.
