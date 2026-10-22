---
kapsam: HFT Classic (StrategyType 4) — kademe erime takibi, pozisyonlu/pozisyonsuz mod, second rule, stop loss/take profit, replace mode, follow max, wire alanları
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# HFT Classic (`HFT`, 4)

Tek bir orderbook üzerinde çalışır. En iyi alış veya satış kademesindeki (header) miktar bir eşiğin altına inince ("eriyince"), kademenin kırılacağını öngörüp karşı tarafa emir atar. Amaç kademe değişiminden önce davranmaktır.

Kod: `src/Strategy/HftClassic.{h,cpp}`, `src/Commands/HftClassicCommand.{h,cpp}`, ortak taban `src/Strategy/Strategy.{h,cpp}`.

## Ters isimlendirme (kritik)

Fonksiyon isimleri yaptıkları işin tersini söyler. Kod okurken buna dikkat et:

| İsim | Gerçekte |
|------|----------|
| `SendBidOrder` / `bidInfoOrder` | **SATIŞ** emri. Alış kademesi eridiğinde çağrılır. |
| `sendAskOrder` / `askInfoOrder` | **ALIŞ** emri. Satış kademesi eridiğinde çağrılır. |
| `passiveAskInfoOrder` | Alıştan sonra yazılan pasif **satış** (take profit) |
| `passiveBidInfoOrder` | Pasif **alış** |

`sendDirectOrderWithItch` içindeki yorum da bunu söyler: `//burda bir terslik var buy eriyorsa sell yolluyor`.

## Modlar

İki ayrı bayrak modu belirler. Karıştırma:

- **`Hft_Type`** (`HftType` enum): miktar hesabını seçer.
  - `1` = `HftClassic` = **Pozisyonlu** → `set*InfoQuantityPozisyonlu`
  - `2` = `HftNoPosition` = **Pozisyonsuz** → `set*InfoQuantityPozisyonsuz`
- **`isNoPositionMode()`** = `Start_With_Buy || Start_With_Sell`. Bu bayrak `Hft_Type`'tan bağımsızdır ve second rule, `updatePosition` ve fiyat limitlerini etkiler.

Engine bu iki bayrağı birbirine bağlamaz. UI tutarlılığı `normalizeHftFields` ile sağlar (bkz. mtrader-trade-ui `AGENTS.md` → "HFT chase type and its hidden fields"). Pozisyonlu moda geçilip eski pozisyonsuz alanlar bırakılırsa motor onları uygulamaya devam eder.

### Pozisyonlu (`Hft_Type` 1)

Strateji kademelerde kendi pasif emirlerinin olduğunu varsayar ve gün boyu döner. Örneğin satış tarafı için gönderilecek alış miktarı:

```
alış = (satış header'ındaki bizim satışlarımız) − balance − (header üstündeki bizim alışlarımız) + (header altındaki bizim satışlarımız)
```

`Chase_Sell_Passive` açıksa bir üst kademedeki satışlarımız da eklenir.

### Pozisyonsuz (`Hft_Type` 2)

Sıfır pozisyonla başlar ve `No_Position_Lot` kadar lotla kademeler arasında döner.
- `Start_With_Buy` → önce alır, `Start_With_Sell` → önce satar.
- `Perform_Single_Operation` → tek işlem yapıp durur.
- Fiyat limitleri yalnız bu modda uygulanır:
  - `Buy_Upper_Limit_Price`: satış header'ı bu fiyatın üstündeyse alış yapılmaz.
  - `Sell_Below_Limit_Price`: alış header'ı bu fiyatın altındaysa satış yapılmaz.
  - ⚠ Limit 0 bırakılırsa alış hiç gitmez, çünkü `0 >= header` sağlanmaz.

## Tetik (erime)

- **Abonelik** (`setupInitialSubscriptions`):
  - header snapshot (ilk senkron)
  - header changed
  - her taraf için `subscribeLevelChanged` eşik aboneliği: `Trigger_Qty_Buy` / `Trigger_Qty_Sell`. Eşik 0 ise abonelik açılmaz; follow-max açıksa yine açılır.
