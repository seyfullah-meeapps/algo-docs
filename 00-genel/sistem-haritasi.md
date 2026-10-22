---
kapsam: Bileşenler, kim kimle hangi protokolle konuşur, emir yolları, OUCH handoff, başlatma sırası
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# Sistem haritası

## Bileşenler

| Bileşen | Repo | Dil | Rolü |
|---------|------|-----|------|
| **HFT** (HftSrvProd) | `HftSrvProd` | C++ | Strateji motoru #1: HFT Classic, Tavan (MaxPrice), Taban (MinPrice), Teorik, Varant, Varant Toplu. Emirleri BIST'e **MAOrderSDK ile doğrudan** gönderir (handoff sonrası). |
| **AlgoProd** (AlgorithmicTrading) | `AlgorithmicTrading` | C++ | Strateji motoru #2: Arbitraj, Sepet Arbitraj, VWAP, Fon Takibi (BYF). Emirleri **order-service üzerinden** gönderir (MAOrderSDK geçişi yolda). |
| **order-service** | `order-service` | C++ | Emir gateway'i. OUCH ve FIX oturumlarını tutar; ikisi de MAOrderSDK üzerinden (FIX motoru QuickFIX, SDK'ya statik gömülü). Sabah / açılış / akşam / YİP toplu emirleri, AlgoProd emirleri, risk kontrolü. Sabah emirlerinden sonra OUCH kullanıcılarını HFT'ye devreder. |
| **trade-data-app** (MADatabaseService, "data app") | `trade-data-app` | Go (cgo) | Merkez hub. MySQL'in tek sahibi; C++ servislere gRPC ile veri sağlar; GUI'nin REST + WebSocket gateway'i; kendi ITCH beslemesiyle emir defteri tutar; VERDA/Datastore/AKD/BYF entegrasyonları. |
| **mtrader-trade-ui** | `mtrader-trade-ui` | TS/React | Operatör arayüzü. `development` = yeni GUI, `main` = eski GUI; ikisi de prod'da (bkz. `branch-ve-ortamlar.md`). |
| **Admin paneli** | `mtrader-frontend-apps` | TS/React | Müşteri tarafında DB ayarlarını (kullanıcı, hesap, OUCH kullanıcısı vb.) arayüzden yönetmek için. |
| itch-sdk (`libMAItchSDK`) | `itch-sdk` | C++ | ITCH piyasa verisi SDK'sı: multicast alım, Glimpse snapshot, Rewinder gap kurtarma, emir defteri. HFT, AlgoProd ve trade-data-app (cgo) kullanır. |
| MAOrderSDK | `MAOrderSDK` | C++ | BIST emir istemci SDK'sı: OUCH (login, heartbeat, replay, token havuzu, Onload hızlı gönderim, ITCH+OUCH execute combiner) ve FIX (QuickFIX, statik gömülü). HFT ve order-service kullanır. |
| ouch-sdk | `ouch-sdk` | C++ | order-service'in **istemci** SDK'sı (isim yanıltıcı: BIST'e değil order-service'e bağlanır). HFT ve AlgoProd kullanır. |
| network-sdk (MARpc) | `network-sdk` | C++ | ouch-sdk ↔ order-service arasındaki TCP RPC katmanı. |
| performance-sdk (`MAPerfSDK`) | `performance-sdk` | C++ | Latency histogramları (HdrHistogram) → ClickHouse push. Prometheus endpoint'i yok (port parametresi kullanılmıyor). HFT, order-service, AlgoProd kullanır. |
| Warrant-Selector | `Warrant-Selector` | Python | Bağımsız araç: bir dayanağın varantlarını takas dağılımına göre tarar (Foreks/Fintables). Stack'e bağlı değil. |
| Itch-Replayer | `Itch-Replayer` | C/C++ | Bağımsız araç: ITCH multicast/Glimpse kaydı ve tekrar oynatma. Stack'e bağlı değil. |
| Algo-Setup | `Algo-Setup` | — | Derlenmiş binary'ler, servis dosyaları, scriptler. Branch = ortam. |
| algo-configs | `algo-configs` | — | İsmine rağmen çalışma config'i değil: container imajları, lisans uygulaması, insan için dokümanlar. Müşteri config'leri Algo-Setup'ta ([config-referansi](../40-operasyon/config-referansi.md)). |

