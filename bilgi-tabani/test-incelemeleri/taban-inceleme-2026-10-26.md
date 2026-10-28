---
kapsam: Taban sanity Excel kaynak kapsamı, test tasarımı ve doğrulama kaydı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-26
durum: taslak
---

# Taban sanity incelemesi

Kullanıcının Tavan sonrası Taban talebiyle [ilk Excel](../../testler/sanity/MTrader_Taban_Sanity_Test.xlsx) oluşturuldu. Beş sekme: Genel, Taban Senaryoları, Regresyon, Parametre Eşleştirme, Listeler. Sürüm v1.0; 8 ön koşul, 52 senaryo, 20 regresyon ve 26 parametre. 80 testin tamamı **Test Edilmedi**; kişi/test tarihi, gerçekleşen sonuç ve kanıt alanları boş. Önceki üç stratejinin dosyaları değiştirilmedi.

## Kaynak ve kapsam

26 Ekim origin fetch başarılı: HftSrvProd development `4275ccc`, master `052dd96`, preprod `1d12633`; yeni GUI development `b0474c3`, main `6715182`, preprod `eff3d37`; MAOrderSDK development `c2b5060`; order-service development `26e9a02`; Algo-Setup development `cade7d0`. Kaynak uçları ile çalışan binary/config aynı kabul edilmez. Fetch'te görülen ilgisiz feature branch değişimi bu kapsama alınmadı.

Yerel kök `C:/Users/Seyf/algo-workspace/`. İncelenen temel kaynaklar:

| Repo | Yol / sembol | Excel kapsamı |
|---|---|---|
| HftSrvProd | `src/Strategy/HftMinPrice.cpp`, `.h`; `setCommand`, `processItchEventTimed` | Başlatma, zaman, snapshot, state |
| HftSrvProd | Aynı dosya; `shouldEnterPosition`, `enterTriggerQty`, `openPosition`, `applySecondaryEnterLot` | A01–A12, E01–E05 |
| HftSrvProd | Aynı dosya; `shouldEscapePosition`, `closePosition`, `scheduleReCloseCheck`, `recheckEscape` | C01–C12 |
| HftSrvProd | Aynı dosya; `shouldTopUpPosition`, `topUpPosition`, `manualCancelOnReBreak`, `setTabanState` | D01–D06 |
| HftSrvProd | Aynı dosya; `maybePlaceAggregateAutoSell`, `computeAutoSellPriceAboveTaban`, `executeOrder`, `deleteOrder`, `updateQtyForFatherOrderRef` | B01–B06, R05/R06/R08/R12/R15 |
| HftSrvProd | `src/Commands/MinPriceCommand.cpp`; varsayılanlar ve `toClientMessage` | P01–P24 wire/geri dönüş |
| mtrader-trade-ui | `app/components/dockview/min-price/minPriceSettings.ts`, `minPricePayload.ts` | Modlar, birimler, toplu alanlar, tolerans |
| mtrader-trade-ui | `app/components/dockview/MinPriceTrackerForm.tsx`; `app/validations/strategySettings.schema.ts` | U01–U05, snapshot kapısı, validasyon |

Önceki branch/feed/manuel rota bağlamı [Taban KB](../20-stratejiler/taban.md) üzerinden alındı; bunlar bu tur yeni canlı doğrulama değildir. K-164, K-212, K-235, K-238 yeniden numaralanmadı. U06/R17 feed anlamı, R16 manuel emir eşleşmesi, R18 master farkı kendi teyit sınırını taşır.

## Tasarım kararları

- Referans RB sentetiktir: taban20 TL/raw20000/divider1000, hedef200 TL/10 lot, giriş100 lot, kaçış200 lot, tolerans3, cooldown0 sn, reClose1 sn, otomatik kâr2 kademe. Gerçek fiyat/limit/tick G08'e kaydedilir.
- Giriş IOC alış; kâr ve kaçış satışı DAY limit. Pasif satış gönderimi fill veya tam kapanış değildir. Yeniden kırılma yeni alış yapmaz; otomatik modda taban satışını yukarı taşır, manuelde iptal eder.
- Tavan'daki father-ref alt taşması Taban'a kopyalanmadı: Taban clamp düzeltmesini R12 korur. Sıfır-fill reseti, toplu satış ailesi, callback kaçış kontrolü ve manuel cancel yarışı da korunacak regresyonlardır.
- `Close_Position_First` tekli GUI alanıdır. Motor bu değeri atadıktan hemen sonra `restorePositionState` açık durumu bakiye/pasif satıştan yeniden belirler; doğrudan anlık tasfiye çağrısı diye anlatılmadı. O04 bu sınırı açıkça kontrol eder.
- Pending callback 2ms TTL, running, flat, satış başının tabanda kalması ve toleransı kontrol eder; normal lot/cooldown filtresinin tamamını yeniden çalıştırdığı iddia edilmedi.
- Kaynak adayları [tek toplu issue taslağında](../../issues/sanity/taban-toplu-issue.md); regresyon Durum etiketi ile manuel Sonuç ayrı. Ürün kararları ve ortam teyitleri kesin hata yapılmadı. Finish_With_Sell ve eski reClose lot/yüzde alanları R19'da kapsam dışı.

## Dosya doğrulaması

Artifact Tool ile özetler yeniden hesaplandı; formül hata taraması sonuç vermedi. Genel B20 geçici Kısmen yapıldığında özet7 Test Edilmedi/1 Kısmen oldu; son kayıttan önce geri alındı. ZIP/XML bütünlüğü, 80 benzersiz test kimliği, 26 parametre, 4 filtreli tablo, açılır listeler, sabit başlıklar ve boş kullanıcı alanları doğrulandı. Beş sekmeden yedi aralık görsel incelendi; liste etiketi kontrolünde yakalanan yazım hatası teslim öncesi düzeltildi.

Native Excel görünmez/salt okunur açılışı ve tam hesaplama8/52/20 toplam ile Test Edilmedi sayılarını doğruladı; tarih26.10.2026 ve sürümv1.0 doğru görüntülendi. Artifact render hazırlama tarihini46321 seri değeriyle gösteriyor; hücre gerçek sayısal tarih ve `dd.mm.yyyy` formatındadır. Render/export işlemi başarı çıktısından sonra süreç çıkış kodu1 verdi; bağımsız ZIP/XML ve native Excel açılışı dosya bütünlüğünü doğruladı.

Build, harness çalıştırması, canlı strateji testi veya uzak issue/push yapılmadı. Kod bulguları uygulama testinden geçmiş sayılmaz. Sonraki adım kullanıcı incelemesi/ürün kararı veya manuel test kanıtıdır.
