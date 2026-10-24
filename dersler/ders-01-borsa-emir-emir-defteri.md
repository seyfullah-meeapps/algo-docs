---
kapsam: Emir, fiyat seviyesi, spread, kuyruk ve piyasa verisinin temel okuması
dogrulama: 2026-10-24
durum: taslak
---

# Ders 01 — Borsa, emir ve emir defteri

Amaç, stratejinin baktığı veriyi okuyabilmek. Pay Piyasası ile vadeli ürünlerin bulunduğu VİOP'u ayırırız. Ürünün miktar birimi ve sözleşme özellikleri ayrıca bilinmelidir; her üründe “1 lot = 1 hisse” denmez. SDK miktarı lot olarak taşır; pay adedi hesabında enstrümanın lot bilgisi önemlidir.

## Emir ve defter

Bir emir; hesap, enstrüman, yön, fiyat, miktar ve süre/geçerlilik koşullarıyla anlam kazanır. Limit alışın fiyatı ödemeyi kabul ettiğin üst sınır, limit satışın fiyatı kabul ettiğin alt sınırdır. Emir uygun karşı taraf bulursa eşleşebilir; kalanın beklemesi TIF ve seansa bağlıdır. Piyasa emri de miktarın mutlaka gerçekleşeceği garantisi değildir.

Aşağıdaki tablo yalnız eğitim örneğidir; fiyat adımının bu örnekte 0,02 TL olduğunu varsayıyoruz.

| Alış miktarı | Alış fiyatı (TL) | Satış fiyatı (TL) | Satış miktarı |
|---|---|---|---|
| 5.000 | 45,18 | 45,20 | 3.000 |
| 12.000 | 45,16 | 45,22 | 8.000 |
| 20.000 | 45,14 | 45,24 | 15.000 |

En yüksek alış **bid**, en düşük satış **ask**; aradaki fark **spread**: 0,02 TL. Ekibin “header” dediği en iyi seviyedir. Bir satır, o fiyattaki birden fazla emrin toplamını gösterebilir. Defterde boş fiyat seviyeleri bulunabilir; yan yana görünen iki dolu satır mutlaka bir tick uzakta değildir.

Sürekli işlem örneğinde 45,20 TL limitli 1.000 lot alış, satıştaki 3.000 lotun 1.000'ini tüketirse orada 2.000 lot kalır. Daha yüksek limit vermek bütün miktarın tek fiyattan dolacağı anlamına gelmez: karşı seviyelerin fiyatı ve miktarı ayrı izlenir.

Fiyat-zaman önceliği olan örnekte aynı fiyatın kuyruğu `A:1000 → B:500 → C:1500` ise gerçekleşmeler önce A'yı, sonra B'yi tüketir. Yeni emrin o fiyatın toplamını görmekten farklı olarak kuyruğun neresinde bulunduğunu bilmek önemlidir. Hız, gerçekleşme olasılığını etkiler; kâr garantisi vermez.

## Projedeki karşılığı

ITCH piyasa verisi taşır; OUCH kendi emrinin gönderim/cevap yoludur. ITCH'te AddOrder yeni emir ekler, OrderExecuted gerçekleşen miktarı düşürür, OrderDelete kalan emri kaldırır. Tek bir miktar azalması “fiyat kesin kırılacak” demek değildir; yeni emir eklenmesi sonucu değiştirebilir.

`itch-sdk` bu olaylarla bellekte emir defteri kurar. HFT kararları kendi veri yolundan, UI defteri ise hub'ın ITCH beslemesinden gelir. UI'ın görüntüsü tek başına motorun aynı anda gördüğü defterin kanıtı değildir.

Fiyatlar raw tam sayı taşınabilir: `TL = raw / 10^decimalPrice`. Örneğin yalnız `decimalPrice=3` varsayımıyla 45,20 TL = 45.200 raw olur. `decimalPrice=2` olsaydı 4.520 olurdu. Sayının yanında ölçek bulunmadan fiyat karşılaştırılmaz.

## Alıştırma ve PM uygulaması

1. Ask 10,52 TL'de 300 lot, sonraki ask 10,54 TL'de 500 lot. 10,54 limitli 600 lot alışın örnek dolumu nedir?
2. 3.000 lotun 1.000'i iptal oldu. Bu gerçekleşme midir?
3. UI “kademe eridi” diyor. Issue için hangi iki veriyi ayırırsın?

Yanıtlar: 1. Diğer koşullar uygunsa 300 lot 10,52 ve 300 lot 10,54; tek fiyattan 600 lot değil. 2. Hayır; pozisyon yaratmaz. 3. Motorun zamanlı piyasa olayı ve UI'ın gördüğü olay/görüntü.

Kaynaklar: [sözlük](../00-genel/sozluk.md), [ITCH mesajları ve ölçek](../10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md), [hot path](../30-akislar/hot-path.md).

## Oturum kaydı

Eski kayıt revize edildi; yeni sürümün birlikte tekrarı ve kullanıcının alıştırma yanıtları bekleniyor.
