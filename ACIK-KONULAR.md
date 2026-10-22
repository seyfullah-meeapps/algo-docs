---
kapsam: Açık sorunlar, şüpheli davranışlar ve doğrulanmamış iddialar — tek satırlık indeks
dogrulama: 2026-10-22
durum: taslak
---

# Açık konular

Her konu **tek satır**. Ayrıntı yalnızca linklenen dosyada yazılır; burada açıklama büyütülmez.
Kapanan konu buradan silinir, kapanışı `CHANGELOG.md`'ye yazılır. Yeni konu sıradaki numarayı alır (numara tekrar kullanılmaz).

Tür: **bug?** olası hata · **doğrula** kodla/borsayla teyit gerekli · **eksik** dokümana aktarılmadı · **iş** yapılacak iş (doküman dışı)

## Sistem

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-01 | bug? | itch-sdk `partId` VİOP'ta 4 partition varsayıyor, HFT 6 dinliyor; 5–6. partition'da çakışma olabilir. ⏸ ertelendi | [itch-sdk](10-servisler/itch-sdk/README.md) § Glimpse ve Rewinder |
| K-02 | bug? | A1 ve Alnus-Algo'da trade-data-app VİOP'ta 4 partition dinliyor; 5–6. partition enstrümanları GUI'de görünmeyebilir. ⏸ ertelendi | [trade-data-app](10-servisler/trade-data-app/README.md) § Config |
| K-03 | bug? | Tavan: yeni stratejide DB'ye 600/1200 varsayılan saat yazılıyor, UI 36000–64800 bekliyor; yanlış değer UI'dan geri gidebilir | [tavan](20-stratejiler/tavan.md) § Wire alanları |
| K-04 | doğrula | Teorik Fiyat `executeOrder` pozisyonu güncellemiyor (kod yorumda); kasıtlı mı? | [teorik-fiyat](20-stratejiler/teorik-fiyat.md) § Bilinen durumlar |
| K-05 | doğrula | Admin paneli domain → :6688 yönlendirmesi (reverse proxy) | [sistem-haritasi](00-genel/sistem-haritasi.md) § Bağlantı tablosu |
| K-06 | doğrula | itch-sdk eski "bilinen buglar" listesinin hangileri düzeltildi | [itch-sdk](10-servisler/itch-sdk/README.md) § Bilinen notlar |
| K-07 | doğrula | network-sdk eski wire protokol / bağlantı notları tek tek kontrol edilmedi | [network-sdk](10-servisler/network-sdk/README.md) § Build |
| K-08 | eksik | trade-data-app MySQL tam şeması (migration yok) | [trade-data-app](10-servisler/trade-data-app/README.md) § MySQL tabloları |
| K-09 | eksik | `Sabah_Kontrolleri.docx` bilgi tabanına aktarılmadı | [40-operasyon](40-operasyon/README.md) § Sabah kontrolleri |

## Borsa kuralları

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-10 | doğrula | Fiyat adımı: 250 TL üstü kademeler ve tablonun yürürlük tarihi | [borsa-kurallari](00-genel/borsa-kurallari.md) § Fiyat adımı |
| K-11 | doğrula | Pay piyasası günlük marj yüzdesi (±%10?) resmi kaynaktan | [borsa-kurallari](00-genel/borsa-kurallari.md) § Günlük fiyat limitleri |
| K-12 | doğrula | Seans saatleri (2016 kararı sonrası), gün ortası tek fiyat, VİOP saatleri, YİP takvimi | [borsa-kurallari](00-genel/borsa-kurallari.md) § Seanslar |

## Yolda / takip

| # | Tür | Konu | Ayrıntı |
|---|-----|------|---------|
| K-13 | iş | AlgoProd MAOrderSDK + handoff `add-order-sdk` branch'inde; merge edilince dokümanlar güncellenecek | [sistem-haritasi](00-genel/sistem-haritasi.md) § Emir yolları |
| K-14 | iş | Uptick geliştirmesi planlanıyor (şu an global bayrak, hep kapalı) | [borsa-kurallari](00-genel/borsa-kurallari.md) § Açığa satış ve uptick |
| K-15 | iş | Kaynak repolarda açık metin şifreler (ClickHouse, lisans, VERDA, DB, SSH) → Secrets'a taşınmalı. ⏸ sonra ele alınacak | — |
