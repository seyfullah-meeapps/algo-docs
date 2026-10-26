---
kapsam: Heartbeat, timeout, reconnect, snapshot/replay, dedup, idempotency ve retry
dis_kaynak:
  - url: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
    erisim: 2026-10-25
  - url: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Bağlantı ve kurtarma kavramları

Telefon görüşmesi koptuğunda tekrar aramak kolaydır. Ama “100 adet sipariş veriyorum” dedikten sonra ses kesildiyse zor soru şudur: karşı taraf siparişi aldı mı? Tekrar söylemek eksik işi tamamlayabilir veya ikinci sipariş oluşturabilir. Emir sistemindeki kurtarma problemini bu örnekle okuyalım.

## Heartbeat ve timeout

**Heartbeat**, bağlantının veya karşı tarafın canlılığını izlemek için gönderilen periyodik mesajdır. Koridordan “buradayım” diye seslenmek gibi düşünelim. Mesajın neyi kanıtladığı, kimden kime gittiği ve hangi süreyle beklendiği protokole bağlıdır. Heartbeat almak, stratejinin doğru karar verdiğini veya bütün piyasa verisinin güncel olduğunu göstermez.

**Timeout**, beklenen yanıtın belirlenen süre içinde gelmemesidir. “Süre doldu” gözlemdir; “karşı taraf hiç yapmadı” sonucu değildir. Varsayımsal üç durumu ayıralım:

| Kopma anı | Karşı tarafta olabilecek durum | Biz ne biliyoruz? |
|---|---|---|
| İstek ulaşmadan | İş yapılmadı | Sonuç henüz teyitsiz |
| İş yapıldı, yanıt ulaşmadı | İş tamamlandı | Sonuç henüz teyitsiz |
| İş hâlâ sürüyor | Daha sonra sonuçlanabilir | Sonuç henüz teyitsiz |

