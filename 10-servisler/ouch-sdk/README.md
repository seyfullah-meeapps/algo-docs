---
kapsam: ouch-sdk (libouchSDK) — order-service istemci SDK'sı; API, callback'ler, handoff bildirimi, enum farkları
kaynak:
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
dogrulama: 2026-10-22
durum: taslak
---

# ouch-sdk (`libouchSDK`)

**order-service'in istemci SDK'sı** (C++). İsim yanıltıcıdır: BIST OUCH'a **bağlanmaz**. network-sdk (MARpc) üzerinden order-service'in MARpc portuna (8000) bağlanır. BIST'e doğrudan bağlanan SDK [MAOrderSDK](../maordersdk/README.md)'dır.

**Kullananlar:**
- HftSrvProd (`OuchManager`): handoff öncesi yedek emir yolu, strateji kaydı, handoff bildirimi.
- AlgorithmicTrading (`OuchManager`): bütün emirler.

## API (`include/OrderStreamClient.h`, namespace `ouchSDK`)

| Fonksiyon | Ne |
|-----------|----|
| `startOuchStreaming(ip, port)` / `stopOuchStreaming()` | order-service bağlantısı |
| `login(user, password, Application)` | `Application`: `APP_HFT`, `AlgoTrading`, `OUCH` |
| `insertStrategyInfo(StrategyInfo)` / `getStrategyInfo()` | Emir göndermeden önce (orderbook, hesap, strateji identifier, tip) kaydı. order-service bunu trade-data-app'e yazar. |
| `enterOrder`, `cancelOrder`, `replaceOrder` | Gün içi emirler (OUCH veya FIX, `Protocol` alanıyla) |
| `addMorningOrder` / `getMorningOrders` / `clearMorningOrders`, `addOpeningOrder` / … | Sabah ve açılış emirleri (README'deki eski API; GUI yolu trade-data-app üzerindendir) |
| `getAllOrders()` | Günün emirleri (replay) |

## Callback'ler (uygulama implemente eder)

`orderAccepted`, `orderRejected`, `orderExecuted`, `orderCanceled`, `orderReplaced` ve **`orderUserDisconnected(OuchUserDisconnected*)`**.

`orderUserDisconnected` **OUCH handoff** bildirimidir. order-service'in logout olduğu OUCH kullanıcısının IP, port, şifre ve izinli hesaplarını taşır; `callbackNumber/total` alanlarıyla gelir. HFT bu callback'te MAOrderSDK ile kullanıcıya login olur. Bkz. [sistem haritası](../../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri).

## `StrategyType` enum farkı (dikkat)

`include/models/Enums.h`'teki `ouchSDK::enums::StrategyType` proto `StrategyType` ile **aynı değildir**:

| ouch-sdk adı | Değer | Proto karşılığı |
|--------------|-------|-----------------|
| `WARRANT` | **13** | `HFT_Warrant` (13). Proto'daki `Warrant = 2` ouch-sdk'da yok. |
| `WARRANT_ADVANCED` | 15 | `HFT_WarrantAdvanced` |
| `USER` | 1 | `Algo_User` |
| `HFT_User` (12) | — | ouch-sdk'da yok |

Diğerleri (AKD 3, HFT 4, MOVING_AVERAGE 5, ARBITRAGE 6, VWAP 7, THEORETICAL_PRICE 8, MAX_PRICE 9, FUND_TRACKER 10, ORDER_CHASE 11, MIN_PRICE 14) aynıdır. Yeni tip eklerken bu enum da güncellenir (network-sdk'da da karşılığı var).

## Build

CMake + Doxygen. Bağımlılık: `libMARpc`. CI `ouch_actions.yml`:
- Kütüphane → Algo-Setup `MAProdEnv`.
- Doxygen dokümanı → algo-configs `doc/Development/Documentation/Ouch-SDK`.
- Örnek uygulama: `ouchSDKApp/`.
