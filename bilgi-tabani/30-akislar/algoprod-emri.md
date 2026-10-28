---
kapsam: AlgoProd strateji emri uçtan uca — ITCH kararından ouch-sdk/MARpc ve order-service üzerinden BIST'e, callback/userbook dönüşünden hedge, paket kalıcılığı ve GUI'ye
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading
    branch: master
    commit: aa150ee
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-23
durum: taslak
---

# AlgoProd strateji emri

Referans `development 0dc32a7`'dir. Bu sürümde **bütün emirler order-service'ten geçer**; HFT'deki doğrudan MAOrderSDK yolu ve OUCH handoff yoktur. `add-order-sdk` ayrı, merge edilmemiş geliştirmedir; ayrıntı [emir-yolu § 11](../10-servisler/algorithmic-trading/emir-yolu.md#11--add-order-sdk-7d7f705-2026-10-15-merge-edilmedi)'dedir.

Bu dosya ortak taşıma sırasını anlatır. Karar kuralları [Arbitraj](../20-stratejiler/arbitraj.md), [VWAP](../20-stratejiler/vwap.md), [Fon Takibi](../20-stratejiler/fon-takibi.md)'ndedir; SDK modelleri, token ve ret ayrıntıları [AlgoProd emir yolu](../10-servisler/algorithmic-trading/emir-yolu.md)'ndadır. GUI'den serbest emir için [manuel emir](manuel-emir.md#4-algoprod-dalı-strategy_type-1-6-7-10).

## 1. Ön koşullar ve karar

1. Açılışta ITCH hazır olur; `OuchManager::start` order-service'e MARpc login yapar.
2. Başarılı login sonrası `createUserbooks` strateji kayıtlarını alır, `isStrategyInfoMapFilled=true` olur; `getAllOrders` günün olaylarını userbook'lara işler. Stratejiler bundan sonra kurulur; açılış replay'i henüz olmayan strateji subscriber'larına iletilmez.
3. Operatör stratejiyi [strateji başlatma akışı](strateji-baslatma.md) ile başlatır. Strateji kendi ITCH ve emir olayı aboneliklerini kurar.
4. Arbitraj `doPeriodicChecks` worker havuzunda fiyat/parametreleri kontrol eder; uygun koşulda önce türev emrini üretir. ⚠ master'da farklı: arbitraj kendi thread'inde çalışır. VWAP ve Fon Takibi kendi döngülerini kullanır; bunları aynı worker modeliyle varsayma.


## 2. Gönderim zinciri

```text
Strateji → OuchManager::send → sendOrder/sendTransaction
         → ouchSDK::enterOrder → network-sdk gönderim kuyruğu
         → MARpc TCP → order-service OrderServer::RequestReceived
         → hesap-strateji çözümü → OrderDispatcher::SendOrder
         → RiskManager::checkEnterOrder → MAOSdkManager::SendOrderAsync
         → MAOrderSDK → BIST OUCH veya FIX
```

