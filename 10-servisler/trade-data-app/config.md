---
kapsam: trade-data-app config.json tam referansı (tip, varsayılan, anlam, birim, kullanan kod), env override'ları ve müşteri config'leri arasındaki yapısal farklar
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: Algo-Setup                 # Configs/<Müşteri>/dbservice-config.json
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app — `config.json` referansı

## Nasıl okunur

- Dosya yolu `-config` bayrağıyla verilir; varsayılan çalışma dizinindeki `config.json` (`cmd/dataapp/main.go` `init`). Log dizini `-log-path` ile verilir. Log dosyası `{log-path}data_<tarih>.log` adıyla açılır, request log `{log-path}/requests/` altına yazılır.
- Okuma `pkg/conf/config.go` `NewServerConfig` içinde viper ile yapılır. Dosya okunamazsa `panic` olur.
- **Viper default'u tanımlı değil** (`SetDefault` çağrısı yok). Eksik anahtar Go sıfır değerini alır (`""`, `0`, `false`). Aşağıdaki "Varsayılan" kolonu bu sıfır değeri gösterir.
- `itchConfigurations` ve `extServices` dizileri JSON'a geri marshal edilip struct'a açılır. Hata olursa yalnızca loglanır, dizi boş kalır.
- Bazı anahtarlar `ServerConfig` dışında, doğrudan `viper.Get*` ile okunur: `cors`, `requestLog.*`. Bunlar ayrıca işaretlendi.
- Değerler örneklerde maskelidir. Gerçek değerler Algo-Setup ve repo dosyalarındadır; buraya yazılmaz.

## Üst seviye anahtarlar

| Anahtar | Tip | Varsayılan | Anlam / birim | Kullanan kod |
|---------|-----|-----------|---------------|--------------|
| `debug` | bool | false | Yalnızca açılışta "Service RUN on DEBUG mode" basar. Başka etkisi yok. | `conf/config.go` |
| `logLevel` | string | — | **Okunmuyor.** Kod `server.logLevel`'ı okur. Bkz. [Bilinen uyumsuzluklar](#bilinen-uyumsuzluklar). | — |
| `secretKey` | string | "" | JWT HMAC imza anahtarı. Token ömrü 48 saattir ve sabit kodludur (`util/helper.go` `GenerateToken`). | `util/helper.go` |
| `fictiveInstrumentSettingDefinitionPath` | string (yol) | "" | Endeks tanım CSV'si (bölen, kapanış, ISIN). Datastore indirmesi de bu dizine `IndicesDefinitions.csv` yazar. | `itch/itch.go` `createIndices`, `servicemodels/algo_api.go` `UpdateFictiveInstrumentSettings` |
| `fictiveItemSettingDetailPath` | string (yol) | "" | Endeks ağırlık CSV'si (hisse–endeks, ağırlık). Datastore `IndicesDetails.csv` yazar. Dosya yoksa veya bozuksa `log.Fatalf` → process çıkar. | aynı |
| `instrumentBazaarsPath` | string (yol) | "" | `ServerConfig.InstrumentMarketsFilePath` alanına okunur ama **hiçbir yerde kullanılmaz**. Pazar ataması endeks ağırlık dosyasından (`XYLDZ`/`XBANA`) türetilir. | — |
| `maxVolumePath` | string (yol) | — | **Okunmuyor.** | — |
| `interestRate` | float64 (oran, 0.14 = %14) | 0 | Volatilite hesabının faizi. Hesap kodu yorum satırında; açılışta yalnızca stdout'a basılır. | `volatility/manager.go` |
| `itchEnabled` | bool | false | Kendi ITCH beslemesi. false ise snapshot beklenmez; history ve AKD de başlamaz. | `itch/itch.go`, `main.go` |
| `itchWorkerCount` | int | 0 | ITCH SDK worker thread sayısı (`receiveItch`). | `itch/itch.go` |
| `itchTriggerWorkerCount` | int | 0 | ITCH SDK trigger worker sayısı. | `itch/itch.go` |
| `onloadStackName` | string | "" | OpenOnload stack adı; SDK'ya geçer. | `itch/itch.go` |
| `historyManagerEnabled` | bool | false | `TimeBased` mum kaydı ve volatilite yöneticisi. Yalnızca `itchEnabled=true` iken etkili. **AKD'nin ön koşuludur.** | `main.go`, [entegrasyonlar](entegrasyonlar.md#history-timebased-ve-volatility) |
| `cors` | string (regex) | "" | REST ve Admin REST CORS kontrolü. `"*"` her origin'e izin verir; değilse `regexp.MatchString(cors, origin)` uygulanır. **Boş regex her şeyle eşleşir**, yani anahtar yoksa tüm origin'ler kabul edilir. Doğrudan viper ile okunur. | `servicemodels/server.go` `allowedOrigin` |
| `context.timeout` | int | — | **Okunmuyor.** | — |

