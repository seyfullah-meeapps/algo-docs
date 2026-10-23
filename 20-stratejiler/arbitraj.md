---
kapsam: Arbitraj (StrategyType 6, AlgoProd) — spot/vadeli ve iki vadeli arasında fark/faiz arbitrajı; tipler, döngü, açma/kapama kuralları, fiyat formülleri ve ölçek, vade hesabı, paketler, risk/durma, wire alanları, UI, master farkları; sepet arbitraj
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading          # prod binary'si master'dan derlenir
    branch: master
    commit: aa150ee
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui            # eski GUI
    branch: main
    commit: 6715182
dogrulama: 2026-10-22
durum: taslak
---

# Arbitraj (`Arbitrage`, 6) — AlgoProd

**Fikir:** Bir VİOP vadelisi (türev) ile dayanağı (spot pay) ya da iki vadeli arasındaki fark (tick) veya zımni faiz eşiği aşınca pozisyon açar, fark kapanınca kapatır.
- Önce **türev bacağı** gider. Türev dolunca karşılığı (dolan kontrat × çarpan) **dayanak bacağı** gönderilir.
- Açılan her pozisyon bir **paket** (`ArbitragePackage`) olarak DB'ye yazılır. Kapama paket bazında yapılır.

Kod: `algoSrc/Strategy/Arbitrage/ArbitrageTracker.{h,cpp}`, `algoSrc/Commands/ArbitrageTrackerCommand.*`, `algoSrc/Data/ArbitrageData.h` (paket, `DrvOrderDetail`, `UndOrderDetail`), alan adları `algoSrc/Utilities/GuiConstants.h` (`ARB_*`), enum'lar `algoSrc/Globals/Enumarations.h`. Oluşturma `Strategy/StrategyFactory.h` (`ArbitrageTracker` dalı), parametre doğrulama `Managers/StrategyServiceImpl.cpp` `checkParams`.

Başka dosyada anlatılanlar (burada tekrar edilmez):
- Emir gönderimi (`OuchManager::send` → ouch-sdk → order-service): [emir-yolu](../10-servisler/algorithmic-trading/emir-yolu.md)
- Worker havuzu, kendi thread'i, `Manager::start/stop`: [uygulama-ve-threadler](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md)
- gRPC uçları, `AlgoService` kalıcılığı: [grpc-ve-veri](../10-servisler/algorithmic-trading/grpc-ve-veri.md)

## Strateji tipleri (`Arb_Strategy_Type`, char)

| Kod | Ad (motor / UI) | Fark ölçüsü | Açma eşiği alanları | Kapama eşiği alanları |
|-----|-----------------|-------------|---------------------|-----------------------|
| `D` (68) | `DiffTick` / — | türev − (teorik − temettü), tick | `Open_Tick` | `Close_Tick` |
| `F` (70) | `FutureSpotDiffTick` / "Spread" | türev − spot, tick | `Fs_Open_Tick` | `Fs_Close_Tick` |
| `T` (84) | `TwoFutures` / "Çift Vade" | türev − diğer vadeli, tick | `If_Open_Tick` | `If_Close_Tick` |
| `I` (73) | `InterestRate` / "Faiz" | zımni faiz (%) | `Open_By_Buy_Rate` / `Open_By_Sell_Rate` (+ `Funding_Cost`) | `Close_By_Buy_Rate` / `Close_By_Sell_Rate` (+ `Funding_Cost`) |
| `R` (82) | `TwoFuturesInterest` / "Çift Vade Faiz" | iki vade arası zımni faiz (%) | aynı faiz alanları | aynı faiz alanları |

- `T` ve `R` "iki vadeli" tiplerdir (`Enumaration::isTwoFutures`): "dayanak" bacağı da bir vadelidir (`Underlying_Instrument_Id`), çarpan 1'dir, `orderbookId` ile aynı enstrüman verilemez (`StrategyFactory`).
- `I` ve `R` "faiz" tipleridir (`Enumaration::isInterestRate`).
- **İki GUI de `D` üretmez** (yeni GUI `arbitrageSettingsPayload.ts` `getArbitrageCommandTypeCode`, eski GUI `ArbitrageStrategySettingsPage.tsx`: yalnız I/F/T/R). `D` yalnız Excel yüklemesi veya elle yazılmış DB ayarıyla gelebilir. ❓ doğrulanmadı: prod'da `D` kullanan strateji olup olmadığı.
- Tanınmayan kod `toArbitrageStrategyType`'ta `std::invalid_argument` fırlatır; strateji oluşturulmaz.

**Yön** (`ArbitrageSide`, char):
- `B` **Below**: türev ucuz → **türev al, spot sat** (açarken). Kapama: türev sat, spot al.
- `A` **Above**: türev pahalı → **türev sat, spot al** (açarken). Kapama: türev al, spot sat.
- `D`/`I`/`R`'de yön fark işaretinden seçilir: `diffTick >= 0` → Above, aksi Below (`checkOpenable`). `F`/`T`'de `Fs_Arbitrage_Side` sabitler.
- **Tek yön:** `packageList[0]` aktifse ve yönü farklıysa açma yapılmaz ("Opening position from both sides is not permitted"). Yalnız **ilk** paket kontrol edilir.

