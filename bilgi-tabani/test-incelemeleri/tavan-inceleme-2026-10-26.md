---
kapsam: Tavan sanity dosyasının kaynak incelemesi, test kapsamı ve doğrulama kaydı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: HftSrvProd
    branch: master
    commit: 052dd96
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-26
durum: taslak
---

# Tavan sanity incelemesi

Kullanıcının isteğiyle Tavan için ilk Excel sıfırdan oluşturuldu. Düzen HFT/Arbitraj ile aynı beş sayfayı ve test kayıt sütunlarını kullanır; senaryo içeriği Tavan kaynaklarından yazıldı. Aktif dosya [MTrader_Tavan_Sanity_Test.xlsx](../../testler/sanity/MTrader_Tavan_Sanity_Test.xlsx), açık kaynak adayları ve karar bekleyen konular [toplu issue taslağındadır](../../issues/sanity/tavan-toplu-issue.md). HFT ve Arbitraj Excel'leri değiştirilmedi.

## Kaynak kapsamı

26 Ekim origin fetch başarılı: HFT development `4275ccc`, master `052dd96`; GUI development `b0474c3`, main `6715182`; MAOrderSDK development `c2b5060`, main `d5adc6f`; order-service development `26e9a02`, master `298403b`; Algo-Setup development `cade7d0`. Fetch öncesi bu beş çalışma ağacında değişiklik yoktu. Referans uçları önceki kayıtla aynı; uygulama koduna müdahale edilmedi.

Bu incelemenin odağı yeni GUI development ve Tavan motorudur. SDK/order-service/config uçlarının bilinmesi tüm içeriklerinin yeniden incelendiği anlamına gelmez. Canlı müşteri binary/config'i, ITCH SDK dağıtım eşleşmesi, kurum risk politikası, gerçek ağ gecikmesi ve borsanın kabulü teyit edilmedi. Build veya manuel uygulama testi yapılmadı.

### Doğrudan okunan kaynaklar

- HFT: `src/Strategy/HftMaxPrice.cpp` ve `.h`; `setCommand`, `processItchEventTimed`, `shouldEnterPosition`, `shouldCancelPosition`, `shouldCancelPositionViaVolume`, `openPosition`, `closePosition`, `cancelAlreadyExecutedOrders`, `tryConsumePendingOpenAfterClose`, `topUpToTargetIfShort`, accept/fill/cancel/replace/reject callback'leri, `stop`, `restorePositionState`, `syncMomentumParams`, `maxOrderQtyAtTavan`.
- HFT wire: `src/Commands/MaxPriceCommand.cpp`, `MaxPriceStateCommand.cpp`; parse, snapshot ve yeni strateji varsayılanları.
- GUI: `app/components/dockview/max-price/maxPricePayload.ts`, `maxPriceSettings.ts`, `maxPriceLiveState.ts`; `app/components/dockview/MaxPriceTrackerForm.tsx`, `app/components/modals/MaxPriceSettingsModal.tsx`, `app/validations/strategySettings.schema.ts` ve `app/locales/tr/maxPrice.json`. Canlı satış durumu için `app/api/socket/CommandSocket.ts` alan eşlemesi de kontrol edildi.
- Mevcut KB: [Tavan](../20-stratejiler/tavan.md), [strateji çekirdeği](../10-servisler/hftsrvprod/strateji-cekirdegi.md), [emir yaşam döngüsü](../10-servisler/hftsrvprod/emir-yasam-dongusu.md) ve [risk](../10-servisler/order-service/risk.md). Bunların ortam iddiaları yeni test sonucu sayılmadı.

## Excel kapsamı

| Sayfa | Kapsam |
|---|---|
| Genel | G01–G08; sürüm, feed/snapshot, emir yolu, başlangıç durumu, kimlik, referans ayar, kanıt ve enstrüman değerleri |
| Tavan Senaryoları | 60 test: A giriş10, B çıkış10, C recover/restore8, D tolerans4, E süpürme/momentum7, F escape/tiering4, U arayüz12, O operasyon5 |
| Regresyon | R01–R20; açık kaynak adayları, ürün kararları, ortam teyitleri ve korunacak davranışlar |
| Parametre Eşleştirme | P01–P36; GUI etiketi, wire tipi/birimi, motor etkisi, kaynak sembolü ve ilgili test |
| Listeler | Sonuç, ortam, öncelik ve bulgu durumları; veri doğrulama listeleri |

