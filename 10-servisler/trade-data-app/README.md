---
kapsam: trade-data-app (MADatabaseService) — merkez hub; paket haritası, açılış, gRPC servisleri, REST/WS gateway, dış servis bağlantıları, MySQL tabloları, entegrasyonlar, config
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app (MADatabaseService)

Go servisi (cgo ile `libMAItchSDK`). Sistemin merkezidir:
- MySQL'in **tek** sahibi.
- C++ servislerine veri sağlayan gRPC sunucusu.
- GUI'nin REST ve WebSocket gateway'i.
- GUI'den gelen komutları HFT, AlgoProd ve order-service'e ileten istemci.
- Kendi ITCH beslemesiyle emir defteri tutar.
- Dış veri entegrasyonları (VERDA, Datastore, AKD, BYF, AWS).

Sistem içindeki yeri: [`00-genel/sistem-haritasi.md`](../../00-genel/sistem-haritasi.md).

## Paket haritası (`pkg/`)

| Paket | İçerik |
|-------|--------|
| `cmd/dataapp/main.go` | Açılış sırası (aşağıda) |
| `conf` | `config.json` okuma (viper) |
| `db`, `db/mysql`, `db/models` | MySQL erişimi: `ouchdb.go` (order-service ihtiyaçları), `algodb.go`, `guidb.go`, `mysqldb.go` |
| `servicemodels` | gRPC servis implementasyonları (`ouch_api.go` = DataService, `gui_api.go`, `algo_api.go`, `admin_api.go`, limit, risk) + `server.go` (gRPC + grpc-gateway REST) |
| `gui/connections` | **Dışa giden bağlantılar**: `hft.go`, `algotrading.go`, `orderservice.go` (gRPC istemcileri, yeniden bağlanma) ve **WebSocket sunucusu** (`ws_listener.go`, `client.go`) |
| `gui/messages` | WS mesaj modelleri, `unique_key` üretimi (`base_order.go`) |
| `itch` | cgo ITCH SDK sarmalayıcısı, enstrümanlar (`instruments/`, fiyat bölücü `priceDivider = 10^DecimalCount`), emir defteri, abonelikler (header, bounds, denge fiyatı) |
| `pubsub` | WS feed'leri için yayın/abone |
| `extdata/tradeverifier` | **VERDA**: günlük tavan/taban, maks emir değeri, brüt takas dosyaları → `Instrument` tablosu |
| `extdata/datastore` | Borsa İstanbul Datastore indirmeleri |
| `extdata/akd` | **AKD** (aracı kurum dağılımı, Foreks) → VWAP filtresi |
| `history`, `pricedata`, `volatility` | Geçmiş fiyat ve volatilite (`historyManagerEnabled`) |
| `limits` | Limit kontrol modelleri |
| `requestlog` | REST isteklerinin loglanması (kaynak IP, enstrüman çözümleme), ayrı log dizini; `cmd/requestlog-report` rapor aracı |
| `util` | JWT/token, gRPC interceptor'ları, AWS istemcisi (SMS OTP, şifre sıfırlama e-postası) |
| `version` | Linklenmiş MeeApps kütüphanelerinin sürümleri |

## Açılış sırası (`cmd/dataapp/main.go`)

1. Config ve log hazırlanır, request log başlatılır, MySQL bağlantısı kurulur.
2. **ITCH manager** başlar. `itchEnabled` ise ilk snapshot beklenir; enstrümanlar `Instrument` tablosuna yazılır.
3. `historyManagerEnabled` ise geçmiş fiyat ve volatilite yöneticileri başlar.
4. API nesneleri oluşturulur (Ouch=Data, Gui, Algo, Admin, LimitControl, RiskManager). AKD açıksa AKD manager başlar.
5. BYF ayarları güncellenir (`byf.enabled`). Fiktif enstrüman (endeks) ayarları güncellenir; hata varsa açılış **durur**.
6. **TradeVerifier** (`tradeVerifier.enabled`): VERDA dosyalarından tavan, taban, son fiyat ve maks emir değeri `Instrument` tablosuna ve belleğe yazılır.
   - Her pazarın snapshot'ında tekrarlanır.
   - **`minPrice`/`maxPrice`/`maxOrderValue` alanlarını yazan tek yer budur.** Bu adım çalışmazsa C++ servisleri tavan/taban bilmez, Tavan/Taban stratejileri çalışmaz.
7. gRPC sunucusu (:`server.port`), REST gateway (:`server.restPort`) ve Admin REST (:`server.adminApiPort`) başlar.
8. **İlk `DataService.Login`** gelene kadar beklenir; bunu order-service yapar. Ardından dış servislere (order-service, HFT, AlgoProd) bağlanılır ve **WebSocket sunucusu** (:`gui.port`) açılır.

## gRPC servisleri (tek port, `server.port` = 6620)

