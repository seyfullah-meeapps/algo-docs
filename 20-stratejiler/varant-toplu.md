---
kapsam: Varant Toplu (HFT_WarrantAdvanced, StrategyType 15) — tetik, alış/satış mantığı, durumlar, wire alanları, UI
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-22
durum: taslak
---

# Varant Toplu (`HFT_WarrantAdvanced`, 15)

⚠ master'da yok (2026-10-22). 2026-10-19'da development'a merge edildi (HftSrvProd PR #615, order-service #423, network-sdk #84, ouch-sdk #62).

Bir dayanak (ör. BIST30 hissesi) için **birden çok varantı** aynı anda izler. Bir varantta piyasa yapıcının (kotasyoncu) satış kademesi agresif alışla yenince o varantı KIE ile alır, ardından 1 tick yukarıya satış yazar. Satış fiyatı dayanağın hareketine göre maliyet ile maliyet + 1 tick arasında gidip gelir.

Kod: `src/Strategy/HftWarrantAdvanced.{h,cpp}`, `src/Commands/HftWarrantAdvancedCommand.{h,cpp}`, `src/Commands/WarrantAdvancedEventCommand.{h,cpp}`. Sınıf başındaki Türkçe yorum davranışın özetidir.

Varant (13) ile **hiçbir sözleşmeyi paylaşmaz**. Payload, fiyat ölçekleri ve UI yardımcıları farklıdır.

## Akış

1. **Tetik.** Her aktif varant için ITCH `ORDER_EXECUTED` aboneliği açılır. Yalnız `side = Sell` olan fill'ler sayılır: duran satış emri yenmiştir, yani agresif alış gelmiştir.
   - Aynı agresif emrin fill'leri aynı ITCH `ts`'ini taşır. Strateji bunları **ts başına bir kovada** toplar.
   - Sayılan miktar yalnızca **ilk fill'in fiyat kademesindeki** fill'lerdir. Bu kademe kotasyoncunun kademesidir; üst kademelere taşan fill'ler sayılmaz.
