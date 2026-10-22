---
kapsam: Arbitraj (StrategyType 6, AlgoProd) — spot/vadeli ve iki vadeli arasında fark arbitrajı; strateji tipleri, açma/kapama, paketler, wire alanları; sepet arbitraj
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
dogrulama: 2026-10-22
durum: taslak
---

# Arbitraj (`Arbitrage`, 6) — AlgoProd

Bir **türev** (VİOP vadeli kontratı) ile **dayanağı** (spot hisse) veya iki türev arasındaki fiyat farkı eşiği aşınca pozisyon açar, fark kapanınca kapatır.
- Önce türev emri gider. Türev dolunca karşılığı (kontrat × çarpan) spot/diğer türev emri gönderilir.
- Açılan her pozisyon bir **paket** (`ArbitragePackage`) olarak DB'de tutulur.

Kod: `algoSrc/Strategy/Arbitrage/ArbitrageTracker.{h,cpp}`, `algoSrc/Commands/ArbitrageTrackerCommand.*`, `algoSrc/Data/ArbitrageData.h`, alan adları `algoSrc/Utilities/GuiConstants.h` (`ARB_*`).

- **Emir yolu:** AlgoProd → ouch-sdk → order-service → BIST. 🚧 MAOrderSDK + handoff geçişi `add-order-sdk` branch'inde.
- **Kalıcılık:** Paketler ve strateji durumu trade-data-app `AlgoService` (`SetArbitrageData`, `GetArbitrageData`, `UpdateArbitragePackage`, `DeleteArbitragePackage`) üzerinden MySQL'e yazılır.

## Strateji tipleri (`Arb_Strategy_Type`, char)

| Kod | Tip | Fark ölçüsü | Açma / kapama eşiği |
|-----|-----|-------------|---------------------|
| `D` | DiffTick | türev − **teorik fiyat** (tick). Teorik = spot × (1 + vadeye kalan yıl × `Current_Interest_Rate`/100) | `\|diffTick\| ≥ Open_Tick` / kâr ≥ `Close_Tick` × 10 |
| `F` | FutureSpotDiffTick | türev − spot (tick) | `Fs_Open_Tick` / `Fs_Close_Tick`; yön `Fs_Arbitrage_Side` |
| `T` | TwoFutures | iki türev farkı (tick) | `If_Open_Tick` / `If_Close_Tick`; yön `Fs_Arbitrage_Side` |
| `I` | InterestRate | piyasa fiyatlarından türetilen faiz | `Open_By_Buy/Sell_Rate` (+ `Funding_Cost`) / `Close_By_Buy/Sell_Rate` |
| `R` | TwoFuturesInterest | iki türev arasındaki zımni faiz | aynı faiz alanları; süre = iki vade farkı |

İki tarafa birden pozisyon açılmaz. İlk aktif paketin yönü korunur.

**Yön** (`ArbitrageSide`):
- `B` **Below**: türev ucuz → türev al, spot sat. Spot satışı `Sell_Type` = `T` (Short) ise açığa satış olarak gider.
- `A` **Above**: türev pahalı → türev sat, spot al.

D tipinde yön fark işaretinden seçilir, F ve T tiplerinde `Fs_Arbitrage_Side` sabitler.

## Döngü (`doPeriodicChecks`)

AlgoProd'un worker havuzunda (`runsOnWorkerPool`) periyodik çalışır.

1. **Seans kontrolü** (`isOpenSession`):
   - `Start_Time` gelmediyse (iki vadelide 30 dk erken) beklenir.
   - İki enstrümandan biri sürekli işlemde değilse veya `Stop_Time` geçtiyse strateji **durur**.
   - Saat alanları İstanbul günün saniyesidir; kod 3 saati düşüp UTC ile karşılaştırır.
2. **Tavan/taban koruması:** Dayanak tavan veya tabana değerse (iki vadeli tipler hariç) strateji durur.
3. **Güvenlik:** `drvPos < 0` ise strateji durur.
   - **PTRM:** Türev emri `-850002`, `-850004`, `-850044` veya `-420131` (`RX_OUTSIDE_ALLOWED_LIMIT`) ile reddedilirse strateji durur. Eşleme kod veya ret metni üzerinden yapılır. `-850064` AlgoProd'da tanımlı değildir (bkz. [vwap.md](vwap.md#ptrm)).
4. Header'lar okunur, pasif emirler kontrol edilir (`checkPassiveUndOrders`, `checkPassiveDrvOrders`).
5. **`runStrategy`:**
   1. Türev dolumu var mı? Varsa spot emrini gönder (`checkDrvExecution` → `sendUnderlyingOrder`).
   2. Spot dolumu var mı? Varsa paketi açık veya kapalı işaretle (`checkUndExecution` → `positionOpened` / `positionClosed`).
   3. **Kapama:** En kârlı aktif paket bulunur (`getMostProfitablePackage`). Kârlıysa (pasif modda her zaman) `closePosition`. `Closing_Limit_Check` açıksa toplam kapanan `Contract_Limit_Closing`'i aşamaz.
   4. **Açma:** `checkOpenable` (eşik + kontrat limiti + spot satış izni + tek yön) geçerse `openPosition` veya `openPassivePosition`.

## Aktif ve pasif türev (`Derivative_Type`)

- **`Q` Aktif:** Türev emri karşı tarafın en iyi fiyatından **FaK** gider. Açma için kârlılık ve eşik kontrolü şarttır.
- **`Z` Pasif:** Türev için "istenen fiyat" hesaplanır (`calculateWantedPriceOpen` / `calculateWantedPriceClose`) ve **DAY** limit emir tahtaya yazılır. Piyasa değiştikçe emir replace edilir.
  - **`Adaptive_Spread_Enabled`:** Hesaplanan fiyat makas içindeyse emir en iyi fiyattan `Adaptive_Spread_Level` adım içeride konumlanır.
  - **`Closing_By_Spot`:** Kapama fiyatı paketin açılış fiyatlarına göre değil, güncel spot ± kapama tick'ine göre hesaplanır.

