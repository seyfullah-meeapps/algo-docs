---
kapsam: Eski meeapps-ai derslerinden yeni eğitim rotasına aktarım kapsamı ve önemli düzeltmeler
dogrulama: 2026-10-24
durum: taslak
---

# Aktarım ve revizyon kaydı

Kaynak: masaüstündeki `meeapps-ai/dersler/README.md`, `ders-00`–`ders-05` ve `ders-03b` dosyaları; rota için `meeapps-ai--calisma-listesi.md`. Yedi dersin tamamı okundu. Orijinaller eski klasörde korunuyor; bu klasör sohbet dökümünün birebir arşivi değildir. Tekrarlı anlatım, sohbet kapanış cümleleri ve kaynağı doğrulanmamış kesin iddialar çıkarılarak ders notları yeniden yazıldı. Yeni bir kod veya canlı borsa doğrulaması yapılmadı.

| Eski anlatım | Yeni dersteki düzeltme / dayanak |
|---|---|
| UI'ın gRPC kullanımı ve sabit port örnekleri | UI REST/WS kullanır; servis portları config'e bağlıdır. [Sistem haritası](../../00-genel/sistem-haritasi.md) esas alındı. |
| HFT'nin internal OUCH kullandığı, SDK geçişinin gelecekte olduğu; emirlerin hiçbir zaman gateway'den geçmediği | Referans sürümde MAOrderSDK ve handoff var. Öncesi gateway, sonrası doğrudan yol. [Emir yolları](../../00-genel/sistem-haritasi.md). |
| Sekiz bileşen bütün sistemi anlatıyor | AlgoProd ve diğer yardımcı bileşenler eklendi; servis ve SDK ayrıldı. |
| Her lot bir hisse; tek fiyat ölçeği örneği bütün ürünlere yayılıyor | Miktar/enstrüman lot bilgisi ve `decimalPrice` ayrı ele alındı. [ITCH ölçeği](../../10-servisler/itch-sdk/mesajlar-ve-emir-defteri.md). |
| Limit emir mutlaka bekler; piyasa emri hız garantiler | Bekleme TIF ve seansa bağlıdır; gerçekleşme garantisi çıkarıldı. |
| Defterde komşu dolu seviyeler her zaman bir tick uzakta; alış/satış asla çakışmaz | Boş fiyat seviyeleri ve toplama seansı ayrıldı. |
| Replace token'ını borsa atar; yeni token her durumda yeni emir ve sıra kaybıdır | İstemcinin replacement token'ı ile ACK takibi anlatıldı; sıra etkisi otomatik genellenmedi. [Emir yaşam döngüsü](../../10-servisler/hftsrvprod/emir-yasam-dongusu.md). |
| `profit` doğrudan gerçekleşmiş kâr, `net` her yerde aynı formül | Alan adından muhasebe anlamı çıkarılmadı; strateji ve UI metriği ayrıldı. [Strateji çekirdeği](../../10-servisler/hftsrvprod/strateji-cekirdegi.md). |
| Taban merge edilmemiş; OrderChase aktif strateji | Taban referans katalogda mevcut; OrderChase kullanılmıyor. [Katalog](../../20-stratejiler/README.md). |
| Uptick hisse bazında otomatik; bait 1 lot alışla kurala uygunluk sağlıyor | Classic'in config bayrağı ve bait satış/chase sırası ayrıldı; uygunluk garantisi kaldırıldı. [HFT Classic](../../20-stratejiler/hft-classic.md). |
| Bütün brüt takas emirleri koşulsuz engellenir; risk bilgisi yoksa her şey geçer | Yol ve config'e bağlı kontrol sınırları için güncel teknik belgelere yönlendirildi. [Risk](../../10-servisler/order-service/README.md). |
| Tavan ertesi gün mutlaka kazandırır; second rule güvenli çıkış sağlar; reverse kesin nötrler | Amaç ile gerçekleşme garantisi ayrıldı; dolum ve açık pozisyon riski korundu. |
| 2026 uptick kapsamı/tarihleri, takas süresi, emir/işlem oranı kesin güncel kuraldır | Yeniden resmi doğrulama yapılmadığından güncel kural olarak taşınmadı. Tarihli referans [borsa kuralları](../../00-genel/borsa-kurallari.md) dosyasında kalır. |

Bu farklar eski derslerin yeni kopyalarında giderildi. Yeni bir uygulama bug'ı keşfedilmiş sayılmadığından açık konu indeksine yeni K numarası eklenmedi. Bağlantılı teknik belgelerde bulunan mevcut adaylar derslerde gerektiğinde ele alınacak.

Eski listede ağ, protokoller, düşük gecikme, SDK'lar, motor, hub, UI ve uçtan uca akışlar vardı. Bunlar yeni rotada korunuyor; PM ihtiyacı nedeniyle strateji/test çalışmasının içine dağıtıldı. Önce bütün altyapıyı bitirip ancak sonra stratejiye geçme zorunluluğu kaldırıldı.
