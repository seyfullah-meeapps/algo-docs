---
kapsam: Latency/throughput, yüzdelikler, hot/cold path, pinning, cache ve kernel bypass
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dis_kaynak:
  - url: https://docs.kernel.org/admin-guide/cgroup-v2.html
    erisim: 2026-10-25
  - url: https://www.kernel.org/doc/html/latest/networking/af_xdp.html
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Gecikme, colocation ve performans

Bir restorana saatte 1.000 sipariş işleyebilen mutfak kurmakla, tek müşterinin yemeğini 5 dakikada çıkarmak aynı başarı değildir. İlki **kapasite**, ikincisi **bekleme süresi** hakkında bilgi verir. Hız konuşurken bu iki soruyu ayıracağız.

## Latency ve throughput

**Latency (gecikme)**, belirli başlangıçla bitiş arasındaki süredir. **Throughput**, birim zamanda tamamlanan iş miktarıdır. “Saniyede 100.000 olay işliyoruz” demek, her olayın kaç mikrosaniye beklediğini söylemez. Hızlı bir işlemci, önünde uzun kuyruk varsa geç yanıt verebilir.

Öğretici örnek: olay kuyrukta 40 µs bekledi, karar 8 µs sürdü, gönderime hazırlanması 2 µs sürdü. Seçtiğimiz ölçüm aralığı için toplam **50 µs** olur. Yalnız karar fonksiyonunu ölçersek 8 µs görürüz. İkisi de kendi kapsamıyla doğru olabilir; ölçüm sınırları yazılmadığında yanıltır.

**Tick-to-trade**, piyasa olayı ile ona karşı emir üretimi arasındaki gecikme için kullanılan addır. Başlangıç NIC alımı mı, SDK callback'i mi? Bitiş socket'e yazma mı, borsa onayı mı? Adı tek başına cevap vermez. Ölçüm noktaları ve saat kaynağı belirtilmelidir.

## Ortalama neden yetmez?

Varsayımsal 100 ölçümün 99'u 10 µs, biri 1.000 µs olsun. Ortalama `(99 × 10 + 1.000) / 100 = 19,9 µs` çıkar. Oysa bir olay 1 ms beklemiştir. Ortalama, bu nadir uzun beklemeyi tek başına görünür kılmaz.

**p50**, gözlemlerin yaklaşık yarısının; **p99**, yaklaşık yüzde 99'unun altında kaldığı değeri anlatır. Hesap yöntemi, örnek sayısı ve zaman penceresi belirtilmelidir. **Tail latency**, dağılımın yavaş uç kısmıdır; p99/p99.9 gibi değerlerle incelenebilir. Maksimum değer ise yalnız ölçülen aralıktaki en yavaş örnektir; gelecekte aşılmayacak sınır değildir.

Bir raporda yalnız “p99 30 µs” görmek yerine olay sayısı, yük, süre, ölçüm sınırları ve kayıp/atılan örnekler de gerekir. Düşen olaylar ölçüme hiç girmediyse kalan olayların hızlı olması bütün sistemin iyi çalıştığını göstermez.

## Colocation: yolun fiziksel kısmını kısaltmak

**Colocation**, sunucuyu borsanın erişim altyapısına yakın bir veri merkezi ortamında konumlandırmaktır. Şehrin öbür ucundan gelen kurye yerine yakın depodan sevkiyat gibi düşünebiliriz. Fiziksel yol ve ağ düzeni gecikmeyi etkiler; yakınlık fırsatı ilk gören veya emri ilk gerçekleşen olmayı tek başına garanti etmez.

İşlem sırası, uygulama kuyruğu, borsa kontrolleri ve başka katılımcıların davranışı da sonucu etkiler. Bu yüzden colocation ile kârlılık veya sıra önceliği arasında otomatik eşitlik kurmayız. MTrader'ın gerçek dağıtım ve bağlantı haritası [sistem haritasında](../../bilgi-tabani/00-genel/sistem-haritasi.md) ve operasyon belgelerinde kalır; burada fiziksel yakınlığın anlamını öğreniyoruz.

