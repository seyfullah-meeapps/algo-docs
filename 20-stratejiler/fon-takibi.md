---
kapsam: Fon Takibi (FundTracker, StrategyType 10, AlgoProd) — BYF ile PCF sepeti arasında kotasyon/arbitraj; PCF eşleme, lot hesabı, teorik fiyat ve ölçek, kotasyon/replace, sepet emirleri, paketler, durma koşulları, wire alanları, UI, master farkı
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading          # prod binary'si master'dan derlenir
    branch: master
    commit: aa150ee
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui            # eski GUI
    branch: main
    commit: 6715182
dogrulama: 2026-10-22
durum: taslak
---

# Fon Takibi (`FundTracker`, 10) — AlgoProd

**Fikir:** Bir **BYF** (borsa yatırım fonu) için fonun sepetindeki (PCF) hisselerden **teorik fiyat** hesaplar ve fon tahtasına teorik fiyat ± spread'den alış ve satış kotasyonu verir.
- Kotasyondan bir sepet karşılığı kadar fon **alınınca** sepetteki hisseler **satılır**; fon **satılınca** hisseler **alınır**.
- Her sepet işlemi bir **paket** (`BYFPackage`) olarak DB'ye yazılır.

Kod: `algoSrc/Strategy/FundTracker/FundTracker.{h,cpp}`, `algoSrc/Commands/FundTrackerCommand.*`, PCF modeli `algoSrc/Data/BYFData.h`, fon durumu `BYFState` (`FundTracker.h`), DB `Data/DatabaseServiceClient.cpp` (`getBYFData`, `setBYFPackageData`). İç komut `'d'`. Parametre doğrulama `Managers/StrategyServiceImpl.cpp` `checkParams`.

Emir gönderimi: [emir-yolu](../10-servisler/algorithmic-trading/emir-yolu.md). Thread modeli: [uygulama-ve-threadler](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md). gRPC ve `AlgoService`: [grpc-ve-veri](../10-servisler/algorithmic-trading/grpc-ve-veri.md).

## Veri: PCF (fon sepeti)

- trade-data-app açılışta BYF dosyasını indirir ve sepeti bellekte tutar ([trade-data-app/entegrasyonlar](../10-servisler/trade-data-app/entegrasyonlar.md)). AlgoProd sepeti `AlgoService.GetByfSettings` ile okur (`DatabaseServiceClient::getBYFData()`, `readPcfFile`). Tek bir PCF okunur; strateji başına fon seçimi yoktur ❓ doğrulanmadı: birden fazla BYF'nin aynı anda takibi.
- **Eşleme:** her PCF satırının `symbol`'ü, `OrderbookManager`'ın tradable enstrümanları arasında adı bu sembolle **başlayan ilk** enstrümana eşlenir (önek eşlemesi, harita sırası).
- Eşlenemeyen sembol için `stop()` çağrılır. Ama bu yapıcıda olur; strateji henüz çalışmadığından `Manager::stop` hiçbir şey yapmaz. Sonuç: strateji eksik sepetle oluşur ve başlatılabilir (Şüpheli).
- Strateji nesnesi oluşturulurken PCF bir kez okunur; lot ve fon karşılığı yeniden hesaplanmaz.

## Lot hesabı (`readPcfFile`)

PCF alanları: `weight`, `closePrice` (double, TL varsayılıyor), `netActiveValue`.

