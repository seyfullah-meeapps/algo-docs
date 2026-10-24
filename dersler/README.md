---
kapsam: Konu bazlı insan rehberinin ayrıntılı indeksi ve okuma sırası
dogrulama: 2026-10-24
durum: taslak
---

# MTrader uygulama ve sistem rehberi

Bu rehber uygulamanın amacından başlayıp borsa ve teknik temellere, sistem mimarisine ve stratejilere ilerler. Okuyucu frontend bilgisi olan bir PM veya projeye yeni gelen biri olabilir. Hedef; uygulamayı anlamak, davranışı açıklamak, test tasarlamak ve kanıtıyla issue/görev yönetmektir.

**Borsa temellerinin 12 konusu da yazıldı.** Kitapta uygulama girişinin iki konusuyla toplam 14 konu bulunuyor. Borsa bölümü kullanıcı tarafından topluca okunup revize edilecek; teknik temellere henüz geçilmiyor. Kalan 34 konu iskelet. Klasör adı bağlantıların devamlılığı için `dersler/` kaldı; yapı konu bazlı rehberdir.

## Devam edecek agent için

**A4 okuma ve çıktı:** PDF/HTML/EPUB üretimi, canlı önizleme ve VS Code görevleri için [yayın kullanımını](yayin/README.md) izle. Markdown dosyaları ana kaynaktır; PDF sayfaları ve içindekiler otomatik hesaplanır.

Repo kökündeki [oturum notları](../OTURUM-NOTLARI.md), ardından [rehber talimatları](AGENTS.md), [kararlar](kararlar.md), [ilerleme](ilerleme.md) ve [çalışma düzeni](calisma-duzeni.md) okunur. Devamlılık sohbet belleğine bağlı değildir. Yazılmış ve kullanıcıyla konuşulmuş içerik ayrı izlenir.

## Ayrıntılı içerik planı

### 1. Uygulamanın amacı

[Bölüm indeksi](01-uygulama/README.md)

| No | Konu dosyası | İçerik sınırı |
|---|---|---|
| 1.01 | [Ne yapıyoruz ve neyi amaçlıyoruz?](01-uygulama/01-ne-yapiyoruz.md) | Ürünün amacı, kullanıcı ihtiyacı, piyasa verisi, otomatik karar ve emir; kapsam ve sınırlar |
| 1.02 | [Kullanıcılar ve geliştirme süreci](01-uygulama/02-kullanicilar-ve-is-gunu.md) | Müşteri kullanıcıları; MeeApps geliştirme, test, preprod ve dağıtım süreci |

### 2. Borsa temelleri

[Bölüm indeksi](02-borsa-temelleri/README.md)

