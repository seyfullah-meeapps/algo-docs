---
kapsam: Varant (HFT_Warrant, StrategyType 13) — dayanak kriteri tutunca birden çok varanta KIE alış, 1 tick üstüne satış, kriter bozulunca satışı hedefe çekme
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

# Varant (`HFT_Warrant`, 13)

Dayanak (ör. BIST30 hissesi) emir defterinde operatörün tanımladığı kriter tutunca, listedeki **tüm aktif varantlara** operatörün verdiği fiyat ve miktardan aynı anda alış gönderir. Her alış dolunca 1 tick üstüne satış yazar. Kriter bozulursa satışları hedef (alış) fiyatına geri çeker.

Kod: `src/Strategy/HftWarrant.{h,cpp}`, `src/Commands/HftWarrantCommand.{h,cpp}`, `HftWarrantBalanceCommand.*`.

**Varant Toplu (15) ile karıştırma.** O strateji varantın kendi kotasyonunu izler ve sözleşmesi tamamen farklıdır: [varant-toplu.md](varant-toplu.md).

## Akış

1. **Abonelik:** dayanakta header değişimi ve (kalan lot kriterinde) seçilen taraf için level değişimi.
2. **Kriter** (`checkEntryCriteria`), her header/level olayında değerlendirilir:
   - Taraf: `Criteria_Side` (0 alış header, 1 satış header).
   - Lot şartı: header lotu `Lot_Comparison_Type` (0 `<`, 1 `<=`, 2 `>`, 3 `>=`) ile `Criteria_Value` karşılaştırılır.
   - Fiyat şartı: `Criteria_Price ≠ 0` ise header fiyatı `Price_Comparison_Type` ile karşılaştırılır.
   - Tetik = fiyat şartı **ve** (fiyat şartı kesin aşıldı **veya** lot şartı tuttu).
   - `Criteria_Type` (0 kalan lot, 1 yüzde) şu an aynı karşılaştırmayı yapıyor; yüzde modu ayrı hesaplanmıyor.
3. **Alış** (`executeBuyOrders`): Strateji `Idle` iken ve bekleyen satış yokken her aktif varanta `userQuantity` lot, `userPrice` fiyattan **KIE (IOC)** alış gider. Strateji durumu `BuyOrdersActive` olur.
4. **Satış:** Her alış fill'inde, fill miktarı kadar **userPrice + 1 tick** fiyatından DAY satış yazılır. Bütün alışlar sonuçlanınca durum `SellOrdersActive` olur.
5. **Hedefe çekme** (`replaceToTarget`): `SellOrdersActive` iken kriter artık tutmuyorsa bekleyen satışlar **userPrice**'a (başabaş) replace edilir. Bu her turda bir kez yapılır (`isReplacedToTarget`).
6. **Tur sonu:** Satışlar dolunca varant yeni tura hazır olur.

## Tolerans

`Tolerance_Count` = izin verilen **alış fill'i** sayısı.
- Sayaç her alış fill'inde artar (`currentTradeCount`). Sınır dolunca `strategyStopped=true`, `criteriaCheckActive=false`, durum `Idle` olur; bu yol `stop()` ile bütün emirleri iptal etmez. Kriter takibi/hedefe replace yolu da kapanır.
- ⚠ Tolerans 0 iken hiç işlem yapılmaz, çünkü `currentTradeCount < toleranceCount` şartı sağlanmaz. Varant Toplu'da 0 sınırsız demektir; burada değil.

## Fiyat ölçekleri (kritik)

Aynı payload'da iki farklı ölçek var:

| Alan | Ölçek |
|------|-------|
| `Criteria_Price` | **Dayanağın** raw ölçeği (dayanak header fiyatıyla karşılaştırılır) |
| `Derivative_Orders[].userPrice` | **Ondalıklı TL** (double). Motor kendisi **×1000** yapar (`userPrice * 1000`). Varantın `decimalCount`'una bakılmaz. |

