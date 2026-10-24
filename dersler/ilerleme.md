---
kapsam: Rehber yazımının mevcut durumu, tamamlanan yapı işleri ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

Yazım öncesi temel tercihler netleşti: ana okuyucu kullanıcı; mantık/davranış odaklı anlatım, gerektiğinde kısa kod, derin ayrıntı ayrı bölümde. Mevcut hatalar rehberde anlatılmayacak; düzeltme doğrulandıktan sonra rehber güncellemesi kapanış kontrolüne dahil edilecek. Kalıcı kayıt [kararlar](kararlar.md) dosyasında. Başlamak için zorunlu açık tercih yok; sonraki içerik uygulamanın amacı. Ana konu anlatımları henüz başlamadı; bu rehber bir süre ana çalışma konusu.

24 Ekim 2026: kullanıcı ders düzeninden konu bazlı yazılı rehbere geçilmesini istedi. Ayrıntılı indeks, altı bölüm indeksi ve 48 konu iskeleti oluşturuldu. Eski 11 dosya `arsiv/` altında korundu. Rehbere özel talimatlar, kararlar, yazım düzeni ve strateji şablonu hazırlandı.

| Bölüm | Konu sayısı | Yazım durumu | Kullanıcı okuma durumu |
|---|---|---|---|
| Uygulamanın amacı | 2 | İskelet | Henüz bildirilmedi |
| Borsa temelleri | 12 | İskelet | Henüz bildirilmedi |
| Teknik temeller | 10 | İskelet | Henüz bildirilmedi |
| Bizim sistemimiz | 11 | İskelet | Henüz bildirilmedi |
| Stratejiler | 10 | İskelet | Henüz bildirilmedi |
| Test ve proje yönetimi | 3 | İskelet | Henüz bildirilmedi |

Bu turda yeni kod incelemesi, internetten kural doğrulaması, uygulama testi veya ekran/şema üretimi yapılmadı. `dogrulama` bu yapının düzenlenme tarihidir; boş konuya teknik doğruluk atfetmez. Konu iskeletlerinin frontmatter durumu `bos`.

## Sıradaki tek başlangıç noktası

Önce kullanıcıdan gelen indeks değişiklikleri işlenir. İçerik doldurmaya geçildiğinde ilk dosya [Ne yapıyoruz ve neyi amaçlıyoruz?](01-uygulama/01-ne-yapiyoruz.md). Mevcut sistem haritası ve ürün kapsamından kısa, insan için anlatım yazılacak; henüz öğretilmemiş terimler açıklamasız bırakılmayacak. Ardından kullanıcılar/iş günü ve borsa temelleri gelir. Her tur bütün iskeletler topluca doldurulmaz.

İndeksin gözden geçirilmesi formal onay kapısı değildir; kullanıcı içerikten devam et derse mevcut sıra uygulanır. Borsa bölümüne gelindiğinde seans/T+N gibi güncel iddiaların resmi kaynak araştırması yapılır. Bugün araştırılmadığı için güncel kural ilan edilmez.

## Her konu için takip

Konu dosyasındaki devam notuna yazılan kapsam, incelenen kaynak, kalan doğrulama, sorular ve sonraki adım eklenir. İçerik yazılınca bölüm indeksindeki “Planlandı” durumu “Taslak yazıldı” yapılır; kullanıcı okuduğunu/konuştuğunu bildirdiğinde o bilgi tarihli ve ayrıca kaydedilir. Sorular cevaplandıkça ilgili anlatım güncellenir.

## Doğrulama ve Git

Yapısal kontrol tamamlandı: 165 Markdown, 1.842 bağlantı, 0 hata; 48 konu `bos` olarak izleniyor. UTF-8 kontrolü yapıldı; diff sonundaki gereksiz boş satır düzeltildi. Önceki oturumda push otomatik onay incelemesince reddedildi; bu tur kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
