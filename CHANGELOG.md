# CHANGELOG

Her güncelleme oturumu bir kayıt. En yeni en üstte.

## 2026-10-22 — itch-sdk derinleştirme

Kaynak: itch-sdk `35a3b5c` (değişmedi). Tüketici tarafı için HftSrvProd, AlgorithmicTrading ve trade-data-app; eski bug listesi için `meeapps-ai` (salt okunur) okundu.

- `10-servisler/itch-sdk/` alt dosyalara bölündü: `alim-yolu.md`, `mesajlar-ve-emir-defteri.md`, `abonelik-api.md`. README artık giriş ve indeks.
- **README düzeltmeleri:**
  - `header_changed` yalnız fiyat değişiminde tetikleniyor (miktar değil).
  - `isMaxSizeExecution` seviye bazlı: eşik geçilince gruptaki her fill'de 1, yalnız yükselen kenarda bir kez değil.
  - SCHED_FIFO yalnız `ITCH_RT_FIFO` env'iyle, pinleme yalnız core > 0 ile.
  - Birincil/ikincil: `Connect()`'te zaman aşımı yok, multicast hep birincil, ikincil gruba join yok.
  - "Flush'ta emir başına delete" Glimpse'e değil ITCH `FlushOrder` (`Y`) mesajına ait.
  - Config'te worker sayısı alanı yok.
  - `header_snapshot` hareketsiz kitapta hiç gelmiyor.
- **Timestamp modeli netleşti:** ITCH `ts` son `T` saniyesi içindeki ns. Eski bilgi tabanının "gün başından ns" iddiası yanlıştı. `packetTs` kernel SW RX zamanı, `CLOCK_REALTIME` epoch ns; Glimpse ve XLIO'da 0. hftsrvprod/itch-entegrasyonu ve maordersdk/emir-akisi'deki ❓'ler buna göre kapatıldı.
- **K-01 teşhisi düzeltildi:** `partId` yalnız log etiketi, çakışma üretmiyor. Asıl sorun snapshot-end'in pazar başına sabit Partition 1–4 beklemesi (`isMarketGlimpseComplete`). hftsrvprod/config da buna göre güncellendi.
- **Thread adlandırması:** Snapshot-end ve ITCH callback'leri `ItchClient` decode thread'inde çalışıyor, RX thread'inde değil. hftsrvprod/itch-entegrasyonu ve strateji-cekirdegi'nde "receiver thread" ifadeleri düzeltildi.
- **K-06 kapandı:** Eski `bugs-quirks.md`'deki 17 maddenin durumu README § Eski bilinen buglar'da. Düzeltilen: #8 (`T`), #10, #16 (eski bilgi yanlıştı). Kısmen düzelen: #5, #6, #7, #13, #14. Geri kalanı hâlâ var.
- **Yeni konular K-126 – K-148** (ACIK-KONULAR § itch-sdk). Öne çıkanlar:
  - K-126: snapshot-end `market`'i yok sayıyor.
  - K-127: kurtarılamayan gap partition'ı donduruyor.
  - K-146: orderbook başına ömür boyu 32 abonelik sınırı.

## 2026-10-22 — MAOrderSDK derinleştirme

Kaynak: MAOrderSDK `a788782` (değişmedi). Host tarafı için HftSrvProd ve order-service, FIX config'leri için Algo-Setup/algo-configs de okundu.

- `10-servisler/maordersdk/` alt dosyalara bölündü: `api-ve-yasam-dongusu.md`, `emir-akisi.md`, `ouch-protokolu.md`, `fix.md`. README artık giriş ve indeks.
- **README düzeltmeleri:**
  - Bölünen emrin parçaları yalnız host `client_order_id` verirse ana emre bağlanıyor; HFT ve order-service vermediği için iptal yayılmıyor.
  - Yerel ret tablosu tamamlandı (1005, 1006, sentetik 1/4/5/6/15). Hard cap yalnız limit tablosu doluysa ve `price > 0` ise.
  - `onWireExecuted` FIX'te QuickFIX thread'inden. `setCallbacks` Onload bootstrap'tan önce olmalı.
  - Failover yalnız TCP seviyesinde. `onReplayCompleted` logon başına en fazla bir kez. Mlx varyantı. Data dictionary XML'leri çalışma anında okunuyor.
