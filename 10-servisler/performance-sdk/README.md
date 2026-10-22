---
kapsam: performance-sdk (libMAPerfSDK) — latency ölçümü; API, ClickHouse export, kullanan servislerdeki ayarlar
kaynak:
  - repo: performance-sdk
    branch: development
    commit: 6e47f20
dogrulama: 2026-10-22
durum: taslak
---

# performance-sdk (`libMAPerfSDK`)

Uygulama içi latency dağılımlarını HdrHistogram ile tutar ve isteğe bağlı olarak ClickHouse'a gönderir (C++).

**Kullananlar:**
- HftSrvProd: strateji T2T (tick-to-trade) zaman damgaları `ts1..ts6`, `hft::perf`.
- order-service, AlgoProd, MAOrderSDK: kullanıcı başına bağlantı metrikleri.
- itch-sdk: port başına alım metrikleri.

## Çalışma şekli

- Uygulama thread'i yalnızca zaman damgası alır ve olayı kuyruğa koyar.
- Arka plan worker'ı start/stop çiftlerini eşleyip histogramlara yazar.
- Ayrı bir exporter thread'i snapshot'ları ClickHouse'a (HTTP, 8123) gönderir.
- **Prometheus endpoint'i yoktur.** `start(app, port, …)`'taki port parametresi uyumluluk için duruyor, kullanılmıyor. Servis config'lerinde ve kod yorumlarında geçen "Prometheus :monitoringPort" ifadeleri eskidir.

## API (`sdk/Public/PerformanceClient.h`)

```cpp
PerformanceClient::instance().setPerformanceDbExporter(dbConfig);   // ClickHouse (opsiyonel)
PerformanceClient::instance().start(appName, port /*kullanılmıyor*/, minUs, maxUs, printValues);
auto id = PerformanceClient::instance().registerMetric("order_submit");   // açılışta bir kez
PerformanceClient::instance().startBenchmark(id, correlationId);
PerformanceClient::instance().stopBenchmark(id, correlationId);
PerformanceClient::instance().BenchmarkElapsedTime(id, ns);                // süre zaten ölçüldüyse
```

- `registerMetric` hot path'te çağrılmaz. `start()`'tan önce kayıt dönmez: id 0 sessiz no-op'tur. order-service bu yüzden PerfSDK'yı MAOrderSDK'dan önce başlatır.
- `minimumTime` / `maximumTime` **mikrosaniye** (histogram aralığı); saklanan değerler **nanosaniye**.
- Varsayılan üst sınır 2 ms'dir ve uzun kuyrukları kırpar. Servisler 60 sn (`perfMaxTimeUs` / `maxTimeUs` = 60000000) kullanır.

## Servis ayarları

| Servis | Anahtarlar |
|--------|------------|
| HftSrvProd | `monitoringEnabled`, `perfDbHost/Port/Name/Username/Password`, `perfAppName` (boşsa hostname), `perfMinTimeUs`, `perfMaxTimeUs`, `perfPrintValues` (açmayın: hot path'te konsol I/O) |
| order-service | `monitoring.active`, `monitoring.clickhouse.*`, `appName` (boşsa `ordersvc-<hostname>`), `maxTimeUs` |
| AlgoProd | `monitoringEnabled`, `monitoringPort` (app adı `algo_prod`) |

## Build

CMake. `third_party/HdrHistogram_c` git submodule'dür. CI `performance.yml` → Algo-Setup `MAProdEnv`. Örnek uygulama: `PerformanceTestApp/`.
