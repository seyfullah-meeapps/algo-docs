---
kapsam: Servisler arası config indeksi — hangi servisin config'i nerede (repo şablonu, Algo-Setup müşteri dosyası, container yolu, override), paketleme ve gece güncellemesi, servisler arasında uyuşması gereken değerler (port, host, kullanıcı/token, ITCH) ve uyuşmazlıkta görülen log
kaynak:
  - repo: Algo-Setup                 # Configs/, servis klasörleri, install.sh, setup_copy_binary.sh, algosetup.yml
    branch: development
    commit: 2a3c5d5
  - repo: Algo-Setup                 # prod farkları
    branch: main
    commit: 2907757
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: mtrader-trade-ui           # algo_gui.yaml, Dockerfile, default.conf
    branch: development
    commit: b0474c3
  - repo: mtrader-frontend-apps      # adminui.yml
    branch: main
    commit: db10c12
  - repo: algo-configs               # License-Setup/, container-images/MAProdEnvironment
    branch: master
    commit: ab35dde
  - repo: itch-sdk                   # rewinder bind
    branch: development
    commit: 35a3b5c
dogrulama: 2026-10-22
durum: taslak
---

# Config referansı — servisler arası indeks

Bu dosya **anahtar açıklaması içermez.** Anahtarların anlamı servis dokümanlarındadır:
- [hftsrvprod/config.md](../10-servisler/hftsrvprod/config.md)
- [order-service/kalicilik-ve-config.md § B1–B3](../10-servisler/order-service/kalicilik-ve-config.md#b1-config-referansı-configyaml)
- [trade-data-app/config.md](../10-servisler/trade-data-app/config.md)
- [algorithmic-trading/config.md](../10-servisler/algorithmic-trading/config.md)
- [mtrader-trade-ui/backend-sozlesmesi.md § 1](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md)

Burada yalnız şunlar var: dosyaların yeri, paketleme, ve servisler arasında **aynı olması gereken** değerler. Müşteri durumları Algo-Setup `development` `2a3c5d5`'e göredir; prod farkları `⚠ main'de farklı` ile işaretlidir. IP, kullanıcı ve şifre değerleri yazılmaz. "uzak IP" loopback olmayan bir adres demektir.

## 1. Config dosyaları

Container yolları development compose/Dockerfile'larındandır.

| Servis | Dosya / format | Repo şablonu | Algo-Setup kaynağı → paket içi yeri (CI) | Container içi yol | Okuma / override | Ayrıntı |
|--------|----------------|--------------|-------------------------------------------|-------------------|------------------|---------|
| HftSrvProd | `Configuration.toml` (TOML) | `src/Configuration/Configuration.toml` | `Configs/<M>/HFT-Configuration.toml` → `HFT/HftSrvProd/Configuration.toml` | `/workingDirectory/HftSrvProd/Configuration.toml` (`HFT/scripts/run.sh`) | `argv[1]`; env `HFT_REAL_HOT_READY_QUEUE`, `HFT_RT_FIFO`, `LD_PRELOAD` | [config.md](../10-servisler/hftsrvprod/config.md) |
| order-service | `config.yaml` (YAML) | `config.yaml` | `Configs/<M>/order-service-config.yaml` → `OrderService/order-service/config.yaml` | `/workingDirectory/order-service/config.yaml` | `argv[1]`; env yalnız `LD_PRELOAD` | [B1–B3](../10-servisler/order-service/kalicilik-ve-config.md#b1-config-referansı-configyaml) |
| trade-data-app (MADatabaseService) | `config.json` (JSON) | `config.json` | `Configs/<M>/dbservice-config.json` → `MADatabaseService/config.json` | `/workingDirectory/config.json` (Dockerfile `ADD`) | `-config=…`, `-log-path=/workingDirectory/log`; env `REQUESTLOG_*`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` | [config.md](../10-servisler/trade-data-app/config.md) |
| AlgoProd | `Configuration.ini` (özel sözdizimi) | `algoSrc/Configuration/Configuration.ini` | `Configs/<M>/Algo-Configuration.ini` → `MAAlgoProd/AlgorithmicTrading/Configuration.ini`, yanına `holidays.csv` | `/workingDirectory/AlgorithmicTrading/Configuration.ini` | `argv[1]`; env yalnız `LD_PRELOAD` | [config.md](../10-servisler/algorithmic-trading/config.md) |
| nginx-proxy (GUI + admin reverse proxy) | `nginx.conf`, `conf.d/{algo,admin,ssl,security-headers}.conf`, `conf.d/upstream.inc`, `ssl/{dev,production}/` | yok (yalnız Algo-Setup) | `Configs/<M>/nginx/` → paket `nginx/` | Compose `${HOME}/nginx/…` dizinlerini `/etc/nginx/…`'e salt okunur bağlar | — | § 3.1 |
| GUI (mtrader-trade-ui) | Build-time `VITE_API_HOST`, `VITE_WS_HOST` (prod'da boş); imaj içi nginx `default.conf` | `.env.example`, `default.conf` | yok; GUI kendi CI'ı ile dağıtılır (`algo_gui.yaml`) | nginx kökü `/usr/share/nginx/html`; host portu matristen | Build-time env | [backend-sozlesmesi § 1](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md) |
| Admin paneli (mtrader-frontend-apps) | — (build çıktısı) | — | yok; kendi CI'ı (`adminui.yml`) | host portu 4923/4924 | — | [README](../10-servisler/mtrader-frontend-apps/README.md) |
| MAAdminUI (Algo-Setup içi eski admin) | `MAAdminUI/nginx.conf` + statik `build/` | — | `MAAdminUI/` (müşteri farkı yok) | `/etc/nginx/conf.d/default.conf` | Compose `ports: 81:80`, container `MAAdminUITest` | — |
| MySQL | `docker-compose.yml` (`mysql:5.7`) | — | `Configs/<M>/mysql-docker-compose.yml` → `mysql/docker-compose.yml`; `Configs/<M>/db_scripts/` → `mysql/db_scripts/` → `$HOME/db_scripts/` | init: `${HOME}/workingDirectory/mysql/setup.sql` → `/docker-entrypoint-initdb.d/setup.sql` | env `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | [sema.md](../10-servisler/trade-data-app/sema.md) |
| Lisans | İstemcide: HFT `license*`, order-service `license.*` | — | servis config'lerinin içinde | — | Kontrol iki serviste de yorum satırında, yani etkisiz. AlgoProd ve trade-data-app'te lisans anahtarı yok. | aşağıda |

Notlar:
- **trade-data-app imajı** config'in yanına `ext/` dosyalarını (`IndicesDefinitions.csv`, `IndicesDetails.csv`, `InstrumentBazaars.xlsx`, `max_volumes.xlsx`) ve `meeapps.crt`/`meeapps.key`'i ekler. Compose'daki `logPath` env'ini kod okumaz. `AWS_REGION` compose'da yoktur, SES bölgesi boş kalır ([trade-data-app/config.md](../10-servisler/trade-data-app/config.md#requestlog-ve-env-overrideları)).
- **trade-data-app log volume'u:** Yalnız Onload compose'unda `container-logs/MADatabaseService/` bağlıdır. Düz compose'da log container içinde kalır.
- **nginx-proxy** `install.sh` veya `setup_*.sh` tarafından başlatılmaz. ❓ doğrulanmadı: kurulumun elle mi yapıldığı. GUI'nin `/v1/` ve `/ws/` isteklerinin trade-data-app'e nasıl ulaştığı sorusunun cevabı bu katmandır (§ 3.1).
- **Saat dilimi:** C++ servis imajlarının tabanı `meeapps/maprodenv` `TZ=Europe/Istanbul` set eder (algo-configs `container-images/MAProdEnvironment/Dockerfile`). trade-data-app Dockerfile'ı da aynı TZ'yi ayrıca set eder. order-service toplu emir saatleri yerel saattir. ❓ doğrulanmadı: yayınlanmış `maprodenv:3.0` / `4.0` etiketlerinin bu Dockerfile'dan üretildiği.
- **Lisans sunucusu:** algo-configs `License-Setup/` altındadır: `MALicenseApp` (`-config=/workingDirectory/config.json`; config repoda yok) ve kendi MySQL'i (`ConfigurationDB`). İstemci servisler bu sunucuya bugün bağlanmıyor.

## 2. Paketleme ve gece güncellemesi

**CI (`algosetup.yml`):**
- Müşteri dosyaları yukarıdaki tablodaki yerlere kopyalanır.
- Ağ varyantına (`*_network`: `onload`/`mlx`/`regular`) göre Dockerfile, compose, `run*.sh` ve binary standart adlara taşınır.
- `libMAItchSDK_*.so` ve `libMAOrderSDK_*.so` da varyanta göre `libMAItchSDK.so` / `libMAOrderSDK.so` olur.
- `install.sh`'e `setup_mode`; `run.sh` ve `setup_copy_binary.sh`'e `COMPANY_NAME` / `MODE` satır olarak eklenir.
- Ayrıntı: [kurulum-ve-dagitim § CI](kurulum-ve-dagitim.md#ci-githubworkflowsalgosetupyml).

**Config ile ilgili tuzaklar:**
- **`Alnus_Algo_Setup`**: `directory: "Alnus"`, yani Alnus-Algo değil Alnus dosyaları paketlenir. `setup_mode: "order_algo_db"`; bu değer `install.sh`'te yok. Hiçbir `setup_*.sh` çalışmaz, yalnız gece crontab'ı kurulur.
  - ⚠ main'de farklı: `directory: "Alnus_Algo"` (klasör adı da `Configs/Alnus_Algo`). `install.sh`'te `algo_order_db` var ama `order_algo_db` yok, yani sonuç aynı.
- **AlgoProd config'i** her müşteri klasöründe var. development matrisinde AlgoProd'u gerçekten kuran paket yok (yukarıdaki nedenle).
- **Piramit `setup_mode`:** development'ta `hft_order` (DB yok), ⚠ main'de `hft_order_db`.

**Gece güncellemesi (`setup_copy_binary.sh`, crontab 22:00, hafta içi):**
- S3'ten `<Müşteri>_Setup_development.zip` indirir. Dosya adı script'te sabittir; **main'deki script de `_development` zip'ini indirir.** ❓ doğrulanmadı: prod host'larında bu cron'un etkin olup olmadığı ve S3 yolunun CI'ın yüklediği bucket ile aynı olup olmadığı.
- Sonra çalışan container'lara `docker cp` yapar:
  - `config.json` → MADatabaseService
  - `config.yaml` → MAOrderService
  - `HftSrvProd/` dizini (içindeki `Configuration.toml` dahil) → MAHft
- Sonuç: **container içinde elle yapılan config değişikliği gece ezilir.**
- `hft_order` dalında binary `MAOrderServiceTest`'e, config `MAOrderService`'e kopyalanır (tutarsız ad).
- `algo` dalı `MAAlgorithmicTrading` adlı container'ı hedefler; compose'daki ad `MAAlgoProd`.
- development compose'larındaki container adları `MAHftTest`, `MAOrderServiceTest`, `MADatabaseServiceTest`'tir. Crontab ve bu script ise `MAHft`, `MAOrderService`, `MADatabaseService` adlarını kullanır.

**⚠ main'de farklı — HFT config adı:** main `HFT/scripts/run.sh` binary'yi `Configuration.ini` ile başlatır. CI ise `Configuration.toml` üretir ve master HftSrvProd yalnız TOML okur. ❓ doğrulanmadı: prod host'larında `run.sh`'in elle düzeltilip düzeltilmediği. Düzeltilmemişse HFT açılışta config parse hatasıyla çıkar ([hftsrvprod/config.md → Nasıl okunur](../10-servisler/hftsrvprod/config.md#nasıl-okunur)).

**⚠ main'de farklı — MySQL init:** development `install.sh` `setup.sql`'i `$HOME/workingDirectory/mysql/`'e kopyalamaz. Compose'daki bind mount kaynağı bu yüzden yoktur; Docker o yolda boş bir dizin yaratır ve init script çalışmaz. main `install.sh` kopyalar.

## 3. Uyuşması gereken değerler

### 3.1 Port matrisi

| Değer | Sunucu (dosya: anahtar) | İstemci (dosya: anahtar) | Tipik | Müşteri durumu | Uyuşmazsa |
|-------|-------------------------|--------------------------|-------|----------------|-----------|
| trade-data-app gRPC | TDA `server.port` | HFT `dbPort`; AlgoProd `dbPort`; order-service `database.port` | 6620 | HFT ve order-service hepsinde ✓. AlgoProd Alnus/Marbas uzak IP:**4540**, Global uzak IP:**5018**. ⚠ main'de farklı: Kanjo TDA **7720**, HFT/order-service 7720 ✓, AlgoProd 5018 (Global kopyası). | order-service: login boş token, `Fetch*` `UNAUTHENTICATED` `LOG_CRIT`, process ayakta ([A1](../10-servisler/order-service/kalicilik-ve-config.md#a1-dataservice-istemcisi-datadatabaseclient)). AlgoProd: `Credentials are invalid. Error code: …`, ardından `Failed to Connect Database Service!` ile çöküş. HFT: `DatabaseServiceClient::Connect - Login successful` görülmez. |
| TDA REST | TDA `server.restPort` | nginx `upstream.inc` `algo_backend` | 6621 | ✓ (Kanjo main 7721 ✓) | GUI login ve REST çağrıları nginx'te 502 |
| TDA WebSocket | TDA `gui.port` | nginx `algo_websocket` | 6623 | ✓ (Kanjo main 7723 ✓) | GUI canlı feed'ler açılmaz |
| TDA Admin REST | TDA `server.adminApiPort` | nginx `admin_backend` | 6688 | ✓ (Kanjo main 7788 ✓) | Admin paneli 502 |
| order-service MARpc | OS `server.port` | HFT `ouchPort`; AlgoProd `ouchPort` | 8000 | ✓ hepsi | HFT: `"Failed at ouch server login!"` fırlatılır. AlgoProd: aynı mesaj loglanır, açılış sürer. |
| order-service gRPC | OS `server.grpcPort` | TDA `extServices[orderserv].port` | 9035 | ✓ hepsi | TDA toplu emirleri gönderemez |
| HFT gRPC | HFT `grpcPort` | TDA `extServices[hft].port` | 9050 (repo) | **Uyuşmuyor:** A1, Marbas (9098 ↔ 9099); Alnus, Alnus-Algo, Global (9098 ↔ 9036). Piramit 9098 ✓, Seker 9036 ✓. ⚠ main'de farklı: **Piramit da uyuşmuyor** (9098 ↔ 9036); Kanjo 9036 ✓. | TDA yalnız `[HFT Service] Connecting to HFT Service` basar. Bağlanamayınca 2 sn'de bir **sessizce** yeniden dener (hata log'u yorum satırında, `pkg/gui/connections/hft.go` `Connect`). `Login to HFT service Successful` hiç görülmez. ❓ doğrulanmadı: Docker port yönlendirmesi olup olmadığı ([hftsrvprod/config.md](../10-servisler/hftsrvprod/config.md#müşteri-configleri--yapısal-farklar)). |
| AlgoProd gRPC | AlgoProd `clientPort` | TDA `extServices[algotrading].port` | 9098 | ✓ (yalnız A1 ve Piramit_Algo'da tanımlı) | `[AlgoTrading Service] Login to AlgoTrading Successful` görülmez |
| HFT ↔ AlgoProd aynı host | HFT `grpcPort` | AlgoProd `clientPort` | farklı olmalı | Seker dışında hepsinde **ikisi de 9098** (repo şablonları 9050/9098) | İkinci açılan bind edemez. ❓ doğrulanmadı: gRPC hata metni. AlgoProd'da `server` null kalıp health service çağrısında çökme beklenir. Ayrıca TDA'nın `hft` girişi yanlış motora bağlanabilir: sözleşme aynı olduğu için `StrategyLogin` başarılı olur. |
| GUI container | GUI `docker run -p <port>:80` (`algo_gui.yaml` matrisi) | nginx `algo_frontend` | 4921 (Piramit_Dev 6625, Alnus_Yeni 4931) | ✓ | GUI 502 |
| Admin paneli container | `adminui.yml` `port` | nginx `admin_frontend` | 4923 | ✓ | Admin 502 |
| nginx dinleme | nginx `listen` | tarayıcı / DNS | 80, 443; IP tabanlı admin 8080 (Alnus, Alnus-Algo 4542) | ⚠ main'de farklı: Kanjo algo **81/445**, admin 4542 | Kanjo'da nginx 81 ile MAAdminUI `81:80` aynı host'ta çakışır. ❓ doğrulanmadı: main'de MAAdminUI hâlâ başlatılıyor mu (main `setup_db.sh` başlatmıyor). |
| MySQL | compose `3306:3306` | TDA `database.port` | 3306 | ✓ | TDA'da `sql.Open` hatası loglanmaz, `Db` nil kalır ([config.md](../10-servisler/trade-data-app/config.md#database)) |
| Rewinder yerel UDP portu (host genelinde benzersiz) | TDA `itchConfigurations[].rewinderLocalPort`; HFT `partitions[].rewinder.localPort`; AlgoProd `$Itch` `rewinderLocalPort` | — | TDA 25001–25010, HFT 26001–26010, AlgoProd 26001–26010 | **HFT ile AlgoProd aynı aralıkta** (Global'de AlgoProd tanımsız → 28001…). Bugün iki motoru aynı host'a kuran paket yok. | itch-sdk `ItchClient.cpp`: `Failed to bind rewinder socket to local port … for partition …: Address already in use`. Soket `SO_REUSEADDR` olmadan bağlanır. |
| PerfSDK "monitoring" portları | HFT `monitoringPort`, OS `monitoring.port` (9091), AlgoProd `monitoringPort` (9092), TDA `monitoring.port` | — | — | — | PerfSDK port açmaz; çakışma etkisiz. TDA'nınki ITCH SDK'ya gider ve müşterilerde kapalı. |

nginx yönlendirmesi (bütün müşterilerde aynı desen; `conf.d/algo.conf`, `admin.conf`):
- `/v1/` → `algo_backend` (TDA REST). `/v1/login` için ayrı hız sınırı vardır (`login_limit`, 5 istek/dk).
- `/ws/` → `algo_websocket` (TDA WS; okuma zaman aşımı 86400 sn).
- `/hb` → `algo_backend`. A1'de yok.
- `/` → GUI container'ı.
- Admin tarafında aynı desen `admin_backend` / `admin_frontend` ile.
- Domain üzerinden gelen HTTP isteği HTTPS'e 301 ile yönlendirilir; 443'te HSTS başlığı eklenir. IP tabanlı `server` blokları düz HTTP sunar.
- Backend upstream'leri her müşteride `127.0.0.1`'dir, yani **nginx ile trade-data-app aynı host'ta olmalıdır.** Frontend upstream'leri A1'de başka bir host'a gider.

### 3.2 Host adresleri

- **HFT** `dbIp` / `ouchIp` ve **order-service** `database.host` bütün müşterilerde loopback. order-service `server.address` `0.0.0.0`; MARpc bu anahtarı kullanmaz, her arayüze bağlanır.
- ⚠ main'de farklı: A1, Global ve Marbas HFT config'lerinde `dbIp` aynı uzak IP değeri. Bu değer A1 trade-data-app'inin `database.host`'u ile de aynı. ❓ doğrulanmadı: kopyalama mı, ortak altyapı mı.
- **AlgoProd:** A1'de `ouchIp` uzak IP. Alnus/Marbas (aynı adres) ve Global'de `dbIp` uzak IP ve 6620 dışı port ([algorithmic-trading/config.md](../10-servisler/algorithmic-trading/config.md#müşteri-configleri--yapısal-farklar)).
- **trade-data-app** `extServices[].ip`: loopback. İstisna A1 `algotrading`; A1'de AlgoProd başka bir host'ta.
- **trade-data-app** `database.host`: loopback. İstisnalar A1, Piramit ve Piramit_Algo: uzak IP.
  - Piramit DB adı `MATraderTest`, Piramit_Algo `AlgoTest`. İkisinde de DB şifresi MySQL compose'undaki root şifresiyle aynı. ❓ doğrulanmadı: prod config'inde test DB'si kullanılıp kullanılmadığı (Piramit development'ta `hft_order`, yani DB bu host'ta değil).
  - ⚠ main'de farklı: Piramit `dbservice-config.json` loopback DB kullanır; `server.hostname` ve DB kullanıcısı Global'inkiyle aynıdır.
- **trade-data-app** `server.hostname`: REST gateway'in kendi gRPC'sine bağlandığı adres. Bazılarında `0.0.0.0`, bazılarında host IP'si; ikisi de aynı host'u gösterdiği sürece çalışır ([config.md](../10-servisler/trade-data-app/config.md#server)).

### 3.3 Kullanıcı ve token akışı

Uygulama hesaplarının hepsi trade-data-app `Application_Users` tablosundadır ([sema.md](../10-servisler/trade-data-app/sema.md)). Token JWT'dir, 48 saat geçerlidir ve tazelenmez ([api.md § 2](../10-servisler/trade-data-app/api.md#2-kimlik-doğrulama)).

| Kim → kime | İstemci anahtarı | Sunucuda ne olur |
|------------|------------------|------------------|
| order-service → TDA `DataService.Login` | OS `database.username` / `.password` | `Application=OUCH` |
| HFT → TDA `AlgoLogin` | HFT `dbUsername` / `dbPassword` | — |
| AlgoProd → TDA `AlgoLogin` | AlgoProd `dbUsername` / `dbPassword` | `Application=AlgoTrading` |
| HFT → order-service (MARpc login) | HFT `ouchUserName` / `ouchPassword` | order-service bilgiyi `DataService.Login`'e iletir |
| AlgoProd → order-service (MARpc login) | AlgoProd `ouchUsername` / `ouchPassword` (küçük `n`) | aynı |
| TDA → order-service gRPC `Login` | TDA `extServices[orderserv].username` / `.password` | aynı |
| TDA → HFT `StrategyLogin` | TDA `extServices[hft].username` / `.password` | HFT `AlgoLogin(app=HFT)` ile doğrular ([komutlar-ve-grpc](../10-servisler/hftsrvprod/komutlar-ve-grpc.md)) |
| TDA → AlgoProd `StrategyLogin` | TDA `extServices[algotrading].username` / `.password` | AlgoProd `AlgoLogin(app=AlgoTrading)` ile doğrular |
| TDA → MySQL | TDA `database.user` / `.pass` / `.name` | MySQL hesabı |

**Eşit olması gerekenler:**
- `extServices[hft].applicationUser` = HFT `dbUsername`. Strateji ayarları ve emir sahipliği bu adla tutulur. Durum: ✓ hepsi.
- `extServices[algotrading].applicationUser` = AlgoProd `dbUsername`. trade-data-app servis tanımlı değilse sabit `"algoUser"`a düşer (`gui_api.go`). Durum: ✓ (A1, Piramit_Algo).
- `extServices[].username` üç serviste ve bütün müşterilerde aynı hesap.
- HFT'de `dbUsername` = `ouchUserName`; AlgoProd'da `dbUsername` = `ouchUsername`. Hepsinde aynı.
- order-service `database.username`, `extServices[orderserv].applicationUser` (`orderUser`) ile **hiçbir müşteride aynı değil**. ❓ doğrulanmadı: aynı olması gerekip gerekmediği.

**TDA ↔ MySQL eşleşmesi** (`database.*` ↔ compose `MYSQL_*`):

| Müşteri | Kullanıcı | Şifre | DB adı |
|---------|-----------|-------|--------|
| A1, Marbas, Seker | ✓ | ✓ | ✓ (Seker `MTraderProd`, diğerleri `MATraderProd`) |
| Alnus, Alnus-Algo, Global | ✘ | ✘ | ✓ |
| Piramit, Piramit_Algo | ✘ | ✘ | ✘ (uzak DB, § 3.2) |

Algo-Setup'ta `CREATE USER` / `GRANT` yoktur (`mysql/setup.sql`, `db_scripts/`). Compose yalnız `MYSQL_USER`'ı yaratır. ❓ doğrulanmadı: Alnus, Alnus-Algo ve Global'de TDA kullanıcısının elle mi yaratıldığı. Yaratılmamışsa TDA DB'ye bağlanamaz.

**Token ve şifre logları:** order-service başarılı her login'in token'ını basar ([B Şüpheli](../10-servisler/order-service/kalicilik-ve-config.md#şüpheli)). HFT ve AlgoProd `StrategyLogin`'de token'ı stdout'a basar. HFT açılışta bütün düz anahtarları, şifreler dahil, basar. trade-data-app `Login`'de kullanıcı adı ve şifreyi loglar ([api.md](../10-servisler/trade-data-app/api.md)).

### 3.4 ITCH beslemesi

Üç süreç (HFT, AlgoProd, trade-data-app) aynı multicast beslemesini ayrı ayrı alır. Multicast soketi `SO_REUSEPORT` ile açıldığı için grup/port paylaşımı sorun değildir. Benzersiz olması gereken yalnız Rewinder yerel portudur (§ 3.1).

| Kavram | HftSrvProd | trade-data-app | AlgoProd |
|--------|-----------|----------------|----------|
| Pazar adı | `[[markets]].type`: `Spot`; **başka her değer VİOP** | `market`: `spot`, `derivative(s)`; bilinmeyen → VİOP (uyarılı) | `$Equity`, `$Derivative`; başka ad → `ParseException` |
| SDK partition'ı | `on` partition'ların sırası (`id` değil) | `part`; yalnız 1–4, diğeri → Partition1 | `$Partition :On` sırası |
| NIC | `broadcastLocalInterface` (defaults/partition) | eleman başına `localInterface` | pazar başına `localInterface` |
| Kaynak IP (SSM) | `spotSrcIp`, `viopSrcIp` (+ secondary) | eleman başına `srcIp` | pazar başına `srcIp` |
| Glimpse kimliği | `defaults.glimpse.userName/password` | `glimpseUsername/Password` | `$Glimpse userName/password` |
| Onload stack | `itchOnloadStackName` (`hft-itch`; Piramit `mahft-itch`) | `onloadStackName` (`trade-data-stack`; A1'de yok) | `itchOnloadStackName` (tanımsız → `algo-itch`) |

Müşteri durumu:
- **Spot kaynak IP'si:** Üç serviste de hepsinde aynı ✓.
- **VİOP açık mı:**
  - HFT: `Future` pazarı hepsinde kapalı.
  - TDA: VİOP yalnız A1, Alnus-Algo, Piramit_Algo'da açık.
  - AlgoProd: `$Derivative` hepsinde açık (6 partition; Global 4).
  - VİOP 5–6. partition'lar SDK snapshot-end'ine dahil değil: [itch-sdk/alim-yolu § 8](../10-servisler/itch-sdk/alim-yolu.md#8-partition-varsayımları-ve-partid-k-01--ertelendi).
- **NIC:** Aynı host'taki süreçlerin NIC'leri farklı olabilir; çok kartlı host'ta bu meşrudur. development'ta HFT config'i A1, Alnus, Alnus-Algo, Global ve Marbas'ta aynı NIC'i (`…f0.500`) gösterir; bu NIC Piramit trade-data-app'inin NIC'iyle aynıdır, o müşterilerin TDA ve AlgoProd NIC'leri farklıdır. ⚠ main'de farklı: HFT NIC'leri müşteriye göre ayrışmış. ❓ doğrulanmadı: development HFT config'leri bu müşterilerde gerçekten kullanılıyor mu.
- **Glimpse kullanıcısı:**
  - Piramit (development): üç süreç de aynı Glimpse kullanıcısını kullanır.
  - A1, Alnus, Global, Marbas: HFT'nin Glimpse kullanıcısı Piramit'inkiyle aynı, TDA'nınki farklı.
  - ❓ doğrulanmadı: BIST'in aynı Glimpse kullanıcısıyla eşzamanlı oturuma izin verip vermediği.
- **Onload userspace sürümü** host sürücüsüyle aynı olmalıdır. Host `install_onload.sh` 9.2.0.43 kurar. HFT, order-service ve TDA imajları da 9.2.0.43. **AlgoProd imajı 9.0.1.86** ([algorithmic-trading/config.md → Deploy](../10-servisler/algorithmic-trading/config.md#deploy-algo-setup-maalgoprod)).

## Şüpheli

- **HFT gRPC portu trade-data-app ile uyuşmuyor:** development'ta 5 müşteride, main'de Piramit dahil (§ 3.1). TDA bu durumda hata basmadan sonsuza kadar yeniden dener; GUI'den HFT stratejileri yönetilemez.
- **HFT ve AlgoProd aynı portları kullanıyor:** gRPC 9098 ve Rewinder 26001–26010. İki motor aynı host'a kurulursa biri açılamaz.
- **`order_algo_db` setup_mode'u install.sh'te yok** (iki branch'te de): Alnus Algo paketi hiçbir servis kurmuyor.
- **main HFT `run.sh` `Configuration.ini` ile başlatıyor**, oysa paket `Configuration.toml` içeriyor (§ 2).
- **Gece script'i main'de de `_development` zip'ini indiriyor** ve container içi config'leri eziyor (§ 2).
- **TDA ↔ MySQL kullanıcısı** Alnus, Alnus-Algo ve Global'de uyuşmuyor; kullanıcıyı yaratan script yok (§ 3.3).
- **Prod config'lerinde test DB adları:** Piramit `MATraderTest`, Piramit_Algo `AlgoTest` (development).
- **Kopyalama izleri:**
  - AlgoProd Alnus ve Marbas aynı uzak `dbIp:4540`.
  - Kanjo AlgoProd config'i Global'in kopyası (main).
  - main Global/Marbas HFT `dbIp`'si A1'in DB adresi.
  - main Piramit TDA config'inde Global'in hostname'i ve DB kullanıcısı.
- **Kanjo (main) port çakışma adayları:** nginx 81 ↔ MAAdminUI 81. order-service 8000/9035 varsayılan kalmış; aynı host'ta başka bir order-service varsa çakışır. ❓ doğrulanmadı: Kanjo'nun başka bir müşteriyle aynı host'ta olduğu (77xx TDA portları ve 81/445 nginx portları bunu düşündürüyor).
- **MySQL** `3306:3306` ile bütün arayüzlere yayınlanıyor (`network_mode: host` değil). Veri için adlandırılmış volume yok, yalnız imajın anonim volume'u var. ❓ doğrulanmadı: container yeniden yaratılınca verinin korunması.
- **Diğer dokümanlarla fark:**
  - mtrader-trade-ui `AGENTS.md` "HSTS eklenmez" diyor; GUI'nin önündeki nginx-proxy 443'te HSTS ekliyor (§ 3.1).

**Açık metin gizli bilgi** (değerler buraya alınmadı; ❓ rotasyon kararı kullanıcıya ait):
- Algo-Setup `MADatabaseService/docker-compose*.yml`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `aws/credentials`
- `install.sh`: `docker login --password`
- `Configs/<M>/mysql-docker-compose.yml`: `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`
- `Configs/<M>/db_scripts/*.sh`: `MYSQL_PASSWORD`, `-p` argümanı
- `Configs/<M>/nginx/ssl/*/private.key`; `MADatabaseService/ext/meeapps.key`
- Bütün müşteri config'lerindeki şifre anahtarları
- algo-configs `License-Setup/mysql/docker-compose.yml`, `License-Setup/Monitoring/.env` (`ADMIN_PASSWORD`)
- AlgorithmicTrading `Main.cpp` Sentry DSN
