---
kapsam: Rehber yazımının mevcut durumu, tamamlanan işler ve sonraki adım
dogrulama: 2026-10-24
durum: taslak
---

# İlerleme ve devam noktası

## Şu an

**İlk bölüm yazıldı; kullanıcının ilk içerik revizyonları işlendi, yeniden okuma bekleniyor.** “Uygulamanın amacı” bölümündeki iki konu taslak olarak kitapta. Kullanıcı ilk bölümde ürün/şirket ve test süreci düzeltmeleri verdi; bunlar uygulandı. Şimdilik borsa temellerine geçilmeyecek. İçeriklerin onaylandığı varsayılmaz.

| Bölüm | Konu sayısı | Yazım durumu | Kullanıcı okuma durumu |
|---|---|---|---|
| Uygulamanın amacı | 2 | İki konu da taslak yazıldı; kitapta | İlk revizyon işlendi; yeniden okuma bekleniyor |
| Borsa temelleri | 12 | İskelet | Henüz bildirilmedi |
| Teknik temeller | 10 | İskelet | Henüz bildirilmedi |
| Bizim sistemimiz | 11 | İskelet | Henüz bildirilmedi |
| Stratejiler | 10 | İskelet | Henüz bildirilmedi |
| Test ve proje yönetimi | 3 | İskelet | Henüz bildirilmedi |

## Son tamamlanan iş

24 Ekim 2026, ilk okuma revizyonu: ürün **MTrader**, şirket **MeeApps**. Müşteriler aracı kurumlar; günlük kullanıcılar onların traderları/fon yöneticileri. MeeApps'in kullanımı geliştirme/test içindir. Önceki birleşik günlük kullanım anlatımı yerine “Kullanıcılar ve geliştirme süreci” yazıldı. Özellik/senaryo/görev → geliştirici ön testi → test ortamı → anlaşılmış traderlarla preprod düşük lot → kararlılık sonrası yüksek lot → bütün müşterilere aktarım açıklandı. Sayısal lot/süre/onay yetkisi uydurulmadı. Ana KB tek referansı `00-genel/urun-ve-gelistirme-sureci.md` ve ilgili giriş bağlantıları güncellendi.

Yayın sürümü 0.3: **7 A4 sayfa**, iki konu. “Okumaya başlamadan” sayfası kaldırıldı; HTML giriş sayfası ilk konudur. Kitap başlığı MTrader — Algoritmik İşlem Botu; ana başlıklar bölüm rozeti ve marka şeridiyle zenginleştirildi. PDF/HTML/EPUB yenilendi; PDF sayfaları, metin ve HTML görünümü kontrol edildi. Eski küçük harfli ürün adı ve kaldırılan önsöz PDF/EPUB'da yok. Güncel dosyalar aynı çıktı adlarını kullanır.

## Sıradaki tek başlangıç noktası

Kullanıcının ilk bölümle ilgili soruları ve revizyonları ilgili konu dosyasına işlenir; ardından çıktı tekrar üretilir. Kullanıcı devam istediğinde ilk yeni konu `02-borsa-temelleri/01-piyasalar-ve-urunler.md`. Sonraki başlıklarda güncel borsa iddiaları resmi kaynaktan, proje davranışı koddan doğrulanır.

## Kalıcı çalışma düzeni

Önce `AGENTS.md`, `kararlar.md`, ana indeks ve `calisma-duzeni.md` okunur. Ana okuyucu kullanıcı; sonraki okuyucular görevi devralan/yeni katılan kişiler. Mantık/davranış odaklı, kısa kodlu anlatım; mevcut hatalar rehber dışında, düzeltme sonrası rehber güncellemesi kapanış kontrolünde. Kullanıcının gerçek soru/bağlamı ilgili konuya tarihli yazılır.

Yayın kullanımı `yayin/README.md`, tasarım kaynakları `yayin/marka.md`, yayın listesi `yayin/kitap.json` içinde. MD kaynakları düzenlenir; çıktılar yeniden üretilir. Quarto proje içindeki `.tools/` altında taşınabilir kurulu. Eski dersler `arsiv/` içinde tarihsel kayıttır; eski Ders 06 sırası geçersiz.

## Doğrulama ve Git

İki konu `taslak`, kalan 46 konu `bos`. Yapısal kontrol: 168 Markdown, 1.871 bağlantı, 0 hata; `git diff --check` temiz. Çıktılar ve araçlar Git dışında. Önceki push otomatik onay incelemesince reddedildi; kullanıcı uzak depoya gönderim onayı vermedi. Push tekrar denenmez; çalışmalar yerelde saklanır.
