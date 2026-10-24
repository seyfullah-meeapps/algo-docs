---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

**Borsa temellerinin 12 konusu da taslak yazıldı ve kitaba eklendi.** Kullanıcı kalan başlıkların tek turda tamamlanmasını istedi; bölüm artık toplu okuma/revizyon bekliyor. İlk uygulama bölümünün iki konusu ile kitap toplam 14 konu içeriyor. Diğer 34 konu iskelet. Teknik temellere henüz geçilmiyor.

## Son tamamlanan iş

Seanslar/denge fiyatı, pozisyon-bakiye-kâr/zarar ve ayrı kredili işlemler başlığı, T+2/brüt takas/T+1 hazırlıkları, açığa satış/uptick, ITCH/OUCH/FIX, Glimpse/Rewinder/replay ve strateji fikirleri tamamlandı. Tarihli resmi BIST/SPK/MKK/KAP ve protokol kaynakları kullanıldı. T+1 testleri canlı geçiş sayılmadı; 22 Eylül 2026 uptick duyurusu kalıcı izin listesi olarak sunulmadı. ITCH PDF doğrudan açılamadı; erişilebilen Appendix E arama metni ve resmi tanıtımla temel kurtarma kavramları anlatıldı. Yeni kod/canlı test yok. Yayın 0.9 PDF/HTML/EPUB üretildi. PDF toplam 34 A4 sayfa; borsa bölümü 9–34. sayfalarda. Yeni sayfalar ve iki sayfalık içindekiler görsel kontrol edildi; seans tablosu bölünmeden yerleştirildi. EPUB bütünlük kontrolü geçti.

## Sıradaki tek başlangıç noktası

Kullanıcının **borsa bölümüne toplu revizyonları** işlenir. Yeni konuya geçmeden bu geri bildirimler beklenir. Kullanıcı teknik bölüme devam istediğinde ilk dosya `03-teknik-temeller/01-program-servis-container-sdk.md`. Kullanıcı adım adım tek konu tesliminden vazgeçti; bundan sonraki bölüm boyutu mevcut yönlendirmesiyle belirlenir.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

14 konu `taslak`, kalan 34 konu `bos`. Yapısal kontrol: 168 Markdown, 1.860 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