Toplam **88 testin tamamı Test Edilmedi**. Gerçekleşen Sonuç, Kanıt ve Ekler boştur. Hazırlama tarihi 26.10.2026; test tarihi/kişi boş. Hazırlanmış senaryo, gerçekleştirilmiş test veya kullanıcı kabulü değildir.

RA, yalnız sentetik örnektir: 20 TL tavan, raw 20000/divider 1000 ve 200 TL hedef → 10 lot. Güncel piyasa fiyatı veya işlem tavsiyesi değildir. G08 gerçek enstrüman değerlerinin kaydını ister. RA toleransının açık/3 olması R01'deki sıfır sözleşmesini diğer testlerden ayırır; hata düzeltilmiş sayılmaz.

Beklenen Sonuç normal testlerde incelenen kaynak davranışını; açık bulgu testlerinde yeniden üretilecek ayrımı belirtir. Kullanıcının ürün hedefi ayrıca kararlaştırılmadan otomatik kabul ölçütü üretilmedi. Zamanlama, fazla callback, eksik gate ve yüksek tutar sınırları harness/replay ile sınanır; canlı hesapta hata enjeksiyonu öngörülmez.

## HFT'den taşınmayan varsayımlar

Yeni Tavan GUI'si snapshot olmayan satırı tekli başlatmaz. Toplu başlatmada yüksüz satırları atlar. Toplu ayar başarılı satırları durdurur; modal çalışan/farklı değerli satırlar için onay akışı içerir. Çalışan satır silinirken önce stop gönderilir, başarısızsa satır korunur. `Close_Position_First` toplu ayardan dışlanır. Stop emri iptal veya pozisyon kapatma sayılmaz.

Tavan'ın state mesajında pasif satış alanı `Has_Passive_Sell_Order`; yeni GUI aynı alanı okur. Eski GUI K-165 iddiası yeni Tavan Excel'ine gerçekleşmiş hata olarak taşınmadı. Replace geçmişinin yenilemede yüklenmemesi mevcut kullanıcı ürün kararı olarak korundu.

## İnceleme kararları

Yeni adaylar K-254–K-258; ayrıntıları toplu metinde. Önceden kayıtlı K-03, K-63 ve K-238 yeniden numaralanmadı. R15 abonelik yenileme şüphesi, R12/R13 ürün sözleşmesi ve R17 alias önceliği aynı toplu metinde sınırlı kapsamlarıyla tutulur.

Tavan KB'sindeki “%100 ve üzeri tam maksimum” genellemesi development için yanlıştı: pozitif yüzde, 100 üzeri dahil ölçeklenir; 0 tam maksimumdur. Aynı dosyanın branch notuyla çelişiyordu, düzeltildi. Tekrar giriş beklemesi de doğrudan header yolu için koşulsuz ön koşul olarak sunulmamalıdır; R03/K-255 nedeniyle daraltıldı. Canlı sonuç iddiası eklenmedi.

## Dosya doğrulaması

Artifact Tool ile oluşturma, yeniden hesaplama, formül hata taraması ve geçici sonuç değişiminde özet kontrolü yapıldı. G01 sonucu geçici Kısmen olduğunda Test Edilmedi 8→7 ve Kısmen 0→1 oldu; teslim öncesinde geri alındı. Beş sayfanın yedi aralığı görsel olarak incelendi. ZIP/XML, 88 benzersiz kimlik, 36 parametre, 4 filtreli tablo, açılır listeler, sabit başlıklar, özet formülleri ve boş kullanıcı alanları ayrıca doğrulandı.

İlk native Excel denemesi sandbox oturum hatası verdi. İzin sonrası dosya görünmez ve salt okunur açıldı; tam yeniden hesaplama Genel/Senaryolar/Regresyon için 8/60/20 toplam ve Test Edilmedi değerlerini doğruladı. Hazırlama tarihi Excel'de 26.10.2026 görünür; önizleme motoru özel tarih biçimini sayı olarak gösterdiği için native görüntü metni ayrıca kontrol edildi. Dosya Excel'den kaydedilmedi. Uygulama testi yoktur.
