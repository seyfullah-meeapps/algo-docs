---
kapsam: HftSrvProd (HFT strateji motoru) — giriş ve indeks; dizin haritası, açılış özeti, thread modeli özeti, emir gönderme deseni, config özeti, build, yeni strateji ekleme
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# HftSrvProd

HFT strateji motoru (C++20). Strateji mantığı: [`20-stratejiler/`](../../20-stratejiler/README.md). Sistem içindeki yeri: [`00-genel/sistem-haritasi.md`](../../00-genel/sistem-haritasi.md).

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`komutlar-ve-grpc.md`](komutlar-ve-grpc.md) | `StrategyService` RPC'leri, UI'da "Başlat"a basınca ne olur, manuel emir komutları, command pattern ve `map<string, Any>` wire biçimi, GUI'ye dönen mesajlar, yeni wire alanı ekleme |
| [`strateji-cekirdegi.md`](strateji-cekirdegi.md) | `Strategy` taban sınıfı, `StrategyManager` (registry, oluşturma, replay gate, periyodik işler, durum push), thread/kilit modeli ayrıntısı, açılış/durdurma/restart senaryoları |
| [`emir-yasam-dongusu.md`](emir-yasam-dongusu.md) | Emir modeli ve ölçek, yol seçimi (MAOrderSDK / order-service), bölme, callback'ler ve stratejiye eşleme, handoff'un HFT tarafı, çift kayıt koruması, ret kodları, kopma senaryoları |
| [`itch-entegrasyonu.md`](itch-entegrasyonu.md) | ITCH SDK başlatma, hazır olma koşulu, abonelik tipleri × strateji matrisi, olay dağıtımı, seans durumu, fiyat ölçeği/tick, enstrüman bilgisinin kaynağı, uptick |
| [`config.md`](config.md) | `Configuration.toml` anahtar referansı, env değişkenleri, prod'da kapalı tutulanlar, müşteri config farkları |

## Dizin haritası (`src/`)

