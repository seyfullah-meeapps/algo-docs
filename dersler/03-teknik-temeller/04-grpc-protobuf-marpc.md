---
kapsam: RPC, şema, kod üretimi, unary/stream; gRPC-Protobuf ile MARpc-FlatBuffers ayrımı
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
dis_kaynak:
  - url: https://grpc.io/docs/what-is-grpc/core-concepts/
    erisim: 2026-10-25
  - url: https://grpc.io/docs/guides/deadlines/
    erisim: 2026-10-25
  - url: https://protobuf.dev/overview/
    erisim: 2026-10-25
  - url: https://protobuf.dev/programming-guides/proto3/
    erisim: 2026-10-25
  - url: https://flatbuffers.dev/
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# gRPC, Protobuf ve MARpc

Bir servisin başka servisten bilgi istemesi, başka masadaki görevliye “42 numaralı stratejinin ayarlarını getir” demeye benzer. Ancak makinelerin isteği aynı anlaması için hem **nasıl konuşacaklarını** hem **mesajın alanlarını** belirlememiz gerekir.

## RPC: uzaktaki işi çağırmak

**RPC (Remote Procedure Call)**, başka süreçteki bir işi bir fonksiyon çağrısına benzer arayüzle istemektir. Kodda basit görünen çağrının arkasında bağlantı, veri dönüşümü, bekleme ve hata olabilir. Aynı süreçteki fonksiyon çağrısı gibi her zaman anında sonuç dönmez.

**gRPC**, bu iletişim için kullanılan bir çerçevedir. İstemci ve sunucu tarafındaki üretilmiş kodlar, çağrının taşınmasını kolaylaştırır. Yaygın kullanımda servis ve mesajlar `.proto` dosyalarında tanımlanır; **Protobuf**, bu mesajların alanlarını ve ikili kodlamasını sağlar. gRPC ile Protobuf aynı görev değildir. [gRPC temel kavramları](https://grpc.io/docs/what-is-grpc/core-concepts/) · [Protobuf genel bakış](https://protobuf.dev/overview/)

## Şema: iki tarafın aynı formu doldurması

Bir kargo formunda “adres” alanının bir tarafta teslimat, diğer tarafta fatura adresi sanıldığını düşünelim. Veriyi eksiksiz taşısak bile yanlış iş yapılır. **Şema (schema)** bu ortak formdur; alanın adı, numarası ve veri tipi gibi bilgileri tanımlar.

Aşağıdaki küçük sözleşme yalnız eğitim örneğidir; gerçek MTrader mesajı değildir:

```proto
message OrnekAyar {
  int64 strateji_id = 1;
  int32 hedef_lot = 2;
}
```

Buradaki `1` ve `2`, örnek değerler değil **alan numaralarıdır**. `hedef_lot` için 100 göndermek ayrı şeydir. `.proto` değişince kod üretici araç ilgili dillerin okuma/yazma sınıflarını üretir; el ile değiştirilmiş generated dosya kalıcı sözleşmenin yerine geçmez.

Şema tür bilgisi verse de alanın iş anlamı ayrıca açıklanmalıdır. `int32 fiyat` yazmak, bunun TL mi ham ölçek mi olduğunu tek başına söylemez. Eski ve yeni tarafın uyumu da önemlidir: mevcut alan numarasını başka anlam için kullanmak veri yorumunu bozabilir. [Protobuf dil kılavuzu](https://protobuf.dev/programming-guides/proto3/)

## Tek cevap ile olay akışı

**Unary**, bir istek ve bir yanıttır: “ayarları getir” → “ayarlar bunlar”. **Stream**, bir çağrı boyunca birden çok mesajın aktığı iletişimdir. Sunucu akışında tek isteğe karşı birçok güncelleme; istemci akışında birçok isteğe tek yanıt; çift yönlü akışta her iki yönde mesajlar olabilir.

Restoran benzetmesiyle unary bir sipariş fişinin sonucunu sormak; stream ise mutfaktaki durum değişikliklerini açık hat üzerinden dinlemektir. Hangi yöntem olduğu servis sözleşmesinden okunur. “gRPC kullanılıyor” bilgisi tek başına her çağrının stream olduğunu göstermez.

**Deadline**, çağıranın ne zamana kadar bekleyeceğini sınırlar. Sürenin dolması, uzaktaki işin kesin hiç yapılmadığını kanıtlamaz. Özellikle emir veya başlatma gibi durum değiştiren işler için sonucun ayrıca uzlaştırılması gerekebilir. [gRPC deadline açıklaması](https://grpc.io/docs/guides/deadlines/)

## MARpc ve FlatBuffers nerede duruyor?

MTrader belgelerinde **MARpc**, `network-sdk` tarafından sunulan servisler arası iletişim kütüphanesinin adıdır. Bunu gRPC'nin başka adı olarak okumayacağız. Mevcut KB, bu hattı `ouch-sdk` ile `order-service` arasında, uzunluk önekli TCP/Unix socket ve FlatBuffers mesajları olarak belgeliyor. Ayrıntıların tek adresi [network-sdk](../../10-servisler/network-sdk/README.md).

**FlatBuffers**, şemaya göre ikili veri oluşturma ve okuma biçimidir. Alınan tampon üzerinden alanlara erişebilen yapısı vardır; tamponun ömrü bu yüzden önemlidir. Kendiliğinden bağlantı açmaz, yetki vermez veya bir emrin borsaca kabulünü sağlamaz. [FlatBuffers resmi açıklaması](https://flatbuffers.dev/)

| Soru | İlgili kavram |
|---|---|
| Başka süreçte hangi işi çağırıyoruz? | RPC ve servis metodu |
| Alanlar hangi tip ve numarayla tanımlı? | Protobuf / FlatBuffers şeması |
| Veri nasıl gidiyor? | İletişim çerçevesi ve taşıma |
| Karşı taraf işi yaptı mı? | Uygulama sonucu ve sonraki olaylar |

## MTrader'da okuyacağımız ayrım

Referans hub `.proto` dosyasında `GuiService` ve metodları tanımlıdır; HTTP eşlemeleri de bu sözleşmede yer alır. Bu, önceki konudaki GUI isteği ile servis sözleşmesinin bağını görmemizi sağlar. Hub'ın bütün rolü [API belgesinde](../../10-servisler/trade-data-app/api.md), MARpc'nin alanları ise [wire protokolünde](../../10-servisler/network-sdk/wire-protokolu.md) kalır.

Bir PM kaydında “RPC hata verdi” yerine hangi tarafın çağırdığı, metot, zaman, taşıma durumu, dönen uygulama sonucu ve ilgili kimlik yazıldığında sorun daha somut hale gelir. HTTP başarısı, gRPC durumu ve borsa emri kabulü farklı katmanlardır.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Kullanıcının toplu teknik bölüm talebi kapsamında yazıldı. `.proto`, kargo formu ve restoran örnekleri öğreticidir. MARpc'ye standart gRPC garantileri atfedilmedi.

## Kaynaklar ve doğrulama

gRPC core concepts/deadlines, Protobuf overview/proto3 ve FlatBuffers resmi belgeleri 25 Ekim 2026'da okundu. trade-data-app development `1cca9a8`, `api/protobuf-spec/gui-data.proto` içindeki servis/metot ve HTTP eşlemeleri salt okunur incelendi. MARpc özeti mevcut KB'nin network-sdk `3c1b42f` incelemesinden aktarılmıştır; SDK kodu bu tur yeniden okunmadı. Uyumluluk veya canlı RPC testi yapılmadı.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [binary, ölçek ve zaman](05-binary-fiyat-ve-zaman.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
