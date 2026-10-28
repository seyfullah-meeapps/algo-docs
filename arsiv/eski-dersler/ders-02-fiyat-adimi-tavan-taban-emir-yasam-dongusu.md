---
kapsam: Fiyat adımı ve sınırlar, TIF, kabul/ret/fill/cancel/replace ayrımı
dogrulama: 2026-10-24
durum: taslak
---

# Ders 02 — Fiyat ve emir yaşam döngüsü

Ön koşul: Ders 01. Amaç: bir emrin fiyatını, kalan miktarını ve pozisyon etkisini ayrı izlemek.

## Fiyat adımı ve sınırlar

Tick, geçerli fiyatlar arasındaki adımdır. Fiyat bandına ve ürüne bağlı olabilir. “Üç kademe yukarı” hesabında fiyat bandı geçiliyorsa tek tick'i üçle çarpmak yanlış sonuç verebilir. Projede tick bilgisi ITCH'ten, ilgili fiyat ve enstrüman için okunur. Gerçek fiyat adımı tablosunun ayrı kopyasını burada tutmuyoruz.

Tavan ve taban, ilgili ürünün izin verilen üst/alt fiyat sınırlarıdır. Bu değerleri bütün ürünler için sabit bir yüzdeyle hesaplamak yerine sistemin kullandığı kaynağı kontrol ederiz. Güncel mevzuat veya belirli günün sınırı gerektiğinde resmi kaynak ayrıca doğrulanır. [Borsa kuralları](../../bilgi-tabani/00-genel/borsa-kurallari.md) tarihli teknik referanstır.

Tavanda alış kuyruğu ve satış tarafının boş olması bir defter durumudur; **Tavan stratejisinin bütün giriş koşulları** demek değildir. Parametreler, çalışma durumu ve diğer korumalar da değerlendirilir. Taban stratejisi de Tavan kodunun bütün ayrıntılarıyla aynası değildir.

## Emir süreleri: aynı fiyat, farklı kalan miktar

Eğitim örneği: limit fiyatında toplam 300 lot satış var, 1.000 lot alış gönderiyoruz; başka uygun satış yok.

| TIF | Olası sonuç |
|---|---|
| DAY | 300 lot dolar; kalan 700 lot uygun seans/geçerlilik koşullarında bekleyebilir |
| IOC / KIE | 300 lot dolar; kalan 700 lot iptal edilir |
| FOK | Tamamı karşılanamıyorsa kısmi dolum yapılmaz |

Bu tablo kavramları açıklar; her stratejinin veya her emir yolunun bütün TIF türlerini desteklediği anlamına gelmez.

## İstek ve cevap ayrı

`Gönderim isteği → kabul veya ret → sıfır/birden çok fill → kalan miktar için iptal/değişiklik` diye düşün. Kabul, gerçekleşme değildir. Kısmi fill pozisyon yaratır; kalan miktar ayrıca takip edilir. İptal isteğini göndermek, iptalin onaylandığı anlamına gelmez. İptal yoldayken gerçekleşme gelebilir. Gerçekleşmiş miktar iptal edilemez.

Replace fiyat/miktar değişikliği isteğidir. OUCH akışında istemci replacement token üretir; yanıt eski ve yeni kimliğin eşleştirilmesini gerektirir. “Borsa yeni token atıyor” veya “her replace kuyruğu kesin sıfırlar” diye genellemeyiz. İstenen değişiklik, gönderilen token ve ACK ayrı izlenir. Ret gelirse hangi önceki emrin hâlâ geçerli olduğu önemlidir.

Ret borsadan gelebileceği gibi yerel doğrulamadan da gelebilir. Yerel ret callback'i emrin BIST'e ulaştığını kanıtlamaz. UI'daki “reddedildi” etiketi için ret kaynağı/kodu ve gönderim kanıtı gerekir.

## Testte hesap

1.000 lot alışın iki fill'i 200 ve 100 lot olsun. Gerçekleşen toplam 300, kalan 700, başlangıç sıfırsa pozisyon +300 olur. Kalan 700 iptal edilince pozisyon +300 kalır. Pozisyonu kapatmak ayrıca satış gerçekleşmesi gerektirir.

## Alıştırma

- IOC emri 0 lot dolup kalanı iptal olduysa strateji tekrar girişe hazır mı? **Stratejinin state/mandal koduna bakmadan cevaplanamaz.**
- “İptal edildi ama elimde hisse var” tek başına bug mı? **Hayır; önceki fill'ler kontrol edilir.**
- Replace sonrası UI eski token'ı gösteriyor. İlk kanıt? **İstek, ACK ve UI olayındaki eski/yeni kimlikler.**

Kaynaklar: [HFT emir yaşam döngüsü](../../bilgi-tabani/10-servisler/hftsrvprod/emir-yasam-dongusu.md), [emir dönüşü](../../bilgi-tabani/30-akislar/emir-donusu.md), [MAOrderSDK](../../bilgi-tabani/10-servisler/maordersdk/README.md), [Tavan](../../bilgi-tabani/20-stratejiler/tavan.md), [Taban](../../bilgi-tabani/20-stratejiler/taban.md).

## Oturum kaydı

Eski kayıt revize edildi. Yeni örnekler henüz birlikte çözülmedi.