| Sınır | Taşınan bilgi / davranış | Ayrıntı |
|-------|--------------------------|---------|
| Strateji → `OuchManager` | Fiyat **raw** (`TL × 10^decimal_count`), miktar **lot/kontrat**; TIF ve yön stratejiden gelir | [emir-yolu § 3](../10-servisler/algorithmic-trading/emir-yolu.md#3-emir-modelleri-transactionsorder) |
| AlgoProd → MARpc | 14 karakterlik istemci token'ı `passThrough`'dur; strateji kimliği ayrı alanlarda gider | [kimlik tablosu](../10-servisler/algorithmic-trading/emir-yolu.md#31-kimlik-üç-ayrı-token) |
| Kanal | Arbitraj/VWAP `Channel_Enum` kullanır (1 OUCH, 2 FIX); Fon Takibi sabit OUCH | [kanal seçimi](../10-servisler/algorithmic-trading/emir-yolu.md#42-kanal-seçimi-channel_enum) |
| order-service | Hesap-strateji kaydı, risk, protokol ve kullanıcı seçimi; SDK kendi emir token'ını atar | [arayuzler § 6](../10-servisler/order-service/arayuzler.md#6-orderdispatcher-ve-emrin-yolu) |
| BIST | OUCH veya FIX; bu sürümde HFT handoff hesabının doğrudan bağlantısını kullanamaz | [SDK ve oturumlar](../10-servisler/order-service/sdk-ve-oturumlar.md) |

`send`'in dönmesi kabul değildir. `EnterOrder` tek-emir dalı `sendTransaction(*enterOrder, false)` çağırdığı için **yanıt timeout'u 0**'dır. VWAP'ın çağrı yerinde verdiği 10 s bu dalda uygulanmaz; yanıt gelmezse `trackedOrders` kaydı kalabilir. Cancel/replace'in takipsiz static yolları ayrıca vardır; bütün işlemler aynı izleme modeline sahip değildir.

## 3. Dönüş: BIST → userbook → strateji

1. order-service SDK callback'i `OrderResponseCallBack` → `OrderServer::OnOrder*` ile uygulamanın MARpc bağlantılarına yayın yapar.
2. ouch-sdk'nın tek callback thread'i `ouchSDK::order*` → `OuchManager::algoOrder*` çağırır. Bu thread'deki uzun iş bütün emir olaylarını bekletir.
3. Accepted: order-service token'ı ile `acceptedOrders`'a ekler; `TradableInstrument::orderAccepted` userbook'u günceller; passthrough'taki istemci token'ı takibini kaldırır.
4. Executed/Canceled: önce orijinal kabulü bulur; yoksa loglar ve olayı atar. Kabulden hesap/strateji/yön doldurulur; `TradableInstrument` → `AccountDepth` güncellenir.
5. Replaced: eski emre sentetik cancel, yeni token'a sentetik accept üretir. Bu, GUI'ye iki bağımsız yeni emir gönderildiği anlamına gelmez; AlgoProd iç book güncellemesidir.
6. `AccountDepth` subscriber kuyruklarına `TradeData` yollar; strateji kendi döngüsünde `tryPop` ile bunları işler. HFT'nin doğrudan `executeOrder` callback modeliyle karıştırma.

Userbook anahtarı `<hesap>_<stratejiId>_<stratejiTipi>`'dir; kitap ayrıca enstrümanın içindedir. Bellek, pozisyon istatistikleri, ret eşleme ve eksik userbook risklerinin sahibi [emir-yolu § 5–7](../10-servisler/algorithmic-trading/emir-yolu.md#5-olayların-dönüşü-ve-userbooklar)'dir.

## 4. Arbitraj örneği: türev dolumundan hedge'e

| Aşama | Sıra |
|-------|------|
| Türev emri | Karar → `sendTransaction(..., channel)` → § 2 |
| Türev dönüşü | § 3 → `checkDrvExecution` subscriber'lardan accept/ret/iptal/fill okur |
| Dayanak emri | Aktif modda dolum + iptal gönderilen miktarı tamamlayınca dolan toplamın karşılığı; pasif modda her dolum parçası için dayanak emri |
| Dayanak dönüşü | Aynı gateway yolu → `checkUndExecution` → paket açma/kapama durumunun ilerlemesi |
| Kalıcılık | `setArbitrageDataAsync` → trade-data-app `AlgoService.SetArbitrageData` → DB |
| Aktivite | AlgoProd aktivite kuyruğu → `FetchCommands` → trade-data-app `/ws/v1/strategy/start` → abone GUI |

Spot/vadeli çiftinde dayanak miktarı dolan kontrat × çarpandır; iki vadeli tiplerinde çarpan 1'dir. Ham fiyat ölçeği iki enstrüman için ayrı uygulanır; sabit ×1000 varsayılmaz. **Dayanak emrinin gönderilmiş olması hedge'in dolduğu anlamına gelmez.** Paket tutarlılığı ve ret/durma ayrıntıları [Arbitraj](../20-stratejiler/arbitraj.md#paket-yönetimi-ve-kalıcılık)'tadır.

## 5. GUI'de iki ayrı görünüm

| Görünüm | Kaynak |
|---------|--------|
| Emir geçmişi, pasif emirler, "benim emrim" işaretleri | order-service `SubscribeToOrders` → trade-data-app ortak emir belleği → `/orders` ve `/itch` |
| Strateji snapshot'ı, özet, arbitraj/fon aktivitesi | AlgoProd `FetchCommands` → command publisher → `/strategy` |

trade-data-app AlgoProd için `FetchOrders` açmaz. AlgoProd içindeki `notifyAllUsers(MarketPacket)` çağrısını GUI emir geçmişinin ana kaynağı sanma. Wire aktiviteleri ve abonelik anahtarları [grpc-ve-veri § 5](../10-servisler/algorithmic-trading/grpc-ve-veri.md#5-guiye-dönen-akış)'te; gateway emir yolu [emir-donusu § 7](emir-donusu.md#7-order-service-yedek-yolundan-giden-emrin-dönüşü)'dedir.

## 6. Hata ve prod sınırları

| Durum | Sonuç / referans |
|-------|-----------------|
| Risk reddi | Sentetik ret, kod 0 ve boş token; passthrough eşlemesi gerekir (K-197) |
| MARpc kopması | Otomatik yeniden bağlanma yok; strateji emirlerinin tamamı etkilenir (K-152) |
| Dayanak/fon retleri | Stratejiye özel hedge/pozisyon riski; [Arbitraj](../20-stratejiler/arbitraj.md), [Fon Takibi](../20-stratejiler/fon-takibi.md) |
| AlgoProd restart | DB + order-service replay; stratejiler durmuş gelir. Açık GUI abonelikleri için [kopma ve kurtarma](kopma-ve-kurtarma.md#algoprod-restart) |

⚠ master'da farklı (`aa150ee`): Fon Takibi lot düzeltmesi (K-194) ve paket tutarlılığı kontrolü development ile aynı değildir. Kod farkı prod etkisinin dayanağıdır; canlı sunucunun binary sürümü bu oturumda ölçülmedi. Strateji dosyaları ilgili ayrıntıların tek kaynağıdır.
