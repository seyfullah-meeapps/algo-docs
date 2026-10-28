---
kapsam: Arbitraj sanity Excel'indeki 14 belirsiz parametre ve bunlarla ilişkili regresyon kayıtlarının yeni GUI kapsamına göre kod incelemesi
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading
    branch: master
    commit: aa150ee
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui
    branch: main
    commit: 6715182
  - repo: order-service
    branch: development
    commit: 26e9a02
  - repo: order-service
    branch: master
    commit: 298403b
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: Algo-Setup
    branch: development
    commit: cade7d0
dogrulama: 2026-10-26
durum: taslak
---

# Arbitraj Excel incelemesi — 26 Ekim 2026

Güncel kullanıcı Excel kapsamı [sanity girişinde](../../testler/sanity/README.md#arbitraj-güncel-sanity-kapsamı), açık sorunlar [toplu issue dosyasında](../../issues/sanity/arbitraj-toplu-issue.md) tutulur. Aşağıdaki P/R kimlikleri kaynak incelemesine aittir; güncel Excel sayfa ve satır listesi değildir.

Kullanıcı test edilen arayüzü **yeni GUI (`development`)** olarak netleştirdi. [Aktif Excel](../../testler/sanity/MTrader_Arbitraj_Sanity_Test.xlsx) bu kapsama göre revize edildi. Eski GUI `main` yalnız önceki açıklamaların kaynağını ayırmak için okundu; eski GUI hataları düzeltilmedi. Kaynaklar ayrı `C:\Users\Seyf\algo-workspace` klonlarında incelendi; beş repoda origin fetch başarılı, çalışma dosyaları değiştirilmedi. Referans branch'leri checkout/pull ile değiştirmek yerine commit/ref içerikleri okundu.

Bu tur kaynak kod incelemesi ve Excel paket bütünlüğü kontrolüdür. Uygulama build'i, browser/API/DB testi, canlı emir, sunucu config/dosya kontrolü ve deploy yapılmadı. Kodla kapanan bir iddia Excel'in B sütununda başarılı test sayılmadı. Diğer regresyon kayıtları bu turun kapsamına giren ilişkileri dışında yeniden doğrulanmış sayılmaz.

## Kapanan açıklıklar

| Parametre | Sonuç | Dayanak |
|---|---|---|
| P01 | Yeni GUI'de tekil/toplu strateji tipi 6. “SDK enum'u yok / toplu tip null” iddiaları bu kapsamda kapandı | `arbitrageSettingsPayload.ts` → `buildArbitrageSettingsPayload`; SDK `include/models/Enums.h` → `ARBITRAGE=6` |
| P37 / R06 | Yeni GUI, değiştirilen alanları takip eder; 0'a bilerek dönüş değer karşılaştırmasıyla elenmez. Eski GUI hatası yeni GUI'ye genellenemez | `useArbitrageStrategyCommands::handleSettingsSave`; `strategy/bulkSettings.ts` → `selectBulkUpdates` |
| P16 | Pasif bariyer parse/log/geri bildirim alanı; incelenen arbitraj mantığında davranış tüketicisi yok | `ArbitrageTrackerCommand` ve `passiveBarrier` genel referans taraması |
| P20 | Eski vade bayrakları etkin değil; gerçek bacak seçimi kimliklerle yapılıyor | `First_Future`/`Second_Future`/`Third_Future` payload ve motor referansları; `StrategyFactory::createStrategy` |

P16/P20'nin `KULLANILMIYOR` etiketi korundu; açıklaması artık cevapsız soru değil, etkisiz/devre dışı davranışın kaydıdır. Wire alanlarını silmek bu turun kapsamı değildir. P01/P37 `Eşleşiyor` oldu. R06'nın eski hata iddiası `İDDİA GEÇERSİZ` olarak ayrıldı; gerçek toplu kaydetme regresyonu ve `Test Edilmedi` sonucu korundu.

## İnceleme kapsamı

Bu üç konu için okunan kaynaklar: AlgorithmicTrading development `0dc32a7` ve master `aa150ee`; yeni GUI development `117bc34` (ilgili dosyalar yerel `b0474c3` ile aynı); eski GUI main `6715182`; trade-data-app development `1cca9a8`. Canlı müşteri sürümü, emir/iptal yanıtı veya uygulama testi değildir. Kaynak repolar salt okunmuştur.

## Devam eden kaynak bulguları ve çözüm yolu

### Kâr gösterimi — D04 ürün beklentisi ve ekran konumu

Ürün beklentisi: kâr TL gösterilir; gösterilen kârdan komisyon ve fonlama maliyeti düşülmesi beklenmez. Bu beklenti, fonlama parametresinin strateji fiyat hesaplarında kullanılmasını kaldırmaz. Mevcut toplam kâr kapanışlarda birikir; açık paketlere anlık kâr eklemek mevcut hataların giderilmesinden ayrı bir özellik kapsamıdır. D04 için kullanıcıdan ek karar beklenmez; veri/gösterim hataları açıktır ve geliştirme sonraya bırakılmıştır.

Yeni GUI `b0474c3` kaynağında Arbitraj Takip satırının sağ tık menüsündeki **Arbitraj Hareketleri** penceresinde **Net Kar** (`Cur_Profit`) ve **Toplam Kar** (`Total_Profit`) alanları vardır. `ArbitrageTrackerForm.tsx` menüyü açar; `ArbitrageActivitiesModal.tsx` bu iki alanı `formatNumber` ile gösterir; Türkçe etiketler `app/locales/tr/arbitrage.json` içindedir. Veri yoksa pencere boş durum mesajı, alan yoksa `-` gösterir. Bu kod okumasıdır; canlı ekran gözlemi değildir.

**Özet Görünüm** ayrıca **Toplam Kar** sütununu ve **Toplam K/Z** özetini gösterir (`app/components/dockview/ArbitrageSummaryView.tsx`). Buradaki `formatProfit` gelen değeri 1000'e böler; motor özet yolunda aktivitedeki ×1000 çarpanını uygulamaz. Dolayısıyla bu ekranın doğru TL gösterdiği varsayılamaz. Eksik Net Kar verisi, iki mesajın farklı ölçeği ve hesaplama sınırlarının ayrıntısı [toplu issue içindeki kâr alanları](../../issues/sanity/arbitraj-toplu-issue.md#kâr-alanlarının-kaynak-ve-ölçeği) bölümündedir.

### Otomatik yön ve temettü — mevcut K-205 ile ilişkili

P32/R01: motor enum'u yalnız `Above='A'` ve `Below='B'` tanırken GUI 79 (`O`) gönderiyor. `checkOpenable` bu değeri doğrudan yön değişkenine atıyor. `checkParameters` ve pasif fiyat hesapları farklı `if/else` yolları kullanıyor; “her zaman alır” açıklaması doğru değil. GUI otomatikte `Open/Close_Tick` gösterirken F türü motor `Fs_Open/Close_Tick` okuyor. İki motor branch'inde de bu destek eksik.

Motorun ayrı `D/DiffTick` türünde `abs(diffTick) >= openTick` koşulu ve işarete göre Above/Below seçimi vardır: pozitif/0 teorik fark Above (vadeli satış), negatif fark Below (vadeli alış) seçer; açılış/kapanış için birer kademe alanı kullanır. Bu spot-vadeli çıplak farkı kullanan `F` türüyle aynı hesap değildir. Yeni ve eski GUI Spread'i `F` gönderir, otomatik seçimi `D`'ye dönüştürmez. Bu nedenle mevcut Spread Otomatik işleyişine “çalışan otomatik yön desteği” denemez. `O` için doğrulama/reddetme de yoktur; farklı karşılaştırmalar farklı varsayılan dallara düşer.

Çözüm önerisi: otomatik davranışın yön/eşik sözleşmesi belirlenip GUI ve motor birlikte uygulanmalı; uygulama yapılana kadar seçenek kapatılabilir. Yalnız F'yi D yapmak bütün davranışın doğrulandığı anlamına gelmez. Kabul: iki piyasa yönü, aktif/pasif mod ve sıfırdan farklı eşikler birlikte sınanır.

P05/R07: `calculateWantedPriceOpen/Close` Faiz/Çift Vade Faiz fiyatlarında temettüyü `/100` kullanırken `updateArbitrageState` doğrudan çıkarıyor. Sorun yalnız GUI'nin göndermediği D türüyle sınırlı değil. Arayüz sayıyı ölçeklemeden Double gönderir; fiyat hesabı kuruş, yön/fark hesabı TL gibi tüketir. Tek bir doğru giriş birimi koddan çıkarılamaz; aynı türün hesapları tutarlı hale getirilmelidir. Mevcut teknik bağlam: [Arbitraj](../20-stratejiler/arbitraj.md).

### Çift Vade çarpanı

Güncel ürün davranışı (kullanıcı beyanı): Çift Vade ve Çift Vade Faiz için GUI varsayılan çarpanı 1; kullanıcı değeri değiştirebilir. Bu bir açık sorun değildir. P07/P33 ayar açıklamaları ve R04 regresyonu bu davranışı esas alır; canlı test sonucu varsayılmaz.

Motor development `0dc32a7`: genel etkin çarpan 100; T/R kurucusunda 1 olur. Opsiyonel ayar açıkken komuttaki çarpan uygulanır; yeni strateji opsiyonel kapalıyken 1 kullanır. Önceden değiştirilmiş aynı stratejide opsiyoneli kapatmak etkin çarpanı otomatik sıfırlamaz. Miktar, ilk bacak gerçekleşen miktarı × etkin çarpandır. Kaynak: `ArbitrageTracker` kurucusu, `setCommand`, `sendUnderlyingOrder`.

### Ayar doğrulaması


Güncel ürün davranışı (kullanıcı beyanı): başlangıç saati bitişten sonraysa frontend kaydetmeyi engeller. Limitlerin boş/sıfır kaydedilmesi engellenmez; kullanıcı daha sonraki çalıştırma için ayar hazırlayabilir. Mevcut negatif değer kontrolü korunur. Bu iki konu açık sorun değildir; R10/P38 güncel davranışın regresyonudur. Frontend davranışı canlı test sonucu sayılmaz.

Sıfır alan bazında değerlendirilir: Kontrat Limiti 0 yeni pozisyon açılışını engeller; Paket Limiti 0 ek paket miktarı sınırını kaldırır. Kapanış kontrat limiti yalnız ilgili kontrol açıkken uygulanır. “Herhangi bir limit 0 ise strateji durur” denmez. Kaynak: `ArbitrageTracker::checkOpenable` ve açılış/kapanış miktarı hesapları.

### Başlangıç ve durdurma politikası

P19/R02 kaynak zinciri: yeni GUI `arbitrageSettingsPayload.ts::toTimeSeconds` saat:dakika değerini gece yarısından itibaren saniyeye çevirir, saat dilimi kaydırmaz. `ArbitrageTrackerCommand::parseArbitrageParameters` Start/Stop değerlerini doğrudan okur. `doPeriodicChecks` ilk olarak `isOpenSession` çağırır; false ise fiyat güncelleme, bekleyen emir yönetimi ve `runStrategy` yoluna ilerlemez.

**Başlangıç uyumsuzluğu:** `isOpenSession` başlangıçtan normal türlerde 3 saat, Çift Vade/Çift Vade Faiz'de 3,5 saat çıkarır. Karşılaştırma `TimeUtility.h::calcSecondsFromMidnight` içindeki `localtime` ile yapılır. Başlangıç beklenirken strateji running kalabilir; işlem döngüsüne geçmez. Ancak beklenen eşik kullanıcının saati değildir. Container İstanbul saatindeyse 14.00 girişi normal türlerde 11.00, iki vadeli türlerde 10.30 eşiğine dönüşür. Her iki enstrümanın seansı ve diğer işlem koşulları uygunsa 14.00'ten önce emir üretilebilir. Setup `MAProdEnv/Dockerfile` İstanbul TZ tanımlar; canlı container ayarı okunmadı. Development `0dc32a7` ve master `aa150ee` aynı başlangıç/bitiş hesabını içerir.

**Seans kapalıysa:** başlangıç eşiği geçildikten sonra iki enstrümandan biri continuous session değilse motor beklemek yerine `stop()` çağırır. Bu yolda seans açılınca kendiliğinden başlatma yoktur; dolayısıyla seans öncesi başlatılan stratejinin mutlaka seçilen saate kadar bekleyeceği söylenemez.

**Bitiş yolu:** `stopTime <= yerel saat` olduğunda `stop()` çağrılır ve o döngüde emir üretimine geçilmez. `Manager::stop` running'i kapatıp `exitProperly` çağırır. Bitiş saatinden 3/3,5 saat çıkarılmaz. İstanbul saatli ortamda 18.00 bitişi, 18.00 veya sonrasındaki ilk kontrol turunda durdurur. Kontrol döngü başındadır; emir gönderiminin her noktasında bağımsız bitiş saati kontrolü yoktur. Sınırı geçen, zaten başlamış döngü/emir isteği açısından tam saniyede mutlak kesinti garantisi verilmez. `sendOrder` development'ta otomatik türev emirleri için running kontrolü yapar; kullanıcı emirleri ayrı yoldur.

Frontend saat sırası doğrulaması bu motor uyumsuzluğunu çözmez. Çalışan ortamın saat dilimi ve iki tür ailesinde başlangıç/bitiş sınır testi gerekir. Yeni emir üretiminin durması, borsadaki bekleyen emirlerin tümünün iptal olduğu anlamına gelmez; dayanak iptal eksikliği aşağıdaki ayrı R03 bulgusudur. Canlı test veya kaynak kod değişikliği yapılmadı.

R03 ürün beklentisi: kullanıcı durdurulduğunda stratejinin bütün bekleyen emirlerinin iptal edilmesini bekliyor. Kod bunun yalnız vadeli bacağını karşılıyor: `exitProperly` vadeli alış/satış emirlerine iptal gönderiyor; dayanak iptal bloğu ve `undOrderDetails.clear()` yorumda. `BaseStrategy::exitProperly` yalnız durumu/bildirimleri güncelliyor, ek emir iptali yapmıyor. `OrderbookManager::cancelAllOrders` verilen enstrümanın defteriyle sınırlı; vadeli çağrısı dayanağı kapsamaz. Manuel durdurma `BaseStrategy::setCommand → stop`, bitiş saati `isOpenSession → stop` üzerinden aynı `exitProperly` yoluna ulaşır.

Geç gerçekleşmenin paket takibine etkisi kodla desteklenir: `Manager::stop` running'i kapatır; `runStrategy` duruyorsa döner, `checkUndExecution` çalışmaz; çıkışta dayanak trade abonelikleri kaldırılır. Paket tamamlanması `checkUndExecution → positionOpened/positionClosed` yolundadır. Borsa/SDK genel emir kaydı ile arbitraj paket durumu aynı şey değildir; bütün sistem gerçekleşmeyi kaybetti diye genellenmez. Durdurma sırasında zaten işlenmekte olan olay veya iptal onayından önceki gerçekleşme ayrıca mümkündür.

Yeni GUI `handleStartStop` ayrıca tüm-emir-iptal isteği göndermez. İncelenen kaynakta kullanıcının beklediği iki-bacak iptali uygulanmış değildir. Bu teknik uyumsuzluktur; kullanıcıdan aynı ürün kararını tekrar istemek gerekmez.


## Excel'deki değişiklikler ve bütünlük

- 14 parametre kaydının açıklama/kaynakları ve ilgili 12 regresyon kaydı güncellendi. Bütün regresyonun yeniden doğrulandığı iddia edilmez.
- 65 hücre değeri değişti; yalnız `Regresyon`, `Parametre Eşleştirme` ve durum listesindeki D5 hücresi etkilendi. D5'e `İDDİA GEÇERSİZ` eklendi; mevcut açılır liste zaten D2:D10 aralığını kapsıyordu.
- Sonuç/gerçekleşen sonuç sütunları korundu. 19 regresyon testi hâlâ `Test Edilmedi`. HFT Excel'i değişmedi.
- Artifact aracıyla hücreler yazılıp dışa aktarıldı; bu değerler orijinal paketteki hedef hücrelere aktarılarak desteklenmeyen Excel özelliklerinin dönüşümde kaybolması önlendi.
- Hücre, stil ve formül karşılaştırması yapıldı. Hedef dışındaki hücreler ve paket parçaları aynı; açılır listeler, koşullu biçimlendirme, boyutlar, birleşimler ve formüller değişmedi. ZIP/XML kontrolleri geçti.
- Görselleştirme aracı Windows'ta native hata ile kapandı; bu tur Excel'de açma/görsel kontrol yapılamadı. Görsel kontrol yapılmış diye sunulmaz.
- Revizyon öncesi kopya: [_yedek_2026-10-26-kod-incelemesi/MTrader_Arbitraj_Sanity_Test.xlsx](../../arsiv/test-yedekleri/2026-10-26-kod-incelemesi/MTrader_Arbitraj_Sanity_Test.xlsx).
- Repo yapısal kontrolü: 170 Markdown, 1.884 bağlantı, 0 hata. `git diff --check` temiz.

## Önerilen devam sırası

P32 otomatik yön ve P19 saat davranışı açık teknik konulardır. P38/R10 kullanıcı tarafından tanımlanan güncel kaydetme kurallarını sınar. Temettü için fiyat/yön ölçeği tutarlı hale gelmelidir. Durdurma beklentisi iki bacağın bekleyen emirlerinin iptalidir; kaynak bu beklentiyle uyuşmaz. Yeni GUI toplu kaydetme testini R06 ile uçtan uca doğrula. Bu sıralama geliştirmelerin yapıldığı veya canlı testlerin koşulduğu anlamına gelmez.
