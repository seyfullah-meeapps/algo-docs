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

### Neden iki sözleşme 42 TL etmiyor?

**21 TL, bir sözleşmenin toplam satış bedeli değil, bir adet dayanak pay için verilen vadeli fiyat teklifidir.** Emirde miktar ise sözleşme adedidir. Standart pay vadeli sözleşmesindeki **100**, bir sözleşmenin temsil ettiği pay adedidir. Bu nedenle bir sözleşme 100 × 21 = 2.100 TL, iki sözleşme 4.200 TL büyüklük taşır. 2 × 21 hesabında pay/sözleşme çarpanı eksik kalır. [Borsa İstanbul — Pay vadeli sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri)

Spot fiyatın 20 TL, vadeli fiyatın 21 TL olması başka bir ayrımdır: bunlar farklı tarihlerdeki teslim yükümlülüklerinin fiyatlarıdır. Vadeli fiyat spotla aynı olmak zorunda değildir; finansman, beklenen temettü ve piyasa koşulları gibi etkenler aradaki farkla ilişkilidir. Buradaki 1 TL fark teminat değildir.

### Teminatı ne zaman yatırıyoruz?

Vadeli pozisyon açarken 4.200 TL'lik payı hemen satın alıp teslim almayız; sözleşme yükümlülüğü üstleniriz. Pozisyon için gereken **başlangıç teminatı**, bu yükümlülüğün güvencesidir. Teminatı bir peşinat veya sözleşmenin satın alma fiyatı gibi düşünmemeliyiz. Teminat yetersizleşirse tamamlama gereği doğabilir. [Borsa İstanbul — Vadeli işlem sözleşmeleri](https://borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri)

Öğretici varsayım olarak iki sözleşme için toplam **600 TL teminat** gerektiğini düşünelim. Bu gerçek bir ürünün güncel teminatı değildir. 600 TL teminatla temsil edilen büyüklük yine 4.200 TL'dir. Teminat hesabına 600 TL koymak, kalan 3.600 TL'nin vade sonunda otomatik ödenecek sabit bir borç olduğu anlamına gelmez.

Pozisyon açıkken fiyat değişiminden doğan kâr/zarar da hesaba yansır. Örneğin 21 TL'den alınmış iki sözleşme için ilk günün uzlaşma fiyatı 22 TL olursa uzun pozisyonun o güne ait kârı (22 − 21) × 100 × 2 = **200 TL** olur. 20 TL olursa aynı hesapla **200 TL zarar** oluşur. Sonraki gün taşınan pozisyonun hesabında önceki uzlaşma fiyatı esas alınır; her gün yeniden ilk 21 TL'den fark alınmaz. [Takasbank VİOP Prosedürü, madde 41–42](https://www.takasbank.com.tr/documents/prosedurler/viop-proseduru-24012024.pdf)

Bu yüzden nakit ihtiyacı yalnız vade sonunda doğmaz. Teminat gereksinimi ve zararlar süreç boyunca takip edilir; teminatın üzerindeki kayıplar da mümkün olabilir. Gereken gerçek tutar ürün, portföy, güncel risk parametreleri ve aracı kurum koşullarına bağlıdır.

### Vade sonunda 200 payı kim teslim eder?

Pay vadeli sözleşmelerinde vade sonunda açık kalan pozisyonlar **fiziki teslimata** gider. Uzun taraf nakit ödeme, kısa taraf pay teslim etme yükümlülüğü taşır. Paylar hesaplar arasında kayden aktarılır; alıcının payları kendisinin ayrıca piyasadan bulması gerekmez. Fiziki teslimat takası Borsa İstanbul açıklamasında T+2 olarak belirtilir. Bu, aracı kurumun müşteriden parayı ancak o gün isteyeceği anlamına gelmez; kurumun önceden nakit/pay hazır bulundurma koşulları ayrıca kontrol edilir. [Borsa İstanbul — Pay vadeli sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri)

Örneği sadeleştirmek için işlemden vadeye kadar tüm uzlaşma fiyatlarının **21 TL'de kaldığını**, başka pozisyon ve masraf olmadığını varsayalım:

| Aşama | İki sözleşme uzun pozisyon için karşılığı |
|---|---|
| Pozisyon açılır | Örnek 600 TL teminat bulundurulur; 200 pay henüz teslim alınmaz |
| Pozisyon taşınır | Bu özel varsayımda fiyat değişmediği için kâr/zarar sıfırdır |
| Fiziki teslimat | 200 pay karşılığı 4.200 TL nakit yükümlülüğü yerine getirilir |
| Teminat çözülür | Gerekli koşullar tamamlanınca serbestleşen teminat kullanılabilir hâle gelir |

**600 TL teminatın teslimat ödemesine kendiliğinden sayıldığını varsaymayız.** Serbestleşme, mahsup ve kullanılabilir bakiye durumuna göre hesaba eklenecek nakit belirlenir. Fiyat değişirse günlük kâr/zarar ve teslimat hesabı birlikte değerlendirilir; yukarıdaki sabit fiyat örneği aynen uygulanmaz.

Vade gelmeden aynı sözleşmedeki pozisyon uygun ters işlemle kapatılırsa kapanan miktar için teslim yükümlülüğü kalmaz. Örneğin iki sözleşme uzun pozisyonun aynı vadede iki sözleşme satılarak kapatılmasıyla sonuç kâr/zarar üzerinden oluşur. Ayrıca her vadeli ürün pay teslim etmez: **nakdi uzlaşmalı** sözleşmelerde sonuç para üzerinden kapatılır. [Borsa İstanbul — Vadeli işlem sözleşmeleri](https://borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri)

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

## Kaynaklar ve doğrulama

- Borsa İstanbul, [Pay Piyasası — Ürünler](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/urunler): pay, BYF ve varant tanımları. Erişim: 24 Ekim 2026.
- Borsa İstanbul, [VİOP sıkça sorulan sorular](https://www.borsaistanbul.com/sss/viop): piyasa, türev ve sözleşme kodu açıklamaları. Erişim: 24 Ekim 2026.
- Borsa İstanbul, [Pay vadeli işlem sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri): standart büyüklük ve standart olmayan sözleşme istisnası. Erişim: 24 Ekim 2026.

Takasbank PDF’si dosya adında 24 Ocak 2024 tarihini taşır; güncel prosedür sürümünün bütünüyle karşılaştırılması yapılmadı, yalnız günlük kâr/zarar mekanizması için kullanıldı.

Web sayfalarında kullanılan tanımlar için ayrı sürüm/yürürlük tarihi belirtilmiyor; erişim tarihi kaydedildi. Seans saatleri ve güncel teminat oranları kapsam dışıdır. Pay vadeli teslimatına ilişkin T+2 bilgisi ilgili BIST sayfasından okundu; diğer ürünlere genellenmez. Sayısal örnek belirli bir gerçek ürünün güncel işlem koşulu olarak sunulmaz. MTrader bağlantısı kavramsaldır; bu tur kaynak kod, alan dönüşümü veya canlı ortam testi yapılmadı.

## Devam notu

Konu taslak yazıldı ve kitaba eklendi; henüz kullanıcı okumasından geçmedi. Sıradaki konu [Emir defteri ve eşleşme](02-emir-defteri.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
