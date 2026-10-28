---
kapsam: 2026-10-22 doküman güncelleme kayıtlarının arşivi
dogrulama: 2026-10-23
durum: taslak
---

# 2026-10-22 değişiklik arşivi

Güncel kayıtlar: [CHANGELOG](../CHANGELOG.md).


## 2026-10-22 — Doğrulamalar (madde 9)

Kaynak: Borsa İstanbul **Pay Piyasası Prosedürü** (02.PRO.01, sürüm 3.34, revizyon 21/09/2026) PDF'i; HftSrvProd `development` `4275ccc`.

- **K-10 kapandı:** Fiyat adımı tablosu prosedür Tablo-7'den eksiksiz yazıldı; 250 TL üstünde 0,25 / 0,50 / 1,00 / 2,50 kademeleri var. Adım baz fiyata değil, emrin fiyat seviyesine bağlı. Tablo 6 Kasım 2023'ten beri değişmemiş.
- **K-11 kapandı:** Marj tek bir ±%10 değil. Yıldız Pazar ±%20, Ana Pazar ±%15; Alt Pazar, YİP ve PÖİP ±%10. `taban.md`'deki "−%10" düzeltildi.
- **K-12 kapandı:**
  - Kapanış seansının alt bölümleri yazıldı.
  - Varant ve sertifikada seans 10:00:10'da başlıyor; 10:02'ye kadar yalnız piyasa yapıcı kotasyonu.
  - Yarım gün takvimi yazıldı.
  - Gün ortası tek fiyat yalnız tek fiyat yöntemli pazarlarda var. YİP ve PÖİP'te günde 5 tek fiyat süreci var; takvimi yazıldı.
  - VİOP saatleri yalnız ikincil kaynaktan (K-193).
- **K-04 netleşti, açık kaldı (kasıtlı?):** `executeOrder` yalnız log basıyor. Kod yorumla birlikte `c819f28`'de (2025-12-01) geldi. Dolan emir `orderMap`'te kalıyor; sabah modunda sonraki Eşleştirme'de bu emre ters emir gidebilir. Kasıt sorusu ekibe soruluyor.
- **Teorik Fiyat düzeltmesi:** "Sabah" sınırı UTC 12:00 değil 13:00, yani İstanbul 16:00 (`hour <= 12`). Saat `packetTs`'ten hesaplanıyor; bu değer 0 gelirse akşamda da sabah moduna düşülüyor (K-192).
- Yeni konular: K-192, K-193.

## 2026-10-22 — Operasyon derinleştirme (madde 8)

Kaynak: Algo-Setup `development` `2a3c5d5` (`main` `2907757` ve `preprod` `346306a` farkları `git show` ile), algo-configs `master` `ab35dde` (`Sabah_Kontrolleri.docx` dahil); servis repoları manifest'teki commit'lerde.

- `bilgi-tabani/40-operasyon/` alt dosyalara bölündü:
  - `kurulum-ve-dagitim.md`
  - `config-referansi.md`: servisler arası indeks; anahtar açıklaması yok
  - `log-imzalari.md`
  - `sabah-kontrolleri.md`: docx güncel koda göre yeniden yazıldı
  - README artık indeks.
- **Yeni:** `bilgi-tabani/10-servisler/algorithmic-trading/config.md` (AlgoProd config referansı). AlgoProd README'deki config tablosu kaldırıldı; tablo yanlıştı (`akd*` okunmuyor, `triggerWorkerCount` ve `volatilityFile` etkisiz).
- **Eski README'de yanlış çıkanlar:**
  - "Hepsi `network_mode: host`": MySQL ve MAAdminUI bridge ağında.
  - S3'e log yalnız HFT'den gidiyor.
  - Kökte `tunning/` yok.
  - `setup_mode` listesi eksikti.
  - Container adları branch'ten ve varyanttan da etkileniyor.
