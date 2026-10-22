---
kapsam: İki GUI'nin (yeni = development, eski = main) trade-data-app ile sözleşmesi — bağlantı ayarları, auth akışı, REST uçları, WebSocket feed'leri, strateji komutu ve emir payload'ları, JSON lehçesi ve ölçekler; her uç/feed için hangi GUI'nin kullandığı
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui
    branch: main
    commit: 6715182
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# mtrader-trade-ui — backend sözleşmesi

Bu dosya sözleşmeyi **GUI tarafından** anlatır. Sunucu tarafının iç işleyişi başka dosyalardadır:
- trade-data-app REST/gRPC uçları, auth, protojson, CORS → [`../trade-data-app/api.md`](../trade-data-app/api.md)
- WS feed'lerinin sunucu davranışı ve tam alan listeleri → [`../trade-data-app/veri-akisi.md`](../trade-data-app/veri-akisi.md) §4
- Yeni GUI'nin socket kuralları → mtrader-trade-ui `AGENTS.md` → "WebSocket and Performance Constraints". Fiyat ölçeği kuralları → aynı dosya → "Price Scale".

Kısaltmalar: **Y** = yeni GUI (`app/`, development `b0474c3`), **E** = eski GUI (`src/`, main `6715182` = eski GUI'nin development'taki son hali `59f1689` + deploy commit'leri). ✓ kullanıyor, — kullanmıyor.

## 1. Bağlantı ayarları

| | Yeni GUI (`app/lib/apiConfig.ts`) | Eski GUI (`src/configuration/services/AppConfigService.ts`) |
|-|-----------------------------------|-------------------------------------------------------------|
| REST host | `VITE_API_HOST`; boşsa prod'da `window.location.host`, dev'de `127.0.0.1:5000` (`fallbackHost`) | `VITE_API_HOST`; boşsa `window.location.host` (dev'de de) |
| WS host | `VITE_WS_HOST`; boşsa REST host'u | `VITE_WS_HOST`; boşsa REST host'u |
| Protokol | Değerde `http(s)://`/`ws(s)://` yazılıysa o; yoksa sayfa protokolü (https → wss) | REST: `VITE_API_HOST`'ta protokol varsa o. WS: `VITE_WS_HOST` verilmişse yazılı protokol **atılır**, sayfa protokolü kullanılır; `VITE_API_HOST` `http…` ise `ws…`'e çevrilir |
| Ne zaman çözülür | Build-time (`import.meta.env`, Vite inline eder); `getApiConfig` ilk çağrıda önbelleğe alır | Build-time; her çağrıda yeniden hesaplanır |
| HTTP istemcisi | Tek Axios örneği `app/api/client.ts`: `timeout: 10_000`, `Accept: application/json`, `Authorization: Bearer <token>` interceptor'ı | Her fonksiyonda çıplak `axios`, timeout yok; bazı çağrılar `fetch` (`/v1/setPanel`, `/v1/getPanels`) |

- Varsayılan backend portları: REST `server.restPort` (tipik 6621), WS `gui.port` (tipik 6623) — [`../trade-data-app/config.md`](../trade-data-app/config.md). `.env.example` ve `apiConfig.ts` yorumundaki örnekler 6681/6683 der; bunlar örnek kurulum portudur, sözleşme değildir.
- **Deploy imajı env'siz derlenir** (`.github/workflows/algo_gui.yaml`: `npm run build`, `VITE_*` verilmez; `.env.example`: "Leave it OUT of production builds"). Bu durumda REST ve WS, GUI'yi sunan origin'e gider. GUI container'ı nginx (`Dockerfile`, `default.conf`) 80/443'ü müşteri portuna (`matrix.port`/`matrix.ssl_port`) açar ve **`/v1/` ile `/ws/` için `proxy_pass` içermez**. ❓ doğrulanmadı: prod'da `/v1/*` ve `/ws/*`'nin trade-data-app'e nasıl ulaştığı (dış reverse proxy mi, müşteri başına env'li build mi). `apiConfig.ts` yorumu "nginx ve API aynı host:port arkasında" der; repo içinde bunu sağlayan config yok.
- **TLS:** GUI nginx'i 443'te bir sertifikayla da sunar (`certs/`). Sayfa https ise REST `https://`, WS `wss://` olur. trade-data-app REST ve WS süreç içinde TLS sunmaz ([`api.md` §1](../trade-data-app/api.md#1-portlar-ve-dinleyiciler), [`veri-akisi.md` §4.1](../trade-data-app/veri-akisi.md#41-ortak-kurallar)) → https sayfada bir TLS sonlandırıcı şarttır. ❓ doğrulanmadı: nerede yapıldığı. HTTP (port 80) kasıtlı olarak açık, HSTS eklenmez (mtrader-trade-ui `AGENTS.md` → "Decisions and Boundaries").
- **CORS:** GUI origin'i ile REST origin'i farklıysa trade-data-app `cors` regex'i belirler; anahtar yoksa her origin kabul edilir ([`config.md`](../trade-data-app/config.md)). WS `CheckOrigin` her origin'i kabul eder. GUI tarafında CORS ayarı yok.
- Electron/Capacitor (yalnız E): `window.location.host` anlamsızdır; `VITE_API_HOST` build'de verilmelidir. ❓ doğrulanmadı: mobil/Electron build'lerinin hangi host ile alındığı.

## 2. Kimlik doğrulama ve oturum

### 2.1 Login → OTP → token (sunucu sözleşmesi)

- `POST /v1/login` `{username, password}` → `LoginResponse {token, status, isOtpEnabled, errorMessage}`. **Her sonuç HTTP 200**, gerçek sonuç gövdede. Üç durum:
  1. `status:true`, `token` dolu → OTP kapalı, oturum açık.
  2. `isOtpEnabled:true`, `token:""` → SMS gönderildi (veya gönderilemedi, hata yutulur); token yalnız `POST /v1/checkOtpCode` `{otpCode, userName}` ile doğar.
  3. `status:false` + `isOtpEnabled:true` → yeni SMS reddedildi (120 sn dolmadı); telefondaki önceki kod hâlâ geçerli olabilir. **Kasıtlı**, sunucu davranışı.
  4. `status:false` + `isOtpEnabled:false` → hatalı kullanıcı/şifre. `errorMessage` genelde boş.
- OTP 4 hane, 120 sn geçerli; ayrı "yeniden gönder" ucu yok, yeniden gönderme = `/v1/login`'i tekrar çağırmak. Ayrıntı: [`api.md` §2](../trade-data-app/api.md#2-kimlik-doğrulama).
- Token: HS256 JWT, `exp` 48 saat, claim `username` = `Users.id`. **Yenileme ucu yok**; iki GUI de token'ı yenilemez, süre dolunca ilk REST çağrısı 401 alır.
- REST header: `Authorization: Bearer <JWT>`. WS: bağlantı başına ilk çerçeve `{"Type":1,"Body":{"Token":"<JWT>"}}` (§4.1). WS token'ı yalnız authenticate anında doğrulanır; ❓ doğrulanmadı: süresi dolan token'la açık kalan WS bağlantısının yeniden bağlanana kadar veri almaya devam ettiği (koddan çıkarım: sunucuda periyodik kontrol yok).
- Logout ucu **yok**; iki GUI de logout'u yalnız tarayıcıda yapar. Sunucu tarafında token iptal edilemez.

### 2.2 İki GUI'nin uygulaması

| Konu | Yeni GUI | Eski GUI |
|------|----------|----------|
| Login sonucu ayrımı | `app/api/mutations/useLogin.ts` → `LoginOutcome` (`authenticated` / `otp-required` + `reusedPreviousCode`); ret → `AuthRejectedError` (`app/lib/authError.ts`) | `src/pages/LoginPage/LoginPage.tsx` `handleLogin`: yalnız `status`'a bakar. Durum 3'te login ekranında hata toast'ı gösterir (yeni GUI bunu **bilerek** düzeltti, `useLogin.ts` yorumu) |
| Token anahtarı | `accessToken` (`app/lib/storage.ts`) | `token` (`src/utils/TokenUtils.ts`) |
| Nerede | "Beni hatırla" açık → `localStorage`, kapalı → `sessionStorage`; diğeri silinir. Okuma sırası session → local. Varsayılan **açık** (ürün kararı). | Login/OTP sonrası **her zaman** `localStorage.token` + `sessionStorage.token`. "Beni hatırla" yalnız `rememberMe` bayrağını ve `savedUsername`'i yönetir, token'ın kalıcılığını değil. |
| OTP yeniden gönderme için şifre | Bellekte (`app/lib/otpChallenge.ts`); sayfa yenilenince düşer, `/otp` → `/login` | **`sessionStorage.password`'a düz metin** yazılır (`LoginPage.tsx`), `OtpPage.tsx` `handleResendOtp` oradan okur |
| OTP geri sayımı | Tek 120 sn sayaç (`OTP_WINDOW_MS`) | Yalnız resend butonu için 120 sn |
| Otomatik giriş | `_protected.tsx` yalnız token varlığına bakar; geçerlilik ilk 401'de anlaşılır | `LoginPage` açılışta `localStorage.token` varsa `GET /v1/getAllowedStrategies` dener; 200 → `/selectstrategy`, hata → token silinir |
| REST 401 | `client.ts` interceptor → `requestSessionExpiration` (`app/lib/sessionLifecycle.ts`): token silinir, login'e dönüş yolu saklanır (`getSafeReturnPath`) | `handleUnauthorizedError` (`src/ApiService.ts`): yalnız `localStorage.token` silinir, toast, `/login`. `sessionStorage.token` kalır (bug?, bkz. Şüpheli) |
| WS `Unauthorized` | `AuthorizedSocket.handleRawMessage` → `isLoginRejectedMessage` → `requestSessionExpiration` + socket kapatılır | İşlenmez; socket yetkisiz kalır, mesaj gelmez |
| Logout | `useSessionActions.logout` → `clearStoredSessionState` (token, OTP challenge, oturum düzenleri, endeks grupları, emir fotoğrafları) + `socketStore.cleanup` + `queryClient.clear` | `gridActions.tsx` `onSignOut`: `localStorage.token`, `rememberMe` silinir, `sessionStorage.clear()` |
| Şifre sıfırlama | Route `passwordReset/:username/:token`; `_auth` layout bu yolda "zaten girişli" yönlendirmesini atlar; başarıda `clearStoredSessionState` | Route `/passwordReset/:username/:token` (`ChangePasswordPage.tsx`); token ve kullanıcı adını `sessionStorage`'a da yazar |

Şifre sıfırlama sözleşmesi (iki GUI aynı): `POST /v1/forgetPassword` `{userName, email}` → `GuiStatusResponse {status, errorMessage}`; sunucu e-postaya `{hostname}/passwordReset/{username}/{token}` linki koyar. `POST /v1/resetPassword` `{userName, resetToken, newPassword}`. İkisi de token istemez (`excludedMethods`), ikisi de başarısızlıkta 200+`status:false`. Proto'daki `ForgetPasswordRequest.phone` sunucuda okunmaz. Ayrıntı: mtrader-trade-ui `AGENTS.md` → "Authentication and OTP" / "Password reset".

## 3. REST uçları

Hepsi `GuiService`, REST portu. Sunucu davranışı, hata biçimi (200+gövde vs 500) ve hedef servis: [`api.md` §7](../trade-data-app/api.md#7-guiservice-gui-dataproto-gui_apigo--rest-restport). Burada yalnız GUI'nin gördüğü öz ve kullanım.

| Uç | Metod | İstek → yanıt özü | Yeni GUI çağıran | Y | E |
|----|-------|-------------------|------------------|---|---|
| `/v1/login` | POST | §2.1 | `useLogin.ts`, `otpChallenge.ts` (resend) | ✓ | ✓ |
| `/v1/checkOtpCode` | POST | `{otpCode, userName}` → `LoginResponse` | `useCheckOtp.ts` | ✓ | ✓ |
| `/v1/forgetPassword` | POST | §2.2 sonu | `useForgetPassword.ts` | ✓ | ✓ |
| `/v1/resetPassword` | POST | §2.2 sonu | `useResetPassword.ts` | ✓ | ✓ |
| `/v1/getAllowedStrategies` | GET | → izinli strateji adları (`HFT`, `HFT_WARRANT_ADVANCED`, `COLLECTIVE_ORDERS`…); önek eşleşmesi `matchesStrategyKey` | `useAllowedStrategies.ts` (strateji seçimi) | ✓ | ✓ |
| `/v1/getAccounts` | GET | → kullanıcının hesapları | `useAccounts.ts` | ✓ | ✓ |
| `/v1/getAllAccountStrategies` | GET | → `Accounts_Strategies` (kullanıcının hesaplarıyla süzülmüş) | `useStrategies.ts` | ✓ | ✓ |
| `/v1/getSelectedAccountStrategies` | GET | hesap/enstrüman/strateji filtresi | — | — | — (yalnız `API_PATHS`'te) |
| `/v1/getInstruments` | GET | → `instruments[]`: `instrumentId`, `decimalCount`, `tickSize` (**uint64 → string**), `minPrice`/`maxPrice`/`lastPrice` (double, raw), `underlyingInstrument` (yoksa `null`) | `useInstruments.ts` → `instrumentStore` (normalize eder) | ✓ | ✓ |
| `/v1/getIndices` | GET | → endeksler | `useIndices.ts`, Varant Toplu modalı | ✓ | ✓ |
| `/v1/getIndiceInstruments` | GET | query `indice_id` (Y) / `indiceId` (E) | `useIndiceInstruments.ts`, `indiceGroupManifest.ts` | ✓ | ✓ |
| `/v1/getDerivativesByUnderlying` | GET | query `underlying_instrument_id` → varant + vadeli listesi | `useDerivativesByUnderlying.ts`, `WarrantSettingsModal.tsx` | ✓ | ✓ (Varant) |
| `/v1/parseWarrantFile` | POST | `{fileContent (base64), fileName, underlyingInstrumentId?}` → `warrantListJson` + `warnings`; `prevClose` TL | `parseWarrantFile.ts`, `WarrantBulkSettingsModal.tsx`, `warrantBulkBatch.ts` | ✓ | — (Varant Toplu yok) |
| `/v1/getOrdersFromLevel` | GET | query `instrumentId, level, side, account, strategyIdentifier, strategyType`; **`level` = raw fiyat**, kademe indeksi değil → emirler + `isUserOrder`/`isStrategyOrder` | `getOrdersFromLevel.ts` (emir defteri) | ✓ | ✓ |
| `/v1/subscribeToOrderbook` | POST | `{account, strategy_identifier, instrument_id, strategy_type}` → `{success, errorMessage, instrumentId (string), …, orderbookItem {maxPrice, minPrice, lastPrice (float32), position (string)}}`. **Yan etki:** motor strateji yoksa yaratır ve DB'ye yazar | `subscribe.ts` (panel ekleme/geri yükleme) | ✓ | ✓ (`subscribeToSingleHft`/`Theoretic`/`Varant`) |
| `/v1/subscribeToIndice` | POST | `{account, strategy_identifier, indice_id, strategy_type}` | `subscribeToIndice.ts` | ✓ | ✓ |
| `/v1/setAccountStrategy` | POST | motorun `AlgoSetAccountStrategy`'si | `setAccountStrategy.ts` | ✓ | ✓ |
| `/v1/setStrategyCommands` | POST | §5 | `mutations/strategy.ts` | ✓ | ✓ |
| `/v1/getStrategyKeys` | GET | AlgoProd unique key'leri | — | — | — |
| `/v1/sendOrders` | POST | §6 | `sendOrder.ts`, `replaceOrder.ts` | ✓ | ✓ |
| `/v1/subscribeToArbitrage` | POST | tüm vadeler | — | — | — (fonksiyon var, çağıran yok) |
| `/v1/subscribeToSingleArbitrage` | POST | `{account, strategy_identifier, arbitrage_type, instrument_id, spot_instrument_id}` | `mutations/arbitrage.ts` | ✓ | ✓ |
| `/v1/subscribeToArbitrages` | POST | liste | — | — | — |
| `/v1/getAccountArbitrageStrategies` | GET | hesap bazında arbitraj tipleri | `mutations/arbitrage.ts` | ✓ | ✓ |
| `/v1/getAllInstrumentsWithFutures` | GET | `expiryMonth` = sıra indeksi (0,1,2…) | `useInstrumentsWithFutures.ts` | ✓ | ✓ |
| `/v1/uploadArbitrageExcel` | POST | `{fileContent (base64), fileName, validateOnly}` | `features/arbitrage/api/arbitrageExcelApi.ts` | ✓ | ✓ |
| `/v1/downloadArbitrageExcel` | GET | query `strategyType` → `{fileContent (base64), fileName}` | aynı dosya | ✓ | ✓ |
| `/v1/setPanel` | POST | `{strategyType, panelName, isActive, panelDesc, isNew, strategies[]}` | `setPanel.ts` | ✓ | ✓ (`fetch`) |
| `/v1/getPanels` | GET | query `strategyType` | `queries/panels.ts` | ✓ | ✓ (`fetch`) |

- Yeni GUI yolları bazen `/` olmadan yazar (`"v1/sendOrders"`); Axios `baseURL` ile aynı URL'e çıkar.
- Query parametresi isimleri: grpc-gateway v2 hem proto adını (`indice_id`) hem JSON adını (`indiceId`) kabul eder. ❓ doğrulanmadı: v2.7.2'de her iki biçimin de çalıştığı canlıda denenmedi.
- Yanıt bayrağı uca göre değişir: `setStrategyCommands` → `success` (`GuiCommandResponse`, başka alan yok); çoğu uç → `status` + `errorMessage`; `subscribeToOrderbook` → `success` + `errorMessage`. Yeni GUI `isSuccessfulStrategyCommandResponse` ile ikisine de bakar (`app/lib/strategyCommands.ts`).
- Hata türleri: 200+`status:false` (iş kuralı), 401 (token), 500 (`{code, message}`, düz Go `error`; ör. "HFT service is not connected"). Yeni GUI üçünü `describeApiError` / `notifyApiError` ile ayırır; eski GUI hatayı `console.error` + `null` dönüşle yutar.
- **Zaman aşımı:** Y 10 sn (`client.ts`); emir, replace ve "Pozisyon Ekle" bunu ezmez. Zaman aşımına uğrayan istek sunucuda uygulanmış olabilir; otomatik retry **yasak** (mtrader-trade-ui `AGENTS.md` → "Trading and Logging Rules"). E: timeout yok.

## 4. WebSocket feed'leri

### 4.1 Ortak el sıkışma

1. İstemci `ws(s)://<WS_HOST>/ws/v1/<feed>/start`'a bağlanır.
2. Sunucu hemen `{"client_id": <uint32>}` yollar. İstemci bunu görmeden auth göndermez.
3. İstemci `{"Type":1,"Body":{"Token":"<JWT>"}}`.
4. Başarı `{"Type":2,"Body":"Login successful"}`; ret `{"Type":1,"Body":{"Message":"Unauthorized"}}` (bağlantı açık kalır). Sonra subscribe.
5. Diğer hata çerçeveleri de `{"Type":1,"Body":{"Message":…}}` biçimindedir (ör. "HFT service is not connected").

Sunucu ping/pong yapmaz, okuma deadline'ı yoktur; yarı açık bağlantı iki tarafta da tespit edilmez ([`veri-akisi.md` §4.9](../trade-data-app/veri-akisi.md#49-yazma-ve-kopma)). İki GUI'de de uygulama seviyesinde heartbeat yok; yeni GUI bunu **bilerek** frontend'den çözmüyor (`AGENTS.md` → "Sockets heal themselves; nothing may stop that").

### 4.2 Feed tablosu

`RequestType`/`ResponseType` numaraları ve tam alan listeleri: [`veri-akisi.md` §4.1–4.8](../trade-data-app/veri-akisi.md#41-ortak-kurallar).

| Feed (`/ws/v1/…/start`) | Subscribe (Y'nin gönderdiği) | Gelen | Snapshot / replay | Yeni GUI | Y | E |
|-------------------------|------------------------------|-------|-------------------|----------|---|---|
| `best` | `{Type:5, Body:{orderBookIds:[…]}}`; unsub `Type:12 {UnsubscribeAll, OrderBookIDs}` | snapshot `{"<obId>":{BestBid, BestAsk, PriceDivider}}`, güncelleme çıplak `{OrderBookId, Side (66/83), Price (raw), Quantity}` | Her subscribe yalnız gönderilen id'lerin snapshot'ı | `MarketSocket.ts` → `marketDataStore` | ✓ | ✓ (tracker başına ayrı socket) |
| `strategy` | `{Type:4, Body:{strategyType, commands:[{commandType, uniqueKey}]}}` | `{message_type:"Command_Type_<X>Response", unique_key, fields}` | Motor anahtar başına güncel durumu yollar | `CommandSocket.ts` → `strategyDataStore` vb. | ✓ | ✓ (tracker/özet/emir defteri başına ayrı socket) |
| `orders` | `{Type:3, Body:{Types:[…], AccountName:[…]}}` | `MyOrder*` çerçeveleri, `Type` 3–7, 10, 11 | **Her subscribe tüm bellek geçmişini yeniden yollar**, sonlandırıcı çerçeve yok; subscribe filtreyi **değiştirir** | `OrderSocket.ts` (tek sahip, birleşim) | ✓ | ✓ (`gridActions.tsx`) |
| `itch` | `{Type:2, Body:{Account, OrderBookId, StrategyIdentifier, StrategyType}}`; unsub `Type:9` | `Type:8` snapshot (`OrderBook`, `PriceDivider`), seviye güncellemesi `OrderLevelMessage` | Her `Type:2` tam snapshot. Başarısız subscribe'da **hiçbir şey dönmez** | `ItchSocket.ts` (tüm emir defterleri tek socket) | ✓ | ✓ (`WebSocketContext` singleton) |
| `bounds` | `{Type:7, Body:{OrderBookIDs}}`; unsub `Type:14` | `{type:13, orderbookId, maxAskPrice, maxAskLot, minBidPrice, minBidLot, priceDivider, timestamp}` | Subscribe'da snapshot | `BoundsSocket.ts` → `boundsDataStore` (Tavan/Taban Lot) | ✓ | ✓ (Tavan/Taban tracker) |
| `equilibrium` | `{Type:6, Body:{OrderBookIDs}}`; unsub `Type:13` | `{type:12, orderbookId, equilibriumPrice, bestBidPrice, bestAskPrice (raw), …Quantity (lot)}` | **Snapshot yok**; satır ilk seans güncellemesine kadar boş | `EquilibriumSocket.ts` (Teorik Fiyat) | ✓ | ✓ (`TheoreticForm.tsx`) |
| `passive-orders` | `{Type:8, Body:{AccountName:[…], Types:[strategyType]}}` | Her zaman tam snapshot `{Type:14, Orders:[MyOrderAdd]}` | Her canlı emir olayında yeniden tam snapshot; `IsActive` hep `false` gelir | `components/dockview/StrategyPassiveOrders.tsx` (socketStore dışında) | ✓ | ✓ (`StrategyPassiveOrders.tsx`, `VarantPassiveOrders.tsx`) |

Feed'e özgü sözleşme notları:
- **Alan adları büyük/küçük harf duyarsız** (Go `encoding/json`), bu yüzden `orderBookIds` ile `OrderBookIDs` ikisi de çalışır. Sunucu → istemci yönünde adlar Go adıdır (PascalCase), `json` tag'li olanlar (`bounds`, `equilibrium`, `strategy`) camel/snake'tir.
- `strategy` subscribe'ındaki `messageType` ve `fields` alanlarını (Y `StrategyCommandMessage` tipi, `requestHftSummary`) sunucu **okumaz**: `CommandsRequest` yalnız `CommandType` + `UniqueKey` taşır (`pkg/gui/messages/base_command.go`). Strateji komutu WS'ten gönderilemez; yol REST'tir (§5).
- `strategy` `commandType` değerleri (Y): 1 strateji durumu, 3 bakiye (varsayılan `[1,3]`, `requestStrategyStatus`), 5 özet (`SUMMARY_<hesap>`, `BALANCE_<hesap>` ile 3; arbitraj özetinde `uniqueKey:""`; VWAP özetinde `vwap-summary:<client_id>`), 8 tavan durumu (`requestMaxPriceStates`). 8, sunucunun `StrategyCommandType` sabitlerinde yok (0–6); uint8 olarak motora geçer.
- `strategy` `fields` içindeki değerler **protojson**'dır: 64-bit sayı string, ayarlanmamış alan `{}`. Y `CommandSocket.normalize*Field` ile hem `{value:x}` hem çıplak değeri, hem string hem number'ı kabul eder; `{}` "varsayılan" demektir, sıfır değil (`unwrapSocketValue`).
- `orders` `Types`: Y `ORDER_SUBSCRIBE_STRATEGY_TYPES` = `[1–10, 12, 13, 14, 15]` (`app/lib/tradingConstants.ts`); E `[1–10, 13, 14]` (12 HFT_User ve 15 yok).
- `itch` yönlendirmesi: önce `OrderBookId`, sonra `OrderBookKey`. Güncelleme serbest-emir anahtarıyla (`…_1`) da gelebilir; sunucu HFT için de `StrategyType=1` yazar. E yalnız birebir `OrderBookKey` eşleşmesine bakar.
- `itch` snapshot'ındaki `PriceDivider`, `best` snapshot'ındaki `PriceDivider`: Y kullanmaz, ölçeği `getInstruments.decimalCount`'tan alır. E emir defterinde snapshot'ın `PriceDivider`'ını kullanır (`OrderBook.tsx` `transformBackendDataToOrderData`, varsayılan 100).

### 4.3 Yeni GUI socket yönetimi

Kurallar mtrader-trade-ui `AGENTS.md`'de ("WebSocket and Performance Constraints" ve alt başlıkları); burada yalnız sözleşmeye dokunan özet:
- `socketStore` altı socket nesnesi tutar (market, command, order, bounds, equilibrium, itch). Workspace config'i hangilerinin bağlanacağını söyler (`getWorkspaceSockets`); order hep açık, itch ilk emir defteri paneliyle açılır ve son panel kapanınca kapanmaz.
- Ortak taban `app/api/socket/AuthorizedSocket.ts`: yeniden bağlanma **sınırsız**, jitter'lı üstel geri çekilme (500 ms × 2ⁿ, tavan `reconnectInterval` 20 sn); 10. denemede bir kez bildirim; `authTimeout` 10 sn içinde `Login successful` gelmezse kapatıp yeniden dener; `online` olayında yeniden bağlanır. Kopan bağlantının kuyruğu **atılır** (emir komutu yeniden oynatılmaz); abonelik niyetini her socket sınıfı tutar ve `onAuthorized`'da yeniden yollar.
- `OrderSocket` aboneliği tek sahiplidir (`registerSubscription`), her yetkilendirmede birleşimi tek `Type:3` olarak yollar; replay çerçeveleri `{ isReplay }` ile işaretlenir (wire'da ayırt edici alan yok).
- `ItchSocket` `Type:2`'yi kuyruğa koymaz; 15 sn "veri yok" zamanlayıcısı başarısız subscribe'ın tek sinyalidir; "Yenile" `Type:9`+`Type:2` yollar.
- **İstisna, pasif emirler paneli:** `StrategyPassiveOrders.tsx` kendi `WebSocket`'ini açar; en çok **3** yeniden deneme (500 ms × 2ⁿ, tavan 20 sn), sonra durur; `online` olayında sayaç sıfırlanır. Token, effect başında bir kez okunur. `AuthorizedSocket`'in sınırsız iyileşme kuralı bu panele uygulanmaz. ❓ doğrulanmadı: kasıtlı mı.
- Bağlantı göstergesi ve alarm yalnız workspace'in kullandığı çekirdek socket'leri sayar (`getRequiredCoreSockets`); bounds, equilibrium ve itch dahil değil.

### 4.4 Eski GUI socket yönetimi

- Neredeyse her panel kendi socket'ini açar (`new WebSocket` ~27 yerde: tracker formları `best` + `strategy` + Tavan/Taban'da `bounds`, özet görünümleri `strategy`, `OrderBook.tsx` `strategy`, `gridActions.tsx` `orders`). Yalnız `itch`, `WebSocketContext` + `WebSocketService.getInstance` ile tek socket'tir.
- **Otomatik yeniden bağlanma yok.** `gridActions.tsx` `orders` socket'i kapanınca alarm sesi çalar ve gösterge kırmızı olur; yeniden bağlanma operatörün bağlantı düğmesiyle (`handleConnectionToggle`) olur. Diğer socket'ler kapandığında sessizce ölü kalır; panel yeniden açılana kadar veri gelmez.
- `WebSocketService.subscribe` mesajı `subscriptions` listesine ekler, `unsubscribe` listeden çıkarmaz; liste yalnız aynı nesne yeniden yetkilenirse yeniden oynatılır (bu da otomatik olmaz).
- El sıkışma `if (response.client_id)` ile yapılır; `client_id` 0 ise auth hiç gönderilmez (bkz. Şüpheli).

## 5. Strateji komut sözleşmesi (`POST /v1/setStrategyCommands`)

Gövde (`GuiStrategySetCommandRequest`, `api/protobuf-spec/gui-data.proto`):

```json
{
  "commandType": 1,
  "uniqueKey": "<orderbookId>_<hesap>_<strategyId>_<strategyType>",
  "strategyType": 4,
  "fields": {
    "Strategy_Start": {"@type": "type.googleapis.com/servicemodels.GuiBoolValue", "value": true},
    "Orderbook_Id":   {"@type": "type.googleapis.com/servicemodels.GuiLongValue", "value": 1234},
    "Account":        {"@type": "type.googleapis.com/servicemodels.GuiStringValue", "value": "<HESAP>"}
  }
}
```

- `fields` = `map<string, google.protobuf.Any>`. İzinli `@type`'lar: `GuiBoolValue`, `GuiIntValue` (int32), `GuiLongValue` (int64), `GuiDoubleValue`, `GuiStringValue`, `GuiListValue {values:[Any]}`, `GuiMapValue {values:{k:Any}}`. Bilinmeyen `@type` gateway'de protojson çözümünde reddedilir. Sunucu `ConvertFields` ile client tiplerine çevirir, sonra `checkStrategyAttributesType` her alanın tipini `StrategyAttributes.valueType` ile karşılaştırır; uyuşmazlık → **HTTP 500**. Alan adları motorun sözleşmesidir (`HftSrvProd/src/Globals/GuiConstants.h`).
- Yeni GUI zarfı `wrapGuiValue(value, "Long"|"Int"|"Bool"|"String"|"Double")` ile kurar (`app/lib/helpers.ts`; VWAP `features/vwap/vwapContract.ts`). TS tipi `TypedValue` (`app/types/RequestStructs.ts`). Eski GUI `createTypeNumber/String/Bool/Map/List` (`src/Functions/GeneralFunctions.tsx`) ve string değerli `Type` enum'u ile aynı JSON'u üretir.
- `GuiLongValue.value` int64: protojson girdide number da string de kabul eder; iki GUI number gönderir (2⁵³ altı).
- Yanıt `{"success": bool}`; `errorMessage` alanı **yok**. Motor hatası 500 + `message` olarak gelir.
- Motor seçimi `strategyType`'a göre (`getApplicationFromStrategyType`): 4, 8, 9, 12, 13, 14, 15 → HFT; 2, 3, 5, 6, 7, 10 → AlgoProd. Tanımsız → "Unknown strategy type" (500).

**`StrategyType` (wire, değiştirilmez)** — `GuiStrategyType` 0–15: 1 Algo_User (serbest emir), 2 Warrant, 3 AKD, 4 HFT, 5 MovingAverage, 6 Arbitrage, 7 VWAP, 8 TheoreticalPrice, 9 MaxPrice (Tavan), 10 FundTracker, 11 OrderChase, 12 HFT_User (HFT serbest emir), 13 HFT_Warrant (Varant), 14 MinPrice (Taban), 15 HFT_WarrantAdvanced (Varant Toplu). Yeni GUI enum'u yalnız workspace'leri tutar (`app/types/index.ts` `StrategyType`: 4, 6, 7, 8, 9, 10, 13, 14, 15); serbest tipler `FREE_STRATEGY_TYPE_*` (1, 12). "Toplu Emirler" bir StrategyType değildir (`COLLECTIVE_ORDERS_WORKSPACE`).

**`commandType` (REST zarfı)** — proto `GuiCommandType`: 1 StrategyRequest (ayar/başlat/durdur), 2 PackageRequest (arbitraj/fon paketi), 3 BalanceRequest (Y'de "Pozisyon Ekle", `app/lib/addPositionCommand.ts`), 4 OrderRequest (yalnız `GuiSendOrders` içinden), 5 SummaryRequest, 6 ExecuteUnderlyingRequest (`app/lib/executeUnderlyingCommand.ts`, arbitraj pasif emir artır/çalıştır/azalt). Proto dışı, motorun tanıdığı: **7 CancelAllOrders, 9 ClosePosition** (`app/lib/cancelAllOrdersCommand.ts`; yalnız HFT motoru — AlgoProd "Invalid Message Type" döner, bu yüzden Y düğmeyi yalnız HFT ailesi workspace'lerinde gösterir). protojson açık enum olduğu için 7/9 sayı olarak geçer.

**Tam payload kuralı (Y):** her strateji komutu stratejinin **tüm** ayar alanlarını taşır; motor eksik alanı varsayılana çeker, yani kısmi payload diğer ayarları siler. Yeni GUI her yolu (modal, inline hücre, toplu işlem, emir defteri kontrolleri) aynı `create<X>Payload` kurucusundan geçirir ve snapshot yüklenmeden komut göndermez (Varant Toplu'da kesin kural; Varant'ta bilinen boşluk). Çakışan iki komut birbirini geri alabilir; **kabul edilmiş risk** (2026-10-21). Kaynak: mtrader-trade-ui `AGENTS.md` → "Strategy Architecture" ve "Decisions and Boundaries".

**Eski GUI farkı:**
- Tracker başına elle kurulmuş alan listeleri (ör. `TavanTrackerForm.tsx`); aynı strateji için farklı yollar farklı alan kümeleri yollar. ❓ doğrulanmadı: her yolun tam payload gönderip göndermediği tek tek kontrol edilmedi.
- Yanıtı `response.status` ile kontrol eder (`gridActions.tsx` toplu iptal, `VarantTrackerForm.tsx`); bu alan yanıtta yok (bkz. Şüpheli).

## 6. Emir gönderme (`POST /v1/sendOrders`)

Gövde `{"orders": [GuiEnterOrderRequest…]}`; yanıt `GuiStatusResponse {status, errorMessage}`. Sunucu dalları ve kademe açılımı: [`api.md` §7 "GuiSendOrders dalları"](../trade-data-app/api.md#7-guiservice-gui-dataproto-gui_apigo--rest-restport).

| Alan | Değerler / birim |
|------|------------------|
| `order_type` (`OrderType`) | 1 MORNING (sabah, 09:40), 2 OPENING (açılış), 3 STRATEGY, 4 EVENING (akşam). Y ayrıca **5** (`ORDER_TIME_REGULAR`) gönderir (teorik emir); proto'da 5 yok, açık enum olarak geçer. **1/2/4 → toplu emir dalı (order-service)**, diğerleri → motora `Command_Type_OrderRequest` |
| `order_event_type` | 1 ENTER, 2 CANCEL, 3 REPLACE (Y'de aktif/pasif ve güncelle de), 4 THEORIC |
| `side` | **1 BUY, 2 SELL, 3 SHORT** (`SEND_SIDE_*`). WS'teki 66/83/84 değil. Toplu emir kademe açılımında 3 → "Order side is unknown" (500) |
| `protocol` | `GuiProtocol` **1 OUCH, 2 FIX** (`ouch-data.proto` `Protocol` 0/1 ile karıştırma) |
| `time_in_force` | 1 DAY, 2 IOC (KİE), 3 FOK (GİE) |
| `regular_order_type` | 2 MARKET, 3 LIMIT, 4 piyasadan limite (PKP); 2/4'te `price: 0` |
| `price`, `expected_price` | **raw** (TL × 10^decimalCount), uint64 |
| `quantity` | lot, uint64 |
| `order_id` | uint64; Y socket'ten gelen string'i olduğu gibi geri yollar (`MAX_SAFE_INTEGER` korunur) |
| `level_count` | Kademe sayısı. Toplu emirde (1/2/4) ITCH açıksa sunucu emri `level_count` kademeye böler (alışta aşağı, satışta yukarı, her kademe `GetTickSize`); **0 ise hiç emir oluşmaz**. Strateji dalında motora `Order_Lvl_Count` olarak geçer |
| `is_main_order`, `main_order_id` | Kademe ailesi; ENTER'da sunucu yeniden yazar |
| `is_yip` | OPENING emrinde Yakın İzleme Pazarı bayrağı. Y Toplu Emirler gönderir; E göndermez |
| `unique_key` | `<orderbookId>_<hesap>_<strategyId>_<strategyType>`; hesap = stratejinin **kayıtlı** hesabı, emrin çıkış hesabı değil (Y `SendOrderPanel.tsx`) |
| `custom_data` | Toplu emirde Y `buildCollectiveCustomData` (OrderType, StrategyIdentifier, StrategyType) |

Yeni GUI emir kurucuları: `components/dockview/SendOrderPanel.tsx` (`order_type: 3`, `order_event_type: 1`), `components/dockview/collective-order/collectiveOrderPayloads.ts` (1/2/4, `level_count`, `is_yip`), `components/dockview/theoretical-price/theoreticalPricePayload.ts` (5 + 4 THEORIC + `expected_price`), iptal/replace modalları (`protocol: 1`). Gönderimden önce `confirmPriceSanity` son payload'daki raw fiyata bakar.

Eski GUI: `src/ApiService.ts` `sendOrder`/`cancelOrder`/`replaceOrder` aynı uca gider. Fiyatı çoğu formda **sabit ×1000** ile çevirir (`OrderForm.tsx`, `SendOrderModal.tsx`, `CancelReplaceOrderModal.tsx`, `TheoreticForm.tsx`, `AddPositionModal.tsx`; ~50 yer); `getInstrumentPriceDivider` yalnız bazı gösterim yollarında kullanılır.

## 7. JSON lehçesi ve ölçek tablosu

| Kanal | Lehçe | 64-bit sayı | Enum | Boş/eksik |
|-------|-------|-------------|------|-----------|
| REST yanıtı | protojson, `EmitUnpopulated` | **string** (`"tickSize":"0"`, `instrumentId` uint64 olan yanıtlarda string) | **isim** (`"instrumentMarket":"…"`) | sıfır değerler yazılır, alt mesaj `null` |
| REST isteği | protojson, `DiscardUnknown` | number veya string kabul | isim veya sayı (tanımsız sayı da geçer) | bilinmeyen alan **sessizce atılır** — yazım hatası hata vermez |
| WS çerçevesi | Go `encoding/json` | number | sayı | Go sıfır değeri |
| WS `strategy` `fields` | protojson (`@type` silinmiş) | **string** | isim | `{}` = ayarlanmamış |

TS tipleri bunu her yerde söylemez (ör. `SubscribeToStrategyResponse.instrumentId: number`); sayı beklenen REST alanını `Number(...)` ile oku.

| Alan | Birim / ölçek | Not |
|------|---------------|-----|
| Fiyat (emir, seviye, best, ITCH, `sendOrders.price`, `Order_Price`) | raw = TL × `10^decimalCount` | `decimalCount` pratikte 2 (VİOP) veya 3 (pay). Y: `app/lib/priceScale.ts`, enstrüman bilinmiyorsa **3'e (÷1000) düşer** (`DEFAULT_PRICE_DECIMALS`) |
| `getOrdersFromLevel.level` | raw fiyat | kademe indeksi değil |
| `getInstruments.minPrice`/`maxPrice` | raw, VERDA TL × **1000** sabit | [`sema.md`](../trade-data-app/sema.md); decimalCount ≠ 3'te uyumsuz |
| `bounds.maxAskPrice`/`minBidPrice` | aynı ×1000 sabit | `priceDivider` mesajda var |
| `tickSize` (instrument, itch snapshot) | raw | REST'te string |
| `subscribeToOrderbook.orderbookItem.*Price` | float32 | ❓ doğrulanmadı: raw mı TL mi; 2²⁴ üstü raw değerde float32 hassasiyeti kaybolur |
| `parseWarrantFile.prevClose` | **TL** (raw / 10^decimal) | gün içinde son fiyat |
| Varant `Derivative_Orders[].userPrice` | **TL ondalık**; motor ×1000 yapar | `Criteria_Price` ise dayanağın raw ölçeği |
| `Theo_Price` | TL × 1000 sabit (motor `lastThPrc * 1000`) | enstrüman ölçeğiyle bölünmez |
| `expected_price` | raw, `price` ile aynı bölen | Y `theoreticalPricePayload.ts`; `RequestStructs.ts` yorumu "TL × 1000" der (bkz. Şüpheli) |
| K/Z, açık maliyet | fiyat × lot, enstrümanın raw ölçeği | farklı enstrümanların raw tutarları toplanmaz |
| Miktar, lot | lot | `Previous*OrderCount` adına rağmen lot |
| `Side` | WS ve komut `fields`: 66 B / 83 S / 84 T; REST `sendOrders.side`: 1/2/3 | HFT'den gelen emir olaylarında 1/2/3 de görülebilir |
| Ayar alanları (süre, yüzde) | alan başına: sn ×10, ms ×1000, % ×10 veya ×100 | mtrader-trade-ui `AGENTS.md` → "Strategy Architecture"; `Cost_Timeout_Ms` wire'da ms |
| Emir olayı `Timestamp` | ns'den türetilmiş | [`veri-akisi.md` §4.3](../trade-data-app/veri-akisi.md#43-wsv1ordersstart--emir-olayları) |
| FUND_TRACKER | TL × 100 ve TL × 1000 yan yana | ölçek sisteminin dışında, kasıtlı |

Sabit ×1000'in kasıtlı tutulduğu yerler ve gerekçeleri: mtrader-trade-ui `AGENTS.md` → "Price Scale".

## Şüpheli

- **bug? (E) `client_id: 0`'da el sıkışma kilitlenir.** trade-data-app `clientCount` 0'dan başlar (`ws_listener.go`), yani süreç açıldıktan sonraki ilk WS bağlantısı `{"client_id":0}` alır. Eski GUI `if (response.client_id)` ile kontrol ettiği için auth göndermez; o socket yetkisiz kalır ve otomatik yeniden bağlanma olmadığından ölü kalır. Yeni GUI `typeof` ile kontrol eder (`messageGuards.ts` `isClientIdMessage`), etkilenmez.
- **bug? (E) `setStrategyCommands` başarısı hiç görünmez.** Yanıt yalnız `{"success":…}` taşır; eski GUI `response.status`'a bakar (`gridActions.tsx` toplu iptal 7/9, `VarantTrackerForm.tsx`). Toplu iptal başarılı olsa da "Emirler iptal edilemedi: Bilinmeyen hata" toast'ı çıkar. ❓ doğrulanmadı: canlıda gözlenmedi.
- **bug? (E) VİOP'ta fiyat 10× sapar.** Eski GUI emir formları fiyatı sabit ×1000 ile raw'a çevirir; `decimalCount=2` enstrümanda gönderilen fiyat 10 kat büyük olur. Prod `main` eski GUI'dir. ❓ doğrulanmadı: VİOP emrinin hangi eski GUI ekranından girildiği.
- **bug? (E) 401 sonrası sessionStorage token'ı kalır.** `handleUnauthorizedError` yalnız `localStorage.token`'ı siler; `getToken` önce `sessionStorage`'a baktığı için sonraki çağrılar süresi dolmuş token'la devam eder (login ekranı yeni token yazana kadar).
- **güvenlik (E) şifre `sessionStorage`'da düz metin** (`LoginPage.tsx`, OTP resend için). Yeni GUI bunu bellekte tutar.
- **doğrula (Y) pasif emirler paneli 3 denemeden sonra yeniden bağlanmayı bırakır** (`StrategyPassiveOrders.tsx`). `AuthorizedSocket`'in "sınırsız iyileşme" kuralıyla çelişir; panel `socketStore` dışında olduğu için AGENTS.md kuralı kapsamıyor olabilir.
- **eksik (Y) `socketStore.sendCommand` / `CommandSocket.sendCommand`** WS üzerinden `fields`'lı komut yollar; sunucu `CommandsRequest`'te `fields` okumaz, yani komut motora ulaşmaz. Workspace'te çağıranı bulunamadı (ölü kod adayı). `requestHftSummary`'deki `messageType` de okunmaz.
- **doğrula (Y) `SendOrderItemRequest.expected_price` yorumu** "ham birimde (TL × 1000)" der; kod (`theoreticalPricePayload.ts`) enstrüman böleniyle (`toWirePrice(…, divider)`) çevirir. Biri yanlış; motorun beklentisi `HftSrvProd` teorik emir kodunda doğrulanmalı.
- **doğrula (Y) AGENTS.md "HFT_WARRANT_ADVANCED" bölümü eskimiş olabilir:** "`getApplicationFromStrategyType` ve `ConvertStrategyType`'ta 15 için case yok, development'ta değil" der; trade-data-app `1cca9a8`'de (`development`) iki fonksiyonda da 15 case'i var.
- **doğrula** prod'da REST/WS'nin GUI origin'inden trade-data-app'e nasıl ulaştığı ve TLS'in nerede sonlandığı (§1). GUI nginx'inde proxy yok; env'siz build origin'e gider.
- **doğrula** `subscribeToOrderbook.orderbookItem` fiyatlarının birimi (float32; `Instrument.LowestPrice/HighestPrice/LastPrice` float64'ten cast).
- **doğrula (E) `orders` aboneliğinde 12 (HFT_User) ve 15 yok:** HFT serbest emirleri eski GUI emir geçmişine düşmüyor olabilir.