| Servis | İstemci | İçerik |
|--------|---------|--------|
| `DataService` (`ouch-data.proto`) | order-service | Login, OUCH/FIX kullanıcıları, şifre güncelleme, stratejiler, enstrümanlar, pozisyonlar, emirler (`Get/Set/DeleteOrders`), hesap–strateji, endeksler |
| `AlgoService` (`algo.proto`) | HFT, AlgoProd | Login, hesaplar, enstrümanlar, fiktif enstrüman/endeks, skorlar, arbitraj ve fon verisi, BYF, AKD, strateji ayarları |
| `GuiService` (`gui-data.proto`) | UI (REST ile) | Aşağıda |
| `AdminService` (`admin_ui.proto`) | Admin paneli (REST ile) | Kullanıcı, OUCH/FIX kullanıcısı (`OrderUser`), hesap CRUD; hesap–kullanıcı, hesap–OUCH, hesap–strateji izinleri |
| `LimitControlService`, `RiskManagerService` | order-service | Limitler, hesap risk bilgisi, gün içi müşteri limit stream'i |

Kimlik doğrulama: Token gRPC interceptor'ında kontrol edilir (`util.GetHelperInstance(...).UnaryInterceptor`). Login, OTP ve şifre sıfırlama gibi uçlar `excludedMethods` listesindedir.

## REST (grpc-gateway, `server.restPort` = 6621) — `GuiService`

| Yol | Ne |
|-----|----|
| `POST /v1/login`, `/v1/checkOtpCode`, `/v1/forgetPassword`, `/v1/resetPassword` | Giriş ve OTP. Başarısız girişte de HTTP 200 döner, sonuç gövdededir. OTP SMS'i AWS'ten gider; kod 120 sn geçerlidir. |
| `GET /v1/getInstruments`, `/v1/getIndices`, `/v1/getIndiceInstruments`, `/v1/getDerivativesByUnderlying`, `/v1/getAllInstrumentsWithFutures` | Referans veri |
| `GET /v1/getAccounts`, `/v1/getAllowedStrategies`, `/v1/getSelectedAccountStrategies`, `/v1/getAllAccountStrategies`, `/v1/getAccountArbitrageStrategies`; `POST /v1/setAccountStrategy` | Hesap ve strateji izinleri |
| `POST /v1/setStrategyCommands`, `GET /v1/getStrategyKeys` | Strateji komutu (motora iletilir) |
| `POST /v1/sendOrders` | Emir: toplu emirler order-service'e, strateji emirleri motora. Bkz. sistem haritası → Emir yolları. |
| `GET /v1/getOrdersFromLevel`, `POST /v1/subscribeToOrderbook`, `/v1/subscribeToIndice` | Emir defteri |
| `POST /v1/subscribeToArbitrage(s)`, `/v1/subscribeToSingleArbitrage`, `/v1/uploadArbitrageExcel`, `GET /v1/downloadArbitrageExcel` | Arbitraj |
| `POST /v1/parseWarrantFile` | Varant Toplu dosyası; dayanak id eşlemesi yapar |
| `POST /v1/setPanel`, `GET /v1/getPanels` | Kayıtlı panel düzenleri |

JSON lehçesi (protojson): 64-bit sayılar **string** olarak gelir, enum'lar isim olarak gelir, boş mesaj `null` olur. WebSocket ise Go `encoding/json` kullanır, 64-bit sayılar orada **number**'dır. Ayrıntı: mtrader-trade-ui `AGENTS.md`.

## WebSocket (`gui.port` = 6623)