- **Hazırlık:** İlk header snapshot gelmeden hiçbir olay işlenmez. Snapshot gelince her iki taraf için bir kez `sendOrderWithFast` çalışır.
- **Erime koşulu** (`meltEnoughWithFast`): header miktarı ≤ eşik.
- **Kısıtlar:**
  - Yalnız sürekli işlemde (`continuousSession()`) emir gider.
  - OUCH replay penceresinde (`!ouchReplayComplete()`) olaylar işlenmez.
- **`Wait_For_Header`** (`shouldWaitForHeader`):
  - `true`: o tarafta header'da bizim emrimiz varsa beklenir.
  - `false`: yalnızca second rule emrimiz varsa beklenir.
- **Aktif stil** (`Hft_Buy_Active_Style` / `Hft_Sell_Active_Style`): Pozisyonlu modda header kendi lehine kayınca beklemeden doğrudan emir gönderilir (`updateOrderDepthWithItch` → `sendDirectOrderWithItch`).

## Tek emir kuralı: `sent`

`sent` bayrağı stratejinin **yolda bir algo emri** olduğunu gösterir. Bayrak açıkken yeni giriş yapılmaz.
- Emir gönderilmeden **önce** açılır. Sebebi: SDK senkron reject atabilir, `rejectOrder` iç içe çalışır ve bayrağı doğru kapatması gerekir.
- Algo emrinin accept'i gelince kapanır (`addOrder`).
- Aynı fiyata replace ack'i bayrağı kapatmaz (`samePriceReplaceAck`).
- `Replace_Mode` açıksa her Replaced mesajında kapanır.

## Second rule (saniye kuralı)

Tahmin yanlış çıkarsa (kademe kırılmazsa) pozisyondan çıkış mekanizmasıdır.

1. Her algo emri accept olunca (`SecondRule` ve `UserOrder` hariç) `Second_Rule_Duration` **saniye** sonrasına bir `PeriodicJob` kurulur. Süre 0 gelirse 1 sayılır. Replay penceresinde kurulmaz.
2. Süre dolunca `sendSecondRuleOrder` çalışır. Emir fiyatı hâlâ karşı header'a eşitse (yani kademe kırılmadıysa) ters tarafa emir yazılır:
   - **Fiyat: kendi tarafının header'ı** (pasif). Alış emrinin second rule'u satış header'ına satış olarak gider, satışınki alış header'ına alış olarak.
   - Tip `SecondRule`, `TIF_DAY`.
   - Miktar `getOrderQuantity(side, price)`.
3. Pozisyonsuz modda ek kurallar:
   - Fiyat limitleri uygulanır.
   - `Start_With_Buy` + `Buy_Passive_Level != 0` iken alış emrinin second rule'u gönderilmez.
   - Gönderilirse bekleyen pasif TP emri iptal edilir.

⚠ Eski bilgi tabanı second rule fiyatının karşı header (agresif) olduğunu söylüyordu; development'ta kendi header'ı (pasif).

`Second_Rule_Duration` HFT'de **saniyedir** (`uint16_t`); Tavan/Taban'da aynı isimli alan **milisaniyedir**.

## Take profit ve stop loss (pozisyonsuz alış akışı)

- **Hesaplama:** `Buy_Passive_Level != 0` ise alış girişi gönderilirken hesaplanır:
  - TP fiyatı = giriş + `Buy_Passive_Level` × tick
  - `stopLossPrice` = giriş − `Hft_Stop_Loss_Level` × tick
- **TP gönderimi:** Giriş emri giriş fiyatından **tamamen** dolunca `sendPassiveSellInfoOrder` pasif satışı yazar. Miktar `min(No_Position_Lot, balance − satış header'ındaki bizim satışlar)`.
- **Stop:** `checkStopLoss` alış header'ı `stopLossPrice`'a veya altına inince ve alış header miktarı eşiğin altındayken pasif TP emrini alış header'ına (veya `stopLossPrice`'a) replace eder. TP emri yoksa balance kadar yeni stop emri yazar.
- **Kapatma:** `Hft_Stop_Loss_Level = -1` stop loss'u kapatır.
  - ⚠ UI "kapalı" için 0 gönderiyor; bu bilinen ve çözülmemiş bir uyumsuzluk (mtrader-trade-ui `AGENTS.md`).
