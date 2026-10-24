---
kapsam: Long/short/flat, açık emir maruziyeti, nakit ve kıymet bakiyeleri, maliyet, kâr/zarar ve kredili işlemler
dis_kaynak:
  - url: https://mevzuat.spk.gov.tr/api/Mevzuat/File/249
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/files/VIOP-Hakkinda-SSS.pdf
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
---

# Pozisyon, bakiye ve kâr/zarar

Bir ekranda görülen “bakiye” tek başına yeterli bir açıklama değildir. **Kaç ürünümüz var, kaç para harcayabiliriz, ne kadar borcumuz var ve bekleyen emirlerimiz ne kadar yükümlülük doğurabilir?** Bunları ayrı okumamız gerekir.

## Pozisyon: ne kadar taşıyoruz?

**Uzun (long)** pozisyon, ilgili üründe alış yönündeki pozisyondur. **Kısa (short)** pozisyon satış yönündedir; spotta açığa satış, vadelide kısa sözleşme gibi farklı yollarla oluşabilir. **Flat**, ilgili ürün ve hesap bağlamında net pozisyonun sıfır olmasıdır. Vadeli pozisyonun spot pay sahipliği olmadığını önceki miktar örneğinde gördük. [Borsa İstanbul — VİOP soru ve cevapları](https://www.borsaistanbul.com/files/VIOP-Hakkinda-SSS.pdf)

Başlangıçta 0 payımız varken 100 adet alıp 40 adet satarsak **60 adet** kalır. Başka bir üründe ters pozisyon taşımamız bu üründeki 60 adedi yok etmez. “Portföy dengeli” ile “her üründe flat” aynı şey değildir.

## Bekleyen emir de gelecekteki büyüklüğü etkiler

60 adet payımız varken 100 adet alış emrimiz bekliyorsa, henüz 160 adet sahibi değiliz. Ama emir bütünüyle gerçekleşirse 160 adede çıkabiliriz. Bu olası büyüklüğe **maruziyet** açısından bakarız.

| Bilgi | Örnekteki karşılığı |
|---|---:|
| Gerçekleşmiş net pozisyon | 60 adet |
| Bekleyen alış | 100 adet |
| Alışın tamamı gerçekleşirse pozisyon | 160 adet |

Bekleyen emirleri yok saymak risk değerlendirmesini eksik bırakır. Tersine, bekleyen emri gerçekleşmiş gibi pozisyona eklemek de gerçek durumla beklentiyi karıştırır.

## Hangi bakiye?

| Terim | Sorulacak soru |
|---|---|
| Nakit | Hesapta hangi para var, hangisi blokeli veya takasta? |
| Kullanılabilir alış gücü | Yeni emir için kurum hangi tutara izin veriyor? |
| Çekilebilir nakit | Hesaptan dışarı şu anda ne kadar aktarılabilir? |
| Satılabilir kıymet | Hangi üründen ne kadar satış yapılabilir? |
| VİOP serbest teminatı | Risk yükümlülükleri dışında ne kadar teminat kullanılabilir? |

Bunlar kavramsal adlardır; MTrader'daki alan adlarının birebir sözlüğü değildir. Bir kurumun alış gücüne kredi limiti katması, aynı tutarın çekilebilir nakit olduğu anlamına gelmez. Satış bedelinin ekranda görünmesi de takasın bittiği anlamına gelmez. Ayrıntılı kurum hesabı olmadan bu sütunları birbirine eşitlemeyiz.

## Kâr/zarar: gerçekleşmiş mi, değerleme mi?

100 payı 20 TL'den aldığımızı, masrafları şimdilik dışarıda bıraktığımızı düşünelim:

| Olay | Hesap | Sonuç |
|---|---|---:|
| Fiyat 22 TL oldu; henüz satmadık | 100 × (22 − 20) | 200 TL gerçekleşmemiş kâr |
| 40 payı 22 TL'den sattık | 40 × (22 − 20) | 80 TL gerçekleşmiş kâr |
| Kalan 60 pay 22 TL ile değerleniyor | 60 × (22 − 20) | 120 TL gerçekleşmemiş kâr |

Satışın 880 TL tutması, 880 TL kâr ettiğimiz anlamına gelmez; sattığımız payların 800 TL alış maliyeti vardı. Farklı fiyatlarla birden çok alış yapılırsa maliyet yöntemi de tanımlanmalıdır. Ekrandaki değerleme fiyatı son işlem, alış veya başka bir referans olabilir; hangi fiyatın kullanıldığı bilinmeden iki kâr/zarar rakamı karşılaştırılmaz.

**Net sonuç** hesabında komisyon, kredi faizi ve ilgili diğer masraflar da hesaba girer. Fiyat farkından çıkan brüt 80 TL'nin tamamı net kazanç olmayabilir. VİOP'ta günlük uzlaşmayla hesaba yansıyan kâr/zarar mekanizması spotta yalnız ekranda görülen değerleme farkıyla aynı değildir.

## Kredili işlemler: limit, borç ve özkaynak

**Kredi limiti**, borçlanma iznidir; **kullanılmış kredi**, gerçekten kullanılan borçtur. Hesabımızda 5.000 TL kendi paramız ve 5.000 TL kullanılabilir kredi limiti olsun. Kredili işleme izin verilen koşullarda 10.000 TL'lik pay aldığımızı varsayalım:

| İşlem sonrası | Tutar |
|---|---:|
| Payların o andaki değeri | 10.000 TL |
| Kullandığımız kredi borcu | 5.000 TL |
| Basitleştirilmiş özkaynak: varlık − borç | 5.000 TL |

Burada 10.000 TL'nin hepsi kendi paramız değildir. Payların değeri 8.000 TL'ye düşse borç kendiliğinden 4.000 TL'ye düşmez: masraf/faiz yok varsayımıyla borç 5.000 TL, özkaynak 3.000 TL olur. Özkaynak oranı bu basit örnekte 3.000 / 8.000 = **%37,5**'tir. Krediyle işlem, fiyat düşüşünün kendi paramıza oranla etkisini büyütür.

Gerçek özkaynak hesabında kabul edilen kıymetler ve değerleme kuralları önemlidir. Özkaynak azalınca tamamlama gereği ve sözleşmedeki işlemler gündeme gelebilir. Başlangıç/sürdürme oranları, faiz ve krediye uygun ürünler güncel düzenleme ile kurum sözleşmesinden alınır; bu örnek izin veya oran tablosu değildir. [SPK — Kredili alım, açığa satış ve ödünç işlemleri Tebliği](https://mevzuat.spk.gov.tr/api/Mevzuat/File/249)

## Kredili spot ile VİOP teminatını ayıralım

Kredili spotta finansman için borç kullanır, pay alırız. VİOP'ta ise sözleşme yükümlülüğü için teminat taşırız. Vadeli pozisyonun nominal büyüklüğü otomatik kredi borcu değildir. “Kredi limitim var” bilgisinden bu limitin VİOP teminatına aktarılabileceği sonucu çıkmaz.

Tek sözleşme ve 300 TL varsayımsal teminatla hazırladığımız [sade vadeli örneği](01-piyasalar-ve-urunler.md) bu farkı gösteriyor. Burada tekrar bir teminat yüzdesi belirlemiyoruz. Kuruma göre para aktarımı, kabul edilen teminat, blokaj ve çekilebilir tutar ayrı doğrulanmalıdır.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi, anlamı korunmuş özet:** Borsa tarafının kalan konuları topluca tamamlansın; kullanıcı bölümün tamamını okuyup birlikte revize edecek. Bu dosya bu kapsamda taslak yazıldı; ayrı bir konu sorusu henüz yok. Örnekler agent tarafından eğitim amacıyla oluşturuldu.

## Kaynaklar ve doğrulama

SPK Seri V No 65 resmi derlemesinin kredili işlem/özkaynak çerçevesi ve BIST VİOP eğitim belgesinin uzun/kısa ve teminat bağlamı okundu; erişim 24 Ekim 2026. Derlemelerdeki tarihli istisna oranları güncel limit olarak aktarılmadı. Formüller öğretici, sade portföy varsayımlarıdır; müşteri sözleşmesi veya MTrader alan eşlemesi doğrulanmadı. Kullanıcının kredili işlemler için ayrı başlık talebi bu dosyada karşılandı.

Bu tur MTrader kaynak kodu, canlı binary/config veya gerçek işlem testi yapılmadı. Projeye ilişkin bağlantılar mevcut KB taslaklarına dayanır; bunlar yeni kod doğrulaması değildir.

## Devam notu

Bölüm topluca okunacak; kurum bakiyeleri için teknik/kurumsal veri gerektiğinde ayrıca sorulacak.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
