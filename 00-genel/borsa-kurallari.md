---
kapsam: Kodun dayandığı BIST kuralları (fiyat adımı, limitler, seanslar, açığa satış) ve kodun bunları nereden aldığı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
dis_kaynak:
  - url: https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf
    erisim: 2026-10-22
    not: Resmi Pay Piyasası Prosedürü (02.PRO.01), sürüm 3.34, revizyon 21/09/2026. Fiyat adımı, marj, seans saatleri ve tek fiyat seansları buradan.
  - url: https://www.bloomberght.com/bist-ten-fiyat-adimi-ve-kotasyon-araliklarina-yeni-duzenleme-2337339
    erisim: 2026-10-22
    not: 2023 fiyat adımı düzenlemesi (yürürlük 06/11/2023); prosedürdeki tabloyla aynı.
  - url: https://www.garantibbva.com.tr/isim-icin/yatirim/viop
    erisim: 2026-10-22
    not: VİOP seans saatleri — ikincil kaynak, resmi VİOP prosedürüyle karşılaştırılmadı.
  - url: https://www.cnnturk.com/ekonomi/borsa-istanbul-aciga-satis-islemlerinde-bugun-yukari-adim-kuralinin-uygulanacagini-duyurdu-2244665
    erisim: 2026-10-22
  - url: https://www.garantibbva.com.tr/borsa-hisse-senetleri/bist-islem-saatleri
    erisim: 2026-10-22
dogrulama: 2026-10-22
durum: taslak
---

# Borsa kuralları

**Önce kod.** Sistem fiyat adımını, tavan/tabanı ve seans durumunu borsadan (ITCH, VERDA) çalışma anında alır. Bu dosyadaki borsa kuralları **referans** içindir. Bir değerin sistemde nasıl kullanıldığı sorulursa koda ve ilgili dokümana bak. Resmi spesifikasyonlar algo-configs `doc/BIST-Dökümanlar/`'dadır ([40-operasyon](../40-operasyon/README.md#algo-configs-doc-insan-için-yazılmış-kaynaklar)).

Pay piyasası kuralları resmi **Pay Piyasası Prosedürü**'nden (sürüm 3.34, revizyon 21/09/2026) alındı. VİOP saatleri ikincil kaynaktandır; kritik bir cevapta "resmi VİOP prosedüründen teyit edilmedi" de. Borsa bu değerleri Yönetim Kurulu kararıyla değiştirebilir; prosedürün güncel sürümüne bakılmalı.

## Fiyat adımı (tick)