| No | Konu dosyası | İçerik sınırı |
|---|---|---|
| 2.01 | [Piyasalar, ürünler ve miktar birimleri](02-borsa-temelleri/01-piyasalar-ve-urunler.md) | BIST, Pay Piyasası, VİOP; pay, endeks, vadeli, varant, BYF; lot ve sözleşme çarpanı |
| 2.02 | [Emir defteri ve eşleşme](02-borsa-temelleri/02-emir-defteri.md) | Bid/ask, spread, kademe, likidite, fiyat-zaman önceliği, kuyruk, header ve erime |
| 2.03 | [Fiyat adımı ve fiyat sınırları](02-borsa-temelleri/03-fiyat-adimi-ve-limitler.md) | Tick, fiyat bandı, baz fiyat, tavan/taban; günlük veri ve kural ayrımı |
| 2.04 | [Emir tipleri ve geçerlilik süreleri](02-borsa-temelleri/04-emir-tipleri-ve-sureleri.md) | Limit, piyasa, piyasadan limite; DAY, IOC/KIE, FOK; seans ve destek sınırları |
| 2.05 | [Emir yaşam döngüsü](02-borsa-temelleri/05-emir-yasam-dongusu.md) | Gönderim, kabul, ret, kısmi/tam gerçekleşme, iptal, replace; istek ve onay |
| 2.06 | [Seanslar, müzayede ve denge fiyatı](02-borsa-temelleri/06-seanslar-ve-muzayede.md) | Toplama, eşleştirme, sürekli işlem, kapanış, tek fiyat/devre kesici; ürün bazlı saatler ve saat dilimi |
| 2.07 | [Pozisyon, bakiye ve kâr/zarar](02-borsa-temelleri/07-pozisyon-bakiye-kar-zarar.md) | Long/short/flat, açık emir maruziyeti, nakit/satılabilir bakiye, maliyet, komisyon ve kredili işlemler |
| 2.08 | [Takas, T+2 ve brüt takas](02-borsa-temelleri/08-takas-ve-tedbirler.md) | İşlem/takas günü, iş günü ve tatil, T+N; ürün ve yürürlük tarihi; netleştirme ve tedbirler |
| 2.09 | [Açığa satış ve uptick](02-borsa-temelleri/09-aciga-satis-ve-uptick.md) | Sahiplik, işaretleme, izin, fiyat kuralı; tarihli BIST/SPK kararı ve uygulama kontrolü |
| 2.10 | [ITCH, OUCH ve FIX](02-borsa-temelleri/10-itch-ouch-fix.md) | Piyasa verisi ve emir protokolü; kendi emrimiz ve piyasanın defteri; mesaj aileleri |
| 2.11 | [Glimpse, Rewinder ve replay](02-borsa-temelleri/11-glimpse-rewinder-replay.md) | Başlangıç görüntüsü, kayıp piyasa verisini kurtarma ve emir oturumu replay farkı |
| 2.12 | [Stratejilerin temel fikirleri](02-borsa-temelleri/12-strateji-fikirleri.md) | HFT, kademe takibi, arbitraj, hedge ve piyasa yapıcılık; fırsat ve gerçekleşme riski |

### 3. Teknik temeller

[Bölüm indeksi](03-teknik-temeller/README.md)

| No | Konu dosyası | İçerik sınırı |
|---|---|---|
| 3.01 | [Program, servis, container ve SDK](03-teknik-temeller/01-program-servis-container-sdk.md) | Repo, binary, process, servis, image/container ve kütüphane; birebir eşleşme varsaymamak |
| 3.02 | [Ağ, TCP, UDP ve multicast](03-teknik-temeller/02-ag-tcp-udp-multicast.md) | IP/port, istemci/sunucu, bağlantı, paket, sıra numarası; kayıp, tekrar ve gecikme |
| 3.03 | [HTTP, REST ve WebSocket](03-teknik-temeller/03-rest-websocket.md) | İstek/yanıt, durum kodu, kimlik doğrulama; abonelik, push ve reconnect |
| 3.04 | [gRPC, Protobuf ve MARpc](03-teknik-temeller/04-grpc-protobuf-marpc.md) | RPC, proto sözleşmesi, kod üretimi, unary/stream ve FlatBuffers; taşıma ve serileştirme |
| 3.05 | [Binary veri, fiyat ölçeği ve zaman](03-teknik-temeller/05-binary-fiyat-ve-zaman.md) | Byte, endianness, fixed-point, raw/TL, overflow; ms/s/ns ve UTC/yerel saat |
| 3.06 | [C++ bellek ve nesne yaşam süresi](03-teknik-temeller/06-cpp-bellek-ve-yasam-suresi.md) | Stack/heap, pointer/reference, sahiplik, RAII, smart pointer; dangling pointer ve iterator |
| 3.07 | [Thread, kuyruk ve eşzamanlılık](03-teknik-temeller/07-thread-kuyruk-ve-kilit.md) | Callback, event loop, producer/consumer, mutex, atomic, race condition ve deadlock |
| 3.08 | [Gecikme, colocation ve performans](03-teknik-temeller/08-gecikme-ve-colocation.md) | Latency/throughput, tail latency, hot/cold path; pinning, cache, allocation ve kernel bypass |
| 3.09 | [Bağlantı ve kurtarma kavramları](03-teknik-temeller/09-baglanti-ve-kurtarma.md) | Heartbeat, timeout, reconnect, snapshot, replay, dedup, idempotency ve tekrar deneme |
| 3.10 | [Log, test ve sürüm bilgisi](03-teknik-temeller/10-log-test-ve-surum.md) | Log/metric/trace, korelasyon kimliği; unit/entegrasyon/replay/UAT; branch/commit/binary/config |

