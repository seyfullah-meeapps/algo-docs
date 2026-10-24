---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

İlk bölüm revizyonlar sonrasında kullanıcı tarafından uygun bulundu; 24 Ekim 2026 talebiyle borsa temellerine geçildi. “Piyasalar, ürünler ve miktar birimleri” taslak yazıldı. Toplam 3 konu yazılı, 45 konu iskelet; yeni konu henüz okunmadı.

## Son tamamlanan iş

BIST/Pay Piyasası/VİOP, pay/endeks/BYF/varant/vadeli ayrımı ve sözleşme büyüklüğü açıklandı. Borsa İstanbul'un resmi sayfaları okundu; standart pay vadeli sözleşme örneğinde adet ve nominal değer ayrımı kuruldu. MTrader bağlantısı kavramsal; yeni kod/canlı test yok. Yayın sürümü 0.4; PDF/HTML/EPUB yenilendi. PDF toplam 9 A4 sayfa; yeni iki sayfa görsel kontrol edildi, EPUB paket bütünlüğü doğrulandı.

## Sıradaki tek başlangıç noktası

`02-borsa-temelleri/02-emir-defteri.md`: alış/satış tarafı, spread, kademe, eşleşme ve öncelik. Kullanıcının okuma revizyonları gelirse önce ilgili dosyada işlenir. İlk bölüm için önceki bekleme kararı son devam talebiyle kalktı.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

Üç konu `taslak`, kalan 45 konu `bos`. Yapısal kontrol: 168 Markdown, 1.869 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