- **Diğer dosyalarda düzeltmeler (kodla doğrulandı):**
  - `hftsrvprod/emir-yasam-dongusu.md`: replace sonrası callback'ler HFT id'siyle gelir, wire token farklıdır; hard cap koşulu; `onSdkError` kodları (11 `setFavoriteOuch`, 5, 15); End of Session istisnası; replay sequence 1 ve `onReplayCompleted` thread'i ❓'leri kapandı.
  - `order-service/sdk-ve-oturumlar.md`: route'suz split reddi boş id'yle gelir ve atılır; End of Session'da shim tetiklenmez; FIX ilk bağlanma ≤30 s.
  - `order-service/kalicilik-ve-config.md`: FIX `fileStorePath`/`fileLogPath` dizindir; OUCH sequence 1 ❓'si kapandı.
- **Yeni açık konular:** K-100–K-125.

## 2026-10-22 — order-service derinleştirme

Kaynak: order-service `b86c0cf` (değişmedi). Karşı taraf için MAOrderSDK, ouch-sdk, network-sdk, trade-data-app ve Algo-Setup müşteri config'leri de okundu.

- `10-servisler/order-service/` alt dosyalara bölündü: `arayuzler.md`, `sdk-ve-oturumlar.md`, `toplu-emirler.md`, `risk.md`, `kalicilik-ve-config.md`. README artık giriş ve indeks.
- **README düzeltmeleri:**
  - `-110023` yeniden gönderimi yalnız son atışta, `repeatLastShot: true` iken, en çok 900 ms. Fazla kopya iptali thread'ler bittikten 2 sn sonra.
  - `OffHours` bayrağı yalnız `SendOrderAsync` yolunda; toplu/açılış gönderimleri normal seans bayrağıyla gidiyor.
  - Handoff her OUCH `repeatableOrders` satırının ve FIX akışının sonunda tetikleniyor, pazar filtresi yok; +30 sn zamanlayıcısı yalnız `type: morning` için.
  - Kullanıcı partition'ı DB'den gelmiyor, hep 1.
  - Risk: yalnız gün içi limitler stream; satış bakiye kontrolü yalnız kısıtlı hissede; replay fill koruması yalnız FIX.
  - Kalıcılık: olaylar DB'ye yazılmıyor (yalnız enter/replace `STRATEGY` satırı ve toplu akışlar); `RetrieveSentOrders` tarihsiz yüklüyor.
  - FIX replay: müşteri config'lerinin hepsinde `resetOnLogon: true`, replay yok.
- **Diğer dosyalarda düzeltmeler (kodla doğrulandı):**
  - `sistem-haritasi.md`: handoff'ta logout gönderilmiyor, yalnız soket kapanıyor; tetik koşulları.
  - `hftsrvprod/emir-yasam-dongusu.md`: OS yolunda HFT token'ı wire'a çıkmıyor; iki ❓ cevaplandı (cancel → `onSdkError(10)`, bağlantısız hesap → `onSdkError(1)`, sessiz kayıp).
  - `sozluk.md` "Son atış" anlamı ters yazılmıştı; `borsa-kurallari.md` açığa satış kısıtı kısmen uygulanıyor; `30-akislar/README.md` sabah akışı adımları.
  - `network-sdk/README.md`: sabah/açılış isteği yok. `ouch-sdk/README.md`: `addMorningOrder` vb. kodda yok.
  - trade-data-app: `veri-akisi.md` side biçimi ve health servisi ❓'leri cevaplandı; `entegrasyonlar.md` `LimitControlService` order-service tarafından çağrılmıyor, RPC adı `LimitLogin`; `api.md` iki RPC kullanılmıyor; `sema.md` `Orders.type` enum'u.
- **Yeni açık konular:** K-69–K-99; K-43 güncellendi.

## 2026-10-22 — HftSrvProd derinleştirme

Kaynak: HftSrvProd `4275ccc` (değişmedi). Karşı taraf için MAOrderSDK, ouch-sdk ve order-service de okundu.

- `10-servisler/hftsrvprod/` alt dosyalara bölündü: `komutlar-ve-grpc.md`, `strateji-cekirdegi.md`, `emir-yasam-dongusu.md`, `itch-entegrasyonu.md`, `config.md`. README artık giriş ve indeks.
- **README düzeltmeleri:**
  - Kuyruk dolunca eski değil, **yeni** olay düşüyor.
  - `FetchAllUniqueKeys` ve `UpdateExtSettings` HFT'de UNIMPLEMENTED. `SubscribeToCommands` abonelik tutmuyor, yalnız anlık durum yolluyor.
  - Yerel `onRejected` çağıran thread'de senkron geliyor.
  - `ownsAccount` canlı bağlantı istiyor; OUCH koparsa emirler order-service'e düşüyor.
  - Replay gate'te 20 sn watchdog'a ek olarak 60 sn zorunlu açılma var; sonraki handoff gate'i yeniden kapatıyor.
  - HFT Classic second rule emri periyodik thread'den gönderiliyor.
  - `hotWorkerCount` bir bayrak.
  - `sdkLockMemory` ve `mainCpuCores` müşteri config'lerinde açık olabiliyor.
