---
kapsam: AlgoProd emir yolu — OuchManager (login, send, emir modelleri, kanal, token/passthrough), olayların stratejiye dönüşü, AccountDepth ve pozisyon, timeout, fiyat ölçeği, ret kodları/PTRM, serbest emir (Algo_User), order-service kopması; master farkı ve add-order-sdk
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading          # prod binary'si
    branch: master
    commit: aa150ee
  - repo: AlgorithmicTrading          # merge edilmedi
    branch: add-order-sdk
    commit: 7d7f705
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# AlgoProd emir yolu

Kod kökü `algoSrc/`. Giriş noktası [README](README.md). Sözleşmeler başka yerde, burada tekrar edilmiyor:
- ouch-sdk API'si, callback thread'i, model alanları: [ouch-sdk/README.md](../ouch-sdk/README.md)
- order-service'in MARpc tarafı, risk retleri: [order-service/arayuzler.md § 3](../order-service/arayuzler.md#3-marpc-sunucusu-orderserver), [risk.md § 7](../order-service/risk.md#7-reddin-istemciye-dönüşü)
- HFT karşılığı (karşılaştırma için): [hftsrvprod/emir-yasam-dongusu.md](../hftsrvprod/emir-yasam-dongusu.md)
- Strateji karar mantığı: [arbitraj](../../20-stratejiler/arbitraj.md), [vwap](../../20-stratejiler/vwap.md), [fon-takibi](../../20-stratejiler/fon-takibi.md)

## 1. Özet

```
Strateji / GUIManager::dispatchOrders
  → OuchManager::send / cancelOrder / replaceOrder        (çağıran thread, senkron cout + kuyruğa yazma)
  → ouchSDK::enterOrder|cancelOrder|replaceOrder → MARpc → order-service → MAOrderSDK → BIST
BIST → order-service → MARpc → ouch-sdk callback thread
  → ouchSDK::order* (OuchManager.cpp serbest fonksiyonlar) → OuchManager::algoOrder*
  → TradableInstrument::order* → Userbook (AccountDepth) → Subscriber kuyrukları → strateji tryPop
```

- development'ta **BIST'e doğrudan yol yoktur**; her emir order-service'ten geçer. HFT'deki gibi handoff, MAOrderSDK ve replay gate yoktur (`orderUserDisconnected` yalnız `cout` basar). Bunlar `add-order-sdk`'da gelir (§11).
- Olaylar ouch-sdk'nın **tek callback thread'inde** işlenir. `algoOrder*` içindeki her şey (userbook güncellemesi, subscriber bildirimleri, log) bu thread'i tutar. Thread modeli ayrıntısı bu dosyanın kapsamı dışında.

## 2. Açılış ve login (`OuchManager::start`)

Sıra (`Application::runTests` içinde ITCH hazır olduktan sonra):

1. `sleep 3000 ms`.
2. `startOuchStreaming` → `ouchSDK::startOuchStreaming(ouchIp, ouchPort)`. Connect hatası sessizdir.
3. `login()` → `ouchSDK::login(ouchUsername, ouchPassword, Application::AlgoTrading)`. **Timeout yok.** order-service'e ulaşılamazsa burada sonsuza kadar bekler; `GUIManager` ve stratejiler hiç başlamaz (K-151).
   - network-sdk decoder'ı uygulama 2 ile 3'ü yer değiştirdiği için order-service bu login'i `APP_UNKNOWN` görür (K-149, [arayuzler § 3.2](../order-service/arayuzler.md#32-istek-tipleri)).
4. Login `true` ise:
   - `OrderbookManager::createUserbooks` → `OuchManager::fillStrategyInfosMap` (`ouchSDK::getStrategyInfo`, bloklar) → her kayıt için `strategyInfosMap`'e ekler ve userbook açar (§5). `position > 0` olan kayıtlar için "önceki pozisyon" istatistiği üretilir (§5.3). Sonunda `isStrategyInfoMapFilled = true`.
   - `ouchSDK::getAllOrders()`: günün olayları aynı callback'lerden geçer (replay). Dönüşte hepsi işlenmiştir.
   - `mark_replay_completed()`: `replay_completed` development'ta **hiç okunmaz**. ⚠ master'da combiner'ı açar (§10).
5. Login `false` (yalnız 401): `"Failed at ouch server login!"` loglanır, açılış **devam eder**. `isStrategyInfoMapFilled` hiç `true` olmaz. Bundan sonra gelen **bütün olaylar** `"Strategy Info Map is not filled"` uyarısıyla atılır, emirler ise yine gönderilir.

Stratejiler `StrategyManager.start()` ile **replay'den sonra** yaratılır. Bu yüzden replay olayları userbook'u doldurur ama strateji subscriber'larına düşmez.

## 3. Emir modelleri (`Transactions/Order/`)

