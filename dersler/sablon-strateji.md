---
kapsam: GUI ve backend davranışını aynı strateji anlatımında birleştirmek için yazım şablonu
dogrulama: 2026-10-24
durum: taslak
---

# Strateji anlatım şablonu

Bu şablon içerik planıdır; bir stratejinin doğrulanmış davranışı değildir. Alanları uydurarak doldurma. Teknik sözleşmenin asıl adresi kök `20-stratejiler/` belgeleridir; burada insan için açıklama ve sayısal örnekler kaynakla bağlanır.

## Amaç ve kullanım

Ne yapıyor, hangi problemi çözüyor? Ürün, hesap, seans ve bağlantı ön koşulları ne? Hangi motor/route/wire türü? Referans branch/commit ve prod farkı?

## GUI üzerinden kullanım

Ekrana ulaşma, alan grupları, mod seçimi, başlat/durdur ve canlı durum. Gerçek ekran veya temsili SVG açık etiketlenir. Görsel yoksa gerekli ekran görüntüsünün tarifi bırakılır. Kullanıcı eylemi ile gönderilen komut eşleştirilir.

## Parametreler

| UI alanı | Wire/kod adı | Birim/tip | Varsayılan ve kapalı değer | Geçerli sınır/bağlı alan | Etki ve kaynak |
|---|---|---|---|---|---|
| İçerik yazılırken doldurulacak | — | TL/raw, lot, tick, ms/s | UI ve motor ayrı | 0/negatif/boş dahil | — |

## Backend akışı

Hazırlık, çalışır/bekler durumu, tetik koşulu ve eşitlik sınırı; yön/fiyat/miktar/TIF hesabı; gönderim mandalı; kabul/ret; sıfır/kısmi/tam fill; çıkış ve yeniden giriş. Küçük durum/sequence şeması ve kod sembolü eklenir.

## Sayısal örnekler ve ayar değişiklikleri

Örnek defter, başlangıç pozisyonu/açık emirler ve ayarlar yazılır. Her olaydan sonra hangi emir ve durum beklenir gösterilir. Aynı örnekte tek alan değiştirilir; hemen etki, sonraki tetikte etki, mevcut emir/pozisyon/timer ve restart ihtiyacı ayrı belirtilir. Örnekler kaynakla doğrulanır; mevcut hata anlatımı eklenmez. Düzeltme bekleyen ayrıntı teknik yazım takibinde tutulur; hedef davranış gerçekleşmiş gibi yazılmaz. Düzeltme doğrulanınca etkilenen örnek güncellenir.

## Test senaryoları

| Senaryo | Ön koşul ve olay | Beklenen | Kanıt ve gerçek sonuç |
|---|---|---|---|
| Temel akış | Doldurulacak | Yön/fiyat/lot/TIF ve durum | Çalıştırılmadı |
| Sınır | Eşiğin altı/eşiti/üstü | Ayrı beklenti | Çalıştırılmadı |
| Dolum/ret | Sıfır/kısmi/tam ve yerel/borsa ret | Emir ve pozisyon ayrı | Çalıştırılmadı |
| Ayar/start/stop | Açık emir/pozisyon varken değişiklik | Hemen ve sonraki etki | Çalıştırılmadı |
| Kopma/restart | Replay ve tekrar olay | Kurtarma sınırı | Çalıştırılmadı |

Arbitraj için eksik bacak/hedge, Toplu Emirler için saat/tekrar/handoff, Tavan/Taban için kilit/timer özel senaryoları eklenir. Planlanan test çalıştırılmış sayılmaz.

## Sorularımız ve netleşen noktalar

Gerçek soru/bağlam/yanıt tarihli tutulur. Kaynak bulunamayan veya ürün kararı gerektiren nokta açık bırakılır.

## Kaynaklar ve devam notu

Kaynak repo/branch/commit, kod sembolleri, teknik belge ve varsa resmi dış kaynak; son yazılan kısım, açık doğrulama ve sonraki adım belirtilir.
