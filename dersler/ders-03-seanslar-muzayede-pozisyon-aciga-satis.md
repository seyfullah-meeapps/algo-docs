---
kapsam: Sürekli işlem ve toplama ayrımı, denge fiyatı, pozisyon ve kâr metriğini doğru yorumlama
dogrulama: 2026-10-24
durum: taslak
---

# Ders 03 — Seanslar, müzayede ve pozisyon

Ön koşul: emir ve fill ayrımı. Amaç: aynı fiyatların farklı seansta neden farklı davranabildiğini ve işlem sonrası neyin değiştiğini açıklamak.

## Sürekli işlem ve toplama

Sürekli işlemde uygun emirler geldikçe eşleşebilir. Emir toplama aşamasında emirler birikir; eşleştirme aşamasında tek fiyat belirlenir. Bu nedenle toplamada alış ve satış fiyatlarının çakışması tek başına veri hatası değildir. Günün saati yardımcı bilgidir; enstrümanın seans/state verisi ayrıca izlenir. Güncel saat ve iptal kurallarını eski ders tablosundan çıkarmayız.

ITCH OrderBookState (`O`) enstrümanın durumunu; EquilibriumPriceUpdate (`Z`) denge fiyatı ve ilgili miktarları taşır. Denge fiyatı emir toplama sırasında değişebilir. Ekrandaki son denge fiyatı, ileride kesin gerçekleşecek fiyat değildir.

## Denge fiyatı örneği

Alışlar: 1.000 lot 10,10; 1.000 lot 10,00; 500 lot 9,90 TL. Satışlar: 800 lot 9,90; 700 lot 10,00; 600 lot 10,10 TL.

| Aday fiyat | Bu fiyatı karşılayan alış | Bu fiyatı karşılayan satış | Eşleşebilir miktar |
|---|---|---|---|
| 9,90 | 2.500 | 800 | 800 |
| 10,00 | 2.000 | 1.500 | 1.500 |
| 10,10 | 1.000 | 2.100 | 1.000 |

Bu basitleştirilmiş örnekte en fazla miktar 10,00 TL'de eşleşir. 10,10 limitli alışın eşleşen kısmı da 10,00'dan gerçekleşir. Birden çok adayın aynı miktarı vermesi gibi ek fiyat belirleme kuralları bu örneğin dışındadır. Yüksek alış limiti vermek ücretsiz öncelik değildir: denge fiyatı yükselirse kabul edilen fiyat riski de yükselir.

Teorik Fiyat stratejisi denge/state olaylarını kullanır. Sabah ters emir, akşam iptal gibi mevcut davranışın ayrıntıları [strateji belgesindedir](../20-stratejiler/teorik-fiyat.md). Ters emir iki tarafın aynı miktarda kesin dolacağını veya pozisyonun kesin sıfırlanacağını garanti etmez. Eski dersteki “sabah iptal yasak, ters emir kesin nötrler” anlatımı genel borsa kuralı olarak kullanılmaz.

## Pozisyon ile para aynı şey değil

Sıfırdan 1.000 lot alıp 400 lot satarsan net pozisyon +600 lot olur. Satış isteği göndermek pozisyonu değiştirmez; gerçekleşme değiştirir. Bekleyen emirler ise ileride oluşabilecek maruziyeti değiştirir.

Eğitim hesabı: 100 lot 10,00 TL'den alınıp 10,02 TL'den satılırsa ücretler hariç fark 2 TL'dir. Elindeki pozisyonun piyasa fiyatıyla değerlenmesi başka bir metriktir. Komisyon, maliyet yöntemi, başlangıç pozisyonu ve ölçek bilinmeden UI kârı bu hesapla karşılaştırılmaz.

Kodda `balance`, `profit`, `net` gibi adların olması bunların her stratejide aynı muhasebe anlamına geldiğini göstermez. [Strateji çekirdeği](../10-servisler/hftsrvprod/strateji-cekirdegi.md) ve ilgili stratejinin raporlama hesabı okunur. Hesabın nakit bakiyesi, satılabilir hisse bakiyesi ve strateji pozisyonu da ayrı değerlerdir.

Açığa satış, sahip olunmayan ürünü satış işlemiyle açılan pozisyonun temel kavramıdır. Normal satış işaretine geçmek, sahiplik ve izin koşullarını kendiliğinden sağlamaz. Güncel izin/uptick/takas uygulaması bu dersin ezber tablosu değildir; [ek derste](ders-03b-uptick-bait-brut-takas.md) kod ve kural ayrımını ele alıyoruz.

## Alıştırma

1. Toplamada bid > ask gördün. Sürekli işlem hatası diye issue açar mısın? **Önce seansı doğrularım.**
2. +300 lot pozisyon ve 200 lot bekleyen alış var. Kesin pozisyon kaç? **+300; kalan dolarsa +500 olabilir.**
3. Ters yönde 300 lot emir göndermek pozisyonu sıfırladı mı? **Dolumları görmeden söyleyemeyiz.**

Kaynaklar: [borsa kuralları](../00-genel/borsa-kurallari.md), [ITCH mesajları](../10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md), [risk katmanı](../10-servisler/order-service/README.md).

## Oturum kaydı

Eski kayıt revize edildi; yeni açıklamaların birlikte tekrarı henüz yapılmadı.
