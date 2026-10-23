---
kapsam: Hot path uçtan uca — ITCH paketinin NIC'e gelişinden HFT strateji kararına ve MAOrderSDK ile OUCH emrinin TCP'ye yazılmasına kadar; thread'ler, kuyruklar/kopyalar, ön koşullar, emrin gitmediği durumlar, order-service yedek yolu, gecikme ölçüm noktaları
kaynak:
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: performance-sdk
    branch: development
    commit: 6e47f20
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: HftSrvProd
    branch: master
    commit: 052dd96
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-23
durum: taslak
---

# Hot path: ITCH paketi → HFT kararı → OUCH emri

Bu dosya yalnız **sırayı ve sınırları** anlatır. Her adımın iç ayrıntısı linklenen servis dokümanındadır, burada tekrar edilmez. Emrin dönüşü (accept/execute → strateji → GUI): [emir-donusu.md](emir-donusu.md).

Kapsam: HFT içinde, handoff sonrası, SDK yolu (HFT → MAOrderSDK → BIST OUCH). Bütün fiyatlar **raw** (`int32`, TL × 10^`decimal_count`), miktarlar **lot** ([sözlük](../00-genel/sozluk.md)). Yol boyunca hiçbir yerde TL'ye çevrim yapılmaz.

## Sıra diyagramı

```
 NIC (multicast UDP, MoldUDP64)
  │
  ▼  [T1] ItchRx-<port> thread            ItchReceiver::receiverLoop → recvBatch{Posix,ZC,XLIO} → demuxAndEnqueue
  │        kopya #1: payload → SPSC main ring slot (2048 B), receive_ts (kernel SW, REALTIME ns) + demux_ts (steady ns)
  ▼  [T2] ItchClient decode thread         processPacket (seq kontrolü) → parseItchMessage → OrderbookInfo::*Direct
  │        kopya #2: slot → yerel RawPacket;  kitap güncellenir → abonelik callback'leri (aynı thread)
  │        ├─ tiering: onPriceThresholdCrossingCallback → strategy->onPriceThresholdCrossing  (SENKRON, kuyruk yok)
  │        └─ diğerleri: ItchSdkClient::on*Callback → make_unique<Itch*Event> → enqueueStrategyEvent
  │              ├─ realHotReadyQueue && isHot ─► AlgoWorker::hotReadyQueue_   (ts1 = enqueuedAt)
  │              └─ aksi halde               ─► Strategy::itchEventQueue_     (ts1 = enqueuedAt)
  ▼  [T3] AlgoWorker thread (busy-loop)     eventDispatcherLoop → drainHotReady / processSingleEvent   (ts2)
  │        ouchReplayComplete()? ─ hayır ─► olay kuyrukta kalır
  │        try_lock buySellInfoMutex (ts3) → localOrderbook güncelle (ts4) → karar
  │        wrapEnterOrder / satır içi kalıp (ts5) → HftConvert::toSdkMsg
  ▼        MAOrderSDK::enterOrder (AYNI thread, senkron)
  │        yerel kontroller → bölme → pick_connection → send_one: token, maps_mutex, encode_enter_order (114 B)
  │        OuchConnection::send: send_mutex_ → ::send(MSG_NOSIGNAL) / Onload zc
  ▼        enterOrder döner (ts6) → PerfSDK emit
 BIST OUCH (TCP)          false && !ownsAccount ─► OuchManager::enterOrder ─► order-service (yedek yol)
```

## Adımlar

