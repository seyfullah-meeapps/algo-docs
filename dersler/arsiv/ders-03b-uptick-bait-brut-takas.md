---
kapsam: Borsa kuralı ile config ve uygulama kontrolünü uptick, bait ve brüt takas üzerinden ayırmak
dogrulama: 2026-10-24
durum: taslak
---

# Ders 03b — Uptick, bait ve brüt takas

Eski ek ders tarihli haberlerden güncel kural sonucu çıkarıyor, bazı kod davranışlarını da soru olarak bırakıyordu. Burada güncel mevzuat ilan etmiyoruz. Belirli bir günün açığa satış kapsamı, fiyat doğrulaması veya takas süresi gerektiğinde resmi duyuru ve ilgili piyasa/ürün doğrulanmalı. [Borsa kuralları](../../00-genel/borsa-kurallari.md) tarihli kaynakları tutar.

## Üç ayrı soru

1. Borsa hangi işleme izin veriyor?
2. Bizim config ve kullanıcı/hesap izinlerimiz ne diyor?
3. Kod hangi kontrolü gerçekten uyguluyor, hangi yolda uygulamıyor?

Bu soruların cevapları otomatik olarak aynı değildir. Enstrümanda bir bilginin bulunması, motorun onu kullandığını kanıtlamaz. UI seçeneğinin kapalı olması da gönderilen alanın kapalı olduğu garantisi değildir.

## Uptick ve Classic

Uptick, açığa satışın fiyat koşullarıyla ilgili kavramdır. Tam koşulu ve yürürlük kapsamını burada sabitlemiyoruz. Mevcut Classic belgesine göre `hasUptickRule` hisseye özel durum sorgulamak yerine config'teki ortak bayrağı döndürür; otomatik gün içi kural takibi varsayılamaz.

Eski “önce 1 lot alış yaparak uptick oluşturur” anlatımı yanlıştı. Belgelenen Classic chase akışında uptick açıkken önce 1 lot **bait satış**, ardından chase açığa satış gönderimi vardır. Bu bir kod akışı açıklamasıdır; kural uyumluluğu veya iki emrin gerçekleşmesi garantisi değildir. Tam koşullar [HFT Classic / bait + chase](../../20-stratejiler/hft-classic.md) bölümündedir. Buradan canlı kullanım önerisi çıkarılmaz.

PM çalışması: config, strateji parametreleri, üretilen emir yönü/fiyatı ve ret kaynağı ayrı kanıtlanır. “Kural açık” cümlesi tek başına test ön koşulu değildir; hangi katmandaki hangi bayrak olduğu yazılır.

## Brüt takas

Netleştirme, alış ve satış yükümlülüklerinin farkı üzerinden hesaplanmasını anlatır; brüt takasta yükümlülükler ayrı ele alınır. Bunun belirli hesabın satılabilir miktarına ve kullanılabilir nakdine etkisi, takas/tedbir ve sistemin hesap modeliyle birlikte incelenir. “Her gün içi satış yasak” veya “bütün brüt takas emirleri sistemde koşulsuz reddedilir” diye genellemeyiz.

Projede enstrüman kısıtı, order-service risk kontrolü ve SDK/motor korumaları vardır. Etkileri emir yoluna, parametreye, config'e ve sürüme bağlıdır. SDK/service tarafındaki `skip_brut_takas` gibi istisnalar nedeniyle eski “dört katmanda da her zaman engel” tablosu kullanılmaz. Kaynaklar: [order-service](../../10-servisler/order-service/README.md), [MAOrderSDK](../../10-servisler/maordersdk/README.md), [config referansı](../../40-operasyon/config-referansi.md).

## Test tasarımı alıştırması

| Soru | Toplanacak kanıt |
|---|---|
| Aynı ürün bir yolda reddedilip diğerinde geçiyor | HFT doğrudan/gateway/AlgoProd yolu, config ve sürüm |
| UI'da tedbir rozeti var ama emir gönderiliyor | Rozetin veri kaynağı; gerçek gönderim; yerel/borsa ret ayrımı |
| Açığa satış yerine normal satış gönderilmiş | Motor payload'ı ve ilgili mod/bayrak; hesap sahipliği ayrı kontrol |

Kendini kontrol et: “Kodda kontrol var” neden yeterli değil? Yanıt: Çalışan branch, çağrılan yol, config, veri hazırlığı ve kontrolün gerçekten o olayda çalışması da bilinmelidir.

## Oturum kaydı

Eski açık sorular otomatik araştırma kuyruğuna çevrilmedi. Yeni kod/canlı kural doğrulaması yapılmadı; bu revizyon birlikte konuşulmayı bekliyor.