Üçü de bir ouch-sdk modelini (`shared_ptr`) sarar. Wire alanları ve ölçekleri için: [ouch-sdk § 6](../ouch-sdk/README.md#6-model-sınıfları-includemodels).

### 3.1 Kimlik: üç ayrı "token"

| AlgoProd'daki isim | Ne | Nerede üretilir | Wire'da |
|--------------------|----|-----------------|---------|
| `EnterOrder::orderToken` (= `getOrderId()`), olaylarda `OuchInterface::token` (= `getOrderToken()`) | AlgoProd'un **istemci token'ı**: 14 karakter, `[0-9A-Za-z]` | `OrderUtility::createToken` (`mt19937`, açılışta ns zamanla seed) | Yalnız `passThrough` olarak. Wire'da istemci token alanı yoktur. |
| Olaylarda `OuchInterface::orderId` (= `getOrderId()`), koddaki yorumlarda "Borsa Token" | order-service/MAOrderSDK'nın atadığı emir token'ı (ouch-sdk `orderToken`) | MAOrderSDK | `OrderAccepted.orderToken` ile ilk kez öğrenilir; cancel/replace bununla yapılır |
| `itchOrderId` | BIST order id (ouch-sdk `OrderAccepted.orderId`) | BIST | ITCH ile eşleme |

- `passThrough` = 14 karakterlik istemci token'ının kendisidir (BIST customer info alanı 15 karakter). Strateji kimliği passthrough'ta **kodlanmaz** (HFT'den farklı). ⚠ `add-order-sdk`'da HFT biçimine geçer (§11).
- `EnterOrder(const EnterOrder&, isNewToken=true)` kopya yapıcısı varsayılan olarak **yeni token** üretir. `OuchManager::send(EnterOrder)` kopyayı `isNewToken=false` ile alır.
- Kopya yapıcı ouch-sdk modelini **paylaşır** (`sdkEnterOrder = enterOrder.getSDKEnterOrder()`) ve paylaşılan modelin passthrough'unu ezer (Şüpheli).
- `EnterOrder(obInfo, SDKEnterOrderPtr)` yapıcısı `passThrough.substr(14, 16)`'yı `stoi` ile emir tipi sayar. 14 karakterlik passthrough'ta bu `std::invalid_argument` fırlatır. Çağıran yok (ölü kod).

### 3.2 `EnterOrder` alanları

| Alan | Kaynak | Not |
|------|--------|-----|
| `account` | strateji: `exchangeInfo`; GUI: `Exchange_Info` | Hesap adı |
| `orderbookId` | `TradableInstrument::getInstrumentId()` | ITCH orderbook id |
| `side` | `Enumaration::Side` (`'B'/'S'/'T'`) doğrudan cast | ouch-sdk `Side` ile aynı karakterler |
| `quantity` | lot | |
| `price` | `long` → ouch-sdk `int32` | **raw**, §6 |
| `timeInForce` | `convertToOuchTIF`: Day→DAY, FaK→IOC, FoK→FOK, diğer→DAY. GUI yolu hep DAY. | |
| `strategyType` | `convertToOuchStrategy(MyOrderType)`: User→1, WarrantTracker→**13** (ouch-sdk `WARRANT`), BSRatio→AKD(3), MovingAverage→5, Arbitrage→6, VolumeStrategy→VWAP(7), FundTracker→10, diğer→USER(1). GUI yolu `Strategy_Type`'ı aynen kullanır. | order-service bunu DB strateji id'si sayar ([arayuzler § 3.6](../order-service/arayuzler.md#36-enum-ve-id-varsayımı)) |
| `strategyIdentifier` | strateji id'si / GUI `Strategy_Id` | |
| `protocol` | `channel` parametresi (§4) | 0 → order-service **sessizce düşürür** |
| `ordType`, `expireDate`, `isActive` | set edilmez; `make_shared<EnterOrder>()` değer-ilklemesiyle 0 | `regularOrderType=0` wire'a gider. ❓ doğrulanmadı: order-service/MAOrderSDK'nın 0'ı LIMIT saydığı (FIX'te tag 40). |

`isMarketOrder()` hep `false` döner; `sendOrder`'daki piyasa emri dalı (fiyatı en iyi fiyattan 10 adım öteye koyar) ölü koddur.

### 3.3 `ReplaceOrder`, `CancelOrder`

- `ReplaceOrder<T>(order, qty, prx=0)`: yeni istemci token'ı üretir (passthrough olur), `orderToken` = eski emrin **order-service token'ı**. Miktar `qty + order.getExecutedQuantity()` (toplam miktar semantiği). `prx=0` geçilirse wire'a 0 gider ([arayuzler § 3.4](../order-service/arayuzler.md#34-replace-ve-cancel): 0'ın "değiştirme" anlamı ❓).
- `ReplaceOrder(ReplaceOrderInfo)` (GUI) `setProtocol(channel)` çağırır ama ouch-sdk bu alanı serileştirmez; wire'da hep 0.
- `CancelOrder(token, obId=0, side=Unknown)`: yalnız token gider. Protokol alanı yoktur (`// FIXME: remove channel`).

## 4. Gönderim (`OuchManager.h`)

### 4.1 Giriş noktaları

| Çağrı | Ne yapar | `trackedOrders`'a girer mi |
|-------|----------|----------------------------|
| `send(EnterOrder&, timeout=0, channel=OUCH)` | `make_shared<EnterOrder>(order, false)` → `sendOrder`: `setProtocol(channel)`; `levelCount > 1` ise `OrderUtility::generateOrders` ile bölme, değilse `sendTransaction(*order, false)` | Evet, istemci token'ı ile |
| `send(ReplaceOrder&/CancelOrder&, timeout, channel)` | `sendTransaction` → `ouchSDK::replaceOrder/cancelOrder` → `waitForAnswer(timeout)`. `channel` kullanılmaz. | Evet: replace yeni istemci token'ı ile, cancel order-service token'ı ile |
| `cancelOrder(const OrderAccepted&)`, static `cancelOrder(const CancelOrder&)` | Doğrudan `ouchSDK::cancelOrder`. `"CancelOrder won't be tracked"` uyarısı loglanır. | Hayır |
| static `replaceOrder(const ReplaceOrder&)` | Doğrudan `ouchSDK::replaceOrder` | Hayır |

Kim hangisini kullanır (koddan):

| Kullanıcı | Enter | Replace | Cancel | Kanal |
|-----------|-------|---------|--------|-------|
| Arbitraj (`ArbitrageTracker::sendTransaction`) | `send(.., 0, channel)` | `send(.., 0, channel)` | — | `Channel_Enum` (yoksa **0**) |
| VWAP (`TradeByVolume`) | `send(.., 10 s, protocol)` | static `replaceOrder` | static `cancelOrder` | `Channel_Enum` (yoksa **0**) |
| Fon Takibi (`FundTracker::sendTransaction`) | `send(.., 0, OUCH)` | `send(.., 0, OUCH)` | — | sabit OUCH |
| Sepet Arbitraj | `send(*enterOrder)` | — | — | sabit OUCH |
| `AccountDepth::cancelAllOrders` / `cancelSingleOrderWithPriceAndQuantity` | — | — | `cancelOrder(OrderAccepted)` | — |
| GUI serbest emir (§8) | `send` | static `replaceOrder` | static `cancelOrder` | `Order_Channel` |

### 4.2 Kanal seçimi (`Channel_Enum`)

- `ArbitrageTrackerCommand` ve `TradeByVolumeCommand` `Channel_Enum`'u (`ARB_CHANNEL_ENUM`, IntValue) `ouchSDK::enums::Protocol`'e cast eder: 1 OUCH, 2 FIX. Alan **yoksa `PROTOCOL_UNKOWN` (0)** olur. 0 wire'a gider ve order-service emri "Unknown protocol type" log'uyla **yanıtsız düşürür** ([arayuzler § 6.2](../order-service/arayuzler.md#62-enter-girişten-biste)). AlgoProd bunu kontrol etmez (Şüpheli).
- Kanal yalnız enter'da anlamlıdır. Cancel/replace'te order-service protokolü token'dan bulur ([arayuzler § 6.3](../order-service/arayuzler.md#63-cancel--replace)).
- FIX ve OUCH order-service'te aynı `MAOSdkManager`'a gider; fark kullanıcı seçimindedir ([arayuzler § 6.1](../order-service/arayuzler.md#61-manager-seçimi)).

### 4.3 Bölme (`levelCount > 1`) — pratikte ölü

- `EnterOrder::levelCount` üyesi 1 ile başlar ve hiçbir yerde set edilmez. `sendOrder`'ın bölme dalı ve `OrderUtility::generateOrders` / `addNewOrderToListOrders` (maks emir değerine göre bölme, VİOP'ta 100, payda 1000 sabit bölen) development'ta çalışmaz.
- Asıl bölme order-service'te MAOrderSDK'dadır. ARBITRAGE/VWAP/FUND_TRACKER için `no_split` set edilir ([arayuzler § 6.2](../order-service/arayuzler.md#62-enter-girişten-biste)).
- GUI'nin kademe emri (`Order_Lvl_Count`) ayrı ve çalışan bir yoldur (§8).

### 4.4 Timeout (10 sn) ve sonrası

- `waitForAnswer(order, timeout)`: `timeout` **µs**'dir. `sleepPeriod = min(200, timeout)` µs, `timeout / sleepPeriod` kez `trackedOrders`'a bakar. Kayıt silinmezse `BaseException("...response of order not received in timeout period!")` fırlatır.
- **EnterOrder'da timeout uygulanmaz.** `sendOrder` tek emirde `sendTransaction(*enterOrder, false)` çağırır; `false` → `timeout = 0` → `waitForAnswer` hemen döner. Timeout yalnız bölme dalında (ölü, §4.3) ve `send(ReplaceOrder/CancelOrder)`'da kullanılır.
- Sonuç: VWAP'ın `sendTransaction`'ındaki "10 sn içinde yanıt yoksa stratejiyi durdur" (`secondToMicroseconds(10)` + `catch → stop()`) **hiç tetiklenmez**; VWAP yalnız enter gönderir, cancel/replace'i takipsiz static fonksiyonlarla yapar. ⚠ README'deki "Gönderim 10 sn içinde dönmezse strateji durur" ifadesi koda uymuyor.
- Arbitraj ve Fon Takibi `timeout = 0` verir; `catch → stop()` yalnız gerçek bir istisnada (ör. `insertStrategyInfo`, userbook bulunamaması) çalışır.
- `trackedOrders` silinmesi: Accepted (istemci token'ı), Replaced (replace'in passthrough'u), Canceled (order-service token'ı), Rejected (§7). Yanıt hiç gelmezse (order-service sessiz düşüşleri, kopma) kayıt **sonsuza kadar** kalır; timeout kullanılmadığı için strateji bunu fark etmez.

## 5. Olayların dönüşü ve userbook'lar

### 5.1 Callback → strateji

`OuchManager.cpp`'deki `ouchSDK::order*` serbest fonksiyonları ouch-sdk modelini AlgoProd sarmalayıcısına (`OuchMessages/`) çevirir ve `OuchManager::algoOrder*`'ı çağırır. Model nesneleri silinmez ([ouch-sdk § 4.2](../ouch-sdk/README.md#42-sahiplik)).

| Olay | Sarmalayıcıdaki kimlikler | `algoOrder*` adımları |
|------|---------------------------|----------------------|
| Accepted | `token` = passthrough'un ilk 14 karakteri; `orderId` = order-service token'ı; `itchOrderId` | `acceptedOrders[orderId]`'e yazar → `TradableInstrument::orderAccepted` → `untrackOrder(token)` → GUI'ye `MarketPacket` (`notifyAllUsers`) |
| Replaced | `orderId` = yeni token, `oldToken` | `acceptedOrders[oldToken]`'dan eski emri bulur (yoksa ERROR ve çıkış). Yeni `OrderAccepted` kopyası kurar, eskisi için **sentetik `OrderCanceled`** (`isReplaced=true`) üretir. Sıra: `orderCanceled(eski)` → `orderAccepted(yeni)` → `untrackOrder(passthrough)` |
| Executed | `token = orderId` = order-service token'ı | `acceptedOrders`'tan orijinal emri bulur (yoksa WARN ve **olay atılır**). `setOriginalOrder` ile hesap/strateji/yön doldurulur (wire'da yok) → `orderExecuted` |
| Canceled | `token = orderId` = order-service token'ı | Orijinal emri bulur (yoksa WARN ve atılır) → `orderCanceled` → `untrackOrder(token)` |
| Rejected | `token = orderId` = passthrough'un ilk 14 karakteri | §7 |

- Her `algoOrder*` önce `isStrategyInfoMapFilled`'a bakar (§2).
- `getTradableInstrument(orderbookId)` `nullptr` ise olay loglanıp atılır.
- `acceptedOrders` hiç temizlenmez (gün boyu büyür; replace'te eski kayıt da kalır).
- `OrderAccepted` sarmalayıcısında `remainingQuantity = initialQuantity` ve `preTradeQuantity = initial − quantity` atanır. `initialQuantity` ouch-sdk'da wire `preTradeQuantity`'den gelir. ❓ doğrulanmadı: order-service'in `preTradeQuantity`'yi bu anlamda doldurduğu (master combiner yorumu "pre-trade quantity − quantity döner" diyor).

### 5.2 Userbook = strateji başına emir haritası

- `TradableInstrument::accountbooks`: anahtar `<account>_<strategyIdentifier>_<strategyType>` → `Userbook` (`Orderbook<AccountDepth>`), alış ve satış için iki `AccountDepth`.
- Yaratıldığı yerler: `createUserbooks` (açılış, DB'deki strateji kayıtları), `OuchManager::insertStrategyInfo` (strateji başlarken veya GUI emrinde kayıt yoksa; `ouchSDK::insertStrategyInfo` **bloklar**, order-service hep `true` döner).
- `TradableInstrument::getOrderbook(account, id, type)` userbook yoksa `BaseException` fırlatır. Bu çağrı callback thread'inde yakalanmaz → `std::terminate` (Şüpheli).
- `AccountDepth::orderMap` anahtarı order-service token'ıdır. Aynı token ikinci kez gelirse `OrderDepth::addOrder` "duplicate order!" loglar ve eklemez (replay tekrarına karşı tek koruma).
- `AccountDepth` her olayda subscriber'lara `TradeData` yollar (`notifyAddOrderSubscribers`, `notifyAllSubscribers(orderType, …)`, `notifyAllSubscribersNew(OrderEventType, …)`), sonra `ouchHistory`'ye ekler (sınırsız büyür).
- Reddin `TradeData`'sı: `side = ShortSell` (sabit), `orderToken` = ouch-sdk `orderToken` (risk retinde boş), `passThrough`, `rejectCode`, `rejectReason`. `Orderbook::orderRejected` yönü bilinmiyorsa (`Unknown`) **alış** derinliğine yollar.
- Stratejilerin kendi iç emir/paket haritaları strateji dosyalarındadır.

### 5.3 Pozisyon ve istatistik

- Gerçekleşmeler `AccountDepth::executeOrder` içinde `statisticsByOrderType[orderType]`'a eklenir (gün içi bütün dolumlar, replay dahil).
- `currentStatisticsByOrderType`: `AccountDepth` yaratıldıktan **1 sn** (`CURRENT_STATISTICS_TIMEOUT`) sonra gelen dolumlar. Amaç replay'i "bu oturumun pozisyonu"ndan ayırmak. Replay 1 sn'den uzun sürerse eski dolumlar da girer (kodda TODO).
- Önceki gün pozisyonu: `fillStrategyInfosMap` order-service'in `AccountStrategy.position` (lot) ve `lastPrice` (raw) değerinden, **yalnız `position > 0` ise**, `Side::Buy` bir `Statistics` üretir ve `prevPositionNotifier` ile GUI'ye yollar. Negatif (kısa) pozisyon yok sayılır (Şüpheli). `position`/`lastPrice` order-service'te GET yönünde doludur ([ouch-sdk § 6.3](../ouch-sdk/README.md#63-strategyinfo--accountstrategy)).
- Bakiye/hesap limiti takibi AlgoProd'da yoktur; risk order-service'tedir ([risk.md](../order-service/risk.md)). Strateji içi bakiye (`SetBalance`) strateji dosyalarında.

## 6. Fiyat ve miktar ölçeği

- **Miktar:** her yerde lot.
- **Fiyat:** AlgoProd ouch-sdk'ya **raw** tam sayı verir (TL × 10^`decimalCount`, [sözlük](../../00-genel/sozluk.md)). AlgoProd, ouch-sdk ve order-service dönüştürme yapmaz. Yani ölçek hatası olursa doğrudan BIST'e gider.
- `decimalCount`, `Instrument::decimalPrice`'tır (trade-data-app `decimal_count` / ITCH `OrderbookDirectory`). `priceDivider = 10^decimalPrice` (varsayılan 1000).
- Raw değeri kim üretiyor:
  - Market verisinden türeyen fiyatlar (ITCH seviyeleri, `getPriceStep` = `itchsdk_get_tick_size`) zaten raw'dır.
  - **Arbitraj** VİOP fiyatını sabit katsayılarla üretir: `finalPrice = round(drvWantedPrice / 10.0)` ("0.01 TL format" yorumu) veya `round(drvWantedPrice * 100)`. Yapıcıda `decimalPrice == 2` ise `drvDecimalMultiplier = 10`. VİOP'ta `decimalCount ≠ 2` olan kontratta 10× sapma riski vardır (K-122 ile aynı aile). ❓ doğrulanmadı: arbitraj kontratlarının hepsinin `decimalCount = 2` olduğu.
  - `addNewOrderToListOrders` maks emir değeri hesabında sabit bölen kullanır (pay 1000, VİOP 100). Ölü dal (§4.3).
  - **GUI serbest emri** `Order_Price`'ı **aynen** gönderir. Eski GUI fiyatı sabit ×1000 ile çeviriyorsa (K-163) VİOP'ta (`decimalCount = 2`) AlgoProd'dan geçen serbest emir de 10× sapar. AlgoProd kontrol etmez.
- Olaylarda dönen fiyatlar da raw'dır (`OrderAccepted.price` i32, `OrderExecuted.price` işlem fiyatı). `OrderCanceled.price` wire'da 0 gelir ([arayuzler § 3.7](../order-service/arayuzler.md#37-olayların-istemciye-dönüşü)); `AccountDepth::deleteOrder`'ın `TradeData`'sındaki fiyat bu yüzden 0'dır (replace'in sentetik cancel'ı hariç, o da fiyatsız kurulur).

## 7. Ret yolu ve PTRM

### 7.1 `algoOrderRejected`

1. `order_key_1` = passthrough'un ilk 14 karakteri; `trackedOrders`'ta varsa (enter veya tracked replace) kaydın `orderbook_id` ve `side`'ı alınır.
2. Yoksa `order_key_2` = ouch-sdk `orderToken`; tracked cancel retleri için (yalnız `send(CancelOrder)` kullanan, kullanılmayan `TradeByBSRatio`).
3. İkisi de yoksa `"OuchManager::orderRejected: transaction not found"` ERROR. Strateji **haberdar edilmez**, yalnız GUI paketi gider.
4. Bulunduysa `TradableInstrument::orderRejected` → userbook (rejected modelindeki `account` / `strategyIdentifier` / `strategyType` ile) → `AccountDepth::orderRejected` → subscriber.

order-service risk reddi `orderToken` boş, `rejectCode = 0`, açıklama metinli gelir ([risk.md § 7](../order-service/risk.md#7-reddin-istemciye-dönüşü)). AlgoProd passthrough ile eşlediği için bu ret stratejiye ulaşır. Ama kod 0 olduğu için aşağıdaki PTRM kontrollerine **uymaz**.

### 7.2 Kodlar ve strateji davranışı

Kod listesi: [borsa-kurallari § PTRM](../../00-genel/borsa-kurallari.md#ön-işlem-risk-ptrm-ve-diğer-ret-kodları). Sabitler `Globals/GlobalDefinitions.h`.

| Strateji | Durduran retler | Diğer retler |
|----------|-----------------|--------------|
| Arbitraj (yalnız VİOP bacağının subscriber'ı `drvRejectOrderSubscriber`) | `-850004`, `-850002`, `-850044` (kod veya tam `REJ- <…>` metni), `-420131` → `stop()` | `-420177` (emir bulunamadı) → replace bayrakları sıfırlanır, devam. Seans dışı (`-1800042`, `-110023`, `-1004048`, `-704130`) → `checkStatus()`. **Geri kalan her kod (order-service risk reddinin 0'ı dahil) → "Unhandled reject" + `stop()`.** |
| VWAP | `-850004`, `-850002`, `-850044` → `stop()` | Log + `isOrderSent = false`, devam. Risk reddi (0) durdurmaz; sonraki döngüde yeniden emir denenebilir. |
| Fon Takibi | **Her** ret → `stop()` | — |

`-850064` AlgoProd'da tanımlı değil (yalnız HFT). Strateji tarafındaki ayrıntı: [arbitraj](../../20-stratejiler/arbitraj.md#döngü-doperiodicchecks), [vwap](../../20-stratejiler/vwap.md#ptrm).

## 8. Serbest / manuel emir (`Algo_User`)

Yol: GUI → trade-data-app REST (`StrategyType` 1 → AlgoTrading, [trade-data-app/veri-akisi § 5.5](../trade-data-app/veri-akisi.md#55-getapplicationfromstrategytype--iki-kopya)) → AlgoProd gRPC `SetCommandRequest` (`Command_Type_OrderRequest`) → `GUIManager::dispatchOrders`. Sabah/açılış/akşam emirleri bu yoldan değil, order-service gRPC'den gider ([toplu-emirler](../order-service/toplu-emirler.md)).

`dispatchOrders`, `Order_Event_Type`'a göre:

| Değer | İşlem | Okunan alanlar (`Utilities/GuiConstants.h`) |
|-------|-------|---------------------------------------------|
| 1 Enter | `EnterOrderInfo` → `EnterOrder` (yeni istemci token'ı, TIF DAY). Strateji kaydı yoksa `insertStrategyInfo` (bloklar). Kanal `≠ 0` ise `send(enterOrder, 0, kanal)` ve `Order_Lvl_Count > 1` ise en çok 10 kademe: her kademe fiyatı **ilk fiyatın** adımıyla (`getPriceStep(price)`) alışta aşağı, satışta yukarı kaydırılır. Kanal 0 ise `send(enterOrder)` (OUCH, kademe yok). | `Orderbook_Id` (Long), `Exchange_Info`, `Order_Side` (1 B / 2 S / 3 T), `Order_Quantity` (Long, lot), `Order_Price` (Long, **raw**), `Strategy_Id`, `Strategy_Type` (Int), `Order_Lvl_Count` (Int), `Order_Channel` (Int; yoksa OUCH) |
| 2 Cancel | static `cancelOrder` (takipsiz) | `Order_Token` (order-service token'ı), `Order_Channel` (zorunlu ama kullanılmaz) |
| 3 Replace | `ReplaceOrder(ReplaceOrderInfo)` → static `replaceOrder` (takipsiz). Miktar GUI'den gelen değerdir (yürütülen eklenmez). | `Orderbook_Id`, `Order_Quantity`, `Order_Price` (raw), `Order_Token`, `Order_Channel` |

- Zorunlu alan eksikse `INVALID_ARGUMENT`. Enter'da `Order_Lvl_Count` de zorunludur.
- gRPC yanıtı yalnız "kuyruğa kondu" demektir. Sonuç GUI'ye `FetchOrders` / order-service stream'inden döner.
- Kademe adımı ilk fiyatın adımıdır; fiyat bandı sınırını geçen kademelerde geçersiz tick üretebilir (❓ doğrulanmadı).

## 9. order-service bağlantısı koparsa

- **Açılışta ulaşılamıyorsa:** `login` sonsuza kadar bekler (K-151). Process ayakta, gRPC kapalı, strateji yok.
- **Gün içinde koparsa:** kopma algılanmaz ve bildirilmez (K-152). `ouchSDK::enterOrder/replaceOrder/cancelOrder` sessizce kuyruğa yazar; emir gitmez, olay gelmez.
  - `trackedOrders` kayıtları kalır, timeout kullanılmadığı için (§4.4) strateji hata görmez.
  - VWAP `isOrderSent = true`'da takılabilir (yalnız accept/reject sıfırlar). ❓ doğrulanmadı: strateji döngüsünün bu durumda yeni emir göndermeyi bıraktığı.
  - Strateji kaydı gerektiren yeni başlatmalar `insertStrategyInfo`'da sonsuza kadar bekler (gRPC thread'i asılı kalır).
  - BIST'teki açık emirler iptal edilmez (cancel-on-disconnect yok, [arayuzler § 3.9](../order-service/arayuzler.md#39-istemci-kopunca)). Kopukken gelen dolumlar AlgoProd'a hiç ulaşmaz.
- **Kurtarma:** yalnız AlgoProd restart. Restart'ta `getAllOrders` günün olaylarını yeniden oynatır, userbook'lar ve `statisticsByOrderType` yeniden kurulur. Stratejiler DB ayarlarından yeniden yaratılır.
- **order-service restart'ı:** AlgoProd'un MARpc bağlantısı ölür ama AlgoProd bunu bilmez; o da yeniden başlatılmalıdır (`run.sh`/compose `restart: always` yalnız process düşerse çalışır).

## 10. ⚠ master farkı (prod, aa150ee)

Emir yolunda tek anlamlı fark **ExecuteCombiner**'dır (`algoSrc/ExecuteCombiner/`, yalnız master):
- `startOuchStreaming` `combinerEnabled` config'ini okur ([config.md](config.md)). Bütün müşteri config'lerinde `false`.
- `replay_completed && combinerEnabled` ise accepted/replaced/executed/canceled olayları `ExecuteCombinerManager`'dan geçer: ITCH'teki dolumlardan OUCH dolumu gelmeden **sahte execute** üretir, gerçek `OrderExecuted` gelince birleştirir. Yönetilmeyen emir normal yola düşer. Ayrıca `ouch_vs_timestamp` ölçümü ve stderr'e `"ouch ts diff"` basılır.
- `combinerEnabled=false` olduğu için prod'da davranış development ile aynıdır. ❓ doğrulanmadı: hiçbir prod kurulumunda `true` olmadığı.

Diğer farklar emir yolunu etkilemez: `getPriceStep` master'da eski ITCH SDK `getTickSize`'ı kullanır; Arbitraj ve Fon Takibi'nde strateji içi değişiklikler (strateji dosyalarında).

## 11. 🚧 add-order-sdk (7d7f705, 2026-10-15, merge edilmedi)

development'ın üstüne 12 commit. Getirdikleri:

- **Doğrudan BIST yolu:** `MAOrderSdkManager` tek `maordersdk::MAOrderSDK` örneğini `OuchManager`'dan **önce** başlatır. `ouchSDK::orderUserDisconnected` artık handoff yapar: OUCH kullanıcısını `connectUser` ile BIST'e bağlar (1..4 s artan bekleme ile 4 yeniden deneme; ouch-sdk callback thread'inde, yani bu sürede order-service olayları bekler). Onload stack'i yalnız bu thread için `onloadStackName`'e alınır.
- **Yönlendirme (`MAOrderSdkRouter`)**, HFT ile aynı kural: FIX enter → order-service; hesabın sahibi bağlı bir MAOrderSDK kullanıcısıysa → MAOrderSDK; cancel/replace emrin sahibine göre. Hesap/fon kodu/piyasa bilgisi açılışta trade-data-app `GetOuchUsers`'tan okunur (`loadAccounts`). İki piyasada tanımlı hesapta kullanıcı round-robin seçilir.
  - Handoff süresince ve devredilmiş ama bağlı kullanıcısı kalmamış hesapta enter **yerel olarak reddedilir** (order-service artık taşımaz ve yanıtsız düşürürdü). Yerel ret kodları: 2001 handoff, 2002 hesap alanı yok, 2003 strateji id, 2004 bağlantı koptu, 2005 replace gönderilemedi, 2006 cancel gönderilemedi.
  - Fon hesaplarında BIST'in döndürdüğü fon kodu hesap adına geri çevrilir; aynı fon kodunu paylaşan hesaplar gönderim kaydıyla ayrılır.
  - `no_split` ARBITRAGE/VWAP/FUND_TRACKER için order-service'tekiyle aynı; fiyat raw aynen.
- **Tek tüketici (`OrderEventDispatcher`):** ouch-sdk ve MAOrderSDK olayları MPSC kuyruğa yazılır, `algoOrder*` tek thread'de çalışır. Getirdikleri: order-service geçmişi ile BIST replay'i arasında **tekrar eleme** (accept token, dolum token+matchId, cancel token, replace yeni token); sırası bozuk MAOrderSDK olaylarını accept gelene kadar **park** etme (60 s, en çok 100000); replace'le yarışan dolumu güncel token'a yönlendirme; MAOrderSDK emirlerini GUI'ye (`FetchOrders`) yayınlama.
- **Replay beklemesi:** dispatcher yalnız userbook'lar kurulduktan sonra başlar (öncesindeki olaylar kuyrukta bekler, atılmaz). `getAllOrders` sonrası `drain(60 s)` ile işlenmesi beklenir; stratejiler kullanıcının BIST replay'i bitmeden emir veremez (handoff kilidi).
- **Passthrough biçimi değişir:** `"A" + "x" + strategyIdentifier[3] + "x" + strategyType[2] + token[:7]` (HFT `updateExtraData` ile aynı, 15 karakter). Enter artık **tam passthrough** ile takip edilir; `OrderRejected.orderId` order-service token'ı olur (development'ta passthrough'tu).
- Yeni config anahtarları (`sdk*`, `orderEvents*`): [config.md](config.md)'de henüz yok.
- Etkisi: §9'daki "order-service koparsa her şey durur" davranışı handoff edilmiş hesaplar için ortadan kalkar; FIX ve devredilmemiş hesaplar hâlâ order-service'e bağlıdır. `combinerEnabled` bu dalda da yok.

## Şüpheli

- **bug? Kanal 0 → emir yanıtsız kayboluyor:** Arbitraj/VWAP komutunda `Channel_Enum` yoksa `PROTOCOL_UNKOWN` gönderiliyor; order-service düşürüyor, AlgoProd'a ret gelmiyor, `trackedOrders` kaydı kalıyor. ❓ doğrulanmadı: GUI'nin alanı her zaman gönderdiği.
- **bug? order-service risk reddi Arbitraj'ı durduruyor, VWAP'ı durdurmuyor:** `rejectCode = 0` geliyor. Arbitraj "Unhandled reject" ile `stop()`, VWAP log'layıp yeniden deneyebilir. PTRM benzeri bir risk reddi (limit aşımı) PTRM listesine hiç uymuyor.
- **bug? Userbook yoksa callback thread'inde istisna:** `TradableInstrument::getOrderbook` `BaseException` fırlatıyor ve `algoOrder*` bunu yakalamıyor → `std::terminate`. Olayın hesap/strateji üçlüsü için userbook açılmamışsa (ör. aynı uygulama kullanıcısıyla başka yerden girilmiş emir) process düşer. ❓ doğrulanmadı: pratikte tetiklendiği.
- **bug? EnterOrder timeout'u ölü:** `sendOrder` tek emirde timeout'u `false` ile sıfırlıyor; VWAP'ın 10 sn güvencesi çalışmıyor (README yanlış).
- **bug? OUCH login 401 ise bütün olaylar sessizce atılıyor:** `isStrategyInfoMapFilled` hiç `true` olmuyor, emirler yine gönderiliyor. Strateji dolumlarını göremez.
- **bug? Kısa önceki pozisyon yok sayılıyor:** `fillStrategyInfosMap` yalnız `position > 0`'ı ve hep `Side::Buy` ile işliyor.
- **doğrula: Arbitraj VİOP fiyatı sabit ×100 / ÷10** (`ArbitrageTracker`): `decimalCount ≠ 2` kontratta 10× sapma (K-122/K-163 ailesi).
- **doğrula: GUI serbest emir fiyatı aynen geçiyor:** eski GUI'nin sabit ×1000'i (K-163) AlgoProd yolunda da VİOP'ta 10× sapma yapar.
- **bug? Paylaşılan model:** `EnterOrder` kopya yapıcısı ve `generateOrders` ouch-sdk modelini paylaşıyor; kopyada yapılan `setPrice`/`setQuantity`/`setPassThrough` orijinali de değiştiriyor. Bölme dalı ölü, ama `send(EnterOrder)`'ın kopyası da aynı modeli paylaşıyor. `algoOrderReplaced`'teki `OrderAccepted` kopyası da eski kaydın modelinin passthrough'unu eziyor.
- **bug? `OrderUtility::createToken` kilitsiz:** tek `mt19937` birden çok strateji/gRPC thread'inden kilitsiz kullanılıyor (veri yarışı). Çakışma olasılığı düşük ama tanımsız davranış.
- **doğrula: `regularOrderType = 0` gönderiliyor:** AlgoProd `ordType` set etmiyor. order-service bunu MAOrderSDK'ya 0 olarak geçiriyor. FIX kanalında tag 40'ın nasıl üretildiği ❓.
- **kasıtlı? Takipsiz cancel/replace:** GUI, VWAP ve `cancelAllOrders` iptallerini takipsiz gönderiyor; iptal reddi stratejiye ulaşmıyor ("transaction not found").
- **bug? Sınırsız büyüyen haritalar:** `acceptedOrders`, yanıtsız `trackedOrders` kayıtları, `AccountDepth::ouchHistory` gün boyu temizlenmiyor.
- **doğrula: `currentStatistics` 1 sn sezgisi:** replay 1 sn'den uzun sürerse önceki dolumlar "bu oturumun pozisyonu"na giriyor.
- **eksik: Kopma algılama yok** (K-151, K-152): gün içi order-service kopmasında AlgoProd emir göndermeye devam ediyor gibi görünür; tek çare restart.
