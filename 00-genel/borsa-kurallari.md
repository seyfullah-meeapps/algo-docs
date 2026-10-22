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
  - url: https://borsaistanbul.com/tr/sayfa/493/pay-piyasasi-piyasa-isleyisi
    erisim: 2026-10-22
    not: Sayfaya bu ortamdan doğrudan erişilemedi; içerik arama motoru özetinden alındı. Sayfada tarih yok.
  - url: https://www.cnnturk.com/ekonomi/borsa-istanbul-aciga-satis-islemlerinde-bugun-yukari-adim-kuralinin-uygulanacagini-duyurdu-2244665
    erisim: 2026-10-22
  - url: https://www.garantibbva.com.tr/borsa-hisse-senetleri/bist-islem-saatleri
    erisim: 2026-10-22
dogrulama: 2026-10-22
durum: taslak
---

# Borsa kuralları

**Önce kod.** Sistem fiyat adımını, tavan/tabanı ve seans durumunu borsadan (ITCH, VERDA) çalışma anında alır. Bu dosyadaki borsa kuralları **referans** içindir. Bir değerin sistemde nasıl kullanıldığı sorulursa koda ve ilgili dokümana bak. Resmi spesifikasyonlar algo-configs `doc/BIST-Dökümanlar/`'dadır ([40-operasyon](../40-operasyon/README.md#algo-configs-doc-insan-için-yazılmış-kaynaklar)).

Dış kaynaklı bilgiler BIST'in resmi sayfasından doğrudan okunamadı (ağ erişimi yok); arama sonuçlarından derlendi. Kritik bir cevapta "resmi kaynaktan teyit edilmedi" de.

## Fiyat adımı (tick)

