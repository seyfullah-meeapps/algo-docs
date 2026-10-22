---
kapsam: trade-data-app'in API yüzeyi — sunduğu gRPC servisleri ve her RPC (REST yolu, çağıran, davranış), kimlik doğrulama, REST/JSON lehçesi, istemci olduğu sözleşmeler (order-service, strateji motorları)
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: order-service          # çağıran tespiti
    branch: development
    commit: b86c0cf
  - repo: HftSrvProd             # çağıran tespiti
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading     # çağıran tespiti
    branch: development
    commit: 0dc32a7
  - repo: mtrader-trade-ui       # çağıran tespiti
    branch: development
    commit: b0474c3
  - repo: mtrader-frontend-apps  # çağıran tespiti (admin paneli)
    branch: main
    commit: db10c12
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app — API yüzeyi

Giriş ve paket haritası: [`README.md`](README.md). WebSocket feed'leri: [`veri-akisi.md`](veri-akisi.md). Tablolar: [`sema.md`](sema.md). VERDA/AKD/BYF/AWS: [`entegrasyonlar.md`](entegrasyonlar.md). Config anahtarları: [`config.md`](config.md).

Kod yerleri: proto'lar `api/protobuf-spec/` (sunucu) ve `api/client-spec/` (istemci); implementasyon `pkg/servicemodels/*_api.go`; sunucu kurulumu `pkg/servicemodels/server.go` (`server.StartNonBlocking`); auth `pkg/util/helper.go`; dış bağlantılar `pkg/gui/connections/`.

