---
kapsam: Arbitraj ana kaydı ve paketlerinin vade dolmadan yaş bazlı temizlenmesi; issue ve çözüm seçenekleri
kaynak:
  - repo: Algo-Setup
    branch: development
    commit: 1c2b629e4192152cd8ee1ae7c275580a030ab073
  - repo: Algo-Setup
    branch: main
    commit: 29077575f76fd707138a36bbe718801cd6f8093f
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7da21b73a9ae1a61326ea6f4a58e61ea68
  - repo: AlgorithmicTrading
    branch: master
    commit: aa150eec89983a2b11c4273648ac072937431e5e
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8ff8ecd45a8c196ed3e40ffba1a73c0193
  - repo: trade-data-app
    branch: master
    commit: 4a43e19f9eaf3bd963a5105c03af653699a7cce3
dogrulama: 2026-10-27
durum: taslak
---

# [Bug] RemoveOldData, 30 günü geçen arbitraj kayıtlarını açık pozisyon ve vade kontrolü olmadan siliyor

**Takip:** K-263 · **Önerilen öncelik:** Yüksek — açık pozisyonun uygulamadaki kalıcı takip verisinin kaybolması.

## Problem ve doğrulama sonucu

Arbitrajın ana DB kaydı, oluşturulma tarihinden itibaren 30 günlük eşiği geçtiğinde `RemoveOldData` tarafından silinmeye aday oluyor. Silme koşulu vade tarihini, açık pozisyon miktarlarını veya açık paketleri kontrol etmiyor. Depodaki şemada ana kayıt silindiğinde ona bağlı **aktif paketler de `ON DELETE CASCADE` ile siliniyor**.

Bu nedenle ikinci/üçüncü vadedeki bir pozisyon, sözleşmenin vadesi henüz dolmamışken uygulamanın kalıcı kayıtlarından kaybolabilir. Kodda neden doğrulandı; belirli bir müşteri ortamında gerçekleşen olayın kesinleştirilmesi için canlı DB tanımı ve temizlik logları ayrıca görülmelidir. Bu incelemede DB'ye bağlanılmadı, prosedür çalıştırılmadı.

İsim ve kapsam düzeltmesi: depoda bulunan prosedür `RemoveOldData`; `RemoveAllData` değil. Prosedür bütün tabloları aynı yaş kuralıyla temizlemiyor. Bazı kayıtlar yaşa göre, paketler duruma göre, emirler farklı filtrelerle siliniyor; kalan arbitraj kayıtlarında `totalProfit` sıfırlanıyor.

## Kodda kök neden

### 1. Yaş koşulu açık pozisyonu korumuyor

`Algo-Setup/mysql/setup.sql` → `RemoveOldData`:

```sql
DELETE FROM Arbitrage_Package WHERE isActive = 0;
DELETE FROM Arbitrage
WHERE DATE_ADD(FROM_UNIXTIME(timestamp,'%Y-%m-%d'), INTERVAL 30 DAY) < CURDATE();
UPDATE Arbitrage SET totalProfit = 0;
```

İkinci sorguda `derivativePosition`, `spotPosition`, paket varlığı/durumu veya `expirationDate` koşulu yok. Bu hata yalnız uzak vadeye özgü değil; ana kaydı yeterince eski olan herhangi bir arbitrajı etkileyebilir.

Koşul **bir takvim ayı** değil **30 gün** ekliyor; saat bilgisini atıyor ve kesin `<` kullanıyor. Aynı DB saat diliminde 1 Ekim tarihli kayıt, 31 Ekim'de silinmez; 1 Kasım'daki çalıştırmada silinmeye adaydır. Prosedür çağrılmadıkça bu satır kendiliğinden silme yapmaz.

### 2. Timestamp son işlem zamanı değil, normal akışta ana kaydın oluşturulma zamanı

| Kaynak | Kanıt |
|---|---|
| `AlgorithmicTrading/algoSrc/Strategy/Arbitrage/ArbitrageTracker.cpp` → `ArbitrageTracker` yapıcısı | DB kaydı yoksa `ArbitrageStruct(..., getCurrentTimeSeconds(), ...)` oluşturuluyor. Birim Unix saniye. |
| Aynı dosya → `updateArbitragePackage`, `updateDatabaseWithCurrentState` | Yeni pakete yeni timestamp veriliyor; ana `state.timestamp` yenilenmeden state DB istemcisine aktarılıyor. |
| `AlgorithmicTrading/algoSrc/Data/DatabaseServiceClient.cpp` → `getArbitrageData`, `setArbitrageDataAsync`, `setArbitrageData` | DB timestamp'i state'e geri okunuyor; yazmada `arb->set_timestamp(arbitrage.timestamp)` ile aynı değer iletiliyor. |
| `trade-data-app/pkg/servicemodels/algo_api.go` | İstek timestamp'i DB modeline taşınıyor. |
| `trade-data-app/pkg/db/mysql/algodb.go` → `SetArbitrageData` | INSERT ve `ON DUPLICATE KEY UPDATE timestamp = ?`, gelen `data.Timestamp` değerini kullanıyor; DB tarafında `NOW()` ile yenilemiyor. |