## Hot path ile cold path

**Hot path**, gecikmeye en duyarlı ve sık çalışan akıştır: örneğin olayı almak, karar vermek, emri hazırlamak. **Cold path**, açılışta ayar yükleme veya daha seyrek yönetim işleri gibi farklı gecikme beklentisi olan yollardır. Bunlar dilin sabit kuralları değil, mimari tasarımda kullanılan adlardır.

Öğretici örnek: her fiyat olayında diskteki ayar dosyasını okumak yerine ayarları önceden bellekte hazırlamak, karar yolundaki işi azaltabilir. Ama ayar değiştiğinde yeni değerin ne zaman etkin olacağı da tanımlanmalıdır. Hız için durum tutarlılığını gözden kaçırmayız.

## Düşük gecikmede duyacağımız terimler

| Terim | Basit anlamı | Dikkat edilen ayrım |
|---|---|---|
| CPU pinning / affinity | Thread'i belirli CPU'larda çalıştırmak | CPU'yu tek başına ona ayırmak değildir |
| Cache | İşlemcinin yakın ve hızlı veri alanları | Her erişimin cache'de olması garanti değildir |
| Allocation | Nesne için bellek ayırmak | Önceden ayırma ile olay anında ayırma farklıdır |
| Batching | Birden çok işi birlikte işlemek | Kapasite artarken tek olay bekleyebilir |
| Kernel bypass | Ağ yolunun bazı işlerini kullanıcı alanına taşımak | Her mod aynı donanım/garantiyi sunmaz |

Affinity için izin verilen CPU kümesi ve kaynak sınırları işletim sistemi/container ayarlarıyla ilişkilidir. [Linux cgroup v2 kaynak yönetimi](https://docs.kernel.org/admin-guide/cgroup-v2.html)

Kernel bypass tek bir ürünün adı değildir. Örneğin Linux AF_XDP, paketlerin kullanıcı alanındaki tamponlara yönlendirilmesine imkân veren bir mekanizmadır. Bu örnek, MTrader'ın AF_XDP kullandığı iddiası değildir; kullanılan SDK modu, NIC ve build ayrıca belirlenir. [Linux AF_XDP](https://www.kernel.org/doc/html/latest/networking/af_xdp.html)

## MTrader'da ölçümü nasıl okuyacağız?

HFT referans worker kodunda koşullu CPU affinity ayarı bulunur. Bunun bulunması, incelenen makinede pinning'in açık veya başarılı olduğunu kanıtlamaz. Ayar, çalışma log'u ve gerçek CPU yerleşimi birlikte değerlendirilir.

Mevcut KB, performans ölçüm bileşenini [performance-sdk](../../bilgi-tabani/10-servisler/performance-sdk/README.md) altında anlatır. Metrik ismini gördüğümüzde başlangıç/bitiş noktalarını oradan ve çağıran koddan takip ederiz. Ekranın yenilenme süresi ile motorun karar gecikmesini aynı sayı gibi karşılaştırmayız.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Toplu bölüm talebi kapsamında. 50 µs ve 19,9 µs hesapları eğitim senaryosudur; gerçek MTrader benchmark sonucu veya hedefi değildir.

## Kaynaklar ve doğrulama

Linux cgroup v2 ve AF_XDP resmi belgeleri, erişim 25 Ekim 2026. HftSrvProd development `4275ccc`, `src/Workers/AlgoWorker.cpp` içindeki `eventDispatcherLoop` affinity dalı salt okunur incelendi. performance-sdk bağlantısı mevcut KB'dir; bu tur SDK tekrar doğrulanmadı. Gecikme sayıları varsayımsal, percentile açıklaması genel istatistik kavramıdır. Benchmark, NIC/build/config veya canlı CPU yerleşimi doğrulaması yapılmadı.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [bağlantı ve kurtarma](09-baglanti-ve-kurtarma.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
