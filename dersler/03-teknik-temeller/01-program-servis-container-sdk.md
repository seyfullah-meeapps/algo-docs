---
kapsam: Repo, binary, process, servis, image/container ve SDK ayrımı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dis_kaynak:
  - url: https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Program, servis, container ve SDK

Bir ekip arkadaşı “SDK güncellendi ama servis eski” dediğinde iki farklı şeyden söz ediyor olabilir. Bunu anlamak için kodun yazıldığı yerden çalıştığı ana kadar olan adları ayıralım. Bir restoranın tarifi, hazırlanmış yemeği ve o an çalışan mutfağı aynı şey değildir; yazılımda da kaynak kod, çalıştırılabilir dosya ve çalışan süreç ayrıdır.

## Koddan çalışan programa

**Repo (repository)** kaynak kodun ve değişiklik geçmişinin tutulduğu depodur. Frontend'deki React bileşenlerinin Git reposunda durması gibi, C++ motorunun kodu da bir repoda durur. Repo klasörünün bilgisayarda bulunması, programın çalıştığını göstermez.

**Build**, kaynaklardan çalıştırılacak çıktıları üretme işidir. C++ kodu derlenip bağlanarak çalıştırılabilir bir **binary** ve gerekirse kütüphaneler oluşturur. Frontend'deki build'in tarayıcıya gönderilecek dosyaları üretmesine benzetebiliriz; çıktı biçimleri farklıdır.

**Process (süreç)** programın çalıştırılmış halidir. Aynı binary iki kez başlatılırsa ayrı bellekleri ve kimlikleri olan iki süreç oluşabilir. Dosyayı yenilemek ile çalışan süreci yeni dosyadan başlatmak da farklı adımlardır.

| Sorulan şey | Somut karşılığı | Tek başına neyi göstermez? |
|---|---|---|
| Repo güncel mi? | Hangi commit'in kodu var? | O kodun derlendiğini |
| Binary güncel mi? | Hangi build çıktısı var? | O dosyanın şu an çalıştığını |
| Process çalışıyor mu? | Çalışan örnek var mı? | Borsa bağlantılarının hazır olduğunu |
| Servis hazır mı? | İşini yapabilecek durumda mı? | Her stratejinin çalıştığını |

**Servis**, başka bileşenlere sürekli bir iş sunan uygulama rolüdür. Örneğin veri sağlamak veya emir isteklerini işlemek. “Servis” sözcüğü bazen bu rol, bazen çalışan süreç, bazen de Compose içindeki tanım için kullanılır. Bir kayıtta hangisinin kastedildiğini açık yazmak belirsizliği azaltır.

## Image ile container arasındaki fark

**Image**, programın çalışacağı dosya sistemi ve bağımlılıklar için hazırlanmış kalıptır. **Container**, bu kalıptan oluşturulan, kendi ayarları ve çalışma durumu olan örnektir. Aynı image'dan farklı config'lerle iki container başlatılabilir. Container duruyor da olabilir; adının listede görünmesi çalıştığını kanıtlamaz.

Bir benzetmeyle image mutfak için hazırlanmış standart ekipman paketi, container ise o paketle açılmış belirli mutfaktır. Günün menüsü ve malzeme durumu config/veri gibi ayrıca değişebilir. [Docker'ın container açıklaması](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)

Container bir sanal makineyle aynı şey değildir; olağan Linux container'ları host çekirdeğini paylaşır. Ağ, dosya bağlama ve yetki ayarları çalışma koşullarını etkiler. “Image aynı” bilgisi bütün ortamların davranışının aynı olduğunu göstermez.

## SDK ayrı bir servis olmak zorunda değil

**Kütüphane**, başka programın kullandığı hazır kod parçasıdır. **SDK**, belirli işi yapmak için sunulan API, kütüphane, başlık ve yardımcı araç bütünüdür. JavaScript'te bir paketi import edip uygulama içinde kullanmamıza benzetebiliriz.

Bir SDK'nın ayrı reposu olması, ayrı container olarak çalışacağı anlamına gelmez. Paylaşımlı kütüphane biçimindeki `.so` dosyası, onu kullanan sürecin içine yüklenebilir. SDK kendi thread'lerini başlatsa bile bunlar aynı sürecin thread'leri olabilir.

MTrader'da HFT motoru ile ITCH SDK'sını bu ayrımla okuyacağız: motor stratejiyi çalıştırır, kullandığı SDK piyasa verisi için işlevler sunar. HFT'nin referans build tanımı `HftSrvProd` çalıştırılabilir dosyasını üretir ve `MAItchSDK` ile `MAOrderSDK` kütüphanelerini arar. Ayrıntılı bağımlılık haritası [HFT servis belgesindedir](../../10-servisler/hftsrvprod/README.md).

## “Güncelledik” dendiğinde hangi zinciri takip ederiz?

Varsayımsal bir SDK değişikliği düşünelim: geliştirici düzeltmeyi commit'ledi, fakat test makinesinde eski kütüphane kullanılıyor. Kaynak kod doğru olsa da yeni davranış testte görünmeyebilir. Kontrol sırası **kaynak commit → build çıktısı → dağıtılan dosya/image → çalışan süreç → yüklenen config** olur.

Bu sıra, MTrader'ın müşteri kabul sürecinin yerine geçmez. Teknik sürüm zinciri ile test/preprod/müşteri süreci farklı sorulara yanıt verir. Ortam ve dağıtım ayrıntıları [branch ve ortamlar](../../00-genel/branch-ve-ortamlar.md) ile sonraki sistem bölümünde ele alınacak.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Kullanıcı önceki 14 konuyu okuduğunu, ek değişiklik gerekmediğini ve Teknik Temeller bölümünün tamamının tek turda yazılmasını istedi. Ortak karar [kararlar dosyasında](../kararlar.md); bu yeni konu henüz kullanıcı tarafından incelenmedi. Restoran ve SDK güncelleme örnekleri eğitim örnekleridir.

## Kaynaklar ve doğrulama

Docker'ın resmi container sayfası 25 Ekim 2026'da okundu. HftSrvProd development `4275ccc` için `CMakeLists.txt` salt okunur incelendi: executable ve kütüphane bağımlılıkları teyit edildi. Bu KB referans commit'idir; yerel development ucu daha ileridedir. Build, deploy veya çalışan binary/config testi yapılmadı; güncel prod iddiası yoktur.

## Devam notu

Taslak tamamlandı, teknik bölümle birlikte toplu kullanıcı incelemesi bekleniyor. Sonraki konu [ağ ve taşıma protokolleri](02-ag-tcp-udp-multicast.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
