---
kapsam: BIST, Pay Piyasası, VİOP; pay, endeks, vadeli, varant, BYF; miktar ve sözleşme büyüklüğü
dis_kaynak:
  - url: https://borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri
    erisim: 2026-10-24
  - url: https://www.takasbank.com.tr/documents/prosedurler/viop-proseduru-24012024.pdf
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/urunler
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/sss/viop
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# Piyasalar, ürünler ve miktar birimleri

MTrader'da bir stratejiyi anlamanın ilk adımı, **hangi ürün üzerinde işlem yaptığını** bilmektir. Ürünün fiyatı neyi gösteriyor, girilen miktar neyin adedi ve başka bir ürünle nasıl ilişkilendiriliyor? Aynı sayılar, farklı ürünlerde farklı büyüklükleri ifade edebilir.

## Borsa, piyasa ve ürün

**Borsa İstanbul**, farklı piyasaların bulunduğu borsadır; BIST kısaltmasıyla da karşılaşırız. **Piyasa**, belirli araçların kendi işlem kurallarıyla alınıp satıldığı yapıdır. **Ürün** veya **enstrüman** ise üzerinde işlem yaptığımız finansal araçtır.

Bu rehberde önce iki piyasaya odaklanacağız:

| Piyasa | Temel karşılığı |
|---|---|
| Pay Piyasası | Şirket payları, borsa yatırım fonları ve varantlar gibi araçların işlem gördüğü piyasa |
| Vadeli İşlem ve Opsiyon Piyasası (VİOP) | Bir dayanak varlığa bağlı vadeli işlem ve opsiyon sözleşmelerinin işlem gördüğü piyasa |

