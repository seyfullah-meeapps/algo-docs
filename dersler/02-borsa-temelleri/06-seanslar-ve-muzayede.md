---
kapsam: Sürekli işlem, emir toplama ve tek fiyat; denge fiyatı, kapanış, devre kesici ve saat bağlamı
dis_kaynak:
  - url: https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/islem-saatleri
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi
    erisim: 2026-10-25
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# Seanslar, müzayede ve denge fiyatı

Bir ürünün işlem günü boyunca aynı kurallarla çalıştığını düşünmemeliyiz. **Seans**, işlem gününün düzenlenmiş sürecidir; içinde emir toplama, eşleştirme ve sürekli işlem gibi farklı aşamalar bulunabilir. “Borsa açık” demek, o anda her emir türünün gönderilebildiği anlamına gelmez.

## Sürekli işlem ile tek fiyatın farkı

**Sürekli işlemde** gelen uygun emirler bekleyen karşı emirlerle eşleşebilir. Önceki defter örneklerimiz bu aşamayı anlatıyordu. **Tek fiyat yönteminde** ise emirler bir süre toplanır, sonra belirlenen tek fiyat üzerinden eşleştirilir. Emir toplama sırasında yeni bir emir görmek, o anda işlem gerçekleştiğini göstermez. [Borsa İstanbul — Piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

**Müzayede (auction)**, bu toplama ve toplu fiyat belirleme sürecini anlatır. Açılış ve kapanış müzayedeleri vardır; bazı ürünler gün içinde de tek fiyat yöntemiyle işlem görür.

## Denge fiyatı neyi gösterir?

**Denge veya teorik eşleşme fiyatı**, o anda toplanmış emirlerle eşleştirme yapılsaydı oluşması beklenen fiyattır. Temel amaç en yüksek işlem miktarını sağlayan fiyatı bulmaktır; eşitlik durumunda ilave kurallar devreye girer. Toplama devam ederken emirler değişebileceği için denge fiyatı da değişebilir. Bu değer henüz gerçekleşmiş işlem veya kesin kapanış fiyatı değildir.

Önce emir defterini görelim. Aşağıdaki miktarlar **yalnız o limit fiyatındaki** emirlerin toplamıdır; başka kademeleri içermez. Örnekte yalnız bu üç seviyedeki limit emirleri vardır; miktarlar lottur.

| Limit fiyatı | O kademedeki alış | O kademedeki satış |
|---|---:|---:|
| 10,00 TL | 500 | 100 |
| 10,01 TL | 400 | 300 |
| 10,02 TL | 100 | 500 |

Bir aday fiyatı denerken yalnız aynı kademeye bakmayız. **Alış limiti ödenebilecek en yüksek, satış limiti kabul edilebilecek en düşük fiyattır.** Aday fiyata eşit veya daha yüksek limitli bütün alışları; aday fiyata eşit veya daha düşük limitli bütün satışları toplarız. Buna **birikimli (kümülatif) toplam** denir.

**Aday fiyat 10,01 TL olsun:** 10,02 TL limitli 100 lot alış da bu fiyattan alabilir; alış toplamı 400 + 100 = **500 lot** olur. 10,00 TL limitli 100 lot satış da bu fiyattan satabilir; satış toplamı 100 + 300 = **400 lot** olur. Eşleşebilir miktar iki toplamın küçüğüdür: **400 lot**. Bu, 400 lot alış ile 400 lot satışın karşılaşmasıdır; işlem miktarı 800 lot diye toplanmaz.

Aynı hesabı her aday için ayrı yapalım. Bunlar aynı defterin alternatif fiyat hesaplarıdır; bir satırı hesaplayınca emirleri defterden düşmeyiz.

| Aday fiyat | Birikimli alış | Birikimli satış | Eşleşebilir lot |
|---|---:|---:|---:|
| 10,00 TL | 500 + 400 + 100 = 1.000 | 100 | 100 |
| 10,01 TL | 400 + 100 = 500 | 100 + 300 = 400 | 400 |
| 10,02 TL | 100 | 100 + 300 + 500 = 900 | 100 |

Bu örnekte en yüksek işlem miktarını **10,01 TL'de 400 lot** sağlar. Eşleştirme bu defterle yapılırsa eşleşen emirlerin tamamı **10,01 TL'den** gerçekleşir. 10,02 limitli alışın 100 lotu ve 10,01 limitli alışların 300 lotu; 10,00 limitli satışın 100 lotu ve 10,01 limitli satışların 300 lotuyla eşleşir. 10,01'deki alışların 100 lotu bu eşleştirmede karşılanmaz. Aynı fiyat içindeki emirlerin sırasını zaman önceliği belirler.

Emir toplama bitmeden 10,01 TL'yi kesin sonuç saymayız. Bu örnek tam borsa algoritması değildir; fiyat bandı, özel emirler ve eşitlik çözümü ayrıca değerlendirilir. Genel çerçeve: [Borsa İstanbul — Piyasa işleyişi](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi).

## Tam iş gününde örnek akış

Aşağıdaki saatler **sürekli işlem gören normal paylar için tam iş günü**, İstanbul yerel saati bağlamındadır. Ürün istisnaları, yarım gün ve özel duyurular ayrıca kontrol edilir.

| Aşama | Genel saat aralığı | Ne olur? |
|---|---|---|
| Açılış emir toplama | 09:40–09:55 civarı | Emirler birikir; sürekli eşleşme yapılmaz |
| Açılış fiyat belirleme | 09:55 sonrası | Açılış fiyatı ve işlemleri oluşur |
| Sürekli işlem | 10:00–18:00 | Uygun emirler sürekli eşleşebilir |
| Kapanışa hazırlık | 18:00–18:01 | Kapanış marjı yayımlanır |
| Kapanış emir toplama | 18:01–18:05 | Kapanış için emirler toplanır |
| Kapanış eşleştirmesi | 18:05 sonrası | Kapanış fiyatı belirlenir |
| Kapanış fiyatından işlemler | 18:08–18:10 | Belirlenmiş fiyat çerçevesinde işlemler yapılır |

Toplama bitişinde rastlantısal zamanlama, eşleştirmede işlem süresine bağlı geçiş bulunur; saat çizelgesi milisaniyesi kesin bir geçiş garantisi değildir. Kaynak: [Pay Piyasası Prosedürü 3.34, Ek-9](https://www.borsaistanbul.com/files/pay-piyasasi-proseduru.pdf) ve [işlem saatleri](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/islem-saatleri), erişim 24 Ekim 2026.

Bu tablo VİOP'a veya varantlara kopyalanmaz. Test ortamı takvimi de canlı piyasanın günüyle aynı varsayılmaz.

## Devre kesici ve işlem durdurma

**Devre kesici**, belirlenmiş fiyat hareketi koşullarında normal akışı keserek geçici durma veya emir toplama/eşleştirme aşamalarını devreye sokabilir. Pay bazında ve endekse bağlı mekanizmalar farklı kapsam taşır. Süre ve eşikler değişebildiği için burada sabit bir oran ezberlemiyoruz. [Borsa İstanbul — Devre kesici açıklamaları](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

Tavan veya taban fiyatına gelmek, devre kesiciyle aynı şey değildir. Bir ürünün durdurulması da her zaman bütün piyasanın durduğu anlamına gelmez.

## MTrader testinde hangi bilgiyi kullanacağız?

Test senaryosunda **saat + saat dilimi + ürünün gerçek işlem durumu** birlikte yazılır. Saat 10:05 olduğu için ürünün mutlaka sürekli işlemde olduğunu varsaymayız; durdurulmuş veya tek fiyat sürecinde olabilir. Hangi stratejinin hangi aşamada çalışacağı kendi bölümünde açıklanacak.

Aynı fiyat ve miktarın açılışta beklemesi, sürekli işlemde eşleşmesi ve eşleştirme aşamasında yeni isteğin kabul edilmemesi farklı bağlamlardır. Bu nedenle “emir gitmedi” değerlendirmesinden önce seans durumunu sorarız.

## Sorularımız ve netleşen noktalar

**25 Ekim 2026 — Kullanıcının sorusu, anlamı korunmuş özet:** PDF 21. sayfa 8.2'de, üst alış ve alt satış kademeleriyle birlikte 10,01'de 500 alış, 400 satış ve 400 lot eşleşme olmaz mı?

**Yanıt ve değişiklik:** Kademe miktarı olarak okunduğunda bu hesap doğrudur. Önceki tablo zaten birikimli olarak tanımlanmıştı; eski 400 alış, üst seviyedeki 100 alışın dahil olduğu toplamdı. Eski tablo kendi tanımı altında tutarlıydı, ancak ham defter verilmediğinden kademe miktarı gibi okunabiliyordu. Örnek aynı rakamları ham kademe miktarları olarak alacak biçimde yeniden kuruldu; ayrı birikimli tablo, toplama yönleri, tek işlem fiyatı ve kalan miktar açıklandı. Yeni örnekte sonuç 400 lottur. Diğer başlıklar kullanıcı incelemesi bekliyor.

**24 Ekim 2026 — Kullanıcı yönlendirmesi, anlamı korunmuş özet:** Borsa tarafının kalan konuları topluca tamamlansın; kullanıcı bölümün tamamını okuyup birlikte revize edecek. Bu dosya bu kapsamda taslak yazıldı; ayrı bir konu sorusu henüz yok. Örnekler agent tarafından eğitim amacıyla oluşturuldu.

## Kaynaklar ve doğrulama

Resmi Pay Piyasası Prosedürü 3.34, revizyon 21 Eylül 2026; Ek-9 saat çizelgesi ve genel tek fiyat/kapanış açıklamaları okundu. Web kaynakları 24 Ekim 2026 tarihinde erişildi. Tam iş günü normal pay örneği verildi; VİOP/yarım gün/istisna çizelgeleri çıkarılmadı. Örnek denge hesabı kuralın ana fikrini anlatır. 25 Ekim 2026 revizyonunda resmi piyasa işleyişi sayfasının limit emir ve kapanışta tek fiyat açıklamaları yeniden okundu (erişim 2026-10-25); diğer kaynakların önceki erişim tarihleri korunur. Sayısal defter eğitim örneğidir.

Bu tur MTrader kaynak kodu, canlı binary/config veya gerçek işlem testi yapılmadı. Projeye ilişkin bağlantılar mevcut KB taslaklarına dayanır; bunlar yeni kod doğrulaması değildir.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
