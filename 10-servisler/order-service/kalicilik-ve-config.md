---
kapsam: order-service'in trade-data-app DataService istemcisi (RPC'ler, auth, hata davranışı), emir/pozisyon kalıcılığı ve gün içi restart, enstrüman verisi; config.yaml tam anahtar referansı, sabit kodlu ayarlar, env/argüman, müşteri config farkları ve deploy biçimi
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app            # DataService sunucu tarafı (ouchdb.go GetOrders/SetOrders)
    branch: development
    commit: 1cca9a8
  - repo: Algo-Setup                # Configs/<Müşteri>/order-service-config.yaml, OrderService/, mysql/setup.sql, algosetup.yml
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-22
durum: taslak
---

# order-service — kalıcılık ve config

Özet [README](README.md)'dedir. Bu dosya ayrıntıdır. Kardeş dosyalar:
- [arayuzler.md](arayuzler.md): MARpc, gRPC, OrderDispatcher, açılış sırası
- [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md): OUCH/FIX kullanıcı yükleme, handoff, FIX şifre yenileme
- [toplu-emirler.md](toplu-emirler.md): toplu akışların davranışı
- [risk.md](risk.md): risk kontrolü

Sunucu tarafı: [trade-data-app/api.md §4](../trade-data-app/api.md) ve [sema.md](../trade-data-app/sema.md) (`Orders`, `Positions`, `Ouchs`).

## A1. DataService istemcisi (`Data/DatabaseClient`)

- **Kanal:** `database.host:database.port` (tipik 6620) adresine `grpc::CreateChannel` ile **insecure** kanal açılır. Tek kanal ve tek `DataService::Stub` vardır, bütün servisler bunu paylaşır.
- **Login:** `Connect()` → `DataService.Login(database.username, database.password, Application=OUCH(3))`. Dönen JWT `token` üyesine yazılır.
- **Her çağrı:** `MakeRequest` her istekte yeni bir `ClientContext` açar ve `authorization: <token>` metadata'sını `Bearer` öneki olmadan ekler. Çağrılar **senkron** yapılır ve **deadline yoktur**.
- **İstemci login'leri de aynı yoldan geçer.** MARpc'ye bağlanan HFT ve AlgoProd ile gRPC `Login` çağıran trade-data-app, order-service'e kendi kimlik bilgileriyle login olur. order-service bu bilgileri `DatabaseClient::Login` ile DataService'e iletir (`AuthenticationService::Login`, `OrderServiceImpl::Login`). Dönen token `token_username` haritasında tutulur. Sonraki isteklerde istemci token'ı bu haritada aranır. Ayrıntı: [arayuzler.md](arayuzler.md).
- **Risk kanalı ayrıdır:** `RiskManager::Connect` aynı host:port'a 50 MB alım limitli ikinci bir kanal açar ve `db_client->GetToken()` ile aynı token'ı kullanır ([risk.md](risk.md)). `DatabaseClient` içindeki `risk_manager_stub` ve `MakeRiskServiceRequest` hiç oluşturulmaz ve çağrılmaz (ölü kod).

### Çağrılan RPC'ler

| RPC | Sarmalayan | Ne zaman | Ne için |
|-----|-----------|----------|---------|
| `Login` | `DatabaseClient::Login` | Açılışta 1 kez (servis). Her MARpc/gRPC istemci login'inde 1 kez. | JWT |
| `GetInstruments` | `InstrumentService::FetchInstruments` | Açılışta 1 kez | Enstrüman önbelleği (aşağıda) |
| `GetStrategies` | `AccountStrategyService::FetchStrategies` | Açılışta 1 kez | Strateji tipi id ↔ ad (`MADefinitions.h` adları) |
| `GetAccountStrategies` | `FetchAccountStrategies`; ayrıca `GetAccountStrategies(authToken)` | Açılışta. MARpc strateji listesi isteğinde her seferinde tekrar çağrılır. | Hesap-strateji önbelleği. Anahtar: `strategyId-account-identifier-instrumentId-appUser` (`AccountStrategy::Key`). İstek anındaki çağrı **önbelleği güncellemez**; yalnız önbellekte bulunanları döner. |
| `GetPositions` | `FetchAccountStrategyPositions` | Açılışta 1 kez | Pozisyonu, eşleşen hesap-stratejiye (`id` + `application_user_name`) yazar. Hata dalı yok, hata sessizce geçer. |
| `SetAccountStrategy` | `InsertAccountStrategyToDb` | MARpc strateji kaydı ve gRPC `SendOrder` (toplu emir) sırasında | DB'ye yazar ve dönen id ile önbelleğe ekler |
| `GetOuchUsers` / `GetFixUsers` | `UserService::GetUsers` | Manager açılışında. Toplu akış başlangıcında yine çağrılır (`GetUsers(protocol, part, mode)`). | Kullanıcı ve hesap listesi ([sdk-ve-oturumlar.md](sdk-ve-oturumlar.md)) |
| `UpdateOrderUserPassword` | `UserService::UpdateOrderUserPassword` | FIX şifre değişimi ve yenilemesi | ([sdk-ve-oturumlar.md](sdk-ve-oturumlar.md)) |
| `GetOrders(type)` | `OrderService::GetOrders` | Açılışta (`STRATEGY`), toplu akış saatinde (`MORNING`/`OPENING`/`EVENING`), gRPC abonelik ilk yüklemesinde | Aşağıda |
| `SetOrders` | `OrderService::InsertOrder` / `BulkInsertOrder` | Aşağıda | Emir kalıcılığı |
| `DeleteOrders` | `OrderService::RemoveOrder` | Toplu emir silme (GUI) ve toplu akış sonrası | Toplu emir satırını siler |
| `SetPosition` | `OrderService::InsertPosition` | Her yeni fill'de (async kuyruk) | Pozisyon **delta**'sı |