## `server`

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `server.hostname` | string | "" | REST gateway'in iç gRPC'ye bağlandığı adres (`{hostname}:{port}`). Dinleme adresi değildir; gRPC her zaman `:{port}` dinler. | `servicemodels/server.go` |
| `server.port` | int | 0 | gRPC (Data/Algo/Gui/Admin/Limit/Risk servisleri). Tipik değer 6620. | aynı |
| `server.restPort` | int | 0 | `GuiService` REST gateway (gzip + CORS). Tipik değer 6621. | aynı |
| `server.adminApiPort` | int | 0 | `AdminService` REST gateway. Tipik değer 6688. | aynı |
| `server.logLevel` | string | "" | logrus seviyesi (`debug`, `info`, ...). Boş veya geçersizse `info` kullanılır ve uyarı loglanır. | `main.go` |

## `gui` (WebSocket ve link)

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `gui.port` | string | "" | WS sunucusu `:{port}` (düz HTTP, TLS yok). Tipik değer 6623. | `gui/connections/ws_listener.go` `Serve` |
| `gui.hostname` | string (URL) | "" | Şifre sıfırlama e-postasındaki link tabanı: `{hostname}/passwordReset/{user}/{token}`. WS ile ilgisi yok. | `servicemodels/gui_api.go` → `util/aws_client.go` |
| `gui.ip` | string | "" | Okunur, kullanılmaz. | — |
| `gui.certificatePath`, `gui.certificateKeyPath` | string | — | **Okunmuyor.** WS ve REST TLS'siz çalışır; TLS ayrı bir katmanda sonlanmalı. ❓ doğrulanmadı: nginx vb. bir katman mı? | — |

## `database`

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `database.dbType` | string | "" | `sql.Open` sürücü adı. Pratikte `mysql`; kod yolu her zaman MySQL'dir. | `db/mysql/mysqldb.go` `GetMysqlDbInstance` |
| `database.host`, `.port`, `.user`, `.pass`, `.name` | string/int | "" / 0 | DSN: `user:pass@tcp(host:port)/name?multiStatements=true&parseTime=true`. | aynı |
| `database.maxConnection` | int | 0 | `SetMaxOpenConns`. 0 = sınırsız. | aynı |
| `database.maxIdleConnection` | int | 0 | `SetMaxIdleConns`. | aynı |

`sql.Open` hata verirse `Db` nil kalır; hata loglanmaz.

## `monitoring`

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `monitoring.enabled` | bool | false | ITCH SDK'nın izleme portu açılsın mı. | `itch/itch.go` → `receiveItch` |
| `monitoring.port` | int | 0 | İzleme portu. | aynı |

## `itchConfigurations[]`

