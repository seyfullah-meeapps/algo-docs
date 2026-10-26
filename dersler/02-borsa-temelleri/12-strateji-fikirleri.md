---
kapsam: HFT, kademe takibi, arbitraj ve hedge; toplu emir, tavan/taban, piyasa yapıcılık ve gerçekleşme riski
dis_kaynak:
  - url: https://www.borsaistanbul.com/files/VIOP-Hakkinda-SSS.pdf
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
kullanici_incelemesi: 2026-10-25
---

# Stratejilerin temel fikirleri

Strateji, **hangi koşulda, hangi üründe, ne kadar ve nasıl işlem yapılacağını** belirleyen kurallar bütünüdür. Bu bölümde işlem fikirlerini tanıyoruz. MTrader'ın alan adları, GUI ekranları ve kesin tetik koşulları daha sonra her stratejinin kendi bölümünde açıklanacak.

## HFT ve kademe takibi

**HFT (High Frequency Trading)**, düşük gecikmenin ve hızlı otomatik kararların önem taşıdığı işlem yaklaşımını anlatır. Tek başına her HFT sisteminin aynı kuralla işlem yaptığı anlamına gelmez. MTrader'daki **HFT Classic** adı ise belirli bir stratejiyi ifade eder.

Kademe takibinin temel fikri, en iyi alış/satış seviyesindeki fiyat ve miktar değişimlerinden koşul üretmektir. Örneğin satış miktarının 1.000 adetten 100 adede inmesi dikkate alınabilir. Ama miktar azaldı diye fiyatın kesin yükseleceği veya bizim alışımızın gerçekleşeceği sonucu çıkmaz. Yeni emir gelebilir, miktar iptalle azalmış olabilir veya önce başka biri işlem yapabilir.

**Hız, kararın doğruluğunun yerine geçmez.** Testte hem beklenen sinyali hem emir sonucunu hem de sinyalin oluşmadığı durumu inceleriz.

## Arbitraj: ilişkili fiyatlar arasındaki fark

**Arbitraj**, ilişkili araçların fiyat farkından yararlanma fikridir. Spot–vadeli örneğinde pay ile ona dayalı sözleşme birlikte değerlendirilir. **Bacak**, bu birlikte düşünülen işlemlerin her bir tarafıdır.

