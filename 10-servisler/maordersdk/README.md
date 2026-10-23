---
kapsam: MAOrderSDK (BIST OUCH ve FIX emir SDK'sı) — giriş ve indeks; görev, kullananlar, dosya yapısı, alt dosyalar, kısa özetler, build
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
- **FIX:** FIX 5.0SP2, QuickFIX. Kütüphaneye **statik** gömülüdür ve sembolleri gizlidir; host QuickFIX kütüphanesi kurmaz. `useDataDictionary=true` iken spec XML'leri yine de çalışma anında dosyadan okunur ([fix § 1](fix.md#1-build-quickfix-gömme)).
- Emir encode/decode, bölme, yerel retler, ITCH+OUCH combiner.

**Kullananlar:**
- HftSrvProd: handoff sonrası doğrudan emir ([hftsrvprod/emir-yasam-dongusu](../hftsrvprod/emir-yasam-dongusu.md)).
- order-service: bütün OUCH ve FIX emirleri ([order-service/sdk-ve-oturumlar](../order-service/sdk-ve-oturumlar.md)).
- AlgorithmicTrading: 🚧 `add-order-sdk` branch'inde.

ouch-sdk ve network-sdk'ya dokunmaz. Uygulamalar arası (strateji ↔ order-service) iletişim olduğu gibi kalır.

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`api-ve-yasam-dongusu.md`](api-ve-yasam-dongusu.md) | Public metotlar (ne zaman çağrılır, thread-safety), config struct'larının bütün alanları, mesaj struct'ları ve enum'lar, boot sırası ve Onload bootstrap, `connectUser` (statik/dinamik), `ownsAccount`/`ownsOrder`, round-robin ve favori, callback'ler ve thread'leri, **`onSdkError` tam tablosu** |
| [`emir-akisi.md`](emir-akisi.md) | `enterOrder`/`cancelOrder`/`replaceOrder` iç yolu, iç tablolar, token ve kimlik modelleri, **yerel retlerin tam tablosu**, BIST ret kodları özeti, bölme matematiği, hard cap ve `InstrumentLimit`, olay → callback eşlemesi, combiner, ölçek özeti |
| [`ouch-protokolu.md`](ouch-protokolu.md) | SoupBinTCP katmanı, bağlanma ve failover, login (sequence 1), recv thread'i ve heartbeat, replay ve `onReplayCompleted`, End of Session, OUCH mesajlarının byte düzenleri, kopma senaryoları |
| [`fix.md`](fix.md) | QuickFIX gömme, SessionSettings (sabit ve config'ten gelenler), oturum yaşam döngüsü, PossDup ve `is_replay`, encode/decode tag tabloları, **şifre yaşam döngüsü ve 1409 kodları** |
| [`branch-ve-replay-kontrolu.md`](branch-ve-replay-kontrolu.md) | İkinci kod turu: development/main farkları, süreç içi reconnect ile yeni süreç adopt ayrımı, main hard-cap koşulu |

## Dosya yapısı

| Yer | İçerik |
|-----|--------|
| `public/MAOrderSDK.h` | `MAOrderSDK` sınıfı, `Callbacks` |
| `public/MAOrderStruct.h` | `OuchConfig`, `OuchUser`, `OrderSdkConfig`, `InstrumentLimit`, mesaj struct'ları |
| `public/MAOrderEnums.h` | `Side`, `TimeInForce`, `OrdType`, `Market`, `ConnectResult`, `LoginFailureReason` |
| `src/MAOrderSDK.cpp` | `Impl`: emir yolu, iç tablolar, bölme, routing |
| `src/connection/ouch/OuchConnection` | OUCH TCP (birincil/ikincil, yalnız TCP seviyesinde failover), recv thread'i |
| `src/connection/fix/FixEngine`, `FixConnection` | QuickFIX oturumları |
| `src/protocol/ouch`, `src/protocol/fix` | Codec'ler, FIX şifre üretimi |
| `src/combiner/` | ITCH+OUCH execute combiner |
| `src/perf/ConnPerf.h` | Bağlantı başına metrikler |
| `app/main.cpp` | İnteraktif test uygulaması (`ordersdk_test`) |
| `tests/` | `combiner_test`, `fix_codec_test` |
| `docs/` | BIST OUCH ve SoupBinTCP spesifikasyonları (PDF), ret kodları (`reject-codes.txt`) |

## Kısa özetler

Ayrıntı ve kod referansları alt dosyalarda; burada yalnız yön bulmak için.

- **Kullanım sırası:** `setOuchConfig` → `setSdkConfig` → `setItchSdk` (combiner için) → `setInstrumentLimits` → `setStartArguments` → `setCallbacks` → `bootstrapOnloadIfRequested` → `start()` → `connectUser`. `setCallbacks` bootstrap'tan önce gelmeli, yoksa Onload hatası (`onSdkError(7)`) kaybolur ([api § 3](api-ve-yasam-dongusu.md#3-boot-ve-yaşam-döngüsü)).
- **Kimlik:** `client_order_id` boşsa SDK'nın ürettiği 14 baytlık OUCH token'ı kimlik olur (HFT ve order-service). Replace'te host yeni id verirse callback'ler o id'yle gelir, wire token'ı ayrıdır ([emir-akisi § 2](emir-akisi.md#2-token-ve-kimlik-modelleri)).
- **Sahiplik:** `ownsAccount`/`ownsOrder` host'un yedek yola düşüp düşmeyeceğini belirler; SDK sahipse ve gönderim başarısızsa emir order-service'e yönlendirilmemelidir (ghost emir riski). İç tablolar biten emirde silinmediği için `ownsOrder` bitmiş emirde de true döner.
- **Bölme:** Notional enstrümanın `max_order_value`'sunu aşarsa emir parçalanır. Parçalar yalnız host `client_order_id` verirse ana emir altında izlenir; HFT ve order-service vermez, yani parçalar bağımsız emirdir ve iptal yayılmaz ([emir-akisi § 5](emir-akisi.md#5-emir-bölme-15)).
- **Yerel retler:** 1001–1006 (limit tablosunda yok, brüt takas, hard cap, tek lot limitin üstünde, fiyat 0, miktar 0) ve sentetik 1/4/5/6/15. Hard cap yalnız limit tablosu doluysa ve `price > 0` ise uygulanır ([emir-akisi § 4](emir-akisi.md#4-yerel-retler-ve-hatalar)).
- **OUCH login:** Her login'de sequence 1 istenir; günün bütün mesajları baştan gelir. `onReplayCompleted` logon başına en fazla bir kez, `replay_quiet_window_ms` sessizlik + en az bir ServerHeartbeat sonrası. Login reddinde ikincil endpoint'e geçilmez ([ouch-protokolu](ouch-protokolu.md)).
- **`onWireExecuted`:** Ham fill, combiner'dan önce, bastırılmadan. OUCH'ta emrin recv thread'inden, FIX'te QuickFIX thread'inden gelir.
- **Combiner:** Kendi fill'imizi OUCH'tan önce ITCH'ten yakalar; OUCH otoritedir, ikinci fill emilir. `deliver` ITCH thread'inden çalışır, bu yüzden HFT'de `onExecuted` iki thread'den gelebilir. Bağlantı kopunca izlenen emirler zehirlenir (End of Session'da değil).
- **FIX şifre:** `armFixPasswordChange` → sonraki Logon'da 554 eski / 925 yeni; host yeni şifreyi önce kalıcı yazmalı. `generateBistFixPassword` (varsayılan uzunluk 10, en az 4) BIST politikasına uygun şifre üretir ([fix § 7](fix.md#7-şifre-yaşam-döngüsü)).

Açık sorunlar: [`ACIK-KONULAR.md`](../../ACIK-KONULAR.md) § MAOrderSDK.

## Build

- CMake. Statik `libquickfix.a` **zorunludur**.
- Varyantlar: normal, `libMAOrderSDK_Onload.so` ve `libMAOrderSDK_Mlx.so` (CI matrisinde `mlx`).
- CI `ordersdk.yaml` → Algo-Setup `MAProdEnv`.
- Test: `ordersdk_test` (interaktif `connect` / `enter` / `replace` / `cancel` / `perf`), `fix_codec_test`, `combiner_test`.
