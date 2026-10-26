---
kapsam: Teknik temeller konu dosyaları ve kapsamları
dogrulama: 2026-10-24
durum: taslak
---

# Teknik temeller — bölüm indeksi

10 konunun tamamı 25 Ekim 2026 tarihinde yazıldı ve kitaba eklendi. Gündelik benzetmeler, sayısal örnekler ve MTrader KB bağlantıları kullanıldı. Genel teknik kaynaklar ile belirli referans commit’lerinde yapılan sınırlı kod kontrolü ayrı kaydedildi. Yeni bölüm henüz kullanıcı tarafından incelenmedi.

| Konu | Kapsam | Durum |
|---|---|---|
| [Program, servis, container ve SDK](01-program-servis-container-sdk.md) | Repo, binary, process, servis, image/container ve kütüphane; birebir eşleşme varsaymamak | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [Ağ, TCP, UDP ve multicast](02-ag-tcp-udp-multicast.md) | IP/port, istemci/sunucu, bağlantı, paket, sıra numarası; kayıp, tekrar ve gecikme | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [HTTP, REST ve WebSocket](03-rest-websocket.md) | İstek/yanıt, durum kodu, kimlik doğrulama; abonelik, push ve reconnect | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [gRPC, Protobuf ve MARpc](04-grpc-protobuf-marpc.md) | RPC, proto sözleşmesi, kod üretimi, unary/stream ve FlatBuffers; taşıma ve serileştirme | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [Binary veri, fiyat ölçeği ve zaman](05-binary-fiyat-ve-zaman.md) | Byte, endianness, fixed-point, raw/TL, overflow; ms/s/ns ve UTC/yerel saat | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [C++ bellek ve nesne yaşam süresi](06-cpp-bellek-ve-yasam-suresi.md) | Stack/heap, pointer/reference, sahiplik, RAII, smart pointer; dangling pointer ve iterator | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [Thread, kuyruk ve eşzamanlılık](07-thread-kuyruk-ve-kilit.md) | Callback, event loop, producer/consumer, mutex, atomic, race condition ve deadlock | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [Gecikme, colocation ve performans](08-gecikme-ve-colocation.md) | Latency/throughput, tail latency, hot/cold path; pinning, cache, allocation ve kernel bypass | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [Bağlantı ve kurtarma kavramları](09-baglanti-ve-kurtarma.md) | Heartbeat, timeout, reconnect, snapshot, replay, dedup, idempotency ve tekrar deneme | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |
| [Log, test ve sürüm bilgisi](10-log-test-ve-surum.md) | Log/metric/trace, korelasyon kimliği; unit/entegrasyon/replay/UAT; branch/commit/binary/config | Taslak yazıldı; toplu kullanıcı incelemesi bekleniyor |

[Ana indeks](../README.md)