Pay Piyasası'nın adı, oradaki her ürünün şirket payı olduğu anlamına gelmez. Benzer biçimde, VİOP tek bir ürünün adı değildir. Bu ayrım Borsa İstanbul'un [ürün tanıtımları](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/urunler) ve [VİOP açıklamalarında](https://www.borsaistanbul.com/sss/viop) görülebilir.

## Karşılaşacağımız ürünler ve göstergeler

**Pay (hisse senedi)**, bir şirkette ortaklık payını temsil eder. **Borsa yatırım fonu (BYF)** ise payları borsada işlem gören, bir endeksin performansını izlemeyi amaçlayan fondur. BYF almak, tek bir şirketin payını almakla aynı şey değildir.

**Endeks**, belirli araçların performansını bir hesaplama yöntemiyle gösteren değerdir. Örneğin BIST 30 bir endekstir. Endeksin kendisi ile endekse dayalı vadeli sözleşme ayrı kavramlardır. Emir verirken işlem gören aracın kendisi seçilir.

**Vadeli işlem sözleşmesi**, belirlenmiş koşullarla ileri bir tarihe ilişkin alım-satım yükümlülüğü doğuran sözleşmedir. Değerinin bağlı olduğu pay, endeks veya başka varlığa **dayanak varlık** denir. Aynı dayanağın farklı vadelerdeki sözleşmeleri ayrı ürünlerdir; vade, sözleşmenin zaman bilgisidir. VİOP'ta sözleşme kodu da dayanak ve vade bilgilerini içerir. [Borsa İstanbul — VİOP](https://www.borsaistanbul.com/sss/viop)

**Varant**, belirlenmiş koşullarda bir dayanak varlığı alma veya satma hakkı veren araçtır. Varant almak, doğrudan dayanak payı almak değildir; hakkın kendi fiyatı ve vadesi vardır. Pay, BYF ve varant tanımları için [Borsa İstanbul — Ürünler](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/urunler).

## Lot, adet ve sözleşme büyüklüğü

**Lot**, işlem miktarını ifade ederken karşılaşacağımız birimdir. Ancak miktarın ekonomik karşılığını anlamak için ürünün özelliklerini de bilmek gerekir. Ekrandaki “10” değerini, ürüne bakmadan “10 pay” diye okuyamayız.

Vadeli işlemlerde **sözleşme adedi**, kaç sözleşme alınıp satıldığını gösterir. **Sözleşme büyüklüğü** ise bir sözleşmenin ne kadar dayanak varlığı temsil ettiğini belirtir. Fiyatla miktarı ilişkilendiren **çarpan** da sözleşme özelliklerine bağlıdır; her ürüne tek bir sabit sayı uygulanmaz.

Borsa İstanbul'un standart pay vadeli sözleşme tanımında **bir sözleşme 100 payı temsil eder**. Özsermaye halleri nedeniyle büyüklüğü farklılaşan standart olmayan sözleşmeler de bulunabilir. Dolayısıyla 100 sayısını bütün vadeli ürünlere veya her sözleşmeye genelleyemeyiz. [Pay vadeli işlem sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri)

### Basit bir miktar örneği

Bir test örneğinde, birim fiyatı 20 TL olan 200 adet pay ile aynı paya dayalı 2 standart vadeli sözleşmeyi düşünelim. Vadeli sözleşmenin fiyatını da örnek için 21 TL kabul edelim.

| Hesap | Sonuç |
|---|---|
| Pay alımının işlem tutarı: 200 adet × 20 TL | 4.000 TL |
| Vadeli tarafta temsil edilen miktar: 2 sözleşme × 100 pay | 200 pay |
| Vadeli pozisyonun nominal değeri: 2 × 100 × 21 TL | 4.200 TL |

Fiyatlar öğretici varsayımdır; komisyonlar hesaba katılmamıştır. Tablo iki alternatif işlemi karşılaştırır; iki tarafın birlikte alınmasını önermiyor.

### Vadeli işlem açarken 21 TL ödüyor muyuz?

**Hayır. Ekrandaki 21 TL, hesabımızdan kesilen sözleşme ücreti değildir.** Bir pay için üzerinde anlaştığımız vadeli fiyattır. Emir miktarı ise sözleşme adediyle girilir. Bir standart pay vadeli sözleşmesi 100 payı temsil ettiği için toplam büyüklük 100 × 21 = **2.100 TL** olur. İki sözleşme için bu değer 4.200 TL'dir. [Borsa İstanbul — Pay vadeli sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri)

Bir sözleşme aldığımızda “vadesi geldiğinde bu 100 payı, pay başına 21 TL üzerinden alma yükümlülüğünü kabul ediyorum” deriz. Başlangıçta bir pay satın almış olmayız; sonradan ödenecek “kalan 99 pay” da yoktur. Pozisyon açılışında paylar hesabımıza geçmez.

### Kendi paramız ve teminat nasıl değişir?

Başlangıçta **5.000 TL kendi paramız** olduğunu düşünelim. Aşağıdaki iki işlem birbirinin alternatifidir; birlikte yapılmıyor. Komisyon ve diğer masrafları yok sayıyoruz. Bir sözleşmenin teminatını tamamen öğretici varsayım olarak **300 TL** kabul ediyoruz; bu, gerçek bir ürünün güncel teminatı değildir.

| Seçenek | Paranın ve pozisyonun karşılığı |
|---|---|
| Spotta 20 TL'den 100 pay almak | 2.000 TL alış bedeli oluşur; takas yükümlülüğü karşılandıktan sonra 3.000 TL nakit ve 100 pay kalır |
| 21 TL'den 1 vadeli sözleşme almak | 300 TL teminat ayrılır, 4.700 TL bunun dışında kalır; henüz payımız yoktur, 100 paylık vadeli pozisyonumuz vardır |

Vadeli seçenekte **21 TL veya 2.100 TL satın alma bedeli ödemedik**. 300 TL güvence ayırdık. **Teminat**, sözleşme yükümlülüğünün güvencesidir; peşinat değildir. Pozisyon için başlangıç teminatı gerekir ve teminat yetersizleştiğinde tamamlama ihtiyacı doğabilir. [Borsa İstanbul — Vadeli işlem sözleşmeleri](https://borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri)

### Vade sonunda ne öder, ne alırız?

Bu kez fiyatın işlemden vadeye kadar **21 TL'de kaldığını**, günlük kâr/zarar ve masraf oluşmadığını varsayalım. Bir pay vadeli uzun pozisyonu teslimata bıraktığımızda 100 pay için **2.100 TL nakit yükümlülüğünü** karşılarız; 100 pay hesabımıza kayden aktarılır. Payları ayrıca piyasadan bizim bulmamız gerekmez. Başta 21 TL ödemediğimiz için geri alınacak bir “vadeli ücreti” de yoktur.

Pay vadeli sözleşmeleri fiziki teslimatlıdır; Borsa İstanbul bu teslimatın takasını T+2 olarak açıklar. Aracı kurum paranın daha önce hazır bulunmasını isteyebilir; müşterinin son ödeme saati ayrıca öğrenilir. [Borsa İstanbul — Pay vadeli sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri)

300 TL teminat, ilgili yükümlülükler tamamlanıp serbestleştiğinde kullanılabilir hâle gelir. Bunun teslimat ödemesine ne zaman mahsup edilebildiğini bilmeden “yalnız 1.800 TL yeter” diyemeyiz. Bu sade örneğin sonunda, bütün yükümlülükler ve teminat blokajı çözüldüğünde **2.900 TL para + 100 pay** kalır. Teminat ayrıca kaybolmuş 300 TL değildir.

### Fiyat değişirse ne olur?

Vadeli pozisyonun kâr/zararı süreç boyunca hesaplanır. İlk gün 21 TL'den açılmış bir uzun sözleşmenin uzlaşma fiyatı 22 TL olursa (22 − 21) × 100 = **100 TL kâr**; 20 TL olursa **100 TL zarar** oluşur. Sonraki gün taşınan pozisyonun hesabında önceki uzlaşma fiyatı kullanılır. Bu yüzden nakit ihtiyacı için yalnız vade sonunu beklemeyiz. [Takasbank VİOP Prosedürü, madde 41–42](https://www.takasbank.com.tr/documents/prosedurler/viop-proseduru-24012024.pdf)

Fiyat değişen durumda günlük kâr/zarar ile teslimat ödemesi birlikte değerlendirilir; yukarıdaki sabit fiyat örneği aynen uygulanmaz. Vade öncesinde aynı sözleşmede uygun ters işlemle pozisyon kapatılırsa kapanan miktar için teslim yükümlülüğü kalmaz. Her vadeli ürün de pay teslim etmez; nakdi uzlaşmalı sözleşmelerde sonuç para üzerinden kapatılır. [Borsa İstanbul — Vadeli işlem sözleşmeleri](https://borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri)

### Kredili pay alımıyla farkı

**Kredi limiti**, kurumun izin verdiği borçlanma kapasitesidir; **kullanılmış kredi**, gerçekten borç aldığımız tutardır. Örneğin 2.000 TL'lik spot pay alımının 1.000 TL'si kendi paramızdan, 1.000 TL'si krediden karşılanırsa 100 payımızın yanında 1.000 TL kredi borcumuz olur; kredi koşullarına göre faiz işler.

Vadeli pozisyonun 2.100 TL büyüklük taşıması ise otomatik olarak 2.100 TL kredi kullandığımız anlamına gelmez. Buradaki kaldıraç, teminatla daha büyük bir yükümlülük taşımamızdan doğar. Pay alımında kullanılabilen kredi limitinin VİOP teminatında da kullanılabildiği varsayılmaz. Kurumun kabul ettiği teminat ve hesap aktarım düzeni ayrıca bilinmelidir.

Kredi limiti, kredi borcu, faiz, özkaynak ve kullanılabilir bakiye ilişkisini [pozisyon ve bakiye konusundaki ayrı başlıkta](07-pozisyon-bakiye-kar-zarar.md) ele alacağız.

## MTrader'da neden önemli?

**Ürün, üzerinde işlem yapılan araçtır; strateji, o araçla ne yapılacağını belirleyen kurallardır.** Örneğin bir pay üzerinde HFT veya tavan stratejisinin çalışması, ürünün kimliğini değiştirmez; değişen, hangi koşullarla işlem yapılacağıdır.

Bir strateji ayarını veya test senaryosunu okurken önce ürünün kimliğini, piyasa bilgisini, miktar birimini ve varsa vadesini netleştiririz. İki ürün kullanan bir senaryoda her iki taraf için bunu ayrı yaparız. “İki tarafa da 10 girdik” ifadesi, iki tarafta aynı büyüklükte işlem beklendiğini tek başına açıklamaz.

Bu temel, sonraki strateji belgelerinde parametrelerin anlamını doğru okumamızı sağlayacak. Şimdi ürünün alış ve satış emirlerinin nasıl bir araya geldiğine, yani **emir defterine ve eşleşmeye** geçebiliriz.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** “Tamam çok güzel sıradaki bölüme geçebiliriz yazmaya.” İlk bölüm revizyonlarından sonra borsa temellerine geçildi. Bu konuya özgü bir soru henüz sorulmadı; miktar örneği agent tarafından eğitim amacıyla hazırlandı.

**24 Ekim 2026 — Kullanıcı sorusu, anlamı korunmuş özet:** BYF kullanılmayan bir strateji olmasına rağmen neden sık geçiyor; borsada gerçekten BYF var mı, uygulamadaki BYF ile ilişkili mi?

**Yanıt:** BYF, Borsa Yatırım Fonu adlı gerçek ürün türüdür. Mevcut teknik KB taslağında MTrader’ın FundTracker/Fon Takibi stratejisi bu fon ve sepeti arasındaki ilişkiyi kullanır; ürün ile strateji aynı şey değildir. Teknik KB 22 Ekim referanslarına dayanır, bu tur kod yeniden incelenmedi. Kullanıcı stratejinin kullanılmadığını belirtti; kodda bulunması aktif kullanım kanıtı sayılmaz. Genel anlatımda BYF vurgusu azaltılmalı, örnekler öncelikli stratejilere hizmet etmeli. Kullanıcı önce yanıt istediği için bu tur yeni konu yazılmadı ve okuma çıktısı değiştirilmedi.

**24 Ekim 2026 — Kullanıcı sorusu, anlamı korunmuş özet:** Spot 20 TL, vadeli 21 TL iken iki sözleşme neden 42 TL değil? 100 neyi ifade ediyor; teminat nerede, kalan para ne zaman yatırılıyor ve 200 pay nasıl teslim alınıyor?

**Metne yansıması:** Pay başına fiyat kotasyonu ile sözleşme adedi ayrıldı. Varsayımsal 600 TL teminat, günlük uzlaşma kâr/zararı ve sabit 21 TL vade örneğiyle ödeme/teslim süreci açıklandı. Teminat otomatik peşinat sayılmadı; kurumun nakit hazırlık zamanı için evrensel bir saat uydurulmadı.

**24 Ekim 2026 — İkinci açıklama ve kullanıcı geri bildirimi:** Kullanıcı 21 TL'nin başlangıçta ödenip ödenmediğini, kalan 99 pay ve kredi bakiyesi ilişkisini sordu. Sohbette tek sözleşme, 5.000 TL nakit ve varsayımsal 300 TL teminatla sade anlatım yapıldı. Kullanıcı bu anlatımı anladığını belirtti ve dokümana aynı sadelikte aktarılmasını istedi. Önceki uzun örnek bu anlatımla değiştirildi; kredili işlemler için bakiye konusunda ayrı başlık planlandı. Kuruma özgü bakiye alanları açıklanmış sayılmaz.

## Kaynaklar ve doğrulama

- Borsa İstanbul, [Pay Piyasası — Ürünler](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/urunler): pay, BYF ve varant tanımları. Erişim: 24 Ekim 2026.
- Borsa İstanbul, [VİOP sıkça sorulan sorular](https://www.borsaistanbul.com/sss/viop): piyasa, türev ve sözleşme kodu açıklamaları. Erişim: 24 Ekim 2026.
- Borsa İstanbul, [Pay vadeli işlem sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri): standart büyüklük ve standart olmayan sözleşme istisnası. Erişim: 24 Ekim 2026.

Takasbank PDF’si dosya adında 24 Ocak 2024 tarihini taşır; güncel prosedür sürümünün bütünüyle karşılaştırılması yapılmadı, yalnız günlük kâr/zarar mekanizması için kullanıldı.

Web sayfalarında kullanılan tanımlar için ayrı sürüm/yürürlük tarihi belirtilmiyor; erişim tarihi kaydedildi. Seans saatleri ve güncel teminat oranları kapsam dışıdır. Pay vadeli teslimatına ilişkin T+2 bilgisi ilgili BIST sayfasından okundu; diğer ürünlere genellenmez. Sayısal örnek belirli bir gerçek ürünün güncel işlem koşulu olarak sunulmaz. MTrader bağlantısı kavramsaldır; bu tur kaynak kod, alan dönüşümü veya canlı ortam testi yapılmadı.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