**İsim karışıklıkları (sık sorulur):**
- C++ servislerin config'indeki `db*` / `database` anahtarları **MySQL değildir**; trade-data-app'in gRPC portudur (6620). MySQL'e yalnızca trade-data-app bağlanır.
- `ouchIp/ouchPort` (HFT ve AlgoProd config'i) **BIST değil**, order-service'in MARpc portudur (8000).
- "AlgoProd", "algotrading", "AlgorithmicTrading" aynı uygulamadır.
- "MADatabaseService", "DatabaseService", "data app", "trade-data-app" aynı uygulamadır.

## Bağlantı haritası

```
                        ┌──────────────────────────── BIST ────────────────────────────┐
                        │  ITCH multicast + Glimpse + Rewinder        OUCH (TCP)   FIX  │
                        └──────┬─────────────────┬─────────────┬────────┬─────────┬─────┘
                  ITCH (itch-sdk)          ITCH (itch-sdk)   ITCH(cgo)  │         │
                               │                 │             │        │         │
 ┌──────────────┐  MAOrderSDK  │                 │             │        │         │
 │     HFT      │──────────────┼─────────────────┼─────────────┼────────┘(handoff │
 │ (HftSrvProd) │◄─────────────┘                 │             │         sonrası) │
 └──┬───┬────┬──┘                                │             │                  │
    │   │    │ ouch-sdk / MARpc :8000            │             │                  │
    │   │    └───────────────┐                   │             │                  │
    │   │                    ▼                   │             │                  │
    │   │            ┌───────────────┐  MAOrderSDK (OUCH)      │                  │
    │   │            │ order-service │─────── (OUCH + FIX) ────┼──────────────────┘
    │   │            └──┬────────▲───┘                         │
    │   │  ouch-sdk     │        │ ouch-sdk / MARpc :8000      │
    │   │               │   ┌────┴─────┐                       │
    │   │               │   │ AlgoProd │◄──────────────────────┤ ITCH
    │   │               │   └────▲─────┘                       │
    │   │ gRPC :6620    │ gRPC   │ gRPC :9098                  │
    │   │ (AlgoService) │ :6620  │ (StrategyService)           │
    │   ▼               ▼        │                             │
    │  ┌──────────────────────────┴──────────┐                 │
    │  │          trade-data-app             │◄────────────────┘
    └─►│ gRPC :6620  REST :6621  WS :6623    │──── MySQL
gRPC   │ Admin REST :6688                    │
:9050  └──────▲───────────────▲──────────────┘
(Strategy     │ REST + WS     │ Admin REST
 Service)     │               │
       mtrader-trade-ui   admin paneli
```

Portlar `development`'taki örnek config'lerden; ortamlara göre değişebilir (`40-operasyon/`).

### Bağlantı tablosu

| İstemci → Sunucu | Protokol / port | Ne için |
|------------------|-----------------|---------|
| HFT, AlgoProd → BIST | ITCH multicast (UDP) + Glimpse (TCP) + Rewinder (UDP) — itch-sdk | Piyasa verisi. Spot 4 partition, VİOP 6 partition; birincil + ikincil hat. |
| trade-data-app → BIST | Aynı, cgo üzerinden `libMAItchSDK` | GUI emir defteri, best bid/ask, denge fiyatı, tavan/taban lot |
| HFT → BIST | OUCH, **MAOrderSDK** | Strateji emirleri — yalnızca handoff sonrası (aşağıda) |
| order-service → BIST | OUCH + FIX 5.0SP2, ikisi de MAOrderSDK | Toplu emirler, AlgoProd emirleri, HFT'nin handoff öncesi emirleri |
| HFT, AlgoProd → order-service | ouch-sdk / MARpc, TCP :8000 | Emir gönderme (AlgoProd: her zaman; HFT: handoff öncesi yedek yol), strateji kaydı, handoff bildirimi (`orderUserDisconnected`) |
| HFT, AlgoProd → trade-data-app | gRPC :6620 `AlgoService` | Login, enstrümanlar, hesaplar, strateji ayarları, arbitraj/fon verisi |
| order-service → trade-data-app | gRPC :6620 `DataService` | OUCH/FIX kullanıcıları, stratejiler, pozisyonlar, emir kalıcılığı |
| trade-data-app → HFT | gRPC :9050 `StrategyService` | GUI komutları (`SetCommandRequest`), komut/emir stream'leri (`FetchCommands`, `FetchOrders`) |
| trade-data-app → AlgoProd | gRPC :9098 `StrategyService` | Aynı sözleşme (AlgoProd kendi proto kopyasını kullanır) |
| trade-data-app → order-service | gRPC :9035 `OrderService` | Toplu emir gönderme (`SendOrder`; trade-data-app'teki Go sarmalayıcısının adı `OrderService.SetOrders`), emir stream'i (`SubscribeToOrders`) |
| mtrader-trade-ui → trade-data-app | REST :6621 (grpc-gateway) + WebSocket :6623 | Bkz. aşağıdaki WS feed listesi |
| Admin paneli → trade-data-app | REST, `AdminService` grpc-gateway (:6688); müşteri başına `admin<musteri>.meeapps.com.tr` domain'i (`mtrader-frontend-apps/.github/workflows/adminui.yml`). Domain → :6688 yönlendirmesini müşteri sunucusundaki `nginx-proxy` yapar (Algo-Setup `Configs/<M>/nginx/`; [config-referansi § 3.1](../40-operasyon/config-referansi.md#31-port-matrisi)). | Kullanıcı/hesap/OUCH kullanıcısı yönetimi |
| HFT, order-service, AlgoProd → izleme | ClickHouse HTTP push (MAPerfSDK, ayrı thread) | Latency metrikleri |

trade-data-app WebSocket feed'leri (`pkg/gui/connections/ws_listener.go`): `/ws/v1/itch/start` (emir defteri derinliği), `/ws/v1/orders/start` (emir olayları), `/ws/v1/strategy/start` (strateji komut/durum), `/ws/v1/best/start` (best bid/ask), `/ws/v1/equilibrium/start` (denge fiyatı), `/ws/v1/bounds/start` (tavan/taban lot), `/ws/v1/passive-orders/start` (pasif emirler).

## Emir yolları

Bir emrin hangi yoldan BIST'e gittiği, **kimin gönderdiğine** ve **saate** bağlıdır.

| Emir | Yol |
|------|-----|
| HFT strateji emri, handoff **sonrası** | HFT → MAOrderSDK → BIST OUCH. En hızlı yol (hot path). |
| HFT strateji emri, handoff **öncesi** | HFT → ouch-sdk → order-service → BIST. Yedek yol; `OuchManager::enterOrder` WARN log'u basar. |
| AlgoProd strateji emri | AlgoProd → ouch-sdk → order-service → BIST. 🚧 Yolda: AlgoProd'a MAOrderSDK + OUCH handoff geliştirmesi `add-order-sdk` branch'inde (12 commit, son 2026-10-15; `MAOrderSdkManager`, `MAOrderSdkRouter`, `OrderEventDispatcher`). Merge edilince AlgoProd da HFT gibi handoff sonrası doğrudan gönderecek. |
| GUI'den sabah / açılış / akşam / YİP emri (`OrderType` MORNING / OPENING / EVENING) | UI → trade-data-app REST `GuiSendOrders` → order-service gRPC `SendOrder` → order-service emirleri `BulkInsert*Order` ile DB'ye yazar (`DataService.SetOrders`) ve GUI'ye yayınlar → zamanı gelince gönderir (`repeatableOrders`, `openingOrders` config'i). |
| GUI'den strateji ekranında manuel emir (`OrderType` STRATEGY) | UI → trade-data-app → ilgili motora komut (`Command_Type_OrderRequest`) → motor kendi yolundan gönderir. |

Hangi `StrategyType`'ın hangi motora gittiği: trade-data-app `getApplicationFromStrategyType` (`pkg/servicemodels/gui_api.go`). Liste için `20-stratejiler/README.md`.

## OUCH handoff (sabah devri)

Görece yeni bir geliştirme; şu an yalnızca HFT için development'ta. AlgoProd (arbitraj) için aynı mekanizma `add-order-sdk` branch'inde geliştiriliyor.

Sabah emirleri (09:40 civarı, config'e bağlı) order-service'ten gönderilir. HFT'nin kullandığı OUCH kullanıcıları DB'de "only morning order user" olarak işaretlidir ve bir *application user*'a (ör. `hftUser`) bağlıdır. Devir sırası:

1. HFT açılırken MAOrderSDK'yı başlatır ama **hiçbir OUCH kullanıcısına login olmaz**. O kullanıcılar order-service'tedir; ikinci bir login BIST tarafından reddedilir.
2. order-service sabah emirlerini gönderir. Her OUCH `repeatableOrders` satırının (`morning_viop` dahil) ve FIX akışının sonunda, ya da `type: morning` satırının saati + 30 sn geçince ([ayrıntı](../10-servisler/order-service/sdk-ve-oturumlar.md)) `MAOSdkManager::DisconnectMorningOrderUsers` çalışır. Uygulama kullanıcısının (HFT) order-service'e bağlı olmasını bekler, OUCH bağlantısını kapatır (`disconnectUser` yalnız soketi kapatır; SoupBinTCP LogoutRequest gönderilmez) ve `UserDisconnected` mesajını (kullanıcı adı, şifre, IP, port, izinli hesaplar, `callbackNumber/total`) MARpc ile HFT'ye yollar.
3. HFT `ouchSDK::orderUserDisconnected` callback'inde bu bilgilerle `maosdk->connectUser` çağırır. BIST eski oturumu henüz bırakmamış olabileceğinden 4 kez artan beklemeyle tekrar dener (2026-08-03 olayı).
4. Login sonrası MAOrderSDK günün emirlerini **replay** eder. HFT'nin *replay gate*'i tüm devredilen kullanıcıların replay'i bitene kadar stratejileri ITCH'e kapalı tutar.
   - 20 sn içinde hiç handoff gelmezse gate yine de açılır (zero-handoff watchdog, `StrategyManager.cpp`).
5. Bu noktadan sonra o hesapların emirleri doğrudan MAOrderSDK'dan gider.

Sonuçlar:
- Aynı emir hem order-service yolundan hem replay'den gelebilir. Çift kayıt `OrderRegistry` + `claimGlobalAcceptedToken` ile engellenir (`HftMain.cpp` `onAccepted`).
- HFT, OUCH kullanıcılarını handoff'tan öğrenir. Config'deki `[[ouch_users]]`'ın `isActive=false` girişleri yalnızca recv-thread ayar tablosudur. `isActive=true` giriş açılışta SDK'ya önceden kaydedilir ve handoff gelince handoff verisi yerine config'teki ip/şifre kullanılır — müşteri config'lerinde (Algo-Setup `development`, 2026-10-22) hiç `[[ouch_users]]` girişi yok, pratikte bu yol kullanılmıyor ([emir-yasam-dongusu](../10-servisler/hftsrvprod/emir-yasam-dongusu.md)).

Kod: order-service `Managers/Sdk/MAOSdkManager.cpp` (`TriggerOuchDisconnect`, `TryDisconnectUser`), `OrderServiceApplication.cpp` (geç başlatma); HFT `src/Clients/OuchManager.cpp` (`orderUserDisconnected`), `src/Main/HftMain.cpp` (MAOrderSDK boot + callback'ler).

## Başlatma sırası

1. **trade-data-app**: DB + gRPC. ITCH açıksa ilk snapshot'ı bekler, sonra gRPC/REST'i açar. GUI WebSocket ve dış servis bağlantıları (HFT, order-service, AlgoProd) **`DataService.Login` ilk kez başarılı olduktan sonra** başlar; bu login'i yapan order-service'tir (`cmd/dataapp/main.go` `guiChan`, `pkg/servicemodels/ouch_api.go` `Login`). Yani order-service gelmeden UI'ya WebSocket açılmaz.
2. **order-service**: trade-data-app'ten enstrüman/strateji/pozisyon çeker, OUCH/FIX oturumlarını açar, MARpc :8000 ve gRPC :9035'i dinler.
3. **HFT** ve **AlgoProd**: trade-data-app'e ve order-service'e bağlanır, ITCH'i başlatır. HFT ayrıca MAOrderSDK'yı hazır bekletir (login yok, handoff bekler).
4. UI'lar: trade-data-app ayaktayken bağlanır.

Açılış log imzaları ve sorun giderme: `40-operasyon/`.

## Performans prensipleri (tüm C++ kodu için)

- **Hot path** = ITCH alımı → strateji kararı → OUCH gönderimi (HFT içinde, handoff sonrası). Bu yolda allocation, kopya, kilit, sistem çağrısı istenmez.
- **order-service hot path'te değildir** (HFT için handoff sonrası); AlgoProd için ise emir yolunun parçasıdır.
- **Thread safety:** Callback'ler farklı thread'lerden gelir (OUCH recv thread, ITCH client thread, gRPC thread). Paylaşılan her state mutex/atomic ile korunur. Combiner açıkken `onExecuted` ITCH thread'inden de gelebilir (`HftMain.cpp` yorumları).
- CPU pinning, Onload ve `mlockall` config ile açılıp kapanır. Prod'da yaşanmış host kilitlenmeleri nedeniyle bazıları bilerek kapalıdır (`Configuration.toml` yorumları).
