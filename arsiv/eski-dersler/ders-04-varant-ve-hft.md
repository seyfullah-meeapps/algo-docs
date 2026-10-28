---
kapsam: Varant/dayanak ilişkisi, HFT fırsat ve riskleri, projedeki stratejileri birbirinden ayırma
dogrulama: 2026-10-24
durum: taslak
---

# Ders 04 — Varant, dayanak ve HFT

Bu ders temel kavramları korur. Ayrıntılı Varant dersi öncelikli beş konudan sonra gelecek. Amaç bütün stratejileri tek bir “kademe eriyor, alıyoruz” kuralına indirgememek.

## Dayanak ve varant

Türev ürünün değeri bir dayanakla ilişkilidir: pay, endeks veya başka bir varlık. Varant belirli koşullarda bir hak verir; fiziksel teslim şekli ürün koşullarından bağımsız varsayılamaz. Call ve put'un dayanak fiyatına duyarlılığı farklıdır. Vade, kullanım fiyatı, dönüşüm oranı, oynaklık ve diğer fiyatlama girdileri önemlidir.

Basit duyarlılık örneği: delta 0,6 ve dönüşüm oranı 0,1 varsayımıyla dayanak 2 TL yükselirse yaklaşık değişim `2 × 0,6 × 0,1 = 0,12 TL` olur. Bu küçük hareket için basitleştirilmiş model hesabıdır; kesin kotasyon veya getiri değildir. Delta ve diğer koşullar değişebilir.

Piyasa yapıcı kotasyonlarını güncellerken gecikme oluşabilir. Dayanak verisini izleyen stratejinin fırsat fikri bu ilişkidir. Eski fiyattan mutlaka alım veya bir tick yukarıdan mutlaka satış garantisi yoktur.

## HFT tek strateji değildir

HFT düşük gecikmeyle karar ve emir üretme yaklaşımını anlatır. Projedeki **HFT Classic** ise belirli bir stratejinin adıdır. HFT motorunda çalışan her strateji Classic gibi davranmaz. Her HFT işleminin bir tick kazandığı veya gün sonunda kendiliğinden flat kaldığı söylenemez.

| Konu | Temel olarak neyi inceleriz? | Özellikle hangi riski test ederiz? |
|---|---|---|
| HFT Classic | Header erimesi, miktar, mod ve çıkış | Tetik olup fiyatın ilerlememesi; açık çıkış emri |
| Arbitraj | Spot–vadeli fiyat ilişkisi ve bacaklar | Bir bacak dolarken hedge'in dolmaması |
| Toplu Emirler | Kuyruğa kayıt, zamanlama, tekrar | Kaydedilen emrin doğru zamanda doğru sayıda gönderimi |
| Tavan / Taban | Fiyat sınırındaki defter durumu ve geçişler | Kilidin bozulması; kısmi dolum ve açık pozisyon |
| Teorik Fiyat | Toplama, denge ve state olayları | İptal/ters emir sırasında dolum ve zamanlama |
| Varant / Varant Toplu | Dayanak ve varant olayları; ayrı uygulamalar | Girişten sonra çıkış kotasyonunun kaybolması |
| VWAP / BYF | Hacimle yürütme / fon-sepet ilişkisi | Eksik yürütme veya parça uyumsuzluğu |

Aktiflik ve motor eşleşmesi için [strateji kataloğu](../../bilgi-tabani/20-stratejiler/README.md) esastır. OrderChase eski dersteki gibi aktif strateji olarak sayılmaz. Varant ile Varant Toplu'nun davranışı birbirine kopyalanmaz; Toplu Emirler de bu ikisinden farklıdır.

## Hız neyi değiştirir?

Sınırlı likiditede önce ulaşan emir daha çok miktar alabilir. Sonraki emir az miktarda dolabilir veya hiç dolmayabilir. “İkinci gelen hiçbir zaman kazanmaz” yerine fiyat, miktar ve zamanın birlikte etkisini düşünürüz. Girişte hız kazanıp çıkışta likidite bulamamak mümkündür.

CPU pinning, kernel bypass, allocation ve kilit maliyeti bu nedenle önemlidir. Bunlar bütün müşterilerde açık veya bütün kodda kusursuz uygulanmış sayılmaz. Config ve ölçüm gerekir. UI bildirim gecikmesi de operatörün kararını ve müdahalesini etkileyebilir; önemsiz bir yol değildir.

## Alıştırma

- Varantı aldık, satış emri kabul edildi. Kâr kesinleşti mi? **Hayır; satışın dolumu ve maliyeti gerekir.**
- Arbitrajda ilk bacak doldu. İşlem bitti mi? **Hedge ve paket durumunu kontrol ederiz.**
- HFT hızlı diye stop emri kesin dolar mı? **Hayır; fiyat, likidite ve emir koşulları belirler.**

Kaynaklar: [Varant](../../bilgi-tabani/20-stratejiler/varant.md), [Varant Toplu](../../bilgi-tabani/20-stratejiler/varant-toplu.md), [Arbitraj](../../bilgi-tabani/20-stratejiler/arbitraj.md), [hot path](../../bilgi-tabani/30-akislar/hot-path.md).

## Oturum kaydı

Eski dersin temel ürün ve hız örnekleri revize edildi. Yeni soru/yanıt veya uygulanmış test yok.
