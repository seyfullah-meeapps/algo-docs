---
kapsam: Algo-Setup kurulum paketi — CI ve müşteri matrisi, zip içeriği, install.sh ve setup_mode'lar, crontab, run scriptleri, docker-compose varyantları, container adları, volume yolları, tuning, MAProdEnv, binary güncelleme
kaynak:
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
  - repo: Algo-Setup
    branch: main
    commit: 2907757
  - repo: Algo-Setup
    branch: preprod
    commit: 346306a
  - repo: algo-configs
    branch: master
    commit: ab35dde
dogrulama: 2026-10-22
durum: taslak
---

# Kurulum ve dağıtım (Algo-Setup)

Referans `development`. Algo-Setup'ta **branch = ortam** ve branch'ler birbirine merge edilmez; `main` (prod) ve `preprod` farkları `⚠ main'de farklı` / `⚠ preprod'da farklı` ile işaretli. Sunucu adresi, kullanıcı, şifre, bucket adı placeholder'dır.

Genel özet: [README](README.md). Servis config anahtarlarının anlamı burada yok: HFT → [hftsrvprod/config.md](../10-servisler/hftsrvprod/config.md), order-service → [order-service/kalicilik-ve-config.md](../10-servisler/order-service/kalicilik-ve-config.md), trade-data-app → [trade-data-app/config.md](../10-servisler/trade-data-app/config.md), AlgoProd → `config-referansi.md`.

## Repo düzeni

### 24 Ekim paket güncellemesi

Algo-Setup development `2a3c5d5 → cade7d0`, preprod `346306a → 959be34`; main `2907757` değişmedi. Altı dosya değişti: SDK header/struct, regular/Onload SDK .so ve regular/Onload order-service binary. Mlx bu deltada değişmedi. Header yeni EnterOrderOptions API'sini içerir; binary davranışının tamamı header'dan kanıtlanmaz.