### 4. Bizim sistemimiz

[Bölüm indeksi](04-sistem-mimarisi/README.md)

| No | Konu dosyası | İçerik sınırı |
|---|---|---|
| 4.01 | [Repo ve bileşen haritası](04-sistem-mimarisi/01-repolar-ve-bilesenler.md) | Repo, uygulama/kütüphane ve görev; HFT, AlgoProd, hub, gateway, UI ve yardımcılar |
| 4.02 | [Container, süreç ve dağıtım haritası](04-sistem-mimarisi/02-container-ve-dagitim.md) | Compose/service/image/binary/config eşlemesi; container dışında çalışan süreçler; ortam kanıtı |
| 4.03 | [Bağlantılar ve protokoller](04-sistem-mimarisi/03-iletisim-semasi.md) | İstemci/sunucu; REST/WS/gRPC/MARpc/ITCH/OUCH/FIX okları ve port/config kaynağı |
| 4.04 | [Piyasa verisi ve itch-sdk](04-sistem-mimarisi/04-piyasa-verisi-yolu.md) | BIST, SDK, motor/hub ve UI; snapshot, partition, callback, kurtarma ve ayrı veri yolları |
| 4.05 | [Emir SDK’ları ve gateway](04-sistem-mimarisi/05-emir-sdk-ve-gateway.md) | MAOrderSDK, ouch-sdk, network-sdk, order-service; motor yönlendirmeleri ve risk sınırları |
| 4.06 | [Hub, veritabanı ve GUI](04-sistem-mimarisi/06-hub-veritabani-ve-gui.md) | trade-data-app, veri sahipliği, REST/WS, kimlik/yetki, komut ve olay dağıtımı |
| 4.07 | [Motorlar ve strateji durumu](04-sistem-mimarisi/07-motorlar-ve-strateji-durumu.md) | HFT/AlgoProd, strateji kimliği, ayarlar, command, snapshot, pozisyon ve start/stop |
| 4.08 | [Açılış, handoff ve replay](04-sistem-mimarisi/08-acilis-handoff-ve-replay.md) | Bağımlılık ve hazırlık; OUCH devri; doğrudan/yedek yol; replay gate ve restart |
| 4.09 | [Bir işlemin uçtan uca akışı](04-sistem-mimarisi/09-uctan-uca-islem.md) | UI başlat, hub, motor, piyasa tetiği, emir, callback ve ekran; ayrı sequence şemaları |
| 4.10 | [Kopma ve gözlem noktaları](04-sistem-mimarisi/10-kopma-ve-gozlem.md) | ITCH, OUCH, MARpc, gRPC ve WS kopmaları; belirtiden katmana; log/metric ve tekrar olaylar |
| 4.11 | [Ortam, config ve release](04-sistem-mimarisi/11-ortam-config-ve-release.md) | Development/preprod/prod, eski/yeni GUI; image/binary/config ve sürüm farkları |

### 5. Stratejiler

[Bölüm indeksi](05-stratejiler/README.md)

