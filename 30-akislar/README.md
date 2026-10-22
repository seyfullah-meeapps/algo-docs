---
kapsam: Uçtan uca senaryolar — piyasa verisinden karara, emrin BIST'e gidişi ve dönüşü, UI'dan strateji başlatma, sabah emri ve handoff, AlgoProd emri, kopma senaryoları
kaynak:
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
dogrulama: 2026-10-22
durum: taslak
---

# Uçtan uca akışlar

Her akış ilgili ayrıntı dokümanına link verir; burada yalnızca sıra ve sınırlar anlatılır.

## 1. ITCH mesajı → HFT strateji kararı → OUCH emri (hot path)

1. BIST ITCH multicast paketi NIC'e gelir. `libMAItchSDK` RX thread'i (Onload/ZC) paketi alır ve SPSC kuyruğa koyar ([itch-sdk](../10-servisler/itch-sdk/README.md)).
2. ItchClient thread'i paketi decode eder ve `OrderbookInfo`'yu günceller. Abone koşulu tutarsa callback çağrılır (header değişti, kademe eşiğin altına indi, execute, momentum).
3. HFT `ItchSdkClient` olayı stratejinin kuyruğuna koyar. Strateji hot ise worker'ın hazır kuyruğuna gider ([hftsrvprod](../10-servisler/hftsrvprod/README.md#thread-modeli)).
4. AlgoWorker thread'i `processSingleEvent()` ile olayı işler, strateji karar verir (ör. [HFT Classic](../20-stratejiler/hft-classic.md) erime, [Tavan](../20-stratejiler/tavan.md) giriş).
5. `maosdk->enterOrder(...)` ile MAOrderSDK hesabın OUCH bağlantılarından birini round-robin seçer. Gerekirse emri böler, encode eder, TCP'ye yazar ([MAOrderSDK](../10-servisler/maordersdk/README.md)).
6. Ölçüm: `ts1` (kuyruğa giriş) … `ts6` (gönderim sonrası) PerfSDK T2T metrikleri ClickHouse'a gider.

**Koşullar:** handoff tamamlanmış, replay bitmiş (`ouchReplayComplete`), header snapshot alınmış ve sürekli işlem seansında olunmalı. Aksi halde emir gitmez veya order-service yedek yolundan gider.

## 2. Emrin dönüşü: OUCH yanıtı → strateji → GUI

1. BIST'ten OUCH Accepted gelir. MAOrderSDK recv thread'i `onAccepted` çağırır.
2. `HftMain.cpp` callback'i:
   - Emri `OrderRegistry`'ye kaydeder; çift accept koruması burada çalışır (`claimGlobalAcceptedToken`).
   - Stratejiyi `unique_key` ile bulur → `strategy->addOrder` + second rule timer'ı.
   - `StrategyServiceImpl` GUI olay kuyruğuna koyar.
3. Execute:
   - Combiner açıksa fill ITCH'ten önce gelir → `onExecuted` → `strategy->executeOrder`.
   - Ham OUCH fill'i `onWireExecuted` ile GUI kuyruğuna gider (emir başına sıra korunur).
4. trade-data-app HFT `FetchOrders` stream'ini okur, emir modeline çevirir ve `/ws/v1/orders/start` aboneleri ile emir defteri işaretlerine dağıtır.
5. UI emir geçmişini ve emir defterindeki "benim emrim" işaretlerini günceller.

## 3. UI'dan strateji başlatma

1. Operatör workspace'te stratejiyi ayarlayıp başlatır. UI tam payload'u gönderir (`Strategy_Start: true` + bütün ayarlar).
2. `POST /v1/setStrategyCommands` → trade-data-app `getApplicationFromStrategyType` ile hedef motoru bulur → HFT veya AlgoProd gRPC `SetCommandRequest`.
3. Motor:
   - `CommandFactory` ile komutu oluşturur.
   - `StrategyManager` stratejiyi bulur veya oluşturur; yeni strateji için varsayılan ayarlar DB'ye yazılır.
   - `strategy->setCommand()` çağrılır, ITCH abonelikleri kurulur.
