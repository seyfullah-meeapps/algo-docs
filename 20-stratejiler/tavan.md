---
kapsam: Tavan (MaxPrice, StrategyType 9) — tavan kilidinde alış, tavan bozulunca çıkış; giriş/çıkış tetikleri, escape, recover, max-size, sweep, tiering, wire alanları
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# Tavan (`MaxPrice`, 9)

**Fikir:** Gün sonunda tavanda kapanan hisse ertesi gün genellikle pozitif açılır. Strateji tavana oturan hisseyi tavan fiyatından alır ve tavanla kapanışa taşır. Tavan bozulursa satıp çıkar.

Kod: `src/Strategy/HftMaxPrice.{h,cpp}`, `src/Commands/MaxPriceCommand.{h,cpp}`, durum mesajı `src/Commands/MaxPriceStateCommand.*`.

Taban (MinPrice) ayrı bir sınıftır ve farklı bir sözleşmesi vardır: [taban.md](taban.md). Kod `Is_Tavan_Mode=false` ile taban modunu destekliyor gibi görünse de pratikte kullanılmaz.

## Ters isimlendirme

- `sellInfoOrder` → **ALIŞ** emri (`openPosition`).
- `buyInfoOrder` → **SATIŞ** emri.
- `cancelAlreadyExecutedOrders` → **satış gönderir**. Kod yorumu: "this is selling actually".

## Tavan durumu (`TavanState`)

`setTavanState()`:
- `NotTavan → Tavan`: satış tarafı boş (`sellLevel == 0`) **ve** alış header'ı tavan fiyatında.
- Aksi halde `Tavan → NotTavan`. Bu geçişte `tavanMeltedTimestamp` kaydedilir; `Open_Position_Second_Rule` bekleme süresi bu andan sayılır.
- Her geçişte "görülen en yüksek lot" filigranları (`tavanBuyHeaderMaxSeenLot`, `tavanSellHeaderMaxSeenLot`) sıfırlanır.

## Giriş (`shouldEnterPosition` + header yolu)

**Ön koşullar:**
- Pozisyon açık değil.
- Tavan eridikten sonra `Open_Position_Second_Rule × 100 ms` geçmiş.
- Saat `Start_Time`–`End_Time` aralığında.
- Header snapshot alınmış.

Tetikler, sırayla:

1. **Header yolu (doğrudan):** Header değişiminde satış tarafı boş, alış header'ı tavan ve durum `NotTavan` ise (tavan ilk kez kilitleniyor) koşulsuz `openPosition`.
2. **Tavan kilidi** (level yolu): aynı koşul `shouldEnterPosition`'da da var.
3. **Recover:** Alış header'ı tavanda, durum `Tavan`, `Should_Recover` açık ve alış kuyruğu `Cancel_Lot_Number`'a eşit veya üstünde → tekrar gir (`cameFromRecover = true`).
   - Yani pozisyon iptal eşiğiyle kapatılmış ama tavan bozulmamışsa yeniden kuyruğa girer.
   - `Cancel_Lot_Number = 0` iken recover çalışmaz.
4. **Sweep** (`Should_Sweep`): ITCH SDK satış tarafının **tamamını** `Melt_Lot`'un altında bildirirse (`couldSweep`) ve satış header'ı tavanın altındaysa, tavana kadar olan kademeler tek emirle alınır.
5. **Max-size alış** (`Max_Size_Buy_Enter`): Satış kuyruğunu azami emir büyüklüğünde agresif bir alıcı yiyorsa, eşik beklenmeden girilir.
   - Aktivasyon mesafesi `Max_Size_Buy_Enter_Levels` (tavanın kaç kademe altından itibaren) SDK'ya mutlak "arm price" olarak itilir. SDK bu fiyatın altında sinyal üretmez.
   - Kademe sayımı tick bantları gözetilerek tek tek yürünür. Çözülemezse tavana sabitlenir (fail-closed).
6. **Normal erime:** Satış header'ı tavan fiyatındayken:
   - Lot bazlı: `Melt_Lot ≥ satış header lotu`.
   - Yüzde bazlı (`Melt_Lot = 0` ve `Melt_Percentage ≠ 0`): `tavanSellHeaderMaxSeenLot × Melt_Percentage / 100 ≥ satış header lotu`.

