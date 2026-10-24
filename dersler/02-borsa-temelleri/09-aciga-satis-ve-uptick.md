---
kapsam: Açığa satış ve ödünç; işaretleme, izin/tedbir, yukarı adım ve vadeli kısa pozisyondan farkı
dis_kaynak:
  - url: https://mevzuat.spk.gov.tr/api/Mevzuat/File/249
    erisim: 2026-10-24
  - url: https://www.kap.org.tr/tr/Bildirim/1666369
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
---

# Açığa satış ve uptick

Normal bir satışta elimizdeki payı satarız. **Açığa satışta** ise sahip olmadığımız payı satma işlemi söz konusudur. Sonradan daha düşük fiyattan alıp kapatmayı hedeflemek olası bir amaçtır; fiyat yükselirse zarar oluşabilir. İşlemin izin, ödünç ve takas yükümlülükleri vardır. [SPK — Seri V No 65, madde 24 ve ödünç bölümü](https://mevzuat.spk.gov.tr/api/Mevzuat/File/249)

## Basit bir örnek

Gerekli izin ve ödünç düzeninin sağlandığını varsayalım. Sahip olmadığımız 100 payı 20 TL'den satıp daha sonra 19 TL'den geri alırsak, masraflar hariç 100 × (20 − 19) = **100 TL fark** elde ederiz. Geri alış 22 TL olursa **200 TL zarar** doğar.

Satıştan gelen 2.000 TL'yi serbest kazanç sayamayız; payı geri temin etme ve teslim yükümlülüğü sürer. Ödünç, payın kullanımını belirli koşullarla sağlar; bedelsiz ve süresiz sahiplik vermez. Ödünç maliyeti, komisyon ve diğer masraflar net sonucu etkiler.

## Emir neden ayrıca işaretlenir?

Sahip olunan payı satmakla açığa satış yapmak farklı işlem nitelikleridir. Gün içinde sahip olmadan satıp aynı gün geri almak da kendiliğinden normal satışa dönüşmez. BIST'in 22 Eylül 2026 duyurusu, bu işlemlerin de açığa satış seçeneği işaretlenerek iletilmesi gerektiğini hatırlatır. [Borsa İstanbul KAP duyurusu](https://www.kap.org.tr/tr/Bildirim/1666369)

Bu yüzden testte yalnız “satış” yönüne bakmayız. Sahiplik, satılabilir miktar, açığa satış işareti, hesap yetkisi ve ürünün o günkü durumu birlikte ele alınır. İşaret bulunması da tek başına bütün izinlerin sağlandığı anlamına gelmez.

## Yukarı adım (uptick) kuralı

Bu fiyat kuralı, her fiyat seviyesinde açığa satış yapılmasına izin vermez. **22 Eylül 2026 tarihli BIST duyurusu**, BIST 50 kapsamındaki izin verilen paylarda bir sonraki duyuruya kadar yukarı adım uygulanacağını belirtir: açığa satış fiyatı son işlem fiyatından yüksek olmalıdır; son işlem fiyatı bir önceki işlemden yüksekse son fiyat düzeyinden de yapılabilir. [Tarihli resmi duyuru](https://www.kap.org.tr/tr/Bildirim/1666369)

Fiyat adımının 0,01 TL olduğu bir ürün varsayalım:

| Önceki işlem | Son işlem | Duyurudaki fiyat kuralını anlatan örnek |
|---|---|---|
| 10,01 TL | 10,00 TL | Son fiyat yükselmedi; 10,00 yerine daha yüksek geçerli fiyat gerekir |
| 10,00 TL | 10,01 TL | Son fiyat yükseldi; 10,01 düzeyi de kullanılabilir |

Tablo yalnız fiyat kuralını gösterir. Hesap yetkisi, payın endeks kapsamı ve tedbirleri ayrıca uygun olmalıdır. “Uptick”, otomatik olarak her zaman son fiyata bir kuruş eklemek değildir; fiyat adımı ve son iki işlemin yönü önemlidir.

## Tarihli izin ile kalıcı kavramı ayıralım

Açığa satış izni veya yasağı, pay bazlı tedbir ve yukarı adım uygulaması zaman içinde değişebilir. Bir eski duyuruyu okuyup süresiz izin veya yasak sonucu çıkarmayız. Bu bölümdeki tarihli örnek, gerçek işlem günündeki son kararın kontrol edilmesinin yerine geçmez.

Bir ürün açığa satışa uygun olsa bile kurum veya hesabın yetkisi farklı olabilir. Ödünç temininin mümkün olması da o gün açığa satış iznini tek başına kanıtlamaz.

## Vadeli kısa pozisyon aynı işlem mi?

Bir pay vadeli sözleşmesinde kısa pozisyon açmak, spot payı açığa satmakla aynı operasyon değildir. Vadelide sözleşme yükümlülüğü ve teminat vardır; spotta pay sahipliği, ödünç ve teslim ilişkisi ele alınır. Bu iki ürünün emir işaretlerini veya izinlerini birbirine kopyalamayız.

MTrader'da “satış emri” gördüğümüzde önce hangi piyasa, ürün ve işlem niteliği olduğunu sorarız. Stratejinin açığa satış alanlarını nasıl kullandığı ve hangi kontrolü yaptığı kendi kod incelemesinin konusudur.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** Borsa bölümünün kalan konuları tek turda tamamlansın, ardından toplu revize edilsin. Bu konu bu kapsamda yazıldı; özel bir soru henüz yok. Sayısal senaryolar öğretici örnektir.

## Kaynaklar ve doğrulama

SPK resmi Tebliğ derlemesinde kavram/ödünç çerçevesi; BIST tarafından KAP’ta 22 Eylül 2026 09:06:58’de yayımlanan 1666369 numaralı duyuruda BIST 50, işaretleme ve uptick kuralı okundu. Erişim 24 Ekim 2026. Bu bölüm her pay ve hesap için canlı uygunluk teyidi vermez; tarihli duyuru eğitim bağlamıdır, sonraki değişiklikler işlem günü kontrol edilir.

Bu tur MTrader kaynak kodu veya canlı sistem test edilmedi. Proje karşılıkları mevcut KB taslaklarının kavramsal özetidir; güncel prod davranışı olarak sunulmaz.

## Devam notu

Borsa bölümünün tamamıyla birlikte toplu kullanıcı revizyonu bekleniyor; teknik temellere henüz geçilmedi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
