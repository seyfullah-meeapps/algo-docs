---
kapsam: Emir defteri, bid/ask, spread, kademe, likidite, fiyat-zaman önceliği, kuyruk, header ve erime
dis_kaynak:
  - url: https://www.borsaistanbul.com/sss/pay-piyasasi
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# Emir defteri ve eşleşme

Bir ürünü almak isteyenlerle satmak isteyenler farklı fiyatlar önerebilir. **Emir defteri (order book)**, işlem için bekleyen alış ve satış emirlerinin düzenidir. “Tahta” ifadesini de bir ürünün işlem sırası veya emir defteri için duyabiliriz.

Bu konuda Pay Piyasası'nda **sürekli işlem** sırasında, normal limit emirlerden oluşan basit bir defteri ele alıyoruz. Limit emir, alışta ödemeyi kabul ettiğimiz en yüksek; satışta kabul ettiğimiz en düşük fiyatı belirtir. Açılışta veya tek fiyat yöntemindeki emir toplama ve eşleşme süreçlerini seanslar konusunda ayrıca anlatacağız. [Borsa İstanbul — Piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

## Alış, satış ve en iyi fiyat

**Bid**, alış tarafıdır; **ask** veya **offer**, satış tarafıdır. Alıcı için daha yüksek fiyat, satıcı için daha düşük fiyat önceliklidir. Bu nedenle defterin en iyi alışı en yüksek alış fiyatı, en iyi satışı en düşük satış fiyatıdır.

Aşağıdaki tablo hayali bir payın o andaki görünür derinliğidir. Miktarlar adet olarak verilmiştir; fiyatlar öğretici örnektir.

| Alış miktarı | Alış fiyatı (TL) | Satış fiyatı (TL) | Satış miktarı |
|---:|---:|---:|---:|
| 500 | 10,00 | 10,01 | 300 |
| 800 | 9,99 | 10,02 | 700 |
| 1.200 | 9,98 | 10,03 | 900 |

En iyi alış **10,00 TL**, en iyi satış **10,01 TL**. İki fiyat arasındaki fark **spread** olarak adlandırılır: bu örnekte 0,01 TL'dir. Alış ve satış sütunlarının aynı satırda bulunması, o iki taraftaki emirlerin eşleştiğini göstermez. Alıcı 10,00 TL önerirken satıcı en az 10,01 TL istediği için beklerler.

**Son işlem fiyatı**, en son gerçekleşen işlemin fiyatıdır. En iyi alış ve satış ise şu anda bekleyen emirleri anlatır; üçü aynı bilgi değildir.

## Kademe ve derinlik

**Kademe**, belirli bir fiyat seviyesidir. Tabloda 10,01 TL'deki 300 adet, o fiyatta görünen satış miktarının toplamıdır; tek bir emir veya tek bir satıcı olmak zorunda değildir. **Derinlik**, farklı fiyat seviyelerindeki bekleyen miktarları birlikte görmemizi sağlar.

**Likidite**, bir üründe işlem yapabilme kolaylığıyla ilgilidir. Dar spread ve yeterli karşı miktar bu açıdan önemlidir. Yine de görünen miktarlar değişebilir: yeni emir gelebilir, mevcut emir iptal edilebilir veya gerçekleşebilir. Ekrandaki görüntü, emrimiz borsaya ulaşana kadar aynı kalma garantisi vermez.

## Emirler hangi sırayla karşılanır?

Borsa İstanbul Pay Piyasası'nda **fiyat-zaman önceliği** uygulanır. Önce daha iyi fiyatlı emir, aynı fiyatta ise sisteme daha önce kaydedilen emir önceliklidir. Alışta yüksek, satışta düşük fiyat daha iyidir. [Borsa İstanbul — Pay Piyasası SSS](https://www.borsaistanbul.com/sss/pay-piyasasi)

Örneğin 10,00 TL alış seviyesinde önce A emriyle 200, sonra B emriyle 300 adet gelmiş olsun. Tabloda toplam 500 görürüz; fakat bu miktarın içinde bir sıra vardır. Bu seviyeye 250 adetlik satış geldiğinde, diğer koşullar değişmiyorsa A'nın 200 adedi ve B'nin 50 adedi karşılanır. B'nin 250 adedi beklemeye devam eder.

Aynı fiyata sonradan alış yazmak, sıranın başına geçmek anlamına gelmez. Testlerde yalnız toplam kademe miktarına bakarak kendi emrimizin kesin sırasını veya ne zaman gerçekleşeceğini söyleyemeyiz.

## Bir alış emri defterde nasıl ilerler?

İlk tablodaki deftere dönelim. Başka emir veya iptal gelmediğini ve örnek emrin borsa kontrollerinden geçtiğini varsayalım. **10,02 TL limit fiyatlı 500 adet alış** gönderiyoruz:

| Adım | Gerçekleşme | Kalan alış miktarı |
|---|---|---:|
| En iyi satış karşılanır | 300 adet × 10,01 TL | 200 |
| Sonraki uygun satış seviyesi karşılanır | 200 adet × 10,02 TL | 0 |

Alışın limiti 10,02 TL olsa da ilk 300 adet daha iyi olan 10,01 TL'den gerçekleşir. Toplam tutar 5.007 TL, ortalama gerçekleşme fiyatı **10,014 TL** olur. Bu ortalama, iki seviyedeki işlemlerin miktarla ağırlıklandırılmış sonucudur; tek başına bir emir fiyatı değildir.

Limitimiz 10,01 TL olsaydı 10,02 TL'deki satışları alamazdık. Aynı 500 adetlik emrin 300 adedi gerçekleşir; kalan 200 adedin bekleyip beklemeyeceği emrin geçerlilik koşuluna bağlı olurdu. Emir tipleri ve geçerlilik sürelerini kendi konusunda açacağız.

Karşıdaki bekleyen emri hemen karşılayan emre **agresif**, defterde karşılanmayı bekleyene **pasif** diyebiliriz. Agresif davranış için mutlaka piyasa emri kullanılması gerekmez; örneğimizdeki limit alış da karşı satışlarla işlem yapar.

## Header ve erime ne demek?

MTrader'la ilgili teknik anlatımlarda **header**, ilgili tarafın en iyi fiyat seviyesini ve oradaki miktarı ifade etmek için kullanılır. Burada HTTP başlığı gibi bir yazılım teriminden söz etmiyoruz. Alış header'ı ve satış header'ı ayrı izlenir.

Bir kademedeki miktarın azalmasına **erime** denebilir. Örneğin 10,01 TL satış miktarının 300 adetten 80 adede düşmesi bu şekilde anlatılabilir. Ama azalma tek başına 220 adet işlem gerçekleştiğini kanıtlamaz; iptal veya emir değişiklikleri de miktarı azaltabilir. Nedenini anlamak için ilgili olaylara bakarız.

Miktarın azalması, seviyenin kesin kırılacağı veya fiyatın kesin yükseleceği anlamına da gelmez. Aynı seviyeye yeni emirler eklenebilir. Bu ayrım, ileride kademe miktarını kullanan strateji koşullarını okurken önem kazanacak.

## MTrader'da neyi ayıracağız?

Piyasanın emir defteri ile **kendi emirlerimizin durumu** ayrı bilgilerdir. Bir seviyede toplam 500 adet görmek, kendi emrimizden 500 adet beklediğini söylemez. Kendi emrimizin kabulü, gerçekleşen miktarı ve kalan miktarı ayrıca takip edilir.

Bir test senaryosunda ürün ve işlem aşamasıyla birlikte başlangıç defterini, gönderilen emrin yön/fiyat/miktarını ve geçerlilik koşulunu belirtiriz. Ardından olay sırasını ve gerçekleşme sonucunu karşılaştırırız. Böylece “emir gönderildi”, “defter miktarı azaldı” ve “bizim emrimiz gerçekleşti” ifadelerini birbirinin yerine kullanmayız.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı talebi:** BYF kavramı açıklandıktan sonra sıradaki konuya geçilmesi istendi. Bu konuya özgü soru henüz yok. Defter ve eşleşme örnekleri agent tarafından öğretici amaçla hazırlandı; gerçek piyasa kaydı değildir.

## Kaynaklar ve doğrulama

- [Borsa İstanbul — Pay Piyasası SSS](https://www.borsaistanbul.com/sss/pay-piyasasi): sürekli işlem ve fiyat-zaman önceliği. Erişim: 24 Ekim 2026.
- [Borsa İstanbul — Piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi): limit emir ve eşleşme çerçevesi. Erişim: 24 Ekim 2026.
- Projedeki header/erime dilinin bağlamı mevcut [HFT Classic teknik belgesinden](../../bilgi-tabani/20-stratejiler/hft-classic.md) alındı; bu taslak 22 Ekim referanslarına dayanır. Bu tur kod yeniden incelenmedi; stratejinin kesin tetik koşulu burada tanımlanmaz.

Kaynak web sayfalarının kullanılan açıklamalarında ayrı sürüm tarihi verilmedi; erişim tarihi kaydedildi. Örnekler normal görünür emirlerle, sürekli işlem ve değişmeyen defter varsayımıyla sınırlıdır; özel emir öncelikleri ve tek fiyat eşleşmesi genellenmez. İşlem hesabı öğretici örnektir; canlı emir, replay veya uygulama testi yapılmadı.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