`GetIndiceInstruments` ve `GetAllIndices` için sarmalayıcı var (`InstrumentService`), ama **çağıran yok**.

### Hata ve yeniden bağlanma davranışı

- `Connect()`'in dönüş değeri `OrderServiceApplication::Start`'ta kontrol edilmez. Login başarısız olursa servis boş token ile devam eder. Bütün `Fetch*` çağrıları `UNAUTHENTICATED` ile düşer ve yalnız `LOG_CRIT` basılır. Sonuçta kullanıcı yüklenmez ve oturum açılmaz. Process ayakta kalır.
- **Yeniden bağlanma ve yeniden login yok.** gRPC kanalı alttaki TCP'yi kendisi yeniler. Token ise yenilenmez. trade-data-app JWT'si 48 saat geçerlidir ([api.md §2](../trade-data-app/api.md)), yani 48 saatten uzun çalışan bir order-service'in bütün DataService çağrıları düşer. ❓ doğrulanmadı: günlük restart bunu fiilen önlüyor mu.
- **Önbellekler yalnız açılışta dolar.** Gün içinde Admin panelinden eklenen enstrüman, strateji tipi, OUCH kullanıcısı veya pozisyon değişikliği restart'a kadar görülmez. Tek istisna `InsertAccountStrategyToDb`'dir (önbelleğe ekler).
- **Hatalar yalnız loglanır, retry yok.** `SetOrders` hatası "inserting the order" `LOG_CRIT`'i ile kalır; emir BIST'e gitmiştir ama DB'de yoktur.

## A2. Emir kalıcılığı

### Ne, ne zaman yazılır

| Olay | Yol | `OrderType` | Senkron mu |
|------|-----|-------------|------------|
| HFT/AlgoProd emri (MARpc `EnterOrder`) MAOrderSDK'ya gönderildi | `MAOSdkManager::SendOrderAsync(EnterOrder)` → `InsertOrderToDatabaseAsync` | `STRATEGY` | Async. Tek kuyruk ve tek thread (`OrderManager::InsertOrdersToDatabaseAsync`); her emir için bir `SetOrders` RPC'si. SDK split ettiyse her çocuk ayrı satır. |
| Replace gönderildi | `SendOrderAsync(ReplaceOrder)` → `InsertOrderToDatabaseAsync(replacement_copy)` | `STRATEGY` | Async. Yeni token ile **yeni satır** yazılır; eski satır kalır. |
| Toplu sabah/teorik akışında gönderilen emirler | `OrderManager::SendRepeatableOrders` sonunda `BulkInsertStrategyOrder(all_sent_orders)` | `STRATEGY` | Senkron, akış thread'inde, gönderim **bittikten sonra**. Ana emir başına bir RPC. |
| Açılış/varant/YİP akışında gönderilenler | `SendOpeningOrders` sonunda `BulkInsertStrategyOrder` | `STRATEGY` | Aynı |
| GUI toplu emri (gRPC `SendOrder`) | `BulkInsertMorningOrder` / `Opening` / `Evening` | `MORNING` / `OPENING` / `EVENING` | Senkron, gRPC handler'ında |
| Toplu akış sonrası | `RemoveOrder` + (sabah, açılışta hisse grupları) `isActive=false` ile yeniden insert | aynı tip | Senkron ([toplu-emirler.md](toplu-emirler.md)) |
| Fill (`onExecuted`) | `InsertPositionToDatabase` → kuyruk → `SetPosition` + `AccountStrategyService::UpdatePosition` | — | Async, tek thread |

**Yazılmayanlar:** Accept, cancel, reject ve replace sonucu DB'ye **yazılmaz**. `Orders` satırı hiçbir zaman güncellenmez ve iptal edilen emrin satırı silinmez. Olaylar yalnız MARpc istemcilerine ve trade-data-app'in `SubscribeToOrders` stream'ine gider ([arayuzler.md](arayuzler.md)). Emrin BIST durumu (order_id, cum_qty) kalıcı değildir.

