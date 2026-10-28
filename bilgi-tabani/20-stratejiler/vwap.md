---
kapsam: VWAP (StrategyType 7, AlgoProd; kodda TradeByVolume) — piyasa hacminin 1/Ratio'su kadar katılarak hedef lotu alma/satma; döngü, hesap, modlar, fiyat limiti, stop, PTRM, AKD filtresi, Overall, wire alanları, UI
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading          # prod; Strategy/TradeByVolume ve Commands/TradeByVolume* development ile aynı
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

# VWAP (`VWAP`, 7) — AlgoProd

**Fikir:** Bir enstrümanda tek yönde (alış **veya** satış) toplam `Trade_Limit` lotu, fiyat limiti içinde piyasada gerçekleşen hacmin `1/Ratio`'su kadar katılarak gerçekleştirir (hacme bağlı katılım). Kodda adı **TradeByVolume**. Alış ve satış ayrı stratejilerdir (ayrı `unique_key`).

Kod: `algoSrc/Strategy/TradeByVolume/TradeByVolume.{h,cpp}`, `TradeByVolumeOverall.*`, `algoSrc/Commands/TradeByVolumeCommand.*`, `TradeByVolumeOverallCommand.*`. İç komut `'6'` (TradeByVolume), `'V'` (Overall). Parametre doğrulama `Managers/StrategyServiceImpl.cpp` `checkParams`.

⚠ master farkı: `Strategy/TradeByVolume/` ve `Commands/TradeByVolume*` dosyalarında development ile master arasında fark yok (2026-10-22). Ortak altyapı farkları (worker havuzu, ITCH SDK v3, combiner) için [uygulama-ve-threadler](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md); emir gönderimi [emir-yolu](../10-servisler/algorithmic-trading/emir-yolu.md).

## Döngü

2026-10-23 ikinci tur: kaynak fetch/development pull sonrası development `0dc32a7` / master `aa150ee` aynı. `Strategy/TradeByVolume/` ve incelenen command cpp'de branch farkı yok. Bu, ortak event/order altyapısının da aynı olduğu anlamına gelmez. `parseMessages` accept/reject, hacim/kendi fill muhasebesi ve hedef lot sonu durma yolları kaynakla karşılaştırıldı. PTRM listesine giren ret stop eder; diğer retlerde `isOrderSent=false` ile yeniden deneme yolu kalır (K-197). Bütün AKD/Overall ve stop-loss alt yolları bu turda yeniden test edilmedi; build/canlı test yok.

Kendi thread'inde çalışır (`runsOnWorkerPool() == false`, `BaseStrategy::workAsyncron`).

`doPeriodicChecks`:
1. Enstrüman sürekli işlemde değilse 1 sn uyu, dön. **Strateji durmaz**, seansı bekler.
2. `parseMessages`:
   1. Piyasa işlemleri (`marketTradeSubscriber`, ITCH trade): fiyat `Vwap_Price_Limit`'e eşit veya daha iyiyse **ve** `isAkdChecksHold` ise `totalExecutedQty += lot`.
   2. 20 ms uyu.
   3. Kendi dolumlarımız (`myTradeSubscriber`): `tradedQty += lot`, `totalExecutedQty -= lot` (piyasa hacminden kendi payımız düşülür), `activeSentQty` azaltılır, özet yayınlanır.
   4. İptal ve kabul olayları: kabulde `isOrderSent = false`.
   5. Retler: `isOrderSent = false`; PTRM ise `stop()` (aşağıda).
   6. AKD açıksa `checkAKDSubscribers`.
   7. Vadeli enstrümanda fiyat limiti teorik fiyatla kırpılır (aşağıda).
   8. `runStrategy`.
3. `runStrategy` sonunda 100 ms uyku (yalnız emir yolu çalıştıysa). Bir tur ≈ 120 ms.

## Hesap (`runStrategy`)