- **Eski log imzalarında yanlış çıkanlar:**
  - development'ta trade-data-app listener'ları bütün pazarların snapshot-end'inden sonra basılıyor (master'da değil).
  - 1001 metni `enterOrder: unknown instrument (no limit entry)`; limit tablosu boşken üretilmiyor.
  - `Client connected …` yalnız master'da.
  - `Restarting with Onload` Onload'un yüklendiğini kanıtlamaz.
  - `zero-handoff` her sabah normal.
  - `N active OUCH user(s)` N=0 normal.
- **Sabah kontrolleri docx'inde eskiyenler:**
  - `Morning Order For Part1/2` satırı kodda yok; aranacak metin `will be fetched at`.
  - Zaman damgası epoch **ns**.
  - Aktif dosya `order_service.txt`.
  - Container adları değişmiş.
- **Kapanan konular:**
  - K-05 ve K-175: admin domain → 6688 ve GUI `/v1`, `/ws` yönlendirmesini müşteri başına `nginx-proxy` yapıyor (Algo-Setup `Configs/<M>/nginx/`); TLS orada sonlanıyor.
  - K-09: sabah kontrolleri aktarıldı.
- **Diğer dosyalarda:**
  - `sistem-haritasi`: algo-configs tanımı ve admin yönlendirmesi.
  - `backend-sozlesmesi`: `/v1`, `/ws`, TLS; nginx-proxy HSTS ekliyor, GUI kararıyla çelişiyor.
  - Linkler yeni dosyalara yönlendirildi.
  - K-15'e Algo-Setup sırları eklendi.
- **Yeni konular K-179 – K-191** (ACIK-KONULAR § Operasyon). Kodla doğrulananlar:
  - K-179: gece güncellemesi bozuk, main de `_development` zip'ini çekiyor.
  - K-180: trade-data-app login şifreyi log'a basıyor.
  - K-181: HFT gRPC portu ↔ trade-data-app `extServices[hft]` uyuşmuyor.
  - K-183: `kill -15 <isim>` SIGTERM göndermiyor.

## 2026-10-22 — mtrader-trade-ui derinleştirme

Kaynak: mtrader-trade-ui `development` `b0474c3` (yeni GUI) ve `main` `6715182` (eski GUI; salt okunur export), trade-data-app `1cca9a8`.

- `bilgi-tabani/10-servisler/mtrader-trade-ui/` alt dosyalara bölündü: `backend-sozlesmesi.md` (iki GUI ortak), `yeni-gui.md`, `eski-gui.md`. README artık giriş, karşılaştırma tablosu ve indeks.
- **README düzeltmeleri:**
  - Eski GUI'de toplu emirler tek "Sabah Emri" ekranı (`OrderForm`, `COLLECTIVE_ORDERS` izni), YİP yok.
  - İki GUI de bazı uçları kullanmıyor (`getSelectedAccountStrategies`, `getStrategyKeys`, `subscribeToArbitrage(s)`).
  - Fon Takibi'nde "paketler tracker yerine" değil, ayrı özet panelinde.
  - Node sürümü `.nvmrc` 22.23.1.
- **Diğer dosyalarda:**
  - `fon-takibi`: UI bölümü düzeltildi.
  - `taban`: eski GUI'nin `maxAskLot` okuduğu işaretlendi.
  - `bilgi-tabani/20-stratejiler/README`: Toplu Emirler görünürlüğü `COLLECTIVE_ORDERS` iznine bağlı.
  - `trade-data-app/veri-akisi`: yeni GUI'nin `CommandType 8`'i eklendi.
- **Repo dışı not:** mtrader-trade-ui `AGENTS.md` "15 için trade-data-app case'i development'ta yok" diyor; `1cca9a8`'de var. Repoya dokunulmadı.
- **Yeni konular K-163 – K-178** (ACIK-KONULAR § mtrader-trade-ui). Öne çıkanlar (eski GUI, prod):
  - K-163: fiyat sabit ×1000, VİOP'ta 10× sapma riski. Kodla doğrulandı.
  - K-164: Taban Lot alanı.
  - K-168: socket'ler yeniden bağlanmıyor.

