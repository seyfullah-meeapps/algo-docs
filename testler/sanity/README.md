---
kapsam: Strateji bazlı manuel sanity testleri, Excel dosyaları ve kod inceleme kayıtlarının giriş noktası
dogrulama: 2026-10-27
durum: taslak
---

# Sanity testleri

Bu klasörde dört aktif strateji Excel'i bulunur. Excel'ler manuel test kayıtlarıdır; otomatik test paketi değildir. Sonuçlar yalnız çalıştırılmış testin kanıtıyla güncellenir. Teknik incelemeler [bilgi tabanında](../../bilgi-tabani/test-incelemeleri/README.md), issue taslakları [issues/sanity](../../issues/sanity/README.md), eski Excel sürümleri [arşivde](../../arsiv/README.md), Mate örnekleri [referanslar](../referanslar/mate/README.md) altında tutulur.

**Açık teslim kopyası:** Kullanıcının düzenliyor olabileceği Arbitraj dosyası `outputs/arbitraj-sanity-20261027/` içinde açık bırakıldı. Bu kopya kapandıktan sonra değişiklikleri karşılaştırılmadan silinmez veya buradaki aktif Excel'in üzerine yazılmaz. Klasör düzenlemesinde Excel içerikleri değiştirilmedi.

| Strateji | Aktif dosya | Kapsam |
|---|---|---|
| Arbitraj | [Excel](MTrader_Arbitraj_Sanity_Test.xlsx) | Aktif sürüm 3.0; 5 ön koşul, 32 ana sanity, 15 genişletilmiş kontrol; toplam 52 |
| HFT | [Excel](MTrader_HFT_Sanity_Test.xlsx) | Yeni GUI development; sürüm 1.2. 8 ön koşul, 57 senaryo, 33 regresyon; tamamı Test Edilmedi |
| Tavan | [Excel](MTrader_Tavan_Sanity_Test.xlsx) | Yeni GUI development; sürüm 1.0. 8 ön koşul, 60 senaryo, 20 regresyon, 36 parametre; 88 testin tamamı Test Edilmedi |
| Taban | [Excel](MTrader_Taban_Sanity_Test.xlsx) | Yeni GUI development; sürüm v1.0. 8 ön koşul, 52 senaryo, 20 regresyon, 26 parametre; 80 testin tamamı Test Edilmedi |

Arbitraj ve HFT Excel revizyonları, Tavan ve Taban'ın ilk dosya hazırlıkları tamamlandı. Kayıtlar: [Arbitraj incelemesi](../../bilgi-tabani/test-incelemeleri/arbitraj-inceleme-2026-10-26.md), [HFT incelemesi](../../bilgi-tabani/test-incelemeleri/hft-inceleme-2026-10-26.md), [Tavan incelemesi](../../bilgi-tabani/test-incelemeleri/tavan-inceleme-2026-10-26.md), [Taban incelemesi](../../bilgi-tabani/test-incelemeleri/taban-inceleme-2026-10-26.md). Kod incelemesi ile test sonucu ayrıdır. Diğer stratejilere otomatik geçilmez.

## Arbitraj güncel sanity kapsamı

Güncel sürüm 3.0, [aktif Excel](MTrader_Arbitraj_Sanity_Test.xlsx) içindedir. `outputs/` altındaki teslim kopyaları yereldir ve Git ile paylaşılmaz.

Excel teknik olmayan testçiler içindir; kod/repo referansları ve sorun takibi içermez. Mate örneklerinin yaklaşımı ve mevcut tasarım korunur. Genel sayfasında 5 ön koşul, Arbitraj Senaryoları sayfasında 32 ana sanity ve 15 genişletilmiş kontrol bulunur: toplam 52 test. Ayar Rehberi 36 ayar/hazırlık açıklaması içerir. Listeler gizlidir. Sorunların tek takip adresi [Arbitraj issue dosyasıdır](../../issues/sanity/arbitraj-toplu-issue.md).

Çift Vade ve Çift Vade Faiz için çarpan varsayılanı 1; kullanıcı değiştirebilir. Limitler boş/sıfır kaydedilebilir; başlangıç bitişten sonraysa kaydetme engellenir. Fonlama maliyeti yalnız tam sayı girilir. Farklı dayanak/vadeli ilk eklemede seçilir; ayarlarda dayanak alanı pasiftir. Bu davranışlar kullanıcı kararlarına dayanır; bu düzenlemede yeni kod veya canlı test doğrulaması yapılmadı. Kalan senaryoların mevcut sonuçları ve kullanıcı kanıtları korunur.

## 26 Ekim — Taban ilk sürüm

