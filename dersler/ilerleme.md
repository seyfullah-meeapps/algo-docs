---
kapsam: Rehber yazımının mevcut durumu, tamamlanan yapı işleri ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

**Yeni tamamlanan iş: A4 yayın ve önizleme düzeni.** `yayin/` altında Quarto ayarları, yayın listesi, üretim/kurulum scriptleri ve okuma yönergesi var. VS Code görevleri eklendi. Quarto 1.10.18 resmi ZIP paketi SHA-256 doğrulanarak `.tools/` içine taşınabilir kuruldu; sistem PATH ayarı değişmedi. PDF/HTML/EPUB üretildi; PDF 5 A4 sayfa. PDF'nin bütün sayfaları görsel kontrol edildi, EPUB paket kontrolü geçti. Canlı HTML'de kaynak değişikliği ve geri alma otomatik yenilenerek doğrulandı. Farklı EPUB okuyucu görünümü henüz denenmedi.

Kullanıcının sorusu: A4 okuyup gerekirse PDF/EPUB alırken ne kurmalı, nasıl takip ve revizyon yapmalı? Yanıt ve kalıcı kullanım düzeni `yayin/README.md` içinde. Bu bilgisayarda zorunlu ek indirme kalmadı. Güncel çıktılar Git'e alınmaz; ayarlar/scriptler saklanır. Sonraki içerik yine kullanıcılar ve örnek iş günü; yeni konular `yayin/kitap.json` listesine eklendikçe kitaba girer.

Yazım öncesi temel tercihler netleşti: ana okuyucu kullanıcı; mantık/davranış odaklı anlatım, gerektiğinde kısa kod, derin ayrıntı ayrı bölümde. Mevcut hatalar rehberde anlatılmayacak; düzeltme doğrulandıktan sonra rehber güncellemesi kapanış kontrolüne dahil edilecek. Kalıcı kayıt [kararlar](kararlar.md) dosyasında. İlk konu “Ne yapıyoruz ve neyi amaçlıyoruz?” taslak olarak yazıldı; kullanıcı okuma geri bildirimi henüz yok. Sonraki konu kullanıcılar ve örnek iş günü; bu rehber ana çalışma konusu.

24 Ekim 2026: kullanıcı ders düzeninden konu bazlı yazılı rehbere geçilmesini istedi. Ayrıntılı indeks, altı bölüm indeksi ve 48 konu iskeleti oluşturuldu. Eski 11 dosya `arsiv/` altında korundu. Rehbere özel talimatlar, kararlar, yazım düzeni ve strateji şablonu hazırlandı.

| Bölüm | Konu sayısı | Yazım durumu | Kullanıcı okuma durumu |
|---|---|---|---|
| Uygulamanın amacı | 2 | İlk konu taslak; ikinci konu iskelet | Henüz bildirilmedi |
| Borsa temelleri | 12 | İskelet | Henüz bildirilmedi |
| Teknik temeller | 10 | İskelet | Henüz bildirilmedi |
| Bizim sistemimiz | 11 | İskelet | Henüz bildirilmedi |
| Stratejiler | 10 | İskelet | Henüz bildirilmedi |
| Test ve proje yönetimi | 3 | İskelet | Henüz bildirilmedi |

İlk konu mevcut KB kaynaklarından derlendi; kavramsal Mermaid akışı eklendi. Yeni kod incelemesi, internetten kural doğrulaması, uygulama testi veya gerçek ekran üretimi yapılmadı. `dogrulama` bu yapının düzenlenme tarihidir; boş konuya teknik doğruluk atfetmez. Konu iskeletlerinin frontmatter durumu `bos`.

## Sıradaki tek başlangıç noktası

Sıradaki dosya [Kullanıcılar ve örnek iş günü](01-uygulama/02-kullanicilar-ve-is-gunu.md). Önce ilk konuya gelen kullanıcı soruları varsa işlenir. İş günü anlatımı müşteri veya resmi seans saatleri uydurmadan, roller ve örnek akış üzerinden yazılır. Kullanıcı yazım sürerken kodları inceleyeceğini belirtti; kod incelemesinin tamamlandığı varsayılmaz. Sonrasında borsa temellerine geçilir.

İndeksin gözden geçirilmesi formal onay kapısı değildir; kullanıcı içerikten devam et derse mevcut sıra uygulanır. Borsa bölümüne gelindiğinde seans/T+N gibi güncel iddiaların resmi kaynak araştırması yapılır. Bugün araştırılmadığı için güncel kural ilan edilmez.

## Her konu için takip

Konu dosyasındaki devam notuna yazılan kapsam, incelenen kaynak, kalan doğrulama, sorular ve sonraki adım eklenir. İçerik yazılınca bölüm indeksindeki “Planlandı” durumu “Taslak yazıldı” yapılır; kullanıcı okuduğunu/konuştuğunu bildirdiğinde o bilgi tarihli ve ayrıca kaydedilir. Sorular cevaplandıkça ilgili anlatım güncellenir.

## Doğrulama ve Git

Yapısal kontrol tamamlandı: 166 Markdown, 1.856 bağlantı, 0 hata; ilk konu `taslak`, kalan 47 konu `bos`. `git diff --check` temiz. Yayın çıktıları ve araçlar Git dışında. Önceki oturumda push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
