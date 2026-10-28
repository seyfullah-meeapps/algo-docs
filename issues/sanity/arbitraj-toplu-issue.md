---
kapsam: Arbitraj sanity testleri ve kaynak incelemesindeki açık bulguların toplu issue açıklaması
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading
    branch: master
    commit: aa150ee
  - repo: order-service
    branch: development
    commit: 26e9a02
  - repo: order-service
    branch: master
    commit: 298403b
  - repo: Algo-Setup
    branch: development
    commit: cade7d0
dogrulama: 2026-10-26
durum: taslak
---

# Arbitraj: ayar, emir ve hesaplama akışlarında tespit edilen uyumsuzluklar

Bu kayıt yeni arayüz (`mtrader-trade-ui`, `development`) kapsamındaki Arbitraj sanity testlerinde ve kaynak incelemesinde bulunan açık noktaları bir araya getirir. Kullanıcının test gözlemleri ile kod incelemesi bulguları ilgili bölümde ayrılır. Bu metin güncellenirken yeni uygulama testi veya canlı emir denemesi yapılmadı. Olası etkiler, gerçekleşmiş test sonuçları olarak değerlendirilmemelidir. Ürün davranışı veya çalışan ortam bilinmeden kesin hata olarak sınıflandırılamayan noktalar ayrıca belirtilmiştir.

Bu dosya açık Arbitraj sorunlarının takip adresidir. Bölümlerdeki P/TC-ARB kimlikleri kaynak incelemesini eşleştiren sabit kimliklerdir; güncel Excel’de karşılık gelen bir sorun satırı bulunduğu anlamına gelmez. [Aktif Excel](../../testler/sanity/MTrader_Arbitraj_Sanity_Test.xlsx) yalnız kullanıcı testlerini ve ayar rehberini içerir. Eksik test adımları tek başına hata olarak eklenmemiştir.

Son üç sorunun kodla doğrulanan uyumsuzlukları **3. Spread Otomatik**, **5. temettü ölçeği** ve **8. durdurmada dayanak iptali** bölümlerindedir; mevcut K-205 kapsamındadır. Durdurmada bütün bekleyen emirlerin iptali ürün beklentisi olarak nettir. Spread Otomatik'in yön/eşik sözleşmesi ve temettünün ortak birimi ise düzeltmede netleştirilmelidir; mevcut kod tutarlı bir davranış sağlamıyor.

Bu üç konu için kaynak kapsamı: AlgorithmicTrading development `0dc32a7`, master `aa150ee`; yeni GUI development `117bc34` (ilgili dosyalar `b0474c3` ile aynı); eski GUI main `6715182`; trade-data-app development `1cca9a8`. Diğer bölümlerin kaynak tabanı frontmatter'dadır. Ayrıntılı kanıt [teknik incelemede](../../bilgi-tabani/test-incelemeleri/arbitraj-inceleme-2026-10-26.md) bulunur. Bu kayıtlar müşteri ortamında yeniden üretim veya düzeltme doğrulaması değildir.

Arbitrajın 30 günlük temizlikte veri kaybı konusu ayrı [K-263 issue dosyasında](../arbitraj-30-gunluk-temizlik-veri-kaybi.md) tutulur; burada tekrar edilmez.

## 3. Spread Arbitraj'da Otomatik yön ve kademe alanlarının uyumsuzluğu

**İlgili alan:** Frontend ve motor.  
**İnceleme kimliği:** P32, P15; TC-ARB-R01.

Arayüz Otomatik yön seçeneğini `Fs_Arbitrage_Side=79` olarak sunuyor. Motorun yön enum'u ise yalnız `Above=65` ve `Below=66` değerlerini tanıyor. `checkOpenable`, gelen `79` değerini ayrıca ele almadan yön değişkenine atıyor; fiyat ve koşul kontrolleri bu tanımsız değerle farklı `if/else` dallarına giriyor.

Ayrıca GUI Otomatik seçiliyken kademe girişlerini `Open_Tick` ve `Close_Tick` alanlarına bağlıyor. Gönderilen Spread komut türü `F` olarak kalıyor; motor bu türde `Fs_Open_Tick` ve `Fs_Close_Tick` alanlarını kullanıyor.