| Değişken | Formül | Anlam |
|----------|--------|-------|
| `lastOrderDepthQty` | kendi tarafımızdaki bütün pasif emirlerimizin toplamı | |
| `expectedQty` | `totalExecutedQty / Ratio − tradedQty` | şimdiye kadar olması gereken ek katılım |
| `maximumQty` | `Trade_Limit − tradedQty` | kalan hedef |
| `maximumOrderQty` | `maximumQty − lastOrderDepthQty` | henüz emre dönmemiş kalan |
| `thresholdQuantity` | `min(100, Trade_Limit / 100)`, en fazla `maximumQty` | asgari emir büyüklüğü |

Sıra:
1. Kendi veya karşı header yoksa dön.
2. `maximumQty ≤ 0` → bu taraftaki bütün emirleri iptal et, `strategyFinished = true`, **`stop()`**. (Kod yorumu: "When TradeByVolume added to new gui environment, this logic should be deleted.")
3. `cancelOrdersOutsideLimit`: fiyatı `Vwap_Price_Limit`'ten **daha iyi** (alışta yüksek, satışta düşük) pasifleri iptal et. Limit 0 ise atlanır.
4. `checkStopLoss` (aşağıda).
5. `maximumOrderQty < 0` (pasifte hedeften fazla var) → `updateOrdersExcessQuantity`: en kötü fiyatlıdan başlayarak fazlalık kadar emir küçültülür/iptal edilir. Tur biter.
6. Aksi halde: önceki emrin kabulü bekleniyorsa (`isOrderSent`) dön; AKD tutmuyorsa dön; moda göre `runPassiveMode` / `runNormalMode` / `runAgressiveMode`.

**`sendOrder` kuralları:**
- Miktar ≤ 0 veya `< 0,8 × thresholdQuantity` → gönderilmez. `threshold`'un altındaysa `threshold`'a yuvarlanır.
- Miktar `maximumOrderQty`'yi aşıyorsa gönderilmez.
- Emir her zaman **DAY limit**. `Channel_Enum = FIX` ise protokol FIX; aksi halde komuttaki protokol.
- Gönderimden sonra `isOrderSent = true`; kabul veya ret gelene kadar yeni emir yok. Gönderim 10 sn'de dönmezse veya istisna olursa `stop()` (`sendTransaction`).

## Modlar (`Vwap_Mode`, char)

| Kod | Mod | Davranış |
|-----|-----|----------|
| `P` (80) | Pasif | Kendi tarafının en iyi kademesine yazar; o kademe limitten kötüyse limit fiyatına. Hedef: `expectedQty + (kademedeki diğer emirler) / Ratio`, en fazla `maximumQty`. Kademedeki payımız hedef + threshold/2'yi aşarsa küçültülür (`updateLevelQuantity`), eksikse fark gönderilir; fark `maximumOrderQty`'yi aşarsa önce daha kötü kademelerdeki pasifler iptal edilir (`cancelWorseOrders`). |
| `N` (78) | Normal | Karşı en iyi fiyat limit içindeyse: `expectedQty − activeSentQty` kadar (en fazla `maximumQty`) karşı fiyattan **DAY limit (aktif)** emir. Gerekirse önce daha kötü pasifler iptal edilir. Karşı fiyat limit dışındaysa Pasif mod gibi davranır; kendi kademesi limit dışındaysa limit fiyatındaki (yoksa bir alt/üst) kademeye yazar. |
| `A` (65) | Agresif | Yalnız karşı fiyat limit içindeyse: `expectedQty − lastOrderDepthQty` kadar karşı fiyattan DAY limit. Fazlaysa önce daha kötü pasifler iptal edilir. Limit dışında hiçbir şey yapmaz. |

"Aktif" emir de DAY limit emirdir; karşı kademede dolmayan kısım kitapta pasif kalır.

## Fiyat limiti

