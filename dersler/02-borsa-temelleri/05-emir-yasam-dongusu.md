---
kapsam: Gönderim, kabul, ret, kısmi/tam gerçekleşme, iptal ve değişiklik; istek ve sonuç ayrımı
dis_kaynak:
  - url: https://borsaistanbul.com/files/bistech-ouch-protocol-specification.pdf
    belge_tarihi: 2025-02-06
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/sss/pay-piyasasi
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# Emir yaşam döngüsü

Bir emir için “gönderdik”, “kabul edildi” ve “gerçekleşti” farklı şeylerdir. **Emir yaşam döngüsü**, talimatın hazırlanmasından bekleyen miktarının sona ermesine kadar geçirdiği adımlardır. Bir önceki konuda emir koşullarını seçtik; şimdi sonuçlarını nasıl okuyacağımıza bakacağız.

## İstek göndermek ile sonuç almak

MTrader'da bir butona basılması veya stratejinin emir kararı üretmesi, borsada işlem yapıldığını göstermez. Talimat önce uygulamanın ilgili katmanlarından geçer. Borsaya ulaşıp kabul edilmesi ve ardından karşı emirle eşleşmesi ayrı adımlardır.

| Adım | Bildiğimiz şey | Henüz söyleyemeyeceğimiz şey |
|---|---|---|
| İstek oluşturuldu | Uygulama bir talimat hazırladı | Borsa emri gördü |
| Gönderim yapıldı | Talimat iletim yoluna verildi | Borsa kabul etti |
| Kabul sonucu alındı | Emir kabul edildi | Miktarın tamamı gerçekleşti |
| Gerçekleşme sonucu alındı | Bildirilen miktarda işlem oluştu | Emrin geri kalanı da gerçekleşti |

Borsa İstanbul'un OUCH protokolünde yeni emir, değişiklik ve iptal istekleriyle kabul, ret, değişiklik, iptal ve gerçekleşme bildirimleri ayrı mesajlardır. Bunların İngilizce adlarıyla da karşılaşırız: **Accepted, Rejected, Replaced, Canceled, Executed**. [Borsa İstanbul — OUCH, bölüm 4](https://borsaistanbul.com/files/bistech-ouch-protocol-specification.pdf)

## Kabul ve ret ne demek?