Böylece kullanıcının seçtiği Otomatik davranış ile motorun yön/eşik hesabı arasında uyumsuzluk oluşuyor. Görünür alana girilen kademe, motorun işlemde kullandığı eşik olmayabilir; motor görünmeyen alanın mevcut veya varsayılan değerini kullanabilir. Yön seçimi ve emir fiyatı etkilenebilir. Koddan “her zaman alım yapar” veya “her zaman satım yapar” sonucu çıkarılmamıştır. Motorun ayrı D türündeki otomatik teorik fark yönü, GUI’nin gönderdiği F türünün yerine kendiliğinden kullanılmaz.

Motorun `D/DiffTick` türü teorik farkın mutlak büyüklüğünü açılış eşiğiyle karşılaştırır; farkın işareti Above/Below yönünü seçer. `F` türü ise vadeli–dayanak fiyat farkını kullanır. Bu nedenle yalnız komut türünü F'den D'ye çevirmek eşdeğer bir düzeltme kabul edilemez. Kademe alanı uyuşmazlığı özellikle tekil ayar formundadır; toplu ayarın birden fazla kademe alanını birlikte yazması bu sözleşme hatasını ortadan kaldırmaz.

**Kod noktaları (repo → dosya → sembol):**

- `mtrader-trade-ui/app/components/modals/arbitrageSettings/fields.ts` → `SIDE_OPTIONS`; aynı klasörde `sections.tsx` → `SpreadFields`.
- `mtrader-trade-ui/app/components/dockview/arbitrage/arbitrageSettingsPayload.ts` → `getArbitrageCommandTypeCode`, `Fs_Arbitrage_Side` ve kademe alanlarının aktarımı.
- `AlgorithmicTrading/algoSrc/Globals/Enumarations.h` → `ArbitrageSide`, `ArbitrageStrategyType`.
- `AlgorithmicTrading/algoSrc/Strategy/Arbitrage/ArbitrageTracker.cpp` → `checkOpenable`, `checkParameters`, `updateArbitrageState`, `calculateWantedPriceOpen/Close`, `openPosition`, `openPassivePosition`.

## 4. Başlangıç ve bitiş saatlerinin farklı dönüşümlerle karşılaştırılması

**İlgili alan:** Motor ve çalışma ortamının saat dilimi.  
**İnceleme kimliği:** P19; TC-ARB-R02.

GUI başlangıç/bitiş saatlerini gece yarısından itibaren saniye olarak gönderiyor. Motor `isOpenSession` içinde başlangıç saatinden 3 saat, Çift Vade türlerinde 3,5 saat çıkarıyor. Bitiş saatinde aynı dönüşüm yapılmıyor. Karşılaştırılan güncel saat `TimeUtility::calcSecondsFromMidnight` tarafından yerel saatle hesaplanıyor.

Algo-Setup temel imajında `TZ=Europe/Istanbul` tanımlı. Çalışan container'ın gerçek saat dilimi bu incelemede okunmadı. Yerel saat İstanbul olduğunda bu başlangıç hesabı, stratejinin seçilen saatten önce işlem aramasına izin verebilir; emir gönderimi diğer seans ve strateji koşullarına da bağlıdır.

Olası etki, kullanıcının belirlediği çalışma aralığı ile motorun uyguladığı aralığın ayrışmasıdır. Etkinin çalışan ortamda kaç saat olduğu container saatine bağlıdır.

İstanbul saatli ortam örneği: 14.00 başlangıcı normal türlerde 11.00, Çift Vade türlerinde 10.30 eşiğine dönüşür; seans ve diğer koşullar uygunsa erken emir oluşabilir. Frontend'de başlangıcın bitişten sonra olmasını engellemek bu motor hesabını düzeltmez.

