---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

Emir yaşam döngüsü taslak yazıldı. Yedi konu kitapta, 41 konu iskelet; yeni konu henüz kullanıcı okumasından geçmedi. Kredili işlemler bakiye konusunda ayrı başlıkta planlı.

## Son tamamlanan iş

Gönderim/kabul/ret/gerçekleşme/iptal/değişiklik ayrımı yazıldı; 100 adetlik örnekte iptal beklerken ek gerçekleşme ve pozisyon sonucu açıklandı. Resmi OUCH 6 Şubat 2025 belgesi ve Pay SSS okundu; mevcut KB motor/GUI ayrımı için kullanıldı. Yeni kod/canlı test yok. Yayın 0.8 PDF/HTML/EPUB yenilendi. PDF 19 A4 sayfa; yeni sayfalar görsel kontrol edildi, örnek tablo bölünmeden yerleştirildi. EPUB bütünlüğü ve 1.869 bağlantı kontrolü geçti.

## Sıradaki tek başlangıç noktası

`02-borsa-temelleri/06-seanslar-ve-muzayede.md`: sürekli işlem, emir toplama/eşleştirme, denge fiyatı, kapanış ve devre kesici. Saatler ürün/pazar ve güncel resmi kaynakla doğrulanır.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

Yedi konu `taslak`, kalan 41 konu `bos`. Yapısal kontrol: 168 Markdown, 1.869 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