**Kabul**, emrin borsa tarafından kabul edildiğini bildirir. Karşılanamayan miktarın beklemesi veya iptali, emir koşuluna bağlıdır. **Ret**, ilgili isteğin kabul edilmediğini söyler; örneğin geçersiz fiyat adımı bir ret nedeni olabilir. [Borsa İstanbul — Pay Piyasası SSS](https://www.borsaistanbul.com/sss/pay-piyasasi)

Yeni emir isteğinin reddi ile mevcut emri değiştirme isteğinin reddini ayırırız. İkincisinde yalnız “ret geldi” diye eski emrin ortadan kalktığını varsayamayız. Sonucun hangi isteğe ve hangi emre ait olduğunu belirlememiz gerekir.

{{< pagebreak >}}

## 100 adetlik bir emri birlikte izleyelim

Başlangıçta bu üründe pozisyonumuz olmadığını ve başka işlem yapmadığımızı varsayalım. Normal, günlük bir **100 adet alış emri** gönderiyoruz. Aşağıdaki örnekte bekleyen miktarın tamamını iptal etmek istiyoruz.

| Gelen olay veya yapılan işlem | Toplam gerçekleşen | Bekleyen | Anlamı |
|---|---:|---:|---|
| Yeni emir kabul edildi | 0 | 100 | Emir kabul edildi, henüz işlem yok |
| 40 adet gerçekleşti | 40 | 60 | Kısmi gerçekleşme var |
| Kalanı iptal isteği gönderdik | 40 | 60 | Sonuç bekleniyor; iptal henüz kesin değil |
| İptal sonuçlanmadan 10 adet daha gerçekleşti | 50 | 50 | Bu 10 adet de gerçek işlemdir |
| Kalan 50 adedin iptali bildirildi | 50 | 0 | Bekleyen emir kalmadı; 50 adet alış gerçekleşmiş durumda |

Sonuçta **50 adet payımız vardır**. “Emir iptal edildi” demek, gerçekleşmiş 50 adedi geri verdiğimiz anlamına gelmez. İptal, bu örnekte artık gerçekleşmeyecek kalan miktarla ilgilidir.

İptal talebinden sonra gerçekleşme gelmesi tek başına bir hata değildir: talep sonuçlanmadan önce emir eşleşmiş olabilir. Bu yüzden iptal butonuna bastığımız anda bekleyen miktarı kesin olarak sıfırladığımızı düşünmeyiz.

Bu örnekte değişiklik olmadığı için başlangıç miktarı **100 = gerçekleşen 50 + iptal edilen 50** olarak açıklanabilir. Değişiklik içeren senaryolarda miktar hesabını her değişikliğin anlamına göre yeniden kurarız.

## Tam gerçekleşme ve emrin sona ermesi

Emrin tamamı işlem gördüyse **tam gerçekleşme** oluşur; yalnız bir bölümü işlem gördüyse **kısmi gerçekleşme** vardır. Bir emir tek seferde veya birden fazla gerçekleşmeyle tamamlanabilir.

Bekleyen miktar sıfır olduğunda nedenini de bilmeliyiz: tamamı gerçekleşmiş olabilir, kalan iptal edilmiş olabilir veya günlük geçerlilik sona ermiş olabilir. “Aktif emir kalmadı” ifadesi tek başına ne kadar işlem yapıldığını söylemez.

İptal her zaman kullanıcının düğmeye basmasıyla da oluşmaz; emir koşulu veya sistem kaynaklı iptaller olabilir. Sonuç mesajı ve gerekçesi birlikte değerlendirilir. [Borsa İstanbul — OUCH, Order Canceled](https://borsaistanbul.com/files/bistech-ouch-protocol-specification.pdf)

## Emir değiştirme: replace

Fiyatı veya izin verilen başka bir alanı değiştirmek için **değişiklik isteği** gönderilebilir; teknik anlatımlarda **replace** adını görürüz. İsteğin gönderilmesiyle değişikliğin kabul edilmesi ayrı olaylardır. İstek sonuçlanırken gerçekleşme de oluşabilir. [Borsa İstanbul — OUCH, Replace Order ve Order Replaced](https://borsaistanbul.com/files/bistech-ouch-protocol-specification.pdf)

Örneğin 10,00 TL'de bekleyen alışın fiyatını 10,01 TL yapmak istediğimizde, sonucu görmeden yeni fiyatı kesinleşmiş saymayız. Ayrıca değişikliğin zaman önceliğine etkisi piyasa ve değişen alana göre değerlendirilir. “Değiştir” komutunu her durumda sıradaki yerimizi koruyan bir işlem gibi düşünmeyiz.

Miktar değiştirirken “yeni toplam miktar” ile “yeni kalan miktar” da ayrı olabilir. Bu ayrıntı arayüz/SDK sözleşmesinden doğrulanmalıdır. Örneğin 40 adet gerçekleşmişken bir alana 60 yazılması, alanın anlamını bilmeden “20 adet daha alacak” veya “60 adet daha alacak” diye yorumlanamaz.

## Bağlantı koparsa sonuç ne olur?

Yanıt alamamak, isteğin reddedildiğini veya emrin hiç oluşmadığını kanıtlamaz. Protokol belgesi de kopma anında gönderilmiş isteğin ulaşıp ulaşmadığının belirsiz kalabileceğini açıklar. [Borsa İstanbul — OUCH, bölüm 4.1](https://borsaistanbul.com/files/bistech-ouch-protocol-specification.pdf)

Bu durumda sonuç bilinmiyorken aynı işlemi yeni emir gibi tekrar göndermek çift emir riski doğurabilir. Kurtarma ve tekrar gönderim kurallarını teknik temellerde ele alacağız. Buradaki temel nokta, **“sonucu bilmiyoruz” durumunun da “başarısız”dan ayrı olduğudur**.

## MTrader testinde neyi kaydederiz?

Her emir için ürün, hesap, yön, miktar, fiyat ve geçerlilik koşuluna ek olarak emri/isteği ilişkilendiren kimliği takip ederiz. Olayların sırasını, toplam gerçekleşeni, kalan miktarı ve ret/iptal gerekçesini birlikte inceleriz.

Stratejinin olayı işlemesiyle arayüzde görünmesi de ayrı adımlardır. Mevcut teknik bilgi tabanında emir dönüşleri, motor ve arayüz yollarıyla ayrıca belgelenmiştir. Burada ekran etiketlerini kesin durum listesi olarak tanımlamıyoruz; kavramları kuruyoruz. Uçtan uca bağlantıları sistem mimarisi bölümünde açacağız.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı talebi:** “devam”. İndeks sırasıyla emir yaşam döngüsü yazıldı. Konuya özel soru henüz yok. 100 adetlik iptal/gerçekleşme örneği agent tarafından eğitim amacıyla oluşturuldu; canlı kayıt değildir.

## Kaynaklar ve doğrulama

- [Borsa İstanbul — OUCH Protocol Specification](https://borsaistanbul.com/files/bistech-ouch-protocol-specification.pdf), kapakta 6 Şubat 2025: bölüm 4.1 istekler, 4.2 sonuçlar ve kopma bağlamı. Erişim: 24 Ekim 2026. Tüm protokol alanları veya çalıştırılan MTrader protokol sürümü doğrulanmadı.
- [Pay Piyasası SSS](https://www.borsaistanbul.com/sss/pay-piyasasi): fiyat adımı kaynaklı ret ve öncelik kavramları. Erişim: 24 Ekim 2026.
- [Emrin dönüşü](../../30-akislar/emir-donusu.md): mevcut teknik KB taslağından motor/GUI ayrımı. Referanslar ilgili dosyada; bu tur yeni kod kontrolü yapılmadı.

Yeni/kısmi/tam gerçekleşme ve iptal miktarları öğretici modeldir; ham protokol durumlarının veya GUI etiketlerinin birebir listesi değildir. Kaynak araştırması uygulama testi sayılmaz; canlı emir veya replay çalıştırılmadı.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
