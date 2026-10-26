---
kapsam: Açığa satış ve ödünç; işaretleme, izin/tedbir, yukarı adım ve vadeli kısa pozisyondan farkı
dis_kaynak:
  - url: https://mevzuat.spk.gov.tr/api/Mevzuat/File/249
    erisim: 2026-10-24
  - url: https://www.kap.org.tr/tr/Bildirim/1666369
    erisim: 2026-10-25
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
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

**Uptick, açığa satışın hangi fiyattan yapılabileceğini sınırlayan bir kuraldır.** Mantığını şöyle düşünebiliriz: fiyat aşağı giderken açığa satış yapan kişi, daha düşük fiyatlara satış yaparak düşüşe katılamasın; satabilmek için daha yüksek bir fiyat beklesin. Bu, fiyatın düşmesini tamamen engelleyen bir garanti değildir.

Gündelik bir benzetmeyle, aynı ürünün el değiştirdiği bir pazardayız. Elimizde mal olmadan satış yapmak istiyoruz. Görevli önce **son iki satışın fişine** bakıyor: “En son kaç liradan satıldı, ondan önce kaç liraydı?” Buradaki fiş, **gerçekleşmiş işlemdir**; tezgahta yazan veya alıcının teklif ettiği fiyat değildir.

Örneklerde fiyat adımı **0,01 TL**, açığa satış izni ve diğer koşullar uygun, uptick kuralı yürürlükte olsun. Her örnek, verilen son iki işlem anındaki fiyat kontrolünü anlatır.

### Fiyat düştüyse: aynı fiyattan açığa satamam

Son iki işlem **10,01 → 10,00 TL** olsun. 100 lot açığa satmak istiyoruz.

“Birisi az önce 10,00'dan satmış, ben de 10,00'dan satayım” diyemeyiz. Son fiyat düşmüş olduğu için açığa satışın **10,00 TL'nin üzerinde** olması gerekir. Bu örnekte ilk uygun fiyat **10,01 TL** olur; 9,99 TL de uygun değildir.

Peki alıcılar yalnız 10,00 TL veriyorsa? **10,01 TL limitli açığa satış yazmak, hemen satabilmek demek değildir.** Karşı tarafta o fiyatı ödeyen uygun alıcı gerekir. Başka işlem olmadan 10,01 TL'den alacak bir alıcı gelirse eşleşme mümkün olabilir. “Kural beni daha yüksek fiyattan satmaya zorluyor” ile “o fiyata alıcı var” ayrı şeylerdir.

### Fiyat yükseldiyse: son fiyat da kullanılabilir

Bu kez son iki işlem **10,00 → 10,01 TL** olsun. Piyasada son gerçekleşen işlem zaten yukarı yönde yapılmıştır. Bu nedenle açığa satış **10,01 TL'den de** yapılabilir; mutlaka 10,02 TL beklemek gerekmez. Yine uygun alıcı ve yeterli miktar olmalıdır. 10,00 TL'den açığa satış ise bu anda uygun değildir.

### Fiyat aynı kaldıysa: yükselmiş sayılmaz

Son iki işlem **10,00 → 10,00 TL** ise son işlem öncekinden yüksek değildir. Bu nedenle bu örnekte açığa satış için yine **en az 10,01 TL** gerekir.

| Son iki gerçekleşen işlem | Son hareket | Açığa satış için en düşük uygun fiyat |
|---|---|---:|
| 10,01 → 10,00 TL | Düştü | 10,01 TL |
| 10,00 → 10,01 TL | Yükseldi | 10,01 TL |
| 10,00 → 10,00 TL | Aynı kaldı | 10,01 TL |

Tablodaki üç sonuç aynı görünse de nedenleri farklıdır: ilk ve üçüncü satırda **son fiyatın üstüne çıkıyoruz**; ikinci satırda **son fiyatın kendisi yeterli**. Son işlem 10,02 TL'ye yükselmiş olsaydı, örneğin 10,01 → 10,02 akışında, son fiyat olan 10,02 TL kullanılabilirdi.