| Klasör | İçerik |
|--------|--------|
| `Main/HftMain.cpp` | `main()`: config, CPU pin, logger, PerfSDK, ITCH SDK, MAOrderSDK boot ve callback'leri, servislerin başlatılması, kapanış |
| `Strategy/` | `Strategy` taban sınıfı, strateji sınıfları, `StrategyDepth` / `StrategyLevel`, `Service/StrategyServiceImpl` (gRPC stream'leri) |
| `Commands/` | GUI komutları: strateji başına bir command, emir komutları, durum/özet komutları. Fabrika: `CommandFactory.h` |
| `Managers/StrategyManager` | Strateji registry'si (`unique_key` → strateji), oluşturma, periyodik işler, durum push'ları, replay gate |
| `Workers/` | `AlgoWorker` / `AlgoWorkerManager`. `OuchWorker*` ölü kalıntı. |
| `Clients/ItchSdkClient` | `libMAItchSDK` sarmalayıcısı: abonelikler ve olay dağıtımı |
| `Clients/OuchManager` | ouch-sdk istemcisi (order-service): handoff öncesi yedek emir yolu, strateji kaydı, handoff (`orderUserDisconnected`) |
| `Clients/OrderRegistry` | MAOrderSDK yolunda accept edilmiş emirler (`client_order_id` → emir) |
| `Clients/DatabaseServiceClient` | trade-data-app `AlgoService` istemcisi |
| `GUI/GUIManager` | gRPC sunucusu (`grpcPort`, varsayılan 9050), komut dispatch'i |
| `Messages/` | OUCH/ITCH mesaj modelleri, `MsgConvert` (HFT ↔ MAOrderSDK) |
| `Configuration/` | `Configuration.toml` (örnek), `ConfigurationManager` |
| `Globals/` | `GuiConstants.h` (wire alan adları; bazı giden anahtarlar ayrıca string literal), `Enumarations.h`, `GlobalConstants.h` (ret kodları) |
| `License/` | Lisans kontrolü; `HftMain`'de yorum satırında, **çalışmıyor** |
| `*.proto` | `strategies.proto`, `algo.proto`, `ouch-data.proto`, `common.proto` (`buf generate`) |

## Açılış sırası (`HftMain.cpp`)

Özet; ayrıntı ilgili alt dosyalarda.

1. Config dosyası argümanla verilir. Onload derlemesinde `LD_PRELOAD=libonload.so` ile kendini yeniden başlatır.
2. Config yüklenir; main thread `mainCpuCores`'a pinlenir (boşsa pin yok); `sdkLockMemory` açıksa `mlockall`.
3. Logger (Quill, `<logFile>/hft.txt`) ve PerfSDK (`monitoringEnabled`).
4. **ITCH SDK** ([itch-entegrasyonu](itch-entegrasyonu.md)). Combiner ITCH'e ihtiyaç duyduğu için MAOrderSDK'dan önce.
5. **MAOrderSDK boot** (sıra zorunlu): `OuchConfig` → `OrderSdkConfig` → `setInstrumentLimits` → `setStartArguments` + Onload → callback'ler → `start`. **Login yapılmaz**; OUCH kullanıcıları handoff ile gelir ([emir-yasam-dongusu](emir-yasam-dongusu.md#4-handoff--hft-tarafı)).
6. `AlgoWorkerManager`, `GUIManager` (gRPC), `ItchManager`, `StrategyManager` periyodik işleri ve durum worker'ı.
7. Konsola durum kutusu ve linklenen MeeApps kütüphanelerinin sürümleri basılır.
8. Ana döngü sinyal bekler; kapanış main thread'de. Kapanışta emir iptali veya state kaydı yapılmaz.

## Thread modeli

Özet; ayrıntı, kilit sırası ve kuyruklar: [strateji-cekirdegi § 3](strateji-cekirdegi.md#3-thread-modeli-ayrıntısı).

| Thread | Ne yapar |
|--------|----------|
| ITCH SDK thread'leri | Alım, emir defteri, abonelik callback'leri → olay stratejinin kuyruğuna |
| **AlgoWorker** (`workerCount`) | Stratejiler worker'lara dağıtılır; worker busy-loop'ta `processSingleEvent()` çağırır. Kararlar burada. |
| MAOrderSDK OUCH recv (kullanıcı başına) | Accept/cancel/replace/execute callback'leri. Yerel `onRejected` ise çağıran thread'de (AlgoWorker/gRPC) senkron gelir. |
| Combiner (açıksa) | `onExecuted` ITCH thread'inden gelebilir; GUI'ye giden fill `onWireExecuted` ile OUCH thread'inden |
| gRPC (GUIManager) | GUI komutları, `setCommand` |
| StrategyManager periyodik işler | Second rule / reClose timer'ları. Tavan/Taban'da yalnızca olay kuyruğa atar; HFT Classic'te emri bu thread'de gönderir. |
| StrategyStatesWorker | Dirty stratejilerin durum/özet push'u |

- **Hot/cold:** `hotWorkerCount > 0` (sayı değil bayrak) ise worker'lar önce hot stratejileri işler; `realHotReadyQueue` hot olayları hazır kuyruğa koyar.
- **Kuyruk sınırı:** strateji başına `strategyQueueMaxEvents`; dolunca **yeni gelen** olay düşürülür.

## Emir gönderme deseni

Bütün stratejiler aynı deseni kullanır:

```cpp
if (!maosdk || !maosdk->enterOrder(HftConvert::toSdkMsg(order, account, fatherRef))) {
    if (!maosdk || !maosdk->ownsAccount(account))
        OuchManager::instance().enterOrder(order, account, fatherRef);   // order-service yedek yolu
}
```

- SDK hesabın sahibiyse (handoff sonrası, bağlantı canlı) emir doğrudan BIST'e gider; değilse order-service'e.
- `ownsAccount` canlı bağlantı ister: OUCH koparsa emirler order-service'e düşer. SDK sahipken `false` dönerse emir **gönderilmez**.
- **Father order ref:** parçalanan emirlerin accept'leri toplanır (Tavan/Taban `orderCompletelyAccepted`).
- **Replay gate:** handoff sonrası replay bitene kadar stratejiler emir göndermez (20 sn watchdog, 60 sn zorunlu açılma).
- **Çift accept koruması:** `OrderRegistry` + `OuchManager::claimGlobalAcceptedToken`.

Ayrıntı ve istisnalar: [emir-yasam-dongusu](emir-yasam-dongusu.md).

## gRPC (`StrategyService`, :9050)

İstemci trade-data-app. RPC'ler, stream semantiği ve implement edilmeyenler (`FetchAllUniqueKeys`, `UpdateExtSettings` → UNIMPLEMENTED): [komutlar-ve-grpc](komutlar-ve-grpc.md). Wire biçimi `map<string, google.protobuf.Any>`; yeni alan için proto değişikliği gerekmez, DB'de kalıcı olması için `StrategyAttributes` satırı gerekir ([trade-data-app/sema](../trade-data-app/sema.md)).

## Config (`Configuration.toml`)

Tam referans: [config.md](config.md). Sık karıştırılanlar:

| Anahtar | Anlam |
|---------|-------|
| `dbIp`/`dbPort` | **trade-data-app gRPC** (MySQL değil) |
| `ouchIp`/`ouchPort` | **order-service MARpc** (BIST değil) |
| `[[ouch_users]]` | `isActive=false`: recv-thread ayar tablosu. `isActive=true`: açılışta SDK'ya önceden kaydedilir. Müşteri config'lerinde giriş yok. |
| `uptickRule` | Global uptick bayrağı; `uptickEnabled` kullanılmaz |
| `sdkLockMemory`, `mainCpuCores` | Repo örneğinde kapalı; müşteri config'lerinde farklı (bkz. config.md) |

## Build

- CMake + `buf generate` (`src/`). Bağımlılıklar `/usr/local/lib`'den: `libouchSDK`, `libMAItchSDK`, `libMAOrderSDK`, `libMAPerfSDK`, cpprest, gRPC/protobuf, OpenSSL, OpenMP. Onload (`onload_ext`) veya Mellanox (`vma`) bulunursa hızlandırma derlenir.
- CI: [`00-genel/branch-ve-ortamlar.md`](../../00-genel/branch-ve-ortamlar.md). Regular ve Onload binary'leri Algo-Setup `HFT/HftSrvProd/` altına yazılır.

## Yeni strateji eklemek (kontrol listesi)

1. `common.proto` `StrategyType` enum'una değer ekle, **bütün repolarda aynı numarayla**: HftSrvProd, order-service, trade-data-app, ouch-sdk enum'u, UI `app/types/index.ts`. Gerekirse `StrType` karşılığı da ([komutlar-ve-grpc](komutlar-ve-grpc.md)).
2. `Commands/<X>Command.{h,cpp}`: alanları `GuiConstants.h`'a ekle; `toClientMessage` ve `getDefaultSettings` yaz.
3. `Strategy/<X>.{h,cpp}`: `Strategy`'den türet; `setCommand`, `processSingleEvent`, OUCH callback'leri ([strateji-cekirdegi](strateji-cekirdegi.md)).
4. `CommandFactory::createStrategyCommand` ve `StrategyManager::createStrategy`'ye case ekle. Biri eksikse strateji oluşmaz (OrderChase örneği).
5. trade-data-app: `getApplicationFromStrategyType` (REST ve WS kopyası), `ConvertStrategyType`, `StrategyAttributes` SQL satırları.
6. UI: `STRATEGY_WORKSPACE_CONFIGS`, route, paneller.