2. **Koşul** (`quotationLotOp`, varant başına): yenen miktar `eaten`, kotasyon lotu `quotationLot` ise:
   - `eq`: `eaten == quotationLot` (varsayılan; kademede yalnız kotasyoncu varken)
   - `le`: `0 < eaten <= quotationLot` (ilk fill'de tetiklenir)
   - `ge`: `eaten >= quotationLot`
   - Kova başındaki tahta miktarı config'deki kotasyon lotundan farklıysa WARN log basılır, tetik yine config'e göre çalışır.
3. **Alış.** Tetik fiyatından (`execAccumFirstPrx`) `Warrant_Lot_Quantity` lot **KIE (IOC) limit alış** gönderilir. Durum gönderimden önce `BuyPending` olur, böylece ack gelene kadar ikinci tetik ikinci alış göndermez.
   - O anki dayanak kitabı (bid/ask/lot) *referans* olarak saklanır.
   - OUCH replay bitmemişse tetik atlanır (`ouchReplayComplete`).
4. **Satış.** Her alış fill'inde, o fill miktarı kadar **DAY limit satış** yazılır. Kısmi alışlar birden fazla satış emri doğurabilir, her biri ayrı izlenir.
   - Alış fiyatı = kısmi fill'lerin **en yükseği** (`buyPrice = max`). Böylece başabaş çıkış en kötü alışın altına inmez.
5. **Satış hedefi** (`sellTarget`). İzlenen taraf: **Call (`C`) varantta dayanak ask, Put (`P`) varantta dayanak bid**. Referans, alış **gönderildiği** andaki fiyattır.
   - Aleyhte hareket (Call'da ask düştü / Put'ta bid çıktı) → **maliyet** (`Adverse`).
   - Lehte hareket → **maliyet + 1 tick** (`Up`).
   - Referansta → `Cost_Timeout_Ms` dolana kadar maliyet + 1, sonra maliyet (`Stalled`).
   - Dayanak bu turda referanstan **bir kez ayrılıp geri döndüyse** süre beklenmeden maliyet (`leftReference`).
   - Varant tipi bilinmiyorsa (`getWarrantType` = 0) yalnızca süre kuralı uygulanır.
6. **Replace.** Hedef değişince satış emirleri replace edilir. Kurallar:
   - Replace miktarı **her zaman emrin ilk toplamıdır** (`SellOrder.total`, OUCH: gerçekleşen + açık). Açık miktarı borsa kendisi hesaplar, böylece satış hiçbir yolda büyümez (açığa düşmeme).
   - Yukarı çekme son replace'ten sonra **200 ms** bekler (`kRaiseCooldown`), titreyen dayanakta emir yağmasın diye. Maliyete çekme beklemez.
   - Replace reddinden sonra o emir **1 sn** tekrar denenmez (`kReplaceRejectBackoff`).
   - Süre kuralı ITCH olayı beklemez: AlgoWorker kuyruğu boşken `nextCheckNs` gelmişse yeniden değerlendirilir.
7. **Tur sonu** (`closeCycle`): satılan ≥ alınan olunca tur sayacı (`tradeCount`) artar.
   - Satışlardan biri **maliyetten veya altından** gerçekleştiyse varant `ClosedAtCost` olur ve **pasife çekilir**. Motor, aktif bayrağı kapalı ayar snapshot'ını GUI'ye geri yollar.
   - `Tolerance_Count` dolduysa `Done`.
   - Diğer durumlarda varant `Idle` olur ve yeni tetiğe hazırdır.

## Varant durumları (`WarrantState`)

| Durum | Anlamı | GUI'de |
|-------|--------|--------|
| `Idle` | Tetiğe hazır | |
| `BuyPending` | KIE alış yolda | |
| `Bought` | Alış gerçekleşti, satış henüz tahtada değil | |
| `SellPending` | Satış tahtada, hedef maliyet + 1 | |
| `Frozen` | Satış hedefi maliyet | "At Cost" / maliyette |
| `ClosedAtCost` | Maliyetten kapandı, varant pasife çekildi | |
| `Done` | Tur sınırı doldu | |
| `BuyRejected` | Alış reddedildi, varant pasif | |
| `SellRejected` | Bir satış reddedildi. Tahtadaki diğer satışlar hedefe çekilmeye devam eder. | |
| `Passive` | Kullanıcı pasife çekti | |

**Yeniden açma:**
- `ClosedAtCost` veya `BuyRejected` varantı kullanıcı tekrar aktif yapınca `Idle`'a döner (tur sınırı dolmuşsa `Done`).
- `Done` olan varant yalnız tur sınırı artırılınca veya kaldırılınca (0) devam eder.
- Tur sayacı gün boyu korunur.

## Wire alanları (`src/Globals/GuiConstants.h`)

| Alan | Tip | Anlam / birim |
|------|-----|---------------|
| `Underlying_Instrument_Id` | Long | Dayanak orderbook id |
| `Underlying_Symbol` | String | Dayanak sembolü |
| `Warrant_Lot_Quantity` | Long | Her varanta gönderilecek alış lotu |
| `Tolerance_Count` | Int | Varant başına izin verilen tur sayısı; **0 = sınırsız** |
| `Cost_Timeout_Ms` | Long | **Milisaniye.** Dayanak referansta bu kadar kalırsa satış maliyete; 0 = kapalı. GUI saniye (3 ondalık) gösterir. |
| `Hft_Type` | Long | `HftType::WarrantAdvanced` |
| `Warrant_List` | String (JSON) | Varant listesi, aşağıda |
| ortak alanlar | | `Strategy_Start`, `Is_Running`, hesap, identifier… (`BaseStrategyCommand`) |

`Warrant_List` elemanı:
```json
{"instrumentId":123,"symbol":"XXXXX","quotationLot":5000,"quotationLotOp":"eq",
 "isActive":true,"warrantType":"C","strikePrice":12.50,"expiryDate":"..."}
```
`warrantType`, `strikePrice` ve `expiryDate` motor tarafından kullanılmaz, yalnızca UI için taşınır. Motor varant tipini ITCH'ten okur (`ItchSdkClient::getWarrantType`).

**JSON elle parse edilir** (`parseJsonField`):
- Bir değer ilk virgülde, bir nesne ilk `}`'de biter.
- Metin alanlarında `,`, `"`, `{`, `}` kullanılamaz.
- UI `encodeWarrantList` bu karakterleri temizler ve `strikePrice`'ı 2 ondalığa yuvarlar.

## Kritik davranışlar (değiştirmeden önce bil)

- **Her komut varant listesini baştan kurar.** Çalışan emir ve pozisyon durumu `instrumentId` ile korunur. Boş `Warrant_List` veya lot 0 içeren komut **reddedilir** (`setCommand` false döner); durdurma ise her durumda uygulanır.
  - UI, ayar snapshot'ı yüklenmeden komut göndermez: `Warrant_List: []` stratejiyi siler.
- **Listeden çıkarılan ama emri/pozisyonu olan varant** düşürülmez; pasif olarak turunu bitirir. UI ayrıca açık pozisyonlu varantın listeden çıkarılmasını engeller.
- **Strateji çalışırken elle satış engellenir** (`userOrderBlockReason` → `ManualSellBlocked` olayı + gRPC `FAILED_PRECONDITION`). İstisna: satışı reddedilmiş (`SellRejected`) ve tahtada strateji satışı kalmamış varant.
- **Elle satış** stratejinin pozisyonundan düşülür. Pozisyon sıfırlanırsa tahtadaki strateji satışları iptal edilir, tur kapanır.
- **Durdurma:** Tüm varantların emirleri iptal edilir, ITCH abonelikleri kapanır. Kalan pozisyona satış yazılmaz.
  - Tekrar başlatınca strateji o pozisyonu **bırakır** (`releasePosition`): pozisyon hesapta kalır, varant yeniden tetiğe açılır.
  - Durdurulduktan sonra ack alan satış hemen iptal edilir.
- **Emir yolu:** Önce `maosdk->enterOrder` denenir. SDK hesabın sahibi değilse (handoff öncesi) `OuchManager::enterOrder` ile order-service'e düşülür. Replace ve cancel için de aynı sıra geçerlidir.
- Kilit: `warrantMutex` **recursive**'dir, çünkü SDK yerel reject'i `enterOrder` içinden senkron ateşler ve `rejectOrder` aynı kilidi ister.

## GUI'ye giden olaylar

- **Ayar snapshot'ı:** `HftWarrantAdvancedCommand::toClientMessage`. Durdur/başlat ve pasife çekmede geri yollanır.
- **Özet (per-warrant durum, pozisyon, K/Z):** hesap özeti `commandType 5` (`SUMMARY_<hesap>`), saniyede en fazla bir. Pozisyon bilgisi balance mesajından değil, buradan gelir.
- **Anlık olaylar** (`WarrantAdvancedEventCommand`, `Command_Type_HftWarrantDerivativeResponse`): `BuySent`, `ReplaceSent` (order token + gönderim anındaki dayanak kitabı ile), `Frozen`, `Raised`, `ManualSellBlocked`, alış/satış red olayları. Yalnızca o stratejiye abone istemcilere gider, replay edilmez.
- Order History'deki "Dayanak Bid/Ask" kolonu `BuySent` / `ReplaceSent` olaylarından beslenir ve OUCH token ile eşlenir.

## Fiyat ve birimler

- `buyPrice`, satış fiyatları, K/Z: **varantın kendi ölçeğinde raw** (instrument `decimalCount`).
- `underlyingAskAtBuy` / `underlyingBidAtBuy`: **dayanağın ölçeğinde raw**.
- Tick: `ItchSdkClient::getTickSize(varant, fiyat)`. Bulunamazsa 1 kullanılır.

## UI (yeni GUI)

- Workspace route `bulk-warrant`, kod `app/components/dockview/warrant-bulk/`.
- Ayrıntılı UI kuralları (yoğun tablo, mini emir defteri, toplu ayar modalı, dosya yükleme `/v1/parseWarrantFile` (CSV'yi [Warrant-Selector](../10-servisler/warrant-selector/README.md) üretir), Call/Put rozeti): mtrader-trade-ui `AGENTS.md` → "HFT_WARRANT_ADVANCED (Varant Toplu)".
- DB attribute satırları: trade-data-app `scripts/sql/hft_warrant_advanced.sql`.
- Eski GUI'de karşılığı `VarantTopluTrackerForm`. ❓ Eski GUI'de prod'da kullanılıyor mu, doğrulanmadı.

## Gölge kriter (log only)

`sendBuyOrder` her alışta `[WA_SHADOW]` log'u basar: dayanakta lehte taraftaki lot payı ≤ %5 mi? Girişi **engellemez**. Olası bir filtre için veri toplamaya yarar.
