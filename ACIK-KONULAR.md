---
kapsam: Açık sorunlar, şüpheli davranışlar ve doğrulanmamış iddialar — tek satırlık indeks
dogrulama: 2026-10-22
durum: taslak
---

# Açık konular

Her konu **tek satır**. Ayrıntı yalnızca linklenen dosyada yazılır; burada açıklama büyütülmez.
Kapanan konu buradan silinir, kapanışı `CHANGELOG.md`'ye yazılır. Yeni konu sıradaki numarayı alır (numara tekrar kullanılmaz).

Tür: **bug?** olası hata · **doğrula** kodla/borsayla teyit gerekli · **eksik** dokümana aktarılmadı · **iş** yapılacak iş (doküman dışı)

## Sistem

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-01 | bug? | itch-sdk `partId` VİOP'ta 4 partition varsayıyor, HFT 6 dinliyor; 5–6. partition'da çakışma olabilir. ⏸ ertelendi | [itch-sdk](10-servisler/itch-sdk/README.md) § Glimpse ve Rewinder |
| K-02 | bug? | trade-data-app ITCH config'i `Part` 1–4'ü tanıyor, 5–6 Partition1'e düşüyor; 6 partition'lı VİOP'ta (Piramit_Algo) son iki partition gelmiyor, A1/Alnus-Algo zaten 4 tanımlı. ⏸ ertelendi | [config](10-servisler/trade-data-app/config.md) § `itchConfigurations[]` |
| K-03 | bug? | Tavan: yeni stratejide DB'ye 600/1200 varsayılan saat yazılıyor, UI 36000–64800 bekliyor; yanlış değer UI'dan geri gidebilir | [tavan](20-stratejiler/tavan.md) § Wire alanları |
| K-04 | doğrula | Teorik Fiyat `executeOrder` pozisyonu güncellemiyor (kod yorumda); kasıtlı mı? | [teorik-fiyat](20-stratejiler/teorik-fiyat.md) § Bilinen durumlar |
| K-05 | doğrula | Admin paneli domain → :6688 yönlendirmesi (reverse proxy) | [sistem-haritasi](00-genel/sistem-haritasi.md) § Bağlantı tablosu |
| K-06 | doğrula | itch-sdk eski "bilinen buglar" listesinin hangileri düzeltildi | [itch-sdk](10-servisler/itch-sdk/README.md) § Bilinen notlar |
| K-07 | doğrula | network-sdk eski wire protokol / bağlantı notları tek tek kontrol edilmedi | [network-sdk](10-servisler/network-sdk/README.md) § Build |
| K-09 | eksik | `Sabah_Kontrolleri.docx` bilgi tabanına aktarılmadı | [40-operasyon](40-operasyon/README.md) § Sabah kontrolleri |

## trade-data-app

