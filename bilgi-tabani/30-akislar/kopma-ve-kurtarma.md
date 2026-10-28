---
kapsam: Kopma ve restart senaryoları uçtan uca — ITCH gap/Glimpse/partition donması, OUCH kopması (HFT ve order-service), handoff hatası, MARpc kopması, trade-data-app ↔ motor gRPC, GUI WebSocket, servis restart'ları; her biri için tespit, otomatik kurtarma, operatör adımı, veri kaybı ve çift emir riski
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: mtrader-trade-ui
    branch: main
    commit: 6715182
  - repo: order-service
    branch: master
    commit: 298403b
dogrulama: 2026-10-23
durum: taslak
---

# Kopma ve kurtarma

Bu dosya senaryoları uçtan uca bağlar; mekanizmalar ayrıntı dokümanlarındadır ve tekrarlanmaz. Gün içi normal akış (handoff, gate, toplu emirler): [sabah-emri-ve-handoff](sabah-emri-ve-handoff.md). Log satırları: [log-imzalari](../40-operasyon/log-imzalari.md).

Terimler: **SDK yolu** = HFT → MAOrderSDK → BIST; **OS yolu** = HFT/AlgoProd → ouch-sdk (MARpc) → order-service → BIST ([emir-yasam-dongusu](../10-servisler/hftsrvprod/emir-yasam-dongusu.md)).

