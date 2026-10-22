---
kapsam: Yeni GUI'nin (mtrader-trade-ui development, app/) yapı ve davranış haritası; route'lar, workspace'ler, paneller ve state, her soru için hangi koda ve repo AGENTS.md'sinin hangi başlığına bakılacağı
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-22
durum: taslak
---

# Yeni GUI (`development`, `app/`): yapı haritası

Bu dosya bir harita. Ayrıntılı kurallar repodaki `AGENTS.md`'de (~1500 satır). Orayı bölüm adıyla kaynak gösteriyoruz (`AGENTS.md § Bölüm`), satır numarası vermiyoruz. Bu dosyada yalnızca AGENTS.md'de toplu hâlde bulunmayan yapı var: route ağacı, workspace tablosu, panel ve store listesi.

İlgili dosyalar:
- REST/WS/auth sözleşmesi: [backend-sozlesmesi.md](backend-sozlesmesi.md).
- Eski GUI: [eski-gui.md](eski-gui.md).
- Strateji mantığı: `20-stratejiler/*.md`.

## 1. Teknoloji yığını, build, çalıştırma

| Konu | Değer | Yer |
|------|-------|-----|
| UI | React 19, TypeScript; TS 7 (`@typescript/native`, `tsc`) ile TS 6 (`typescript` adı, eslint için) yan yana kurulu | `package.json`; `AGENTS.md § Environment and Commands` |
| Router | React Router 8, framework mode, `ssr: false` (SPA). Route'lar açıkça tanımlı, dosya tabanlı routing yok | `react-router.config.ts`, `app/routes.ts` |
| Build | Vite 8 + `@react-router/dev`. Çıktı `dist/` (`buildEnd`, `dist/client`'ı köke taşır, `dist/server`'ı siler). Dockerfile `dist/`'i nginx köküne kopyalar | `react-router.config.ts`, `vite.config.ts`, `Dockerfile` |
| State | Zustand 5. Yüksek frekanslı veri Zustand dışında, anahtar başına dinleyicili dış store'larda (§5) | `app/stores/` |
| Sunucu state'i | TanStack Query 5. Varsayılanlar: `retry:false`, `refetchOnWindowFocus:false`, `refetchOnReconnect:false` | `app/root.tsx` (`App`) |
| Panel düzeni | Dockview 8 (`dockview-react`). Popout belgesi `public/popout.html` | `app/routes/strategies/StrategyWorkspace.tsx` |
| Tablo | TanStack Table v9 | `app/components/ui/DataTable.tsx`, `tableTypes.ts`; `AGENTS.md § Tables` |
| Stil | Tailwind v4, semantik token'lar `app/global.css` | `AGENTS.md § UI, Styling, and Dockview`, `§ Color tokens` |
| Diğer | axios (REST), zod (form doğrulama, `app/validations/`), sonner (toast), react-select, react-tooltip, @dnd-kit | `package.json` |
| Node | `engines >=22.22.0`, `.nvmrc` = `22.23.1` | `package.json`, `.nvmrc` |
| Ortam değişkeni | `VITE_API_HOST`, `VITE_WS_HOST`. Prod imajı bunlar **olmadan** derlenir; boşsa sayfanın origin'ine düşer. Tek imaj bütün müşterilere gider | `app/lib/apiConfig.ts`, `.env.example` |

Komutlar: `npm run dev` (port 5173), `npm run build`, `npm run typecheck`, `npm run lint`, `npm run check` (typecheck, lint, format:check, `check:i18n`, `check:contrast`), `npm run knip`.

- **Test yok.** Ürün kararı; test framework'ü önerilmez (`AGENTS.md § Decisions and Boundaries`).
- **`npm run check` CI'da yok.** `check.yml` 2026-09-28'de eklenip kaldırıldı. `.github/workflows/` altında iki dosya var:
  - `algo_gui.yaml`: deploy. Elle tetiklenir (`workflow_dispatch`, müşteri listesi input). Yalnızca `npm install --legacy-peer-deps` ve `npm run build` çalıştırır. Vite type-check yapmaz.
  - `codex.yml`: PR'larda Codex review zorunluluğu. Kod kontrolü değildir.
