---
kapsam: MAOrderSDK içinde bir emrin yolu — enterOrder/cancelOrder/replaceOrder iç akışı, token ve iç tablolar, yerel retler, bölme ve hard cap, OUCH olaylarının host callback'lerine eşlenmesi, ITCH+OUCH combiner
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
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
dogrulama: 2026-10-22
durum: taslak
---

# MAOrderSDK — emir akışı

Kod: `src/MAOrderSDK.cpp` (`MAOrderSDK::Impl`), `src/protocol/ouch/OuchCodec.cpp`, `src/connection/ouch/OuchConnection.cpp` (`send`, `dispatch_message`), `src/combiner/Combiner.*`, `tests/combiner_test.cpp`.

Bu dosyada olmayanlar:
- Public API, config struct'ları, boot, kullanıcı/bağlantı modeli, `ownsAccount`/`ownsOrder` sözleşmesi, round-robin ve favori bağlantı, callback listesi, `onSdkError` tablosu → [api-ve-yasam-dongusu.md](api-ve-yasam-dongusu.md)
- SoupBinTCP, login, heartbeat, failover, sequence/replay, OUCH byte düzenleri → [ouch-protokolu.md](ouch-protokolu.md)
- FIX yolu (`FixEngine`, `fix_send_one`, PossDup) → [fix.md](fix.md)
- Host tarafları: [hftsrvprod/emir-yasam-dongusu.md](../hftsrvprod/emir-yasam-dongusu.md), [order-service/sdk-ve-oturumlar.md](../order-service/sdk-ve-oturumlar.md)

## 1. İç tablolar

Hepsi `MAOrderSDK::Impl` üyesidir.

| Tablo | Anahtar → değer | Eklenir | Silinir | Kilit |
|-------|-----------------|---------|---------|-------|
| `orders_by_token` | wire OUCH token (14 karakter) → `shared_ptr<ClientOrder>` | `send_one` (enter), `replace_one` (yeni token), `on_wire_accepted`/`on_wire_replaced` (replay adopt) | Yalnız: gönderim hatası rollback'i ve `on_wire_replaced` (eski token) | `maps_mutex` |
| `wire_by_client` | host'un `client_order_id`'si → wire token | Aynı anlar | Aynı anlar | `maps_mutex` |
| `split_parents_` | parent `client_order_id` → `[(child id, child qty)]` | `enterOrder` split sonu, yalnız host id verdiyse | Yalnız `replaceOrder` split dalında yeniden anahtarlanırken | `maps_mutex` |
| `token_pool` | indeks → önceden üretilmiş token | `setOuchConfig` → `fill_token_pool` | `setOuchConfig` her çağrıda baştan kurar | Yok (`pool_index` atomic) |
| `account_routes_` | hesap → `AccountRoute` | `setOuchConfig`, `connectUser(OuchUser)` | `setOuchConfig` | Okuma kilitsiz ([api](api-ve-yasam-dongusu.md)) |
| `instrument_limits_` | `orderbook_id` → `InstrumentLimit` | `setInstrumentLimits` (kopya) | Bir sonraki `setInstrumentLimits` | Okuma kilitsiz |

**`ClientOrder`** (gönderim kaydı): `conn`, `client_order_id`, `orderbook_id`, `quantity` (gönderilen lot), `client_account` (route hesabı), `passthrough`, `*_sent_at` (RTT, PerfSDK), `sent_before/after_write_ns`, `cancel_before/after_write_ns` (epoch ns), `combiner_eligible`.

