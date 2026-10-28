---
kapsam: Eski GUI (mtrader-trade-ui main, src/) — prod'daki ekranların nasıl çalıştığı, ne gönderdiği, nerede durum tuttuğu ve yeni GUI'den farkları
kaynak:
  - repo: mtrader-trade-ui
    branch: main
    commit: 6715182
dogrulama: 2026-10-22
durum: taslak
---

# Eski GUI (`main`)

Eski GUI'yi kullanan kurulumlar: Piramit prod, A1, Alnus, Kanjo, Global, Marbas, Piramit_Algo ([branch-ve-ortamlar](../../00-genel/branch-ve-ortamlar.md#eski-gui--yeni-gui-parçalı-geçiş)). "Prod'da şu ekran nasıl çalışıyor?" sorusunun cevabı bu dosyadadır, yeni GUI'nin `AGENTS.md`'sinde değildir.

`main` = development'taki son eski GUI hali `59f1689` + yalnızca deploy commit'leri. Kod yolları `main:src/...` biçimindedir; `59f1689:src/...` ile aynı içeriği verir. REST/WS uçlarının tablosu burada yoktur: [backend-sozlesmesi.md](backend-sozlesmesi.md). Yeni GUI yapısı: [yeni-gui.md](yeni-gui.md).

## 1. Teknoloji ve platformlar

| Konu | Değer (`main:package.json`) |
|------|-----------------------------|
| Paket adı / sürüm | `mTrader` / `214.0.0` |
| Çatı | React 18 (`^18.2.0`), Ionic React 7 (`IonReactRouter`), react-router-dom 5 |
| Build | Vite 4. `npm run build` = `tsc && vite build`, yani tip kontrolü build'in parçası. |
| UI kütüphaneleri | dockview 1.x (panel düzeni), MUI 6, react-select, react-toastify, react-tooltip, `xlsx` (Excel dışa aktarım), i18next (`locales/tr.json`, `locales/en.json`, varsayılan `tr`) |
| Durum | React context + `useReducer`. Redux, zustand, socket.io, grpc-web paketleri bağımlılıkta duruyor ama `src/` içinde import edilmiyor (zustand yalnızca `TavanContext.tsx` yorumunda geçiyor). |
| Mobil | Capacitor 5 (`@capacitor/android`, `@capacitor/ios`). `src/` hiçbir Capacitor plugin'i import etmiyor; mobilde saf web uygulaması gibi çalışıyor. ❓ doğrulanmadı: `android/`, `ios/`, kök `capacitor.config.ts` bu inceleme kopyasında yok. |
| Electron | `electron/` (`@capacitor-community/electron`). Ayrıntı aşağıda. |