Her eleman bir (pazar, partition) beslemesidir (`conf.ItchConfiguration`, JSON tag'leri):

| Alan | Tip | Anlam |
|------|-----|-------|
| `market` | string | `spot` veya `derivative`/`derivatives`. Bilinmeyen değer uyarıyla `Viop` olur. |
| `part` | int | Partition. **Kod yalnız 1–4'ü eşler; diğer değerler uyarıyla `Partition1` olur** (`itch/itch.go`). |
| `localInterface` | string | Multicast alınan NIC. |
| `itchIp`/`itchPort`, `itchSecondaryIp`/`itchSecondaryPort` | string/int | ITCH multicast grubu, birincil ve ikincil. |
| `srcIp`, `srcSecondaryIp` | string | Multicast kaynak IP (SSM). |
| `glimpseIp`/`glimpsePort`, `glimpseSecondaryIp`/`glimpseSecondaryPort` | string/int | GLIMPSE snapshot sunucusu. |
| `glimpseUsername`, `glimpsePassword` | string | GLIMPSE kimliği (gizli). |
| `rewinderIp`/`rewinderPort`, `rewinderSecondaryIp`/`rewinderSecondaryPort` | string/int | Rewinder (kayıp paket tekrarı). |
| `rewinderLocalPort` | int | Rewinder yerel portu. Eleman başına farklı olmalıdır (repo örneğinde 36001–36008). ❓ doğrulanmadı: çakışırsa ne olur? |

ITCH akışının kendisi: [veri-akisi.md](veri-akisi.md).

## `tradeVerifier` (VERDA)

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `tradeVerifier.enabled` | bool | false | Açılışta tavan/taban/maks emir değeri ve `isBrutTakas` yazımı. **Kapalıysa `minPrice`/`maxPrice`/`maxOrderValue` hiç güncellenmez.** |
| `tradeVerifier.downloadEnabled` | bool | false | false ise VERDA'ya gidilmez. Bugünün `DDMMYYYY_bulletin.csv` ve `DDMMYYYY_margin.csv` dosyaları çalışma dizininde aranır; yoksa process çıkar. |
| `tradeVerifier.verifierType` | int | 0 | `1` = VERDA. Başka değerde `NewTradeVerifier` nil döner → panic. |
| `tradeVerifier.verifierUrl` | string (URL) | "" | VERDA servisi taban adresi. `/files` ve dosya linkleri buna eklenir. |
| `tradeVerifier.verifierUser`, `.verifierPass` | string | "" | Basic Auth (gizli). |

Davranış ve hata tablosu: [entegrasyonlar.md → TradeVerifier](entegrasyonlar.md#tradeverifier-verda).

## `datastore`

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `datastore.enabled` | bool | false | ITCH bootstrap'ta endeks CSV'lerini Borsa İstanbul Datastore'dan indir. |
| `datastore.url` | string (URL) | "" | API tabanı. **`/` ile bitmeli**, çünkü `login`, `library` ve `file` doğrudan eklenir. |
| `datastore.username`, `.password` | string | "" | Login e-postası ve şifresi (gizli). |

## `akd` (Foreks)

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `akd.isEnabled` | bool | false | AKD yöneticisi. Ayrıca `itchEnabled` ve `historyManagerEnabled` gerekir. |
| `akd.akdUrl` | string (URL) | "" | Dağılım servisi tabanı (`/code/{SYM}.BIST/type/E/from/..`). |
| `akd.bistInstUrl` | string (URL) | "" | Aracı kurum listesi tabanı (`/search?status=ACTIVE&type=A`). |
| `akd.akdUserName`, `.akdPassword` | string | "" | Basic Auth (gizli). |
| `akd.bist30InstrumentId` | int | 0 | Skorlanacak endeksin (BIST30) bellek/DB id'si. Bulunamazsa AKD manager nil olur → panic. Tüm müşteri config'lerinde `3`. |

Skor formülleri: [entegrasyonlar.md → AKD](entegrasyonlar.md#akd-aracı-kurum-dağılımı-foreks).

## `byf` (Fon Takibi sepeti)

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `byf.enabled` | bool | false | Açılışta BYF dosyasını indir ve oku. |
| `byf.isHtmlBased` | bool | false | true: `.xls` uzantılı HTML tablo (goquery). false: gerçek Excel (excelize). |
| `byf.byfFileUrl` | string (URL) | "" | Fon portföy şirketinin sepet dosyası. Repo örneğinde ZPX30 kullanılıyor. |
| `byf.byfFileName` | string | "" | İndirilen dosyanın yerel adı (çalışma dizinine göre). |
| `byf.byfSheetIndex` | int | 0 | Excel modunda sayfa indeksi (0-tabanlı). |
| `byf.byfInfoColumnName` | string (tek harf) | — | Fon başlık bilgilerinin kolon harfi (`"B"`). **İlk karakteri `[0]` ile okunur; anahtar yoksa veya boşsa config yüklenirken panic olur. Bu, `byf.enabled=false` iken de geçerlidir.** |
| `byf.byfInstrumentsStart` | uint32 | 0 | Sepet satırlarının başladığı satır indeksi (0-tabanlı). |
| `byf.rowIndexes.{nameRow, codeRow, isinRow, indexRow, calculationDateRow, minTransValueRow, cashEquivalentsRow, noOfStocksRow, netActiveValueRow, valuationDateRow, validityDateRow, freeFloatRow, totalNumberRow, netAssetValRow}` | uint32 | 0 | Başlık alanlarının satır indeksleri (0-tabanlı, `byfInfoColumnName` kolonunda). |

`BYFConfig.ByfFilePath` struct'ta var ama hiçbir anahtardan okunmaz.

## `extServices[]`

| Alan | Tip | Anlam |
|------|-----|-------|
| `application` | string | `orderserv`, `hft` veya `algotrading` (`gui/connections/connections.go` `Applications.String`). Başka değer bağlanmaz. |
| `ip`, `port` | string / int | Hedef gRPC adresi. Tipik portlar: orderserv 9035, algotrading 9098; hft müşteriye göre değişir (aşağıdaki tablo). |
| `username`, `password` | string | Hedef serviste `Login` için kullanılan kimlik (gizli). |
| `applicationUser` | string | Strateji emirlerinde kullanılan uygulama kullanıcısı (`GetApplicationUsername`), `Application_Users` tablosundaki adla eşleşir. |

Bağlantılar, ilk `DataService.Login`'den (order-service) sonra kurulur. Bkz. [README → Açılış sırası](README.md#açılış-sırası-cmddataappmaingo).

## `requestLog` ve env override'ları

`main.go`'da `viper.BindEnv` ile bağlanır. Env değişkeni varsa dosyadaki değeri ezer. Gerekçe (kod yorumu): `config.json` bir branch'in tüm kurulumlarında ortaktır, bu üç değer ise host'a özgüdür.

| Anahtar | Env | Tip | Varsayılan | Anlam |
|---------|-----|-----|-----------|-------|
| `requestLog.trustedProxies` | `REQUESTLOG_TRUSTED_PROXIES` | string listesi (IP veya CIDR) | boş | Bu kaynaklardan gelen `X-Real-IP`/`X-Real-Port`/`X-Server-*` başlıklarına güvenilir. Loopback her zaman güvenilir. Geçersiz CIDR → request log kapanır. ❓ doğrulanmadı: env'de çoklu değerin ayraç biçimi (viper `GetStringSlice` boşlukla böler). |
| `requestLog.targetIp` | `REQUESTLOG_TARGET_IP` | string | "" | Kayıtlara yazılacak sabit hedef IP. Boşsa istekteki `X-Server-Addr` veya yerel adres kullanılır. |
| `requestLog.targetPort` | `REQUESTLOG_TARGET_PORT` | string | "" | Aynısı, port için. |

Config dışı, zorunlu env'ler:

| Env | Anlam |
|-----|-------|
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | **Zorunlu.** Yoksa `NewAwsClient` `log.Fatal` çağırır, process açılmaz. |
| `AWS_REGION` | SES (şifre sıfırlama e-postası) bölgesi. SNS bölgesi sabit kodlu `eu-west-2`. |

## Müşteri config'leri — yapısal farklar

Kaynak: Algo-Setup `development` `2a3c5d5`, `Configs/<Müşteri>/dbservice-config.json`. Sekiz müşterinin tümünde ortak:
- `itchEnabled=true`, `akd.isEnabled=false`, `byf.enabled=false`, `monitoring.enabled=false`, `verifierType=1`, `interestRate=0.14`.
- Portlar 6620/6621/6688/6623.
- Üst seviye `logLevel=debug` (okunmaz). `server.logLevel`, `cors` ve `requestLog` anahtarları **hiçbirinde yok**.

| Müşteri | Spot part | VİOP part | `tradeVerifier` enabled / download | `datastore` | `historyManager` | `extServices` (hft portu) | worker / trigger | `onloadStackName` |
|---------|-----------|-----------|-----------------------------------|-------------|------------------|----------------------------|------------------|-------------------|
| A1 | 1–4 | 1–4 | ✔ / ✔ | anahtar yok | ✔ | orderserv, hft (9099), algotrading | 8 / 1 | anahtar yok |
| Alnus | 1–4 | — | ✔ / **✘** | anahtar yok | ✘ | orderserv, hft (9036) | 8 / 1 | var |
| Alnus-Algo | 1–4 | 1–4 | ✘ / ✘ | anahtar yok | ✘ | orderserv, hft (9036) | 8 / 1 | var |
| Global | 1–4 | — | ✔ / ✔ | anahtar yok | ✘ | orderserv, hft (9036) | 4 / 1 | var |
| Marbas | 1–4 | — | ✘ / ✘ | anahtar yok | ✘ | orderserv, hft (9099) | 4 / 1 | var |
| Piramit | 1–4 | — | ✔ / ✔ | ✔ | ✘ | orderserv, hft (**9098**) | 10 / 1 | var |
| Piramit_Algo | 1–4 | **1–6** | ✘ / ✘ | anahtar yok | ✘ | orderserv, algotrading | 10 / 1 | var |
| Seker | 1–4 | — | ✔ / ✔ | ✔ | ✘ | orderserv, hft (9036) | 10 / 1 | var |

Çıkarımlar. Hepsi aday; dağıtım ortamının gerçek durumu doğrulanmadı.
- **Tavan/taban yazılmayanlar:** Alnus-Algo, Marbas ve Piramit_Algo'da `tradeVerifier` kapalı, dolayısıyla `Instrument.minPrice/maxPrice/maxOrderValue` bu servisçe güncellenmez. ❓ doğrulanmadı: bu müşterilerde değerler başka bir yoldan mı yazılıyor?
- **Alnus `downloadEnabled=false`:** Açılışta çalışma dizininde günün bülten ve marj CSV'leri yoksa process gRPC açılmadan çıkar. ❓ doğrulanmadı: dosyalar elle mi konuyor?
- **Piramit_Algo VİOP 5–6:** Kod partition 5 ve 6'yı `Partition1`'e eşler. README'deki "5–6. partition görünmüyor" sorusundan farklı bir durum: burada yanlış partition'a abonelik söz konusu. A1 ve Alnus-Algo VİOP'ta 4 partition tanımlıyor; README'deki açık soru sürüyor.
- **Datastore kapalı altı müşteri:** Endeks CSV'leri imajdaki yerel dosyadan gelir (repo kopyası 31/10/2024 tarihli). Elle güncellenmiyorsa endeks bölen ve ağırlıkları eskidir.
- **AKD ön koşulu:** `akd.isEnabled` her yerde false. Açılsa bile yalnız A1'de `historyManagerEnabled=true` olduğu için AKD yalnız orada çalışabilir.

## Bilinen uyumsuzluklar

- **`logLevel`:** Tüm config'ler (repo dahil) seviyeyi üst seviye `logLevel` altında veriyor, kod ise `server.logLevel`'ı okuyor. Sonuç: her kurulumda log seviyesi fiilen `info`. Açılışta `Unrecognised logLevel "", falling back to info` uyarısı görünür.
- **Okunmayan anahtarlar:** `logLevel`, `maxVolumePath`, `context.timeout`, `gui.certificatePath`, `gui.certificateKeyPath`. `instrumentBazaarsPath` ve `gui.ip` okunur ama kullanılmaz.
- **`ServerConfig.TokenTimeout`:** Struct'ta var, hiçbir anahtardan okunmaz. JWT süresi sabit 48 saat.
- **Repodaki `config.json` gerçek kimlik bilgileri içeriyor:** DB, VERDA, Datastore, AKD, GLIMPSE ve `secretKey`. Bu dokümana alınmadı. ❓ Rotasyon ve repo dışına taşıma kararı kullanıcıya ait.
