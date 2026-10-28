---
kapsam: Stack/heap, pointer/reference, sahiplik, RAII, smart pointer ve iterator
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dis_kaynak:
  - url: https://eel.is/c++draft/basic.life
    erisim: 2026-10-25
  - url: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
    erisim: 2026-10-25
  - url: https://eel.is/c++draft/unique.ptr
    erisim: 2026-10-25
  - url: https://eel.is/c++draft/util.smartptr.shared
    erisim: 2026-10-25
  - url: https://eel.is/c++draft/vector.modifiers
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# C++ bellek ve nesne yaşam süresi

Bir arkadaşının ev adresini bilmek, evin sahibi olmak değildir. Ev yıkılıp yerine başka bina yapıldığında eski adres notunu elinde tutman da eski eve girebileceğin anlamına gelmez. C++'ta bir nesnenin adresiyle o nesnenin sahipliği ve yaşam süresi arasındaki farkı böyle düşünebiliriz.

## Stack ve heap: verinin yaşadığı yer

**Bellek (RAM)**, program çalışırken nesnelerin ve verilerin bulunduğu alandır. **Stack**, fonksiyon çağrılarının ve çoğu yerel değişkenin yaşamıyla ilişkili alan; **heap**, dinamik olarak ayrılan bellek için kullanılan yaygın addır. Dilin daha kesin kavramları otomatik ve dinamik saklama süresidir.

Bir fonksiyondaki yerel `int kalan = 100;` değişkeninin ömrü, bulunduğu kapsamdan çıkılınca biter. Dinamik oluşturulan nesne ise onu oluşturan fonksiyondan daha uzun yaşayabilir; ne zaman yok edileceğini sahiplik düzeni belirler. “Heap'te” demek sonsuza kadar geçerli demek değildir. [C++ nesne yaşam süresi](https://eel.is/c++draft/basic.life)

## Pointer ve reference

**Pointer**, bir nesnenin adresini tutabilen değerdir; boş (`nullptr`) olabilir. **Reference**, mevcut nesneye başka bir ad gibi erişmektir. İkisi de tek başına nesnenin yaşamını garanti etmez. Bir nesneye erişebilmek ile onu yok etmekten sorumlu olmak ayrıdır.

Aşağıdaki kısa örnek hatayı göstermek içindir; kullanılacak uygulama kodu değildir:

```cpp
const int* hataliAdres() {
    int kalan = 100;
    return &kalan;
}
```

Fonksiyon bittiğinde `kalan` artık yaşamaz. Dönen adreste bir süre 100 görünüyor olması adresi kullanmayı geçerli hale getirmez. Buna **dangling pointer**, yani ömrü bitmiş nesneyi gösteren pointer denir. Böyle bir erişim bazen çökme, bazen anlamsız veri, bazen de görünürde normal çalışma üretebilir.

JavaScript'teki garbage collector deneyimi burada yanıltabilir: C++'ta adresi bir yerde saklamak, o nesnenin ömrünü kendiliğinden uzatmaz. Bu yüzden “callback geldiğinde bu veri hâlâ var mı?” sorusu önemlidir.

## Sahiplik ve RAII

**Sahiplik (ownership)**, kaynağın ne zaman bırakılacağından kimin sorumlu olduğudur. Kaynak yalnız bellek olmayabilir; dosya, socket veya kilit de olabilir. **RAII**, kaynağın ömrünü bir C++ nesnesinin ömrüne bağlama yaklaşımıdır. Kapsam bittiğinde nesnenin destructor'ı, yani yıkıcısı, kaynağı bırakır. Erken dönüşlerde de bu düzen iş görür. [C++ Core Guidelines — kaynak yönetimi](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)

{{< pagebreak >}}

| Araç | Sahiplik fikri | Günlük benzetme |
|---|---|---|
| `unique_ptr` | Tek sahip; sahiplik taşınabilir | Anahtarı bir görevliye devretmek |
| `shared_ptr` | Paylaşılan sahiplik | Son sorumlu ayrılınca kapatılan oda |
| `weak_ptr` | Sahipliği artırmadan gözlemek | Oda hâlâ açık mı diye kontrol etmek |
| Ham pointer/reference | Erişim; sahiplik sözleşmesi ayrıca gerekir | Adres notu veya başka bir ad |

