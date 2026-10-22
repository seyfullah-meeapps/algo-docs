---
kapsam: Strateji kataloğu — StrategyType numarası, motor, sınıf, UI workspace, durum
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-22
durum: taslak
---

# Strateji kataloğu

`StrategyType` bir **wire değeridir**: proto'larda (`common.proto`), DB'de, `unique_key`'de ve UI'da aynı sayı kullanılır. Numaralar değiştirilmez.

Strateji kimliği (`unique_key`): `<orderbookId>_<hesap>_<strategyIdentifier>_<StrategyType>`. Bkz. HFT `StrategyManager::findStrategy`.

## HFT motorunda (HftSrvProd)

| # | Wire adı | Türkçe ad | Sınıf (`src/Strategy/`) | Yeni GUI route | Dosya |
|---|----------|-----------|-------------------------|----------------|-------|
| 4 | `HFT` | HFT / Klasik | `HftClassic` | `hft` | [hft-classic.md](hft-classic.md) |
| 8 | `TheoreticalPrice` | Teorik Fiyat | `HftTheoreticalPrice` | `theoretical-price` | [teorik-fiyat.md](teorik-fiyat.md) |
| 9 | `MaxPrice` | Tavan | `HftMaxPrice` | `max-price` | [tavan.md](tavan.md) |
| 14 | `MinPrice` | Taban | `HftMinPrice` | `min-price` | [taban.md](taban.md) |
| 13 | `HFT_Warrant` | Varant | `HftWarrant` | `warrant` | [varant.md](varant.md) |
| 15 | `HFT_WarrantAdvanced` | Varant Toplu | `HftWarrantAdvanced` | `bulk-warrant` | [varant-toplu.md](varant-toplu.md) |

Varant Toplu 2026-10-19'da development'a merge edildi (HftSrvProd PR #615). ⚠ master'da yok (2026-10-22).

## AlgoProd motorunda (AlgorithmicTrading)

AlgoProd stratejileri iç `Commands` enum'u ile oluşturulur (`algoSrc/Globals/Enumarations.h`, `Strategy/StrategyFactory.h`); wire `StrategyType`'a çevrimi `Utilities/OrderUtility.h` `convertMyOrderStrategy`.

| # | Wire adı | Türkçe ad | Sınıf (`algoSrc/Strategy/`) | İç komut | Yeni GUI route | Dosya |
|---|----------|-----------|-----------------------------|----------|----------------|-------|
| 6 | `Arbitrage` | Arbitraj (spot–vadeli) | `Arbitrage/ArbitrageTracker` | `ArbitrageTracker` `'3'` | `arbitrage` | [arbitraj.md](arbitraj.md) |
| 6 | `Arbitrage` | Sepet Arbitraj (endeks vadeli) — **henüz kullanılmıyor** | `BasketArbitrage/BasketArbitrageTracker` | `BasketArbitrageTracker` `'E'` | — | [arbitraj.md](arbitraj.md) |
| 7 | `VWAP` | VWAP | `TradeByVolume/TradeByVolume`, `TradeByVolumeOverall` | `TradeByVolume` `'6'`, `TradeByVolumeOverall` `'V'` | `vwap` | [vwap.md](vwap.md) |
| 10 | `FundTracker` | Fon Takibi (BYF) | `FundTracker/FundTracker` | `FundTracker` `'d'` | `fund-tracker` | [fon-takibi.md](fon-takibi.md) |
Sepet arbitraj wire'da da `Arbitrage` (6) olarak gider: `BasketArbitrageTracker` taban sınıfa `MyOrderType::ArbitrageTracker` verir, `convertMyOrderStrategy` bunu `ARBITRAGE`'a çevirir. İç komut (`'E'`) farklıdır.

🚧 AlgoProd'un MAOrderSDK + handoff geçişi `add-order-sdk` branch'inde (bkz. `00-genel/sistem-haritasi.md`).

## Kullanılmayan kod

Kodda duran ama uzun süredir kimsenin kullanmadığı tipler (kullanıcı beyanı, 2026-10-22). Bu bilgi tabanında belgelenmez. Kodda görürsen aktif sanma:
- HFT: `OrderChase` (11). Komut parse ediliyor, strateji oluşturulmuyor.
- AlgoProd: `Warrant` (2, WarrantTracker), `AKD` (3, TradeByBSRatio), `MovingAverage` (5).

## Strateji olmayan tipler

| # | Wire adı | Anlamı |
|---|----------|--------|
| 0 | `Unknown` | — |
| 1 | `Algo_User` / `User` | Serbest (manuel) emir. order-service ve AlgoProd yolu. |
| 12 | `HFT_User` | HFT üzerinden serbest emir. |

Yeni GUI'de ayrıca **Toplu Emirler** (`collective-orders`) workspace'i var: sabah / açılış / akşam / YİP emirleri. Backend'de `StrategyType`'ı yok; emirler `OrderType` (MORNING=1, OPENING=2, STRATEGY=3, EVENING=4) ile order-service'e gider. Bkz. `00-genel/sistem-haritasi.md` → Emir yolları.

## Motor yönlendirmesi

UI'dan gelen bir komutun hangi motora gideceğine trade-data-app karar verir: `pkg/servicemodels/gui_api.go` `getApplicationFromStrategyType`. Bu fonksiyona yeni bir tip eklenmezse komut düşer. Varant Toplu (15) için bu eksik bulunmuş ve düzeltilmişti (mtrader-trade-ui `AGENTS.md`).