**Yazılan alanlar** (`InsertOrder`, `AddOrderToRequest`):
- `quantity` (lot)
- `price` (ham tamsayı fiyat, `uint32`; ölçek enstrümanın `decimalCount`'u)
- `order_type`
- `account_strategy_id`
- `application_user_name`
- `token` (SDK'nın atadığı client order id)
- `custom_data` = passThrough ve `custom_data_size`
- `protocol` (OUCH/FIX; `kUnknown` OUCH olarak yazılır)
- `time_in_force`, `regular_order_type`, `side`
- `is_active`, `is_main_order`, `is_yip`
- Yalnız bulk yolu: `main_order_id`, `level_count`. Tekil `InsertOrder` bu iki alanı yazmaz.

**Atlanan satırlar:** `account_strategy_id == 0` olan emir yazılmaz (`InsertOrder`: `LOG_CRIT`; bulk: `LOG_WARN`).

### `RetrieveSentOrders` (açılışta)

`MAOSdkManager::StartProperly` içinde çalışır: kullanıcılar yüklendikten sonra, `sdk_->start()` ve `connectUser`'dan **önce**.
1. `GetOrders(STRATEGY)` çağrılır ve OUCH ile FIX satırları ayrılır. Hesap-stratejisi önbellekte olmayan satır atlanır ("Skipping order…").
2. FIX satırları `sdk_->adoptFixOrders` ile MAOrderSDK registry'sine tohumlanır. Alanlar: token, FIX kullanıcısı (`getNextFixClient`), orderbook, yön, miktar, fiyat, hesap, passthrough, ord_type, tif. Enstrümanı veya FIX kullanıcısı bulunamayan satır atlanır.
3. OUCH ve FIX satırlarının hepsi `entered_orders`'a (token → `EnterOrder` bağlamı) yazılır. Sonradan gelen olaylar (replay dahil) hesap-strateji ve passthrough bağlamını buradan bulur.

**"Günün emirleri" sunucu tarafında filtrelenmez.** trade-data-app `GetOrders` yalnız `type` ile filtreler, tarih koşulu yoktur (`ouchdb.go GetOrders`). `STRATEGY` satırlarını gece temizleyen şey Algo-Setup'taki `RemoveOldData` prosedürüdür (`mysql/setup.sql`, `db_scripts/dbNightEvent.sh` çağırır):
- OUCH'ta `type` 3 (STRATEGY) ve 4 (EVENING) satırlarını siler, ayrıca VİOP enstrümanlı bütün satırları.
- FIX'te bütün satırları siler.
- `dbNightEvent.sh` Alnus ve Alnus-Algo klasörlerinde yok. ❓ doğrulanmadı: bu müşterilerde temizlik başka yerden mi yapılıyor. Yapılmıyorsa `RetrieveSentOrders` günler boyu biriken satırları yükler.

### Gün içi restart senaryosu

1. Açılış: `Login` çağrılır, ardından instruments, strategies, account strategies ve positions yüklenir. Pozisyonlar DB'deki delta toplamıdır.
2. `RetrieveSentOrders` çalışır (yukarıda).
3. **OUCH:** `connectUser`. MAOrderSDK her OUCH login'inde sequence 1 ister (`OuchCodec::encode_login`), günün olayları baştan replay edilir ([maordersdk/ouch-protokolu](../maordersdk/ouch-protokolu.md)).
   - OUCH olaylarında `is_replay` bayrağı yoktur (`MAOrderStruct.h`: bayrak yalnız FIX PossDup için set edilir).
   - Pozisyonun iki kez yazılmasını yalnız bir zaman penceresi önler: `sdk_->start()`'tan sonraki **10 sn** içinde (`PARSE_LOOP_START_TIMEOUT`) gelen OUCH fill'leri `SetPosition`'a yazılmaz.
   - Aynı oturumdaki tekrarlar `processed_execution_keys_` (bellek içi) ile atlanır. Restart sonrası bu küme boştur.
4. **FIX:** Davranış `fixSession.reset*` ayarına göre değişir.
   - `resetOnLogon/Logout/Disconnect=false` (repo örneği): `replayFromSeq=1` store'a yazılır. QuickFIX gap'i görüp ResendRequest atar ve BIST günün ExecutionReport'larını PossDup ile yeniden yollar (`is_replay=true`). Replay fill'leri pozisyona yazılmaz ("position already persisted at fill time").
   - **Müşteri config'lerinin hepsinde `reset*=true`** (aşağıda). Bu durumda logon'da sequence sıfırlanır ve replay olmaz. `replayFromSeq` etkisizdir. Restart sırasında gelen FIX fill'leri order-service'e hiç ulaşmaz. Tohumlanan DB kayıtları yalnız iptal için güvenlik ağıdır (kod yorumu).

### Çift kayıt riskleri

- **OUCH replay fill'i 10 sn penceresinden sonra gelirse** `SetPosition` ikinci kez çağrılır. `SetPosition` delta eklediği için pozisyon iki katına çıkar. Ters yönde, restart'tan sonraki ilk 10 sn'de gelen **gerçek** yeni OUCH fill'i de pozisyona yazılmaz.
- **Risk bakiyesi:** `risk_manager->OnOrderExecuted(apply_balance = !is_replay)`. OUCH'ta `is_replay` hep false olduğu için replay edilen OUCH fill'i bakiyeye yeniden uygulanır. README'deki "Replay edilen fill bakiyeye ikinci kez yazılmaz" ifadesi yalnız FIX için doğrudur. Ayrıntı: [risk.md](risk.md).
- **Son atış tekrarları iki kez yazılıyor:** `RepeatedLastShotStrategy`, `-110023` sonrası yeniden gönderimde ve timeout kopyalarında `SendOrderWithUsername(..., insert_to_db=true)` çağırır. Aynı emri `all_sent_orders`'a da ekler ve akış sonunda `BulkInsertStrategyOrder` onu tekrar yazar. Sonuç: aynı token'lı iki `STRATEGY` satırı. İlk atış ve tur gönderimleri `insert_to_db=false` olduğu için yalnız bir kez yazılır.
- **Alt emir (kademe) satırları:** `BulkInsertOrder` yalnız `IsMainOrder()` olan emirler için RPC açar. Alt emirleri, passthrough'u ana emirle **aynı** olanlar arasından toplar. Ana emri gönderilmemiş, ya da passthrough'u farklı olan alt emir `STRATEGY` olarak yazılmaz ve restart'ta `entered_orders`'a gelmez. ❓ doğrulanmadı: kademe alt emirlerinin passthrough'u ana emirle aynı mı.

## A3. Enstrüman verisi

- **Kaynak:** trade-data-app `Instrument` tablosu (`GetInstruments`, `RequestBase` boş istek). Açılışta bir kez okunur, bir daha yenilenmez. Alım limiti varsayılan 4 MB'tır: `DatabaseClient::Connect` 50 MB'lık `channel_args`'ı hazırlar ama `CreateChannel`'a geçirmez.
- **Model** (`Data/Models/Instrument`): `id` (orderbook id), `name`, `symbol`, `market` (EQUITY → kEquity, VIOP → kDerivative), `partition`, `financial_product`, `max_order_val` (uint64), `last_price`, `min_price`, `max_price` (double), `decimal_prx` = 10^`decimal_count`, `is_brut_takas`.
- **Kullanım:**
  - `MAOSdkManager::StartProperly`: her enstrüman için `maordersdk::InstrumentLimit{max_order_val (uint32'ye cast), decimal_count, is_brut_takas}` → `sdk_->setInstrumentLimits`.
  - Emir yönlendirme: pazar ve partition (`SendOrderAsync`, iki pazarlı hesapta OUCH kullanıcısı seçimi, FIX `getNextFixClient`).
  - Toplu akışlar: partition filtresi; açılış grubu (`BelongsToOpeningGroup`: pazar + `IsWarrantOrCertificate`, financial product 14/18).
  - `RiskManager`: brüt takas ve hisse kontrolleri.
  - `last_price`, `min_price` ve `max_price` (tavan/taban) order-service içinde okunmuyor.
- **`Service/InstrumentService.h`** derlemeye girmeyen eski bir başlıktır. `Service/Network/InstrumentService.h` ile aynı include guard'ı (`MEEAPPSORDERSERVICE_INSTRUMENTSERVICE_H`) taşır. `Managers/OrderManager.h` eskisini, diğer dosyalar yenisini include eder. Hangisi önce gelirse sınıf tanımı o olur. İki tanım arasındaki tek fark eskisinde `GetBist30Indices` bildiriminin olmamasıdır. Bu bildirim yenisinde var ama tanımı yok.

## B1. Config referansı (`config.yaml`)

### Nasıl okunur

- Tek argüman: `PiramitOrderService <config.yaml>`. Argüman yoksa `exit 1`.
- `ConfigurationManager` yapıcısı yaml-cpp kullanır ve **bütün okuma tek bir `try` içindedir**. Zorunlu bir anahtar eksik veya tipi hatalıysa istisna yakalanır, stdout'a "An error occurred while reading the configuration file" basılır ve process **devam eder**. O anahtardan sonra okunacak bütün alanlar varsayılanda kalır. Okuma sırası: genel → server → database → monitoring → license → protocols → log → eveningSessionStart → repeatableOrders → openingOrders → fixSession → maordersdk.
- Yalnız `openingOrders.warrant` ve `openingOrders.yip` kendi `try`'ları içindedir. Bozuk olurlarsa yalnız o akış kapanır.
- "Zorunlu" aşağıda bu anlamdadır: eksikse sonraki her şey okunmaz.

### Genel, server, log

| Anahtar | Tip | Varsayılan | Anlam / birim | Kullanan kod |
|---------|-----|-----------|---------------|--------------|
| `appname` | string | zorunlu | Yalnız açılış logunda | `main` |
| `mode` | string | zorunlu | `prod` → kProduction, `test` → kTest, **başka her değer kUnknown**. kUnknown'da hiçbir OUCH/FIX kullanıcısı yüklenmez. | `OrderManager::IsProductionEnvironment`/`IsTestEnvironment`, `UserService::GetUsers(…, mode)` |
| `protocols` | string listesi | [] | `ouch` veya `fix` varsa MAOSdkManager kurulur (ikisi aynı manager). Liste boşsa manager kurulmaz. | `OrderDispatcher` yapıcısı |
| `server.address` | string | zorunlu | gRPC bind adresi. MARpc bu anahtarı kullanmaz, `getaddrinfo(nullptr, AI_PASSIVE)` ile bütün arayüzlere bind eder ([arayuzler § 1](arayuzler.md)) | `OrderServer` |
| `server.port` | uint16 | zorunlu | MARpc (ouch-sdk istemcileri) | `OrderServer` |
| `server.grpcPort` | uint16 | zorunlu | gRPC (`OrderServiceImpl`) | `OrderServer` |
| `log.name` | string | zorunlu | **Okunur, kullanılmaz** | — |
| `log.path` | string (dizin, `/` ile biter) | zorunlu | Yoksa `mkdir 0744`; yaratılamazsa `exit 1` | `main`, `log::init` |
| `log.fileName` | string | zorunlu | Quill dosyası `<path><fileName>.txt`; 256 MB'ta döner, 30 yedek (sabit) | `log::init` |
| `log.level` | string | zorunlu | `log::parseLevel` | `log::init` |
| `log.stdout` | bool | zorunlu | Konsola da yaz | `log::init` |

### database, monitoring, license

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `database.host`, `database.port` | string, uint32 | zorunlu | trade-data-app gRPC (6620). Risk kanalı da aynı adresi kullanır. | `DatabaseClient`, `RiskManager::Connect` |
| `database.username`, `database.password` | string | zorunlu | DataService login'i (`Application_Users`) | `DatabaseClient::Connect` |
| `database.riskControl` | bool | false | Risk kontrolü ([risk.md](risk.md)) | `RiskManager::Start` |
| `monitoring.active` | bool | zorunlu | false ise PerfSDK hiç başlamaz; MAOrderSDK kullanıcı başı metrikleri de no-op olur. | `OrderServiceApplication::Start` (`HAS_PERFSDK`) |
| `monitoring.port` | string | zorunlu | `PerformanceClient::start`'a geçer. Başlık yorumu "Prometheus" diyor; [sistem haritasına](../../00-genel/sistem-haritasi.md) göre PerfSDK portu kullanmaz. `active=false` ise "0". `GetMonitoringPort()` getter'ını çağıran yok. | aynı |
| `monitoring.maxTimeUs` | uint32 (µs) | 60000000 | HDR histogram üst sınırı | aynı |
| `monitoring.clickhouse.host` | string | "" | Boşsa ClickHouse exporter kurulmaz | aynı |
| `monitoring.clickhouse.port` / `.dbName` / `.username` / `.password` | uint16 / string | 8123 / "default" / "" / "" | ClickHouse HTTP | aynı |
| `monitoring.clickhouse.appName` | string | "" → `ordersvc-<hostname>` | Metrik uygulama adı | aynı |
| `monitoring.clickhouse.printValues` | bool | false | Her örneği konsola basar | aynı |
| `license.url`, `.code`, `.username`, `.password`, `.interface` | string | **zorunlu** | Lisans kontrolü `main`'de yorum satırında, yani etkisiz. Yine de hepsi zorunlu okunur; biri eksikse sonraki her şey okunmaz. | (`LicenseManager`, çağrılmıyor) |

### Toplu emir saatleri

Akışların davranışı: [toplu-emirler.md](toplu-emirler.md). Burada yalnız anahtarların anlamı var.

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `eveningSessionStart.hour/minute/second` | uint16 | zorunlu | Yerel saat. Bu andan sonra bütün OUCH emirleri `OffHours` bayrağıyla gider (`offhours_invertor`). |
| `repeatableOrders.settings.schedPolicy` | string | FIFO | Bulk thread'leri: `OTHER` → SCHED_OTHER; **başka her değer** FIFO (öncelik 99). Pin çekirdeği DB'deki `coreToPin`'dir. |
| `repeatableOrders.ouch[]` / `.fix[]` | liste | yoksa boş | Her eleman bir akış. `ouch` altındakiler `protocol=kOuch`, `fix` altındakiler `kFix`. |
| `…[].type` | string | zorunlu | Büyük harfe çevrilir (`MAOSdkManager::StartProperly`): `MORNING`, `MORNING_VIOP`, `THEORIC`; başkası "Unknown repeatable orders type". ⚠ Handoff tetiği (`OrderServiceApplication::Start`) ham değeri **küçük harf** `"morning"` ile karşılaştırır, yani config'te `MORNING` yazılırsa handoff zamanlayıcısı kurulmaz. |
| `…[].part` | uint16 | 1 | Partition filtresi: yalnız bu partition'daki enstrümanlar ve kullanıcılar |
| `…[].mode` | string | — | **Okunmuyor** (struct'ta alan var, parse yok) |
| `…[].hour/minute/second/millisecond` | uint16 | zorunlu | Gönderim anı. Emirler bundan 1 dk önce DB'den çekilir. |
| `…[].duration` | uint16 (sn) | zorunlu | Tekrar turlarının yayıldığı süre |
| `…[].repeatSellOrders` | bool | zorunlu | Satış emirleri de tekrarlansın mı |
| `…[].repeatLastShot` | bool | zorunlu | Son atış stratejisi: true → `RepeatedLastShot`, false → `SingleLastShot` |
| `…[].timeoutOrderCount` | uint16 | 2 | Son atışta yanıt gelmeyen alış emri için en fazla kaç timeout kopyası (2 ms sonra) gönderileceği. 0 = hiç. |
| `…[].packOrders` | bool | zorunlu | Tur emirlerini paket olarak gönder |
| `openingOrders.equity`, `.derivative` | h/m/s/ms | **zorunlu** | Açılış grupları (hisse; VİOP) |
| `openingOrders.warrant` | h/m/s/ms | yoksa akış kapalı | Varant ve sertifika (10:02). ⚠ master'da yok (2026-10-22). |
| `openingOrders.yip.sessions[]` | h/m/s/ms listesi | yoksa akış kapalı | YİP seansları. ⚠ master'da yok (2026-10-22). |
| `maordersdk.orderHardCapTry` | uint32 (**tam TL**) | 50000000 | MAOrderSDK tek emir notional üst sınırı. 0 verilirse `LOG_CRIT` basılır ve SDK varsayılanı kalır. ⚠ master'da yok. |

### fixSession

Hepsi `MAOSdkManager::StartProperly`'de `sdk_config.fix_session`'a birebir kopyalanır. Davranış: [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md).

| Anahtar | Tip | Varsayılan | Not |
|---------|-----|-----------|-----|
| `connectionType`, `beginString`, `defaultApplVerID` | string | zorunlu | `initiator`, `FIXT.1.1`, `FIX.5.0SP2` |
| `fileStorePath`, `fileLogPath` | string | zorunlu | Örnekte `incoming.log`/`outgoing.log`. QuickFIX'te bunlar dosya değil **dizin**; store `incoming.log/` altında oturum başına `.seqnums/.body/.header/.session` dosyaları tutar ([maordersdk/fix § 3](../maordersdk/fix.md#3-sessionsettings-fixenginebuild_session_settings)). |
| `allowUnknownMsgFields`, `validateUserDefinedFields`, `validateUserDefinedMessages` | bool | zorunlu | QuickFIX |
| `resetOnLogon`, `resetOnLogout`, `resetOnDisconnect` | bool | zorunlu | false = sequence korunur ve restart replay'i mümkün olur |
| `useDataDictionary`, `dataDictionary`, `useTransportDataDictionary`, `transportDataDictionary` | bool / string (dosya yolu) | zorunlu | QuickFIX spec dosyaları |
| `reconnectInterval` | uint16 (sn) | zorunlu | QuickFIX yeniden bağlanma; FIX şifre değişiminin relogon penceresi |
| `heartBtInt` | uint16 (sn) | zorunlu | |
| `replayFromSeq` | uint32 | 1 | Store'a yazılan beklenen gelen sequence. Yalnız `reset*=false` iken anlamlıdır. ⚠ master'da yok. |
| `autoRenewExpiredPasswords` | bool | true | 1409=8'de otomatik yenileme kill-switch'i |
| `newPasswords` | map kullanıcı → şifre | {} | İlk logon şifre değişimi; başarıdan sonra config'ten silinmesi beklenir |

### Config'te olmayan, sabit kodlu ayarlar

| Ayar | Değer | Yer |
|------|-------|-----|
| DataService login uygulaması | `Application=OUCH (3)` | `DatabaseClient::Connect` |
| DataService kanalı | insecure, deadline yok, varsayılan 4 MB alım (50 MB ayarı uygulanmıyor) | `DatabaseClient::Connect` |
| Risk kanalı | insecure, 50 MB alım; fetch retry 5 sn | `RiskManager` |
| OUCH heartbeat | aralık 3000 ms, timeout 15000 ms | `MAOSdkManager::StartProperly` (`OuchConfig`) |
| Token havuzu | 100000 | aynı |
| `use_onload`, `lock_memory` | false, false (Onload derlemesinde de) | aynı (`OrderSdkConfig`) |
| OUCH replay fill penceresi | 10 sn (`PARSE_LOOP_START_TIMEOUT`) | `MAOSdkManager.cpp` |
| Kullanıcı partition'ları | Pazar başına yalnız 1 ve 2. Diğer partition'daki OUCH kullanıcısı "Cannot find user partition" ile atlanır. | `MAOSdkManager::StartProperly` |
| Toplu emir çekme | gönderimden 1 dk önce | `OrderManager::WaitUntilFetch` |
| Fazla kopya iptali beklemesi | 2 sn | `OrderManager::SendRepeatableOrders` |
| Açılış gönderim penceresi | 2000 ms | `MAOSdkManager::SendOpeningOrders` |
| Handoff zaman aşımı | sabah saati + 30 sn | `OrderServiceApplication::shouldTriggerOuchDisconnectOnStartup` |
| Bulk thread FIFO önceliği | 99 | `OrderManager::SendRepeatableOrders` |
| Log rotasyonu | 256 MB × 30 dosya, `.txt` | `Logger/OsLogger.cpp` |
| Sürüm logu | `"20210210.0850"` (sabit, gerçek sürüm `ma::build::PrintAll`'dadır) | `main` |

### Env, argüman, sinyal

- `argv[1]`: config yolu (zorunlu). Başka argüman okunmaz.
- `LD_PRELOAD`: Onload derlemesinde (`HAS_ONLOAD`, CMake `libonload` bulursa) boşsa `libonload.so` set edilip `execvp` ile yeniden başlanır. Mellanox derlemesinde (`HAS_MLX`, `libvma` bulunursa) aynısı `libvma.so` ile yapılır. Onload derlemesinde ayrıca `onload_set_stackname(ALL_THREADS, GLOBAL, DONT_ACCELERATE)` çağrılır, yani açıkça hızlandırılmayan soketler kernel'de kalır.
- Başka `getenv` yok. Mlx compose'daki `VMA_*` değişkenleri VMA kütüphanesine gider.
- Sinyaller: SIGINT, SIGTERM, SIGABRT, SIGHUP, SIGUSR1, SIGUSR2 → `app.Stop()`. SIGPIPE yok sayılır. SIGSEGV için handler kaydedilmez (handler'da metni olsa da).

### Okunup kullanılmayanlar / etkisizler (özet)

- `appname`: yalnız log
- `log.name`
- `license.*`: kontrol yorum satırında
- `repeatableOrders.*[].mode`
- `repeatableOrders.settings.coreCount` / `coreIndex`: development'ta hiç okunmaz, master'da okunur (aşağıda)
- `monitoring.port`: ❓ PerfSDK'da etkisi doğrulanmadı
- Müşteri `fixSession` blokları `reset*=true` iken `replayFromSeq`

## B2. Müşteri config'leri — yapısal farklar

Kaynak: Algo-Setup `2a3c5d5`, `Configs/<Müşteri>/order-service-config.yaml`. CI bu dosyayı `OrderService/order-service/config.yaml` olarak kopyalar (`algosetup.yml`).

**Müşteri config'leri master şemasında yazılmış.** master'daki `ConfigurationManager` `settings.coreCount`/`coreIndex`'i okur ve bulk thread'lerini `i % coreCount + coreIndex` çekirdeğine pinler. Şu anahtarlar master'da yoktur ve müşteri dosyalarında da yoktur: `schedPolicy`, `warrant`, `yip`, `maordersdk`, `replayFromSeq`, `monitoring.clickhouse`/`maxTimeUs`. development bu dosyalarla çalıştırılırsa sonuçlar aşağıdaki "Çıkarımlar"dadır.

**Hepsinde ortak:**
- `mode: prod`; `protocols: [ouch, fix]`
- `server.address` hepsi aynı; `server.port: 8000`, `grpcPort: 9035`
- `database.port: 6620`; host hepsinde aynı yerel adres (`<DB_HOST>`); `riskControl: false`
- `monitoring.active: false`, `monitoring.port: 9091`
- `log.level: info`, `log.stdout: false`
- `eveningSessionStart: 19:00:00`
- `morning_viop` 09:20:00.010, `duration: 40`, `repeatSellOrders: true`
- FIX `theoric` 18:01:00.130, `duration: 20`
- `openingOrders.derivative` 09:30:00.100, `equity` 10:00:00.100
- `fixSession.resetOnLogon/Logout/Disconnect: true`, `reconnectInterval: 3600`, `heartBtInt: 30`
- `license.*` dolu (`<REDACTED>`). `interface` müşteriye göre farklı NIC.

| Müşteri | `settings.coreCount`/`coreIndex` (dev'de etkisiz) | OUCH `morning` ms / `duration` / `timeoutOrderCount` | `morning_viop` `timeoutOrderCount` | FIX `morning` ms / `duration` |
|---------|------|------|------|------|
| A1 | 69 / 1 | 144 / 16 / **0** | 1 | 120 / 20 |
| Alnus | 69 / 1 | 144 / 16 / **0** | 1 | 120 / 20 |
| Alnus-Algo | 69 / 1 | 144 / 16 / **0** | 1 | 120 / 20 |
| Global | 62 / 1 | **146** / 16 / **0** | **0** | 120 / 20 |
| Marbas | 47 / 1 | 144 / 16 / **0** | **0** | **130** / 20 |
| Piramit | 32 / 1 | 144 / 16 / 2 | 1 | 120 / 20 |
| Piramit_Algo | 32 / 1 | **135 / 20** / 2 | 1 | 120 / 20 |
| Seker (eski) | 32 / 1 | 144 / 16 / 2 | 1 | 120 / 20 |

Bütün saatler 09:40:00.<ms> biçimindedir. Repo örneğinin farkları: `morning_viop` .050/55 sn; FIX morning .136/24 sn; derivative 09:40:00.100; equity .050; `reset*=false`; `stdout: true`; `monitoring.port: 9093`.

**Port uyumu:** order-service `server.port` 8000, bütün müşterilerde HFT `ouchPort` ve AlgoProd `ouchPort` ile aynı. `grpcPort` 9035, bütün müşterilerde trade-data-app `extServices` orderserv portu ile aynı. `database.port` 6620, trade-data-app `server.port` ile aynı. Uyumsuzluk yok. (HFT gRPC portundaki uyumsuzluk için: [hftsrvprod/config.md](../hftsrvprod/config.md).)

**Çıkarımlar** (development bu config'lerle koşarsa; prod'un master'da olduğu unutulmamalı):
- **Varant/sertifika açılış emirleri hiç gönderilmez.** `warrant` bloğu yok ve `equity` grubu varant/sertifikayı dışlıyor (`BelongsToOpeningGroup`). Log'da yalnız "Opening orders are not configured … Warrant" görünür.
- **YİP işaretli açılış emirleri hiç gönderilmez.** `yip` bloğu yok. Her biri için "YIP-flagged opening order has no openingOrders.yip session configured" `LOG_CRIT`'i basılır.
- **Bulk pinleme değişir.** master'da config `coreCount/coreIndex` ile yapılan pinleme, development'ta DB'deki `Ouchs.coreToPin` ile yapılır (`-1` = pinsiz). DB'de bu alan dolu değilse sabah thread'leri pinsiz ama FIFO 99 ile koşar.
- **FIX restart replay'i yok** (`reset*=true`, yukarıda A2).
- `timeoutOrderCount: 0` olan müşterilerde (A1, Alnus, Alnus-Algo, Global, Marbas OUCH sabah) son atışta timeout kopyası gönderilmez.
- Teorik akış her yerde aynı; tek fark FIX `morning` milisaniyesi.

## B3. Deploy biçimi

Algo-Setup `OrderService/`:
- Imaj tabanı `meeapps/maprodenv`. `MAProdEnv/lib` ve `include` imaja eklenir. Binary `/workingDirectory/order-service/PiramitOrderService`, config `/workingDirectory/order-service/config.yaml`. `scripts/run.sh` binary'yi bu config ile başlatır. SIGTERM'de `order_service.*.txt` log'ları zip'lenip yedeklenir.
- Compose: `network_mode: host`. Log volume'u `$HOME/workingDirectory/container-logs/OrderService[Test]/`. Capability'ler `NET_ADMIN`, `IPC_LOCK`, `SYS_NICE`. `memlock` sınırsız, `rtprio 99`. json-file log 2 × 5 GB.
- **Varyantlar:** CI matrisi (`algosetup.yml`, `orderserv_network`) `regular`, `onload` veya `mlx` seçer. Seçilen varyantın Dockerfile'ı, compose dosyası, `run_*.sh` script'i ve binary'si (`PiramitOrderService_Onload` / `_Mlx`) standart adlara taşınır, diğerleri silinir.
  - **Onload:** maprodenv 4.0 üzerine OpenOnload 9.2.0.43 ve TCPDirect derlenir. Compose `/dev/onload*` ve `/dev/sfc_char` cihazlarını verir. `run_onload.sh` binary'yi `onload` ile sarar. `cpuset: 0-18,36-55,66-71` (yorum: "19-35 HFT'ye ayrıldı").
  - **Mlx:** VMA kütüphaneleri imaja eklenir. Compose `/dev/infiniband/*` cihazlarını ve `LD_PRELOAD=libvma.so`, `VMA_SPEC=latency` gibi değişkenleri verir. `cpuset` yok.
- CI matrisinde müşteri ve varyant: Piramit, A1, Alnus, Marbas, Global → `onload`. `Alnus_Algo_Setup` → `regular`, ama `directory: "Alnus"`, yani `Configs/Alnus-Algo` dosyası değil `Configs/Alnus` dosyası kullanılır. Piramit_Algo ve Seker matriste yok.

Genel kurulum adımları: [kurulum-ve-dagitim](../../40-operasyon/kurulum-ve-dagitim.md).

## Şüpheli

- **Token ve şifre logu (bug?):**
  - `DatabaseClient::Login` başarılı login'de token'ı `LOG_CRIT` ve `std::cout` ile basar. Bu yalnız servisin kendi token'ı için değil, HFT, AlgoProd ve trade-data-app istemcilerinin her login'i için de geçerlidir. Token 48 saat boyunca bütün trade-data-app servislerinde geçerlidir ([api.md §11](../trade-data-app/api.md)).
  - Repo `config.yaml` gerçek görünen ClickHouse host ve şifresi ile lisans url/kod/kullanıcı/şifre içeriyor. Buraya alınmadı. ❓ Rotasyon kararı kullanıcıya ait.
- **Config hatası sessiz (bug?):** Tek `try` bloğu yüzünden, zorunlu bir anahtarın eksikliği o anahtardan sonraki bütün blokları varsayılanda bırakır. Process çıkmaz. Örnek: `license.interface` silinirse `protocols` boş kalır, manager kurulmaz ve hiçbir emir gönderilmez. Lisans kontrolü kapalı olduğu halde `license.*` zorunludur.
- **Login hatası ve token süresi (doğrula):** `Connect()` sonucu kontrol edilmez, retry ve yeniden login yok, JWT 48 saatte düşer (A1).
- **DataService çağrılarında deadline yok (doğrula):** trade-data-app takılırsa:
  - `SetOrders` / `SetPosition` kuyruk thread'i bloklanır, kuyruk (sınırsız `ThreadSafeQueue`) büyür.
  - Toplu akış thread'leri ve gRPC handler'ları bloklanır.
  - Kapanışta (`Stop`) kuyrukta kalan kayıtlar yazılmadan kaybolur (detached thread'ler).
- **50 MB ayarı uygulanmıyor (bug?):** `DatabaseClient::Connect` `channel_args` hazırlıyor ama `CreateChannel` argümansız çağrılıyor. Alım limiti 4 MB kalıyor. `GetOrders`, `GetAccountStrategies` veya `GetInstruments` yanıtı 4 MB'ı aşarsa çağrı `RESOURCE_EXHAUSTED` ile düşer. ❓ Gerçek yanıt boyutları doğrulanmadı.
- **Son atış tekrarlarının çift `STRATEGY` satırı (bug?):** A2 → Çift kayıt riskleri.
- **OUCH replay'inin pozisyon ve risk etkisi (doğrula):** 10 sn penceresi sezgisel bir korumadır. OUCH'ta `is_replay` olmadığı için risk bakiyesi replay fill'leriyle yeniden güncellenir.
- **`STRATEGY` satırları tarihsiz yükleniyor (doğrula):** Temizlik gece script'ine bağlı. Alnus ve Alnus-Algo'da script yok.
- **`FetchAccountStrategies` kontrolsüz deref (bug?):** `strategies.find(acc_str.strategy_type())->second` sonucu kontrol edilmeden kullanılıyor. Bilinmeyen strateji tipli bir `Accounts_Strategies` satırı `end()` deref ile tanımsız davranışa yol açar (muhtemelen açılışta çöküş).
- **`account_strategy_id == 0` (doğrula):** `InsertAccountStrategyToDb` DB'nin döndürdüğü id'yi doğrudan kullanır. Satır zaten varsa `SetAccountStrategy`'nin `LastInsertId`'si güvenilir değildir ([sema.md](../trade-data-app/sema.md)). 0 dönerse o stratejinin emirleri DB'ye hiç yazılmaz ("invalid account_strategy_id (0)"). Repo'da `account_strategy_id_zero` adlı bir branch var.
- **Kilitsiz paylaşılan haritalar (doğrula):**
  - `AuthenticationService::token_username`: MARpc ve gRPC login thread'lerinden kilitsiz insert edilir.
  - `AccountStrategyService::account_strategies`: `UpdatePosition` pozisyon thread'inden, `InsertAccountStrategyToDb` istek thread'lerinden kilitsiz yazılır.
- **`type` büyük/küçük harf tutarsızlığı:** Handoff tetiği `"morning"`'i küçük harfle arar. Akışlar ise büyük harfe çevrilmiş değeri kullanır.
- **`max_order_val` uint64 → uint32 cast:** `InstrumentLimit`'e geçerken 2^32'nin üstü kesilir. ❓ Değerin birimi ve gerçek aralığı doğrulanmadı.
- **İki `InstrumentService.h`:** Aynı include guard'ı taşıyorlar (A3). Ölü başlık silinmeli mi? Kullanıcı kararı.
- **Deploy:**
  - `Alnus_Algo_Setup` `Configs/Alnus` dosyasını kullanıyor (B3).
  - Onload derlemesinde bile MAOrderSDK'ya `use_onload=false` geçiliyor. ❓ Kasıtlı mı, doğrula.