## Döngü (`doPeriodicChecks`)

development: worker havuzunda (`runsOnWorkerPool() == true`) çağrılır, bloklamaz; beklemeler `retryAfterNs_` ile yapılır. ⚠ master'da farklı (2026-10-22): kendi thread'inde `while(isRunning())` döngüsü, beklemeler `sleep_for` (200 µs / 5 ms), aradaki döngü uyumadan döner (strateji başına bir çekirdek ❓ doğrulanmadı). Ayrıntı: [uygulama-ve-threadler](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md).

Her tur sırası:

1. `retryAfterNs_` dolmadıysa dön.
2. **Seans** (`isOpenSession`):
   - `Start_Time − 3 sa` (iki vadelide `− 3 sa 30 dk`) henüz gelmediyse 200 µs sonra tekrar dene (strateji çalışır kalır).
   - Dayanak **veya** türev sürekli işlemde değilse → **`stop()`**. Yani `Start_Time` geçtikten sonra seans dışı (açılış seansı, ara, kapanış) stratejiyi durdurur; kendiliğinden yeniden başlamaz.
   - `Stop_Time ≤ şimdi` → `stop()`. (Saat karşılaştırması aşağıda, Şüpheli.)
3. `state.drvPos < 0` → `stop()`.
4. Dayanak header'larını oku (`itchHeaderChangedSubscriber`). İki vadelide bunlar `othDrvBest*` olur (× `undDecimalMultiplier`).
5. **Tavan/taban** (iki vadeli hariç): `undBestBuy ≥ tavan` veya `0 < undBestSell ≤ taban` → `stop()`. Tavan/taban değerleri strateji nesnesi oluşturulurken bir kez okunur (`instrumentPtr->getMaxPrice/getMinPrice`).
6. Türev header'ları yalnız `Adaptive_Spread_Enabled` açıksa **veya** `Derivative_Type = Q` ise okunur. Pasif (`Z`) modda adaptive kapalıysa `drvBest*` yalnız `startProperly`'deki ilk değerde kalır.
7. `updateArbitrageState` (fiyatlar, `diffTick`/`fsDiffTick`/`ifDiffTick`, zımni faizler, teorik fiyat), `checkPassiveUndOrders`.
8. Bir header değiştiyse veya yeni komut geldiyse `checkPassiveDrvOrders` (pasif türev replace).
9. **`runStrategy`** (`ArbitragePackageMtx` altında):
   1. `checkDrvExecution`: türev add/reject/cancel/execute olayları → dolum tamamsa dayanak emri (`sendUnderlyingOrder`).
   2. `checkUndExecution`: dayanak add/execute → bacak tamamsa `positionOpened` / `positionClosed`.
   3. **Kapama:** `closing_position` yoksa ve (`Closing_Limit_Check` kapalı **veya** `totalClosedQty < Contract_Limit_Closing` ve `drvPos > 0`) ise `getMostProfitablePackage`. Pasif modda kârlılığa bakmadan `closePosition(…, true)` (fiyat zaten kâr hedefinden hesaplanır); aktif modda yalnız `isProfitable` ise.
   4. **Açma:** `checkOpenable` geçerse ve `opening_position` yoksa: pasifte `openPassivePosition`, aktifte `openPosition` (son turda "hepsi iptal" olmadıysa).

Bayraklar: `opening_position`, `closing_position`, `isDrvReplacingOpen/Close` aynı anda en fazla bir açma ve bir kapama türev emri olmasını sağlar (`openingDod`, `closingDod`). `checkStatus` hepsini sıfırlar (start, stop, "illegal transaction time" reddi, tüm emir iptali).

## Açma kuralları

**`checkOpenable`:**
- Aktif (`Q`) modda `isProfitableOpen` ve `checkParameters` şart. Pasif (`Z`) modda eşik kontrolü **yok**; pasif emir sürekli "istenen fiyat"ta bekler.
- `drvPos ≥ Contract_Limit` → açma yok.
- Below + `Is_Spot_Sell_Allowed = P` + iki vadeli değil → açma yok.
- Tek yön kuralı (yukarıda).

**`checkParameters` (yalnız aktif):**

| Tip | Koşul |
|-----|-------|
| D | `\|diffTick\| ≥ Open_Tick` |
| F, Below | `fsDiffTick ≤ Fs_Open_Tick`, `fsDiffTick = round((drvAsk − undBid)/0,01)` |
| F, Above | `fsDiffTick ≥ Fs_Open_Tick`, `fsDiffTick = round((drvBid − undAsk)/0,01)` |
| T | `\|ifDiffTick\| ≥ If_Open_Tick` (Below: `drvAsk − othBid`, Above: `drvBid − othAsk`) |
| I, R | Below: `Open_By_Buy_Rate + Funding_Cost > 0`, `diffTick ≤ 0`, `calcIntRateByBuy ≤ Open_By_Buy_Rate + Funding_Cost`. Above: `Open_By_Sell_Rate + Funding_Cost > 0`, `diffTick > 0`, `calcIntRateBySell ≥ Open_By_Sell_Rate + Funding_Cost` |

`isProfitableOpen` (`updateArbitrageState`): `drvBid − (teo(undAsk) − temettü)` ≥ 0 ise true; değilse `drvAsk − (teo(undBid) − temettü)` < 0 ise true. Türev teorik bandın içindeyse false. Bu D-tipi hesap **bütün tiplerde** aktif açmayı kapılar.

