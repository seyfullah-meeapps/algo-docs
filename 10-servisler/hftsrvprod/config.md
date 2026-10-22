---
kapsam: HftSrvProd Configuration.toml tam referansı (tip, varsayılan, anlam, birim, kullanan kod, okunup kullanılmayanlar), env değişkenleri, sabit kodlu ayarlar, prod'da kapalı tutulanlar ve müşteri config'leri arasındaki yapısal farklar
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: Algo-Setup                 # Configs/<Müşteri>/HFT-Configuration.toml
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-22
durum: taslak
---

# HftSrvProd — `Configuration.toml` referansı

Özet tablo [README → Config](README.md#config-configurationtoml)'dadır. Bu dosya tam referanstır. ITCH tarafındaki kullanım: [itch-entegrasyonu.md](itch-entegrasyonu.md).

## Nasıl okunur

- **Dosya:** Tek argüman olarak verilir (`HftSrvProd <config>`), argüman yoksa process çıkar. Repo örneği `src/Configuration/Configuration.toml`, müşteri dosyaları Algo-Setup `Configs/<Müşteri>/HFT-Configuration.toml`.
- **Parse:** `ConfigurationManager::loadConfiguration` toml++ kullanır. Parse hatası olursa `exit(1)`. `ConfigurationManager` master ile development'ta aynıdır. Master'da ayrıca kullanılmayan eski `Configuration.ini` dosyası durur.
- **Düz anahtarlar** (tablo olmayan her üst seviye anahtar) `configMap<string,string>`'e string olarak yazılır:
  - bool → `"Y"` / `"N"`
  - int → ondalık string
  - float → `ostringstream`
  - dizi → virgülle birleştirilmiş (yalnız int ve string elemanlar)
  - Bool getter'ları `== "Y"` karşılaştırır. Bu yüzden `"true"` string'i **false** sayılır, TOML bool kullanılmalıdır.
- Her düz anahtar açılışta `key: value` olarak stdout'a basılır, **şifreler dahil**.
- **Varsayılan kolonu:** "—" getter'ın değeri olduğu gibi döndüğünü gösterir (eksikse `""` / false). "**zorunlu**" `std::stoi` ile okunduğunu gösterir: eksik veya boşsa yakalanmayan istisna fırlar ve process çöker.
- Değerler maskelidir. Gerçek değerler Algo-Setup'tadır.

## Genel, log

| Anahtar | Tip | Varsayılan | Anlam / birim | Kullanan kod |
|---------|-----|-----------|---------------|--------------|
| `path` | string (dizin) | "" | Çalışma kökü. Log dizini `<path>/log` olur (`mkdir -p` ile `system()` üzerinden yaratılır). Quill dosyası `<path>/log/hft.txt` (1 GB'ta döner, 30 dosya). ITCH SDK log'u da aynı dizine yazar. | `ConfigurationManager::loadConfiguration`, `hft::log::init`, `ItchSdkClient::startItchSdkClient` |
| `logLevel` | string | "" → Info | Quill: `debug`, `info`, `warn(ing)`, `crit(ical)`, `none`; tanınmayan değer Info. ITCH SDK: `debug`→Debug, `info`→Info, **diğer her şey → Error**. `debug` ITCH yükünde log seli yaratır (toml yorumu). | `HftMain`, `ItchSdkClient::getItchLogLevel` |

## Worker'lar ve CPU pinleme

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `workerCount` | int | **zorunlu** | AlgoWorker thread sayısı. Stratejiler round-robin dağıtılır. | `AlgoWorkerManager` |
| `algoWorkerCores` | int dizisi | [] | i. worker → i. core. Listede olmayan worker pinlenmez. Pin ancak `HFT_RT_FIFO` env'i varsa SCHED_FIFO@80'e çıkar. | `AlgoWorkerManager::start`, `AlgoWorker::eventDispatcherLoop` |
| `mainCpuCores` | int dizisi | [] (pin yok) | Main thread'in affinity'si. Quill ve gRPC thread'leri açılmadan önce uygulanır, bu yüzden onlar da bu maskeyi miras alır. | `HftMain` |
| `receiverCpuCores` | int dizisi (ilk 4) | -1 ×4 | ITCH SDK RX thread'leri. Sırayla (iface, port) receiver'ı başına bir core atanır. 4'ten fazla receiver varsa fazlası pinsizdir. Bozuk token atlanır. | `ItchSdkClient::startItchSdkClient` |
| `triggerWorkerCount` | int | **zorunlu** | Yalnız konsol durum kutusunda basılır ("Triggers"). Başka etkisi yok. | `displaySystemStatus` |
| `ouchWorkerCount` | int | — | **Okunmuyor** (getter var, çağıran yok). | — |
| `internalOuchCores`, `internalOuchSchedFifo`, `internalOuchPriority` | int dizisi / bool / int | [] / false / 0 | Parse edilir. Tek kullanıcısı `OuchWorkerManager` yapıcısıdır ve o hiç oluşturulmaz (eski internal-OUCH kalıntısı). **Etkisiz.** | — |
| `affinityActive` | bool | false | **Okunmuyor.** | — |

## Hot öncelik ve Tavan/Taban tiering

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `hotWorkerCount` | uint16 | 0 | Adı sayı gibi ama **yalnız `> 0` kontrolü** yapılır. Değeri 0'dan büyükse iki şey olur: (1) worker'lar önce hot stratejileri işler, (2) Tavan ve Taban tiering'i (PriceThreshold aboneliği + cold'da callback kapatma) açılır. Ayrı bir hot worker havuzu yoktur. | `AlgoWorker`, `HftMaxPrice/HftMinPrice::setupTieringSubscription` |
| `realHotReadyQueue` | bool | false | Hot stratejinin ITCH olayını worker'ın hazır kuyruğuna koyar ([itch-entegrasyonu §4](itch-entegrasyonu.md#4-olayların-stratejilere-dağıtımı)). Env `HFT_REAL_HOT_READY_QUEUE` **önceliklidir** (aşağıda). | `ItchSdkClient`, `AlgoWorker` |
| `activationPctFromPreviousClose` | float (%) | 6.5 | Promote fiyatı = önceki kapanış × (1 + %/100), tick'e aşağı yuvarlanır. | Tavan ve Taban (aynı getter `getHftMaxPriceTier*`) |
| `demoteBandTicks` | int (tick) | 2 | Demote = promote − N tick | aynı |
| `minTierBandTicks` | int (tick) | 1 | Promote ile demote arasındaki asgari fark. Aşağısında tiering kapanır. | aynı |
| `minHotDwellMs` | uint64 (ms) | 250 | Promote'tan sonra en az bu kadar süre hot kalınır (steady clock) | aynı |
| `coldReentryCooldownMs` | uint64 (ms) | 250 | Demote'tan sonra yeniden promote için bekleme | aynı |
| `emergencyReentryTicks` | int (tick) | 2 | Fiyat promote + N tick'e ulaşırsa cooldown atlanır (0 = kapalı) | aynı |
| `minHotDwellUpdates` | uint32 | 1 | Getter var, **çağıran yok**. | — |

Hesabın ayrıntısı [tavan.md](../../20-stratejiler/tavan.md) ve [taban.md](../../20-stratejiler/taban.md)'dedir. Taban da `MaxPriceTier` adlı anahtarları kullanır; Taban'a özel anahtar yoktur.

## Strateji ITCH kuyruğu

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `strategyQueueMaxEvents` | size_t (olay) | 50000 | Strateji başına ITCH kuyruğunun yumuşak sınırı. Tüm stratejilerde ortaktır ve açılışta bir kez set edilir. Aşılırsa **yeni gelen olay** düşer. 0 verilirse 50000 kullanılır. `Strategy::setItchEventQueueMaxEvents` |

## ITCH beslemesi

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `spotSrcIp`, `spotSecondarySrcIp` | string (IP) | "" | Spot multicast kaynak IP'si (birincil/ikincil hat). Spot'un bütün partition'larında hem ITCH hem Rewinder kaynak filtresi olarak kullanılır. | `getItchSdkConfigurations` |
| `viopSrcIp`, `viopSecondarySrcIp` | string (IP) | "" | Aynısı, VİOP için | aynı |
| `itchOnloadStackName` | string | "" | ITCH SDK'ya giden Onload stack adı (UDP) | `ItchSdkClient` |
| `onloadStackName` | string | "" | OUCH TCP soketinin Onload stack'i. Handoff'ta `onload_set_stackname(THIS_THREAD)` ile yalnız soket açılırken uygulanır. Boşsa soket kernel'de kalır (uyarı loglanır). | `OuchManager::orderUserDisconnected` |
| `[[markets]]` | tablo dizisi | — | Bkz. aşağı | |

## MAOrderSDK (`sdk*`)

Boot sırası: [README → Açılış sırası](README.md#açılış-sırası-hftmaincpp). SDK tarafı anlamları: [maordersdk](../maordersdk/README.md).

| Anahtar | Tip | Varsayılan | Anlam / birim | Kullanan kod |
|---------|-----|-----------|---------------|--------------|
| `sdkLockMemory` | bool | false | true ise HftMain `mlockall(MCL_CURRENT\|MCL_FUTURE\|MCL_ONFAULT)` çağırır ve SDK'ya `lock_memory` geçer. mlockall başarısız olursa yalnız uyarı basılır. | `HftMain` |
| `sdkUseOnload` | bool | false | `use_onload`. `bootstrapOnloadIfRequested` yalnız bu Y **ve** `LD_PRELOAD` boşken bir şey yapar. | `HftMain` |
| `sdkRecvPinCore` | int | -1 | `OrderSdkConfig.recv_pin_core`. Handoff'ta gelen kullanıcının varsayılan recv core'u da budur. | `HftMain`, `OuchManager` |
| `sdkRecvSchedPolicy` | string | OTHER | `FIFO`→SCHED_FIFO, `RR`→SCHED_RR, diğer her şey → OTHER. **Yalnız handoff kullanıcısının** varsayılanı; `OrderSdkConfig`'e geçmez. | `OuchManager::orderUserDisconnected` |
| `sdkRecvSchedPriority` | int | 0 | Aynısı, öncelik | aynı |
| `sdkWarmIntervalMs` | int (ms) | 0 | MSG_WARM aralığı; 0 = kapalı | `HftMain` |
| `sdkReplayQuietWindowMs` | uint32 (ms) | 10000 | Replay bitiş tespiti. Toml yorumu: "prod doğrulaması olmadan kısaltmayın". | `HftMain` |
| `sdkFavoriteIdleResetMs` | uint32 (ms) | 1000 | Favori bağlantıya dönüş için boşta kalma süresi | `HftMain` |
| `sdkOrderHardCapTry` | uint32 (**tam TL**) | 50000000 | Tek emir notional üst sınırı. Aşan emir SDK'da 1003 ile reddedilir. | `HftMain` |
| `sdkHeartbeatIntervalMs` | uint32 (ms) | 1000 | İstemci → sunucu heartbeat | `HftMain` (`OuchConfig`) |
| `sdkTokenPoolSize` | uint32 | 100000 | Wire-token havuzu | aynı |
| `combinerEnabled` | bool | false | `enable_combiner`. true ise `maosdk->setItchSdk(itch::getItchSdk())` çağrılır. ouch-sdk yolunda `OuchManager::combinerEnabled`'a da yazılır. | `HftMain`, `OuchManager` |

### `[[ouch_users]]` (opsiyonel) ve `[[viop_ouch_users]]`

Kullanıcılar handoff ile gelir ([sistem-haritasi](../../00-genel/sistem-haritasi.md)). Bu tablo iki iş için okunur:
- `isActive=true` olan girişler boot'ta `OuchConfig.ouch_users`'a konur. Login yapılmaz. Konsoldaki "OUCH Users: N connected" sayısı da bunlardan hesaplanır.
- Handoff'ta `userName` eşleşirse recv-thread ayarları **override** edilir. `isActive=false` girişler yalnız ayar tablosu işlevi görür.

| Alan | Tip | Varsayılan | Anlam |
|------|-----|-----------|-------|
| `isActive` | bool | false | Boot listesine girsin mi |
| `ip`, `port`, `secondaryIp`, `secondaryPort` | string | "" | BIST OUCH uç noktası (`<OUCH_IP>`) |
| `userName`, `password` | string | "" | `<OUCH_USER>`, `<REDACTED>` |
| `accounts` | string (virgüllü) | "" | İzinli hesaplar |
| `market` | string | (Equity) | `"Derivative"` → Derivative, aksi halde Equity |
| `recvPinCore` | int | -1 | ≥0 ise global `sdkRecvPinCore`'u ezer |
| `recvSchedPolicy` | string | — | `FIFO` / `RR` / diğer → OTHER. ⚠ Eşleşen girişte bu alan boşsa politika OTHER'a düşer, global değer korunmaz. |
| `recvSchedPriority` | int | 0 | Eşleşen girişte koşulsuz ezer |

`[[viop_ouch_users]]` aynı şemayla parse edilir, ama `getViopOuchConfigurations()`'ı çağıran yok. **Etkisiz.** Hiçbir müşteri config'inde bu iki tablo yok.

## Bağlantılar

| Anahtar | Tip | Varsayılan | Anlam | Kullanan kod |
|---------|-----|-----------|-------|--------------|
| `dbIp`, `dbPort` | string | "" | **trade-data-app gRPC** (`AlgoService`), MySQL değil. Tipik port 6620. | `DatabaseServiceClient` |
| `dbUsername`, `dbPassword` | string | "" | trade-data-app login. `dbUsername` ayrıca strateji ayarlarının **`application_user` anahtarıdır** (`getStrategySettings` / `setStrategySettings`). Değiştirilirse DB'deki strateji ayarları başka kullanıcıya ait görünür. | `DatabaseServiceClient`, `BaseStrategyCommand::saveStrategySettings` |
| `ouchIp`, `ouchPort` | string | "" | **order-service MARpc** (ouch-sdk streaming), BIST değil. Tipik port 8000. | `OuchManager::startOuchStreaming` |
| `ouchUserName`, `ouchPassword` | string | "" | ouch-sdk login (`APP_HFT`). Başarısızsa `OuchManager` yapıcısı string fırlatır (`"Failed at ouch server login!"`). | `OuchManager::login` |
| `grpcPort` | int | **zorunlu** | StrategyService dinleme portu (`0.0.0.0:<port>`). Bkz. [komutlar-ve-grpc.md](komutlar-ve-grpc.md). | `GUIManager::startGrpcServer` |

## PerfSDK (monitoring)

`monitoringEnabled=false` ise `PerformanceClient::start` hiç çağrılmaz ve bütün histogramlar no-op olur. Ayrıntı: [performance-sdk](../performance-sdk/README.md).

| Anahtar | Tip | Varsayılan | Anlam |
|---------|-----|-----------|-------|
| `monitoringEnabled` | bool | false | PerfSDK'yı başlat. `ItchSdkClient` ayrıca "Performance monitoring enabled on port" basar, başka bir iş yapmaz. |
| `monitoringPort` | string | "" | `start(app, port, …)`'a geçer; SDK portu kullanmaz. Yorumlardaki "Prometheus" eskidir. |
| `perfDbHost` | string | "" | ClickHouse host (`<PERF_DB_HOST>`). **Boşsa exporter kurulmaz**, ölçüm bellekte kalır. |
| `perfDbPort` | uint16 | 8123 | ClickHouse HTTP |
| `perfDbName`, `perfDbUsername` | string | "default" (boşsa da) | |
| `perfDbPassword` | string | "" | `<REDACTED>` |
| `perfAppName` | string | "" → `gethostname()` | Metrik uygulama adı |
| `perfPrintValues` | bool | false | Her örneği konsola basar. Toml yorumu: hot-path'te I/O seli yaratır. |
| `perfMinTimeUs`, `perfMaxTimeUs` | int (µs) | 0 / 60000000 | Histogram aralığı. 60 s üst sınırı, "default 2 ms tail'leri clamp eder" sorununu önlemek için konmuş. |

## Lisans ve okunup kullanılmayanlar

- `licenseUsername`, `licensePassword`, `licenseCode`, `licenseUrl`: yalnız `LicenseManager`/`RestfulAuth` okur. `HftMain`'deki lisans kontrolü yorum satırında, yani **etkisiz**. Değerler gizli bilgidir (`<REDACTED>`).
- `uptickEnabled` (bool): yalnız konsol kutusunda "Uptick: ON/OFF" yazar. Gerçek kural `uptickRule`'dur.
- `uptickRule` (bool, false): **global** uptick. `ItchSdkClient::hasUptickRule` her orderbook için bunu döner. Kullanan HFT Classic ([itch-entegrasyonu §9](itch-entegrasyonu.md#9-uptick)).
- Okunmayan veya etkisiz olanların toplu listesi: `affinityActive`, `ouchWorkerCount`, `internalOuch*`, `minHotDwellUpdates`, `[[viop_ouch_users]]`, `license*`, `[[markets]]` içindeki `coreAffinity` ve `id` (aşağıda).

## `[[markets]]`

Her eleman bir pazardır. Yalnız `on` olan partition'lar SDK'ya gider.

| Alan | Tip | Anlam |
|------|-----|-------|
| `type` | string | `"Spot"` → Spot. **Başka her değer VİOP'tur** (örneklerde `"Future"`). |
| `on` | bool | Pazar varsayılanı. Partition'daki `on` bunu ezer. Eksikse false. |
| `defaults.itch` | tablo | `ip`, `port`, `secondaryIp`, `secondaryPort`, `broadcastLocalInterface`, `coreAffinity`. Partition'da olmayan alan buradan alınır. |
| `defaults.glimpse` | tablo | `ip`, `port`, `secondaryIp`, `secondaryPort`, `userName`, `password` (`<GLIMPSE_USER>`, `<REDACTED>`) |
| `defaults.rewinder` | tablo | `ip`, `port`, `secondaryIp`, `secondaryPort`, `localPort` |
| `partitions[].id` | int | Yalnız VİOP bağlantı adında (`future<id>`) ve legacy `getMulticastConfigurations`'ta kullanılır. **SDK partition numarası `id` değildir**: pazar içinde `on` olan partition'ların sırasıdır (1, 2, …). |
| `partitions[].on` | bool | Partition'ı aç/kapa |
| `partitions[].clientCore` | int | ITCH decode (client) thread core'u. **Eksikse 0 olur.** SDK yalnız `> 0` değerde pinler, yani 0 ve -1 "pin yok" demektir. |
| `partitions[].coreAffinity`, `itch.coreAffinity` | string | Parse edilir ama SDK'ya **geçmez**. Etkisiz. |
| `partitions[].itch/glimpse/rewinder` | tablo | `defaults` ile aynı alanlar; partition başına port ve `localPort` |

Notlar:
- Portlar ve IP'ler string tutulur (struct'lar `std::string`). TOML int verilirse de string'e çevrilir.
- SDK, receiver'ları (iface, port) çiftine göre gruplar. Aynı port numarasını kullanan Spot ve VİOP partition'ları tek RX thread'ini paylaşır ve `receiverCpuCores` bu receiver sırasına göre dağıtılır.
- Bağlantı adı bütün Spot partition'larında aynıdır: `"spot"`.
- VİOP için 6 partition tanımlı, ama SDK snapshot-end için pazar başına sabit Partition 1–4 bekliyor; 5–6. partition'lar snapshot tamamlanmasına dahil değil. `partId` yalnız log etiketi, çakışma üretmez ([itch-sdk/alim-yolu § 8](../itch-sdk/alim-yolu.md#8-partition-varsayımları-ve-partid-k-01--ertelendi), K-01).

## Config'te olmayan, sabit kodlu ITCH SDK ayarları

`ConfigurationManager.h`'taki üye başlangıç değerleridir. Hiçbir anahtardan okunmaz; yorum "populated from Configuration.ini" diyor ama yanlış.

| Ayar | Değer | Not (kod yorumu) |
|------|-------|------------------|
| `mainRingBufferSize` | 65536 slot | 1M'den düşürüldü: 4×1M×2112 B memset = 8.9 GB → açılışta host wedge (2026-06-15) |
| `rewinderRingBufferSize` | 16384 slot | 65536'dan düşürüldü |
| `busyPollUsec`, `socketRcvBufBytes` | 0, 0 | |
| `glimpseRetryCount`, `glimpseRetryBackoffMs` | 3, 500 ms | |
| `glimpseStartTimeoutMs` | 30000 ms | Aşılırsa ITCH start başarısız olur ve HFT `exit(1)` ile çıkar |
| `rewinderRequestTimeoutMs` | 5000 ms | |

## Env değişkenleri

| Env | Etki |
|-----|------|
| `HFT_REAL_HOT_READY_QUEUE` | **Tanımlıysa config'i her durumda ezer.** `1`, `Y`, `y`, `true`, `TRUE` → açık; başka her değer (ör. `0`, `yes`, boş string) → **kapalı**. Tanımlı değilse `realHotReadyQueue` okunur. |
| `HFT_RT_FIFO` | Tanımlıysa (değeri önemsiz) pinli AlgoWorker'lar SCHED_FIFO@80 alır. Kod yorumu (2026-07-03): host'ta `stalld` şarttır, yoksa kworker aç kalır ve host wedge olur. |
| `LD_PRELOAD` | Onload derlemesinde boşsa `libonload.so` set edilip `execvp` ile yeniden başlanır. Mellanox derlemesinde aynı şey `libvma.so` ile yapılır. |

## Prod'da kapalı tutulanlar (toml yorumlarından)

| Anahtar | Repo örneği | Gerekçe (yorum) |
|---------|-------------|-----------------|
| `mainCpuCores` | `[]` | "KAPALI 2026-06-15: pin host'u wedge'liyordu (ping+ssh öldü, iLO reset)" |
| `sdkLockMemory` | false | "leak çözülene kadar KAPALI (mlockall host-hang yapıyordu)" |
| `algoWorkerCores`, `internalOuchCores`, `receiverCpuCores`, `clientCore`, `sdkRecvPinCore=-1`, `sdkRecvSchedPolicy=OTHER`, `internalOuchSchedFifo=false` | boş / -1 / OTHER | "SAFE .28": Docker kontrolü ve VS Code'dan başlatma sırasında RT FIFO ve pin yok. ❓ doğrulanmadı: ".28" bir test host'u mu? Müşteri config'lerinde bunlar açık (aşağıda). |
| `monitoringEnabled` | **true** | Yorum "SAFE .28: disabled during control-plane stability profile" diyor ama değer true. Yorum ile değer çelişiyor. |
| `perfPrintValues` | false | Hot-path I/O seli |
| `logLevel` | info | `debug` = ITCH yükünde log seli |

Repo örneği bir müşteri config'i değildir. Prod değerleri aşağıdaki tablodadır.

## Müşteri config'leri — yapısal farklar

Kaynak: Algo-Setup `development` `2a3c5d5`, `Configs/<Müşteri>/HFT-Configuration.toml` (8 müşteri).

**Hepsinde ortak:**
- `uptickRule=false`, `uptickEnabled=false`, `monitoringEnabled=true`
- `sdkLockMemory=true`
- `triggerWorkerCount=5`, `dbPort=6620`, `ouchPort=8000`, `path=/workingDirectory/HftSrvProd`
- `perfPrintValues=false`, `sdkReplayQuietWindowMs=10000`, `sdkOrderHardCapTry=50000000`
- Spot 4 partition açık, `Future` 6 partition tanımlı ama **pazar `on=false`**
- `[[ouch_users]]` yok
- Tiering anahtarları (`activationPct…` vb.) ve `strategyQueueMaxEvents` hiçbirinde yok, yani varsayılanlar geçerli.
- `onloadStackName=hft-stack`

**Grup A** (A1, Alnus, Alnus-Algo, Global, Marbas, Piramit_Algo) gizli alanlar hariç birebir aynıdır.

| Müşteri | `workerCount` / `algoWorkerCores` | `hotWorkerCount` / `realHotReadyQueue` | `mainCpuCores` | `receiverCpuCores` | `clientCore` | `combinerEnabled` | `sdkUseOnload` | `sdkRecvPinCore` / policy | `internalOuch*` | `logLevel` | `grpcPort` | `itchOnloadStackName` |
|---------|-----------------------------------|----------------------------------------|----------------|--------------------|--------------|-------------------|----------------|---------------------------|-----------------|------------|------------|-----------------------|
| Grup A | 4 / [12,14,16,18] | — / — | — | [4,6,8,10] | yok (0 = pinsiz) | ✘ | ✔ | 20 / FIFO | [20,22], FIFO | debug | 9098 | hft-itch |
| Piramit | **2 / [28,29]** | **1 / true** | **[30–35]** | [20,21,22,23] | **24–27** | **✔** | ✔ | 19 / OTHER | [54,55,56], OTHER; `ouchWorkerCount=1` | **info** | 9098 | **mahft-itch** |
| Seker | 4 / [5,7,9,11] | — / — | — | [4,6,8,10] | yok | ✘ | **✘** | 13 / FIFO | [3,12,14], FIFO | debug | **9036** | hft-itch |

Çıkarımlar (hepsi aday; dağıtım ortamının gerçek durumu doğrulanmadı):
- **Tiering ve hot-ready queue yalnız Piramit'te açık.** Diğer müşterilerde Tavan/Taban bütün abonelikleri sürekli açık çalışır.
- **Combiner yalnız Piramit'te açık.** Diğerlerinde fill her zaman OUCH'tan gelir.
- **`sdkLockMemory=true` bütün müşterilerde açık.** Repo örneği bunu "host-hang" gerekçesiyle kapalı tutuyor. ❓ Müşteri host'larında mlockall sorunu görülmedi mi?
- **Piramit `mainCpuCores` dolu.** README'deki "2026-06'da kapalı tutuluyor" notu repo örneğine aittir; Piramit'te pin açık.
- **`logLevel=debug` 7 müşteride.** Toml yorumuna göre ITCH yükünde log seli yaratır. ITCH SDK da Debug seviyesine geçer.
- **`internalOuch*` ve `ouchWorkerCount` farkları etkisiz** (bkz. yukarı).
- **`grpcPort` ile trade-data-app `extServices` hft portu uyuşmuyor.** HFT tarafında A1, Alnus, Alnus-Algo, Global ve Marbas 9098 dinliyor. trade-data-app config'inde ise hft portu A1/Marbas için 9099, Alnus/Alnus-Algo/Global için 9036 ([trade-data-app/config.md](../trade-data-app/config.md#müşteri-configleri--yapısal-farklar)). Yalnız Piramit (9098) ve Seker (9036) eşleşiyor. ❓ doğrulanmadı: Docker port yönlendirmesi mi, yoksa yanlış config mi?
- **Grup A'da `clientCore` yok**, yani ITCH decode thread'leri pinsiz. RX thread'leri ise `receiverCpuCores` ile pinli.

## Şüpheli davranışlar / uyumsuzluklar (koddan)

- **Şifreler stdout'a basılıyor:** `loadConfiguration` her düz anahtarı `key: value` olarak yazar. `dbPassword`, `ouchPassword`, `perfDbPassword`, `licensePassword` konsola ve konteyner log'una düşer.
- **Repo örneği gerçek görünen kimlik bilgileri içeriyor:** lisans, PerfSDK ClickHouse host/şifre, Glimpse kullanıcıları ve iç IP'ler. Buraya alınmadı. ❓ Rotasyon kararı kullanıcıya ait.
- **Zorunlu anahtar eksikse çöküş:** `workerCount`, `triggerWorkerCount` (yalnız durum kutusunda kullanılmasına rağmen) ve `grpcPort` `std::stoi` ile okunur. Eksik olursa yakalanmayan `std::invalid_argument` fırlar.
- **`HFT_REAL_HOT_READY_QUEUE=0`:** Config'te `realHotReadyQueue=true` olsa bile kapatır (env her zaman kazanır). `yes`/`on` gibi değerler de kapalı sayılır.
- **`hotWorkerCount` adı yanıltıcı:** Sayı olarak kullanılmıyor, yalnız tiering ve hot öncelik için bir bayrak.
- **`[[markets]].partitions[].id` SDK partition'ı değil:** Bir partition `on=false` yapılırsa sonraki partition'lar SDK'da bir aşağı kayar. Örneğin Spot 2 kapatılırsa id=3 partition SDK'ya 2 olarak gider. ❓ doğrulanmadı: SDK'nın Glimpse/partition eşlemesinde bunun etkisi.
- **`type` doğrulaması yok:** `"Spot"` dışındaki her değer (yazım hatası dahil) VİOP olur.
- **`coreAffinity` etkisiz:** Repo ve müşteri config'lerinde `coreAffinity` değerleri var, ama hiçbiri SDK'ya ulaşmıyor.
- **`recvSchedPolicy` override'ı:** `[[ouch_users]]` girişinde politika boş bırakılırsa global `sdkRecvSchedPolicy` korunmaz, OTHER'a düşer. `recvSchedPriority` da koşulsuz ezer.
- **`monitoringEnabled` yorumu yanlış:** Repo örneğindeki "disabled" yorumu `true` değerle çelişiyor.
- **README ile fark:** README'deki "`strategyQueueMaxEvents` … aşılırsa eski olaylar düşürülür" ifadesi koda uymuyor; düşen yeni olaydır ([itch-entegrasyonu](itch-entegrasyonu.md#şüpheli-davranışlar--uyumsuzluklar-koddan)). README'deki "`mainCpuCores` kapalı tutuluyor" ifadesi Piramit için geçerli değil.