`unique_ptr` kopyalanmaz; **move**, sahipliği başka yere devretmeyi sağlar. `shared_ptr` ise nesneyi son sahip bırakana kadar yaşatır. Karşılıklı güçlü sahiplik döngüsü kaynağın bırakılamamasına yol açabilir; `weak_ptr` uygun tasarımda bu döngüyü kırmaya yardımcı olur. [unique_ptr](https://eel.is/c++draft/unique.ptr) · [shared_ptr](https://eel.is/c++draft/util.smartptr.shared)

## Kuyruğa pointer koyunca veriyi kopyalamış olmayız

Öğretici senaryo: SDK bir mesaj tamponundaki metnin adresini callback'e verdi. Callback adresi kuyruğa koydu, işçi thread daha sonra okuyacak. SDK o sırada tamponu serbest bıraktıysa kuyruktaki adres artık güvenli değildir.

Çözüm sözleşmeye göre seçilir: gereken veriyi kendi nesnemize kopyalamak, tamponun sahipliğini devretmek veya ömrünü paylaşmak. Yalnız pointer değerini kopyalamak, metnin kendisini kopyalamaz. **Asenkron işe devredilen verinin, iş bitene kadar geçerli olması gerekir.**

MTrader'daki ilgili API ömür sözleşmeleri [ITCH abonelik API'si](../../bilgi-tabani/10-servisler/itch-sdk/abonelik-api.md) ve [MARpc wire belgesi](../../bilgi-tabani/10-servisler/network-sdk/wire-protokolu.md) içindedir. Her callback'in aynı sahiplik kuralına sahip olduğunu varsaymayacağız.

## Iterator neden geçersizleşebilir?

**Iterator**, bir koleksiyonun elemanları üzerinde gezinme aracıdır. Bir `vector` büyürken elemanları yeni bellek alanına taşımak zorunda kalabilir. Bu yeniden ayırma gerçekleşirse eski eleman pointer/reference/iterator'ları geçersizleşir. Silme gibi işlemlerin de kendi geçersizleştirme kuralları vardır. [C++ vector değişiklikleri](https://eel.is/c++draft/vector.modifiers)

Numaralı koltuklara yerleştirilmiş dosyaları başka dolaba taşıyınca eski raf konumlarıyla çalışmaya devam etmek gibi düşünelim. Nesneye erişim yolu, koleksiyonun her değişiminden sonra otomatik doğru kalmaz.

## MTrader kodunu okurken hangi soruları soracağız?

HFT referans `AlgoWorker` arayüzünde stratejiler için `shared_ptr`, kuyruklanan olay için `unique_ptr` kullanımı görülür. Bu isimler sahiplik düzenini okumamıza yardım eder; tek başına tüm programın güvenli olduğunu kanıtlamaz. Detaylı yaşam döngüsü [strateji çekirdeğinde](../../bilgi-tabani/10-servisler/hftsrvprod/strateji-cekirdegi.md) kalır.

PM açısından iyi gözlem; olayın start/stop veya restart sırasında mı olduğu, aynı nesne/strateji kimliğine mi ait olduğu ve tekrar üretim sırasıdır. “Bellek hatasıdır” sonucunu yalnız ekrandaki belirtiyle koymayız.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Toplu bölüm talebiyle yazıldı. Adres, oda ve geçersiz yerel değişken örnekleri eğitim içindir; mevcut MTrader hatası anlatılmaz.

## Kaynaklar ve doğrulama

C++ çalışma taslağı basic.life, unique.ptr, util.smartptr.shared, vector.modifiers ve Core Guidelines, erişim 25 Ekim 2026. Taslak standardın güncel web metni, C++20'ye özgü yeni özellik iddiası için kullanılmadı; ortak temel kavramlar anlatıldı. HftSrvProd development `4275ccc`, `src/Workers/AlgoWorker.cpp` içindeki `addStrategy`, `enqueueHotReady`, `start/stop` salt okunur incelendi. Bellek analizi, sanitizer veya canlı test yapılmadı. SDK callback bağlantıları mevcut KB'dir; bu tur yeniden kod doğrulaması değildir.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [thread, kuyruk ve kilit](07-thread-kuyruk-ve-kilit.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