**Akılda kalacak soru:** “Son işlem bir öncekinden yüksek mi?” Evetse son fiyat da kullanılabilir; hayırsa son fiyatın üzerindeki geçerli fiyat gerekir. “Yukarı adım” her durumda son fiyata bir kuruş eklemek değildir; fiyat adımı ürüne ve fiyat seviyesine bağlıdır. Yeni bir işlem gerçekleştiğinde karşılaştırılan son iki işlem de değişir; tabloyu gün boyu sabit bir fiyat sınırı gibi kullanmayız.

Bu anlatım **22 Eylül 2026 tarihli BIST duyurusundaki** fiyat kuralına dayanır. Duyuru, BIST 50 kapsamındaki açığa satış yapılabilen paylar için bir sonraki duyuruya kadar uygulama belirtir. Örnekler eğitim içindir; işlem günündeki izin ve tedbirler ayrıca kontrol edilir. [BIST — KAP duyurusu](https://www.kap.org.tr/tr/Bildirim/1666369)

## Tarihli izin ile kalıcı kavramı ayıralım

Açığa satış izni veya yasağı, pay bazlı tedbir ve yukarı adım uygulaması zaman içinde değişebilir. Bir eski duyuruyu okuyup süresiz izin veya yasak sonucu çıkarmayız. Bu bölümdeki tarihli örnek, gerçek işlem günündeki son kararın kontrol edilmesinin yerine geçmez.

Bir ürün açığa satışa uygun olsa bile kurum veya hesabın yetkisi farklı olabilir. Ödünç temininin mümkün olması da o gün açığa satış iznini tek başına kanıtlamaz.

## Vadeli kısa pozisyon aynı işlem mi?

Bir pay vadeli sözleşmesinde kısa pozisyon açmak, spot payı açığa satmakla aynı operasyon değildir. Vadelide sözleşme yükümlülüğü ve teminat vardır; spotta pay sahipliği, ödünç ve teslim ilişkisi ele alınır. Bu iki ürünün emir işaretlerini veya izinlerini birbirine kopyalamayız.

MTrader'da “satış emri” gördüğümüzde önce hangi piyasa, ürün ve işlem niteliği olduğunu sorarız. Stratejinin açığa satış alanlarını nasıl kullandığı ve hangi kontrolü yaptığı kendi kod incelemesinin konusudur.

## Sorularımız ve netleşen noktalar

**25 Ekim 2026 — Kullanıcının isteği, anlamı korunmuş özet:** PDF 27. sayfa, 11.3 uptick anlatımı çok soyut; gündelik ve somut örneklerle basitleştirilsin.

**Yanıt ve değişiklik:** Son iki satış fişi benzetmesi; düşen, yükselen ve aynı kalan fiyat örnekleri eklendi. Son gerçekleşen fiyat ile bekleyen teklif; fiyat uygunluğu ile alıcı bulunması ayrıldı. Son iki işlem değiştikçe karşılaştırmanın yenilendiği açıklandı. KAP 1666369 duyurusu 25 Ekim 2026'da yeniden okundu; örnekler agent tarafından üretildi. Metin taslak; kullanıcının yeni anlatımı okuduğu/onayladığı varsayılmaz.

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** Borsa bölümünün kalan konuları tek turda tamamlansın, ardından toplu revize edilsin. Bu konu bu kapsamda yazıldı; özel bir soru henüz yok. Sayısal senaryolar öğretici örnektir.

## Kaynaklar ve doğrulama

SPK resmi Tebliğ derlemesinde kavram/ödünç çerçevesi; BIST tarafından KAP’ta 22 Eylül 2026 09:06:58’de yayımlanan 1666369 numaralı duyuruda BIST 50, işaretleme ve uptick kuralı okundu. SPK erişimi 24 Ekim 2026; KAP duyurusu yeniden erişimi 25 Ekim 2026. Bu bölüm her pay ve hesap için canlı uygunluk teyidi vermez; tarihli duyuru eğitim bağlamıdır, sonraki değişiklikler işlem günü kontrol edilir.

Bu tur MTrader kaynak kodu veya canlı sistem test edilmedi. Proje karşılıkları mevcut KB taslaklarının kavramsal özetidir; güncel prod davranışı olarak sunulmaz.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
