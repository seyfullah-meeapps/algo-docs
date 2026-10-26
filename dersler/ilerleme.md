---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

**Teknik Temeller'in 10 konusu da taslak yazıldı; yeni bölüm toplu kullanıcı incelemesi bekliyor.** Önceki Uygulama ve Borsa Temelleri'nin toplam 14 konusu kullanıcı tarafından 25 Ekim 2026 tarihinde okundu ve uygun bulundu. Okuma onayı, yeni kod/canlı doğrulaması olarak kaydedilmedi; kaynak dosyaların teknik `durum` etiketleri bu nedenle otomatik değiştirilmedi.

Kitap toplam 24 konu içeriyor; kalan 24 konu iskelet. Yayın 0.12 PDF/HTML/EPUB üretildi. PDF 56 A4 sayfa; Teknik Temeller 37–56. sayfalarda. Yeni 20 sayfa, içindekiler ve düzeltilen sahiplik tablosu görsel kontrol edildi; EPUB paket/XML bütünlüğü ve HTML konu sayısı kontrolü geçti. Sonraki bölüm Bizim Sistemimiz'e henüz geçilmiyor.

## Son tamamlanan iş

Program/servis/container/SDK, ağ/TCP/UDP/multicast, HTTP/REST/WS, gRPC/Protobuf/MARpc, binary/fiyat/zaman, C++ bellek/ömür, thread/kuyruk/kilit, gecikme/colocation, kurtarma ve log/test/sürüm konuları yazıldı. Benzetmeler, sayısal örnekler ve ilgili KB bağlantıları eklendi. Resmi protokol/ürün belgeleri okundu. HFT development `4275ccc` ve hub development `1cca9a8` referanslarında sınırlı salt okunur kod kontrolleri yapıldı; yerel branch uçlarının daha ileride olduğu açık kaydedildi. SDK özeti aktarımı yeni kod doğrulaması sayılmadı. Yeni uygulama build'i, canlı emir, benchmark veya deploy testi yok.

## Sıradaki tek başlangıç noktası

Kullanıcının **Teknik Temeller bölümüne toplu revizyonları** işlenir. Yeni bölüm okunmuş/onaylanmış sayılmaz. Kullanıcı bir sonraki bölüme geçiş istediğinde başlangıç `04-sistem-mimarisi/01-repolar-ve-bilesenler.md`; kapsam mevcut toplu bölüm inceleme tercihiyle belirlenir.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

24 konu `taslak`, kalan 24 konu `bos`. Yapısal kontrol: 168 Markdown, 1.868 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