**Aktif açma (`openPosition`):** miktar = `Contract_Limit − drvPos`, `Package_Limit > 0` ise onunla sınırlı (yarım kalan paket hakkı `currentDrvOrderQtyPackage` ile taşınır). Below: türev **alış**, fiyat `drvBestSell`; Above: türev **satış**, fiyat `drvBestBuy`. TIF **FaK** (`TIF_IMMEDIATE_OR_CANCEL`).

**Pasif açma (`openPassivePosition`):** miktar = `Contract_Limit − drvPos − passiveOrderQty`, `Package_Limit` ile sınırlı. Fiyat `calculateWantedPriceOpen`, TIF **DAY**. Header değiştikçe istenen fiyat yeniden hesaplanır, farklıysa replace (`checkPassiveDrvOrders` → `replaceOrderDrv`, miktar değişmez).

**Dolum işleme:**
- Aktif: `excQty + iptal ≥ gönderilen` olana kadar beklenir, sonra toplam dolan kadar dayanak emri. Gönderilen miktarın **tamamı** iptal olursa (`cancelData->quantity == currentDrvOrderQty`) bayraklar sıfırlanır, 5 ms sonra yeniden denenir (`allCancelledCheck`).
- Pasif: her dolum parçası hemen paket + dayanak emri üretir.
- Açma dolumunda paket eklenir (`updateArbitragePackage`): `drvPos += dolan`, `drvPrice = dolum fiyatı × drvDecimalMultiplier`, `undPrice = 0`, `undExcQty = 0`, paket DB'ye yazılır. Dayanak bacağı dolunca (`positionOpened`) `undPrice`, `undExcQty`, `intRate`, beklenen/gerçek marj yazılır ve paket `isActive` olur.

## Kapama kuralları