Dolayısıyla stratejide yakın zamanda işlem yapılması veya yeni paket açılması, normal akışta 30 günlük sayacı sıfırlamaz. Yeni açılmış bir paket bile eski ana kayıt üzerinden silinebilir. Buradaki tarih ilk paket tarihiyle de aynı olmak zorunda değildir; strateji kaydı daha önce oluşturulmuş olabilir.

### 3. Ana kayıt silinince aktif paketler de siliniyor

`Algo-Setup/mysql/setup.sql` → `Arbitrage_Package` tablosu:

```sql
CONSTRAINT fk_Arbitrage_Package_Arbitrage1
FOREIGN KEY (arbitrage) REFERENCES Arbitrage (id)
ON DELETE CASCADE ON UPDATE NO ACTION
```

Aktif paket ilk DELETE'ten kurtulsa bile ana kaydı silen ikinci DELETE onu cascade üzerinden siliyor. Sepet paket tablosunda da pakete bağlı cascade ilişkisi bulunuyor.

**Şema sınırı:** `setup.sql` içindeki ana tablo eski `spotInstrument/derivativeInstrument` alanlarını taşıyor; güncel Go kodu `spotStrategy/derivativeStrategy` kullanıyor. Bu yüzden dosya canlı DB'nin eksiksiz güncel şeması kabul edilemez. Cascade depoda doğrulandı; canlı DB'de `SHOW CREATE TABLE` ile ayrıca teyit edilmelidir.

### 4. Çağrı yolu ve ikinci temizlik tanımı

- `Algo-Setup/Configs/<MUSTERI>/db_scripts/dbNightEvent.sh` dosyaları `call RemoveOldData;` çalıştırıyor. Gerçek host cron saati, son başarılı çağrı ve o DB'deki prosedür gövdesi bu incelemede doğrulanmadı.
- `AlgorithmicTrading/scripts/mysql_scheduled_job.sql` içindeki `remove_old_instruments` günlük event taslağı aynı 30 günlük `Arbitrage` silmesini içeriyor. Burada paket filtresi `contractQty = 0`; prosedürdeki `isActive = 0` ile farklı. Event'in ortamda kurulu/aktif olduğu kanıtlanmadı; dosyada bir TimeBased DELETE sonrasında eksik noktalı virgül de var. Dağıtımda etkin tüm temizlik yolları envanterlenmeli.
- Fetch sonrası `Algo-Setup` development/main `mysql/setup.sql` dosyaları aynı. `AlgorithmicTrading` development/master event ve DB istemci dosyaları aynı; ilk timestamp ataması master'da da mevcut. `trade-data-app` development/master arasındaki ilgili dosya farkları bu yaş mekanizmasını değiştirmiyor. Bu, yalnız development'a özgü bir sorun değil; kurulu DB prosedürü yine ayrıca doğrulanmalı.

## Etki

Kesin silinen nesne `Arbitrage` durum kaydıdır; depodaki FK uygulanıyorsa ona bağlı paketler de silinir. Bu SQL'in doğrudan strateji ayarlarını veya `Accounts_Strategies` satırlarını sildiği söylenemez. Kullanıcının gördüğü “strateji silindi” belirtisi, pozisyon/paket durumunun kaybı olarak ayrıştırılmalıdır.

`GetArbitrageData`, ana kayıt ve paketleri DB'den okur. Motor yapıcısı kayıt bulamazsa sıfır pozisyonlu yeni `ArbitrageStruct` oluşturur. Temizlik sonrası yeniden oluşturma/başlatma akışında eski pozisyonların geri yüklenememesi bu kod yoluyla açıklanır. Bellekteki cache nedeniyle kayıp çalışan ekranda hemen görünmeyebilir; kesin görünme zamanı entegrasyon testine bırakılır.

DB kaydının silinmesi borsadaki gerçek pozisyonu kapatmaz. Uygulamanın paket, maliyet ve kapama takibi ile gerçek pozisyon arasında ayrışma riski doğar.

