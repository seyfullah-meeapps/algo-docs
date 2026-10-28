---
kapsam: MAOrderSDK public API'si (metotlar, config ve mesaj struct'ları, enum'lar), boot sırası ve SDK yaşam döngüsü, kullanıcı/bağlantı modeli, callback'lerin thread'leri ve onSdkError kodları, SDK içi thread ve kilit modeli
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: order-service
    branch: development
    commit: b86c0cf
dogrulama: 2026-10-22
durum: taslak
---

# MAOrderSDK — public API ve yaşam döngüsü

Özet ve dosya yapısı: [README.md](README.md). Bu dosyada anlatılmayan konular:
- enter/cancel/replace iç yolu, token ve `client_order_id` tabloları, bölme, yerel ret tablosu, hard cap, combiner → [emir-akisi.md](emir-akisi.md)
- `OuchConnection`, SoupBinTCP, login, heartbeat, failover, replay, byte düzenleri → [ouch-protokolu.md](ouch-protokolu.md)
- `FixEngine`, QuickFIX oturumları, PossDup, şifre yaşam döngüsü, 1409 kodları → [fix.md](fix.md)

Kod: `public/MAOrderSDK.h`, `public/MAOrderStruct.h`, `public/MAOrderEnums.h`, `src/MAOrderSDK.cpp` (`MAOrderSDK::Impl`).

## 1. Public metotlar (`maordersdk::MAOrderSDK`)

"Config-time" ifadesi şu anlama gelir: `start()`'tan önce, tek thread'den çağrılmalı. Bu metotlar kilit almaz.

| Metot | Ne yapar | Ne zaman / thread-safety | Dönüş |
|-------|----------|--------------------------|-------|
| `setOuchConfig(const OuchConfig&)` | Config'i kopyalar. Token havuzunu `token_pool_size` kadar yeniden üretir. `connections` ve `account_routes_`'u **siler**, yeniden kurar. `protocol==Fix` kullanıcılar için `FixEngine` + `FixConnection` havuzu kurar. Geçersiz `market` görürse `std::exit(1)`. | Config-time. `start()`'tan sonra çağrılırsa heartbeat thread'inin gezdiği bağlantılar yok edilir (UB). | — |
| `setSdkConfig(const OrderSdkConfig&)` | Config'i kopyalar, mevcut OUCH connection'lara `recv_pin_core`, `warm_interval_ms`, `replay_quiet_window_ms` ve `OuchConfig.heartbeat_timeout_ms`'yi yayar. `setOuchConfig` ile sırası önemsizdir; ikisi de birbirinin değerini uygular. | Config-time. FIX oturumlarına uygulanmaz. | — |
| `setItchSdk(itch::ItchSdk*)` | Combiner için ITCH SDK pointer'ını saklar. Yalnız `start()` okur. | `start()`'tan önce. | — |
| `setInstrumentLimits(map<uint64_t, InstrumentLimit>)` | Bölme tablosunu kopyalar (anahtar `orderbook_id`). Tablo boşsa bölme ve 1001–1004 kontrolleri hiç çalışmaz. | Config-time. Çalışırken kilitsiz okunur, bu yüzden canlıda değiştirilmemeli. | — |
| `setStartArguments(int argc, char** argv)` | Onload self-restart için `argv`'yi saklar. Kopyalamaz; pointer'lar süreç boyunca geçerli kalmalıdır. | `bootstrapOnloadIfRequested`'dan önce. | — |
| `bootstrapOnloadIfRequested()` | §3.2. Başarılı olursa `execvp` yapar ve **geri dönmez**. | `setSdkConfig` + `setStartArguments`'tan sonra, `main()`'in başında. | — |
| `setCallbacks(const Callbacks&)` | Callback'leri kopyalar, mevcut OUCH connection'lara çeviri lambda'larını yeniden kurar. Lambda'lar `impl_->callbacks`'i canlı okur. | Config-time. `start()`/`connectUser` sonrası çağrılırsa recv thread'lerinin okuduğu `std::function`'lar kilitsiz değişir. | — |
| `start()` | §3.1. | Bir kez. | `false`: zaten çalışıyor, ya da `FixEngine::start` başarısız (`onSdkError(20)`; `running` geri alınır, tekrar denenebilir). |
| `stop()` | Heartbeat thread'ini durdurur ve join eder, bütün OUCH connection'ları `disconnect()` eder, `FixEngine::stop`, combiner stop. Destructor da çağırır. | Çağıran thread'de `onUserDisconnected` tetiklenir (bağlı olan her OUCH kullanıcısı için). Join, en çok bir `heartbeat_interval_ms` sürebilir. | — |
| `connectUser(const std::string&)` | Statik kullanıcıya bağlanır (§4.1). OUCH'ta **bloklar**. | `connections_mutex_` yalnız arama sırasında tutulur. Aynı kullanıcı için iki thread'den eşzamanlı çağrılmamalı. | `ConnectResult` (§5.4) |
| `connectUser(const OuchUser&)` | Dinamik kayıt + bağlanma (§4.1). | Heartbeat thread'ine karşı güvenli. Emir akışına karşı güvenli değil (Şüpheli 4). | `ConnectResult` |
| `disconnectUser(const std::string&)` | OUCH: `OuchConnection::disconnect()` (LogoutRequest yok, soket kapanır, recv thread join). FIX: `Session::logout()`, oturum devre dışı kalır. | Recv thread'inden çağrılırsa join atlanır. | Kullanıcı bilinmiyorsa `false`. |
| `isConnected(username)` | OUCH: `connected_` bayrağı. FIX: `Session::isLoggedOn`. | Thread-safe. | |
| `isConnected()` | Herhangi bir OUCH bağlı ya da herhangi bir FIX oturumu logon'lu mu? | Thread-safe. | |
| `ownsAccount(account)` | §4.3 | Thread-safe (`connections_mutex_`). | |
| `ownsOrder(client_order_id)` | §4.3 | Thread-safe (`maps_mutex`). | |
| `enterOrder(msg)` / `enterOrder(msg, on_token_assigned)` | Emir gönderir. Bölme, yerel ret ve token mantığı → [emir-akisi.md](emir-akisi.md). | Çok thread'den çağrılabilir. Callback'ler (yerel ret, token ataması) çağıran thread'de, SDK kilidi tutulmadan çalışır. | `true` = (bütün parçalar) wire'a yazıldı. `false` = en az bir parça gitmedi ya da yerel ret. |
| `cancelOrder(client_order_id)` | Tek emir ya da split parent'ın bütün çocukları. | Çok thread'den çağrılabilir. | `true` = (bütün) cancel mesajları yazıldı. |
| `replaceOrder(msg)` / `replaceOrder(msg, on_token_assigned)` | Tek emir ya da split parent (yalnız fiyat yayılır). | Çok thread'den çağrılabilir. | `true` = (bütün) replace mesajları yazıldı. |
| `setFavoriteOuch(account, ouch_username)` | Hesabın round-robin favorisini ayarlar (§4.2). | Atomik yazar, `account_routes_`'u kilitsiz okur. Hesap ya da kullanıcı yoksa `onSdkError(11)`. | — |
| `clearFavoriteOuch(account)` | Favoriyi kaldırır. | Aynı. | — |
| `armFixPasswordChange(user, new_pw)` | → [fix.md](fix.md) | `creds_mutex_`. | Bilinmeyen/FIX olmayan kullanıcıda ya da boş şifrede `false`. |
| `setFixPassword(user, pw)` | → [fix.md](fix.md) | Aynı. | Aynı. |
| `adoptFixOrders(vector<AdoptedFixOrder>)` | → [fix.md](fix.md) | `setOuchConfig`'den sonra, `start()`'tan önce ya da sonra. | Adopt edilen emir sayısı. FIX yoksa 0. |
| `generateBistFixPassword(size_t len=10)` (serbest fonksiyon) | → [fix.md](fix.md) | Thread-safe. | |