| No | Konu dosyası | İçerik sınırı |
|---|---|---|
| 5.01 | [HFT Classic](05-stratejiler/01-hft.md) | Öncelik 1; GUI modları, tetik/lot, TP/stop/second rule, ayar değişiklikleri ve testler |
| 5.02 | [Arbitraj](05-stratejiler/02-arbitraj.md) | Öncelik 2; GUI, spot/vadeli miktar ve fiyat, giriş/çıkış, hedge ve eksik bacak |
| 5.03 | [Toplu Emirler](05-stratejiler/03-toplu-emirler.md) | Öncelik 3; sabah/açılış/akşam/YİP, kayıt, zamanlama, tekrar ve handoff; Varant Toplu değildir |
| 5.04 | [Tavan](05-stratejiler/04-tavan.md) | Öncelik 4; GUI, kilit/erime, eşikler, süpürme, çıkış, yeniden kapanma ve timer |
| 5.05 | [Taban](05-stratejiler/05-taban.md) | Öncelik 5; GUI, IOC ve kısmi dolum, satış, stop/timer ve açık pozisyon |
| 5.06 | [Teorik Fiyat](05-stratejiler/06-teorik-fiyat.md) | GUI, denge ve seans olayları, beklenen fiyat, iptal/ters emir ve zamanlama |
| 5.07 | [Varant](05-stratejiler/07-varant.md) | GUI, dayanak, tetik, varant girişi, çıkış ve maliyet |
| 5.08 | [Varant Toplu](05-stratejiler/08-varant-toplu.md) | GUI ve feature sınırları, çoklu ürün, miktar ve çıkış; SDK/dağıtım uyumu |
| 5.09 | [VWAP](05-stratejiler/09-vwap.md) | GUI, hacme göre yürütme, hedef/kalan, zaman ve tamamlanma |
| 5.10 | [BYF / Fon Takibi](05-stratejiler/10-byf.md) | En düşük strateji önceliği; fon/sepet verisi, GUI, fiyat/lot ve parça bazlı dolum |

### 6. Test ve proje yönetimi

[Bölüm indeksi](06-test-ve-proje-yonetimi/README.md)

| No | Konu dosyası | İçerik sınırı |
|---|---|---|
| 6.01 | [Test tasarımı ve kanıt](06-test-ve-proje-yonetimi/01-test-tasarimi.md) | Ön koşul, sınır ve etkileşim, ret ve kısmi dolum; beklenen/gözlenen ve kanıt |
| 6.02 | [Issue ve görev yönetimi](06-test-ve-proje-yonetimi/02-issue-ve-gorev.md) | Etki/öncelik, tekrar adımları, kabul kriteri, katmana göre sorumlu ve bağlı işler |
| 6.03 | [Regresyon ve sürüm kabulü](06-test-ve-proje-yonetimi/03-regresyon-ve-kabul.md) | Düzeltme sürümü, aynı senaryo tekrarı, etkilenen stratejiler ve kapanış kanıtı |

## Stratejilerin ortak içeriği

Amaç ve ön koşullar → GUI görünümü → parametre/birim/varsayılan → backend akışı → sayısal örnek → çalışırken ayar değişikliği → sıfır/kısmi/tam fill ve ret → start/stop/kurtarma → beklenen testler → sorular ve kaynaklar. [Strateji şablonu](sablon-strateji.md) kullanılır. Büyüyen strateji kendi alt klasöründe GUI/parametre/akış/test dosyalarına bölünür; indeks güncellenir.

## Kaynaklar ve görseller

Borsa kuralları ve değişebilir teknik bilgiler içerik yazılırken resmi/birincil kaynaklardan araştırılacak; bağlantı, erişim ve yürürlük tarihi tutulacak. Bu indeks turunda internet araştırması yapılmadı. Projenin davranışını kaynak kod ve sürüm belirler. Araştırma, yerel test ve canlı doğrulama ayrı kanıtlardır.

GUI için frontend kodu ve çalıştırılabilirlik incelenir. Gerçek ekran görüntüsü alınabiliyorsa kullanılır. SVG hazırlanırsa **temsili ekran şeması** diye etiketlenir. Görsel üretilemiyorsa kullanıcının görüntü ekleyeceği yer ve çekim tarifi bırakılır. Mimari için bileşen, dağıtım ve sequence şemaları ayrıdır; container ile SDK aynı tür bileşen gibi gösterilmez.

## Önceki kayıtlar

[Eski dersler](arsiv/README.md) tarihsel arşivdir; oradaki eski sıra ve Ders 06 önerisi güncel plan değildir. İçerik kaynak adayıdır, yeni rehberde tamamlandı sayılmaz. Asıl teknik bilgi tabanı mevcut yerinde kalır: [manifest](../manifest.yaml), [sistem haritası](../00-genel/sistem-haritasi.md), [strateji kataloğu](../20-stratejiler/README.md).