**Kodda:**
- Tablo kodda sabit değildir, ITCH'ten gelir: `itchsdk_get_tick_size(obId, price)` ([itch-sdk](../10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md#4-fiyat-ve-miktar-ölçeği)).
- Adım fiyat bandına göre değiştiği için "N kademe aşağı/yukarı" hesapları bantları tek tek yürür (ör. [tavan](../20-stratejiler/tavan.md) max-size arm price).
- Tick bulunamazsa bazı stratejiler 1 kullanır ([varant-toplu](../20-stratejiler/varant-toplu.md#fiyat-ve-birimler)).

**Borsada (paylar, referans):**

Prosedür Tablo-7 (paylar ve yeni pay alma hakları):

| Fiyat seviyesi (TL) | Fiyat adımı (TL) |
|---------------------|------------------|
| 0,01 – 19,99 | 0,01 |
| 20,00 – 49,99 | 0,02 |
| 50,00 – 99,99 | 0,05 |
| 100,00 – 249,99 | 0,10 |
| 250,00 – 499,99 | 0,25 |
| 500,00 – 999,99 | 0,50 |
| 1.000,00 – 2.499,99 | 1,00 |
| 2.500,00 ve üzeri | 2,50 |

- **Adım baz fiyata değil, emrin fiyat seviyesine bağlıdır.** Baz fiyatı 19,97 olan payda 20,00'ye kadar adım 0,01, üstünde 0,02'dir (prosedür örneği). Kodun bantları tek tek yürümesi bu yüzdendir.
- Tablo 6 Kasım 2023'te yürürlüğe girdi; prosedürün 2026-09 sürümünde değişmemiş.
- BYF'lerin tablosu ayrıdır (Tablo-8). Varant, sertifika, emtia sertifikası ve TAS işlemlerinde her seviyede adım **0,01**.

## Günlük fiyat limitleri (tavan / taban)

**Kodda:**
- Tavan, taban ve maks emir değeri günlük **VERDA** dosyalarından gelir. Bunları `Instrument` tablosuna yazan tek yer trade-data-app TradeVerifier'dır ([trade-data-app](../10-servisler/trade-data-app/README.md#açılış-sırası-cmddataappmaingo)). Kod limit yüzdesini kendisi hesaplamaz.
- **Brüt takas** enstrümanlarına MAOrderSDK emir göndermez (yerel ret 1002).
- **Maks emir değeri** (`max_order_value`, tam TL): aşan emir bölünür; tek lot bile aşıyorsa yerel ret 1004 ([MAOrderSDK](../10-servisler/maordersdk/emir-akisi.md)).

**Borsada (referans):**
- Baz fiyat normalde önceki günün kapanış fiyatıdır. Sermaye artırımı, temettü, bölünme gibi olaylarda düzeltilmiş baz fiyat kullanılır.
- Tavana veya tabana gelmek işlemi durdurmaz; o fiyattan karşı emir varsa eşleşme sürer.
- Hesaplanan limit fiyat adımına denk gelmezse tavan aşağı, taban yukarı yuvarlanır. Bu kural pay vadelilerinde açıkça belirtilmiştir.
- Pay vadeli sözleşmelerinde günlük limit, baz fiyatın ±%20'sidir.
- **Marj (prosedür § 5.1.11):** Paylarda **Yıldız Pazar ±%20, Ana Pazar ±%15, Alt Pazar, YİP ve PÖİP ±%10**. BYF ±%20, GMF ve girişim sermayesi fonları ±%20, yeni pay alma hakları ±%50, gayrimenkul ve emtia sertifikaları ±%5. Varantlarda baz fiyat yoktur (serbest marj).
- Yaygın bilinen "±%10" yalnız Alt Pazar, YİP ve PÖİP için doğrudur. Yıldız Pazar hissesinde taban −%20'dir. Kod yüzdeye dayanmaz, tavan/tabanı VERDA'dan okur.

## Seanslar

**Kodda:**

| Kural | Nerede |
|-------|--------|
| Strateji emirleri yalnız sürekli işlemde gider (`continuousSession()`). Seans durumu ITCH orderbook state'inden gelir. | [hft-classic](../20-stratejiler/hft-classic.md#tetik-erime) |
| Sabah emirleri seans açılmadan gönderilir, `-110023` ("Illegal transaction at this time") reddi alındıkça, kabul alınana kadar (en çok 900 ms, yalnız `repeatLastShot: true` iken) son atış yeniden gönderilir. | [order-service](../10-servisler/order-service/toplu-emirler.md) |
| Sabah emri saati config'tedir (örnek 09:40:00.144). Açılış emirleri payda 10:00, varant/sertifikada 10:02. | aynı yer |
| Müzayedede denge fiyatı yayınlanır; Eşleştirme durumunda Teorik Fiyat stratejisi değerlendirme yapar. Denge güncellemesinin saati UTC 13:00'ten (İstanbul 16:00) önceyse "sabah", sonrası "akşam" sayılır. | [teorik-fiyat](../20-stratejiler/teorik-fiyat.md) |
| Strateji saat alanları İstanbul saatiyle günün saniyesidir (36000 = 10:00). | strateji dosyaları |

**Borsada (pay piyasası, prosedür Ek-9, tam iş günü):**

| Bölüm | Saat |
|-------|------|
| Açılış: emir toplama | 09:40 – 09:55 (+30 sn içinde rastgele bitiş) |
| Açılış: fiyat belirleme | 09:55 (+) |
| Sürekli işlem | 10:00 – 18:00 |
| Kapanış: marj yayını | 18:00 – 18:01 |
| Kapanış: emir toplama | 18:01 – 18:05 |
| Kapanış: fiyat belirleme | 18:05 (+) |
| Kapanış fiyatından / tek fiyattan işlemler: marj yayını | 18:07 – 18:08 |
| Kapanış fiyatından / tek fiyattan işlemler | 18:08 – 18:10 |

- **BYF:** açılış emir toplama 09:40 – 09:56.
- **Varant ve sertifika:** açılış seansına girmez. Seans 10:00:10'da başlar; 10:00 – 10:02 arası yalnız piyasa yapıcı kotasyonu kabul edilir (`P_SALTKOTASYON`). order-service config'indeki 10:02 gönderimiyle uyumlu.
- **Yarım iş günü (arife):** 09:40 – 12:40. Sürekli işlem 10:00 – 12:30, kapanış 12:30 – 12:37, kapanış fiyatından işlemler 12:37 – 12:40.
- **Gün ortası tek fiyat** sürekli işlem gören pazarlarda (Yıldız, Ana, Alt) **yoktur**. Yalnız tek fiyat yöntemiyle işlem gören araçlarda vardır.
- **YİP ve PÖİP: günde 5 kez tek fiyat** (prosedür Tablo-4 ve Tablo-10):

  | Tek fiyat süreci | Bölüm | Emir toplama | Fiyat belirleme |
  |------------------|-------|--------------|-----------------|
  | 1. Açılış | 09:40 – 10:00 | 09:40 – 09:55 | 09:55 (+) |
  | 2. | 10:00 – 13:00 | 10:00 – 12:55 | 12:55 (+) |
  | 3. Gün ortası | 13:00 – 14:00 | 13:00 – 13:55 | 13:55 (+) |
  | 4. | 14:00 – 18:00 | 14:00 – 17:55 | 17:55 (+) |
  | 5. Kapanış | 18:01 – 18:07 | 18:01 – 18:05 | 18:05 (+) |

  Ardından 18:08 – 18:10 kapanış fiyatından işlemler. Eşleşmeyen geçerli emirler bir sonraki sürece aktarılır. order-service örnek config'indeki YİP seansları (10:00, 13:00, 14:00) 2.–4. süreçlerin emir toplama başlangıçlarıdır ([toplu-emirler](../10-servisler/order-service/toplu-emirler.md)).

**VİOP (ikincil kaynak):** Gün içi seans 09:20'de emir toplamayla açılır, sürekli müzayede 09:30 – 18:15 arasındadır (bazı kaynaklar kapanışı 18:10 verir). Akşam seansı 19:00 – 23:00 arasındadır; endeks ve bazı emtia sözleşmeleri girer, yarım günlerde yapılmaz. order-service config'indeki VİOP sabah (09:20) ve vadeli açılış (09:30) saatleriyle uyumludur. ❓ Resmi VİOP prosedüründen teyit edilmedi.

## Açığa satış ve yukarı adım (uptick) kuralı

**Kodda:**
- Satış emri `SELL` veya `SHORT_SELL` gider. HFT'de uptick kararı **global bir config bayrağıdır** (`uptickRule`); enstrümana veya güne göre değişmez ([hftsrvprod config](../10-servisler/hftsrvprod/README.md#config-configurationtoml), [hft-classic](../20-stratejiler/hft-classic.md#bait--chase-uptick)).
- order-service `RiskManager` açığa satış yasaklarını hisse kısıtı olarak uygular. Kısmen: pazar geneli `ACIGA_SATIS` listede adı geçmeyen hisseye uygulanmaz; `DEPO`/`BRUT_TAKAS` kısıtlı hissede açığa satış reddedilmez; açığa satışta bakiye kontrolü yoktur ([order-service/risk](../10-servisler/order-service/risk.md)).

**Borsada (referans):**
- **Kural:** Açığa satış, son gerçekleşen işlem fiyatının üzerinden yapılabilir. Son işlem bir öncekinin üzerinde gerçekleştiyse son fiyattan da yapılabilir.
- **Ne zaman:** Kural sürekli değildir. Borsa İstanbul onu **belirli seanslar için** ilan eder (ör. 24 Şubat 2025; 11, 13 ve 17 Mart 2025).
- **Kapsam:** Gün içinde sahip olunmadan yapılıp aynı gün kapatılan satış da açığa satıştır; emir açığa satış işaretiyle iletilmelidir. SPK'nın 5 Aralık 2024 kararıyla açığa satış BIST 50 paylarında yapılabilir.
- **Sonuç:** HFT'de bu günlere özel bir mekanizma yok. `uptickRule` bütün müşteri config'lerinde `false`; açmak config değişikliği ve yeniden başlatma ister. Strateji bazında `Send_Sell_Orders_Instead_Of_Short` açığa satışı kapatır ([hft-classic](../20-stratejiler/hft-classic.md#bait--chase-uptick)). **Operasyon pratiği:** İlan günlerinde genelde strateji çalıştırılmıyor; sistem bu kurala henüz uygun değil, geliştirme planlanıyor (kullanıcı beyanı, 2026-10-22). ❓ Kuralın 2026'daki güncel uygulaması doğrulanmadı.

## Ön-işlem risk (PTRM) ve diğer ret kodları

| Kod | Anlam | Kim tanıyor |
|-----|-------|-------------|
| `-850002` | User blocked (risk grubu breach) | HFT, AlgoProd |
| `-850004` | Pre-trade risk limiti aşıldı | HFT, AlgoProd |
| `-850044` | Hesap margin breach durumunda | HFT, AlgoProd |
| `-850064` | Margin limiti nedeniyle user blocked | Yalnız HFT |
| `-420131` | İzin verilen limit dışında (`RX_OUTSIDE_ALLOWED_LIMIT`) | AlgoProd Arbitraj |
| `-110023` | Bu saatte geçersiz işlem (seans dışı) | order-service son atış |

Kaynak: HFT `src/Globals/GlobalConstants.h`, AlgoProd `algoSrc/Globals/GlobalDefinitions.h`. Davranış: [taban](../20-stratejiler/taban.md#tolerans-ve-durma), [vwap](../20-stratejiler/vwap.md#ptrm), [arbitraj](../20-stratejiler/arbitraj.md#döngü-doperiodicchecks).
