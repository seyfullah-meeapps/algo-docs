---
kapsam: Frontend marka kaynakları ve rehberin PDF/HTML/EPUB görsel tasarım kararları
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-24
durum: taslak
---

# Rehberin marka ve tipografi kaydı

Kaynak klon `mtrader-trade-ui`, development `b0474c3f564a8f2513352014c3c1c80841d5a068`. Bu tur `app/global.css` tokenları, logo dosyası ve `_auth.tsx` içindeki logo kullanımı okundu. Frontend kaynak dosyaları değiştirilmedi; ağdan yeni sürüm çekilmedi.

## Kaynaktan alınanlar

| Öğe | Kaynak | Rehber kullanımı |
|---|---|---|
| Beyaz, saydam MeeApps logosu | `public/assets/images/MeeApps_Logo.png` | Aynı dosya [brand-logo.png](brand-logo.png) olarak kopyalandı; marka yeşili logo alanı ve HTML sidebar |
| Marka yeşili `#94c04e` | `app/global.css`, `--color-primary` | Ayırıcılar ve seçili bölüm vurgusu |
| Kapak zemini beyaz `#ffffff` | Light `--color-bg` | Kullanıcı revizyonuyla beyaz kapak; siyah metin |
| Başlık `#212121`, gövde `#333333` | Light `--color-fg-strong` / `--color-fg` | Beyaz iç sayfalardaki yüksek kontrastlı metin |
| Çizgi `#d9d9d9`, yüzey `#f4f4f5` | `--color-border` / `--color-soft-dark` | Tablolar ve ayırıcılar |
| Bağlantı `#15803d` | Light `--color-up` / `--color-action-start` | Beyaz zeminde daha koyu yeşil bağlantı tonu |

Logo yeniden çizilmedi, yeniden renklendirilmedi. SHA-256: `EAF8C713A28F508AB8B9019627F5032248978EA19C1D97FCC8A18DD04BF57140`.

## Okuma tasarımı

24 Ekim 2026 kullanıcı geri bildirimi: metinler büyük, başlık ve metinler birbirine yakın. Gövde 11 pt yerine **10,25 pt Arial**, bölüm başlığı **18 pt**, alt başlık **12 pt** yapıldı. Alt başlık öncesi **7 mm**, sonrası **3,5 mm** boşluk; paragraf aralığı **0,95 em**. A4 ve 20 mm sayfa kenarları korundu. Başlıklar izleyen metinle tutulur; kapak sayfa numarası göstermez, devam eden fiziksel sayfalar numaralanır.

Özgün UI'ın yoğun işlem ekranı düzeni basılı sayfaya aynen taşınmadı. Marka vurguları korundu; içerik beyaz zeminde, daha küçük metin ve daha belirgin bölüm aralarıyla düzenlendi. Yardımcı yazı için `#6b6b6b` çıktı tasarımında seçildi; frontend'in birebir muted tokenı olduğu iddia edilmez.

HTML ana metni 15 px, satır yüksekliği 1,85; başlık/paragraf boşlukları artırıldı. EPUB ayrı [epub.css](epub.css) ile göreli `1em` boyut kullanır; okuyucunun font tercihi korunur. PDF/HTML renk ve ölçüleri tek bir ekranın piksel eşlemesi değildir.

PDF'nin beş sayfası ve HTML bölüm görünümü görsel olarak kontrol edildi. EPUB paket kontrolü yapıldı; ayrı e-kitap okuyucusundaki görünüm henüz denenmedi. Yeni tasarım kullanıcı tarafından onaylanmış sayılmaz.

## Ürün kimliği ve başlık revizyonu

24 Ekim 2026: kullanıcı ürün adını **MTrader**, şirketi **MeeApps** olarak düzeltti; kitap başlığı “MTrader — Algoritmik İşlem Botu” oldu. Ana bölüm başlıklarına açık yeşil zemin, sol marka çizgisi ve ayrı “BÖLÜM N” etiketi eklendi. İçindekiler aynı başlıkların izini tutar. Genel okuma önsözü kaldırıldı. Bu revizyonun ilk bölümü 7 sayfadır; önceki sayfa sayıları tarihsel tasarım kayıtlarıdır.

## Kapak ve ok ucu revizyonu

24 Ekim 2026: kullanıcı koyu kapağı beyaz, kapak metinlerini siyah istedi. Beyaz logo marka primary rengi `#94c04e` zeminli bir alana yerleştirildi; HTML logo alanı da aynı yeşile alındı. SVG ok uçları `markerUnits=userSpaceOnUse` ile çizgi kalınlığından bağımsız 8 birimlik alana indirildi; önceki örtük strokeWidth ölçeklemesi kaldırıldı. Çıktılar yeniden üretildi, kapak ve şema PDF üzerinden görsel kontrol edildi.