Önceki örnekte spot pay 20 TL, vadeli fiyat 21 TL idi. Bu farkı doğrudan “pay başına garanti 1 TL kâr” diye okumayız. Finansman, temettü, vade, komisyon ve gerçekleşebilecek alış/satış fiyatları değerlendirilmelidir. Teorik karşılaştırma ile gerçekten işlem yapılabilen fiyat ayrıdır. [Borsa İstanbul — VİOP eğitim belgesi](https://www.borsaistanbul.com/files/VIOP-Hakkinda-SSS.pdf)

Birinci bacak gerçekleşip ikinci bacak gerçekleşmezse geçici açık risk oluşur. İki sözleşmenin 200 payı temsil ettiği örnekte yalnız 120 paylık karşı işlem yapılmışsa miktar dengesi tamamlanmamıştır. Fırsat hesabı doğru olsa bile uygulama sonucunun ayrıca izlenmesi gerekir.

MTrader'ın hangi bacağı önce gönderdiğini, miktarı nasıl eşlediğini ve eksik gerçekleşmede ne yaptığını arbitraj bölümünde kod referansıyla anlatacağız.

## Hedge: riski dengelemek

**Hedge (korunma)**, mevcut veya beklenen bir riski başka bir pozisyonla azaltmayı amaçlar. Örneğin elde tutulan payların fiyat düşüş riskini azaltmak için uygun vadeli kısa pozisyon düşünülebilir. Amaç mutlaka iki taraftan da kâr etmek değildir; bir taraftaki kaybın diğer taraftaki sonuçla dengelenmesidir.

Dayanak, miktar ve vade tam uyuşmazsa korunma eksik kalabilir. İki fiyatın ilişkisi beklendiği gibi değişmeyebilir; buna **baz riski** bağlamında bakılır. Arbitrajla hedge benzer araçları kullanabilir, fakat amaçları aynı değildir. [Borsa İstanbul — Korunma ve baz riski açıklamaları](https://www.borsaistanbul.com/files/VIOP-Hakkinda-SSS.pdf)

## Toplu emirler: birlikte hazırlamak, birlikte gerçekleşmek değildir

**Toplu emir**, birden fazla talimatın hazırlanması veya belirli zamanda iletilmesi fikridir. Her emir yine kendi fiyat, miktar, hesap ve geçerlilik koşulunu taşır. On emirden sekizi kabul edilip ikisi reddedilebilir; kabul edilenlerin de yalnız bir kısmı gerçekleşebilir.

Bu nedenle toplu gönderim sonucunu tek bir “başarılı” etiketine indirgemeyiz. Kaç isteğin üretildiğini, her birinin sonucunu ve varsa tekrar gönderimin nasıl ilişkilendirildiğini takip ederiz. Bu, bütün grubun tek atomik işlem olarak gerçekleştiği anlamına gelmez.

## Tavan ve taban stratejileri

Borsadaki **tavan/taban fiyatı** ürünün günlük fiyat sınırıdır. MTrader'daki **Tavan** ve **Taban** ise bu sınırlar çevresindeki olayları kullanan strateji adlarıdır. Sınırın kendisiyle stratejinin çalıştırılması farklı şeylerdir.

Bir pay tavanda beklerken büyük alış kuyruğu bulunabilir. Tavandan alış göndermek kesin gerçekleşme sağlamaz. Taban tarafında satış kuyruğu ve karşı alış miktarı da önemlidir. “Fiyat sınıra geldi” bilgisi, hangi yönde ne kadar emir üretileceğini tek başına tanımlamaz; ayarlar ve strateji durumu ayrıca gerekir.

## Piyasa yapıcılık ve kotasyon

**Kotasyon**, alış ve satış için fiyat/miktar sunmaktır. **Piyasa yapıcılık**, belirli kurallar altında çift taraflı kotasyonla likidite sağlamaya yönelik faaliyettir. BIST'in bu faaliyete ilişkin yetki ve yükümlülükleri vardır; yazılımın iki taraflı emir vermesi tek başına resmi piyasa yapıcı statüsü kazandırmaz. [Borsa İstanbul — Piyasa yapıcılık](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/piyasa-isleyisi)

Alış ve satış arasındaki fark gelir fırsatı olabilir; yalnız alışların gerçekleşmesi hâlinde ise elde pozisyon birikir. Spread bulunması garanti gelir değildir. Genel fikri tanımamız yeterli; kullanılmayan BYF/Fon Takibi stratejisini burada ana örnek yapmıyoruz.

## Strateji belgelerini nasıl okuyacağız?

Her stratejide aynı zinciri kuracağız: **başlangıç durumu → parametreler → gelen olay → beklenen karar → emir sonucu → yeni durum**. Sonucun yalnız emir üretmek veya kâr etmek olmadığını; doğru koşulda beklemek, durmak ve kısmi sonucu yönetmek de olabileceğini göreceğiz.

Ayrıntılı çalışma önceliğimiz **HFT → Arbitraj → Toplu Emirler → Tavan → Taban**. Bu bölüm temel fikirleri tamamladı. Borsa bölümünün toplu revizyonundan sonra teknik temellere, ardından sistem bağlantılarına geçilecek.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi:** Borsa bölümünün kalan konuları tek turda tamamlansın, ardından toplu revize edilsin. Bu konu bu kapsamda yazıldı; özel bir soru henüz yok. Sayısal senaryolar öğretici örnektir.

## Kaynaklar ve doğrulama

Resmi BIST VİOP eğitim belgesinin korunma/baz riski/arbitraj kavramları ve Pay Piyasası piyasa yapıcılık açıklaması okundu; erişim 24 Ekim 2026. VİOP eğitim PDF’si tarihsel (2017) kavram kaynağıdır, güncel ürün/teminat kuralı için kullanılmadı. MTrader adları ve kapsamı mevcut [strateji kataloğu](../../20-stratejiler/README.md) ile kullanıcının önceliklerinden alındı; kesin parametre sözleşmesi oluşturulmadı.

Bu tur MTrader kaynak kodu veya canlı sistem test edilmedi. Proje karşılıkları mevcut KB taslaklarının kavramsal özetidir; güncel prod davranışı olarak sunulmaz.

## Devam notu

Kullanıcı 25 Ekim 2026 tarihinde buraya kadarki bütün içeriği okuduğunu ve ek değişiklik gerekmediğini belirtti. İçerik incelemesi tamamlandı; bu beyan yeni kod/canlı sistem doğrulaması değildir. Teknik Temeller bölümüne geçiş onayı verildi.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