Eşleşen kaynaklar da güncellendi: SDK development `a788782 → c2b5060`, order-service `b86c0cf → 26e9a02`; main/master aynı. [Davranış farkı](../10-servisler/order-service/toplu-emirler.md#24-ekim-güncel-davranış-farkı). Paket script/workflow'ları bu deltada değişmedi; K-179 kapanmadı. algo-configs master `ab35dde` zaten günceldi. Script/binary/container/deploy çalıştırılmadı; bütün config envanteri yeni SHA'ya karşı doğrulandı denmez. Frontmatter önceki ayrıntılı turun commit'ini gösterir.

| Yol | İçerik |
|-----|--------|
| `HFT/` | `HftSrvProd/` (binary'ler: `HftSrvProd`, `HftSrvProd_Onload`, `HftSrvProd_Mlx`), `Dockerfile`, `HFT_Onload_Dockerfile`, `HFT_Mlx_Dockerfile`, `docker-compose{,-onload,-mlx}.yml`, `scripts/run.sh`, `scripts/run_mlx.sh` |
| `OrderService/` | `order-service/PiramitOrderService{,_Onload,_Mlx}`, üç Dockerfile, üç compose, `scripts/run.sh`, `run_onload.sh`, `run_mlx.sh` |
| `MADatabaseService/` | trade-data-app binary'si (`MADatabaseService`, tek varyant), üç Dockerfile, üç compose, `ext/` (endeks CSV'leri, `InstrumentBazaars.xlsx`, `max_volumes.xlsx`, TLS sertifika/anahtar), `scripts/run{,_onload,_mlx}.sh` |
| `MAAlgoProd/` | `AlgorithmicTrading/AlgoProd{,_Onload,_Mlx}`, üç Dockerfile, üç compose, `scripts/run.sh`, `scripts/copy_strategy_logs.sh` |
| `MAAdminUI/` | Derlenmiş eski admin UI (`build/`), nginx imajı, compose |
| `MAProdEnv/` | Base imaj Dockerfile'ı, `lib/` + `include/` (SDK `.so`'ları), `onload/`, `mellanox/`, `scripts/holidays.csv` |
| `Configs/<Müşteri>/` | `HFT-Configuration.toml`, `order-service-config.yaml`, `dbservice-config.json`, `Algo-Configuration.ini`, `mysql-docker-compose.yml`, `db_scripts/`, `nginx/` (+ yalnız `Seker`'de `tunning/`) |
| `mysql/` | `setup.sql` (şema dump'ı) |
| `aws/` | Container içine `/root/.aws/` olarak giren AWS CLI ayarları |
| kök | `install.sh`, `install_centos.sh`, `install_onload.sh`, `install_onload_centos.sh`, `install_mlx.sh`, `setup_*.sh`, `uninstall*.sh`, `chrony.conf`, `package.json` (MAProdEnv imaj sürümü) |

`Configs/` klasörleri branch'e göre: development `A1, Alnus, Alnus-Algo, Global, Marbas, Piramit, Piramit_Algo, Seker`; ⚠ main'de farklı: `Seker` yok, `Kanjo` ve `Oyak` var, `Alnus-Algo` → `Alnus_Algo`; ⚠ preprod'da farklı: yalnız `A1, Alnus, Piramit, Piramit_Algo`.

## CI: `.github/workflows/algosetup.yml`

Tetik: `main`, `development`, `preprod` push. Servis repolarının CI'ı binary'yi bu branch'lere commit'lediği için ([branch-ve-ortamlar](../00-genel/branch-ve-ortamlar.md#c-servislerin-cicdsi)) **her binary commit'i tüm müşteri zip'lerini yeniden üretir**.

### Müşteri matrisi

Her satırda `hft_network`, `itch_network`, `algo_network`, `orderserv_network`, `dbserv_network` (`onload` / `mlx` / `regular`) ve `setup_mode` var.

| packname | `directory` (Configs) | Ağ (5 alan) | `setup_mode` | Branch |
|----------|------------------------|-------------|--------------|--------|
| `Piramit_Setup` | `Piramit` | onload | `hft_order` (⚠ main'de `hft_order_db`) | dev, preprod, main |
| `A1_Setup` | `A1` | onload | `hft_order` | dev, preprod, main |
| `Alnus_Setup` | `Alnus` | onload | `hft_order_db` | dev, preprod, main |
| `Alnus_Algo_Setup` | dev: `Alnus` (⚠ main'de `Alnus_Algo`) | regular | `order_algo_db` | dev, main |
| `Marbas_Setup` | `Marbas` | onload | `hft_order_db` | dev, main |
| `Global_Setup` | `Global` | onload | `hft_order_db` | dev, main |
| `Kanjo_Setup` | `Kanjo` | onload | `hft_order_db` | yalnız main |

- Hiçbir matriste `mlx` yok. `Piramit_Algo`, `Seker`, `Oyak`, development'taki `Alnus-Algo` klasörleri hiçbir matriste kullanılmıyor.
- development'ta `Alnus_Algo_Setup` `Configs/Alnus`'u kullanır ve zip'i `Alnus/` S3 klasörüne düşer.

### Adımlar

1. **Zip adı** (`file-path-generator`): main → `<packname>.zip`; preprod → `<packname>_preprod.zip`; diğer → `<packname>_development.zip`. `MODE` env: varsayılan `Production`, yalnız development'ta `Test`. Yani **preprod da `MODE=Production`** ile paketlenir.
2. **Config kopyalama** (`Configs/<directory>/` → paket):
   - `nginx/` → `nginx/`
   - `mysql-docker-compose.yml` → `mysql/docker-compose.yml`
   - `db_scripts/` → `mysql/db_scripts/`
   - `dbservice-config.json` → `MADatabaseService/config.json`
   - `order-service-config.yaml` → `OrderService/order-service/config.yaml`
   - `HFT-Configuration.toml` → `HFT/HftSrvProd/Configuration.toml`
   - `Algo-Configuration.ini` → `MAAlgoProd/AlgorithmicTrading/Configuration.ini`; ayrıca `MAProdEnv/scripts/holidays.csv` yanına
3. **SDK varyantı:** `itch_network`'e göre `libMAItchSDK_{Onload,Mlx}.so` → `libMAItchSDK.so` olarak yeniden adlandırılır (diğeri silinir). Aynısı `orderserv_network`'e göre `libMAOrderSDK`. ⚠ main'de farklı: main'de `libMAOrderSDK` seçim adımları yok; `_Onload`/`_Mlx` dosyaları pakette kalır.
4. **Servis varyantı:** her servis için seçilen ağın Dockerfile'ı → `Dockerfile`, compose'u → `docker-compose.yml`, run script'i → `run.sh`, binary'si → asıl isim olarak yeniden adlandırılır; diğer varyantlar silinir. `regular` seçilince yalnız onload/mlx dosyaları silinir.
5. **Script'lere değişken gömme** (`sed -i '2s/^/…/'`, 2. satıra ekleme): `install.sh` ve `install_centos.sh` ← `setup_mode`; `setup_copy_binary.sh` ← `companyName`, `setup_mode`; `HFT/scripts/run.sh`, `MAAlgoProd/scripts/run.sh`, `copy_strategy_logs.sh` ← `COMPANY_NAME` (= `directory`), `MODE`.
6. **Zip** (`vimtor/action-zip`, `recursive: false`), dosya listesi: `HFT/ MADatabaseService/ MAAlgoProd/ MAProdEnv/ mysql/ OrderService/ MAAdminUI/ aws/ Monitoring/ nginx/ setup_db.sh setup_hft.sh setup_prod_env.sh setup_order_service.sh setup_algo.sh install.sh install_centos.sh install_onload.sh uninstall.sh uninstall_onload.sh chrony.conf setup_copy_binary.sh`.
   - Pakette **olmayanlar:** `install_mlx.sh`, `install_onload_centos.sh`, `setup_tunning.sh`, `Configs/*/tunning/`; main'de ayrıca `setup_monitoring.sh`, `sysctl.conf`.
   - `Monitoring/` development ve preprod'da yok (yalnız main'de). ❓ doğrulanmadı: action eksik yolu sessizce atlıyor mu.
7. **Yükleme:** GitHub Artifacts (14 gün) + S3: `s3://<S3_SETUP_BUCKET>/<directory>/<zip>`.

### `maprodenv.yml`

Yalnız `main` push'unda `MAProdEnv/Dockerfile`'ı build edip `meeapps/maprodenv:<package.json version>` olarak Docker Hub'a iter. `package.json` sürümü development'ta `2.6`, ⚠ main'de `4.0`.

## Sunucuda kurulum

### 24 Ekim CI hedef ve varyant kontrolü

SDK `c2b5060` ordersdk.yaml ve order-service `26e9a02` orderservice.yml okundu. İkisinin aktif build matrix'i regular/onload'dır; Mlx koşullu adımları bulunması Mlx job'ı çalıştığı anlamına gelmez. Son Setup deltası da Mlx binary'lerini yenilemedi; eski Mlx dosyasının bulunması yeni API'yi içerdiği kanıtı değildir.

**K-243 — SDK preprod artifact hedefi main kalıyor:** SDK build job'ı preprod için BRANCH_NAME=preprod yapar. Ayrı `push_binaries` job'ı ise BRANCH_NAME=main ile başlar, yalnız development için override içerir; preprod override yoktur. Download edilen regular/onload artifact'ları bu job'ın checkout/destination_branch=main hedefindeki Algo-Setup/MAProdEnv'e kopyalama konfigürasyonuna gider. Job env'i diğer job'dan miras alınmış sayılmaz. Bu statik workflow hedefidir; action'ın başarılı çalışıp prod paketini değiştirdiği iddia edilmez. order-service push job'ı preprod override'ını içerir; iki CI aynı kabul edilmez.

K-182 config sınırı da sürüyor: development HFT run.sh Configuration.toml kullanır; main run.sh Configuration.ini, development run_mlx.sh da Configuration.ini kullanır. Paketleme HFT-Configuration.toml'ı Configuration.toml'a kopyalar. Çalışan sunucuda elle dosya/argüman düzeltmesi olup olmadığı bilinmiyor. Script/CI/deploy çalıştırılmadı.

Algo-Setup `README.md` adımları: zip indirilir, `unzip -d Setup/ <Paket>.zip`, `cd Setup/`, `chmod +x *.sh`, gerekirse `install.sh`'taki `setup_mode` düzenlenir, `./install.sh`.

### `install.sh` sırası

1. **chrony:** `chrony.conf` → `/etc/chrony/` (tek `server <BIST_NTP_IP>`, `minpoll 1 maxpoll 4`, `makestep 1 3`). ⚠ main'de ayrıca `timedatectl set-timezone`.
2. **Saat dilimi:** `/etc/localtime` → `Europe/Istanbul`.
3. **sysctl:** `sysctl -w net.core.rmem_default/rmem_max=134217728, wmem_default/wmem_max=16777216, vm.swappiness=10` — **kalıcı değil**, reboot'ta kaybolur. ⚠ main'de farklı: `sysctl.conf` → `/etc/sysctl.conf` (rmem 512 MiB, `netdev_max_backlog=30000`, `tcp_timestamps=0`, `vm.swappiness=1`, `vm.nr_hugepages=1024`, `vm.min_free_kbytes=8388608`, `kernel.core_pattern=/workingDirectory/cores/core.%e.%p`).
4. **Docker CE** (apt) + `docker login` (gömülü Docker Hub hesabı, `<REDACTED>`) + **docker-compose 1.29.2** (`/usr/local/bin`). `chmod 666 /var/run/docker.sock`.
5. `unzip make gcc libpcap-dev`; `setup_copy_binary.sh` → `$HOME/`; `mysql/db_scripts/` → `$HOME/db_scripts/`.
6. `mkdir $HOME/workingDirectory/sock` + `touch …/sock/mysocket`. ⚠ main'de ayrıca `mysql/setup.sql` → `$HOME/workingDirectory/mysql/`.
7. Binary'lere `chmod +x`.
8. **NIC algılama** (`lshw`): Solarflare veya Xilinx → `./install_onload.sh`; Mellanox → `./install_mlx.sh`; yoksa atlanır. `ACCEL_MODE` export edilir ama hiçbir `setup_*.sh` kullanmaz; compose seçimi CI'da yapılmıştır. ⚠ main/preprod'da `ACCEL_MODE` yok.
9. `setup_mode`'a göre `setup_*.sh` + crontab (aşağıda). Her modda sonuna `00 22 * * 1-5 $HOME/setup_copy_binary.sh` eklenir. ⚠ main'de ayrıca `./setup_monitoring.sh` ve çoğu modda `sudo ./install_logBackupCleanPush.sh <user>`.

`install_onload.sh`: OpenOnload 9.2.0.43 (md5 kontrolü; paket MeeApps web sunucusundan), host'a **kernel modülleriyle tam kurulum** (`onload_install`); `ONLOADZF_PACKAGE_URL` set ise TCPDirect. Container içindeki Onload yalnız userspace'tir (`onload_install --userfiles`); host sürümü container ile **eşleşmeli** (Dockerfile notu).
`install_mlx.sh`: Mellanox apt deposu (`latest-24.10/ubuntu24.04` sabit), `mlnx-ofed-xlio` + `libxlio*`, `vm.nr_hugepages=512`, memlock unlimited (`/etc/security/limits.d/99-xlio-memlock.conf`), `ib_uverbs mlx5_ib rdma_ucm` modülleri.

### `setup_<servis>.sh`

| Script | Yaptığı |
|--------|---------|
| `setup_db.sh` | `mysql/` → `docker-compose up -d --build`; `mysql/db_scripts/install_data.sh` (`datas.sql`'i `mysql_container`'a basar); `MADatabaseService/` ve `MAAdminUI/` → `up -d --build`. ⚠ main'de farklı: `install_data.sh` ve MAAdminUI adımları yok. |
| `setup_order_service.sh` | `OrderService/` → `up -d --build` |
| `setup_hft.sh` | `HFT/` → `up -d --build` |
| `setup_algo.sh` | `MAAlgoProd/` → `up -d --build` |
| `setup_prod_env.sh` | `MAProdEnv/` → `docker build -t meeapps/prod-env:1.0.0` (install akışında çağrılmaz) |
| `setup_tunning.sh` | Aşağıda "Tuning". ⚠ main/preprod'da dosya yok. |
| `setup_copy_binary.sh` | Gece binary güncellemesi; aşağıda "Güncelleme". |

`nginx/` pakete girer ama hiçbir script başlatmaz; compose (`container_name: nginx-proxy`, host network) `${HOME}/nginx/{nginx.conf,conf.d,ssl,logs}` bekler. ❓ doğrulanmadı: nginx elle mi kuruluyor.

### `setup_mode` → servisler ve crontab (development)

Tüm satırlar `* * 1-5` (hafta içi). Saatler sunucu yerel saati (Europe/Istanbul).

| `setup_mode` | Kurulan | Başlat | Durdur | Diğer |
|--------------|---------|--------|--------|-------|
| `hft_order` | order-service, HFT | 07:44 `MAOrderService`, 07:45 `MAHft` | 23:30 `MAHft`, 23:45 `MAOrderService` | — |
| `hft_order_db` | DB (mysql + trade-data-app + AdminUI), order-service, HFT | 07:43 `MADatabaseService`, 07:44 `MAOrderService`, 07:45 `MAHft` | 23:29 `MAHft`, 23:30 `MAOrderService`, 23:45 `MADatabaseService` | 22:30 `$HOME/db_scripts/backupAllDatabases.sh` |
| `order_db` | DB, order-service | 07:43 DB, 07:44 OS | 23:30 OS, 23:45 DB | 22:30 yedek |
| `db` | DB | 07:43 | 23:45 | 22:30 yedek |
| `hft` | HFT | 07:45 | 23:29 | — |
| `order` | order-service | 07:44 | 23:30 | — |
| `algo_order` | order-service, AlgoProd | **cron yok** | **cron yok** | — |
| `order_algo_db` (Alnus_Algo matrisi) | **hiçbiri** — `install.sh`'ta dalı yok | — | — | yalnız 22:00 satırı |

Her modda ek: `00 22 * * 1-5 $HOME/setup_copy_binary.sh`. `mysql_container` ve `MAAdminUITest` için cron yok (sürekli açık).

⚠ main'de farklı:
- Tüm `docker stop`'lar `docker stop --time 90` (development'ta varsayılan 10 sn).
- `algo_order`: 07:44 OS, **07:55 `MAAlgoProd`**; 23:30 OS, 23:40 AlgoProd.
- Yeni modlar: `algo` (yalnız AlgoProd, cron yok), `algo_order_db` (07:40 DB, 07:44 OS, 07:55 AlgoProd; 23:30 OS, 23:40 AlgoProd, 23:45 DB), `algo_db` (07:40 DB, 07:55 AlgoProd; 23:40, 23:45).
- `order_algo_db` main'de de karşılıksız (main'deki ad `algo_order_db`).

**Cron container adları her branch'te prod adlarıdır** (`MAHft`, `MAOrderService`, `MADatabaseService`). development ve preprod compose'ları farklı adlar ürettiğinden (aşağıda) o kurulumlarda cron satırları container bulamaz.

Başlatma sırasının gerekçesi: [sistem haritası → başlatma sırası](../00-genel/sistem-haritasi.md#başlatma-sırası).

## Container'lar

### Adlar (compose `container_name`)

| Servis | dev normal/onload | dev mlx | preprod normal/onload | main normal/onload | mlx (main/preprod) |
|--------|-------------------|---------|-----------------------|--------------------|--------------------|
| HFT | `MAHftTest` | `MAHft` | `MAHftPreProd` | `MAHft` | `MAHft` |
| order-service | `MAOrderServiceTest` | `MAOrderService` | `MAOrderServicePreProd` | `MAOrderService` | `MAOrderService` |
| trade-data-app | `MADatabaseServiceTest` | `MADatabaseService` | `MADatabaseServicePreProd` | normal: `MADatabaseServiceTest`, onload: `MADatabaseService` | main: `MADatabaseService`; preprod'da mlx compose yok |
| AlgoProd | `MAAlgoProd` | `MAAlgoProd` | `MAAlgoProd` | `MAAlgoProd` | `MAAlgoProd` |
| Admin UI | `MAAdminUITest` (her branch) | | | | |
| MySQL | `mysql_container` (`Configs/*/mysql-docker-compose.yml`, `mysql:5.7`) | | | | |
| nginx | `nginx-proxy` (`Configs/*/nginx/docker-compose.yml`) | | | | |

Not: AlgoProd compose'larında servis anahtarı `hft` (kopyala-yapıştır); container adı doğru.

### Ağ, CPU, yetkiler

- `network_mode: host`: HFT, order-service, trade-data-app, AlgoProd, nginx. **İstisnalar:** MAAdminUI bridge + `81:80`; MySQL bridge + `3306:3306`; main'deki `Monitoring/` (node-exporter `9100`, cadvisor `8079`, bridge; pushprox host).
- **cpuset:**

  | Servis | development | preprod | main |
  |--------|-------------|---------|------|
  | HFT (normal, onload) | `19-35` | yok | `32-63` |
  | order-service, trade-data-app (normal, onload) | `0-18,36-55,66-71` | yok | `0-31` |
  | mlx compose'lar, AlgoProd | yok | yok | yok |

  development yorumu: "CPU 20-29 izole (isolcpus); HFT pinleri: 20-29 (FIFO spin), 30-35 (destek), 19"; "56-65 izole çekirdeklerin HT kardeşleri – boş kalmalı". Bu değerler belirli bir donanıma göre yazılmış; ❓ doğrulanmadı: hangi sunucu.
- **cap_add `NET_ADMIN`, `IPC_LOCK`, `SYS_NICE`** + **ulimit `memlock -1`, `rtprio 99`**: HFT, order-service, trade-data-app (normal, onload, mlx). `nofile 65536`: HFT ve trade-data-app (order-service normal/onload'da yok). ⚠ preprod'da farklı: HFT ve order-service **normal** compose'unda cap_add ve ulimit yok. AlgoProd: hiçbiri yok (mlx'te yalnız memlock).
- **devices:** onload → `/dev/onload`, `/dev/onload_epoll`, `/dev/sfc_char`; mlx → `/dev/infiniband/uverbs0`, `uverbs1`, `rdma_cm`.
- **env:** mlx HFT `LD_PRELOAD=libxlio.so` + `XLIO_*` (`XLIO_SPEC=latency`, `RX_POLL=-1`, `INTERNAL_THREAD_AFFINITY=0`…); mlx order-service/trade-data-app `libvma.so` + `VMA_*`. ⚠ preprod'da onload compose'lara `EF_MAX_ENDPOINTS=1024`, `EF_STACK_NAME=hft|db_service`. trade-data-app compose'ları AWS anahtarlarını düz metin env olarak taşır (`<REDACTED>`).
- **restart:** `always` yalnız trade-data-app normal compose ve tüm AlgoProd compose'larında; nginx `unless-stopped`. Diğerleri restart politikasız — host reboot sonrası ertesi sabah cron'u başlatır.
- **logging:** json-file, `max-file: 2`, `max-size: 5g` (AdminUI 1g, nginx 50m×10).

### Volume'ler ve config yolları

Config dosyaları **volume değildir**; build sırasında imaja `ADD` edilir. Config değişikliği için ya imaj yeniden build edilir ya `docker cp` + restart yapılır (aşağıda).

| Servis | Container içi config | Kaynak (repo) | Host log dizini → container |
|--------|----------------------|---------------|------------------------------|
| HFT | `/workingDirectory/HftSrvProd/Configuration.toml` | `Configs/<M>/HFT-Configuration.toml` | `$HOME/workingDirectory/container-logs/MAHft/` → `/workingDirectory/HftSrvProd/log` |
| order-service | `/workingDirectory/order-service/config.yaml` | `Configs/<M>/order-service-config.yaml` | onload/mlx: `$HOME/workingDirectory/container-logs/OrderService/`; **normal compose: `…/container-logs/OrderServiceTest/`** (her branch) → `/workingDirectory/log` |
| trade-data-app | `/workingDirectory/config.json` (+ `ext/` dosyaları `/workingDirectory/`) | `Configs/<M>/dbservice-config.json` | onload/mlx: `$HOME/workingDirectory/container-logs/MADatabaseService/` → `/workingDirectory/log`; **normal compose: log volume'ü yok** |
| AlgoProd | `/workingDirectory/AlgorithmicTrading/Configuration.ini`, `holidays.csv` | `Configs/<M>/Algo-Configuration.ini` | `$HOME/workingDirectory/container-logs/MAAlgoProd/` → `/workingDirectory/log` |
| MySQL | init: `/docker-entrypoint-initdb.d/setup.sql` | `mysql/setup.sql` | host `$HOME/workingDirectory/mysql/setup.sql` (veri dizini volume değil) |
| nginx | `/etc/nginx/nginx.conf`, `conf.d/`, `ssl/` | `Configs/<M>/nginx/` | `$HOME/nginx/logs` → `/var/log/nginx` |

Ortak: `$HOME/workingDirectory/sock/` → `/workingDirectory/sock` (HFT, order-service, AlgoProd). Core dump dizini `/workingDirectory/cores` (HFT, AlgoProd imajında oluşturulur, volume değil; `run.sh` `ulimit -c unlimited`).

Diğer host yolları: `$HOME/db_scripts/` (yedek/gece scriptleri), `$HOME/workingDirectory/Outputs/` (yedek çıktıları; `config.sh` `OUTPUT_DIR`), `$HOME/workingDirectory/backups/database/<tarih>/` (`mysql_backup.sh`, 30 gün), `$HOME/setup_copy_binary.sh`, `$HOME/Setup/` (paket).

### İmajlar

| Dockerfile | `FROM` | Not |
|------------|--------|-----|
| HFT, OrderService, MADatabaseService `Dockerfile` (normal) | `meeapps/maprodenv:3.0` (⚠ main'de `4.0`) | `MAProdEnv/lib`→`/usr/local/lib`, `include`→`/usr/local/include`, binary + scripts `ADD` |
| `*_Onload_Dockerfile` | `meeapps/maprodenv:4.0` | OpenOnload 9.2.0.43 userspace'i imaj içinde derler (`onload_build --user64`). TCPDirect: HFT `ONLOAD_WITHZF=0`, OrderService `=1` |
| `*_Mlx_Dockerfile` | `meeapps/maprodenv:3.0` | `MAProdEnv/mellanox/lib` → `/usr/local/lib`, `ldconfig`; HFT için XLIO host'tan bind-mount edilir (compose yorumu: vendored DPCP 1.1.38 XLIO 3.x için eski) |
| `MAAlgoProd/Dockerfile` | `maprodenv:3.0` | WORKDIR `/workingDirectory/AlgorithmicTrading` |
| `MAAdminUI/Dockerfile` | `nginx:1.21.0-alpine` | statik `build/` |

`trade-data-app` imajı yalnız `libMAItchSDK.so` ve `libMAPerfSDK.so`'yu alır.

### `MAProdEnv/`

- `Dockerfile`: `ubuntu:22.04` + build araçları, `zip`, `awscli`, prometheus-cpp, flatbuffers v1.12.0, gRPC v1.33.1 (`scripts/install_grpc.sh`), protobuf, sentry-native; `aws/` → `/root/.aws/`; `libcpprest-dev`. AWS anahtarları Dockerfile'da düz metin (`<REDACTED>`). Docker Hub'daki `meeapps/maprodenv:<sürüm>` buradan (`maprodenv.yml`).
- `lib/`: `libMAItchSDK{,_Onload,_Mlx}.so`, `libMAOrderSDK{,_Onload,_Mlx}.so`, `libMARpc.so`, `libouchSDK.so`, `libMAPerfSDK.so`, `libAsyncLogger.so`, quickfix, cpprest, yaml-cpp, fmt, flatbuffers. SDK CI'ları buraya yazar ([branch-ve-ortamlar](../00-genel/branch-ve-ortamlar.md#c-servislerin-cicdsi)).
- `include/`: aynı SDK'ların header'ları. `onload/`, `mellanox/`: hızlandırma kütüphaneleri.
- `scripts/run.sh`: eski, kullanılmıyor (`OrderService` binary adını çağırıyor).
- algo-configs `container-images/MAProdEnvironment/` ayrı bir build imajıdır (`meeapps/ma-prod-env`, geliştirme araçları); kurulum paketine girmez.

## `run*.sh` — başlatma ve SIGTERM

Her container'da PID 1 `bash run.sh`; binary arka planda başlar, `wait $!`. `docker stop` SIGTERM'i yalnız PID 1'e (bash) yollar; `trap _term SIGTERM` çalışır.

| Script | Başlatma | `_term` | Arşiv | S3 |
|--------|----------|---------|-------|----|
| `HFT/scripts/run.sh` | `HftSrvProd /workingDirectory/HftSrvProd/Configuration.toml` (⚠ main/preprod'da `Configuration.ini`) | `kill -15 HftSrvProd` | `hft*` + `itchsdk*` → `log-backups-<ddmmyyyy_HHMMSS>.zip` | `aws s3 cp` → `s3://<S3_BACKUP_BUCKET>/<MODE>/<COMPANY_NAME>/HFT/logs/` |
| `HFT/scripts/run_mlx.sh` (dev; ⚠ main/preprod'da yok) | `LD_PRELOAD=libxlio.so`, config `Configuration.ini` | aynı | aynı | aynı (ama `MODE`/`COMPANY_NAME` gömülmez) |
| `OrderService/scripts/run{,_onload,_mlx}.sh` | `PiramitOrderService …/config.yaml`; onload: `onload` önekiyle; mlx: `LD_PRELOAD=libvma.so` | `killall PiramitOrderService` | `order_service.*.txt` → zip | **yok** |
| `MADatabaseService/scripts/run{,_onload,_mlx}.sh` | `MADatabaseService -config=… -log-path=/workingDirectory/log` | `killall MADatabaseService`; `/workingDirectory/*.txt` silinir | `*.txt` → zip | **yok** |
| `MAAlgoProd/scripts/run.sh` | `AlgoProd …/Configuration.ini` | `kill -15 AlgoProd` | `strategyLog/WarrantTracker` ve `algo*`+`itchsdk*` → `…-<YYYY-mm-dd-HH-MM-SS>.tar.gz` (pigz) | **yok** |

- Arşivler log dizininde, yani host'ta `container-logs/<servis>/` altında kalır.
- `copy_strategy_logs.sh` (AlgoProd strateji logu → `…/AlgorithmicTrading/strategylogs/`) hiçbir yerden çağrılmıyor.
- `Configs/Marbas/db_scripts/logBackupCleanPush.sh`: `container-logs/{MAAlgoProd,MAHft,OrderService}` altındaki dünkü `log-backups-<YYYY-mm-dd>-*.tar.gz`'leri S3'e yükler, 8 günden eski dosyaları siler, Discord'a bildirir. development `install.sh` bunu kurmaz. ⚠ main `install.sh` `./install_logBackupCleanPush.sh`'ı çağırır ama dosya main ağacında yok.
- Gece DB işleri (`backupAllDatabases.sh` 22:30): `dbNightEvent.sh` (`CALL RemoveOldData` her DB'de) → her DB için `mysqldump | gzip`.

## Tuning (`setup_tunning.sh`, `hft-tuning.service`)

Kodda olan: yalnız `Configs/Seker/tunning/` (development; Şeker eski müşteri) ve kök `setup_tunning.sh` (development). Script'ler belirli bir sunucuya (Mellanox ConnectX-5, belirli arayüz adları, `/home/<USER>/` yolları) yazılmış:

| Dosya | Etki | Kalıcı mı |
|-------|------|-----------|
| `01-power.sh` | governor `performance`, `scaling_min_freq=max`, C1E/C6 kapalı, sched migration cost, KSM kapalı | hayır |
| `02-sysctl.sh` | `/etc/sysctl.d/99-itch-sdk.conf`: rmem/wmem 128 MiB, `netdev_max_backlog 50000`, `busy_poll/busy_read 50`, `rp_filter 0`, `igmp_max_memberships 200`, `tcp_timestamps 0`, `numa_balancing 0`, `timer_migration 0`, `min_free_kbytes 2 GiB` | evet |
| `03-nic.sh` | ethtool: coalescing 0, ring max, GRO/LRO/TSO/GSO off, `rx_cqe_compress off`, `tx_push on`, threaded NAPI | hayır |
| `04-irq.sh` | NIC IRQ'ları housekeeping çekirdeklere | hayır |
| `04b-move-stray-irqs.sh` | diğer IRQ'ları izole çekirdeklerden çıkarır | hayır |
| `05-thp.sh` | THP `never` (runtime) | hayır |
| `06-grub-extras.md` | Sonraki bakımda eklenecek GRUB parametreleri (doküman) | — |
| `10-isolcpus-grub.sh` | GRUB: `isolcpus=domain,managed_irq,…`, `nohz_full`, `rcu_nocbs`, `transparent_hugepage=never`; `update-grub` | evet (reboot) |
| `20-post-reboot.sh` | 01, 03, 04, 04b, 05'i yeniden uygular | — |
| `hft-tuning.service` | oneshot; trading NIC `up` olana kadar 30 sn bekler, `/home/<USER>/tunning/20-post-reboot.sh` çalıştırır; `WantedBy=multi-user.target` | evet |

`setup_tunning.sh` `cd tunning/` yapar ve `01-cpu.sh`, `02-kernel.sh`, `03-nic.sh`, `04b-…`, `05-thp.sh`, `06-grub-extras.md`, `10-isolcpus-grub.sh` çalıştırır, sonra servisi `/etc/systemd/system/`'e kopyalayıp `enable` eder. Kök dizinde `tunning/` yok ve adlar Seker'dekilerle uyuşmuyor; script pakete de girmiyor. Pratikte tuning elle uygulanıyor. ❓ doğrulanmadı: diğer müşteri sunucularında uygulanmış tuning.

Bilerek kapalı tutulan ayarlar (`mlockall`, main thread pinleme, `SCHED_FIFO`): [hftsrvprod/config.md](../10-servisler/hftsrvprod/config.md) (toml yorumları).

## Güncelleme / yeniden deploy

Binary'nin sunucuya ulaşma yolu:

1. Servis repo CI'ı binary'yi Algo-Setup'ın aynı adlı branch'ine commit'ler (`master` → `main`).
2. Bu push `algosetup.yml`'ı tetikler; her müşteri için zip S3'e yeniden yüklenir.
3. Sunucuda iki yol tanımlı:

**a) Gece otomatik kopyalama — `setup_copy_binary.sh` (cron 22:00, hafta içi).** Niyet: `<companyName>_Setup_development.zip`'i S3'ten indirmek, `$HOME/Setup`'ı silip yeniden açmak, sonra `docker cp` ile çalışan container'lara binary, config ve `MAProdEnv/{lib,include}` kopyalamak (imaj build edilmez; yeni binary ertesi sabah `docker start` ile devreye girer):

| `setup_mode` | Kopyalanan |
|--------------|-----------|
| `hft_order_db` | `MADatabaseService` binary + `config.json`; `HftSrvProd/` dizini → `MAHft`; `PiramitOrderService` + `config.yaml` → `MAOrderService`; lib/include → `MAHft`, `MAOrderService` |
| `hft_order` | aynı (DB hariç); order-service binary'si **`MAOrderServiceTest`**'e, config ve lib'ler `MAOrderService`'e |
| `order_db`, `db` | ilgili alt küme |
| `algo` | `AlgoProd` + `Configuration.ini` → `MAAlgorithmicTrading` (compose adı `MAAlgoProd`) |

- Zip adı branch'ten bağımsız olarak hep `_development`'tır (⚠ main'de de aynı).
- Script şu an çalışmaz (bkz. Şüpheli: `companyName` boş).

**b) Elle yeniden build.** Yeni zip indirilip açılır, ilgili servis dizininde `docker-compose up -d --build` (`setup_<servis>.sh`) çalıştırılır. Bu komut imajı yeniden build eder (binary + config `ADD`) ve container'ı yeniden yaratıp **hemen başlatır**; seans saatinde dikkat. Config değişikliği de bu yoldan ya da `docker cp <dosya> <container>:<yukarıdaki yol>` + `docker restart` ile yapılır. ❓ doğrulanmadı: operasyonun fiilen hangi yolu kullandığı (kodda kayıt yok).

Kaldırma: `uninstall.sh` Docker'ı ve `/var/lib/docker`'ı tamamen siler, `crontab -r` (tüm crontab), `../*-Setup/` dizinlerini siler. Onload yalnız Solarflare'de kaldırılır.

## Doğrulama komutları

```bash
crontab -l                                   # setup_mode'a uygun satırlar + 22:00 copy_binary
sudo sysctl -a | grep -a net.core            # rmem/wmem (dev: install.sh değerleri; main: sysctl.conf)
chronyc tracking                             # BIST NTP'ye senkron
docker ps -a --format '{{.Names}}\t{{.Status}}'   # container adları cron'dakiyle aynı mı
docker inspect -f '{{.HostConfig.CpusetCpus}} {{.HostConfig.CapAdd}}' <container>
docker logs --tail 100 -f <container>
ls $HOME/workingDirectory/container-logs/    # MAHft, OrderService|OrderServiceTest, MADatabaseService, MAAlgoProd
docker exec <container> cat /workingDirectory/HftSrvProd/Configuration.toml | head   # imajdaki config
onload --version; ls /dev/onload*            # Onload host sürümü (container ile eşleşmeli)
docker exec MAHft xlio_stats -v 5            # mlx: XLIO soket hızlandırması
cat /proc/cmdline; cat /sys/devices/system/cpu/isolated   # isolcpus
systemctl status hft-tuning.service
```

Açılış log imzaları: [log-imzalari.md](log-imzalari.md).

## Şüpheli

- **`setup_copy_binary.sh` bozuk:** 1. satırda shebang yok, CI `companyName`'i 2. satıra ekliyor; `zipFile=$companyName"_Setup_development.zip"` 1. satırda boş değerle hesaplanıyor → URL `…/<Müşteri>/_Setup_development.zip`. Script önce `rm -rf $HOME/Setup` yapıyor, yani her gece 22:00'de kurulum dizini silinip indirme başarısız oluyor. Doğrula: sunucularda `$HOME/Setup` var mı, cron satırı duruyor mu.
- **Prod sunucusu development zip'ini çekmeye çalışıyor:** `setup_copy_binary.sh` main'de de `_Setup_development.zip` adını kullanıyor. Script düzelirse prod container'lara development binary'leri kopyalanır.
- `setup_copy_binary.sh` `hft_order`: order-service binary'si `MAOrderServiceTest`'e, diğer dosyalar `MAOrderService`'e; `algo` modu `MAAlgorithmicTrading` adını kullanıyor (compose: `MAAlgoProd`).
- **Cron ↔ container adı uyuşmazlığı:** development (`*Test`) ve preprod (`*PreProd`) compose adları cron'daki prod adlarıyla eşleşmiyor; bu ortamlarda günlük start/stop çalışmaz. main normal (regular) DB compose'u da `MADatabaseServiceTest`.
- **`order_algo_db` (Alnus_Algo matrisi) `install.sh`'ta karşılıksız** (dev ve main; main'deki dal `algo_order_db`). Paket hiçbir servis kurmaz, yalnız 22:00 cron'u ekler. development'ta `algo_order` cron eklemiyor.
- **HFT config adı:** main ve preprod `HFT/scripts/run.sh` `Configuration.ini` veriyor; CI `Configuration.toml` yazıyor; HftSrvProd master `loadConfiguration(argv[1])` TOML parse ediyor. Temiz kurulumda HFT config bulamamalı. Doğrula: prod container'da hangi dosya var.
- `HFT/scripts/run_mlx.sh` `Configuration.ini` kullanıyor ve CI ona `MODE`/`COMPANY_NAME` gömmüyor (S3 yolu `//HFT/logs/`).
- **Graceful kapanış çalışmıyor olabilir:** HFT ve AlgoProd `_term` içinde `kill -15 <isim>` (bash `kill` isim kabul etmez); binary SIGTERM almıyor, `wait $!` docker stop zaman aşımına (dev 10 sn, main 90 sn) kadar bekleyip SIGKILL'e düşüyor. order-service/trade-data-app `killall` kullanıyor; doğrula: `psmisc` (killall) ve AlgoProd için `pigz` maprodenv imajında var mı.
- Log arşivi S3'e yalnız HFT'den gidiyor; order-service, trade-data-app, AlgoProd yalnız yerelde zip/tar.gz bırakıyor. README "S3'e yükler" genellemesi yanlış.
- **Mlx yolu kırık:** CI mlx seçince `HFT_Mlx_Dockerfile` / `OrderService_Mlx_Dockerfile`'ı `Dockerfile`'a yeniden adlandırıyor ama mlx compose'ları eski adı referans ediyor; OrderService mlx Dockerfile `run_mlx.sh` çağırıyor ama CI onu `run.sh`'a çeviriyor; trade-data-app için mlx compose/Dockerfile seçim adımı yok; `install_mlx.sh` zip'e girmiyor. Şu an mlx müşterisi yok.
- Zip'e girmeyen ama çağrılan dosyalar: `install_mlx.sh` (her branch); main'de `sysctl.conf`, `setup_monitoring.sh`, `install_logBackupCleanPush.sh` (sonuncusu main ağacında hiç yok).
- development `install.sh` `$HOME/workingDirectory/mysql/setup.sql`'i oluşturmuyor ama MySQL compose oraya bind-mount ediyor → Docker boş dizin yaratır, şema init edilmez. Ayrıca `mkdir $HOME/workingDirectory/sock` `-p`'siz.
- `install_data.sh` (Piramit, Global, Piramit_Algo, Seker) son satırında kapanmamış `"` → bash sözdizimi hatası. `backupAllDatabases.sh` (Piramit, Global, Piramit_Algo, Seker) `./mysqlBackup.sh` çağırıyor, dosya adı `mysql_backup.sh` → gece yedeği alınmıyor olabilir.
- trade-data-app normal compose'unda log volume'ü yok; loglar container silinince kaybolur.
- Düz metin sırlar repoda: `install.sh` Docker Hub şifresi, trade-data-app compose'ları ve `MAProdEnv/Dockerfile` AWS anahtarları, `aws/credentials`, `Configs/*/mysql-docker-compose.yml` ve `db_scripts` MySQL şifreleri, Marbas Discord webhook'u, `MADatabaseService/ext/meeapps.key`.
- `setup_tunning.sh` var olmayan dizin/dosyaları çağırıyor ve bir `.md` dosyasını çalıştırmaya çalışıyor; Seker `06-grub-extras.md` (`3-15,35-47`) ile `10-isolcpus-grub.sh` (`4-13,36-45`) izole çekirdek aralıkları farklı.
- preprod `MODE=Production` ile paketleniyor; preprod HFT logları prod S3 yoluna gider.
- `install.sh` sysctl ayarları (development/preprod) `sysctl -w` ile, kalıcı değil.
