---
kapsam: Fiyat adımı, baz fiyat, tavan/taban; strateji fiyat sınırları ve günlük ürün verisi ayrımı
dis_kaynak:
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/sss/pay-piyasasi
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/viop/sozlesme-ozellikleri/baz-fiyat-ve-gunluk-fiyat-degisim-limitleri
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
---

# Fiyat adımı ve fiyat sınırları

Emir verirken istediğimiz her ondalıklı sayıyı fiyat olarak kullanamayız. Fiyatın hem **izin verilen adımlara** hem de ilgili ürün için geçerli **fiyat sınırlarına** uyması gerekir. Bunlar ayrı kontrollerdir.

## Fiyat adımı: hangi fiyatlara emir yazabiliriz?

**Fiyat adımı (tick size)**, geçerli fiyat seviyeleri arasındaki en küçük değişimdir. Örneğimizde adımın 0,01 TL olduğunu varsayalım: 20,00 ve 20,01 TL uygun seviyelerken 20,005 TL bu adıma uymaz. Fiyat adımına uymayan emir borsa tarafından reddedilir. [Borsa İstanbul — Pay Piyasası SSS](https://www.borsaistanbul.com/sss/pay-piyasasi)

| Örnek fiyat | Varsayımsal 0,01 TL adımına uygun mu? |
|---|---|
| 20,00 TL | Evet |
| 20,01 TL | Evet |
| 20,005 TL | Hayır |

Bir önceki konuda hesapladığımız **10,014 TL ortalama gerçekleşme fiyatı**, tek bir emrin fiyatı değildi. Farklı fiyatlardaki gerçekleşmelerin ağırlıklı ortalamasıydı. Ortalamanın adımların arasına düşebilmesi, o ortalamayla yeni emir yazılabileceğini göstermez.

Fiyat adımı ürün ve fiyat aralığına göre değişebilir. Bir üründe gördüğümüz 0,01 TL'yi bütün ürünlere sabitlemeyiz. **Bir kademe ilerlemek** ile **bir kuruş ilerlemek** her zaman aynı değildir.

## Spread ile fiyat adımı aynı mı?

Fiyat adımı, kullanılabilecek seviyeleri tanımlar. **Spread** ise o anda en iyi satış ile en iyi alış arasındaki farktır. Örneğin adım 0,01 TL, en iyi alış 20,00 TL ve en iyi satış 20,03 TL ise spread 0,03 TL, yani üç adımdır. Aradaki seviyelerde emir bulunması zorunlu değildir.

Dolayısıyla fiyat adımı değişmeden spread değişebilir. Boş bir kademe, fiyatın geçersiz olduğu anlamına gelmez; orada o anda bekleyen emir olmayabilir.

## Baz fiyat, tavan ve taban

**Baz fiyat**, günlük alt ve üst fiyat sınırlarının hesabında kullanılan referanstır. **Tavan**, üst fiyat limiti; **taban**, alt fiyat limitidir. Baz fiyatı, en iyi alış/satış veya son işlem fiyatıyla karıştırmamalıyız. Paylarda genel hesap önceki kapanışa dayanır; baz fiyat bulunmaması gibi özel durumlar ayrıca düzenlenir. [Borsa İstanbul — Piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

Hesabı anlamak için baz fiyatı 20 TL, günlük marjı **varsayımsal ±%10** kabul edelim:

| Hesap | Örnek sonuç |
|---|---|
| Alt sınır: 20 × (1 − 0,10) | 18 TL taban |
| Üst sınır: 20 × (1 + 0,10) | 22 TL tavan |

Bu oran öğretici varsayımdır; bütün payların veya vadeli sözleşmelerin güncel kuralı değildir. Hesapta sınır adımla uyuşmazsa üst limit aşağı, alt limit yukarı adıma yuvarlanır. Böylece sınırlar içeri doğru düzeltilir. [Borsa İstanbul — Piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

VİOP'ta baz fiyat, ilk işlem günü ve sonraki günler için ayrı esaslarla belirlenir; sonraki günlerde önceki normal seans uzlaşma fiyatı kullanılır. Marj sözleşme özelliklerine bağlıdır. Paydaki hesabı doğrudan vadeli ürüne kopyalamayız. [Borsa İstanbul — VİOP fiyat limitleri](https://www.borsaistanbul.com/piyasalar/viop/sozlesme-ozellikleri/baz-fiyat-ve-gunluk-fiyat-degisim-limitleri)

## Fiyat uygun olsa da işlem neden gerçekleşmez?

Örnekte 22 TL tavan fiyata alış emri vermek, kesin pay alacağımız anlamına gelmez. Satıcı yoksa emir bekleyebilir; aynı fiyatta bizden önce gelen alışlar da olabilir. Tavan/taban, fiyatın izin verilen sınırını anlatır; karşı miktar ve sıradaki yerimizi söylemez.

Tavan/taban ile **devre kesici** de farklı kavramlardır. Devre kesici, belirli koşullarda işlem yöntemini etkileyen mekanizmadır; günlük fiyat sınırının başka adı değildir. Seanslar konusunda işleyişini ayrıca ele alacağız.

## MTrader'da hangi sınırı konuşuyoruz?

Bir stratejinin “bu fiyatın üstünde alış yapma” ayarı, kullanıcının işlem tercihidir. Borsanın günlük tavanı ise ürünün o günkü sınırıdır. Testte bunları ayrı isimlendiririz: **borsa fiyat limiti** ve **stratejinin fiyat koşulu**.

Örneğin borsa tavanı 22 TL, stratejinin alış üst sınırı 21 TL olsun. 21,50 TL borsa sınırları içinde kalabilir; ama stratejinin belirlediği alış koşuluna uymaz. Borsa açısından geçerli fiyat, stratejinin mutlaka emir göndereceği fiyat değildir.

Bir fiyat testini anlatırken ürün/tarih, fiyat adımı, günlük alt/üst limit ve kullanıcı ayarı birlikte kaydedilir. Hesaplanan fiyatın adıma yuvarlanması da davranışı değiştirebilir: aşağı ve yukarı yuvarlamak farklı fiyatlar üretir. MTrader'ın her stratejide hangi yöntemi kullandığını ilgili stratejinin koduyla doğrulayacağız; burada otomatik bir düzeltme yapıldığı varsayılmıyor.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** Vadeli fiyat/teminat açıklamasının sadeleştirilerek kaydedilmesi, kredili işlemlerin ayrı başlıkta ele alınması ve sıradaki konuya devam edilmesi istendi. Bu konuya özgü soru henüz yok; sayısal fiyat ve marjlar öğretici varsayımlardır.

## Kaynaklar ve doğrulama

Borsa İstanbul'un [Pay Piyasası SSS](https://www.borsaistanbul.com/sss/pay-piyasasi), [piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi) ve [VİOP günlük limit](https://www.borsaistanbul.com/piyasalar/viop/sozlesme-ozellikleri/baz-fiyat-ve-gunluk-fiyat-degisim-limitleri) sayfaları 24 Ekim 2026'da okundu. Kullanılan genel açıklamalarda ayrı sürüm tarihi yoktur. Güncel oran/adım kataloğu hazırlanmadı; ürün ve gün bazlı gerçek limit verisi doğrulanmadı. Örnek %10 ve 0,01 TL varsayımdır. Kod veya canlı emir testi yapılmadı.

## Devam notu

Taslak yazıldı ve kitaba eklendi; kullanıcı okuması bekleniyor. Sıradaki konu [Emir tipleri ve geçerlilik süreleri](04-emir-tipleri-ve-sureleri.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