"Çağıran" sütunu, istemci repolarında stub çağrısı aranarak bulundu (yukarıdaki commit'ler). Bulunamayan yerde "—" yazılır.

## 1. Portlar ve dinleyiciler

| Dinleyici | Config | Örnek `config.json` | Ne sunar |
|-----------|--------|---------------------|----------|
| gRPC | `server.port` | 6620 | 6 servisin hepsi: `DataService`, `GuiService`, `AlgoService`, `LimitControlService`, `RiskManagerService`, `AdminService`. TLS yok. |
| REST (grpc-gateway) | `server.restPort` | 6621 | Yalnız `GuiService` (http annotation'ları `gui-data.proto` içinde). `cors(GzipMiddleware(router))` |
| Admin REST (grpc-gateway) | `server.adminApiPort` | 6688 | Yalnız `AdminService` (kurallar `admin_ui.yaml`, `buf.gen.yaml` → `grpc_api_configuration`). `cors(adminRouter)`, gzip yok. |
| WebSocket | `gui.port` | — | Bkz. [`veri-akisi.md`](veri-akisi.md) |

- Tüm portlar `":<port>"` ile bağlanır, yani tüm arayüzleri dinler.
- Gateway, gRPC sunucusuna `server.hostname:server.port` adresinden insecure bağlanır (`grpcgo.DialContext`). `server.hostname` yanlışsa REST çalışmaz, gRPC çalışır.
- `DataService`, `AlgoService`, `LimitControlService` ve `RiskManagerService` için REST yolu yoktur; bunlar yalnız gRPC'dir.
- gRPC sunucusunda `MaxRecvMsgSize` ayarlanmamış (varsayılan 4 MB). Dosya taşıyan REST çağrıları (`uploadArbitrageExcel`, `parseWarrantFile`) da gateway üzerinden bu sınıra takılır. ❓ doğrulanmadı: büyük dosyayla denenmedi.
- Panic recovery interceptor'ı yok. Handler içindeki bir panic process'i düşürür.

## 2. Kimlik doğrulama

**Token:** `util.Helper.GenerateToken`. HS256 JWT, claim `username`, `exp` = 48 saat. Anahtar config'teki `secretKey` (değeri burada yazılmaz). Tüm servisler **aynı anahtarı ve aynı claim'i** kullanır.

**Interceptor:** `Helper.UnaryInterceptor` ve `Helper.StreamInterceptor` gRPC sunucusuna kayıtlıdır; REST istekleri de gateway üzerinden buradan geçer.
- `authorization` metadata'sı okunur, `"Bearer "` öneki varsa atılır (C++ istemcileri öneksiz yollar, Go istemcileri `Bearer` ile).
- Token yoksa veya geçersizse `codes.Unauthenticated` döner (REST'te 401). Metadata hiç yoksa `codes.InvalidArgument` döner.
- Yalnız imza ve süre kontrol edilir. **Rol veya servis ayrımı yoktur:** herhangi bir login'den alınan token, altı servisin hepsinde geçerlidir (bkz. §11).
- Unary çağrılar `requestlog.Record` ile loglanır; stream'ler loglanmaz. Request log ayrıntısı: [`config.md`](config.md).
- REST'te `Authorization` header'ı gateway tarafından `authorization` metadata'sına aktarılır (grpc-gateway v2.7.2 varsayılanı). `requestlog.GatewayMetadata` ayrıca istemci ve sunucu IP/port bilgisini ekler.

**`excludedMethods`** (token istemeyen metotlar):

| Metot | Not |
|-------|-----|
| `/servicemodels.DataService/Login` | order-service |
| `/servicemodels.AlgoService/AlgoLogin` | HFT, AlgoProd |
| `/servicemodels.GuiService/GuiLogin`, `GuiCheckOtpCode`, `GuiForgetPassword`, `GuiResetPassword` | UI |
| `/adminui.v1.AdminService/Login` | Admin paneli |
| `/servicemodels.LimitControlService/LimitLogin` | — |
| `/servicemodels.RiskManagerService/Login` | **Böyle bir RPC yok.** `RiskManagerService` login sunmaz. order-service, `DataService.Login` token'ını kullanır. |

**Token'daki `username` claim'inin anlamı servise göre değişir:**

| Login | Doğrulanan tablo | Şifre | `username` claim'i |
|-------|------------------|-------|--------------------|
| `DataService.Login`, `AlgoService.AlgoLogin`, `LimitControlService.LimitLogin` | `Application_Users` | MD5 hex | uygulama kullanıcı adı |
| `GuiService.GuiLogin` / `GuiCheckOtpCode` | `Users` | MD5 hex | **`Users.id` (string)** |
| `AdminService.Login` | `Admins` | MD5 hex | admin kullanıcı adı |

- GUI handler'ları (`GuiGetAccounts`, `GuiGetPanels` vb.) claim'i `strconv.Atoi` ile kullanıcı id'sine çevirir. Bu yüzden admin veya uygulama token'ı bu handler'larda hata verir.
- `AlgoService.SetFundData`, `GetFundData`, `SetArbitrageData`, `GetArbitrageData` ve `GetAllFundsData` claim'i uygulama kullanıcı adı olarak DB'ye geçirir.

**GUI giriş akışı (`GuiLogin`):**
- `Users.otpEnabled` kapalıysa token hemen döner.
- Açıksa token boş döner ve `isOtpEnabled=true` olur. 4 haneli kod üretilir (`GenerateOtpCode`, `math/rand`), `Users.lastOtp` alanına yazılır ve AWS SNS ile SMS gönderilir.
- Kod 120 sn geçerlidir (`GuiDB.CheckOtpCode`). 120 sn dolmadan yeni kod istenirse `SetOtpCode` reddeder ("2 minutes have not passed…").
- `GuiForgetPassword`: `crypto/rand` ile 32 hex karakterlik bir token üretir, `Users.resetPasswordToken` alanına yazar ve e-posta gönderir. `GuiResetPassword` token eşleşirse şifreyi değiştirir. Reset token'ının süresi yoktur.

**Admin farkı:** `AdminService.Login` aynı `GenerateToken`'ı kullanır. `CheckAuthentication` boş bir handler'dır; yalnız interceptor'dan geçip geçmediğini sınar (panelin token geçerlilik kontrolü). Admin handler'larında ek yetki kontrolü yok.

## 3. REST/JSON lehçesi, hata biçimi, CORS

- `server.go`'da `WithMarshalerOption` yok, yani grpc-gateway v2.7.2 varsayılanı geçerli: `protojson` + `EmitUnpopulated: true` + `DiscardUnknown: true`. Bunun sonuçları:
  - Sıfır değerli alanlar da gövdeye yazılır (`false`, `0`, `""`). Set edilmemiş alt mesaj `null` olur.
  - 64-bit tamsayılar (`int64`/`uint64`) JSON'da **string** olur. Enum'lar **isim** olarak gelir (girdi olarak sayı da kabul edilir).
  - Alan adları lowerCamelCase (`json_name`) olur. `admin_ui.proto` açıkça snake_case `json_name` verir (`user_id`, `order_user`).
  - Bilinmeyen alanlar sessizce atılır. UI'da alan adı yazım hatası hata vermez, alan boş gelir.
- Hata biçimi: Handler bir `error` dönerse gateway gRPC kodunu HTTP koduna çevirir ve gövdeye `{"code":…,"message":…,"details":[]}` yazar. Düz `errors.New`/`fmt.Errorf` hatası `codes.Unknown` sayılır ve **HTTP 500** olur.
- **HTTP 200 + gövdede hata:** Birçok GUI handler'ı hatayı `status/success=false` + `errorMessage` olarak döner ve `error` dönmez. İstemci HTTP koduna değil gövdedeki bayrağa bakmalıdır. Hangi uçların böyle davrandığı §7 tablosunda "200+gövde" olarak işaretlidir.
- CORS (`cors`):
  - Config `cors` değeri `"*"` ise her `Origin` kabul edilir. Değilse regex olarak `regexp.MatchString` ile eşleştirilir; regex çapasızdır, kısmi eşleşme yeter.
  - Kabul edilen origin geri yansıtılır. `Allow-Methods: GET, POST, PUT, DELETE`, `Allow-Headers: Content-Type, Authorization`, `Expose-Headers: X-Total-Count`.
  - `OPTIONS` istekleri origin'e bakılmadan boş 200 ile kesilir.
- Gzip: REST portunda istemci `Accept-Encoding: gzip` gönderirse yanıt gzip'lenir. Admin portunda gzip yok.
- Admin listeleri react-admin tarzıdır:
  - Query'de `filter`, `range`, `sort` JSON string olarak gelir (ör. `range=[0,24]`, `sort=["username","DESC"]`).
  - Toplam satır sayısı `X-Total-Count` header'ına yazılır (`setPayloadSizeHeader` → `withContentRangeOption`).
  - Sayfalama DB'de değil bellekte yapılır: tüm liste çekilip dilimlenir.

## 4. DataService (`ouch-data.proto`, `ouch_api.go`) — yalnız gRPC

Çağıran: order-service (`Data/DatabaseClient`, `Service/Network/*`). Aşağıdaki 15 RPC'nin order-service'te sarmalayıcısı var; `GetAllIndices` ve `GetIndiceInstruments`'i çağıran yok ([order-service/kalicilik-ve-config § A1](../order-service/kalicilik-ve-config.md#a1-dataservice-istemcisi-datadatabaseclient)).

| RPC | Ne yapar / önemli davranış |
|-----|----------------------------|
| `Login` | `Application_Users` doğrulaması, JWT. **Yan etki:** ilk başarılı login `guiChan`'a sinyal yollar ve `main` GUI tarafını başlatır (dış bağlantılar + WS). Sonraki login'ler "Already Loggedin" loglar. Başarısızlıkta: DB hatası varsa error döner; kullanıcı bulunamazsa `nil, nil` döner. ❓ doğrulanmadı: grpc-go bu `nil` yanıtı istemciye boş mesaj olarak mı iletir. Kullanıcı adı ve şifre **düz metin loglanır**. |
| `GetOuchUsers` / `GetFixUsers` | `Ouchs` + hesaplar + hesap stratejileri. OUCH/FIX şifresi ve `pendingPassword` **düz metin** döner (order-service oturum açmak için kullanır). FIX'te ek olarak SenderCompId/TargetCompId/SubId döner. |
| `UpdateOrderUserPassword` | FIX şifre yenileme. `Ouchs.password` ve `pendingPassword` tek UPDATE ile yazılır; şifre loglanmaz. `username`/`password` boşsa hata. |
| `GetStrategies` | `Strategies` (id, ad) |
| `GetInstruments` | `Instrument` tablosu (tavan/taban, `maxOrderVal`, `decimalCount`, `isBrutTakas`, pazar). Fiyat ölçeği: bkz. [`sema.md`](sema.md). |
| `GetPositions` | `Positions` + strateji/hesap adları |
| `SetPosition` | `INSERT … ON DUPLICATE KEY UPDATE position=position+?`: gelen değer **delta** olarak eklenir, mutlak değer yazılmaz. `price` üzerine yazılır. `instrumentId` sorguda kullanılmaz (anahtar `strategy`). |
| `GetOrders(orderType)` | `Orders` (açılışta toplu/sabah emirlerini geri yüklemek için) |
| `SetOrders` | `Orders`'a yazar. Önce ana emirler tek tek eklenir, sonra alt emirler strateji bazında eklenir. Alt emirlerin ana emri ya aynı istekte gelmeli ya da `mainOrderId` ile DB'de bulunmalıdır. Dönen `orderId` **ilk ana emrin** DB id'sidir; yalnız alt emir gönderildiyse 0 döner. Transaction yok; yarıda kalan hata kısmi yazım bırakır. |
| `DeleteOrders` | Her id için önce `mainOrderId=id` olan alt emirler, sonra emrin kendisi silinir. |
| `SetAccountStrategy` | `Accounts_Strategies` INSERT, çakışmada `ON DUPLICATE KEY UPDATE timestamp` |
| `GetAccountStrategies` | `Accounts_Strategies` hepsi |
| `GetAllIndices` / `GetIndiceInstruments` | Endeksler; endeksteki enstrüman id'leri (`Instrument_Indices`) |

## 5. AlgoService (`algo.proto`, `algo_api.go`) — yalnız gRPC

H = HftSrvProd (`src/Clients/DatabaseServiceClient`), A = AlgorithmicTrading/AlgoProd (`algoSrc/Data/DatabaseServiceClient`).

| RPC | Çağıran | Ne yapar / önemli davranış |
|-----|---------|----------------------------|
| `AlgoLogin` | H, A | `Application_Users`. Başarısızlıkta **error yok, boş token** döner. |
| `GetUserAccounts(userId string)` | A | `userId` sayıya çevrilemezse "invalid user id" döner. Yanıtta yalnız hesap id ve adı var. |
| `GetAllInstruments` | H, A | `Instrument` tablosu |
| `GetAllInstrumentsInIndice` | H, A | Endeks üyeleri |
| `GetFictiveInstrumentSettings` / `GetFictiveItemSettings` | A | Bellekteki fiktif endeks tanımları (açılışta `external-files/` CSV/XLSX'ten yüklenir, `UpdateFictive*Settings`). DB'ye gitmez. |
| `GetIndice` | A | Tek endeks; `INDICE_TYPE_SECTOR` → `isMainIndice=true` (isimlendirme ters görünüyor) |
| `GetInstrumentScores` / `SetInstrumentScore` | A | `Scores` |
| `SetArbitrageData` / `GetArbitrageData` / `GetAllArbitrageData` | A | `Arbitrage*` tabloları; kullanıcı token claim'inden alınır |
| `DeleteArbitragePackage` | A | Paket token'ına göre siler |
| `UpdateArbitragePackage` | — | `packageId<=0` ise hata. Çağıran bulunamadı. |
| `SetFundData` / `GetFundData` | A | `Fund*` tabloları; kullanıcı token claim'inden alınır |
| `GetAllFundsData` | — | Çağıran bulunamadı |
| `GetIndiceOpeningPrice` | A | Endeks açılış fiyatı |
| `GetTimeBasedData` | A | `TimeBased`/volatilite tablosundan mum verisi. Zaman damgaları **Unix saniye**. |
| `FetchHistoricalData` | A | `historyManager` üzerinden. `historyManagerEnabled=false` ise "history manager is disabled". |
| `FetchAkd` (server stream) | A | Önce `initialHistoricalDataCount` kadar geçmiş gönderilir, sonra canlı AKD yayını. AKD kapalıysa "akd is disabled". |
| `GetUnderlyingInstrumentsWithFuture` | A | Vadelisi olan dayanaklar |
| `GetBrokerageFirmList` | A | AKD aracı kurum listesi |
| `SubscribeBrokarageResults` (bidi stream) | A | İstemci kriter listesi yollar (`BrokerageReqKey` başına). Sonuçlar `ReceiveBrokerageFirmResults` goroutine'inden 500 ms'lik tarama döngüsüyle gönderilir. Stream kapanınca tüm kriterler unsubscribe edilir. |
| `UnsubscribeBrokerageResults` / `UnsubscribeBrokerageSide` | A | Anahtar (+taraf) bazında aboneliği bırakır |
| `GetByfSettings` | A | Bellekteki BYF dosyası (`byf.enabled`). Kapalıysa boş yanıt döner, hata dönmez. |
| `SetStrategySettings` / `GetStrategySettings` | H, A | `StrategySettings`. Ayarlar `map<string, Any>` olarak taşınır (`ConvertAlgoFields`/`ConvertDbFields`). `Get` uygulama kullanıcısı ister; boşsa hata mesajı yanlışlıkla "strategy Id is required" der. |

## 6. LimitControlService ve RiskManagerService (`limit_control.proto`, `risk_manager.proto`)

Limitler yalnız **bellekte** tutulur (`limits.GetLimitsManager` singleton), DB'ye yazılmaz. Model: LimitControl limitleri **yazar**, RiskManager aynı limitleri **okur**.

| Servis.RPC | Çağıran | Davranış |
|------------|---------|----------|
| `LimitControlService.LimitLogin` | — | `Application_Users`. Her zaman `error=nil` döner, sonuç `status` alanındadır. Şifre ve token **loglanır**. |
| `LimitControlService.SetCustomerLimits` | — | Müşteri TL overall'ı, pazar limitleri, hisse overall'ları → bellek |
| `LimitControlService.SetStockLimits` | — | Hisse limit tipleri, pazar limitleri, varsayılan açığa satış bayrağı → bellek |
| `LimitControlService.SetIntraDayCustomerLimits` (bidi) | — | Her mesaj tamponsuz `ClientSrvChan`'a yazılır; her mesaja `status=true` ile cevap verilir. |
| `RiskManagerService.GetCustomerLimits` / `GetStockLimits` | order-service (`Managers/RiskManager`) | Bellekteki son değerler |
| `RiskManagerService.GetIntraDayCustomerLimits` (server stream) | order-service | `ClientSrvChan`'dan okur ve istemciye iletir |

- `LimitControlService` için workspace'teki repolarda istemci bulunamadı. Proto yorumları ("Her loginden sonra ilk olarak bu methodu çağırmanız gerekmektedir") harici bir limit sağlayıcıya hitap ediyor. ❓ doğrulanmadı: bu sağlayıcının kim olduğu.
- `ClientSrvChan` tamponsuzdur. Açık bir `GetIntraDayCustomerLimits` okuyucusu yoksa `SetIntraDayCustomerLimits` ilk mesajda bloklanır.
- Okuyucu birden fazlaysa her mesaj yalnız birine gider.

## 7. GuiService (`gui-data.proto`, `gui_api.go`) — REST `:restPort`

Çağıran: mtrader-trade-ui (dosya yolları `app/` altında). "Hedef" sütunu, çağrının iletildiği yeri gösterir: DB, ITCH (trade-data-app'in kendi ITCH defteri) veya bir dış servis (H = HFT, A = AlgoProd, O = order-service; bkz. §9). Strateji tipinden uygulamaya eşleme `getApplicationFromStrategyType` ile yapılır.

Dış servis gerektiren uçlar ilk `DataService.Login` gelmeden önce "Gui external services is not found" döner (`SetGuiExtServices` henüz çağrılmamıştır). Bağlantı yoksa "… is not connected" döner.

| RPC | REST | UI çağıran | Hedef | Davranış |
|-----|------|------------|-------|----------|
| `GuiLogin` | `POST /v1/login` | `api/mutations/useLogin.ts` | DB, AWS | §2. **Her durumda 200+gövde** (`status`, `isOtpEnabled`). SMS gönderim hatası yutulur, `status=true` kalır. Şifre loglanır. |
| `GuiCheckOtpCode` | `POST /v1/checkOtpCode` | `useCheckOtp.ts` | DB | Yanlış kod: 200+gövde `status=false`. DB hatası: 500. |
| `GuiForgetPassword` | `POST /v1/forgetPassword` | `useForgetPassword.ts` | DB, AWS | Kullanıcı/e-posta eşleşmezse 200+gövde. E-posta gönderilemezse 500. |
| `GuiResetPassword` | `POST /v1/resetPassword` | `useResetPassword.ts` | DB | 200+gövde |
| `GuiGetInstruments` | `GET /v1/getInstruments` | `queries/useInstruments.ts` | DB+ITCH | `Instrument` tablosu + `tickSize` (ITCH SDK'dan `lastPrice` kademesine göre) + dayanak |
| `GuiGetIndices` | `GET /v1/getIndices` | `useIndices.ts` | DB | |
| `GuiGetIndiceInstruments` | `GET /v1/getIndiceInstruments` | `useIndiceInstruments.ts`, Varant Toplu modalı | DB | |
| `GuiGetDerivativesByUnderlying` | `GET /v1/getDerivativesByUnderlying` | `WarrantSettingsModal.tsx` | ITCH | Varant + vadeli listesi. Haritadan tip kontrolsüz `.(type)` dönüşümü yapılır; beklenmeyen alan tipi panic'e yol açar. |
| `GuiParseWarrantFile` | `POST /v1/parseWarrantFile` | `WarrantBulkSettingsModal.tsx`, `warrantBulkBatch.ts` | ITCH | §10. 200+gövde. |
| `GuiGetAllowedStrategies` | `GET /v1/getAllowedStrategies` | `useAllowedStrategies.ts` | DB | Token'daki kullanıcıya göre |
| `GuiGetAccounts` | `GET /v1/getAccounts` | `useAccounts.ts` | DB | Token'daki kullanıcıya göre |
| `GuiGetSelectedAccountStrategies` | `GET /v1/getSelectedAccountStrategies` | — | DB | Hesap/enstrüman/strateji filtresi. Kullanıcı sahipliği kontrol edilmez. |
| `GuiGetAccountArbitrageStrategies` | `GET /v1/getAccountArbitrageStrategies` | `mutations/arbitrage.ts` | DB | Kullanıcı sahipliği kontrol edilmez. |
| `GuiGetAllAccountStrategies` | `GET /v1/getAllAccountStrategies` | `useStrategies.ts` | DB | Tüm `Accounts_Strategies` çekilir, kullanıcının hesap adlarıyla bellekte filtrelenir. |
| `GuiSetAccountStrategy` | `POST /v1/setAccountStrategy` | `setAccountStrategy.ts` | H veya A | Motorun `AlgoSetAccountStrategy` RPC'si. trade-data-app DB'ye yazmaz; ❓ doğrulanmadı: motorun bunu `DataService`/`AlgoService` üzerinden kalıcı yapıp yapmadığı. Boş identifier veya bilinmeyen tip: 200+gövde. |
| `GuiStrategySetCommands` | `POST /v1/setStrategyCommands` | `mutations/strategy.ts` | H veya A | `ConvertFields` ile GUI Any tipleri client tiplerine çevrilir. `checkStrategyAttributesType` her alanın TypeUrl'ini `StrategyAttributes.valueType` ile karşılaştırır; uyuşmazsa 500. Sonra `SetCommandRequest` çağrılır. |
| `GuiFetchAllStrategyKeys` | `GET /v1/getStrategyKeys` | — | A | AlgoProd'dan `FetchAllUniqueKeys`. **HFT tipi için hiçbir çağrı yapılmaz, boş liste döner.** |
| `GuiSendOrders` | `POST /v1/sendOrders` | `sendOrder.ts`, `replaceOrder.ts` | O ve/veya H/A | Ayrıntı aşağıda |
| `GuiGetOrdersFromLevel` | `GET /v1/getOrdersFromLevel` | `queries/getOrdersFromLevel.ts` | ITCH+O | `level` alanı bir kademe indeksi değil, **fiyattır** (ITCH ham tamsayı). Seviye defterde yoksa order-service önbelleğindeki strateji emirleri döner. Her emirde `isUserOrder`/`isStrategyOrder` işareti var. `itchEnabled=false` ise hata. |
| `GuiSubscribeToOrderbook` | `POST /v1/subscribeToOrderbook` | `mutations/subscribe.ts` | H veya A | Motorun `SubscribeToOrderbook` RPC'si; yanıta ITCH'ten min/max/son fiyat eklenir (`float32`). Tip `ConvertStrategyType` ile çevrilir; AKD, MovingAverage, FundTracker, OrderChase → `Unknown`. |
| `GuiSubscribeToIndice` | `POST /v1/subscribeToIndice` | `mutations/subscribeToIndice.ts` | H | Endeksteki her enstrüman için sırayla HFT `SubscribeToOrderbook`. Biri başarısız olursa öncekiler abone kalır. Tip çevrimi `ConvertStrategyType` olmadan ham cast. |
| `GuiSubscribeToArbitrage` | `POST /v1/subscribeToArbitrage` | — | A | `SubscribeToAllFutures` (vade ay indeksleri) |
| `GuiSubscribeToSingleArbitrage` | `POST /v1/subscribeToSingleArbitrage` | `mutations/arbitrage.ts` | A | `SubscribeToFuture` |
| `GuiSubscribeToArbitrages` | `POST /v1/subscribeToArbitrages` | — | A | `SubscribeToFutures` (liste) |
| `GuiGetAllInstrumentsWithFutures` | `GET /v1/getAllInstrumentsWithFutures` | `useInstrumentsWithFutures.ts` | ITCH | Endeks, BYF ve kıymetli maden hariç. `expiryMonth` = sıra indeksi (0,1,2…). `itchEnabled=false` ise error döner (500); gövdedeki `status=true` istemciye ulaşmaz. |
| `GuiUploadArbitrageExcel` | `POST /v1/uploadArbitrageExcel` | `features/arbitrage/api/arbitrageExcelApi.ts` | DB+A | Excel parse edilip doğrulanır. Panel başına `Panels`, `Accounts_Strategies`, `StrategySettings` ve `Arbitrage` yazılır; AlgoProd'a `UpdateExtSettings` ile iki kez (başla/bitti) bildirilir. Transaction yok. Hatalar 200+gövde. Uygulama kullanıcısı bulunamazsa sabit `"algoUser"` kullanılır. |
| `GuiDownloadArbitrageExcel` | `GET /v1/downloadArbitrageExcel` | aynı dosya | DB+A/H | Kullanıcının arbitraj panelleri + ayarları Excel olarak döner. 200+gövde. |
| `GuiSetPanel` | `POST /v1/setPanel` | `mutations/setPanel.ts` | DB | `Panels`, `Strategy_Panels`. 200+gövde. Claim sayısal değilse (GUI dışı token) 200 + "Invalid user ID" döner. |
| `GuiGetPanels` | `GET /v1/getPanels` | `queries/panels.ts`, arbitraj panel seed | DB | DB hatasında hem gövdede `status=false` hem error döner; sonuç 500. |

**`GuiSendOrders` dalları** (her emir için, `orderType`'a göre):

1. **`MORNING` / `OPENING` / `EVENING` (toplu emir):** Emir order-service'e gidecek listeye eklenir. Ardından ilgili motora (`getApplicationFromStrategyType`) `SetAccountStrategy` çağrılır; bu çağrının hatası yalnız loglanır.
   - `ENTER`/`REPLACE` olayında, ITCH açıksa ve defter bulunursa, emir `levelCount` kademeye açılır. İlk kademe ana emirdir (`isMainOrder=true`). Fiyat her kademede `GetTickSize` kadar kaydırılır: alışta aşağı, satışta yukarı. Fiyat ITCH ham tamsayısıdır.
   - ITCH kapalıysa tek emir gider.
   - Diğer olaylarda (iptal vb.) tek ana emir gider.
2. **Diğer tipler (strateji emri):** `ConvertOrderRequestToAlgoOrders` ile `map<string,Any>` oluşturulur (`Order_Event_Type`, `Exchange_Info`, `Orderbook_Id`, `Strategy_Id`, …). Bu map motorun `SetCommandRequest` RPC'sine `Command_Type_OrderRequest` olarak gönderilir.
3. Döngü bitince toplu liste boş değilse **tek** `OrderService.SetOrders` çağrısı yapılır; bu, client RPC'si `SendOrder`'dır.
   - Döngü ortasında hata çıkarsa, o ana kadar motorlara gitmiş strateji emirleri geri alınmaz ve toplu liste hiç gönderilmez.

`applicationUsername`, config'teki `extServices[].applicationUser` değerinden gelir (`GetApplicationUsername`). Ayrıntılı emir yolculuğu: [`30-akislar/`](../../30-akislar/).

## 8. AdminService (`admin_ui.proto` + `admin_ui.yaml`, `admin_api.go`) — REST `:adminApiPort`

Çağıran: admin paneli mtrader-frontend-apps (`app/lib/api/{auth,users,accounts,order-users}.ts`, `baseURL = VITE_API_URL` = `…/v1`). Algo-Setup'ta derlenmiş eski bir `MAAdminUI` bundle'ı da aynı yolları kullanıyor.

| RPC | REST | Davranış |
|-----|------|----------|
| `Login` | `POST /v1/authorize` (body `credentials`) | `Admins` tablosu, MD5. Hata: 500 "invalid username or password". İstek `%+v` ile loglanır; **şifre log'a düşer**. |
| `CheckAuthentication` | `POST /v1/authorize/check` | Boş handler; yalnız token kontrolü |
| `CreateUser` / `GetUsers` / `GetUser` / `UpdateUser` / `DeleteUser` / `DeleteUserMany` | `POST/GET /v1/users`, `GET/PUT/DELETE /v1/users/{user_id}`, `DELETE /v1/users` | GUI kullanıcıları (`Users`). Şifre MD5'lenerek yazılır; `UpdateUser`'da boş şifre mevcut şifreyi korur. Liste: §3 react-admin kuralları. |
| `CreateOrderUser` / `GetOrderUsers` / `GetOrderUser` / `UpdateOrderUser` / `DeleteOrderUser` / `DeleteOrderUserMany` | `POST/GET /v1/orders/users`, `GET/DELETE /v1/orders/users/{user_id}`, `PUT /v1/orders/users/{order_user_id}`, `DELETE /v1/orders/users` | OUCH/FIX kullanıcıları (`Ouchs`). `market`: EQUITY→1, DERIVATIVE→2; başka değer hata verir. `protocol`: OUCH/FIX. **`GetOrderUsers` OUCH/FIX şifresini düz metin döner.** |
| `CreateUserAccount` / `GetUserAccounts` / `GetUserAccount` / `UpdateUserAccount` / `DeleteUserAccount` / `DeleteUserAccountMany` | `/v1/users/accounts[/{user_account_id}]` | `Accounts` CRUD |
| `AllowOrderUserForAccount` / `DenyOrderUserFromAccount` | `POST` / `PUT /v1/users/accounts/orders/users` | Hesap–OUCH kullanıcısı izni (`Users_Ouch`); "deny" PUT ile yapılır |
| `AddUserToAccount` / `RemoveUserFromAccount` | `POST` / `PUT /v1/users/accounts/users` | `Users_Accounts` |
| `AllowStrategyForAccount` / `DenyStrategyFromAccount` | `POST` / `PUT /v1/users/accounts/strategies` | `Account_Allowed_Strategies` |
| `GetStrategies` | `GET /v1/strategies` | `Strategies` |

Hangi RPC'nin hangi tabloya yazdığının kesin listesi `pkg/db/mysql/admin_db.go` içindedir; tablo adları [`sema.md`](sema.md) ile karşılaştırılmalıdır. ❓ doğrulanmadı: yukarıdaki tablo eşlemesi her RPC için tek tek kontrol edilmedi.

## 9. trade-data-app'in istemci olduğu sözleşmeler (`api/client-spec/`, `pkg/gui/connections/`)

`extServices[]` config'indeki her kayıt için `GuiExtServ.Connect` bir bağlantı açar. Bu, ilk `DataService.Login`'den sonra olur (`cmd/dataapp/main.go`).
- `grpc.Dial` insecure, `WithBlock` ile yapılır ve başarılı olana kadar 2 sn arayla denenir. Mesaj boyutu sınırı `MaxInt`.
- Ardından login yapılır, token saklanır ve sonraki çağrılarda `authorization: Bearer <token>` gönderilir.
- `monitorConnection`, gRPC health `Watch` stream'ini izler; stream hata verirse yeniden bağlanır.
- **Login başarısız olursa** yeniden bağlanma goroutine'i `return` eder ve o servis process yeniden başlatılana kadar bağlantısız kalır.
- `IsConnected()` yalnız token'ın boş olmadığını kontrol eder.

**`OrderService` (`order-service.proto`) → order-service** (`orderservice.go`)

| RPC | Kullanım |
|-----|----------|
| `Login` | `Connect`; `Application_OUCH` ile |
| `SubscribeToOrders` (server stream) | `StartWorker`. Tüm `Application_Users` için `MORNING`, `OPENING`, `STRATEGY` ve `EVENING` emirleri istenir. Akış GUI emir feed'ini besler ([`veri-akisi.md`](veri-akisi.md)). |
| `SendOrder` | Go sarmalayıcısı `OrderService.SetOrders` (§7, `GuiSendOrders`) |
| `StopSubscription` | **Tanımlı, kullanılmıyor** |

`OrderService.SubscribeToOrderbook` Go tarafında boş bir stub'tır; RPC çağrısı yapmaz.

**`StrategyService` (`strategies.proto`) → HFT (`hft.go`) ve AlgoProd (`algotrading.go`)**

| RPC | HFT | AlgoProd | Not |
|-----|-----|----------|-----|
| `StrategyLogin` | ✓ | ✓ | `Connect` |
| `SetCommandRequest` | ✓ | ✓ | `SetStrategyCommand` (strateji komutu ve strateji emri) |
| `FetchCommands` (stream) | ✓ | ✓ | `getCommandsFromService`; strateji WS feed'i |
| `SubscribeToCommands` / `UnsubscribeFromCommands` | ✓ | ✓ | WS istemcisinin abonelikleri |
| `AlgoSetAccountStrategy` | ✓ | ✓ | `SetAccountStrategy` |
| `SubscribeToOrderbook` | ✓ | ✓ | |
| `FetchOrders` (stream) | ✓ | — | `HftService.getOrdersFromService` |
| `FetchAllUniqueKeys` | — | ✓ | `GetAllUniqueKeys` |
| `SubscribeToAllFutures` / `SubscribeToFuture` / `SubscribeToFutures` | — | ✓ | Arbitraj |
| `UpdateExtSettings` | — | ✓ | Excel import bildirimi |

`strategies.proto`'daki RPC'lerin hepsi en az bir istemcide kullanılıyor. `common.proto` yalnız ortak enum/mesaj tanımlar (`StrategyType`, `OrderType`, …). `clientmodels.StrategyType` ile `GuiStrategyType` sayısal olarak aynıdır (0–15).

## 10. `warrant_api.go` — `GuiParseWarrantFile`

Varant Toplu (HFT Warrant Advanced) için kotasyoncu dosyasını HFT'ye gönderilecek listeye çevirir. Dosyayı kaydetmez ve HFT'ye kendisi göndermez; listeyi UI'a döner.

1. `util.ParseWarrantFile(fileContent, fileName)` satırları okur.
2. `singleUnderlyingSymbol`: Dosya **tek dayanak** içermelidir; birden fazla dayanak varsa hata.
3. `resolveUnderlying`: Dayanak önce birebir, bulunamazsa `".E"` ekiyle aranır ("ASTOR" → "ASTOR.E"). İstekte `underlyingInstrumentId` verilmiş ve farklıysa hata.
4. Her satır için:
   - Varant önce dayanağın ITCH varant listesinde, sonra genel sembol aramasında aranır.
   - Boş kod, tekrar eden kod, ITCH'te bulunamayan kod ve kotasyon miktarı 0 olan satırlar `warnings`'e eklenir. Bulunamayanlar listeye girmez.
5. `prevClose` = ITCH `LastPrice / 10^DecimalPrice` (TL). Gün içinde ilk işlemden sonra bu değer önceki kapanış değil **son fiyattır**.
6. `warrantListJson`: `hftWarrantListEntry` dizisi döner (`instrumentId`, `symbol`, `quotationLot`, `prevClose`, `quotationLotOp:"eq"`, `isActive`, `warrantType`, `strikePrice`, `expiryDate`). Alan adları HftSrvProd `HftWarrantAdvancedCommand::parseWarrantsFromJson` ile birebir aynı olmalıdır; oradaki ayrıştırıcı elle yazılmış ve düz nesne bekliyor.
7. Hatalar 200+gövde (`status=false`, `errorMessage`) olarak döner. Yalnız ITCH yoksa veya JSON üretilemezse error döner.

## 11. Şüpheli davranış adayları (doğrulanmadı, koddan okuma)

- **Token kapsamı yok:** GUI kullanıcısının JWT'si gRPC portunda `DataService.GetOuchUsers` çağırıp OUCH/FIX şifrelerini alabilir. Aynı token admin REST'te kullanıcı yaratabilir (`AdminService`'te rol kontrolü yok).
- Düz metin şifre/token logu: `DataService.Login`, `LimitLogin` (şifre + token), `GuiLogin`, `AdminService.Login` (`%+v`), `GuiResetPassword` (reset token).
- OTP 4 hanelidir ve deneme sınırı yoktur (120 sn pencerede kaba kuvvete açık). Reset token'ının süresi yoktur.
- Admin liste sayfalaması: `range` başlangıcı liste uzunluğunu aşarsa `users[Min:Max+1]` panic verir. Recovery olmadığı için process düşer (`GetUsers`, `GetOrderUsers`, `GetUserAccounts`).
- `RiskManagerService.GetIntraDayCustomerLimits`: `select … default` boş döngüsüyle stream açık kaldıkça bir CPU çekirdeğini %100 meşgul eder. `Send` `io.EOF` dönerse `CloseChannel` limit manager'ı kalıcı olarak durdurur.
- `SubscribeBrokarageResults`: `SubscribeToBrokerageFirms` hatasında `subscribersMtx` kilitliyken `return` edilir; sonrasında `ReceiveBrokerageFirmResults` ve tüm abonelikler kilitlenir. Ayrıca AKD açıkken `ReceiveBrokerageFirmResults` `main`'de iki kez başlatılır.
- `UnsubscribeBrokerageSide`: AKD kapalıyken `nil` manager üzerinde metot çağrılır.
- `GuiGetOrdersFromLevel`: Seviye yoksa ve order-service bağlantısı yoksa `nil` `orderService` üzerinde metot çağrılır.
- `main`: `guiChan` tamponsuzdur ve `DataService.Login` non-blocking `select` ile gönderir. Login, `main` `<-guiChan`'a ulaşmadan gelirse sinyal kaybolur ve GUI tarafı hiç başlamaz (dar pencere).
- `monitorConnection`: Karşı taraf gRPC health servisini sunmuyorsa ❓ `Watch` hemen hata verip sürekli yeniden bağlanmaya yol açabilir. Eski `conn` kapatılmıyor.