`OrderTokenAssignedCallback` = `std::function<void(const OrderTokenAssignment&)>`. Token atandıktan ve haritaya yazıldıktan sonra, soket yazımından **önce**, çağıran thread'de çalışır. İstisna fırlatırsa kayıt geri alınır ve `onSdkError(15)` verilir. Ayrıntı: [emir-akisi.md](emir-akisi.md).

## 2. Struct'lar ve enum'lar

### 2.1 Config struct'ları

**`OuchEndpoint`**

| Alan | Tip | Varsayılan | Anlam |
|------|-----|-----------|-------|
| `ip`, `port` | string, `uint16` | "", 0 | Birincil. Boş ya da 0 ise denenmez. |
| `secondary_ip`, `secondary_port` | string, `uint16` | "", 0 | Birincil TCP bağlanamazsa denenir → [ouch-protokolu.md](ouch-protokolu.md) |

**`OuchCredentials`**: `username` (SDK içinde kullanıcının anahtarı, benzersiz olmalı), `password` (`<REDACTED>`), `allowed_accounts` (vector<string>; routing ve `ownsAccount` bununla yapılır).

**`OuchUser`**

| Alan | Tip | Varsayılan | Anlam |
|------|-----|-----------|-------|
| `endpoint`, `credentials` | yukarıda | | |
| `market` | `Market` | **başlatılmamış** | `Equity` (1) ya da `Derivative` (2). Başka değer `setOuchConfig`'de `std::exit(1)`. Değer verilmezse çöp kalabilir. |
| `partition` | `uint32` | 0 | SDK içinde kullanılmıyor. |
| `morning_only` | bool | false | SDK içinde kullanılmıyor (yalnız host). |
| `recv_pin_core` | int | -1 | Recv thread'inin CPU çekirdeği. -1 → `OrderSdkConfig.recv_pin_core`. |
| `recv_sched_policy` | int | `SCHED_OTHER` | `SCHED_FIFO`/`SCHED_RR` için `CAP_SYS_NICE` gerekir. Başarısızlık yalnızca stderr uyarısı verir. |
| `recv_sched_priority` | int | 0 | `sched_param.sched_priority` |
| `protocol` | `WireProtocol` | `Ouch` | `Fix` → kullanıcı FIX havuzuna gider |
| `fix_sender_comp_id`, `fix_target_comp_id`, `fix_sender_sub_id` | string | "" | FIX header 49 / 56 / 50 |
| `fix_new_password` | string | "" | Doluysa ilk Logon şifre değişikliği yapar → [fix.md](fix.md) |

**`FixSessionConfig`** (`OuchConfig.fix_session`, yalnız en az bir FIX kullanıcısı varsa kullanılır; anlamları → [fix.md](fix.md))

