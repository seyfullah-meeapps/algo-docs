---
kapsam: itch-sdk alım yolu — RX/decoder thread'leri ve başlatma sırası, recv modları, MoldUDP64 çerçeveleme ve sequence takibi, birincil/ikincil hat, Rewinder, Glimpse ve canlıya geçiş tamponu, kuyruk dolması, partition varsayımları, PerfSDK metrikleri, kopma senaryoları
kaynak:
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# itch-sdk — alım yolu (ağ → emir defteri)

İndeks: [README.md](README.md). Bu dosyada olmayanlar:
- ITCH mesaj kataloğu, alan ofsetleri, `OrderbookInfo`/`OrderDepth` iç yapısı, header/level/momentum mantığı → [mesajlar-ve-emir-defteri.md](mesajlar-ve-emir-defteri.md)
- C API, abonelik türleri, callback imzaları, snapshot-end payload'ının alanları → [abonelik-api.md](abonelik-api.md)
- HFT tarafı (`ItchSdkClient`, strateji kuyruğu, snapshot-end sonrası yükleme) → [hftsrvprod/itch-entegrasyonu.md](../hftsrvprod/itch-entegrasyonu.md)

Kod: `Clients/SDKItchManager.{h,cpp}` (`start`, `createSPSCQueues`, `createReceiversAndClients`, `initializeAndStartComponents`, `fireSnapshotEndEvent`, `isMarketGlimpseComplete`, `waitForMarketLiveRelease`), `Clients/ItchReceiver.{h,cpp}` (`receiverLoop`, `recvBatchPosix`, `recvBatchZC`/`zcCallback`, `recvBatchXLIO`, `demuxAndEnqueue`, `pinToCore`), `Clients/ItchClient.{h,cpp}` (`clientThreadMain`, `runGlimpsePhase`, `bufferLiveUntilRelease`, `processPacket`, `handleSequenceGap`, `processRewinderQueue`, `drainRewinderSocket`), `Clients/GlimpseClient.{h,cpp}`, `Connections/ITCHTCPConnection.cpp` (`Connect`, `parse`), `Messages/Session/RequestPacket.cpp`, `Public/spsc_ring_buffer.h`, `Public/config.h`, `Globals/TimestampExtract.h`, `Globals/TscClock.h`.

## 1. Bileşenler, thread'ler, başlatma sırası

```
NIC ─► ItchReceiver (ItchRx-<port>) ─demux(src IP)─► main SPSC ring ─► ItchClient thread ─► OrderbookInfo ─► callback
                                                                         ▲
                     Rewinder sunucusu ─UDP unicast─► rewinderSocket ────┘ (aynı thread okur → rewinder SPSC ring)
                     Glimpse sunucusu ─TCP────────────────────────────────┘ (aynı thread, yalnız açılışta)
```

