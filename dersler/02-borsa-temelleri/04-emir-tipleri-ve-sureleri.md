---
kapsam: Limit, piyasa, piyasadan limite; günlük/DAY, KİE/IOC, GİE/FOK; piyasa ve seans desteği ayrımı
dis_kaynak:
  - url: https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf
    surum: 3.34
    revizyon: 2026-09-21
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/viop/piyasa-isleyisi/emirler
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
---

# Emir tipleri ve geçerlilik süreleri

Emirde iki ayrı karar veririz: **hangi fiyat koşuluyla işlem yapılacağı** ve **gerçekleşmeyen miktarın ne olacağı**. Örneğin “10,01 TL'den fazla ödemeyeyim” fiyat koşuludur; “hemen alamadığım kısım iptal olsun” ise gerçekleşme/geçerlilik koşuludur. Aynı fiyat ve miktar, farklı koşullarla farklı sonuçlar üretir.

## Önce fiyatı nasıl belirlediğimize bakalım

| Emir tipi | Verdiğimiz talimat |
|---|---|
| Limit | Alışta en fazla, satışta en az kabul ettiğim fiyatı belirtiyorum |
| Piyasa | Fiyat yazmıyorum; uygun karşı emirlerle en iyi fiyattan başlayarak işlem istiyorum |
| Piyasadan limite | Fiyat yazmıyorum; yalnız karşıdaki en iyi seviyede işlem istiyorum, kalan için limit emir davranışı uygulanıyor |

**Limit**, işlemin kesin o fiyattan gerçekleşeceği anlamına gelmez. 10,02 TL limitli alış, uygun satış varsa daha düşük fiyattan da gerçekleşebilir. Ancak 10,02 TL'nin üstünü ödemez. Piyasa emrinde ise kullanıcı tarafından yazılmış böyle bir limit bulunmaz; bu, borsanın bütün kontrollerinin kalktığı anlamına gelmez. [Borsa İstanbul — Pay Piyasası işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

## Aynı defterde üç farklı alış

Sürekli işlemde hayali bir payın satış tarafı şöyle olsun. Her örneğe bu başlangıçtan ayrı başlıyoruz; başka emir, iptal veya özel koşul olmadığını varsayıyoruz.

| Satış fiyatı | Bekleyen adet |
|---|---:|
| 10,01 TL | 100 |
| 10,02 TL | 200 |
| 10,03 TL | 400 |

**250 adet almak** istediğimizde:

| Emir | Örnekteki sonuç |
|---|---|
| 10,01 TL limitli günlük alış | 100 adet 10,01 TL'den alınır; kalan 150 adet 10,01 TL alış olarak bekler |
| Piyasa alış | 100 adet 10,01 TL'den, 150 adet 10,02 TL'den alınır |
| Günlük piyasadan limite alış | Yalnız 100 adet 10,01 TL'den alınır; kalan 150 adet aynı fiyattan limit alış olarak bekler |