## Spot (dayanak) emri

- Miktar = dolan kontrat × `Underlying_Multiplier` (varsayılan 100).
- Fiyat: Below açılışta spot alış header'ı, Above açılışta spot satış header'ı.
- `Stop_Loss_Type`:
  - `A` Aktif: spot emri **piyasa** emri olarak gider.
  - `P` Pasif: DAY limit emir gider.
- Pasif spot emirleri `Passive_Barrier` ile izlenir: en üstte kalmazsa veya bariyer bozulursa replace edilir.

## Limitler

- **`Contract_Limit`:** toplam açık kontrat sınırı (`drvPos`).
- **`Package_Limit`:** tek seferde açılacak paket büyüklüğü (0 = sınırsız).
- **`Contract_Limit_Closing` / `Package_Limit_Closing`:** kapama tarafı için aynı sınırlar.
- **Strateji başlamadan paket tutarlılığı kontrol edilir** (`arePackagesConsistent`):
  - Her paketin spot dolumu = kontrat × çarpan olmalı.
  - Paketlerin kontrat toplamı = `drvPos` olmalı.
  - Yarım açılmış paket varsa strateji başlamaz; kullanıcı paketleri düzeltmelidir.

## Fiyat birimleri

AlgoProd'da fiyat birimleri karışıktır. Değiştirmeden önce koda bak.
- Spot fiyatları raw (×1000).
- Türev hesapları 0,01 TL adımlarıyla yapılır (`drvDecimalMultiplier`, `undDecimalMultiplier`).
- `Theo_Price` GUI'ye **TL × 1000** olarak gider (`theoPrc = lastThPrc * 1000`). Enstrüman ölçeğine bölünmemelidir (mtrader-trade-ui `AGENTS.md`).
- `Dividend_Prc`, faiz oranları: double, yüzde.

## Wire alanları (`ARB_*`)

| Alan | Tip | Anlam |
|------|-----|-------|
| `Underlying_Instrument_Id` | Long | Dayanak (veya iki vadelide diğer türev) |
| `Arb_Strategy_Type` | Int (char) | `D`/`F`/`T`/`I`/`R` |
| `Derivative_Type` | Int (char) | `Q` aktif, `Z` pasif |
| `Fs_Arbitrage_Side` | Int (char) | `A` / `B` (F ve T tipleri) |
| `Sell_Type` | Int (char) | `S` normal, `T` açığa |
| `Is_Spot_Sell_Allowed` | Int (char) | `F` serbest, `P` yasak (yasaksa Below açılmaz) |
| `Open_Tick` / `Close_Tick` | Long | D tipi eşikleri (tick) |
| `Fs_Open_Tick` / `Fs_Close_Tick` | Long | F tipi |
| `If_Open_Tick` / `If_Close_Tick` | Long | T tipi |
| `Open_By_Buy_Rate`, `Open_By_Sell_Rate`, `Close_By_Buy_Rate`, `Close_By_Sell_Rate` | Double | Faiz tipleri (%) |
| `Funding_Cost` | Long | Faiz eşiklerine eklenir |
| `Current_Interest_Rate` | Double | Teorik fiyat için faiz (%) |
| `Dividend_Prc` | Double | Temettü düzeltmesi |
| `Contract_Limit`, `Package_Limit`, `Contract_Limit_Closing`, `Package_Limit_Closing` | Long | Limitler |
| `Closing_Limit_Check`, `Closing_By_Spot` | Bool | |
| `Underlying_Multiplier` | Long | Kontrat başına spot adedi |
| `Stop_Manual_Mode`, `Stop_Loss_Type` (`A`/`P`), `Stop_Loss_Second`, `Stop_Loss_Level` | | Stop parametreleri |
| `Passive_Barrier` | Long | |
| `Adaptive_Spread_Enabled`, `Adaptive_Spread_Level` | Bool / Long | |
| `First_Future`, `Second_Future`, `Third_Future`, `Optional_Underlying` | Bool | ❓ Kontrat seçimi; kullanım ayrıntısı doğrulanmadı |
| `Start_Time`, `Stop_Time` | Long | Günün saniyesi |
| `Channel_Enum` | Int | OUCH / FIX |

GUI'ye giden mesajlar: `ArbitrageStrategyActivity`, `ArbitragePackageActivity` (paket listesi `Arb_Package_List`, paket alanları `Arb_*`), özet (`ArbitrageSummary`, `Strategy/StrategySummary.h`).

## UI

- Yeni GUI route `arbitrage`. Paket yönetimi (güncelle, sil), toplu ayar, Excel ile ayar yükleme.
- Paket ve pozisyon ekleme komutları: `PackageCommand`, `SetBalanceCommand`, `PassiveUnderlyingCommand` (dayanağı elle gerçekleştirme).
- Eski masaüstü arayüzü (Algo-GUI) emeklidir.

## Sepet arbitraj (`BasketArbitrageTracker`)

- **Ne yapar:** BIST30 endeks vadelisini endeks bileşenlerinden oluşan bir sepete karşı arbitrajlar. Ağırlıklar endeks tanımından gelir (`XU30_INSTRUMENT_ID`). Wire tipi yine `Arbitrage` (6), iç komut `'E'`.
- **Parametreler:** `Deposit`, faiz, temettü verimi, satılacak enstrümanlar, minimum kapama kâr oranları.
- **Henüz kullanılmıyor** (kullanıcı beyanı, 2026-10-22). Yeni GUI'de route'u yok.