`Vwap_Price_Limit` (raw, enstrüman ölçeği):
- Alışta bu fiyatın üstüne, satışta altına emir yazılmaz. Piyasa hacmi de yalnız bu limit içindeki işlemlerden sayılır.
- Limit **0** ise: alışta hiçbir fiyat "eşit veya daha iyi" sayılmaz, emir gitmez ve hacim sayılmaz; satışta her fiyat geçerlidir (taban yok). Yani 0 "kapalı" anlamına gelmez.
- **Vadeli enstrümanda** (`isFuture()`) her tur: `limit = min(limit, teo / 10)`, `teo = underlyingOppositeLevel × (1 + yıl/100 × Base_Interest)` (`TradeByVolume::calculateTheoreticalPrice`, yıl = `getYearsToExpiration`, takvim günü/365). Değer komut nesnesine yazılır (`setPriceLimit`), yani kalıcı olarak değişir. `underlyingOppositeLevel` yalnız Overall tarafından doldurulur; Overall çalışmadığı için (aşağıda) pratikte 0 → limit 0'a iner (Şüpheli).

## Stop (`checkStopLoss`)

`Stop_Loss_Level` > 0 ise her tur:
- Alışta **kendi tarafımızın** en iyi fiyatı ≥ stop, satışta ≤ stop olunca:
  1. Bu taraftaki bütün emirlerimiz iptal edilir.
  2. `maximumQty` (kalanın tamamı) karşı en iyi fiyattan tek **DAY limit** emirle gönderilir. Fiyat limiti ve threshold kontrolü yapılmaz.
  3. `stop()`.
- `stop()` → `exitProperly` 100 ms bekleyip bu taraftaki bütün emirleri yeniden iptal eder; stop emrinin o ana kadar dolmayan kısmı da iptal olur (Şüpheli).

## PTRM

### 24 Ekim kontrolü: AKD/Overall ve stop-loss

2026-10-24 AlgorithmicTrading fetch/pull sonrası development `0dc32a7`, master `aa150ee`; TradeByVolume dizininde fark yok. AKD `subscribeToVWAPData` hâlâ `isThisMainStrategy && false` ile kapalı. Overall `mainStrategy` boş/default, incelenen sınıfta ana/çocuk bağlama ataması yok; periyodik kontrol null durumunda bekler. Bunlar önceki K-206'yı kapatmaz.

`checkStopLoss` kalan hedef miktarla karşı fiyattan DAY limit gönderip `stop()` çağırır. `exitProperly` 100 ms sonra kalan emirleri iptal eder. Çağıran `runStrategy`, checkStopLoss sonrasında return/running kontrolü yapmadan miktar küçültme veya kabul/AKD/mod kontrolüne devam eder. Bu, aynı turda ek kodun çalışabileceğini gösterir; yeni emrin mutlaka gittiği veya iki kez fill olduğu iddia edilmez. Stop anının fiyatı, cancel ACK sırası ve gerçek fill sonucu bu statik incelemede denenmedi.

Alttaki AKD/Overall açıklamaları motor davranışıdır; GUI broker payload'ları bugün yeniden incelenmedi. Kaynaklar: `TradeByVolume.cpp`, `TradeByVolumeOverall.{h,cpp}`. Yeni sorun numarası yerine K-206 kapsamı netleştirildi.

Ret kodu `-850002`, `-850004` veya `-850044` ise strateji durur (`TradeByVolume::parseMessages`; yalnız **kod** karşılaştırılır, ret metni değil). AlgoProd bu üç kodu tanımlar (`Globals/GlobalDefinitions.h`). HFT'deki `-850064` (margin user blocked) ve Arbitraj'daki `-420131` burada kontrol edilmez; bu kodlarla gelen ret yalnız loglanır, `isOrderSent` sıfırlanır ve strateji emir göndermeye devam eder. Kasıtlı mı, bilinmiyor. Kod listesi: [borsa-kurallari](../00-genel/borsa-kurallari.md).

## AKD (aracı kurum dağılımı) filtresi

