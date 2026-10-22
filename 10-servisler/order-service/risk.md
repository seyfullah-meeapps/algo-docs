---
kapsam: order-service ön-işlem risk kontrolü (RiskManager) — veri kaynağı ve birimler, checkEnterOrder/replace kontrolleri, rezervasyon takibi, replay/restart davranışı, LimitControlService ve hard cap ile ilişkisi, şüpheli davranışlar
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# Risk kontrolü (`RiskManager`)

Bu dosya risk mantığını anlatır. Başka konular kardeş dosyalarda:
- Emrin MARpc/gRPC'den dispatcher'a gelişi, `OrderRejected`'ın istemciye taşınması: [arayuzler.md](arayuzler.md)
- MAOrderSDK oturumları, SDK callback'leri, yerel retler: [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md), [maordersdk](../maordersdk/README.md#emir-gönderme)
- Toplu emir akışları: [toplu-emirler.md](toplu-emirler.md)
- Config, emir kalıcılığı, `RetrieveSentOrders`: [kalicilik-ve-config.md](kalicilik-ve-config.md)
- Sunucu tarafı (`pkg/limits`, `RiskManagerService`): [trade-data-app api § 6](../trade-data-app/api.md#6-limitcontrolservice-ve-riskmanagerservice-limit_controlproto-risk_managerproto), [entegrasyonlar § Limits](../trade-data-app/entegrasyonlar.md#limits-pkglimits)

Kod: `Managers/RiskManager.*`, `Data/Models/RiskInfo.*`, protolar `Service/limit/risk_manager.proto` ve `limit_control.proto` (yalnız `StockLimitType` enum'u için).

## 1. Kapsam: hangi emir riskten geçer

| Giriş | Yol | Risk kontrolü |
|-------|-----|---------------|
| MARpc `EnterOrderRequest` (ouch-sdk istemcileri: HFT OS yolu, AlgoProd) | `OrderServer` → `OrderDispatcher::SendOrder(EnterOrder)` | **Evet**, `checkEnterOrder` |
| gRPC `SendOrder`, `order_type = STRATEGY`, `ORDER_EVENT_ENTER` | `OrderServiceImpl::InsertRegularOrder` → `OrderDispatcher::SendOrder(EnterOrder)` | **Evet**. ❓ doğrulanmadı: trade-data-app `GuiSendOrders` STRATEGY emirlerini motorlara gönderiyor, order-service'e değil ([api § 7](../trade-data-app/api.md#7-guiservice-gui-dataproto-gui_apigo--rest-restport)); bu dalı çağıran bir istemci bulunamadı. |
| MARpc `ReplaceOrderRequest` | `OrderDispatcher::SendOrder(ReplaceOrder)` → `MAOSdkManager::SendOrderAsync(ReplaceOrder)` | **Evet**, fark emri üzerinden (§ 6) |
| MARpc `CancelOrderRequest` | `OrderDispatcher::SendOrder(CancelOrder)` | Hayır |
| gRPC `SendOrder` MORNING / OPENING / EVENING (GUI toplu emirleri) | DB'ye yazılır, sonra toplu akışlar `MAOSdkManager::SubmitEnterOrder` ile doğrudan gönderir | **Hayır**. Toplu emirler `checkEnterOrder`'a hiç uğramaz. |
| Sabah/açılış/YİP/teorik akışları, son atış tekrarları, `CancelRepeatedOrders` | `OrderManager` / `MAOSdkManager` içi | **Hayır** |

- Kontrol protokolden bağımsızdır; `kFix` emirleri de aynı `checkEnterOrder`'dan geçer.
- Riskten geçmeyen emirlerin olayları (accept/execute/cancel/replace) yine de rezervasyonları günceller. Bunun şartı, emrin host registry'sinde (`entered_orders`) olmasıdır. Toplu akışlarda bu `insert_to_entered_orders` parametresine bağlıdır. Registry'de olmayan emrin olayı SDK callback'inde "no host registry entry" ile düşer ve riske de ulaşmaz (ayrıntı: [toplu-emirler.md](toplu-emirler.md)).
- MAOrderSDK'nın yerel kontrolleri (hard cap, brüt takas, bölme) **bütün** emirlere uygulanır (§ 11).

## 2. Açılış ve başlatma

- Config: `database.riskControl` (`ConfigurationManager` → `DatabaseConfig::risk_manager_enabled`). Anahtar yoksa varsayılan `false`. Örnek `config.yaml`'da `false`.
- `OrderServiceApplication::Start` sırası:
  1. `RiskManager` her durumda oluşturulur.
  2. `db_client->Connect()` (DataService login, token alınır), enstrümanlar ve stratejiler yüklenir.
  3. `risk_manager->Start(risk_manager_enabled)`.
  4. `order_dispatcher->Start()`: MAOrderSDK açılır, OUCH/FIX login ve replay burada başlar.
- `Start(false)`: hiçbir şey yapmaz, `running` `false` kalır. `checkEnterOrder` her emre `true` döner; `On*` olay metotları hemen döner.
- `Start(true)` → `Connect()`:
  - Token `db_client->GetToken()`'dan alınır (DataService.Login JWT). `authorization` metadata'sına öneksiz konur. Ayrı bir risk login'i yoktur.
  - Adres `database.host:database.port`, yani DataService'le aynı trade-data-app gRPC portu. Kanal **insecure**, `GRPC_ARG_MAX_RECEIVE_MESSAGE_LENGTH` = 50 MB.
  - `StartTryingToFetchAccountLimits()` ve `StartTryingToFetchStockLimits()`: iki **detached** thread (§ 3.1, § 3.2).
  - `StartIntraDayCustomerLimitsStream()`: `intradayThread` (§ 3.3).
  - Ardından `setRunning(true)`.
- `running` `true` olduğu andan itibaren kontrol aktiftir. Hesap limitleri henüz yüklenmemiş olabilir. Bu durumda hesap bulunamaz ve emir geçer (§ 5, adım 2).
- `setIntrumentMap()` sembol → enstrüman haritası kurar; risk kontrolünde kullanılmıyor (ölü kod). `initializeSymbolRestrictionMap` hiç çağrılmıyor.

## 3. Veri: trade-data-app `RiskManagerService`

Sunucu tarafında limitler yalnız bellektedir (`limits.GetLimitsManager` singleton). Onları `LimitControlService` çağrılarıyla harici bir sağlayıcı yazar (§ 10). Sağlayıcı yazmadıysa bütün yanıtlar boş döner.

Yalnız `GetIntraDayCustomerLimits` stream'dir. Hesap limitleri ve hisse kısıtları **unary** RPC'lerle çekilir.

### 3.1 `GetCustomerLimits` → `CustomersOverallResponse`

`RiskManager::FetchAccountLimits`. Döngü: 5 sn arayla çağrılır, `account_limits` boş olmaktan çıkınca durur. Sonrasında **bir daha çağrılmaz**; sağlayıcının sonradan gönderdiği `SetCustomerLimits` güncellemeleri restart'a kadar görülmez.

| Proto alanı (`CustomerOverallResponse`) | Tip | order-service'te | Birim / ölçek |
|---|---|---|---|
| `customerAccount` | string | `RiskInfo::customerAccount`, `account_limits` anahtarı | Emrin `AccountStrategy().AccountName()` ile birebir eşleşmeli |
| `customerTLOverall` | uint64 | `customerTLOverall` | Proto: TL bakiyesi, **"bizim yaptığımız işlemler dahil olmadan"**. Kod tam TL varsayar ve ölçekler: hesap `D` ile başlıyorsa ×100, değilse ×1000. Sonuç emir tutarıyla (`qty × raw price`) aynı ölçekte olmalıdır (§ 5). |
| `stockOverallList[]` (`stockSymbol`, `stockOverall` int64) | | `stockBalanceList[symbol]` (uint64), `stockPassiveOrderQuantityList[symbol] = 0` | Adet. Sembol formatı proto örneğinde `GARAN.E`. Eşleşme `Instrument::Symbol()` ile yapılır (DB `instrument_symbol`). ❓ doğrulanmadı: iki formatın aynı olduğu. |
| `isProhibited` | bool | `isProhibited` | Hesap yasaklı |
| `mainMarketLimit`, `secondaryMarketLimit`, `otherMarketLimit` | uint64 | Saklanır | **Kullanılmıyor.** `RiskInfo::validateMarketLimit` vb. bildirilmiş ama tanımsız; kontrolde pazar limiti yok. |

- Aynı hesap iki kez gelirse `unordered_map::insert` ilkini korur.
- Stream ile sonradan gelen bir hisse için `stockPassiveOrderQuantityList`'te kayıt açılmaz (§ 13).

### 3.2 `GetStockLimits` → `StockLimitationsResponse`

`RiskManager::FetchStockMarketRestrictions`. 5 sn arayla çağrılır. Döngü, `stockRestrictions` dolunca **veya** pazar geneli kısıt `NONE` değilse durur. Hiç kısıt tanımlanmamışsa döngü gün boyu sürer; bu durumda sonradan girilen kısıtlar da görülür.

`StockLimitType` (`limit_control.proto`): `NONE=0`, `DEPO=1`, `BRUT_TAKAS=2`, `ACIGA_SATIS=3`.

| Alan | order-service'te |
|---|---|
| `stockMarketLimitations[]` | `generalStockRestrictionOnBIST` (atomic). Listeden en "üstün" olan seçilir (`findSuperiorStockLimit`). Öncelik: `BRUT_TAKAS` > `DEPO` > `ACIGA_SATIS` > `NONE`. |
| `stockLimitationList[]` (`stockSymbol`, `stockLimitType`) | `stockRestrictions[symbol] = findSuperior(hisse tipi, pazar geneli)`. Pazar geneli kısıt yalnız listede **adı geçen** hisselere karışır. |
| `isShortSellDefault` | `isDefaultShortSellRestriction`. Listede olmayan hisse `ACIGA_SATIS` sayılır. Her fetch'te üzerine yazılır. |

### 3.3 `GetIntraDayCustomerLimits` (server stream) → `CustomerIntraDayOverallResponse`

`RiskManager::ReadFromStream`, `intradayThread` içinde.

| Alan | Tip | Anlam (proto) | order-service'te |
|---|---|---|---|
| `customerAccount` | string | Hesap | `account_limits`'te yoksa `LOG_WARN` ve mesaj atılır |
| `customerTLOverall` | int64 | **Delta**, tam TL (ör. 1000 TL çekildi → `-1000`) | `D` hesap ×100, diğer ×1000; `updateCustomerTlOverral(delta, brutTakas=false)` ile eklenir |
| `stockOverall.stockSymbol` / `.stockOverall` | string / int64 | **Delta adet** (100 alındı → `100`, satıldı → `-100`) | `updateStockQuantity(symbol, delta, depo=false)` ile eklenir |

- trade-data-app her mesajda `stockOverall` alt mesajını doldurur. Sembol boşsa `stockBalanceList[""]` kaydı oluşur; zararsızdır.
- Sunucu tarafında kanal tamponsuzdur; okuyucu yoksa sağlayıcının `SetIntraDayCustomerLimits` çağrısı bloklanır ([api § 6](../trade-data-app/api.md#6-limitcontrolservice-ve-riskmanagerservice-limit_controlproto-risk_managerproto)).

### 3.4 Stream kopunca

`ReadFromStream`: `rpc->Read` `false` dönünce "Stream Dropped" loglanır, `Finish()` çağrılır, ardından "yeniden bağlanma" döngüsü çalışır:

```
while (isRunning()) { Connect(); if (isLoginSuccedd(token)) break; sleep 5 s }
```

- `Connect()` `running` zaten `true` olduğu için "Already Connected" deyip hemen döner. Token boş değilse döngü ilk turda kırılır ve thread biter.
- **Sonuç:** Stream bir kez koptuktan sonra yeniden açılmaz. Gün içi delta'lar restart'a kadar gelmez. Ayrıca sunucudaki tamponsuz kanalın okuyucusu kalmadığı için sağlayıcının `SetIntraDayCustomerLimits` çağrısı bloklanır (§ 13).
- Emir kontrolü çalışmaya devam eder; son bilinen bakiyelerle karar verilir. Fail-closed değildir.
- trade-data-app tarafında `Send` `io.EOF` dönerse `CloseChannel` limit manager'ı kalıcı kapatır. Bu durumda sonraki stream'ler de "Channel closed" ile biter.

## 4. Bellek modeli (`RiskInfo`, hesap başına)

| Alan | Tip | Anlam |
|---|---|---|
| `customerTLOverall` | uint64 | Bakiye, ölçekli (×1000 / ×100). Fill ve stream delta'larıyla değişir. |
| `customerTLUsedInPassiveOrders` | uint64 | **Alış rezervasyonu**: açık alış emirlerinin `price × qty` toplamı (raw fiyat ölçeği) |
| `stockBalanceList[symbol]` | uint64 | Hisse bakiyesi, adet |
| `stockPassiveOrderQuantityList[symbol]` | uint64 | **Satış rezervasyonu**: açık satış (Sell ve ShortSell) emirlerinin adedi |
| `isProhibited`, pazar limitleri | | § 3.1 |

- Rezervasyon güncellemeleri (`updatePassiveOrderTLUsed`, `updateStockPassiveOrderQuantity`) sonuç negatife düşerse 0'a kırpılır.
- Bakiye güncellemeleri kırpılmaz; uint64'te sarar (§ 13).
- `updateCustomerTlOverral(amount, brutTakas)`: `brutTakas && amount > 0` ise yok sayılır. Brüt takaslı hissede satış geliri aynı gün kullanılabilir bakiyeye eklenmez.
- `updateStockQuantity(qty, depo)`: `depo && qty > 0` ise yok sayılır. `DEPO` veya `BRUT_TAKAS` hissede alınan hisse aynı gün satılabilir bakiyeye eklenmez.

## 5. `checkEnterOrder` adım adım

`RiskManager::checkEnterOrder(order, desc)` → `checkOrderConstraints`. Sıra:

1. `running == false` → **geçer** (risk kapalı).
2. `account_limits`'te `AccountStrategy().AccountName()` yoksa `LOG_CRIT "RiskInfo not found"` → **geçer** (fail-open).
3. `isProhibited` → ret: `"Account is prohibited"`. Bütün yönlere uygulanır.
4. **TL kontrolü** (`Side != kSell`, yani **Buy ve ShortSell**):
   - `orderAmount = (Buy ? +1 : −1) × qty × price`. `price` raw `int32` (TL × 10^`decimal_count`), `qty` adet.
   - Geçme koşulu: `(int64)customerTLOverall − (int64)customerTLUsedInPassiveOrders > orderAmount` (kesin büyüktür).
   - Değilse ret: `"Insufficient Account Balance"`.
   - ShortSell'de `orderAmount` negatif olduğundan bu kontrol pratikte hep geçer.
   - **Ölçek varsayımı:** Bakiye ×1000 ölçeklenir. Bu yüzden karşılaştırma yalnız `decimal_count = 3` olan enstrümanda TL ↔ TL'dir. `D` ile başlayan hesaplarda ×100 kullanılır, yani `decimal_count = 2` varsayılır; VİOP kontrat çarpanı hesaba katılmaz. ❓ doğrulanmadı: pay enstrümanlarının hepsinde `decimal_count = 3` olduğu ([sema](../trade-data-app/sema.md)), `D` önekinin VİOP hesabı anlamına geldiği.
5. Enstrüman `instrument_service->GetInstrumentById(order.OrderBookId())`. `Instrument::IsBrutTakas()` (DB `isBrutTakas`) ise ret: `"Stock Has Brut Takas Restriction"`. Bütün yönlere uygulanır. Bu kontrol `StockLimitType`'tan bağımsızdır; MAOrderSDK'nın 1002 yerel reddiyle örtüşür.
6. Hisse kısıtı `stckLimit` şöyle belirlenir: `stockRestrictions[symbol]` varsa o değer, yoksa `isDefaultShortSellRestriction` ise `ACIGA_SATIS`, o da değilse `NONE`.
7. `stckLimit != NONE` **veya** `generalStockRestrictionOnBIST != NONE` ise:
   - `ShortSell` ve `stckLimit == ACIGA_SATIS` → ret: `"Short Sell is not allowed on this instrument: <symbol>"`.
     - Hisse `DEPO` veya `BRUT_TAKAS` ise üstünlük sırası yüzünden `stckLimit` `ACIGA_SATIS` olmaz ve açığa satış **reddedilmez**.
   - `Sell` ise `checkCustomerStockBalanceSufficiency` çalışır. Koşul: `stockBalanceList[symbol] − passiveQty ≥ qty` (uint64). Sembol yoksa veya enstrüman bulunamadıysa ret: `"Insufficient Stock Quantity for this instrument: <symbol>"`.
8. Aksi halde geçer. Sonuç ve `RiskInfo::ToString()` her emirde `LOG_CRIT` ile loglanır.

**Dikkat:**
- **Satışta bakiye kontrolü koşulludur.** Ne hisse kısıtı ne pazar geneli kısıt varsa `Sell` emri bakiyeye bakılmadan geçer.
- ShortSell'de bakiye kontrolü yoktur.
- Pazar geneli `ACIGA_SATIS`, listede adı geçmeyen hisselerde açığa satışı engellemez (yalnız adım 7'yi tetikler, o da Sell bakiye kontrolü olarak).
- **Rezervasyon kontrol anında değil, `OrderAccepted` geldiğinde yapılır (§ 8).** Accept gelmeden art arda giren emirlerin her biri aynı serbest bakiyeye karşı kontrol edilir.

## 6. Replace kontrolü

`MAOSdkManager::SendOrderAsync(ReplaceOrder)`:
1. Eski emir `entered_orders[orderToken]`'dan bulunur. Yoksa `LOG_CRIT` atılır ve dönülür; istemciye cevap gitmez.
2. `checkEnterOrder(orderedDifference(eski, yeni))` çağrılır.

`RiskManager::orderedDifference` bir "fark emri" kurar; bu emir eski emrin kopyasıdır (hesap, yön, enstrüman aynı):
- `Δp = yeniFiyat − eskiFiyat`, `Δq = yeniAdet − eskiAdet` (`int`'e cast).
- `Δp ≤ 0` ise fiyat = eski fiyat; `Δq ≤ 0` ise adet = eski adet.

| Değişiklik | Kontrol edilen tutar (alış) | Gerçek ek ihtiyaç |
|---|---|---|
| Yalnız fiyat ↑ | `eskiQ × Δp` | aynı |
| Yalnız adet ↑ | `Δq × eskiP` | aynı |
| Fiyat ↑ ve adet ↑ | `Δq × Δp` | `yeniQ×yeniP − eskiQ×eskiP` (daha büyük) |
| Fiyat ↓ ve/veya adet ↓, ya da değişiklik yok (`0` = değişmez) | `eskiQ × eskiP` (eski emrin tamamı) | ≤ 0 |

- Satışta da aynı fark emri kullanılır. Kısıt varken yalnız fiyatı değişen bir satış replace'i eski adedin tamamını, eski emri zaten içeren `passiveQty`'ye karşı kontrol eder. Bu yüzden haksız ret mümkündür (§ 13).
- Ret durumunda `sendOrderRejectedToApplication(eskiEmir, desc)` çağrılır. Borsadaki eski emir yerinde kalır.

## 7. Reddin istemciye dönüşü

`OrderManager::sendOrderRejectedToApplication`:
- `OrderRejected` oluşturulur:
  - `RejectDescription` = yukarıdaki metin.
  - `RejectCode` = **0** (atanmıyor).
  - `OrderToken` atanmaz. Yeni emirde token SDK'da üretildiği için **boştur**. Replace reddinde de `entered_order`'dan kopyalanmaz.
  - Hesap/strateji, enstrüman, yön, fiyat, adet, passthrough ve `SenderApplication` doldurulur.
- `OrderResponseCallBack(OnOrderRejected)` iki yere gider:
  - `OrderServer::OnOrderRejected` → `SenderApplication`'ın bütün MARpc bağlantıları.
  - `OrderServiceImpl::OnOrderRejected` → gRPC `SubscribeToOrders` aboneleri.
  - Ayrıntı: [arayuzler.md](arayuzler.md).
- `rejected_orders` haritasına eklenmez, DB'ye yazılmaz, BIST'e gitmez.
- İstemci emri token ile değil, passthrough/hesap/strateji ile eşleştirmek zorundadır. ❓ doğrulanmadı: ouch-sdk ve HFT tarafında token'sız `OrderRejected`'ın nasıl eşlendiği.

## 8. Rezervasyon takibi

Olaylar MAOrderSDK callback'lerinden (`MAOSdkManager::ConfigureSdkCallbacks`) gelir. Risk çağrısından önce istemciye callback yapılır (`OrderResponseCallBack`). `running == false`, hesap yok veya enstrüman yoksa çağrılar sessizce döner.

| Olay | Çağrı | Alış (`kBuy`) | Satış (`kSell`, `kShortSell`) |
|---|---|---|---|
| Accepted | `RiskInfo::OnOrderAccepted` | `passiveTL += price × PreTradeQuantity` | `passiveQty[sym] += PreTradeQuantity` |
| Executed | `RiskInfo::OnOrderExecuted(…, stockLimitType, apply_balance)` | `apply_balance` ise `TL −= execPrice × qty` (brüt takasta da uygulanır) ve `bakiye[sym] += qty` (`DEPO`/`BRUT_TAKAS` ise eklenmez). Her durumda `passiveTL −= execPrice × qty`. | `apply_balance` ise `TL += execPrice × qty` (`BRUT_TAKAS` ise eklenmez) ve `bakiye[sym] −= qty`. Her durumda `passiveQty[sym] −= qty`. |
| Canceled | `RiskInfo::OnOrderCanceled(order, sym, entered.Price(), entered.Quantity())` | `passiveTL −= entered.Price × entered.Quantity` | `passiveQty[sym] −= entered.Quantity` |
| Replaced | `RiskManager::OnOrderReplaced(old, new)` | `OnOrderCanceled(eskiP, eskiQ)` + `OnOrderAccepted(yeni)` | aynı |

- `stockLimitType` hissenin `stockRestrictions` değeridir; listede yoksa pazar geneli değer kullanılır.
- `PreTradeQuantity` OUCH OrderAccepted'ın alanıdır (`msg.pre_trade_quantity`). ❓ doğrulanmadı: BIST'te bu alanın "eşleşme öncesi toplam adet" mi olduğu.
- `entered` = host registry'deki emir. Accept'te `msg.quantity` ve `msg.price` ile güncellenir; fill'lerde güncellenmez.
- Executed'da fiyat **gerçekleşme fiyatıdır**, rezervasyon ise limit fiyatıyla yapılmıştı. Fiyat iyileşmesi olursa aradaki fark rezervasyonda kalır (§ 13).
- **Replace'te yeni rezervasyon sıfırdır:** `OnOrderReplaced` yeni `OrderAccepted`'a yalnız `Side`, `Price`, `Quantity` atar, `PreTradeQuantity` 0 kalır. `RiskInfo::OnOrderAccepted` ise `PreTradeQuantity` kullanır. Sonuç: eski rezervasyon serbest kalır, yenisi 0 olur (§ 13).
- Rejected olayı riske gitmez. Emir kabul edilmediği için rezervasyon zaten yoktur.

## 9. Replay, tekrarlanan olaylar ve gün içi restart

**Oturum içi tekrar** (OUCH reconnect replay, MAOrderSDK callback'lerinde, riskten önce):

| Olay | Tekrar kontrolü | Atlanırsa |
|---|---|---|
| Accepted | `entered.OrderID() != 0 && == msg.order_id` | Rezervasyon ikinci kez yapılmaz |
| Executed | `processed_execution_keys_` kümesi; anahtar `token:match_id:timestamp` | Bakiye ve rezervasyon ikinci kez değişmez |
| Canceled | `canceled_orders[token].OrderId() == msg.order_id` | Serbest bırakma ikinci kez yapılmaz |
| Replaced | Accept ile aynı | |

**FIX replay fill'i** (`msg.is_replay == true`, commit `f1fd998`):
- `OnOrderExecuted(…, apply_balance=false)` çağrılır. Yalnız rezervasyon (replay edilen accept'in yaptığı) serbest bırakılır, bakiye değişmez.
- Gerekçe (kod yorumu): "balances already include it", yani yüklenen bakiyelerin bu fill'i zaten içerdiği varsayılır.

**OUCH replay fill'i:** MAOrderSDK'da OUCH için `is_replay` bayrağı yok. Restart sonrası BIST'in replay ettiği OUCH fill'leri `apply_balance=true` ile bakiyeye **yazılır**. `PARSE_LOOP_START_TIMEOUT` (10 sn) penceresi yalnız pozisyonun DB'ye yazılmasını (`InsertPositionToDatabase`) atlar; riski etkilemez.

**Gün içi restart'ta durum şöyle kurulur:**
1. Bakiyeler `GetCustomerLimits`'ten yeniden yüklenir. Proto'ya göre bu değerler order-service işlemlerini **içermez**.
2. `RetrieveSentOrders` günün emirlerini DB'den `entered_orders`'a koyar. `OrderID` set edilmez (`OrderUtility::ConvertOrderToEnterOrder`). Bu yüzden replay edilen accept'ler dedup'a takılmaz ve rezervasyon yeniden kurulur.
3. Replay edilen fill/cancel'lar rezervasyonu düşürür. OUCH fill'leri bakiyeye de yazılır.
4. Gün içi stream delta'ları yalnız yeni stream açıldıktan sonrakilerdir. Restart öncesi delta'lar `GetCustomerLimits`'e yansıdıysa korunur. ❓ doğrulanmadı: sağlayıcının `SetCustomerLimits`'i gün içinde güncelleyip güncellemediği.

- **OUCH ve FIX tutarsızlığı:** Proto'ya göre doğru olan OUCH davranışıdır (bakiye bizim işlemleri içermiyor, replay yeniden uygular). FIX'teki "already include" varsayımı proto yorumuyla çelişir (§ 13).
- **Yarış:** `risk_manager->Start` limitleri detached thread'de çeker; `order_dispatcher->Start` hemen ardından SDK'yı açar. Replay olayları `account_limits` dolmadan gelirse "RiskInfo not found" ile atılır. Bu durumda o emirlerin rezervasyon ve bakiye etkisi kaybolur. ❓ doğrulanmadı: pratikte bu sıranın tersine dönüp dönmediği.

## 10. `LimitControlService` ilişkisi

- order-service `LimitControlService`'in **istemcisi değildir**. `LimitLogin`, `SetCustomerLimits`, `SetStockLimits`, `SetIntraDayCustomerLimits` için hiçbir çağrı yoktur. Yalnız `RiskManagerService::NewStub` oluşturulur (`RiskManager::Connect`).
- `limit_control.proto` yalnız `StockLimitType` enum'u için derlenir. `RiskInfo.h` ve `risk_manager.proto` bunu import eder. Üretilen `LimitControlService` stub'ı kullanılmaz.
- Bu, [ACIK-KONULAR K-43](../../ACIK-KONULAR.md)'ü order-service açısından teyit eder: workspace'te `LimitControlService` istemcisi yok. Limitleri harici bir sağlayıcı (aracı kurum risk sistemi) yazar. ❓ doğrulanmadı: sağlayıcının kim olduğu.
- **Proto kopyaları ayrışmış.** order-service'teki `limit_control.proto`'da `StockLimitationsRequest.isShortSellDefault` (alan 3) yok; trade-data-app'te var. order-service bu mesajı kullanmadığı için etkisi yok. `risk_manager.proto` iki repoda aynı.
- `DatabaseClient` içinde `risk_manager_stub` ve `MakeRiskServiceRequest` tanımlı, ama stub hiç oluşturulmuyor: ölü kod.

## 11. Hard cap ve MAOrderSDK yerel kontrolleri

| | `RiskManager` | MAOrderSDK yerel kontrol |
|---|---|---|
| Yer | order-service, dispatcher ve replace yolu | SDK, `enterOrder` içinde |
| Kapsam | § 1 tablosu (toplu emirler hariç) | Bu SDK'dan geçen **bütün** emirler: toplu emirler, FIX, HFT'nin kendi SDK'sı |
| Kontrol | Hesap bakiyesi, hisse bakiyesi, kısıtlar (müşteri bazlı, dinamik) | `order_hard_cap_try` (tek emir notional, **tam TL**, statik), brüt takas, enstrüman limiti ve bölme (`max_order_value`) |
| Ret | `OrderRejected`, kod 0, token boş | `onRejected` ile kod 1001–1004, `LOG_CRIT "LOCAL REJECT"` |

- `maordersdk.orderHardCapTry` (`ConfigurationManager` → `SdkLimitsConfig`, varsayılan 50 000 000). `0` verilirse `LOG_CRIT` atılır ve SDK varsayılanı korunur (`MAOSdkManager` init).
- İki mekanizma birbirinden habersizdir. RiskManager'ın geçirdiği emir hard cap'e takılabilir. Brüt takas enstrümanı iki yerde de reddedilir (önce RiskManager).
- Ayrıntı: [maordersdk § Emir gönderme](../maordersdk/README.md#emir-gönderme), [kalicilik-ve-config.md](kalicilik-ve-config.md).

## 12. Thread ve kilit modeli

| Thread | Ne yapar |
|---|---|
| MARpc sunucu thread'leri, gRPC handler thread'leri | `checkEnterOrder` (okuma) |
| MAOrderSDK callback thread'leri (`sdk_callback_mutex_` ile kendi aralarında sıralı) | `On*` → `RiskInfo` yazma |
| `intradayThread` | `RiskInfo` bakiye yazma |
| İki detached fetch thread'i | `account_limits.insert`, `stockRestrictions.insert`, `isDefaultShortSellRestriction` yazma |
| MAOSdkManager replace yolu | `checkEnterOrder` |

- `RiskManager` ve `RiskInfo`'da **hiç kilit yok**. `<shared_mutex>` include edilmiş, kullanılmıyor.
- Atomik olanlar yalnız `running`, `generalStockRestrictionOnBIST` ve iki "fetched" bayrağı.
- Sonuç:
  - `account_limits` / `stockRestrictions` (`unordered_map`) fetch thread'i yazarken okunabilir. Bu bir veri yarışıdır ve rehash sırasında çökme riski taşır.
  - `RiskInfo` alanları ve haritaları eşzamanlı yazılır/okunur.
  - Kontrol + rezervasyon atomik değildir (§ 5 "Dikkat").
- `Stop()`: `running = false` yapar ve `intradayThread.join()` çağırır. Thread `rpc->Read` içinde bloklu ve context iptal edilmiyor. Bu yüzden join, sunucudan bir mesaj gelene veya stream kapanana kadar bekler. ❓ doğrulanmadı: kapanışta pratikte asılı kalıp kalmadığı.

## 13. Şüpheli

Hepsi `development` `b86c0cf` itibarıyla; düzeltme kararı verilmedi.

- **bug? Stream yeniden açılmıyor.** `RiskManager::ReadFromStream` kopmadan sonra `Connect()`'i çağırıyor, ama `running` `true` olduğu için `Connect` "Already Connected" deyip dönüyor ve thread bitiyor. Gün içi limit delta'ları restart'a kadar kaybolur. Sunucuda okuyucu kalmadığı için sağlayıcının `SetIntraDayCustomerLimits` çağrısı tamponsuz kanalda bloklanır. Doğrula.
- **bug? Replace sonrası rezervasyon 0.** `RiskManager::OnOrderReplaced` yeni accept'e `PreTradeQuantity` atamıyor; `RiskInfo::OnOrderAccepted` ise `PreTradeQuantity` kullanıyor. Replace edilen her emrin rezervasyonu sıfırlanıyor; sonraki emirler daha fazla serbest bakiye görüyor.
- **bug? Kısmi fill sonrası iptal fazla serbest bırakıyor.** `onCanceled` `entered.Price() × entered.Quantity()` geçiriyor (accept anındaki adet), iptal edilen kalan adet `msg.quantity` değil. Fill'lerin serbest bıraktığı kısım tekrar düşülüyor. 0'a kırpma bunu gizler, ama aynı hesabın diğer emirlerinin rezervasyonunu da siler.
- **bug? Fiyat iyileşmesinde rezervasyon sızıntısı.** Alış rezervasyonu limit fiyatla yapılıyor, fill gerçekleşme fiyatıyla serbest bırakılıyor (`RiskInfo::OnOrderExecuted`). Fark gün sonuna kadar kalıyor; bu muhafazakâr yönde bir hata.
- **bug? uint64 sarması hisse kontrolünü delik bırakıyor.** `checkCustomerStockBalanceSufficiency`'de `it->second − passiveQty` uint64. Rezervasyon bakiyeyi aşarsa veya bakiye negatife düşüp sararsa (`updateStockQuantity` kırpmıyor) sonuç dev bir sayı olur ve satış geçer. Ayrıca `getStockPassiveOrderQuantity` kayıt yoksa `-1` döner; bu uint64'te `+1` etkisi yapar.
- **bug? `updateCustomerTlOverral` negatif uyarısı hiç tetiklenmez.** `customerTLOverall + amount < 0` uint64 karşılaştırmasıdır. TL kontrolü `int64` cast sayesinde yine doğru çalışır.
- **doğrula: Satış bakiye kontrolü yalnız kısıt varken.** `checkOrderConstraints`'te `Sell` bakiye kontrolü `stckLimit != NONE || generalStockRestrictionOnBIST != NONE` bloğunun içinde. Kısıtsız hissede bakiyesiz satış geçer. Kasıtlı olabilir (açığa satış serbestse fark etmez); niyet belirsiz.
- **doğrula: Pazar geneli `ACIGA_SATIS` listede olmayan hisseye uygulanmıyor.** `stockRestrictions`'ta olmayan hissede `stckLimit` yalnız `isShortSellDefault` ile `ACIGA_SATIS` oluyor. Proto ise "Buradaki kurallar hisse kurallarının üzerindedir" diyor.
- **doğrula: `DEPO`/`BRUT_TAKAS` hissede açığa satış serbest.** `findSuperiorStockLimit` tek değer tuttuğu için `ACIGA_SATIS` daha üstün bir kısıtla birleşince kayboluyor.
- **doğrula: Replace fark emri.** `orderedDifference` fiyat↑+adet↑'da `Δq × Δp` kontrol ediyor (eksik). Azaltma veya değişmeyen alanda eski emrin tamamını kontrol ediyor (fazla). Satışta kısıt varken fiyat replace'i haksız reddedilebilir.
- **doğrula: FIX replay bakiye varsayımı proto ile çelişiyor.** `apply_balance=!is_replay` "loaded balances already include it" varsayıyor. `risk_manager.proto` ise `customerTLOverall` ve `stockOverallList` için "bizim yaptığımız işlemler dahil olmadan" diyor. Ya FIX restart'ında fill'ler bakiyeden düşmüyor, ya da OUCH restart'ında iki kez düşüyor.
- **doğrula: Fail-open noktaları.**
  - Hesap `account_limits`'te yoksa emir geçer.
  - Limitler henüz yüklenmemişse emir geçer.
  - `running` `setRunning(true)`'dan önce `false` iken emir geçer.
  - Stream kopuksa emir geçer.
  - Hiçbiri alarm üretmez; yalnız `LOG_CRIT`.
- **bug? Limitler bir kez çekiliyor.** `StartTryingToFetchAccountLimits` ilk dolu yanıttan sonra duruyor. Sağlayıcının gün içi `SetCustomerLimits` güncellemesi (ör. hesap yasaklama, `isProhibited`) restart'a kadar görülmez.
- **bug? Kilit yok.** § 12: `account_limits`, `stockRestrictions`, `RiskInfo` haritaları eşzamanlı yazılıp okunuyor.
- **doğrula: Ölçek.** Bakiye `D` hesapta ×100, diğerlerinde ×1000 ölçekleniyor; emir tutarı `qty × raw price`. Doğruluk `decimal_count`'un 3 (pay) / 2 (`D`) olmasına bağlı. Kontrat çarpanı yok. Pazar limitleri (`main/secondary/otherMarketLimit`) hiç kullanılmıyor.
- **doğrula: Token yenilenmiyor.** Risk RPC'leri açılıştaki DataService JWT'sini (48 saat) kullanıyor. Süre dolunca fetch döngüleri `Unauthenticated` alır.
- **doğrula: Başlangıç yarışı.** `ReadFromStream` döngüsü `isRunning()`'i `Read`'den sonra kontrol ediyor; thread `setRunning(true)`'dan önce başlıyor. İlk mesaj bu dar pencerede gelirse stream sessizce kapanır.
- **doğrula: Ret mesajında token ve kod yok.** `sendOrderRejectedToApplication` `OrderToken` ve `RejectCode` atamıyor (§ 7).