Uygulama tarafında **kopmada otomatik toplu iptal uygulanmaz**. Kopma veya restart sırasında açık emirlerin iptal olduğu varsayılmaz ([order-service/arayuzler § 3.9](../10-servisler/order-service/arayuzler.md#39-istemci-kopunca), [strateji-cekirdegi § Servis restart'ı](../10-servisler/hftsrvprod/strateji-cekirdegi.md#servis-restartı)). ❓ doğrulanmadı: BIST tarafında OUCH oturumu düşünce emirlerin iptal edilip edilmediği.

## Senaryo tablosu

| Senaryo | Tespit eden | Otomatik kurtarma | Operatör | Kayıp / çift emir riski | K |
|---------|-------------|-------------------|----------|-------------------------|---|
| ITCH tekil paket kaybı | itch-sdk (sequence) | Var: Rewinder | — | Yok (kurtarılırsa) | K-131 |
| Rewinder cevap vermiyor | Yalnız itchsdk log'u | Yok, süresiz deneme | İlgili servisi restart | Partition donar, kitap bayatlar | K-127 |
| Glimpse hatası (açılış) | itch-sdk `start()` | Retry'lar etkisiz | Bağlantıyı düzelt, restart | Servis açılmaz | K-128, K-134 |
| OUCH koptu (HFT, handoff sonrası) | Yalnız SDK içi `is_connected` | Yok | order-service + HFT restart | Yeni emirler OS yoluna düşer, orada sessiz kayıp; açık emir cancel'ları düşer | K-58, K-108 |
| OUCH yarı açık / heartbeat yok | `onHeartbeatTimeout` (HFT kurmaz; OS yalnız log) | Yok | Restart | Emir yazılır, cevap gelmez | K-115, K-87 |
| End of Session (`Z`) | Hiçbiri | Yok | Gün sonunda normal | Gün içinde olursa yukarıdaki gibi | K-113 |
| OUCH koptu (order-service) | `onUserDisconnected` | Var: 1 s shim | — | Arada o kullanıcıya giden emir sessiz kayıp; replay | K-77, K-73 |
| Handoff `connectUser` başarısız | HFT WARN log | Yok | order-service + HFT restart | Kullanıcı gün boyu kimsede yok | — |
| MARpc koptu | Hiçbiri (istemci FIN görmez) | Yok | İstemci (HFT/AlgoProd) restart | İstekler sessizce kuyrukta kalır | K-151, K-152, K-150 |
| trade-data-app ↔ motor gRPC | trade-data-app health watch | Var: 2 s retry | Login hatasında restart | Komut kaybı; çift yayın | K-23, K-25 |
| GUI WS (yeni GUI) | UI | Var: sınırsız, jitter'lı | — | Kuyruktaki komut atılır | K-173 |
| GUI WS (eski GUI) | UI (yalnız orders socket alarmı) | Yok | Bağlantı düğmesi / sayfa yenileme | Paneller donar | K-168, K-171 |
| order-service gün içi restart | — | Kısmen (replay, tetik C) | HFT/AlgoProd da restart | Pozisyon/risk çift yazımı; toplu akış atlanır | K-73, K-94, K-24 |
| HFT gün içi restart (handoff sonrası) | — | Yok (yeni handoff gelmez) | Yeniden devir için order-service de değerlendirilmeli; SetBalance bağlantıyı düzeltmez | Pozisyon kaybı; OUCH yok | K-49 |
| AlgoProd restart | — | Var: DB + `getAllOrders` | Stratejileri başlat | Durum DB'de | K-202 |
| trade-data-app restart | — | Kısmen | order-service login'i gerekir | Arada DB yazımları kaybolur | K-22, K-97 |

## ITCH

### Gap ve Rewinder

1. ItchClient thread'i MoldUDP64 sequence boşluğunu görür, Rewinder'a UDP istek atar, partition `isRecovering`'e girer ([alim-yolu § 5](../10-servisler/itch-sdk/alim-yolu.md#5-gap-ve-rewinder)).
2. Kurtarma sırasında main ring okunmaz; yanıt gelince eksik mesajlar normal parse yolundan, doğal sırayla işlenir. Kısmi yanıt yeni gap tetikler, aralık parça parça kapanır.
3. Host (HFT, AlgoProd, trade-data-app) kurtarmayı görmez; callback gecikmeli gelir. Log: `Gap detected in partition …`, `Sent rewinder request …` ([log-imzalari § HFT Hata imzaları](../40-operasyon/log-imzalari.md#hata-imzaları-2)).

Risk: kesik paket veya 2048 bayttan uzun Rewinder yanıtında mesaj sessizce atlanır (K-131). Birincil/ikincil Rewinder seçimi yarışlıdır (K-129). trade-data-app `rewinderSourceIp`'yi set etmez (K-148).

### Glimpse hatası

- Açılışta Glimpse, her partition için TCP + SoupBinTCP login ister. Login reddinden sonraki retry'lar etkisizdir (K-128); bütün denemeler biterse `itchsdk_start` hata döner ([alim-yolu § 6](../10-servisler/itch-sdk/alim-yolu.md#6-glimpse-ve-canlıya-geçiş)).
- Sonuç servis başına farklıdır:

| Servis | Glimpse başarısız olursa |
|--------|--------------------------|
| HFT | `ItchSdkClient::startItchSdkClient() failed — aborting`, `exit(1)` |
| AlgoProd | 600 s `waitForInitialization` sonunda `Application::startApplication failed`, çıkış kodu 0 ([uygulama-ve-threadler § 2](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md#2-kapanış-sinyal-gün-sonu-hata)) |
| trade-data-app | `main` snapshot kanalında **süresiz** bekler; gRPC/REST açılmaz, order-service ve motorlar DB'ye erişemez ([veri-akisi § 1](../10-servisler/trade-data-app/veri-akisi.md#1-açılış-sırası-cmddataappmaingo-main)) |

- Glimpse snapshot ortasında koparsa yeni deneme yapılır. Login sonrası susan Glimpse sunucusu `glimpseStartTimeoutMs`'e kadar bekletir; `cleanup()` `join`'de takılabilir (K-134).
- Partition sayısı 4'ten azsa veya VİOP'ta P5–P6 varsa snapshot-end hiç gelmez veya eksik gelir (K-01, K-64).

### Partition donması (K-127)

- Rewinder hiç cevap vermezse (adres yanlış, session boş, veri Rewinder penceresi dışında) partition **süresiz** recovery'de kalır. 5 s'de bir istek yeniden atılır, main ring okunmaz, RX bütün canlı paketleri düşürür.
- Deneme sınırı, Glimpse'e dönüş ve host bildirimi yoktur. Diğer partition'lar etkilenmez. Strateji o partition'daki kitaplarda bayat veriyle karar verir veya hiç olay görmez.
- Tespit: yalnız itchsdk log'u (`Rewinder resend … tryCount=`). Multicast hattı tamamen susarsa log bile yoktur ([alim-yolu § 10](../10-servisler/itch-sdk/alim-yolu.md#10-kopma-ve-yeniden-başlama-senaryoları)).
- Kurtarma: yalnız process restart (yeni Glimpse, yeni baseline). Aynı süreçte `itchsdk_stop`/`start` desteklenmez. HFT restart'ının OUCH sonuçları için § Servis restart'ları.

## OUCH — HFT tarafı (MAOrderSDK)

Ayrıntı: [emir-yasam-dongusu § 6](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#6-kopma-senaryoları), [ouch-protokolu § 6 ve § 10](../10-servisler/maordersdk/ouch-protokolu.md#10-kopma-senaryoları).

**Akış (TCP kapandı veya read hatası, handoff sonrası):**
1. Recv döngüsü biter, `connected_ = false`. Combiner `poison_all` yapar, sonra `onUserDisconnected` çağrılır. HFT bu callback'i **kurmaz**; log'da iz kalmaz ([log-imzalari § HFT Hata imzaları](../40-operasyon/log-imzalari.md#hata-imzaları-2)).
2. SDK kendiliğinden yeniden bağlanmaz. HFT'nin `connectUser` çağırdığı tek yer handoff callback'idir.
3. **Yeni emirler:** hesabın başka canlı SDK bağlantısı varsa round-robin onu kullanır. Yoksa `ownsAccount` false → emir OS yoluna düşer → order-service o kullanıcıyı `intended down` tutar → hesabın order-service'te bağlı başka OUCH kullanıcısı yoksa `onSdkError(1)`, ret yok, **sessiz kayıp** ([sdk-ve-oturumlar § 7.5](../10-servisler/order-service/sdk-ve-oturumlar.md#75-handoff-sonrası-o-kullanıcıyla-ilgili-order-service-davranışı)).
4. **Açık emirler:** `ownsOrder` true kalır (harita silinmez, K-100), cancel/replace OS'ye gitmez, `onSdkError(10)` ile düşer. Emirler BIST'te yaşar; fill'leri HFT'ye ulaşmaz.
5. **Kurtarma:** tek yol yeni bir `orderUserDisconnected`. order-service bunu aynı process'te ikinci kez göndermez (`disconnected_users_`). Pratikte: order-service ve HFT restart (§ Servis restart'ları). `replaysRegistered` static olduğundan aynı HFT process'inde ikinci tur gate'i kurmaz (K-58).

**Heartbeat yok / yarı açık TCP (K-115):** SDK `onHeartbeatTimeout` çağırır (logon başına bir kez), soketi kapatmaz. Bağlantı `is_connected` görünür, emirler yazılır, cevap gelmez. HFT callback kurmadığından tespit yoktur; strateji accept beklerken kalır.

**End of Session `Z` (K-113):** `connected_ = false` olur ama `onUserDisconnected` çağrılmaz, combiner zehirlenmez, soket açık kalır. Gün sonunda beklenir. Gün içinde gelirse yukarıdaki 3–5 adımları geçerlidir; ek olarak combiner izlemesi sürer.

**Combiner zehirleme (K-106):** Tek bir kullanıcının kopması combiner'daki **bütün** izlenen emirleri zehirler; bu emirler gün sonuna kadar yalnız OUCH'tan dolar (ITCH hız avantajı kaybolur). Aynı process'te yeniden login olursa (HFT'de pratikte olmaz) replay fill'leri combiner sayaçlarını taşırıp ikinci kez teslim edilebilir ([emir-akisi § 9](../10-servisler/maordersdk/emir-akisi.md#9-combiner-srccombiner)).

**Çift emir riski:** Replay'siz kopmada yok. Kopma sonrası restart + handoff replay'i execute'ları stratejiye tekrar verebilir (K-57).

## OUCH — order-service tarafı (`SdkSessionManager`)

Ayrıntı: [sdk-ve-oturumlar § 9](../10-servisler/order-service/sdk-ve-oturumlar.md#9-oturumlar-yeniden-bağlanma-ve-kopma-senaryoları).

1. Handoff dışı kullanıcının TCP'si koparsa `onUserDisconnected` → `scheduleReconnect`: kullanıcı başına tek thread, 1 s uyku + `connectUser`, sınırsız, backoff yok, 10 denemede bir `MAOrderSDK reconnect still failing …` ([log-imzalari § order-service Hata imzaları](../40-operasyon/log-imzalari.md#hata-imzaları-1)).
2. Arada o kullanıcıya route edilen emir: hesabın başka bağlı kullanıcısı varsa ona gider; yoksa `onSdkError(1)`, uygulamaya ret gitmez (K-77). Toplu akışlar exact-route kullandığından o kullanıcının satırları gitmez ve pasife alınır (K-93). AlgoProd emri `trackedOrders`'ta sonsuza kadar kalır.
3. Login olunca BIST sequence 1'den replay eder. Proses içi dedup haritaları tekrarı eler; pozisyon tekrar yazılmaz.
4. **Muaf:** handoff'ta kapatılan kullanıcı (`markIntendedDown`) shim'e girmez.
5. Heartbeat timeout (K-87) ve End of Session (K-113) shim'i tetiklemez.
6. FIX ayrı: QuickFIX `reconnectInterval` (örnek config 3600 s) sonra dener ([maordersdk/fix](../10-servisler/maordersdk/fix.md)).

## Handoff başarısız

| Durum | Ne olur | Operatör |
|-------|---------|----------|
| HFT `connectUser` 5 denemede de başarısız (eski oturum BIST'te açık, login reddi) | `… FAILED after retries` WARN. order-service kullanıcıyı `intended down` tuttuğu için kimse bağlı değil. Hesabın HFT emirleri OS yoluna düşer ve orada sessizce kaybolur; toplu akışlar da o kullanıcıdan gidemez. Gate 60 s sonra zorla açılır (`replay gate TIMEOUT`) | order-service + HFT restart (§ Servis restart'ları). order-service restart'ı yeni login ve yeniden devir yapar |
| HFT order-service'e bağlı değil | Tetik thread'i `TryDisconnectUser`'da süresiz bekler (`… not connected yet, waiting...`), `disconnect_mutex_`'i tutar (K-85). Kullanıcı order-service'te kalır, toplu akışlar çalışır | HFT'nin MARpc login'ini düzelt (K-151) |
| `UserDisconnected` gönderimi exception | `LOG_CRIT`; kullanıcı devredilmiş sayılır, HFT habersiz → yukarıdaki ilk satırla aynı sonuç | Aynı |
| Toplam 0 gönderildi (sdk-ve-oturumlar Şüpheli 8) | HFT `registerExpectedReplays(total > 0 ? total : 1)` ile 0'ı 1'e çevirir; gate ilk kullanıcının replay'inde açılır | — |
| Replay 60 s'de bitmedi | Gate zorla açılır; bitmemiş kullanıcının replay olayları gate açıkken akmaya devam eder | Log'da `TIMEOUT` varsa replay'i izle |

Handoff'ta order-service LogoutRequest göndermez (K-86); BIST'in oturumu TCP kapanışıyla bırakması HFT'nin ilk login'ini geciktirebilir. ⚠ master order-service'te LogoutRequest gönderilir ([sabah-emri-ve-handoff § 12](sabah-emri-ve-handoff.md#12--masterda-farklı-order-service-298403b)).

## MARpc kopması (HFT/AlgoProd ↔ order-service)

Ayrıntı: [network-sdk/baglanti-ve-threadler § 4](../10-servisler/network-sdk/baglanti-ve-threadler.md#4-kopma-tespiti-ve-yeniden-bağlanma), [ouch-sdk § 5.3](../10-servisler/ouch-sdk/README.md#53-kopma-ve-yeniden-bağlanma).

- **Açılışta order-service'e ulaşılamıyor (K-151):** connect hatası sessiz, `ouchSDK::login` zaman aşımsız bekler. HFT: banner basılır, `login() called` var `returned` yok; handoff hiç gelmez. AlgoProd: gRPC hiç açılmaz, strateji yok.
- **Gün içinde koptu (K-152):** istemci FIN'i fark etmez; host'a bildirim ve yeniden bağlanma yoktur. Sonraki `enterOrder`/`cancelOrder` kuyruğa girer, hiç gönderilmez, hata dönmez.
  - HFT: SDK yolu (handoff edilmiş hesaplar) etkilenmez. OS yolu (handoff öncesi, FIX kanallı GUI emirleri, OUCH'u kopmuş hesaplar) ölüdür. Yeni handoff da gelemez.
  - AlgoProd: bütün emir yolu ölüdür; strateji hata görmez (`trackedOrders` timeout'suz, [emir-yolu § 9](../10-servisler/algorithmic-trading/emir-yolu.md#9-order-service-bağlantısı-koparsa)).
- **Sunucu tarafı:** order-service istemci kopmasını gönderim hatasıyla veya 15 s watchdog'la görür; açık emirler iptal edilmez, kopukken gelen olaylar atılır. Watchdog fd 0'da sonsuz döngüye girip sunucuyu dondurabilir (K-150).
- **Kurtarma:** yalnız istemci process restart'ı. Yeniden bağlanan istemci `getAllOrders` ile günün olaylarını alır (yalnız order-service'in gördükleri; handoff sonrası SDK yolu olayları dahil değil).

## trade-data-app ↔ motor gRPC kopması

Ayrıntı: [veri-akisi § 5.1–5.2](../10-servisler/trade-data-app/veri-akisi.md#51-bağlanma-yeniden-bağlanma-bağlantı-yokken).

1. **Tespit:** trade-data-app gRPC Health `Watch` stream'i hata verince yeniden `Connect` başlar (2 s aralıkla sınırsız `Dial`). HFT varsayılan health servisini `GUIManager::startGrpcServer` içinde etkinleştirir ve `""` için SERVING bildirir (`4275ccc`).
2. **Arada:** komut kuyruğu yok. `POST /v1/setStrategyCommands` `"HFT service is not connected"` veya gRPC hatası döner; komut kaybolur. GUI'nin WS strateji aboneliği motora otomatik yenilenmez.
3. **Yeniden bağlanınca:** login (`StrategyLogin`); login hatası olursa yeniden bağlanma **kalıcı** durur, trade-data-app restart gerekir (K-23).
   - `FetchCommands` iki kez açılabilir → her yanıt GUI'ye iki kez gider (K-25; AlgoProd zombi stream K-204).
   - HFT `FetchOrders`: yeniden bağlanmada ilk mesaj (geçmiş) atlanır, kopukken kaçan emir olayları telafi edilmez.
4. **Motor tarafı:** stratejiler çalışmaya devam eder; emir yolu bu bağlantıya bağlı değildir. HFT `FetchOrders` yazamazsa batch'i bir sonraki stream'e saklar ([emir-yasam-dongusu § 3](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#3-dönüş-olaylar--strateji--gui)).
5. **order-service ↔ trade-data-app** koparsa yeniden bağlanmada bellekteki emir geçmişi sıfırlanır; HFT emirleri `/orders` geçmişinden ve emir defteri işaretlerinden kaybolur (K-24).

## GUI WebSocket kopması

Ayrıntı: [backend-sozlesmesi § 4.3–4.4](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#43-yeni-gui-socket-yönetimi), [veri-akisi § 4.9](../10-servisler/trade-data-app/veri-akisi.md#49-yazma-ve-kopma).

| | Yeni GUI (`development`) | Eski GUI (`main`, prod'da da kullanılıyor) |
|-|--------------------------|--------------------------------------------|
| Yeniden bağlanma | `AuthorizedSocket`: sınırsız, jitter'lı üstel (500 ms × 2ⁿ, tavan 20 s); `online` olayında; 10 s auth timeout | **Yok.** `orders` socket'i kapanınca alarm + kırmızı gösterge, bağlantı düğmesi gerekir; diğer paneller sessizce ölü kalır (K-168) |
| Abonelik | Her socket sınıfı niyeti tutar, `onAuthorized`'da yeniden yollar | Otomatik yeniden oynatma yok |
| İstisna | Pasif emirler paneli 3 denemeden sonra durur (K-173) | `client_id` 0 gelirse auth hiç gönderilmez (K-168) |
| Kopukken gönderilen komut | Kuyruk atılır, yeniden oynatılmaz | — |

- **Geçmiş:** `/orders` subscribe'ı trade-data-app belleğindeki bütün geçmişi yeniden yollar; yeni GUI bunları `isReplay` ile işaretler. Eski GUI'de socket yeniden açılınca çift emir görünebilir (K-171).
- **Sunucu tarafı:** ping/pong ve okuma deadline'ı yok; yarı açık bağlantı tespit edilmez, ölü istemci listede kalır. Yavaş istemci ITCH hattını 10 s'ye kadar bekletebilir (K-21).
- Emir akışı WS'ten bağımsızdır; kopma emir kaybı üretmez, yalnız görünürlük kaybı.

## Servis restart'ları

Container `docker stop/start`: HFT ve AlgoProd SIGTERM almaz, SIGKILL ile ölür (K-183). Hiçbir servis kapanışta emir iptal etmez veya durum yazmaz.

### order-service gün içi restart

Ayrıntı: [sdk-ve-oturumlar § 9](../10-servisler/order-service/sdk-ve-oturumlar.md#9-oturumlar-yeniden-bağlanma-ve-kopma-senaryoları), [kalicilik-ve-config § Gün içi restart senaryosu](../10-servisler/order-service/kalicilik-ve-config.md#gün-içi-restart-senaryosu).

1. DB'den günün `STRATEGY` emirleri `entered_orders`'a (`RetrieveSentOrders`), FIX emirleri SDK'ya seed edilir.
2. Bütün OUCH kullanıcılarına login; BIST replay'i accept/reject/cancel olaylarını uygulamalara **yeniden** yayar (dedup yok, `OrderID = 0`). Pozisyon çift yazımını yalnız 10 s penceresi önler; risk bakiyesi OUCH replay fill'leriyle yeniden uygulanır (K-73, K-37).
3. Saati geçmiş toplu akışlar atlanır (K-94). 09:40 sonrası ise tetik C hemen devri başlatır.
4. Bağlı istemciler: HFT ve AlgoProd'un MARpc bağlantısı ölür ve kendiliğinden geri gelmez (K-152). trade-data-app gRPC'yi yeniden bağlar ama bellekteki emir geçmişini sıfırlar (K-24).
5. Handoff edilmiş kullanıcılar HFT'deyken order-service ikinci kez login olmayı dener; BIST'in davranışı ❓ doğrulanmadı (reddederse shim 1 s'de bir dener; kabul edip eski oturumu düşürürse HFT'nin SDK bağlantısı kopar).

Operatör (koddan çıkarım): HFT ve AlgoProd'u durdur → order-service'i başlat ve hazır olmasını bekle → HFT ve AlgoProd'u başlat. HFT yeniden bağlanınca devir ve replay yeniden yürür; HFT pozisyonları replay'den kurulur. Sabah kontrol dokümanındaki "yalnız arızalı servisi yeniden başlat" prosedürü bu bağımlılığı içermez ([sabah-kontrolleri § Yeniden başlatma](../40-operasyon/sabah-kontrolleri.md#yeniden-başlatma)).

### HFT gün içi restart — strateji ve pozisyon

Ayrıntı: [strateji-cekirdegi § Servis restart'ı](../10-servisler/hftsrvprod/strateji-cekirdegi.md#servis-restartı), [§ DB'den yükleme](../10-servisler/hftsrvprod/strateji-cekirdegi.md#dbden-yükleme-ve-restorepositionstate).

1. Stratejiler DB ayarlarıyla yeniden kurulur, **durmuş** gelir (`Strategy_Started` DB'ye yazılmaz, kasıtlı). Bellekteki bakiye, kâr, FIFO lotlar ve Tavan `isPositionOpen` kaybolur; hepsi 0 başlar (K-49).
2. `getAllOrders` order-service'ten günün OS yolu olaylarını getirir (`SenderApplication` = HFT kullanıcısı). Bunlar stratejiye `addOrder`/`executeOrder` ile işlenir.
3. **Handoff edilmiş kullanıcılar geri gelmez.** order-service `disconnected_users_` nedeniyle `UserDisconnected`'ı tekrar göndermez; yeni HFT process'i hiçbir OUCH kullanıcısına bağlanmaz, replay de olmaz. Sonuç:
   - Handoff sonrası SDK yolundan girilmiş emirlerin accept/fill'leri stratejiye **gelmez**; pozisyon eksik kurulur.
   - Gate 20 s watchdog'la açılır; yeni emirler OS yoluna düşer ve order-service'te o hesabın bağlı kullanıcısı yoksa sessizce kaybolur.
   - Eski process'in BIST oturumu SIGKILL ile düşmüştür; o kullanıcılar kimsede bağlı değildir.
4. **Kurtarma değerlendirmesi (canlıda denenmedi):**
   - (a) order-service + HFT restart (yukarıdaki sıra): yeni devir, replay, pozisyon replay'den kurulur. Execute tekrarı riski (K-57) ve order-service tarafı çift yazım riski (K-73) var.
   - (b) Yalnız HFT restart edildiyse SetBalance ile görünen bakiye düzeltilebilir (`setBalance` mutlak değil, fill gibi **eklenir**), fakat bu işlem OUCH bağlantısını ve açık emir yönetimini geri getirmez; bağlantı kurtarmasının alternatifi değildir.
5. Tavan/Taban bir sonraki `setCommand`'da `restorePositionState` ile `isPositionOpen`'ı kurulan bakiyeden yeniden türetir. Operatör stratejileri GUI'den yeniden başlatır.
6. Handoff'tan **önce** HFT restart'ında kullanıcılar henüz order-service'tedir; yeniden devir bildirimini kaybetme sorunu oluşmaz. Pozisyon geri yükleme, MARpc login ve seans başlangıç durumu riskleri yine geçerlidir; sabit 09:40 sınırı yerine gerçek devir durumu esas alınır (VİOP tetiği daha erken olabilir).
7. Ek riskler: seans durumu haritası ilk değişime kadar her kitabı sürekli işlem sayar (K-62); 20 s watchdog stratejiler başlatılmadan gate'i açar.

### AlgoProd restart

Ayrıntı: [grpc-ve-veri § 7.3](../10-servisler/algorithmic-trading/grpc-ve-veri.md#73-kalıcılık-ve-restart), [uygulama-ve-threadler § 1](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md#1-açılış-sırası).

1. Glimpse → order-service MARpc login → userbook'lar → `getAllOrders` (günün order-service tarafından saklanan olayları; AlgoProd handoff'a girmez, ancak geçmişin eksiksizliği kalıcılık/replay sınırlarına bağlıdır) → gRPC → `readAlgoSettings`.
2. Stratejiler durmuş kurulur. Arbitraj (`getArbitrageData`) ve Fon Takibi (`GetFundData`) durumunu DB'den geri alır; VWAP'ın DB durumu yoktur.
3. gRPC restore'dan önce açılır; o aralıkta gelen komut yarışabilir (K-202). `StrategyFactory` hatası yutulur (K-203).
4. order-service restart'ı AlgoProd'un da restart'ını gerektirir (MARpc, K-152).

### trade-data-app restart

1. ITCH snapshot bitene kadar gRPC kapalıdır. Bu sürede order-service'in `SetOrders`/`SetPosition` çağrıları düşer, yeniden denenmez (K-97); HFT/AlgoProd'un DB çağrıları da düşer (Arbitraj durum kuyruğu, yeni strateji ayarı).
2. Eski JWT'ler geçerlidir (durumsuz HS256, aynı `secretKey`); istemcilerin yeniden login'i gerekmez.
3. **GUI WS ve motor bağlantıları ancak bir `DataService.Login` gelince açılır** (`guiChan`). order-service yeniden login olmaz (K-97). HFT/AlgoProd'un order-service'e MARpc login'i de order-service üzerinden `DataService.Login` çağırır; yani tetik ancak order-service, HFT veya AlgoProd yeniden başlatılınca gelir (K-22; koddan çıkarım, `ouch_api.go` `Login`).
4. Bağlantılar açılınca: order-service `SubscribeToOrders` geçmişi, HFT `FetchOrders` geçmişi (ilk mesaj yayınlanmaz, belleğe alınır), `FetchCommands` (K-25).

## Şüpheli

- **doğrula — HFT-only restart handoff sonrası OUCH'u kalıcı kaybettiriyor.** order-service `disconnected_users_` yüzünden yeniden devretmez; HFT kullanıcıyı başka yoldan öğrenmez (`[[ouch_users]]` müşteri config'lerinde boş). Restart sonrası devredilmiş hesaplar order-service restart edilene kadar OUCH'suzdur ve OS yolundaki emirler sessizce düşer. `strateji-cekirdegi`'nin "❓ gün içi restart'ta order-service'in handoff + replay'i yeniden yapıp yapmadığı" sorusunun koddan cevabı: yapmaz (`MAOSdkManager::DisconnectMorningOrderUsers`).
- **doğrula — Sabah kontrolü restart prosedürü eksik.** [sabah-kontrolleri § Yeniden başlatma](../40-operasyon/sabah-kontrolleri.md#yeniden-başlatma) yalnız arızalı servisi yeniden başlatmayı söylüyor. order-service restart'ı HFT/AlgoProd'u MARpc'siz bırakır (K-152); HFT restart'ı 09:40 sonrası devri kaybettirir. Prosedür bağımlı servisleri de kapsamalı.
- **doğrula — trade-data-app tek başına restart'ta GUI açılmıyor.** `guiChan` tetiği yalnız `DataService.Login`'dir; order-service yeniden login olmaz, motorların login'i order-service üzerinden ancak onların restart'ında gelir. Sonuç: trade-data-app ayakta, REST çalışıyor, WS ve motor bağlantıları hiç açılmıyor.
- **doğrula — order-service gün içi restart'ında ikinci OUCH login'i.** order-service açılışta `onlyMorningOrderUser` ayrımı yapmadan herkese login olur. HFT kullanıcıyı tutarken BIST'in ikinci login'e cevabı bilinmiyor; eski oturumu düşürüyorsa HFT'nin SDK bağlantısı kopar ve HFT bunu fark etmez (callback yok).