**`getMostProfitablePackage`:** aktif ve `contractQty > 0` paketler arasında en yüksek `profitTick`:
- Below paket: `(drvBid − ap.drvPrice) + (ap.undPrice − undAsk)`
- Above paket: `(ap.drvPrice − drvAsk) + (undBid − ap.undPrice)`
- (T'de `und*` yerine `othDrv*`.) Birim: ×1000 ölçek (1 tick = 10).

**Kârlı mı (`isProfitable`, aktif kapama için):**
- D: `profitTick ≥ Close_Tick × 10`; F: `≥ Fs_Close_Tick × 10`; T: `≥ If_Close_Tick × 10`.
- I/R: seçilen paketin `profitRate ≥ 0`. Below: `calcIntRateBySell − (Close_By_Buy_Rate + Funding_Cost)`; Above: `(Close_By_Sell_Rate + Funding_Cost) − calcIntRateByBuy`. Paket seçimi yine `profitTick`'e göredir.

**`closePosition`:** miktar = paketin `contractQty`'si; `Closing_Limit_Check` açıksa `Contract_Limit_Closing − totalClosedQty` ile, `Package_Limit_Closing > 0` ise onunla sınırlı. Paket `drvPos`'tan büyükse `drvPos`'a kırpılır. `drvPos ≤ 0` iken çağrılırsa `stop()`.
- Aktif: Below paket → türev satış `drvBestBuy`'dan; Above → türev alış `drvBestSell`'den; **FaK**.
- Pasif: `calculateWantedPriceClose` fiyatından **DAY**; replace `checkPassiveDrvOrders`.
- Türev dolunca `contractQty -= dolan`, `drvPos -= dolan`, dayanak emri gider. Dayanak dolunca (`positionClosed`) `undExcQty -= dolan`; 0 olunca paket `isActive=false`, `isCompleted=true`. Kâr `state.totalProfit`'e eklenir.

`totalClosedQty` yalnız bellekte tutulur; process yeniden başlarsa sıfırlanır (❓ doğrulanmadı: `Contract_Limit_Closing`'in gün bazlı mı kastedildiği).

## Fiyat hesapları ve ölçek

**İç ölçek (motor sözleşmesi):** bütün `long` fiyatlar **TL × 1000**; `double` olanlar **TL**.
- `drvDecimalMultiplier` / `undDecimalMultiplier` = 10 eğer enstrümanın `decimalPrice == 2`, değilse 1 (`ArbitrageTracker` yapıcısı). VİOP ham fiyatı (kuruş) × 10 → ×1000.
- Spot (iki vadeli olmayan) dayanak header'ı **çarpansız** alınır, yani spotun 3 ondalıklı (×1000) olduğu varsayılır.
- `*Double = long / 1000` (`undPriceDivider`), `tickSize = 0,01` TL sabit (enstrümanın gerçek adımından bağımsız; adım yuvarlaması ayrıca yapılır).
- Wire'a giderken türev fiyatı `/ drvDecimalMultiplier` (kuruş), iki vadeli dayanak `/ undDecimalMultiplier`.
- Yeni GUI aynı ×1000 referansını kullanır (`arbitrageScale.ts` `ARBITRAGE_REFERENCE_DIVIDER`); paket fiyatları `Arb_Drv_Price`, `Arb_Und_Price` bu ölçektedir.

**Teorik fiyat (`calculateTheoreticalPrice`):** `teo = fiyat × (1 + yıl × Current_Interest_Rate / 100)`. ⚠ master'da farklı (2026-10-22): `/100` yok, `teo = fiyat × (1 + yıl × Current_Interest_Rate)` (development commit c811418 "Fix theoretical price calculation", 2026-09-03). Etki: master'da oran yüzde girilirse (ör. 45) teorik fiyat ~yıl×45 kat şişer; `diffTick`, `isProfitableOpen`, D/I/R yön seçimi ve `Theo_Price` bundan etkilenir. ❓ doğrulanmadı: prod kullanıcılarının bu alana 45 mi 0,45 mi girdiği.

**`diffTick`** (`updateArbitrageState`): önce `round((drvBid − (teo(undAsk) − Dividend_Prc)) / 0,01)`; negatifse `round((drvAsk − (teo(undBid) − Dividend_Prc)) / 0,01)`. İki vadelide `und` yerine diğer vadeli, yıl = `|yıl_türev − yıl_diğer|`.

**Zımni faiz (`calculateInterestRate`):** `((drv / und) − 1) / yıl × 100` (basit yıllık %). `calcIntRateByBuy = f(undBid, drvAsk)`, `calcIntRateBySell = f(undAsk, drvBid)`.

**Pasif açma fiyatı (`calculateWantedPriceOpen`)**, TL; sonra `round(×100)` kuruş, adıma yuvarlama (Below aşağı, Above yukarı):

| Tip | Below (türev al) | Above (türev sat) |
|-----|------------------|-------------------|
| F | `undBid − 0,01 × Fs_Open_Tick` | `undAsk + 0,01 × Fs_Open_Tick` |
| D | `teo(undBid) − 0,01 × Open_Tick − Dividend_Prc` | `teo(undAsk) + 0,01 × Open_Tick − Dividend_Prc` |
| T | `othBid − 0,01 × If_Open_Tick` | `othAsk + 0,01 × If_Open_Tick` |
| I | `((Open_By_Buy_Rate + Funding_Cost)/100 × yıl + 1) × undBid − Dividend_Prc/100` | aynı, `Open_By_Sell_Rate`, `undAsk` |
| R | I gibi, `yıl = \|yıl_türev − yıl_diğer\|`, `othBid/othAsk` | |

- İstenen fiyat < 0 → `stop()`. Adım 0 → `stop()`.
- **Adaptive spread** (`Adaptive_Spread_Enabled`): istenen fiyat makasın içindeyse (ve son gönderilen fiyat değilse) Below için `drvBid + Adaptive_Spread_Level × adım`'ı, Above için `drvAsk − Level × adım`'ı geçmeyecek şekilde kırpılır; yani emir en iyi fiyattan `Level` adım içeride, istenen fiyattan daha iyi tarafta durur. Zaten en iyi fiyattaysak fiyat korunur.

**Pasif kapama fiyatı (`calculateWantedPriceClose`)**, yuvarlama Below yukarı, Above aşağı (kâr lehine):
- F/D, `Closing_By_Spot` kapalı: Below `ap.drvPrice + CloseTick×10 − round10(ap.undPrice) + undAsk`; Above `ap.drvPrice + undBid − round10(ap.undPrice) − CloseTick×10`. Yani paket kârı tam `Close_Tick` (F'de `Fs_Close_Tick`) olacak türev fiyatı. T aynı formül (`If_Close_Tick`, `othDrv*`, `round10` yok).
- `Closing_By_Spot` açık: Below `undAsk + 0,01 × CloseTick`, Above `undBid − 0,01 × CloseTick` (paketin açılış fiyatına bakılmaz).
- I/R: açma formülü, `Close_By_Buy_Rate` (Below) / `Close_By_Sell_Rate` (Above), Below `undAsk`, Above `undBid`.

**Kâr (`positionClosed`):** `closeProfitTick = ((drvKapama − ap.drvPrice) + (ap.undPrice − undKapama)) / 10` (Below; Above tersi), `netProfit = closeProfitTick × kapanan kontrat`, `state.totalProfit += netProfit`. GUI'ye `Total_Profit = totalProfit × 1000` gider. Birim: kontrat başına 0,01 TL × kontrat; çarpan uygulanmaz (Şüpheli).

## Vade ve tatil hesabı

`DerivedInstrument` yapıcısı (`Instruments/TradableInstruments/DerivedInstrument.h`), process açılışında **bir kez**:
- `daysToExpiration` = vade tarihi 00:00 − bugün 00:00 (yerel saat), gün.
- `daysToTrade` (yalnız vadeli) = `daysToExpiration + daysDelayed(vade) − daysDelayed(bugün)`. `daysDelayed(t)` = t'den sonra **2. iş gününe** ulaşmak için gereken takvim günü (hafta sonu ve `holidays.csv` atlanır; `TimeUtility::daysToTrade`, `IsHoliday`). Yani iki tarihin T+2 valör günleri arasındaki takvim günü.
- Yıl = gün / 365.

| Tip | `derivativeYearsToExpiration` | dayanak/diğer vadeli yılı |
|-----|-------------------------------|---------------------------|
| D, F, I | `daysToTrade / 365` | — |
| T | `daysToTrade / 365` | diğer vadelinin `daysToTrade / 365` |
| R | **`daysToExpiration / 365`** | diğer vadelinin `daysToExpiration / 365` |

Tatil dosyası config'teki `holidaysBIST` yolundan okunur; dosya yoksa tatilsiz hesaplanır ([config](../10-servisler/algorithmic-trading/config.md)). Process gün içinde yeniden başlatılmazsa değerler ertesi güne taşınır (AlgoProd günlük kapanır, `EndOfMessages`).

## Dayanak (spot) emri

`sendUnderlyingOrder`:
- Miktar = `totalDrvExecQty × underlyingMultiplier`. Çarpan varsayılan 100; `Optional_Underlying` açıksa komuttaki `Underlying_Multiplier`; iki vadelide 1.
- Yön: türevin tersi. Below açılış spot **satışı**; `Sell_Type = T` ve iki vadeli değilse `ShortSell` (açığa).
- Fiyat: satışta `undBestBuy`, alışta `undBestSell` (iki vadelide `othDrv*`). `Stop_Manual_Mode` + `Stop_Loss_Type = P` ise türev emri gönderildiği andaki dayanak fiyatı kullanılır (`dod.undCurrentPrice` / `lastCalcUndPrice*`). Yeni GUI `Stop_Manual_Mode`'u her zaman `true` gönderir.
- TIF: `Stop_Loss_Type = A` → kodda `TimeInForce::Market`, **ama** `EnterOrder::convertToOuchTIF` Market'i tanımaz ve **DAY**'e düşürür. Yani "aktif" dayanak emri karşı en iyi fiyattan DAY limit emirdir, piyasa emri değil. `P` → DAY.
- Takip (`checkPassiveUndOrders`): dayanak emri bekledikçe, `Stop_Loss_Type = P` iken `tickDiff ≤ Stop_Loss_Level` **ve** geçen süre ≤ `Stop_Loss_Second` sn olduğu sürece dokunulmaz. Biri aşılınca güncel karşı en iyi fiyata replace edilir (kalan miktar). `Stop_Loss_Type = A`'da bekleme koşulu yoktur.
- **Elle müdahale** (`PassiveUnderlyingCommand`, `commandType` 6, `Arb_Package_Id` + `Arb_Und_Cmd_Type`): 1 Execute (karşı fiyata replace), 2 Increase (+1 adım), 3 Decrease (−1 adım). Aynı emirde bekleyen işlem varsa `ALREADY_EXISTS`.
- `Passive_Barrier` motor tarafından **okunmaz** (yalnız parse ve geri yollama).

## Paket yönetimi ve kalıcılık

- **Durum:** `ArbitrageStruct` (`drvPos`, `undPos`, `totalProfit`, `packageList`). Yapıcıda DB'den okunur, yoksa oluşturulur. Değişiklikler `DatabaseServiceClient::setArbitrageDataAsync` ile kuyruğa atılır ve yerel önbellek güncellenir; okuma (`getArbitrageData`) önbellekten döner. Ayrıntı: [grpc-ve-veri](../10-servisler/algorithmic-trading/grpc-ve-veri.md).
- **Başlatma kontrolü (`arePackagesConsistent`):** durmuş strateji başlatılırken her paket için `undExcQty == contractQty × çarpan` ve `Σ contractQty == drvPos` aranır. Tutmazsa `StrategyStartException` → gRPC `FAILED_PRECONDITION` (HTTP 400), strateji başlamaz; ilk oluşturmada strateji kayıttan silinir (`StrategyManager::commandReceived`). ⚠ master'da yok (2026-10-22): master yarım paketle de başlar.
- **Pozisyon ekle** (`SetBalanceCommand`, `commandType` 3): yalnız durmuşken (aksi `UNAVAILABLE`). `Order_Side` `S` → Above paket, `B` → Below paket; fiyat verilmezse güncel en iyi fiyatlar. `Arb_Und_Exc_Qty` hem pakete hem `undPos`'a yazılır.
- **Paket güncelle** (`PackageCommand`, `commandType` 2, `Arb_Package_Type = 1`): yalnız durmuşken; çalışırken sessizce yok sayılır ama gRPC OK döner. Alanlar `Arb_Contract_Qty`, `Arb_Und_Exc_Qty`, `Arb_Drv_Price`, `Arb_Und_Price`; farklar `drvPos`/`undPos`'a yansıtılır.
- **Paket sil** (`Arb_Package_Type = 2`): önce DB'den silinir, sonra bellekten; **çalışırken de** yapılabilir.
- ⚠ master'da farklı (2026-10-22): `updatePackage` ve `setBalance`'ta `isRunning` kontrolü kilit alınmadan yapılır; `updateStateFromDatabase` `state`'i kilitsiz değiştirir; `setCommand` `ArbitragePackageMtx` almaz (start/stop yarışı mümkün).

## Risk ve durma koşulları

| Koşul | Davranış | Yer |
|-------|----------|-----|
| Türev reddi `-850002`, `-850004`, `-850044`, `-420131` (kod veya ret metni) | `stop()` (PTRM) | `checkDrvExecution` |
| Türev reddi `-420177` (order not found) | replace bayrakları sıfırlanır, devam | aynı |
| Türev reddi illegal transaction time (`-1800042`, `-110023`, `-1004048`, `-704130`) | `checkStatus`, devam | aynı |
| Türev, diğer her ret kodu | `stop()` | aynı |
| Dayanak reddi | **dinlenmez** (dayanak bacağına reject aboneliği yok) | `startProperly` |
| `OuchManager::send` istisnası | `stop()` | `sendTransaction` |
| Seans dışı, `Stop_Time`, tavan/taban, `drvPos < 0`, adım 0, istenen fiyat < 0 | `stop()` | yukarıda |
| DB yazımı başarısız / durum okunamadı | `stop()` | `updateDatabaseWithCurrentState` |

`-850064` AlgoProd'da tanımlı değildir. Kodlar: `Globals/GlobalDefinitions.h`, [borsa-kurallari](../00-genel/borsa-kurallari.md).

- `stop()` → `exitProperly`: **yalnız türev** emirleri iptal edilir. Dayanak emirlerinin iptali yorum satırında (`TODO: Check if this is necessary`); bekleyen dayanak emirleri ve `undOrderDetails` kalır.
- development: `sendOrder`/`replaceOrderDrv` strateji durmuşsa emir göndermez (stop yarışına karşı). ⚠ master'da yok (2026-10-22).

## Parametreler (wire, `GuiConstants.h` `ARB_*`)

`checkParams` zorunlu tutar: unique key, `Arb_Strategy_Type`, `Strategy_Id`, `Exchange_Info`, `Orderbook_Id`, `Underlying_Instrument_Id` (≠ orderbook), `Channel_Enum`, `Is_Spot_Sell_Allowed`, `Derivative_Type`, `Sell_Type`, `Start_Time`, `Stop_Time` (> 0), `Underlying_Multiplier` (> 0), ayrıca limitler, stop alanları, `Open_Tick`, `Close_Tick`, dört faiz oranı, `Dividend_Prc`, `Current_Interest_Rate` alanlarının varlığı. Eksikse `INVALID_ARGUMENT`.

| Alan | Tip | Birim | Yeni GUI varsayılanı | Anlam |
|------|-----|-------|----------------------|-------|
| `Orderbook_Id` | Long | — | — | Türev (vadeli) |
| `Underlying_Instrument_Id` | Long | — | satırın `spotId`'si | Dayanak; T/R'de diğer vadeli |
| `Exchange_Info` | String | — | — | Türev hesabı. Spot hesabı = ilk `-`'ten sonraki kısım (`params.underlyingExchangeInfo`); `-` yoksa aynısı |
| `Arb_Strategy_Type` | Int (char) | — | satır tipi | `D`/`F`/`T`/`I`/`R` |
| `Derivative_Type` | Int (char) | — | 90 `Z` | `Q` aktif (FaK), `Z` pasif (DAY + replace) |
| `Fs_Arbitrage_Side` | Int (char) | — | 0 | F/T yönü: 65 `A`, 66 `B`. GUI'deki "Automatic" (79 `O`) için Şüpheli'ye bak |
| `Sell_Type` | Int (char) | — | 83 `S` | `S` normal satış, `T` açığa satış |
| `Is_Spot_Sell_Allowed` | Int (char) | — | 80 `P` | `F` serbest, `P` yasak (Below açılmaz) |
| `Open_Tick` / `Close_Tick` | Long | tick (0,01 TL) | 0 | D |
| `Fs_Open_Tick` / `Fs_Close_Tick` | Long | tick | 0 | F |
| `If_Open_Tick` / `If_Close_Tick` | Long | tick | 0 | T |
| `Open_By_Buy_Rate`, `Open_By_Sell_Rate`, `Close_By_Buy_Rate`, `Close_By_Sell_Rate` | Double | % yıllık | 0 | I/R eşikleri |
| `Funding_Cost` | Long | % (tam sayı) | boş | Faiz eşiklerine eklenir |
| `Current_Interest_Rate` | Double | % (dev) / ⚠ master: oran | 0 | Teorik fiyat faizi |
| `Dividend_Prc` | Double | D'de TL, I/R'de /100 (Şüpheli) | 0 | Temettü düzeltmesi |
| `Contract_Limit` | Long | kontrat | 0 | Toplam açık kontrat (`drvPos`) üst sınırı |
| `Package_Limit` | Long | kontrat | 0 | Tek emir/paket büyüklüğü; 0 = sınırsız |
| `Contract_Limit_Closing` | Long | kontrat | 0 | `Closing_Limit_Check` açıkken process ömrü boyunca kapatılabilecek toplam |
| `Package_Limit_Closing` | Long | kontrat | 0 | Tek kapama emri; 0 = sınırsız |
| `Closing_Limit_Check` | Bool | — | true | |
| `Closing_By_Spot` | Bool | — | false | Pasif kapama fiyatı güncel spot ± tick |
| `Optional_Underlying` / `Underlying_Multiplier` | Bool / Long | adet/kontrat | false / 100 | Açıksa çarpan komuttan |
| `Stop_Loss_Type` | Int (char) | — | 80 `P` | Dayanak emri: `A` (DAY, hemen replace) / `P` (bekle) |
| `Stop_Loss_Level` | Long | tick | 0 | Pasif dayanak emrinin karşı fiyattan izin verilen uzaklığı |
| `Stop_Loss_Second` | Long | saniye | 0 | Pasif dayanak emrinin bekleme süresi |
| `Stop_Manual_Mode` | Bool | — | true (sabit) | Dayanak fiyatı = türev gönderimindeki fiyat |
| `Adaptive_Spread_Enabled` / `Adaptive_Spread_Level` | Bool / Long | adım | false / boş | Pasif açmada en iyi fiyattan N adım içeride |
| `Start_Time` / `Stop_Time` | Long | günün saniyesi, İstanbul | 36000 / 64800 | Saat karşılaştırması Şüpheli'de |
| `Channel_Enum` | Int | — | 1 | 1 OUCH, 2 FIX ([emir-yolu](../10-servisler/algorithmic-trading/emir-yolu.md)) |
| `Passive_Barrier` | Long | — | `Dividend_Prc` kopyası | **Okunmaz** |
| `First_Future`, `Second_Future`, `Third_Future` | Bool | — | false | **Okunmaz** (parse + geri yollama) |

GUI'ye giden mesajlar:
- `ArbitrageStrategyActivity` (`StrategyActivities.h`): `Drv_Pos`, `Und_Pos`, `Drv_Avg_Price`, `Und_Avg_Price` (×1000), `Theo_Price` (`lastThPrc × 1000`, son işlem fiyatından, **TL × 1000**, enstrüman ölçeğine bölünmez), `Int_By_Buy`, `Int_By_Sell`, `Avg_Calc_Int_Rate` (% × 1000), `Total_Profit` (× 1000), `Closed_Position_Qty`, `First_Open_Date`, `Last_Up_Date`.
- `ArbitragePackageActivity`: paket (`Arb_Package_Id`, `Arb_Pack_Token`, `Arb_Contract_Qty`, `Arb_Init_Contract_Qty`, `Arb_Drv_Price`, `Arb_Und_Price`, `Arb_Und_Exc_Qty`, `Arb_Int_Rate`, `Arb_Is_Active`, `Arb_Is_Completed`, `Arb_Strategy_Side`, beklenen/gerçek marjlar), durum (`Arb_Package_List`), `Package_Activity_Is_Update/Is_Delete`.
- Pasif dayanak emri aktivitesi (`PassiveOrderActivity`) ve özet `ArbitrageSummary` (`Strategy/StrategySummary.h`; marj farkları paket ortalaması).

## UI

**Yeni GUI** (route `arbitrage`, [yeni-gui](../10-servisler/mtrader-trade-ui/yeni-gui.md)):
- Paneller: `arbitrage_tracker_form` (`ArbitrageTrackerForm.tsx` + `components/dockview/arbitrage/`), `arbitrage_summary_view`, `arbitrage_passive_orders` (`arbitrage/PassiveOrders.tsx`; tracker açık değilse boş).
- Ayar: `ArbitrageSettingsModal` + `modals/arbitrageSettings/` (`sections.tsx`, `fields.ts`); payload `arbitrageSettingsPayload.ts` `buildArbitrageSettingsPayload` (`Command_Type` 51). Bölümler: Genel (açığa satış, işlem tipi, kanal, satış tipi), Saat, Faiz, Spread / Çift Vade, Limitler, Stop Loss, Adaptive spread, opsiyonel dayanak ve finansman maliyeti.
- Toplu ayar: `arbitrageBulkFields.ts`; toplu modda tick kutusu `Fs_Open_Tick`, `Open_Tick`, `If_Open_Tick`'i birlikte yazar.
- Paket: `ArbitragePackageFormModal` (güncelle), `AddPositionModal` (`addPositionCommand.ts`), pasif dayanak emri artır/çalıştır/azalt (`executeUnderlyingCommand.ts`). Excel indir/yükle `features/arbitrage/api/arbitrageExcelApi.ts`.
- Ekleme: `AddArbitrageStrategyModal`; abonelik `/v1/subscribeToSingleArbitrage` ([backend-sozlesmesi](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md)). Abonelik ucu tipi 1/2/4/5 numaralarıyla, komut ucu ASCII kodlarıyla bekler.

**Eski GUI** (`origin/main`, [eski-gui § 3.8](../10-servisler/mtrader-trade-ui/eski-gui.md)): `src/pages/Arbitrage/`; ayar `ArbitrageStrategySettingsPage` + `StrategySettingsBox.tsx` (`Command_Type` 51), paket `AddPackageModal` / `PackageSettingsModal`.

## Sepet arbitraj (`BasketArbitrageTracker`) — kullanılmıyor

- BIST30 endeks vadelisi ile endeks bileşen sepeti arasında cash-and-carry. Endeks `XU30_INSTRUMENT_ID` (3) fiktif enstrümanından okunur; vadelinin dayanağı `Index` olmalıdır (`StrategyFactory`).
- Wire tipi yine `Arbitrage` (6); `MyOrderType::ArbitrageTracker`. İç komut `'E'`. `checkParams` bu komut için hiçbir alan doğrulamaz.
- Parametreler `BasketArbitrageTrackerCommand` (`Deposit`, faiz, temettü verimi, satılacak enstrümanlar, minimum kapama kâr oranları); varsayılanlar `BasketParameters.h` (`interestRate 17,95 %`, endeks puan değeri 10).
- **Kullanılmıyor** (kullanıcı beyanı, 2026-10-22); yeni GUI'de route'u yok. Kod: `algoSrc/Strategy/BasketArbitrage/`.

## Şüpheli

- **master'da teorik faiz `/100` yok (prod etkisi, doğrula):** master `calculateTheoreticalPrice` oranı ham kullanıyor. Yüzde girilmişse `diffTick` dev'e göre çok farklı çıkar; I/R'de yön ve `diffTick ≤ 0`/`> 0` açma koşulu, bütün tiplerde `isProfitableOpen` ve `Theo_Price` etkilenir. development düzeltmesi prod'a gitmemiş.
- **Yeni GUI "Automatic" yönü (bug?):** Spread (`F`) satırında `Fs_Arbitrage_Side = 79` (`O`) seçilince UI tick'leri `Open_Tick`/`Close_Tick`'e yazar, tipi yine `F` gönderir. Motor `F`'de yalnız `Fs_*` okur ve `O`'yu `A`/`B` olarak tanımaz: `checkOpenable` yönü `O` yapar, `openPosition` bunu Above (türev satış) gibi işler, eşik `Fs_Open_Tick` (çoğunlukla 0) ile `fsDiffTick ≥` kontrolüne düşer. Eski GUI'de de aynı seçenek var. Niyet büyük olasılıkla `D` (teorik fiyatlı) tipiydi.
- **F/T eşik işaretleri (doğrula):** F Below aktif açma `drvAsk − undBid ≤ Fs_Open_Tick` (UI 0 ve üstünü kabul eder; yani prim varken de açar), pasif Below istenen fiyat ise `undBid − Fs_Open_Tick` tick (ters işaret). T aktif açma `|ifDiffTick| ≥ If_Open_Tick`; Below sabitken türev çok pahalıyken de türev alır.
- **Saat karşılaştırması asimetrik (bug?):** `isOpenSession` `Start_Time`'dan 3 sa düşüyor, `Stop_Time`'dan düşmüyor; ikisi de `localtime` ile hesaplanan `getSecondsFromMidnight` ile karşılaştırılıyor. Container UTC ise `Stop_Time = 18:00` 21:00 TR'ye denk gelir (pratikte seans sonu kontrolü durdurur); container İstanbul saatindeyse `Start_Time` 3 sa erken açılır. ❓ doğrulanmadı: AlgoProd container saat dilimi.
- **Seans dışı = stop (kasıtlı?):** `Start_Time`'dan sonra iki enstrümandan biri sürekli işlemde değilse strateji durur, ara seanstan sonra kendiliğinden dönmez.
- **Dayanak emri "piyasa" değil:** `Stop_Loss_Type = A` → `TimeInForce::Market` → OUCH'a DAY. Karşı fiyattan limit; kitap kayarsa dolmayabilir.
- **Aktif stop-loss tipinde replace döngüsü (doğrula):** `Stop_Loss_Type = A` iken `checkPassiveUndOrders`'ta bekleme koşulu yok; dayanak emri her kabulden sonra (fiyat aynı olsa da) yeniden replace ediliyor gibi görünüyor.
- **`checkPassiveUndOrders` geçersiz iterator (bug):** `order_id_orders`'ta emir bulunamazsa `stop()` çağrılıyor ama döngü `order_it->second`'ı yine okuyor (tanımsız davranış).
- **Dayanak reddi dinlenmiyor:** spot bacağı reddedilirse `UndOrderDetail` asılı kalır; paket yarım (`undExcQty = 0`) kalır. development'ta bir sonraki başlatma `arePackagesConsistent` ile engellenir; master'da engellenmez.
- **Stop'ta dayanak emirleri iptal edilmiyor (kasıtlı?):** `exitProperly` yalnız türev emirlerini iptal ediyor.
- **Tavan/taban fiyatı bir kez okunuyor:** strateji nesnesi oluşturulurken. `getMaxPrice()` 0 ise `undBestBuy ≥ 0` her turda doğru olur ve strateji ilk turda durur ❓ doğrulanmadı.
- **`Dividend_Prc` birimi tutarsız:** D formüllerinde TL, I/R formüllerinde `/100`.
- **`Total_Profit` birimi:** kâr kontrat başına 0,01 TL × kontrat; `underlyingMultiplier` ile çarpılmıyor ve `closeProfitTick` `int`'e kırpılıyor (`auto closeProfitTick{0}`).
- **Paket indeksi kırılgan:** açılış paketlerinde `dod.packageId = packageList.size() + 1`, `positionOpened` `packageList[packageId − 2]` okuyor; kapamada `packageId` doğrudan indeks. Arada paket silinirse (çalışırken silmeye izin var) indeksler kayar.
- **Paket güncelleme çalışırken sessiz:** `updatePackage` strateji çalışırken hiçbir şey yapmıyor ama gRPC OK dönüyor; UI başarılı sanır.
- **Tek yön kontrolü yalnız `packageList[0]`'a bakıyor:** ilk paket kapanmış (pasif) ise ters yönde açma mümkün.
- **Pasif açılış dolumunda `closing_position = true`:** dayanak bacağı bitene kadar kapamayı bloklamak için olduğu varsayılıyor (kasıtlı?).
