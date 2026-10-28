---
kapsam: trade-data-app (MADatabaseService) — giriş ve indeks; rolü, portlar, paket haritası, açılış özeti, alt dosyalar
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app (MADatabaseService)

Go servisi (cgo ile `libMAItchSDK`). Sistemin merkezidir:
- MySQL'in **tek** sahibi.
- C++ servislerine (order-service, HFT, AlgoProd) veri sağlayan gRPC sunucusu.
- GUI'nin ve admin panelinin REST gateway'i, GUI'nin WebSocket sunucusu.
- GUI'den gelen komutları HFT, AlgoProd ve order-service'e ileten istemci.
- Kendi ITCH beslemesiyle emir defteri tutar.
- Dış veri entegrasyonları (VERDA, Datastore, AKD, BYF, AWS).

Sistem içindeki yeri: [`00-genel/sistem-haritasi.md`](../../00-genel/sistem-haritasi.md).

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`api.md`](api.md) | Hangi gRPC/REST ucu var, kim çağırıyor, kimlik doğrulama, JSON lehçesi; trade-data-app'in istemci olduğu sözleşmeler (order-service, HFT, AlgoProd) |
| [`veri-akisi.md`](veri-akisi.md) | Açılış ayrıntısı, ITCH → emir defteri, WebSocket feed'leri (mesaj alanları), motor/order-service stream'leri, goroutine/kilit modeli |
| [`sema.md`](sema.md) | MySQL tabloları ve kolonları, ilişkiler, strateji ayar modeli (`StrategyAttributes`/`StrategySettings`), yeni wire alanı eklerken DB'de ne gerekir |
| [`entegrasyonlar.md`](entegrasyonlar.md) | VERDA (TradeVerifier), Datastore, fiktif endeksler, AKD skorları, BYF, history/volatilite, limitler, AWS, dosya parser'ları, request log |
| [`config.md`](config.md) | `config.json` anahtar referansı, env override'ları, müşteri config'leri arasındaki farklar |

## Portlar

| Port (örnek config) | Config | Ne |
|------|--------|----|
| 6620 | `server.port` | gRPC: `DataService`, `AlgoService`, `GuiService`, `AdminService`, `LimitControlService`, `RiskManagerService` |
| 6621 | `server.restPort` | REST (grpc-gateway) — `GuiService` (UI) |
| 6688 | `server.adminApiPort` | REST (grpc-gateway) — `AdminService` (admin paneli) |
| 6623 | `gui.port` | WebSocket (`/ws/v1/...`) |

Process içinde TLS yok; REST ve WS düz HTTP dinler ([config.md](config.md)).

Dışa giden bağlantılar (`extServices`): order-service gRPC :9035, HFT :9050, AlgoProd :9098 — RPC listesi [api.md](api.md), akış [veri-akisi.md](veri-akisi.md).

## Paket haritası (`pkg/`)

| Paket | İçerik |
|-------|--------|
| `cmd/dataapp/main.go` | Açılış sırası |
| `cmd/requestlog-report` | Request log rapor aracı |
| `conf` | `config.json` okuma (viper; varsayılan yok, eksik anahtar = Go sıfır değeri) |
| `db`, `db/mysql`, `db/models` | MySQL erişimi: `ouchdb.go` (order-service), `algodb.go` (motorlar), `guidb.go`, `admin_db.go`, `mysqldb.go` |
| `servicemodels` | gRPC servis implementasyonları (`ouch_api.go` = DataService, `gui_api.go`, `algo_api.go`, `admin_api.go`, `limit_control_api.go`, `risk_manager_api.go`, `warrant_api.go`) + `server.go` (gRPC + grpc-gateway) |
| `gui/connections` | Dışa giden gRPC istemcileri (`hft.go`, `algotrading.go`, `orderservice.go`, yeniden bağlanma) ve WebSocket sunucusu (`ws_listener.go`, `client.go`) |
| `gui/messages`, `gui/clientmodels` | WS mesaj modelleri |
| `itch` | cgo ITCH SDK sarmalayıcısı, enstrümanlar (`priceDivider = 10^DecimalCount`), emir defteri, abonelikler |
| `pubsub` | WS feed'leri için yayın/abone |
| `extdata/tradeverifier`, `extdata/datastore`, `extdata/akd` | VERDA, Datastore, AKD |
| `history`, `pricedata`, `volatility` | Geçmiş fiyat ve volatilite |
| `limits` | Limit modelleri |
| `requestlog` | REST isteklerinin loglanması |
| `util` | JWT/token, gRPC interceptor'ları, AWS (SMS OTP, e-posta), Excel/varant dosyası parser'ları |
| `version` | Linklenmiş MeeApps kütüphanelerinin sürümleri |

## Açılış sırası (`cmd/dataapp/main.go`)

Özet; bekleme noktaları ve hata davranışı [veri-akisi.md](veri-akisi.md), entegrasyon adımları [entegrasyonlar.md](entegrasyonlar.md).

1. Config, log, request log, MySQL.
2. ITCH manager. `itchEnabled` ise config'deki **tüm** pazarların snapshot'ı ve tek seferlik bootstrap (endeksler, dayanak ilişkileri, `Instrument` tablosuna yazım) beklenir.
3. History/volatilite (`historyManagerEnabled` ve `itchEnabled` gerekir).
4. API nesneleri; AKD manager (`akd` + history + ITCH açıksa).
5. BYF ve fiktif enstrüman (endeks) ayarları; hata açılışı durdurur.
6. **TradeVerifier** (`tradeVerifier.enabled`): VERDA dosyalarından tavan/taban/son fiyat/maks emir değeri `Instrument` tablosuna ve belleğe. **`minPrice`/`maxPrice`/`maxOrderValue`'yu yazan tek yer budur**; çalışmazsa C++ servisleri tavan/taban bilmez, Tavan/Taban stratejileri çalışmaz.
7. gRPC, REST ve Admin REST sunucuları.
8. **İlk `DataService.Login`** (order-service) beklenir; ardından dış servislere (order-service, HFT, AlgoProd) bağlanılır ve WebSocket sunucusu açılır.

## Entegrasyonlar

| Entegrasyon | Config | Ne |
|-------------|--------|----|
| VERDA (Borsa İstanbul) | `tradeVerifier.*` | Günlük tavan/taban, son fiyat, maks emir değeri, brüt takas (yalnızca pay piyasası) |
| Datastore (Borsa İstanbul) | `datastore.*` | Endeks CSV'lerini indirir |
| AKD (Foreks) | `akd.*` | Aracı kurum dağılımı ve skorlar (VWAP filtresi, AlgoProd) |
| BYF dosyası | `byf.*` | Fon sepeti (Fon Takibi); bellekte tutulur |
| AWS | env | OTP SMS, şifre sıfırlama e-postası |

Ayrıntı: [entegrasyonlar.md](entegrasyonlar.md).

## Build ve çalıştırma

- Go modülü, cgo ile `libMAItchSDK` gerekir. `Dockerfile`, `docker-compose.yml`; `generate.sh` proto üretimi.
- Proto kaynakları: `api/protobuf-spec/` (sunduğu servisler), `api/client-spec/` (istemcisi olduğu sözleşmeler).
- CI `dbservice.yaml` → Algo-Setup (DatabaseService). Deploy: [kurulum-ve-dagitim](../../40-operasyon/kurulum-ve-dagitim.md).
