---
kapsam: Piyasa verisi ve emir kanalı ayrımı; ITCH, OUCH ve FIX görevleri, mesaj akışı ve referans veri
dis_kaynak:
  - url: https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/itch-protokolu
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/ouch-protokolu
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/fix-protokolu
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# ITCH, OUCH ve FIX

Uygulamanın borsayla konuşması tek bir bağlantıdan ibaret değildir. Bir tarafta **piyasada ne olduğunu öğreniriz**, diğer tarafta **kendi emirlerimizi iletir, sonuçlarını alırız**. Protokol, bu iletişimde mesajların nasıl kurulacağını belirleyen kurallardır.

## Üç adı görevleriyle eşleştirelim

| Protokol | Bu rehberdeki temel görev | Örnek soru |
|---|---|---|
| ITCH | Emir bazlı piyasa verisi | Bu üründe hangi alış/satış emirleri ve işlemler var? |
| OUCH | Yeni emir, değişiklik, iptal ve sonuçlar | Bizim gönderdiğimiz emre ne oldu? |
| FIX | Standart mesajlarla finansal iletişim; emir iletimi ve başka hizmetler | Emir isteği/sonucu veya ilgili referans veri nasıl aktarılır? |

**ITCH**, BIST'in binary, yani ikili biçimde mesaj taşıyan emir bazlı piyasa veri yayınıdır. Veri çok sayıda alıcıya multicast ile dağıtılır. **OUCH**, emir iletimine yönelik düşük gecikmeli arayüzdür. **FIX** ise Financial Information eXchange adlı standarttır; BIST'in desteklediği profil ve mesajlar kendi spesifikasyonlarıyla belirlenir. [ITCH](https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/itch-protokolu), [OUCH](https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/ouch-protokolu), [FIX](https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/fix-protokolu)

## Bir işlemde iki ayrı bilgi akışı

Öğretici akışımız şöyle olabilir:

1. Piyasa verisinde bir satış kademesinin miktarı değişir.
2. Strateji, kendi kuralları uygunsa alış kararı verir.
3. Emir iletim kanalıyla yeni emir gönderilir.
4. Emir kanalından kabul, ret veya gerçekleşme sonucu gelir.
5. Piyasa verisinde de defter/işlem değişiklikleri görülebilir.

Bu sıra kavramsaldır; farklı bağlantılardaki mesajların uygulamaya ulaşma sırası aynı olmak zorunda değildir. Piyasa verisinde işlem görmek, bu işlemin bize ait olduğunu tek başına söylemez. Kendi emrimizin kimliği ve sonuç mesajı ayrıca ilişkilendirilir.

## Piyasa defteri ile kendi emir kaydımız

**Piyasa defteri** başkalarının emirlerini de içeren görünümü anlatır. **Kendi emir kaydımız** ise hangi hesapla ne gönderdiğimizi, kabul/ret ve gerçekleşme bilgisini içerir. Hesap sahibini piyasa defterindeki her emirden okuyabildiğimizi varsaymayız.

Bu nedenle “fiyat güncelleniyor, demek emir kanalımız da çalışıyor” diyemeyiz. Piyasa verisi alınırken emir iletimi kopmuş olabilir; emir sonuçları gelirken defter verisi eski kalmış olabilir. Testlerde bu yollar ayrı gözlemlenir.

## FIX yalnız bir emir bağlantısının adı mı?

BIST, FIX emir iletiminden ayrı **FIX Reference Data** ve **FIX Drop Copy** hizmetlerini de açıklar. Reference Data kıymet/seans gibi tanımları, Drop Copy ise kapsamına göre emir ve işlem mesajlarının ek kopyalarını sağlar. Her FIX bağlantısının aynı bilgiyi taşıdığı varsayılmaz. [Borsa İstanbul — FIX hizmetleri](https://www.borsaistanbul.com/bistech-teknolojisi/baglanti-protokolleri/fix-protokolu)

OUCH/FIX seçimi stratejinin işlem fikrini değiştirmek zorunda değildir; fakat desteklenen alanlar, emir türleri, oturum kuralları ve mesaj eşlemesi değişebilir. Bir protokoldeki alanı diğerine yalnız adı benziyor diye kopyalamayız.

## MTrader'daki karşılığı

Mevcut bilgi tabanında piyasa verisi tarafı **itch-sdk**, doğrudan borsa emir bağlantıları ise **MAOrderSDK** bağlamında anlatılır. **ouch-sdk** adlı proje ise isminden beklenebileceğinin aksine uygulamanın order-service istemci katmanıdır; doğrudan BIST OUCH bağlantısı diye okunmamalıdır. Ayrıntılı bileşen haritasını mimari bölümünde kuracağız.

Şimdilik şu üç soruyla ilerlemek yeterli: “Bu veri piyasayı mı, kendi emrimizi mi anlatıyor?”, “Hangi bağlantıdan geldi?” ve “Hangi sürüm/mesaj sözleşmesiyle yorumlanıyor?” TCP/UDP, binary ve bağlantı ayrıntıları teknik temellerde açılacak.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** Borsa bölümünün kalan konuları tek turda tamamlansın, ardından toplu revize edilsin. Bu konu bu kapsamda yazıldı; özel bir soru henüz yok. Sayısal senaryolar öğretici örnektir.

## Kaynaklar ve doğrulama

BIST’in resmi ITCH, OUCH ve FIX tanıtım sayfaları 24 Ekim 2026’da okundu; web sayfalarında ayrı sürüm tarihi yoktur. Teknik belge kataloğunda sürümler bulunduğu görüldü, çalışan sistemin bu sürümlerden hangisini kullandığı bu tur doğrulanmadı. Proje eşlemesi mevcut [sözlük](../../00-genel/sozluk.md), [itch-sdk](../../10-servisler/itch-sdk/README.md), [MAOrderSDK](../../10-servisler/maordersdk/README.md) ve [ouch-sdk](../../10-servisler/ouch-sdk/README.md) taslaklarına dayanır.

Bu tur MTrader kaynak kodu veya canlı sistem test edilmedi. Proje karşılıkları mevcut KB taslaklarının kavramsal özetidir; güncel prod davranışı olarak sunulmaz.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