**Sızıntı:** Cancel, tam fill ve BIST reject kayıtları **silmez** (`on_wire_rejected`'daki `TODO(user-decision)` yorumu bunu açıkça bırakır). `orders_by_token`/`wire_by_client` gün boyu büyür. `ownsOrder` biten emirler için de `true` döner (Şüpheli #1).

## 2. Token ve kimlik modelleri

- **Format:** `generate_ouch_token`: 14 karakter `[0-9A-Za-z]`, `std::mt19937 rng` ile. `rng` paylaşımlıdır; config dışı her çağrı `maps_mutex` altındadır.
- **Havuz:** `OuchConfig.token_pool_size` (varsayılan 100 000; order-service 100 000; HFT `getSdkTokenPoolSize`) kadar token `setOuchConfig`'te üretilir.
  - Çekim: `pool_index.fetch_add(1)`; `idx < size` ise kilitsiz havuz token'ı.
  - Havuz bitince: `maps_mutex` altında `generate_ouch_token`. Sarma (wrap) yoktur, havuz tekrar kullanılmaz.
  - Havuzdan çekenler: `send_one` (her enter/child), `assign_local_reject_token` (yerel ret), `draw_token` (FIX enter, FIX replace, FIX cancel ClOrdID).
  - **Replace token'ı havuzdan gelmez:** `replace_one` her seferinde `generate_ouch_token` çağırır.
- **Çakışma:** `send_one` ve `replace_one` yeni token'ı `orders_by_token`'da varsa yeniden üretir (replay ile adopt edilmiş token'larla çakışma). Bu, host duplicate'i sayılmaz.

| Model | Kim kullanır | Enter'da `client_order_id` | Callback'teki id | Replace'te yeni id |
|-------|--------------|----------------------------|------------------|--------------------|
| SDK-owned token | HftSrvProd, order-service | boş | wire token | order-service: boş → yeni wire token. **HftSrvProd: kendi ürettiği id** (`UtilityClass::generateToken`) → callback'te HFT id'si, wire'da SDK'nın ayrı token'ı |
| Host id | `app/main.cpp` test uygulaması; ❓ doğrulanmadı: başka kullanan | dolu, SDK'ya opak | host id | host id veya boş → wire token |
| Adopt (replay) | — | — | wire token | — |

Sonuç: HFT'de replace sonrası host id'si ile wire token'ı **farklıdır**. Eşleme yalnız SDK içindeki `wire_by_client` üzerinden yapılır.

## 3. `enterOrder` adım adım

`MAOrderSDK::enterOrder(order, on_token_assigned)`, çağıran thread'de, senkron:

1. **Fiyat:** `price == 0` ve `ord_type` `Market`/`MarketWithLeftoverLimit` değilse → 1005.
2. **Miktar:** `quantity == 0` → 1006.
3. **Hesap anahtarı:** `routing_account`, boşsa `client_account`, boşsa `exchange_info`.
4. **Limit bloğu** — yalnız `instrument_limits_` boş değilse **ve** `price > 0` ise (§6):
   1. `orderbook_id` tabloda yok → 1001
   2. `is_brut_takas` → 1002
   3. hard cap → 1003
   4. `no_split` değilse bölme kararı; tek lot sığmıyorsa → 1004
5. **FIX'e mi?** `routes_to_fix(account, preferred_ouch_username)`: tercih edilen kullanıcı FIX kullanıcısıysa ya da hesap OUCH route'unda yok, FIX route'unda varsa FIX dalına girer ve orada döner. Bölme matematiği aynıdır → [fix.md](fix.md).
6. **OUCH, bölünmeyen emir:**
   - `pick_connection(account, preferred)` ([api](api-ve-yasam-dongusu.md)). `nullptr` ise `onSdkError(1)` + `false`. **Ret üretilmez, token atanmaz.**
   - `send_one` → başarısızsa `notify_send_failure` (§4).
7. **OUCH, bölünen emir:** §5.

**`send_one(msg, conn, on_token_assigned)`:**
1. Havuzdan token çekilir (kilitsiz).
2. `maps_mutex` altında:
   - Host id doluysa ve `wire_by_client`'ta varsa → `Duplicate` (çekilen havuz token'ı boşa gider).
   - Token gerekirse üretilir/yeniden çekilir.
   - `cid` = host id, boşsa token.
   - `ClientOrder` kurulur (`client_account` = adım 3'teki hesap anahtarı). İki haritaya yazılır, `combiner_eligible = true`.
3. Kilit dışında `on_token_assigned({cid, qty, conn->username()})` çağrılır. Exception atarsa rollback → `AssignmentCallbackFail`.
   - Callback wire'a yazmadan **önce** çalışır; host kaydı accept'ten önce hazırdır (order-service `entered_orders` bunu kullanır).
4. `OuchCodec::encode_enter_order` → 0 dönerse rollback → `EncodeFail`.
5. `conn->send`: per-connection `send_mutex_` altında tek `::send` (kısmi yazımda `send_raw_slow`, `select` 1 s). `connected_` false ise hemen `false`. Başarısızsa rollback → `SendFail`.
6. `sent_before/after_write_ns` yazılır (epoch ns). Accept bu satırdan önce gelirse gecikme alanları 0 kalır (koddaki "benign race").

Kayıt wire'a yazmadan önce haritadadır; recv thread'i accept'i her zaman bulur.

## 4. Yerel retler ve hatalar

### Enter yolu (`onRejected` üretenler)

Hepsi **senkron**dur ve `enterOrder`'ı çağıran thread'de, `enterOrder` dönmeden çalışır. `reject_order` `onRejected` set değilse sessizdir. Sentetik ret: `timestamp = 0`, gecikmeler 0, `ouch_username` boş; `orderbook_id`, `account`, `quantity`, `passthrough` emirden doldurulur.

| Kod | Sebep | Kontrol (sembol) | Token | `onSdkError` |
|-----|-------|------------------|-------|--------------|
| 1005 | Fiyat 0, market emri değil | `enterOrder` adım 1 | `assign_local_reject_token` | — |
| 1006 | Miktar 0 | adım 2 | 〃 | — |
| 1001 | `orderbook_id` limit tablosunda yok | adım 4 | 〃 | — |
| 1002 | Brüt takas enstrümanı | adım 4 | 〃 | — |
| 1003 | Hard cap aşıldı veya cap 0 | adım 4 | 〃 | — |
| 1004 | `max_order_value`'ya tek lot bile sığmıyor (`limit_raw / price == 0`; `max_order_value == 0` dahil) | adım 4 | 〃 | — |
| 1 | Split: hesabın `account_routes_` kaydı **yok** | split girişi | **yok**: `client_order_id` = host id (SDK-owned modelde **boş string**), `on_token_assigned` çağrılmaz | — |
| 1 | Split: route var, bu child için bağlı bağlantı yok | split döngüsü, child başına | `assign_local_reject_token` | — |
| 4 | Host id duplicate | `send_one` → `notify_send_failure` | host id | 4 |
| 5 | Encode hatası | 〃 | `cid` | 5 |
| 6 | Soket yazımı başarısız | 〃 | `cid` | 6 |
| 15 | `on_token_assigned` exception attı | 〃 | `cid` | 15 |

- **`assign_local_reject_token`:** Host id doluysa onu döner. Boşsa havuzdan token çeker ve `on_token_assigned({token, qty, ""})` çağırır (kullanıcı adı boş). Callback exception atarsa `onSdkError(15)` çağrılır, ret yine gider. Token haritalara **yazılmaz**; `ownsOrder(token)` false döner (order-service yerel reti bununla ayıklar).
- **Ret üretmeyen `false`:** Bölünmeyen OUCH emrinde bağlı bağlantı yoksa → `onSdkError(1)`. FIX'te de aynısı.
- Kontroller bağlantı kontrolünden **önce** koşar; hesabın sahibi bağlı olmasa da 1001–1006 üretilir. HFT'deki sonucu: [hftsrvprod Şüpheli #1](../hftsrvprod/emir-yasam-dongusu.md#şüpheli-davranışlar-koddan).

### Cancel/replace yolu (yalnız `onSdkError`, ret yok)

| Kod | Durum | Sembol |
|-----|-------|--------|
| 8 | Replace'te `client_order_id` boş | `replace_one`, `fix_replace_one` |
| 9 | `wire_by_client`'ta yok | `cancel_one`, `replace_one` |
| 10 | Kaydın `conn`'u yok veya `is_connected()` false | `cancel_one`, `replace_one` |
| 4 | Replace'te host'un yeni id'si duplicate | `replace_one` |
| 12 | Bölünmüş emirde miktar değişikliği (`quantity` ≠ 0 ve ≠ toplam) | `replaceOrder` |
| 15 | Replace'te `on_token_assigned` exception | `replace_one` |
| 5 | Encode hatası | `cancel_one`, `replace_one` |
| — | Soket yazımı başarısız: **`onSdkError` yok, ret yok**, yalnız `false` | `cancel_one`, `replace_one` (Şüpheli #6) |

9, 10 ve 4 `maps_mutex` **tutulurken** çağrılır (Şüpheli #2).

### BIST ret kodları (`docs/reject-codes.txt`)

Dosyada yalnız 9 kod vardır: `-420131` fiyat limit dışı, `-800002` token tekrarı, `-850008` geçersiz hesap, `-850004` ön-işlem risk limiti ihlali, `-420135` gizli miktar yasak, `-420365` bu seansta emir tipi değişmez, `-420325` hesap alanı değişmez, `-420579` emir değeri azami değeri aşıyor, `-420701` hesap tipi belirtilmiş.

SDK bu kodları yorumlamaz; wire reject'teki `reject_code` olduğu gibi `onRejected`'a geçer, `reject_reason` boştur. Dosyada **olmayan** ama host'larda işlenen kodlar:
- `-110023`: "Illegal transaction at this time" — order-service toplu akış tekrarı ([toplu-emirler](../order-service/toplu-emirler.md))
- `-420029`: fiyat adımı
- `-420177`: emir bulunamadı (HFT)
- `-850002/-850044/-850064`: PTRM (HFT)

Tam liste order-service `kRejectCodes` ve HFT `GlobalConstants.h`'tadır: [order-service/sdk-ve-oturumlar § 5](../order-service/sdk-ve-oturumlar.md), [hftsrvprod § 5](../hftsrvprod/emir-yasam-dongusu.md).

## 5. Emir bölme (#15)

**Matematik** (`enterOrder`, HftSrvProd eski `OuchManager` ile birebir; tamamen tamsayı):

```
decimal_prx   = 10^decimal_count              (döngüyle, float yok)
limit_raw     = max_order_value(TL) × decimal_prx
split         = !no_split && (limit_raw == 0 || quantity > limit_raw / price)
max_child_qty = limit_raw / price             (tamsayı bölme, aşağı yuvarlar; 0 → 1004)
full_children = quantity / max_child_qty
remainder_qty = quantity − full_children × max_child_qty
child sayısı  = full_children + (remainder_qty > 0 ? 1 : 0)
```

- `quantity > limit_raw / price` (tamsayı) ⇔ `quantity × price > limit_raw`. Çarpım yapılmaz, böylece büyük miktarda `uint64` taşması olmaz.
- Her child'da `qty × price ≤ limit_raw` olur. Son child küçük olan kalandır.
- Örnek: `max_order_value` = 1 000 000 TL, `decimal_count` = 2, `price` = 2500 raw (25,00 TL), `quantity` = 100 000 lot → `limit_raw` = 10^8, `max_child_qty` = 40 000 → child'lar 40 000 + 40 000 + 20 000.
- Bölme kararı emir fiyatıyla verilir; market emri (fiyat 0) bölünmez.

**Bağlantı dağıtımı:**
- `preferred_ouch_username` boşsa: child 0 → `pick_connection(account)` (favori bilinçli), child 1..N → `Impl::round_robin(route)`.
- `preferred_ouch_username` doluysa: her child aynı kullanıcıya gider (`pick_connection(account, username)`).

**Child kimliği ve parent izleme:**
- Host id `P` verdiyse child id'leri `P#0`, `P#1`… olur. Başarılı child'lar `split_parents_[P]`'ye yazılır, `ownsOrder(P)` true döner.
- Host id boşsa (HFT, order-service) child id'leri boştur. Her child kendi wire token'ını alır, `split_parents_` **kaydı yoktur**. Child'lar host'a birbirinden bağımsız emirler olarak görünür; HFT'de onları bağlayan tek şey ortak passthrough/father ref'tir.
- `on_token_assigned` child başına bir kez çağrılır.

**Kısmi başarı:**
- Bir child başarısız olursa (bağlantı yok → ret 1; send hatası → 4/5/6/15) döngü **devam eder**. Diğer child'lar gider.
- Dönüş: `all_sent` (hepsi gittiyse `true`). Kısmi başarıda `false` döner ama gönderilen child'lar canlıdır. Host `false`'u "hiç gitmedi" sanmamalı. order-service bunu `ownsOrder` ile ayıklar ([sdk-ve-oturumlar § 4.3](../order-service/sdk-ve-oturumlar.md)).
- BIST'in child bazında accept/reject'i normal olay yolundan, child id'siyle gelir.

**Cancel/replace yayılımı** (yalnız `split_parents_` kaydı varsa, yani host id modelinde):
- `cancelOrder(P)`: her child için `cancel_one` (FIX child'ı ise FIX cancel). Dönüş: hepsi başarılıysa `true`. Kayıt silinmez.
- `replaceOrder(P)`:
  - `quantity` 0 ya da toplam olmalıdır, aksi halde 12. Yalnız fiyat yayılır.
  - OUCH child'ına child'ın **ilk** miktarı (`children[i].second`) yazılır; FIX child'ına 0 (koru) yazılır.
  - Child'ın yeni id'si `new_client_order_id#i` olur; yeni id boşsa SDK token'ı kullanılır.
  - Başarısız child eski id'siyle listede kalır. `split_parents_` yeni parent id'sine taşınır; yeni id boşsa eski anahtar korunur.

## 6. Hard cap ve `InstrumentLimit`

`InstrumentLimit` (`public/MAOrderStruct.h`):

| Alan | Tip | Birim |
|------|-----|-------|
| `max_order_value` | `uint32` | **tam TL** (emir başı notional üst sınırı; bölme eşiği) |
| `decimal_count` | `uint32` | fiyat ondalık hanesi; raw fiyat = TL × 10^`decimal_count` |
| `is_brut_takas` | `bool` | true → 1002, emir hiç gönderilmez |

- Kaynak: HFT DB'den (`DatabaseServiceClient`), order-service `InstrumentService`'ten, açılışta bir kez yükler. Değerler: [order-service § 3](../order-service/sdk-ve-oturumlar.md), [hftsrvprod/config.md](../hftsrvprod/config.md).
- **Hard cap:** `OrderSdkConfig.order_hard_cap_try` (`uint32`, **tam TL**, varsayılan 50 000 000).
  - `hard_cap_raw = cap × decimal_prx`. Emir `quantity > hard_cap_raw / price` ise reddedilir; `hard_cap_raw == 0` ise koşulsuz reddedilir. Kod 1003'tür.
  - Kap **bölmeden önce** uygulanır. Kapı aşan emir bölünmez, reddedilir.
  - `no_split` kapı ve enstrüman kontrollerini atlatmaz.
- **Kapsam dışı kalanlar:** Limit bloğunun tamamı `!instrument_limits_.empty() && price > 0` koşuluna bağlıdır:
  - `setInstrumentLimits` hiç çağrılmadıysa (ya da boş tabloyla çağrıldıysa) hard cap, brüt takas ve bölme **uygulanmaz**.
  - Market emirleri (fiyat 0) ve negatif fiyatlar da bu bloğu atlar (Şüpheli #3).

## 7. `cancelOrder` ve `replaceOrder`

**`cancelOrder(id)`:**
1. `split_parents_[id]` varsa §5'teki yayılım yapılır.
2. Yoksa: FIX emri ise (`fix_engine_->ownsOrder`) FIX'e gider, değilse `cancel_one(id)` çalışır.
3. `cancel_one`:
   - `maps_mutex` altında `wire_by_client[id]` → token → `ClientOrder`; bağlantısı canlı olmalı (aksi halde 9/10).
   - Kilit dışında `encode_cancel_order(token)` ve `conn->send`.
   - Cancel, emrin **kendi** bağlantısından gider. Aynı hesabın başka bağlı bağlantısına düşmez.
   - Biten (fill/cancel) emir de haritada olduğu için cancel BIST'e gider. ❓ doğrulanmadı: BIST'in cevabı (`-420177`?) ve bu cevabın hangi token'la geldiği.

**`replaceOrder(order)`** (`replace_one`):
1. Boş id → 8.
2. `maps_mutex` altında:
   - eski token bulunur (9/10)
   - host'un yeni id'si duplicate mi kontrol edilir (4)
   - yeni wire token **`generate_ouch_token`** ile üretilir
   - yeni `ClientOrder` kurulur: `orderbook_id` eskiden; `quantity` = `order.quantity`, 0 ise eskisi; `client_account`/`passthrough` mesajda boşsa eskiden; `combiner_eligible` eskiden (adopt edilen emir combiner dışı kalır)
   - yeni (id, token) çifti eklenir. **Eski çift kalır**; `OrderReplaced` gelene kadar iki çift yan yanadır.
3. Kilit dışında `on_token_assigned({yeni id, efektif qty, username})` çağrılır (exception → rollback + 15).
4. `encode_replace_order(order, eski token, yeni token)`:
   - `quantity` ve `price` mesajdaki **raw** değerlerdir; 0 olduğu gibi yazılır. Anlamı (koru?): [ouch-protokolu.md](ouch-protokolu.md).
   - Boş `client_account`/`passthrough` → ilk bayt `'\0'` (koru). Exchange Info her zaman korunur, display qty 0, client category 0 (değişmez).
5. `conn->send`. Hata → rollback, `false`.

BIST replace'i reddederse yeni çift haritada kalır (§1 sızıntı). Eski emir canlı kalır, eski id'yle erişilebilir.

## 8. Olayların dönüşü

Recv thread'i `OuchConnection::dispatch_message` mesajı decode eder ve `Impl::on_wire_*`'ı çağırır. Bu fonksiyon `maps_mutex` altında wire token → host id çözer, kilidi bırakır, sonra host callback'ini çağırır. Combiner kancaları da kilit dışındadır.

| OUCH mesajı | `Impl` | Token bulunursa | Bulunmazsa | Harita etkisi | Host | Combiner |
|-------------|--------|-----------------|------------|---------------|------|----------|
| Order Accepted | `on_wire_accepted` | `client_order_id`; boş `account` → kayıttaki hesap; `ouch_username`; gecikmeler; `conn` boşsa doldurulur | **Adopt:** `ClientOrder{conn, id=wire, obid, account, passthrough}` iki haritaya yazılır; `quantity` 0, combiner dışı | adopt'ta ekleme | `onAccepted` | Sonra `on_accepted` (yalnız `combiner_eligible`) |
| Order Rejected | `on_wire_rejected` | id; `orderbook_id`, `account`, `passthrough`, `quantity` **gönderim kaydından** (wire'da yoktur); gecikmeler | id = wire token, diğer alanlar boş | yok | `onRejected` | — |
| Order Canceled | `on_wire_canceled` | id; cancel gecikmeleri | id = wire | yok | `onCanceled` | Sonra `on_canceled` |
| Order Executed | `on_wire_executed` | id, `ouch_username` | id = wire | yok | `onWireExecuted`, sonra `onExecuted` | Arada `on_executed_adjust` |
| Order Replaced | `on_wire_replaced` | yeni token → id; boş `account` → kayıttan | Yeni token'ı adopt eder | Eski token bulunursa `previous_client_order_id` = eski id; eski çift **silinir** | `onReplaced` | Sonra `on_replaced` |

- **Replace'te eski/yeni:** `client_order_id` = yeni id, `previous_client_order_id` = eski id. Eski token bilinmiyorsa (replay) eski wire token yazılır.
- **Execute alanları:** yalnız `timestamp`, id, `orderbook_id`, `quantity` (lot), `price` (raw), `match_id`, `ouch_username`. Side, hesap ve passthrough **yoktur**.
  - `match_id`: wire'daki 12 baytlık Match ID'nin son 8 baytıdır (`decode_order_executed`).
- **`is_replay`:** OUCH decoder'ı hiç set etmez; replay olayı canlıdan ayırt edilemez.
- **Reject alanı:** `reject_reason` wire'dan gelmez, boştur.

### `onWireExecuted` vs `onExecuted`

| | `onWireExecuted` | `onExecuted` |
|---|---|---|
| Kaynak | Ham OUCH fill | OUCH (combiner'ca kırpılmış) **veya** ITCH (combiner) |
| Thread | Her zaman emrin recv thread'i (accept ile aynı) | Recv thread **veya** ITCH client thread'i |
| Bastırılır mı | Hiç | Combiner'ın daha önce ITCH'ten verdiği lotlar için evet (qty 0 → çağrılmaz) |
| Miktar | Wire'daki | Host'a daha önce ulaşmamış kısım |
| `match_id` | Gerçek BIST | OUCH'ta gerçek; ITCH kaynaklı fill'de **0** |
| Combiner kapalıyken | Aynı mesaj | Aynı mesaj |

Host kullanımı: HFT stratejiye `onExecuted`, GUI'ye `onWireExecuted` verir ([hftsrvprod § 3](../hftsrvprod/emir-yasam-dongusu.md)). order-service combiner kullanmaz.

## 9. Combiner (`src/combiner/`)

**Amaç:** Kendi emirlerimizin fill'ini OUCH execute'tan önce ITCH beslemesinden host'a vermek; her lot host'a **bir kez** ulaşır. OUCH otoritedir.

**Devreye girme** (`MAOrderSDK::start`):
- `MAORDER_HAS_ITCHSDK=1` olmalıdır (CMake `MAItchSDK` kütüphanesini bulursa).
- `sdk_config.enable_combiner` true olmalı ve `setItchSdk` çağrılmış olmalıdır. İşaretçi yoksa `onSdkError(13)` + kapalı.
- Trampoline yönlendirmesi süreç geneli tek örnektir (`self_`). İkinci örnek `onSdkError(14)` ile kapalı kalır.

**İzlenen emir:** `send_one` ile bu oturumda girilmiş olmalıdır (`combiner_eligible`; replace'te miras kalır). Ayrıca:
- `client_order_id` dolu, `order_id != 0`
- side `B` / `S` / `T` (`T` ITCH'te `'S'` tarafındadır)

Replay ile adopt edilen emirler izlenmez.

**Durum (`OrderState`, emir başına, kendi `mtx`'i):**
- `epoch_rest_qty`: accept/replace anındaki **dinlenen** miktar (`OrderAccepted.quantity`).
- `insta_pending`: `pre_trade_quantity − quantity`, girişte agresif eşleşen kısım. Bu kısmı ITCH bizim emrimiz için raporlamaz; yalnız OUCH verir.
- `remaining_total`: `pre_trade_quantity`, otoriter açık miktar.
- `cum_ouch_rest`, `cum_itch_rest`, `delivered_rest`: epoch içi sayaçlar.
- `poisoned`, `done`, `subscription`, `slot`, `itch_order_id`, `itch_side`.

**Durum makinesi:**

| Olay | Thread | Ne olur |
|------|--------|---------|
| Accept (`on_accepted`, host `onAccepted`'dan **sonra**) | recv | Durum kurulur. `pre_trade < quantity` → poison. `quantity > 0` ve poison yoksa `subscribeSpecificOrderEvents(obid, order_id, side, trampoline, slot)`. Abonelik `nullptr` (kitap yok / itch-sdk'da kitap başına 32 slot dolu, `MAX_CALLBACKS_PER_TYPE`) → OUCH pass-through. Aynı id zaten izleniyorsa yok sayılır (replay tekrarı). |
| ITCH execute (`on_itch_event`) | ITCH client | Atlanır: `done`/`poisoned`; `orderId`/side eşleşmiyor (eski epoch veya yeniden kullanılmış slot); event DELETED (yalnız bilgi); `priceReliable == 0` (`'C'` cross fill); `price ≤ 0`. Aksi halde `cum_itch_rest += q`; `> epoch_rest_qty` → poison. `deliver = min(q, cum_itch_rest − delivered_rest)`. 0 ise bastırılır. Değilse `deliver_` **tüm kilitler dışında** host `onExecuted`'ı çağırır. |
| OUCH execute (`on_executed_adjust`, `onExecuted`'dan **önce**) | recv | İzlenmiyor/`done` → miktarın tamamı geçer. `insta = min(q, insta_pending)` her zaman geçer. `rest = q − insta`; `cum_ouch_rest += rest` (`> epoch` → poison). `deliver = min(rest, cum_ouch_rest − delivered_rest)`. `remaining_total −= q` (taşarsa poison + 0). 0 olunca `finalize` (unsubscribe) + kayıt silinir. Dönüş `insta + deliver`. |
| Replace (`on_replaced`, host'tan sonra) | recv | Kayıt eski id'den yeni id'ye taşınır. Epoch sıfırlanır (`epoch_rest_qty` = yeni qty; sayaçlar 0; insta/remaining `pre_trade`'den). Abonelik `updateSpecificOrderEventsSubscription` ile yeni `order_id`'ye taşınır (hata → poison). Abonelik yoksa ve qty > 0 ise yeni abonelik açılır. |
| Cancel (`on_canceled`) | recv | `finalize` + sil. ITCH DELETED olayı tek başına hiçbir şey yapmaz. |
| Bağlantı kopması (`poison_all`) | kopmayı gören thread | `set_on_disconnected` içinde **bütün** izlenen emirler zehirlenir (yalnız kopan kullanıcınınkiler değil). |
| `stop()` | çağıran | Trampoline kesilir, her şey finalize edilir ve temizlenir. |

**Değişmez:** Epoch içinde `delivered_rest = max(cum_itch_rest, cum_ouch_rest)` olur. Hangi kaynak önce gelirse o lotu verir; diğerinin kopyası emilir (çift kayıt koruması). Parça boyları farklı olabilir (ITCH 10, OUCH 5+5).

**Poison:**
- ITCH'ten fill üretimi durur; `onSdkError(13, "[combiner] poisoned order …")` çağrılır.
- OUCH muhasebesi sürer. Daha önce ITCH'ten verilen lotlar OUCH geldiğinde yine emilir.
- Kayıt tam fill veya cancel'a kadar kalır.

**ITCH kaynaklı fill'in alanları:**
- `timestamp` = ITCH `packetTs`: kernel SW RX zamanı, `CLOCK_REALTIME` epoch ns; 0 olabilir ([itch-sdk/mesajlar § 3](../itch-sdk/mesajlar-ve-emir-defteri.md#3-timestamp-modeli)). ❓ OUCH timestamp'iyle aynı domende karşılaştırılıp karşılaştırılmadığı doğrulanmadı.
- `price` = ITCH'teki dinlenen emir fiyatı (raw `int32`)
- `match_id` = 0, `ouch_username` boş

**Kilitler:**
- `reg_mtx_`: `by_client_id_`, `slots_`, `free_slots_`
- `OrderState::mtx`: emir başına
- Combiner kancaları hiçbir zaman `maps_mutex` altında çağrılmaz. `deliver_` ve `onSdkError` kilit dışındadır, ama `poison_locked` `on_error_`'u `st->mtx` altında çağırır.
- `slots_` küçülmez. Silinen slot `nullptr` olur ve yeniden kullanılır; eski olay `orderId` koruması ile düşer.

**Testler** (`tests/combiner_test.cpp`, sahte itch API'si `CombinerItchApi`, ağsız, `BUILD_TEST_APP`; 18 senaryo):
- ITCH önce / OUCH önce tam fill
- Araya giren parçalar
- Parça uyuşmazlığı (ITCH 10 – OUCH 5+5; OUCH 5 – ITCH 10)
- Girişte insta fill; insta ile dinlenen kısmı aynı OUCH mesajında taşıyan parça
- Replace akışı (eski id olayının düşmesi) ve insta'lı replace
- Cancel (DELETED yalnız bilgi, finalize sonrası pass-through)
- `'C'` güvenilmez fiyat
- Anomali poison'ı (toplamlar korunur)
- Tamamı insta accept (abonelik yok)
- İzlenmeyen emir, duplicate accept, slot yeniden kullanımı ve stale guard
- `poison_all`, kapalı combiner

Kapsanmayanlar: gerçek itch-sdk, eşzamanlı thread'ler, yeniden bağlanma replay'i, replace'te `order_id`'nin değişmediği durum.

## 10. Thread ve kilitler (emir yolu)

| İş | Thread |
|----|--------|
| `enterOrder`/`cancelOrder`/`replaceOrder`, `on_token_assigned`, yerel `onRejected`, bu yollardaki `onSdkError` | Çağıran (HFT AlgoWorker/gRPC, order-service MARpc/gRPC/toplu akış) |
| Wire olayları, `onWireExecuted`, combiner OUCH kancaları | Emrin `OuchConnection` recv thread'i |
| Combiner kaynaklı `onExecuted` | itch-sdk client thread'i |

| Kilit | Kapsam |
|-------|--------|
| `maps_mutex` (tek, **bütün bağlantılar** için ortak) | §1 haritaları, havuz sonrası token üretimi. Encode, send ve host callback'leri kilit dışındadır; istisnası `onSdkError` 9/10/4. |
| `OuchConnection::send_mutex_` | Bağlantı başına soket yazımı; mesajlar karışmaz, bağlantılar paraleldir |
| `connections_mutex_` | Exact-route `pick_connection(account, username)`, `ownsAccount` |
| Kilitsiz | `account_routes_`, `instrument_limits_`, `token_pool` okuması |

## 11. Ölçek özeti

| Değer | Tip | Birim |
|-------|-----|-------|
| `EnterOrderMsg.price`, `ReplaceOrderMsg.price` | `int64` → wire'da `int32` (`static_cast`) | raw = TL × 10^`decimal_count` |
| `quantity` (enter/replace/olaylar) | `uint64` | lot |
| `orderbook_id` | `uint64` → wire'da `uint32` | — |
| `max_order_value`, `order_hard_cap_try` | `uint32` | tam TL |
| `limit_raw`, `hard_cap_raw` | `uint64` | raw notional (TL × 10^`decimal_count`) |
| `timestamp` (OUCH olayları) | `uint64` | BIST damgalı epoch ns (`epoch_ns_now` yorumu) |
| `latency_*_ns`, `sent_*_write_ns` | `uint64` | ns (epoch domeni) |
| `favorite_idle_reset_ms`, `replay_quiet_window_ms` | `uint32` | ms |
| Token | 14 karakter | `[0-9A-Za-z]` |
| `passthrough` | ≤15 bayt | wire Customer Info |
| `client_account` / `exchange_info` | ≤16 / ≤32 bayt | |

## Şüpheli

1. **bug? İç haritalar hiç küçülmüyor** (`MAOrderSDK::Impl`).
   - `orders_by_token`/`wire_by_client` cancel, fill ve reject'te silinmez; `split_parents_` hiç silinmez. Reddedilen replace'in yeni çifti de kalır.
   - Bellek gün boyu büyür. `ownsOrder` biten emirler için `true` döner (header yorumu "live order" der).
   - Biten emre cancel/replace BIST'e gider.
   - `on_wire_rejected`'taki `TODO(user-decision)` yalnız ret için bunu kabul eder.
2. **bug? `onSdkError` kilit altında.** `cancel_one` ve `replace_one`, 9/10/4 kodlarını `maps_mutex` tutulurken çağırır. Host `onSdkError` içinden SDK'ya girerse (ör. `ownsOrder`) `std::mutex` kendi kendini kilitler. HFT ve order-service bugün yalnız log basıyor; doğrula.
3. **doğrula: Market emri ve negatif fiyat limitleri atlıyor.** `enterOrder` limit bloğu `price > 0` koşulludur. `OrdType::Market`/`MarketWithLeftoverLimit` ve `price < 0` emirleri 1001/1002/1003'e takılmaz, bölünmez. Brüt takas enstrümanına market emri gidebilir.
4. **bug? Limit tablosu boşsa hard cap yok.** `order_hard_cap_try` kontrolü `!instrument_limits_.empty()` bloğunun içindedir. `setInstrumentLimits` çağrılmazsa ya da DB'den boş liste gelirse statik TL kapı da devre dışı kalır.
5. **bug? Split'te route yokken ret kimliksiz.** `enterOrder`'ın split dalında `account_routes_` kaydı yoksa `reject_order(order.client_order_id, …)` çağrılır: SDK-owned modelde id boş string'dir, `on_token_assigned` çağrılmaz. order-service `context_for("")` kayıt bulamaz ve olayı atar; uygulamaya ret gitmez. Route var ama bağlantı yoksa token atanır. Davranış tutarsızdır.
6. **bug? Cancel/replace soket hatası sessiz.** `cancel_one`/`replace_one`'da `conn->send` false ise ne `onSdkError` ne `onRejected` çağrılır. HFT `ownsOrder` true gördüğü için yedek yola da gitmez.
7. **doğrula: Split replace child'ın ilk miktarını yazıyor.** `replaceOrder` OUCH child'ına `children[i].second`'ı (girişteki child miktarı) yazar. Kısmen dolmuş child'da wire'daki replace miktarının anlamı (yeni toplam mı, kalan mı) emrin büyümesine yol açabilir. Yalnız host id modelinde etkili.
8. **doğrula: `max_order_value == 0`.** `limit_raw == 0` → `split` true → `max_child_qty == 0` → `no_split` olmayan her emir 1004 alır. DB'de 0 değerli enstrüman olup olmadığı bilinmiyor.
9. **doğrula: `poison_all` bütün kullanıcıları etkiliyor.** Tek bir OUCH bağlantısı kopunca combiner diğer canlı bağlantıların emirlerini de zehirler; o emirler gün sonuna kadar yalnız OUCH'tan dolar (`install_callbacks` → `set_on_disconnected`). Kasıtlı mı, bilinmiyor.
10. **doğrula: Yeniden bağlanma replay'i ve combiner.**
    - Aynı süreçte login sequence 1'den replay ederse, izlenen emrin OUCH execute'ları `on_executed_adjust`'a tekrar girer. `cum_ouch_rest`/`remaining_total` taşar → poison; lotlar host'a ikinci kez verilir.
    - Aynı süreçte bitmiş emrin combiner kaydı silinse de SDK token kaydı eligible kalır; replay accept'i izlemeyi yeniden kurabilir. Yeni süreçte bilinmeyen token adopt'u eligible değildir; izleme kurmaz. [İkinci tur ayrımı](branch-ve-replay-kontrolu.md#replay-ve-combiner-sınırı).
    - Combiner'sız durumda da replay fill'leri tekrarlanır ([hftsrvprod Şüpheli #2](../hftsrvprod/emir-yasam-dongusu.md#şüpheli-davranışlar-koddan)).
11. **doğrula: Replace'te ITCH `order_id` değişmezse.** `on_replaced` sayaçları sıfırlar; stale guard yalnız `orderId` farkına dayanır. BIST replace'te ITCH order id'yi korursa, OUCH'tan geride kalan eski epoch ITCH fill'i yeni epoch'ta sayılıp ikinci kez verilebilir. itch-sdk yorumu ("DELETED = cancel or replace") yeni id'yi ima eder; test (`test_replace_flow`) yalnız farklı id'yi kapsar.
12. **doğrula: Wire reject'in token'ı.** Cancel/replace reddinde BIST'in hangi token'ı döndüğü bilinmiyor. Eski token dönerse `on_wire_rejected` canlı emrin id'siyle `onRejected` üretir; host emri reddedilmiş sanabilir.
13. **Daraltan cast'ler.** `encode_enter_order` `price`'ı `int32`'ye, `orderbook_id`'yi `uint32`'ye kontrolsüz çevirir. Pratikte sınır aşılmaz.
14. **`onSdkError(6)` iki anlamlı.** Hem gönderim hatası (`notify_send_failure`) hem `mlockall` hatası (`start`) 6 kodunu kullanır.
