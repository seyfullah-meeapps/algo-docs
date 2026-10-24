---
kapsam: Operatör, geliştirici, PM ve operasyon rolleri; hazırlık, çalışma, izleme ve kapanış
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-24
durum: taslak
---

# Kullanıcılar ve örnek iş günü

Bir önceki konuda sistemin piyasa verisini kurallarla değerlendirip emir ürettiğini gördük. Şimdi bu sistemin etrafındaki insanları ve bir işlem gününde nelerin takip edildiğini ele alalım.

Uygulamayı kullanan kişi ile uygulamayı geliştiren ve işleten ekip farklı sorumluluklar taşır. Bir stratejinin ayarını seçmek, sunucunun hazır olduğunu kontrol etmek ve beklenen davranış için test hazırlamak aynı iş değildir. Bunlar birlikte yürütülür; birinin tamamlanması diğerlerinin de tamamlandığı anlamına gelmez.

## Sistemin etrafında kimler var?

Aşağıdaki roller, rehberde işleri ayırt etmek için kullandığımız sorumluluk başlıklarıdır. Şirketteki kesin unvan veya kişi ataması değildir; bir kişi birden fazla sorumluluğu üstlenebilir.

| Rol | Temel sorumluluk | Sorduğu örnek soru |
|---|---|---|
| İşlem kullanıcısı / operatör | Yetkili hesaplarda strateji seçmek, ayarları yönetmek, emir ve pozisyonları izlemek | Hangi hesapta, hangi ürün için, hangi ayarlarla çalışıyorum? |
| Operasyon sorumlusu | Uygulamaların, bağlantıların ve gerekli verilerin çalışma hazırlığını takip etmek | Program açılmış mı; gerekli bağlantı ve veriler de hazır mı? |
| Geliştirici | Arayüz, servis veya strateji kodunu geliştirmek ve değişikliğin teknik doğrulamasını yapmak | Bu komut hangi kod yoluna gidiyor, üretilen sonuç neden böyle? |
| PM / test sorumlusu | Beklenen davranışı netleştirmek, senaryo ve kabul kriteri hazırlamak, kanıt toplamak ve işi takip etmek | Hangi koşulda ne bekliyoruz; bunu nasıl sınayıp tamamlandı diyeceğiz? |

Örneğin kullanıcı bir stratejinin miktarını değiştirirken PM bu değişikliğin açık emirler üzerindeki beklenen etkisini tarif eder; geliştirici uygulayan kodu inceler; operasyon ise testin veya çalışmanın hangi ortam ve sürümde yapıldığını netleştirmeye yardımcı olur. Bu iş bölümü, hem aynı dili konuşmayı hem de sonucu doğru kişiye yönlendirmeyi kolaylaştırır.

## Birbirine benzeyen üç farklı kimlik

Arayüzde oturum açan **kullanıcı**, alım-satımın adına yapıldığı **hesap** ve işlem yapılan **ürün** farklı kavramlardır. Kullanıcının sisteme girebilmesi her hesabı veya stratejiyi kullanabileceği anlamına gelmez; yetkili olduğu alanlar ayrıca belirlenir.

Bu ayrım günlük iletişimde de önemlidir. “HFT çalışıyor” ifadesi tek başına yeterli bağlam vermez. Hangi ortamda, hangi kullanıcı yetkisiyle, hangi hesap ve ürün üzerinde, hangi ayarlarla çalıştığını bilmek gerekir. **Ortam**, örneğin test için ayrılan sistem ile gerçek işlemlerin yürütüldüğü sistem arasındaki ayrımdır.

## Örnek iş gününün akışı

Bu anlatım, günün mantıksal aşamalarını gösterir. Sabit borsa saatleri veya bütün müşterilere uygulanacak bir operasyon talimatı değildir. Gerçek çalışma saatleri, hesap izinleri ve servis ayarları ilgili ortamdan belirlenir.

### Hazırlık: çalışmaya hazır mıyız?