Kullanıcının talebiyle ilk Taban dosyası kaynak koddan hazırlandı. Kapsam ve doğrulama [Taban incelemesinde](../../bilgi-tabani/test-incelemeleri/taban-inceleme-2026-10-26.md), açık adaylar [Taban toplu issue taslağında](../../issues/sanity/taban-toplu-issue.md). K-259–K-262 eklendi; mevcut konu numaraları tekrar kullanılmadı. Sekmeler, sonuç listeleri ve kanıt düzeni önceki dosyalarla aynı. Kullanıcı sonuçları boş; uygulama testi yapılmadı. Özet/girdi/paket/görsel kontrolleri ve native Excel salt okunur tam hesaplama geçti. Diğer Excel dosyaları değişmedi.

## 26 Ekim — Tavan ilk sürüm

Tavan kaynak kodu, yeni GUI, parametre birimleri, canlı durum ve emir callback yollarından sıfırdan hazırlandı. Beş sayfanın düzeni HFT/Arbitraj ile uyumlu; içerik Tavan'a özgüdür. Açık adaylar ve ürün/ortam ayrımları [Tavan toplu issue taslağında](../../issues/sanity/tavan-toplu-issue.md). K-254–K-258 eklendi; K-03/K-63/K-238 tekrar numaralanmadı. Tüm kullanıcı gözlem/kanıt alanları boştur; test yapılmış izlenimi verilmedi.

Artifact Tool hesaplama ve geçici girdi değişimi, yedi görsel aralık, ZIP/XML/88 kimlik/36 parametre/4 filtreli tablo/açılır liste/sabit başlık ve boş alan kontrolleri geçti. Native Excel görünmez ve salt okunur açıldı; tam hesaplama 8/60/20 toplam ve Test Edilmedi sayısını, hazırlama tarihi görüntüsünü doğruladı. HFT/Arbitraj dosyaları değişmedi; build/canlı strateji testi/uzak issue/push yok. Sonraki adım kullanıcının ürün kararları veya manuel test sonuçlarıdır.

## 26 Ekim — HFT revizyonunun tamamlanması

HFT için [toplu issue taslağı](../../issues/sanity/hft-toplu-issue.md) hazırlandı; uzak issue açılmadı. Altı eski iddia kapsam dışına ayrıldı, ürün/ortam teyitleri kesin hatalardan ayrıştırıldı. R02 kâr al alan sözleşmesi K-252, R01 miktar hesabı adayı K-253 olarak indekslendi; mevcut K-236/K-237 yeniden numaralanmadı. Ayrıntı ve kaynak kapsamı HFT inceleme kaydındadır.

Excel ZIP/XML, 98 benzersiz test kimliği, mevcut sonuç/gerçekleşen sonuç/kişi-tarih ve açılır liste koruması kontrol edildi. Artifact Tool yeniden hesaplaması, hata taraması, geçici sonuç değişiminde özetin güncellenmesi ve beş sayfadan altı aralığın görsel incelemesi geçti. Bu devamda native Excel açılışı ve uygulama testi yapılmadı. Önceki kopya `arsiv/test-yedekleri/2026-10-26-hft-inceleme/` içinde. Arbitraj dosyası değişmedi.

## Güncel ürün davranışı

Açık Arbitraj bulgularının tek issue metni [arbitraj-toplu-issue.md](../../issues/sanity/arbitraj-toplu-issue.md). Kod adayları, önceki kaynak notları, kullanıcı test gözlemleri ve ürün/operasyon kapsamı bekleyen noktalar dayanakları belirtilerek burada birleştirilir. Eksik test kanıtı tek başına yeni bug sayılmaz. F10 panel kapsamı ve abonelik ayrımı toplu metinde açıklanır; ikinci bacakta fiili veri kaybı henüz doğrulanmadı. Kullanıcının panel gözlemi issue dosyasında yer alır.

Değiştirildi/replace kayıtları, işlem hacmi ve yeniden yükleme yükü nedeniyle sayfa yenilenince tekrar yüklenmez. Bu ürün davranışı hata değildir. Açık sorun metninde yalnız güncel problemler bulunur; giderilmiş konular kapanış günlüğü olarak tutulmaz. Teknik bulgular Excel'e taşınmaz.

Excel açıklamalarında belirli branch/commit kapsamı korunur. Yeni GUI `development`, eski GUI `main`; motor referansı `development`, prod kaynak farkı `master`. Kaynak davranışı ile dağıtılmış binary/config aynı kabul edilmez. Genel teknik kaynak [strateji kataloğudur](../../bilgi-tabani/20-stratejiler/README.md); yeni sorunlar [açık konu indeksinden](../../issues/ACIK-KONULAR.md) izlenir.