- **`[[ouch_users]]`:** `isActive=true` girişler açılışta SDK'ya kaydediliyor; handoff'ta handoff verisi yerine config verisi kullanılıyor. Müşteri config'lerinde giriş yok. Kodla doğrulandı; sistem haritası düzeltildi.
- **`StrType`:** `StrategyService`'in iki mesajı ayrı strateji numaralandırması kullanıyor (sözlük ve strateji kataloğu düzeltildi).
- **Varant Toplu olayları:** HFT'de istemci başına yönlendirme yok (`varant-toplu.md` düzeltildi).
- **Restart:** HFT stratejileri durmuş ve bakiye 0 olarak geliyor (`30-akislar/README.md` düzeltildi).
- **Yeni açık konular:** K-44–K-68.

## 2026-10-22 — trade-data-app derinleştirme

Kaynak: trade-data-app `1cca9a8` (değişmedi).

- `10-servisler/trade-data-app/` alt dosyalara bölündü. README artık giriş ve indeks; ayrıntılar: `api.md`, `veri-akisi.md`, `sema.md`, `entegrasyonlar.md`, `config.md`.
- **README'deki düzeltmeler:**
  - WS ve REST'te process içi TLS yok; sertifika anahtarları okunmuyor.
  - TradeVerifier her snapshot'ta değil, bootstrap bildirimiyle yalnızca bir kez tekrar uygulanıyor.
  - Emir geçmişi order-service yeniden bağlanınca sıfırlanıyor.
  - LimitControlService'i order-service çağırmıyor; yalnızca RiskManagerService'i çağırıyor.
  - AlgoProd `FetchOrders` kullanmıyor; onun yerine `FetchAllUniqueKeys` ve `UpdateExtSettings` kullanıyor.
  - `logLevel` üst seviyede etkisiz.
- **Tablo listesi:** `Instrument_Futures` ve `Volatility` eklendi. Şema yönetimi: migration yok; `scripts/sql/` elle çalıştırılıyor. K-08 kapandı (kolonlar koddan `sema.md`'de; tipler ve unique key'ler K-39).
- **`getApplicationFromStrategyType`:** Varant Toplu eksik değil. Gerçek fark iki kopyanın tip 1 ve 12'de ayrışması (`20-stratejiler/README.md` düzeltildi).
- **`fon-takibi.md`:** BYF sepeti DB'ye değil belleğe yazılıyor.
- **K-02:** ITCH config'i `Part` 5–6'yı Partition1'e düşürüyor.
- **Yeni açık konular:** K-16–K-43.

## 2026-10-22 — ❓ temizliği, sözlük, manifest

Commit'ler değişmedi; hepsi manifest'teki doğrulama commit'lerine karşı.

- **Kullanılmayan alanlar** (parse edilip geri yollanıyor, karar vermiyor):
  - HFT Classic `Start_Time`/`Stop_Time`
  - Fon Takibi `Byf_Package_Limit`
  - VWAP `Trade_Pay_Limit`/`Trade_Vade*_Limit`
  - Arbitraj `First/Second/Third_Future`
- **Arbitraj `Optional_Underlying`:** Açıkken komuttaki `Underlying_Multiplier` kullanılıyor; iki vadeli tiplerde çarpan 1.
- **Sepet arbitraj wire tipi:** `Arbitrage` (6), doğrulandı.
- **Tavan saat alanları:**
  - `End_Time` okunuyor, `Stop_Time` olarak geri yollanıyor.
  - `getDefaultSettings`'in 600/1200 varsayılanı UI'dan geri gidebilir; ❓ test edilmedi.
- **order-service:**
  - `eveningSessionStart` bir gönderim akışı değil: o saatten sonraki emirlere `OffHours` bayrağı koyuyor.
  - EVENING emirlerini teorik akışı gönderiyor.
  - Lisans kontrolü kapalı.
  - YİP örnek seans saatleri eklendi.