**Aynı temizlikte ek risk:** `isActive = 0`, “tamamlandı ve risksiz” demek değildir. `ArbitragePackage` başlangıçta `isActive=false`, `isCompleted=false` olur; türev dolmuş, dayanak henüz dolmamış paket bu durumda kaydedilebilir. İlk DELETE bu tür yarım paketi yaşına bakmadan silebilir. Yalnız 30'u 90 yapmak veya ana kayıt DELETE'ini kaldırmak bu ayrı silme yolunu düzeltmez.

## Yeniden üretim senaryosu

Aşağıdaki adımlar izole test DB'si içindir; bu incelemede çalıştırılmadı.

1. Geçerli hesap/strateji/enstrüman ilişkileriyle vadesi gelecekte olan bir arbitraj oluştur. Ana kaydın timestamp'ini DB tarihine göre 31 gün öncesine ayarla.
2. Ana kayda `isActive=1`, `isCompleted=0`, `contractQty>0` olan bir paket bağla; ana pozisyon alanlarını buna uygun doldur. Paket timestamp'i bugünün tarihi olsun.
3. Ana kayıt ve paket kimliklerini, miktarlarını, vade tarihini ve FK tanımlarını kaydet.
4. `CALL RemoveOldData();` çalıştır.
5. Mevcut kodla beklenen hata: ana kayıt silinir; belirtilen FK varsa aktif paket de silinir. Gelecekteki vade ve yeni paket tarihi koruma sağlamaz.
6. Motoru izole ortamda yeniden oluştur; eski paketlerin restore edilmediğini ve yeni sıfır state yolunu gözle.
7. Ayrı senaryoda ana kaydı yeni tut; `isActive=0`, `isCompleted=0`, `contractQty>0` yarım paket oluştur. İlk DELETE nedeniyle oluşan paket kaybını test et.

## Ortamda kesin teyit için salt okunur kontroller

Doğru uygulama DB'si seçilerek:

```sql
SHOW CREATE PROCEDURE RemoveOldData;
SHOW CREATE TABLE Arbitrage;
SHOW CREATE TABLE Arbitrage_Package;
SHOW EVENTS;
SELECT @@session.time_zone, @@global.time_zone, CURDATE();

SELECT a.id, FROM_UNIXTIME(a.timestamp) AS stored_at,
       a.derivativePosition, a.spotPosition,
       COUNT(p.id) AS package_count,
       SUM(CASE WHEN p.isActive = 1 THEN 1 ELSE 0 END) AS active_packages
FROM Arbitrage a
LEFT JOIN Arbitrage_Package p ON p.arbitrage = a.id
WHERE DATE_ADD(FROM_UNIXTIME(a.timestamp,'%Y-%m-%d'), INTERVAL 30 DAY) < CURDATE()
GROUP BY a.id, a.timestamp, a.derivativePosition, a.spotPosition;

SELECT id, arbitrage, contractQty, underlyingExecQty, isActive, isCompleted
FROM Arbitrage_Package
WHERE isActive = 0 AND
      (isCompleted = 0 OR contractQty <> 0 OR underlyingExecQty <> 0);
```

Varsa event'in `SHOW CREATE EVENT` çıktısı da alınmalı. Geçmişte kaybolmuş kayıt için temizlik öncesi yedek/binlog ve başarılı çağrı logu karşılaştırılmalı; güncel SELECT tek başına geçmiş silinmenin kanıtı değildir. Elde edilen veriler hesap/müşteri bilgileri maskelenerek eklenmeli.

## Çözüm seçenekleri

| Seçenek | Kazanç | Sınır / maliyet |
|---|---|---|
| **A — 30 günü 90 güne çıkarmak** | Küçük SQL değişikliğiyle mevcut erken silme penceresini uzatır. | Açık pozisyon kontrolü eklemez; 90 gün sonunda aynı hata oluşur. Üç takvim ayı her zaman 90 gün değildir. Yarım paket DELETE'i devam eder. Tek başına kalıcı çözüm değil. |
| **B — Arbitrajın yaş bazlı ana kayıt silmesini kaldırmak** | Açık ana kayıtların yalnız yaş nedeniyle silinmesini durdurur. | Kayıt büyümesi için izleme/arşiv gerekir; bağımsız paket silme ve enstrüman cascade yolları ayrıca korunmalıdır. Bütün `RemoveOldData` prosedürünü kaldırmak anlamına gelmez. |
| **C — Pozisyon/paket yaşam döngüsüne göre temizlemek (önerilen)** | Açık veya yarım kayıt yaşı ne olursa olsun korunur; kapanmış veri kontrollü temizlenir. | Açık/yarım/tamamlanmış durum tanımı, `closed_at` benzeri kapanış tarihi ve atomik temizlik tasarımı gerektirir. |
| **D — Vade + mutabakat/takas sonrasını esas almak** | Gerçek sözleşme tarihine uyar; sabit 90 güne bağımlılığı kaldırır. | Vadenin geçmesi tek başına pozisyonun kapandığını kanıtlamaz. İki vadeli stratejide iki bacak da değerlendirilir; C'nin güvenlik koşullarıyla birlikte kullanılmalıdır. |

