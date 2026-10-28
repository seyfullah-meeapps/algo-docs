---
kapsam: Byte ve endianness; raw/TL, fixed-point, taşma; zaman birimi ve saat kaynağı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dis_kaynak:
  - url: https://eel.is/c++draft/basic.fundamental
    erisim: 2026-10-25
  - url: https://eel.is/c++draft/time.clock.steady
    erisim: 2026-10-25
  - url: https://www.rfc-editor.org/rfc/rfc3339.html
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Binary veri, fiyat ölçeği ve zaman

Bir ekranda 10,01 TL görüyoruz, log'da ise `1001` yazıyor. İkisi farklı fiyat mı? Her zaman değil: biri insanın okuduğu değer, diğeri belirli ölçekle saklanmış tam sayı olabilir. Önce birimin ve veri biçiminin ne olduğunu bulmalıyız.

## Byte ve binary ne demek?

**Bit**, 0 veya 1 değeridir. Buradaki ağ örneklerinde **byte (bayt)** sekiz bittir; bir byte 0–255 arası işaretsiz sayı taşıyabilir. **Binary veri**, mesajın insanın okuyacağı metin yerine belirlenmiş bayt düzeniyle yazılmasıdır. Anlamı, protokoldeki alan düzeninden gelir.

Örneğin `1001` yazısını metin olarak göndermek dört rakam karakteri taşır. Sayıyı 32 bit tam sayı alanında göndermek ise dört byte içinde sayısal temsilini taşır. Aynı uzunlukta olmaları aynı içerik oldukları anlamına gelmez. Mesajın fiyat alanının nerede başladığını ve kaç byte olduğunu parser, yani ayrıştırıcı bilmelidir.

**Endianness**, birden fazla byte kullanan sayının byte sırasıdır. 258 sayısının 16 bit gösterimini düşünelim: hexadecimal yazımda `0x0102`. Big-endian sırası `01 02`, little-endian sırası `02 01` olur. Yanlış sırayla okumak başka sayı üretir. Bir mesajın başlığıyla içeriğinin aynı sırayı kullandığını da varsaymayız; sözleşmeye bakarız.

## Fiyatı neden tam sayıyla tutarız?

**Fixed-point**, ondalık basamak sayısını önceden belirleyip değeri tam sayıyla temsil etmektir. Ondalık virgül bellekte taşınmaz; ölçekten geri hesaplanır. Ölçeğin iki ondalık basamak olduğu öğretici örnekte:

| İnsan için fiyat | Çarpan | Ham sayı (raw) |
|---|---:|---:|
| 10,00 TL | 100 | 1.000 |
| 10,01 TL | 100 | 1.001 |
| 10,02 TL | 100 | 1.002 |

Hesap **TL = raw / 10^ondalık_basamak** biçimindedir. `raw = 1001`, basamak 2 ise 10,01 TL; basamak 3 ise 1,001 TL demektir. “Fiyat alanı 1001” bilgisi ölçek olmadan eksiktir.

MTrader HFT referansında enstrüman başına çarpan, `OuchManager` içinde `10^decimal_count` olarak hazırlanır. Bütün ürünlerde sabit 100 kullanma varsayımı doğru olmaz. Fiyat/miktar sözleşmesinin aslı [emir yaşam döngüsü](../../bilgi-tabani/10-servisler/hftsrvprod/emir-yasam-dongusu.md), veri tarafının ayrıntısı [ITCH mesajları](../../bilgi-tabani/10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md) içindedir.

**Fiyat ölçeği ile fiyat adımı ayrıdır.** İki ondalık basamak, sayıyı nasıl sakladığımızı anlatır; geçerli emir fiyatlarının birer kuruş arayla olmak zorunda olduğunu söylemez. Geçerli kademe aralığı ayrıca ürünün ve fiyat seviyesinin kuralıdır.

## Kuruş kayması ve taşma nasıl görünür?