Ayrıntılar alt dosyaların kendi "şüpheli davranışlar" bölümlerinde.

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-16 | bug? | Token'larda kapsam yok: GUI JWT'siyle `DataService.GetOuchUsers` (OUCH/FIX şifreleri) ve admin REST çağrılabiliyor | [api](10-servisler/trade-data-app/api.md) § 2 |
| K-17 | bug? | Şifreler/token'lar düz metin loglanıyor (`DataService.Login`, `GuiLogin`, `AdminService.Login`, `LimitLogin`, reset token) | [api](10-servisler/trade-data-app/api.md) § 11 |
| K-18 | bug? | OTP 4 haneli, deneme sınırı yok; şifre sıfırlama token'ının süresi yok; kullanıcı şifreleri salt'sız MD5 | [api](10-servisler/trade-data-app/api.md) § 2 |
| K-19 | bug? | gRPC'de panic recovery yok; admin liste dilimleme, nil AKD manager, boş AKD/VERDA yanıtı gibi yollarla process düşebilir | [api](10-servisler/trade-data-app/api.md) § 11 |
| K-20 | bug? | Meşgul döngüler bir çekirdeği %100 tutuyor: `processItchData`, `history.workAsync`, `GetIntraDayCustomerLimits` | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 7 |
| K-21 | bug? | `Publish` `InstrumentMtx` altında bloklayıcı; yavaş bir WS istemcisi tüm ITCH hattını durdurabilir | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 7 |
| K-22 | bug? | `guiChan` bildirimi bloklamasız; ilk Login erken gelirse WS ve dış bağlantılar hiç açılmaz | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 1 |
| K-23 | bug? | Dış servise yeniden bağlanırken login hatası olursa yeniden bağlanma kalıcı durur; bilinmeyen `extServices.application` → panic | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 5.1 |
| K-24 | bug? | order-service yeniden bağlanınca bellekteki emir geçmişi (HFT emirleri dahil) sıfırlanıyor | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 5.4 |
| K-25 | bug? | HFT/AlgoProd yeniden bağlanınca iki `FetchCommands` stream'i açılıp her yanıt iki kez yayınlanabiliyor | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 7 |
| K-26 | bug? | WS: seçici `/strategy` unsubscribe çalışmıyor (tip uyuşmazlığı); equilibrium istemcilerine `/itch` mesajı sızabiliyor | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 7 |
| K-27 | bug? | `getApplicationFromStrategyType` iki kopyası ayrışıyor: tip 1 REST→AlgoProd / WS→HFT; tip 12 WS'de yok | [veri-akisi](10-servisler/trade-data-app/veri-akisi.md) § 5.5 |
| K-28 | bug? | TradeVerifier kapalı müşterilerde (Alnus-Algo, Marbas, Piramit_Algo) tavan/taban hiç yazılmıyor; Alnus'ta `downloadEnabled=false` dosya yoksa açılışı düşürür | [config](10-servisler/trade-data-app/config.md) § Müşteri config'leri |
| K-29 | bug? | TradeVerifier yalnızca bootstrap'te bir kez tekrar uygulanıyor; kod yorumu her snapshot'ta der | [entegrasyonlar](10-servisler/trade-data-app/entegrasyonlar.md) § TradeVerifier |
| K-30 | doğrula | VERDA fiyatları sabit ×1000; `DecimalCount` ≠ 3 olan payda ölçek yanlış olur mu | [entegrasyonlar](10-servisler/trade-data-app/entegrasyonlar.md) § TradeVerifier |
| K-31 | bug? | VERDA/AKD/BYF HTTP istemcilerinde timeout yok; VERDA `/files` hatasında boş listeye indeks → panic | [entegrasyonlar](10-servisler/trade-data-app/entegrasyonlar.md) § Açık sorunlar |
| K-32 | bug? | AKD endeks OpenSell kuralında iki dal da +20 ekliyor; `IndiceFuture` nil ise panic | [entegrasyonlar](10-servisler/trade-data-app/entegrasyonlar.md) § Endeks skoru |
| K-33 | bug? | History birleştirme hataları: `time.Add` sonucu atılıyor, `Low` `High` ile karşılaştırılıyor | [entegrasyonlar](10-servisler/trade-data-app/entegrasyonlar.md) § History |
| K-34 | bug? | Açılış iptalleri (BYF, VERDA) exit code 0 ile çıkıyor; on-failure restart tetiklenmez. SES hatası `log.Fatal` | [entegrasyonlar](10-servisler/trade-data-app/entegrasyonlar.md) § Açık sorunlar |
| K-35 | bug? | `setArbitrageBasketPackage` UPDATE'inde argüman eksik (hep hata); `SetArbitrageData` paket hatasını yutuyor | [sema](10-servisler/trade-data-app/sema.md) § Arbitraj ve fon |
| K-36 | bug? | `SetIndiceInstruments` sektör bayrağını `isMainIndice` kolonuna yazıyor | [sema](10-servisler/trade-data-app/sema.md) § Enstrüman ve referans veri |
| K-37 | bug? | `SetPosition` delta ekliyor (idempotent değil); `SetOrders`/`DeleteOrders` transaction'sız | [sema](10-servisler/trade-data-app/sema.md) § Orders / Positions |
| K-38 | bug? | `InsertOrderUser` `applicationUser = 4` sabit; `Instrument.relatedPart` hep 1; `Order.ApplicationType` kaydedilmiyor | [sema](10-servisler/trade-data-app/sema.md) § Tablolar |
| K-39 | doğrula | Kolon tipleri ve unique key'ler koddan görünmüyor (`SHOW CREATE TABLE` gerekli); `Scores` upsert ↔ "son N" okuma | [sema](10-servisler/trade-data-app/sema.md) § Şema yönetimi |
| K-40 | bug? | `StrategyAttributes` tip kontrolü strateji tipine göre filtrelemiyor; bilinmeyen TypeUrl sessizce düşüyor | [sema](10-servisler/trade-data-app/sema.md) § Ayar saklama modeli |
| K-41 | bug? | Config'de etkisiz anahtarlar: `logLevel` üst seviyede (kod `server.logLevel` okur), `maxVolumePath`, `gui.ip`, sertifika yolları, `interestRate` | [config](10-servisler/trade-data-app/config.md) § Bilinen uyumsuzluklar |
| K-42 | bug? | `cors` anahtarı yoksa boş regex her origin'i kabul ediyor | [config](10-servisler/trade-data-app/config.md) § `server` |
| K-43 | doğrula | LimitControlService'in workspace'te istemcisi yok (order-service de çağırmıyor); harici sağlayıcı kim? | [api](10-servisler/trade-data-app/api.md) § 6 |