| Bileşen | Adet | Thread | Ne yapar |
|---------|------|--------|----------|
| `ItchReceiver` | (`broadcastLocalInterface`, ITCH `port`) çifti başına 1 | `ItchRx-<port>` | UDP soketi, multicast join, recv, kaynak IP ile demux, ring'e memcpy |
| `ItchClient` | `MulticastConfiguration` başına 1 (receiver grubu başına en çok 1 Spot + 1 VİOP) | isimsiz | Glimpse, canlı tampon, sequence, Rewinder, parse, **abone callback'leri** |
| `GlimpseClient` | `ItchClient` başına 1 | yok (`ItchClient` thread'inde çalışır) | SoupBinTCP login + snapshot |
| SPSC ring | config başına 1 main + 1 rewinder | — | `SPSCRingBuffer`, üretici RX (main) / `ItchClient` (rewinder) |

Aynı port'u paylaşan Spot ve VİOP partition'ı (HFT config'inde Spot P1 ve VİOP P1 ikisi de `21001`) tek receiver'a düşer. Ayrım kaynak IP ile yapılır (§3.1). Aynı grupta aynı pazar iki kez varsa `createReceiversAndClients` hata döner, `start()` başarısız olur.

**Sabitlenme ve öncelik:**
- RX: `receiverCpuCores[4]`'ten sırayla, receiver grubu oluşma sırasına göre. 5. ve sonraki receiver'a çekirdek verilmez (`core = -1`).
- Client: `MulticastConfiguration.clientCpuCore`.
- İkisinde de `core <= 0` sabitleme yok demektir. Çekirdek 0'a sabitlemek mümkün değildir (kasıtlı: sıfır-init güvenli varsayılan).
- `SCHED_FIFO` önceliği 80'dir. Yalnız sabitleme başarılıysa **ve** ortamda `ITCH_RT_FIFO` tanımlıysa uygulanır (2026-07-03 yorumu: host'ta `stalld` yoksa kworker aç kalıp makine kilitleniyor).
- ⚠ Eski bilgi tabanı RX'in her zaman FIFO@80 olduğunu söylüyordu. development'ta FIFO env'e bağlı.
- HFT `src/Configuration/Configuration.toml` bugün `receiverCpuCores = [-1,-1,-1,-1]` ve `clientCore = -1` ile geliyor ("SAFE .28" yorumu). Yani o config'le ne sabitleme ne FIFO var.

**`SDKItchManager::start()` sırası** (host thread'inde, bloklayıcı):
1. Onload/XLIO derlemesinde `LD_PRELOAD` kontrolü, gerekirse `execvp` (§2).
2. `createSPSCQueues`: config başına main ring (`mainRingBufferSize`, varsayılan `MAIN_RING_SIZE` = 16384 slot) ve rewinder ring (`rewinderRingBufferSize`, varsayılan 1024 slot).
3. `createReceiversAndClients`: gruplama, `setMarketSourceIps`, `partId`, `ItchClient` nesneleri.
4. `setupReceiversWithQueues`: ring işaretçileri receiver'a ve client'lara dağıtılır.
5. `initializeAndStartComponents`, **grup grup**:
   - `receiver->initialize`: soket ve join.
   - Client `initialize`: rewinder soketi `bind(rewinderLocalPort)`, rewinder adresi seçimi (§4), `GlimpseClient` kurulumu.
   - `receiver->start`.
   - Client `start`: thread hemen Glimpse'e başlar.
6. Glimpse kapısı: 10 ms aralıkla bütün client'larda `isGlimpseFinished()` kontrol edilir.
   - Biri bitmeden ölmüşse (`!isRunning()`): `cleanup()`, `ITCH_SDK_ERROR_CONNECTION_FAILED`.
   - `glimpseStartTimeoutMs` (varsayılan 30000 ms) aşılırsa: aynı sonuç.
7. `running = true`, `ITCH_SDK_SUCCESS`.

`start()` başarı döndüğünde canlı işleme **başlamamış olabilir**: canlı serbest bırakma ayrı bir kapıdır (§6.3).

**Config anahtarları** (`Public/config.h` `ItchSdkConfigurations`; 0 = varsayılan):

| Alan | Birim | Varsayılan | Kullanıldığı yer |
|------|-------|-----------|------------------|
| `mainRingBufferSize` / `rewinderRingBufferSize` | slot | 16384 / 1024 | `createSPSCQueues` (2'nin kuvveti olmalı, kontrol yok, Şüpheli 9) |
| `receiverCpuCores[4]` | çekirdek no | — (≤0 = yok) | `createReceiversAndClients` |
| `busyPollUsec` | µs | 50 | `SO_BUSY_POLL` |
| `socketRcvBufBytes` | byte | 64 MiB | `SO_RCVBUF` + `SO_RCVBUFFORCE` |
| `glimpseRetryCount` | adet | 0 → tek deneme (yorum "default 3" der, kod 0'ı olduğu gibi kullanır) | `runGlimpsePhase` |
| `glimpseRetryBackoffMs` | ms | 0 → bekleme yok | `runGlimpsePhase` |
| `glimpseStartTimeoutMs` | ms | 30000 | `start` kapısı |
| `rewinderRequestTimeoutMs` | ms | 5000 | `processRewinderQueue` yeniden gönderim |
| `onloadStackName` | — | `"hft-itch"` | `onload_set_stackname` |

Varsayılanlar SDK içinde yalnız ring boyutu, buffer, busy poll, Glimpse zaman aşımı ve Rewinder zaman aşımı için uygulanır. Retry sayısı/backoff için uygulanmaz. Değeri tüketici config'i verir (HFT `ConfigurationManager::getGlimpseRetryCount` vb.).

## 2. Recv modları ve derleme varyantı

Mod **derleme anında** seçilir. CMake kütüphaneyi bulursa tanımı ekler (`CMakeLists.txt`):

| Tanım | Koşul | RX fonksiyonu |
|-------|-------|---------------|
| (yok) | — | `recvBatchPosix`: `recvmmsg`, batch `RECV_BATCH_SIZE` = 16, `MSG_DONTWAIT`, `MSG_TRUNC` ve `< MIN_PKT` (20 byte) eleme |
| `ITCH_ONLOAD_ZC` | `libonload_ext` | `recvBatchZC`: `onload_zc_recv` + `zcCallback`, datagram başına callback, kopyala-kuyruğa koy, `ONLOAD_ZC_CONTINUE` |
| `ITCH_MLX_ZC` | `libxlio` + `mellanox/xlio_extra.h` | `recvBatchXLIO`: `socketxtreme_poll` + `socketxtreme_free_packets`. `xlio_get_api()` NULL ise **çalışma anında** POSIX'e düşer |

- İkisi birden tanımlıysa `receiverLoop` önceliği Onload ZC'ye verir.
- CI (`.github/workflows/itchsdk.yml`) aynı `libMAItchSDK.so`'yu üç adla kopyalar: `_Onload`, `_Mlx`, düz. Hangisinin hangi ortamda derlendiği CI makinesindeki kütüphanelere bağlıdır.
- ❓ doğrulanmadı: `scripts/build.sh` `-DITCH_ONLOAD_ZC` cmake değişkeni geçiyor ama `CMakeLists.txt` bu değişkeni okumuyor. Seçim yalnız `find_library` ile yapılıyor.

**`LD_PRELOAD` ve `execvp`** (`SDKItchManager::start`):
- **Onload:** `LD_PRELOAD` boşsa `LD_PRELOAD=libonload.so` set edilir ve `execvp(savedArgv[0], savedArgv)` ile süreç yeniden başlar.
- **XLIO:** `LD_PRELOAD` içinde `libxlio` yoksa mevcut değerin başına `libxlio.so:` eklenip aynı şekilde yeniden başlanır.
- Bunun için host'un önceden `itchsdk_set_arguments(argc, argv)` çağırmış olması gerekir. Çağırmadıysa `start()` `ITCH_SDK_ERROR_NOT_INITIALIZED` döner.
  - AlgorithmicTrading (`algoSrc/Managers/ItchSdkManager.cpp`) çağırıyor.
  - HftSrvProd çağırmıyor. Onload varyantıyla HFT, `onload` sarmalayıcısıyla (LD_PRELOAD dolu) başlatılmak zorundadır.
- `initialize()` Onload için `EF_*`, XLIO için `XLIO_*` değişkenlerini `setenv(..., 0)` ile yazar (operatör değeri ezilmez). Bu değişkenler kütüphane yüklenirken okunur:
  - `execvp` yolunda yeni sürece miras geçtikleri için etkilidirler.
  - Süreç zaten preload'la başlatıldıysa büyük ölçüde etkisizdirler. Tuning shell'den verilmelidir (`scripts/onload-env.sh`).

Zaman damgası: soket `SO_TIMESTAMPING` (RX HW+SW) ile açılır, ama `extractHwTimestamp` yalnız `ts[0]`'ı alır. Bu, kernel SW RX damgasıdır (CLOCK_REALTIME, ns). Kasıtlı: PHC senkronu yok. XLIO yolunda damga yoktur (`pktTs = 0`).

## 3. Paket çerçeveleme ve sequence

### 3.1 Demux (RX thread, `demuxAndEnqueue`)

Kaynak IP sırayla karşılaştırılır. İlk eşleşen kazanır:

| Sıra | Kaynak IP | Hedef ring |
|------|-----------|------------|
| 1 | Spot `sourceIp` / `secondarySourceIp` | Spot main |
| 2 | VİOP `sourceIp` / `secondarySourceIp` | VİOP main |
| 3 | Spot `rewinderSourceIp` / `secondaryRewinderSourceIp` | Spot rewinder ring |
| 4 | VİOP aynıları | VİOP rewinder ring |
| — | eşleşme yok veya ring null | `packetsUnknownSrc++`, düşer |

- Ring'e yazılan: ham UDP payload (MoldUDP64 başlığı dahil) + `receive_timestamp` (kernel SW, CLOCK_REALTIME ns) + `demux_timestamp` (`steady_clock` ns).
- HFT `rewinderSourceIp` olarak ITCH kaynak IP'sini veriyor (`ConfigurationManager::getItchSdkConfigurations`). 1. satır önce eşleştiği için receiver'ın rewinder ring'ine fiilen hiçbir şey gitmez.
- Gerçek Rewinder yanıtları ITCH portuna değil `rewinderLocalPort`'a gelir ve `ItchClient::drainRewinderSocket` tarafından okunur (§5).

### 3.2 MoldUDP64 başlığı (`ItchClient::processPacket`)

| Ofset | Uzunluk | Alan | Okuma |
|-------|---------|------|-------|
| 0 | 10 | session | **okunmaz** |
| 10 | 8 | sequence (BE `uint64`) | `be64toh` |
| 18 | 2 | message count (BE `uint16`) | `ntohs` |
| 20 | — | `[2 byte BE uzunluk][ITCH mesajı]` × count | `parseItchMessage` |

Sequence **mesaj** sayar, paket değil: bir sonraki beklenen = `sequence + messageCount`.

| Durum | Davranış |
|-------|----------|
| İlk canlı paketler, `seq < baseline` | Sessizce atılır, `droppedBeforeBaseline++`. İlk kabul edilen pakette bir kez "live transition" log'u basılır (baseline, firstUdp, dropped, initialGap). |
| `seq == expected` | `expected += messageCount`, mesajlar parse edilir. Heartbeat (count 0) expected'ı değiştirmez. |
| `seq > expected` | Gap → `handleSequenceGap` (§5). Tetikleyen paket parse **edilmez**, istek aralığına dahil edilir. |
| `seq < expected` | Duplicate/geç gelen paket, yok sayılır. Kısmen örtüşen paket (`seq < expected < seq+count`) de tamamen atılır. |

`expected`, mesajlar parse edilmeden önce ilerletilir. Kesik paketteki (uzunluk kontrolünde `break`) kalan mesajlar yeni bir gap üretmeden kaybolur (Şüpheli 7).

### 3.3 A/B hattı

**A/B arbitration yok.**
- Receiver yalnız `itchConfiguration.clientConfiguration.ip` grubuna join eder ve ITCH `port`'a bind eder.
- `secondaryIp`/`secondaryPort` alım yolunda hiç kullanılmaz. HFT config'inde ikincil hat ayrı port'tadır (Spot P1: `21001` / `21101`), dolayısıyla ikincil hattın paketleri sürece hiç gelmez.
- Demux'taki `secondarySourceIp` yalnız birincil grup/port'a ikinci bir kaynaktan paket gelirse işe yarar. O durumda tekilleştirme "ilk gelen kazanır + `seq < expected` atılır" şeklinde örtük olur. Bekleme penceresi yoktur: A'da kaybolan paket B'den geç gelirse önce Rewinder'a gidilir.

## 4. Birincil/ikincil seçimi

- Tek global bayrak vardır: `SDKItchManager::isPrimaryOrSecondaryVar`. Varsayılanı `Primary`, atomic değildir.
- **Glimpse:** `ITCHTCPConnection::Connect` bayrağa göre IP/port seçer. Birincilde `connect()` hata dönerse bayrağı `Secondary` yapar ve kendini yeniden çağırır. Geri dönüş yoktur.
  - Zaman aşımı yoktur: bloklayıcı `connect`, kernel SYN tekrarları kadar bekler.
  - `ConnectWithTimeout` tanımlıdır ama hiçbir yerden çağrılmaz.
- **Rewinder:** Adres `ItchClient::initialize` içinde bir kez seçilir.
  - Initialize grup grup yapılır ve önceki grubun Glimpse'i o sırada çalışmaya başlamıştır. Bu yüzden sonraki grupların rewinder adresi, önceki grubun Glimpse sonucuna göre birincil ya da ikincil olur (yarış).
  - Bayrak değiştikten sonra, önceden initialize edilmiş client'ların rewinder adresi birincilde kalır.
- **Multicast:** Bayraktan etkilenmez, hep birincil grup (§3.3).
- Çalışma sırasında failover yoktur (`ItchClient.cpp` yorumu "start-time only"). Kasıtlı.

## 5. Gap ve Rewinder

Durum makinesi `ItchClient` thread'ine aittir. Alanlar: `missedStartSeq`, `requestEndSeq`, `requestTs`, `recoveryTryCount`, `isRecovering`.

1. **Tespit** (`handleSequenceGap(expected, seq, count)`):
   - `missedStartSeq = expected`, `requestEndSeq = seq + count - 1`.
   - İstek gönderilir, `isRecovering = true`.
2. **İstek** (`sendRewinderRequest`):
   - 20 byte UDP: `[session 10][başlangıç seq 8 BE][count 2 BE]`.
   - `count = end - start + 1`, `RequestPacket` içinde [1, 65535]'e sıkıştırılır.
   - Session, Glimpse `LoginAccept`'ten gelir (`GlimpseClient::getSession`). Boşsa istek gönderilmez ve log basılır, `isRecovering` true kalır.
   - ⚠ Eski bilgi tabanı bu durumda `isRecovering`'in sıfırlandığını söylüyordu. development'ta sıfırlanmaz, istek her zaman aşımında tekrar denenir.
   - `sendto` hatası `isRecovering = false` yapar. İlk istekte bu satır `handleSequenceGap` içindeki sonraki `isRecovering = true` ile ezilir.
3. **Kurtarma döngüsü** (ana döngü, her tur):
   - `drainRewinderSocket`: non-blocking `recv` (2048 byte tampon), sonuç rewinder ring'e yazılır.
   - `isRecovering` ise `processRewinderQueue` çalışır, **main ring okunmaz**.
     - Yanıt yoksa ve `rewinderRequestTimeoutMs` geçmişse aynı istek tekrar gönderilir. **Deneme sınırı yoktur.**
     - Yanıtın sequence'ı `missedStartSeq` değilse `rewinderUnwantedPackets++`, atlanır.
     - Eşleşirse: `expected += messageCount`, mesajlar normal parse yolundan geçer (callback'ler doğal sırayla), `isRecovering = false`.
4. **Kısmi yanıt:** Yanıt istenenden az mesaj taşırsa (tek UDP paketi, MTU sınırı) kurtarma yine "tamamlandı" sayılır. Main ring'deki sıradaki paket yeni bir gap tetikler ve döngü kalan aralık için tekrarlanır. 65535'ten büyük boşluklar da böyle parça parça kapanır.
5. Kurtarma bitip `isRecovering = false` iken rewinder ring'de kalan paketler her tur boşaltılır (`rewinderUnwantedPackets++`).

**Kurtarılamazsa:**
- Örnekler: sunucu cevap vermiyor, adres yanlış, session boş, veri Rewinder'ın tuttuğu aralığın dışında.
- O partition süresiz recovery'de kalır ve her 5 s'de (varsayılan) istek yeniden gönderilir.
- Main ring okunmadığı için RX bu partition'ın bütün paketlerini düşürür (`packetsDroppedFull`).
- Glimpse'e geri dönüş, host'a callback veya public sayaç yoktur. Durum yalnız log'dan (`Rewinder resend ... tryCount=`) görülür. Diğer partition'lar etkilenmez.

## 6. Glimpse ve canlıya geçiş

### 6.1 Glimpse oturumu (`GlimpseClient::startReferanceDataClients`)

1. `connect()` (§4), `TCP_NODELAY`.
2. `login()`: SoupBinTCP `LoginRequest` gönderilir, gövde 46 byte:
   - username 6 byte, password 10 byte (config `userName`/`password` → `<GLIMPSE_USER>`/`<REDACTED>`)
   - requested session 10 byte boşluk
   - requested sequence 20 byte, değeri `"1"`, sola boşlukla doldurulur.
   - Yanıt için `SO_RCVTIMEO` = 3 s, tek `recv`, en çok 33 byte. Ardından zaman aşımı kaldırılır.
   - `A` gelirse session saklanır. `J` gelirse veya yanıt yoksa başarısızdır.
3. `parseGlimpseMessages`:
   - Bloklayıcı `recv` (20 MiB tampon), `ITCHTCPConnection::parse` ile SoupBinTCP çerçeveleri ayrıştırılır.
   - `S` + ITCH mesajı: doğrudan `ItchClient::parseItchMessage(payload+1, len-1, 0, 0)`. Canlı akışla aynı parser kullanılır, ts = 0.
   - `S` + `G` (EndOfGlimpse): `payload[2..]` ASCII ondalık sayı olarak okunur → baseline sequence (`extractEndOfGlimpseSeq`). Ardından `stopClient()` (logout + close).
   - `H`/`A`/`J` yok sayılır.
4. Baseline ≠ 0 ise başarılıdır ve `ItchClient::expectedSequenceNumber = baseline` olur.

- **Retry:** `runGlimpsePhase`, `glimpseRetryCount + 1` deneme yapar, denemeler arasında `glimpseRetryBackoffMs` beklenir. Hepsi başarısızsa thread çıkar ve `start()` kapısı SDK'yı iptal eder (§1).
- Login başarısızlığından sonraki retry'lar etkisizdir (Şüpheli 2).
- Snapshot fazında **main ring okunmaz.** Glimpse uzun sürerse ring dolar (16384 paket) ve RX düşürmeye başlar. Ring'de kalan paketler baseline altında kalıp atılır, düşenler canlıya geçişte gap → Rewinder ile kapanır.

### 6.2 Partition tamamlanması → snapshot-end

Glimpse biten client sırasıyla şunları yapar:
1. Underlying işaretçilerini bağlar.
2. `glimpseFinished = true`.
3. `onGlimpseCompleted` → `SDKItchManager::fireSnapshotEndEvent(market, partition)` (`glimpseMutex` altında):
   - `completedGlimpsePartitions[market]` kümesine eklenir.
   - `isMarketGlimpseComplete(market)` true ise:
     - `buildMarketSnapshot` ile o pazarın bütün client'larının kitapları `ItchFullSnapshot`'a kopyalanır. Seviyedeki emirler `OrderDepth::getOrdersAtPrice` ile `rankingSeqTime` → `rankingSeqNum` → `orderId` artan sırada dizilir (PR #152 "add order ordering on orderbook snapshot").
     - `snapshotCallbacks[32]` sırayla çağrılır, sonra snapshot serbest bırakılır.
     - Küme temizlenir.
     - `marketLiveReleased[market] = true`, `liveReleaseCv.notify_all()`.

- Snapshot-end callback'leri **son biten partition'ın client thread'inde** ve `glimpseMutex` tutulurken çalışır. HFT bu yüzden ağır yüklemeyi kendi loader thread'ine devreder (`ItchSdkClient::onSnapshotEndCallback`, 2026-08-03 olayı).
- `isMarketGlimpseComplete` her iki pazar için de **sabit {P1, P2, P3, P4}** bekler (§8).

### 6.3 Canlı tampon (`bufferLiveUntilRelease`)

- ⚠ Yeni davranış (2026-10). ❓ doğrulanmadı: master'da var mı.
- Glimpse'i biten her partition, kendi pazarı serbest bırakılana kadar canlı işlemeye geçmez:
  - Main ring boşaltılıp paketler `pendingLiveBytes`'e (tek arena) ve `pendingLive`'a (ofset, uzunluk, iki damga) eklenir.
  - Döngü her turda `waitForMarketLiveRelease(market, 200 µs)` çağırır.
- **Üst sınır** `MAX_PENDING_LIVE_BYTES` = 256 MiB'dir. Dolunca kopyalama durur ve bir kez uyarı loglanır. Ring dolar, RX düşürür, kayıp serbest bırakmadan sonra Rewinder ile kapanır.
- **Flush sırası:**
  - Serbest bırakmadan sonra ana döngü her turda `pendingLive`'dan **bir** paketi FIFO sırayla `processPacket`'e verir. Main ring ancak tampon bitince okunur.
  - Gap ve Rewinder tampon oynatılırken de çalışır. Recovery sırasında tampon bekler.
  - Tampon bitince bellek bırakılır (`swap`).
- Amaç (kod yorumu): erken biten partition, aboneler snapshot'ı alıp bağlanmadan canlı delta işlemesin, hayalet emir/çapraz kitap oluşmasın.
- Not: README'deki "flush'ta emir başına delete" ifadesi bu tampona değil ITCH `FlushOrder` (`Y`) mesajına aittir. `OrderbookInfo::deleteOrderLevels` kitabı boşaltmadan önce her emir için `ORDER_DELETE` ve specific `DELETED` olayı üretir → [mesajlar-ve-emir-defteri.md](mesajlar-ve-emir-defteri.md).

## 7. Kuyruk dolması ve paket düşmesi

- **Backpressure yok.** `spsc_ring_enqueue_with_demux_ts` doluysa false döner. RX `packetsDroppedFull++` sayar ve paketi atar. RX hiçbir zaman beklemez.
- Ring: `RawPacket` slot = 2048 byte veri + `length` + 2×`uint64` damga, 64 hizalı ≈ 2112 byte. 16384 slot ≈ 33 MiB/main ring.
  - Ring'e memcpy, okumada slot'un tamamı (`sizeof(RawPacket)`) kopyalanır.
  - Kapasite kontrolü `write - read >= ring_size`, indeks `& ring_mask`.
- Ring'in okunmadığı zamanlar:
  - Glimpse fazı (§6.1)
  - snapshot-end callback'leri sürerken, son partition'da (§6.2)
  - 256 MiB tampon sınırı aşıldıktan sonra (§6.3)
  - Rewinder recovery (§5)
  - abone callback'i yavaşsa (callback'ler decode thread'indedir)
- Düşen paket sonraki pakette sequence gap'i olarak görülür ve Rewinder'a gidilir. Veri kaybı kalıcı olmaz, gecikme olur.
- Rewinder ring dolarsa yanıt kaybolur (`LOG_ERROR`, `rewinderUnwantedPackets++`). Zaman aşımı sonrası yeniden istenir.
- `ItchClient` ana döngüsünde `pause`/`yield`/sleep yoktur: thread bir çekirdeği %100 kullanır. Kasıtlı (spin), ama sabitleme kapalıysa (HFT bugünkü config'i) paylaşılan çekirdekte döner.

## 8. Partition varsayımları ve `partId` (K-01, ⏸ ertelendi)

**`partId` kuralı** (`createReceiversAndClients`):
- Spot: `partId = partition` (1–4).
- VİOP: `partId = partition + 4` (P1–P4 → 5–8, P5 → 9, P6 → 10).
- `partition < 1` ise 1'e çekilir.
- `partId` yalnız log etiketidir: `ItchClient`/`GlimpseClient` log mesajları ve logger adı `itch.cli.pay.<partId>` / `itch.cli.viop.<partId>`. Pazar ayrı ad alanında olduğu için logger'lar çakışmaz.
- `partId` ile indekslenen bir map veya dizi **yok**. VİOP P5/P6'nın log'larda "partition 9/10" görünmesi yanıltıcıdır, ama veri çakışması üretmez.

6 VİOP partition'lı bir config'de (HFT `Configuration.toml` Future bloğu, bugün `on = false`) 4-partition varsayımı şu yerlerde somut etki yapar:

| Yer | Ne olur |
|-----|---------|
| `isMarketGlimpseComplete` (sabit {P1..P4}) | P1–P4 bitince snapshot-end tetiklenir, küme temizlenir, pazar serbest bırakılır. O anda bitmemiş P5/P6 kitapları snapshot'a girmez. Sonradan bittiklerinde küme {P5} olur, tekrar tetiklenmez, ama serbest bırakma zaten yapıldığı için canlıya geçerler. Snapshot alınırken Glimpse'i süren client'ın `orderbookInfos`'u başka thread'den okunur (veri yarışı). |
| Aynı fonksiyon, **4'ten az** partition | Bir pazarda P1–P4'ün hepsi config'te yoksa snapshot-end hiç tetiklenmez, `marketLiveReleased` hiç true olmaz. O pazarın partition'ları sonsuza dek tamponlar (256 MiB'a kadar, sonra düşürür). `start()` yine başarı döner. |
| `receiverCpuCores[4]` | Spot ve VİOP P1–P4 aynı 4 port'u paylaşınca 4 receiver olur, VİOP P5/P6 port'ları 5. ve 6. receiver'dır ve çekirdek alamaz. |
| `getPartitionIndex` (0–7), `getPortForPartition` (`21001 + p - 1`), `getMarketForPartition` | Yalnız P1–P4 için anlamlıdır. Hiçbir yerden çağrılmazlar (ölü kod). |
| trade-data-app `pkg/itch/itch.go` | `Part` 5/6 → `Partition1` (uyarı log'u). SDK'da aynı pazarda iki "P1" oluşur. Farklı port'taysalar ikisi de çalışır, küme tekilleştirir. → [trade-data-app K-02](../trade-data-app/config.md) |

- AlgorithmicTrading `ItchSdkManager.cpp` yorumu "snapshot-end, pazarın **config'teki** bütün partition'ları bitince tetiklenir" der. Kod config'e bakmaz, sabit P1–P4 bekler.
- Erteleme notu korunur: konu K-01 / K-02 ile birlikte ele alınacak.

## 9. PerfSDK metrikleri ve sayaçlar

`ItchReceiver::initHistograms` şunları yapar:
- `PerformanceClient::start("itch_sdk_recv", "0", 0, 1'000'000, false)` çağırır. Süreç genelinde bir kez çalışır. Aralık yorumu "1 s = 1e6 µs" der.
- Port başına metrik kaydeder. Metrikler yalnız `ENABLE_BENCHMARKS=1` ile çalışır, bu da derlemede `libMAPerfSDK` bulunursa açılır.

| Metrik | Değer | Ölçüldüğü yer |
|--------|-------|---------------|
| `demux_<port>` | ns, `demuxAndEnqueue` süresi (TSC) | RX, her paket |
| `w2d_<port>` | ns, kernel SW RX damgası → demux başı. 0 < değer < 100 ms ise yazılır. XLIO'da yok | RX, her paket |
| `batch_<port>` | adet, recv çağrısı başına paket | RX, her batch |
| `drop_<port>` | adet, ardışık ring-dolu düşme sayısı. Düşmeden sonraki ilk başarılı enqueue'da yazılır | RX |
| `demux2callback_<port>` | ns, `steady_clock` demux anı → callback | `ItchClient` thread'i, `OrderbookInfo` callback'lerinde (`recordDemux2Callback`). Metrik ID thread girişinde `thread_local`'e kopyalanır |

- `idle_<port>` 2026-06-12'deki OOM olayından sonra kaldırıldı. `ItchReceiverHistogramSnapshot.idle_*` alanları API uyumu için 0 döner.
- ⚠ Eski `performance.md` bu metriği hâlâ anlatıyor.

**Sayaçlar** (`ReceiverCounters`, `itch_sdk_get_receiver_metrics(receiverIndex)`):
- `packetsReceived`, `packetsEnqueued`, `packetsDroppedFull`, `packetsUnknownSrc`
- `packetsTruncated` (< 20 byte veya `MSG_TRUNC`)
- `recvErrors`, `zcReleaseErrors` (yalnız XLIO)

Histogram yüzdelikleri `itch_sdk_get_receiver_histogram` ile alınır. Receiver indeksi grup oluşma sırasıdır.

Rewinder/Glimpse sayaçları (`rewinderRequestsSent`, `rewinderResponsesReceived`, `rewinderUnwantedPackets`, `recoveryCount`, `lastRecoveryDurationUs` µs, `lastRecoveryTryCount`) public değildir. Yalnız `ItchClient::stop` log'unda basılır.

Teşhis: `packetsReceived > 0 && packetsEnqueued == 0 && packetsUnknownSrc > 0` → kaynak IP config'i yanlış. Ayrıca log basılmaz.

## 10. Kopma ve yeniden başlama senaryoları

| Senaryo | Davranış | Host'a görünür mü |
|---------|----------|-------------------|
| Tekil UDP kaybı | Gap → Rewinder → kurtarma (§5) | Hayır (log) |
| Uzun kayıp > 65535 mesaj | İstek 65535'e sıkıştırılır, parça parça kapanır | Hayır |
| Rewinder cevap vermiyor / adres yanlış / session boş | Süresiz yeniden deneme (varsayılan 5 s). Partition donar, RX düşürür | Hayır |
| Multicast hattı tamamen susar | Tespit yok (heartbeat zaman aşımı yok). Kitap sessizce bayatlar. İkincil hatta geçiş yok | Hayır |
| Açılışta Glimpse birincil TCP `connect` hatası | Global bayrak `Secondary` olur, ikincile bağlanılır (§4) | Hayır |
| Glimpse login reddi / 3 s login zaman aşımı | Retry'lar etkisiz (Şüpheli 2). Thread çıkar → `start()` `CONNECTION_FAILED` | `start()` dönüşü |
| Glimpse snapshot ortasında kopma (`recv <= 0`) | `stopClient`, baseline 0 → yeni deneme. `OrderBookDirectory` tekrar gelince kitap nesneleri yenilenir | Yalnız tüm denemeler biterse |
| Glimpse sunucusu login sonrası susar | Bloklayıcı `recv`, zaman aşımı yok. `start()` `glimpseStartTimeoutMs` sonunda `cleanup()` | `start()` dönüşü |
| Partition sayısı bir pazarda < 4 (P1–P4 eksik) | Snapshot-end ve canlı serbest bırakma hiç olmaz (§8) | Snapshot-end gelmez |
| Yeni MoldUDP64 session'ı (sequence 1'e döner), süreç yeniden başlatılmadan | Session alanı okunmaz. Bütün paketler `seq < expected` görünür ve süresiz yok sayılır. ❓ doğrulanmadı: BIST gün içi session değiştiriyor mu, servisler her gün yeniden başlatılıyor mu | Hayır |
| `itchsdk_stop()` → `itchsdk_start()` aynı süreçte | Desteklenmez: `stop()` ring/receiver/client listelerini temizlemez, ikinci `start()` bunlara ekleme yapar | ❓ |
| `shutdown()` → `initialize()` → `start()` | `cleanup()` her şeyi sıfırlar. Ancak `findClientForOrderbook`'un `static` önbelleği temizlenmez (Şüpheli 5) | — |
| Süreç yeniden başlatma | Yeni Glimpse, yeni baseline, temiz durum | — |

## Şüpheli

1. **bug? Kurtarılamayan gap partition'ı kalıcı dondurur.** Deneme sınırı, Glimpse'e geri dönüş veya host bildirimi yok. Recovery sürerken main ring okunmaz, bütün canlı veri düşer (`ItchClient::processRewinderQueue`, §5).
2. **bug? Login başarısızlığından sonra Glimpse retry'ları boşa gider.** `GlimpseClient::startClient` login hatasında `disconnect()` çağırmaz, `connected` true kalır. Sonraki denemede `Connected()` true döner, `clientStopped` true olduğu için `parseGlimpseMessages` döngüsü hiç çalışmaz ve deneme anında başarısız olur. Soket de sızar.
3. **bug? İkincil TCP `connect` hatası başarı sayılıyor.** `ITCHTCPConnection::Connect` bayrak zaten `Secondary` iken `connect()` hata verirse dalın dışına düşer, `connected = true` ve `return true` olur. Birincil denemenin soketi kapatılmaz.
4. **bug? Birincil/ikincil bayrağı yarışlı ve tutarsız.** `isPrimaryOrSecondaryVar` atomic değil, birden çok Glimpse thread'i yazar. Rewinder adresi grup grup initialize sırasında okunur. Aynı süreçte bazı partition'lar birincil, bazıları ikincil Rewinder'a gidebilir (§4).
5. **bug? `findClientForOrderbook` `static` önbelleği kilitsiz ve `cleanup()`'ta temizlenmiyor.** Birden çok host thread'i (`getTickSize`, subscribe) eşzamanlı `insert` yapabilir. `shutdown` + yeniden `start` sonrası serbest bırakılmış `ItchClient*` döner.
6. **bug? Tek `glimpseMutex` iki pazara ortak.** Spot snapshot-end callback'leri sürerken Glimpse'i biten bir VİOP partition'ı `fireSnapshotEndEvent`'te bekler. Bu sırada kendi ring'ini boşaltmaz, ring dolar ve Rewinder'a gider. Callback ne kadar uzun sürerse o kadar kayıp olur.
7. **doğrula: Kesik paket sessiz kayıp.** `processPacket` ve `processRewinderQueue` `expected`'ı `messageCount` kadar ilerletip sonra parse eder. Uzunluk tutmazsa döngü `break` olur, eksik mesajlar için gap üretilmez. Rewinder yanıtı 2048 byte'ı aşarsa `drainRewinderSocket` `recv` ile sessizce keser (MSG_TRUNC kontrolü yok).
8. **bug? ZC/XLIO yolunda 2048 byte üstü uzunluk kontrolü yok.** `zcCallback` ve `recvBatchXLIO`, `iov_len`/`buff->len`'i doğrudan `spsc_ring_enqueue_with_demux_ts`'e verir. `memcpy` slot'u taşabilir (eski bug listesi #13, hâlâ var). Ayrıca çok parçalı datagramın her parçası ayrı paket gibi demux edilir.
9. **bug? Ring boyutu 2'nin kuvveti değilse indeksleme bozulur.** `spsc_ring_create` `ring_mask = size - 1` kullanır, `createSPSCQueues` boyutu doğrulamaz.
10. **bug? `rewinderResponsesReceived` çift sayılıyor, `rewinderUnwantedPackets` üç farklı olayı (beklenmedik seq, stale drain, ring taşması) karıştırıyor** (`drainRewinderSocket`, `processRewinderQueue`; eski #3, hâlâ var). Yalnız teşhis etkilenir.
11. **doğrula: Snapshot-end garantisi gecikmeli abonelikleri kapsamaz.** Canlı serbest bırakma, snapshot-end callback'leri döndüğü anda yapılır. HFT abonelikleri loader thread'inde sonradan kurar (`requestStrategyLoadAsync`). Bu abonelikler snapshot ile ilk canlı delta arasındaki olayları görmeyebilir. HFT tarafında header-snapshot ile telafi ediliyor mu, doğrulanmalı.
12. **doğrula: Snapshot alınırken veri yarışı.** `buildMarketSnapshot` başka partition client'larının `orderbookInfos`/`OrderDepth`'ini kilitsiz okur. P1–P4 tamamlandıysa güvenli, ama 6 partition'da P5/P6 hâlâ Glimpse'teyse güvenli değil (§8). `getOrdersAtPrice` her seviye için bütün emir haritasını tarar (seviye × emir).
13. **doğrula: `snapshotCallbacks` 32 slot.** 33. `subscribeSnapshotEnd` bir handle döner ama hiçbir zaman çağrılmaz (`subscribeSnapshotEnd`).
14. **doğrula: Onload preload kontrolü yalnız "boş mu" diye bakıyor.** `LD_PRELOAD` başka bir kütüphaneyle doluysa `execvp` yapılmaz. Onload yüklü değilse `onload_zc_recv` ne döner, sessizce `recvErrors` mı sayar, bilinmiyor. Yorum `ONLOAD_MSG_RECV_OS_INLINE` der, ama `args.flags = 0`. Kernel yolundan gelen paketin akıbeti doğrulanmalı.
15. **doğrula: Bloklayıcı Glimpse `recv`'i `close()` ile açmak.** `ItchClient::stop` → `GlimpseClient::stopClient` başka thread'den `close` çağırır. Linux'ta bu, `recv`'de bekleyen thread'i uyandırmayabilir (`shutdown()` gerekir). `start()` zaman aşımı → `cleanup()` → `join` takılabilir.
16. **doğrula: End-of-session paketi.** MoldUDP64 end-of-session (count 0xFFFF) `seq == expected` ise `expected`'ı 65535 artırır. Gün sonu dışında etkisi yok sayılıyor.
17. **Ölü kod:** `ConnectWithTimeout`, `getPartitionIndex`, `getPortForPartition`, `getMarketForPartition`. Receiver'ın rewinder ring demux'u (HFT config'iyle hiç eşleşmez). Rewinder ring'inin RX tarafında gerçekten üretici olduğu bir config olursa, aynı ring'e `drainRewinderSocket` de yazdığı için SPSC tek-üretici varsayımı bozulur.