- **Kullanılmayan alan:** `Take_Profit_Level` command'da okunmuyor (satır yorum dışı).

## Pozisyon sıfırlanınca

`updatePosition`, strateji çalışırken ve replay bittikten sonra balance 0 olunca:
- `Start_With_Buy` açıksa tüm satışları iptal eder.
- `Start_With_Sell` açıksa tüm alışları iptal eder.
- Stop/TP durumunu sıfırlar.

## Bait + chase (uptick)

- **Satış tipi:** `Send_Sell_Orders_Instead_Of_Short` açıksa veya uptick kuralı açıksa (`ItchSdkClient::hasUptickRule`) satış emri `SELL` gider, yoksa `SHORT_SELL`.
  - ⚠ `hasUptickRule` enstrümana bakmaz; **bütün orderbook'lar için** config'teki `uptickRule` bayrağını döner (örnek config'te `false`). Borsa kuralı yalnızca ilan edilen günlerde uygulanır; o günlerde bayrağın elle açılması gerekir. ❓ Operasyonda nasıl yönetildiği doğrulanmadı.
- **Chase miktarı:** `Chase_Buy_Passive` açıkken, alış header'ının bir altındaki kendi alışlarımızın miktarı.
  - Uptick yoksa bu miktar doğrudan satış miktarına eklenir.
  - Uptick varsa: alış kademesi tamamen eriyince önce 1 lot **bait** satış (alış header − 1 tick, tip `ChaseBait`), ardından **chase** açığa satış (alış header'ı, tip `Chase`) gönderilir.
- Uptick kuralının kendisi: `00-genel/borsa-kurallari.md`.

## Base lot

- **Alanlar:** `Lot_Qty_Buy` / `Lot_Qty_Sell` (+ `Is_Lot_Qty_*_Enabled`).
- **Davranış:** Header dışındaki kademelerde duran kendi emirlerimiz için üst sınırdır. Her header değişiminde `OrderDepth::updateCumulativeOrders` çalışır: önden başlayarak limite kadar olan emirler tutulur, fazlası replace veya cancel edilir.
- **Header'daki emirlere dokunulmaz.**

## Replace mode (`Replace_Mode`)

- **Ne zaman:** Yalnız satış tarafında ve yalnız `Hft_Type` = 1 (pozisyonlu) iken.
- **Nasıl:** Satış gerektiğinde iki iş yapılır:
  1. Tahtada duran **tüm** satışlar hedef fiyata, **kendi miktarlarıyla** replace edilir (`replaceModeOrderForSelling`). Sıra en kötüden en iyiye: en yüksek fiyat ve kuyruğun arkası önce (`sellSortedTokens`).
  2. Eksik kalan `wantQty − resting` kadar yeni satış girilir.
- Hangisi daha büyük lot taşıyorsa önce o gönderilir.
- **Neden kendi miktarıyla:** Replace'te farklı miktar göndermek, combiner açıkken fill'ler Replaced'den önce geldiği için `orderMap`'i borsadan koparır.

⚠ Eski bilgi tabanındaki "yalnız en kötü emri, kalan miktar kadar replace eder" anlatımı geçersiz.

## Follow max (azami emir takibi)

Yeni özellik; eski bilgi tabanında yok.

- **Alanlar:** `Follow_Max_Buy` / `Follow_Max_Sell` (+ `Follow_Max_*_Percentage`).
- **Tetik:** Bir taraftaki agresif emir enstrümanın **azami emir büyüklüğündeyse** (ITCH SDK `isMaxSizeExecution`), kademe eşiğin üstünde olsa bile erime sayılır (`forceMelt`).
  - Azami emir lotu = `maxOrderValue` (tam TL, VERDA marj dosyasından DB'ye) × yüzde ÷ fiyat.
  - Yüzde 0 veya ≥100 ise tam azami emir kullanılır.
  - Header fiyatı değiştikçe yeniden hesaplanıp SDK'ya itilir (`pushMaxOrderQty`).
- **`Follow_Max_Buy` (alış girişi):**
  - Envanter hesabını atlar ve satış header'ından giriş yapar.
  - Lot: `No_Position_Lot`, yoksa `Lot_Qty_Buy`. İkisi de 0 ise giriş yapılmaz, WARN basılır.
  - Pozisyon turu başına **tek giriş** yapar (`followMaxBuyArmed_` mandalı). Balance 0'a dönüp alış tarafında çalışan emir kalmayınca yeniden kurulur (`rearmFollowMaxIfFlat`).
  - `Buy_Passive_Level` varsa TP/stop da kurar.

## Thread ve kilit

- **ITCH olayları:** Strateji kuyruğundan AlgoWorker thread'i işler (`processSingleEvent`).
- **OUCH callback'leri:** `addOrder` / `executeOrder` / `deleteOrder` / `updateOrder` / `rejectOrder` OUCH recv thread'inden gelir. Combiner açıkken `executeOrder` ITCH thread'inden de gelebilir.
- **Second rule:** periodic jobs thread'inde çalışır.
- **Kilit:** `buySellInfoMutex` (`recursive_timed_mutex`). ITCH yolu ve `setCommand` kilidi **100 µs** dener; alamazsa olayı **düşürür** (WARN "Lock timeout").

## Wire alanları

Kaynak: `src/Globals/GuiConstants.h`, `HftClassicCommand.cpp`.

| Alan | Tip | Varsayılan | Anlam |
|------|-----|-----------|-------|
| `Hft_Type` | Long | 1 | 1 pozisyonlu, 2 pozisyonsuz |
| `Trigger_Qty_Buy` / `Trigger_Qty_Sell` | Long | 0 | Erime eşiği (lot) |
| `Wait_For_Header` | Bool | false | |
| `Start_With_Buy` / `Start_With_Sell` | Bool | false | Pozisyonsuz başlangıç yönü |
| `No_Position_Lot` | Long | 0 | Pozisyonsuz lot, TP lotu |
| `Perform_Single_Operation` | Bool | false | |
| `Chase_Buy_Passive` / `Chase_Sell_Passive` | Bool | false | |
| `Send_Sell_Orders_Instead_Of_Short` | Bool | false | |
| `Replace_Mode` | Bool | false | |
| `Lot_Qty_Buy` / `Lot_Qty_Sell` | Long | 0 | Base lot |
| `Is_Lot_Qty_Buy_Enabled` / `Is_Lot_Qty_Sell_Enabled` | Bool | false | |
| `Follow_Max_Buy` / `Follow_Max_Sell` | Bool | false | |
| `Follow_Max_Buy_Percentage` / `Follow_Max_Sell_Percentage` | **Int** | 0 | Azami emrin yüzdesi; 0 = tam |
| `Buy_Upper_Limit_Price` / `Sell_Below_Limit_Price` | Long | 0 | **Raw fiyat** (enstrüman ölçeği) |
| `Buy_Passive_Level` / `Sell_Passive_Level` | Long | 1 | Kademe sayısı |
| `Hft_Stop_Loss_Level` | Long | -1 (command), 0 (default settings) | Kademe; -1 = kapalı |
| `Is_Stop_Loss_Enabled` | Bool | false | |
| `Second_Rule_Duration` | Long | 1 | **Saniye**; 0 → 1 |
| `Hft_Buy_Active_Style` / `Hft_Sell_Active_Style` | Bool | false | |
| `Time_In_Force` | Long | 0 | |
| `Start_Time` / `Stop_Time` | Long | 600 / 1200 | ❓ Birim ve kullanım doğrulanmadı |

Tüm fiyatlar **raw** (enstrümanın `decimalCount` ölçeğinde).

## UI

Yeni GUI route `hft`. Inline ayar hücreleri, pozisyonlu/pozisyonsuz alan normalizasyonu ve stop loss uyumsuzluğu: mtrader-trade-ui `AGENTS.md`.