Tasarım: seçilen aracı kurumların alış/satış payı eşiği sağladığında piyasa hacmi sayılır ve emir gönderilir (`isAkdChecksHold`).
- **Açılma:** `Broker_Alis_Count + Broker_Satis_Count > 0` ise `isAkdDataEnabled` (listenin kendisine değil, **sayaç alanlarına** bakılır).
- AKD kapalıysa `isAkdChecksHold = true` (filtre yok).
- AKD açıksa: `setCommand`'daki `DatabaseServiceClient::subscribeToVWAPData` çağrısı `isThisMainStrategy && false` ile **devre dışı** ("todo temporary disabled"). Bağımsız bir VWAP'ta `VWAPSubscriberAlis` hiç beslenmez, `isAkdChecksHold` `false` kalır; strateji hacim saymaz ve emir göndermez. Değeri yalnız Overall (`setIsAkdChecksHold`) değiştirebilir.
- Karar yalnız **alış** sonucuna bakar (`isAkdChecksHoldForAlis`); satış sonucu okunur ama kullanılmaz.
- **İki GUI de broker alanlarını göndermez** (yeni GUI `vwapContract.ts`, eski GUI `OrderBookSettings.tsx`). Pratikte filtre kapalıdır.
- AKD verisi trade-data-app'ten gelir (`FetchAkd`); config: [trade-data-app/entegrasyonlar](../10-servisler/trade-data-app/entegrasyonlar.md).

## Overall (`TradeByVolumeOverall`)

Tasarım: birden çok VWAP'ı bir "ana" stratejiye bağlamak; ana stratejinin AKD durumu ve karşı fiyatı (`getOppositeLevel`) çocuklara aktarılır, hepsi bitince hepsi durdurulur.
- `mainStrategy` ve `strategies` alanlarına **kodda hiçbir yerde atama yok**. `doPeriodicChecks` her turda "mainStrategy is null" yazıp 1 sn uyur. Yani Overall işlevsizdir.
- Yeni GUI'de karşılığı yok (Overall'ı oluşturan ekran veya payload bulunmuyor). `checkParams` Overall için alan doğrulamaz.

## Parametreler (wire, `GuiConstants.h`)

`checkParams` zorunlu tutar: `Vwap_Side`, `Vwap_Mode`, `Vwap_Price_Limit`, `Ratio` (> 0), `Strategy_Unique_Key`.

| Alan | Tip | Birim | Yeni GUI varsayılanı | Anlam |
|------|-----|-------|----------------------|-------|
| `Vwap_Side` | Int (char) | — | 66 / 83 | `B` alış, `S` satış |
| `Vwap_Mode` | Int (char) | — | 78 `N` | `P` (80) / `N` (78) / `A` (65) |
| `Vwap_Price_Limit` | Long | raw (enstrüman ölçeği) | "0" | Fiyat limiti (yukarıda; 0 kapalı değil) |
| `Trade_Limit` | ULongLong (UI Long) | lot | "1" | Hedef toplam lot |
| `Ratio` | ULongLong (UI Long) | — | "1" | Piyasa hacminin `1/Ratio`'su |
| `Stop_Loss_Level` | Long | raw | "0" | Stop fiyatı; 0 = kapalı. Sabit adı `ARB_STOP_LOSS_LEVEL` (arbitrajla ortak) |
| `Channel_Enum` | Int | — | 2 FIX | 1 OUCH, 2 FIX. Eski GUI yeni ayarda 0 gönderir, modalda varsayılan 2 |
| `Base_Interest` | Long | % (tam sayı) | gönderilmez | Vadelide teorik fiyat faizi |
| `Broker_Alis_Count`, `Broker_Alis_List`, `Broker_Percentage_Alis`, `Broker_Lot_Alis` | Int / List / Int / ULongLong | — | gönderilmez | AKD alış filtresi |
| `Broker_Satis_Count`, `Broker_Satis_List`, `Broker_Percentage_Satis`, `Broker_Lot_Satis` | Int / List / Int / LongLong | — | gönderilmez | AKD satış filtresi |
| `Trade_Pay_Limit`, `Trade_Vade1_Limit`, `Trade_Vade2_Limit` | ULongLong | — | gönderilmez | **Kullanılmıyor.** Yalnız command'da parse edilir. |

Yeni GUI fiyatları "ham wire biriminde" alır ve tick bölünebilirliğini uyarır (`getVwapValidationWarnings`); ölçekleme yapmaz.