Günün başında yalnız giriş ekranının açılmasıyla yetinilmez. İşlem yapılacak sistemin doğru ortam ve sürümde olduğu; gerekli uygulamaların, piyasa verisinin ve emir bağlantılarının hazır olduğu kontrol edilir. Arayüzden veri görebilmek ile stratejinin emir göndermeye hazır olması ayrı koşullardır.

Kullanıcı tarafında hangi hesap ve ürünlerde, hangi stratejilerin kullanılacağı netleşir. Başlangıçta görülen pozisyon ve bekleyen emirler de değerlendirilir. Önceki bir durumu bilmeden yeni işlem sonucunu yorumlamak, aynı miktarın nereden geldiğini karıştırmaya neden olabilir.

### Ayarlama: ne yapmasını istiyoruz?

İşlem kullanıcısı stratejiyi ve ilgili hesabı seçer; stratejiye özgü miktar, eşik ve fiyat koşullarını düzenler. Başlatma öncesinde amaçlanan ayar seti net olmalıdır. Bir alanın boş, sıfır veya kapalı olması aynı anlama gelmeyebilir; bunların karşılığını strateji konularında ayrı ayrı açıklayacağız.

Bazı emir akışlarında önceden hazırlanmış emirler belirlenen zamanda gönderilir. Bu nedenle arayüzde bir emrin kaydedilmiş olması ile o emrin borsaya iletilmiş olması ayrı aşamalardır. Toplu Emirler konusunu işlerken bu zamanlama ilişkisine döneceğiz.

### Çalışma: hangi olay ne doğurdu?

Strateji çalışırken piyasa verisi değiştikçe kurallar değerlendirilir. Koşullar uygun olduğunda emir üretilebilir. İzlerken üç şeyi ayrı tutarız: stratejinin çalışma durumu, emrin durumu ve gerçekleşmelerden oluşan pozisyon.

Örneğin “strateji çalışıyor” bilgisi her an emir göndermesi gerektiğini söylemez; koşulları bekliyor olabilir. “Emir kabul edildi” bilgisi de miktarın alınıp satıldığını göstermez. Bunu gerçekleşme olaylarıyla takip ederiz. Aynı emir kısmen gerçekleşebilir; kalan miktar ayrıca izlenir.

### Değişiklik ve değerlendirme: neyi değiştirdik?

Gün içinde bir ayar güncellendiğinde eski değer, yeni değer ve değişiklik anındaki emir/pozisyon durumu birlikte anlam taşır. Sıfır pozisyonda miktar değiştirmek ile kısmi gerçekleşme sonrasında miktar değiştirmek aynı başlangıç koşulu değildir.

PM veya test sorumlusu açısından yararlı kayıt; ortam ve sürüm, hesap/ürün bağlamı, ayarlar, olay sırası ve gözlenen sonuçtur. Böylece “aynı ayarlarla farklı sonuç çıktı” denildiğinde gerçekten aynı başlangıç durumundan söz edilip edilmediği kontrol edilebilir. Gerçek hesap ve erişim bilgileri paylaşılacak kayıtlarda maskelenir.

### Gün sonu: hangi durum kaldı?

İşlem dönemi biterken çalışan stratejiler, bekleyen emirler, gerçekleşmiş işlemler ve kalan pozisyon birlikte değerlendirilir. Durdurma komutu, emir iptali ve pozisyon kapatma ayrı eylemlerdir; bunların etkisi ilgili strateji ve komut akışına göre izlenir. Bir durdurma isteği gönderildi diye bütün işlemlerin tamamlandığı varsayılmaz.

Operasyon tarafında günün kayıtları ve kapanış durumu takip edilir. PM tarafında ise test sonuçları, açık görevler, alınan kararlar ve sonraki çalışma için gereken bilgiler kayda geçirilir. Bu rehberde ilerledikçe hem uygulamanın durumunu hem de o durumu açıklayan kanıtı okumayı öğreneceğiz.

{{< pagebreak >}}

## Küçük bir takip örneği

Bir test ortamında, belirli bir ürün için 100 lotluk alış beklediğimiz basitleştirilmiş bir senaryo düşünelim. Bu sayılar eğitim örneğidir; belirli bir stratejinin hazır ayar seti değildir.

