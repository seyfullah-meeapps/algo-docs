---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

**İlk bölümün yazımı tamamlandı; kullanıcı okuması ve revizyonları bekleniyor.** “Uygulamanın amacı” bölümündeki iki konu taslak olarak kitapta. Kullanıcı önce bu bölümü okuyup geri bildirim vereceğini belirtti. Şimdilik borsa temellerine geçilmeyecek. İçeriklerin onaylandığı varsayılmaz.

| Bölüm | Konu sayısı | Yazım durumu | Kullanıcı okuma durumu |
|---|---|---|---|
| Uygulamanın amacı | 2 | İki konu da taslak yazıldı; kitapta | Okuma ve revizyon bekleniyor |
| Borsa temelleri | 12 | İskelet | Henüz bildirilmedi |
| Teknik temeller | 10 | İskelet | Henüz bildirilmedi |
| Bizim sistemimiz | 11 | İskelet | Henüz bildirilmedi |
| Stratejiler | 10 | İskelet | Henüz bildirilmedi |
| Test ve proje yönetimi | 3 | İskelet | Henüz bildirilmedi |

## Son tamamlanan iş

24 Ekim 2026: “Kullanıcılar ve örnek iş günü” yazıldı. Roller, kullanıcı/hesap/ürün ayrımı, beş aşamalı örnek gün ve 100 lot emrin 40 lot gerçekleşip 60 lot iptal edildiği takip örneği eklendi. Roller kesin şirket unvanı olarak sunulmadı; müşteri/seans saatleri uydurulmadı. Metin mevcut KB ve kullanıcının PM bağlamından derlendi; yeni kod incelemesi, internetten kural doğrulaması veya uygulama testi yok.

Kitap sürümü 0.2: iki konu, kapak ve ön sayfalarla **8 A4 sayfa**. PDF/HTML/EPUB yenilendi; yeni sayfalar ve içindekiler görsel kontrol edildi. Takip örneğinin tablosu tek sayfada tutuldu. Önceki beyaz kapak, siyah metin, primary yeşil logo alanı ve küçük ok uçları korundu. Kullanıcının son mesajı görsel tasarımı olumlu bulduğunu gösterir; içerik onayı değildir.

## Sıradaki tek başlangıç noktası

Kullanıcının ilk bölümle ilgili soruları ve revizyonları ilgili konu dosyasına işlenir; ardından çıktı tekrar üretilir. Kullanıcı devam istediğinde ilk yeni konu `02-borsa-temelleri/01-piyasalar-ve-urunler.md`. Sonraki başlıklarda güncel borsa iddiaları resmi kaynaktan, proje davranışı koddan doğrulanır.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

İki konu `taslak`, kalan 46 konu `bos`. Yapısal kontrol: 167 Markdown, 1.863 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
