---
kapsam: BIST, Pay Piyasası, VİOP; pay, endeks, vadeli, varant, BYF; miktar ve sözleşme büyüklüğü
dis_kaynak:
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

**Endeks**, belirli araçların performansını bir hesaplama yöntemiyle gösteren değerdir. Örneğin BIST 30 bir endekstir. “Endeks değeri”, “o endeksi izleyen BYF” ve “endekse dayalı vadeli sözleşme” ayrı kavramlardır. Emir verirken işlem gören aracın kendisi seçilir.

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

Fiyatlar öğretici varsayımdır; komisyonlar hesaba katılmamıştır. **Nominal değer**, pozisyonun temsil ettiği büyüklüktür; vadeli işlem için yatırılan teminatla aynı kavram değildir. **Teminat**, yükümlülükleri karşılamak amacıyla bulundurulan güvencedir. Burada teminat veya kâr hesabı yapmıyoruz.

İki tarafta aynı dayanak adedine ulaşmak, fiyatların veya bütün risklerin eşitlendiğini göstermez. Örneğin farklı vade seçmek işlemin anlamını değiştirir. Arbitrajı anlatırken bu ilişkiyi daha ayrıntılı kuracağız.

## MTrader'da neden önemli?

**Ürün, üzerinde işlem yapılan araçtır; strateji, o araçla ne yapılacağını belirleyen kurallardır.** Örneğin BYF bir ürün türüdür; BYF üzerinde çalışan stratejinin mantığı ayrıca açıklanır. Aynı şekilde, varantın tanımı ile MTrader'daki varant stratejisinin ayarları ayrı konulardır.

Bir strateji ayarını veya test senaryosunu okurken önce ürünün kimliğini, piyasa bilgisini, miktar birimini ve varsa vadesini netleştiririz. İki ürün kullanan bir senaryoda her iki taraf için bunu ayrı yaparız. “İki tarafa da 10 girdik” ifadesi, iki tarafta aynı büyüklükte işlem beklendiğini tek başına açıklamaz.

Bu temel, sonraki strateji belgelerinde parametrelerin anlamını doğru okumamızı sağlayacak. Şimdi ürünün alış ve satış emirlerinin nasıl bir araya geldiğine, yani **emir defterine ve eşleşmeye** geçebiliriz.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** “Tamam çok güzel sıradaki bölüme geçebiliriz yazmaya.” İlk bölüm revizyonlarından sonra borsa temellerine geçildi. Bu konuya özgü bir soru henüz sorulmadı; miktar örneği agent tarafından eğitim amacıyla hazırlandı.

## Kaynaklar ve doğrulama

- Borsa İstanbul, [Pay Piyasası — Ürünler](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/urunler): pay, BYF ve varant tanımları. Erişim: 24 Ekim 2026.
- Borsa İstanbul, [VİOP sıkça sorulan sorular](https://www.borsaistanbul.com/sss/viop): piyasa, türev ve sözleşme kodu açıklamaları. Erişim: 24 Ekim 2026.
- Borsa İstanbul, [Pay vadeli işlem sözleşmeleri](https://www.borsaistanbul.com/piyasalar/viop/vadeli-islem-sozlesmeleri/pay-vadeli-islem-sozlesmeleri): standart büyüklük ve standart olmayan sözleşme istisnası. Erişim: 24 Ekim 2026.

Web sayfalarında kullanılan tanımlar için ayrı sürüm/yürürlük tarihi belirtilmiyor; erişim tarihi kaydedildi. Seans saatleri, güncel teminat oranları veya takas süreleri bu konunun kapsamında değildir. Sayısal örnek belirli bir gerçek ürünün güncel işlem koşulu olarak sunulmaz. MTrader bağlantısı kavramsaldır; bu tur kaynak kod, alan dönüşümü veya canlı ortam testi yapılmadı.

## Devam notu

Konu taslak yazıldı ve kitaba eklendi; henüz kullanıcı okumasından geçmedi. Sıradaki konu [Emir defteri ve eşleşme](02-emir-defteri.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
