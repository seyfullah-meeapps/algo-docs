---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

Emir tipleri ve geçerlilik süreleri taslak yazıldı; altı konu kitapta, 42 konu iskelet. Yeni konu henüz kullanıcı tarafından okunmuş sayılmaz. Kredili işlemler bakiye konusunda ayrı başlıkta planlı.

## Son tamamlanan iş

Limit/piyasa/piyasadan limite aynı defterle, günlük/KİE/FOK ayrı miktar tablosuyla açıklandı. Pay Piyasası Prosedürü 3.34 (21 Eylül 2026) ve resmi web açıklamaları okundu. VİOP piyasa emri kısıtı ile teknik yetenek/fiili kullanım ayrıldı. MTrader kodu veya canlı test yapılmadı. Yayın 0.7 PDF/HTML/EPUB yenilendi. PDF 16 A4 sayfa; yeni iki sayfa görsel kontrol edildi, EPUB bütünlük kontrolü geçti.

## Sıradaki tek başlangıç noktası

`02-borsa-temelleri/05-emir-yasam-dongusu.md`: gönderim/kabul/ret/gerçekleşme/iptal/değişiklik. Okuma revizyonları gelirse önce ilgili konu güncellenir.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

Altı konu `taslak`, kalan 42 konu `bos`. Yapısal kontrol: 168 Markdown, 1.869 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
