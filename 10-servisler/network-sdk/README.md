---
kapsam: network-sdk (MARpc) — ouch-sdk ile order-service arasındaki TCP RPC katmanı
kaynak:
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
dogrulama: 2026-10-22
durum: taslak
---

# network-sdk (`libMARpc`)

FlatBuffers tabanlı, düşük gecikmeli TCP RPC kütüphanesi (C++). Tek görevi **ouch-sdk istemcileri (HFT, AlgoProd) ile order-service arasındaki** mesajlaşmadır.
- Hot path'te değildir: HFT'nin doğrudan emirleri MAOrderSDK ile gider.
- BIST ile ilgisi yoktur.

## Yapı (`sdk/`)

| Yer | İçerik |
|-----|--------|
| `Public/MARpc.h`, `MAOrderClient.h`, `MAOrderServer.h`, `MAOrderStruct.h`, `MAOrderEnums.h` | Public API: istemci (ouch-sdk kullanır) ve sunucu (order-service `OrderServer` kullanır) |
| `Client/MATCPClient`, `Server/MATCPServer` | TCP katmanı |
| `Models/orders.fbs`, `orders_response.fbs` | FlatBuffers şemaları (istek / yanıt) |
| `Models/ThreadPool.h`, `concurrentqueue.h` | İç kuyruklar |

## Mesajlar

- **İstek** (`RequestTypes`, `sdk/Public/MAOrderEnums.h`): Enter, Replace, Cancel, Login, AllOrders, AccountStrategy, Heartbeat. Sabah/açılış emri isteği yoktur.
- **Yanıt:** order accepted/rejected/executed/canceled/replaced ve `UserDisconnected` (handoff bildirimi).

`StrategyType` gibi enum'lar burada da tanımlıdır. Son commit'te `HFT_WARRANT_ADVANCED (15)` eklendi. Yeni strateji tipinde bu enum da güncellenir.

## Build

- CMake, `flatbuffers` bağımlılığı. Kütüphane adı `MARpc` (shared).
- CI `network.yml` → Algo-Setup `MAProdEnv`. Örnek uygulama: `demoapp/`.

Eski bilgi tabanının wire protokol ve bağlantı ayrıntıları (`network-sdk--wire-protocol.md`, `--connection-management.md`) büyük ölçüde geçerli. ❓ Tek tek yeniden doğrulanmadı.