Piyasa emriyle piyasadan limite emrin farkı, ikinci satış seviyesine geçilip geçilmemesinde görülür. Piyasadan limite emir sürekli işlemde hiç karşı emir bulamazsa iptal edilir. KİE koşulu seçilirse gerçekleşmeyen kısmı pasife yazılmaz. [Borsa İstanbul — Pay Piyasası işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

## Günlük, KİE ve FOK neyi değiştirir?

**Günlük / DAY:** Uygun emirlerde gerçekleşmeyen miktar, geçerlilik koşulları çerçevesinde gün boyunca bekleyebilir. “Günlük” ifadesi emrin mutlaka gerçekleşeceği anlamına gelmez.

**Kalanı İptal Et / KİE / IOC (Immediate or Cancel):** O anda karşılanabilen miktar gerçekleşir; kalan iptal edilir. Kısmi gerçekleşmeye izin verir.

**Gerçekleşmezse İptal Et / GİE / FOK (Fill or Kill):** Miktarın tamamı o anda karşılanabiliyorsa işlem olur; aksi hâlde tümü iptal edilir. Bir kısmı alınarak devam edilmez. Tamamı birden fazla karşı emirle karşılanabilir; tek bir satıcı bulma şartı değildir. [Borsa İstanbul — Pay Piyasası Prosedürü, Ek-1 emir koşulları](https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf)

İlk tablodaki deftere **250 adet, 10,01 TL limitli alış** gönderelim:

| Koşul | Gerçekleşen | Sonuçta bekleyen |
|---|---:|---|
| Günlük | 100 adet | 150 adet bekler |
| KİE / IOC | 100 adet | Yok; 150 adet iptal |
| GİE / FOK | 0 adet | Yok; 250 adedin tamamı iptal |

FOK'ta 100 adet alınıp sonra geri verilmez; şart sağlanmadığı için kısmi işlem oluşmaz. KİE'de ise gerçekleşen 100 adet kalır. **Kalanın iptali, gerçekleşen işlemi geri almaz.**

FOK, bazen başka sistemlerde görülen “hepsi ya da hiçbiri / AON” ile de karıştırılmamalıdır. Buradaki FOK hemen tam gerçekleşme koşuludur; tamamını bulana kadar defterde bekleyen emir anlamına gelmez.

## Her kombinasyonu her yerde kullanabilir miyiz?

Hayır. Piyasa, ürün, seans aşaması ve emir iletim kanalının desteklediği seçenekler birlikte değerlendirilir. Pay Piyasası'nda piyasa emrinin KİE kullanımı ve tek fiyat aşamalarındaki bekleme/iptal kuralları ayrıca düzenlenir. Teknik ekte bir koşulun tanımlanması, her seansta her ürün için kullanılabildiğini göstermez. [Pay Piyasası Prosedürü, 5.4 ve Ek-1](https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf)

VİOP'un resmi emir sayfası, **1 Mart 2021'den itibaren piyasa emir yöntemine izin verilmediğini** belirtir. Bu nedenle yukarıdaki Pay Piyasası piyasa emri örneğini VİOP için hazır test senaryosu olarak kullanmayız. VİOP'ta KİE ve GİE koşulları da girildiği veya aktif olduğu andaki uygun karşı emirler üzerinden değerlendirilir. [Borsa İstanbul — VİOP emirler](https://www.borsaistanbul.com/piyasalar/viop/piyasa-isleyisi/emirler)

İptale kadar geçerli ve tarihli emir adlarıyla da karşılaşabiliriz. Bunların kullanılabilirliği pazara ve ürüne bağlıdır; “iptale kadar” ifadesini her üründe sınırsız bekleme izni gibi okumayız. İlk aşamada günlük, KİE ve FOK ayrımını doğru kurmamız yeterli.

## MTrader'da nasıl okuyacağız?

Stratejiyi **başlatmak**, borsaya hemen belirli bir emir türünün gönderildiğini tek başına söylemez. Strateji koşulu oluştuğunda üretilen emrin fiyat tipi ve geçerlilik koşulu ayrıca incelenir.

Bir testte “250 adet alış gönderildi” yerine ürün, yön, miktar, fiyat tipi, varsa limit fiyat ve geçerlilik koşulunu birlikte yazarız. Sonra gerçekleşen, iptal edilen ve bekleyen miktarı ayrı kontrol ederiz. Aynı defterde yukarıdaki üç koşulun sonuçlarının farklı olması beklenir.

Bu konu MTrader'daki bütün ekranların ve stratejilerin destek listesini vermiyor. Bir seçeneğin arayüzde görünmesi, motorun onu aynı anlamla ilettiğinin kanıtı değildir; GUI, motor ve borsa mesajı eşleşmesini ilgili stratejinin bölümünde kodla doğrulayacağız.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı talebi:** “sıradaki konu ile devam”. Emir tipleri ve geçerlilik süreleri yazıldı. Bu konuya özgü soru henüz yok. Defter ve miktarlar agent tarafından hazırlanmış öğretici örnektir.

## Kaynaklar ve doğrulama

- [Pay Piyasası Prosedürü](https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf): sürüm 3.34, revizyon 21 Eylül 2026; 5.4 ve Ek-1 emir türleri/koşulları incelendi. Erişim: 24 Ekim 2026. Teknik yetenek ile aşama/pazar bazlı kullanım ayrıldı; bütün destek kombinasyonları çıkarılmadı.
- [Pay Piyasası işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi): temel limit/piyasa/piyasadan limite anlatımı. Erişim: 24 Ekim 2026.
- [VİOP emirler](https://www.borsaistanbul.com/piyasalar/viop/piyasa-isleyisi/emirler): piyasa emri kısıtı ve KİE/GİE tanımları. Erişim: 24 Ekim 2026; sayfada ayrı sürüm tarihi yok, kısıt için 1 Mart 2021 başlangıcı belirtiliyor.

Bu tur MTrader kaynak kodu, protokol enum eşlemeleri veya canlı sistem test edilmedi. Örnekler değişmeyen normal görünür defter varsayımıyla sınırlıdır; özel emirler ve müzayede için doğrudan genellenmez.

## Devam notu

Taslak yazıldı ve kitaba eklendi; henüz kullanıcı okumasından geçmedi. Sıradaki konu [Emir yaşam döngüsü](05-emir-yasam-dongusu.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
