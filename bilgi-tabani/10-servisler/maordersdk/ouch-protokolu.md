---
kapsam: MAOrderSDK'nın OUCH bağlantısı — SoupBinTCP katmanı, bağlanma/login/failover, recv thread'i, heartbeat, sequence ve replay, onReplayCompleted, kopma/End of Session, OUCH mesajlarının byte düzeni, ölçek ve kodlama tuzakları
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: a788782
dis_kaynak:
  - dosya: MAOrderSDK/docs/bistech-ouch-protocol-specification.pdf
    not: yalnız koddaki ofset/kodları teyit için
  - dosya: MAOrderSDK/docs/soupbintcp-protocol-specification2B66B4A034F0.pdf
    not: yalnız login/heartbeat/End of Session anlamını teyit için
dogrulama: 2026-10-22
durum: taslak
---

# MAOrderSDK — OUCH bağlantısı ve wire protokolü

İndeks: [README.md](README.md). Bu dosyada olmayanlar:
- Public API, config alanları, callback listesi ve thread'leri, `ownsAccount`, round-robin → [api-ve-yasam-dongusu.md](api-ve-yasam-dongusu.md)
- enter/cancel/replace iç yolu, token havuzu, bölme, yerel retler, replay adopt, combiner → [emir-akisi.md](emir-akisi.md)
- FIX → [fix.md](fix.md)
- Host tarafı: HFT handoff/replay gate [hftsrvprod/emir-yasam-dongusu § 4](../hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı), order-service reconnect shim [order-service/sdk-ve-oturumlar § 9](../order-service/sdk-ve-oturumlar.md#9-oturumlar-yeniden-bağlanma-ve-kopma-senaryoları)

Kod: `src/connection/IConnection.h`, `src/connection/ouch/OuchConnection.{h,cpp}`, `src/protocol/ouch/OuchProtocol.h` (paket/mesaj tipleri, uzunluk sabitleri), `src/protocol/ouch/OuchCodec.{h,cpp}` (encode/decode), `src/MAOrderSDK.cpp` (`Impl::install_callbacks`, `MAOrderSDK::start` heartbeat thread'i, `connectUser`, `disconnectUser`, `stop`).

## 1. Yapı

- `IConnection`: soyut arayüz (`connect`, `disconnect`, `is_connected`, `send`, `receive`, `send_heartbeat`, `username`). Tek OUCH gerçeklemesi `OuchConnection`. `receive()` tanımlı ama SDK içinde kullanılmaz; okuma recv thread'indedir.
- Bir `OuchConnection` = bir OUCH kullanıcısı = bir TCP soketi = bir recv thread'i. `setOuchConfig` her `protocol == Ouch` kullanıcısı için bir tane kurar; `connectUser(OuchUser)` dinamik olarak ekler.
- `OuchConnection` callback'leri ham wire token'ı taşır. `Impl::install_callbacks` bunları `client_order_id`'ye çevirip public callback'lere iletir ([emir-akisi.md](emir-akisi.md)).
- Codec durumsuzdur (`OuchCodec` statik fonksiyonlar), çağıranın tamponuna yazar, heap kullanmaz. Tampon boyutu `kMaxOuchMsgLen = 256`; yetmezse encode 0 döner.

## 2. SoupBinTCP katmanı

Çerçeve: `[uzunluk: 2 bayt big-endian][tip: 1 bayt][payload]`. Uzunluk = tip baytı + payload (yani payload = uzunluk − 1). Bütün tamsayılar big-endian.

| Tip | Kod (`PacketType`) | Yön | SDK |
|-----|--------------------|-----|-----|
| Login Request | `L` | istemci → | `login()` içinde gönderir (§3.2) |
| Login Accepted | `A` | ← sunucu | `login()` işler; session/sequence saklanır, kullanılmaz (§5) |
| Login Rejected | `J` | ← sunucu | `login()` işler; neden baytı `A`/`S` (§3.3) |
| Sequenced Data | `S` | ← sunucu | Recv thread'i: sayaç++ ve OUCH mesajı dispatch (§8) |
| Unsequenced Data | `U` | istemci → | Bütün emir mesajları bununla gider |
| Server Heartbeat | `H` | ← sunucu | Replay sırasında sayılır; her paket watchdog'u besler |
| Client Heartbeat | `R` | istemci → | SDK heartbeat thread'i gönderir (§4.2) |
| Logout Request | `O` | istemci → | `OuchConnection::logout()` var, **hiçbir yerden çağrılmaz** (§6) |
| End of Session | `Z` | ← sunucu | Login sırasında: başarısız login. Sonrasında: `connected_ = false` (§6, Şüpheli 1) |
| Debug | `+` | iki yön | Okunur ve atılır |

Sunucudan gelen Unsequenced Data ve bilinmeyen tipler recv thread'inde okunup atılır. Login sırasında bilinmeyen paketlerin payload'ı boşaltılıp beklemeye devam edilir.

## 3. Bağlanma ve login (`connect_with_diagnostics`)

### 3.1 TCP ve failover

1. Önceki döngüden kalan recv thread'i joinable ise join edilir, eski soket kapatılır. Çağrı recv thread'inin **kendi içinden** geliyorsa (ör. `onUserDisconnected` callback'inde yeniden bağlanma) join yerine hemen `TcpFailed` döner. Yeniden bağlanma callback dışında planlanmalıdır.
2. `connect_to(ip, port)`, olmazsa `connect_to(secondary_ip, secondary_port)`. ip boş veya port 0 ise o uç atlanır.
   - Soket: `TCP_NODELAY`, `O_NONBLOCK`. `SO_KEEPALIVE`/buffer ayarı yok.
   - Non-blocking `connect` + `select` yazılabilirlik beklemesi: uç başına **2 s**. Sonra `SO_ERROR` kontrolü.
3. **Failover yalnız TCP seviyesindedir.** Birincil TCP bağlanıp login başarısız olursa (ret, zaman aşımı) ikincil denenmez.
4. TCP iki uçta da başarısızsa `TcpFailed` döner; `onLoginFailed` **çağrılmaz**.
5. TCP + login başarılıysa: `connected_ = true`, Onload `MSG_WARM` desteği yoklanır, replay ve watchdog durumu sıfırlanır (§5, §4.3), recv thread'i başlatılır, ardından **çağıranın thread'inde** `onUserConnected`.
   - Recv thread'i `onUserConnected`'dan önce başladığı için replay mesajları `onUserConnected` dönmeden gelmeye başlayabilir.

En kötü süre: 2 s (birincil) + 2 s (ikincil) + 2 s (login) ≈ 6 s, çağıran thread'i bloklar.

BIST notu (OUCH spec § 3.3): bir OUCH hesabı iki gateway'e bağlanabilir, ama aynı anda ikisinde login olunamaz; ikinci login birinciyi düşürür. `to_string(ConnectResult::LoginTimeout)` metni "no response (possibly connected elsewhere)" bu duruma işaret eder. ❓ doğrulanmadı: başka yerde açık oturum varken BIST'in login'e cevap vermeyip vermediği.

### 3.2 Login Request (`OuchCodec::encode_login`)

Toplam 49 bayt; uzunluk alanı 47 (`kLoginRequestLen` 46 + 1). Tampon önce boşlukla (0x20) doldurulur.

| Ofset | Uzunluk | Alan | Değer |
|-------|---------|------|-------|
| 0 | 2 | Packet Length | 47, big-endian |
| 2 | 1 | Packet Type | `L` |
| 3 | 6 | Username | `<OUCH_USER>`; sağdan boşluk dolgulu, 6'dan uzunsa **sessizce kesilir** |
| 9 | 10 | Password | `<REDACTED>`; sağdan boşluk dolgulu, 10'dan uzunsa kesilir |
| 19 | 10 | Requested Session | 10 boşluk = o an aktif oturum |
| 29 | 20 | Requested Sequence Number | 19 boşluk + `'1'` (ASCII, sağa yaslı) = **1** |

- Her login sabit olarak **sequence 1** ister: o oturumun bütün Sequenced Data mesajları baştan yeniden gelir. Önceki bağlantıdan kalan sequence ile devam etme (SoupBinTCP'nin önerdiği "next expected sequence") uygulanmamıştır.
- Neden: restart sonrası SDK hiçbir emri bilmez; günün accept/replace'lerinden token'ları adopt edebilmek için tam replay gerekir ([emir-akisi.md](emir-akisi.md)). Aynı davranış yeniden bağlanmada da geçerlidir; host tarafı dedup yapmak zorundadır.

### 3.3 Login yanıtı (`OuchConnection::login`)

Login gönderimi `send_raw` iledir (`connected_` henüz false). Sonra **toplam 2 s** deadline ile (`recv_exact`, `select` + `read`) paketler okunur:

| Gelen | Sonuç | `LoginFailureReason` | `ConnectResult` |
|-------|-------|----------------------|-----------------|
| `A` Login Accepted | Session (10 bayt) ve sequence (20 bayt, ASCII) `current_session_`/`current_sequence_`'a yazılır; başarı | — | `Ok` |
| `J`, neden `A` | Başarısız | `NotAuthorized` | `LoginRejected` |
| `J`, neden `S` | Başarısız | `SessionNotAvailable` | `LoginRejected` |
| `J`, diğer neden | Başarısız | `Unknown` | `LoginRejected` |
| `Z` End of Session | Başarısız | `SessionNotAvailable` | `LoginRejected` |
| `H` Server Heartbeat | Yok sayılır, beklemeye devam | — | — |
| Diğer | Payload boşaltılır, beklemeye devam | — | — |
| 2 s içinde başlık gelmedi | Başarısız | `Timeout` | `LoginTimeout` |
| Gönderim/okuma hatası, payload okunamadı | Başarısız | `NetworkError` | `TcpFailed` |

- Her başarısızlıkta `fail_login` → `onLoginFailed(username, reason)` **çağıranın thread'inde**, ardından soket kapatılır.
- Çağrı sırası public API'de: `connectUser` → `ConnectResult`; ayrıntı [api-ve-yasam-dongusu.md](api-ve-yasam-dongusu.md).

## 4. Recv thread'i ve heartbeat

### 4.1 Recv thread'i (`recv_loop`, `recv_until_stop`)

- Thread başında `apply_recv_thread_config` (best-effort, hata yalnız `std::cerr` uyarısı):
  - Pin: `OuchUser::recv_pin_core >= 0` ise o; değilse `OrderSdkConfig::recv_pin_core` (`set_recv_affinity`). `-1` = pin yok.
  - Sched: `OuchUser::recv_sched_policy != SCHED_OTHER` ise `pthread_setschedparam(policy, recv_sched_priority)`. FIFO/RR için `CAP_SYS_NICE` gerekir.
- Döngü: 3 baytlık başlık, sonra `uzunluk − 1` baytlık payload okunur, `handle_packet` çağrılır.
  - Payload tamponu 256 bayttır; payload > 256 ise döngü kırılır (kopma, Şüpheli 4).
- Okuma: **`select` 100 ms timeout + `read`** — busy-poll değildir. `select` 0 dönerse (100 ms boşluk) idle tick çalışır: Onload warm bayrağı, `maybe_fire_replay_completed`, `maybe_fire_heartbeat_timeout`.
- Onload: `bootstrapOnloadIfRequested` `EF_POLL_USEC=100000` ile yeniden başlatır. ❓ doğrulanmadı: Onload altında bu `select`'in 100 ms'ye kadar kullanıcı alanında spin ettiği (Onload davranışı; SDK kodunda açık busy-poll yok).
- Her başarılı `read`'de `last_recv_ns_` (CLOCK_MONOTONIC) güncellenir — paket tipi ayırt edilmez.
- Döngü `connected_` false olunca veya okuma hatası/EOF'ta biter. Çıkışta `connected_.exchange(false)` true dönerse (yani kopmayı recv thread'i fark ettiyse) `onUserDisconnected` **recv thread'inden** çağrılır. Soket burada kapatılmaz; sonraki `connect_with_diagnostics` veya `disconnect` kapatır.

### 4.2 Heartbeat gönderme

- Connection değil, SDK seviyesinde **tek thread** (`MAOrderSDK::start` içinde `heartbeat_thread`):
  - Her turda connection listesi kilit altında kopyalanır, `is_connected()` olan her birine `send_heartbeat()` (`R`, 3 bayt), sonra `heartbeat_interval_ms` uyku (varsayılan 1000 ms; order-service 3000 kullanır, [sdk-ve-oturumlar § 3](../order-service/sdk-ve-oturumlar.md#3-sdk-config-kodda-sabit)).
  - Koşulsuz gönderir: son emir gönderiminden bağımsız. Gerçek periyot = interval + gönderim süresi.
  - `start()` çağrılmadan heartbeat gitmez. Gönderim hatası yok sayılır.
- Heartbeat `send_raw` kullanır: connection'ın `send_mutex_`'ini emir gönderimiyle paylaşır ve `mark_sent()` yapar.
- SoupBinTCP: istemci 1 s'den uzun sessiz kalmamalı; sunucu tipik olarak ~15 s veri görmezse soketi kapatır.

### 4.3 Heartbeat izleme (`maybe_fire_heartbeat_timeout`)

- Yalnız recv thread'inin idle tick'inde (100 ms) kontrol edilir.
- `now − last_recv_ns_ >= heartbeat_timeout_ms` (`OuchConfig`, varsayılan 5000 ms; 0 = kapalı) ise `onHeartbeatTimeout(username)` **recv thread'inden**, logon başına **bir kez** (`heartbeat_fired_`, yalnız başarılı login'de sıfırlanır).
- **Yalnız bildirim.** Soket kapatılmaz, `connected_` değişmez, yeniden bağlanma yok. Trafik geri gelse bile aynı logon'da ikinci kez tetiklenmez.

## 5. Sequence, replay ve `onReplayCompleted`

- `current_seq_num_` her Sequenced Data'da artar; login'de **sıfırlanmaz** ve hiçbir yerde okunmaz. `current_session_`/`current_sequence_` da saklanır ama kullanılmaz. Gap tespiti, sequence uyuşmazlığı kontrolü veya session değişimi takibi **yoktur**.
- Replay ile canlı akış wire'da ayırt edilmez; ikisi de aynı `dispatch_message` yolundan geçer. OUCH mesajlarında `is_replay` hiç set edilmez (yalnız FIX).
- **Replay bitiş tespiti** (`maybe_fire_replay_completed`), logon başına en fazla bir kez:
  - Login başarısında: `replay_start_ns_ = now`, `last_seq_data_ns_ = 0`, `heartbeat_seen_count_ = 0`, `in_replay_ = true`.
  - `in_replay_` iken her Sequenced Data `last_seq_data_ns_`'i günceller; her Server Heartbeat sayacı artırır.
  - Koşul: en az 1 Server Heartbeat görülmüş **ve** `now − max(last_seq_data_ns_, replay_start_ns_) >= replay_quiet_window_ms` (varsayılan 10 000 ms).
  - Kontrol noktaları: her Server Heartbeat ve her 100 ms idle tick. Sequenced Data gelirken kontrol edilmez.
  - Tetiklenince `in_replay_ = false` (CAS), PerfSDK'ya `maordersdk_replay_quiet_window_ns` yazılır, `onReplayCompleted(username)` **recv thread'inden**.
- Sonuçlar:
  - Replay'siz (boş) oturumda bile en erken login + 10 s'de tetiklenir.
  - Hiç Server Heartbeat gelmezse hiç tetiklenmez (SoupBinTCP sunucusu yalnız 1 s veri göndermezse heartbeat yollar; sürekli veri akan oturumda gecikir).
  - Quiet window içinde gelen **canlı** mesajlar da pencereyi uzatır; SDK bunları replay'den ayıramaz.
  - Login'den önce kopulursa tetiklenmez; sonraki login yeniden kurar. Host'un gate sayacı her logon'da bir tetik görür ([emir-yasam-dongusu § Replay gate](../hftsrvprod/emir-yasam-dongusu.md#replay-gate-strategymanager)).
- Config: `OrderSdkConfig::replay_quiet_window_ms` (`set_replay_quiet_window`), HFT'de `sdkReplayQuietWindowMs`.

## 6. Disconnect, logout, yeniden bağlanma, End of Session

- `disconnect()` (`disconnectUser`, `stop`, destructor): `connected_.exchange(false)` → recv thread join (≤ ~100 ms; recv thread'inin içinden çağrılırsa join atlanır) → soket `close` → önceden bağlıysa `onUserDisconnected` **çağıranın thread'inde**.
  - **Logout Request (`O`) gönderilmez.** `logout()`/`encode_logout` tanımlı, çağıran yok. BIST oturumu TCP kapanışıyla düşer.
- **Yeniden bağlanma yoktur.** SDK hiçbir durumda kendiliğinden bağlanmaz. Host `connectUser(username)` ile tetikler (order-service shim'i 1 s aralıkla; HFT yalnız handoff'ta). `connectUser` bağlıysa `AlreadyConnected` döner.
- `connect_with_diagnostics` aynı connection için eşzamanlı çağrıya karşı korumalı değildir; tekilliği host sağlar (order-service `reconnect_in_progress_`).
- **End of Session** (`Z`, login sonrası): `handle_packet` yalnız `connected_ = false` yapar. Recv döngüsü çıkar, ama `connected_` zaten false olduğu için `exchange` false döner ve **`onUserDisconnected` çağrılmaz**; combiner `poison_all` da çalışmaz; soket açık kalır (Şüpheli 1).
- Kopmada combiner: `Impl::install_callbacks` → `onUserDisconnected` öncesi `combiner_.poison_all` ([emir-akisi.md](emir-akisi.md)).

## 7. Gönderim (`send`, `send_raw`)

- `send()` `connected_` false ise `false`. Yazım connection başına `send_mutex_` altında; farklı connection'lar paralel.
- Sıra: `maybe_warm_send` (bekleyen Onload `MSG_WARM` varsa 8 baytlık warm send, `mark_sent` yapmaz) → Onload derlemesinde `send_raw_zc` (zero-copy; fd Onload değilse POSIX'e düşer) → tek `::send(MSG_NOSIGNAL)` → kısmi/EAGAIN ise `send_raw_slow` (`select` 1 s, döngü).
- Warm bayrağı recv idle tick'inde, son gerçek gönderimden `warm_interval_ms` geçtiyse kurulur (0 = kapalı).
- Gönderim hatası connection'ı düşürmez; yalnız `false` döner (ret üretimi [emir-akisi.md](emir-akisi.md)).

## 8. OUCH mesajları

Ortak: tüm sayısal alanlar big-endian. Alpha alanlar sağdan boşluk (0x20) dolgulu, uzunsa kesilir (`write_alpha`). Giden mesajlarda tampon önce tamamen boşlukla doldurulur; yazılmayan/rezerve baytlar 0x20 olur. Ofsetler OUCH mesajının başından (SoupBinTCP 3 baytlık başlık hariç). Fiyat: işaretli int32, raw; ondalık sayısı ITCH Order Book Directory'den (SDK'da `InstrumentLimit::decimal_count`), yani TL × 10^decimals. Miktar: lot. Timestamp: Unix epoch ns.

### 8.1 Enter Order `O` (`encode_enter_order`) — 114 bayt (`kEnterOrderLen`), çerçeve uzunluğu 115

| Ofset | Uz. | Alan | Tip | Kaynak / kodlama |
|-------|-----|------|-----|------------------|
| 0 | 1 | Message Type | char | `O` |
| 1 | 14 | Order Token | alpha | SDK token'ı ([emir-akisi.md](emir-akisi.md)) |
| 15 | 4 | Order book ID | uint32 BE | `orderbook_id` (uint64 → uint32 kesme) |
| 19 | 1 | Side | char | `Side`: `B`, `S`, `T` (açığa satış); `Unknown` → 0x00 |
| 20 | 8 | Quantity | uint64 BE | `quantity`, lot |
| 28 | 4 | Price | int32 BE | `price` (int64 → int32 kesme), raw |
| 32 | 1 | Time In Force | uint8 | `Day`→0, `ImmediateOrCancel`→3, `FillOrKill`→4; **diğerleri → 0** (Şüpheli 6) |
| 33 | 1 | Open Close | uint8 | `OpenClose` ham değer: 0 hesap varsayılanı, 1 Open, 2 Close |
| 34 | 16 | Client/Account | alpha | `client_account` (spec: VİOP hesabı bu alanda) |
| 50 | 15 | Customer Info | alpha | `passthrough` |
| 65 | 32 | Exchange Info | alpha | `exchange_info` (spec: pay piyasası hesabı bu alanda; ilk 16 bayt kullanılır) |
| 97 | 8 | Display Quantity | uint64 BE | `display_quantity`; 0 = gizli emir değil |
| 105 | 1 | Client Category | uint8 | `Client`→1, `House`→2, `Fund`→7, `InvestmentTrust`→9, `PrimaryDealerGovt`→10, `PrimaryDealerCorp`→11, `PortfolioManagementCompany`→12, `Unknown`→0 (VİOP), tanımsız→1 |
| 106 | 1 | OffHours | uint8 | `OffHours` ham: 0 normal, 1 seans dışı (VİOP) |
| 107 | 1 | SMP Level | uint8 | 0 boş, 1 üye içi, 2 üyeler arası |
| 108 | 1 | SMP Method | uint8 | 0 boş, 1 aggressive iptal, 2 passive iptal, 3 ikisi |
| 109 | 3 | SMP ID | alpha | Yalnız Level ve Method ikisi de `Unknown` değilse yazılır; değilse boşluk |
| 112 | 2 | Reserved | — | boşluk |

Dikkat: enum'ların C++ değeri wire değeri değildir (`ClientCategory::Client` = 0 ama wire 1; `TimeInForce::Day` = 1 ama wire 0). Wire'a yalnız codec çevirisiyle gider.

### 8.2 Replace Order `U` (`encode_replace_order`) — 125 bayt (`kReplaceOrderLen`), çerçeve uzunluğu 126

| Ofset | Uz. | Alan | Tip | Kodlama |
|-------|-----|------|-----|---------|
| 0 | 1 | Message Type | char | `U` |
| 1 | 14 | Existing Order Token | alpha | değiştirilen emrin wire token'ı |
| 15 | 14 | Replacement Order Token | alpha | yeni token (daha önce kullanılmamış olmalı) |
| 29 | 8 | Quantity | uint64 BE | `quantity` olduğu gibi. Spec: **toplam** miktar (açık + gerçekleşmiş), açık miktar değil |
| 37 | 4 | Price | int32 BE | `price`; spec: 0 = değişiklik yok |
| 41 | 1 | Open Close | uint8 | sabit 0 = değişiklik yok |
| 42 | 16 | Client/Account | alpha | `client_account` boşsa ilk bayt `\0` = koru |
| 58 | 15 | Customer Info | alpha | `passthrough` boşsa ilk bayt `\0` = koru |
| 73 | 32 | Exchange Info | alpha | **her zaman** ilk bayt `\0` = koru (struct'ta alan yok) |
| 105 | 8 | Display Quantity | uint64 BE | sabit 0 = değişiklik yok (boşluk dolgusu büyük sayı okunmasın diye açıkça yazılır) |
| 113 | 1 | Client Category | uint8 | sabit 0 = değişiklik yok |
| 114 | 11 | (dolgu) | — | boşluk |

Spec bu mesajı 122 bayt (114 + 8 rezerve) verir; kod 125 gönderir. Kod yorumu: "125 matches order-service prod encoder; spec p.12 shows 122 — prod-tested value wins". ❓ doğrulanmadı: BIST'in fazla 3 baytı yok saydığı (prod'da çalıştığı belirtiliyor).

### 8.3 Cancel Order `X` (`encode_cancel_order`) — 15 bayt

| Ofset | Uz. | Alan |
|-------|-----|------|
| 0 | 1 | `X` |
| 1 | 14 | Order Token (spec: orijinal Enter token'ı; ara replace token'ı da şimdilik kabul edilir) |

### 8.4 Uygulanmayan giden mesajlar

- **Cancel by Order ID** (`Y`): `kCancelByOrderIdLen = 14` sabiti var, encoder yok.
- **Mass Quote** (`Q`): yok.

### 8.5 Gelen mesajlar (decode)

`decode_message_type` ilk baytı okur; `dispatch_message` yalnız aşağıdaki beş tipi işler. Mass Quote Ack (`K`), Mass Quote Rejection (`R`) ve diğerleri sessizce atılır. Uzunluk kontrolü başarısızsa decode **varsayılan struct + boş token** döner ve callback yine çağrılır (Şüpheli 5).

**Order Accepted `A`** (min. 137 bayt):

| Ofset | Uz. | Alan | Decode |
|-------|-----|------|--------|
| 1 | 8 | Timestamp | `timestamp` (ns) |
| 9 | 14 | Order Token | wire token |
| 23 | 4 | Order book ID | `orderbook_id` |
| 27 | 1 | Side | `side` |
| 28 | 8 | Order ID | `order_id` (spec: yalnız orderbook+side içinde tekil) |
| 36 | 8 | Quantity | `quantity` = **kitapta açık kalan** miktar |
| 44 | 4 | Price | `price` (int32 → int64) |
| 48 | 1 | Time In Force | okunmaz |
| 49 | 1 | Open Close | okunmaz |
| 50 | 16 | Client/Account | `account`; boşsa Exchange Info'dan (82, 32) doldurulur |
| 66 | 1 | Order State | **okunmaz** (1 kitapta, 2 kitapta değil, 98 durdurulmuş) |
| 67 | 15 | Customer Info | `passthrough` |
| 82 | 32 | Exchange Info | yalnız `account` yedeği |
| 114 | 8 | Pre Trade Quantity | `pre_trade_quantity` |
| 122–136 | | Display Qty, Client Category, OffHours, SMP Level/Method/ID | okunmaz |

**Order Rejected `J`** (min. 27): 1 Timestamp (8), 9 Order Token (14), 23 Reject Code (int32 BE, işaretli; ör. `-420177`). Enter, replace ve cancel retlerinin hepsi bu mesajdır; hangi işlemin reddedildiği token'dan çözülür. Kod listesi: MAOrderSDK `docs/reject-codes.txt`, [emir-yasam-dongusu § 5](../hftsrvprod/emir-yasam-dongusu.md#5-ret-ve-hata-kodları).

**Order Replaced `U`** (min. 145):

| Ofset | Uz. | Alan | Decode |
|-------|-----|------|--------|
| 1 | 8 | Timestamp | `timestamp` |
| 9 | 14 | Replacement Order Token | wire token (spec: sistem değiştirdiyse **boşluk** → boş string, Şüpheli 3) |
| 23 | 14 | Previous Order Token | prev wire token |
| 37 | 4 | Order book ID | `orderbook_id` |
| 41 | 1 | Side | `side` |
| 42 | 8 | Order ID | `order_id` |
| 50 | 8 | Quantity | `quantity` = kitapta açık kalan |
| 58 | 4 | Price | `price` |
| 62, 63 | 1+1 | TIF, Open Close | okunmaz |
| 64 | 16 | Client/Account | `account`; boşsa Exchange Info'dan (96, 32) |
| 80 | 1 | Order State | **okunmaz** (99 = OUCH sahipliği kaybedildi dahil) |
| 81 | 15 | Customer Info | `passthrough` |
| 128 | 8 | Pre Trade Quantity | `pre_trade_quantity` |
| 136, 144 | 8+1 | Display Qty, Client Category | okunmaz |

**Order Canceled `C`** (min. 37): 1 Timestamp, 9 Order Token, 23 Order book ID (4), 27 Side, 28 Order ID (8), 36 Reason (uint8 → `reason_code`; ör. 1 kullanıcı, 9 sistem, 46 SMP, 115–125 PTRM). Wire'da miktar yoktur; `OrderCanceledMsg::quantity` decode'da 0 kalır. Spec: bağlantı kaybında emirler askıya alınınca da Canceled gelir; aynı emir için birden fazla Canceled gelebilir.

**Order Executed `E`** (min. 51; spec uzunluğu 68):

| Ofset | Uz. | Alan | Decode |
|-------|-----|------|--------|
| 1 | 8 | Timestamp | `timestamp` |
| 9 | 14 | Order Token | wire token |
| 23 | 4 | Order book ID | `orderbook_id` |
| 27 | 8 | Traded Quantity | `quantity` (bu fill'in lotu) |
| 35 | 4 | Trade Price | `price` |
| 39 | 12 | Match ID | `match_id` = **yalnız son 8 bayt** (43–50, düşük 64 bit); ilk 4 bayt atılır |
| 51 | 1 | Client Category | okunmaz |
| 52 | 16 | Reserved | — |

## 9. Ölçek ve kodlama tuzakları

- **Endian:** her şey big-endian (`htobe*`/`be*toh`, `htons`). Fiyat işaretli (`write_signed_be32`/`read_signed_be32`).
- **Fiyat:** API `int64`, wire `int32`. Encode `static_cast<int32_t>` ile kontrolsüz keser. Ölçek host'un sorumluluğu: raw = TL × 10^`decimal_count` ([order-service/sdk-ve-oturumlar § 6](../order-service/sdk-ve-oturumlar.md#6-ölçek-özeti)).
- **Orderbook ID:** API `uint64`, wire `uint32`; kontrolsüz kesme.
- **Replace miktarı:** spec'e göre toplam (açık + gerçekleşmiş); Accepted/Replaced'teki `quantity` ise açık kalan miktardır. SDK dönüştürmez.
- **Replace'te 0/`\0`:** sayısal 0 = "değişiklik yok"; bu yüzden fiyat 0'a çekilemez. Alpha alanın ilk baytı `\0` = koru.
- **Hesap alanı:** pay piyasasında hesap Exchange Info'da, VİOP'ta Client/Account'ta (spec). Decode, Client/Account boşsa Exchange Info'yu `account` yapar; `Impl` ayrıca kendi kaydındaki `client_account` ile tamamlar ([emir-akisi.md](emir-akisi.md)).
- **Alpha okuma:** `read_alpha` yalnız sondaki boşlukları kırpar; NUL veya baştaki boşluklar kalır.
- **Dolgu:** giden mesajlarda rezerve/yazılmayan baytlar 0x20'dir, 0x00 değil. Replace'te sayısal "değişmez" alanlar bu yüzden açıkça 0 yazılır.
- **Login:** kullanıcı adı 6, şifre 10 baytı aşarsa sessizce kesilir.
- **Mesaj tipi çakışması:** `U` hem giden Replace Order hem gelen Order Replaced'tir (`MessageType` enum'unda iki isim aynı değer).

## 10. Kopma senaryoları

| Senaryo | SDK ne yapar | Host'a giden | Thread |
|---------|--------------|--------------|--------|
| Birincil ve ikincil TCP başarısız | Soket kapatılır | `connectUser` → `TcpFailed`; callback yok | çağıran |
| Login rejected (`J`) | Soket kapatılır | `onLoginFailed(NotAuthorized / SessionNotAvailable / Unknown)` + `LoginRejected` | çağıran |
| Login cevabı 2 s içinde yok | Soket kapatılır; ikincil denenmez | `onLoginFailed(Timeout)` + `LoginTimeout` | çağıran |
| Login sırasında End of Session | Soket kapatılır | `onLoginFailed(SessionNotAvailable)` + `LoginRejected` | çağıran |
| Sunucu soketi kapattı / read hatası | Recv döngüsü biter, `connected_ = false`, soket açık kalır | combiner `poison_all` → `onUserDisconnected` | recv |
| Payload > 256 bayt | Kopma gibi | `onUserDisconnected` | recv |
| Heartbeat yok (`heartbeat_timeout_ms`) | Hiçbir şey; bağlı görünmeye devam eder | `onHeartbeatTimeout` (logon başına bir kez) | recv |
| End of Session (login sonrası) | `connected_ = false`, recv biter, soket açık | **hiçbir şey** (Şüpheli 1) | — |
| Sequence uyuşmazlığı / gap | Tespit edilmez (TCP sıralı; tek kaynak tam replay) | — | — |
| Host `disconnectUser` / `stop` | Join + close; Logout gönderilmez | `onUserDisconnected` (önceden bağlıysa) | çağıran |
| Gönderim hatası | Connection düşmez | `enterOrder` vb. `false` / yerel ret ([emir-akisi.md](emir-akisi.md)) | çağıran |

Hiçbir senaryoda SDK yeniden bağlanmaz. Yeniden bağlanınca sequence 1'den tam replay gelir ve yeni bir `onReplayCompleted` üretilir.

## Şüpheli

1. **bug? End of Session'da `onUserDisconnected` yok.** `OuchConnection::handle_packet` `Z` için `connected_ = false` yapar; `recv_loop` çıkışındaki `connected_.exchange(false)` false döndüğü için callback çağrılmaz. Combiner zehirlenmez, soket açık kalır, order-service reconnect shim'i tetiklenmez. Host yalnız `is_connected()` ile fark edebilir. Gün sonunda görülmesi beklenir; gün içi oturum değişiminde etkisi doğrulanmalı.
2. **doğrula: Heartbeat timeout yalnız bildirim.** `maybe_fire_heartbeat_timeout` soketi kapatmaz, `connected_`'ı değiştirmez ve logon başına bir kez tetiklenir. Yarı açık TCP'de connection bağlı görünür, emir yazılır, cevap gelmez. Bkz. [order-service Şüpheli 6](../order-service/sdk-ve-oturumlar.md#şüpheli).
3. **bug? Sistemin değiştirdiği emirde boş token adopt'u.** Spec: emir sistem tarafından değiştirilirse Order Replaced'in Replacement Token'ı boşluktur. `decode_order_replaced` bunu `""` yapar; `Impl::on_wire_replaced` `orders_by_token[""]` bulamazsa `""` anahtarıyla yeni emir adopt eder ve host'a `client_order_id = ""` ile `onReplaced` gider. Order State (99 = sahiplik kaybı) da okunmadığı için host bunu ayırt edemez.
4. **doğrula: 256 bayttan uzun paket bağlantıyı düşürür.** `recv_loop` payload > 256'da döngüyü kırar. OUCH mesajları ≤ 145 bayt ama Debug (`+`) paketi serbest metindir; uzun bir Debug paketi kopmaya yol açar.
5. **doğrula: Kısa mesajda boş token ile callback.** `decode_order_*` uzunluk yetersizse varsayılan struct ve boş token döner, `dispatch_message` callback'i yine çağırır; accept/replace yolunda `""` adopt edilir (3 ile aynı etki).
6. **doğrula: Desteklenmeyen TIF sessizce Day olur.** `encode_tif` `GoodTillCancel`, `GoodTillDate`, `AtCrossing` için 0 (Day) yazar; ret veya hata yok (`MAOrderSDK.cpp`'de TIF kontrolü yok, grep).
7. **doğrula: Fiyat ve orderbook kesmesi.** `encode_enter_order`/`encode_replace_order` `int64` fiyatı ve `uint64` orderbook'u kontrolsüz 32 bite keser.
8. **doğrula: Match ID'nin üst 4 baytı atılıyor.** `decode_order_executed` 12 baytlık Match ID'nin yalnız son 8 baytını okur. Combiner ve host dedup'ı `match_id`'ye dayanıyorsa üst baytlarda fark eden iki fill çakışabilir.
9. **doğrula: Kısmi yazımda akış bozulması.** `send_raw_slow` mesajın bir kısmını yazıp 1 s `select` timeout'unda `false` döner; connection düşürülmez. TCP akışında yarım OUCH çerçevesi kalır ve sonraki mesajlar BIST'te yanlış çerçevelenir.
10. **doğrula: Replace 125 bayt.** Spec 122 diyor; kod prod encoder'ı izliyor (§8.2).
11. **doğrula: Login failover yalnız TCP'de.** Birincil gateway TCP kabul edip login'e cevap vermezse (ör. standby) ikincil denenmez (`connect_with_diagnostics`).
12. **doğrula: Heartbeat ve warm etkileşimi.** Heartbeat thread'i her `heartbeat_interval_ms`'de `mark_sent` yaptığı için `warm_interval_ms >= heartbeat_interval_ms` iken warm hiç kurulmaz. Kurulursa da bir sonraki gönderimde tüketilir; bu gönderim heartbeat olabilir.
13. **Ölü kod / kullanılmayan durum:** `logout()`, `encode_logout`, `IConnection::receive`, `kCancelByOrderIdLen`, `current_session_`, `current_sequence_`, `current_seq_num_` (login'de sıfırlanmıyor). Order State, TIF, Client Category, SMP alanları decode edilmiyor.
14. **doğrula: `onUserConnected` ile replay yarışı.** Recv thread'i `onUserConnected`'dan önce başlar; host bağlantı durumunu `onUserConnected`'da kuruyorsa ilk replay callback'leri ondan önce gelebilir (`connect_with_diagnostics`).