4. Snapshot `FetchCommands` stream'iyle geri döner → trade-data-app → `/ws/v1/strategy/start` → UI tablosu güncellenir.
5. Aynı stratejiye art arda gelen komutlar koordine edilmez; birbirini ezebilir. Bu bir ürün kararıdır (mtrader-trade-ui `AGENTS.md`).

## 4. Sabah emri ve OUCH handoff

1. Operatör gün içinde (sabah saatinden önce) Toplu Emirler ekranından `OrderType = MORNING` emir girer → `POST /v1/sendOrders` → trade-data-app → order-service gRPC `SendOrder` → DB (`DataService.SetOrders`).
   - Kademeli emirler `LevelCount` ile açılır.
2. order-service sabah thread'i config'teki saatte (ör. 09:40:00.144) emirleri DB'den çeker ve OUCH kullanıcılarına dağıtır. Her kullanıcı ayrı FIFO thread'de aynı anda göndermeye başlar.
3. Seans açılmadan giden emirler `-110023` ile reddedilir; kabul edilene kadar tekrar gönderilir. Kabul edilen ilk emir kuyruk önceliğini alır, fazlalar iptal edilir ([order-service](../10-servisler/order-service/README.md#toplu-emir-akışları)).
4. Sabah emirleri bitince order-service `onlyMorningOrderUser` kullanıcılarından logout olur ve MARpc ile HFT'ye `UserDisconnected` gönderir.
5. HFT `connectUser(OuchUser)` ile login olur ve BIST günün emirlerini replay eder. Replay bitince (`onReplayCompleted`) HFT stratejileri emir göndermeye başlar ([sistem haritası](../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri)).
6. Açılış (10:00), varant açılışı (10:02) ve YİP seansları kendi saatlerinde aynı yoldan gider.

## 5. AlgoProd (arbitraj) emri

1. Arbitraj `doPeriodicChecks` (worker havuzu) eşiği görür. Vadeli emri gider: `OuchManager::send` → ouch-sdk → MARpc → **order-service** → risk kontrolü → MAOrderSDK → BIST.
2. Accept/execute order-service'ten MARpc ile AlgoProd'a döner. Dolan kontrat × çarpan kadar spot emri aynı yoldan gider.
3. Paket trade-data-app `AlgoService.SetArbitrageData` ile DB'ye yazılır. GUI'ye `ArbitragePackageActivity` olarak gider.
4. 🚧 `add-order-sdk` merge edilince AlgoProd da HFT gibi handoff sonrası doğrudan MAOrderSDK kullanacak.

## 6. Kopma ve kurtarma senaryoları

| Olay | Ne olur |
|------|---------|
| ITCH paket boşluğu | itch-sdk Rewinder ile eksik paketleri ister. Açılışta canlı paketler Glimpse snapshot bitene kadar tamponlanır. |
| OUCH bağlantısı koptu (HFT) | MAOrderSDK birincil/ikincil hatta yeniden bağlanır. Yeniden bağlanınca replay yapılır; combiner o emirlerde OUCH'a döner (zehirleme). |
| OUCH bağlantısı koptu (order-service) | `SdkSessionManager` yeniden bağlanmayı planlar. Kasıtlı logout (handoff) bundan muaftır (`markIntendedDown`). |
| Handoff'ta BIST eski oturumu bırakmadı | HFT `connectUser`'ı artan bekleme süreleriyle 4 kez dener. Başaramazsa WARN basar; o kullanıcı için gün boyu doğrudan yol olmaz. |
| Hiç handoff gelmedi | 20 sn sonra replay gate açılır. Emirler order-service yolundan gider. |
| trade-data-app ↔ motor gRPC koptu | trade-data-app yeniden bağlanır. GUI komutları o sırada "service is not connected" hatası alır. |
| UI WebSocket koptu | UI üst sınırı olmayan, jitter'lı geri çekilmeyle yeniden bağlanır. Order socket subscribe olunca bütün emir geçmişi yeniden gelir. Yarı açık bağlantı tespit edilemez (ping/pong yok). |
| Servis yeniden başlatıldı | order-service günün emirlerini DB'den ve replay'den geri yükler. HFT stratejileri `restorePositionState` ile pozisyon bayraklarını düzeltir. AlgoProd stratejileri DB ayarlarından yeniden kurar. |
