# CHANGELOG

Her güncelleme oturumu bir kayıt. En yeni en üstte.

## 2026-10-22 — Çelişki doğrulaması ve borsa kuralları

Kaynak repoların HEAD'leri manifest'teki doğrulama commit'leriyle aynı (değişiklik yok). Düzeltmeler bu commit'lere karşı kodla doğrulandı.

- **Toplu emir yolu:** trade-data-app → order-service RPC'si `SendOrder`, `SetOrders` değil. Go sarmalayıcının adı yanıltıcı. order-service emirleri `BulkInsert*Order` ile DB'ye yazar (sistem haritası, akışlar, order-service, trade-data-app).
- **Sabah emri fazla kopya iptali** (`CancelRepeatedOrders`) order-service'e yazıldı.
- **UI WebSocket'leri:** 6 merkezi socket ↔ feed eşlemesi; `passive-orders` yalnız pasif emir paneli.
- **performance-sdk:** AlgoProd'un metrikleri düzeltildi (bağlantı metriği yok).
- **PTRM:** AlgoProd `-850064`'ü tanımıyor (VWAP, Arbitraj). Arbitraj'ın PTRM'de durması ve `-420131` eklendi.
- **Uptick:** HFT'de enstrüman bazlı değil, global config bayrağı (`uptickRule`); `uptickEnabled` kullanılmıyor.
- **Tavan:** `Profit_Percentage` kullanılmıyor.
- **trade-data-app VİOP partition'ları:** Müşteri config'lerinde sayılar farklı. Piramit_Algo 6, A1 ve Alnus-Algo 4, diğerlerinde VİOP yok; HFT config'leri hepsinde 6.
- **Algo-Setup kurulum matrisi branch'e göre değişiyor:** Kanjo yalnızca `main`'de (prod). `Seker` (development) ve `Oyak` (main) config klasörleri hiçbir matriste yok (❓).
- **Piramit_Algo eski GUI'de:** Son başarılı deploy 2026-04-24'te `preprod`'dan (GitHub Actions run geçmişinden çıkarım).
- **Uptick'in çalışma anında açılma yolu yok:** Bütün müşteri config'lerinde `uptickRule = false`.
- **Kullanıcı beyanları:** Sepet arbitraj henüz kullanılmıyor; Warrant-Selector Varant Toplu'ya yüklenen CSV'yi üretiyor; Global ve Marbas eski GUI'de.
- `00-genel/borsa-kurallari.md` yazıldı (`bos` → `taslak`): fiyat adımı, limitler, seanslar, uptick, ret kodları. Her bölümde "kodda" ve "borsada (referans)" ayrımı var. Borsa sitesine bu ortamdan erişilemedi; dış bilgiler arama sonuçlarından derlendi, kesinleşmeyenler ❓.

## 2026-10-22 — İlk sürüm (devam ediyor)

- Repo oluşturuldu; eski `meeapps-ai` bilgi tabanının yerini alır.
- Yapı agent-odaklı kuruldu: `AGENTS.md`, `manifest.yaml`, frontmatter kuralları.
- Tüm repolar referans branch'lerinden çekildi; doğrulama commit'leri `manifest.yaml`'da.
- Warrant Advanced (Varant Toplu) 2026-10-19'da HftSrvProd, order-service, network-sdk ve ouch-sdk development'a merge edildi; dokümanlar merge sonrası haline göre yazılıyor.