**Öneri:** Acil önlem olarak B değerlendirilsin; aynı değişiklikte yarım paketleri silebilen ilk DELETE korumaya alınsın. Kalıcı çözüm C, gerekiyorsa D ile desteklensin. Aktif veri ile tarihsel/arşiv verisinin saklama politikası ayrıştırılsın. 90 gün isteniyorsa açık pozisyonun ömrü olarak değil, güvenle kapanmış/arşivlenmiş kaydın saklama süresi olarak değerlendirilsin. Nihai ürün kararı henüz alınmadı.

C için silinebilir kayıt: iki bacağın pozisyonu sıfır, açık/yarım paket yok, bekleyen emir veya mutabakat işi yok, kapanış tarihi biliniyor ve kapanıştan sonraki saklama süresi dolmuş. Sadece `isActive=0` veya sadece `contractQty=0` yeterli değil. Bilinmeyen/çelişkili durumda kayıt korunsun ve incelemeye ayrılsın. Kontrol ile DELETE arasına yeni paket yazılabilmesi de transaction/kilitleme veya servislerin durduğu doğrulanmış bakım akışıyla önlenmeli.

**Vade varsayımı:** Borsa İstanbul'un pay vadeli ürün sayfası, içinde bulunulan ay ve en yakın iki ay olmak üzere üç vade ayı tanımlıyor; bu “bugünden itibaren kesin 90 gün” kuralı değildir. Bütün VİOP ürünleri için genel üç ay sınırı da çıkarılamaz. Silme kararı enstrümanın gerçek vadesine ve pozisyon durumuna dayanmalı. Kaynaklar, erişim 2026-10-27: [Pay vadeli sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri), [vade ayları ve son işlem günü](https://www.borsaistanbul.com/piyasalar/viop/sozlesme-ozellikleri/vade-aylari-sozlesme-vadesi-son-islem-gunu).

## Kabul ölçütleri ve uygulama kapsamı

- [ ] 31, 91 ve 92 günlük ana kayıtlarda açık pozisyon/aktif paket korunur; bugünkü paket eski ana kayıt yüzünden silinmez.
- [ ] `isActive=0`, `isCompleted=0` yarım paket; ayrıca türevi kapanmış ama dayanak bakiyesi kalan paket korunur.
- [ ] Tam kapanmış ve mutabık kayıtlar seçilen saklama politikasına göre temizlenir; süre kapanış tarihinden ölçülür. Tarihi/durumu belirsiz kayıt otomatik silinmez.
- [ ] Gelecek vade, vade günü, vade sonrası takas/mutabakat ve çift vade senaryoları test edilir; vade geçmesi açık pozisyonu tek başına silmez.
- [ ] Tam eşik günü, eşikten sonraki gün, saat dilimi, ay/yıl geçişi ve NULL timestamp testleri bulunur.
- [ ] Temizlik sonrası restart/restore, paket miktarlarını ve maliyetlerini kayıpsız geri getirir; eşzamanlı yazma sırasında aktif kayıt silinmez.
- [ ] Prosedür, varsa DB event'i ve enstrüman silmeye bağlı cascade yolları aynı koruma ilkesini uygular. Diğer tabloların mevcut saklama politikaları ayrı tutulur.
- [ ] Yeni kurulum SQL'i yanında mevcut DB'ler için sürümlü migration hazırlanır; yalnız repo dosyasını değiştirmekle yetinilmez. Mevcut tablo silen setup scripti doğrudan yeniden çalıştırılmaz.
- [ ] Dağıtım öncesi etkilenecek kayıt sayıları ve yedek alınır; dağıtım sonrası `SHOW CREATE PROCEDURE/TABLE/EVENT` ile kurulu tanımlar doğrulanır. Silinen kayıtların migration ile geri gelmeyeceği dikkate alınarak gerekiyorsa yedekten mutabakatlı kurtarma yapılır.

**Bu çalışmanın sınırı:** Üç kaynak repoda fetch yapıldı, ilgili development ve master/main kodları karşılaştırıldı. Uygulama/SQL değişikliği, build, canlı DB testi veya uzakta issue açma yapılmadı. Bu dosya issue olarak kullanılacak taslaktır.