Öğretici hesap: iki basamak ölçeğinde 10,01 TL'den 100 payın ham fiyat × miktar çarpımı `1001 × 100 = 100100` olur. Bu sayı **TL değildir**. Ölçeğe bölündüğünde 1.001 TL tutardır. Pay/sözleşme çarpanı gereken ürünlerde o dönüşüm de ayrıca hesaba katılır.

**Overflow (taşma)**, sonucun kullanılan sayı tipine sığmamasıdır. 32 bit işaretli tam sayı en fazla 2.147.483.647 tutar. Örneğin `1.000.000 × 3.000`, 3.000.000.000 eder ve bu tipe sığmaz. Sonucu daha geniş değişkene koymak yeterli olmayabilir; işlemin kendisinin de yeterli genişlikte yapılması gerekir. C++'ta işaretli taşmanın davranışı tanımsızdır; işaretsiz aritmetik ise modüler olarak sarar. [C++ tam sayı türleri](https://eel.is/c++draft/basic.fundamental)

Bu örnek MTrader'da bulunmuş bir hata değildir; birim ve tip kontrolünün neden birlikte yapıldığını gösterir.

## Zaman: sayı kadar birim ve başlangıç da önemli

| Birim | Bir saniyedeki karşılığı | Örnek |
|---|---:|---|
| ms, milisaniye | 1.000 | 5 ms = 0,005 s |
| µs, mikrosaniye | 1.000.000 | 5 µs = 0,000005 s |
| ns, nanosaniye | 1.000.000.000 | 5.000 ns = 5 µs |

`5000` yazan süre, ns ise 5 µs; ms ise 5 saniyedir. Üstelik **timestamp**, bir olaya ait zaman noktası; **duration**, iki nokta arasındaki süredir. Her timestamp Unix epoch'tan, gün başından veya aynı saat kaynağından gelmez.

**Wall clock**, tarih ve saatle ilişkilendirdiğimiz saat; **monotonic/steady clock**, geçen süreyi ölçmek için geriye gitmeyen saat yaklaşımıdır. Aynı steady saat kaynağından alınan başlangıç ve bitiş farkı süre hesabına uygundur; iki ayrı makinenin böyle sayaçlarını doğrudan birbirinden çıkaramayız. [C++ steady_clock](https://eel.is/c++draft/time.clock.steady)

Varsayımsal bir log'daki `2026-10-25T07:00:00Z` ile `2026-10-25T10:00:00+03:00` aynı anı gösterir. Yalnız “10:00” yazarsak tarih ve saat dilimi kaybolur. [RFC 3339 zaman gösterimi](https://www.rfc-editor.org/rfc/rfc3339.html)

## Bir sayıyı karşılaştırmadan önce

Fiyat için ürün, raw/TL ayrımı ve ölçek; miktar için pay/lot/sözleşme ve çarpan; zaman için birim, başlangıç ve saat kaynağı belirlenir. Özellikle iki farklı log'un zamanını karşılaştırırken saat eşitleme doğruluğu da bilinmelidir. Ekrandaki yuvarlanmış gösterim ile içerideki değerin aynı ayrıntıyı taşıması beklenmez.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Toplu bölüm talebi kapsamında. Bütün sayısal örnekler belirtilen ölçek ve birim varsayımlarıyla öğreticidir; gerçek müşteri/emir kaydı kullanılmadı.

## Kaynaklar ve doğrulama

C++ çalışma taslağı basic.fundamental/time.clock.steady ve RFC 3339 (2002), erişim 25 Ekim 2026. HftSrvProd development `4275ccc`, `src/Clients/OuchManager.cpp` içinde `getInstrumentDecimalPrice` ve `obidToDecimalPrice` yüklemesi salt okunur incelendi; enstrüman çarpanı `std::pow(10, instrument.getDecimalCount())`. Genel raw/TL sözleşmesi mevcut KB'den bağlandı. Wire codec, diğer SDK ölçekleri, canlı emir veya saat senkronizasyonu bu tur test edilmedi.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [C++ bellek ve yaşam süresi](06-cpp-bellek-ve-yasam-suresi.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