İstemci yalnız timeout gördüyse bu olasılıkları birbirinden ayıramayabilir. Özellikle durum değiştiren işlemlerde körlemesine tekrar yerine protokolün sorgulama ve tekrar kurallarına uyulur. [AWS — timeout ve retry](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

## Reconnect ile hazır olmak farklıdır

**Reconnect**, kopan iletişim kanalının yeniden kurulmasıdır. Bunun ardından login, yetki kontrolü, abonelik ve durum eşitlemesi gibi adımlar gerekebilir. Kapıyı yeniden açmak, içeride yokluğumuzda neler olduğunu öğrenmek değildir.

Genel bir toparlanma sırasını şöyle düşünebiliriz: **bağlantı → oturum → eksik/güncel durumu alma → uzlaştırma → iş yapmaya hazır olma**. Bu sıra öğretici modeldir; her MTrader bileşeninin otomatik ve aynı biçimde uyguladığı iddiası değildir. Bileşenin gerçek hazır olma koşulu kendi belgesinden okunur.

## Snapshot ve replay hangi boşluğu doldurur?

**Snapshot**, belirli bir noktadaki durum görüntüsüdür. “Şu an raflarda ne var?” sorusuna benzer. **Replay**, önceki olayların tekrar verilmesidir: “Ben yokken hangi ürünler girdi, hangileri çıktı?”

Öğretici akış: son işlediğimiz olay 120. Bağlantı kopukken 121–125 oluştu. Yeni snapshot 125 sonrasındaki durumu temsil ediyorsa canlı 126'dan devam etmek tutarlı bir seçenek olabilir. Aynı snapshot üzerine 121–125'i tekrar uygulamak, zaten içerilen değişiklikleri iki kez sayabilir. Snapshot'ın hangi sıra noktasını kapsadığı bu yüzden önemlidir.

Başka bir düzende 121–125 eksiksiz replay edilip sonra 126'ya geçilir. Hangi yöntem olduğu, oturum/partition kimliği, sıra numarası kapsamı ve canlıya geçiş tamponu protokolün konusudur. **Snapshot ile canlı akışın arasında boşluk veya çifte uygulama kalmamalıdır.**

Borsa bağlamındaki Glimpse/Rewinder ve emir oturumu replay ayrımı [önceki bölümde](../02-borsa-temelleri/11-glimpse-rewinder-replay.md) anlatıldı. Piyasanın defterini kurtarmak, kendi hesabımızın emir/gerçekleşme durumunu tek başına kurtarmış sayılmaz.

## Dedup: aynı olayı ikinci kez saymamak

**Deduplication**, aynı olay tekrar geldiğinde etkisini ikinci kez uygulamamaktır. Örneğin aynı gerçekleşme bildirimi yeniden alındığında pozisyonu tekrar +100 artırmamak gerekir. Bunun için doğru kapsamda güvenilir olay kimliği gerekir; yalnız fiyat ve miktar yeterli olmayabilir.

İki farklı gerçek işlem de aynı fiyat ve miktarda olabilir. “10 TL, 100 lot” aynı diye ikincisini atmak gerçek işlemi kaybettirebilir. Sequence veya işlem kimliğinin hangi oturum ve ürün kapsamında tekil olduğu ayrıca belirlenir.

## Idempotency: aynı talebin etkisini çoğaltmamak

**Idempotent işlem**, aynı isteğin tekrarlanmasının hedef durum üzerindeki etkisini çoğaltmayan işlemdir. “Durumu durdurulmuş yap” ile “100 lotluk yeni emir ekle” bu açıdan farklı düşünülmelidir. İkinci talep için desteklenen bir tekrar kimliği/dedup düzeni yoksa iki çağrı iki emir yaratabilir.

Kargo benzetmesinde aynı sipariş numarasıyla tekrar aradığımızda görevlinin mevcut siparişi bulması, yeni fiş açmaması istenir. Bu davranış, yalnız istemcinin bir numara yazmasıyla oluşmaz; karşı tarafın o numarayı hangi süre ve kapsamda nasıl işlediği sözleşmede tanımlı olmalıdır. [AWS — idempotent API ve güvenli tekrar](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

Dedup çoğunlukla **gelen olayın tekrarını**, idempotency **tekrarlanan talebin etkisini** konuşurken işimize yarar. İkisi ilişkili araçlardır; tek başlarına uçtan uca “tam bir kez” garantisi kurmazlar.

## Retry neden bekleyerek yapılır?

**Retry**, başarısız veya sonucu belirsiz denemeyi yeniden yapmaktır. **Backoff**, denemeler arasındaki beklemeyi artırmak; **jitter**, birçok istemcinin aynı anda yüklenmesini azaltmak için beklemeleri dağıtmaktır. Örneğin bütün istemcilerin tam aynı saniyede yeniden bağlanması, toparlanan sunucuyu tekrar zorlayabilir.

Ancak daha nazik aralıklarla tekrar etmek, tekrarın iş açısından güvenli olduğu anlamına gelmez. Önce neyin yeniden denenebileceği ve hangi kimlikle yapılacağı belirlenir; sonra süre ve sayı sınırları seçilir. Emir tekrarını bağlantı kurma tekrarıyla aynı kurala bağlamayız.

## MTrader testinde sonuç nasıl ifade edilir?

“Bağlantı geri geldi” yerine hazırlığın hangi aşamaya ulaştığını yazarız: oturum kuruldu mu, görüntü geldi mi, eksik olaylar tamamlandı mı, açık emirlerle gerçekleşmeler uzlaştı mı? Ekrandaki miktar ile kaynağın durumu birlikte kontrol edilir. Teknik ayrıntılar [HFT emir yaşam döngüsü](../../10-servisler/hftsrvprod/emir-yasam-dongusu.md) ve [ITCH alım yolu](../../10-servisler/itch-sdk/alim-yolu.md) belgelerinde kalır.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Kullanıcının toplu bölüm talebi kapsamında yazıldı. Telefon/kargo ve 120–126 sıra örnekleri öğreticidir. Yeni canlı kopma, replay veya emir testi yapılmadı.

## Kaynaklar ve doğrulama

AWS Builders' Library timeout/retry/backoff ve idempotent API yazıları, erişim 25 Ekim 2026. Genel toparlanma modeli bir MTrader garanti listesi değildir. Proje bağlantıları mevcut KB'deki referans incelemelere yönlendirir; bu konuda uygulama/SDK kodu yeniden doğrulanmadı.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [log, test ve sürüm](10-log-test-ve-surum.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
