---
kapsam: Callback, event loop, producer/consumer, mutex, atomic, race ve deadlock
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dis_kaynak:
  - url: https://eel.is/c++draft/intro.races
    erisim: 2026-10-25
  - url: https://eel.is/c++draft/thread.mutex.requirements.mutex
    erisim: 2026-10-25
  - url: https://eel.is/c++draft/atomics.order
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Thread, kuyruk ve eşzamanlılık

Bir restoranda garson sipariş alırken aşçı yemek hazırlayabilir. İki kişi aynı işi yapmaz ama aynı sipariş hakkında bilgi kullanır. Yazılımda **eşzamanlılık**, birden fazla işin zaman içinde birlikte ilerlemesidir. **Paralellik**, bunların gerçekten aynı anda farklı yürütme kaynaklarında çalışmasıdır.

## Process'in içinde çalışan thread'ler

**Thread**, süreç içindeki yürütme akışıdır. Aynı process'in thread'leri belleğin önemli bölümünü paylaşır. Biri strateji ayarını değiştirirken diğeri fiyat olayı işliyor olabilir. Her thread'in kendi çağrı akışı olsa da ortak nesneler üzerinde anlaşmaları gerekir.

Frontend'deki event handler fikri tanıdıktır: kullanıcı tıklar, bir fonksiyon çalışır. **Callback**, bir olay olduğunda çağrılmak üzere verilen fonksiyondur. **Event loop**, bekleyen olayları alıp ilgili işlemleri yürüten döngüdür. Callback, kendiliğinden yeni thread demek değildir; onu çağıran thread'de çalışabilir.

Öğretici örnek: fiyat callback'i içinde 100 ms süren dosya okuması yaparsak aynı akışın sonraki olayları bekleyebilir. Bu yüzden “fonksiyon kısa” ile “beklemeden çalışıyor” aynı şey değildir. İşin nerede çalıştığını ve hangi beklemeleri yaptığını bilmek gerekir.

## Kuyruk: işi başka çalışana devretmek

**Producer (üretici)** olayı kuyruğa koyar; **consumer (tüketici)** alıp işler. Garsonun fişi mutfağın panosuna bırakması gibi düşünelim. Fişin panoya konması, yemeğin hazır olduğu anlamına gelmez.

| An | Üretici | Kuyruk / tüketici |
|---|---|---|
| 1 | Fiyat olayı A'yı aldı | Tüketici önceki işi yapıyor |
| 2 | A'yı kuyruğa koydu | A bekliyor |
| 3 | Başka olay almaya devam etti | Tüketici A'yı alıp işledi |

Kuyruk gecikmeyi ortadan kaldırmaz; beklemenin yerini değiştirir. Öğretici hesap: 1 ms içinde 1.000 olay geldi, tüketici aynı sürede 800 olay işledi. Başlangıçta boşsa ve olay atılmıyorsa 200 olay birikir. Bu hız farkı sürerse kuyruk büyür.

**Backpressure**, tüketici yetişemediğinde üretim/gönderim hızını sınırlamaya yönelik düzendir. Kapasiteli kuyruğun dolunca ne yaptığı ayrıca sözleşmedir: bekletebilir, reddedebilir veya olay düşürebilir. Sınırsız kuyruk da sınırsız RAM vermez. **SPSC**, tek üretici ve tek tüketici; **MPSC**, çok üretici ve tek tüketici gibi kullanım düzenlerini anlatır. Bir kuyruğun hangi düzen için tasarlandığı önemlidir.

## Aynı sayıyı iki kişi değiştirirse

Başlangıçta `gerceklesen = 0` olsun. İki görevli aynı kaydı okuyup biri +30, diğeri +20 ekliyor. İkisi de 0'ı okur ve kendi sonucunu yazarsa son değer 50 yerine 20 veya 30 kalabilir. Bu, işlemlerin iç içe geçmesiyle oluşan **race condition** fikrini gösterir.