Bitişte `doPeriodicChecks → isOpenSession → stop → exitProperly` yolu vardır; kontrol bitiş saatine eşit veya sonrasındaki turda işlem döngüsünü keser. Bitiş aynı yerel saatle, kaydırmasız karşılaştırılır. Kontrol öncesinde başlamış döngü/emir isteği için tam saniyede kesinti garantisi yoktur. Bekleyen dayanak emirlerinin iptal edilmemesi 8. bölümdeki ayrı sorundur. Ayrıca başlangıç eşiği geçildiğinde enstrümanlardan birinin seansı kapalıysa motor beklemek yerine durur. Ayrıntılı çağrı sırası ve kaynak kapsamı [başlangıç ve durdurma incelemesindedir](../../bilgi-tabani/test-incelemeleri/arbitraj-inceleme-2026-10-26.md#başlangıç-ve-durdurma-politikası).


**Kod noktaları:** `buildArbitrageSettingsPayload` → `Start_Time`/`Stop_Time`; `ArbitrageTracker::isOpenSession`; `TimeUtility::calcSecondsFromMidnight`; Algo-Setup `MAProdEnv/Dockerfile`, `MAAlgoProd/Dockerfile`.

## 5. Temettü değerinin fiyat ve yön hesaplarında farklı ölçekle kullanılması

**İlgili alan:** Motor hesapları ve frontend alanının birimi.  
**İnceleme kimliği:** P05; TC-ARB-R07.

Motor, Faiz ve Çift Vade Faiz türlerinin emir fiyatı hesaplarında `Dividend_Prc` değerini `100`'e bölerek çıkarıyor. Yön/kârlılık değerlendirmesinde kullanılan `updateArbitrageState` ise aynı değeri doğrudan çıkarıyor. GUI alanında birim açıklaması bulunmuyor; eski/yeni GUI sayıyı ölçeklemeden Double gönderiyor. 250 girişi emir fiyatında 2,50 TL, yön/fark hesabında 250 TL düzeltme yapar; 2,50 girişi ise sırasıyla 0,025 TL ve 2,50 TL etki yapar (fiyat-adımı yuvarlaması öncesi). Bu alan yüzde hesabı olarak tüketilmiyor; tek bir tutarlı giriş birimi mevcut değil.

Bu nedenle sıfırdan farklı temettüde, emir fiyatını kuran hesap ile yön değerlendirmesi aynı temettü düzeltmesini farklı büyüklükte uyguluyor. Bu fark, yön/kârlılık kararının emir fiyatıyla tutarsızlaşmasına neden olabilir. Sorun yalnız arayüzün göndermediği Oto-Spread türüyle sınırlı değildir; kullanılan faiz türlerinin hesap yollarında da görülüyor.

**Geliştirme iddiasının yeniden kontrolü — 2026-10-28:** Temettü desteği için gerçek geliştirmeler vardır; kayıt “temettü hiç uygulanmıyor” anlamına gelmez. Motor, GUI ve trade-data-app uzak referansları fetch ile güncellendi. Motor development `0dc32a7`, preprod `b776d49`, master `aa150ee`, yeni `add-order-sdk` dalı `f119ad3`; GUI development `117bc34`, `feat/new-gui-updates` `6958374`; veri servisi development `1cca9a8` incelendi. Uygulama kaynakları değiştirilmedi.

| Bulunan geliştirme | Doğrulanan kapsam | Bu kayıttaki ölçek ayrımını gideriyor mu? |
|---|---|---|
| Motor `28c3e1a` / `ea10e43`, 30 Mart 2023 | DiffTick türünün pasif açılış fiyatına temettü eklenmesi; son durumda iki yönde de ham temettü çıkarılır | Hayır; Faiz türlerindeki `/100` ile ortak birim sağlamaz |
| Motor `f0c3b12`, 18 Şubat 2025, `arbitrage fixes` | Faiz türünün açılış/kapanış fiyatına `dividendPrc / 100.0` düşümü eklenmiş | Emir fiyatı desteği var; `updateArbitrageState` ham kullanımını değiştirmiyor |
| Motor `0468428`, 12 Mart 2025, `added margin diffs for packages` | Çift Vade Faiz açılış/kapanış fiyatına aynı `/100.0` düşümü eklenmiş | Aynı sınırlama geçerli |
| Yeni GUI `arbitrageMetrics.ts`, development ve yeni GUI geliştirme dalı | Faiz satırının açılış değeri hesabı temettüyü kuruş kabul edip referans fiyat ölçeğine çevirir: `Dividend_Prc × (1000 / 100)` | GUI hesabıdır; motorun yön hesabını veya gönderilen ayarı değiştirmez |

2025'teki iki motor geliştirmesi development, preprod, master ve `add-order-sdk` dallarında bulunur; yalnız eski veya birleşmemiş dalda kalmış değildir. Motorun bütün 40 uzak dal ucunda `ArbitrageTracker.cpp` temettü satırları karşılaştırıldı (ayrıca origin HEAD sembolik referansı okundu). Faiz yollarını içeren 38 dalda sekiz `/100` kullanımı ile yön hesabındaki ham kullanım birlikte bulunur; iki eski dal Faiz temettü yollarını içermez. Bu tarama temettü ifadeleri içindir, bütün dalların tüm kodunun doğrulandığı anlamına gelmez.

**Gizli ölçek dönüşümü kontrolü:** GUI `Dividend_Prc` değerini ölçeklemeden gönderir. Veri servisinin `SetStrategyCommand` yolu alan haritasını komuta aktarır; motorun `extractDouble` yordamı protobuf Double değerini aynen döndürür. `dividendPrc` alanında sonradan bir `/100` normalizasyonu bulunmadı. Yeni `params.dividendPrice` alanına da ham değer kopyalanır; incelenen hesaplar bu alanı kullanarak ölçeği düzeltmez. Motor fiyatları `undPriceDivider=1000` ile TL karşılığına getirir; emir fiyatının sonradan ×100/×10 ile aktarılması, daha önce TL hesabında yapılan farklı temettü düşümlerini eşitlemez.

**Somut birim karşılaştırması:** Giriş 250 ise Faiz/Çift Vade Faiz emir fiyatından 2,50 TL çıkarılır; `updateArbitrageState` aynı girdiyi teorik fiyat düzeltmesinde 250 TL olarak çıkarır. Giriş 2,50 yapılırsa iki etki 0,025 TL ve 2,50 TL olur. Salt frontend çarpanı bu iki motor kullanımını aynı anda tutarlı hâle getiremez. Faiz GUI hesabının kuruş yorumu ile pasif emir fiyatı uyumludur; motorun yön/fark hesabı bu yoruma uymamaktadır.

**Sonuç ve sınır:** Önceki inceleme, yapılmış geliştirmelerin geçmişini ve GUI'deki kuruş dönüşümünü yeterince açıklamıyordu; bunlar bu kontrolde netleştirildi. Bununla birlikte fiyat/yön ölçek uyumsuzluğu güncel motor kodunda sürüyor. Kullanıcının meslektaşının kastettiği commit bilinmediği için bulunan commit'lerden hangisini kastettiği söylenemez; uzak depoya gönderilmemiş veya erişilmeyen başka repo/fork değişikliği dışlanamaz. Sayısal örnekler kod hesabını açıklar; canlı emir/test sonucu değildir. Excel sonuçları değiştirilmedi.

**Kod noktaları (repo → dosya → sembol):**

- `mtrader-trade-ui/app/components/modals/arbitrageSettings/sections.tsx` → `InterestFields`, `Dividend_Prc`.
- `mtrader-trade-ui/app/components/dockview/arbitrage/arbitrageSettingsPayload.ts` → `Dividend_Prc`, `wrapGuiDouble`, `toDecimalNumber`; değer ölçeklenmeden aktarılır.
- `AlgorithmicTrading/algoSrc/Commands/ArbitrageTrackerCommand.cpp` → `Dividend_Prc` için `extractDouble`; aynı adlı `.h` dosyasında `dividendPrc` tipi `double`.
- `AlgorithmicTrading/algoSrc/Strategy/Arbitrage/ArbitrageTracker.cpp` → `calculateWantedPriceOpen`, `calculateWantedPriceClose` (`/100`) ve `updateArbitrageState` (doğrudan çıkarma).

## 8. Durdurmada bekleyen emirler

### Durdurmada bekleyen dayanak emirleri

**İlgili alan:** Motor.  
**İnceleme kimliği:** P19, P18; TC-ARB-R03.

`ArbitrageTracker::exitProperly` türev emirlerini iptal ediyor; dayanak emirlerinin iptalini yapan blok yorum satırında. Dolayısıyla strateji durduğunda ikinci bacaktaki bekleyen emir tahtada kalabilir ve sonradan gerçekleşebilir. İlk bacak gerçekleşmiş, ikinci bacak bekliyorsa paket bu süreçte tamamlanmamış pozisyon taşır.

Kullanıcının ürün beklentisi strateji durduğunda bütün bekleyen emirlerin iptalidir. Mevcut yol dayanak bacağını kapsamadığı için beklentiyle uyumsuzdur. Manuel durdurma ve bitiş saati aynı çıkışa gider. Durdurulduktan sonra dayanak trade abonelikleri kaldırılır ve paket tamamlayan işlem döngüsü çalışmaz; sonradan gerçekleşen emir genel emir kaydında bulunabilse de paket aynı yoldan güncellenmez. İptal isteği, iptal onayı değildir; arada gerçekleşen miktar ayrıca kontrol edilmelidir.

İptal çağrısı yalnız verilen enstrümanın emir defterini kapsar; türev iptali dayanak emirlerini dolaylı olarak iptal etmez. Temel sınıfın çıkışı da ek iptal göndermez. GUI durdurma komutu ayrıca genel tüm-emir-iptal komutu üretmediğinden, başka bir iptal yolunun bu açığı kapattığı varsayılamaz.

**Kod noktaları (repo → dosya → sembol):**

- `mtrader-trade-ui/app/components/dockview/arbitrage/useArbitrageStrategyCommands.ts` → `handleStartStop`, `buildStartStopPayload` çağrısı.
- `AlgorithmicTrading/algoSrc/Strategy/BaseStrategy.h` → `setCommand`, `exitProperly`; `algoSrc/Managers/Manager.h` → `stop`.
- `AlgorithmicTrading/algoSrc/Strategy/Arbitrage/ArbitrageTracker.cpp` → `isOpenSession`, `exitProperly` (dayanak iptali ve `undOrderDetails.clear()` yorumda), `runStrategy`, `checkUndExecution` → `positionOpened/positionClosed`.
- `AlgorithmicTrading/algoSrc/Managers/OrderbookManager.cpp` → `cancelAllOrders`; verilen enstrümanın defterine yönlendirme.

## 9. Pasif Emirler paneline veri gelmemesi

**İlgili alan:** Panelin emir kapsamı ve strateji aboneliği; ikinci bacakta fiili veri kaybı henüz doğrulanmadı.  
**İnceleme kimliği:** TC-ARB-F10 (`Başarısız`).  
**Dayanak:** Kullanıcının mevcut test kaydı.

Kullanıcı açık pozisyonları ve çok sayıda bekleyen emri olduğunu, özellikle vadeli emirlerin görünmediğini belirtiyor. **Bu panel bütün Arbitraj emirlerinin listesi değildir.** Yeni GUI `development` paneli yalnız motorun ikinci/dayanak bacağı için ürettiği `Command_Type_PassiveOrderResponse` mesajlarını okur. Normal Faiz/Spread Arbitrajında bu bacak spottur; Çift Vade türlerinde ikinci vadeli olabilir. İlk bacaktaki vadeli emirler bu mesaj akışına dahil değildir. Açık pozisyon/paket bulunması da bekleyen ikinci bacak emri bulunduğunu tek başına kanıtlamaz.

**Kodla doğrulanan kapsam nedeni:** Motor `checkDrvExecution` içinde ilk bacak kabulünü `openingDod` / `closingDod` üzerinden izler; bu emirleri `notifyPassiveOrderActivity` ile yayınlamaz. `checkUndExecution` ikinci bacak kabulü ve gerçekleşmelerinden bildirim üretir. Yeniden abonelikte `sendSnapshotOfStrategy` yalnız aktif `undOrderDetails` kayıtlarını pasif emir olarak yollar. `PassiveOrderActivity::toMessage` bu kayıtları serileştirir. GUI `PassiveOrders.tsx` yalnız bu mesajların deposunu okur; `Order_Is_Active == false` veya gerçekleşen miktarı gönderilen miktarına ulaşmış kayıtları eler. Dolayısıyla ilk bacak vadeli emrin bu panelde görünmemesi için soket arızası gerekmez; mevcut veri kapsamı bunu zaten dışarıda bırakır. GUI alt başlığı da açıkça “dayanak bacağında bekleyen pasif emirler” der. Bunun bütün vadeli emirleri kapsaması istenirse yalnız tablo filtresi değiştirmek yeterli olmaz; veri ve emir aksiyonlarının kapsamı birlikte ele alınmalıdır. Böyle bir genişletme henüz kullanıcı kararı değildir.

**Ayrı, doğrulanmış abonelik koşulu:** Panel kendi strateji aboneliğini kurmaz. `useArbitrageSubscriptions` takip panelinin çiftlerinden abonelik kaydı oluşturur; `buildSubscriptionSnapshot` bu kayıtlardan anahtar üretir. Boş anahtar listesinde `CommandSocket.requestStrategyStatus` istek göndermez. Veri servisi `transmitAlgoMessages` içinde yalnız ilgili anahtara abone GUI istemcisine yollar; GUI de `socketStore` içinde etkin anahtar kümesinde olmayan pasif emir mesajını eler. İlgili çiftin aboneliği yoksa ikinci bacak emri de görünmez. Kullanıcının testinde bu koşulun oluştuğu kanıtlanmış değildir.

**Uçtan uca yol:** İkinci bacak emir kabulü → `OuchManager::algoOrderAccepted` → enstrümanın hesap/strateji emir defteri → `OrderDepth::addOrder` → `checkUndExecution` → `notifyPassiveOrderActivity` → `GUIManager::sendPassiveOrderActivities` → `StrategyServiceImpl::FetchCommands` → trade-data-app `getCommandsFromService` / `transmitAlgoMessages` → GUI `CommandSocket` → `socketStore.passiveOrderData` → panel. Alan adları, mesaj türü, sayısal değer ve boolean dönüşümleri bu kaynaklarda birbirine karşılık gelir; incelenen kodda bütün geçerli ikinci bacak mesajlarını koşulsuz düşüren bir ad/tür uyuşmazlığı saptanmadı. Genel `PassiveOrdersSnapshot` ve `/ws/v1/passive-orders/start` başka bir emir akışıdır; bu Arbitraj panelinin kaynağı değildir.

**Açık kalan ayrım:** İlk bacak vadeli emirlerin görünmemesinin nedeni kodla belirlendi. Çalışan stratejinin kabul edilmiş, henüz tamamen gerçekleşmemiş ikinci bacak emri; ilgili çiftin aktif aboneliğine rağmen görünmüyorsa ayrıca mesaj/log kanıtı gerekir. `Notifying passive order activity` kaydı motorun mesajı ürettiğini; tarayıcı komut soketindeki `Command_Type_PassiveOrderResponse`, `unique_key`, `Order_Is_Active`, `Order_Sent_Qty`, `Order_Exc_Qty` alanları mesajın ulaşıp ulaşmadığını ayırır. Canlı emir gönderilmedi, müşteri logu/soket kaydı görülmedi. Excel'deki kullanıcının `Başarısız` sonucu değiştirilmedi; inceleme başarılı canlı test sayılmaz.

**Güncel kaynak kapsamı (2026-10-28):** 15 reponun `origin` bilgisi fetch ile güncellendi. GUI `development` `117bc34`, motor `development` `0dc32a7`, trade-data-app `development` `1cca9a8` üzerindeki akışın 12 kaynak dosyası doğrudan branch içerikleriyle karşılaştırıldı. GUI'nin henüz birleşmemiş `feat/new-gui-updates` `11b1646` dalında panel, komut normalizasyonu, soket deposu ve abonelik dosyaları development ile aynıdır. Motorun `add-order-sdk` `2eae46d` dalı emir kabul yolunu genişletir fakat pasif emir bildiriminin ilk/ikinci bacak kapsamını değiştirmez; dağıtılmış motorun bu dalda olduğu varsayılmaz. Motor master `aa150ee` karşılaştırmasında da bu kapsamı değiştiren fark görülmedi. trade-data-app master `4a43e19`, development ile aynı kaynak kabul edilmez; değerlendirme development esaslıdır.

Fetch kontrolündeki diğer referanslar: order-service development `26e9a02`, ouch-sdk development `0c3589e`, network-sdk development `3c1b42f`, MAOrderSDK development `c2b5060`, itch-sdk development `02a60dd`, HftSrvProd development `e64d49e`, Algo-Setup development `1c2b629`, performance-sdk development `6e47f20`, mtrader-frontend-apps main `db10c12`, algo-configs master `ab35dde`, Itch-Replayer main `c4b6029`, Warrant-Selector main `582987f`. Fetch kontrolü bu repoların tamamının yeniden fonksiyonel doğrulandığı anlamına gelmez; Arbitraj panelinin doğrudan üretici/taşıyıcı/tüketici yolu yukarıdaki üç repodadır. Uygulama kaynakları değiştirilmedi.

**Kod noktaları:** AlgorithmicTrading `algoSrc/Strategy/Arbitrage/ArbitrageTracker.cpp` → `checkDrvExecution`, `checkUndExecution`, `sendSnapshotOfStrategy`, `notifyPassiveOrderActivity`; `algoSrc/Strategy/StrategyActivities.h` → `PassiveOrderActivity::toMessage`; `algoSrc/Managers/GUIManager.h` → `sendPassiveOrderActivities`; `algoSrc/Managers/StrategyServiceImpl.cpp` → `HandleStrategySubscribers`, `FetchCommands`. trade-data-app `pkg/gui/connections/algotrading.go`, `pkg/gui/connections/ws_listener.go`, `pkg/gui/messages/base_command.go`. mtrader-trade-ui `app/components/dockview/arbitrage/PassiveOrders.tsx`, `useArbitrageSubscriptions.ts`, `app/lib/strategyWorkspace.ts`, `app/api/socket/CommandSocket.ts`, `app/stores/socketStore.ts`.

## 13. Ana senaryolardaki diğer açık davranış kayıtları

### Kâr alanlarının kaynak ve ölçeği

**İlgili alan:** Motor ve frontend gösterimi.  
**İnceleme kimliği:** TC-ARB-D04.

Ürün beklentisi TL gösterimidir; komisyon ve fonlama maliyeti kârdan düşülmez. Mevcut toplam kâr pozisyon kapanışlarında birikir. Açık paketlere anlık kâr eklenmesi bu hataların giderilmesi için gereken bir ürün kararı değildir ve mevcut düzeltme kapsamına eklenmemiştir. Ekran konumları [kâr gösterimi kaydındadır](../../bilgi-tabani/test-incelemeleri/arbitraj-inceleme-2026-10-26.md#kâr-gösterimi--d04-ürün-beklentisi-ve-ekran-konumu).

Kaynakta üç ayrı uyumsuzluk bulunur:

- **Arbitraj Hareketleri / Net Kar:** GUI `Cur_Profit` okur; motorun Arbitraj aktivite mesajı bu alanı üretmez. Alan yokken GUI `-` gösterir. Bu, toplam kârın da hesaplanmadığı anlamına gelmez.
- **Arbitraj Hareketleri / Toplam Kar:** `notifyStrategyActivityAndSummary`, aktiviteye `state.totalProfit × 1000` yazar; `ArbitrageStrategyActivity` bunu `Total_Profit` olarak gönderir. GUI `formatNumber` ile ölçek dönüşümü yapmadan gösterir.
- **Özet Görünüm / Toplam Kar:** Aynı motor fonksiyonu özete çarpan uygulamadan `state.totalProfit` yazar; `StrategySummary` bunu `Total_Profit` olarak gönderir. GUI bu kez `formatProfit` içinde 1000'e böler. Aktivite ve özet yollarının ölçek sözleşmeleri birlikte düzeltilmelidir; yalnız bir ekrana bölen eklemek bütün hesabı doğrulamaz.

`positionClosed` kapanış fiyat farkından kâr üretip `state.totalProfit` değerine ekler; bu hesapta komisyon/fonlama kesintisi yoktur. `closeProfitTick` tam sayı ara değeri ve miktar/çarpan hesabı da parasal sonuç doğrulanırken dikkate alınmalıdır. Standart dışı dayanak çarpanı ve küsuratlı farklarda fiili kârla ayrışma mümkündür. Burada iç değişkenin her durumda doğru TL olduğu varsayılmamıştır. Bulgular kod incelemesidir; canlı ekranda gerçekleşen işlemlerle karşılaştırma yapılmadı. Geliştirme sonraya bırakılmıştır; mevcut veri/gösterim sorunlarını kaydetmek için kullanıcıdan ek ürün kararı beklenmez.

**Kod noktaları:** `AlgorithmicTrading/algoSrc/Strategy/Arbitrage/ArbitrageTracker.cpp` → `positionClosed`, `notifyStrategyActivityAndSummary`; `algoSrc/Strategy/StrategyActivities.h` → `ArbitrageStrategyActivity`; `algoSrc/Strategy/StrategySummary.h` → `Total_Profit` serileştirmesi. `mtrader-trade-ui/app/components/modals/ArbitrageActivitiesModal.tsx` → `formatNumber`; `app/components/dockview/ArbitrageSummaryView.tsx` → `formatProfit`; `app/components/dockview/arbitrage/arbitrageActivityPayload.ts` → `getActivityField`; `app/api/socket/CommandSocket.ts` → `Total_Profit` normalizasyonu.