Karıştırmak emri 10× veya 1000× yanlış fiyata gönderir. UI tarafı `WARRANT_ENGINE_PRICE_SCALE` sabitini kullanır ve fiyat için bir sağlık kontrolü yapar (mtrader-trade-ui `AGENTS.md` → HFT_WARRANT).

## Wire alanları

| Alan | Tip | Anlam |
|------|-----|-------|
| `Underlying_Instrument_Id` / `Underlying_Symbol` | Long / String | Dayanak |
| `Criteria_Type` | Int | 0 kalan lot, 1 yüzde |
| `Criteria_Side` | Int | 0 alış header, 1 satış header |
| `Lot_Comparison_Type` / `Price_Comparison_Type` | Int | 0 `<`, 1 `<=`, 2 `>`, 3 `>=` |
| `Criteria_Value` | Long | Lot (veya yüzde) |
| `Criteria_Price` | Long | Dayanak ölçeğinde raw; 0 = fiyat filtresi yok |
| `Tolerance_Count` | Int | Alış fill sınırı |
| `Hft_Type` | Long | `HftType::Warrant` (4) |
| `Derivative_Orders` | String (JSON) | `[{instrumentId, symbol, userPrice, userQuantity, isActive}]` |

## İkinci kod turu — ret ve parçalı satış sınırları

2026-10-23 HFT fetch/pull sonrası development `4275ccc` ve master `052dd96` değişmedi. `HftWarrant.{h,cpp}` ve incelenen command cpp'si iki uçta aynı; SDK/callback altyapısı ve prod binary'nin eşitliği buradan çıkmaz. Trigger, alış/satış, fill/ret, replace ve tolerans yolları okundu; canlı test yok.

**K-241 — senkron ret kendi mutex'ini yeniden istiyor:** `processItchEventTimed` `derivativeMutex` (`std::mutex`) tutarken `executeBuyOrders` SDK'ya girer. `executeOrder` da aynı kilit altında `placeSellOrder` çağırır. SDK yerel validasyon/gönderim reddini senkron `onRejected` ile iletirse HFT `rejectOrder` aynı mutex'i almaya çalışır. Aynı thread recursive olmayan mutex'te kalabilir. Bu statik çağrı zinciridir; bütün emirlerin kilitlendiği veya canlıda yaşandığı iddia edilmez. SDK'nın senkron ret ürettiği yol koşuldur.

**K-242 — birden çok satış için tek token:** Her buy fill'i ayrı satış gönderebilir; `addOrder` her satış accept'inde tek `sellOrderToken` alanını üzerine yazar. `replaceToTarget` yalnız bu token'a, bütün türev için `buyFilledQuantity-sellFilledQuantity` miktarıyla replace dener. Önceki satışlar böylece aynı hedef yönetiminde ayrı ayrı temsil edilmez. İki parçalı buy fill/iki satış ACK senaryosu koddan görülebilir; exchange miktar semantiği ve canlı sonuç test edilmedi. Varant Toplu'nun satış listesi modeliyle karıştırma.

`replaceToTarget` gönderim sonucu başarısız olsa da `isReplacedToTarget=true` yazar; bu alan ACK teyidi değildir ve otomatik tekrar garantisi vermez. Tolerans sınırı yalnız trade fill sayacında değil, tamamlanan tur `cycleCount` kontrollerinde de kullanılır. Ayar 0 komutta geçersiz sayılır; “0 sınırsız” değildir.

### Arayüz ve bakiye

- Elle girilen (`UserOrder`) emirler strateji mantığına girmez; yalnızca varant veya dayanak bakiyesini günceller.
- Varant bakiyeleri `HftWarrantBalanceCommand` ile GUI'ye gider.
- UI (route `warrant`): varantlar dayanak satırının altında çocuk satırlar olarak gösterilir. Piyasa aboneliği için varant listesi canlı snapshot'taki `Derivative_Orders`'tan alınır.
