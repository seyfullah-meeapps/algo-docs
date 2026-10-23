---
kapsam: Servis log dosyalarının yeri ve açılış, sabah işi, hata ve kapanış log imzaları (trade-data-app → order-service → HftSrvProd → AlgoProd)
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-22
durum: taslak
---

# Log imzaları

Satırlar koddaki format string'lerinden alındı. `{}` / `%v` / `N` değişken kısımdır. Grep'te sabit kısmı kullan. Başlatma sırası ve neden bu sırada başlatıldığı: [sistem haritası § Başlatma sırası](../00-genel/sistem-haritasi.md#başlatma-sırası). Crontab saatleri: [kurulum-ve-dagitim § setup_mode → servisler ve crontab](kurulum-ve-dagitim.md#setup_mode--servisler-ve-crontab-development).

**Kural:** Bir servisin "HAZIR" satırını görmeden sıradakini başlatma.

## 0. Log nerede?

Her C++ serviste iki kanal vardır:
- `std::cout` / `std::cerr` → `docker logs <container>`.
- `LOG_*` (Quill) → yalnız dosya.

order-service'te müşteri config'lerinde `log.stdout: false` olduğundan `LOG_*` satırları `docker logs`'ta **görünmez**. Hangi satırın hangi kanalda olduğu aşağıda `[stdout]` / `[dosya]` diye işaretli.

| Servis | Dosya (container içi) | Host (bind mount) | Rotasyon | Satır zaman damgası |
|--------|----------------------|-------------------|----------|---------------------|
| trade-data-app | logrus: `/workingDirectory/logdata_<DD00YYMMDD>.log` (bkz. Şüpheli). İstek log'u: `/workingDirectory/log/requests/` | **Yok.** Compose'da volume yok; dosya container içinde kalır | Yok. Aynı gün yeniden başlatmada dosya `os.Create` ile **sıfırlanır** | logrus: `time="…" level=… msg="…"`. stdlib `log`: `YYYY/MM/DD HH:MM:SS`. İkisi de yerel saat (`TZ=Europe/Istanbul`, Dockerfile) |
| order-service | `<log.path><log.fileName>.txt` = `/workingDirectory/log/order_service.txt` | `$HOME/workingDirectory/container-logs/OrderServiceTest/` (development compose'undaki ad) | 256 MB'ta döner. Dönen dosya `order_service.1.txt` olur (en yeni dönen = `.1`), 30 dosyaya kadar. Açılışta append | `HH:MM:SS.nnnnnnnnn` yerel saat, **tarih yok**. Format: `%(time) [%(log_level)] [T%(thread_id)] [%(file_name):%(line_number)] %(message)` (`Logger/OsLogger.cpp`) |
| HftSrvProd | `<path>/log/hft.txt` = `/workingDirectory/HftSrvProd/log/hft.txt`. ITCH SDK: aynı dizinde `itchsdk_<YYYYMMDD>.log` | `$HOME/workingDirectory/container-logs/MAHft/` | `hft.txt`: 1 GB'ta döner (`hft.1.txt` … `hft.30.txt`). itchsdk: günlük 00:00 + boyut | order-service ile aynı format (`src/Containers/HftLogger.cpp`) |
| AlgoProd | `/workingDirectory/log/algo_<YYYYMMDD>.<n>.txt` (NanoLog, `logFile=algo`, `n` 1'den başlar) | `$HOME/workingDirectory/container-logs/MAAlgoProd/` | 1000 MB'ta yeni `<n>` | NanoLog formatı |

- Kaynaklar: trade-data-app `cmd/dataapp/main.go`; Algo-Setup `*/docker-compose.yml`, `*/scripts/run.sh`; AlgoProd `Logger/Logger.h`, `Logger/NanoLog.cpp`.
- `docker logs`: json-file sürücüsü, en çok 2 × 5 GB.
- trade-data-app'te `log.Printf` kullanan paketlerin çoğu (`pkg/itch`, `pkg/servicemodels`, `pkg/gui/connections`) stdlib `log` paketini kullanır. Bunların çıktısı **yalnız `docker logs`'a** gider (stderr), logrus dosyasına gitmez. `[SNAPSHOT]`, `[AdminAPI]`, `[RestAPI]` satırları bu gruptadır.

## 1. trade-data-app (MADatabaseService)

### Açılış

`docker logs <db container>` içinde sırayla:

| # | Satır | Kanıtladığı | Kaynak |
|---|-------|-------------|--------|
| 1 | `Unrecognised logLevel "", falling back to info` | Normal. Config seviyeyi okunmayan anahtara yazıyor ([config](../10-servisler/trade-data-app/config.md)) | `main.go` |
| 2 | `Starting data server application.` | Proses başladı | `main.go` |
| 3 | `Subscribed to SnapShotEnd Information` (×2) | `itchEnabled=true`; snapshot beklenecek | `itch.go` `NotifyOnSnapshotEnd` |
| 4 | `[SNAPSHOT] Market 1 snapshot end received with N total instruments` | Pay (Market 1) Glimpse bitti. `N` o ana kadar alınmış **toplam** enstrümandır, pazar başına değil. VİOP için `Market 2` | `itch.go` `processItchData` |
| 5 | `[SNAPSHOT] All configured markets are ready; running one-time bootstrap` | Config'teki **bütün** pazarların snapshot-end'i geldi. ⚠ master'da yok (2026-10-22) | aynı |
| 6 | `[SNAPSHOT] Bulk inserting N instruments to database...` → `[SNAPSHOT] ✓ Database insertion completed` | Enstrümanlar MySQL'e yazıldı | aynı |
| 7 | `[SNAPSHOT] ✓ Notified subscriber 0 (market M)` | `main` bekleyişinden çıktı | aynı |
| 8 | `TradeVerifier: enabled=…`, `TradeVerifier[startup]: writing fresh bounds for X of Y DB instruments` | Tavan/taban/maxOrderValue yazıldı (VERDA) | `main.go` `applyBounds` |
| 9 | `Starting Server` → `Server Started at Port  <server.port>` | gRPC (`server.port`, tipik 6620) dinliyor | `servicemodels/server.go` `StartNonBlocking` |
| 10 | `[AdminAPI] listening on :<server.adminApiPort>` ve `[RestAPI] listening on <server.restPort>` | Gateway'ler kalktı. İkisi de iç gRPC'ye dial + handler kaydından **sonra** basılır | aynı |
| 11 | `Binding to Signal Handler` | **HAZIR** (order-service başlatılabilir) | `main.go` |
| 12 | `Incoming Login Request Username: … Password: … Application …` → `Login Successfull for User: <user> Token: …` | order-service login oldu (ilk login GUI'yi açar) | `servicemodels/ouch_api.go` `Login` |
| 13 | `Starting WSListener on: :<gui.port>` → `MADatabaseSERVICE is now running. Press CTRL + C to interrupt.` | WebSocket açık; sinyal handler kuruldu | `ws_listener.go` `Serve`, `main.go` |

**Snapshot ile listener'ların sırası (development):**
- `itchEnabled=true` iken `main`, ITCH bootstrap'ı bitene kadar bekler (`<-snapshotEndChan`).
- Bootstrap (5–7) ancak config'teki bütün pazarlar snapshot-end verince çalışır (`configuredSnapshotsReady`).
- Bu yüzden 9–10 satırları **her zaman** yapılandırılmış bütün `[SNAPSHOT] Market … snapshot end` satırlarından sonra gelir. Listener'ı görmek yeterlidir.
- `main.go`'daki "whichever finishes first" yorumu eskidir.

⚠ **master (2026-10-22):** `configuredSnapshotsReady` yok; bootstrap ve bildirim **ilk** gelen pazarda çalışır. VİOP önce biterse listener'lar `Market 1`'den önce basılabilir. Bu durumda erken başlayan order-service/HFT eksik enstrüman listesi alır. master'da `Market 1` (VİOP varsa `Market 2` de) snapshot-end satırını ayrıca bekle.

### Hata imzaları

| Satır | Anlam | İlk bak |
|-------|-------|---------|
| `[ERROR] receiveItch failed with code: N` | ITCH SDK başlamadı. `main` snapshot'ı sonsuza kadar bekler; listener'lar hiç basılmaz | [itch-sdk alım yolu](../10-servisler/itch-sdk/alim-yolu.md#6-glimpse-ve-canlıya-geçiş), `itchConfigurations` ([config](../10-servisler/trade-data-app/config.md)) |
| `[SNAPSHOT] Market 1 …` geliyor ama `All configured markets are ready` gelmiyor | Config'te olup snapshot-end vermeyen pazar var (ör. VİOP partition sorunu, K-01/K-02). Servis açılmaz | [ACIK-KONULAR](../ACIK-KONULAR.md) K-01, K-02 |
| `Error on inserting instruments: …` | MySQL yazımı başarısız. Bağlantı açılışta `Ping` ile **test edilmez** (`GetMysqlDbInstance`); MySQL hatası ilk sorguda görünür | MySQL container'ı, `database` config |
| `Aborting startup after fictive settings: …` / `Aborting startup: initial bounds application failed: …` | `main` döner, servis kapanır; gRPC hiç açılmaz | [trade-data-app README](../10-servisler/trade-data-app/README.md) |
| `TradeVerifier[snapshot]: no instrument matched between …` | Bilgi. Bound yazımı sonraki snapshot'ta yeniden denenir | aynı |
| `gRPC serve error: …` / `error on serving rest api: …` (`log.Fatalf`) | Port meşgul vb. Proses çıkar | `ss -ltnp` |
| `Already Loggedin` | Bilgi. İkinci ve sonraki `DataService.Login` | — |

## 2. order-service

### Açılış

| # | Satır | Kanal | Kanıtladığı | Kaynak |
|---|-------|-------|-------------|--------|
| 1 | `/workingDirectory/log/ is a directory.` | stdout | Log dizini var | `main.cpp` |
| 2 | `Connecting to database service. Address: <ip>:<database.port>` | stdout + dosya | — | `Data/DatabaseClient.cpp` `Connect` |
| 3 | `Token is received: <token>` | stdout | trade-data-app login tamam | `DatabaseClient::Login` |
| 4 | `Instruments were fetched successfully. Count: N` | stdout + dosya | Enstrüman listesi alındı. `N` trade-data-app'teki satır sayısıdır; pay+VİOP toplamına yakın olmalı | `Service/Network/InstrumentService.cpp` `FetchInstruments` |
| 5 | `Login accepted for user <ouchUser>` | **dosya** | Her OUCH kullanıcısı BIST'e login oldu. `connectUser` senkron çağrılır | `MAOSdkManager::ConfigureSdkCallbacks` (`onUserConnected`) |
| 6 | `FIX Logon - <sessionID>` | stdout | FIX oturumu açıldı (MAOrderSDK QuickFIX) | MAOrderSDK `FixEngine::onLogon` |
| 7 | `Repeatable orders will be fetched at …`, `Opening orders will be fetched at …` | dosya | Toplu emir zamanlayıcıları kuruldu (§ Sabah işleri) | `OrderManager::WaitUntilFetch`, `MAOSdkManager::SendOpeningOrders` |
| 8 | `Current time is before morning configured time. Setting up timeout check.` | dosya | Zamana bağlı handoff tetiği kuruldu (T+30 s) | `OrderServiceApplication::shouldTriggerOuchDisconnectOnStartup` |
| 9 | `Starting order server.` → `Starting order service via network. Port:<server.port>` | dosya | — | `OrderServer::Start` |
| 10 | `[Server] Started Listening` | stdout | MARpc (`server.port`, tipik 8000) dinliyor. HFT/AlgoProd buraya bağlanır | network-sdk `MATCPServer.cpp` |
| 11 | `Grpc Server listening on 0.0.0.0:<server.grpcPort>` | stdout + dosya | **HAZIR.** OUCH/FIX login'leri (5–6) bundan önce denenmiştir. gRPC tipik 9035 | `OrderServer::StartServiceWithGRPC` |
| 12 | `[Server] Login Request Username: <user> Password: … Application: N ConnectionId: N` | stdout | MARpc login: `Application: 1` = HFT, `2` = AlgoProd | `OrderServer::RequestReceived` |

- 5 numaralı satır yoksa `MAOrderSDK login failed …` veya `MAOrderSDK reconnect still failing …` ara (hata tablosu).
- ⚠ master'da OUCH login satırı farklıdır: `Client connected. IP: <ip>, Port: <port>` (stdout + dosya, `Managers/Ouch/OuchClient.cpp`). development'ta bu satır **yoktur**.

### Sabah işleri

**Zamanlayıcı satırları** (hepsi `[dosya]`, `LOG_CRIT`). Açılışta, her config satırı için ayrı thread'den basılır:

```
SendRepeatableOrders: <TYPE> <part>
Repeatable orders will be fetched at <epoch_ns>, Protocol: Ouch, Part: <part>, Type: <TYPE>
Opening orders will be fetched at <epoch_ns>, group: <Derivative|Equity|Warrant|Yip>, session: HH:MM:SS.mmm
YIP opening sessions configured: N. Group: Yip
Opening orders are not configured, flow is disabled. Group: <Grup>        (WARN; config bloğu yoksa)
```

- **`<epoch_ns>` birimi:** Unix epoch **nanosaniye**dir (`system_clock::time_point::time_since_epoch().count()`, libstdc++ `system_clock` periyodu ns). Epoch UTC tabanlıdır, ama gösterdiği an config'teki **yerel (TR) saatin** 1 dk öncesidir.
  - Saat `GetTimePoint` içinde `localtime`/`mktime` ile kurulur. Container'larda `TZ=Europe/Istanbul` (`MAProdEnvironment` imajı).
  - Değer tam saniyedir; config'teki `millisecond` dahil değildir. Son 9 hane hep `000000000` olur.
  - Örnek: 2026-10-22 09:39:00 TR = `1792651140000000000`. Çözmek için: `date -d @$((N/1000000000))`.
- **`<TYPE>`** büyük harflidir: `MORNING`, `MORNING_VIOP`, `THEORIC` (`StartProperly` `toupper` uygular).
- **`Protocol:`** FIX satırlarında da `Ouch` yazar. Değer `OrderManager::protocol_type`'tan gelir ve `MAOSdkManager` için sabit `kOuch`'tır. Satırın FIX olduğunu config sırasından anla.
- **Hiç satır basılmaması:**
  - `IsLateToSend(5)`: tekrarlı akış T'ye 5 sn'den az kalmışsa ya da T geçmişse **log basmadan** döner. `SendRepeatableOrders:` satırı da basılmaz.
  - Açılışta T'ye 30 sn'den az kalmışsa `It is too late to send opening orders. Group: …, Session: …` basılır.
- `"Morning Order For Part1/Part2"` veya `"Opening Order For …"` biçiminde bir format string development'ta da master'da da **yok**. Sabah kontrolünde aranacak sabit metin `will be fetched at`'tır.
- ⚠ master'da biçim farklıdır:
  - `Repeatable orders will be fetched at <ns>, Protocol: …, Part: …, Type: …` (aynı metin, stream logger).
  - `Opening orders will be fetched at <ns>, market: <MARKET>` (grup ve seans yok).

**Beklenen saatler.** Config anahtarları `repeatableOrders.ouch[]`, `repeatableOrders.fix[]` (`type`, `part`, `hour`, `minute`, `second`, `millisecond`) ve `openingOrders.{derivative,equity,warrant,yip}`. Değerler Algo-Setup `development` müşteri config'lerinden (A1, Alnus, Alnus-Algo, Global, Marbas, Piramit, Piramit_Algo aynı; yalnız sabah `millisecond` farklı):

| Config satırı | T (yerel) | `fetched at` anı | Satır |
|---------------|-----------|------------------|-------|
| `ouch` `morning_viop` part 1 | 09:20:00.010 | 09:19:00 | `Type: MORNING_VIOP` |
| `openingOrders.derivative` | 09:30:00.100 | 09:29:00 | `group: Derivative, session: 09:30:00.100` |
| `ouch` `morning` part 1 | 09:40:00.135–146 | 09:39:00 | `Type: MORNING` |
| `fix` `morning` part 1 | 09:40:00.120/130 | 09:39:00 | `Type: MORNING` (`Protocol: Ouch` yazar) |
| `openingOrders.equity` | 10:00:00.100 | 09:59:00 | `group: Equity, session: 10:00:00.100` |
| `warrant`, `yip` | — | — | Config'te yok → `Opening orders are not configured, flow is disabled. Group: Warrant` / `Group: Yip` (WARN) |
| `fix` `theoric` part 1 | 18:01:00.130 | 18:00:00 | `Type: THEORIC` |

Akışın ayrıntısı (çekme, gönderme, iptal, zaman çizelgesi): [toplu-emirler § 3.1](../10-servisler/order-service/toplu-emirler.md#31-zamanlama), [§ 4](../10-servisler/order-service/toplu-emirler.md#4-açılış-akışı-maosdkmanagersendopeningordersconfig-group), [§ 8](../10-servisler/order-service/toplu-emirler.md#8-örnek-zaman-çizelgesi-örnek-configyaml-servis-0900dan-önce-başlamış). Müşteri değerleri: [kalicilik-ve-config](../10-servisler/order-service/kalicilik-ve-config.md).

**Gönderim anı satırları** (dosya):
- Tekrarlı: `repeatable_orders: N non_repeatable_orders: M`, `Partition<p> … Account Orders for …`, `Cancellation starting...`.
  - Satırda seçilen emir yoksa akış `repeatable_orders:` basmadan döner ve disconnect çağırmaz.
- Açılış: `Preparing opening orders to send. Group: <G>` → `Started sending opening orders. Group: <G>` → her emir için `Sending an opening order. … Group: <G>, Protocol: <FIX|OUCH>`.
  - Zaman aşımında `Sending opening orders timed out. Group: …`.
- YİP: `YIP opening session HH:MM:SS.mmm. Group: Yip` … `YIP opening sessions finished for today. Group: Yip`.

**Handoff (order-service tarafı)** ([sdk-ve-oturumlar § 7](../10-servisler/order-service/sdk-ve-oturumlar.md#7-ouch-handoff--order-service-tarafı)):

| Satır | Kanal | Anlam |
|-------|-------|-------|
| `Calculated total callbacks for <appUser>: N` | dosya | Devredilecek kullanıcı sayısı |
| `Morning Order for Ouch <u> disconnecting...` | dosya | Akış sonu tetiği (A) |
| `SendRepeatableOrders Callback is invoking for : <u> currentCallback : i totalCallbacks : N` | stdout | Akış sonu devri |
| `MAOSdkManager::TriggerOuchDisconnect - Triggering OUCH user disconnection for time-based recovery` | dosya | Zaman tetiği (`morning` T + 30 s, ya da geç açılış) |
| `Late Callback is invoking for : <u> currentCallback : i totalCallbacks : N` | stdout | Zaman tetiğiyle devir |
| `It is already disconnected after SendRepeatableOrders for ouch <u> . We are passing ...` | dosya | Normal; zaten devredilmiş |
| `MAOSdkManager::TryDisconnectUser - user <appUser> not connected yet, waiting...` | dosya | HFT order-service'e bağlı değil. 500 ms'de bir tekrar basılır, **sınırsız** bekler |
| `Current time is past morning configured time (9:40:0). Triggering ouch disconnect required.` → `OrderServiceApplication::Start - Late startup detected, starting disconnect thread` | dosya | order-service sabah saatinden sonra açıldı; devir hemen tetiklenir |

### Hata imzaları

| Satır | Kanal | Anlam | İlk bak |
|-------|-------|-------|---------|
| `Credentials are invalid. <code> error: <msg>` | stdout + dosya | trade-data-app login başarısız. Kod 14 (`UNAVAILABLE`) = trade-data-app ayakta değil. Dönüş değeri kontrol edilmez; servis boş token ile devam eder | trade-data-app açılışı (§ 1) |
| `An error occurred while fetching instruments. ErrorCode: …` / `No instruments were found in the database.` | dosya / stderr | Enstrüman listesi yok. MAOrderSDK limit tablosu boş kalır | trade-data-app snapshot |
| `MAOrderSDK login failed. User=<u> reason=<not authorized\|session not available\|timeout\|network error\|unknown>` | dosya | OUCH login reddi | [sdk-ve-oturumlar § 9](../10-servisler/order-service/sdk-ve-oturumlar.md#9-oturumlar-yeniden-bağlanma-ve-kopma-senaryoları) |
| `MAOrderSDK reconnect still failing. user=<u> attempt=N` | dosya | Kopma sonrası 1 s'lik yeniden bağlanma döngüsü; her 10 denemede bir basılır | aynı |
| `MAOrderSDK heartbeat timeout. User=<u>` | dosya | BIST heartbeat'i kesildi | aynı |
| `FIX Logout - <sessionID>` | stdout | FIX oturumu düştü. QuickFIX `reconnectInterval` ile yeniden dener (3600 s olabilir) | [MAOrderSDK fix](../10-servisler/maordersdk/fix.md) |
| `FIX logon rejected for <u> (1409=<n>)` / `FIX logon rejected. user=… sessionStatus(1409)=…` | stdout / dosya | 5 = kullanıcı/şifre, 6 = kilitli, 8 = şifre süresi doldu, 9 = SubID/CompID | aynı |
| `MAOrderSDK FIX connectUser failed. user=<u>` | dosya | FIX oturumu enable edilemedi | aynı |
| `MAOrderSDK LOCAL REJECT (never sent to BIST). token=… code=1001 reason=enterOrder: unknown instrument (no limit entry) …` | dosya | Limit tablosu dolu ama bu orderbook yok. Açılışta eksik enstrüman listesi alındığı anlamına gelir | § 1, [emir-yasam-dongusu § 5](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#5-ret-ve-hata-kodları) |
| `MAOrderSDK error code=<n> message=<msg>` | dosya | SDK iç hatası (kod listesi MAOrderSDK'da) | [MAOrderSDK](../10-servisler/maordersdk/README.md) |
| `MAOrderSDK start failed` | dosya | `runtime_error` fırlatılır, servis açılmaz | aynı |
| `Instrument not found for opening order. Group: …` / `YIP-flagged opening order has no openingOrders.yip session configured, it will not be sent. …` | dosya | Açılış satırı atlandı | [toplu-emirler](../10-servisler/order-service/toplu-emirler.md) |

- **Limit tablosu tamamen boşsa 1001 üretilmez.** MAOrderSDK boş tabloda bölmeyi kapatır ve emri bütün olarak gönderir (`MAOrderSDK.cpp` `enterOrder`). 1001 yalnız tablo dolu olup orderbook eksikken üretilir.
- **Lisans:** development ve master'da lisans kontrolü yorum satırı (`main.cpp`). Lisans imzası **yoktur**.

## 3. HftSrvProd

### Açılış

`docker logs <hft container>` (stdout). `[dosya]` işaretliler `hft.txt`'te.

| # | Satır | Kanıtladığı | Kaynak |
|---|-------|-------------|--------|
| 1 | `HftMain.cpp` | Proses başladı. Onload re-exec varsa iki kez görünür | `HftMain.cpp` `main` |
| 2 | `Restarting with Onload` | Binary `HAS_ONLOAD_ZC` ile derlenmiş ve `LD_PRELOAD` boşmuş; proses `LD_PRELOAD=libonload.so` ile kendini yeniden `exec` ediyor. Bkz. not | aynı |
| 3 | `File name: <config>` ve ardından üst seviye her TOML anahtarı `key: value` | Config parse edildi (şifreler dahil basılır, Şüpheli) | `ConfigurationManager::loadConfiguration` |
| 4 | `mlockall skipped (sdkLockMemory=false)` | Beklenen | `main` |
| 5 | `Start Glimpse Client <part> <user>` → `Login accepted for part: <part>` | Her ITCH partition'ı için Glimpse login (Spot 4) | itch-sdk `GlimpseClient.cpp` |
| 6 | `ItchSdkClient started (unified method).` | `itchsdk_start` döndü = bütün partition'larda Glimpse bitti | `ItchSdkClient::startItchSdkClient` |
| 7 | `MAOrderSDK: N active OUCH user(s) loaded from #SpotOuchConfiguration` | Config'teki `isActive=true` `[[ouch_users]]` sayısı. Müşteri config'lerinde bu tablo yok, **N=0 normaldir**. Kullanıcılar handoff ile gelir | `main` MAOrderSDK boot |
| 8 | `DatabaseServiceClient::Connect - Connecting to database service. Address: <ip>:<dbPort>` → `… - Login successful, token received (length: N)` → `… - Connection result: SUCCESS` | trade-data-app login (`AlgoLogin`). İlk `DatabaseServiceClient::instance()` çağrısında basılır: ya 7'nin hemen ardından limit tablosu için, ya strateji yükleyici thread'inde. ❓ doğrulanmadı: 7 ile 8'in sırası | `Clients/DatabaseServiceClient.cpp` |
| 9 | `[dosya] setInstrumentLimits: pushing N instruments to MAOrderSDK` | Limit tablosu. `N` order-service'teki `Count`'a yakın olmalı | `main` |
| 10 | `[combiner] enabled (ITCH+OUCH execute combiner armed)` | Yalnız `combinerEnabled=Y` | MAOrderSDK `start` |
| 11 | `Server listening on 0.0.0.0:<grpcPort>` | StrategyService gRPC (trade-data-app → HFT) | `GUIManager::startGrpcServer` |
| 12 | Banner: `HFT INITIALIZATION COMPLETE` / `Status: LIVE` / `Startup Time: N ms` / `Network: Onload Enabled\|Disabled` / `Database: …` / `OUCH Users: 0 connected` | **HAZIR.** `ItchManager::start` Glimpse sonunu bekledikten sonra basılır | `displaySystemStatus` |
| 13 | `[DEBUG] ouchSDK::login() called with username: <ouchUserName>` → `[DEBUG] ouchSDK::login() returned: true` | order-service'e MARpc login. Banner'dan **sonra** gelebilir: ayrı thread'de, DB strateji yüklemesi bitince çalışır (`ItchManager::start`) | `OuchManager::login` |
| 14 | `[dosya] StrategyManager replay gate: no OUCH handoff within 20s — opening gate (zero-handoff). A later handoff will re-gate during its replay.` | **Normal sabah satırı.** Watchdog `startPeriodicJobs`'tan (banner'dan hemen önce) 20 s sonra çalışır; 09:40 handoff'u o saatte gelmediği için her gün basılır | `StrategyManager::startPeriodicJobs` |

**Onload notları:**
- `Restarting with Onload` satırı `execvp`'den **önce** basılır. `libonload.so` yüklenemezse dynamic loader `ERROR: ld.so: object 'libonload.so' from LD_PRELOAD cannot be preloaded … ignored.` basar ve proses Onload'suz devam eder. Bu yüzden satır tek başına Onload'un yüklendiğini kanıtlamaz. Kanıt: bu satır var **ve** `ld.so` hatası yok.
- Proses `onload` wrapper'ıyla (`LD_PRELOAD` dolu) başlatılırsa satır hiç basılmaz.
- Banner'daki `Network: Onload Enabled` derleme bayrağıdır (`HAS_ONLOAD_ZC`), çalışma anı kanıtı değildir.
- Banner'daki `OUCH Users: N connected` yalnız config'teki `isActive` kullanıcıları sayar; handoff kullanıcılarını saymaz. Pratikte hep 0'dır.

### Handoff ve replay (HFT tarafı)

Sıra ([emir-yasam-dongusu § 4](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı)):

```
orderUserDisconnected: handoff for OUCH user <u> i/N                                        [stdout]
orderUserDisconnected: order-service handing OUCH user '<u>' over to HFT (i/N)               [dosya]
StrategyManager::registerExpectedReplays - waiting for N OUCH user replay(s)                 [dosya]
orderUserDisconnected: OUCH socket for '<u>' will be created under Onload stack '<stack>'    [dosya, Onload build]
orderUserDisconnected: HFT took over OUCH user '<u>' via MAOrderSDK (<ip>:<port>, K account(s))  [dosya]
StrategyManager::notifyUserReplayCompleted - user '<u>' done; R remaining                    [dosya]
StrategyManager::notifyUserReplayCompleted - ALL OUCH user replays complete; strategies may go live  [dosya]
```

### Hata imzaları

| Satır | Anlam | İlk bak |
|-------|-------|---------|
| `Failed to connect to databaseService.` (kırmızı) / `DatabaseServiceClient::Connect - Login failed, no token received` | trade-data-app'e login yok. Proses **devam eder**, sonraki gRPC çağrıları token'sız gider. Yanlış şifrede trade-data-app OK + boş token döndürür; o durumda da bu satır basılır | trade-data-app (§ 1), [hftsrvprod config](../10-servisler/hftsrvprod/config.md) `db*` |
| `[dosya] Credentials are invalid. Error code: N, error message: …` | Aynı, gRPC hata kodu ile | aynı |
| `Glimpse client login failed for part: <p> port: <port>` / `Login rejected for part: <p>` / `TCPConnection::Connect: connection timed out. Tried both primary and secondary for port: <port>` | Glimpse oturumu yok | [itch-sdk alım yolu § 6](../10-servisler/itch-sdk/alim-yolu.md#6-glimpse-ve-canlıya-geçiş) |
| `ItchSdkClient: Failed to start, error: N` → `Failed to start ITCH SDK` → `ItchSdkClient::startItchSdkClient() failed — aborting` | Glimpse süresi doldu ya da partition öldü; `exit(1)` | [itch-entegrasyonu](../10-servisler/hftsrvprod/itch-entegrasyonu.md) |
| itchsdk log: `Gap detected in partition <p>: expected <a>, received <b> (requesting <x>-<y>)`, `Sent rewinder request for sequences …`, `Rewinder resend partition …`, `Rewinder SPSC overflow on partition <p> (dropped response)`, `partition <p> live buffer cap reached …` | ITCH gap / Rewinder | [alım yolu § 5](../10-servisler/itch-sdk/alim-yolu.md#5-gap-ve-rewinder) |
| `[DEBUG] ouchSDK::login() called …` var, `returned:` yok | order-service MARpc'ye ulaşılamıyor. `ouchSDK::login` yanıtı zaman aşımsız bekler (`OrderStreamClient.cpp`); bağlanma hatası network-sdk'da log basmaz | order-service § 2, `ouchIp/ouchPort` |
| `[DEBUG] ouchSDK::login() returned: false` → `[dosya] Failed at ouch server login!` | order-service login reddi (401/403). `OuchManager` ctor'u `std::string` fırlatır; ayrı thread'de yakalanmadığı için proses sonlanır. ❓ doğrulanmadı: stderr'de `terminate called after throwing an instance of …` | order-service `[Server] Login Request` satırı |
| `[dosya] orderUserDisconnected: connectUser('<u>' <ip>:<port>) returned code=<n>, retrying (k/4) in ks` → `… FAILED after retries, code=<n>` | Handoff login'i başarısız. Kodlar: 2 user yok, 3 TCP, 4 login red, 5 cevap yok (eski oturum BIST'te açık) | [emir-yasam-dongusu § 4](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı) |
| `[dosya] MAOrderSDK::onLoginFailed user='<u>' reason=<n>` | 1 not authorized, 2 session not available, 3 timeout, 4 network | aynı |
| `[dosya] StrategyManager replay gate TIMEOUT after 60000ms with N replay(s) still pending — FORCING gate open …` | Handoff geldi ama replay 60 s'de bitmedi | aynı |
| `[dosya] MAOrderSDK::onSdkError code=<n> msg=<m>` | SDK hatası. Ör. `7 onload self-restart failed …`, `13 [combiner] requested but itch-sdk pointer was not set …` | [MAOrderSDK](../10-servisler/maordersdk/README.md) |
| `MAOrderSDK::start() failed — aborting` | `exit(1)` | aynı |
| `[dosya] GUIManager::startGrpcServer - Exception during gRPC server startup …` | gRPC portu açılamadı | `grpcPort` |

- **OUCH kopması HFT log'unda görünmez.** HFT `onUserDisconnected` / `onHeartbeatTimeout` callback'i kurmaz ve SDK kendiliğinden yeniden bağlanmaz ([ouch-protokolu](../10-servisler/maordersdk/ouch-protokolu.md)).
- **1001 reddi HFT log'unda kodla görünmez.** `onRejected` reddi stratejiye ve GUI'ye iletir, kodu log'a yazmaz. ❓ doğrulanmadı: strateji katmanında ayrı bir log satırı.

## 4. AlgoProd (AlgorithmicTrading)

| # | Satır (stdout) | Kanıtladığı | Kaynak |
|---|----------------|-------------|--------|
| 1 | `Working directory: "/workingDirectory"`, `Log directory: …` | Config yüklendi | `Configuration/ConfigurationManager.cpp` |
| 2 | `reading fictive instrument started from database...` | trade-data-app'e bağlanıldı; ayar okuma başladı | `SettingsManager.cpp` |
| 3 | Glimpse satırları (§ 3, 5) → `ItchSdkManager started (ITCH SDK v3).` | Glimpse bitti | `Managers/ItchSdkManager.cpp` |
| 4 | `startOuchStreaming()` → `ouch streaming started` → `login()` → `login succesful` | order-service MARpc login. `start`'tan 3 s sonra | `Managers/OuchManager.cpp` `start` |
| 5 | `Server listening on 0.0.0.0:<clientPort>` | **HAZIR.** StrategyService gRPC (tipik 9098) | `Managers/GUIManager.cpp` |

- Sentry `debug=1` açık olduğundan stderr'de `[sentry] …` satırları normaldir (`Main.cpp`).
- **Hatalar:**
  - DB bağlantısı yoksa `DatabaseServiceClient` ctor'u `… Failed to Connect Database Service!` fırlatır. ❓ doğrulanmadı: `try` dışında, proses `terminate` ile biter.
  - Orderbook 600 s'de hazır olmazsa `Application::startApplication failed` + `… orderbook has not been initialized in expected duration!` basılır ve uygulama durur.
  - order-service login reddinde log dosyasına `… Failed at ouch server login!` yazılır, süreç devam eder. Bağlantı hiç kurulamazsa `login()` satırından sonra beklemede kalır (§ 3 ile aynı mekanizma).
- Ayrıntı: [algorithmic-trading](../10-servisler/algorithmic-trading/README.md).

## 5. Kapanış

Crontab `docker stop` yapar. Docker PID 1'e (`run.sh`) SIGTERM gönderir. `run.sh` `_term` trap'i çalışır, varsayılan 10 s sonra SIGKILL gelir.

| Servis | `run.sh` ne yapar | Uygulama satırı | Arşiv |
|--------|-------------------|-----------------|-------|
| trade-data-app | `echo "SIGTERM received"` → `killall MADatabaseService` → `log/*.txt` taşınır → `Logs backed up and cleaned up.` / `Exiting...` | `terminated signal received. Gracefully shutting down the application.` → `[DEBUG] Stop() called - shutting down ITCH manager`. Sinyal handler ancak order-service login'inden sonra kurulur; öncesinde SIGTERM prosesi sessizce bitirir | `/workingDirectory/log/log-backups-<DDMMYYYY_HHMMSS>.zip`. logrus dosyası (`.log`, dizin dışı) arşive **girmez**. S3 yok |
| order-service | `killall PiramitOrderService` → `order_service.*.txt` taşınır, zip | `SIGTERM received. Closing the application.` (stdout), `SIGTERMsignal received. Application is going to be closed` (dosya), `Stopping ouch manager properly.` | `log/log-backups-<DDMMYYYY_HHMMSS>.zip` (host'ta container-logs). Glob `order_service.txt`'yi kapsamaz (Şüpheli). S3 yok |
| HftSrvProd | `kill -15 HftSrvProd` (Şüpheli) → `hft*` ve `itchsdk*` taşınır, zip → `aws s3 cp … s3://meeapps-backup/${MODE}/${COMPANY_NAME}/HFT/logs/` | `The interrupt signal is (15).` (yalnız sinyal prosese ulaşırsa) | Yerel zip + S3 |
| AlgoProd | `kill -15 AlgoProd` → strategyLog `WarrantTracker` ve `algo*`/`itchsdk*` → `tar.gz` (pigz) | SIGTERM handler kapalı (yorum satırı), SIGKILL ile ölür. Gün sonu `EndOfMessages` kapanışı ölü kod (olay yayınlanmıyor); `Application::waitCloseSignalEitherFromUserOrSystem system will be closed!` satırı pratikte basılmaz. Düzenli kapanış yalnız SIGINT/SIGHUP/SIGUSR1/SIGUSR2 ile ([uygulama-ve-threadler § 2](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md#2-kapanış-sinyal-gün-sonu-hata)) | `log-backups-<YYYY-MM-DD-HH-MM-SS>.tar.gz`, S3 yok (`copy_strategy_logs.sh` ayrı ve elle) |

S3'e log yükleyen yalnız HFT'dir; diğer servisler arşivi yerelde bırakır (K-185).

## Şüpheli

- **trade-data-app log dosya adı:** `time.Now().Format("200060102")` geçersiz bir Go layout'u. Sonuç `DD` + `00` + `YYMMDD` olur (2026-10-22 → `data_2200261022.log`).
  - `-log-path` sonuna `/` konmadığı için dosya `/workingDirectory/logdata_….log` olur, `log/` dizinine yazılmaz.
  - `!os.IsExist(err)` her zaman true olduğundan dosya her açılışta `os.Create` ile sıfırlanır.
  - Volume yok; container silinirse log gider. `run.sh` `*.txt` arar ve bu dosyayı arşivlemez.
- **Gizli bilgi log'a yazılıyor:**
  - trade-data-app `Incoming Login Request … Password:` basar.
  - order-service `[Server] Login Request Username: … Password: …` basar.
  - HFT config dökümü `dbPassword`, `ouchPassword` vb. dahil bütün üst seviye anahtarları basar.
  - order-service `Token is received: <token>`, trade-data-app `Login Successfull … Token:` basar.
  - Hepsi `docker logs`'ta.
- **HFT/AlgoProd `run.sh` `kill -15 <isim>`:** `kill` isim değil PID ister. Komut hata verir ve uygulama SIGTERM almaz.
  - HFT'de `The interrupt signal is (15).` ve düzenli MAOrderSDK kapanışı muhtemelen hiç çalışmaz; proses 10 s sonra SIGKILL ile ölür.
  - ❓ doğrulanmadı: prod'da `docker stop` çıktısıyla teyit edilmedi.
- **HFT S3 yolu:** `MODE` ve `COMPANY_NAME` hiçbir compose dosyasında set edilmiyor. Yol `s3://meeapps-backup///HFT/logs/` olur. ❓ doğrulanmadı: başka bir yerden (host env, imaj) geliyor olabilir. `aws` CLI'ın imajda olduğu da doğrulanmadı.
- **order-service arşiv glob'u:** `order_service.*.txt` deseni aktif `order_service.txt` dosyasını eşlemez. Bu dosya arşivlenmez ve günler boyunca append edilerek büyür.
- **order-service SIGTERM:** `OrderServiceApplication::Start` gRPC `server->Wait()` içinde bloklu kalır, `Stop()` bu beklemeyi bitirmez. ❓ doğrulanmadı: proses SIGKILL'e kadar yaşıyor olabilir.
- **`Protocol: Ouch` FIX satırlarında da basılıyor** (`OrderManager::protocol_type` sabit). Sadece log hatası; davranış etkilenmiyor.
- **HFT order-service login'i zaman aşımsız:** `ouchSDK::login` `future.get()` ile sonsuza kadar bekler. order-service yoksa HFT banner'ı basar ama order-service yolu hiç açılmaz; log'da hata satırı da çıkmaz.
- **trade-data-app sinyal handler'ı geç kuruluyor:** order-service hiç login olmazsa SIGTERM log basmadan prosesi bitirir.
- **container-logs dizin adı branch'e göre değişir:** development compose'u `OrderServiceTest` kullanıyor. ❓ doğrulanmadı: `main` (prod) compose'larındaki dizin adları.
- ❓ doğrulanmadı: itchsdk log dosya adındaki tarihin saat dilimi (Quill `StartDate`); AlgoProd'un itchsdk log dizini.
