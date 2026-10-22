---
kapsam: mtrader-trade-ui — operatör arayüzü; yeni GUI (development) ve eski GUI (main) yapısı, backend sözleşmesi, deploy, iki sürüm arasındaki farklar
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui
    branch: main
    commit: 6715182
dogrulama: 2026-10-22
durum: taslak
---

# mtrader-trade-ui

Operatör arayüzü. **Aynı repoda iki ayrı uygulama var.** Hangi müşterinin hangisini kullandığı: [`00-genel/branch-ve-ortamlar.md`](../../00-genel/branch-ve-ortamlar.md#eski-gui--yeni-gui-parçalı-geçiş).

| | Yeni GUI | Eski GUI |
|-|----------|----------|
| Branch | `development` (preprod'a da gidiyor) | `main` (prod imajı) |
| Kaynak | `app/` | `src/` |
| Teknoloji | React 19, React Router 8 (framework mode, `ssr:false`), Vite, Zustand, TanStack Query, Dockview, Tailwind v4, TypeScript 7 | Vite + Ionic/Capacitor (Android/iOS) + Electron, React, context'ler |
| Geçmiş | Kişisel repoda (`mtrader-new`) sıfırdan yazıldı, 2026-09-14'te merge edildi (`7e14a00`) | Development'taki son hali `59f1689`. `main`'de bunun üstüne yalnızca deploy commit'leri var (Alnus/VPN, `algo_gui.yaml`). |
| Varant Toplu | Var (`bulk-warrant`) | **Yok** |
| Toplu Emirler workspace'i | Var (`collective-orders`) | Sabah emri ekranları var (`src/pages/...`, "Sabah Emri") |

**Yeni GUI için asıl kaynak repodaki `AGENTS.md`'dir** (~1500 satır, güncel tutuluyor). Bu doküman onu tekrar etmez, yalnızca harita verir. GUI davranışıyla ilgili bir soruda önce oraya bak:
- **Strateji kuralları:** HFT gizli alanlar, Varant Toplu, Fon Takibi etkisiz kutular, Tavan/Taban farkları.
- **WebSocket kuralları:** kendi kendine iyileşme, order socket aboneliği, paylaşılan itch socket, replay.
- **Fiyat ölçeği.**
- **Ürün kararları:** "Decisions and Boundaries".

## Yeni GUI (`development`)

### Yapı (`app/`)

| Yer | İçerik |
|-----|--------|
| `routes.ts` | Açık route tanımları (dosya tabanlı routing yok). `_auth` (login, otp, forgot/reset password), `_protected`, `_strategy`, `strategy-select`, `strategies/StrategyWorkspace.tsx`. |
| `lib/strategyWorkspace.ts` | **`STRATEGY_WORKSPACE_CONFIGS`**: strateji başına route, paneller, abonelik anahtarları, komut tipleri, gereken socket'ler. `matchesStrategyKey`: `HFT_WARRANT_ADVANCED` ⊃ `HFT_WARRANT` ⊃ `HFT` önek çakışmasını çözer. |
| `components/dockview/` | Paneller: tracker formları, emir defteri, emir geçmişi, emir gönderme, özetler, pasif emirler; strateji klasörleri (`hft/`, `max-price/`, `min-price/`, `warrant/`, `warrant-bulk/`, `arbitrage/`, `fund-tracker/`, `theoretical-price/`, `collective-order/`) |
| `api/` | REST istemcileri (Axios), React Query sorguları ve mutation'ları, WebSocket sınıfları (`api/socket/`) |
| `stores/` | Zustand store'ları ve yüksek frekanslı dış store'lar (`socketStore`, `marketDataStore`, `strategyDataStore`, `maxPriceStateStore`, `orderSnapshotStore`, `instrumentStore`) |
| `types/index.ts` | `StrategyType` (wire değerleri, değiştirilmez) |
| `locales/tr`, `locales/en` | Çeviriler (`npm run check:i18n`) |

### Workspace'ler

HFT (`hft`), Arbitraj (`arbitrage`), VWAP (`vwap`), Tavan (`max-price`), Taban (`min-price`), Teorik Fiyat (`theoretical-price`), Varant (`warrant`), Varant Toplu (`bulk-warrant`), Fon Takibi (`fund-tracker`), Toplu Emirler (`collective-orders`, backend `StrategyType`'ı yok).

Panel kapsamı eşit değildir: VWAP'ın tracker'ı yok, Teorik'in ayar modalı yok, Fon Takibi'nde tracker yerine paketler var.

### Backend sözleşmesi

- **REST:** trade-data-app :6621 (grpc-gateway, protojson; 64-bit sayılar **string** gelir).
- **WebSocket:** :6623 (Go json, sayılar **number**). `socketStore`'un merkezi yönettiği altı socket ve feed karşılıkları: market → `/ws/v1/best`, command → `/ws/v1/strategy`, order → `/ws/v1/orders`, bounds, equilibrium, itch. Yedinci feed `/ws/v1/passive-orders` merkezi değildir; yalnızca pasif emirler paneli (`StrategyPassiveOrders.tsx`) açar.
- Endpoint listesi: [trade-data-app](../trade-data-app/README.md).
- Login başarısız olsa da HTTP **200** döner, sonuç gövdededir. OTP penceresi 120 sn'dir.

### Komutlar

```
npm install
npm run dev            # geliştirme
npm run check          # typecheck + lint + format + i18n + contrast (CI'da YOK; push öncesi elle)
npm run build          # deploy workflow yalnızca install + build yapar; Vite type-check etmez
```

Node ≥ 22.22 (`.nvmrc`). Test script'i yok; bu bir ürün kararı.

## Eski GUI (`main`, referans `59f1689`)

- **Yapı:** `src/pages/<Ekran>` (Arbitrage, Hft, Tavan, Taban, Varant, TheoreticForm, OrderBook, OrderForm, OrderHistory, SelectStrategy, StrategySettings, CreatePanel, DockView, Login/Otp/ForgetPassword, FundTrackerSummaryView, VWAPSummaryView), `src/ApiService.ts`, `src/contexts`, `src/Functions`, `src/structs`.
- **Platformlar:** Web, Electron (`electron/`), Android/iOS (Capacitor, `android/`, `ios/`).
- **Backend:** Aynı REST ve WS uçlarını kullanır. `/v1/parseWarrantFile` hariç; Varant Toplu yok.
- **Kod okuma:** Branch değiştirmeden okunabilir:
  ```bash
  git show 59f1689:src/pages/<dosya>
  git ls-tree --name-only 59f1689 src/
  ```
- **Davranış farkları:** Yeni GUI eski GUI'nin birçok davranışını **bilerek** korur ya da **bilerek** değiştirir. Yeni GUI kodundaki "previous frontend …" yorumları bu kararları kaydeder. Bir farkın bug mı karar mı olduğunu anlamak için o yorumlara ve `AGENTS.md`'ye bak.
- **Eski branch:** `origin/eski_gui` aynı kod tabanının 2026-03 haliyle duruyor; `59f1689` tercih edilmelidir.

## Deploy

- `.github/workflows/algo_gui.yaml`, **elle tetiklenir**, müşteri listesi parametre olarak verilir.
- Branch → Docker imajı:
  - `development` → `mtrader-frontend-dev` (container `MTraderGuiDev`)
  - `preprod` → `mtrader-frontend-preprod`
  - `main` → `mtrader-frontend`
- Ayrıntı: [`00-genel/branch-ve-ortamlar.md`](../../00-genel/branch-ve-ortamlar.md#gui-dağıtımı-mtrader-trade-ui).
