---
kapsam: MAOrderSDK — BIST OUCH ve FIX emir SDK'sı; public API, bağlantı/replay, emir bölme ve yerel retler, round-robin, combiner, FIX şifre yaşam döngüsü, kullananlar
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: a788782
dogrulama: 2026-10-22
durum: taslak
---

# MAOrderSDK (`libMAOrderSDK`)

Uygulamalar ile BIST emir portları arasındaki katman (C++, PIMPL, namespace `maordersdk`).
- **OUCH:** SoupBinTCP, login, heartbeat, replay.
- **FIX:** FIX 5.0SP2, QuickFIX. Kütüphaneye **statik** gömülüdür ve sembolleri gizlidir, bu yüzden host QuickFIX kurmaz.
- Emir encode/decode ve bölme işlemleri.

**Kullananlar:**
- HftSrvProd: handoff sonrası doğrudan emir.
- order-service: bütün OUCH ve FIX emirleri.
- AlgorithmicTrading: 🚧 `add-order-sdk` branch'inde.

ouch-sdk ve network-sdk'ya dokunmaz. Uygulamalar arası (strateji ↔ order-service) iletişim olduğu gibi kalır.

## Dosya yapısı

| Yer | İçerik |
|-----|--------|
| `public/MAOrderSDK.h` | `MAOrderSDK` sınıfı, `Callbacks` |
| `public/MAOrderStruct.h` | `OuchConfig`, `OuchUser`, `OrderSdkConfig`, `InstrumentLimit`, mesaj struct'ları |
| `public/MAOrderEnums.h` | `Side`, `TimeInForce`, `OrdType`, `Market`, `ConnectResult`, `LoginFailureReason` |
| `src/connection/ouch/OuchConnection` | OUCH TCP (birincil/ikincil failover), recv thread'i |
| `src/connection/fix/FixEngine`, `FixConnection` | QuickFIX oturumları |
| `src/protocol/ouch`, `src/protocol/fix` | Codec'ler, FIX şifre üretimi |
| `src/combiner/` | ITCH+OUCH execute combiner |
| `app/main.cpp` | İnteraktif test uygulaması (`ordersdk_test`) |
| `docs/` | Mimari, ret kodları (`reject-codes.txt`) |

## Kullanım sırası (host)

1. `setOuchConfig`: kullanıcılar (endpoint, kimlik, izinli hesaplar, pazar, recv pin/policy), heartbeat, token havuzu, FIX oturum ayarları.
2. `setSdkConfig`: `lock_memory`, `use_onload`, `recv_pin_core`, `warm_interval_ms`, `replay_quiet_window_ms` (varsayılan 10000), `favorite_idle_reset_ms`, `order_hard_cap_try`, `enable_combiner`.
3. `setItchSdk`: yalnızca combiner için.
4. `setInstrumentLimits`: orderbook başına `max_order_value` (tam TL), `decimal_count`, `is_brut_takas`.
5. `setStartArguments` + `bootstrapOnloadIfRequested`.
6. `setCallbacks`, ardından `start()`.
7. `connectUser(username)` veya `connectUser(OuchUser)`. İkincisi **dinamik kayıttır**: HFT handoff'ta order-service'in verdiği bilgilerle kullanıcıyı ekler ve login olur.

## Callback'ler

- **Bağlantı:** `onUserConnected`, `onUserDisconnected`, `onLoginFailed`, `onHeartbeatTimeout`, `onSdkError`.
- **`onReplayCompleted`:** Her logon'dan sonra bir kez çalışır.
  - OUCH: `replay_quiet_window_ms` boyunca yeni `SequencedData` gelmemiş ve en az bir ServerHeartbeat görülmüş olmalı.
  - FIX: PossDup replay'i bitmiş olmalı.
  - Host stratejileri bunu bekler (HFT replay gate).
