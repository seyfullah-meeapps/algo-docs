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

## Oturum, şifre ve ret yolları — ikinci alt tur

İki kaynak repoda yeniden fetch/development pull başarılı, uçlar aynı. Bu alt tur `FIXManager::toAdmin/fromAdmin/createSessionSettings/resetSeqExpectedNo`, cancel-reject handler'ı; SDK karşılıkları ve `SdkSessionManager` şifre callback/persist akışını kapsar. Gerçek şifre kullanılmadı/değiştirilmedi.

| Alan | Master | Development |
|------|--------|-------------|
| Oturum ayarları | Reset, dictionary, heartbeat/reconnect alanları config'ten; pencere sabit 05:00–03:00 | Aynı temel eşleme ve sabit pencere korunur (K-125). Saat dilimi/QuickFIX runtime doğrulaması yapılmadı |
| Sequence dosyası | Başlangıçta expected seq alanına koşulsuz 1 yazmayı dener | `replay_from_seq=0` ise dokunmaz; diğer değeri dosyaya yazar |
| Şifre Logon alanları | Header'a mevcut 553/554; otomatik 925/1409 akışı yok | 925 adayı, 1409 sonucu, pending DB kaydı, otomatik yenileme/kurtarma akışları var |
| Admin Reject 35=3 | `fromAdmin` boş; emir callback'i yok | Replay takibi var, emir callback'i yok (K-120) |
| BusinessMessageReject 35=j | Özel handler yok | Özel handler yok; yerel QuickFIX FIX50SP2 varsayılan handler'ı boş (K-120) |
| Cancel-reject 35=9 | 434 cancel/replace türleri aynı bloğa düşer; önce ClOrdID, sonra OrigClOrdID kaydı aranır | Tür alanı yerine yine önce yeni token, sonra orijinal kayıt aranır; replace reddinde SDK yeni kaydı callback sonrası siler |
| “already cancelled” ret metni | Birebir metin eşleşmesiyle quantity=0 canceled üretir | Aynı metin eşleşmesi korunur; diğer cancel retleri rejected olur |

Ret metni ve kayıt eşleşmesine dayanan dönüşler, borsanın bütün hata çeşitlerinin kapsandığını kanıtlamaz. 35=3/35=j hakkında mevcut K-120 açık kalır; ayrı sorun açılmadı.

### K-233 — 1409'suz Logon'da SDK ve host şifre sonucu ayrışıyor

24 Ekim takip: gerçek SDK/host fonksiyon gövdeleri sahte oturum/DB adaptörleriyle derlenip çalıştırıldı; aşağıdaki ayrışma yerel handler düzeyinde gözlendi. Açık 1409=0/1 kontrol senaryoları doğru şifreyi promote etti. [Test kanıtı ve sınırları](../../_surec/dogrulama-sifre-akisi-2026-10-24.md); canlı QuickFIX/DB sonucu değildir.

`FixEngine::fromAdmin`, aday varken **Logon + status=-1** sonucunu başarı kabul eder; SDK belleğinde mevcut şifreyi adaya geçirip adayı temizler. `onFixPasswordChangeResult(-1)` host'a iletilir. Host `SdkSessionManager` ise -1'i yalnız “1409'suz logout/bilinmiyor” gibi ele alır: `armed` temizlenir, `live` eski şifrede kalır. Ardından `onUserConnected` pending kayıt nedeniyle promote worker'ı başlatır; `UpdateOrderUserPassword(username, live, "")` eski şifreyi yazıp pending'i temizleyebilir.

Statik senaryo: eski DB/live şifre A, pending/armed aday B → 1409'suz Logon → SDK canlı B, host canlı A → başarılı DB promote ile DB=A/pending boş. Böylece aday B'nin kalıcı kopyası kaybolabilir. Hem config hem auto-renew adayında geçerli olabilir. BIST'in bu cevap biçimini üretip üretmediği, gerçek callback sırası ve DB sonucu entegrasyon testinde denenmedi; adayın prod'da kaybolduğu iddia edilmez. Alan yokluğu ile parse edilemeyen 1409 kodda aynı -1 sonucuna gider.

### K-234 — manuel config adayı DB onayı olmadan arm ediliyor

24 Ekim takip: başarısız sahte pending write sonrası gerçek armFromConfig gövdesi adayı döndürdü; çözülmemiş pending kontrolü yeni adayı engelledi. Aynı [yerel doğrulama](../../_surec/dogrulama-sifre-akisi-2026-10-24.md) beş senaryo içerir; otomatik renew bütünü çalıştırılmadı.

`armFromConfig` pending yazma RPC'si başarısız olsa da adayı döndürür; `MAOSdkManager` bunu SDK kullanıcısının `fix_new_password` alanına koyar. Otomatik `RenewExpiredFixPassword` ise DB yazımı başarısızsa arm etmeden döner. Bu nedenle crash-safe invariant manuel yola koşulsuz genellenemez. Manuel aday kalıcı config'te bulunabilir; bulgu her kopyanın kaybolması değil, DB password/pending ikilisinin kabul edilen şifreyi kapsadığı garantisinin bozulmasıdır. Kaynak kod değiştirilmedi.

## Kapsam ve kalanlar

2026-10-23 iki klonda origin fetch ve development pull --ff-only başarılı, uçlar değişmedi. İncelenenler: master FIXManager/OrderUtility/OrderManager fill ve replace yolları; development MAOSdkManager callback/restore; SDK FixEngine replay/ER ve FixCodec encode/decode. Kaynak çalışma ağaçları değiştirilmedi. Build, QuickFIX entegrasyon testi ve canlı emir denemesi yapılmadı.

İkinci alt turla temel şifre/config/ret yolları da karşılaştırıldı. FIX için planlanan statik ikinci tur tamamlandı; QuickFIX entegrasyonu, gerçek exchange ret çeşitleri ve prod config/binary doğrulaması açık sınırdır. İlk belgelerdeki açık konular geçerlidir. Sıradaki strateji kod incelemesidir.
