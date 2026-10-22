---
kapsam: MARpc istemci ve sunucu yaşam döngüsü, login ve heartbeat, kopma ve yeniden bağlanma, thread modeli, callback thread'leri, sıralama, backpressure, kapanış
kaynak:
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
dogrulama: 2026-10-22
durum: taslak
---

# MARpc bağlantı ve thread modeli

İndeks: [README.md](README.md). Çerçeve ve şema: [wire-protokolu.md](wire-protokolu.md). order-service'in sunucu callback'lerinde ne yaptığı: [order-service/arayuzler § 3](../order-service/arayuzler.md#3-marpc-sunucusu-orderserver), [§ 7](../order-service/arayuzler.md#7-thread-ve-kilit-modeli). İstemci host'u: [ouch-sdk](../ouch-sdk/README.md).

## 1. İstemci yaşam döngüsü

Public API `Public/MAOrderClient.h`, uygulama `Client/MAOrderClient.cpp` → `Client/MATCPClient.*`. Process başına **tek** istemci vardır: global `MATCPClientPtr tcpClient`.

| Çağrı | Ne yapar |
|-------|----------|
| `startOrderClient(ip, port)` | `tcpClient = make_shared<MATCPClient>()` (constructor heartbeat çerçevesini önbelleğe alır) → `connectToServer` |
| `setResponseDelegate(cb)` | `callback = cb` (kilitsiz atama). Delegate yokken gelen yanıt sessizce atılır. |
| `sendOrderRequest(req)` | `MATCPClient::sendMessage(BaseRequest*)`: `builderMutex` spin `try_lock` → encode → `sendingMessageList.enqueue`. Ağa yazmaz, hata döndürmez (`void`). |
| `closeClientConnection()` | `CLOSE_MSG` çerçevesini kuyruğa koyar ([wire § 2.1](wire-protokolu.md#21-close_msg)). Thread'leri durdurmaz (§ 7). |

`MATCPClient::connectToServer`:
1. `ip` tam olarak `"localhost"` ise (`UNIX_SOCKET_ADDR`) `AF_UNIX` kullanılır ve `/workingDirectory/sock/mysocket`'e (`UNIX_SOCKET_PATH`) bağlanılır. Diğer her değerde `AF_INET` + `inet_pton` kullanılır, yani **yalnız IPv4 noktalı adres** kabul edilir. Hostname ve IPv6 kabul edilmez. `"127.0.0.1"` TCP'ye gider.
2. Bloklu `connect`. Ardından `O_NONBLOCK`; TCP'de `TCP_NODELAY` set edilir.
3. `isRunning = true` → üç thread açılır ve **detach** edilir (§ 5.1).

Herhangi bir adım başarısız olursa fonksiyon **sessizce `return` eder**: hata kodu yoktur, socket fd kapatılmaz, thread açılmaz. Sonraki `sendOrderRequest`'ler kuyrukta birikir ve hiç gönderilmez. ouch-sdk `login()` `LoginResponse` promise'ini **süresiz** bekler. Bu yüzden order-service'e ulaşılamazsa HFT ve AlgoProd açılışta takılır; exception atmaz. HFT `OuchManager` constructor'ındaki exception yalnız 401/403 yanıtında atılır.

## 2. Sunucu yaşam döngüsü

Public API `Public/MAOrderServer.h`, uygulama `Server/MAOrderServer.cpp` → `Server/MATCPServer.*`. Global tek `MATCPServerPtr tcpServer` vardır.

| Çağrı | Ne yapar |
|-------|----------|
| `startOrderServer(port)` | `tcpServer = make_shared<MATCPServer>()` → `startServer(port)` |
| `setRequestDelegate(cb)` | İstek callback'i. `startOrderServer`'dan **sonra** çağrılmalıdır (`tcpServer` önce null). Arada gelen istek atılır. |
| `setConnectionClosedDelegate(cb)` | Kapanış callback'i (`connectionId` = fd) |
| `setOrderResponse(resp, connId)` | Herhangi bir thread'den çağrılabilir. `responseMtx` altında encode → `sendingMessageList[connId].enqueue` (§ 6, § 8) |
| `setPerformanceSDK(ptr, enabled)` | MAPerfSDK metrikleri (`network-*`). order-service çağırmaz. |

`MATCPServer::startServer` sırası:
1. Unix soket yolu `unlink` edilir.
2. `getaddrinfo(nullptr, port, AF_UNSPEC, AI_PASSIVE)`. Hata olursa **`exit(1)`**. Dönen ilk adres kullanılır, yani bind tüm arayüzlerdir. ❓ doğrulanmadı: ilk adresin IPv4 `0.0.0.0` mı IPv6 `::` mı olduğu. İstemci IPv4 bağlandığı için iki durumda da çalışır (dual-stack varsayımı).
3. TCP ve Unix socket'leri açılır. Sonra `bind(TCP)` ve `bind(Unix)` yapılır. **Ardından** `SO_REUSEADDR` ve `TCP_NODELAY` (dinleyen socket'e) ile `O_NONBLOCK` (yalnız TCP dinleyicisine) set edilir. Son olarak `listen(…, 10)` çağrılır.
4. Hata olursa `perror` + `return` (host'a hata dönmez). Unix soket `bind`'ı TCP `listen`'dan **önce** geldiği için `/workingDirectory/sock/` dizini yoksa **TCP portu da dinlenmez**. Bu durumda log'da `[Server] Started Listening` satırı çıkmaz ([40-operasyon](../../40-operasyon/README.md)).
5. `acceptTask` (TCP), `acceptLocalTask` (Unix) ve `timerTask` (heartbeat watchdog) açılır, hepsi detach edilir.

`SO_REUSEADDR` `bind`'dan sonra set edildiği için bind'ı etkilemez. Sunucu kapattığı bağlantılarda `TIME_WAIT` socket'leri bırakır. Restart bu socket'ler yaşarken olursa `bind` `EADDRINUSE` ile başarısız olabilir. ❓ doğrulanmadı: canlıda görüldüğü. ⚠ Eski bilgi tabanı setsockopt'u bind'dan önce gösteriyordu.

### 2.1 Accept ve bağlantı sınırı (`MATCPServer::acceptClient`)

- Her dinleyici kendi `ThreadPool(MAX_ALLOWED_CONNECTION * 2 = 10)`'unu kurar. Toplamda 2 × 10 worker thread açılıştan itibaren bekler.
- TCP dinleyicisi non-blocking olduğu için `accept` `EAGAIN` ile döner ve döngü **busy-spin** yapar (bir çekirdek). Unix dinleyicisi bloklu `accept` kullanır. `accept < 0` her durumda `continue` ile geçilir (`EBADF` dahil).
- Sınır: global `connectionCount`, TCP ve Unix toplamında `MAX_ALLOWED_CONNECTION = 5`. Sınıra ulaşılmışsa accept edilen fd **kapatılmaz ve işlenmez**: istemci bağlı sanır, login yanıtı hiç gelmez. Kontrol ve artırma ayrı kilit bölgelerindedir; iki dinleyici aynı anda 6. bağlantıyı kabul edebilir.
- Kabul edilen bağlantı: TCP'de `TCP_NODELAY` set edilir; başarısız olursa **`return`** ile accept thread'i kalıcı olarak biter. Ardından `O_NONBLOCK`, `isRunning[fd] = true`, `heartbeatMap[fd] = now` yazılır. Havuza `receiveMessage(fd)` ve `processCallback(fd)` verilir, `connectionCount++` yapılır.
- **Bağlantı kimliği = fd.** Kapanan fd'yi kernel yeniden verebilir (§ 8).

## 3. Login ve heartbeat

### 3.1 Login

SDK login'i **zorlamaz** ve doğrulamaz. `LoginRequest` sıradan bir istek tipidir. `authToken` her `RequestHolder`'da taşınır ve sunucu SDK'sı ona bakmaz. Yetki kontrolü host'tadır (order-service `AuthenticationService::ValidateToken`, [arayuzler § 3.2](../order-service/arayuzler.md#32-istek-tipleri)). Login'den önce gönderilen istek de host callback'ine ulaşır.

### 3.2 Heartbeat

| Yön | Var mı | Kod |
|-----|--------|-----|
| İstemci → sunucu | Evet, ~3 sn | `MATCPClient::sendHeartbeatMessage` (`timerTask`) |
| Sunucu → istemci | **Yok** | — |
| TCP `SO_KEEPALIVE` | Yok (iki taraf) | — |

- İstemci: `isRunning` true iken `getCurrentTimestampSeconds()` farkı ≥ 3 olunca önbellekteki heartbeat çerçevesi kuyruğa girer. Zaman saniye çözünürlüğünde ölçülür, gerçek aralık ~2–3 sn'dir. Döngü `std::this_thread::yield()` ile busy-spin yapar.
- Sunucu: heartbeat çerçevesi `processCallback`'te `heartbeatMap[fd] = now (ms)` olarak işlenir. Diğer istekler zamanı **yenilemez**.
- Watchdog (`MATCPServer::checkHeartbeatMessages`, `timerTask`): sonsuz döngüdür. `heartbeatLock.try_lock()` alınırsa her kayıt için `now - last > CONNECTION_TIMEOUT_MS (15000)` kontrol edilir. Aşılmışsa `isRunning[fd] = false` yapılır ve kayıt silinir. Kilit alınamazsa beklemez. Her turda `yield` çağrılır (busy-spin).
- Sonuç: istemci heartbeat'i kesilirse (process donması, ağ kesilmesi) sunucu bağlantıyı **15 sn** sonra kapatır.

## 4. Kopma tespiti ve yeniden bağlanma

### 4.1 Recv döngüsünün kopma koşulu

İki taraf da aynı kalıbı kullanır (`MATCPClient::receiveMessage`, `MATCPServer::receiveMessage`):

```
do {
  r = recv(fd, buf, 4096, 0)            // non-blocking
  if (errno ∉ {EWOULDBLOCK, EAGAIN, 0}) → kopma
  kuyrukta gönderilecek varsa 1 tanesini gönder
  if (r > 0) parse kuyruğuna koy
} while (errno ∈ {EWOULDBLOCK, EAGAIN, 0} [&& isRunning[fd]  ← yalnız sunucu])
```

- `errno` sıfırlanmaz, son hatayı taşır. Başarılı `recv` `errno`'yu değiştirmez.
- **`recv() == 0` (karşı taraf FIN gönderdi) kopma sayılmaz.** `errno` değişmediği için döngü boş dönmeye devam eder.
- Kopma ancak bir **gönderim** başarısız olduğunda (`EPIPE`, `ECONNRESET`, bir sonraki turda `errno` kontrolünde) veya `recv` `-1` + `ECONNRESET` döndüğünde (karşıdan RST gelmişse) anlaşılır. Sunucuda bunlara ek olarak watchdog / `CLOSE_MSG` ile `isRunning=false` da kopma sayılır.

⚠ Eski bilgi tabanı "server crash olursa client `recv()` 0 döner (FIN) ya da errno" diyordu. development'ta `recv()==0` işlenmez. Kopma ancak sonraki gönderim hatasıyla anlaşılır.

### 4.2 Senaryolar

| Olay | İstemci (HFT/AlgoProd) | Sunucu (order-service) |
|------|-------------------------|------------------------|
| order-service process'i öldü / restart | FIN/RST gelir. İlk heartbeat gönderimi genelde başarılıdır, ikincisi `EPIPE` alır (ya da RST sonrası `recv` hata döner). ~3–6 sn içinde `receiveMessage` çıkar. **Host'a bildirim yok.** | — |
| İstemci process'i öldü | — | `recv()==0` görmezden gelinir. Bekleyen bir yanıt gönderimi hata verirse hemen, vermezse watchdog ile **15 sn** sonra kapanır → `close_protocol`. |
| Ağ kesildi (RST/FIN yok) | Gönderimler kernel tamponuna yazılır, hata dönmez. Hata ancak TCP yeniden iletim zaman aşımında gelir (Linux varsayılanı `tcp_retries2`, ~15 dk). ❓ doğrulanmadı: canlı ayarlar. | 15 sn watchdog |
| İstemci `closeClientConnection()` | § 7 | `CLOSE_MSG` → hemen kapanır |
| 6. bağlantı | Bağlı görünür, login yanıtı gelmez (§ 2.1) | İşlenmez |

### 4.3 İstemci kopunca

- `receiveMessage` çıkar ve `isRunning = false` olur. Heartbeat thread'i biter. `processCallback` thread'i **`while(true)` ile sonsuza kadar** boş döner.
- Host'a callback, durum sorgusu ya da hata kodu **yoktur**. `isRunning` private'tır. Sonraki `sendOrderRequest` çağrıları kuyruğa girer, hiç gönderilmez, hata da dönmez: **sessiz kayıp**.
- ouch-sdk de kopmayı izlemez ([ouch-sdk](../ouch-sdk/README.md)). HFT tarafındaki etkisi: [hftsrvprod/emir-yasam-dongusu § 6](../hftsrvprod/emir-yasam-dongusu.md#6-kopma-senaryoları).

### 4.4 Yeniden bağlanma

**Yoktur** (ne network-sdk'da ne ouch-sdk'da). `startOrderClient` ikinci kez çağrılırsa global `tcpClient` değişir. Eski `MATCPClient` yok edilir ama detach edilmiş thread'leri eski `this` üzerinden çalışmaya devam eder: use-after-free. Destructor `join` çağırmaz, çünkü detach sonrası `joinable()` false'tur. HFT ve AlgoProd `startOuchStreaming`'i bir kez çağırır. Yeniden bağlanmanın tek yolu **process restart**'tır. Yeniden bağlanan istemci login olur ve `getAllOrders` ile günün olaylarını çeker ([arayuzler § 3.9](../order-service/arayuzler.md#39-istemci-kopunca)).

## 5. Thread modeli

### 5.1 İstemci (3 detached thread, process başına)

| Thread | Fonksiyon | İş | Bekleme biçimi |
|--------|-----------|----|----------------|
| `receiveTask` | `MATCPClient::receiveMessage` | `recv` + gönderim kuyruğundan **tur başına 1 çerçeve** `send` | Busy-spin (non-blocking recv, her turda 4096 baytlık `std::string` ayrılır) |
| `callbackTask` | `MATCPClient::processCallback` | Parse → decode → **`response_protocol` callback** → `clearOwnership` | Busy-spin `try_dequeue`. Hiç bitmez. |
| `timerTask` | `MATCPClient::sendHeartbeatMessage` | ~3 sn'de bir heartbeat kuyruğa | `yield` spin |

- **Bütün yanıt callback'leri tek thread'de, `callbackTask`'ta** çalışır; recv thread'inde çalışmaz. ouch-sdk `handleIncomingMessage` ve oradan çağrılan `ouchSDK::orderAccepted` / `orderUserDisconnected` vb. bu thread'dedir.
- Callback bloklanırsa bütün yanıtlar durur. Recv thread'i okumaya devam eder ve parse kuyruğu sınırsız büyür.
- **Deadlock kuralı:** Callback içinden yanıt bekleyen senkron bir çağrı yapılmamalıdır. ouch-sdk `login`, `getAllOrders`, `getStrategyInfo` ve `insertStrategyInfo` promise bekler. Beklenen yanıtı yalnız bu thread teslim edebileceği için callback içinden çağrılırlarsa sonsuz bekleme olur.
- `sendOrderRequest` herhangi bir thread'den çağrılabilir (`builderMutex`). Çağıran yalnız encode + enqueue süresince bekler.

### 5.2 Sunucu

| Thread | Sayı | Fonksiyon | Callback |
|--------|------|-----------|----------|
| TCP accept | 1 | `acceptClient(listenfd, false)` | — |
| Unix accept | 1 | `acceptClient(listenfdLocal, true)` | — |
| Watchdog | 1 | `checkHeartbeatMessages` | — |
| Bağlantı recv/send | bağlantı başına 1 (havuzdan) | `receiveMessage(fd)` | **`close_protocol(fd)`**, kapanışın sonunda |
| Bağlantı parse | bağlantı başına 1 (havuzdan) | `processCallback(fd)` | **`request_protocol(req)`**, senkron |
| Havuz worker'ları | 2 × 10 (sabit) | `ThreadPool` | Yukarıdaki iki görevi taşır |

- Bir bağlantının istekleri **tek thread'de sırayla** işlenir. Farklı bağlantıların callback'leri **paralel** çalışır, bu yüzden host callback'i thread-safe olmalıdır.
- Callback'in süresi o bağlantının bütün isteklerini bekletir. order-service Enter'da risk + MAOrderSDK gönderimini, AccountStrategy SET'te trade-data-app gRPC çağrısını bu thread'de yapar ([arayuzler § 7](../order-service/arayuzler.md#7-thread-ve-kilit-modeli)). Bu sürede gelen veri parse kuyruğunda birikir. Heartbeat de bu kuyrukta beklediği için callback 15 sn'den uzun sürerse watchdog bağlantıyı düşürür.
- `setOrderResponse` hangi thread'den çağrılırsa encode orada yapılır. Gönderimi o bağlantının `receiveMessage` thread'i yapar.
- Bütün döngüler busy-spin'dir. Boştayken bile yaklaşık şu kadar çekirdek dönüşte kalır: TCP accept 1, watchdog 1 (`yield`), bağlantı başına 2. ❓ doğrulanmadı: canlı CPU tüketimi ve Onload etkileşimi.

### 5.3 Paylaşılan durum ve kilitler (sunucu)

| Durum | Tip | Kilit |
|-------|-----|-------|
| `isRunning` | `std::map<int,bool>` | Yazma `isRunningLock` (shared_mutex) altında. Okuma (`find(fd)->second`) **kilitsiz**. |
| `heartbeatMap` | `std::map<int,ull>` | `heartbeatLock` |
| `sendingMessageList`, `parseDataQueue` | `std::map<int, ConcurrentQueue>` | **Yok.** `operator[]` farklı thread'lerden eleman ekleyebilir (ilk erişimde). |
| `connectionCount` | global int | global `connectionCountLock` (elle lock/unlock) |
| `MAHelper` builder | singleton | Sunucuda `responseMtx`, istemcide `builderMutex`. İkisi farklı kilittir; client ve server aynı process'te olursa yarışırlar. Mevcut kullanımda böyle bir process yok: order-service yalnız sunucu, HFT ve AlgoProd yalnız istemci. |

## 6. Sıralama garantisi

- **İstek yönü (istemci → sunucu):** `sendingMessageList` moodycamel `ConcurrentQueue`'dur. Bu kuyruk yalnız **aynı üretici thread** için FIFO'dur; farklı thread'lerden konan öğeler arasında sıra garanti değildir. Tek thread'den gönderilen istekler sırayla gider. Strateji thread'lerinden paralel gönderilen istekler ve heartbeat birbirine göre karışabilir. TCP ve sunucunun tek parse thread'i alınan sırayı korur.
- **Yanıt yönü (sunucu → istemci):** `setOrderResponse` `responseMtx` altında enqueue eder. Enqueue sırası tekildir ama dequeue yine moodycamel üretici-başına FIFO kuralına bağlıdır. order-service olayları birden çok thread'den gönderir: Login yanıtı bağlantının parse thread'inden, AllOrders ve AccountStrategy GET detached thread'lerden, emir olayları MAOrderSDK callback thread'lerinden gelir. **Farklı thread'lerden gelen olayların wire sırası garanti değildir.** Örnek: `OrderExecuted` ile `OrderAccepted` farklı thread'lerden gelirse yer değiştirebilir; aynı şey AllOrders yanıtı ile canlı olaylar arasında da olabilir. Gönderici thread kuyruğu hızlı boşalttığı için pratikte nadir olmalıdır. ❓ doğrulanmadı: canlıda gözlendiği.
- **Callback yönü:** istemcide tek callback thread'i vardır, wire sırası korunur. Sunucuda bağlantı içi sıra korunur, bağlantılar arası sıra yoktur.

## 7. Kapanış

### 7.1 İstemci `closeClientConnection()`

1. `CLOSE_MSG` kuyruğa girer. Önündeki çerçevelerle sırası yalnız aynı thread'den konmuşlarsa korunur (§ 6).
2. Sunucu `"C"`'yi görünce (tamponun ilk çerçevesiyse, [wire § 2.1](wire-protokolu.md#21-close_msg)) `isRunning[fd] = false` yapar. Aynı tampondaki sonraki çerçeveler atılır. `receiveMessage` çıkar → `close(fd)` → `close_protocol`.
3. İstemci tarafında `isRunning` true kalır. Thread'ler ancak sonraki gönderim hata verince durur (§ 4.1). `callbackTask` hiç durmaz. `tcpClient` serbest bırakılmaz.

HFT (`HftMain`) ve AlgoProd (`Application`, `~OuchManager`) kapanışta `ouchSDK::stopOuchStreaming()` → `closeClientConnection()` çağırır. Process çıkışı detach edilmiş thread'leri keser.

### 7.2 Sunucu bağlantı kapanışı (`MATCPServer::receiveMessage` sonu)

Sıra: `close(fd)` → `isRunning[fd] = false` → `heartbeatMap.erase(fd)` → `connectionCount--` → `close_protocol(fd)`. Parse thread'i `isRunning` false görünce çıkar. Henüz işlenmemiş parse kuyruğu ve gönderilmemiş yanıtlar **map'te kalır** (§ 8).

### 7.3 Sunucunun kendisi

Durdurma API'si yoktur. Thread'ler detach edilmiştir, destructor'daki `join`'ler çalışmaz (`joinable()` false). `startOrderServer` ikinci kez çağrılırsa Unix soketi `unlink` edilir, port bind'ı başarısız olur, eski nesne yok edilir ve thread'leri serbest bırakılmış belleği kullanır. Kapanış = process çıkışı.

## 8. Backpressure ve fd yeniden kullanımı

- **Backpressure yok.** `sendingMessageList` ve `parseDataQueue` sınırsızdır. `sendOrderRequest` / `setOrderResponse` hiçbir zaman bloklamaz ve reddetmez. Yavaş tüketici bellek büyümesine yol açar.
- Gönderim, recv thread'inde tur başına bir çerçevedir. `send` `EAGAIN` alırsa aynı yerde döner; bu sürede o bağlantıda `recv` yapılmaz. İki tarafın da çekirdek tamponu dolarsa ve ikisi de aynı anda gönderimde dönerse kimse okumadığı için **karşılıklı kilitlenme** olur. ❓ doğrulanmadı: büyük `AllOrdersResponse` ile eşzamanlı yoğun istek altında oluşup oluşmadığı.
- **fd yeniden kullanımı:**
  - Kapanan bağlantının `sendingMessageList[fd]` ve `parseDataQueue[fd]` kuyrukları silinmez.
  - `setOrderResponse` kapanmış bir `connId` için de kuyruğa yazar. order-service'te emir olayları `GetUserConnections` ile yönlendirilir ve `RemoveConnection` kapanan fd'yi bu listeden çıkarır. Ancak `connectionId`'yi önceden almış detached thread'ler (AllOrders, AccountStrategy GET) kapanıştan sonra da yazabilir.
  - Kernel aynı fd numarasını yeni bağlantıya verirse eski yanıtlar **yeni bağlantıya gider**. Eski parse kuyruğundaki yarım çerçeve de yeni bağlantının akışını kaydırabilir.
  - `close(fd)` temizlikten önce yapılır. Bu yüzden aradaki pencerede accept edilen yeni bağlantının `isRunning[fd]`'i eski thread tarafından `false`'a çekilebilir ve `heartbeatMap` kaydı silinebilir. Gecikmeli `close_protocol(fd)` da order-service'te yeni bağlantıyı kullanıcı listesinden çıkarabilir.

## 9. Soket seçenekleri özeti

| Seçenek | İstemci | Sunucu dinleyici | Sunucu bağlantı |
|---------|---------|------------------|-----------------|
| `TCP_NODELAY` | TCP'de evet | evet | TCP'de evet |
| `O_NONBLOCK` | evet | yalnız TCP | evet |
| `SO_REUSEADDR` | — | bind'dan sonra (etkisiz) | — |
| `MSG_NOSIGNAL` | her `send` | — | her `send` |
| `SO_KEEPALIVE`, `SO_RCVBUF`/`SO_SNDBUF`, `TCP_QUICKACK` | yok | yok | yok |
| `listen` backlog | — | 10 | — |

## Şüpheli

"bug?" = koddan çıkarım, canlıda doğrulanmadı.

1. **bug?** Watchdog: zaman aşımına uğramış kayıt `fd == 0` ise `continue` çalışır ama iterator **ilerletilmez** (`MATCPServer::checkHeartbeatMessages`). Döngü `heartbeatLock` tutulurken sonsuza kadar döner. Bundan sonra yeni accept, heartbeat güncellemesi ve bağlantı kapanışı `heartbeatLock.lock()`'ta kalır, yani MARpc sunucusu donar. Yalnız stdin kapalı başlatılan bir process'te fd 0 bir socket'e verildiğinde olur. ⚠ Eski bilgi tabanı bunu "sentinel check, bug-ish" diye anıyordu; gerçek etkisi sunucunun donmasıdır.
2. **bug?** İstemci kopmayı host'a bildirmez, yeniden bağlanmaz ve `recv()==0`'ı kopma saymaz (§ 4). order-service restart olduğunda HFT/AlgoProd process restart olana kadar order-service yolu sessizce ölüdür. İstekler hata vermeden kaybolur.
3. **bug?** `connectToServer` hatası sessizdir (§ 1). ouch-sdk login'i süresiz bekler, HFT/AlgoProd açılışta takılır. Socket fd de sızar.
4. **bug?** Unix soket `bind` hatası (dizin yok, yetki) TCP dinlemeyi de engeller. `SO_REUSEADDR` bind'dan sonra set edildiği için etkisizdir. `getaddrinfo` hatasında `exit(1)` çağrılır (§ 2).
5. **bug?** fd yeniden kullanımı ve kapanış sırası yarışı (§ 8). Eski yanıt yeni bağlantıya gidebilir, yeni bağlantı eski thread tarafından kapatılabilir.
6. **bug?** Farklı thread'lerden gönderilen olaylar arasında sıra garantisi yok (§ 6). İstemcide Executed → Accepted ters sırası görülebilir.
7. **bug?** Bağlantı sınırını aşan fd kapatılmaz ve hiç işlenmez (§ 2.1). `TCP_NODELAY` hatası TCP accept thread'ini bitirir.
8. **bug?** Kilitsiz `std::map` erişimleri (§ 5.3): `isRunning.find` okumaları, `sendingMessageList[]`/`parseDataQueue[]` ile eşzamanlı ekleme. Biçimsel olarak tanımsız davranıştır.
9. **bug?** Busy-spin: istemcide 3, sunucuda bağlantı başına 2 thread, ayrıca TCP accept ve watchdog sürekli CPU tüketir. Onload ile aynı çekirdekleri paylaşıyorsa gecikmeye etki edebilir. doğrula.
10. **bug?** İkinci `startOrderClient` / `startOrderServer` çağrısında use-after-free (§ 4.4, § 7.3). Mevcut host'lar bunu yapmıyor.
11. Küçük:
    - `connectToServer` içinde `std::to_string(port).c_str()` geçici nesneyi gösterir (dangling) ve `atoi` ile okunur. `memset(&service, '0', …)` sıfır yerine ASCII `'0'` doldurur.
    - `setResponseDelegate` / `setRequestDelegate` kilitsiz atanır.
    - `MATCPClient` destructor'ı `timerTask`'ı hiç ele almaz.
