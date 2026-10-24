---
kapsam: MTrader kullanıcıları; özellik geliştirme, strateji testleri, preprod ve dağıtım
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
kullanici_beyani:
  tarih: 2026-10-24
  baglam: Ürün kullanıcıları ve şirketin özellik geliştirme/test akışı
---

# Kullanıcılar ve geliştirme süreci

MTrader'ın müşterileri **aracı kurumlardır**. Günlük işlem kullanıcıları bu kurumların çalışanlarıdır; traderlar ve fon yöneticileri bunlara örnektir. Kullanıcılar yetkili oldukları hesap ve ürünlerde stratejileri çalıştırır, ayarları yönetir, emirleri ve pozisyonları takip eder.

## Müşteri tarafında kim kullanır?

Trader veya fon yöneticisi, kendi kurumunun yetkileri ve çalışma yaklaşımı doğrultusunda MTrader'ı kullanır. Gün içinde hangi hesapta, hangi ürün için, hangi stratejinin çalıştığını; açık emirleri, gerçekleşmeleri ve elde kalan pozisyonu izler. Buradaki **pozisyon**, yapılan işlemler sonucunda ilgili üründe elde tutulan net miktardır.

Günün başında mevcut durum ve ayarlar değerlendirilir, işlem sırasında sonuçlar takip edilir, günün sonunda açık emir ve pozisyonlar kurumun kendi sürecine göre ele alınır.

## Geliştirmede sorumluluklar

MTrader'da bir özellik ihtiyacının anlaşılmasıyla başlayan çalışma, geliştirme, test ve müşteriye aktarım boyunca sürer. Aşağıdaki tablo bu süreçteki sorumlulukları açıklar; değişmez kişi veya unvan ataması değildir.

| Sorumluluk | Ürün geliştirme sürecindeki karşılığı |
|---|---|
| PM / test sorumluluğu | Özellik detaylarını ve olası senaryoları netleştirmek, etkilenen alanlara göre işleri düzenlemek, test ve kabul sonuçlarını takip etmek |
| Yazılım geliştirme | Verilen görevleri tamamlamak, arayüz/servis/motor üzerindeki değişiklikleri yapmak ve geliştirici ön testlerini gerçekleştirmek |
| Ortam ve dağıtım sorumluluğu | Geliştirmenin uygun ortama alınmasını, kullanılan sürüm ve ayarların bilinmesini, test sırasında gerekli çalışma hazırlığını sağlamak |
| Anlaşılmış traderların katılımı | Preprod aşamasında özelliği gerçek kullanıcı bakışıyla sınamak ve kullanım sonuçlarını paylaşmak |

Bir özellik yalnız arayüzdeki bir alanı etkileyebilir; başka bir özellik arayüzü, merkez servisi ve strateji motorunu birlikte değiştirebilir. Görev dağılımı da bu etkiye göre yapılır. Ekran değişikliğinin tamamlanması bütün özelliğin tamamlandığı anlamına gelmez; diğer parçalar ve birlikte çalışma senaryoları da ele alınır.

## Bir özellik müşteriye nasıl ulaşır?

MTrader'ın özellik geliştirme süreci, farklı kişilerin ve ortamların katıldığı aşamalardan oluşur. **Ortam**, bir geliştirmenin hangi sistem ve sürüm üzerinde çalıştırılıp izlendiğini belirtir; test ve preprod bu akışta farklı amaçlarla kullanılır.

### Özellik detayları, senaryolar ve görevler

Önce özelliğin ne yapacağı konuşulur. Olası kullanım senaryoları, karşılaşılabilecek durumlar ve problemler değerlendirilir. Hangi ekranların, servislerin veya strateji davranışlarının etkileneceği belirlenir; görevler bu alanlara göre dağıtılır.

Bu aşamanın amacı, geliştirmenin sonunda ne beklediğimizi ortaklaştırmaktır. Örneğin bir miktar alanı eklenecekse yalnız alanın ekranda görünmesi değil, gönderilen değerin hangi davranışı değiştireceği ve mevcut emirlerle nasıl etkileşeceği de ele alınır.

### Geliştirme ve geliştiricinin ön testleri

