---
kapsam: Güncel defter görüntüsü, eksik mesaj kurtarma, sıra numarası ve emir oturumu replay ayrımı
dis_kaynak:
  - url: https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/itch-protokolu
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/files/bistech-itch-protocol-specification-sr-3-12.pdf
    erisim: 2026-10-24
  - url: https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/soupbintcp.pdf
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# Glimpse, Rewinder ve replay

Uygulama açıldığında piyasa gün boyunca çalışmış olabilir. Bağlantı sırasında bazı mesajlar kaçırılmış da olabilir. Böyle durumlarda “yeni mesajları dinlemeye başladım” demek, elimizdeki defterin eksiksiz olduğunu göstermez.

## Görüntü ile olay geçmişi

**Snapshot**, belirli bir andaki durumun görüntüsüdür. **Olay akışı** ise bu durumun zaman içinde nasıl değiştiğini anlatır. Bir defter fotoğrafında 500 adet görmek, daha önce kaç emir girilip iptal edildiğini söylemez.

Bir apartmanın o anki sakin listesini almakla gün boyunca kimlerin girip çıktığını kaydetmek arasındaki fark gibi düşünebiliriz. İkisi farklı soruları yanıtlar.

| Araç | Yanıtladığı soru |
|---|---|
| Glimpse | Şu andaki emir defteri görüntüsünü nasıl alırım? |
| Rewinder | Kaçırdığım belirli piyasa verisi mesajlarını nasıl geri isterim? |
| Emir oturumu replay | Kendi emir bağlantımın kaçırdığım sonuçlarını nasıl yeniden alırım? |

BIST, Glimpse ve Rewinder'ı ITCH veri akışının başlangıç/kayıp kurtarma hizmetleri olarak açıklar. Bunlar kendi emrimizi borsaya tekrar gönderme komutu değildir. [Borsa İstanbul — ITCH hizmetleri](https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/itch-protokolu)

## Sıra numarası neden gerekli?

**Sequence**, akışın sıra numarasıdır. Örnek bir akışta 100, 101 ve ardından 104 geldiğini düşünelim. 102 ve 103'ün görünmemesi bir **boşluk (gap)** olduğunu gösterir. 104'ü görmek, eksik iki mesajın etkisini tahmin etmemizi sağlamaz.

| Gelen olay | Nasıl yorumlarız? |
|---|---|
| 100, 101 | Beklenen sıra ilerliyor |
| 104 | Arada eksik bölüm var |
| 102 ve 103 kurtarıldı | Eksik bölüm sıralı işlenebilir |
| 104 tekrar geldi | Aynı olayın etkisini iki kez uygulamamak gerekir |

Numaralar gerçek piyasa kaydı değildir. Sıra, ilgili akış/oturum bağlamında anlamlıdır; farklı akışların 104 numaralı mesajları aynı olay sayılmaz.

## Glimpse ile başlangıç

Geç bağlanan istemci önce güncel defter görüntüsünü alabilir. Canlı yayın bu sırada ilerlediği için görüntü ile sonrasındaki mesajlar **doğru sıra sınırında** birleştirilmelidir. Eski olayın iki kez uygulanması veya aradaki olayın atlanması defteri bozabilir.

BIST ITCH belgesinin akış açıklamasında Glimpse sonunda bildirilen sıra ile canlı yayına devam edilmesi; kurtarma sırasında canlı yayının da dinlenmesi anlatılır. Snapshot, geçmişteki bütün işlemlerin listesi değildir. [ITCH spesifikasyonu, Appendix E](https://www.borsaistanbul.com/files/bistech-itch-protocol-specification-sr-3-12.pdf)

## Rewinder ile eksik bölümü tamamlama

Güncel bir defterimiz varken belirli mesajlar kaçmışsa eksik bölüm Rewinder'dan istenebilir. Bu, baştan yeni defter görüntüsü almaktan farklıdır. Kurtarılan mesajlar da doğru sıralama ve tekrar kontrolüyle işlenmelidir.

Birincil/ikincil yayın hatlarının ve geçmiş mesaj saklama sınırlarının davranışı protokol/servis sözleşmesine bağlıdır. Her büyüklükte boşluğun her zaman Rewinder ile kapatılabildiğini varsaymayız; kurtarma başarısızsa eksiksiz veri varmış gibi devam etmek doğru bir test beklentisi olmaz.

## Emir oturumu replay farklıdır

Emir bağlantısı koptuğunda borsadan gelen kabul veya gerçekleşme mesajı kaçmış olabilir. Oturumun geçmiş mesajlarını yeniden almak **yeni emir oluşturmak** değildir. SoupBinTCP, oturum ve istenen sıra üzerinden sıralı veriye devam etme mekanizmasını tanımlar. [Nasdaq — SoupBinTCP 3.00](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/soupbintcp.pdf)

Örneğin kopma sırasında 40 adet gerçekleştiyse aynı gerçekleşmeyi tekrar öğrenmek, 40 adet daha işlem yapmak anlamına gelmez. Uygulama yeniden gelen bilgiyi mevcut kayıtla ilişkilendirmelidir. “Replay tamamlandı” ile “yeni emir göndermeye hazırız” arasındaki uygulama hazırlık koşulları ayrıca belirlenir.

## MTrader'da neyi gözlemleriz?

Mevcut itch-sdk belgesi başlangıç görüntüsü, canlı mesaj tamponu ve gap kurtarmasını ayrı anlatır. Bu konudaki amacımız thread ve paket ayrıntılarını ezberlemek değil, **bağlantı varlığı ile veri bütünlüğünün ayrı olduğunu** anlamaktır.

Testte yalnız ekranın yeniden hareket ettiğine bakmayız. Hangi akışta boşluk olduğu, neyin kurtarıldığı, son bilinen emrin/pozisyonun nasıl doğrulandığı ve uygulamanın ne zaman hazır sayıldığı kaydedilir. Veri kurtarma, kendi emir sonuçlarını kurtarma ve yeni emir gönderimini birbirine karıştırmayız.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** Borsa bölümünün kalan konuları tek turda tamamlansın, ardından toplu revize edilsin. Bu konu bu kapsamda yazıldı; özel bir soru henüz yok. Sayısal senaryolar öğretici örnektir.

## Kaynaklar ve doğrulama

Resmi BIST ITCH tanıtımı ve ITCH SR 3.12 belgesinin arama motorunda erişilebilen Appendix E metni kullanıldı; PDF’nin doğrudan web açılması bu tur başarısız oldu. Bu nedenle byte/transport ayrıntıları veya en güncel sürüm iddiası verilmedi. SoupBinTCP Nasdaq 3.00 belgesi doğrudan okundu. Erişim 24 Ekim 2026. Uygulama bağlamı [itch-sdk alım yolu](../../bilgi-tabani/10-servisler/itch-sdk/alim-yolu.md) ve [emir dönüşü](../../bilgi-tabani/30-akislar/emir-donusu.md) mevcut taslaklarından alındı; kurtarma testi yapılmadı.

Bu tur MTrader kaynak kodu veya canlı sistem test edilmedi. Proje karşılıkları mevcut KB taslaklarının kavramsal özetidir; güncel prod davranışı olarak sunulmaz.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