**Sunucu adresi** (`main:src/configuration/services/AppConfigService.ts`):
- REST: `getBaseUrl()`. `VITE_API_HOST` set ise o kullanılır, yoksa `window.location.host` ve sayfanın protokolü kullanılır.
- WS: `getWsUrl()`. Önce `VITE_WS_HOST`, sonra `VITE_API_HOST`'tan `http→ws` dönüşümü, en son sayfa host'u.
- Sonuç: Docker'da GUI'yi sunan host, API ile aynı host olarak kabul edilir. Port eşlemesi ve reverse proxy ayrıntısı deploy tarafındadır.
- `AppConfigData` (`ip`, `port`, `wsPort`) ve `sessionStorage.configData` eski bir yapının kalıntısıdır. Yalnızca ölü kodda (`OrderBookSettingsWsContext.tsx`, gridActions'taki yorum bloğu) geçer.

**Deploy:** `main` → Docker imajı `meeapps/mtrader-frontend:<müşteri>`, container `MTraderGui` ([branch-ve-ortamlar](../../00-genel/branch-ve-ortamlar.md#gui-dağıtımı-mtrader-trade-ui)). Development'taki `algo_gui.yaml` `npm install --legacy-peer-deps` + `CI=false npm run build` çalıştırır, `dist/`'i nginx imajına kopyalar. ❓ doğrulanmadı: `main`'deki `Dockerfile`, `algo_gui.yaml` ve `vite.config.ts` bu kopyada yok; main'in workflow'u aynı adımları izliyor varsayımı kontrol edilmedi.

**Electron'a özgü** (`main:electron/src/index.ts`, `setup.ts`):
- `ElectronCapacitorApp` web build'ini (`webDir: dist`) özel URL şemasıyla (`capacitor-electron://`) sunar. Splash ekranı ve tray menüsü (yalnız "Quit App") vardır.
- `autoUpdater.checkForUpdatesAndNotify()` her açılışta çalışır; publish sağlayıcısı `github` (`electron-builder.config.json`, Windows NSIS, mac dmg). `appId` hâlâ şablon değerindedir (`com.yourdoamnin.yourapp`).
- Pencere `nodeIntegration: true`, `contextIsolation: false` ile açılır.
- `setupContentSecurityPolicy` CSP'ye sabit bir sunucu adresi (`<PROD_IP>:<PORT>`, http ve wss) yazar ve `'unsafe-eval'`/`'unsafe-inline'` içerir. Electron build'i bu yüzden belirli bir kuruluma bağlıdır.
- Kök `package.json` `"main": "electron-main.ts"` diyor. ❓ doğrulanmadı: bu dosya kopyada yok; Electron girişi `electron/package.json` `main: build/src/index.js`.

## 2. Uygulama yapısı

### 2.1 Routing (`main:src/App.tsx`)

`IonReactRouter` + `IonRouterOutlet`, özel `history` (`src/contexts/History.ts`, `createBrowserHistory`). Provider sırası (dıştan içe): Theme → WebSocket (itch) → Language → DockviewApi → SelectedStrategy → OrderHistory → OrderForm → FundTrackerPackages → PassiveOrderResponse.

| Path | Bileşen |
|------|---------|
| `/` | → `/selectstrategy` |
| `/login` | `LoginForm` |
| `/otp` | `OTPForm` |
| `/forgetpassword` | `ForgetPasswordForm` |
| `/passwordReset/:username/:token` | `ChangePasswordForm` |
| `/selectstrategy` | `SelectStrategy` |
| `/main?strategyTypeId=<n>` | `MainPage` (Dockview çalışma alanı) |
| `/oh`, `/settings` | `OrderHistory`, `StrategySettings` tek başına. Geliştirme kalıntısı; `/settings`'in prop'ları `throw` eder. |

Route guard yok. Her sayfa `useEffect` içinde token'a bakar ve gerekirse `/login`'e veya `/selectstrategy`'ye `history.push` yapar.

### 2.2 Ekranlar (`main:src/pages/`)

| Klasör | İş |
|--------|----|
| `LoginPage`, `OtpPage`, `ForgetPassword`, `ChangePassword` | Auth (§7) |
| `SelectStrategy` | Strateji kartları (§3.1) |
| `MainPage` | `DockviewReact` + üst araç çubuğu (`GridActions`). Dockview `components` haritası burada (§6). |
| `DockView/` | `gridActions.tsx` (araç çubuğu, **order socket**, layout kaydet/yükle, panel açıcılar), `controls.tsx` (grup başlığı: kilit, pin, popout, maximize), `defaultLayout.tsx`, `debugPanel.tsx` |
| `StrategySettings` | "Strateji ekle" modalı: HFT/Tavan/Taban/Arbitraj satırı ekleme, VWAP/Fon Takibi için hesap–strateji ataması |
| `CreatePanel` | "Yeni Panel" modalı: `/v1/getPanels` ile kayıtlı paneli seç ya da yeni isim yaz |
| `Hft/`, `Tavan/`, `Taban/`, `Varant/`, `Arbitrage/` | Tracker formları, özet panelleri, ekleme ve ayar modalları |
| `TheoreticForm` | Teorik Fiyat ekranı (tek panel, tracker + emir) |
| `OrderBook` | Enstrüman başına derinlik paneli. Strateji ayar modalları (`OrderBookSettings` = HFT/VWAP/Fon, `TavanSettings`, `TabanSettings`) ve başlat/durdur (`StartStopButton`) buradadır. |
| `OrderForm` | Toplu (sabah/açılış/akşam) emir ekranı (§4.1) |
| `OrderHistory` | Emir geçmişi (§4.3) |
| `FundTrackerSummaryView`, `VWAPSummaryView` | Özet panelleri |
| `Components/` | `SendOrderModal`, `CancelReplaceOrderModal`, `CancelAllAccountOrdersModal`, `StrategyPassiveOrders`, `DataTable`, `FileTransferModal` (arbitraj Excel), `SaveLayoutModal`, `Fab` |

### 2.3 Context'ler (`main:src/contexts/`)

| Context | Tuttuğu |
|---------|---------|
| `WebSocketContext` + `WebSocketService` | Tekil (singleton) **itch** socket'i: `/ws/v1/itch/start` (§5) |
| `SelectedStrategyContext` | `strategies` (`getAllowedStrategies` sonucu) ve `selectedStrategy` (`{strategyName, strategyId}`). Seçim `sessionStorage.selectedStrategy`'de saklanır. |
| `OrderHistoryContext` | Order socket'ten gelen bütün emir olayları (dizi, en yeni başta, sınırsız büyür) |
| `OrderFormContext` | `OrderHistoryContext`'ten `type === 10` (CollectiveOrder) süzülmüş kopya |
| `PassiveOrdersContext` | Tracker'ların strateji socket'inden aldığı `PassiveOrderResponse`'lar |
| `FundTrackerPackagesContext` | Fon Takibi paketleri (OrderBook doldurur, `FundTrackerSummaryView` okur) |
| `TavanContext`, `TabanContext`, `VarantContext` | Tracker başına `useReducer` store'u (ayar, bakiye, `maxPriceStates`, orderData). Provider tracker formunun içinde kurulur; her panelin ayrı store'u olur. `VarantContext` ayarları `localStorage.varant-strategy-settings`'e yazar. |
| `ThemeContext`, `LanguageContext`, `DockViewApiContext` | Tema, dil, Dockview API referansı |
| `OrderBookSettingsWsContext` | Ölü kod (hiçbir yerde mount edilmiyor) |

### 2.4 `src/Functions`, `src/structs`, `src/utils`

- `Functions/GeneralFunctions.tsx`: `createTypeNumber`/`createTypeString`/`createTypeBool` (komut alanlarını `{"@type": "type.googleapis.com/servicemodels.Gui*Value", value}` sarmalına koyar), `sideMapping`, `getStrategyTypeByName`, para formatlama (`convertInitialValueToCurrency` ÷1000, `currencyStringToNumber` ×1000), `getInstrumentPriceDivider(decimalCount)`.
- `Functions/React-Select/useNumberField.tsx`: ayar modallarındaki sayısal alan hook'u (precision, min, binlik ayırıcı).
- `structs/RequestStructs.ts`, `ResponseStructs.ts`: wire tipleri. Strateji başına alan arayüzleri burada (`HftStrategyRequestFields`, Taban için ayrı "dedicated wire contract" bloğu).
- `utils/TokenUtils.ts`: `getToken()` = `sessionStorage.token || localStorage.token`. `utils/StringUtils.ts`: `normalizeStrategyIdentifier` (Türkçe karakter → ASCII).

### 2.5 Tarayıcı depolaması (önemli)

Eski GUI'de tracker panellerinin **satır listesi tarayıcıda** tutulur. Backend'e yazılan kopya panel kaydıdır (`/v1/setPanel`).

| Anahtar | İçerik |
|---------|--------|
| `localStorage.hftParams` / `tavanParams` / `tabanParams` / `arbitrageParams` / `varantParams` | `{ <panelId>: Item[] }`: panel başına satırlar (hesap, enstrüman, strateji kimliği; Tavan/Taban toplu satırlarda `indiceId`) |
| `panelIds`, `panelMeta` | Panel isimleri ve açıklamaları |
| `savedLayouts`, `<STRATEJI><isim>`, `lastLayout<STRATEJI>` | Dockview layout JSON'ları (§6) |
| `tavan_stability_ms`, `taban_stability_ms` | Satır sıralama kararlılık penceresi |
| `order-history-column-*`, DataTable kolon tercihleri | Kolon genişliği, sırası, görünürlüğü |
| `soundEnabled`, `token`, `rememberMe`, `savedUsername` | Ses, oturum |

localStorage origin'e bağlıdır. Aynı kurulum farklı host ya da port ile açılırsa paneller boş gelir. Backend'deki panel kaydından `CreatePanel` ile geri yüklenebilir.

## 3. Strateji ekranları

Strateji mantığı ve alanların anlamı: [`20-stratejiler/`](../../20-stratejiler/README.md). Burada yalnızca eski GUI'nin ne gönderdiği yazılıdır.

### 3.1 Strateji seçimi (`SelectStrategy.tsx`)

- `getAllowedStrategies(token)` (`/v1/getAllowedStrategies`) çağrılır. Kartlar `strategyName.startsWith(...)` ile açılır. `HFT_WARRANT` kontrolü `HFT`'den önce yapılır, Varant kartı bu yüzden doğru açılır.
- Kartlar: HFT, Arbitraj, VWAP, **Sabah Emri** (`COLLECTIVE_ORDERS`), Fon Takibi, Tavan, Taban, Teorik, Varant. İzin yoksa kart **disabled** olur (yeni GUI'de Varant Toplu kartı gizlenir).
- Navigasyon `/main?strategyTypeId=<id>`. Varant kartı `{strategyName: "VARANT", strategyId: "13"}` değerini **sabit** yazar.
- Varant Toplu (15) kartı **yok**. `HFT_WARRANT_ADVANCED` izni gelirse de `startsWith("HFT_WARRANT")` Varant kartını açar.

### 3.2 Ortak kalıp

1. **Satır ekleme:** `StrategySettings` modalı (HFT/Tavan/Taban/Arbitraj) ya da tracker'ın kendi modalı (Tavan/Taban `AddStrategyModal`, Varant `AddUnderlyingModal`, Arbitraj `AddPackageModal`). Strateji ID'si tam 3 karakter olmalıdır. Satır `localStorage.<x>Params[panelId]`'e eklenir.
2. **Abonelik:** Tracker, satırı REST ile backend'e kaydeder. HFT/Tavan/Taban için `subscribeToSingleHft` (`/v1/subscribeToOrderbook`, `strategy_type` 4/9/14), Varant için `subscribeToVarant`, Teorik için `subscribeToTheoretic` (üçü de aynı uca gider), Arbitraj için `subscribeToSingleArbitrage`, Tavan/Taban toplu ekleme için `subscribeToIndice`.
3. **Ayar/başlat/durdur:** `setCommandRequest` (`/v1/setStrategyCommands`), gövde `{commandType: 1, uniqueKey, strategyType, fields}`. `unique_key` = `<orderbookId>_<hesap>_<stratId>_<StrategyType>`. VWAP'ta sonuna `_66`/`_83` eklenir.
4. **Canlı durum:** Her tracker panelinin kendi `/ws/v1/strategy/start` socket'i vardır. Login sonrası `Type: 4` mesajıyla satır başına `commandType 1` (ayar) + `3` (bakiye) ister (§5).
5. **Panel senkronu:** `/v1/setPanel` (`fetch`, timeout yok) üç durumda çağrılır: satır ekleme/silme (HFT, Tavan, Taban, Arbitraj, Varant tracker'ları), layout kaydı (`GridActions.handleSaveLayout`, yalnızca aktif panel ve yalnızca ARBITRAGE/HFT/MAX_PRICE/MIN_PRICE) ve StrategySettings'te Arbitraj satırı ekleme. `applicationUserName` HFT/Tavan/Taban/Varant'ta `"hftUser"`, Arbitrajda `"algoUser"`.

### 3.3 Fiyat ve birim ölçeği

- Eski GUI fiyatı neredeyse her yerde **sabit ×1000** ile çevirir: emir modalları, OrderForm, HFT `Buy_Upper_Limit_Price`/`Sell_Below_Limit_Price`, Teorik `price`/`expected_price`, Varant `Criteria_Price`, Tavan/Taban gösterimi. `decimalCount` yalnızca Varant fiyat **gösteriminde** ve Varant pasif emirlerde kullanılır (`getInstrumentPriceDivider`).
- Sonuç: `decimalCount = 2` olan enstrümanlarda (VIOP) ×1000 varsayımı 10 kat hatalıdır. Yeni GUI bunu `decimalCount`'tan türetir; istisnaları yeni GUI `AGENTS.md` → "Price Scale" bölümü sayar.
- Fon Takibi teorik fiyatı `theoPrice / 100` ile gösterilir (`StartStopButton.tsx`). Arbitraj kademe getirisi `/10000` ve `/100` kullanır (`ArbitrageTrackerFormUtils.getTickYields`).
- `Second_Rule_Duration`: HFT'de değer olduğu gibi (**saniye**, `Math.max(1, x)`) gider. Tavan/Taban'da UI saniye gösterir, **×1000 ms** gönderir (`TavanSettings`, `TabanSettings`, `Virtualized*Row`). Taban `Re_Close_Duration` aynı şekilde gider. Tavan `Escape_Percentage` ×100.

### 3.4 HFT (4): `Hft/HftTrackerForm/`, `OrderBook/OrderBookSettings.tsx`

- Payload: `createHftPayload` (`HftTrackerFormUtils.tsx`; inline hücreler ve başlat/durdur) ve `OrderBookSettings` `hftFields` (ayar modalı). `strategyType: 4`, `Command_Type: 51`.
- **Stop loss:** Kapalıyken `Is_Stop_Loss_Enabled: false`, `Hft_Stop_Loss_Level: 0` gider. Modal backend'den 0 gelince ekranda `-1` gösterir, `-1` girilirse 0 gönderir. Motor ise yalnızca `-1`'i "kapalı" sayar ([hft-classic](../../20-stratejiler/hft-classic.md)). Yeni GUI bu davranışı bilerek aynen taşır; çözülmemiş açık konudur.
- **Hft_Type:** `createHftPayload` yalnızca Pozisyonsuz'da (2) `Replace_Mode` ve `Chase_*_Passive` alanlarını false yapar; `Replace_Mode` açıksa `Send_Sell_Orders_Instead_Of_Short = true` olur. Modal Pozisyonsuz → Pozisyonlu geçişinde pozisyonsuz alanları sıfırlar. Bu sıfırlama yalnızca **geçiş anında** ve yalnızca modalda yapılır; eski kayıtlarda kalmış değerler temizlenmez. Yeni GUI'nin `normalizeHftFields`'ı bunu her yolda zorlar.
- Inline "Alarak/Satarak başla" kapatılınca karşı tarafın `*_Active_Style = true`, `*_Passive_Level = 0` yapılır; iki taraf da kapalıysa stop loss kapatılır (`VirtualizedHftRow.tsx`).
- Pozisyon ekleme: `AddPositionModal` → `commandType: 3`, `Order_Price` ×1000.

### 3.5 Tavan (9) ve Taban (14): `Tavan/`, `Taban/`, `OrderBook/TavanSettings.tsx`, `TabanSettings.tsx`

- Payload: `createTavanPayload` (`Hft_Type: 3`, `Is_Tavan_Mode: true`) ve `createTabanPayload` (`Hft_Type: 5`). İkisi de `Is_Running: false` gönderir. Saat yoksa `Start_Time || 36000`, `End_Time || Stop_Time || 64800` (10:00 / 18:00, gün başından saniye).
- Tavan `Finish_With_Buy` gönderir. **Taban `Finish_With_Sell` göndermez**; yeni GUI aynı kararı korur ([taban](../../20-stratejiler/taban.md)).
- Tavan `Cancel_Tolarence` yazımını, Taban `Tolerance` alanını kullanır.
- **"Taban Lot" kolonu bounds feed'inin `maxAskLot` alanını okur** (`TabanTrackerForm.tsx`, Tavan'dan kopyalanmış). Bug; yeni GUI `minBidLot` okur.
- **Canlı durum:** Tavan tracker'ı `Command_Type_MaxPriceStateResponse` işler ama abonelikte yalnızca `commandType [1, 3]` ister. ❓ doğrulanmadı: bu durumda type-8 akışının gelip gelmediği. Taban bu mesajı **hiç işlemez**.
- Tavan state'i `Has_Passive_Sell_Order_At_Tavan` adıyla saklar, satır ise `Has_Passive_Sell_Order`'ı okur. Backend soneksiz gönderir, yani kırmızı "pasif satış" vurgusu hiç tetiklenmez (bug; yeni GUI `CommandSocket.ts` yorumu).
- Toplu ekleme (`StrategySettings` "Toplu"): `getIndices` → `getIndiceInstruments` → `subscribeToIndice`. Satırlara `indiceId` yazılır; panel kaydında `overallValue = indiceId` olarak saklanır.

### 3.6 Varant (13): `Varant/VarantTrackerForm/`

- Ekleme: `AddUnderlyingModal` → `subscribeToVarant`, `varantParams`'a yazar. Varant listesi: `VarantSettings` → `getDerivativesByUnderlying`.
- Payload `createVarantPayload`: `Hft_Type: 4`, `Criteria_Price` ×1000, `Derivative_Orders` JSON metni. Dayanak satırı ile varant alt tablosu iki ayrı tablodur.
- Varsayılan kriter `criteriaValue: 0`, `toleranceCount: 0`. Motor bu değerleri reddeder; ayar kaydetmeden başlat'a basılırsa komut sessizce düşer (bug; yeni GUI'de alt sınır 1).
- Panel geri yüklemede backend yalnızca dayanak iskeletini verir (`CreatePanel.mapServerToLocalVarant`); kriterler strateji socket'inden hidrate olur.
- **Varant Toplu (15) yok** ([varant-toplu](../../20-stratejiler/varant-toplu.md)).

### 3.7 Teorik Fiyat (8): `TheoreticForm/TheoreticForm.tsx`

- Satırlar **yalnızca bileşen state'inde** tutulur; localStorage'a ya da panel kaydına yazılmaz. Panel kapanınca veya sayfa yenilenince liste kaybolur.
- Strateji kimliği sabit `"teo"`. Başlat/durdur: `commandType: 1`, **`strategyType: 4`**, `Strategy_Id` = **hesap adı**, `unique_key` `…_teo_8`. Yeni GUI 8 ve strateji kimliğini gönderir. Eski değer, motorun ters emirlerine yanlış kimlik yazdırıyordu ([teorik-fiyat](../../20-stratejiler/teorik-fiyat.md); yeni GUI `theoreticalPricePayload.ts`).
- Emir: `sendOrder`, `order_type: 5`, `order_event_type: 4`, `protocol: 1`, `expected_price` ×1000, `custom_data: "Deneme"`.
- Denge fiyatı: kendi `/ws/v1/equilibrium/start` socket'i. `onopen`'da login, `Type: 6 {OrderBookIDs}` ile abonelik. Gösterim ÷1000.

### 3.8 Arbitraj (6): `Arbitrage/`

- Satırlar `StrategySettings`'ten (Tekli/Toplu; tipler Faiz, Spread, Çift Vade, Çift Vade Faiz) `arbitrageParams`'a eklenir, abonelik `subscribeToSingleArbitrage` ile yapılır.
- Ayar: `ArbitrageStrategySettingsPage` (`Command_Type: 51`). Paket: `AddPackageModal`/`PackageSettingsModal` (`Command_Type: 72`). Pasif emir kapatma: `PassiveOrders.tsx` (`commandType: 6`).
- Excel: `downloadArbitrageExcel` / `uploadArbitrageExcel` (base64 JSON gövde). Panel yenileme `getPanels?strategyType=6`.
- Ayrıntı: [arbitraj](../../20-stratejiler/arbitraj.md).

### 3.9 VWAP (7) ve Fon Takibi (10)

- Tracker yok. Araç çubuğundaki "+" `StrategySettings` açar → `setSelectedAccountStrategy` (`/v1/setAccountStrategy`) → `orderBook` paneli açılır. Ayar ve başlat/durdur OrderBook panelindeki FAB'lardan yapılır.
- VWAP: `Command_Type: 54`, alış ve satış ayrı `unique_key` (`_66`/`_83`). Özet: `VWAPSummaryView`.
- Fon Takibi: `Command_Type: 100`, `Byf_*` alanları. Modaldaki "Alış/Satış Miktar" kutuları HFT'nin `Trigger_Qty_*` alanlarına bağlıdır ve pakete ulaşmaz; yeni GUI bunu bilerek etkisiz bırakır ([fon-takibi](../../20-stratejiler/fon-takibi.md)).

## 4. Emir ekranları

### 4.1 Sabah Emri / toplu emirler (`OrderForm/OrderForm.tsx`)

- `COLLECTIVE_ORDERS` workspace'i. Varsayılan layout tek bir `OrderForm` paneli (`defaultLayout.tsx`).
- Emir zamanı (`order_type`): 1 Sabah, 2 Açılış, 4 Akşam. **YİP yok.** Varsayılan değer İstanbul saatine göre seçilir (`OrderFormUtils.getDefaultCollectiveOrderTime`): 09:40–10:00 → Açılış, 10:00–18:00 → Akşam, diğer saatler → Sabah. UI metni: "Sabah 09:40, Açılış 10:00, Akşam 18:01'de iletilir."
- Gönderim: `sendOrder` (`/v1/sendOrders`). `side` **1/2** (66/83 değil), `protocol` = kanal (1 Ouch, 2 Fix), strateji tipi seçimi 4/6/9, `order_event_type` 1 yeni / 2 sil / 3 güncelle-aktifleştir, `level_count`, `custom_data` = `<order_type>x<stratId>x<tip,2 hane><7 rastgele karakter>`.
- Liste `OrderFormContext`'ten gelir (order socket'te `Type === 10`). Toplu seç, aktifleştir, sil, fiyat/miktar/kademe düzenle. Aktif/pasif geçişinde 5 sn içinde socket teyidi gelmezse loading kaldırılır.
- Fiyat girişi en fazla 2 ondalık kabul eder, ×1000 gönderilir. Backend tarafı: [order-service toplu emirler](../order-service/toplu-emirler.md).

### 4.2 Emir defteri (`OrderBook/OrderBook.tsx`)

- Panel parametreleri: `instrumentId`, `accountName`, `strategyId`, `strategyType`, `tickSize`, `isPinned`. Panel, tracker satırından ya da StrategySettings'ten açılır (`GridActions.onAddPanel`).
- Derinlik: paylaşılan itch socket'e `Type: 2 {Account, StrategyIdentifier, StrategyType, OrderBookId}` ile abone olur, unmount'ta `Type: 9` gönderir. Mesajlar `OrderBookKey` = `<hesap>_<inst>_<strat>_<tip>` ile süzülür.
- Kademe tıklama → `getOrdersFromLevel` (`/v1/getOrdersFromLevel`). Kullanıcı ve strateji emirleri işaretlidir.
- Emir: `SendOrderModal` → `sendOrder` (`order_type: 3`, `order_event_type: 1`, `is_main_order: true`, `is_active: false`). "Serbest" seçeneği HFT'de `strategy_type 12`, diğerlerinde `1` gönderir. HFT'de satış tarafının varsayılanı "Short"tur. Kanal HFT ve Tavan'da OUCH, diğerlerinde FIX.
- İptal/düzelt: `CancelReplaceOrderModal` → `cancelOrder` / `replaceOrder`. İkisi de `/v1/sendOrders` ucuna gider; `order_event_type` 2/3. Toplu iptal: kademedeki son N dışındakiler iptal edilir.
- Strateji emirlerini toplu iptal: `setCommandRequest` `commandType 7` ya da `9`.
- Strateji ayar modalı ve başlat/durdur da bu paneldedir: HFT, VWAP, Fon, Tavan, Taban.

### 4.3 Emir geçmişi (`OrderHistory/OrderHistory.tsx`)

- Kaynak `OrderHistoryContext` (order socket, §5). Filtre: `strategyType === 1` **veya** (`strategyType === seçili strateji` **ve** `type < 10`).
- Tip haritası (`gridActions`): 3 Accepted, 4 Executed, 5 Deleted, 6 Replaced, 7 Rejected, 8 SnapShot, 9 State, 10 CollectiveOrder. Type 11 gelirse emir listeden silinir. Executed (4) gelince "coin" sesi çalar.
- Gecikme kolonları `latency*Ns` değerini µs'ye yuvarlar. 0 ya da 1 sn'den büyük değerler "-" gösterilir (yeni GUI aynı kuralı alır).
- Excel dışa aktarım (`xlsx`). Kolon tercihleri localStorage'da.

### 4.4 Hesap bazlı toplu iptal (araç çubuğu, `CancelAllAccountOrdersModal`)

`setCommandRequest` `commandType 7` gönderir; "Aktiften Kapat" işaretliyse `commandType 9`. Alanlar: `Account`, `Order_Side` (0 hepsi / 66 / 83), `Orderbook_Id: 0`, boş `uniqueKey`, seçili `strategyType`.

## 5. WebSocket yönetimi

Mesaj tipleri ve uçlar: [backend-sozlesmesi.md](backend-sozlesmesi.md). Ortak el sıkışma: sunucu `client_id` gönderir → istemci `{Type: 1, Body: {Token}}` → sunucu `Type: 2` / `"Login successful"` → abonelik. Teorik ve `OrderBookSettingsWs` login'i `onopen`'da gönderir.

| Socket | Sahibi | Sayı |
|--------|--------|------|
| itch `/ws/v1/itch/start` | `WebSocketService` singleton (context) | Uygulama başına 1, bütün OrderBook panelleri paylaşır |
| orders `/ws/v1/orders/start` | `GridActions` (araç çubuğu) | 1. Abonelik `Type: 3 {Types: [1..10,13,14], AccountName: [tüm hesaplar]}` |
| strategy `/ws/v1/strategy/start` | Her tracker, her özet paneli, her VWAP/Fon OrderBook paneli; ayrıca `OrderBookSettingsWs.ts` modül singleton'ı | Panel başına 1 |
| best `/ws/v1/best/start` | HFT, Tavan, Taban, Varant, Arbitraj tracker'ları (`Type: 5 {orderBookIds}`) | Panel başına 1 |
| bounds `/ws/v1/bounds/start` | Tavan, Taban tracker'ları | Panel başına 1 |
| equilibrium | TheoreticForm | 1 |
| passive-orders | `StrategyPassiveOrders`, `VarantPassiveOrders` (`Type: 8`) | Panel başına 1 |

**Yeniden bağlanma yok.** Kodda otomatik reconnect ya da backoff bulunmuyor:
- Panel socket'leri yalnızca `useEffect` bağımlılıkları değişince (ör. `itemsArray`, satır ekleme/silme) kapatılıp yeniden açılır. Sunucu bağlantıyı koparırsa panel, kullanıcı bir şey değiştirene ya da paneli yeniden açana kadar donuk kalır.
- itch singleton koparsa `connectionStatus` "disconnected" olur. `WebSocketContext.connect()` mevcut servis varken çağrıyı yok sayar, yani sayfa yenilenmeden itch geri gelmez. `unsubscribe` mesajı `subscriptions` listesinden çıkarılmaz.
- Order socket: kopunca araç çubuğundaki daire kırmızı olur ve alarm sesi çalar (`alarm-sound.wav`). Daireye tıklamak manuel durdur/başlat yapar: durdururken alarm döngüde çalar, başlatırken socket yeniden açılır. Strateji değişince emir listesi temizlenir ve socket kapatılır.

Yeni GUI'de socket'ler `socketStore`'da merkezidir ve kendi kendine iyileşir (yeni GUI `AGENTS.md` → "Sockets heal themselves").

## 6. Panel düzeni (Dockview)

- `MainPage` `DockviewReact`'i `components` haritasıyla kurar: `default` (logo), `orderBook`, `ArbitrageTrackerForm`, `HftTrackerForm`, `TavanTrackerForm`, `TabanTrackerForm`, `VarantTrackerForm`, `*SummaryView`, `OrderHistory`, `OrderForm`, `PassiveOrders`, `StrategyPassiveOrders`, `VarantPassiveOrders`, `SendOrderModal`, `TheoreticForm`.
- İlk açılışta `defaultConfig`: COLLECTIVE_ORDERS'ta `OrderForm`, diğerlerinde "Başlangıç" paneli. `onReady` `localStorage["dv-demo-state"]`'i okur, ama bu anahtarı yazan kod yok (demo kalıntısı). Sekmeye sağ tıklama `alert("context menu")` açar (demo kalıntısı).
- **Araç çubuğu** (`gridActions.tsx`), butonlar stratejiye göre değişir: "+" (Arbitraj/HFT/Tavan/Taban/Varant'ta `CreatePanel`; VWAP/Fon'da `StrategySettings`; Teorik'te `TheoreticForm`; Sabah Emri'nde `OrderForm`), Emir Geçmişi, Özet, Pasif Emirler, Layout kaydet, Strateji seçimine dön, Layout sil, Toplu iptal, Çıkış, bağlantı dairesi, ses, tema.
- **Panel oluşturma** (`CreatePanel`): açılışta `GET /v1/getPanels?strategyType=<6|4|9|14|13>` ile yalnızca `isActive` paneller listelenir. Kayıtlı panel seçilirse `strategies` `*Params[panelName]`'e yazılır (Varant'ta doğrudan prop olarak geçer). Yeni isim yazılırsa boş panel açılır. Panel id'si = panel adı.
- **Layout kaydı**: `onSave` `api.toJSON()` sonucunu `localStorage["<STRATEJI><isim>"]`'e yazar. Popout grupları ana grid'in sağına taşınarak kaydedilir. Ardından aktif panel `/v1/setPanel` ile backend'e yazılır (§3.2).
- **Layout yükleme**: `onLoad`, tracker panellerinin `params.data`'sını güncel `*Params`'tan ezer, sonra `fromJSON` çağırır. Strateji açılışında `lastLayout<STRATEJI>` otomatik yüklenir.
- Grup başlığı (`controls.tsx`): maximize, popout (`addPopoutGroup`), kilit (`params.isLocked`), pin (`params.isPinned`; OrderBook butonlarını küçük panelde de gösterir).

## 7. Auth akışı

- `LoginForm`: `sendLoginRequest` (`/v1/login`). Başarılı olunca `sessionStorage.username` ve **`sessionStorage.password` (düz metin)** yazılır, ardından `localStorage.token`. OTP açıksa backend token'ı boş döner ([trade-data-app api](../trade-data-app/api.md)) ve kullanıcı `/otp`'ye yönlenir. OTP kapalıysa `sessionStorage.token` yazılır, `/selectstrategy`'ye geçilir.
- Otomatik giriş: `/login` açılınca `localStorage.token` varsa `/v1/getAllowedStrategies` ile doğrulanır. 200 dönerse `/selectstrategy`'ye geçilir.
- `OTPForm`: 4 kutu, dördüncü dolunca `guiCheckOtpCode` (`/v1/checkOtpCode`) çağrılır. "Tekrar gönder" saklanan kullanıcı adı ve şifreyle login'i yeniden çağırır; 120 sn geri sayım vardır.
- Şifre: `sendForgetPassword` (`/v1/forgetPassword`), e-postadaki bağlantı `/passwordReset/:username/:token` → `changePassword` (`/v1/resetPassword`).
- 401: `ApiService.handleUnauthorizedError` `localStorage.token`'ı siler, toast gösterir ve `/login`'e gider. Çıkış (`onSignOut`) `token`, `rememberMe` ve bütün `sessionStorage`'ı temizler.

## 8. Yeni GUI ile davranış farkları

Kaynak: yeni GUI kodundaki "eski GUI / eski uygulama / eski arayüz / `@ 59f1689`" yorumları ve `AGENTS.md`. Bir fark için yeni GUI'de değişiklik önermeden önce o yoruma bak.

**Bilerek korunan**

| Konu | Davranış |
|------|----------|
| HFT stop loss kapalı | `Hft_Stop_Loss_Level: 0` gider (motor `-1` bekler; açık konu) |
| Taban `Finish_With_Sell` | Gönderilmez |
| Fon Takibi "Alış/Satış Miktar" | Etkisiz |
| `tavan_stability_ms` / `taban_stability_ms` | Aynı anahtar adları (aynı origin'de değer taşınır) |
| Teorik strateji kimliği | Sabit `"teo"` |
| Emir geçmişi gecikme kuralı | µs, 0 ve >1 sn → "-" |
| Toplu ayar kaydında `Strategy_Start: false` | Operatör gözden geçirip yeniden başlatır |
| `setPanel` / `subscribeToIndice` | Eski GUI'de timeout yoktu; yeni GUI uzun timeout ile korur |

**Bilerek değişen (eski GUI'de bug)**

| Konu | Eski GUI | Yeni GUI |
|------|----------|----------|
| Fiyat ölçeği | Sabit ×1000 | `decimalCount`'tan (istisnalar `AGENTS.md` → Price Scale) |
| Taban Lot | `maxAskLot` | `minBidLot` |
| Taban canlı durum | `MaxPriceStateResponse` işlenmiyor | `[1, 3, 8]`, `minPriceLiveState` |
| Tavan pasif satış vurgusu | `…_At_Tavan` okunur, hiç yanmaz | `Has_Passive_Sell_Order` |
| Teorik başlat/durdur | `strategyType: 4`, `Strategy_Id` = hesap | 8 ve strateji kimliği |
| Varant varsayılan kriter | `criteriaValue`/`toleranceCount` 0, komut düşer | Alt sınır 1, motor varsayılanları |
| HFT gizli alanlar | Yalnızca modalda, geçiş anında sıfırlanır | `normalizeHftFields` her yolda |
| OTP kilidi (`status:false`, `isOtpEnabled`) | Login ekranında kalır | OTP ekranına geçer |
| Socket'ler | Panel başına, reconnect yok | Merkezi, kendi kendine iyileşir |
| Taban özet "Pozisyon/Taban Durumu" | Kolon var, gerçek değer göstermez | Kolon yok |

**Eski GUI'de olmayan**: Varant Toplu (15) ve `/v1/parseWarrantFile`; Toplu Emirler'de YİP; Varant'ta tek tablo (eski: iki tablo).

**Yeni GUI'de olmayan / farklı**: Eski GUI'nin Electron ve Capacitor paketleri, arayüzden manuel order socket durdur/başlat ve alarm sesi. ❓ doğrulanmadı: yeni GUI'de birebir karşılıkları; [yeni-gui.md](yeni-gui.md)'ye bak.

## 9. Kod okuma ipucu

```bash
git show 59f1689:src/pages/Tavan/TavanTrackerForm/TavanTrackerForm.tsx
git ls-tree -r --name-only 59f1689 src/
git log --oneline 59f1689..origin/main     # main'deki deploy commit'leri
```

- `origin/eski_gui` aynı kod tabanının 2026-03 halidir. **`59f1689` tercih edilmelidir.**
- Dosyalar büyüktür (Tavan tracker ~3200, Taban ~3000, HFT ~2700 satır). Grep ile girin: `message_type ===` (socket mesajları), `createType` (payload alanları), `setCommandRequest(` (komut yolları), `/v1/` (fetch ile çağrılan uçlar: `setPanel`, `getPanels`).
- `ApiService.ts` dışında da REST çağrısı vardır: `setPanel`/`getPanels` (`fetch`) ve login sayfasındaki otomatik giriş (`axios.get`).

## Şüpheli

- **bug? — HFT kartı yanlış tipe gidebilir:** `setStrategyAndNavigate("HFT")` `strategies.find(s => s.strategyName.startsWith("HFT"))` kullanıyor. İzin listesinde `HFT_WARRANT…` `HFT`'den önce gelirse HFT kartı strateji id 13/15 ile açılır. ❓ doğrulanmadı: `getAllowedStrategies` sıralaması.
- **bug? — CreatePanel tip tutarsızlığı:** MAX_PRICE için başlangıç state'i 9, `useEffect` ise `setStrategyType(12)` yapıyor. `getPanels` fetch'i ilk render'ın değerini (9) kullandığı için bugün zararsız. 12 = `HFT_User`.
- **bug? — Order socket tekrarlanan emirler:** Socket yeniden açıldığında (manuel durdur/başlat, `accounts` değişimi) liste temizlenmiyor. Sunucu snapshot'ı yeniden gönderirse kayıtlar çift görünebilir. ❓ doğrulanmadı: yeniden bağlanmada snapshot gönderilip gönderilmediği.
- **bug? — OrderHistory filtresi:** HFT'den "Serbest" emir `strategy_type 12` ile gider. Filtre yalnızca 1 ve seçili stratejiyi gösterdiği için bu emirler HFT workspace'inin geçmişinde görünmeyebilir. ❓ doğrulanmadı: order socket'in bu emirlerde döndüğü `StrategyType`.
- **güvenlik — düz metin şifre:** `sessionStorage.password` OTP "tekrar gönder" için tutuluyor, çıkışta temizleniyor.
- **güvenlik — Electron:** `nodeIntegration: true` + `contextIsolation: false`; CSP'de sabit sunucu adresi ve `unsafe-eval`.
- **bug? — 401 sonrası oturum:** `handleUnauthorizedError` yalnızca `localStorage.token`'ı siliyor; `getToken()` önce `sessionStorage`'a bakıyor. Süresi dolmuş token sekmede kalır.
- **kasıtlı? — `SendOrderModal` `is_active: false`:** Yeni emir `is_active: false` ile gönderiliyor (`order_type: 3`). Teorik emir de öyle. ❓ doğrulanmadı: backend'in bu alanı strateji/serbest emirde nasıl yorumladığı.
- **bug? — OrderForm `custom_data`:** Güncelle/sil/aktifleştir isteklerinde `custom_data`'nın ilk alanı emrin kendi `orderType`'ı yerine formdaki seçili emir zamanından alınıyor. Liste filtresi farklı bir zamandayken yapılan işlemlerde yanlış önek gider.
- **❓ doğrulanmadı — Tavan type-8 akışı:** Tavan tracker `commandType 8` istemeden `MaxPriceStateResponse` işliyor. Akışın gelip gelmediği backend davranışına bağlı.
- **ölçek — VIOP fiyatları:** Sabit ×1000, `decimalCount = 2` enstrümanlarda (OrderBook emir modalları, HFT limit fiyatları) 10 kat sapma yaratır. ❓ doğrulanmadı: eski GUI'de VIOP enstrümanına hangi ekranlardan emir/limit girildiği (Arbitraj vadeli bacağı dahil).
