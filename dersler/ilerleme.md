---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

Kullanıcı BYF açıklamasından sonra devam istedi. Emir defteri ve eşleşme taslağı yazıldı; önceki konuda BYF tekrarları azaltıldı, kısa ürün tanımı korundu. Dört konu kitapta, 44 konu iskelet. Yeni konu henüz kullanıcı okumasından geçmedi.

## Son tamamlanan iş

Alış/satış, spread, kademe/derinlik, fiyat-zaman önceliği, kuyruk, kısmi ve çok seviyeli eşleşme örneği yazıldı. Header/erime ve piyasa defteri/kendi emri ayrımı açıklandı. Resmi BIST kaynakları okundu; yeni kod veya canlı test yok. Yayın sürümü 0.5; PDF/HTML/EPUB yenilendi. PDF 11 A4 sayfa; yeni sayfalar görsel olarak, EPUB paket bütünlüğü ve belge bağlantıları araçlarla kontrol edildi.

## Sıradaki tek başlangıç noktası

`02-borsa-temelleri/03-fiyat-adimi-ve-limitler.md`: fiyat adımı, baz fiyat, tavan/taban ve ürün bazlı kurallar. Okuma revizyonları gelirse önce ilgili dosyada işlenir.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

Dört konu `taslak`, kalan 44 konu `bos`. Yapısal kontrol: 168 Markdown, 1.870 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