| Gözlenen olay | Ne söyleyebiliriz? |
|---|---|
| Kullanıcı stratejiyi başlattı | Başlatma isteği verildi; motorun dönen durumu ayrıca izlenir |
| Motor stratejinin çalıştığını bildirdi | Çalışma durumu alındı; işlem koşulunun oluştuğu henüz söylenemez |
| Koşul oluştu ve 100 lot emir üretildi | Emir kararı oluştu; kabul ve gerçekleşme sonucu takip edilir |
| Emirden 40 lot gerçekleşti | Bu olay 40 lotluk gerçekleşme yarattı; 100 lotun tamamı gerçekleşmedi |
| Kalan 60 lotun iptali onaylandı | O emirden bekleyen miktar kalmadı; gerçekleşmiş 40 lot kendiliğinden geri alınmadı |

Başlangıç pozisyonu sıfırsa ve başka işlem yoksa sonuç +40 lot pozisyondur. “Emir iptal edildi” ile “pozisyon sıfır” arasındaki fark burada görünür. Günün her aşamasında olayları bu ayrımla okumak, hem ekranı anlamayı hem de doğru test beklentisi yazmayı kolaylaştırır.

## Bizim sistemdeki karşılığı

mTrader işlem kullanıcısının ayar ve izleme ekranlarını sunar. Admin paneli kullanıcı, hesap ve ilgili yönetim ayarları için ayrı bir arayüzdür. Strateji kararları motorlarda, emir iletimi ilgili emir yolunda, arayüzün servislerle iletişimi merkez serviste yürütülür. Operasyon bu parçaların çalışma hazırlığını, geliştirici kod davranışını, PM ise beklenen sonuç ve doğrulama kaydını birlikte değerlendirir.

Bu ilk bölümün iki konusu artık birbirini tamamlıyor: sistemin hangi ihtiyacı karşıladığını ve insanların onu gün içinde hangi sorumluluklarla yönettiğini gördük. Sıradaki bölümde bu anlatımda geçen ürün, lot, emir defteri ve eşleşme gibi borsa kavramlarını temelden açacağız.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcının talebi, anlamı korunmuş özet:** İlk bölümün kalan konusunu da yazalım; bölüm tamamlanınca okuyup revizyon vereceğim.

**Metne yansıması:** Roller, kullanıcı/hesap/ürün ayrımı, beş aşamalı örnek gün ve emir–pozisyon takip örneği eklendi. Buradaki roller bir şirket organizasyon şeması olarak sunulmadı. Kullanıcı bu içerikleri henüz okuduğunu veya onayladığını belirtmedi.

## Kaynaklar ve doğrulama

Sistem karşılıkları mevcut [sistem haritası](../../00-genel/sistem-haritasi.md), [arayüz özeti](../../10-servisler/mtrader-trade-ui/README.md), [admin paneli](../../10-servisler/mtrader-frontend-apps/README.md), [sabah kontrolleri](../../40-operasyon/sabah-kontrolleri.md), [emir dönüşü](../../30-akislar/emir-donusu.md) ve [sabah emri/handoff akışından](../../30-akislar/sabah-emri-ve-handoff.md) derlendi. PM sorumluluğu kullanıcının verdiği bağlamdan; diğer rol başlıkları öğretici sorumluluk ayrımından gelir. Bunlar gerçek kişi ataması değildir.

Frontmatter commit'leri referans belgelerin kaynak sürümleridir; bu tur kod yeniden incelenmedi. Örnek iş günü operasyon komutları veya güncel seans kuralları belirlemez. İnternet araştırması, canlı emir veya uygulama testi yapılmadı. Metin kullanıcı incelemesini bekleyen taslaktır.

## Devam notu

Birinci bölümün iki konu taslağı tamamlandı ve yayın listesine alındı. Kullanıcı ilk bölümü okuyup revizyon verecek; şimdilik ikinci bölüme geçilmeyecek. Gelen sorular ve değişiklikler ilgili konu dosyasında işlenecek.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
