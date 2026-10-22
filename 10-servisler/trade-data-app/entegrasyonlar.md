---
kapsam: trade-data-app dış veri entegrasyonları (VERDA, Datastore, AKD, BYF, AWS) ve yan modüller (history/volatility, limits, dosya parser'ları, request log); ne zaman çalışır, neyi günceller, kim tüketir, hata olunca ne olur
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: AlgorithmicTrading          # yalnızca tüketici tespiti (Scores, TimeBased)
    branch: development
    commit: 0dc32a7
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app — entegrasyonlar ve yan modüller

Genel yapı ve açılış sırası: [README.md](README.md). Config anahtarları: [config.md](config.md). RPC listesi: [api.md](api.md). Tablo kolonları: [sema.md](sema.md). ITCH/WS akışları: [veri-akisi.md](veri-akisi.md).

## Özet tablo

| Modül | Kod | Ne zaman | Dış kaynak | Yazdığı yer | Tüketici |
|-------|-----|----------|------------|-------------|----------|
| TradeVerifier (VERDA) | `pkg/extdata/tradeverifier` | Açılış (+ bootstrap bildirimiyle bir tekrar) | VERDA servisi (Borsa İstanbul) | `Instrument` tablosu (`lastPrice`, `minPrice`, `maxPrice`, `maxOrderValue`, `isBrutTakas`) + bellek | HFT, AlgoProd, UI, bounds WS feed |
| Datastore | `pkg/extdata/datastore` | ITCH bootstrap (tüm pazarların ilk snapshot'ı) | Borsa İstanbul Datastore API | Endeks CSV'lerinin üzerine yazar | Fiktif endeksler (HFT/AlgoProd) |
| Fiktif endeks ayarları | `pkg/util/excel_parser.go`, `pkg/itch/itch.go` `createIndices` | ITCH bootstrap + açılış | Yerel CSV (`external-files/`) | Bellek | `AlgoService.GetFictive*Settings`, endeks enstrümanları |
| AKD | `pkg/extdata/akd` | Dakikada bir (goroutine) | Foreks AKD servisi | `Scores` tablosu + pubsub | AlgoProd (AKD/TradeByBSRatio, Warrant, VWAP AKD filtresi) |
| BYF | `algo_api.go` `UpdateBYFSettings`, `util.ReadByfFile` | Yalnız açılış | BYF portföy şirketi sitesi (HTTP) | Bellek (`s.byfSettings`) | AlgoProd Fon Takibi (`GetByfSettings`) |
| History (TimeBased) | `pkg/history`, `pkg/pricedata` | Sürekli döngü; dakikada bir DB'ye yazar | ITCH trade feed (iç) | `TimeBased` tablosu | AKD skorları, AlgoProd |
| Volatility | `pkg/volatility` | Aynı döngü | — | `Volatility` tablosu (fiilen boş) | — |
| Limits | `pkg/limits` | İstek | — | Yalnız bellek | `RiskManagerService` istemcileri |
| AWS | `pkg/util/aws_client.go` | Açılış (bağlantı) + istek | AWS SNS / SES | — | GUI login OTP, şifre sıfırlama |
| Varant dosyası | `pkg/util/warrant_file_parser.go`, `warrant_api.go` | İstek | — (yüklenen dosya) | — (yanıt) | UI → HFT Varant Toplu |
| Arbitraj Excel | `pkg/util/arbitrage_excel_*.go` | İstek | — | `Arbitrage*` tabloları (çağıran API) | UI |
| Request log | `pkg/requestlog`, `cmd/requestlog-report` | Her izlenen istek | — | `<log-path>/requests/requests-YYYY-MM-DD.jsonl` | Aracı kurum emir-IP raporu |

## TradeVerifier (VERDA)

**Ne yapar:** VERDA servisinden günlük bülten ve marj dosyasını indirir. Pay piyasası enstrümanlarının tavan, taban, kapanış ve maks emir değerini `Instrument` tablosuna ve ITCH bellek modeline yazar.

**`minPrice`, `maxPrice`, `maxOrderValue` alanlarını yazan tek yer burasıdır.** Bu adım çalışmazsa:
- C++ servisleri `AlgoService.GetAllInstruments` ile tavan/taban/maks emir değeri alamaz.
- Tavan/Taban stratejileri ve HFT azami emir lotu hesabı çalışmaz. Bkz. [tavan.md](../../20-stratejiler/tavan.md), [hft-classic.md](../../20-stratejiler/hft-classic.md).
- `/ws/v1/bounds/start` feed'i (`maxAskLot`) bellekteki `MaxPrice`'ı kullanır (`gui/messages/base_order.go`).

**Ne zaman:** `cmd/dataapp/main.go`, `tradeVerifier.enabled` ise, fiktif ayarlardan sonra ve gRPC sunucusu açılmadan önce çalışır.
1. `UPDATE Instrument SET isBrutTakas = 0` (tüm satırlar).
2. `GetAllFiles`: `GET {verifierUrl}/files`, Basic Auth. Dönen listeyi `name-tr` alanına göre `filesMap`'e koyar. `downloadEnabled=false` ise hiçbir şey çekmez.
3. `GetInstrumentUpdates(true, "", TVMarketTypeEquity, TVInstrumentTimeMorning)`:
   - `"BISTECH PP - Bulten"` dosyasını `DDMMYYYY_bulletin.csv` adıyla çalışma dizinine indirir ve `parseBulletin` ile ayrıştırır.
   - `"BISTECH PP - Sabah Marj Bilgileri"` dosyasını `DDMMYYYY_margin.csv` olarak indirir ve `parseMorningMarginInfo` ile ayrıştırır.
   - İş bitince iki dosyayı da siler.
4. `applyBounds("startup")`:
   - `ConvertToDbInstruments`: DB enstrümanlarını **sembolle** eşler.
   - `UpdateAllInstrumentsInfo`: tek transaction, satır başına `UPDATE ... WHERE id=?`.
   - Ardından DB'yi yeniden okur ve bellekteki `TradableInstrument`'lara `SetMaxPrice`/`SetMinPrice` uygular.
5. Arka plan goroutine'i `reconcileChan`'i dinler ve `applyBounds("snapshot")` çalıştırır. VERDA dosyaları **yeniden indirilmez**; açılışta bellekte tutulan `instUpdates` tekrar uygulanır.
   - Kodun niyeti her pazar snapshot'ında tekrar uygulamak (yorumlar öyle der). Ama `itch.Manager` bildirimi yalnızca **tek seferlik bootstrap** anında gönderir (`snapshotBootstrapDone` sonrası `break`); pratikte goroutine bir kez çalışır, sonraki snapshot'larda tetiklenmez. Ayrıntı: [veri-akisi.md](veri-akisi.md).

**Ayrıştırılan alanlar ve ölçek:**

| Dosya | Kolon (0-tabanlı) | Alan | Ölçek |
|-------|-------------------|------|-------|
| Bülten (`;` ayraçlı) | 1 | sembol | — |
| Bülten | 16 | `PrevLastPrice` | TL × 1000, `math.Round` |
| Bülten | 21 | `ClosingPrice` → `Instrument.lastPrice` | TL × 1000 |
| Bülten | 23, 26 | `ChangePercInDay`, `VWAPPrice` | ham (DB'ye yazılmaz) |
| Marj | 4 | `MinPrice` → `minPrice` (taban) | TL × 1000 |
| Marj | 5 | `MaxPrice` → `maxPrice` (tavan) | TL × 1000 |
| Marj | 11 | `IsBrutTakas` (`strconv.ParseBool`) | bool |
| Marj | 17 | `MaxOrderVal` → `maxOrderValue` (`MaxAllowedVol`) | tam sayı, tam TL ([tavan.md](../../20-stratejiler/tavan.md)) |

- ×1000 sabit kodlanmıştır. Enstrümanın `DecimalCount`'una bakılmaz. ITCH tarafında `priceDivider = 10^DecimalCount` kullanılır (bkz. [README](README.md)).
- ❓ doğrulanmadı: ×1000 her pay için ITCH raw ölçeğiyle örtüşüyor mu?

**Kapsam sınırı:** Yalnızca pay piyasası (sabah) işlenir. VİOP ve BAP enstrümanlarının tavan/tabanı burada **hiç güncellenmez**. Kod VİOP/BAP bülten ayrıştırıcılarını içerir ama `main.go` çağırmaz.

**Kullanılmayan VERDA yetenekleri** (`ITradeVerifier` arayüzünde var, repoda çağıran yok):
- Üye işlem defteri ve karşılaştırma (`CompareAllAccountsExecutedOrders`).
- Tüm emir defteri, emir iptal defteri.
- Yatırımcı/menkul tedbir listeleri, `UpdateInstrumentsWithPrecautions` (`PBRUT` → brüt takas).
- Özsermaye halleri, VİOP mevcut sözleşmeler.

**Hata davranışı:**

| Durum | Sonuç |
|-------|-------|
| `isBrutTakas` sıfırlama hatası | `main` döner → **process çıkar** (gRPC hiç açılmaz) |
| `GetAllFiles` hatası (ağ, auth, JSON) | Yalnızca loglanır. Ama `filesMap` boş kalır, sonraki adım `filesMap[...].Links[0]` ile nil slice'a indeksler → **panic**. |
| VERDA dosya adı (`name-tr`) değişirse | Aynı panic |
| `GetInstrumentUpdates` hatası (indirme/ayrıştırma) | `main` döner → process çıkar |
| `downloadEnabled=false` | İndirme yok. Çalışma dizininde `DDMMYYYY_bulletin.csv` ve `DDMMYYYY_margin.csv` (bugünün tarihi) aranır. Yoksa ayrıştırma hatası → process çıkar. |
| `applyBounds("startup")` DB hatası | Process çıkar |
| 0 eşleşme | Hata değil; tek bildirimdeki tekrar beklenir, sonrası yok |
| Snapshot tekrar denemesi hatası | Loglanır; yeni bildirim gelmediği için tekrar denenmez |

- HTTP istemcisinde timeout yok. HTTP status kontrol edilmez; hata sayfası da dosyaya yazılıp ayrıştırılmaya çalışılır.
- `verifierType` yalnızca `1` (VERDA) destekli. Başka değer verilirse `NewTradeVerifier` `nil` döner, sonraki çağrı nil interface üzerinden panic eder.

## Datastore (Borsa İstanbul)

**Ne yapar:** Fiktif endeks hesabı için iki dosyanın günceli indirilir:
- endeks bölen dosyası (`endeks_bolen_ds_genel_YYYYMMDD.csv`),
- endeks ağırlık dosyası (`endeks_agirlik_ds_genel_YYYYMMDD.csv`).

**Ne zaman:** `itch.Manager.createIndices` içinde çalışır. Bu fonksiyon tüm config'li pazarların ilk snapshot'ı tamamlanınca **bir kez** çağrılır (`[SNAPSHOT] ... one-time bootstrap`). Yalnızca `datastore.enabled=true` ise devreye girer.

**Akış** (`DownloadIndicesFiles`):
1. `POST {url}login` (JSON e-posta/şifre) → `accessToken`.
2. `GET {url}library?page=1&page-size=50` (`x-auth-token`) → önekle eşleşen **ilk** kayıt alınır. API'nin `createDate` azalan sıraladığı varsayılır.
3. `GET {url}file?file-name=...&file-date=yyyyMMdd` → gzip desteğiyle indirilir.
   - Hedef: `fictiveInstrumentSettingDefinitionPath` ve `fictiveItemSettingDetailPath` dizinlerindeki `IndicesDefinitions.csv` ve `IndicesDetails.csv`.
   - Config'teki dosya adı da bu isimdeyse yerel dosyanın **üzerine yazılır**.
- `url` sonunda `/` olmalıdır, çünkü yollar doğrudan eklenir. HTTP timeout 60 sn.

**Hata:** Herhangi bir adım başarısız olursa loglanır ve yerel dosyalara düşülür ("falling back to local files").
- Repodaki yerel dosyalar **31/10/2024** tarihlidir.
- Datastore kapalı müşterilerde endeks bölen ve ağırlıkları bu tarihten kalır, dosya elle güncellenmedikçe değişmez. Müşteri dağılımı: [config.md](config.md#müşteri-configleri--yapısal-farklar).

## Fiktif enstrüman (endeks) ayarları

İki ayrı okuma vardır:

1. **`itch.Manager.createIndices`** (bootstrap). Endeks enstrümanlarını bellekte oluşturur (`NewIndexFromFictiveInstrumentSetting`). Ağırlık dosyasıyla hisseleri endekslere bağlar:
   - `TopIndice` önceliği: XU030 > XU050 > XU100.
   - `SectorIndice`: yalnız top endeksi XU030 olan hisseler için, XU500 hariç, `WeightingFactor × WeightPercentage` en büyük olan endeks.
   - **Pazar ataması** buradan çıkar: `XYLDZ` → Primary (Yıldız), `XBANA` → Secondary (Ana), diğer paylar → Other (`setInstrumentBazaars`). `instrumentBazaarsPath` config'i bu işte kullanılmaz (bkz. [config.md](config.md)).
2. **`AlgoApi.UpdateFictiveInstrumentSettings` / `UpdateFictiveItemSettings`** (`main.go`, kodda `// DEPRECATED` ve `// to be removed`). Config yollarındaki dosyayı okuyup paket seviyesindeki değişkenlere koyar. `AlgoService.GetFictiveInstrumentSettings` / `GetFictiveItemSettings` buradan döner (AlgoProd okur: [algorithmic-trading](../algorithmic-trading/README.md)).

**Dosya formatı:**
- `;` ayraçlı. İlk iki satır başlıktır (TR + EN).
- Tanım dosyası alanları: `[1]` bölen, `[2]` kapanış, `[3]` düzeltme, `[4]` kod, `[5]` uzun ad, `[7]` kur, `[8]` ISIN, `[9]` FDP katsayılı piyasa değeri.
- Tanım dosyasında `XU100_`, `XU050_`, `XU030_` önekli varyantlar (USD vb.) atlanır.
- DB'de olmayan yeni endekse `max(DB endeks id) + 1` id verilir (`getIndiceId`).
- Satırlar önce `encoding/csv` ile `,` ayracına göre okunur, sonra `fields[0]` `;` ile bölünür. ❓ doğrulanmadı: alan içinde virgül olan satırlar bölünür mü?

**Hata:** `UpdateFictive*` içindeki parse hatası `log.Fatalf` çağırır → **process exit 1**. `main.go`'daki "Aborting startup" dalına hiç ulaşılmaz. `createIndices` içindeki hata ise yalnızca loglanıp fonksiyondan çıkılır.

## AKD (aracı kurum dağılımı, Foreks)

**Ön koşul:** `akd.isEnabled` **ve** `historyManager != nil`. Yani `itchEnabled=true` ve `historyManagerEnabled=true` olmalıdır (`main.go`). Aksi halde:
- `FetchAkd`, `GetBrokerageFirmList` ve `SubscribeBrokarageResults` "akd is disabled" döner.
- `UnsubscribeBrokerageSide` ise nil manager üzerinden çağrı yapar → bkz. açık sorunlar.

**Kurulum** (`NewAkdManager`):
- `akd.bist30InstrumentId` id'li endeks bellekten alınır. Bulunamazsa `nil` döner.
- Endeksin her bileşeni için `InstrumentScoreCalculator` kurulur. Bileşenin ağırlık, toplam pay ve fiili dolaşım oranı ağırlık dosyasından gelir.
- Endeks için bir `IndexScoreCalculator` kurulur.

**Dış çağrılar** (`extdata.ExecuteRequest`, Basic Auth, timeout yok, HTTP status kontrolü yok):
- Dağılım: `GET {akdUrl}/code/{SYMBOL}.{BIST|VIOP}/type/{E|VIOP}/from/{yyyyMMdd}/to/{yyyyMMdd}` (bugün). Yanıt dizisinin `[0]` elemanı alınır.
- Kurum listesi: `GET {bistInstUrl}/search?status=ACTIVE&type=A`. `MemberInfo.Code` ← JSON `name`, `Name` ← `legacyCode`. ❓ doğrulanmadı: alanlar ters mi eşlenmiş, yoksa kasıtlı mı?

**Döngü** (`workAsync`, `time.Tick(1 dk)`):
1. `checkBrokerageFirmActivities`: abone olunan her enstrüman için AKD çeker ve kriterleri değerlendirir. Seans kontrolü yoktur, her dakika çalışır. Yeni abonelikte de (1 sn bekleyip) hemen çalışır.
2. BIST30 endeksi sürekli işlem seansında değilse skor hesabı atlanır.
3. `calculateScores`: her bileşen için AKD çekilir, `updateInstrumentDistribution` çalışır (pubsub ile `FetchAkd` abonelerine yayın), sonra `calculateScore`. En sonda endeks skoru hesaplanır.

### Dağılım istatistikleri (`instrument_distribution.go`, `calculation_parameters.go`)

- Kurumlar `NetAmount`'a göre azalan sıralanır.
- `getNetSum(Buy)`: baştan, `NetAmount ≥ 0` olan kurumlar alınır. İlk `breakLevel=5` kurum **top**, kalanlar **others** grubuna girer.
- `getNetSum(Sell)`: sondan, `NetAmount ≤ 0` olan kurumlar aynı şekilde ayrılır. Sonuç mutlak değerdir.
- **`TradeRatio` (log'da "DSDA") = SellSum / BuySum.** `BuySum < 0.1` ise −1 olur.
- `DiffRatio`: 5 dk önceki AKD kaydında (aynı dakika anahtarı) eski `SellSum / BuySum`. Kayıt yoksa 0.
- `TimeBased` tablosundan son 5 adet 1 dk mum alınır ([History](#history-timebased-ve-volatility)):
  - `BuyQuantity`, `SellQuantity`, `TotalBuyVolume`, `TotalSellVolume` 5 dakikanın toplamıdır.
  - `PreviousBuy/SellQuantity` = `data[1]` mumu.
- Endeks fiyatları: top endeks, sektör endeksi ve en yakın vadeli kontrat için son 5 dk kapanışları `historicalIndexPrices[0..4]`'te tutulur.
  - `IndexPreviousPrice` = `[4]`. Kodda "1 dakika önce" diye geçen karşılaştırmalar `[1]`'i kullanır.
  - ❓ doğrulanmadı: `TimeBased` sorgusunun sıralaması (yeni→eski varsayımı).
- `indexPricesAverage = (IndexLast + SectorIndexLast) / 2`.

### Hisse skoru (`InstrumentScoreCalculator.calculateScore`)

Skorlar **others** grubu (ilk 5 kurum hariç) parametreleriyle hesaplanır. Top grubu parametreleri endeks skoruna aktarılır.

Atlama koşulları: `others.TradeRatio < 0.00001` (−1 dahil) veya `IndexPreviousPrice < 0.00001` → skor yazılmaz.

Sabitler: `tradeCoefficient=1.4`, `volumeTotalNeeded=100000`, `quantityRatio=110` (→ 1.10), `quantityWeaknessRatio=10` (→ 1.00 eşiği). Aşağıda `TR`=TradeRatio, `avg`=indexPricesAverage, `avg5`=5 dk önceki ortalama, `avg1`=`[1]` ortalaması.

| Kural | OpenBuy | OpenSell | CloseBuy | CloseSell |
|-------|---------|----------|----------|-----------|
| TR eşiği | TR > 1.4 → +30 | TR < 1/1.4 → −30 | TR > 1/1.4 → +20 | TR < 1.4 → −20 |
| Son fiyat vs açılış | Last > Open → +15 | Last < Open → −15 | — | — |
| Günlük değişim vs endeks | hisse > endeks → +10 | hisse < endeks → −10 | — | — |
| TR vs DiffRatio (DiffRatio>0) | TR > Diff → +20 | TR < Diff → −20 | TR > Diff → +10 | TR < Diff → −10 |
| Hacim ≥ 100000 ve miktar oranı | Sell/Buy qty ≥ 1.10 → +30 | Buy/Sell qty ≥ 1.10 → −30 | Buy/Sell qty < 1.00 → +15 | Sell/Buy qty < 1.00 → −15 |
| 5 dk endeks (`avg` vs `avg5`) | > ×1.003 → +20; < ×0.993 → −20 | < ×0.997 → −20; > ×1.007 → +20 | > ×1.007 → +20 | < ×0.993 → −20 |
| Önceki dakika miktar oranı | prevSell/Buy ≥ 1.10 → +15; < 1.00 → −15 | prevBuy/Sell ≥ 1.10 → −15; < 1.00 → +15 | prevBuy/Sell < 1.00 → +15 | prevSell/Buy < 1.00 → −15 |
| 1 dk endeks (`avg` vs `avg1`) | ≥ ×1.003 → +20; < ×0.991 → −20 | ≤ ×0.997 → −20; > ×1.009 → +20 | ≥ ×1.009 → +20 | < ×0.991 → −20 |

Her skorla birlikte şunlar yazılır:
- `DsDaScore = round(TR, 2)`.
- `IsProperBuy`: şu durumlarda false olur:
  - endeks yükselirken TR > 1.4 ve Last < Open,
  - `avg ≤ avg1×0.991`,
  - `avg ≤ avg5×0.984`,
  - BestBid ≥ gün yükseği.
- `IsProperSell`: simetrik koşullar (×1.009, ×1.016, BestAsk ≤ gün düşüğü).
- `IsTired`: daima false.

Log mesajlarındaki yüzdeler ("0.003%") çarpanla uyuşmaz. ×1.003 = %0.3'tür.

### Endeks skoru (`IndexScoreCalculator`)

- Girdi: her bileşenin **top** grubu parametreleri (`calcParamsTop`). Yalnızca `SellQuantity > 0` olan bileşenler katılır.
  - `TR = Σ(SellSum×Weight) / Σ(BuySum×Weight)`.
  - Hacimler ağırlıklı toplamdır, miktarlar düz toplamdır. `PreviousBuy/SellQuantity` bir önceki dakikanın toplamıdır.
  - `IndexPreviousPrice` = ilk bileşenin değeri (map iterasyon sırası).
- Son 5 hesap halka tamponda tutulur. "n dakika önceki" değer en eski kayıttır.

| Kural | OpenBuy | OpenSell | CloseBuy | CloseSell |
|-------|---------|----------|----------|-----------|
| TR | > 1.4 → +30 | < 1/1.4 → −30 | > 1/1.4 → +20 | < 1/1.4 → −20 |
| Last vs Open | > → +20 | < → −20 | — | — |
| Last vs IndexPrevious | > ×1.0003 → +20 | < ×0.9993 → −20 | — | — |
| TR vs n dk önceki TR | > → +20 | < → −20 | — | — |
| Last vs n dk önceki Last | > ×1.0003 → +20; < ×0.9993 → −20 | < ×0.9993 → +20; > ×0.9993 → +20 (**iki dal da +20**, bkz. açık sorunlar) | — | — |
| Hacim oranı (Sell/Buy vol) | > 1.00 → +30 | < 1.00 → −30 | — | — |
| Önceki qty oranı (prevSell/Buy) | — | — | < 1.00 → +15 | < 1.00 → −15 |

Endeks skoru `Scores`'a iki kez yazılır: endeksin kendi id'si ve en yakın vadeli kontrat (`IndiceFuture`) id'si.

**Yazım:** `Scores` tablosuna `INSERT ... ON DUPLICATE KEY UPDATE` yapılır (anahtar: [sema.md](sema.md)). 4 karar tipi vardır: `Buy`, `Sell`, `CloseBuy`, `CloseSell`.

**Tüketiciler:**
- `AlgoService.GetInstrumentScores` → AlgoProd `TradeByBSRatio` (strateji tipi 3, "AKD") ve `WarrantUnderlyingTracker`.
- `FetchAkd` (stream, ham dağılım) ve `SubscribeBrokarageResults` (kurum kriteri) → AlgoProd VWAP AKD filtresi ([vwap.md](../../20-stratejiler/vwap.md#akd-aracı-kurum-dağılımı-filtresi)).

### Kurum kriteri (`brokarage_instrument.go` `checkCriterias`)

- Her abonelik anahtarı (`BrokerageReqKey`) için taraf başına bir kriter tutulur: kurum kodları, `net_percentage`, `quantity`.
- Kurumun payı `NetAmount×100 / GrandNetAmount`. İşaret kurumun tarafını belirler (+ alış, − satış).
- Strateji yönüyle **aynı** taraf: listedeki kurumların toplam |pay| ≥ yüzde ve toplam |NetAmount| ≥ `quantity` olmalı.
- **Karşı** taraf: son kuruma gelindiğinde toplam ≤ yüzde ve (≤ `quantity` veya `quantity=0`) olmalı.
- `quantity` lot değil, `NetAmount` (tutar) ile karşılaştırılır. ❓ doğrulanmadı: UI'daki "Lot" alanının (`Broker_Lot_*`) anlamıyla örtüşüyor mu?
- Tüm taraflar sağlanınca durum true olur; durum değişince `BrokerageInstrumentResponse` yayınlanır.
- `ReceiveBrokerageFirmResults` her 500 ms'de abonelik kanallarını tarar ve ilgili stream'e `FetchBrokarageResponse` gönderir.

**Hata:**
- AKD isteği hata verirse o enstrüman o dakika atlanır.
- Boş dizi yanıtı `[0]` indeksinde goroutine içinde **panic** eder ve process çöker.
- HTTP timeout yoktur. Takılan istek `WaitGroup`'u, dolayısıyla tüm dakikalık döngüyü bloklar.

## BYF (Fon Takibi sepeti)

**Ne zaman:** Yalnız açılışta, `byf.enabled=true` ise (`main.go` → `AlgoApi.UpdateBYFSettings`). Gün içinde yenilenmez.

**Akış:**
1. `Helper.DownloadByfFile`: `http.Get(byfFileUrl)` ile indirilir, çalışma dizininde `byfFileName` adıyla kaydedilir.
2. `util.ReadByfFile`:
   - `isHtmlBased=true` ise `.xls` uzantılı ama HTML tablolu dosya `goquery` ile okunur (`table tr` → `th, td`).
   - Değilse `excelize` ile `byfSheetIndex` sayfası okunur.
   - Fon başlık bilgileri `byfInfoColumnName` kolonundan, `rowIndexes.*` satırlarından alınır. Sayılarda `,` → `.` dönüşümü yapılır.
   - Sepet satırları `byfInstrumentsStart`'tan başlar, `NoOfStocks` satır sürer. Kolonlar: `0` id, `1` sembol, `2` ISIN, `3` ad, `4` gerekli lot, `5` kapanış (TL), `6` toplam değer, `7` ağırlık, `9` sektör.
3. Sonuç bellekte tutulur. `AlgoService.GetByfSettings` döner. Tüketici AlgoProd Fon Takibi: [fon-takibi.md](../../20-stratejiler/fon-takibi.md).
   - Çelişki: [fon-takibi.md](../../20-stratejiler/fon-takibi.md) "sepeti DB'ye yazar" diyor; kod sepeti yalnız bellekte tutar, DB'ye yazmaz.

**Hata:**
- İndirmede ağ hatası `panic` olur. Non-200 yanıtta yalnızca loglanır ve gövde yine dosyaya yazılır.
- Ayrıştırma hatasında `main` döner → process çıkar (gRPC açılmaz).

## History (TimeBased) ve Volatility

**Ön koşul:** `itchEnabled=true` ve `historyManagerEnabled=true`. ITCH snapshot'ından sonra başlar.

**`pricedata` + `history.CandleStickManager`:**
- ITCH trade feed'ine abone olur (`SubscribeToTrade`).
- Her trade için enstrüman başına dakika, saat ve gün mumu günceller: Open/Close/High/Low, toplam/alış/satış miktar ve hacim.
- Fiyatlar ITCH raw ölçeğindedir. Hacim = `quantity × raw price`.
- Dakika değiştiğinde değişen mumları `TimeBased` tablosuna `InsertTimeBasedTradeData` ile yazar. Hata olursa tüm mumlar yeniden "kaydedilmedi" işaretlenir ve bir sonraki dakikada tekrar denenir.

**`history.Manager`:**
- `GetDataWithOptions` blokları birleştirir (`mergeBlocks`).
- `FetchHistoricalData` RPC'si (AlgoProd) ve AKD skor hesabı bunu kullanır.
- `GetTimeBasedData` RPC'si ise tabloyu doğrudan okur. History kapalıysa tablo dolmaz.

**`volatility`:**
- Fiyat değişimine abone olur. Varant volatilitesi hesabı (Black-Scholes, Newton iterasyonu, `interestRate`) **yorum satırına alınmış** (`TODO: Calculate volatility removed`).
- Yayıncı hiç yayın yapmadığı için `Volatility` tablosuna fiilen veri yazılmaz.

## Limits (`pkg/limits`)

- Singleton `LimitsManager`. Kalıcılık yoktur, process ömrü boyunca bellekte tutar.
- `LimitControlService`:
  - `SetCustomerLimits`: müşteri TL toplamı, yasaklı mı, Ana/Yıldız/Diğer pazar TL limitleri, hisse bazlı miktarlar.
  - `SetStockLimits`: hisse bazlı `DEPO`/`BRUT`/`SHORT` kısıtı, pazar kısıtları, varsayılan açığa satış kısıtı.
  - `SetIntraDayCustomerLimits` (bidi stream): gün içi işlemler.
- `RiskManagerService`:
  - `GetCustomerLimits`, `GetStockLimits`.
  - `GetIntraDayCustomerLimits`: stream; gün içi işlemleri tamponsuz `ClientSrvChan` kanalından iletir.
- ❓ doğrulanmadı: `LimitControlService`'i besleyen istemci hangisi? order-service değil: yalnız `RiskManagerService` istemcisi var, `limit_control.proto`'yu yalnız `StockLimitType` enum'u için derliyor ([order-service/risk](../order-service/risk.md)). (K-43)
- Tamponsuz kanal yüzünden okuyucu (`GetIntraDayCustomerLimits` aboneliği) yoksa `SetIntraDayCustomerLimits` ilk mesajda bloklanır.

## AWS (`pkg/util/aws_client.go`)

- `NewAwsClient` açılışta `main` içinde çağrılır. **`AWS_ACCESS_KEY_ID` ve `AWS_SECRET_ACCESS_KEY` env'leri yoksa `log.Fatal` → process açılmaz.**
- SMS OTP: SNS, bölge `eu-west-2` sabit kodlu. Mesaj: `mTrader Giriş Kodunuz: <kod>`.
- Şifre sıfırlama e-postası: SES.
  - Bölge `AWS_REGION` env'inden alınır.
  - Gönderen adres sabit kodludur.
  - Link: `{gui.hostname}/passwordReset/{user}/{token}`.
- **SES oturum veya gönderim hatası `log.Fatal` çağırır → tüm process çöker** (bkz. açık sorunlar).

## Varant dosyası parser'ı (`POST /v1/parseWarrantFile`)

`GuiParseWarrantFile` (`warrant_api.go`) + `util.ParseWarrantFile`. Kotasyoncu programının dosyasını HFT Varant Toplu listesine çevirir. Strateji tarafı: [varant.md](../../20-stratejiler/varant.md).

**Format algılama:**
- `.xlsx`, `.xlsm`, `.xls` → excelize (ilk sayfa). ❓ doğrulanmadı: eski ikili `.xls` excelize ile açılamaz; o durumda "excel dosyasi acilamadi" döner.
- Diğer uzantılar ayraçlı metin olarak okunur. Ayraç ilk satırdan seçilir: `\t ; , |` içinden en çok geçen.

**Başlıklar:**
- Normalize edilerek eşlenir: küçük harf, Türkçe karakter yok, boşluk yok. Örn. `Varant Kodu`, `Dayanak Varlık`, `Kotasyon Miktarı`, `Kullanım Fiyatı`, `Vade Sonu`, `Vadeye Kalan Gün`.
- `symbol`, `underlying` ve `quotationlot` kolonları zorunludur.

**Sayı ayrıştırma:**
- Lot: `.` ve `,` binlik ayracı sayılır. Tek nokta ve 3'ten farklı kesir hanesi varsa kesir atılır.
- Kullanım fiyatı: iki ayraç birden varsa sonuncusu ondalıktır.

**Çözümleme:**
- Dosyada tek dayanak olmalı.
- Dayanak önce birebir aranır, bulunamazsa `.E` ekiyle aranır.
- Varant önce dayanağın varant listesinde, sonra genel sembol aramasında aranır.
- `prevClose = LastPrice / 10^DecimalPrice` (TL).
- Tekrar eden semboller atlanır. Lot 0 olan satır uyarı üretir.

**Çıktı:** `WarrantListJson`. Alanlar HFT `HftWarrantAdvancedCommand::parseWarrantsFromJson` ile birebir aynıdır; `quotationLotOp="eq"`. DB'ye yazılmaz.

## Arbitraj Excel (`util/arbitrage_excel_parser.go`, `_generator.go`)

- `uploadArbitrageExcel` (parse) ve `downloadArbitrageExcel` (generate) uçlarının iç kütüphanesidir.
- Üç sayfa: paneller, stratejiler, paketler. Hiyerarşi kurulur ve doğrulanır.
- Ayrıntı bu dosyanın kapsamı dışında: [api.md](api.md), [arbitraj.md](../../20-stratejiler/arbitraj.md).

## Request log (`pkg/requestlog`, `cmd/requestlog-report`)

**Ne yapar:** Kullanıcının elle tetiklediği çağrıları günlük JSON-lines dosyasına yazar: `<log-path>/requests/requests-YYYY-MM-DD.jsonl`.
- İzlenen metotlar sabit listededir (`trackedMethods`): GUI login/OTP/şifre, `GuiSendOrders`, `GuiStrategySetCommands`, `GuiSetAccountStrategy`, `GuiSetPanel`, `GuiUploadArbitrageExcel`, Admin kullanıcı/hesap/izin CRUD'u.
- Okuma ve abonelik çağrıları yazılmaz.

**Kayıt alanları:**
- `time`, `ip`/`port`, `target_ip`/`target_port`, `forwarded_for`, `user`, `method`, `code`, `error`, `duration_ms`, `user_agent`.
- `request`: protojson. 64 KB üstü kayıtlar `{"truncated":true}` olur.
- Maskeleme: anahtar adında `password` geçen alanlar ile `resettoken` ve `otpcode` → `***`.
- `session_id`: `authorization` token'ının (yoksa yanıttaki `token` alanının) SHA-256'sının ilk 16 hex hanesi.
- `instruments`: istekteki `orderbookId`'ler ITCH'ten sembol ve `price_divider` ile çözülür.

**İstemci IP'si:**
- REST gateway `GatewayMetadata` ile metadata'ya `x-client-ip` vb. koyar.
- Uzak adres güvenilir proxy ise (loopback daima güvenilir, ek olarak `requestLog.trustedProxies`) `X-Real-IP`/`X-Real-Port` ve `X-Server-Addr`/`X-Server-Port` başlıkları kullanılır.
- `target_ip`/`target_port` config/env ile sabitlenebilir ([config.md](config.md#requestlog-ve-env-overrideları)).

**Hata:**
- Kuyruk 4096 kayıttır. Doluysa kayıt stdout log'una düşer.
- Dosya açma veya yazma hatası loglanır, kayıt log satırında kalır.
- `Start` hatası (dizin, geçersiz proxy CIDR) request log'u kapatır; servis çalışmaya devam eder.

**`cmd/requestlog-report`:**
- Bir günün dosyasından `GuiSendOrders` emirlerini Excel'e döker. Varsayılan çıktı `emir-ip-raporu-<date>.xlsx`, aracı kurumun emir-IP raporu kolonlarıyla.
- Bayraklar: `-dir`, `-date` (YYYY-MM-DD), `-file`, `-out`.
- Fiyat `price_divider` ile TL'ye bölünür. Sembol çözülemediyse raw fiyat yazılır.

## Açık sorunlar / şüpheli davranışlar

Hepsi aday; kullanıcı onayı yok. "Bug" etiketi kodun açık niyetiyle çeliştiği yerlerde kullanıldı.

- **ITCH partition 5+ desteklenmiyor:** `itch.go`'daki `Part` switch'i yalnız 1–4'ü eşler. 5 ve 6 uyarıyla `Partition1`'e düşer; SDK `enums.h` ise `Partition10`'a kadar tanımlar. VİOP 6 tanımlayan config'te 5. ve 6. partition yanlış eşlenir ([config.md](config.md#müşteri-configleri--yapısal-farklar)).
- **VERDA `filesMap` boşken panic:** `GetAllFiles` hatası loglanıp geçiliyor, sonra `Links[0]` nil slice'a indeksleniyor.
- **VERDA ilk veri satırı atlanıyor olabilir:** `parseBulletin` ve `parseMorningMarginInfo` başlığı hem `reader.Read()` ile hem `rowIndex==0` ile atlıyor. ❓ doğrulanmadı: dosyada iki başlık satırı var mı?
- **VERDA `lastPrice=0` riski:** Marj dosyasında olup bültende olmayan sembolde `ClosingPrice=0` olur ve `Instrument.lastPrice` 0 yazılır.
- **`isBrutTakas` ayrıştırma:** `strconv.ParseBool` yalnızca `1/t/true/...` değerlerini kabul eder. Dosya başka gösterim kullanıyorsa hep false olur. ❓ doğrulanmadı.
- **AKD nil manager:** Endeks bulunamazsa `NewAkdManager` nil döner ve `main` `akdManager.Start()` çağırır → panic. `UnsubscribeBrokerageSide` AKD kapalıyken nil manager'ı çağırır.
- **AKD boş yanıt:** Boş dizi `[0]` ile indekslenir → goroutine panic → process çöker.
- **Endeks OpenSell skoru (bug):** "n dk önceki Last" kuralının iki dalı da +20 ekler.
- **Endeks skoru `IndiceFuture` nil ise panic** (`writeToDatabase`).
- **`ReceiveBrokerageFirmResults` iki kez başlatılıyor** (AKD açıkken). Mutex tutulurken blocking `Send` yapılıyor. `brokerageFirmsNotifier` map'i kilitsiz eşzamanlı erişiliyor.
- **History busy-loop:** `history.Manager.workAsync` uyku olmadan döner; kanal boşken bir CPU çekirdeğini sürekli meşgul eder.
- **History birleştirme:** `updateTimestampForBlock`'ta `time.Add` sonucu atılıyor (no-op). `addData` `Low`'u `data.High` ile karşılaştırıyor (bug). `mergeBlocks` sonuç dilimini kırpmıyor; birleşen blok kadar sıfır kayıt sonda kalıyor.
- **SES hatasında `log.Fatal`:** Tek bir şifre sıfırlama e-postası hatası tüm servisi düşürür.
- **Açılış iptalleri exit 0:** BYF, VERDA ve `isBrutTakas` hataları `main`'den `return` ile çıkar, yani exit code 0. ❓ doğrulanmadı: restart politikası `on-failure` ise servis yeniden başlamaz.
- **BYF indirmesi panic:** Ağ hatasında `panic`. Non-200 yanıtta hata sayfası ayrıştırılıyor.
- **Dış HTTP istemcilerinde timeout yok:** VERDA, AKD ve BYF (Datastore'da 60 sn var).
- **`LimitControlService.LimitLogin` şifreyi düz metin logluyor.**