Yazılımcılar görevlerini tamamlar ve kendi ön testlerini gerçekleştirir. Değiştirdikleri alanın beklenen şekilde çalıştığını kontrol ederler. Bu çalışma daha sonra test ortamında yapılacak izleme ve senaryo testlerinden ayrı bir aşamadır.

### Test ortamında izleme

Geliştirme test ortamına alınır; bir süre test edilir ve takip edilir. Bu aşamada çıkan hatalara müdahale edilir, düzeltmelerden sonra ilgili senaryolar yeniden değerlendirilir.

Önceki aşamalarda ve preprod'un başlangıcında düşük lot miktarlarıyla test edilir. Lot, işlem miktarının birimidir; bu bölümde “düşük” veya “yüksek” için sabit sayılar vermiyoruz. Miktarlar ilgili testin koşullarına göre değerlendirilir.

### Preprod'da traderlarla düşük lot testleri

Test ortamındaki çalışmalardan sonra geliştirme **preprod** ortamına alınır. Burada önceden anlaşılmış gerçek traderlar testlere katılır. Böylece özellik, geliştirme ekibinin senaryolarının yanında gerçek kullanıcıların kullanımından da geçer.

İlk preprod testleri düşük lotla sürer. “Gerçek trader” ifadesi burada testi yapan kişiyi anlatır; tek başına ortamın teknik bağlantısını veya bütün müşterilerin özelliği kullanmaya başladığını söylemez.

### Kararlılık sonrası yüksek lot testleri

İlk preprod testlerinde sorun çıkmaz ve ürünün kararlılığı doğrulanırsa yüksek lot miktarlarıyla testlere geçilir. Bu ölçekte de bir süre test ve izleme sürer. Dolayısıyla düşük lotta ilk testin geçmesi, bütün doğrulama sürecinin sona erdiği anlamına gelmez.

### Bütün müşterilere aktarım

Yüksek lotlu preprod testlerinde de sorun görülmezse özelliğin bütün müşterilere aktarımı sağlanır.

Bu akıştaki test süreleri ve lot sınırları burada sabitlenmez. Ayrıca bir kod branch'inin adı, testlerin tamamlandığı veya özelliğin müşterilere açıldığı bilgisinin yerine geçmez. Branch, sürüm ve dağıtımın teknik ayrıntılarını sistem mimarisi bölümünde ayrıca inceleyeceğiz.

{{< pagebreak >}}

## Testte neyi takip ederiz?

Her stratejinin amacı, giriş parametreleri ve çalışma koşulları farklıdır. Bu yüzden testin başlangıç noktası, **seçilen stratejinin belirli ayarlar ve koşullar altında ne yapmasının beklendiğini** yazmaktır. Aynı parametre adı farklı stratejilerde aynı anlama gelmeyebilir; alanın birimi, sınırları ve diğer ayarlarla ilişkisi ilgili stratejinin açıklamasından alınır.

| Takip edilen | Testte sorulacak soru |
|---|---|
| Strateji ve başlangıç durumu | Hangi strateji/mod, hesap ve ürün seçili? Senaryoyu etkileyen mevcut emir veya pozisyon var mı? |
| Girilen parametreler | Hangi değerler kullanıldı? Arayüzde girilen değerler beklenen ayarlarla eşleşiyor mu? |
| Koşullar ve olay sırası | Stratejinin değerlendirdiği piyasa, zaman veya diğer koşullar hangi sırayla oluştu? |
| Beklenen ve gözlenen davranış | Strateji işlem yapmalı mı, beklemeli mi? Oluşan emirler ve durum değişiklikleri beklentiyle uyuşuyor mu? |
| Ayar değişikliğinin etkisi | İlgili değer değiştiğinde hangi davranış değişmeli? Yeni değer ne zaman geçerli olmalı? |
| Sonuç ve izlenebilirlik | Arayüz, strateji durumu ve varsa emir/gerçekleşme kayıtları aynı sonucu gösteriyor mu? |

Önce temel bir senaryo belirler, sonra bir parametreyi değiştirerek etkisini karşılaştırırız. Ardından birbirine bağlı ayarları birlikte sınarız. İlgili alanın izin verilen sınırları, geçersiz değer girişleri ve koşulun oluşmadığı durumlar da senaryolara eklenir. Beklemek veya emir üretmemek de doğru sonuç olabilir; başarı ölçütü her zaman işlem yapılması değildir.