- **Varant Toplu:** Eski GUI'de yok. Önceki "`VarantTopluTrackerForm`" iddiası yanlıştı.
- **VWAP Overall:** Yeni GUI'de karşılığı yok.
- **itch-sdk:**
  - Hat seçimi açılışta ve process genelinde yapılıyor; Glimpse bağlantısı başarısız olursa ikincile tek yönlü geçiliyor.
  - `partId` VİOP için 5–8 aralığını varsayıyor. HFT'nin 6 VİOP partition'ıyla olası çakışma, ertelenen VİOP konusuna eklendi.
- `00-genel/sozluk.md` yazıldı (`bos` → `taslak`). Yalnızca mevcut dokümanlardan derlendi, terimler kaynaklarına linkli.
- `manifest.yaml`: 15 reponun `durum: bos` alanı `taslak` yapıldı (dokümanların frontmatter'ıyla uyumlu).

## 2026-10-22 — Çelişki doğrulaması ve borsa kuralları

Kaynak repoların HEAD'leri manifest'teki doğrulama commit'leriyle aynı (değişiklik yok). Düzeltmeler bu commit'lere karşı kodla doğrulandı.

- **Toplu emir yolu:** trade-data-app → order-service RPC'si `SendOrder`, `SetOrders` değil. Go sarmalayıcının adı yanıltıcı. order-service emirleri `BulkInsert*Order` ile DB'ye yazar (sistem haritası, akışlar, order-service, trade-data-app).
- **Sabah emri fazla kopya iptali** (`CancelRepeatedOrders`) order-service'e yazıldı.
- **UI WebSocket'leri:** 6 merkezi socket ↔ feed eşlemesi; `passive-orders` yalnız pasif emir paneli.
- **performance-sdk:** AlgoProd'un metrikleri düzeltildi (bağlantı metriği yok).
- **PTRM:** AlgoProd `-850064`'ü tanımıyor (VWAP, Arbitraj). Arbitraj'ın PTRM'de durması ve `-420131` eklendi.
- **Uptick:** HFT'de enstrüman bazlı değil, global config bayrağı (`uptickRule`); `uptickEnabled` kullanılmıyor.
- **Tavan:** `Profit_Percentage` kullanılmıyor.
- **trade-data-app VİOP partition'ları:** Müşteri config'lerinde sayılar farklı. Piramit_Algo 6, A1 ve Alnus-Algo 4, diğerlerinde VİOP yok; HFT config'leri hepsinde 6.
- **Algo-Setup kurulum matrisi branch'e göre değişiyor:** Kanjo yalnızca `main`'de (prod). `Seker` (development) ve `Oyak` (main) config klasörleri hiçbir matriste yok; ikisi de eski müşteri (kullanıcı beyanı).
- **Piramit_Algo eski GUI'de:** Son başarılı deploy 2026-04-24'te `preprod`'dan (GitHub Actions run geçmişinden çıkarım).
- **Uptick'in çalışma anında açılma yolu yok:** Bütün müşteri config'lerinde `uptickRule = false`. İlan günlerinde genelde strateji çalıştırılmıyor; uptick geliştirmesi planlanıyor (kullanıcı beyanı).
- **A1 / Alnus-Algo VİOP 4 partition:** İncelemesi ertelendi.
- **Kullanıcı beyanları:** Sepet arbitraj henüz kullanılmıyor; Warrant-Selector Varant Toplu'ya yüklenen CSV'yi üretiyor; Global ve Marbas eski GUI'de.
- `00-genel/borsa-kurallari.md` yazıldı (`bos` → `taslak`): fiyat adımı, limitler, seanslar, uptick, ret kodları. Her bölümde "kodda" ve "borsada (referans)" ayrımı var. Borsa sitesine bu ortamdan erişilemedi; dış bilgiler arama sonuçlarından derlendi, kesinleşmeyenler ❓.

## 2026-10-22 — İlk sürüm (devam ediyor)

- Repo oluşturuldu; eski `meeapps-ai` bilgi tabanının yerini alır.
- Yapı agent-odaklı kuruldu: `AGENTS.md`, `manifest.yaml`, frontmatter kuralları.
- Tüm repolar referans branch'lerinden çekildi; doğrulama commit'leri `manifest.yaml`'da.
- Warrant Advanced (Varant Toplu) 2026-10-19'da HftSrvProd, order-service, network-sdk ve ouch-sdk development'a merge edildi; dokümanlar merge sonrası haline göre yazılıyor.
