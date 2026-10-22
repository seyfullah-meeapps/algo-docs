---
kapsam: order-service (OUCH/FIX emir gateway'i) — giriş ve indeks; görev, dizin haritası, alt dosyalar, kısa özetler, build
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
dogrulama: 2026-10-22
durum: taslak
---

# order-service

Emir gateway'i (C++). BIST'e giden emirlerin HFT doğrudan yolu dışındaki tamamı buradan geçer:
- AlgoProd emirleri
- HFT'nin handoff öncesi emirleri ve OUCH'u kopmuş hesapların emirleri
- GUI'den girilen toplu emirler (sabah/açılış/YİP/akşam/teorik)

Sistem içindeki yeri: [`00-genel/sistem-haritasi.md`](../../00-genel/sistem-haritasi.md).

⚠ Eski bilgi tabanından farklar:
- order-service artık **MAOrderSDK** kullanıyor. **FIX de MAOrderSDK içinden** gidiyor (issue #402); QuickFIX SDK'ya statik gömülü.
- Sabah emirlerinden sonra OUCH kullanıcılarını HFT'ye devrediyor (handoff).
- ⚠ `master` (prod) hâlâ eski OuchManager/FIXManager yapısında. YİP, varant grubu, OUCH başına slice dağıtımı, `schedPolicy`, `coreToPin` yalnız `development`/`preprod`'da ([toplu-emirler](toplu-emirler.md)). Müşteri config'leri master şemasında yazılmış ([kalicilik-ve-config § B2](kalicilik-ve-config.md#b2-müşteri-configleri--yapısal-farklar)).

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`arayuzler.md`](arayuzler.md) | MARpc sunucusu (`OrderServer`, ouch-sdk istemcileri: HFT, AlgoProd), gRPC sunucusu (`OrderServiceImpl`, istemci trade-data-app), wire alanları ve ölçekleri, `OrderDispatcher` ile emrin girişten BIST'e ve olayın geri dönüşüne yolu, açılış sırası, thread/kilit modeli |
| [`sdk-ve-oturumlar.md`](sdk-ve-oturumlar.md) | `MAOSdkManager`: SDK boot, OUCH/FIX kullanıcı modeli, emir gönderme ve alan dönüşümleri, callback'ler, ölçek özeti, **OUCH handoff'un order-service tarafı**, FIX yolu ve şifre yenileme, yeniden bağlanma ve kopma senaryoları |
| [`toplu-emirler.md`](toplu-emirler.md) | Sabah (OUCH/VİOP/FIX), açılış, YİP, teorik/akşam, off-hours; zamanlama, kullanıcılara dağıtım, son atış ve `-110023` döngüsü, fazla kopya iptali, örnek zaman çizelgesi |
| [`risk.md`](risk.md) | `RiskManager`: hangi emir riskten geçer, trade-data-app'ten gelen veri ve birimler, `checkEnterOrder`/replace adımları, rezervasyon takibi, replay/restart, `LimitControlService` ve hard cap ile ilişki |
| [`kalicilik-ve-config.md`](kalicilik-ve-config.md) | trade-data-app `DataService` istemcisi, emir/pozisyon kalıcılığı ve gün içi restart, enstrüman verisi, `config.yaml` tam referansı, müşteri config farkları, deploy (Docker, Onload/Mlx) |

## Dizin haritası

| Yer | İçerik | Ayrıntı |
|-----|--------|---------|
| `main.cpp`, `OrderServiceApplication.*` | Başlatma: DB client, servisler, risk, dispatcher, MARpc ve gRPC sunucuları, PerfSDK; geç başlatmada handoff tetikleme | [arayuzler § 2](arayuzler.md#2-açılış-sırası) |
| `OrderServer.*` | **MARpc sunucusu** (network-sdk, `server.port`). Tüm arayüzleri dinler, ayrıca Unix soketi açar. gRPC sunucusunu da başlatır. | [arayuzler § 3](arayuzler.md#3-marpc-sunucusu-orderserver) |
| `Service/servicemodel/OrderServiceImpl.*` | **gRPC sunucusu** (`server.grpcPort`), istemci trade-data-app: `Login`, `SubscribeToOrders`, `StopSubscription`, `SendOrder` | [arayuzler § 4](arayuzler.md#4-grpc-sunucusu-orderserviceimpl) |
| `Managers/OrderDispatcher` | Protokole göre manager seçimi (FIX → OUCH manager'ına düşer), risk kontrolü, olay bağlama. `OrderManagerFactory` boş ve kullanılmıyor. | [arayuzler § 6](arayuzler.md#6-orderdispatcher-ve-emrin-yolu) |
| `Managers/OrderManager` | Taban sınıf: toplu emir akışları, DB yazma kuyruğu | [toplu-emirler](toplu-emirler.md) |
| `Managers/Sdk/MAOSdkManager` | MAOrderSDK adaptörü, açılış/YİP akışları, handoff | [sdk-ve-oturumlar](sdk-ve-oturumlar.md) |
| `Managers/Sdk/SdkSessionManager` | Yeniden bağlanma shim'i (OUCH), FIX şifre yenileme | [sdk-ve-oturumlar § 9](sdk-ve-oturumlar.md#9-oturumlar-yeniden-bağlanma-ve-kopma-senaryoları) |
| `Managers/RepeatableOrders/` | Son atış stratejileri (`SingleLastShot`, `RepeatedLastShot`) | [toplu-emirler § 3](toplu-emirler.md#3-tekrarlı-akış-ordermanagersendrepeatableordersconfig) |
| `Managers/RiskManager` | Ön-işlem risk | [risk](risk.md) |
| `Data/DatabaseClient`, `Service/Network/*` | trade-data-app `DataService` istemcisi | [kalicilik-ve-config § A1](kalicilik-ve-config.md#a1-dataservice-istemcisi-datadatabaseclient) |
| `Service/*/*.proto` | `servicemodel` (gRPC sunucu), `clientmodel` (DataService istemci), `limit` (risk). Paket/dizin adları ters. | [arayuzler § 5](arayuzler.md#5-proto-dosyaları--isimler-ters) |
| `Configuration/`, `config.yaml` | Config yükleme, örnek config | [kalicilik-ve-config § B1](kalicilik-ve-config.md#b1-config-referansı-configyaml) |

## Kısa özetler

Ayrıntı ve kod referansları alt dosyalarda; burada yalnız yön bulmak için.

- **Kullanıcılar:** OUCH ve FIX kullanıcıları DB'den gelir (`DataService.GetOuchUsers` / `GetFixUsers`), `mode` ile prod/test filtrelenir. Kullanıcının partition'ı DB'den okunmaz, hep 1'dir. `onlyMorningOrderUser` olanlar handoff'a girer.
- **Toplu emirler:** GUI → trade-data-app → gRPC `SendOrder`. Sabah akışı config saatinden 60 sn önce emirleri çeker, kullanıcı başına thread'de tam saatte gönderir. `-110023` yeniden gönderimi yalnız son atışta ve `repeatLastShot: true` iken, en çok 900 ms. Fazla kopya iptali thread'ler bittikten 2 sn sonra, yalnız `IsCancelAllowed` hesaplarda. `OffHours` bayrağı yalnız tekil gönderim yolunda (`SendOrderAsync`) konur.
- **Handoff:** Her OUCH `repeatableOrders` satırının (`morning_viop` dahil) ve FIX akışının sonunda, ya da `type: morning` saati + 30 sn'de tetiklenir. Pazar filtresi yoktur. `disconnectUser` yalnız soketi kapatır, SoupBinTCP logout gönderilmez. Sonra MARpc `UserDisconnected` gider.
- **Risk:** `database.riskControl: true` iken. Yalnız gün içi limitler stream; hesap ve hisse limitleri açılışta bir kez çekilir. Satış bakiye kontrolü yalnız kısıtlı hissede yapılır. Replay fill'i bakiyeye yazılmaması yalnız FIX için geçerlidir; OUCH replay fill'leri yeniden uygulanır.
- **Kalıcılık:** `SetOrders` yalnız enter ve replace'te (`STRATEGY` satırı) ve toplu akışlarda çağrılır; olaylar (accept/cancel/reject) DB'ye yazılmaz, fill'ler `SetPosition` (delta) ile yazılır. Açılışta `STRATEGY` satırları tarih filtresi olmadan yüklenir.
- **FIX replay:** Repo `config.yaml`'ında `resetOnLogon: false`, `replayFromSeq: 1`. Bütün müşteri config'lerinde `resetOnLogon: true`, yani restart'ta replay olmaz.

Açık sorunlar: [`ACIK-KONULAR.md`](../../ACIK-KONULAR.md) § order-service.

## Build

CMake, binary adı **`PiramitOrderService`**; `buf generate` (`Service/*`). Bağımlılıklar: `libMAOrderSDK` (QuickFIX içinde), `MARpc` (network-sdk), cpprest, yaml-cpp, fmt, OpenSSL, (opsiyonel) `libMAPerfSDK`, gRPC/protobuf. CI `orderservice.yml` → Algo-Setup. Deploy: [kalicilik-ve-config § B3](kalicilik-ve-config.md#b3-deploy-biçimi).
