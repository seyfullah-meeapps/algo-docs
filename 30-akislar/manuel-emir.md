---
kapsam: GUI'den elle girilen emir (tek emir paneli ve Toplu/Sabah Emri ekranı), iptal ve replace — REST → trade-data-app → hangi motor/servis → order-service risk → MAOrderSDK → BIST ve dönüşün GUI'ye gelişi; fiyat ölçeği
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui        # eski GUI
    branch: main
    commit: 6715182
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: trade-data-app          # prod farkı
    branch: master
    commit: 4a43e19
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
dogrulama: 2026-10-23
durum: taslak
---

# Akış: GUI'den manuel emir, iptal ve replace

Tek uç: `POST /v1/sendOrders` (`GuiSendOrders`). Hedefi **`order_type`** ve **`strategy_type`** belirler; ayrı bir "manuel emir servisi" yoktur. Ayrıntılar (burada tekrarlanmaz):
- Payload alanları ve birimleri: [backend-sozlesmesi § 6](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#6-emir-gönderme-post-v1sendorders)
- `GuiSendOrders` dalları: [api.md § 7](../10-servisler/trade-data-app/api.md#7-guiservice-gui-dataproto-gui_apigo--rest-restport)
- HFT manuel emir komutları: [komutlar-ve-grpc § 3.2](../10-servisler/hftsrvprod/komutlar-ve-grpc.md#32-manuel-emir-komutları-command_type_orderrequest); yol seçimi: [emir-yasam-dongusu § 2](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#2-gönderim)
- AlgoProd serbest emir: [emir-yolu § 8](../10-servisler/algorithmic-trading/emir-yolu.md#8-serbest--manuel-emir-algo_user)
- order-service girişi ve risk: [arayuzler § 6](../10-servisler/order-service/arayuzler.md#6-orderdispatcher-ve-emrin-yolu), [risk.md](../10-servisler/order-service/risk.md)

## 1. Hedef tablosu (koddan, `gui_api.go` `GuiSendOrders`)

| GUI ekranı | `order_type` | `strategy_type` | Hedef | Sonraki yol |
|------------|--------------|-----------------|-------|-------------|
| Toplu Emir (Y) / Sabah Emri (E) | 1 MORNING, 2 OPENING, 4 EVENING | seçilen strateji tipi | **order-service** gRPC `SendOrder` (tek çağrı, döngü sonunda) | DB'ye yazılır, saatinde gönderilir → [sabah-emri-ve-handoff](sabah-emri-ve-handoff.md) |
| Emir paneli, "Strateji" seçili | 3 STRATEGY | workspace tipi (4, 8, 9, 13, 14, 15 / 6, 7, 10) | HFT veya AlgoProd `SetCommandRequest(Command_Type_OrderRequest=4)` | Motorun kendi yolu (§3, §4) |
| Emir paneli, "Serbest" — HFT workspace'i | 3 | **12** `HFT_User` | **HFT** | §3 — pratikte başarısız (Şüpheli) |
| Emir paneli, "Serbest" — diğer workspace'ler (Tavan, Taban, Teorik, Varant, Arbitraj, VWAP, Fon) | 3 | **1** `Algo_User` | **AlgoProd** (REST kopyası; K-27) | §4 → order-service |
| Teorik Fiyat formu | 5 (Y; proto dışı) / 5 (E) | 8 | HFT, `Order_Event_Type=4` THEORIC | [teorik-fiyat](../20-stratejiler/teorik-fiyat.md) |
| İptal / replace (her ekran) | **gönderilmez (0)** | çağıran panelin `strategy_type`'ı | O tipin motoru | §5 |

- `order_type` 1/2/4 dışındaki **her değer** (3, 5, 0) motor dalına gider. gRPC `SendOrder`'ın STRATEGY dalı order-service'te vardır ama trade-data-app onu **hiç kullanmaz** (risk.md § 1'deki ❓ kapanır: çağıran yok).
- Yeni GUI "Serbest" tipini `getFreeStrategyType` ile seçer (`app/lib/tradingConstants.ts`): HFT (4) → 12, diğer her şey → 1. VWAP panelinde varsayılan Serbest'tir. Eski GUI `SendOrderModal` aynı kuralı uygular ([eski-gui § 4.2](../10-servisler/mtrader-trade-ui/eski-gui.md#42-emir-defteri-orderbookorderbooktsx)).
- Kanal (`protocol`): Y emir paneli 4 ve 9'da OUCH, diğerlerinde FIX varsayılanı; E "HFT ve Tavan'da OUCH, diğerlerinde FIX". İptal/replace modalları hep `protocol: 1`.

## 2. Ortak giriş (GUI → trade-data-app)

1. **GUI** gövdesi `{"orders":[GuiEnterOrderRequest]}`; `side` 1/2/3, `price` **raw**, `quantity` lot, `unique_key` = `<obid>_<stratejinin kayıtlı hesabı>_<sid>_<strategy_type>`. Y `SendOrderPanel.tsx` fiyatı `displayToRawPrice(…, 10^decimalCount)` ile çevirir ve `confirmPriceSanity` sorar. **E fiyatı sabit ×1000 ile çevirir** (`SendOrderModal`, `CancelReplaceOrderModal`, `OrderForm`): VİOP'ta (`decimalCount=2`) emir 10× sapar (K-163); bu katmanlar ölçeği otomatik düzeltmez (raw değer aktarılır). Risk/fiyat limiti emri ayrıca reddedebilir; 10× fiyatın mutlaka BIST'e kabul edileceği sonucu çıkarılmaz.
2. **trade-data-app** her emir için:
   1. `GetApplicationUsername(strategy_type)`: `extServices[]`'teki motorun `applicationUser`'ı; bulunamazsa döngü 500 ile biter.
   2. `order_type` ∈ {1,2,4} → toplu liste (kademe açılımı ITCH'ten; `side=3` → "Order side is unknown") + motora `SetAccountStrategy` (hata yalnız log). **Yan etki:** HFT `AlgoSetAccountStrategy` o anahtar için stratejiyi çıplak komutla yaratır ve DB'ye taban ayar yazar ([komutlar-ve-grpc § 2](../10-servisler/hftsrvprod/komutlar-ve-grpc.md#2-rpcler)).
   3. Diğer → `ConvertOrderRequestToAlgoOrders`: Enter'da `Order_Event_Type`, `Exchange_Info`, `Orderbook_Id`, `Strategy_Id`, `Order_Channel` (Int), `Strategy_Unique_Key`, `Order_Side` (Int 1/2/3), `Order_Quantity`, `Order_Price` (Long raw), `Order_Lvl_Count`, `Strategy_Type`, ve sıfır değilse `Order_Type`, `Time_In_Force`. ⚠ master'da yok (2026-10-23): trade-data-app `master` `Order_Type`/`Time_In_Force` yollamaz → motor LIMIT/DAY varsayar.
   4. Motor bağlı değilse 500 "… service is not connected". Motor hatası (`INVALID_ARGUMENT` vb.) gRPC kodu korunarak döner.
3. Döngü ortasında hata → önceki motor emirleri **geri alınmaz**, toplu liste hiç gönderilmez. Başarı `{"status": true}`; yalnız "gönderim denendi" demektir.

## 3. HFT dalı (`strategy_type` 4, 8, 9, 12, 13, 14, 15)

```
GUI ─REST─► trade-data-app ─gRPC SetCommandRequest(4)─► HFT gRPC thread: GUIManager::dispatchOrders → handleEnterOrder
                                                          ├─ OUCH + SDK hesabın sahibi ─► MAOrderSDK ─OUCH─► BIST     (risk YOK)
                                                          └─ FIX, veya SDK sahip değil ─► OuchManager ─MARpc─► order-service ─risk─► MAOrderSDK ─► BIST
```

1. Strateji anahtarı `<Orderbook_Id>_<Exchange_Info>_<Strategy_Id>_<Strategy_Type>`; yoksa `getStrategyByDerivative`; o da yoksa `OuchManager::insertStrategy` (yalnız order-service kaydı) ve tekrar arama → bulunamazsa **`INTERNAL "Strategy creation failed"`** (HTTP 500). Yani strateji paneli önceden açılmış (`subscribeToOrderbook`) olmalıdır.
2. Doğrulamalar: miktar > 0, limitte fiyat > 0, `Order_Lvl_Count ≥ 1`, MARKET yalnız FIX ve tek kademe ⚠ master'da yok (2026-10-23), `userOrderBlockReason` (Varant Toplu çalışırken elle satış) → `FAILED_PRECONDITION` ⚠ master'da yok.
3. Gönderim **gRPC thread'inde**, replay gate'e takılmaz. `Order_Channel=2` (FIX) → her zaman order-service. OUCH → `maosdk->enterOrder`; `false` ve `ownsAccount` false → order-service yedek yolu; SDK sahipken `false` → **emir gitmez, yanıt yine OK**. `Order_Lvl_Count=N` → N emir, her biri bir tick daha pasif (tick stratejinin defterinden).
4. **Risk:** order-service `checkEnterOrder` yalnız order-service yolundan gidene uygulanır. Handoff sonrası OUCH ile SDK'dan giden manuel emir yalnız MAOrderSDK yerel kontrollerinden (hard cap, brüt takas, bölme) geçer ([risk § 11](../10-servisler/order-service/risk.md#11-hard-cap-ve-maordersdk-yerel-kontrolleri)).
5. **Dönüş:** SDK yolu → `HftMain.cpp` callback'leri → `internalOuchOrdersQueue` → `FetchOrders` (3 sn bekleme, 50'lik paket) → trade-data-app `transmitOuchMessages` → `/ws/v1/orders/start`. order-service yolu → order-service `SubscribeToOrders` → trade-data-app → aynı feed (HFT'nin `FetchOrders`'ına girmez). Ayrıntı: [emir-donusu](emir-donusu.md).

## 4. AlgoProd dalı (`strategy_type` 1, 6, 7, 10)

```
GUI ─REST─► trade-data-app ─gRPC SetCommandRequest(4)─► AlgoProd gRPC thread: GUIManager::dispatchOrders
     ─► (strategy info yoksa insertStrategyInfo, bloklar) ─► OuchManager::send ─ouch-sdk/MARpc─► order-service
     ─► OrderDispatcher::SendOrder ─► RiskManager::checkEnterOrder ─► MAOSdkManager::SendOrderAsync ─► MAOrderSDK ─OUCH/FIX─► BIST
```

1. `dispatchOrders`: strateji **aranmaz**. Zorunlu alan eksikse `INVALID_ARGUMENT`; enstrüman yoksa `INVALID_ARGUMENT`. `findStrategyInfo` yoksa `insertStrategyInfo` (ouch-sdk, timeout yok, K-151).
2. `Order_Channel ≠ 0` → `send(enterOrder, 0, kanal)` + `Order_Lvl_Count > 1` ise en çok 10 kademe (ilk fiyatın adımıyla). Kanal 0 → OUCH, kademe yok. TIF hep DAY; `Order_Type`/`Time_In_Force` AlgoProd'da okunmaz.
3. ouch-sdk `enterOrder` kuyruğa koyar ve döner (gönderim network-sdk recv thread'inde). gRPC yanıtı OK = "kuyruğa kondu".
4. **order-service** (bağlantının MARpc `processCallback` thread'i): `RequestReceived` → `GetAccountStrategy(strategyType, …)` (bulunamazsa **sessiz düşüş**) → `OrderDispatcher::SendOrder` → `checkEnterOrder` (ret → sentetik `OrderRejected`, `rejectCode=0`, token boş; K-197) → `SendOrderAsync` (senkron; hesap/enstrüman/FIX kullanıcısı yoksa sessiz düşüş) → MAOrderSDK bölme + gönderim. FIX kanalında kullanıcı `getNextFixClient`.
5. **Dönüş:** MAOrderSDK callback → `OrderResponseCallBack` → (a) `OrderServer::OnOrder*` → AlgoProd'un MARpc bağlantıları (userbook güncellenir; strateji yok, kimse beklemiyor); (b) `OrderServiceImpl::On*` → `order_queue` → `SubscribeToOrders` → trade-data-app `checkUserOrders` → `/ws/v1/orders/start` (`StrategyType` 1) ve `/itch` "benim emrim" işaretleri.

## 5. İptal ve replace

1. GUI `order_id`'yi (**BIST order id**, socket'ten string) yollar; `order_type` yok, `strategy_type` = panelin tipi. Replace'te Y `price` yalnız fiyat değiştiyse raw, değilse 0; E ×1000.
2. trade-data-app `orderService.GetOrderTokenByID(order_id)`: kendi **bellek** emir listesinde o id'li son olayın token'ını bulur; yoksa 500 "Order not found". Bellek order-service yeniden bağlanınca sıfırlanır ve HFT emirleri geri gelmez (veri-akisi § 5.4 madde 9) → o anda HFT emri iptal edilemez.
3. Motor (`strategy_type`'a göre, emrin kaynağına göre değil):

| | HFT | AlgoProd |
|-|-----|----------|
| Cancel | `Order_Token` zorunlu; `ownsOrder(token)` → SDK, değilse order-service. Yanıt hep OK | `Order_Token` + `Order_Channel` var olmalı; `cancelOrder` takipsiz → order-service. Kanal Long gelir, Int okunur → 0 (kullanılmadığı için zararsız) |
| Replace | Fiyat ve miktarın **ikisi birden pozitif olamaz** (400); yeni token HFT üretir; yönlendirme cancel ile aynı | Kontrol yok; miktar GUI'den aynen; takipsiz → order-service |
| order-service | Cancel'da risk yok; protokol `order_protocols[token]`'dan. Replace'te `orderedDifference` risk kontrolü ([risk § 6](../10-servisler/order-service/risk.md#6-replace-kontrolü)) | aynı |

4. Sessiz düşüşler: order-service'te bilinmeyen token, SDK `false` → istemciye olay gitmez; GUI'de emir değişmeden kalır.
5. Toplu emirlerde iptal/replace `order_type` 1/2/4 ile gelir ve order-service DB'sindeki **bekleyen** toplu emri siler/yeniden ekler ([arayuzler § 4.3](../10-servisler/order-service/arayuzler.md#43-sendorder-dalları)); gönderilmiş emri BIST'te iptal etmez.

## 6. Hata yolları (özet)

| Durum | GUI'nin gördüğü |
|-------|-----------------|
| order-service login olmamış | 200 `status:false` "Gui external services is not found" |
| `applicationUser` config'te yok | 500 "ApplicationType user is not found" |
| Motor bağlı değil | 500 "… service is not connected" |
| HFT stratejisi bellekte yok (Serbest 12 dahil) | 500 "Strategy creation failed" |
| HFT doğrulama retleri | 400 (`INVALID_ARGUMENT`) / `FAILED_PRECONDITION` |
| order-service risk reddi | 200; sonra `/orders`'ta `MyOrderReject` (`ReasonCode` 0, açıklama metni) |
| order-service sessiz düşüş (hesap-strateji yok, protokol 0, hesap/enstrüman yok) | 200; **hiçbir olay gelmez** |
| İptal: `order_id` trade-data-app belleğinde yok | 500 "Order not found" |
| Y istemci 10 sn zaman aşımı | Hata bildirimi; emir sunucuda gitmiş olabilir, otomatik retry yok; yeniden göndermeden önce emir durumu kontrol edilmeli |

## Şüpheli

- **bug? HFT "Serbest" (12) emri gönderim yolu başarısız (koddan çıkarım).** HFT `handleEnterOrder` anahtarı `…_12` ile arar; `createStrategy`'de `HFT_User` case'i yok ve HftSrvProd kodunda 12 için strateji yaratma dalı bulunmuyor. `insertStrategy` belleğe strateji eklemediği için ikinci arama da başarısız → `INTERNAL "Strategy creation failed"`. Yeni GUI (`tradingConstants.ts` yorumu "12 ile gönderildiğinde geçerlidir") ve eski GUI HFT workspace'inde Serbest'i 12 ile gönderiyor. ❓ doğrulanmadı: canlıda denendi mi; K-171'deki "12 emir geçmişine düşmüyor" şüphesinin asıl sebebi bu olabilir.
- **doğrula: HFT ailesi workspace'lerinden (Tavan, Taban, Teorik, Varant, Varant Toplu) "Serbest" emir AlgoProd'dan gider.** `getFreeStrategyType` yalnız 4'ü 12'ye çevirir, gerisi 1 → REST kopyasında AlgoProd. AlgoProd bağlı değilse bu workspace'lerde serbest emir 500 alır; emir order-service risk yolundan geçer, HFT SDK yolundan değil. Kasıtlı mı, ekibe sorulmalı.
- **doğrula: iptal/replace emrin değil panelin motoruna gider.** AlgoProd panelinden (6/7/10) handoff sonrası HFT SDK'sına ait bir emir iptal edilirse istek order-service'e gider; order-service'in MAOrderSDK'sı o token'ın sahibi değildir, iptal sessizce düşer (❓ doğrulanmadı: senaryonun UI'da mümkün olup olmadığı).
- **güvenlik: `GuiSendOrders` hesap sahipliğini kontrol etmez.** `account`/`unique_key` token kullanıcısının hesaplarıyla karşılaştırılmaz; motora ve order-service'e trade-data-app'in uygulama kullanıcısıyla gider (K-16 ailesi).
- **bug? Toplu emir girişi HFT'de strateji yaratır.** Her 1/2/4 emrinde HFT `AlgoSetAccountStrategy` çağrılır; anahtar yoksa çıplak `BaseStrategyCommand` ile strateji ve taban DB ayarı oluşur (aynı tanımsız davranış, [komutlar-ve-grpc Şüpheli](../10-servisler/hftsrvprod/komutlar-ve-grpc.md#şüpheli-davranışlar-koddan)). Stratejiler hiç silinmediği için toplu emirde kullanılan her anahtar HFT belleğinde kalır.