| Yol | Feed |
|-----|------|
| `/ws/v1/itch/start` | Emir defteri derinliği (snapshot + güncelleme; kendi emir işaretleriyle) |
| `/ws/v1/orders/start` | Emir olayları. Her subscribe **tüm geçmişi yeniden yollar** ve önceki aboneliği **değiştirir**. Geçmiş process ömrü boyunca bellekte tutulur. |
| `/ws/v1/strategy/start` | Strateji snapshot, durum ve özetleri (HFT/AlgoProd `FetchCommands` stream'inden) |
| `/ws/v1/best/start` | Best bid/ask |
| `/ws/v1/equilibrium/start` | Denge fiyatı (snapshot yok) |
| `/ws/v1/bounds/start` | Tavan/taban lot (`maxAskLot`, `minBidLot`) |
| `/ws/v1/passive-orders/start` | Pasif emirler |

Bilinen sınır: Uygulama seviyesinde ping/pong yok. Yazılamayan istemci kapatılmaz, yalnızca `running=false` olur. Yarı açık bağlantı tespit edilemez.

## Dış servis bağlantıları (`gui/connections`, `extServices` config'i)

| Uygulama | Port | Kullanılan RPC'ler |
|----------|------|--------------------|
| `orderserv` | 9035 | `SubscribeToOrders` (stream), `SendOrder`. Go tarafındaki sarmalayıcının adı `OrderService.SetOrders`'tır (`orderservice.go`); aynı isimli `DataService.SetOrders` RPC'siyle karıştırma. |
| `hft` | 9050 | `SetCommandRequest`, `FetchCommands` / `FetchOrders` (stream), `SubscribeToCommands`, `SubscribeToOrderbook`, `AlgoSetAccountStrategy` |
| `algotrading` | 9098 | Aynı sözleşme + vadeli abonelikleri |

Bağlantılar koparsa yeniden bağlanır. `StrategyType` → uygulama eşlemesi: `gui_api.go` `getApplicationFromStrategyType`. WS tarafında da aynı isimli ayrı bir fonksiyon var; yeni tip eklerken **ikisini birden** güncelle (Varant Toplu'da eksik kalmıştı).

## MySQL tabloları (kodda geçenler)

`Users`, `Admins`, `Application_Users`, `Accounts`, `Users_Accounts`, `Ouchs`, `Users_Ouch`, `Strategies`, `Accounts_Strategies`, `Account_Allowed_Strategies`, `Applications_Strategies`, `StrategyAttributes`, `StrategySettings`, `Orders`, `Positions`, `Instrument`, `Instrument_Indices`, `Arbitrage`, `Arbitrage_Package`, `Arbitrage_Basket_Package`, `Fund`, `Fund_Package`, `Fund_Und_Package`, `Panels`, `Strategy_Panels`, `Scores`, `TimeBased`.

- `StrategyAttributes`: strateji tipi başına izin verilen ayar alanları. Yeni bir wire alanının kalıcı olması için buraya satır gerekir.
- Örnek scriptler: `scripts/sql/hft_warrant_advanced.sql`, `orders_isyip.sql`.
- ❓ Tam şema (kolonlar) repoda migration olarak yok; bu dosyalar ve kod üzerinden çıkarılabilir.

## Entegrasyonlar

| Entegrasyon | Config | Ne |
|-------------|--------|----|
| VERDA (Borsa İstanbul) | `tradeVerifier.*` | Günlük tavan/taban, son fiyat, maks emir değeri, brüt takas |
| Datastore (Borsa İstanbul) | `datastore.*` | Dosya indirme |
| AKD (Foreks) | `akd.*` | Aracı kurum dağılımı (VWAP filtresi) |
| BYF dosyası | `byf.*` | Fon sepeti (Fon Takibi) |
| AWS | (ortam) | OTP SMS, şifre sıfırlama e-postası (`{hostname}/passwordReset/{user}/{token}`) |
| Request log | `requestLog.*` + env `REQUESTLOG_*` | İstek kayıtları; host'a özgü değerler env ile verilebilir |

## Config (`config.json`)

| Anahtar | Anlam |
|---------|-------|
| `server.port` / `restPort` / `adminApiPort` | gRPC / REST / Admin REST |
| `gui.port`, `gui.hostname`, sertifika yolları | WS sunucusu |
| `database.*` | MySQL |
| `itchEnabled`, `itchWorkerCount`, `itchTriggerWorkerCount`, `onloadStackName`, `itchConfigurations[]` | ITCH. Repodaki örnek `config.json` Spot 4 + **VİOP 4** partition tanımlar; HFT ve AlgoProd örnekleri VİOP için 6 tanımlar. Müşteri config'lerinde (Algo-Setup `development`, `Configs/<Müşteri>/dbservice-config.json`):
  - **Piramit_Algo:** VİOP 6.
  - **A1, Alnus-Algo:** VİOP 4.
  - **Alnus, Global, Marbas, Piramit, Seker:** VİOP hiç yok (yalnız Spot 4).

  Aynı müşterilerin HFT config'leri VİOP'ta 6 partition dinliyor. A1 ve Alnus-Algo'da trade-data-app'in VİOP 5–6. partition'larındaki enstrümanları görmemesi muhtemel. ❓ Kasıtlı mı (o partition'larda işlem yapılmıyor olabilir) doğrulanmadı. |
| `historyManagerEnabled`, `interestRate` | Geçmiş, volatilite |
| `tradeVerifier`, `datastore`, `akd`, `byf` | Entegrasyonlar |
| `extServices[]` | Dış uygulamalar (`application`, ip, port, kullanıcı, `applicationUser`) |
| `fictiveInstrumentSettingDefinitionPath`, `fictiveItemSettingDetailPath`, `maxVolumePath`, `instrumentBazaarsPath` | `external-files/` altındaki CSV/XLSX'ler (endeks tanımları, maks hacim, pazar listesi) |
| `logLevel`, `secretKey` (JWT) | |

## Build ve çalıştırma

- Go modülü, cgo ile `libMAItchSDK` gerekir. `Dockerfile` ve `docker-compose.yml` mevcut, `generate.sh` proto üretimi yapar.
- CI `dbservice.yaml` → Algo-Setup (DatabaseService).