C++'ta senkronize edilmemiş, aynı bellek konumuna yapılan çakışan erişimlerde en az biri yazmaysa ve gerekli sıralama yoksa **data race** oluşabilir; dil düzeyinde davranış tanımsızdır. Yukarıdaki kayıp güncelleme, öğretici bir sıra örneğidir; böyle C++ kodunun yalnız o iki sonucu vereceği garantisi değildir. [C++ data race modeli](https://eel.is/c++draft/intro.races)

## Mutex ve atomic farklı araçlardır

**Mutex**, ortak verinin belirli bölümüne aynı anda tek thread'in girmesini sağlar. Tek anahtarlı kayıt dolabı gibi: anahtarı alan işi bitirip bırakır. Koruma işe yarasın diye aynı veriye erişen ilgili yolların aynı kurala uyması gerekir. RAII tabanlı kilit nesneleri kapsam bitince kilidi bırakmaya yardımcı olur. [C++ mutex](https://eel.is/c++draft/thread.mutex.requirements.mutex)

**Atomic**, belirli değişken üzerindeki işlemler için atomiklik ve seçilen bellek sıralaması sağlar. Örneğin atomik bir sayaca `fetch_add` ile ekleme yapılabilir. Fakat pozisyon, ortalama maliyet ve durum gibi üç alanı ayrı ayrı atomic yapmak, üçünün birlikte tutarlı bir fotoğraf olarak görülmesini kendiliğinden sağlamaz. [C++ atomic sıralama](https://eel.is/c++draft/atomics.order)

**Lock-free**, kilit kullanmadan ilerleme sağlayan algoritma sınıfıdır; bütün işlemlerin anında biteceği veya bütün tasarımın daha hızlı olacağı anlamına gelmez. **Busy-spin**, yeni iş var mı diye sürekli kontrol etmektir; **blocking wait**, beklerken thread'in uyumasına izin verir. CPU kullanımı, uyanma gecikmesi ve yük arasında seçim yapılır.

## Deadlock: iki kişinin birbirini beklemesi

Thread A pozisyon kilidini almış, emir kilidini bekliyor. Thread B emir kilidini almış, pozisyon kilidini bekliyor. İkisi de elindekini bırakmadan diğerini istediği için ilerleyemez. Buna **deadlock** denir.

Bu durum yavaş çalışmaktan farklıdır. Çok beklenen bir ağ yanıtı, uzun hesap ve deadlock ekranda benzer donma üretebilir; kanıt için hangi thread'in nerede beklediği gerekir. Kilit sırası ve kilit altında çağrılan işler kod incelemesinin konusudur.

## MTrader'da göreceğimiz karşılık

HFT referans `AlgoWorker` kodunda ayrı worker thread'i, olay kuyruğuna sahiplik devri ve kuyruktan olay çekme vardır. Bunlar bu konudaki “alım” ile “işleme” ayrımına somut örnektir. Hangi stratejinin hangi thread yolunu kullandığı [strateji çekirdeği belgesinde](../../bilgi-tabani/10-servisler/hftsrvprod/strateji-cekirdegi.md) anlatılır; bütün stratejilerin tek thread'de olduğu varsayılmaz.

Bir test kaydına olayların sırasını, strateji kimliğini, start/stop anını ve yük koşulunu eklemek işe yarar. Eşzamanlılıkla ilgili davranışın düşük yükte görülmeyip yoğunlukta ortaya çıkabilmesi, yalnız test süresini uzatmanın neden her zaman yeterli olmadığını gösterir.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Toplu yazım talebi kapsamında. Restoran, sayaç, kuyruk ve kilit örnekleri eğitim içindir; mevcut hata veya canlı test sonucu değildir.

## Kaynaklar ve doğrulama

C++ çalışma taslağı intro.races, mutex ve atomics.order, erişim 25 Ekim 2026. HftSrvProd development `4275ccc`, `src/Workers/AlgoWorker.cpp`: `start`, `enqueueHotReady`, `drainHotReady` salt okunur incelendi. Her thread yolu veya kilit kanıtlanmış sayılmaz. Thread sanitizer, yük veya canlı test yapılmadı. Bu konu genel kavramları anlatır; açık sorun kuyruğu yeniden başlatılmadı.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [gecikme ve performans](08-gecikme-ve-colocation.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