**`openPosition` ek kontrolleri:**
- Önceki emir parçaları tamamen kabul edilmemişse veya eski pozisyon/emir duruyorsa giriş atlanmaz, **niyet saklanır** (`armPendingOpenAfterClose`).
  - Pozisyon kapanınca (execute/cancel callback'i) `tryConsumePendingOpenAfterClose` yeniden dener.
  - TTL **2 ms**. Tavan hâlâ kilitli değilse niyet düşürülür. (Eski doküman 20 ms diyordu; development'ta 2 ms.)
- `escapeDeceptionRejects()` → giriş reddedilir.
- Tolerans dolduysa strateji durur.

**Emir:** `Tl_Size × 1000 / tavanFiyat` lot, tavan fiyatından **DAY limit alış** (tip `QtyBarrier`). Büyük emirler father-order-ref ile parçalanır; bütün parçalar accept olmadan (`orderCompletelyAccepted`) kapatma yapılmaz.

- **`Is_Set_To_One`:** İlk girişten sonra `Melt_Lot` 1'e çekilir, sonraki girişler çok daha temkinli olur. Değişiklik UI'ya geri yollanır (`queueSetToOneUpdate`).
- **Kısmi çıkıştan geri dönüş:** Çıkış satışı kısmen dolmuş ve kalanı tavanda duruyorken tavan yeniden oluşursa kalan satış iptal edilir, pozisyon hedefe tamamlanır (`restoreFromPartialExit`, ardından `topUpToTargetIfShort`).

## Çıkış

| Tetik | Koşul |
|-------|-------|
| **Header** | Alış header'ı tavanın altına indi. `shouldCancelPosition` anında true döner. |
| **Lot / yüzde** | Alış header'ı hâlâ tavanda ama kuyruk eridi. Lot bazlı: `Cancel_Lot_Number ≥ alış header lotu`. Yüzde bazlı (`Cancel_Lot_Number = 0`): `tavanBuyHeaderMaxSeenLot × Cancel_Percentage / 100 ≥ alış header lotu`. |
| **Max-size satış** (`Max_Size_Sell_Exit`) | Durum `Tavan`'dayken tavandaki alış kuyruğunu azami emir büyüklüğünde agresif satıcı yedi. Sert çıkış. |
| **Hacim** | `Cancel_Time` (×100 ms) sonra tavandaki alış lotu `bizim lot × Cancel_Volume_Ratio` altına indi. Pratikte kullanılmıyor. |

**Bekleme (`Second_Rule_Duration`, ms):** Pozisyon açıldıktan sonra bu süre dolmadan çıkış yapılmaz. Header tetiği de bu kurala uyar.
- İstisna: `Recover_Second_Rule = false` iken recover girişlerinde bekleme yoktur.
- Süre dolduğu anda kitap sessizse bir timer `TIMER_TRIGGER_CHECK` olayı kuyruğa atar ve karar yeniden değerlendirilir (`sendSecondRuleOrder`).

**Kapatma işlemi** (`closePosition` → `cancelAlreadyExecutedOrders`): Tüm emirler iptal edilir, ardından balance kadar satış gönderilir. Satış fiyatı:

| Ayar | Fiyat |
|------|-------|
| `Is_Cancel_Mode_One_Price` = true | tavan fiyatı |
| `Activate_Percentage` ≠ 0 | tavan × (1 − pct/1000), tick'e yuvarlanır (binde birim) |
| `Cancel_Level_Number` > 0 | tavan − N × tick |

- OUCH'ta piyasa emri yok; düşük fiyatlı limit emir piyasa emrini taklit eder, borsa en iyi fiyattan eşleştirir.
- `Kie_Sell` açıksa çıkış **KIE (IOC)** gider: dolmayan kalan borsada iptal olur, sonraki girişte geri dönüş yolu bunu absorbe eder.
- Güvenlik: `balance × tavan > 50.000.000.000` raw (~50M TL) ise satış gönderilmez.

**Tolerans (`Cancel_Tolarence`):**
- Her kapatma `cancelNumberForTolerance`'ı artırır. Sınıra gelince strateji durur. `-1` = sınırsız.
- **`Finish_With_Buy`:** Tolerans sınırından bir önceki girişte alış gönderilir ve strateji kapanmadan durur (pozisyon korunur).
  - Kullanıcı toleransı artırırsa veya bu ayarı kapatırsa devam eder.
  - UI'da tolerans kapalıysa bu ayar devre dışıdır.

## Escape deception (manipülasyon filtresi)

Hisseyi hızla tavana koşturup oradan satan manipülatörlere karşı koruma.

- **Eşik:** `escapeCalculatedPrice = tavan × (10000 − Escape_Percentage) / 10000`, tick'e yuvarlanır. Birim **on binde bir**: 500 = %5. (Eski doküman /1000 diyordu.)
- **Örnekleme:** Her `Escape_Time` saniyede bir alış header'ı örneklenir (`sampleEscapePrice`).
  - İki noktalı zincir kullanılır: karşılaştırılan fiyat **en az `Escape_Time`, en fazla `2×Escape_Time` saniye önceki** fiyattır.
  - Az önce alınmış bir örnek kullanılmaz. Eski davranışta dikey koşular bu yüzden filtreden geçebiliyordu.
- **Karar:** Eski fiyat eşiğin altındaysa giriş reddedilir.
  - Henüz yeterince yaşlanmış örnek yoksa giriş **reddedilir** (fail-closed).
  - `Escape_Time = 0` filtreyi kapatır.
- Örnekler stratejinin başlatılmasında, `Escape_Time` artışında ve tiering cold'a düşüşünde sıfırlanır.

## Max-size (momentum) parametreleri

- **Azami emir lotu** = `maxOrderValue` (tam TL, VERDA) / tavan fiyatı.
  - Yüzde parametresi (`Max_Size_*_Percentage`) ile küçültülebilir; 0 veya ≥100 tam değer demektir.
  - %1 güvenlik payı düşülür (`maxSizeTolerance`).
- **`Max_Size_*_Delta`:** **Nanosaniye** pencere. Bu kadar yakın gelen fill'ler tek emir sayılır; dilimlenmiş aracı kurum algo emirleri de yakalanır.
  - UI bu alanı mikrosaniye (3 ondalık) olarak alır ve ×1000 yapar.
  - 0 = yalnız aynı borsa damgalı fill'ler birleştirilir.
- Bir gate push'u reddedilirse alış girişi tamamen kapatılır (fail-closed). Satış çıkışı tarafı açık bırakılır, çünkü yanlış çıkış ucuzdur.

## Hot/cold tiering (performans)

- **Ne zaman açık:** HFT config'inde `hotWorkerCount > 0` ise. Eşikler config'tedir (`HftMaxPriceTier*`).
- **Eşikler:**
  - **Promote (hot):** önceki kapanış × (1 + aktivasyon%), tick'e yuvarlanır.
  - **Demote (cold):** promote − N tick.
- **Cold'dayken:** Header ve level callback'leri kapatılır; strateji ITCH thread'ine ve worker'a yük bindirmez. Fiyat eşiği geçince hot olur ve callback'ler açılır.
- **Anti-flap:** hot'ta minimum kalma süresi, cold'dan dönüş cooldown'u, acil geri dönüş için tick eşiği.
- Ayrıntı: `10-servisler/hftsrvprod/` (AlgoWorker hot önceliği).

## Wire alanları

| Alan | Tip | Birim / anlam |
|------|-----|---------------|
| `Tl_Size` | Int | Pozisyon büyüklüğü; lot = `Tl_Size × 1000 / tavan` |
| `Melt_Lot` | Int | Giriş eşiği (lot) |
| `Melt_Percentage` | Int | Yüzde (%, /100); `Melt_Lot=0` iken |
| `Cancel_Lot_Number` | Int | Çıkış eşiği (lot); recover için de gerekli |
| `Cancel_Percentage` | Int | Yüzde (/100); `Cancel_Lot_Number=0` iken |
| `Cancel_Tolarence` | Int | Kapatma sayısı sınırı; -1 sınırsız. **Yazım: "Tolarence"** |
| `Second_Rule_Duration` | Long | **Milisaniye** (HFT Classic'te saniye!) |
| `Open_Position_Second_Rule` | Int | **100 ms** birimi |
| `Cancel_Time` | Int | 100 ms birimi |
| `Cancel_Volume_Ratio` | Int | Çarpan |
| `Is_Cancel_Mode_One_Price` | Bool | |
| `Cancel_Level_Number` | Int | Kademe |
| `Activate_Percentage` | Int | **Binde** |
| `Should_Recover` / `Recover_Second_Rule` | Bool | |
| `Finish_With_Buy` | Bool | |
| `Kie_Sell` | Bool | |
| `Should_Sweep` | Bool | |
| `Max_Size_Sell_Exit` / `Max_Size_Buy_Enter` | Bool | |
| `Max_Size_*_Percentage` | Int | % |
| `Max_Size_*_Delta` | Int | **Nanosaniye** |
| `Max_Size_Buy_Enter_Levels` | Int | Kademe |
| `Escape_Time` | Int | Saniye |
| `Escape_Percentage` | Int | **On binde** |
| `Is_Set_To_One` | Bool | |
| `Close_Position_First` | Bool | Başlarken pozisyonu açık say (`isPositionOpen` başlangıç değeri) |
| `Is_Tavan_Mode` | Bool | |
| `Profit_Percentage` | Int | ❓ Kodda kullanımı görülmedi |
| `Start_Time` / `Stop_Time` (çıkışta) / `End_Time` (girişte) | Long | **Günün saniyesi, İstanbul saati** (36000 = 10:00, 64800 = 18:00). ⚠ `getDefaultSettings` 600/1200 yazıyor; saniye olarak yorumlanırsa 00:10–00:20 olur. UI doğru değeri gönderiyor olmalı. ❓ |

## GUI'ye giden durum

`MaxPriceStateCommand` (`Command_Type_MaxPriceStateResponse`): tavan durumu (0/1), tolerans sayacı, pozisyon açık mı, çalışıyor mu, pasif satış var mı, tavanda pasif alış var mı. Dirty işaretiyle periyodik push edilir.

UI (yeni GUI, route `max-price`): canlı durum `maxPriceStateStore`'da tutulur, "Tavan Lot" kolonu bounds feed'inden gelir. Taban ile farkları: mtrader-trade-ui `AGENTS.md` → "MAX_PRICE and MIN_PRICE".

## Thread ve kilit

- ITCH olayları AlgoWorker'da işlenir. OUCH callback'leri recv thread'inden gelir. Second rule timer'ı periodic jobs thread'indedir; karar vermez, sadece olay kuyruğa atar.
- Kilit: `buySellInfoMutex` (`setCommand` 500 ms dener). Emir gönderilmeden önce kilit bırakılır.