## 2026-10-22 — ouch-sdk / network-sdk derinleştirme

Kaynak: ouch-sdk `0c3589e`, network-sdk `3c1b42f` (değişmedi). Host tarafı için HftSrvProd, AlgorithmicTrading ve order-service; eski notlar için `meeapps-ai` (salt okunur) okundu.

- `bilgi-tabani/10-servisler/ouch-sdk/README.md` tek dosya olarak yeniden yazıldı: public API, model alan tabloları, callback thread'i, bağlantı yaşam döngüsü, enum farkları, sabah emri API'leri.
- `bilgi-tabani/10-servisler/network-sdk/` alt dosyalara bölündü: `wire-protokolu.md` (çerçeve, FlatBuffers şemaları, enum'lar, pointer ömrü) ve `baglanti-ve-threadler.md` (istemci/sunucu yaşam döngüsü, heartbeat, kopma, thread modeli, kapanış). README artık giriş ve indeks.
- **K-07 kapandı:** Eski `wire-protocol.md`, `connection-management.md`, `bugs-and-quirks.md` maddeleri tek tek kontrol edildi; tablo network-sdk README § Eski bilgi tabanı'nda. Eski bilgilerden yanlış çıkanlar:
  - Decode derin kopya değil.
  - `SO_REUSEADDR` bind'dan önce değil, sonra.
  - Watchdog sorunu kötü bir sentinel değil, kilit altında sonsuz döngü.
  - İstemci `recv()==0`'ı görmüyor.
  - Alan adlarını değiştirmek wire'ı bozmaz.
- **Diğer dosyalarda düzeltilenler:**
  - `hftsrvprod/emir-yasam-dongusu`:
    - Callback thread'i recv değil, ayrı `processCallback` thread'i.
    - Reconnect yok.
    - order-service'e ulaşılamazsa HFT exception atmıyor, login'de asılı kalıyor.
  - `order-service/arayuzler`:
    - `MATCPClient` network-sdk'da.
    - `applicationType` takası.
    - `OrderCanceled` `price`/`matchId` kaybının nedeni.
  - `order-service/kalicilik-ve-config`: `server.address` MARpc'de kullanılmıyor.
  - `algorithmic-trading`: `libouchSDK` MARpc'yi içermiyor.
- **Yeni konular K-149 – K-162** (ACIK-KONULAR § ouch-sdk / network-sdk). Kodla doğrulanan üç tanesi:
  - K-149: AlgoProd login'i `APP_UNKNOWN`.
  - K-150: watchdog sonsuz döngüsü.
  - K-152: kopma tespiti ve yeniden bağlanma yok.

## 2026-10-22 — itch-sdk derinleştirme

Kaynak: itch-sdk `35a3b5c` (değişmedi). Tüketici tarafı için HftSrvProd, AlgorithmicTrading ve trade-data-app; eski bug listesi için `meeapps-ai` (salt okunur) okundu.

- `bilgi-tabani/10-servisler/itch-sdk/` alt dosyalara bölündü: `alim-yolu.md`, `mesajlar-ve-emir-defteri.md`, `abonelik-api.md`. README artık giriş ve indeks.
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

- `bilgi-tabani/10-servisler/maordersdk/` alt dosyalara bölündü: `api-ve-yasam-dongusu.md`, `emir-akisi.md`, `ouch-protokolu.md`, `fix.md`. README artık giriş ve indeks.
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

- `bilgi-tabani/10-servisler/order-service/` alt dosyalara bölündü: `arayuzler.md`, `sdk-ve-oturumlar.md`, `toplu-emirler.md`, `risk.md`, `kalicilik-ve-config.md`. README artık giriş ve indeks.
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
  - `sozluk.md` "Son atış" anlamı ters yazılmıştı; `borsa-kurallari.md` açığa satış kısıtı kısmen uygulanıyor; `bilgi-tabani/30-akislar/README.md` sabah akışı adımları.
  - `network-sdk/README.md`: sabah/açılış isteği yok. `ouch-sdk/README.md`: `addMorningOrder` vb. kodda yok.
  - trade-data-app: `veri-akisi.md` side biçimi ve health servisi ❓'leri cevaplandı; `entegrasyonlar.md` `LimitControlService` order-service tarafından çağrılmıyor, RPC adı `LimitLogin`; `api.md` iki RPC kullanılmıyor; `sema.md` `Orders.type` enum'u.
- **Yeni açık konular:** K-69–K-99; K-43 güncellendi.

## 2026-10-22 — HftSrvProd derinleştirme

Kaynak: HftSrvProd `4275ccc` (değişmedi). Karşı taraf için MAOrderSDK, ouch-sdk ve order-service de okundu.

- `bilgi-tabani/10-servisler/hftsrvprod/` alt dosyalara bölündü: `komutlar-ve-grpc.md`, `strateji-cekirdegi.md`, `emir-yasam-dongusu.md`, `itch-entegrasyonu.md`, `config.md`. README artık giriş ve indeks.
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
- **Restart:** HFT stratejileri durmuş ve bakiye 0 olarak geliyor (`bilgi-tabani/30-akislar/README.md` düzeltildi).
- **Yeni açık konular:** K-44–K-68.

## 2026-10-22 — trade-data-app derinleştirme

Kaynak: trade-data-app `1cca9a8` (değişmedi).

- `bilgi-tabani/10-servisler/trade-data-app/` alt dosyalara bölündü. README artık giriş ve indeks; ayrıntılar: `api.md`, `veri-akisi.md`, `sema.md`, `entegrasyonlar.md`, `config.md`.
- **README'deki düzeltmeler:**
  - WS ve REST'te process içi TLS yok; sertifika anahtarları okunmuyor.
  - TradeVerifier her snapshot'ta değil, bootstrap bildirimiyle yalnızca bir kez tekrar uygulanıyor.
  - Emir geçmişi order-service yeniden bağlanınca sıfırlanıyor.
  - LimitControlService'i order-service çağırmıyor; yalnızca RiskManagerService'i çağırıyor.
  - AlgoProd `FetchOrders` kullanmıyor; onun yerine `FetchAllUniqueKeys` ve `UpdateExtSettings` kullanıyor.
  - `logLevel` üst seviyede etkisiz.
- **Tablo listesi:** `Instrument_Futures` ve `Volatility` eklendi. Şema yönetimi: migration yok; `scripts/sql/` elle çalıştırılıyor. K-08 kapandı (kolonlar koddan `sema.md`'de; tipler ve unique key'ler K-39).
- **`getApplicationFromStrategyType`:** Varant Toplu eksik değil. Gerçek fark iki kopyanın tip 1 ve 12'de ayrışması (`bilgi-tabani/20-stratejiler/README.md` düzeltildi).
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
- `bilgi-tabani/00-genel/sozluk.md` yazıldı (`bos` → `taslak`). Yalnızca mevcut dokümanlardan derlendi, terimler kaynaklarına linkli.
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
- `bilgi-tabani/00-genel/borsa-kurallari.md` yazıldı (`bos` → `taslak`): fiyat adımı, limitler, seanslar, uptick, ret kodları. Her bölümde "kodda" ve "borsada (referans)" ayrımı var. Borsa sitesine bu ortamdan erişilemedi; dış bilgiler arama sonuçlarından derlendi, kesinleşmeyenler ❓.

## 2026-10-22 — İlk sürüm (devam ediyor)

- Repo oluşturuldu; eski `meeapps-ai` bilgi tabanının yerini alır.
- Yapı agent-odaklı kuruldu: `AGENTS.md`, `manifest.yaml`, frontmatter kuralları.
- Tüm repolar referans branch'lerinden çekildi; doğrulama commit'leri `manifest.yaml`'da.
- Warrant Advanced (Varant Toplu) 2026-10-19'da HftSrvProd, order-service, network-sdk ve ouch-sdk development'a merge edildi; dokümanlar merge sonrası haline göre yazılıyor.