1. `maxPricePerWeight = max(closePrice / weight)` (eşlenen hisseler arasında).
2. Her hisse: `calculatedLotCount = round(maxPricePerWeight × weight / closePrice)`. En pahalı/ağırlık oranlı hisse 1 lot olur; diğerleri ağırlıkla orantılı.
3. `totalPackagePrice = Σ calculatedLotCount × closePrice` (int'e kırpılır), TL.
4. **Sepet karşılığı fon lotu** `calculatedRequiredLotCount`:
   - Fonun alış header'ı > 0 ise `round(totalPackagePrice / (BYFBestBuy / 1000))` (BYF fiyatı raw ×1000 varsayımı).
   - Değilse `round(totalPackagePrice / netActiveValue)`.

Bu değer BIST'in "minimum işlem birimi" parametresi değildir; sepetin TL değerinin fon fiyatına bölümüdür. Kodda adı `minTransactionUnitReached` olsa da eşik bu değerdir.

## Döngü (`doPeriodicChecks`, ~5 ms)

Kendi thread'inde (`BaseStrategy::workAsyncron`), her tur sonunda 5 ms uyku.

1. `strategyChecks`: fon **veya** sepetteki herhangi bir hisse sürekli işlemde değilse → `stop()`. Seans beklenmez; sürekli işlemden önce başlatılan strateji ilk turda durur.
2. `byfState.fundId == -1` → `stop()`.
3. Bu iki `stop()`'tan sonra `return` yok; tur sonuna kadar devam eder (Şüpheli).
4. `checkBYFExecution`: fon emirlerinin olayları (aşağıda).
5. `calculatePrices`: teorik fiyat.
6. Sepet emirleri gönderiliyorsa `checkUnderlyingOrdersSide(Buy/Sell)`.
7. Kotasyon varsa `checkPassiveMassQuoteOrder` (replace).
8. En az bir tarafta kotasyon güncellenmiyor ve sepet gönderilmiyorsa `sendMassQuoteOrder`.

`Byf_Start_Time` / `Byf_Stop_Time` **hiçbir kararda kullanılmaz**; yalnız parse edilir, loglanır ve snapshot'ta geri yollanır.

## Fiyat hesapları ve ölçek

- Hisse header'ları raw (×1000, `bestBuy`/`bestSell`, `BYFInstrument::updateBestPrices`).
- `calculatedPriceBuy = Σ bestBuy × lot / 10`, `calculatedPriceSell = Σ bestSell × lot / 10` → **kuruş (TL × 100)**.
- `theoreticalPriceBuy = calculatedPriceBuy / calculatedRequiredLotCount`, `theoreticalPriceSell` benzer; **kuruş, fon lotu başına**.
- **Kotasyon fiyatı:**
  - Alış: `theoreticalPriceBuy − Byf_Spread_Buy` (kuruş), adım katına **aşağı** yuvarlanır.
  - Satış: `theoreticalPriceSell + Byf_Spread_Sell` (kuruş), adım katına **aşağı** yuvarlanır.
  - Adım `instrumentPtr->getPriceStep(kuruş fiyat)` ile alınır; emre `× 10` (raw ×1000) yazılır. Bu dönüşüm fonun 3 ondalıklı (×1000) olduğunu varsayar ❓ doğrulanmadı: BYF ITCH ondalığı ve `getPriceStep`'in birimi.
- Yani fon alışı sepetin **alış** (bid) değerinden, fon satışı sepetin **satış** (ask) değerinden fiyatlanır; hedge sırasında da hisseler sırasıyla bid'e satılır, ask'tan alınır.

GUI'ye: teorik fiyat `FundTrackerUnderlyingPriceActivity` → `Byf_Underlying_Price` = `theoreticalPriceBuy` (**TL × 100**); paket `Byf_Package_Total_Price` TL × 100; paket içi hisse `Byf_Order_Mean_Price` **TL × 1000**. UI bölenleri: `FUND_TRACKER_PRICE_DIVIDER = 100`, `BYF_UNDERLYING_ORDER_DIVIDER = 1000` (`features/fund-tracker/fundTrackerContract.ts`).

## Kotasyon (`sendMassQuoteOrder`, `checkPassiveMassQuoteOrder`)

Adı "mass quote" olsa da iki ayrı **DAY limit** emirdir; kanal sabit **OUCH** (`PROTOCOL_OUCH`), `Channel_Enum` okunmaz.

**Yeni kotasyon** (taraf başına), koşulların hepsi:
- O tarafta güncelleme bekleyen emir yok (`updating_*_side`), sepet emri gönderilmiyor (`sending_underlying_order_*`), kotasyon miktarı 0 (`BidSize`/`OfferSize`).
- Miktar > 0. development: `min(Byf_Lot_Count_*, calculatedRequiredLotCount − toplam_alınan/satılan)`. ⚠ master'da farklı (2026-10-22): `min(Byf_Lot_Count_*, Byf_Lot_Count_* − toplam_alınan/satılan)` (development commit 41adb60 "fixed byf lot calculation"). Etki aşağıda.
- `byfState.buyPackagesCount < Byf_Package_Limit_Buy` (satışta `sellPackagesCount < Byf_Package_Limit_Sell`). Paket sayıları DB'den okunan paketlerden sayılır (`getBYFData`), yani limit kalıcı paket sayısına uygulanır ❓ doğrulanmadı: DB'nin yalnız günün paketlerini dönüp dönmediği. Limit 0 → hiç kotasyon yok (iki GUI'nin varsayılanı 0).

**Replace:** kotasyon fiyatı istenen fiyattan farklıysa (her ~5 ms turda kontrol) `ReplaceOrder` ile fiyat değiştirilir, miktar korunur. Kabul (add) gelene kadar o taraf `updating_*_side`'dır.

**Olaylar (`checkBYFExecution`):**
- **Ret** (her kod) → `stop()`.
- İptal → `BidSize`/`OfferSize` azaltılır.
- Add (yeni emir veya replace kabulü) → fiyat/miktar/token güncellenir, `updating_*_side = false`.
- **Dolum** → `totalFundBought` / `totalFundSold` artar; `≥ calculatedRequiredLotCount` olunca `minTransactionUnitReached`.

**master etkisi:** iki GUI `Byf_Lot_Count_*`'ı 1 gönderir (kutu etkisiz, aşağıda). master'da ilk 1 lot dolunca miktar `1 − 1 = 0` olur ve o tarafta kotasyon biter. `calculatedRequiredLotCount > 1` ise eşik hiç aşılmaz: **sepet hedge'i gönderilmez, fon pozisyonu açık kalır** ve taraf kilitlenir. development'ta kotasyon eşik dolana kadar 1'er lot devam eder.

## Sepet emirleri ve paket

`minTransactionUnitReached(side)`:
- Fon alındıysa: `fundPos++`, `buyPackagesCount++`, hisseler **satılır**. Fon satıldıysa: `fundPos--`, `sellPackagesCount++`, hisseler **alınır**.

`sendUnderlyingOrders`:
- Paket: `packageId = paket sayısı + 1`, `side` = fon tarafı, `fundQty = initFundQty = toplam alınan/satılan` (eşiği aşan kısım dahil), sonra sayaç sıfırlanır, yeni token.
- Her hisse için `calculatedLotCount` lot, karşı en iyi fiyattan (alışta ask, satışta bid) **DAY limit**, OUCH. `totalPrice += (fiyat / 10) × lot` (kuruş).

`checkUnderlyingOrdersSide` (her tur):
- Her hisse emri için add/execute/cancel/reject olayları işlenir. Dolum `≥ gönderilen` → emir `isCompleted`. Ret → `isRejected`.
- Kabul edilmiş, bitmemiş emrin fiyatı güncel karşı en iyi fiyattan farklıysa o fiyata **replace** (kovalama).
- Bütün emirler `isCompleted` **veya** `isRejected` olunca paket `isCompleted`; GUI'ye paket aktivitesi gider, paket `byfState.packages`'a eklenir ve `setBYFPackageData` ile DB'ye yazılır. DB sonucu `fundId == -1` ise `stop()`.
- Sepet gönderilirken o tarafta yeni kotasyon verilmez.

## Risk ve durma koşulları

| Koşul | Davranış |
|-------|----------|
| Fon emri reddi (her kod; PTRM ayrımı yok) | `stop()` |
| Fon veya sepetten bir hisse sürekli işlemde değil | `stop()` |
| DB'den fon kaydı alınamadı / paket yazımı başarısız (`fundId == -1`) | `stop()` |
| `OuchManager::send` istisnası | `stop()` |
| Sepet hissesi emri reddi | Strateji durmaz; emir `isRejected` sayılır, paket yine tamamlanır |
| PCF sembolü eşlenemedi | Yapıcıda `stop()` (etkisiz, yukarıda) |

`stop()` → `exitProperly`: **yalnız fon** emirleri (iki taraf) iptal edilir. Bekleyen sepet hissesi emirleri iptal edilmez.

## Parametreler (wire, `GuiConstants.h` `BYF_*`)

`checkParams` zorunlu tutar: `Byf_Start_Time`, `Byf_Stop_Time`, `Byf_Spread_Buy`, `Byf_Spread_Sell`, `Byf_Lot_Count_Buy`, `Byf_Lot_Count_Sell`, `Strategy_Unique_Key`.

| Alan | Tip | Birim | GUI varsayılanı | Anlam |
|------|-----|-------|-----------------|-------|
| `Byf_Spread_Buy` / `Byf_Spread_Sell` | Long | kuruş (TL × 100) | 1 / 1 | Teorik fiyattan uzaklık |
| `Byf_Lot_Count_Buy` / `Byf_Lot_Count_Sell` | Long | fon lotu | 1 / 1 | Tek kotasyonun azami miktarı (UI'da kutusu etkisiz) |
| `Byf_Package_Limit_Buy` / `Byf_Package_Limit_Sell` | Long | paket | 0 / 0 | Taraf başına paket sınırı; 0 = kotasyon yok |
| `Byf_Package_Limit` | Long | — | gönderilmez | **Kullanılmıyor.** Parse edilir, loglanır |
| `Byf_Start_Time` / `Byf_Stop_Time` | Long | günün saniyesi | 36000 / 64800 | **Kullanılmıyor** (yalnız log ve snapshot) |

**UI notu:** Yeni GUI'deki fon ayar modalındaki "Alış/Satış Miktar" kutuları **bilerek etkisizdir**. Değer gönderilmez, `Byf_Lot_Count_*` snapshot'tan aynen geri yollanır (eski GUI'de bu kutular HFT'nin `Trigger_Qty_*` alanlarına bağlıydı). Bunu bug diye "düzeltmeyin" (mtrader-trade-ui `AGENTS.md` → "FUND_TRACKER dead lot boxes"). master'daki lot hesabıyla birleşince etkisi büyür (yukarıda).

GUI'ye giden mesajlar:
- `FundTrackerUnderlyingPriceActivity`: `Byf_Fund_Id`, `Byf_Underlying_Price` (teorik alış, TL × 100), `Byf_Total_Fund_Bought_Qty`, `Byf_Total_Fund_Sold_Qty`. Teorik fiyat değiştikçe ve her fon dolumunda.
- Paket aktivitesi (`BYFPackageActivity`, mesaj tipi dizesi `FundTrackerStrategyActivity`): `Byf_Package_Id`, `Byf_Package_Token`, `Byf_Package_Timestamp`, `Byf_Package_Total_Price`, `Byf_Package_Is_Completed`, `Byf_Package_Order_Side`, `Byf_Package_Instrument_Name`, `Byf_Package_Fund_Position`, `Byf_Package_Executed_Fund_Qty`, `Byf_Package_Underlying_Orders` (hisse başına `Byf_Order_*`: ad, gönderilen, dolan, ortalama fiyat ×1000, ağırlık, tamamlandı).
- `FundTrackerUnderlyingPriceActivity` gRPC'de `Command_Type_BYFTheoreticalPriceResponse` mesaj tipiyle gider (`StrategyActivities.h`).

## UI

**Yeni GUI** (route `fund-tracker`, [yeni-gui](../10-servisler/mtrader-trade-ui/yeni-gui.md)):
- Tracker paneli yok; strateji `order_book` üzerinden yönetilir (`orderbook/FundTrackerControlsOverlay.tsx`, `FundTrackerOrderBookControls.tsx`). Ayar `modals/FundTrackerSettingsModal.tsx`, ekleme `AddFundTrackerStrategyModal` ("+" doğrudan bu modalı açar).
- Wire: `features/fund-tracker/fundTrackerContract.ts` `buildFundTrackerSettingsPayload` (`Command_Type` 100). `unique_key = <orderbookId>_<hesap>_<stratejiId>_10` (yan taşımaz; tek `Strategy_Start` iki tarafı birlikte başlatır/durdurur). Abonelik commandType'ları 1, 3.
- Paketler `fund_tracker_summary_view` panelinde (`FundTrackerSummaryView.tsx` + `dockview/fund-tracker/fundTrackerPackage.ts`, "Paketler"; Sidebar'dan açılır). Teorik fiyat `byfTheoreticalPriceStore`.

**Eski GUI** (`origin/main`, [eski-gui § 3.9](../10-servisler/mtrader-trade-ui/eski-gui.md)): OrderBook paneli, `OrderBookSettings` (`Command_Type` 100), teorik fiyat `theoPrice / 100` (`StartStopButton.tsx`), paketler `FundTrackerSummaryView` + `FundTrackerPackagesContext`.

## Şüpheli

- **master'da kotasyon miktarı hatası (prod etkisi, doğrula):** `min(L, L − alınan)` ile `Byf_Lot_Count = 1` iken ilk dolumdan sonra kotasyon biter, sepet eşiği aşılmaz, hedge gönderilmez; fon pozisyonu hedge'siz kalır. Düzeltme (41adb60) yalnız development'ta.
- **Eşlenemeyen PCF sembolü stratejiyi durdurmuyor (bug):** `stop()` yapıcıda çağrıldığı için etkisiz; strateji eksik sepetle teorik fiyat hesaplar ve hedge'i eksik hisseyle yapar.
- **Önek eşlemesi:** sembolle başlayan **ilk** tradable enstrüman seçiliyor; aynı önekli başka bir enstrüman (ör. farklı pazar/varyant) önce gelirse yanlış hisse eşlenir ❓ doğrulanmadı.
- **Sepet hissesi reddi paketi "tamamlandı" sayıyor:** `isRejected` emir `allCompleted`'ı engellemiyor; hedge eksik olduğu halde paket `isCompleted` olur ve strateji devam eder.
- **`stop()` sonrası tur devam ediyor:** `strategyChecks` veya `fundId` kontrolünde `stop()` sonrası `return` yok; aynı turda `sendMassQuoteOrder` yeni kotasyon gönderebilir (iptal `exitProperly`'de zaten yapılmış olur).
- **Stop'ta sepet emirleri iptal edilmiyor:** `exitProperly` yalnız fon emirlerini iptal ediyor.
- **Satış kotasyonu aşağı yuvarlanıyor:** `wantedSellPrice` da adım katına aşağı yuvarlanıyor; spread'in bir kısmı kaybolur (alışta aşağı yuvarlama doğru yöndür).
- **Eşiği aşan dolum:** paket `fundQty` eşiği aşan miktarı da içeriyor, sepet ise tam bir sepet karşılığı gönderiliyor; fazla fon lotu hedge'siz kalır.
- **`calculatedRequiredLotCount` bir kez hesaplanıyor:** strateji nesnesi oluşturulurken (çoğunlukla açılışta, seans öncesi) fon header'ı 0 ise `netActiveValue`'ya düşülür; gün içi fiyat değişse de yenilenmez.
- **`Byf_Start_Time` / `Byf_Stop_Time` etkisiz:** UI saat girdisi alıyor ama motor kullanmıyor; strateji yalnız seans durumuna bakıyor.
- **Seans dışı = stop:** sürekli işlemden önce veya ara seansta başlatılan strateji hemen duruyor (kasıtlı?).
