---
kapsam: order-service — OUCH/FIX emir gateway'i; MAOrderSDK adaptörü, toplu emirler (sabah/açılış/YİP/akşam/teorik), OUCH handoff, risk, MARpc ve gRPC arayüzleri, config
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
dogrulama: 2026-10-22
durum: taslak
---

# order-service

Emir gateway'i (C++). BIST'e giden emirlerin HFT doğrudan yolu dışındaki tamamı buradan geçer:
- AlgoProd emirleri
- HFT'nin handoff öncesi emirleri
- GUI'den girilen toplu emirler (sabah/açılış/YİP/akşam/teorik)

Sistem içindeki yeri: [`00-genel/sistem-haritasi.md`](../../00-genel/sistem-haritasi.md).

⚠ Eski bilgi tabanından farklar:
- order-service artık **MAOrderSDK** kullanıyor.
- **FIX de MAOrderSDK içinden** gidiyor (issue #402). Ayrı FIX manager yok; QuickFIX SDK'ya statik gömülü.
- Sabah emirlerinden sonra OUCH kullanıcılarını HFT'ye devrediyor (handoff).

## Dizin haritası

| Yer | İçerik |
|-----|--------|
| `main.cpp`, `OrderServiceApplication.*` | Başlatma: DB client, servisler, risk, dispatcher, MARpc sunucusu, PerfSDK; geç başlatmada handoff tetikleme |
| `OrderServer.*` | **MARpc sunucusu** (network-sdk, :`server.port`=8000). ouch-sdk istemcileri (HFT, AlgoProd) buraya bağlanır. Emir isteği, emir olayları, `UserDisconnected` (handoff) bildirimi. |
| `Service/servicemodel/OrderServiceImpl.*` | **gRPC sunucusu** (:`server.grpcPort`=9035), istemci trade-data-app: `Login`, `SubscribeToOrders` (stream), `StopSubscription`, `SendOrder` |
| `Managers/OrderDispatcher` | Protokole göre manager seçimi (FIX → OUCH manager'ına düşer), risk kontrolü, olay bağlama |
| `Managers/OrderManager` | Taban sınıf: **toplu emir akışları** (`SendRepeatableOrders`, `PrepareOuchOrders`, bulk thread'leri) |
| `Managers/Sdk/MAOSdkManager` | MAOrderSDK adaptörü: OUCH ve FIX kullanıcıları, emir gönderme, callback'ler, açılış/YİP akışları, **handoff** (`TriggerOuchDisconnect`) |
| `Managers/Sdk/SdkSessionManager` | Yeniden bağlanma shim'i (OUCH), FIX şifre yenileme |
| `Managers/RepeatableOrders/` | Son atış stratejileri (`SingleLastShot`, `RepeatedLastShot`), `-110023` ret döngüsü |
| `Managers/RiskManager` | Hesap TL limiti, hisse bakiyesi, açığa satış kısıtları |
| `Data/DatabaseClient`, `Service/Network/*` | trade-data-app `DataService` istemcisi: kullanıcılar, enstrümanlar, stratejiler, pozisyonlar, emir kalıcılığı |
| `config.yaml` | Örnek config |

## Kullanıcılar ve hesaplar

- OUCH ve FIX kullanıcıları DB'den gelir (`DataService.GetOuchUsers` / `GetFixUsers`). Admin panelinden yönetilir.
- Her kullanıcının pazarı (Equity/Derivative), partition'ı, izinli hesapları, `repeatCount`, `capacity`, `coreToPin` ve **`onlyMorningOrderUser`** (handoff'a girecek kullanıcı) bayrağı vardır.
- Ortam filtresi: `mode: prod` iken yalnızca `IsProduction` kullanıcılar, test modunda yalnızca test kullanıcıları yüklenir.
- Aynı hesap iki pazarda tanımlıysa emir pazarı enstrümana göre seçilir.
- OUCH kullanıcılarına açılışta login olunur; FIX oturumları QuickFIX ile açılır (yeniden bağlanma `reconnectInterval`).
- FIX şifre süresi dolarsa (1409=8) otomatik yenilenir ve DB'ye yazılır.

## Toplu emir akışları

GUI'den `OrderType` MORNING / OPENING / EVENING ile girilen emirler trade-data-app'ten gRPC `SendOrder` ile gelir (`OrderServiceImpl::SendOrder` → `InsertCollectiveOrder`). order-service bunları `BulkInsertMorningOrder` / `Opening` / `Evening` ile DB'ye yazar (`DataService.SetOrders`), GUI'ye yayınlar (`PublishCollectiveOrders`) ve config'teki saatte gönderir.

| Akış | Config | Ne yapar |
|------|--------|----------|
| **Sabah** (`repeatableOrders.ouch[type=morning]`, `morning_viop`; FIX için `repeatableOrders.fix`) | saat:dk:sn.ms, `duration`, `repeatSellOrders`, `repeatLastShot`, `timeoutOrderCount`, `packOrders` | Emirler OUCH kullanıcılarına dağıtılır (her kullanıcı izinli hesaplarının **tüm** emirlerini gönderir). Tekrar sayısı `min(repeatCount, (capacity − tekrarsız) / tekrarlı)`. Her kullanıcı ayrı thread'de (FIFO, `coreToPin`) tam saatte başlar. Seans açılmadan giden emir `-110023` ("Illegal transaction at this time") ile reddedilir; kabul edilene kadar yeniden gönderilir (son atış stratejileri). Amaç kuyruk önceliğidir. **Fazla kopyaların iptali** (`OrderManager::CancelRepeatedOrders`): gönderimden 2 sn sonra kabul edilen kopyalar (hesap-strateji, fiyat, yön, miktar, TIF, tip) ile gruplanır. Gruplama **bütün OUCH kullanıcıları üzerinden** yapılır. Hesap başına en erken `OrderRepeatRemainingCount` kadarı tutulur, kalanı iptal edilir. Yalnızca hesapta iptal izni varsa (`IsCancelAllowed`) çalışır. |
| **Açılış** (`openingOrders.derivative` / `equity` / `warrant`) | saat | Grup başına bir thread. Varant ve sertifikalar 10:02'de (10:00–10:02 yalnız piyasa yapıcı kotasyonu). |
| **YİP** (`openingOrders.yip.sessions`) | seans saatleri | Yakın İzleme Pazarı (tek fiyat) satırları sıradaki seansa gönderilir, sonra pasife alınır. |
| **Teorik** (`repeatableOrders.fix[type=theoric]`) | saat | Kapanış müzayedesi emirleri (FIX) |
| **Akşam** (`eveningSessionStart`) | saat | ❓ Akşam seansı emirleri; ayrıntı doğrulanmadı |

Kademeli emir: GUI'den `LevelCount` > 1 ile girilen emir, trade-data-app'te ana emir ve alt emirlere (her biri bir tick uzakta) açılır.

## OUCH handoff (HFT'ye devir)

Ayrıntı: [sistem haritası → OUCH handoff](../../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri). order-service tarafının özeti:
- **Tetik:** Sabah emirleri bittikten sonra, veya sabah saati + 30 sn geçince `TriggerOuchDisconnect` çalışır. Uygulama sabah saatinden sonra başlatılmışsa bu hemen tetiklenir.
- **İşlem:** `onlyMorningOrderUser` olan her OUCH kullanıcısı için:
  1. Bağlı uygulama kullanıcısının (ör. HFT) gelmesi beklenir.
  2. `sdk_->disconnectUser` ile logout olunur.
  3. MARpc ile `UserDisconnected` (kullanıcı, şifre, IP, port, hesaplar, `callbackNumber/total`) gönderilir.
- 🚧 AlgoProd için aynı devir `add-order-sdk` branch'inde (AlgorithmicTrading).

## Risk (`RiskManager`)

`database.riskControl: true` iken açılır.

- **Veri:** trade-data-app `RiskManagerService`'ten hesap limitleri, hisse kısıtları ve gün içi müşteri limitleri **stream** olarak gelir.
- **`checkEnterOrder`:** müşteri TL limiti, satışta hisse bakiyesi yeterliliği, hisse kısıtları (açığa satış yasağı vb.).
- **Ret:** Reddedilen emir uygulamaya `OrderRejected` olarak döner, BIST'e gitmez.
- **Takip:** Accept, execute, cancel ve replace olaylarıyla rezervasyonlar güncellenir. Replay edilen fill bakiyeye ikinci kez yazılmaz.

## Emir yaşam döngüsü ve kalıcılık

- Gönderilen emirler ve olaylar DB'ye `DataService.SetOrders` ile yazılır. Açılışta `RetrieveSentOrders` günün emirlerini geri yükler.
- FIX'te `resetOnLogon: false` ve `replayFromSeq: 1`: yeniden başlatmada BIST günün ExecutionReport'larını yeniden yollar (OUCH sequence=1 ile eşdeğer).
- Emir olayları iki tarafa gider: ouch-sdk istemcilerine (MARpc) ve trade-data-app'e (`SubscribeToOrders` stream → GUI).

## Config (`config.yaml`)

| Anahtar | Anlam |
|---------|-------|
| `mode` | `prod` / test: hangi OUCH/FIX kullanıcılarının yükleneceği |
| `protocols` | `ouch`, `fix` |
| `server.port` | MARpc (ouch-sdk istemcileri) |
| `server.grpcPort` | gRPC (trade-data-app) |
| `database.*` | **trade-data-app gRPC** adresi ve kullanıcısı (MySQL değil); `riskControl` |
| `monitoring.*` | PerfSDK → ClickHouse (`port` artık kullanılmıyor); `appName` boşsa `ordersvc-<hostname>`. MAOrderSDK kullanıcı başına metrikleri de buraya gider. |
| `license.*` | Lisans sunucusu ❓ (kontrolün etkin olup olmadığı doğrulanmadı) |
| `repeatableOrders.settings.schedPolicy` | Bulk thread'leri: `FIFO` (öncelik 99) veya `OTHER` |
| `repeatableOrders.ouch[]` / `.fix[]` | Sabah ve teorik akışlar (yukarıda) |
| `openingOrders.*` | Açılış ve YİP |
| `eveningSessionStart` | Akşam seansı |
| `maordersdk.orderHardCapTry` | Tek emir notional sınırı (tam TL); 0 geçersiz |
| `fixSession.*` | QuickFIX: FIXT.1.1 / FIX.5.0SP2, data dictionary yolları, reset/replay, heartbeat, şifre yenileme |

## Build

CMake, binary adı **`PiramitOrderService`**; `buf generate` (`Service/*`). Bağımlılıklar: `libMAOrderSDK` (QuickFIX içinde), `MARpc` (network-sdk), cpprest, yaml-cpp, fmt, OpenSSL, (opsiyonel) `libMAPerfSDK`, gRPC/protobuf. CI `orderservice.yml` → Algo-Setup.
