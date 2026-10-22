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
| K-43 | doğrula | LimitControlService'in workspace'te istemcisi yok; harici sağlayıcı kim? | [api](10-servisler/trade-data-app/api.md) § 6 |

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
