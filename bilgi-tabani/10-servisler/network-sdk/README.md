---
kapsam: network-sdk (libMARpc) — giriş ve indeks; görev, kullananlar, dosya yapısı, alt dosyalar, kısa özetler, build
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

# network-sdk (`libMARpc`)

FlatBuffers yüklü, uzunluk önekli TCP/Unix-soket RPC kütüphanesi (C++17, public API `extern "C"`). Tek görevi **ouch-sdk istemcileri (HFT, AlgoProd) ile order-service arasındaki** mesajlaşmadır.
- Hot path'te değildir: HFT'nin handoff sonrası doğrudan emirleri MAOrderSDK ile gider ([maordersdk](../maordersdk/README.md)).
- BIST ile ilgisi yoktur. Kimlik doğrulama, yetki, emir mantığı yoktur; bunlar order-service'tedir.
- Şifreleme yoktur (düz TCP). Login şifresi ve `UserDisconnected` içindeki OUCH şifresi açık metin gider.

**Kullananlar:**
- **İstemci** (`Public/MAOrderClient.h`): ouch-sdk `OrderStreamClient.cpp` → HftSrvProd ve AlgorithmicTrading `OuchManager` ([ouch-sdk](../ouch-sdk/README.md)).
- **Sunucu** (`Public/MAOrderServer.h`): order-service `OrderServer` ([order-service/arayuzler § 3](../order-service/arayuzler.md#3-marpc-sunucusu-orderserver)). İstek tiplerinin order-service'te nasıl işlendiği, alanların anlamı ve olay yönlendirmesi oradadır; bu klasörde tekrarlanmaz.

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`wire-protokolu.md`](wire-protokolu.md) | Çerçeve (4 bayt big-endian uzunluk + FlatBuffers), `orders.fbs` / `orders_response.fbs` bütün tablo ve alanları (tip, C karşılığı, birim), union indeksleri ve `RequestTypes`/`ResponseTypes` farkı, enum'lar, istek ↔ yanıt eşlemesi, C struct ↔ FlatBuffers dönüşümü ve pointer ömrü, `CLOSE_MSG`, heartbeat çerçevesi, versiyonlama ve uyumluluk |
| [`baglanti-ve-threadler.md`](baglanti-ve-threadler.md) | İstemci ve sunucu yaşam döngüsü, TCP/Unix soket seçimi, soket seçenekleri, login'in SDK'daki yeri, heartbeat ve 15 sn zaman aşımı, kopma tespiti ve yeniden bağlanma (yok), thread modeli, callback thread'leri, sıralama garantisi, backpressure, kapanış, bağlantı sınırı ve fd yeniden kullanımı |

## Dosya yapısı (`sdk/`)

| Yer | İçerik |
|-----|--------|
| `Public/MARpc.h` | Şemsiye başlık (`MAOrderClient.h` + `MAOrderServer.h`) |
| `Public/MAOrderClient.h` | `startOrderClient`, `closeClientConnection`, `sendOrderRequest`, `setResponseDelegate`; `response_protocol` |
| `Public/MAOrderServer.h` | `startOrderServer`, `setRequestDelegate`, `setOrderResponse`, `setConnectionClosedDelegate`, `setPerformanceSDK`; `request_protocol`, `close_protocol` |
| `Public/MAOrderStruct.h`, `MAOrderEnums.h` | Host'un gördüğü C struct'ları ve enum'lar (wire biçimi değildir) |
| `Client/MATCPClient.*`, `Client/MAOrderClient.cpp` | İstemci: global tek `tcpClient` |
| `Server/MATCPServer.*`, `Server/MAOrderServer.cpp` | Sunucu: global tek `tcpServer` |
| `Models/orders.fbs`, `orders_response.fbs` | FlatBuffers şemaları. `*_generated.h` repoda yok; CI `flatc -c` ile üretir. |
| `Models/MAHelper.*` | Singleton: FlatBuffers builder, C struct ↔ FB dönüşümü, enum eşlemesi, zaman yardımcıları |
| `Models/MAConstants.h` | `CLOSE_MSG "C"`, `LENGTH_INT 4`, `LENGTH_SHORT 2`, `CONNECTION_TIMEOUT_MS 15000` |
| `Models/MAInternalStructs.h` | `HeartBeatRequest` (public değil) |
| `Models/ThreadPool.h` | Sunucunun bağlantı thread havuzu |
| `Models/concurrentqueue.h` | moodycamel `ConcurrentQueue` (kilitsiz, sınırsız) |
| `../demoapp/` | Örnek istemci/sunucu (`main.cpp`, `main.c`). Kök `CMakeLists.txt`'te `add_subdirectory(demoapp)` **yorum satırında**; build edilmez, `main.c` güncel struct'larla derlenmez (`orderType` alanı yok). |

## Kısa özetler

Ayrıntı ve kod referansları alt dosyalarda; burada yalnız yön bulmak için.

- **Çerçeve:** `[uint32 big-endian payload uzunluğu][FlatBuffers]`. Uzunluk kendini içermez. FlatBuffers içeriği little-endian. Sürüm alanı, file identifier, verifier, boyut sınırı yoktur ([wire § 1](wire-protokolu.md#1-çerçeve)).
- **İstek:** `RequestHolder{request: BaseRequest union, authToken:[byte]}`. Union: Login, EnterOrder, CancelOrder, ReplaceOrder, AllOrdersRequest, AccountStrategyRequest, HearthbeatRequest (yazım hatası şemada). Sabah/açılış emri isteği yoktur.
- **Yanıt:** `ResponseHolder{response, status, statusCode}`. Union: Login, OrderAccepted, OrderReplaced, OrderCanceled, OrderExecuted, OrderRejected, AccountStrategiesResponse, AllOrdersResponse, `UserDisconnectedResponse` (handoff bildirimi; [order-service/arayuzler § 3.8](../order-service/arayuzler.md#38-userdisconnected-handoff-bildirimi)).
- **Korelasyon yok:** Protokolde istek id'si yoktur. Emir olayları istemcide `orderToken`/`passThrough` ile, diğer yanıtlar tipiyle eşlenir ([wire § 5](wire-protokolu.md#5-istek--yanıt-eşlemesi)).
- **`StrategyType`:** 0–15. `HFT_WARRANT_ADVANCED (15)` son commit'te eklendi (network-sdk #84). ⚠ master'da yok (2026-10-22), bkz. [varant-toplu](../../20-stratejiler/varant-toplu.md). Yeni tip için `orders.fbs` **ve** `MAHelper::getStrategyType` / `getStrategyTypeResult` güncellenmelidir; eşlenmeyen değer sessizce `0` (UNKNOWN) olur.
- **Bilinen bug:** `MAHelper::getApplicationResult` OUCH(3) ile AlgoTrading(2)'yi ters çevirir. AlgoProd'un login'i order-service'e `APPLICATION_OUCH` olarak ulaşır, order-service bunu `APP_UNKNOWN` yapar ([wire § 4](wire-protokolu.md#4-enumlar)).
- **Ömür:** Sunucu callback'ine ve istemci callback'ine verilen struct'lardaki `const char*` alanlar alınan FlatBuffers tamponunu gösterir. **Yalnız callback süresince geçerlidir** ([wire § 6](wire-protokolu.md#6-c-struct--flatbuffers-dönüşümü-ve-pointer-ömrü)).
- **Bağlantı:** İstemci process başına tek bağlantıdır (global `tcpClient`). `"localhost"` adresi Unix soketine (`/workingDirectory/sock/mysocket`), diğerleri IPv4 TCP'ye gider. Sunucu TCP portu ve Unix soketini birlikte açar. Toplam en çok 5 bağlantı vardır ([bağlantı § 2](baglanti-ve-threadler.md#2-sunucu-yaşam-döngüsü)).
- **Heartbeat:** Yalnız istemci → sunucu, ~3 sn'de bir. Sunucu 15 sn heartbeat görmezse bağlantıyı kapatır. Sunucu → istemci heartbeat yoktur.
- **Kopma:** Yeniden bağlanma yoktur. İstemci kopmayı host'a **bildirmez**; kopuk bağlantıya gönderilen istekler sessizce kaybolur. `recv() == 0` (FIN) kopma sayılmaz ([bağlantı § 4](baglanti-ve-threadler.md#4-kopma-tespiti-ve-yeniden-bağlanma)).
- **Thread:** İstemci 3 detached thread kullanır (recv+send, parse+callback, heartbeat). Sunucu bağlantı başına 2 thread kullanır (recv+send, parse+callback); bunlara ek olarak 2 accept thread'i ve 1 watchdog vardır. Hepsi busy-spin ile döner. Kuyruklar sınırsızdır, backpressure yoktur ([bağlantı § 5](baglanti-ve-threadler.md#5-thread-modeli)).
- **Sıra:** Bir bağlantının istekleri sırayla işlenir. Gönderim kuyruğu (moodycamel) yalnız **aynı üretici thread** için FIFO'dur. Farklı thread'lerden `setOrderResponse` ile gönderilen olayların sırası garanti değildir ([bağlantı § 6](baglanti-ve-threadler.md#6-sıralama-garantisi)).

Açık sorunlar: [`ACIK-KONULAR.md`](../../../issues/ACIK-KONULAR.md). Bu klasördeki şüpheli maddeler alt dosyaların `## Şüpheli` bölümlerinde.

## Eski bilgi tabanı (K-07)

`meeapps-ai/algo/context/context-network-sdk/` altındaki `wire-protocol.md`, `connection-management.md` ve `bugs-and-quirks.md` maddeleri 3c1b42f'e karşı tek tek kontrol edildi. Doğru olanlar alt dosyalara koddan yeniden yazıldı. Değişen ve yanlış olanlar ilgili yerde `⚠ Eski bilgi tabanı … diyordu` notuyla işaretlendi. Belli başlı düzeltmeler:
- Decode **derin kopya değildir**; pointer'lar FlatBuffers tamponunu gösterir.
- Watchdog'daki `connection == 0` dalı sonsuz döngüdür. Eski not bunu yalnız "kötü sentinel" diye anıyordu.
- Sunucu çökünce istemci `recv()==0` ile kopmayı **anlamaz**.
- `SO_REUSEADDR` `bind`'dan **sonra** set edilir.
- `Hearthbeat` adını düzeltmek wire uyumluluğunu bozmaz; FlatBuffers ikili biçiminde isim yoktur.
- `timeToSent` kullanılıyor: order-service bunu `expire_date` olarak okur.

## Build

- CMake (≥ 3.10), C++17, `-fconcepts`, varsayılan `Release` (`-O2`). Kök `CMakeLists.txt` yalnız `sdk/`'yi ekler.
- Çıktı: `libMARpc.so` (shared) → `/usr/local/lib`. Public başlıklar → `/usr/local/include/MARpc/`.
- Bağımlılık: `flatbuffers` (CI v23.5.9, `-fPIC` ile yeniden derlenir) ve `pthread`. `MAPerfSDK` kütüphanesi bulunursa link edilir. Başlığı (`MAPerfSDK/PerformanceClient.h`) ise `Server/MATCPServer.h` tarafından koşulsuz include edilir, yani build'de zorunludur.
- `ma_add_git_version(MARpc COMPONENT MARpc REPO network-sdk)`: git sürüm bilgisi artifact'e gömülür (`cmake/`).
- CI `.github/workflows/network.yml`: `development`/`preprod`/`master` push'unda `meeapps/maprodenv:4.0` container'ında çalışır. Adımlar: `flatc -c` → build → Sentry debug sembolleri → `libMARpc.so` + başlıklar Algo-Setup `MAProdEnv`'e (master → `main` branch'i).
- Şema değişikliği hem istemciyi (ouch-sdk + HFT/AlgoProd) hem sunucuyu (order-service) etkiler. Uyumluluk kuralları: [wire § 9](wire-protokolu.md#9-versiyonlama-ve-uyumluluk).
