---
kapsam: MTrader belgeleri, yayınları, testleri ve sorun kayıtlarının ana dizini
dogrulama: 2026-10-27
durum: taslak
---

# MTrader dokümanları

Ürün **MTrader**, şirket **MeeApps**. Teknik bilgi tabanı, insan rehberi, yayınlar, test dosyaları ve issue kayıtları ayrı alanlarda tutulur.

| Aradığın içerik | Giriş |
|---|---|
| AI için sistem, servis, strateji ve akış bilgisi | [Bilgi tabanı](bilgi-tabani/README.md) |
| Konu konu okunacak yazılı rehber | [Rehber kaynakları](dersler/README.md) |
| Güncel PDF, EPUB ve HTML kitap | [Yayınlar](yayinlar/README.md) |
| Kullanıcıların çalıştıracağı sanity testleri | [Testler](testler/README.md) |
| Açık sorunlar ve issue taslakları | [Issue'lar](issues/README.md) |
| Eski sürümler ve tamamlanmış çalışmalar | [Arşiv](arsiv/README.md) |

## Güncel çalışma

Arbitraj sanity incelemesi sürüyor; aktif sürüm ve kapsam [sanity dizininde](testler/sanity/README.md) tutulur. Diğer stratejilere otomatik geçilmez. Rehberde 24 konu yazıldı; ayrıntı [ilerleme kaydında](dersler/ilerleme.md). AI bilgi tabanının ilk kapsamı kapalıdır; yeni araştırma ayrı taleple başlar.

## Çalışma kuralları

- Agent başlangıcı: [AGENTS.md](AGENTS.md), ardından [oturum notları](OTURUM-NOTLARI.md).
- Kaynak repo ve doğrulama sürümleri: [manifest.yaml](manifest.yaml). Klasör taşıması kodun yeniden doğrulandığı anlamına gelmez.
- [Güncelleme süreci](_surec/guncelleme.md), [yazım kuralları](_surec/yazim-kurallari.md), [değişiklik geçmişi](CHANGELOG.md).
- Yapısal kontrol: `python _surec/kontrol.py`.
- Kitap üretimi: `python dersler/yayin/uret.py --format all` veya VS Code'da **Ctrl+Shift+B**. Kaynak Markdown düzenlenir.

Aktif Excel'lerin tek adresi `testler/sanity/`, güncel kitap çıktılarının tek adresi `yayinlar/mtrader-rehberi/` olur. `outputs/` teslim kopyaları, `tmp/` geçici çalışmalar içindir. Açık Arbitraj teslim dosyası kullanıcı isteğiyle `outputs/` içinde bırakılmıştır; değişiklikleri karşılaştırılmadan silinmez veya aktif dosyanın üzerine aktarılmaz.

Mate dosyaları yalnız test yaklaşımı için [referans örneklerdir](testler/referanslar/mate/README.md). `.tools/` yayın araçlarını, `.vscode/` hazır görevleri içerir.