**Kodda:**
- Tablo kodda sabit değildir, ITCH'ten gelir: `itchsdk_get_tick_size(obId, price)` ([itch-sdk](../10-servisler/itch-sdk/README.md#abonelik-apisi-publicitch_sdkh-c)).
- Adım fiyat bandına göre değiştiği için "N kademe aşağı/yukarı" hesapları bantları tek tek yürür (ör. [tavan](../20-stratejiler/tavan.md) max-size arm price).
- Tick bulunamazsa bazı stratejiler 1 kullanır ([varant-toplu](../20-stratejiler/varant-toplu.md#fiyat-ve-birimler)).

**Borsada (paylar, referans):**

| Baz fiyat aralığı (TL) | Fiyat adımı (TL) |
|------------------------|------------------|
| 0,01 – 19,99 | 0,01 |
| 20,00 – 49,98 | 0,02 |
| 50,00 – 99,95 | 0,05 |
| 100,00 – 249,90 | 0,10 |
| 250,00 ve üzeri | 0,25'ten başlayıp artan kademeler |

❓ 250 TL üstü kademeler ve tablonun yürürlük tarihi doğrulanmadı. Bilinen son değişiklik 6 Kasım 2023'te yürürlüğe girdi (paylar ve BYF'ler için ayrı tablolar, piyasa yapıcı kotasyon aralıkları dahil). BYF ve varantların tabloları farklıdır.

## Günlük fiyat limitleri (tavan / taban)

**Kodda:**
- Tavan, taban ve maks emir değeri günlük **VERDA** dosyalarından gelir. Bunları `Instrument` tablosuna yazan tek yer trade-data-app TradeVerifier'dır ([trade-data-app](../10-servisler/trade-data-app/README.md#açılış-sırası-cmddataappmaingo)). Kod limit yüzdesini kendisi hesaplamaz.
- **Brüt takas** enstrümanlarına MAOrderSDK emir göndermez (yerel ret 1002).
- **Maks emir değeri** (`max_order_value`, tam TL): aşan emir bölünür; tek lot bile aşıyorsa yerel ret 1004 ([MAOrderSDK](../10-servisler/maordersdk/README.md#emir-gönderme)).

**Borsada (referans):**
- Baz fiyat normalde önceki günün kapanış fiyatıdır. Sermaye artırımı, temettü, bölünme gibi olaylarda düzeltilmiş baz fiyat kullanılır.
- Tavana veya tabana gelmek işlemi durdurmaz; o fiyattan karşı emir varsa eşleşme sürer.
- Hesaplanan limit fiyat adımına denk gelmezse tavan aşağı, taban yukarı yuvarlanır. Bu kural pay vadelilerinde açıkça belirtilmiştir.
- Pay vadeli sözleşmelerinde günlük limit, baz fiyatın ±%20'sidir.
- ❓ Pay piyasası marj yüzdesi (yaygın bilinen ±%10) resmi kaynaktan doğrulanmadı. [Taban](../20-stratejiler/taban.md) dokümanı tabanı −%10 diye anlatır.

## Seanslar

**Kodda:**

| Kural | Nerede |
|-------|--------|
| Strateji emirleri yalnız sürekli işlemde gider (`continuousSession()`). Seans durumu ITCH orderbook state'inden gelir. | [hft-classic](../20-stratejiler/hft-classic.md#tetik-erime) |
| Sabah emirleri seans açılmadan gönderilir, `-110023` ("Illegal transaction at this time") reddi alındıkça tekrar gönderilir. | [order-service](../10-servisler/order-service/README.md#toplu-emir-akışları) |
| Sabah emri saati config'tedir (örnek 09:40:00.144). Açılış emirleri payda 10:00, varant/sertifikada 10:02. | aynı yer |
| Müzayedede denge fiyatı yayınlanır; Eşleştirme durumunda Teorik Fiyat stratejisi değerlendirme yapar. UTC 12:00 öncesi "sabah", sonrası "akşam" sayılır. | [teorik-fiyat](../20-stratejiler/teorik-fiyat.md) |
| Strateji saat alanları İstanbul saatiyle günün saniyesidir (36000 = 10:00). | strateji dosyaları |

**Borsada (pay piyasası, referans):**

| Bölüm | Saat |
|-------|------|
| Açılış seansı: emir toplama | 09:40 – 09:55 |
| Açılış: eşleştirme | 09:55 – 10:00 |
| Sürekli işlem | 10:00 – 18:00 |
| Kapanış seansı (marj yayını, emir toplama, kapanış fiyatından işlem) | 18:00 – 18:10 |

- Varant ve sertifikalarda 10:00–10:02 arası yalnızca piyasa yapıcı kotasyonu vardır (order-service config'iyle uyumlu).
- BYF açılış seansı: emir toplama 09:40–09:56, eşleştirme 09:56–10:00.
- Arife günleri seans öğleden sonra kapanır (ör. 12:40).
- ❓ Kaynak 2016 tarihli Yönetim Kurulu kararı. Sonraki değişiklikler, gün ortası tek fiyat bölümü ve VİOP saatleri doğrulanmadı.
- **YİP** (Yakın İzleme Pazarı) payları tek fiyat seanslarıyla işlem görür. order-service seans saatlerini config'ten alır (`openingOrders.yip.sessions`). ❓ Seans saatleri doğrulanmadı.

## Açığa satış ve yukarı adım (uptick) kuralı

**Kodda:**
- Satış emri `SELL` veya `SHORT_SELL` gider. HFT'de uptick kararı **global bir config bayrağıdır** (`uptickRule`); enstrümana veya güne göre değişmez ([hftsrvprod config](../10-servisler/hftsrvprod/README.md#config-configurationtoml), [hft-classic](../20-stratejiler/hft-classic.md#bait--chase-uptick)).
- order-service `RiskManager` açığa satış yasaklarını hisse kısıtı olarak uygular ([order-service](../10-servisler/order-service/README.md#risk-riskmanager)).

**Borsada (referans):**
- **Kural:** Açığa satış, son gerçekleşen işlem fiyatının üzerinden yapılabilir. Son işlem bir öncekinin üzerinde gerçekleştiyse son fiyattan da yapılabilir.
- **Ne zaman:** Kural sürekli değildir. Borsa İstanbul onu **belirli seanslar için** ilan eder (ör. 24 Şubat 2025; 11, 13 ve 17 Mart 2025).
- **Kapsam:** Gün içinde sahip olunmadan yapılıp aynı gün kapatılan satış da açığa satıştır; emir açığa satış işaretiyle iletilmelidir. SPK'nın 5 Aralık 2024 kararıyla açığa satış BIST 50 paylarında yapılabilir.
- **Sonuç:** Kuralın ilan edildiği gün HFT'de `uptickRule`'ün açılması gerekir. ❓ Operasyonda bunun nasıl yapıldığı ve 2026'daki güncel durum doğrulanmadı.

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