| # | Thread | Kod (repo: dosya → sembol) | Veri / kuyruk | Ayrıntı |
|---|--------|----------------------------|---------------|---------|
| 1 | `ItchRx-<port>` (receiver başına 1) | itch-sdk `Clients/ItchReceiver.cpp` → `receiverLoop`, `recvBatchPosix` / `recvBatchZC` / `recvBatchXLIO`, `demuxAndEnqueue` | Kaynak IP ile Spot/VİOP ring seçimi. Ring doluysa paket **atılır** (`packetsDroppedFull`), backpressure yok. HFT ring boyutu sabit 65536 slot. | [alim-yolu § 1–3, § 7](../10-servisler/itch-sdk/alim-yolu.md#1-bileşenler-threadler-başlatma-sırası) |
| 2 | `ItchClient` decode (partition başına 1, spin) | itch-sdk `Clients/ItchClient.cpp` → `clientThreadMain`, `processPacket`, `handleSequenceGap`; `OrderBook/OrderbookInfo.cpp` → `addOrderDirect` / `executeOrderDirect` / `deleteOrderDirect` | MoldUDP64 sequence; gap'te Rewinder'a gidilir ve recovery bitene kadar main ring **okunmaz**. Tek olayda callback sırası: header snapshot → add/exec/delete → specific-order (combiner) → threshold → header changed → level changed. | [alim-yolu § 3, § 5](../10-servisler/itch-sdk/alim-yolu.md#5-gap-ve-rewinder), [abonelik-api § 3.2](../10-servisler/itch-sdk/abonelik-api.md#32-ortak-kurallar) |
| 3 | aynı decode thread | HftSrvProd `src/Clients/ItchSdkClient.cpp` → `on*Callback` (static), `enqueueStrategyEvent` | Handle → `Strategy*` (`handleToStrategy_`, 65536 slot, lock-free). Filtre: yalnız `strategy->isRunning`. Olay heap'te kurulur (`make_unique`). `LEVEL_CHANGED`/`HEADER_CHANGED` zaman damgası kuralı itch-entegrasyonu § 5'te. | [itch-entegrasyonu § 4–5](../10-servisler/hftsrvprod/itch-entegrasyonu.md#4-olayların-stratejilere-dağıtımı) |
| 3a | aynı decode thread | `onPriceThresholdCrossingCallback` → `strategy->onPriceThresholdCrossing` | Tavan/Taban hot↔cold geçişi **kuyruğa girmez**, ITCH thread'inde senkron çalışır. `false` dönüş SDK'da geçişi reddeder. | [abonelik-api § 6](../10-servisler/itch-sdk/abonelik-api.md#6-tiering--fiyat-eşiği-geçişi-orderbookinfoevaluatepricethresholdcallbacks), [tavan](../20-stratejiler/tavan.md#hotcold-tiering-performans), [taban](../20-stratejiler/taban.md#hotcold-tiering) |
| 4 | aynı decode thread | `AlgoWorker::enqueueHotReady` veya `Strategy::enqueueItchEvent` | Hot-ready yalnız `realHotReadyQueue=Y` (veya env) **ve** `isHot` iken; ≥65536 ise strateji kuyruğuna düşer. Strateji kuyruğu `moodycamel::ConcurrentQueue`, sınır `strategyQueueMaxEvents` (vars. 50000); taşınca **yeni** olay düşer. `enqueuedAt` (ts1) yalnız ilk enqueue'da yazılır. | [strateji-cekirdegi § 3](../10-servisler/hftsrvprod/strateji-cekirdegi.md#hotcold-ve-realhotreadyqueue) |
| 5 | AlgoWorker (`workerCount`; strateji worker'a round-robin, ömür boyu) | `src/Workers/AlgoWorker.cpp` → `eventDispatcherLoop`, `drainHotReady`, `processHotReadyItem`; strateji `processSingleEvent` / `processReadyEvent` | Tur başına strateji başına en çok **bir** olay. `hotWorkerCount > 0` ise önce hot stratejiler. Hot-ready öğesi doğrudan yalnız Tavan/Taban'da işlenir; strateji kuyruğu boş değilse FIFO için kuyruğa eklenir. | [strateji-cekirdegi § AlgoWorker döngüsü](../10-servisler/hftsrvprod/strateji-cekirdegi.md#algoworker-döngüsü-algoworkereventdispatcherloop) |
| 6 | AlgoWorker | `HftClassic::processItchEventTimed`, `HftMaxPrice::processItchEventTimed`, `HftMinPrice::processItchEventTimed` | Strateji kilidi (`buySellInfoMutex`): HftClassic 100 µs `try_lock_for`, alamazsa olayı **işlemeden atar**. `localOrderbook` güncellenir, karar verilir. | [hft-classic](../20-stratejiler/hft-classic.md#tetik-erime), [tavan](../20-stratejiler/tavan.md#giriş-shouldenterposition--header-yolu), [taban](../20-stratejiler/taban.md#giriş-shouldenterposition) |
| 7 | AlgoWorker | `HftClassic.cpp` → `wrapEnterOrder` (anonim namespace); Tavan/Taban/Varant'ta aynı kalıbın satır içi kopyası; `src/Messages/.../MsgConvert` → `HftConvert::toSdkMsg` | `Hft::EnterOrder` → `maordersdk::EnterOrderMsg`: `client_order_id` **boş** (token'ı SDK üretir), passthrough 15 B (`customerInfo`, strateji id, tip, father ref), `price` raw. | [emir-yasam-dongusu § 1–2](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#2-gönderim), [README § Emir gönderme deseni](../10-servisler/hftsrvprod/README.md#emir-gönderme-deseni) |
| 8 | AlgoWorker (SDK'da send thread'i yok) | MAOrderSDK `src/MAOrderSDK.cpp` → `MAOrderSDK::enterOrder`, `Impl::pick_connection` / `round_robin`, `Impl::send_one`; `src/protocol/ouch/OuchCodec.cpp` → `encode_enter_order`; `src/connection/ouch/OuchConnection.cpp` → `send` | Sıra: fiyat/miktar (1005/1006) → limit bloğu (1001–1004, bölme kararı) → FIX mi OUCH mu → bağlantı seçimi → token (havuzdan, kilitsiz) → `maps_mutex` altında haritalara kayıt → encode → `send_mutex_` altında tek `::send`. Kayıt wire'a yazılmadan önce haritadadır. | [emir-akisi § 3–5](../10-servisler/maordersdk/emir-akisi.md#3-enterorder-adım-adım), [ouch-protokolu § 7](../10-servisler/maordersdk/ouch-protokolu.md#7-gönderim-send-send_raw) |

Kilit ve paylaşım özeti: decode thread → AlgoWorker arasında yalnız lock-free kuyruk vardır. AlgoWorker'da strateji kilidi + SDK'nın global `maps_mutex`'i (bütün bağlantılar için tek) + bağlantı başına `send_mutex_` (heartbeat thread'iyle paylaşılır) alınır ([api-ve-yasam-dongusu § 6](../10-servisler/maordersdk/api-ve-yasam-dongusu.md#6-thread-modeli-ve-kilitler-sdk-içi)).

## Ön koşullar

Hepsi sağlanmadan hot path ya hiç çalışmaz ya da olay kuyrukta bekler.

| Koşul | Sağlanmazsa | Kod / ayrıntı |
|-------|-------------|---------------|
| ITCH SDK başladı (bütün partition'larda Glimpse bitti) | `exit(1)`; HFT kalkmaz | [itch-entegrasyonu § 1–2](../10-servisler/hftsrvprod/itch-entegrasyonu.md#2-hazır-olma-koşulu-ve-açılış-zinciri) |
| Pazarın canlı akışı serbest bırakıldı (snapshot-end, sabit P1–P4) | Partition canlı paketleri tamponlar, callback gelmez (K-01) | [alim-yolu § 6.3](../10-servisler/itch-sdk/alim-yolu.md#63-canlı-tampon-bufferliveuntilrelease) |
| Strateji DB'den yüklendi **ve** GUI'den başlatıldı (`Strategy_Start=true` → `setCommand` → abonelikler, `isRunning`) | Abonelik yok veya callback olay üretmez. Restart sonrası stratejiler **durmuş** gelir (K-49). | [strateji-cekirdegi § 4](../10-servisler/hftsrvprod/strateji-cekirdegi.md#4-yaşam-döngüsü-senaryoları) |
| Header snapshot geldi (`headerSnapshotReceived`) | HEADER/LEVEL olayları atlanır. Snapshot kitapta bir sonraki add/exec/delete'te gelir; hareketsiz kitapta hiç gelmez. | [abonelik-api § 3.3](../10-servisler/itch-sdk/abonelik-api.md#33-abonelik-fonksiyonları-ve-callback-argümanları) |
| Replay gate açık (`StrategyManager::isAllOuchReplayComplete`) | `processSingleEvent` dequeue etmez, olaylar kuyrukta birikir; Tavan/Taban hot-ready olayını kuyruğa geri koyar | [strateji-cekirdegi § Replay gate](../10-servisler/hftsrvprod/strateji-cekirdegi.md#replay-gate) |
| Seans / zaman penceresi | Genel bir seans kapısı **yoktur**. HftClassic üç giriş noktasında `continuousSession()` (global durum haritası) bakar; Tavan/Taban komuttaki `startTime`/`stopTime` penceresine olay damgasıyla bakar. Gün içi restart'ta harita `SurekliMuzayede` ile başlar (K-62). | [itch-entegrasyonu § 6](../10-servisler/hftsrvprod/itch-entegrasyonu.md#6-orderbook-durumu-ve-seans) |
| Tavan/Taban için hot olma (tiering açıksa) | Cold stratejinin ITCH callback'leri SDK'da kapalıdır (`setCallbackEnabled(false)`), olay hiç üretilmez | [strateji-cekirdegi § Hot/cold](../10-servisler/hftsrvprod/strateji-cekirdegi.md#hotcold-ve-realhotreadyqueue) |
| Handoff yapıldı (SDK hesabın sahibi) | Emir **gider** ama order-service yedek yolundan; hot path'in son adımı değişir (aşağıda) | [emir-yasam-dongusu § 4](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı) |

Handoff bir ön koşul değil, **yol seçicidir**. Tipik günde HFT 09:40'tan önce açılır, 20 sn watchdog gate'i açar, stratejiler order-service yolundan çalışır. Handoff gelince gate kapanır, replay bitince açılır ve emirler SDK yolundan gider ([emir-yasam-dongusu § Replay gate](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#replay-gate-strategymanager)).

## Emrin gitmediği / yolun değiştiği durumlar

| Nerede | Durum | Sonuç |
|--------|-------|-------|
| RX | Ring dolu | Paket düşer → sonraki pakette gap → Rewinder. Kurtarma başarılıysa eksik veri tamamlanır; başarısızsa partition donabilir (K-127). |
| Decode | Kurtarılamayan gap | Partition süresiz donar, HFT'ye bildirim yok (K-127) |
| HFT callback | Handle ≥ 65536, strateji kayıtlı değil, `!isRunning` | Olay sessizce üretilmez (K-54) |
| Strateji kuyruğu | `strategyQueueMaxEvents` aşıldı | Yeni olay düşer; sayaç log'lanmaz (K-68) |
| Hot-ready | Generation farklı / strateji durdu | Olay atılır (`hotReadyStale_`) |
| Karar | HftClassic kilidi 100 µs'de alınamadı | Olay işlenmeden atılır |
| Karar | `sent` / `chaseSent` kilidi (tek emir kuralı) | Yeni emir üretilmez | 
| SDK | Yerel ret 1001–1006 (bağlantı kontrolünden **önce**) | Senkron `onRejected` (AlgoWorker thread'inde). Hesabın SDK sahibi yoksa emir **ayrıca** order-service'e gider (K-56). |
| SDK | Bölünmeyen emirde bağlı connection yok | `onSdkError(1)` + `false`, ret yok → `ownsAccount` false → order-service yolu |
| SDK | Bağlantı var, encode/send/duplicate hatası (4/5/6/15) | `false` + `onRejected`; `ownsAccount` true → **hiçbir yoldan gitmez** |
| SDK | Bölünen emirde kısmi başarı | `false` döner ama giden çocuklar canlıdır; `ownsAccount` true olduğu için yedek yola gidilmez |
| SDK | Hesap OUCH+FIX havuzunda, OUCH kopuk FIX logon'lu | `ownsAccount` true, OUCH seçilir, `onSdkError(1)`; emir sessizce düşer (K-108) |

Tam kod tabloları: [emir-akisi § 4](../10-servisler/maordersdk/emir-akisi.md#4-yerel-retler-ve-hatalar), [emir-yasam-dongusu § Yol seçimi](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#yol-seçimi).

## Yedek yol (order-service)

Koşul: `!maosdk || (!maosdk->enterOrder(...) && !maosdk->ownsAccount(account))`. Yani handoff öncesi, OUCH kopmuş hesap, ya da FIX kanallı GUI emri.

```
AlgoWorker ─► OuchManager::enterOrder (WARN "-> order-service (no SDK OUCH for account …)", ouchSDKCallMutex)
          ─► ouch-sdk ─► MARpc TCP :8000 ─► order-service OrderServer::RequestReceived
          ─► OrderDispatcher::SendOrder ─► risk_manager->checkEnterOrder ─► MAOSdkManager::SendOrderAsync (senkron)
          ─► order-service'in kendi MAOrderSDK'sı (bölme, token, encode) ─► BIST
```

- Hot path'e göre farklar: ek süreç atlaması ve TCP/MARpc turu, order-service'te risk kontrolü ve DB yazımı (`STRATEGY` satırı, async), token'ı order-service'in SDK'sı üretir. HFT'nin `OuchManager` token havuzu wire'a çıkmaz.
- `getAllOrders` sürerken `ouchSDKCallMutex` tutulur; bu sürede yedek yoldan emir bloklanır (emir-yasam-dongusu Şüpheli 6).
- order-service'e ulaşılamıyorsa kopma bir gönderim başarısız olunca görülür; reconnect yoktur (K-151).
- Ayrıntı: [order-service/arayuzler § 6.2](../10-servisler/order-service/arayuzler.md#62-enter-girişten-biste), [ouch-sdk § 3](../10-servisler/ouch-sdk/README.md#3-public-api-includeorderstreamclienth). Dönüşü: [emir-donusu § 7](emir-donusu.md#7-order-service-yedek-yolundan-giden-emrin-dönüşü).

## Gecikme ölçüm noktaları

Üç ayrı PerfSDK metrik ailesi vardır. Ortak bir korelasyon kimliği yoktur: wire-to-wire tek histogramdan okunamaz.

| Bölüm | Metrik | Başlangıç → bitiş | Saat | Kod |
|-------|--------|-------------------|------|-----|
| Ağ → demux | `w2d_<port>` | kernel SW RX damgası → demux başı (XLIO'da yok) | REALTIME ns | itch-sdk `ItchReceiver::initHistograms` |
| Demux | `demux_<port>` | `demuxAndEnqueue` süresi | TSC ns | aynı |
| Demux → callback | `demux2callback_<port>` | demux anı → `OrderbookInfo` callback'i | steady ns | `recordDemux2Callback` |
| ts1 → ts2 | `<p>_t2t_ingest` | `enqueuedAt` (ilk enqueue) → worker dequeue | steady ns | HftSrvProd `src/Performance/PerfSdkSession.h` → `emit` |
| ts2 → ts3 | `<p>_t2t_lock` | dequeue → strateji kilidi alındı | | |
| ts3 → ts4 | `<p>_t2t_book` | kilit → yerel kitap güncellendi | | |
| ts4 → ts5 | `<p>_t2t_decide` | kitap → `enterOrder` çağrısı öncesi | | |
| ts5 → ts6 | `<p>_t2t_send` | `enterOrder` (+ gerekirse yedek yol) dönüşü | | `wrapEnterOrder` |
| ts1 → ts6 | `<p>_t2t_total` | toplam | | |
| SDK enter | `maordersdk_enter_{tokenmap,encode,send,order,rtt}_ns__<user>`, `maordersdk_enter_route_ns` | SDK içi aşamalar; `rtt` = gönderim → cevap | ns | MAOrderSDK `src/perf/ConnPerf.h` |

- `<p>` = `hft_classic`, `hft_maxprice`, `hft_minprice`. Teorik, Varant ve Varant Toplu T2T ölçmez.
- `emit` yalnız emir gönderilen olayda çağrılır; emir üretmeyen olaylar örneklenmez. Tavan/Taban'da ts3/ts4 emir fonksiyonunun içinde, 0 ise yazılır (`openPosition` vb.).
- ts1 gate kapalıyken kuyrukta geçen süreyi de içerir; replay sonrası ilk örnekler şişkin görünür.
- Kod yorumu ts5/ts6'yı "`OuchManager::enterOrder` öncesi/sonrası" diye anlatır; gerçekte `maosdk->enterOrder` (ve yedek yol) çevrelenir.
- Histogramlar `monitoringEnabled` ve ClickHouse exporter'ı ayarlıysa dışarı çıkar; Prometheus yok ([performance-sdk](../10-servisler/performance-sdk/README.md)).
- Accept mesajındaki `latency_writing_ns` / `latency_network_ns` / `latency_bist_ns` gönderim sonrası yarıyı ölçer; GUI'ye gider ([emir-donusu](emir-donusu.md)).

## Şüpheli

- **bug? Hot path'te her olayda WARN log'u.** `HftClassic::processItchEventTimed` kilidi aldıktan hemen sonra koşulsuz `LOG_WARN_U("{}", sent)` basıyor (bir debug kalıntısı gibi görünüyor). İşlenen her ITCH olayında AlgoWorker thread'inde format + log kuyruğu maliyeti var, log dosyası olay sayısıyla büyüyor. `master`'da da var (2026-10-23).
- **bug? Combiner açıkken ITCH decode thread'i strateji kilidinde bekleyebilir.** Combiner fill'i `onExecuted`'u ITCH client thread'inden çağırır; HFT callback'i `strategy->executeOrder`'ı doğrudan çağırır ve HftClassic/Tavan/Taban/Teorik bu metotta `buySellInfoMutex`'i **bloklayan** `lock_guard` ile alır. AlgoWorker kilidi karar + `enterOrder` süresince tuttuğu için o partition'ın decode thread'i (ve o partition'daki bütün stratejilerin olayları) bekler; uzun beklemede ring dolar, Rewinder'a gidilir. `combinerEnabled` repo örneğinde ve bir müşteri config'inde açık (Algo-Setup `development`, 2026-10-23). Kod: HftSrvProd `src/Main/HftMain.cpp` `cbs.onExecuted`, `HftClassic::executeOrder`.
- **performans? ITCH thread'inde olay başına heap allocation.** `ItchSdkClient::on*Callback` her olay için `std::make_unique<Itch*Event>` yapıyor; kuyruk `unique_ptr` taşıyor. [Sistem haritası](../00-genel/sistem-haritasi.md#performans-prensipleri-tüm-c-kodu-için) hot path'te allocation istemiyor.
