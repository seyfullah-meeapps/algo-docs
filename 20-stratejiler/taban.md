---
kapsam: Taban (MinPrice, StrategyType 14) — taban duvarı eriyince alış, sıçramada satış; giriş/kaçış/reClose/top-up, satış modları, PTRM durdurma, wire alanları
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: HftSrvProd
    branch: master
    commit: 052dd96
dogrulama: 2026-10-22
durum: taslak
---

# Taban (`MinPrice`, 14)

**Fikir:** Taban fiyatında (pazara göre −%10 / −%15 / −%20, [borsa-kurallari](../00-genel/borsa-kurallari.md#günlük-fiyat-limitleri-tavan--taban)) duran satış duvarını alıcılar eritmeye başladığında fiyat tabandan kalkmak üzeredir. Strateji duvar incelince taban fiyatından **KIE alış** yapar ve sıçramaya satar.
- Yalnız long çalışır.
- Günü tabanda pozisyonla bitirmek kötü senaryodur; bu yüzden kaçış kuralları baskındır.

Kod: `src/Strategy/HftMinPrice.{h,cpp}` (header yorumları ayrıntılı), `src/Commands/MinPriceCommand.*`, `MinPriceStateCommand.*`.

Tavan ile **aynı sözleşmeyi paylaşmaz**. Ortak alanlar yalnızca genel yaşam döngüsü alanlarıdır (`Start_Time`, `End_Time`, `Strategy_Start`, `Is_Running`, `Close_Position_First`, `Second_Rule_Duration`, `Tl_Size`). Ayrıca `Second_Rule_Duration` burada **giriş cooldown'udur**, Tavan'daki gibi çıkış beklemesi değildir. Bkz. mtrader-trade-ui `AGENTS.md` → "MAX_PRICE and MIN_PRICE".

⚠ Eski bilgi tabanı Taban'ı "merge edilmemiş branch" olarak anlatıyordu; development'ta merge edilmiş ve büyük ölçüde yeniden yazılmış durumda.

## Taban durumu (`TabanState`)

- `Taban` (kilitli): satış header'ı taban fiyatında **ve** alış tarafı boş (`buyLevel == 0`).
- `NotTaban → Taban` geçişinde `tabanSecuredTimestamp` damgalanır; giriş cooldown'u buradan sayılır.
- Gerçek defter olayları ITCH damgasını kullanır; sentetik timer olayı `system_clock` epoch ns ile kurulur. Timer planlama `steady_clock` kullanır; bütün zamanlamayı yalnız ITCH saati sayma (ikinci tur ayrıntısı aşağıda).

## Giriş (`shouldEnterPosition`)

1. Pozisyon açık olmamalı.
2. Taban yeniden kilitlendikten sonra `Second_Rule_Duration` ms geçmiş olmalı (0 = kapalı).
3. Satış header'ı **taban fiyatında** olmalı. Duvar orada durmuyorsa giriş yoktur.
4. Tetik, iki seçenekten biri:
   - **Max-size alış** (`Min_Max_Size_Buy_Enter`): duvarı azami emir büyüklüğünde agresif alıcı yiyorsa lot kriterinin yerine geçer. Tavan'daki gibi fiyat bandı yoktur; KIE emri zaten yalnızca duvar tabandayken dolar.
   - **Erime:** `enterTriggerQty() ≥ satış header lotu`.
     - `enterTriggerQty()` = `Enter_Lot`. `Enter_Lot = 0` ise `tabanMaxSeenLot × Enter_Percentage / 100`.

**Emir** (`openPosition`): `Tl_Size × 1000 / taban` lot, **KIE (IOC) limit alış**, taban fiyatından.
- Önceki tur tamamen düz değilse (balance ≠ 0 veya emir duruyorsa) giriş atlanır: satışlar iptal edilir ve niyet 2 ms TTL ile saklanır (`armPendingOpenAfterClose`).
- **İkincil lot** (`Secondary_Enter_Lot`): Turun ilk alışı gittiği anda `Enter_Lot` kalıcı olarak bu değere çekilir ve UI'ya geri yollanır. Yüzde modunda uygulanmaz.
- IOC alış hiç dolmazsa `resetPositionIfFlat` pozisyon bayrağını temizler. Bu durum tur sayılmaz.

## Satış modları (`Is_Sell_Mode_Auto`)

- **Otomatik (varsayılan true):** Alış ailesinin tamamı yerleşince (bütün parçalar accept, alış derinliği boş), gerçekleşen balance kadar **tek** pasif satış yazılır (`maybePlaceAggregateAutoSell`). Fiyat:
  - `Sell_Level_Number > 0` → taban + N tick
  - aksi halde `Sell_Percentage` → tabanın en az %X üstü, tick'e yukarı yuvarlanır
  - İkisi de yoksa satış yazılmaz.
- **Manuel:** Kâr satışını operatör yönetir. Strateji yalnızca kaçış satışını yapar.

## Kaçış (`shouldEscapePosition`)

Çıkış zaten verilmişse (`isExiting`) tekrar tetiklenmez. Sıra:

| # | Tetik | Koşul |
|---|-------|-------|
| b | **Taban yeniden kilitlendi** | Satış header'ı tabana döndü ve durum `NotTaban` → anında kaç. |
| c | **reClose** | Satış header'ı tabanda. `Re_Close_Duration` ms boyunca taban erimeye fırsat verilir. Bu sürede duvar giriş kriterine eşit veya üstüne yeniden yükselirse erken kaç. Süre dolunca koşulsuz kaç ("TABAN HAS NOT MELTED"). 0 = bekleme yok. |
| a | **Alış desteği çöktü** | Alış header'ı tabanda ve `Escape_Lot` (veya `tabanMaxSeenLot × Escape_Lot_Percentage / 100`) ≥ alış header lotu. `Consider_All_Buy_Levels` açıksa ölçü **tüm alış kademelerinin toplamıdır** (SDK `sideTotalQuantity`); bu durumda "alış header'ı tabanda" şartı aranmaz. Aynı `Re_Close_Duration` beklemesi burada da geçerlidir. |

**Kaçış işlemi** (`closePosition`):
- Tahtada pasif satış varsa hepsi **taban fiyatına replace edilir**. Replace emri tahtada tuttuğu için arada çıplak kalınmaz.
- Pasif satış yoksa balance kadar taban fiyatından **DAY** satış gönderilir (`dumpPositionAtTaban`).
- Pozisyon hemen kapatılmış sayılmaz; `isExiting` açılır. Satış dolup balance 0 olunca `onPositionFullyClosed` turu kapatır.
  - Alıcısız tabanda satış uzun süre dolmayabilir. Erken kapatmak, yeni girişin bu çıkış satışını iptal etmesine yol açıyordu.
- Güvenlik: notional > 50M TL ise satış gönderilmez.

## Re-break (top-up)

Kaçış satışı tabanda beklerken taban **yeniden kırılırsa** (yükseliş), strateji satmayı bırakır (`shouldTopUpPosition` kaçıştan önce değerlendirilir):
- **Otomatik modda:** taban satışları kâr hedefine yukarı replace edilir (`topUpPosition`). Yeni alış yapılmaz.
- **Manuel modda:** taban satışları iptal edilir (`manualCancelOnReBreak`).

Koşullar:
- Balance > 0.
- Aile yerleşmiş.
- Cooldown geçmiş.
- Tabanda bizim satışımız var.
- **Taban yeniden oluşmuş olmalı** (`topUpArmed`): duvar giriş kriterinin kesinlikle üstüne çıkıp tekrar altına inmiş olmalı. Bu kural reClose ↔ top-up ping-pong'unu engeller.

## Tolerans ve durma

- **Tolerans:** Her tam kapanan tur `toleranceCounter`'ı artırır. `Tolerance` dolunca strateji durur; `-1` = sınırsız.
- **`Finish_With_Sell`:** Tolerans dolunca durma durumunu işaretler. ⚠ UI bu alanı **göndermez** (ürün kararı 2026-09-25). Motor eksik alanı false sayar. Simetri için eklemeyin (mtrader-trade-ui `AGENTS.md`).
- **PTRM reddi → anında dur** (`stopOnPtrmReject`): Ret kodu borsa ön-işlem risk koduysa strateji ilk redde durur. Kodlar: `-850002` user blocked, `-850004` pretrade breach, `-850044` margin breach, `-850064` margin user blocked (`GlobalConstants.h` `isPtrmRejectCode`).
  - **⚠ master'da yok:** `052dd96` legacy `rejectOrder` bu sınıflandırmayı/durdurmayı yapmaz; development `4275ccc` davranışıdır (K-235).
  - Açık pozisyon **bırakılır**, manuel müdahale gerekir.
  - GUI satırı bu duruşu ayrı renkte gösterir (`Stopped_By_Ptrm`).

## Hot/cold tiering

Tavan'ın tersine çalışır: satış fiyatı yukarıdan tabana yaklaşınca hot olur. Koşullar aynıdır (`hotWorkerCount > 0`); ayrıntı [tavan.md](tavan.md).

## Wire alanları

| Alan | Tip | Birim / anlam |
|------|-----|---------------|
| `Tl_Size` | Int | Lot = `Tl_Size × 1000 / taban` |
| `Enter_Lot` | Int | Giriş kriteri (satış duvarı lotu) |
| `Enter_Percentage` | Int | % (`tabanMaxSeenLot`'un); `Enter_Lot=0` iken |
| `Secondary_Enter_Lot` | Int | İlk girişten sonra `Enter_Lot` buna çekilir; 0 = kapalı |
| `Escape_Lot` | Int | Kaçış kriteri (alış desteği lotu) |
| `Escape_Lot_Percentage` | Int | %; `Escape_Lot=0` iken |
| `Consider_All_Buy_Levels` | Bool | Kaçışta tüm alış tarafının toplamı |
| `Min_Max_Size_Buy_Enter` | Bool | Momentum girişi |
| `Min_Max_Size_Buy_Enter_Percentage` | Int | Azami emrin %'si (300 = üç azami emir) |
| `Min_Max_Size_Buy_Enter_Delta` | Int | **Nanosaniye** pencere (UI µs × 1000) |
| `Sell_Level_Number` | Int | Otomatik satış: taban + N tick |
| `Sell_Percentage` | Int | Otomatik satış: tabanın %X üstü |
| `Is_Sell_Mode_Auto` | Bool | Varsayılan true |
| `Second_Rule_Duration` | Long | **Milisaniye**: taban yeniden kilitlendikten sonra giriş cooldown'u |
| `Re_Close_Duration` | Long | **Milisaniye**: reClose ve alış desteği için bekleme |
| `Tolerance` | Int | Tur sınırı; -1 sınırsız |
| `Finish_With_Sell` | Bool | UI göndermiyor |
| `Close_Position_First` | Bool | |
| `Start_Time` / `End_Time` | Long | Günün saniyesi, İstanbul (varsayılan 36000 / 64800) |

## GUI'ye giden durum

### İkinci kod turu — branch sınırı

2026-10-23 fetch/pull sonrası uçlar aynı. Development'ın `Secondary_Enter_Lot`, `Consider_All_Buy_Levels` ve `Min_Max_Size_Buy_Enter` alanları/giriş yolu master `052dd96` command/strateji koduna genellenmez. Master ayrı `Re_Close_Lot`/`Re_Close_Percentage` okurken development reClose eşiğini giriş kriterine bağlar. ReClose timer'ı **iki branch'te de vardır**; önceki alt turdaki master'da olmadığı ifadesi düzeltildi. Üstteki tetik anlatımı development içindir.

**K-235:** Master `rejectOrder` father-ref çözme, çıkış durumunu serbest bırakma ve `recheckEscape` yolunu sürdürür; PTRM kodunda `stopOnPtrmReject` çağrısı yoktur. Development PTRM muhasebesini yaptıktan sonra kilidi bırakıp durdurur; açık pozisyonu otomatik kapatma garantisi vermez. Kaynak: `HftMinPrice.cpp`, `MinPriceCommand.cpp` master/development farkı. Statik inceleme; prod binary ve gerçek ret senaryosu denenmedi.

### İkinci tur — timer ve callback sırası

`scheduleReCloseCheck` açılış/otomatik lift/manuel re-break sırasında kurulur. `openPositionTimestamp` ile system clock arasındaki geçen süre çıkarılır; kalan bekleme +1 ms steady-clock job yapılır. Job tek sefer tüketilir. `sendSecondRuleOrder` yalnız çalışan/açık pozisyonda `TIMER_TRIGGER_CHECK` ekler; karar AlgoWorker'dadır. Timer cached defterle **yalnız escape** kontrolünü çalıştırır, top-up/giriş çalıştırmaz; yeni bir piyasa snapshot'ı istemez.

Normal level olayı sırası giriş → top-up → escape'tir. Auto top-up yeni alış yapmaz, tabandaki satışları yukarı replace eder; manual top-up bunları iptal etmeyi dener. Her ikisi `isExiting/topUpArmed` durumunu ve hold başlangıcını yeniler. Gönderim denemesi ACK garantisi değildir. Manuel cancel ACK'i geldiğinde long pozisyon sürüyorsa ve tabanda satış kalmamışken `isExiting` açıksa, `deleteOrder` bu mandalı çözer; ardından escape kontrolü kuyruğa alınabilir.

Buy fill/cancel callback'leri aile yerleşip buy depth boşalınca tek aggregate kâr satışı kontrolünü yapar. Sell fill balance'ı sıfırlayınca tur kapanır. Callback sonlarında `tryConsumePendingOpenAfterClose` ve `recheckEscape` değerlendirilir. Bekleyen giriş 2 ms TTL'yi çağrıldığında kontrol eder; ayrı bir 2 ms otomatik gönderim timer'ı yoktur. Sıfır balance, boş iki depth, yerleşmiş aile ve hâlâ tabanda satış duvarı şartlarıyla yeniden dener.

`Consider_All_Buy_Levels` yolunda eşik sınırı header yolundan farklıdır: SDK thin sinyali toplam **<** eşik iken header karşılaştırması **≤** eşiği kabul eder. Üstteki ortak eşik anlatımını bütün seviyelerde eşitlik için kullanma.

**K-238 — çalışma saati filtresi koruyucu timer'ı da eler:** `processItchEventTimed` snapshot hariç bütün olayları `Start_Time < currentSec < End_Time` filtresinden geçirir. Dolayısıyla bitiş sınırında/sonrasında gelen reClose timer'ı ve yeni defter olayı escape kararına ulaşmaz; timer'ın varlığı pencere dışında otomatik satış garantisi değildir. Açık emir callback'leri ayrı yoldan işlenebilir; olay filtresi cancel veya pozisyon kapatma komutu değildir. Tavan'ın ikinci kural timer'ı da aynı filtreye tabidir. Kaynak: iki stratejinin event handler'ı, `EventDriven/ItchEvents.h`, `StrategyManager::periodicJobsWorker`. İki HFT branch'inde koddan görüldü; istenen ürün politikası ve canlı etkisi doğrulanmadı.

İkinci alt tur statik callback/timer yollarını tamamlar; eşzamanlı thread sıraları, saat kayması ve gerçek ACK/fill yarışları entegrasyon testinde denenmedi.

### Durum alanları

`MinPriceStateCommand` (`Command_Type_MaxPriceStateResponse` zarfıyla, Tavan ile aynı store). Alanlar: `Taban_State`, `Has_Passive_Buy_Order`, `Has_Passive_Sell_Order_At_Taban`, `Stopped_By_Ptrm`, tolerans sayacı, çalışma durumu.

UI (yeni GUI, route `min-price`): "Taban Lot" kolonu bounds feed'indeki `minBidLot`'tan gelir. ⚠ Eski GUI (prod) aynı kolonu `maxAskLot`'tan okuyor ([eski-gui § 3.5](../10-servisler/mtrader-trade-ui/eski-gui.md#35-tavan-9-ve-taban-14-tavan-taban-orderbooktavansettingstsx-tabansettingstsx), K-164). Satır yedi farklı durum rengiyle gösterilir.