- Branch → imaj eşlemesi: [README](README.md#deploy). Deploy dosyaları DevOps'a ait; agent bunları düzenlemez (`AGENTS.md § Decisions and Boundaries`).

## 2. Route ağacı ve guard'lar

Kaynak `app/routes.ts`. Kök layout `app/root.tsx`. Kök şunları kurar:
- `QueryClientProvider`
- `I18nProvider` (`initialNs: common, auth`)
- tema efekti, `Toaster`, global tooltip
- `ErrorBoundary`, 404 dahil (`RouteErrorPage`)

```
root.tsx
├─ _auth.tsx                 (layout; token varsa ve yol /passwordReset/ değilse → getSafeReturnPath(state.from))
│  ├─ index  _index.tsx      token var → /strategy-select, yok → /login
│  ├─ login                  login.tsx
│  ├─ otp                    otp.tsx (otpChallenge bellekte yoksa → /login)
│  ├─ forgot-password        forgot-password.tsx
│  └─ passwordReset/:username/:token   password-reset.tsx (yol sunucunun e-posta linkiyle sabit)
└─ _protected.tsx            (layout; token guard + global sorgular)
   ├─ strategy-select        strategy-select.tsx
   └─ _strategy.tsx          (layout; 6 soketin yaşam döngüsü, Sidebar, DockviewApiProvider)
      ├─ hft                 ┐
      ├─ arbitrage           │
      ├─ vwap                │
      ├─ max-price           │  hepsi aynı modül:
      ├─ min-price           │  routes/strategies/StrategyWorkspace.tsx
      ├─ theoretical-price   │  (ayrı route id'leriyle)
      ├─ warrant             │
      ├─ bulk-warrant        │
      ├─ fund-tracker        │
      └─ collective-orders   ┘
```

Guard davranışı:
- **Token kaynağı:** `getToken()` (`app/lib/storage.ts`). Önce `sessionStorage`, sonra `localStorage`'a bakar. "Beni hatırla" açıkken token `localStorage`'a yazılır.
- **`_protected`, token yoksa:** `/login`'e `replace` ile yönlendirir. `state.from` = mevcut yol (+ query). Hiçbir şey render etmez.
- **`_protected`, global sorgular:**
  - `strategy-select`'te yalnızca `allowedStrategies` bloklar.
  - Workspace'lerde beş sorgu bloklar: `allowedStrategies`, `instruments`, `instrumentsWithFutures`, `accounts`, `accountStrategies`.
  - Sorgular yüklenirken `GlobalLoading` görünür.
  - Hata olursa:
    - `unauthorized` → `expireSession`
    - workspace'te `forbidden` → `/strategy-select`
    - diğer hatalar → `ConnectionError` (tekrar dene, çıkış, strateji seçimine dön)
- **Oturum sonu:** axios interceptor 401 alınca `requestSessionExpiration()` çağırır (`app/api/client.ts`). `_protected`, `subscribeToSessionExpiration` ile bunu dinler. Oturumu temizler ve `/login`'e `reason: "session-expired"` ile gönderir. Mantık `app/lib/sessionLifecycle.ts`'te.
- **`getSafeReturnPath`:** Yalnızca `/` ile başlayan, `//`, `/login` ve `/otp` olmayan bir yolu kabul eder. Diğer her şey `/strategy-select`'e çevrilir.
- **Workspace yetkisi:** `StrategyWorkspace` mount olunca `getAllowedStrategies` listesinde `isStrategyAllowedByName` ile eşleşme arar. Eşleşme yoksa `/strategy-select`'e döner.
- **Strateji seçimi (`strategy-select.tsx`, `STRATEGIES`):** On kart var. `HFT_WARRANT_ADVANCED` kartı `hiddenUnlessAllowed`: yetki yoksa kart hiç görünmez. Kartın gideceği route `getRouteSegmentForStrategyKey` ile workspace config'inden çıkar.
- Auth/OTP/parola sıfırlama sözleşmesi: `AGENTS.md § Authentication and OTP`, `§ Password reset`; [backend-sozlesmesi.md](backend-sozlesmesi.md).

## 3. Workspace modeli (`app/lib/strategyWorkspace.ts`)

Workspace'e özel davranış `STRATEGY_WORKSPACE_CONFIGS`'te tanımlıdır. `StrategyWorkspace.tsx` bu config'i okur. Akış:
1. `getStrategyTypeFromPath(pathname)`: yol parçası tam eşitlikle eşleşir; eşleşmezse varsayılan `HFT`.
2. `getStrategyWorkspaceConfig`: bilinmeyen bir tip `HFT` config'ine düşer.
3. `buildSubscriptionSnapshot`, `subscriptionStore.panelSubscriptions`'tan bir abonelik anlık görüntüsü üretir. Yalnızca `strategyType === wireStrategyType` olan kayıtlar girer. Görüntü sıralı JSON anahtarıyla karşılaştırılır; değiştiyse `socketStore.resubscribeAll` çağrılır.
4. Soket kümesini `getWorkspaceSockets(config)` hesaplar. `StrategyWorkspace` bunu kendi effect'inde `setWorkspaceSockets` ile uygular.

`StrategyType` değerleri wire değeridir, değiştirilmez (`app/types/index.ts`): HFT 4, ARBITRAGE 6, VWAP 7, THEORETICAL_PRICE 8, MAX_PRICE 9, FUND_TRACKER 10, HFT_WARRANT 13, MIN_PRICE 14, HFT_WARRANT_ADVANCED 15. Toplu Emir'in `StrategyType`'ı yok; anahtarı `COLLECTIVE_ORDERS_WORKSPACE = "COLLECTIVE_ORDERS"`.

| Workspace | Route | `trackerComponent` | `commandTypes` | Soketler (order her yerde açık) | Abonelik enstrümanları | `unique_key` |
|-----------|-------|--------------------|----------------|----------------|------------------------|--------------|
| HFT (4) | `hft` | `hft_tracker_form` | 1, 3 | market, command | `instrumentId` | `inst_acc_sid_4` |
| Arbitraj (6) | `arbitrage` | `arbitrage_tracker_form` | 1 | market, command | `instrumentId` + `spotId` | `generateArbitrageUniqueKey` (`arbitrage/arbitragePayload.ts`) |
| VWAP (7) | `vwap` | `order_book` (tracker yok) | 1 | market, command | `instrumentId` | Taraf başına iki anahtar: `buildVwapUniqueKey` × `VWAP_SIDES` (`features/vwap/vwapIdentity.ts`) |
| Tavan (9) | `max-price` | `max_price_tracker_form` | 1, 3, 8 | market, command, **bounds** | `instrumentId` | `inst_acc_sid_9` |
| Taban (14) | `min-price` | `min_price_tracker_form` | 1, 3, 8 | market, command, **bounds** | `instrumentId` | `inst_acc_sid_14` |
| Teorik (8) | `theoretical-price` | `theoretical_price_tracker_form` | 1 (3 bilerek yok) | market, command, **equilibrium** | `instrumentId` | `inst_acc_sid_8` |
| Varant (13) | `warrant` | `warrant_tracker_form` | 1, 3 | market, command | `instrumentId` + `derivativeInstrumentIds` | `inst_acc_sid_13` |
| Varant Toplu (15) | `bulk-warrant` | `warrant_bulk_tracker_form` | 1 (3 bilerek yok; K/Z için commandType 5 özeti) | market, command | `instrumentId` + `derivativeInstrumentIds` | `inst_acc_sid_15` |
| Fon Takibi (10) | `fund-tracker` | `order_book` (tracker yok) | 1, 3 | market, command | `instrumentId` | `inst_acc_sid_10` |
| Toplu Emir | `collective-orders` | `collective_order` (`initialPanel`) | — | **yalnızca order** (`coreSockets: {market:false, command:false}`) | — | — |

Tabloda `inst_acc_sid_N` = `${instrumentId}_${account}_${strategyIdentifier}_${StrategyType}`. Hesap kimliğin parçasıdır: `AGENTS.md § A strategy's account is part of its identity`.

`allowedComponents` (dockview component id'leri):

| Workspace | Ortak paneller dışında izinli |
|-----------|-------------------------------|
| HFT | `hft_tracker_form`, `hft_summary_view`, `strategy_passive_orders` |
| Arbitraj | `arbitrage_tracker_form`, `arbitrage_summary_view`, `arbitrage_passive_orders` |
| VWAP | `vwap_summary_view` |
| Tavan / Taban | `max_price_*` / `min_price_*` (`_tracker_form`, `_summary_view`), `strategy_passive_orders` |
| Teorik | `theoretical_price_tracker_form`. Özet ve pasif emir paneli yok; eski sistemle aynı kapsam |
| Varant / Varant Toplu | `warrant_*` / `warrant_bulk_*` (`_tracker_form`, `_summary_view`), `strategy_passive_orders` |
| Fon Takibi | `fund_tracker_summary_view` ("Paketler") |
| Toplu Emir | yalnızca `collective_order`, `order_history`, `order_book`. `welcome` ve `send_order` yok |

Ortak paneller (Toplu Emir hariç): `welcome`, `order_book`, `order_history`, `send_order`.

Config bayrakları:
- `usesBoundsLot`: bounds soketi açılır. Tavan Lot / Taban Lot sütunlarını besler.
- `usesEquilibrium`: equilibrium soketi açılır. Teorik tracker'ın canlı sütunlarını besler.
- `coreSockets`: market/command açık mı. Varsayılan ikisi de açık.
- `trackerUsesPanelStrategies`: HFT, Tavan, Taban, Teorik, Varant ve Varant Toplu'da açık. Layout kaydında `params.strategies` canlı aboneliklerden tazelenir.
- `initialPanel`: yalnızca Toplu Emir'de var. Diğer workspace'ler boş `welcome` paneliyle açılır.

`trackerComponent` ilk kez eklendiğinde `welcome` paneli kapanır. VWAP ve Fon Takibi'nde tracker olmadığı için bu rolü `order_book` üstlenir.

**Önek çakışması (`matchesStrategyKey`):** Backend, `getAllowedStrategies` cevabında strateji adlarını önekle döndürür ve bu adlar iç içe geçer: `HFT_WARRANT_ADVANCED` ⊃ `HFT_WARRANT` ⊃ `HFT`. `matchesStrategyKey(name, key)` için `name.startsWith(key)` yetmez; daha uzun bir config anahtarı da eşleşiyorsa kayıt o anahtarın sayılır. Böylece yalnızca Varant yetkisi olan kullanıcıya HFT workspace'i açık görünmez. Eski GUI bunu `if` sırasıyla çözüyordu. Ayrıca bkz. `AGENTS.md § Project Overview`.

❓ doğrulanmadı: Toplu Emir kartının yetkisi, backend'in `getAllowedStrategies` cevabında `COLLECTIVE_ORDERS` ile başlayan bir ad döndürmesine bağlı. Backend tarafındaki ad kontrol edilmedi.

Workspace'in üç durumu `StrategyWorkspace.tsx`'te (`SOCKET_READY_TIMEOUT_MS = 15_000`):
1. **İlk bağlantı:** tam ekran `GlobalLoading`. 15 sn dolarsa `ConnectionError` gösterilir. Soketler kapatılmaz, arka planda denemeye devam eder.
2. **Hazır.**
3. **Kopuk** (`hasBeenReady && !isWorkspaceReady`): engellemeyen `ConnectionBanner` görünür, zaman aşımı yok.

Hazır olma koşulu yalnızca workspace'in kullandığı çekirdek soketlere bakar (`getRequiredCoreSockets`). Ayrıntı: `AGENTS.md § WebSocket and Performance Constraints`, `§ Sockets heal themselves; nothing may stop that`.

## 4. Panel kataloğu (`app/components/dockview/`)

Panel bileşenleri `StrategyWorkspace.tsx` içindeki `Components` haritasında `React.lazy` ile yüklenir. Her panel `renderPanel` ile üç sarmalayıcıya girer:
- `PanelErrorBoundary`: render hatasını yalnızca o panelde gösterir.
- `PanelVisibilityProvider` (`app/context/PanelVisibilityContext.tsx`): arka plandaki panelin dış store aboneliklerini keser.
- `Suspense`.

Panel açma isteği `usePanelStore.addPanel` ile gelir. Workspace bu isteği şöyle işler:
1. `isComponentAllowedForStrategy` ile filtreler.
2. Aynı id'li panel zaten varsa parametrelerini günceller ve onu öne getirir.
3. **Aynı başlıklı tracker paneli ikinci kez açılmaz** (`panelAlreadyOpen` uyarısı).

Bu kuralı koruyan yardımcılar:
- `lib/openSingletonPanel.ts`: özet, emir geçmişi ve pasif emir panelleri için tekil panel açar.
- `lib/openOrderBookPanel.ts`: emir defteri panel id'si `orderbook_<symbol>_<account>_<strategyIdentifier>`.
- `orderbook/useSendOrderLauncher.ts`: emir gönderme paneli, id `send_order_<ts>`, başlıksız popout olarak açılır.

| Component id | Dosya | İş | Veri kaynağı |
|--------------|-------|----|--------------|
| `welcome` | `WelcomePanel.tsx` | Boş başlangıç paneli | — |
| `hft_tracker_form` | `HftTrackerForm.tsx` + `hft/`, `HftTrackerCells.tsx`, `HftSettingsSections.tsx` | HFT tracker tablosu, satır içi ayar, toplu ayar, endeksten toplu ekleme | `strategyDataStore`, `marketDataStore`, `balanceDataStore`, `subscriptionStore`, `activeHftStore` (`hft/useHftTrackerStrategies.ts`); REST `getPanels`, `subscribeToOrderbook`, `subscribeToIndice`, `setStrategyCommands`, `setPanel` |
| `arbitrage_tracker_form` | `ArbitrageTrackerForm.tsx` + `arbitrage/` | Arbitraj paketleri, toplu ayar, paket ekleme | `strategyDataStore`, `socketStore` (aktivite), `arbitrage/useArbitrageSubscriptions.ts`; `features/arbitrage/` (Excel indir/yükle) |
| `max_price_tracker_form` / `min_price_tracker_form` | `MaxPriceTrackerForm.tsx` / `MinPriceTrackerForm.tsx` + `max-price/`, `min-price/` | Tavan / Taban tracker'ı: canlı durum renkleri, eşik filtresi, stability penceresi | `maxPriceStateStore` (Taban da bu store'u kullanır), `boundsDataStore`, `marketDataStore`, `strategyDataStore`; `useHftTrackerStrategies` |
| `theoretical_price_tracker_form` | `TheoreticalPriceTrackerForm.tsx` + `theoretical-price/` | Teorik fiyat tracker'ı. Emir onayı `ConfirmTheoreticalOrderModal` | `equilibriumDataStore`, `strategyDataStore`; REST `sendOrders` |
| `warrant_tracker_form` | `WarrantTrackerForm.tsx` + `warrant/` | Dayanak satırı + iç içe varant satırları | `strategyDataStore` (`Derivative_Orders`), `marketDataStore`; `useDerivativesByUnderlying`, `useIndiceInstruments` |
| `warrant_bulk_tracker_form` | `WarrantBulkTrackerForm.tsx` + `warrant-bulk/` | Varant Toplu: yoğun tablo, mini emir defteri, olay toast'ları, dosya yükleme | `strategyDataStore`, `socketStore.summaryData` (commandType 5), `orderSnapshotStore` (BuySent/ReplaceSent); REST `parseWarrantFile` |
| `hft_summary_view`, `arbitrage_summary_view`, `max_price_summary_view`, `min_price_summary_view`, `warrant_summary_view`, `warrant_bulk_summary_view` | `*SummaryView.tsx` | Hesap bazlı özet / K-Z | `socketStore.summaryData` (`requestHftSummary`, `requestArbitrageSummary`, `requestPriceLimitSummary`). Tavan özeti ayrıca `watchMaxPriceStates` + `maxPriceStateStore` kullanır |
| `vwap_summary_view` | `VwapSummaryView.tsx` | VWAP özet satırları | `vwapSummaryStore` (kuşak / `generationKey` mantığı), `requestVwapSummary` |
| `fund_tracker_summary_view` | `FundTrackerSummaryView.tsx` + `fund-tracker/` | "Paketler": paket satırı ve altında spot emirleri | `socketStore.packageActivityData`; BYF teorik fiyatı `byfTheoreticalPriceStore` |
| `order_book` | `OrderBook.tsx` + `orderbook/` | Derinlik, kendi emir işaretleri, sürükle-bırak, sağ tık menüsü. Sol altta `StrategyControlsOverlay` (VWAP / Fon Takibi overlay'leri ayrı) | Paylaşılan `ItchSocket` (`registerBook`), `getOrdersFromLevel`, `orderBookPreferencesStore`, `subscriptionStore` |
| `order_history` | `OrderHistory.tsx` + `order-history/` | Emir geçmişi, filtreler, sütun ayarı, Varant Toplu için "Dayanak Bid/Ask" | `OrderSocket.registerSubscription` (`ORDER_SUBSCRIBE_STRATEGY_TYPES`, `lib/tradingConstants.ts`), `orderSnapshotStore` |
| `send_order` | `SendOrderPanel.tsx` + `send-order/` | Manuel emir. Layout'a **hiç girmez** (`TRANSIENT_PANEL_COMPONENTS`, `hooks/useLayoutManager.ts`) | REST `sendOrders` |
| `strategy_passive_orders` | `StrategyPassiveOrders.tsx` + `passive-orders/` | Strateji tipine göre pasif emirler | **Kendi** WebSocket'i: `/ws/v1/passive-orders/start`. `socketStore` dışında, kendi reconnect'iyle |
| `arbitrage_passive_orders` | `arbitrage/PassiveOrders.tsx` | Arbitrajın dayanak bacağında motorun taşıdığı pasif emirler | `socketStore.passiveOrderData` (komut soketi). Tracker yoksa veri gelmez; bilinen ve görünür kılınmış bir boşluk |
| `collective_order` | `CollectiveOrderPanel.tsx` + `collective-order/` | Toplu Emir: Sabah / Açılış / Akşam sekmeleri, toplu aktif/pasif/sil. Sekme kapatılamaz | `collective-order/useCollectiveOrderStream.ts`, REST `sendOrders`, `instrumentStore` |

Panelin dışındaki parçalar:
- `RightControls.tsx`: grup başlığındaki aksiyonlar.
- `panelToolbarActions.tsx`: toolbar; yalnızca görünüm tercihlerini taşır.
- `components/layout/Sidebar.tsx`: panel ekleme (`CreatePanelModal`, `getPanels` ile kayıtlı panel adlarını listeler), özet ve pasif emir kısayolları, layout kaydet/seç (`LayoutSelector`), hesap geneli iptal, ses ve bağlantı alarmı (`sidebar/useSidebarSoundAlarms.ts`), çıkış.
- `components/modals/`: strateji ekleme modalları (`Add*StrategyModal`) ve ayar modalları (`*SettingsModal`; Teorik'te yok).

## 5. State yönetimi

Kural özeti:
- REST state'i React Query'de tutulur.
- Düşük frekanslı istemci ve soket state'i Zustand'da tutulur.
- Tick verisi, anahtar başına `useSyncExternalStore` dinleyicili düz modül store'larında tutulur. Tek bir Zustand Map'ine taşınmaz.
- Ayrıntı: `AGENTS.md § State and Data Access`, `§ WebSocket and Performance Constraints`.

### 5.1 Yüksek frekanslı dış store'lar

Hepsine **`socketStore` yazar**. Tamponlama aralıkları: market, bounds ve equilibrium için `MARKET_DATA_THROTTLE = 40` ms (~25 Hz), komut verisi için `COMMAND_DATA_THROTTLE = 33` ms. Abonelik kapsamı değişince eski veri budanır (`retainInstruments` / `retainKeys`).

| Store | Anahtar | Tutar | Kaynak soket | Okuyan hook |
|-------|---------|-------|--------------|-------------|
| `marketDataStore` | instrumentId | best bid/ask, trend, `lastPrice` | market `/ws/v1/best` | `useMarketEntry` |
| `strategyDataStore` | unique_key | strateji ayar snapshot'ı (`WsStrategyResponse`), global sürüm sayacı; `patch` / `revertPatch` (optimistik) | command | `useStrategyEntry`, `useStrategyEntryWhenVisible`, `useStrategyDataVersion` |
| `balanceDataStore` | unique_key | bakiye / pozisyon (commandType 3) | command | `useBalanceEntry` |
| `maxPriceStateStore` | unique_key (`…_9` ve `…_14`) | Tavan/Taban canlı durumu (`Command_Type_MaxPriceStateResponse`). Optimistik `patch`'i tracker'lar ve `useOrderBookStrategyControls` da yazar | command | `useMaxPriceStateEntry` |
| `boundsDataStore` | instrumentId | `maxAskLot`, `minBidLot`, tavan/taban fiyatı | bounds `/ws/v1/bounds/start` | `useBoundsEntry` |
| `equilibriumDataStore` | instrumentId | denge fiyatı / miktar + istemci `updatedAt` | equilibrium `/ws/v1/equilibrium/start` | `useEquilibriumEntry` |
| `byfTheoreticalPriceStore` | unique_key (`…_10`) | BYF teorik fiyatı | command | `useByfTheoreticalPrice` |
| `vwapSummaryStore` | VWAP kimliği | VWAP özet satırları. Kuşak (`setGeneration`) değişince eski satırlar atılır, flush 33 ms | command | `useVwapSummaryEntries`, `useVwapSummaryEntry` |
| `orderSnapshotStore` | OUCH token | Varant Toplu `BuySent` / `ReplaceSent` anında dayanak kitabı. Yalnızca bellekte, en fazla 5000 kayıt; yenilemede kaybolur | command (`recordOrderSnapshot`) | `useOrderSnapshot` (`order-history/UnderlyingSnapshotCell.tsx`) |

### 5.2 Zustand store'ları

| Store | Tutar | Kalıcılık | Yazan → okuyan |
|-------|-------|-----------|----------------|
| `socketStore` | Altı soket örneği, durumları, URL'ler, `workspaceSockets`. Düşük frekanslı Map'ler (`summaryData`, `activitiesData`, `packageActivityData`, `passiveOrderData`), aktif abonelik kümeleri, bağlantı alarmı | yok | `_strategy.tsx` (init/connect/pause/cleanup), `StrategyWorkspace` (`setWorkspaceSockets`, `resubscribeAll`) → paneller |
| `subscriptionStore` | `panelSubscriptions: Map<panelId, PanelSubscription[]>` | yok | Tracker'lar, `OrderBook`, `useLayoutManager` → `buildSubscriptionSnapshot` |
| `activeHftStore` | Panel başına strateji listesi; `incompletePanels` (eksik geri yüklenmiş panel listesi DB'ye yazılmaz) | yok | `hft/useHftTrackerStrategies.ts` (HFT, Tavan, Taban) → Sidebar layout kaydı |
| `panelStore` | `panelToAdd` (tek elemanlık panel açma kuyruğu) | yok | Sidebar, modallar, hücreler → `StrategyWorkspace` |
| `layoutStore` | Kayıtlı layout'lar, workspace başına `activeLayoutIdsByStrategy` | `localStorage` `layout-storage` | `useLayoutManager`, `SaveLayoutModal`, `LayoutSelector` |
| `instrumentStore` | Enstrüman kataloğu; id/sembol indeksleri; `tickSize` sayıya çevrilir; `spotInstruments` | yok | `api/queries/useInstruments.ts` → fiyat ölçeği, hücreler |
| `futuresStore` | `getAllInstrumentsWithFutures` sonucu | yok | `useInstrumentsWithFutures` → arbitraj |
| `tablePreferencesStore` | Sütun sırası / görünürlük / genişlik; anahtar `"<strategyType>:<panelAdı>"`; eski `table:*` anahtarlarından göç | `localStorage` `table-preferences-storage` | `DataTable` tüketicileri |
| `tableRuntimeStore` | Tablo scroll offset'leri | yok | `useDockviewTableScrollRestore` |
| `orderBookPreferencesStore` | `compactLots` (varsayılan açık) | `localStorage` `orderBook.compactLots` | Emir defterleri |
| `themeStore` | `light` / `dark` | `localStorage` `theme-storage` | `root.tsx`, Dockview teması |
| `tradingSoundStore` | İşlem sesleri, bağlantı alarmı çalma / erteleme | `localStorage` `soundEnabled` (yalnızca açık/kapalı tercihi) | `useCentralOrderSubscription`, `useSidebarSoundAlarms` |

Diğer tarayıcı depoları:
- Token: `sessionStorage` / `localStorage` (`lib/storage.ts`).
- Kaydedilmemiş oturum düzeni: `sessionStorage` `mtrader.workspace-session.v1.<workspace>` (`lib/sessionLayout.ts`).
- Dil: `localStorage` `locale` (`i18n/config.ts`).
- Stability penceresi: `tavan_stability_ms` / `taban_stability_ms` (`strategy/stabilityWindow.ts`).

### 5.3 React Query anahtarları (`app/api/queries/`)

| queryKey | Uç | staleTime | Kim tetikler |
|----------|----|-----------|--------------|
| `["allowedStrategies"]` | `/v1/getAllowedStrategies` | 30 dk | `_protected`, `StrategyWorkspace` |
| `["instruments"]` | `/v1/getInstruments` | 1 sa | `_protected` (workspace'te) → `instrumentStore` |
| `["instrumentsWithFutures"]` | `/v1/getAllInstrumentsWithFutures` | 1 sa | `_protected` → `futuresStore` |
| `["accounts"]` | `/v1/getAccounts` | 30 dk | `_protected`, özetler, Sidebar |
| `["accountStrategies"]` | `/v1/getAllAccountStrategies` | 5 dk | `_protected`. VWAP / BYF ekleme modalları invalidate eder |
| `["panels", strategyType]` | `/v1/getPanels` | 5 sn | `panelsQueryOptions`; tracker'lar `fetchQuery` ile çağırır (aynı anda açılan N panel tek isteğe iner) |
| `["indices"]` | `/v1/getIndices` | 1 sa | Tavan / Taban / HFT endeks ekleme |
| `["indiceInstruments", id]` | `/v1/getIndiceInstruments` | 1 sa | Varant (Toplu) ekleme |
| `["derivativesByUnderlying", id]` | `/v1/getDerivativesByUnderlying` | 1 sa | Varant ayar modalı |

Mutation'lar (`app/api/mutations/`):
- `setStrategyCommands`, `subscribeToOrderbook`, `subscribeToIndice` (timeout 5 dk)
- `setPanel` (timeout 120 sn)
- `sendOrders` (emir ve replace), `setAccountStrategy`, `parseWarrantFile`, arbitraj uçları
- auth uçları

Bu uçların sözleşmesi (alan adları, ölçek, string/number lehçesi): [backend-sozlesmesi.md](backend-sozlesmesi.md).

## 6. Ortak UI kuralları: nereye bakılır

| Soru | Kod | AGENTS.md |
|------|-----|-----------|
| Raw fiyat ↔ TL, bölen, giriş basamağı | `lib/priceScale.ts` (`getPriceScale`, `rawToDisplayPrice`, `displayToRawPrice`, `formatRawPrice`, `PRICE_ENTRY_DECIMALS = 2`), `lib/instrumentPriceScale.ts`, `hooks/usePriceStep.ts` | `§ Price Scale` (bilinçli sabit ×1000'ler: `Theo_Price`, varant `userPrice`, `Arb_Total_Profit`) |
| Fiyat makullük kapısı (emir öncesi) | `lib/priceSanity.ts` (`PRICE_SANITY_MAX_RATIO = 10`), `hooks/usePriceSanityGate.ts`, `ConfirmPriceSanityModal` | `§ Strategy Architecture` |
| Sayı girişi (ondalık ayraç, yapıştırma, sınır) | `lib/numberField.ts`. Doğrulama hatasının ne zaman gösterileceği (blur veya submit sonrası): `hooks/useFieldReveal.ts` | — |
| Satır içi ayar düzenleme | `strategy/EditableStrategySettingCell.tsx` (Tavan, Taban, Varant), `hft/HftSettingCell.tsx`, `hft/EditableCell.tsx`, `strategy/strategySettingEditor.ts` | `§ Strategy Architecture` (modalla aynı payload builder, `confirmSave`, `revertPatch`) |
| Toplu ayar (çoklu seçim) | `strategy/bulkSettings.ts` (`splitCommonAndMixed`, `selectBulkUpdates`, `readStrategyField`), `modals/BulkSettingsConfirm.tsx`. Kullananlar: HFT, Arbitraj, Tavan, Taban | — |
| `extraFields` ve `get<X>Field` okuyucuları | Strateji klasörlerindeki `*Settings.ts` / `*Payload.ts` | `§ Strategy Architecture` |
| Çalışan satırı üstte tutma, eşik filtresi, stability | `strategy/pinRunningRows.ts`, `ColumnThresholdFilter.tsx`, `useStabilityWatcher.ts`, `stabilityWindow.ts`, `ui/useStickyRowOrder.ts` | `§ MAX_PRICE and MIN_PRICE` |
| Panel düzeni: dockview JSON | `hooks/useLayoutManager.ts` (`loadLayout`, `restoreSnapshot`, `TRANSIENT_PANEL_COMPONENTS`), `hooks/useSessionLayoutAutosave.ts`, `lib/sessionLayout.ts`, `stores/layoutStore.ts`. Geri yükleme önceliği: sessionStorage anlık görüntüsü → aktif kayıtlı layout → başlangıç paneli | `§ UI, Styling, and Dockview` |
| Panel stratejileri: DB (`Strategy_Panels`) | `lib/strategyPanelPersistence.ts` (`persistPanelStrategies`, `persistArbitragePanelItems`; her zaman `isNew: true`, yani sil ve yeniden yaz), `api/mutations/setPanel.ts`, `api/queries/panels.ts`, `lib/indiceGroupManifest.ts`; Sidebar `onSaveLayout` | — |
| Hesap seçimi, `DE-` / spot | `lib/tradingAccounts.ts` (`accountForOrderBook`, `isSpotStrategyAccount`) | `§ A strategy's account is part of its identity` |
| Wire sabitleri (taraf, emir tipi, abone tip listesi) | `lib/tradingConstants.ts` | `§ Trading and Logging Rules` |
| Hata bildirimi | `lib/notifyApiError.ts`, `lib/backendErrors.ts`, `lib/logger.ts` (`notifications`, `createLogger`) | `§ Trading and Logging Rules` |
| i18n | `i18n/I18nProvider.tsx` (`useT(ns)`, namespace lazy yüklenir), `locales/{tr,en}/*.json` (16 namespace), `scripts/check-i18n.mjs` | `§ Internationalization` |
| Renk, ikon buton, rozet, tooltip, Enter ile onay, CSS katmanları | `app/global.css`, `components/ui/` | `§ Color tokens`, `§ Icon buttons`, `§ Badges`, `§ Tooltips and accessible names`, `§ Enter to confirm`, `§ CSS cascade layers` |
| Prop'a bağlı state (render sırasında set) | `hooks/useDepsChanged.ts`, `hooks/useOpenTransition.ts` | `§ State that follows a prop` |

## 7. Eski GUI'den bilerek korunan / değiştirilen davranışlar

Bu bilgi kod yorumlarında durur. Yorumlar Türkçe; arama kalıbı `eski (uygulama|arayüz|sistem|GUI|frontend)`, `b0474c3`'te ~117 eşleşme var. AGENTS.md bu yorumları "load-bearing" sayar ve silinmemeleri gerekir (`§ Implementation Guidelines`). Eski ekranların kendisi: [eski-gui.md](eski-gui.md). Aşağıda yorum başına bir satır var; ayrıntı yorumun yanındaki kodda.

**Korunan:**
- Toplu Emir'de bağlantı göstergesi ve alarm yalnızca order soketine bakar (`lib/strategyWorkspace.ts`, `getRequiredCoreSockets`).
- Teorik'te özet ve pasif emir paneli yok. Strateji kimliği sabit `"teo"` (`theoretical-price/theoreticalPricePayload.ts`, `AddTheoreticalStrategyModal.tsx`).
- Fon Takibi'nde tracker yok; strateji order book'tan yönetilir. Abonelik commandType'ları 1, 3. BYF alım/satım lot kutuları bilerek etkisiz (`AGENTS.md § FUND_TRACKER dead lot boxes`). Fiyatlar TL×100 / ×1000 (`features/fund-tracker/fundTrackerContract.ts`).
- Varant Toplu bakiye (3) istemez. Toplu kayıt güncellenen stratejileri durdurur (`WarrantBulkBatchSettingsModal.tsx`, `WarrantBulkTrackerForm.tsx`). Yetki yoksa kartı gizlidir.
- Tavan/Taban'da ayarı gelmemiş satıra toplu işlem uygulanmaz; satır renk önceliği ve brüt takas opaklığı aynıdır (`max-price/`, `min-price/` `*LiveState.ts`, `*TrackerForm.tsx`). Stability `localStorage` anahtarları ve 1 sn varsayılanı aynıdır (`strategy/stabilityWindow.ts`).
- `setPanel` her zaman `isNew: true` ile gider (`lib/strategyPanelPersistence.ts`).
- Fiyat giriş kutuları 2 basamak kabul eder; `decimalCount` yalnızca böleni seçer (`lib/priceScale.ts`).
- Emir geçmişinde OUCH kimliği ham, adet ayraçsız; gecikme sütunları aynı (`order-history/orderHistoryUtils.ts`, `orderHistoryColumns.tsx`).
- `financialProduct` yoksa `F_` önek kuralı (`lib/tradingAccounts.ts`).
- Hesap geneli iptal Arbitraj/VWAP/BYF'de gösterilmez. Eski GUI de aynı isteği yolluyordu ve hiç çalışmıyordu; regresyon değil (`lib/cancelAllOrdersCommand.ts`).
- Panelin endeks grubu kaydı (`lib/indiceGroupManifest.ts`). HFT'de satır eşleştirmesi `instrumentId` üzerinden (`hft/useHftTrackerStrategies.ts`).

**Değiştirilen (eski davranış bug sayıldı):**
- Login'de `status:false` + `isOtpEnabled:true` kullanıcıyı `/otp`'ye götürür. Eski GUI login ekranında kilitliyordu (`api/mutations/useLogin.ts`).
- OTP challenge (parola dahil) yalnızca bellekte. Eski GUI düz metin olarak `sessionStorage`'a yazıyordu (`lib/otpChallenge.ts`). Parola sıfırlama token'ı da hiçbir depoya yazılmaz (`routes/password-reset.tsx`).
- `/otp`'de erken `return` hook sırasını bozup ekranı çökertiyordu; düzeltildi (`routes/otp.tsx`).
- Strateji yetkisinin önekle eşleşmesi artık sıradan bağımsız (`matchesStrategyKey`).
- `setPanel` ve `subscribeToIndice` eski GUI'de zaman aşımsızdı. Şimdi 120 sn ve 5 dk (`api/mutations/setPanel.ts`, `subscribeToIndice.ts`).
- Aynı adlı tracker paneli ikinci kez açılamaz; iki kopya birbirinin DB satırlarını siliyordu (`StrategyWorkspace.tsx`).
- `setPanel` gövdesinde `strategyName` artık gönderilmiyor; zaten hiç kaydedilmiyordu (`lib/strategyPanelPersistence.ts`).
- Varant `criteriaValue` / `toleranceCount` varsayılanı 0'dan 1'e çıktı. Motor 0'ı reddediyor ve komut sessizce düşüyordu (`warrant/warrantPayload.ts`, `warrantSettings.ts`).
- Varant özetinde `toleranceCount` alanı "döngü sayısı" olarak gösterilir. Eski GUI "Tolerans" diyordu (`warrant/warrantSummary.ts`).
- Teorik komutunda `strategyType` 4'ten 8'e, `Account` alanı hesap adından strateji kimliğine düzeltildi (`theoretical-price/theoreticalPricePayload.ts`).
- Taban Lot `maxAskLot` yerine `minBidLot` okur (`min-price/MinPriceTrackerCells.tsx`). Taban özetinden gerçek değer göstermeyen iki sütun kaldırıldı (`MinPriceSummaryView.tsx`).
- Tavan `Has_Passive_Sell_Order` alan adı düzeltildi; kırmızı vurgu artık tetikleniyor (`api/socket/CommandSocket.ts`).
- Emir geçmişi abone tip listesine 12 (`HFT_User`, "Serbest" elle emir) eklendi (`lib/tradingConstants.ts`).
- Stability filtresi bekleyen geçişi pencere dolunca zamanlayıcıyla uygular. Eski GUI bir sonraki mesajı bekliyordu (`strategy/useStabilityWatcher.ts`).
- Yeni GUI, workspace'ler arasında `hasBeenReady` sıfırlar ve 15 sn sonra soketleri kapatmaz (`AGENTS.md § Sockets heal themselves; nothing may stop that`). ❓ doğrulanmadı: eski GUI'de aynı yolun bulunup bulunmadığı.

## 8. Repo `AGENTS.md` başlık haritası

| Başlık | Cevapladığı soru |
|--------|------------------|
| Project Overview | Hangi workspace'ler var, panel kapsamı neden eşit değil, önek eşleşmesi |
| Environment and Commands | Node / TS 7+6 düzeni, komutlar, test ve CI yokluğu, LF satır sonu |
| Repository Structure | `app/` klasörleri, `@/*` alias |
| External Reference Points → Backend / Strategy engines / Previous GUI | Wire sözleşmesi için trade-data-app'te nereye bakılır; REST protojson ve WS Go-json lehçesi; C++ motor dosyaları; eski GUI `59f1689` nasıl okunur |
| Implementation Guidelines | Değişiklik disiplini, "eski GUI" yorumlarının korunması |
| Authentication and OTP → Password reset | Login HTTP 200 semantiği, OTP challenge, sıfırlama linkinin yolu |
| Strategy Architecture | Config güdümlü workspace; satır içi ayar, `extraFields`, `revertPatch`; komut yarışlarının kabulü; Varant iç içe satır ve iki fiyat ölçeği |
| → HFT chase type and its hidden fields | `Hft_Type`'a göre gizlenen alanlar |
| → HFT_WARRANT_ADVANCED (Varant Toplu) | Varant Toplu sözleşmesi, yoğun tablo, mini book, dosya yükleme, eksik gateway case'leri |
| → FUND_TRACKER dead lot boxes | BYF lot kutularının neden etkisiz olduğu |
| → MAX_PRICE and MIN_PRICE | İkiz görünen iki stratejinin farkları; neden birleştirilmedikleri |
| WebSocket and Performance Constraints | Altı soket, workspace başına soket kümesi, hazır olma kapısı, dış store kuralları |
| → Sockets heal themselves… | Backoff, `pauseSockets` yasağı, half-open boşluğu |
| → The order socket owns its subscription | `registerSubscription`, birleşik filtre, replay sonrası reset |
| → The itch socket is shared | Tek itch bağlantısı, `registerBook`, Type 2/8/9 kuralları, Refresh |
| → Replayed order history… | `isReplay`, ses / bildirimlerin replay'i yok sayması |
| State and Data Access → State that follows a prop | Query / Zustand / dış store ayrımı; render sırasında set |
| UI, Styling, and Dockview (+ Color tokens, Icon buttons, Badges, Tooltips…, Enter to confirm, CSS cascade layers, Tables) | Popout, Popover, panel scroll düzeni, send_order'ın layout dışında kalması, tema token'ları, tablo kabuğu |
| Internationalization | `useT`, iki dil eşliği, `check:i18n` |
| Price Scale | Bölen, bilinçli ×1000'ler, arbitrajın ÷1000 referansı, BYF istisnası |
| Trading and Logging Rules → A strategy's account is part of its identity | Logger'ın prod'da sessiz olması, `notifyApiError`, zaman aşımına uğrayan emrin gönderilmiş olabilmesi; strateji hesabı ↔ emir hesabı |
| Decisions and Boundaries | Ürün kararları (HTTP 80, beni hatırla), kapsam dışı işler (deploy, backend), kabul edilen riskler, reddedilen işler (test, CI, yeniden yapılandırma) |
| Verification / Documentation | Değişiklik türüne göre kontrol; AGENTS.md'ye bölümle atıf |

## Şüpheli

- **Layout kaydı her tracker'ı DB'ye yazmıyor.**
  - `Sidebar.tsx` `onSaveLayout`, `setPanel` adımını yalnızca HFT, Arbitraj, Tavan ve Taban'da çalıştırır (`HFT_LIKE_TRACKER_TYPES` = HFT, Tavan, Taban, + `arbitrage_tracker_form`).
  - Varant, Varant Toplu ve Teorik tracker'ları `persistPanelStrategies`'i yalnızca kendi ekleme/silme akışlarında çağırır.
  - Yorumdaki gerekçeye göre, `setPanel`'i düşmüş bir toplu ekleme bu üç workspace'te layout kaydıyla onarılmaz.
  - ❓ doğrulanmadı: kasıtlı mı, eksik mi.
- **Satır zemin renkleri ham Tailwind palet sınıfı kullanıyor.**
  - Örnekler: `bg-red-600/30`, `bg-purple-500/25`, `bg-green-500/40`. Dosyalar: `max-price/maxPriceLiveState.ts`, `min-price/minPriceLiveState.ts`, `warrant/warrantLiveState.ts`, `theoretical-price/theoreticalPriceLiveState.ts`, `HftTrackerForm.tsx`, `orderbook/StrategyControlsOverlay.tsx`, `order-history/orderHistoryUtils.ts`.
  - `AGENTS.md § Color tokens` "ham palet sınıfları kaldırıldı, geri getirmeyin" diyor; tablo satır durumu zeminlerini ayrıca anmıyor.
  - ❓ doğrulanmadı: istisna mı, kalıntı mı.
- **Deploy workflow AGENTS.md ve `.nvmrc` ile uyumsuz.**
  - `algo_gui.yaml` hâlâ `npm install --legacy-peer-deps` kullanıyor. AGENTS.md artık gerekmediğini, `npm ci`'nin temiz çözdüğünü söylüyor.
  - `setup-node` `node-version: 22` (yüzen major). `.nvmrc` ise `22.23.1`.
  - Dosya DevOps kapsamında. İş olarak not edildi.
- **Arbitraj pasif emir paneli tracker'sız açılırsa boş kalır** (`arbitrage/PassiveOrders.tsx`). Kasıtlı: maliyet nedeniyle kapatılmadı, ekranda "önce takip panelini aç" der. Bilgi için.
- **Bilinmeyen yol HFT'ye düşer.** `getStrategyTypeFromPath` ve `getStrategyWorkspaceConfig`, eşleşmeyen yol veya tip için HFT döndürür. Route ağacı yalnızca tanımlı on yolu kabul ettiği için bugün zararsız. Yeni workspace eklenirken üç yer birlikte güncellenmeli: `routes.ts`, `STRATEGY_WORKSPACE_CONFIGS` ve `getStrategyTypeFromPath`'teki `if` zinciri.
- **Token guard reaktif değil.** `_protected` token'ı render sırasında `getToken()` ile okur. Başka sekmede yapılan çıkış ancak ilk 401'de fark edilir. ❓ doğrulanmadı: pratik etkisi. AGENTS.md "her makinede tek operatör" kararını kaydediyor.
- **Zaman aşımına uğrayan emir gönderilmiş olabilir** (axios 10 sn; `sendOrders` ve "Pozisyon Ekle" bu süreyi ezmez). Bilinen ve kabul edilmiş durum: `AGENTS.md § Trading and Logging Rules`.
