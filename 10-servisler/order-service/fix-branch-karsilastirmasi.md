---
kapsam: Legacy master FIXManager ile development MAOSdkManager ve SDK FIX dönüş/replay yollarının karşılaştırılması
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: order-service
    branch: master
    commit: 298403b
  - repo: MAOrderSDK
    branch: development
    commit: a788782
dogrulama: 2026-10-23
durum: taslak
---

# FIX branch karşılaştırması

İnceleme kaynak branch davranışını anlatır; hangi binary/config'in prod'da bulunduğu bu karşılaştırmadan çıkmaz. Development host ayrıntısı [SDK ve oturumlarda](sdk-ve-oturumlar.md), SDK decode/replay mekanizması [FIX belgesinde](../maordersdk/fix.md). Aynı bilgi burada yeniden tarif edilmez.

## Dönüş ve replay farkları

| Alan | Master legacy FIXManager | Development host + SDK |
|------|--------------------------|-------------------------|
| Gelen uygulama mesajı | `fromApp` doğrudan `crack` eder; replay bayrağı üretmez | `FixEngine::track_replay`, thread-local işaret ve callback `is_replay` alanı |
| Fill eşlemesi | `entered_orders` içinde ClOrdID bulunmalı; yoksa log ve olay düşer | SDK bilinmeyen ClOrdID'yi ER'den adopt edebilir; fakat host callback'i ayrıca kendi kayıt bağlamını arar, bulamazsa düşürür |
| Fill dedup | İncelenen ER fill handler'ında olay anahtarıyla dedup yok | Host `token:match_id:timestamp` kümesiyle aynı süreçte tekrar teslimi düşürür |
| Pozisyon yazma | Eşleşen her fill `InsertPositionToDatabase` kuyruğuna konur | `is_replay=true` ise pozisyon yazılmaz; FIX canlı fill'i OUCH açılış penceresinden bağımsız yazılır |
| Risk bakiye güncellemesi | SDK `apply_balance` bayrağı yok; development callback kuralı buraya taşınamaz | `OnOrderExecuted(apply_balance=!msg.is_replay)`; replay'de rezervasyon çözülür, bakiye yeniden uygulanmaz |
| Giden PossDup uygulama mesajı | `toApp` `DoNotSend` atar | Aynı davranış korunur; gelen rapor dedup'ıyla karıştırma |
| Fill fiyatı | Payda Price → `Price`; LastPx → `LastPrice`. VİOP LastPx kolu `LastPrice` yerine `Price`'ı ×100 yazar, `LastPrice` ×1000 kalır | SDK LastPx'i tercih eder, yoksa Price; market price_divider ile raw'a çevirir. Host iki alana da bu fill fiyatını yazar |

SDK `is_replay`, her PossDup mesaj için koşulsuz true değildir: `track_replay` aktif logon gap penceresinde true döndürür. Bu pencere dışındaki resend, `is_replay=false` olabilir; süreç içi host dedup anahtarı ayrıca önemlidir. “Development bütün geçmiş fill'lerini mutlaka tanır” sonucu çıkarılmaz.

## K-121 legacy kodda da mevcut

Legacy `Utilities/OrderUtility.h::ConvertFixReplaceOrderToOrderCancelReplaceRequest` miktar replace'inde tag 38'e `istenen kalan + executedQuantity` yazar. `FIXManager` yeni token kaydına ise yalnız istenen kalan miktarı koyar. Sonraki fiyat replace'i tag 38'i bu kayıt miktarından alır. SDK `FixEngine::replaceOrder` ve `FixCodec::encode_replace_order` aynı ayrımı korur.

Statik örnek: 100 lot emir, 20 lot dolum → 50 lot kalan isteği tag 38=70 gönderir, replacement kaydı quantity=50 olur → sonraki yalnız fiyat replace'i tag 38=50 gönderir. Wire sayı farkı iki kaynakta da vardır; exchange'in bunu nasıl uyguladığı canlıda denenmedi. Mevcut [K-121 ayrıntısı](../maordersdk/fix.md#10-şüpheli) geçerlidir; ayrı sorun numarası açılmadı.

## Şüpheli

**K-232 — legacy FIX geçmiş fill'in yeniden yazılması:** Master `FIXManager::fromApp` gelen PossDup için replay filtresi kurmaz. `ExecutionReport` FILL/PARTIAL_FILL/TRADE handler'ı ClOrdID kaydını bulursa callback, pozisyon kuyruğu ve executed listesi yan etkilerini yeniden çalıştırır. `OrderManager::InsertPositionToDatabase` yalnız kuyruğa koyar; async tüketici `SetPosition` üzerinden DB istemcisine ve hesap-strateji pozisyonuna gider. İncelenen bu yolda uygulama düzeyinde replay/dedup koruması yoktur.

Koşul: QuickFIX'in geçmiş ExecutionReport'u handler'a yeniden teslim etmesi ve host kayıt eşleşmesidir. Gerçek oturum sequence/reset ayarları, QuickFIX'in teslim kararı ve uzak veri servisinin tekrar davranışı bu statik adaydan kanıtlanmaz. Prod'da çift pozisyon oluştuğu iddia edilmez. Development'ın replay bayrağı/host dedup koruması master'a genellenmemelidir.

## Kapsam ve kalanlar

2026-10-23 iki klonda origin fetch ve development pull --ff-only başarılı, uçlar değişmedi. İncelenenler: master FIXManager/OrderUtility/OrderManager fill ve replace yolları; development MAOSdkManager callback/restore; SDK FixEngine replay/ER ve FixCodec encode/decode. Kaynak çalışma ağaçları değiştirilmedi. Build, QuickFIX entegrasyon testi ve canlı emir denemesi yapılmadı.

Şifre yenileme, FIX oturum config'leri, cancel-reject çeşitleri ve admin/business reject yollarının tamamı bu alt turla yeniden doğrulanmış sayılmaz. İlk belgelerdeki açık konular geçerlidir. Strateji incelemesinden önce kalan FIX yolları kontrol edilecek.
