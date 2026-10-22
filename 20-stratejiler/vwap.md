---
kapsam: VWAP (StrategyType 7, AlgoProd) — piyasa hacminin belirli bir oranında katılarak hedef miktarı alma/satma; modlar, AKD filtresi, stop, wire alanları
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
dogrulama: 2026-10-22
durum: taslak
---

# VWAP (`VWAP`, 7) — AlgoProd

Bir enstrümanda **toplam `Trade_Limit` lotu**, piyasada gerçekleşen hacmin `1/Ratio` oranında katılarak alır veya satar (hacme bağlı katılım). Kodda adı **TradeByVolume**.

Kod: `algoSrc/Strategy/TradeByVolume/TradeByVolume.{h,cpp}`, `TradeByVolumeOverall.*`, `algoSrc/Commands/TradeByVolumeCommand.*`. İç komut `'6'` (TradeByVolume), `'V'` (Overall).

Emir yolu: AlgoProd → ouch-sdk → order-service (`Channel_Enum` ile OUCH veya FIX).

## Hesap (`runStrategy`)

Her döngüde (yaklaşık 100 ms):

- `tradedQty`: stratejinin şimdiye kadar gerçekleşen miktarı.
- `totalExecutedQty`: fiyat limiti içinde piyasada gerçekleşen toplam hacim (yalnızca AKD şartı tutarken sayılır).
- **beklenen** = `totalExecutedQty / Ratio − tradedQty`
- **kalan** = `Trade_Limit − tradedQty`
- **henüz emre dönmemiş** = kalan − pasifteki toplam miktarımız
- Kalan ≤ 0 ise tüm emirler iptal edilir, strateji biter ve durur.
- Fiyat limiti dışında kalan pasif emirler iptal edilir (`cancelOrdersOutsideLimit`).
- Önceki emrin accept'i gelmeden yeni emir gönderilmez (`isOrderSent`).

## Modlar (`Vwap_Mode`, char)

| Kod | Mod | Davranış |
|-----|-----|----------|
| `P` | Pasif | Kendi tarafının en iyi kademesine (fiyat limitini aşmadan) yazar. Beklenen miktara kademedeki diğer emirlerin `1/Ratio`'su eklenir. |
| `N` | Normal | Karşı taraf fiyat limiti içindeyse beklenen miktar kadar karşı fiyattan **aktif** emir; değilse pasif moddaki gibi. |
| `A` | Agresif | Yalnız karşı taraftan aktif. Gerekirse daha kötü pasif emirleri iptal eder. |

Fazla pasif miktar `updateLevelQuantity` / `updateOrdersExcessQuantity` ile küçültülür. Kalandan fazla emir gerekiyorsa en kötü fiyatlı pasifler iptal edilir (`cancelWorseOrders`).

## Fiyat limiti

`Vwap_Price_Limit` (raw):
- Alışta bu fiyatın üstüne, satışta altına emir yazılmaz.
- Vadeli enstrümanda limit ayrıca **teorik fiyatla** sınırlanır: dayanak karşı fiyatı × (1 + vadeye kalan yıl/100 × `Base_Interest`), /10.

## Stop

`Stop_Loss_Level` > 0 ise:
- Alışta kendi header'ı stop fiyatına ulaşınca (≥), satışta düşünce (≤) tüm emirler iptal edilir.
- Kalan miktar karşı fiyattan tek emirle gönderilir ve strateji durur.

## AKD (aracı kurum dağılımı) filtresi

- `Broker_Alis_List` / `Broker_Satis_List` ile seçilen aracı kurumların alış veya satış payı `Broker_Percentage_*` / `Broker_Lot_*` eşiklerini sağladığında piyasa hacmi sayılır.
- Liste boşsa filtre kapalıdır.
- Veri trade-data-app AKD entegrasyonundan (Foreks) gelir. AKD config'te kapalıysa (`akd.isEnabled=false`) filtre kullanılamaz.

## PTRM

Ret kodu `-850002`, `-850004` veya `-850044` ise strateji durur (`TradeByVolume.cpp` ret kontrolü). AlgoProd bu üç kodu tanımlar (`Globals/GlobalDefinitions.h`). HFT'deki `-850064` (margin user blocked) AlgoProd'da **tanımlı değildir**; bu kodla gelen ret stratejiyi durdurmaz. Kasıtlı mı, bilinmiyor.

## Overall (`TradeByVolumeOverall`)

Birden çok VWAP'ı bir "ana" stratejiye bağlar. Ana stratejinin AKD durumu ve karşı fiyatı çocuk stratejilere aktarılır. Yeni GUI'de karşılığı yok (Overall'ı oluşturan bir ekran veya payload bulunmuyor).

## Wire alanları

| Alan | Tip | Anlam |
|------|-----|-------|
| `Vwap_Side` | Int (char) | Alış/satış |
| `Vwap_Mode` | Int (char) | `P` / `N` / `A` |
| `Vwap_Price_Limit` | Long | Raw fiyat limiti |
| `Trade_Limit` | ULongLong | Hedef toplam lot |
| `Ratio` | ULongLong | Piyasa hacminin 1/Ratio'su kadar katıl |
| `Stop_Loss_Level` | Long | Stop fiyatı (raw); 0 = kapalı |
| `Base_Interest` | Long | Vadelide teorik fiyat faizi |
| `Trade_Pay_Limit`, `Trade_Vade1_Limit`, `Trade_Vade2_Limit` | ULongLong | **Kullanılmıyor.** Yalnızca command'da parse edilir. |
| `Broker_Alis_Count`, `Broker_Alis_List`, `Broker_Percentage_Alis`, `Broker_Lot_Alis` | | AKD alış filtresi |
| `Broker_Satis_Count`, `Broker_Satis_List`, `Broker_Percentage_Satis`, `Broker_Lot_Satis` | | AKD satış filtresi |
| `Channel_Enum` | Int | OUCH / FIX |

## UI

- Yeni GUI route `vwap`. Tracker paneli yok; özet `VWAPSummary` (`Vwap_Pos`, `Vwap_Buy_Volume`, …) ile gelir.
- Sabah emri ile ilgili ayrı bir düzeltme var (`fix/vwap-morning-order`).
- Kod yorumları ("When TradeByVolume added to new gui environment, this logic should be deleted") stratejinin bittiğinde kendini durdurmasının yeni GUI'ye geçişte değişebileceğini söylüyor.