- **Emir:** `onAccepted`, `onRejected`, `onExecuted`, `onCanceled`, `onReplaced`. Olaylar host'un `client_order_id`'siyle gelir. `client_order_id` boşsa SDK'nın ürettiği 14 baytlık OUCH token'ı kimlik olur; HftSrvProd bu modeli kullanır.
- **`onWireExecuted`:** Ham OUCH fill'i. Combiner'dan önce çalışır, hiç bastırılmaz ve **her zaman emrin kendi recv thread'inden** gelir. Emir başına sıra gerekiyorsa (GUI) bunu kullanın.
- **FIX şifre:** `onFixPasswordChangeResult`, `onFixLogonRejected` (1409 SessionStatus: 8 süresi doldu, 5 hatalı şifre, 6 kilitli, 9 hatalı CompID…).

## Emir gönderme

- `enterOrder` / `cancelOrder` / `replaceOrder` başarıda `true` döner. `false` dönerse host yedek yola düşebilir.
- Host'un yedek yola düşüp düşmeyeceğini `ownsAccount` / `ownsOrder` belirler: SDK sahipse ve gönderim başarısızsa emir order-service'e **yönlendirilmemelidir** (ghost emir riski).
- **Round-robin:** Bir hesabın sahibi olan bağlantılar arasında döner. `setFavoriteOuch` ile tercih edilen bağlantı tanımlanabilir: hesap `favorite_idle_reset_ms` kadar boşta kalırsa dönüş favoriden yeniden başlar. OUCH ve FIX havuzları birbirine karışmaz.
- **Bölme (#15):** Emir notional'ı enstrümanın `max_order_value`'sunu aşarsa emir parçalara bölünür. HftSrvProd'daki eski OuchManager ile bire bir aynı matematik kullanılır. Parçalar ana emir altında izlenir, iptal parçalara yayılır.
- **Yerel retler** (BIST'e gitmez, `onRejected` ile döner):

| Kod | Sebep |
|-----|-------|
| 1001 | Enstrüman limit tablosunda yok |
| 1002 | **Brüt takas** enstrümanı (izin verilmez) |
| 1003 | Statik `order_hard_cap_try` (tam TL) aşıldı |
| 1004 | Tek lot bile enstrüman limitinin üstünde |

## Combiner (ITCH + OUCH execute)

- **Amaç:** Kendi emirlerimizin fill'ini OUCH execute'tan **önce** ITCH beslemesinden yakalayıp host'a iletmek.
- **Doğruluk:** OUCH otoritedir; ikinci kez gelen fill emilir.
- **Thread:** `deliver` ITCH client thread'inden, kilit altında olmadan çalışır. Bu yüzden HFT'de `onExecuted` iki farklı thread'den gelebilir.
- **Bağlantı kopması:** İzlenen emirler "zehirlenir", OUCH tek doğruluk kaynağı olur.
- `enable_combiner` ile açılır (HFT `combinerEnabled`).

## FIX şifre yaşam döngüsü

- **`armFixPasswordChange(user, new)`:** Bir sonraki Logon'da Password(554) = eski, NewPassword(925) = yeni gönderilir. Yeni şifre **önce kalıcı yazılmalıdır**.
- **`setFixPassword`:** Çökme sonrası kurtarma içindir.
- **`generateBistFixPassword()`:** BIST politikasına uygun şifre üretir: büyük harf, küçük harf, rakam ve `*#+.` karakterlerinden tam bir tanesi. `%` ve `-` BIST tarafından reddedilir.
- order-service süresi dolan şifreyi otomatik yeniler ve DB'ye yazar.

## Build

- CMake. Statik `libquickfix.a` **zorunludur**.
- Varyantlar: normal ve `libMAOrderSDK_Onload.so`.
- CI `ordersdk.yaml` → Algo-Setup `MAProdEnv`.
- Test: `ordersdk_test` (interaktif `connect` / `enter` / `replace` / `cancel` / `perf`), `fix_codec_test`.
