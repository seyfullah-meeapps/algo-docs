---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

Kullanıcı sade vadeli anlatımını anladığını belirtti ve kaydedilmesini istedi. Tek sözleşme, 5.000 TL nakit ve varsayımsal 300 TL teminat örneği kaydedildi; 21 TL’nin açılışta ödenmediği açıklandı. Kredili işlemler için bakiye konusunda ayrı başlık planlandı. Fiyat adımı ve fiyat sınırları yazıldı; beş konu kitapta, 43 konu iskelet.

## Son tamamlanan iş

Vadeli örneği sadeleşti; kredi ile VİOP teminatı ayrıldı. Yeni konuda tick/spread, baz/tavan/taban, yuvarlama ve strateji fiyat koşulu açıklandı. Resmi BIST kaynakları okundu; gerçek günlük oran/adım kataloğu, kod veya canlı test yok. Yayın 0.6; PDF/HTML/EPUB yenilendi. PDF 14 A4 sayfa; değişen ve yeni sayfalar görsel kontrol edildi, EPUB bütünlüğü ve 1.870 bağlantı kontrolü geçti.

## Sıradaki tek başlangıç noktası

`02-borsa-temelleri/04-emir-tipleri-ve-sureleri.md`. Kredili işlemlerin ayrıntısı `07-pozisyon-bakiye-kar-zarar.md` içinde ayrı başlık olarak yazılacak; kurum bilgisi olmadan kredi/teminat bakiye eşlemesi uydurulmaz.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

Beş konu `taslak`, kalan 43 konu `bos`. Yapısal kontrol: 168 Markdown, 1.870 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