| Alan | Varsayılan | Alan | Varsayılan |
|------|-----------|------|-----------|
| `begin_string` | `FIXT.1.1` | `reset_on_logon` / `_logout` / `_disconnect` | true / true / true |
| `default_appl_ver_id` | `FIX.5.0SP2` | `use_data_dictionary` | true |
| `connection_type` | `initiator` | `data_dictionary` | `/usr/local/include/quickfix/spec/FIX50SP2.xml` |
| `file_store_path`, `file_log_path` | "" | `use_transport_data_dictionary` | true |
| `allow_unknown_msg_fields` | true | `transport_data_dictionary` | `.../FIXT11.xml` |
| `validate_user_defined_fields` / `_messages` | false / false | `reconnect_interval` | 3600 (**s**, `uint16`) |
| `replay_from_seq` | 1 (0 = store'a dokunma) | `heart_bt_int` | 30 (**s**) |

**`OuchConfig`**

| Alan | Tip | Varsayılan | Birim | Anlam |
|------|-----|-----------|-------|-------|
| `ouch_users` | vector<`OuchUser`> | boş | | OUCH ve FIX kullanıcıları birlikte |
| `heartbeat_interval_ms` | `uint32` | 1000 | ms | Heartbeat thread'inin her bağlı OUCH connection'a ClientHeartbeat gönderme aralığı |
| `token_pool_size` | `uint32` | 100000 | adet | Önceden üretilen 14 karakterlik token. Bitince `maps_mutex` altında üretilir. |
| `heartbeat_timeout_ms` | `uint32` | 5000 | ms | Recv watchdog'u: bu süre paket gelmezse `onHeartbeatTimeout` (connect döngüsü başına bir kez). 0 = kapalı. Soketi kapatmaz. |
| `fix_session` | `FixSessionConfig` | | | |

**`OrderSdkConfig`**

| Alan | Tip | Varsayılan | Birim | Anlam |
|------|-----|-----------|-------|-------|
| `send_pin_core` | int | -1 | çekirdek | **Kullanılmıyor.** SDK'da send thread'i yoktur; gönderim çağıran thread'de yapılır. |
| `recv_pin_core` | int | -1 | çekirdek | Bütün OUCH recv thread'leri için varsayılan pin. Kullanıcı başına override `OuchUser.recv_pin_core`. |
| `lock_memory` | bool | false | | `start()`'ta `mlockall(MCL_CURRENT\|MCL_FUTURE)`. Başarısızsa `onSdkError(6)` ile devam eder. |
| `use_onload` | bool | false | | `bootstrapOnloadIfRequested` self-restart (§3.2) |
| `warm_interval_ms` | int | 0 | ms | 0 = kapalı. >0: bu süre gerçek gönderim olmazsa sonraki gönderimden önce `ONLOAD_MSG_WARM`. Yalnız Onload build'inde. |
| `replay_quiet_window_ms` | `uint32` | 10000 | ms | OUCH replay sonu: bu süre SequencedData gelmemişse ve en az bir ServerHeartbeat görülmüşse `onReplayCompleted`. |
| `favorite_idle_reset_ms` | `uint32` | 1000 | ms | §4.2 |
| `order_hard_cap_try` | `uint32` | 50000000 | **tam TL** | Notional üst sınırı (1003) → [emir-akisi.md](emir-akisi.md) |
| `enable_combiner` | bool | false | | `start()`'ta combiner'ı kurar. `setItchSdk` verilmemişse `onSdkError(13)`. SDK ITCH olmadan derlendiyse (`MAORDER_HAS_ITCHSDK=0`) sessizce etkisizdir. |

**`InstrumentLimit`**: `max_order_value` (`uint32`, emir başına notional limiti, **tam TL**), `decimal_count` (`uint32`, fiyat ondalık basamağı; raw fiyat = TL × 10^`decimal_count`), `is_brut_takas` (bool; limit bloğunda ve skip_brut_takas=false iken true → 1002). 24 Ekim development `c2b5060` per-call seçenek overload'ı için [güncel emir akışı](emir-akisi.md#7-cancelorder-ve-replaceorder).

### 2.2 İstek struct'ları

**`EnterOrderMsg`**

| Alan | Tip | Birim / anlam |
|------|-----|---------------|
| `client_order_id` | string | Boş → SDK'nın ürettiği 14 karakterlik token public id olur (iki host da bunu kullanır) |
| `orderbook_id` | `uint64` | BIST orderbook id; `InstrumentLimit` anahtarı |
| `side` | `Side` | |
| `quantity` | `uint64` | **lot**. 0 → yerel ret 1006 |
| `price` | `int64` | **raw** = TL × 10^`decimal_count`. Market/MarketWithLeftoverLimit dışında 0 → yerel ret 1005 |
| `tif`, `ord_type`, `open_close`, `client_category`, `off_hours` | enum | Varsayılan `Day`, `Standard`, `Default`, `Client`, `NormalHours` |
| `client_account`, `exchange_info` | string | Wire hesap alanları |
| `routing_account` | string | Yalnız SDK route anahtarı, wire'a gitmez. Route anahtarı önceliği: `routing_account` → `client_account` → `exchange_info` |
| `preferred_ouch_username` | string | Exact route (§4.2). Boş = hesap round-robin |
| `display_quantity` | `uint64` | lot |
| `smp_level`, `smp_method`, `smp_id` | enum, string | |
| `no_split` | bool | Bölmeyi atlar. Enstrüman kontrolü ve hard cap yine uygulanır. |
| `passthrough` | string | Host'un opak Customer Info alanı |
| `expire_date` | `uint64` | **epoch saniye**. Yalnız FIX GTD (tag 432); OUCH yok sayar |

**`ReplaceOrderMsg`**: `client_order_id` (değişecek emir, zorunlu), `new_client_order_id` (boş → SDK atar), `quantity` (lot), `price` (raw), `client_account`, `passthrough`. 0 değerlerinin anlamı → [emir-akisi.md](emir-akisi.md).

**`OrderTokenAssignment`**: `client_order_id` (etkin id), `quantity` (lot; parçada parça miktarı, replace'te etkin miktar), `ouch_username` (taşıyan bağlantı; yerel retlerde boş). **`CancelOrderMsg`**: boş struct, kullanılmıyor.

**`AdoptedFixOrder`**: `client_order_id`, `fix_username`, `order` (`EnterOrderMsg`), `cum_qty` (lot), `order_id`. → [fix.md](fix.md)

### 2.3 Olay struct'ları

Ortak kurallar:
- `price` **raw** (`int64`), `quantity` **lot**.
- `timestamp`: OUCH'ta BIST wire Timestamp alanı (epoch ns). FIX'te TransactTime(60) ns'ye çevrilir.
- `client_order_id`: SDK haritasından çevrilir. Harita kaydı yoksa (restart replay'i) wire token'ın kendisidir.
- `ouch_username`: emri taşıyan bağlantı.
- `latency_*_ns` (epoch ns farkları, 0 = bilinmiyor/replay/yerel ret):
  - `writing` = soket `write` süresi
  - `network` = yazım sonu → cevabın yerelde alınması
  - `bist` = yazım sonu → BIST damgası
- `is_replay`: yalnız FIX PossDupFlag=Y'de true. OUCH replay'inde hep false.

| Struct | Alanlar (ortaklar dışında) |
|--------|----------------------------|
| `OrderAcceptedMsg` | `order_id`, `orderbook_id`, `side`, `quantity`, `price`, `pre_trade_quantity`, `account` (wire'da boşsa gönderim kaydından), `passthrough`, latency'ler |
| `OrderRejectedMsg` | `reject_code` (`int32`: BIST negatif kodu ya da SDK yerel kodu), `reject_reason`, `passthrough`, `orderbook_id`, `account`, `quantity` (gönderilen). Wire reject'te son dördü gönderim kaydından doldurulur. Latency'ler |
| `OrderExecutedMsg` | `orderbook_id`, `quantity` (fill), `price` (fill), `match_id` (combiner'ın ITCH'ten ürettiği fill'de 0). Latency **yok**. |
| `OrderCanceledMsg` | `order_id`, `orderbook_id`, `side`, `reason_code`, `quantity`, latency'ler (cancel yazımına göre) |
| `OrderReplacedMsg` | `previous_client_order_id`, `order_id`, `orderbook_id`, `side`, `quantity`, `price`, `pre_trade_quantity`, `account`, `passthrough`, latency'ler |

Wire alanlarının anlamı (`quantity` = kalan mı vb.): [ouch-protokolu.md](ouch-protokolu.md), [fix.md](fix.md).

### 2.4 Enum'lar (`MAOrderEnums.h`)

| Enum | Değerler |
|------|----------|
| `Side : char` | `Unknown=0`, `Buy='B'`, `Sell='S'`, `ShortSell='T'` |
| `TimeInForce` | `Unknown, Day, ImmediateOrCancel, FillOrKill, GoodTillCancel, GoodTillDate, AtCrossing` (0..6) |
| `OrdType` | `Unknown, Standard, Market, Limit, MarketWithLeftoverLimit` (0..4) |
| `Market` | `Equity=1`, `Derivative=2` |
| `ClientCategory` | `Client=0, House, Fund, Unknown, InvestmentTrust, PrimaryDealerGovt, PrimaryDealerCorp, PortfolioManagementCompany`. `Unknown` VİOP içindir, wire'a 0 gider. |
| `OpenClose` | `Default, Open, Close` |
| `OffHours` | `NormalHours, OffHours` |
| `SMPLevel` | `Unknown=0, WithinMember=1, AcrossMembers=2` |
| `SMPMethod` | `Unknown=0, CancelAggressive=1, CancelPassive=2, CancelBoth=3` |
| `WireProtocol` | `Ouch=0, Fix=1` |
| `LoginFailureReason` | `Unknown, NotAuthorized, SessionNotAvailable, Timeout, NetworkError` |
| `ConnectResult` | `Ok, AlreadyConnected, UserNotFound, TcpFailed, LoginRejected, LoginTimeout` |
| `StrategyType` (unscoped) | `USER=1, AKD=3, HFT=4, … MIN_PRICE=14`. SDK içinde kullanılmıyor. |

`to_string(ConnectResult)` ve `to_string(LoginFailureReason)` log metni üretir. `LoginTimeout`: "no response (possibly connected elsewhere)".

## 3. Boot ve yaşam döngüsü

### 3.1 Zorunlu sıra ve nedeni

| # | Çağrı | Neden bu sırada |
|---|-------|-----------------|
| 1 | `setOuchConfig` | Connection'ları, hesap rotalarını, token havuzunu ve `FixEngine`'i kurar. Tekrar çağrılırsa hepsi sıfırlanır. |
| 2 | `setSdkConfig` | `use_onload` (3.2), `lock_memory` ve `enable_combiner` (`start`) okunmadan önce set edilmelidir. 1 ile sırası serbesttir. |
| 3 | `setItchSdk` | Yalnız combiner için. `start()` okur. |
| 4 | `setInstrumentLimits` | İlk `enterOrder`'dan önce; kilitsiz okunur. |
| 5 | `setCallbacks` | Bootstrap'tan önce gelirse `onSdkError(7)` görülür; sonra gelirse kaybolur (Şüpheli 2). `start`'tan ve bağlantılardan önce gelmelidir. |
| 6 | `setStartArguments` + `bootstrapOnloadIfRequested` | `execvp` süreci baştan başlatır. Öncesinde açılan soket/thread'ler yeni süreçte yeniden kurulur. Header "call early in main()" der. |
| 7 | `start()` | Aşağıda. |
| 8 | `connectUser` | OUCH için heartbeat thread'i `start()` ile başlar. FIX oturumları `start()`'tan önce yoktur (§4.1). |

**`start()` adımları:** `running` = true → `lock_memory` ise `mlockall` → `enable_combiner` ise combiner kurulur (ITCH pointer yoksa 13) → PerfSDK metrikleri kaydedilir (host `PerformanceClient::start()`'ı önce çağırmış olmalı, yoksa id 0 ve ölçüm no-op) → `FixEngine::start()` (QuickFIX `SocketInitiator`; oturumlar `logout("awaiting connectUser")` ile **kapalı** başlar) → heartbeat thread'i. Hiçbir kullanıcıya bağlanmaz.

### 3.2 Onload bootstrap (`bootstrapOnloadIfRequested`)

- Yalnız Onload build'inde (`MAORDER_HAS_ONLOAD=1`, CI'da `libMAOrderSDK_Onload.so`) çalışır; diğerinde no-op. `use_onload` false, `MAORDER_ONLOAD_BOOTSTRAPPED` set ya da `LD_PRELOAD` set ise bir şey yapmaz. `argv` yoksa `onSdkError(7)`.
- Env: `EF_POLL_USEC=100000`, `EF_TX_PUSH=1`, `EF_PIO=1`, `EF_CTPIO=1`, `EF_FORCE_TCP_NODELAY=1`, `EF_USE_HUGE_PAGES=2`, `EF_LOG=warnings`, `LD_PRELOAD=libonload.so`, `MAORDER_ONLOAD_BOOTSTRAPPED=1`. Sonra `execvp(argv[0], argv)`. Başarısızsa `onSdkError(7, "... errno N")`, süreç Onload'suz devam eder. Header'daki "no-op in Phase A" yorumu güncel değil.

### 3.3 Pinleme ve bellek

- **OUCH recv thread'i** (`OuchConnection::apply_recv_thread_config`): çekirdek `OuchUser.recv_pin_core`, yoksa `OrderSdkConfig.recv_pin_core`. Global değer kullanılırsa bütün recv thread'leri **aynı** çekirdeğe pinlenir.
- Heartbeat ve QuickFIX thread'leri pinlenmez. Gönderim çağıran thread'dedir (`send_pin_core` etkisiz). Bellek: yalnız `lock_memory` → `mlockall`.

### 3.4 İki hostun boot'u

| | HftSrvProd (`src/Main/HftMain.cpp`) | order-service (`MAOSdkManager::StartProperly`) |
|-|------------------------------------|-----------------------------------------------|
| Kullanıcılar | `#SpotOuchConfiguration`'da `isActive=true` olanlar, yalnız OUCH | trade-data-app'ten OUCH + FIX |
| `heartbeat_interval_ms` / `heartbeat_timeout_ms` | config / **set edilmez** (5000) | 3000 / 15000 |
| `OrderSdkConfig` | Bütün alanlar config'ten (`sdk*`, `combinerEnabled`) | `order_hard_cap_try` dışı varsayılan |
| `setItchSdk` | combiner açıksa | yok |
| `setInstrumentLimits` | var | var |
| Sıra | Önce PerfSDK, sonra ITCH client start. Ardından setOuchConfig → setSdkConfig → setItchSdk → limits → setStartArguments → **bootstrap** → setCallbacks → start | setOuchConfig → setSdkConfig → limits → setCallbacks → `adoptFixOrders` → start. Bootstrap yok. |
| Açılışta `connectUser` | **Yok.** Handoff'ta `connectUser(OuchUser)` çağrılır → [hftsrvprod/emir-yasam-dongusu § 4](../hftsrvprod/emir-yasam-dongusu.md) | Her OUCH kullanıcısı için sırayla `connectUser(username)`, ardından FIX → [order-service/sdk-ve-oturumlar § 1](../order-service/sdk-ve-oturumlar.md) |
| `setFavoriteOuch` | kullanılmıyor | kullanılmıyor |
| Reconnect | SDK'da otomatik reconnect yoktur. HFT reconnect yapmaz. | OUCH shim'i (1 s döngü) |

## 4. Kullanıcı ve bağlantı modeli

### 4.1 `connectUser`

**Statik (`connectUser(username)`):**
- OUCH'ta bulunursa: bağlıysa `AlreadyConnected`. Değilse `OuchConnection::connect_with_diagnostics` **bloklar**: önceki recv thread join → TCP birincil (2 s), olmazsa ikincil (2 s) → SoupBinTCP login (2 s) → replay/watchdog durumu sıfırlanır, recv thread başlar, **çağıran thread'de** `onUserConnected`. En kötü ~6 s.
- FIX'te bulunursa: logon'luysa `AlreadyConnected`; değilse `Session::logon()` ile oturum etkinleştirilir ve hemen `Ok` döner (**asenkron**, sonuç callback'lerle). `Session` yoksa (`start()` öncesi) `UserNotFound`.
- İkisinde de yoksa `UserNotFound`.

**Dinamik (`connectUser(const OuchUser&)`):**
- `username` zaten kayıtlıysa **mevcut connection** kullanılır; verilen endpoint/şifre yok sayılır.
- Değilse `setOuchConfig`'deki gibi `OuchConnection` kurulur (callback, pin, warm, quiet window, watchdog, PerfSDK). `connections_mutex_` altında `connections`'a ve her hesabın `account_routes_` girdisine eklenir; sonra kilit dışında bloklayan connect. `protocol` alanına bakılmaz (Şüpheli 3).

**Reconnect:** SDK kendiliğinden yeniden bağlanmaz. Kopmadan sonra host `connectUser` çağırmalıdır. `onUserDisconnected` callback'i içinden (recv thread) çağrılırsa `TcpFailed` döner; reconnect başka bir thread'den yapılmalıdır.

### 4.2 Hesap → bağlantı eşlemesi, round-robin, favori

- **`account_routes_`** (`unordered_map<string, AccountRoute>`): yalnız OUCH. `setOuchConfig`'de `allowed_accounts`'tan kurulur, dinamik kullanıcıyla büyür, hiç silinmez (kopuk bağlantı listede kalır). `AccountRoute`: `conns` (config sırası), atomik `rr`, `favorite_idx` (-1 = yok), `last_order_ns` (CLOCK_MONOTONIC ns).
- **FIX havuzu** (`fix_account_routes_`): ayrı harita, kendi `rr`'ı; favori yok.
- **Havuz seçimi** (`Impl::routes_to_fix`): `preferred_ouch_username` doluysa, FIX kullanıcısıysa FIX, değilse OUCH. Boşsa hesap OUCH haritasında **yoksa** ve FIX'te varsa FIX, aksi halde OUCH. Round-robin havuzlar arası geçmez.
- **Round-robin** (`Impl::round_robin`): `rr.fetch_add(1)`'den başlayıp ilk bağlı connection. Hiçbiri bağlı değilse `onSdkError(1)` + `false`.
- **Exact route** (`pick_connection(account, username)`): `connections_mutex_` altında adı eşleşen, hesabın sahibi ve bağlı connection. Yoksa başkasına **düşmez**.
- **Favori** (yalnız favori set iken): her emirde `last_order_ns` güncellenir; ilk emirde ya da `now - prev >= favorite_idle_reset_ms` ise `rr` favori indeksine çekilir (patlama favoriden başlar, sonra dönüş sürer). Favori kopuksa sıradaki bağlı seçilir. Favorisiz `rr` kaldığı yerden devam eder. Dinamik kullanıcıya favori `connectUser(OuchUser)`'dan **sonra** verilmeli, yoksa `onSdkError(11)`.
- **Bölmede:** çocuk 0 favori-duyarlı, 1..N ham round-robin → [emir-akisi.md](emir-akisi.md).

### 4.3 `ownsAccount` / `ownsOrder` tam semantiği

**`ownsAccount(account)`:**
- OUCH tarafı: `connections`'ta `is_connected()` olan ve `allowed_accounts`'unda hesap bulunan herhangi bir connection varsa true.
- FIX tarafı: logon'lu herhangi bir oturum hesabı taşıyorsa true.
- `account_routes_`'a ve `preferred_ouch_username`'e bakmaz. Hesap anahtarını host verir; SDK route anahtarı (`routing_account` → `client_account` → `exchange_info`) ile aynı olmalıdır.

**`ownsOrder(client_order_id)`:** OUCH `wire_by_client`, `split_parents_` ya da `FixEngine::orders_`'ta varsa true. Replay ile adopt edilenler de girer. Kayıtlar cancel/fill/reject ile **silinmez** (yalnız replace eski id'yi siler); bitmiş emir için de true döner. Yerel ret (1001–1006, 1) ve gönderim hatası (4/5/6/15) kayıt bırakmaz → false.

**Host deseni:** `enterOrder` false + `ownsAccount` false → yedek yol; cancel/replace false + `ownsOrder` false → yedek yol. SDK sahipse yedek yola gidilmez (ghost emir riski). Bkz. [hftsrvprod/emir-yasam-dongusu § 2](../hftsrvprod/emir-yasam-dongusu.md).

## 5. Callback'ler

### 5.1 Liste ve thread'ler

| Callback | İmza | OUCH thread'i | FIX thread'i |
|----------|------|---------------|--------------|
| `onUserConnected` | `(const string& username)` | `connectUser`'ı **çağıran** thread (recv thread başladıktan sonra) | QuickFIX initiator (`onLogon`) |
| `onUserDisconnected` | `(username)` | Kopmada recv thread'i. `disconnectUser`/`stop` çağrıldığında çağıran thread. | QuickFIX (`onLogout`) |
| `onLoginFailed` | `(username, LoginFailureReason)` | `connectUser`'ı çağıran thread. TCP her iki uca da bağlanamazsa **çağrılmaz**. | çağrılmaz |
| `onHeartbeatTimeout` | `(username)` | recv thread (100 ms idle tick) | çağrılmaz |
| `onReplayCompleted` | `(username)` | recv thread | QuickFIX |
| `onSdkError` | `(int code, const string&)` | Kaynağa göre (§5.3) | |
| `onAccepted`, `onRejected` (wire), `onCanceled`, `onReplaced` | `(const Order*Msg&)` | Emrin recv thread'i | QuickFIX |
| `onRejected` (yerel/sentetik) | | `enterOrder`'ı çağıran thread, senkron | aynı |
| `onExecuted` | `(const OrderExecutedMsg&)` | Recv thread. Combiner açıksa ITCH client thread'i de olabilir. | QuickFIX |
| `onWireExecuted` | `(const OrderExecutedMsg&)` | Her zaman recv thread, `onExecuted`'dan önce | QuickFIX, `onExecuted`'dan önce |
| `onFixPasswordChangeResult`, `onFixLogonRejected` | `(username, int session_status)` | — | QuickFIX → [fix.md](fix.md) |

### 5.2 Sıralama garantileri

- Emir callback'leri SDK kilidi (`maps_mutex`) **bırakıldıktan sonra** çağrılır. Callback içinden `enterOrder`/`cancelOrder` çağırmak deadlock üretmez.
- Bir connection'ın olayları wire sırasıyla tek thread'den gelir. Connection'lar arasında sıra garantisi yoktur.
- Combiner açıkken:
  - `onExecuted` için emir başına sıra yoktur.
  - `onWireExecuted` accept ile aynı thread'den gelir ve emir başına sıralıdır.
- OUCH'ta `onUserConnected` recv thread başlatıldıktan sonra çağıran thread'de tetiklenir. Replay'in ilk olayları onunla eşzamanlı ya da ondan önce gelebilir (Şüpheli 5).
- **`onReplayCompleted`** (logon başına bir kez):
  - OUCH (`OuchConnection::maybe_fire_replay_completed`, paket gelince ve 100 ms idle tick'te): en az bir ServerHeartbeat görülmüş **ve** `now - max(son SequencedData, login anı) >= replay_quiet_window_ms`. Replay boşsa pencere login anından sayılır. Sezgiseldir; pencereden sonra gelen bir replay mesajı `onReplayCompleted`'dan sonra gelir.
  - FIX: PossDup replay'i bitince ya da Logon cevabında gap yoksa hemen → [fix.md](fix.md).
- Bağlantı kesildiğinde OUCH'ta combiner, `onUserDisconnected`'dan önce `poison_all` yapar. FIX'te bu yapılmaz.
- Host callback'inden fırlayan istisnayı SDK yakalamaz. İstisna yalnız token callback'inde yakalanır (Şüpheli 9).

### 5.3 `onSdkError` kodları

| Kod | Kaynak | Mesaj / durum | Ek olarak `onRejected`? |
|-----|--------|---------------|-------------------------|
| 1 | `enterOrder` (bölünmeyen, OUCH/FIX) | hesabın bağlı connection'ı yok (exact route bulunamadı dahil) | Hayır. Split'te `onSdkError` yok, `onRejected(1)` var. |
| 4 | `enterOrder` / `replaceOrder` | duplicate `client_order_id` / `new_client_order_id` | enter: evet, replace: hayır |
| 5 | enter / cancel / replace | encode başarısız | yalnız enter |
| 6 | `enterOrder` | wire send başarısız | evet |
| 6 | `start` | `mlockall` başarısız (devam eder) | — (aynı kod, Şüpheli 1) |
| 7 | `bootstrapOnloadIfRequested` | `argv` yok / `execvp` başarısız | — |
| 8 | `replaceOrder` | boş `client_order_id` | hayır |
| 9 | cancel / replace (OUCH) | bilinmeyen `client_order_id` | hayır |
| 10 | cancel / replace (OUCH) | emrin connection'ı yok ya da kopuk | hayır |
| 11 | `setFavoriteOuch` | bilinmeyen hesap / kullanıcı hesabın sahibi değil | — |
| 12 | `replaceOrder` (split parent) | bölünmüş emrin miktarı değiştirilemez | hayır |
| 13 | `start` / `Combiner` | ITCH pointer yok (combiner kapalı); ya da `poisoned order <id>` | — |
| 14 | `Combiner` | ITCH trampoline'i başka örnek tutuyor | — |
| 15 | enter / replace | token-assignment callback istisna fırlattı | enter: evet |
| 20 | `FixEngine::start` | QuickFIX başlatılamadı; `start()` false döner | — |
| 21 | `FixEngine::send_to` | FIX gönderim hatası (bilinmeyen kullanıcı / istisna) | → [fix.md](fix.md) |
| 22 | `FixEngine` | bilinmeyen ClOrdID/token için ExecutionReport veya CancelReject | — |

OUCH cancel/replace'te soket yazımı başarısız olursa yalnız `false` döner; `onSdkError` verilmez. Yerel `onRejected` kodları (1001–1006 ve 1/4/5/6/15): [emir-akisi.md](emir-akisi.md).

### 5.4 `ConnectResult` (OUCH)

| Sonuç | Durum |
|-------|-------|
| `Ok` | Login kabul edildi. FIX'te yalnız oturum etkinleştirildi. |
| `AlreadyConnected` | Zaten bağlı / logon'lu |
| `UserNotFound` | Kullanıcı yok. FIX'te ayrıca `start()` öncesi. |
| `TcpFailed` | İki uca da TCP kurulamadı, login `NetworkError`, ya da recv thread'inden çağrıldı |
| `LoginRejected` | LoginRejected `A`/`S`, login sırasında EndOfSession, bilinmeyen sebep |
| `LoginTimeout` | 2 s içinde login cevabı yok |

Login cevabı → `LoginFailureReason`: `A` → `NotAuthorized`, `S` / EndOfSession → `SessionNotAvailable`, süre doldu → `Timeout`, encode/yazma/okuma hatası → `NetworkError`. Ayrıntı: [ouch-protokolu.md](ouch-protokolu.md).

## 6. Thread modeli ve kilitler (SDK içi)

| Thread | Sayı | İş |
|--------|------|----|
| Çağıran (host) | — | `enterOrder`/`cancelOrder`/`replaceOrder` encode + soket `write`. Token callback'i ve yerel `onRejected`. OUCH `connectUser` + `onUserConnected`/`onLoginFailed`. |
| OUCH recv | Bağlı OUCH connection başına 1 | `select` 100 ms. Decode, token çevirisi, emir callback'leri, replay sonu, watchdog, Onload warm işareti. |
| Heartbeat | SDK başına 1 | Her `heartbeat_interval_ms`'de bağlı OUCH'lara ClientHeartbeat. Bağlantı snapshot'ı `connections_mutex_` altında alınır, gönderim kilitsiz yapılır. |
| QuickFIX `SocketInitiator` | QuickFIX'e ait | FIX oturumları ve bütün FIX callback'leri |
| ITCH client | itch-sdk'ya ait | Combiner `deliver` → `onExecuted` |

| Kilit | Korur | Not |
|-------|-------|-----|
| `Impl::connections_mutex_` | `connections` vektörü, dinamik `account_routes_` eklemesi | Exact-route `pick_connection`, `ownsAccount`, `isConnected` alır. Round-robin yolu almaz. |
| `Impl::maps_mutex` | `orders_by_token`, `wire_by_client`, `split_parents_`, havuz bitince token üretimi (`rng`) | Callback'ler bu kilit dışında çağrılır |
| `OuchConnection::send_mutex_` | Connection başına soket yazımı (emir + heartbeat + login) | Farklı connection'lar paralel yazar |
| `FixEngine::orders_mutex_`, `creds_mutex_` | FIX emir kayıtları, şifreler | → [fix.md](fix.md) |
| Kilitsiz okunanlar | `account_routes_` (round-robin), `instrument_limits_`, `token_pool` (atomik indeks), `sdk_config` | Config-time sabit kabul edilir |

### `src/perf/ConnPerf.h`

- `MAORDER_HAS_PERFSDK=1` build'inde; her `OuchConnection` ve FIX `SessionEntry`'de bir örnek, `register_all(prefix, user, with_decode)` ile kaydedilir. Ad: `<prefix>_<ad>_ns__<username>` (prefix `maordersdk` / `maordersdk_fix`).
- Metrikler (ns): enter `tokenmap/encode/send/order/rtt`; cancel ve replace `lookup/encode/send/order/rtt` (`rtt` = gönderim → cevap); recv `recv_decode_<tip>` (yalnız OUCH) ve `recv_cb_<tip>` (accepted/rejected/replaced/canceled/executed).
- Global: `maordersdk_enter_route_ns` (connection seçimi), `maordersdk_replay_quiet_window_ns` (login → replay sonu). Id 0 = no-op.

## Şüpheli

1. **bug? `onSdkError(6)` iki anlamlı.** `MAOrderSDK::start` `mlockall` hatasında 6 verir. `Impl::notify_send_failure` wire send hatasında da 6 verir. Koda göre ayıran host ikisini karıştırır.
2. **doğrula: Onload bootstrap hataları kayboluyor; HFT bootstrap'ı geç çağırıyor.**
   - README sırası ve `HftMain.cpp` `bootstrapOnloadIfRequested`'ı `setCallbacks`'ten önce çağırır. `onSdkError(7)` o anda boş callback'e gider.
   - HFT bootstrap'ı PerfSDK ve ITCH client başlatıldıktan sonra çağırır. `execvp` bunları yeni süreçte baştan kurar. Header "call early in main()" der.
   - Yalnız `sdkUseOnload=Y` ve Onload build'inde etkilidir.
3. **bug? `connectUser(const OuchUser&)` `protocol` alanını yok sayıyor.** `protocol==Fix` olan bir kullanıcı için `OuchConnection` kurup SoupBinTCP login dener. Bugün iki host da yalnız OUCH kullanıcısı veriyor.
4. **doğrula: Dinamik kayıt ile kilitsiz route okuması yarışı.**
   - `connectUser(OuchUser)` `account_routes_[acc].conns.push_back` yapar. Bu `unordered_map` rehash'ine ve vektör realloc'una yol açabilir.
   - `pick_connection`/`round_robin`/`setFavoriteOuch` aynı yapıyı kilitsiz okur.
   - Kod yorumu "handoff penceresinde güvenli" der. HFT'de gate'siz GUI emirleri ve watchdog sonrası handoff bu varsayımı bozar ([hftsrvprod/emir-yasam-dongusu, Şüpheli 8](../hftsrvprod/emir-yasam-dongusu.md)).
5. **doğrula: OUCH `onUserConnected` ile replay olayları arasında sıra yok.** `connect_with_diagnostics` önce recv thread'ini başlatır, sonra çağıran thread'de `onUserConnected`'ı çağırır. Hızlı bir replay accept'i host bağlantıyı "connected" saymadan gelebilir. `onReplayCompleted` için header'daki "after onUserConnected" garantisi yalnız quiet window (≥ bir heartbeat) sayesinde pratikte tutar.
6. **bug? `ownsAccount` ile routing tutarsız olabilir.**
   - Durum: hesap hem OUCH hem FIX havuzunda, OUCH bağlantıları kopuk, FIX logon'lu.
   - `ownsAccount` true döner. `routes_to_fix` hesabı OUCH haritasında gördüğü için OUCH'u seçer. Sonuç `onSdkError(1)` + `false`. Host yedek yola gitmez ve emir sessizce düşer.
   - `ownsAccount` ayrıca `preferred_ouch_username`'i bilmez: exact-route kullanıcısı kopuksa ama hesabın başka bağlı kullanıcısı varsa da aynı sonuç olur.
7. **bug? Split yolunda route yoksa ret boş id ile gidiyor.** `enterOrder` split dalında hesap OUCH haritasında yoksa `reject_order(order.client_order_id, …, 1, …)` çağrılır. Boş id modelinde (iki host) `client_order_id` boş gider ve token callback'i çağrılmaz; host reddi eşleyemez. Diğer yerel retler `assign_local_reject_token` kullanıyor.
8. **doğrula: OUCH cancel/replace soket hatası sessiz.** `Impl::cancel_one` ve `Impl::replace_one` `conn->send` false olunca `onSdkError` vermeden `false` döner. Host log'unda sebep görünmez.
9. **doğrula: Host callback istisnası recv thread'ini öldürür.** `on_wire_*` ve `OuchConnection::recv_loop` istisna yakalamaz. `std::thread` içinde yakalanmayan istisna `std::terminate` ile sonuçlanır. Yalnız `OrderTokenAssignedCallback` sarılıdır.
10. **doğrula: Emir haritaları gün boyu büyüyor.** `orders_by_token`/`wire_by_client` cancel, fill ve reject'te silinmez (`on_wire_rejected` TODO'su). Bu yüzden `ownsOrder` bitmiş emirler için de true döner. Bellek gün içi emir sayısıyla büyür. Ayrıntı: [emir-akisi.md](emir-akisi.md).
11. **kasıtlı? Kütüphane süreci sonlandırıyor.** `setOuchConfig` geçersiz `market`'te `std::exit(1)` çağırır. `OuchUser.market` varsayılan başlatıcısı yoktur; host set etmezse değer belirsizdir.
12. **doğrula: FIX `connectUser` dönüşü yanıltıcı.** `Ok`, yalnız `Session::logon()` çağrıldığı anlamına gelir. `start()`'tan önce çağrılırsa `UserNotFound` döner, oysa kullanıcı vardır.
13. **doğrula: Aynı kullanıcıya eşzamanlı `connectUser`.** `connect_with_diagnostics` `recv_thread_`/`socket_fd_`'yi kilitsiz join eder ve yeniden atar. İki thread aynı anda çağırırsa `std::thread` yeniden ataması `std::terminate`'e yol açabilir. order-service shim'i kullanıcı başına tek thread çalıştırır; boot döngüsüyle çakışması ❓ doğrulanmadı.
