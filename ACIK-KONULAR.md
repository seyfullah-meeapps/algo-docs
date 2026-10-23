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
| K-01 | bug? | itch-sdk snapshot-end pazar başına sabit Partition 1–4 bekliyor (`isMarketGlimpseComplete`); 6 partition'lı VİOP'ta P5–P6 tamamlanmaya dahil değil, 4'ten azında pazar hiç canlıya geçmez. `partId` yalnız log etiketi. ⏸ ertelendi | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#8-partition-varsayımları-ve-partid-k-01--ertelendi) |
| K-02 | bug? | trade-data-app ITCH config'i `Part` 1–4'ü tanıyor, 5–6 Partition1'e düşüyor; 6 partition'lı VİOP'ta (Piramit_Algo) son iki partition gelmiyor, A1/Alnus-Algo zaten 4 tanımlı. ⏸ ertelendi | [config](10-servisler/trade-data-app/config.md) § `itchConfigurations[]` |
| K-03 | bug? | Tavan: yeni stratejide DB'ye 600/1200 varsayılan saat yazılıyor, UI 36000–64800 bekliyor; yanlış değer UI'dan geri gidebilir | [tavan](20-stratejiler/tavan.md) § Wire alanları |
| K-04 | kasıtlı? | Teorik Fiyat `executeOrder` yalnız log basıyor: pozisyon güncellenmiyor, dolan emir `orderMap`'ten silinmiyor; sabah modunda sonraki Eşleştirme'de dolmuş emre ters emir gidebilir (kod `c819f28`'de yorumla geldi). Ekibe sorulmalı | [teorik-fiyat](20-stratejiler/teorik-fiyat.md#bilinen-durumlar) |

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
| K-56 | bug? | Handoff öncesi yerel ret (1001–1006) sonrası fallback deneniyor; ikinci yol kendi limitlerini ayrıca kontrol ediyor | [emir-yasam-dongusu](10-servisler/hftsrvprod/emir-yasam-dongusu.md) § Şüpheli |
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
| K-192 | bug? | Teorik Fiyat sabah/akşam ayrımı `packetTs`'ten; Glimpse/XLIO'da 0 → akşam müzayedesinde iptal yerine ters emir | [teorik-fiyat](20-stratejiler/teorik-fiyat.md#akış) |

## order-service

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-69 | bug? | Gün içi limit stream'i koptuktan sonra yeniden açılmıyor; delta'lar kayboluyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-70 | bug? | Rezervasyon hesabı hatalı: replace sonrası 0'a düşüyor, kısmi fill sonrası iptal fazla düşüyor, alış limit fiyatla ayrılıp fill fiyatıyla bırakılıyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-71 | bug? | Hisse yeterlilik kontrolünde uint64 çıkarma sarıyor; rezervasyon bakiyeyi aşınca satış geçiyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-72 | doğrula | Satış bakiye kontrolü yalnız kısıtlı hissede; açığa satışta bakiye kontrolü yok; pazar geneli `ACIGA_SATIS` listede olmayan hisseye uygulanmıyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-73 | doğrula | Replay fill'i bakiyeye yazılmaması yalnız FIX'te; OUCH replay fill'leri risk bakiyesine yeniden uygulanıyor, pozisyonu yalnız 10 sn pencere koruyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-74 | doğrula | Risk fail-open: hesap/limit yoksa emir geçiyor; stream kopunca eski limitlerle kontrol sürüyor, hesap limitleri bir kez çekiliyor | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-75 | bug? | `RiskManager`/`RiskInfo` kilitsiz; risk reddi `OrderRejected`'ta token boş, `RejectCode` 0 | [risk](10-servisler/order-service/risk.md#13-şüpheli) |
| K-229 | bug? | price=0 FIX market alışta RiskManager tahmini TL tutarı hesaplamıyor; SDK hard cap de fiyat sıfırken atlanıyor (K-104 ile ilişkili) | [risk](10-servisler/order-service/risk.md#11-hard-cap-ve-maordersdk-yerel-kontrolleri) |
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

## MAOrderSDK

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-100 | bug? | İç haritalar (`orders_by_token`, `wire_by_client`, `split_parents_`) biten emirde silinmiyor; bellek büyüyor, `ownsOrder` bitmiş emirde true | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-101 | bug? | `cancel_one`/`replace_one` `onSdkError` 9/10/4'ü `maps_mutex` altında çağırıyor; host SDK'ya geri girerse deadlock | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-102 | bug? | Cancel/replace soket yazım hatası sessiz: ne `onSdkError` ne ret, yalnız `false`; HFT yedek yola da gitmiyor | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-103 | bug? | Split'te hesabın route'u yoksa ret boş `client_order_id` ile geliyor, token callback'i yok; order-service olayı atıyor | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-104 | bug? | Limit tablosu boşsa `order_hard_cap_try` hiç uygulanmıyor; market emri ve negatif fiyat 1001–1003 ve bölmeyi atlıyor (brüt takasa market emri gidebilir) | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-105 | doğrula | Split replace kısmen dolmuş child'a girişteki miktarı yazıyor; `max_order_value == 0` enstrümanda her emir 1004 | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-106 | doğrula | Combiner: `poison_all` tek bağlantı kopunca bütün kullanıcıları zehirliyor; aynı süreçte reconnect replay'i fill'leri tekrar teslim ediyor; replace'te ITCH `order_id` değişmezse çift fill | [emir-akisi](10-servisler/maordersdk/emir-akisi.md#şüpheli) |
| K-107 | bug? | `connectUser(OuchUser)` `protocol` alanını yok sayıyor; FIX kullanıcısı için OUCH bağlantısı kuruluyor | [api-ve-yasam-dongusu](10-servisler/maordersdk/api-ve-yasam-dongusu.md#şüpheli) |
| K-108 | bug? | `ownsAccount` ile routing tutarsız: OUCH kopuk + FIX logon'lu ya da exact-route kullanıcısı kopukken emir sessizce düşüyor | [api-ve-yasam-dongusu](10-servisler/maordersdk/api-ve-yasam-dongusu.md#şüpheli) |
| K-109 | bug? | `onSdkError(6)` iki anlamlı (`mlockall` ve wire send); Onload hata kodu 7 `setCallbacks`'ten önce kayboluyor | [api-ve-yasam-dongusu](10-servisler/maordersdk/api-ve-yasam-dongusu.md#şüpheli) |
| K-110 | doğrula | Host callback'inden fırlayan istisna recv thread'inde `std::terminate`; aynı kullanıcıya eşzamanlı `connectUser` `recv_thread_` yeniden atamasında terminate riski | [api-ve-yasam-dongusu](10-servisler/maordersdk/api-ve-yasam-dongusu.md#şüpheli) |
| K-111 | doğrula | OUCH `onUserConnected` recv thread başladıktan sonra çağıran thread'de; replay olaylarıyla sıra garantisi yok | [api-ve-yasam-dongusu](10-servisler/maordersdk/api-ve-yasam-dongusu.md#şüpheli) |
| K-112 | kasıtlı? | `setOuchConfig` geçersiz `market`'te `std::exit(1)`; `OuchUser.market` başlatılmamış | [api-ve-yasam-dongusu](10-servisler/maordersdk/api-ve-yasam-dongusu.md#şüpheli) |
| K-113 | bug? | End of Session'da `onUserDisconnected` yok; combiner zehirlenmez, soket açık kalır, order-service reconnect shim'i tetiklenmez | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-114 | bug? | Sistemin değiştirdiği emirde Replacement Token boşluk; `""` ile adopt edilip host'a boş id gidiyor; Order State (sahiplik kaybı) okunmuyor | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-115 | doğrula | Heartbeat timeout yalnız bildirim; soket kapanmıyor, yarı açık TCP'de bağlı görünüyor | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-116 | doğrula | Kesmeler: fiyat int64→int32, orderbook uint64→uint32 kontrolsüz; 12 baytlık Match ID'nin üst 4 baytı atılıyor (dedup/combiner riski) | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-117 | doğrula | GTC, GTD, AtCrossing TIF'leri sessizce Day gidiyor (OUCH ve MARpc) | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-118 | doğrula | Kısmi yazım + 1 s timeout'ta yarım OUCH çerçevesi kalıyor; 256 bayttan uzun paket bağlantıyı düşürüyor; Replace 125 bayt (spec 122) | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-119 | doğrula | Login reddinde ikincil endpoint'e geçilmiyor; failover yalnız TCP seviyesinde | [ouch-protokolu](10-servisler/maordersdk/ouch-protokolu.md#şüpheli) |
| K-120 | bug? | FIX oturum Reject (35=3) ve BusinessMessageReject (35=j) host'a callback üretmiyor; emir askıda kalır | [fix](10-servisler/maordersdk/fix.md#10-şüpheli) |
| K-121 | bug? | FIX miktar replace'inden sonra `order.quantity` kalan miktara dönüyor; sonraki replace/cancel kısmi dolmuş emirde yanlış `38` gönderiyor | [fix](10-servisler/maordersdk/fix.md#10-şüpheli) |
| K-122 | doğrula | FIX fiyat böleni sabit (pay 1000, VİOP 100), `decimal_count` kullanılmıyor; bölme/hard cap `10^decimal_count` ile — ölçekler ayrışabilir | [fix](10-servisler/maordersdk/fix.md#10-şüpheli) |
| K-123 | doğrula | `armFixPasswordChange` sonrası herhangi bir Logout şifre değişimi başarısız sayılıp oturum devre dışı kalıyor | [fix](10-servisler/maordersdk/fix.md#10-şüpheli) |
| K-124 | doğrula | FIX: ExecType `H`/`G` (trade cancel/correct) sessizce düşüyor; ClOrdID uzunluk kontrolü yok; yabancı ClOrdID'ler sahipleniliyor | [fix](10-servisler/maordersdk/fix.md#10-şüpheli) |
| K-125 | doğrula | QuickFIX oturum penceresi sabit kodlu 05:00–03:00 UTC (06:00–08:00 TR oturum dışı) | [fix](10-servisler/maordersdk/fix.md#10-şüpheli) |

## itch-sdk

Ayrıntılar alt dosyaların kendi "Şüpheli" bölümlerinde. Sistem genelindeki K-01 (partition varsayımı) yukarıda.

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-126 | bug | snapshot-end aboneliği `market`'i saklamıyor; her pazarın snapshot'ı bütün abonelere gidiyor (AlgoProd çift teslim, trade-data-app çift replay) | [abonelik-api](10-servisler/itch-sdk/abonelik-api.md#şüpheli) (1) |
| K-127 | bug? | Kurtarılamayan gap partition'ı kalıcı donduruyor; deneme sınırı, Glimpse'e dönüş, host bildirimi yok | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-128 | bug? | Glimpse login hatasından sonra retry'lar boşa gidiyor (`connected` true kalıyor, soket sızıyor); `Connect` ikincilde hata verse de `true` dönüyor | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-129 | bug? | Birincil/ikincil bayrağı atomic değil; Rewinder adresi client init sırasına göre seçiliyor; ikincil multicast'e join ve A/B arbitraj yok | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#4-birincilikincil-seçimi) |
| K-130 | bug? | Ortak `glimpseMutex`: Spot snapshot callback'leri sürerken VİOP partition'ı ring'ini boşaltamıyor | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-131 | doğrula | Kesik paket / Rewinder yanıtında `expected` önceden ilerliyor (sessiz mesaj kaybı); MoldUDP64 session okunmuyor, sequence 1'e dönerse akış yok sayılır | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-132 | doğrula | Ring boyutu 2'nin kuvveti mi kontrol edilmiyor; `receiverCpuCores[4]` 5.+ receiver'a çekirdek vermiyor; ZC/XLIO yolunda 2048 bayt üstü paket taşması | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-133 | doğrula | Canlı tamponun serbest bırakılması HFT'nin sonradan (async) kurduğu abonelikleri kapsamıyor | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-134 | doğrula | Glimpse `recv`'i `close()` ile açılmayabilir, `cleanup()` `join`'de takılabilir; Onload preload kontrolü yalnız "boş mu" | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-135 | doğrula | Rewinder sayaçlarında çift sayım (eski #3); `setArguments` HFT'de çağrılmıyor, Onload/XLIO yeniden başlatma (eski #4) | [alim-yolu](10-servisler/itch-sdk/alim-yolu.md#şüpheli) |
| K-136 | bug? | `header_changed` yalnız fiyat değişince tetikleniyor, miktar değişimini kaçırıyor (eski #1) | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#7-header-ve-kademe-hesabı) |
| K-137 | bug? | `F` (AddOrderWithMPID) `len<45` şartıyla sessizce düşebilir; `C`'de fiyat hâlâ kitap fiyatı | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#25-f-addorderwithmpid) |
| K-138 | bug? | Header/level/threshold callback `timestamp`'i kaynağa göre ITCH saniye içi ns / `packetTs` / 0; equilibrium'daki `packetTs` aslında ITCH ns; ts her saniye sarıyor, ts ile gruplama farklı saniyeleri birleştirebilir | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#3-timestamp-modeli) |
| K-139 | bug? | seed/reseed/`update_level_subscription` host thread'inden kitabı kilitsiz okuyor/yazıyor (vektör `resize` yarışı) | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#11-thread-ve-kilit-modeli) |
| K-140 | bug? | Canlıda tekrar gelen `R` (OrderBookDirectory) kitabı ve callback'lerini siliyor; dışarıdaki pointer'lar sallanıyor | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#şüpheli) |
| K-141 | bug? | Flush sonrası atomik header aynası bayat kalıyor | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#şüpheli) |
| K-142 | doğrula | Tick tablosunda `prxTo=0` = sonsuz kuralı kodda yok; satır bulunamazsa 1 dönüyor | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#4-fiyat-ve-miktar-ölçeği) |
| K-143 | eksik | Orderbook state eşlemesi eksik (`P_SALTKOTASYON`, `P_SUREKLI_ISLEM_HFL` → `Other`); `V`/`S`/`M` mesajları parse edilmiyor | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#8-orderbook-state) |
| K-144 | bug? | `OrderExecutedWithPrice` DTO'su `comboGroupId`'yi 8 bayt okuyor; `operator<<(Side)` bool basıyor | [mesajlar](10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#şüpheli) |
| K-145 | bug? | `headerSnapshotCallbacks` dizisi ilklendirilmiyor (C++17, heap'te belirsiz değer) | [abonelik-api](10-servisler/itch-sdk/abonelik-api.md#şüpheli) |
| K-146 | bug | Çoğu abonelik türünde slot geri kazanılmıyor: orderbook başına ömür boyu 32 abonelik, sonrası callback'siz geçerli handle (aynı sembolde 33. strateji start'ı) | [abonelik-api](10-servisler/itch-sdk/abonelik-api.md#şüpheli) |
| K-147 | doğrula | `findClientForOrderbook` static cache yarışı (combiner OUCH thread'inden subscribe ediyor), shutdown sonrası dangling pointer (eski #12) | [abonelik-api](10-servisler/itch-sdk/abonelik-api.md#şüpheli) |
| K-148 | doğrula | trade-data-app `rewinderSourceIp`'yi set etmiyor; Rewinder yanıtları demux'ta tanınıyor mu | [abonelik-api](10-servisler/itch-sdk/abonelik-api.md#şüpheli) |

## ouch-sdk / network-sdk

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-149 | bug? | network-sdk `getApplicationResult` AlgoTrading (2) ile OUCH'u (3) yer değiştiriyor; AlgoProd order-service'e `APP_UNKNOWN` ile login oluyor (etkisi doğrulanmadı) | [wire-protokolu](10-servisler/network-sdk/wire-protokolu.md#4-enumlar) |
| K-150 | bug? | MARpc sunucu watchdog'u fd 0'da `heartbeatLock` altında sonsuz döngüye giriyor (`continue` iteratörü ilerletmiyor); sunucu donar | [baglanti](10-servisler/network-sdk/baglanti-ve-threadler.md#şüpheli) |
| K-151 | bug? | Bloklayan ouch-sdk çağrılarında timeout yok; connect hatası sessiz, order-service'e ulaşılamazsa `login` sonsuza kadar bekler (HFT/AlgoProd açılışta asılı kalır) | [ouch-sdk](10-servisler/ouch-sdk/README.md#51-açılış) |
| K-152 | bug? | MARpc istemcisi FIN'i fark etmiyor (`recv()==0` yok sayılıyor), host'a bildirim yok, yeniden bağlanma yok; istekler sessizce kaybolur | [baglanti](10-servisler/network-sdk/baglanti-ve-threadler.md#4-kopma-tespiti-ve-yeniden-bağlanma) |
| K-153 | bug? | Pointer ömrü: login token'ı, `getStrategyInfo` string'leri ve yanıt struct'ları callback döndükten sonra serbest kalan FlatBuffers tamponundan okunuyor (use-after-free) | [wire-protokolu](10-servisler/network-sdk/wire-protokolu.md#6-c-struct--flatbuffers-dönüşümü-ve-pointer-ömrü) |
| K-154 | bug? | Callback içinden bloklayan ouch-sdk çağrısı yapılırsa deadlock (tek callback thread'i) | [ouch-sdk](10-servisler/ouch-sdk/README.md#33-thread-safety) |
| K-155 | bug? | `ReplaceOrder::protocol` wire'a gitmiyor, `CancelOrder`'da alan yok (hep `protocolType=0`); `StrategyInfo` `position`/`lastPrice` SET'te serileştirilmiyor | [ouch-sdk](10-servisler/ouch-sdk/README.md#62-replaceorder-cancelorder) |
| K-156 | bug? | İstek ve olay başına bellek sızıntısı (HFT/AlgoProd olay nesnelerini silmiyor); her `AccountStrategyResponse` (~1.4 MB) okunmayan `networkMap` için kopyalanıyor | [ouch-sdk](10-servisler/ouch-sdk/README.md#şüpheli) |
| K-157 | bug? | MARpc sunucu: Unix socket bind hatası TCP dinlemeyi de durduruyor; `SO_REUSEADDR` bind'dan sonra (etkisiz); reddedilen bağlantının fd'si sızıyor; `accept<0` döngüsü spin | [baglanti](10-servisler/network-sdk/baglanti-ve-threadler.md#2-sunucu-yaşam-döngüsü) |
| K-158 | bug? | fd yeniden kullanım yarışı (`close` temizlikten önce) ve fd başına kuyrukların silinmemesi: bayat yanıt aynı fd'ye gelen yeni bağlantıya gidebilir | [baglanti](10-servisler/network-sdk/baglanti-ve-threadler.md#8-backpressure-ve-fd-yeniden-kullanımı) |
| K-159 | bug? | Farklı thread'lerden gönderilen istek/olaylar arasında sıra garantisi yok (moodycamel yalnız üretici başına FIFO) | [baglanti](10-servisler/network-sdk/baglanti-ve-threadler.md#6-sıralama-garantisi) |
| K-160 | bug? | `CLOSE_MSG` sabit offset'te kontrol ediliyor; bilinmeyen union tipi iki tarafı da düşürür; `[byte]` alanlarında sonlandırıcı yok (`authToken`, Replace `passThrough` çöp bayt alabilir) | [wire-protokolu](10-servisler/network-sdk/wire-protokolu.md#şüpheli) |
| K-161 | doğrula | network-sdk/ouch-sdk thread'leri yield'siz busy-spin (CPU, Onload etkisi); iki tarafın tamponları dolunca send/recv kilitlenmesi | [baglanti](10-servisler/network-sdk/baglanti-ve-threadler.md#şüpheli) |
| K-162 | eksik | `ouchSDKApp/main.cpp`'de sabit IP/kullanıcı/şifre düz metin; `Application::OUCH` (3) order-service'te `APP_UNKNOWN` | [ouch-sdk](10-servisler/ouch-sdk/README.md#93-ouchsdkapp) |

## mtrader-trade-ui

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-163 | bug? | Eski GUI (prod) fiyatı çoğu yerde sabit ×1000 ile çeviriyor (`OrderForm` sabah emri dahil), `decimalCount` kullanılmıyor; VİOP'ta (`decimalCount=2`) emir 10× sapar | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#33-fiyat-ve-birim-ölçeği) |
| K-164 | doğrula | Taban "Taban Lot" kolonu: eski GUI (prod) `maxAskLot`, yeni GUI `minBidLot` okuyor; hangisi doğru? | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#35-tavan-9-ve-taban-14-tavan-taban-orderbooktavansettingstsx-tabansettingstsx) |
| K-165 | bug? | Eski GUI Tavan pasif satış vurgusu hiç yanmıyor (`Has_Passive_Sell_Order` okunuyor, motor `…_At_Tavan` yolluyor) | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#35-tavan-9-ve-taban-14-tavan-taban-orderbooktavansettingstsx-tabansettingstsx) |
| K-166 | bug? | Eski GUI Varant varsayılan `criteriaValue`/`toleranceCount` 0; motor komutu sessizce düşürüyor | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#36-varant-13-varantvaranttrackerform) |
| K-167 | bug? | Eski GUI Teorik başlat/durdur `strategyType: 4` ve `Strategy_Id` = hesap adı gönderiyor | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#37-teorik-fiyat-8-theoreticformtheoreticformtsx) |
| K-168 | bug? | Eski GUI socket'leri yeniden bağlanmıyor; ilk bağlantıda `client_id` 0 gelirse auth gönderilmiyor, socket ölü kalıyor (paneller donar, sayfa yenilemesi gerekir) | [backend-sozlesmesi](10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#44-eski-gui-socket-yönetimi) |
| K-169 | bug? | Eski GUI `setStrategyCommands` yanıtında olmayan `response.status`'a bakıyor; toplu iptal başarılı olsa da hata toast'ı | [backend-sozlesmesi](10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#şüpheli) |
| K-170 | bug? | Eski GUI 401 sonrası yalnız localStorage token'ını siliyor, `sessionStorage` token'ı kalıyor; şifre OTP yeniden gönderimi için `sessionStorage`'da düz metin; Electron `nodeIntegration: true`, CSP `unsafe-eval` | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#25-tarayıcı-depolaması-önemli) |
| K-171 | doğrula | Eski GUI emir aboneliğinde 12 (HFT_User) ve 15 yok; HFT serbest emirleri emir geçmişine düşmüyor olabilir; order socket yeniden açılınca çift emir | [backend-sozlesmesi](10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#42-feed-tablosu) |
| K-172 | bug? | Eski GUI OrderForm güncelle/sil `custom_data` önekini emrin değil formun seçili saatinden alıyor | [eski-gui](10-servisler/mtrader-trade-ui/eski-gui.md#şüpheli) |
| K-173 | doğrula | Yeni GUI pasif emirler paneli 3 denemeden sonra yeniden bağlanmayı bırakıyor (`AGENTS.md`'deki sınırsız iyileşme kuralıyla çelişiyor) | [backend-sozlesmesi](10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#43-yeni-gui-socket-yönetimi) |
| K-174 | bug? | Yeni GUI Sidebar düzen kaydı Varant, Varant Toplu ve Teorik tracker panellerini `setPanel` ile yazmıyor | [yeni-gui](10-servisler/mtrader-trade-ui/yeni-gui.md#şüpheli) |
| K-176 | doğrula | `expected_price` ölçeği: `RequestStructs.ts` yorumu "TL × 1000", kod enstrüman bölenini kullanıyor; `subscribeToOrderbook` fiyatları float32 | [backend-sozlesmesi](10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#7-json-lehçesi-ve-ölçek-tablosu) |
| K-177 | eksik | Yeni GUI `socketStore.sendCommand` WS'ten `fields` gönderiyor ama sunucu okumuyor, çağıranı yok (ölü kod adayı); satır zemin renkleri ham Tailwind sınıfı (AGENTS.md renk token kuralı) | [yeni-gui](10-servisler/mtrader-trade-ui/yeni-gui.md#şüpheli) |
| K-178 | iş | `algo_gui.yaml` hâlâ `npm install --legacy-peer-deps` ve yüzen `node-version: 22`; `.nvmrc` 22.23.1 | [yeni-gui](10-servisler/mtrader-trade-ui/yeni-gui.md#şüpheli) |

## AlgorithmicTrading (AlgoProd)

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-194 | bug | **Prod:** Fon Takibi lot düzeltmesi (`41adb60`, 2025-08) master'da yok; L=1 ile ilk dolumdan sonra kotasyon biter, sepet hedge'i hiç gönderilmez, fon pozisyonu hedge'siz kalır | [fon-takibi](20-stratejiler/fon-takibi.md#şüpheli) |
| K-195 | bug | **Prod:** Arbitraj teorik fiyatta faiz `/100` düzeltmesi (`c811418`) master'da yok; `diffTick`, açma koşulu ve `Theo_Price` etkileniyor | [arbitraj](20-stratejiler/arbitraj.md#şüpheli) |
| K-196 | bug? | `Channel_Enum` yoksa kanal 0 gider, order-service emri yanıtsız düşürür (ret yok, takip kaydı kalır) | [emir-yolu](10-servisler/algorithmic-trading/emir-yolu.md#şüpheli) |
| K-197 | bug? | order-service risk reddi `rejectCode=0` gelir: Arbitraj durur, VWAP durmaz/yeniden dener; PTRM kontrolleri yakalamaz | [emir-yolu](10-servisler/algorithmic-trading/emir-yolu.md#şüpheli) |
| K-198 | bug? | Userbook yoksa `getOrderbook` callback thread'inde istisna → `std::terminate`; OUCH login 401'de olaylar sessizce atılır, emirler gider | [emir-yolu](10-servisler/algorithmic-trading/emir-yolu.md#şüpheli) |
| K-199 | doğrula | Arbitraj VİOP fiyatı sabit ×100/÷10; `decimalCount ≠ 2` kontratta 10× sapma (K-122/K-163 ailesi); GUI serbest emir fiyatı aynen geçer | [emir-yolu](10-servisler/algorithmic-trading/emir-yolu.md#şüpheli) |
| K-200 | bug? | Gün sonu `EndOfMessages` kapanışı ölü kod (olay yayınlanmıyor); SIGTERM handler yorumda → hep SIGKILL | [uygulama-ve-threadler](10-servisler/algorithmic-trading/uygulama-ve-threadler.md#şüpheli) |
| K-201 | bug? | K-126 nedeniyle `orderbookInitialized` VİOP gelmeden çalışabilir (dayanak/vade/endeks ilişkileri eksik); snapshot ile ilk canlı olay arasında sıra yok | [uygulama-ve-threadler](10-servisler/algorithmic-trading/uygulama-ve-threadler.md#şüpheli) |
| K-202 | bug? | Kilitsiz paylaşılan yapılar (Marketbook, `strategyMap`, `accountbooks`); gRPC restore'dan önce açılıyor; `Manager::stop` detach → aynı strateji iki thread'de koşabilir; strateji thread'i istisnayla ölünce `running` true kalır | [uygulama-ve-threadler](10-servisler/algorithmic-trading/uygulama-ve-threadler.md#şüpheli) |
| K-203 | bug? | `StrategyFactory` istisnası yutuluyor: GUI `OK` görür, ayar DB'ye yazılır, strateji yok; `readAlgoSettings` anahtarı bayt kırparak çıkarıyor | [grpc-ve-veri](10-servisler/algorithmic-trading/grpc-ve-veri.md#şüpheli) |
| K-204 | bug? | `SubscribeToOrderbook` `return`'süz (tanımsız davranış); `FetchCommands` iptali kontrol etmiyor (zombi stream, K-25 ile ilişkili); `GUIManager::workAsyncron` ve AKD stream meşgul döngü | [grpc-ve-veri](10-servisler/algorithmic-trading/grpc-ve-veri.md#şüpheli) |
| K-205 | bug? | Arbitraj: yeni GUI "Automatic" (`O`) yönü motorda tanınmıyor, Above gibi işleniyor; `Passive_Barrier` okunmuyor; dayanak retleri dinlenmiyor, stop'ta dayanak emirleri iptal edilmiyor; `checkPassiveUndOrders` `end()` okuyor | [arbitraj](20-stratejiler/arbitraj.md#şüpheli) |
| K-206 | bug? | VWAP: AKD aboneliği `&& false` ile kapalı ve `brokerMap` boş → AKD açılırsa hiç emir gitmez; vadelide fiyat limiti 0'a iniyor; Overall işlevsiz; stop'taki son emir 100 ms'de iptal | [vwap](20-stratejiler/vwap.md#şüpheli) |
| K-207 | bug? | Fon Takibi: eşlenemeyen PCF sembolünde `stop()` yapıcıda etkisiz, eksik sepetle başlar; reddedilen sepet emri paketi tamamlanmış sayar | [fon-takibi](20-stratejiler/fon-takibi.md#şüpheli) |

## Operasyon

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-179 | bug? | Gece `setup_copy_binary.sh` bozuk (shebang yok, `rm -rf $HOME/Setup`, zip adı boş); main'de de `_development` zip'ini çekiyor → düzelirse prod'a dev binary/config; container içi config elle değişiklikleri ezer; yanlış container adları | [kurulum-ve-dagitim](40-operasyon/kurulum-ve-dagitim.md#şüpheli) |
| K-180 | bug? | Gizli bilgi log'a düşüyor: trade-data-app login şifreyi düz metin basıyor (`gui_api.go`, `ouch_api.go`), HFT açılışta `dbPassword`/`ouchPassword` dahil config'i döküyor, token'lar basılıyor | [log-imzalari](40-operasyon/log-imzalari.md#şüpheli) |
| K-181 | bug? | HFT gRPC portu ↔ trade-data-app `extServices[hft].port` uyuşmuyor (dev: A1, Marbas, Alnus, Alnus-Algo, Global; main: Piramit) → TDA sessizce 2 sn'de bir dener; HFT ve AlgoProd aynı gRPC (9098) ve Rewinder (26001–26010) portlarında | [config-referansi](40-operasyon/config-referansi.md#31-port-matrisi) |
| K-182 | doğrula | main/preprod HFT `run.sh` `Configuration.ini` veriyor, paket `.toml` içeriyor, HFT yalnız TOML okuyor; prod sunucuda elle düzeltilmiş mi | [config-referansi](40-operasyon/config-referansi.md#2-paketleme-ve-gece-güncellemesi) |
| K-183 | bug? | HFT/AlgoProd `run.sh` `kill -15 <isim>` (bash isim kabul etmez) → SIGTERM gitmiyor, SIGKILL; AlgoProd SIGTERM handler'ı yorumda; order-service gRPC `Wait()` SIGTERM'de çıkmayabilir | [kurulum-ve-dagitim](40-operasyon/kurulum-ve-dagitim.md#şüpheli) |
| K-184 | bug? | Cron prod container adlarını kullanıyor, dev (`*Test`) ve preprod (`*PreProd`) adları farklı → otomatik start/stop çalışmaz; `order_algo_db` `install.sh`'ta yok (Alnus Algo paketi servis kurmuyor); dev `algo_order` cron eklemiyor | [kurulum-ve-dagitim](40-operasyon/kurulum-ve-dagitim.md#şüpheli) |
| K-185 | bug? | Log arşivi: S3'e yalnız HFT; `MODE`/`COMPANY_NAME` boş → S3 yolu bozuk; order-service glob'u aktif `order_service.txt`'yi kapsamıyor; trade-data-app log dosya adı bozuk, her açılışta sıfırlanıyor, volume yok | [log-imzalari](40-operasyon/log-imzalari.md#şüpheli) |
| K-186 | bug? | Algo-Setup script hataları: dev `install.sh` MySQL `setup.sql`'i koymuyor (şema init edilmez); `install_data.sh` sözdizimi hatası; `backupAllDatabases.sh` yanlış dosya adı (gece yedeği alınmıyor olabilir); zip'e girmeyen dosyalar; mlx yolu kırık | [kurulum-ve-dagitim](40-operasyon/kurulum-ve-dagitim.md#şüpheli) |
| K-187 | bug? | AlgoProd config parser'ı `:` içeren değerleri ve `secondaryRewinderIp` satırlarını sessizce atlıyor, `$`/`&` parse'ı bozuyor, hata `terminate`; DB login hatası çökertir, OUCH login hatası sessiz | [algorithmic-trading/config](10-servisler/algorithmic-trading/config.md#şüpheli) |
| K-188 | doğrula | Müşteri config'lerinde kopyala-yapıştır izleri: AlgoProd Alnus/Marbas aynı uzak adres, Kanjo = Global (yanlış `dbPort`), main HFT `dbIp`'leri, dev HFT config'lerinde Piramit NIC'i ve Glimpse kullanıcısı | [config-referansi](40-operasyon/config-referansi.md#şüpheli) |
| K-189 | doğrula | Onload sürümü: AlgoProd imajı 9.0.1.86, host ve diğer imajlar 9.2.0.43 (userspace ↔ sürücü eşleşmeli) | [config-referansi](40-operasyon/config-referansi.md#şüpheli) |
| K-190 | bug? | MySQL `3306` bütün arayüzlere açık, adlandırılmış veri volume'u yok; Kanjo'da nginx 81 ↔ MAAdminUI 81 çakışma adayı | [config-referansi](40-operasyon/config-referansi.md#şüpheli) |
| K-191 | doğrula | Sabah kontrolü: Piramit prod container adları (docx `*Prod`, Algo-Setup'ta yok); bant dışı fiyatlı seans öncesi test emrinin `-110023` alıp almadığı | [sabah-kontrolleri](40-operasyon/sabah-kontrolleri.md) |

## Borsa kuralları

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-193 | doğrula | VİOP seans saatleri (09:20/09:30–18:15, akşam 19:00–23:00) yalnız ikincil kaynaktan; resmi VİOP prosedürüyle teyit | [borsa-kurallari](00-genel/borsa-kurallari.md#seanslar) |

## Uçtan uca akışlarda yeni bulgular (2026-10-23)

Koddan çıkarılan sonuçlar canlıda gözlemle doğrulanmış sayılmaz; ayrıntı ve koşullar linklenen akıştadır.

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-208 | bug? | HftClassic her işlenen ITCH olayında koşulsuz WARN log'u üretiyor (development ve master) | [hot-path](30-akislar/hot-path.md#şüpheli) |
| K-209 | bug? | Combiner fill callback'i ITCH decode thread'inde strateji kilidinde bloklanabilir | [hot-path](30-akislar/hot-path.md#şüpheli) |
| K-210 | doğrula | HFT ITCH callback'lerinde olay başına heap allocation var; gecikme etkisi ölçülmedi | [hot-path](30-akislar/hot-path.md#şüpheli) |
| K-211 | bug? | HFT Serbest (tip 12) için strateji yaratma dalı yok; manuel emir yolu Strategy creation failed dönebilir | [manuel-emir](30-akislar/manuel-emir.md#şüpheli) |
| K-212 | doğrula | Tavan/Taban/Teorik/Varant workspace'lerinde Serbest emir tip 1 ile AlgoProd'a yönleniyor | [manuel-emir](30-akislar/manuel-emir.md#şüpheli) |
| K-213 | doğrula | İptal/replace hedef motoru emir sahibinden değil panelin strategy_type alanından seçiliyor | [manuel-emir](30-akislar/manuel-emir.md#şüpheli) |
| K-214 | bug? | AlgoProd restart'ında anahtar bildirim kuyrukları kayboluyor; gateway abonelikleri otomatik yenilemiyor | [strateji-baslatma](30-akislar/strateji-baslatma.md#şüpheli) |
| K-215 | bug? | Handoff sonrası yalnız HFT restart'ı OUCH kullanıcılarını geri getirmiyor; eski tek-servis restart prosedürü yetersiz | [kopma-ve-kurtarma](30-akislar/kopma-ve-kurtarma.md#hft-gün-içi-restart--strateji-ve-pozisyon) |
| K-216 | bug? | trade-data-app tek başına restart sonrası yeni DataService.Login gelmezse WS ve motor bağlantıları açılmıyor | [kopma-ve-kurtarma](30-akislar/kopma-ve-kurtarma.md#trade-data-app-restart) |
| K-217 | doğrula | Pay açılışında hesabın bütün OUCH kullanıcıları devredilmişse order-service satırı gönderemeyebilir | [sabah-emri-ve-handoff](30-akislar/sabah-emri-ve-handoff.md#8-açılış-gönderimleri-vadeli-pay-varant-yip) |
| K-218 | doğrula | T−60 s çekiminden sonra girilen aktif pay MORNING/OPENING satırı sonraki güne kalabilir | [sabah-emri-ve-handoff](30-akislar/sabah-emri-ve-handoff.md#1-toplu-emir-girişi-önceki-gün-veya-gün-içi) |
| K-219 | doğrula | HFT SDK ve toplu emir yolları off_hours set etmiyor; borsa gereksinimi teyit edilmedi | [sabah-emri-ve-handoff](30-akislar/sabah-emri-ve-handoff.md#9-gün-içi-ve-akşam) |
| K-220 | bug? | AlgoProd'a bağlı morning-only OUCH kullanıcısı devredilirse referans sürüm devralmıyor; başka canlı kullanıcı yoksa hesap OUCH'suz | [sabah-emri-ve-handoff](30-akislar/sabah-emri-ve-handoff.md#13-algoprodun-yeri) |

## Admin paneli (2026-10-23)

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-221 | bug? | Panel hesap repeat_count/Dedicated alanlarını koruyor; development backend bunları kaldırmış, OUCH repeat_count/core_to_pin alanlarını panel sunmuyor | [sürüm farkları](10-servisler/mtrader-frontend-apps/dagitim-ve-surum-farklari.md#1-frontend--backend-sözleşme-farkı) |
| K-222 | doğrula | İzinli strateji UI listesi 0–12 ile sabit; 13/14/15 yok, DB Strategies ucu kullanılmıyor | [alanlar](10-servisler/mtrader-frontend-apps/alanlar-ve-servislere-etkisi.md#şüpheli) |
| K-223 | doğrula | Admin yeni OUCH/FIX kaydında applicationUser=4 sabit; hedef uygulama panelden seçilemiyor | [alanlar](10-servisler/mtrader-frontend-apps/alanlar-ve-servislere-etkisi.md#şüpheli) |
| K-224 | bug? | Order-user formunda boşaltılıp payload'dan çıkarılan parola backend update SQL'inde boş yazılabilir | [alanlar](10-servisler/mtrader-frontend-apps/alanlar-ve-servislere-etkisi.md#şüpheli) |
| K-225 | bug? | Order-user mutation'ları dropdown cache'ini invalid etmiyor; logout QueryClient cache'ini temizlemiyor | [arayüz](10-servisler/mtrader-frontend-apps/arayuz-ve-oturum.md#şüpheli) |
| K-226 | doğrula | Tüm export 10 000, bazı ilişki seçimleri 1000 kayıtla sınırlı | [arayüz](10-servisler/mtrader-frontend-apps/arayuz-ve-oturum.md#4-liste-toplu-silme-ve-csv) |
| K-227 | bug? | Admin ilişki insert/update hatalarının bazıları rollback yerine devam ediyor; eksik ilişkilerle başarı dönebilir | [alanlar](10-servisler/mtrader-frontend-apps/alanlar-ve-servislere-etkisi.md#şüpheli) |
| K-228 | doğrula | npm start server build'i bekliyor; build script'i server dizinini siliyor (production nginx yolu ayrı) | [dağıtım](10-servisler/mtrader-frontend-apps/dagitim-ve-surum-farklari.md#şüpheli) |
| K-230 | bug? | Replace rekey'i kuyruktaki eski token'lı execute olayının GUI'de varsayılan proto'ya dönüşmesine yol açabilir | [emir yaşam döngüsü](10-servisler/hftsrvprod/emir-yasam-dongusu.md#ikinci-tur-gui-token-eşlemesi) |
| K-231 | bug? | SDK main hard cap yalnız enstrüman limitini aşan emirlerde çalışıyor; development'ta koşul ve çarpım taşması koruması farklı | [branch kontrolü](10-servisler/maordersdk/branch-ve-replay-kontrolu.md#şüpheli) |

| K-232 | bug? | Legacy master FIX fill handler'ında replay ayrımı/dedup yok; yeniden teslim edilen eşleşen geçmiş fill pozisyon kuyruğuna tekrar girer | [FIX branch kontrolü](10-servisler/order-service/fix-branch-karsilastirmasi.md#şüpheli) |

| K-233 | bug? | 1409'suz Logon SDK'da şifre değişimi başarısı, host'ta bilinmiyor sayılıyor; DB promote eski şifreyi yazıp pending'i silebilir | [FIX karşılaştırması](10-servisler/order-service/fix-branch-karsilastirmasi.md#k-233--1409suz-logonda-sdk-ve-host-şifre-sonucu-ayrışıyor) |
| K-234 | bug? | Manuel FIX config adayı pending DB yazımı başarısız olsa da arm ediliyor; otomatik akışın DB onayı garantisi burada yok | [FIX karşılaştırması](10-servisler/order-service/fix-branch-karsilastirmasi.md#k-234--manuel-config-adayı-db-onayı-olmadan-arm-ediliyor) |

| K-235 | doğrula | Taban PTRM reddinde durma development'ta var, master'da yok; ret sonrası aynı stop koruması varsayılmamalı | [Taban](20-stratejiler/taban.md#ikinci-kod-turu--branch-sınırı) |
| K-236 | bug? | HFT Classic `Is_Stop_Loss_Enabled` strateji alanına alınır ama karar yolunda okunmaz; false tek başına stop'u kapatmaz | [Classic](20-stratejiler/hft-classic.md#ikinci-kod-turu--classic-kontrol-sınırları) |
| K-237 | bug? | HFT Classic tek işlem accept kontrolü satış dalında da Start_With_Buy kullanıyor; satış başlangıcında mandal kurulmayabilir | [Classic](20-stratejiler/hft-classic.md#ikinci-kod-turu--classic-kontrol-sınırları) |

| K-238 | doğrula | Tavan/Taban çalışma saati filtresi koruyucu timer/defter olaylarını da eler; bitiş sonrasında otomatik çıkış garantisi yok | [Taban timer sırası](20-stratejiler/taban.md#ikinci-tur--timer-ve-callback-sırası) |

## Yolda / takip

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-13 | iş | AlgoProd MAOrderSDK + handoff `add-order-sdk` branch'inde; merge edilince dokümanlar güncellenecek | [sistem-haritasi](00-genel/sistem-haritasi.md) § Emir yolları |
| K-14 | iş | Uptick geliştirmesi planlanıyor (şu an global bayrak, hep kapalı) | [borsa-kurallari](00-genel/borsa-kurallari.md) § Açığa satış ve uptick |
| K-15 | iş | Kaynak repolarda açık metin şifreler (ClickHouse, lisans, VERDA, Datastore, AKD, Glimpse, DB, JWT `secretKey`, SSH; Algo-Setup: AWS anahtarları, Docker Hub, MySQL, Discord webhook, TLS özel anahtarları; AlgoProd Sentry DSN) → Secrets'a taşınmalı. ⏸ sonra ele alınacak | [config-referansi](40-operasyon/config-referansi.md#şüpheli) |
