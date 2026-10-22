---
kapsam: AlgorithmicTrading (AlgoProd) Configuration.ini tam referansı — sözdizimi ve parser tuzakları, anahtarlar (tip, varsayılan, birim, kullanan kod, okunup kullanılmayanlar), sabit kodlu ayarlar, env/argüman, deploy, müşteri config farkları
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading          # prod binary'si master'dan derlenir (algo.yml → Algo-Setup main)
    branch: master
    commit: aa150ee
  - repo: Algo-Setup                  # Configs/<Müşteri>/Algo-Configuration.ini, MAAlgoProd/
    branch: development
    commit: 2a3c5d5
  - repo: itch-sdk                    # rewinder local port bind
    branch: development
    commit: 35a3b5c
dogrulama: 2026-10-22
durum: taslak
---

# AlgorithmicTrading (AlgoProd) — `Configuration.ini` referansı

Özet tablo [README → Config](README.md#config-configurationini)'dadır. Bu dosya tam referanstır. Servisler arası uyuşması gereken değerler (portlar, kullanıcılar, ITCH): [40-operasyon/config-referansi.md](../../40-operasyon/config-referansi.md).

Değerler maskelidir. Gerçek değerler Algo-Setup `Configs/<Müşteri>/Algo-Configuration.ini` ve repo şablonundadır; buraya yazılmaz.

## Nasıl okunur

- **Dosya yolu:** `argv[1]` (`Main.cpp` `loadConfiguration`). Argüman yoksa cwd'ye göre `Configuration/Configuration.ini`; 2'den fazla argüman `BaseException` fırlatır. Deploy'da `/workingDirectory/AlgorithmicTrading/Configuration.ini` (`MAAlgoProd/scripts/run.sh`).
- **Parser:** `ConfigurationManager::loadConfigurations` + `ParserUtility::readLine` / `getTokens`. INI değil, özel sözdizimi:
  - Her satır baştan ve sondan kırpılır (boşluk, `\t`, `\r`, `\n`, `\f`, `\v`).
  - **İçinde `&` geçen her satır** bölüm kapanışıdır. Kapanış bulunmazsa **içinde `$` geçen satır** bölüm açılışıdır. Değerde `&` veya `$` olan satır (ör. şifre) bölüm işaretçisi sanılır, parse bozulur.
  - Yorum sözdizimi yok. `#` ile başlayan satır da anahtar-değer gibi işlenir.
  - Anahtar-değer: satır `:` ile bölünür. Boş parçalar atlanır, kalanlar kırpılır. **Tam 2 parça yoksa satır sessizce atlanır.** Sonuçlar:
    - Değerinde `:` olan satır okunmaz: `http://…` URL'leri, IPv6, `host:port`.
    - `anahtar:<TAB>:değer` biçimi 3 parça üretir: ortadaki `"\t"` uzunluğu 1 olduğu için atlanmaz, kırpılınca `""` olur. Satır atlanır. Repo şablonundaki ve bütün müşteri config'lerindeki `secondaryRewinderIp:` / `secondaryRewinderPort:` satırları bu yüzden **hiç okunmuyor** (aşağıda, Şüpheli).
  - Bölüm açılışı `$Ad :On`. Tam 2 parça gerekir, yoksa `ParseException("invalid token count")` fırlar. Değer büyük harfe çevrilir; yalnız `ON` olan bölüm üst bölüme eklenir. Başka değerde bölüm parse edilir ama atılır, içindeki anahtarlar kaybolur. Kök bölümün (`$MainConfiguration`) On/Off değeri dikkate alınmaz.
  - Kapanış adı açılışla eşleşmezse veya bölümler dengesizse `ParseException`.
  - Aynı anahtar iki kez yazılırsa sonuncusu geçerli olur (`std::map` ataması).
- **Hata davranışı:** `loadConfiguration` `main` içinde `try` dışında çağrılır. Parse istisnası yakalanmaz, process `std::terminate` ile düşer. `run.sh` `ulimit -c unlimited` yaptığı için core dump bırakır.
- **Bölüm yapısı:** Kökün altında yalnız `Equity` ve `Derivative` olabilir; başka ad `ParseException("unknown market type")`. Pazarın her alt bölümü partition sayılır. Partition altında yalnız `Glimpse` ve `Itch` olabilir; başka ad `ParseException("unknown user type")`.
- **Arama:** Ana bölüm getter'ları yalnız kök haritaya bakar. Pazar düzeyindeki `localInterface`, `srcIp`, `secondarySrcIp` doğrudan pazar haritasından okunur; köke düşmez.
- **Tipler:** Değerler string tutulur.
  - `std::stoi` ile okunanlar (**zorunlu**): eksik veya sayısal değilse `std::invalid_argument` fırlar ve process çöker.
  - Bölüm içi portlar `std::atoi` ile okunur; eksikse 0 olur.
  - ITCH ayar anahtarları `getIntItem` ile okunur; eksik veya bozuksa varsayılan kullanılır.
  - Bool yalnız **tam olarak `true`** ise doğrudur. `True`, `Y`, `1` → false. (HftSrvProd'daki `"Y"` kuralından farklıdır.)
- **Dizinler:** Çalışma kökü `std::filesystem::current_path().parent_path()`'tir, yani **cwd'nin bir üstü**. Container'da WORKDIR `/workingDirectory/AlgorithmicTrading` olduğu için kök `/workingDirectory` olur. `logDirectory`, `cnfDirectory`, `strategyLogPath` bu köke göre birleştirilir.
  - `createFullPath(kök, değer)` yalnız **kökü** `mkdir` eder, hedef dizini yaratmaz. Hedefi yalnız `strategyLogPath` için ayrıca `mkdir 0755` yapılır. Log dizini container'da volume olarak bağlı olduğu için zaten vardır.
  - Binary başka bir cwd'den çalıştırılırsa bütün log yolları kayar.
- **stdout:** Açılışta dosya adı, çalışma, config, log ve strateji log dizinleri ile log seviyesi basılır. Şifreler basılmaz (HftSrvProd'dan farklı). Ama `StrategyServiceImpl::StrategyLogin` dönen token'ı stdout'a basar.

## Ana bölüm (`$MainConfiguration`)

| Anahtar | Tip | Varsayılan | Anlam / birim | Kullanan kod |
|---------|-----|-----------|---------------|--------------|
| `logDirectory` | string (dizin) | "" | `<kök>/<değer>`. NanoLog dosyaları ve ITCH SDK log'u buraya yazılır. Deploy'da `log` → `/workingDirectory/log` (compose volume'u). | `Logger.h`, `ItchSdkManager::startItchSdkManager` |
| `logFile` | string (önek) | "" | NanoLog dosya adı `<logFile>_<YYYYMMDD>`. GuaranteedLogger; dönme eşiği 1000 (NanoLog'da MB ❓ doğrulanmadı). `run.sh` `algo*` ve `itchsdk*` dosyalarını yedekler. | `Logger.h` |
| `logLevel` | string | "" | NanoLog: `debug` ve `info` → INFO, `warn` → WARN, **diğer her şey (boş dahil) → CRIT**. `debug` NanoLog'da DEBUG açmaz. ITCH SDK: `debug` → Debug, `info` → Info, diğer → Error. | `getNanoLogLevel`, `getItchSDKLogLevel` |
| `strategyLogPath` | string (dizin) | "" | Strateji başına log kökü. `StrategyLogger` altına `<komut tipi>/<exchangeInfo>/` açar. | `StrategyLogger.cpp` |
| `cnfDirectory` | string (dizin) | "" | Yol hesaplanır ve basılır, **kullanılmaz** (eski yerel strateji ayarı kalıntısı; ayarlar artık DB'de). | — |
| `volatilityFile` | string | "" | Tek kullanıcısı (`WarrantEuropeanFormula`) yorum satırında. **Etkisiz.** | — |
| `monitoringEnabled` | bool (`true`) | false | PerfSDK `start("algo_prod", monitoringPort, 0, 2000, false)`. Histogram üst sınırı 2000 µs (HftSrvProd'daki 60 s ayarı yok). `setPerformanceDbExporter` hiç çağrılmaz, yani **ClickHouse'a push yok**, ölçümler bellekte kalır. Ayrıca `TIME_MEASUREMENT` makrolarını açar. | `Application::runTests`, `TimeUtility.h` |
| `monitoringPort` | string | "" | `start`'a geçer. PerfSDK port açmaz ([performance-sdk](../performance-sdk/README.md)). | aynı |
| `clientPort` | int | **zorunlu** | gRPC `StrategyService` dinleme portu, `0.0.0.0:<port>`, insecure, health check açık. `std::stoi` gRPC thread'inde çağrılır. | `GUIManager::startGrpcServer` |
| `ouchIp`, `ouchPort` | string | "" | **order-service MARpc**, BIST değil. | `OuchManager::startOuchStreaming` |
| `ouchUsername`, `ouchPassword` | string | "" | ouch-sdk login (`Application::AlgoTrading`). Anahtar adı `ouchUsername`'dir, HftSrvProd'daki `ouchUserName` değil. Login başarısızsa yalnız `"Failed at ouch server login!"` loglanır ve açılış **devam eder**: userbook'lar yaratılmaz, `getAllOrders` çağrılmaz. HftSrvProd bu durumda istisna fırlatır. | `OuchManager::login`, `OuchManager::start` |
| `dbIp`, `dbPort` | string | "" | **trade-data-app gRPC** (`AlgoService`), MySQL değil. Kanal insecure, mesaj boyu sınırsız (-1). | `DatabaseServiceClient::Connect` |
| `dbUsername`, `dbPassword` | string | "" | `AlgoLogin(application=AlgoTrading)`. Boş token dönerse yapıcı `"Failed to Connect Database Service!"` fırlatır. İlk çağrı `startApplication` içinde `try` dışındaki `SettingsManager::loadAllSettingsFiles`'tan gelir, yani process çöker. `dbUsername` ayrıca strateji ayarlarının **`application_user` anahtarıdır** (`setStrategySettings`, `DatabaseServiceClient.cpp`). | `DatabaseServiceClient`, `BaseStrategyCommand` |
| `holidaysBIST` | string (dosya yolu, cwd'ye göre) | "" | BIST tatil günleri; ilk satır virgüllü tarih listesi. Dosya yoksa yalnız "File is empty" basılır ve vade hesabı tatilsiz yapılır. CI `MAProdEnv/scripts/holidays.csv` dosyasını binary'nin yanına koyar. | `TimeUtility.h` |
| `workerCount` | int | **zorunlu** | `AlgoWorkerManager` thread sayısı (Arbitraj worker havuzu, [README](README.md#strateji-çalıştırma-modeli)). | `AlgoWorkerManager` |
| `triggerWorkerCount` | int | — | Okunur; getter'ı çağıran yok. **Etkisiz.** | — |
| `TRY`, `USD`, `EUR` | double (oran; 0.14 = %14) | — | Varant teorik fiyatının faizi, para birimine göre. Tek kullanıcı `WarrantTracker` (kullanılmayan strateji, [katalog](../../20-stratejiler/README.md#kullanılmayan-kod)). Pratikte **etkisiz**. Eksik para birimi `std::stod` istisnası verir. ❓ doğrulanmadı: oranın yıllık olduğu. | `WarrantEuropeanFormula.cpp` |
| `akdUrl`, `akdUserName`, `akdPassword`, `akdLogFile` | string | — | **Okunmuyor.** AlgoProd AKD'yi trade-data-app'ten (`FetchAkd`) alır. | — |
| `combinerEnabled` | bool (`true`) | false | development'ta okunur ama **kullanılmaz**. ⚠ master'da farklı: `OuchManager` `isCombinerEnabled()` ile okur. | — |
| `onloadStackName` | string | "" | development'ta okunur ama **kullanılmaz**; ITCH stack'i `itchOnloadStackName`'dir. ⚠ master'da farklı: ITCH SDK'ya bu değer gider (`ItchSdkManager.cpp`). | — |
| `localIp` | string | — | Getter var, çağıran yok. | — |

### ITCH SDK ayarları (ana bölüm, hepsi opsiyonel)

⚠ master'da yok (2026-10-22): ITCH SDK v3 geçişiyle (2026-07-07) development'a geldi. Hiçbir müşteri config'inde bu anahtarlar yok, yani varsayılanlar geçerli.

| Anahtar | Varsayılan | Birim / anlam |
|---------|-----------|---------------|
| `itchOnloadStackName` | `algo-itch` | ITCH UDP soketlerinin Onload stack'i |
| `itchMainRingBufferSize` | 65536 | slot |
| `itchRewinderRingBufferSize` | 16384 | slot |
| `itchReceiverCpuCore1` … `4` | -1 | RX thread core'u; -1 = pin yok |
| `itchBusyPollUsec` | 0 | µs |
| `itchSocketRcvBufBytes` | 0 | byte; 0 → SDK 64 MB kullanır (`ItchReceiver::setupSocket`) |
| `itchGlimpseRetryCount` | 3 | deneme |
| `itchGlimpseRetryBackoffMs` | 500 | ms |
| `itchGlimpseStartTimeoutMs` | 60000 | ms (HftSrvProd'da sabit 30000) |
| `itchRewinderRequestTimeoutMs` | 5000 | ms |

## Pazar bölümleri (`$Equity`, `$Derivative`)

`$Equity` Spot, `$Derivative` VİOP'tur. Bölüm `:Off` ise pazar hiç kurulmaz.

| Anahtar (pazar düzeyi) | Anlam |
|------------------------|-------|
| `localInterface` | Multicast'in alındığı NIC (`broadcastLocalInterface`) |
| `srcIp`, `secondarySrcIp` | Multicast kaynak IP'si (SSM). Hem ITCH hem Rewinder kaynak filtresi olarak kullanılır. |

**Partition numarası:** `ReadMarket` partition'a `partitionMap.size() + 1` verir. Yalnız `:On` olanlar sayıldığı için **SDK partition'ı, `On` partition'ların sırasıdır** (1, 2, …). Bağlantı adı `spot<i>` / `viop<i>`'dir. HftSrvProd'daki `[[markets]]` ile aynı mantıktır. VİOP için 5. ve 6. partition'lar SDK'nın snapshot-end beklentisine dahil değildir: [itch-sdk/alim-yolu § 8](../itch-sdk/alim-yolu.md#8-partition-varsayımları-ve-partid-k-01--ertelendi).

**`$Partition` → `$Glimpse`:** `ip`, `port`, `secondaryIp`, `secondaryPort`, `userName` (`<GLIMPSE_USER>`), `password` (`<REDACTED>`).

**`$Partition` → `$Itch`:**

| Anahtar | Tip | Anlam |
|---------|-----|-------|
| `ip`, `port`, `secondaryIp`, `secondaryPort` | string / int | ITCH multicast grubu, birincil ve ikincil hat |
| `rewinderIp`, `rewinderPort` | string / int | Rewinder sunucusu |
| `secondaryRewinderIp`, `secondaryRewinderPort` | string / int | İkincil Rewinder. Müşteri config'lerinde yazım hatası yüzünden okunmuyor (yukarıda). Okunmazsa SDK'ya `""` ve `"0"` gider. |
| `rewinderLocalPort` | int | Rewinder yanıtlarının geldiği yerel UDP portu. ITCH SDK `SO_REUSEADDR` olmadan `bind` eder, yani **host genelinde benzersiz olmalıdır**. development: eksik veya ≤0 ise Spot `28000+i`, VİOP `28100+i` (kod yorumu: "HftSrv'nin 26xxx'iyle çakışmasın"). ⚠ master'da farklı: varsayılan yok, eksikse `"0"` gider. |
| `clientCpuCore` | int | ITCH decode thread core'u; eksikse -1, ≤0 = pin yok. ⚠ master'da yok. |

Kurallar:
- Partition başına yalnız ilk `Glimpse` ve ilk `Itch` kullanılır (`[0]`).
- `$Glimpse` bölümü `$Itch`'ten **önce** gelmelidir: `Itch` yapıcısı `glimpseClients[0]`'ı okur. Glimpse yoksa, kapalıysa ya da sonra geliyorsa tanımsız davranış oluşur. Itch'i kapalı partition da `getItchSdkConfigurations`'ta `itchClients[0]` ile aynı soruna düşer.
- Emir defterinin hazır olması için en fazla 600 sn beklenir (`Application::runTests` → `waitForInitialization`). Süre dolarsa açılış istisnayla durur.

## Config'te olmayan, sabit kodlu ayarlar

| Ayar | Değer | Yer |
|------|-------|-----|
| Varsayılan config yolu | `Configuration/Configuration.ini` (cwd'ye göre) | `Main.cpp` `loadConfiguration` |
| Çalışma kökü | cwd'nin üst dizini | `ConfigurationManager::loadConfigurations` |
| order-service'e bağlanmadan önce bekleme | 3000 ms | `OuchManager::start` |
| Emir defteri hazır bekleme | 600 sn | `Application::runTests` |
| Strateji emir gönderim zaman aşımı | 10 sn (VWAP) | [README → Emir yolu](README.md#emir-yolu) |
| PerfSDK | app adı `algo_prod`, aralık 0–2000 µs, ClickHouse exporter yok | `Application::runTests` |
| gRPC sunucusu | `0.0.0.0`, insecure, health service | `GUIManager::startGrpcServer` |
| DataService kanalı | insecure, gönderim/alım sınırı yok, deadline yok | `DatabaseServiceClient::Connect` |
| Sentry | DSN (`<REDACTED>`), release `mtrader-algoprod@1.5`, debug açık, veritabanı `.sentry-native` | `Main.cpp` |

## Env, argüman, sinyal

- `argv[1]`: config yolu. argv ayrıca `itchsdk_set_arguments` ile ITCH SDK'ya geçer. ❓ doğrulanmadı: SDK'nın argv'den ne okuduğu (birincil/ikincil hat seçimi olabilir).
- `LD_PRELOAD`: Onload derlemesinde (`HAS_ONLOAD`) boşsa `libonload.so` set edilip `execvp` ile yeniden başlanır; ardından `onload_set_stackname(ALL_THREADS, GLOBAL, DONT_ACCELERATE)` çağrılır. Mellanox derlemesinde (`HAS_MLX`) aynısı `libvma.so` ile yapılır. HftSrvProd ve order-service ile aynı desendir.
- Config'i ezen başka env yoktur (`getenv` yalnız `LD_PRELOAD`).
- Sinyaller (`Application::startApplication`): SIGINT, SIGHUP, SIGUSR1, SIGUSR2 → `signalHandler`. SIGPIPE yok sayılır. **SIGTERM ve SIGABRT handler'ı yorum satırında.**

## Deploy (Algo-Setup `MAAlgoProd/`)

- **İmaj:** `meeapps/maprodenv:3.0`, WORKDIR `/workingDirectory/AlgorithmicTrading`. Binary ve config `/workingDirectory/AlgorithmicTrading/`'e konur.
  - Onload Dockerfile OpenOnload **9.0.1.86** derler. HFT, order-service ve trade-data-app imajları ile host kurulumu (`install_onload.sh`) **9.2.0.43** kullanır. Dockerfile notuna göre host sürücüsü ile userspace sürümü aynı olmalıdır. ❓ doğrulanmadı: bu farkla Onload'un çalışıp çalışmadığı.
  - Onload Dockerfile ayrıca `/workingDirectory/config/AlgoSettings`'i yaratır (kalıntı).
- **Compose:** container `MAAlgoProd`, `network_mode: host`, `restart: always`. Volume'lar `container-logs/MAAlgoProd/` → `/workingDirectory/log` ve `sock/`. HFT'deki `cpuset`, `cap_add`, `ulimits` **yok**; Onload varyantında yalnız `/dev/onload*` ve `/dev/sfc_char` cihazları verilir.
- **`run.sh`:** `AlgoProd <config>`. SIGTERM'de log ve `strategyLog/WarrantTracker` dizinini `tar.gz` yapar. HFT'nin aksine S3'e yüklemez. `COMPANY_NAME` ve `MODE` CI'da script'e eklenir ama `run.sh`'te kullanılmaz.
- CI'daki paketleme, `setup_mode` ve gece güncellemesi: [config-referansi § 2](../../40-operasyon/config-referansi.md#2-paketleme-ve-gece-güncellemesi).

## Müşteri config'leri — yapısal farklar

Kaynak: Algo-Setup `development` `2a3c5d5`, `Configs/<Müşteri>/Algo-Configuration.ini` (8 müşteri). Dosya her müşteri klasöründe var, ama development CI matrisinde AlgoProd kuran tek paket `Alnus_Algo_Setup`'tır ve o da kurulmaz ([config-referansi § 2](../../40-operasyon/config-referansi.md#2-paketleme-ve-gece-güncellemesi)).

**Hepsinde ortak:**
- `clientPort=9098`, `ouchPort=8000`, `monitoringEnabled=false`, `monitoringPort=9092`, `logLevel=info`, `combinerEnabled=false`
- `TRY=0.14`, `USD=0.0225`, `EUR=0.024`
- `dbUsername` ile `ouchUsername` aynı uygulama kullanıcısı (`algoUser`)
- ITCH SDK ayar anahtarları, `clientCpuCore` ve `itchOnloadStackName` hiçbirinde yok
- Equity 4 partition açık. Derivative pazarı açık.
- `secondaryRewinderIp:` / `secondaryRewinderPort:` satırları (pazar ve partition başına) hepsinde okunmuyor; toplam 136 satır.
- AKD anahtarları dolu ama okunmuyor.

| Müşteri | `workerCount` / `trigger…` | `dbIp`:`dbPort` | `ouchIp` | Derivative partition | `rewinderLocalPort` | `onloadStackName` |
|---------|----------------------------|-----------------|----------|----------------------|---------------------|-------------------|
| A1 | 10 / 10 | loopback:6620 | **uzak IP** | 6 | 26001–26010 | — |
| Alnus | 10 / 7 | **uzak IP:4540** | loopback | 6 | 26001–26010 | — |
| Alnus-Algo | 8 / 2 | loopback:6620 | loopback | 6 | 26001–26010 | — |
| Global | 7 / 2 | **uzak IP:5018** | loopback | **4** | **yok** → 28001–28004 / 28101–28104 | — |
| Marbas | 10 / 7 | **uzak IP:4540** | loopback | 6 | 26001–26010 | — |
| Piramit, Piramit_Algo, Seker | 10 / 10 | loopback:6620 | loopback | 6 | 26001–26010 | `algo-stack` (etkisiz) |

`localInterface` her müşteride farklıdır (Global'de Equity ile Derivative de farklı NIC). Değerleri config'tedir.

Çıkarımlar (hepsi aday; dağıtım ortamının gerçek durumu doğrulanmadı):
- **Alnus ve Marbas aynı uzak `dbIp:4540`'ı gösteriyor.** Değer iki müşteride birebir aynı. Kopyalama izi olabilir. ❓ doğrulanmadı: 4540/5018 bir NAT/port yönlendirmesi mi.
- **`rewinderLocalPort` 26001–26010, HftSrvProd müşteri config'leriyle birebir aynı** ([hftsrvprod/config.md](../hftsrvprod/config.md)). İki motor aynı host'ta çalışırsa ikinci açılan process'in Rewinder soketi bağlanamaz (log imzası: [config-referansi § 3.1](../../40-operasyon/config-referansi.md#31-port-matrisi)).
- **`clientPort=9098`, HftSrvProd müşteri config'lerindeki `grpcPort=9098` ile aynı** (Seker hariç). Aynı host'ta iki motor çalışamaz.
- **VİOP 6. partition'ın `secondaryPort`'u 21105**, yani 5. partition'la aynı (6 partition'lı bütün müşterilerde). ❓ doğrulanmadı: 21106 olması gerekip gerekmediği.
- **`onloadStackName=algo-stack`** development'ta etkisiz; ITCH `algo-itch` stack'ine geçer. master binary'sinde ise `algo-stack` kullanılır.

### ⚠ main'de farklı (Algo-Setup `main`, 2026-10-22)

- `Configs/Alnus`: `workerCount` 8 / 4; `dbIp` loopback:6620; NIC Alnus-Algo'nunkiyle aynı.
- `Configs/Alnus-Algo` → `Configs/Alnus_Algo` adıyla duruyor.
- `Configs/Kanjo` (yalnız main): Global'in kopyası. `dbIp:dbPort` Global'in uzak adresi:5018. Oysa Kanjo trade-data-app'i 7720'de dinliyor ([config-referansi § 3.1](../../40-operasyon/config-referansi.md#31-port-matrisi)).
- Prod binary'si `master`'dan derlenir. Bu yüzden `combinerEnabled` ve `onloadStackName` etkilidir; ITCH ayar anahtarları, `clientCpuCore` ve `rewinderLocalPort` varsayılanı yoktur.

## Şüpheli

- **`secondaryRewinder*` satırları okunmuyor (bug?):** Şablonda ve bütün müşteri config'lerinde `secondaryRewinderIp:<TAB>:<ip>` biçimi kullanılıyor. Parser bunu 3 parça görüp satırı atlıyor. İkincil Rewinder adresi SDK'ya hiç ulaşmıyor. ❓ doğrulanmadı: SDK ikincil hatta açılırsa Rewinder'ın davranışı.
- **Parser sessiz:** `:` içeren değerler ve 2 parçadan farklı satırlar uyarısız atlanıyor. `$`/`&` içeren değer bölüm yapısını bozuyor. Şifrelerde bu karakterler kullanılamaz.
- **Zorunlu anahtar eksikse çöküş:** `clientPort` gRPC thread'inde, `workerCount` worker başlatılırken `std::stoi` ile okunuyor. Parse istisnası da `try` dışında. Hepsi `std::terminate` ile biter.
- **DB login hatası çöküş, OUCH login hatası sessiz:** `dbUsername/dbPassword` yanlışsa process düşer. `ouchUsername/ouchPassword` yanlışsa process ayakta kalır ama order-service'e login olmamıştır; emir gönderimi ❓ doğrulanmadı.
- **SIGTERM handler kapalı:** `startApplication`'da SIGTERM satırı yorumlu. `run.sh` `kill -15 ${EXECUTABLE_NAME}` ile **isim** veriyor; bash `kill` isim kabul etmez. ❓ doğrulanmadı: `docker stop` sırasında AlgoProd'un düzgün kapanıp kapanmadığı (HFT `run.sh`'inde de aynı satır var).
- **Strateji logları kalıcı değil:** `/workingDirectory/strategyLog` volume'a bağlı değil, container yeniden yaratılınca kaybolur. `copy_strategy_logs.sh` `/workingDirectory/AlgorithmicTrading/strategyLog`'a bakıyor, yani yanlış dizine. Yalnız `WarrantTracker` (kullanılmayan strateji) dizinini yedekliyor.
- **README ile fark:** README'deki config tablosu `akdUrl…`'i "Foreks AKD" ve `triggerWorkerCount`'u "worker havuzu" diye listeliyor. İkisi de development'ta okunmuyor ya da etkisiz. `volatilityFile` de etkisiz.
- **master/development farkı:** Prod (master) binary'si `combinerEnabled`'ı kullanıyor, development kullanmıyor. `add-order-sdk` merge edilince combiner'ın yeniden bağlanıp bağlanmayacağı ❓.
- **Onload sürüm farkı:** AlgoProd imajı 9.0.1.86, host ve diğer imajlar 9.2.0.43 (Deploy).
- **Sentry DSN kaynak kodda sabit** (`Main.cpp`) ve debug modu açık. Değer buraya alınmadı.
- **Repo şablonu** gerçek görünen kimlik bilgileri (AKD, Glimpse, OUCH/DB şifreleri) ve iç hostname içeriyor. ❓ Rotasyon kararı kullanıcıya ait.