## HftSrvProd

Ayrıntılar alt dosyaların kendi "şüpheli davranışlar" bölümlerinde.

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-44 | bug? | Çıplak `BaseStrategyCommand` somut tipe `static_pointer_cast` ediliyor (SubscribeToOrderbook, AlgoSetAccountStrategy, SetBalance) — tanımsız davranış | [komutlar-ve-grpc](10-servisler/hftsrvprod/komutlar-ve-grpc.md) § Şüpheli |
| K-45 | bug? | `handleTheoreticalOrder` null kontrolsüz `dynamic_pointer_cast`; `getTickSize` bilinmeyen kitapta 0, çağıranlar kontrol etmiyor | [komutlar-ve-grpc](10-servisler/hftsrvprod/komutlar-ve-grpc.md) § Şüpheli |
| K-46 | bug? | CancelAll/ClosePosition `Orderbook_Id=0` ile bütün hesaplardaki stratejileri durduruyor; replay gate'e bakmıyor | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Cancel-all |
| K-47 | bug? | Manuel EnterOrder SDK hesabın sahibiyken `false` dönse de OK yanıtı veriyor; emir sessizce gitmiyor | [komutlar-ve-grpc](10-servisler/hftsrvprod/komutlar-ve-grpc.md) § 3.2 |
| K-48 | bug? | `userTokenMap` kilitsiz, token süresiz; `globalCommandQueue` sınırsız, birden çok stream'de mesajlar bölünüyor | [komutlar-ve-grpc](10-servisler/hftsrvprod/komutlar-ve-grpc.md) § 5.1 |
| K-49 | doğrula | Restart sonrası stratejiler durmuş ve bakiye 0 geliyor (`Strategy_Start`/bakiye kalıcı değil) — kasıtlı mı? | [strateji-cekirdegi](10-servisler/hftsrvprod/strateji-cekirdegi.md) § Servis restart'ı |
| K-50 | bug? | Strateji silme yolu yok (`removeStrategy`/`stopAllStrategies` çağrılmıyor); `stopAllStrategies` yanlış kilit | [strateji-cekirdegi](10-servisler/hftsrvprod/strateji-cekirdegi.md) § Silme |
| K-51 | bug? | `periodicJobsMap` strateji başına tek job (second rule ezilebilir), raw `OrderAccepted*` taşıyor, worker sleep'siz dönüyor | [strateji-cekirdegi](10-servisler/hftsrvprod/strateji-cekirdegi.md) § Periyodik işler |
| K-52 | bug? | `AlgoWorker::addStrategy` çalışan worker'ın vektörüne kilitsiz ekliyor; `strategyToWorkerMap_` kilitsiz | [strateji-cekirdegi](10-servisler/hftsrvprod/strateji-cekirdegi.md) § Kilitler |
| K-53 | bug? | Tavan/Taban kendi `isRunning`'iyle taban sınıfınkini gölgeliyor; `strategyType` iki sınıfta tanımlı | [strateji-cekirdegi](10-servisler/hftsrvprod/strateji-cekirdegi.md) § Şüpheli |
| K-54 | bug? | Durdurmada `unregisterStrategyForHandle` çağrılmıyor (HFT Classic, Varant, Teorik); Teorik her başlatmada yeni abonelik açıyor; handle'lar 65536'da sessizce düşüyor | [itch-entegrasyonu](10-servisler/hftsrvprod/itch-entegrasyonu.md) § Şüpheli |
| K-55 | bug? | Gün içi handoff gate'i tekrar kapatınca kuyruk birikiyor, açılınca bayat olaylar işleniyor | [strateji-cekirdegi](10-servisler/hftsrvprod/strateji-cekirdegi.md) § Replay gate |
| K-56 | bug? | Handoff öncesi yerel ret (1001–1006) hem stratejiye ret olarak dönüyor hem order-service'e gidiyor; hard cap (1003) fiilen aşılıyor | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Şüpheli |
| K-57 | doğrula | Replay, order-service yolunda işlenmiş fill'leri yeniden getiriyor; strateji `match_id` kontrolü yok | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Çift kayıt koruması |
| K-58 | bug? | OUCH kopunca reconnect callback'i yok; tek kurtarma yeni handoff, gate yeniden kurulmuyor (`replaysRegistered` static) | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Kopma senaryoları |
| K-59 | bug? | `tokens`/`refs` havuzları (100 000) wrap etmiyor; Tavan her girişte `refs` harcıyor | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Şüpheli |
| K-60 | bug? | Kilitsiz paylaşılan durum: `orderTokenToOuchClientUsername`, SDK `account_routes_`, `globalOrderbookStates_` | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Şüpheli |
| K-61 | doğrula | SDK yolu SMP alanlarını göndermiyor (eski `toBISTBytes` gönderiyordu); `DE` hesaplarda `client_cat` House | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Şüpheli |
| K-62 | bug? | Seans durumu haritası `SurekliMuzayede` ile başlıyor; gün içi restart'ta ilk değişime kadar her kitap sürekli işlem sayılıyor | [itch-entegrasyonu](10-servisler/hftsrvprod/itch-entegrasyonu.md) § 6 |
| K-63 | bug? | Tavan `shouldCancelPositionViaVolume`: header hiç güncellenmediği için kontrol hep true, fonksiyonda `return` eksik | [itch-entegrasyonu](10-servisler/hftsrvprod/itch-entegrasyonu.md) § Şüpheli |
| K-64 | bug? | Hazır olma yalnızca Spot snapshot-end'e bağlı; yalnız VİOP kurulumda sonsuz bekler | [itch-entegrasyonu](10-servisler/hftsrvprod/itch-entegrasyonu.md) § 2 |
| K-65 | bug? | `[[markets]]` partition `id`'si SDK partition'ı değil; biri kapatılınca diğerleri kayıyor | [config](10-servisler/hftsrvprod/config.md) § `[[markets]]` |
| K-66 | bug? | Etkisiz config anahtarları (`coreAffinity`, `internalOuch*`, `ouchWorkerCount`, `minHotDwellUpdates`, `[[viop_ouch_users]]`, `license*`); `loadConfiguration` şifreleri stdout'a basıyor | [config](10-servisler/hftsrvprod/config.md) § Lisans ve okunup kullanılmayanlar |
| K-67 | doğrula | HFT `grpcPort` ile trade-data-app `extServices` hft portu A1, Alnus, Alnus-Algo, Global, Marbas'ta uyuşmuyor | [config](10-servisler/hftsrvprod/config.md) § Müşteri config'leri |
| K-68 | doğrula | 7 müşteride `logLevel=debug` (ITCH SDK da debug'a geçiyor); strateji kuyruğu düşürme sayacı loglanmıyor | [config](10-servisler/hftsrvprod/config.md) § Müşteri config'leri |

## order-service

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-69 | bug? | Gün içi limit stream'i koptuktan sonra yeniden açılmıyor; delta'lar kayboluyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-70 | bug? | Rezervasyon hesabı hatalı: replace sonrası 0'a düşüyor, kısmi fill sonrası iptal fazla düşüyor, alış limit fiyatla ayrılıp fill fiyatıyla bırakılıyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-71 | bug? | Hisse yeterlilik kontrolünde uint64 çıkarma sarıyor; rezervasyon bakiyeyi aşınca satış geçiyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-72 | doğrula | Satış bakiye kontrolü yalnız kısıtlı hissede; açığa satışta bakiye kontrolü yok; pazar geneli `ACIGA_SATIS` listede olmayan hisseye uygulanmıyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-73 | doğrula | Replay fill'i bakiyeye yazılmaması yalnız FIX'te; OUCH replay fill'leri risk bakiyesine yeniden uygulanıyor, pozisyonu yalnız 10 sn pencere koruyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-74 | doğrula | Risk fail-open: hesap/limit yoksa, stream kopuksa emir geçiyor; hesap limitleri bir kez çekiliyor, gün içi güncelleme görülmüyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-75 | bug? | `RiskManager`/`RiskInfo` kilitsiz; risk reddi `OrderRejected`'ta token boş, `RejectCode` 0 | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-76 | bug? | Başarısız MARpc login'i `""` token'ını kullanıcıya eşliyor; boş token'lı istekler yetkili sayılıyor | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-77 | bug? | Enter/Replace/Cancel hatalarının çoğu istemciye yanıtsız düşüyor; bağlı OUCH connection yoksa da sessiz kayıp (`onSdkError` 1/9/10) | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-78 | bug? | MARpc'de GTC/AT_CROSSING TIF'i sessizce DAY'e çevriliyor | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-79 | bug? | Her `SubscribeToOrders` callback'leri yeniden bağlıyor (olaylar çoğalıyor); tek paylaşılan `order_queue` kopmuş stream'lerde olay yutuyor | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-80 | bug? | Bellek/ömür: MARpc istek/yanıt nesneleri serbest bırakılmıyor; AccountStrategy GET thread'i dangling referans; `OrderReplaced` token sonlandırıcısı yanlış | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-81 | bug? | Kilitsiz paylaşılan durum: `token_username`, `account_strategies`, `SendOrder` üye vektörleri | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-82 | bug? | Gizli bilgi loglanıyor: MARpc şifresi, DataService ve istemci JWT'leri; `UserDisconnected` açık OUCH şifresini gRPC kuyruğuna da koyuyor | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |
| K-83 | bug? | SIGTERM'de process gRPC `Wait`'te kalıyor; handler async-signal-safe değil | [arayuzler](10-servisler/order-service/arayuzler.md#8-şüpheli) |
| K-84 | bug? | `morning_viop` akışı sonunda pay piyasası dahil bütün morning-only kullanıcılar devrediliyor (pazar filtresi yok) | [sdk-ve-oturumlar](10-servisler/order-service/sdk-ve-oturumlar.md#şüpheli) |
| K-85 | doğrula | `morning` + 30 sn zamanlayıcısı süren sabah akışının kullanıcısını devredebilir; `TryDisconnectUser` kilit tutarken süresiz bekliyor | [sdk-ve-oturumlar](10-servisler/order-service/sdk-ve-oturumlar.md#şüpheli) |
| K-86 | doğrula | Handoff'ta SoupBinTCP LogoutRequest gönderilmiyor (`OuchConnection::logout` ölü kod) | [sdk-ve-oturumlar](10-servisler/order-service/sdk-ve-oturumlar.md#şüpheli) |
| K-87 | bug? | OUCH heartbeat timeout'u yalnız log basıyor; yarı açık TCP'de reconnect yok | [sdk-ve-oturumlar](10-servisler/order-service/sdk-ve-oturumlar.md#şüpheli) |
| K-88 | doğrula | Kullanıcı partition'ı DB'den gelmiyor, hep 1; partition 2 enstrümanda FIX routing çalışmaz | [sdk-ve-oturumlar](10-servisler/order-service/sdk-ve-oturumlar.md#şüpheli) |
| K-89 | bug? | Handoff tetiği `type == "morning"` küçük harf arıyor, akışlar büyük harfe çeviriyor; `MORNING` yazılırsa zamanlayıcı kurulmaz | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |
| K-90 | bug? | Son atış: pointer anahtarlı timeout haritaları `erase` sonrası kayıyor; FIFO 99 thread'inde uykusuz dönüyor | [toplu-emirler](10-servisler/order-service/toplu-emirler.md#10-şüpheli) |
| K-91 | bug? | Son atış kopyaları DB'ye iki kez yazılıyor (`insert_to_db` + `BulkInsertStrategyOrder`) | [toplu-emirler](10-servisler/order-service/toplu-emirler.md#10-şüpheli) |
| K-92 | doğrula | `CancelRepeatedOrders`: kilitsiz okuma, ayraçsız grup anahtarı; `IsCancelAllowed=false` hesapta N kopya iptalsiz kalıyor | [toplu-emirler](10-servisler/order-service/toplu-emirler.md#10-şüpheli) |
| K-93 | doğrula | Gönderilmemiş/reddedilmiş toplu satırlar da pasife alınıyor; kapasite yetmezse alışlar hiç gitmiyor; `SHORT` satırlar seçilmiyor | [toplu-emirler](10-servisler/order-service/toplu-emirler.md#10-şüpheli) |
| K-94 | doğrula | Geç başlatmada (sabah/teorik T−5 sn, açılış/YİP T−30 sn) akış sessizce atlanıyor | [toplu-emirler](10-servisler/order-service/toplu-emirler.md#10-şüpheli) |
| K-95 | doğrula | Müşteri config'lerinde `resetOnLogon: true`, `replayFromSeq` yok; master şemasında yazılmışlar (development'ta varant/YİP açılışı gönderilmez) | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |
| K-96 | bug? | Config okuma tek `try` içinde; eksik anahtar sonraki blokları sessizce varsayılanda bırakıyor (ör. `protocols` boş → emir gitmez) | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |
| K-97 | doğrula | DataService: `Connect()` sonucu kontrol edilmiyor, yeniden login yok (JWT 48 sa), deadline yok, yazma kuyruğu sınırsız; alım limiti 4 MB kalıyor | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |
| K-98 | doğrula | `STRATEGY` satırları tarihsiz yükleniyor; Alnus ve Alnus-Algo'da gece temizleme (`dbNightEvent.sh`) yok | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |
| K-99 | doğrula | CI'da Alnus_Algo `Configs/Alnus`'u kullanıyor; Piramit_Algo matriste yok; Onload derlemesinde `use_onload=false` | [kalicilik-ve-config](10-servisler/order-service/kalicilik-ve-config.md#şüpheli) |

## Borsa kuralları

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-10 | doğrula | Fiyat adımı: 250 TL üstü kademeler ve tablonun yürürlük tarihi | [borsa-kurallari](00-genel/borsa-kurallari.md) § Fiyat adımı |
| K-11 | doğrula | Pay piyasası günlük marj yüzdesi (±%10?) resmi kaynaktan | [borsa-kurallari](00-genel/borsa-kurallari.md) § Günlük fiyat limitleri |
| K-12 | doğrula | Seans saatleri (2016 kararı sonrası), gün ortası tek fiyat, VİOP saatleri, YİP takvimi | [borsa-kurallari](00-genel/borsa-kurallari.md) § Seanslar |

## Yolda / takip

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-13 | iş | AlgoProd MAOrderSDK + handoff `add-order-sdk` branch'inde; merge edilince dokümanlar güncellenecek | [sistem-haritasi](00-genel/sistem-haritasi.md) § Emir yolları |
| K-14 | iş | Uptick geliştirmesi planlanıyor (şu an global bayrak, hep kapalı) | [borsa-kurallari](00-genel/borsa-kurallari.md) § Açığa satış ve uptick |
| K-15 | iş | Kaynak repolarda açık metin şifreler (ClickHouse, lisans, VERDA, Datastore, AKD, Glimpse, DB, JWT `secretKey`, SSH) → Secrets'a taşınmalı. ⏸ sonra ele alınacak | — |
