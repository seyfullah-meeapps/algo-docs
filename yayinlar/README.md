---
kapsam: İnsan rehberinin güncel PDF, EPUB ve HTML çıktıları
dogrulama: 2026-10-27
durum: taslak
---

# Okunacak yayınlar

Güncel MTrader rehberi 0.12 sürümüdür; 24 konu içerir.

- [A4 PDF](mtrader-rehberi/meeapps-rehber.pdf)
- [EPUB](mtrader-rehberi/meeapps-rehber.epub)
- [HTML giriş sayfası](mtrader-rehberi/index.html)

Üç biçim aynı `mtrader-rehberi/` klasöründe tutulur. HTML'yi taşırken bölüm dosyaları, görseller ve `site_libs/` birlikte taşınmalıdır. Aynı PDF'nin ikinci bir aktif kopyası üretilmez.

Metin değişiklikleri [dersler](../dersler/README.md) altındaki Markdown kaynaklarında yapılır. Repo kökünde `python dersler/yayin/uret.py --format all` veya VS Code'da **Ctrl+Shift+B** ile bu klasör üretilir. [Ayrıntılı yayın yönergesi](../dersler/yayin/README.md).

Üretilen dosyalar Git dışında, yayın ayarları ve kaynaklar Git'te tutulur. Yeni bilgisayarda çıktıları üretmek gerekir.