Başlatma, durdurma ve çalışma sırasında ayar değiştirme davranışları da stratejiye göre değerlendirilir. Her stratejinin aynı alanlara sahip olduğu veya çalışan stratejide her ayarın anında değiştirilebildiği varsayılmaz. Ayrıntılı parametre–koşul–beklenen sonuç örneklerini ileride her stratejinin kendi bölümünde açıklayacağız.

Arayüzde oturum açan **kullanıcı**, işlemin adına yapıldığı **hesap** ve işlem yapılan **ürün** de ayrı bilgilerdir. Testi açıklarken bunlara ortam, sürüm, ayarlar ve olay sırası eklenir. Böylece aynı senaryoyu tekrar çalıştırıp sonucu karşılaştırabiliriz. Paylaşılacak kayıtlarda gerçek hesap ve erişim bilgileri maskelenir.

## Strateji testleri sistem bilgisiyle nasıl birleşir?

MTrader arayüzü kullanıcı eylemlerini ve sonuçları gösterir; strateji motorları kuralları değerlendirir, ilgili emir katmanı emir iletimini ve dönüşlerini işler. Bir stratejiyi test ederken ekrandaki ayarı, arka taraftaki değerlendirmeyi ve oluşan sonucu birlikte anlamamız gerekir.

İlk bölümde MTrader'ın amacını, kullanıcılarını ve bir özelliğin geliştirmeden müşteriye ulaşmasına kadar geçen süreci tanıdık. Sıradaki bölümde ürün, lot, emir defteri ve eşleşme gibi borsa kavramlarını temelden açacağız.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı düzeltmesi, anlamı korunmuş özet:** MTrader algoritmik işlem botunun adı, MeeApps şirketin adı. Günlük kullanıcılar müşteri aracı kurumların traderları/fon yöneticileri; MeeApps günlük trade yapmıyor. Şirket, özellik detayları/senaryolar → görev dağılımı → geliştirici ön testi → test ortamı → anlaşılmış traderlarla preprod düşük lot → kararlılık sonrası yüksek lot → bütün müşterilere dağıtım akışıyla ilerliyor.

**Metne yansıması:** Önceki birleşik günlük kullanım anlatımı kaldırıldı. Müşterinin işlem günü ile MeeApps'in geliştirme/test sorumlulukları ayrıldı; preprod katılımı ve miktar artırma koşulu açıklandı. Sayısal lot sınırı, test süresi ve son onay yetkisi belirtilmediği için eklenmedi.

**24 Ekim 2026 — İkinci okuma revizyonu:** Kullanıcı, rehberin yalnız MTrader dokümanı olduğunu; MeeApps’in birden fazla ürünü bulunduğunu belirtti. Şirketin günlük kullanımını açıklayan paragraf ve tekrarlar kaldırıldı. Test anlatımı tek emir/miktar örneğinden çıkarılıp stratejiye özgü parametreler, koşullar, ayar değişiklikleri ve beklenen sonuçlar üzerinden genelleştirildi. Diğer içerik şimdilik uygun bulundu; yeni bölüm talebi verilmedi.

## Kaynaklar ve doğrulama

Ürün kimliği ve iş sürecinin tek kaynak kaydı [ürün ve geliştirme süreci](../../00-genel/urun-ve-gelistirme-sureci.md) dosyasıdır; kullanıcı beyanına dayanır. Sistem karşılıkları [sistem haritası](../../00-genel/sistem-haritasi.md), [arayüz özeti](../../10-servisler/mtrader-trade-ui/README.md) ve [emir dönüşü](../../30-akislar/emir-donusu.md) belgelerinden derlendi.

Bu tur kod yeniden incelenmedi, canlı test veya dağıtım yapılmadı. Kullanıcıdan alınan süreç bilgisi teknik ortam kanıtı olarak sunulmaz. Metin revizyon incelemesini bekleyen taslaktır.

## Devam notu

İlk bölüm kullanıcının ürün/şirket ve test süreci düzeltmeleriyle revize edildi. Okuma geri bildirimleri bekleniyor; şimdilik ikinci bölüme geçilmeyecek.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
