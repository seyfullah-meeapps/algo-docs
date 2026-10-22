---
kapsam: Fon Takibi (FundTracker, StrategyType 10, AlgoProd) — borsa yatırım fonu (BYF) ile sepetindeki hisseler arasında piyasa yapıcılık/arbitraj; teorik fiyat, kotasyon, sepet emirleri, paketler
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# Fon Takibi (`FundTracker`, 10) — AlgoProd

Bir **BYF** (borsa yatırım fonu, ör. ZPX30) için fonun sepetindeki hisselerden **teorik fiyat** hesaplar. Fon tahtasına teorik fiyat ± spread'den alış ve satış kotasyonu verir.
- Kotasyonda minimum işlem birimi kadar fon alınınca sepetteki hisseler satılır.
- Fon satılınca sepetteki hisseler alınır.
- Her tamamlanan sepet işlemi bir **paket** olarak DB'ye yazılır.

Kod: `algoSrc/Strategy/FundTracker/FundTracker.{h,cpp}`, `algoSrc/Commands/FundTrackerCommand.*`, `algoSrc/Data/BYFData.h`. İç komut `'d'`.

## Veri: PCF (fon sepeti)

- trade-data-app açılışta BYF dosyasını indirir ve sepeti **bellekte** tutar; DB'ye yazmaz, gün içinde yenilenmez (`config.json` → `byf`; `UpdateBYFSettings`). Ayrıntı: [trade-data-app/entegrasyonlar.md](../10-servisler/trade-data-app/entegrasyonlar.md).
- AlgoProd sepeti `AlgoService.GetByfSettings` ile okur (`readPcfFile`). Her sepet hissesini sembol önekiyle tradable enstrümana eşler.
- Eşlenemeyen sembol olursa strateji durur.
- Her hisse için ağırlıktan hesaplanan bir lot (`calculatedLotCount`) ve fonun minimum işlem birimine karşılık gelen fon lotu (`calculatedRequiredLotCount`) bulunur.

## Akış (`doPeriodicChecks`, yaklaşık 5 ms)

1. **Fiyat** (`calculatePrices`):
   - Sepet alış değeri = Σ (hisse best bid × lot); satış değeri = Σ (best ask × lot).
   - Teorik fon fiyatı = değer / `calculatedRequiredLotCount` (kuruş).
2. **Kotasyon** (`sendMassQuoteOrder`):
   - Alış: teorik alış − `Byf_Spread_Buy`.
   - Satış: teorik satış + `Byf_Spread_Sell`.
   - Fiyatlar tick'e yuvarlanır; DAY limit emir, **OUCH** gider.
   - Miktar = `min(Byf_Lot_Count_*, kalan minimum birim)`.
   - Paket sayısı `Byf_Package_Limit_Buy` / `Byf_Package_Limit_Sell` altındaysa gönderilir.
3. **Takip** (`checkPassiveMassQuoteOrder`): Teorik fiyat değişince kotasyon replace edilir.
4. **Gerçekleşme** (`checkBYFExecution`): Fon alışı minimum birime ulaşınca (`minTransactionUnitReached`) fon pozisyonu +1 olur ve sepetteki hisseler **satılır**. Fon satışı ulaşınca tersi yapılır.
5. **Sepet emirleri** (`sendUnderlyingOrders`):
   - Her hisse için karşı en iyi fiyattan emir gider.
   - Bütün hisse emirleri tamamlanınca paket `isCompleted` olur ve trade-data-app'e yazılır (`SetFundData`).
6. **Hata:** Fon emri reddedilirse strateji durur. DB'den fon kaydı alınamazsa durur.

## Wire alanları

| Alan | Tip | Anlam |
|------|-----|-------|
| `Byf_Spread_Buy` / `Byf_Spread_Sell` | Long | Teorik fiyattan uzaklık (kuruş) |
| `Byf_Lot_Count_Buy` / `Byf_Lot_Count_Sell` | Long | Kotasyon miktarı (fon lotu) |
| `Byf_Package_Limit_Buy` / `Byf_Package_Limit_Sell` | Long | Taraf başına paket sınırı |
| `Byf_Package_Limit` | Long | **Kullanılmıyor.** Parse edilir, yalnızca loglanır; sınırlar taraf bazlı alanlarla uygulanır. |
| `Byf_Start_Time` / `Byf_Stop_Time` | Long | Çalışma aralığı |

**UI notu:** Yeni GUI'deki fon ayar modalındaki "Alış/Satış Miktar" kutuları **bilerek etkisizdir**. Değer gönderilmez, eski GUI'nin davranışı birebir korunmuştur. `Byf_Lot_Count_*` snapshot'tan aynen geri yollanır. Bunu bug diye "düzeltmeyin" (mtrader-trade-ui `AGENTS.md` → "FUND_TRACKER dead lot boxes").

GUI'ye giden mesajlar: `FundTrackerStrategyActivity`, `FundTrackerUnderlyingPriceActivity`, paket aktivitesi (`Byf_Package_*`, `Byf_Order_*`).

## UI

Yeni GUI route `fund-tracker`. Tracker yerine paket listesi gösterilir.