GUI'ye giden durum: `VWAPSummary` (`Strategy/StrategySummary.h`): `Vwap_Pos`, `Vwap_Buy_Position`, `Vwap_Sell_Position`, `Vwap_Buy_Volume`, `Vwap_Sell_Volume`, `Vwap_Side`, mod, çalışıyor mu. Her kendi dolumumuzda yayınlanır. Özet anahtarı `<hesap>_<stratejiId>_<orderbookId>`.

## UI

**Yeni GUI** (route `vwap`, [yeni-gui](../10-servisler/mtrader-trade-ui/yeni-gui.md)):
- Tracker paneli yok; strateji `order_book` panelinden yönetilir: `orderbook/VwapControlsOverlay.tsx`, `VwapOrderBookControls.tsx`, ayar `modals/VwapSettingsModal.tsx` + `modals/vwap-settings/`, ekleme `AddVwapStrategyModal`.
- Wire: `features/vwap/vwapContract.ts` (`buildVwapSettingsPayload`, `Command_Type` 54), kimlik `vwapIdentity.ts`: `unique_key = <orderbookId>_<hesap>_<stratejiId>_7_<66|83>`. Alış ve satış iki ayrı strateji olarak yönetilir (`VWAP_SIDES`).
- Özet paneli `vwap_summary_view` (`VwapSummaryView.tsx`, `vwapSummaryStore`).

**Eski GUI** (`origin/main`, [eski-gui § 3.9](../10-servisler/mtrader-trade-ui/eski-gui.md)): OrderBook paneli, ayar `OrderBookSettings.tsx` (`Command_Type` 54), `unique_key` sonuna `_66`/`_83`, özet `VWAPSummaryView`.

## Şüpheli

- **Vadelide fiyat limiti 0'a iniyor (bug?):** `underlyingOppositeLevel` yalnız işlevsiz Overall'dan beslendiği için 0 kalıyor; `teo = 0`, `limit = min(limit, 0) = 0`. Vadeli **alışta** strateji hiç emir göndermez; vadeli **satışta** fiyat tabanı kalkar. Değer komuta yazıldığı için snapshot'ta UI'ya 0 döner. `Base_Interest` de hiçbir GUI'den gelmiyor. ❓ doğrulanmadı: prod'da VİOP'ta VWAP kullanılıp kullanılmadığı.
- **AKD açıkken strateji kilitleniyor (bug?):** abonelik devre dışı olduğu için `isAkdChecksHold` hiç `true` olmuyor. GUI'ler broker alanlarını göndermediği için şu an tetiklenmiyor.
- **Overall işlevsiz:** `mainStrategy` hiç atanmıyor.
- **Stop emri hemen iptal edilebilir:** stop tetiklenince gönderilen DAY emir, `stop()` → `exitProperly`'deki `cancelAllOrders` ile 100 ms sonra iptal ediliyor; dolmayan kısım piyasada kalmaz ve kalan miktar gerçekleşmemiş olur.
- **Stop karşılaştırması kendi tarafın en iyi fiyatıyla:** alışta en iyi alış fiyatı (bizimki dahil olabilir) stop'u geçince tetiklenir; karşı tarafa (son işlem / satış) bakılmaz. Kasıtlı mı, doğrula.
- **PTRM listesi eksik:** `-850064` ve `-420131` durdurmuyor; ret metni de kontrol edilmiyor (Arbitraj ediyor).
- **Hedefe ulaşınca kendini durdurma:** yorumdaki "yeni GUI'ye geçince silinmeli" notu duruyor; yeni GUI bu davranışı korunmuş olarak kullanıyor. Kasıtlı mı, netleşmedi.
- **`totalExecutedQty` kendi dolumlarımızı düşüyor:** piyasa trade akışında kendi işlemlerimizin de geldiği varsayılıyor; fiyat limiti dışındaki kendi dolumumuz da düşüldüğü için (piyasa tarafında sayılmamışken) beklenen miktar fazla azalabilir. ❓ doğrulanmadı.
