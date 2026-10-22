# CHANGELOG

Her güncelleme oturumu bir kayıt. En yeni en üstte.

## 2026-10-22 — trade-data-app derinleştirme

Kaynak: trade-data-app `1cca9a8` (değişmedi).

- `10-servisler/trade-data-app/` alt dosyalara bölündü. README artık giriş ve indeks; ayrıntılar: `api.md`, `veri-akisi.md`, `sema.md`, `entegrasyonlar.md`, `config.md`.
- **README'deki düzeltmeler:**
  - WS ve REST'te process içi TLS yok; sertifika anahtarları okunmuyor.
  - TradeVerifier her snapshot'ta değil, bootstrap bildirimiyle yalnızca bir kez tekrar uygulanıyor.
  - Emir geçmişi order-service yeniden bağlanınca sıfırlanıyor.
  - LimitControlService'i order-service çağırmıyor; yalnızca RiskManagerService'i çağırıyor.
  - AlgoProd `FetchOrders` kullanmıyor; onun yerine `FetchAllUniqueKeys` ve `UpdateExtSettings` kullanıyor.
  - `logLevel` üst seviyede etkisiz.
- **Tablo listesi:** `Instrument_Futures` ve `Volatility` eklendi. Şema yönetimi: migration yok; `scripts/sql/` elle çalıştırılıyor. K-08 kapandı (kolonlar koddan `sema.md`'de; tipler ve unique key'ler K-39).
- **`getApplicationFromStrategyType`:** Varant Toplu eksik değil. Gerçek fark iki kopyanın tip 1 ve 12'de ayrışması (`20-stratejiler/README.md` düzeltildi).
- **`fon-takibi.md`:** BYF sepeti DB'ye değil belleğe yazılıyor.
- **K-02:** ITCH config'i `Part` 5–6'yı Partition1'e düşürüyor.
- **Yeni açık konular:** K-16–K-43.

## 2026-10-22 — ❓ temizliği, sözlük, manifest

Commit'ler değişmedi; hepsi manifest'teki doğrulama commit'lerine karşı.

- **Kullanılmayan alanlar** (parse edilip geri yollanıyor, karar vermiyor):
  - HFT Classic `Start_Time`/`Stop_Time`
  - Fon Takibi `Byf_Package_Limit`
  - VWAP `Trade_Pay_Limit`/`Trade_Vade*_Limit`
  - Arbitraj `First/Second/Third_Future`
- **Arbitraj `Optional_Underlying`:** Açıkken komuttaki `Underlying_Multiplier` kullanılıyor; iki vadeli tiplerde çarpan 1.
- **Sepet arbitraj wire tipi:** `Arbitrage` (6), doğrulandı.
- **Tavan saat alanları:**
  - `End_Time` okunuyor, `Stop_Time` olarak geri yollanıyor.
  - `getDefaultSettings`'in 600/1200 varsayılanı UI'dan geri gidebilir; ❓ test edilmedi.
- **order-service:**
  - `eveningSessionStart` bir gönderim akışı değil: o saatten sonraki emirlere `OffHours` bayrağı koyuyor.
  - EVENING emirlerini teorik akışı gönderiyor.
  - Lisans kontrolü kapalı.
  - YİP örnek seans saatleri eklendi.
- **Varant Toplu:** Eski GUI'de yok. Önceki "`VarantTopluTrackerForm`" iddiası yanlıştı.
- **VWAP Overall:** Yeni GUI'de karşılığı yok.
- **itch-sdk:**
  - Hat seçimi açılışta ve process genelinde yapılıyor; Glimpse bağlantısı başarısız olursa ikincile tek yönlü geçiliyor.
  - `partId` VİOP için 5–8 aralığını varsayıyor. HFT'nin 6 VİOP partition'ıyla olası çakışma, ertelenen VİOP konusuna eklendi.
- `00-genel/sozluk.md` yazıldı (`bos` → `taslak`). Yalnızca mevcut dokümanlardan derlendi, terimler kaynaklarına linkli.
- `manifest.yaml`: 15 reponun `durum: bos` alanı `taslak` yapıldı (dokümanların frontmatter'ıyla uyumlu).

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
- **Algo-Setup kurulum matrisi branch'e göre değişiyor:** Kanjo yalnızca `main`'de (prod). `Seker` (development) ve `Oyak` (main) config klasörleri hiçbir matriste yok; ikisi de eski müşteri (kullanıcı beyanı).
- **Piramit_Algo eski GUI'de:** Son başarılı deploy 2026-04-24'te `preprod`'dan (GitHub Actions run geçmişinden çıkarım).
- **Uptick'in çalışma anında açılma yolu yok:** Bütün müşteri config'lerinde `uptickRule = false`. İlan günlerinde genelde strateji çalıştırılmıyor; uptick geliştirmesi planlanıyor (kullanıcı beyanı).
- **A1 / Alnus-Algo VİOP 4 partition:** İncelemesi ertelendi.
- **Kullanıcı beyanları:** Sepet arbitraj henüz kullanılmıyor; Warrant-Selector Varant Toplu'ya yüklenen CSV'yi üretiyor; Global ve Marbas eski GUI'de.
- `00-genel/borsa-kurallari.md` yazıldı (`bos` → `taslak`): fiyat adımı, limitler, seanslar, uptick, ret kodları. Her bölümde "kodda" ve "borsada (referans)" ayrımı var. Borsa sitesine bu ortamdan erişilemedi; dış bilgiler arama sonuçlarından derlendi, kesinleşmeyenler ❓.

## 2026-10-22 — İlk sürüm (devam ediyor)

- Repo oluşturuldu; eski `meeapps-ai` bilgi tabanının yerini alır.
- Yapı agent-odaklı kuruldu: `AGENTS.md`, `manifest.yaml`, frontmatter kuralları.
- Tüm repolar referans branch'lerinden çekildi; doğrulama commit'leri `manifest.yaml`'da.
- Warrant Advanced (Varant Toplu) 2026-10-19'da HftSrvProd, order-service, network-sdk ve ouch-sdk development'a merge edildi; dokümanlar merge sonrası haline göre yazılıyor.
