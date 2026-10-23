---
kapsam: Emrin dönüşü uçtan uca — HFT SDK callback'leri, strateji ve GUI yollarının ayrılması, FetchOrders, order-service dönüşü, trade-data-app belleği ve WebSocket görünürlüğü
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: HftSrvProd
    branch: master
    commit: 052dd96
dogrulama: 2026-10-23
durum: taslak
---

# Emrin dönüşü: BIST → strateji ve GUI

Bu akış HFT'nin [hot path](hot-path.md) gönderiminin devamıdır. AlgoProd'un strateji içi dönüşü [algoprod-emri](algoprod-emri.md)'ndedir. Model ve callback ayrıntılarının sahibi [HFT emir yaşam döngüsü](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#3-dönüş-olaylar--strateji--gui), gateway ayrıntılarının sahibi [trade-data-app veri akışı](../10-servisler/trade-data-app/veri-akisi.md#54-order-service-orderservicego-ve-bellekteki-emir-durumu)'dır.

## 1. İki dönüş yolu

```text
BIST OUCH → HFT MAOrderSDK
              ├─ onAccepted/onExecuted/onRejected/onCanceled/onReplaced → strateji
              └─ onAccepted/onWireExecuted/onRejected/onCanceled/onReplaced
                   → internalOuchOrdersQueue → FetchOrders gRPC
                   → trade-data-app → /ws/v1/orders/start → GUI

BIST OUCH/FIX → order-service MAOrderSDK → OrderResponseCallBack
              ├─ MARpc → HFT/AlgoProd ouch-sdk callback'leri → strateji/userbook
              └─ OrderServiceImpl → SubscribeToOrders gRPC
                   → trade-data-app → aynı WebSocket feed'i → GUI
```

GUI'de olay görülmesi ile stratejinin olayı işlemesi ayrı adımlardır. REST'te başarılı emir gönderim yanıtı, BIST kabulü anlamına gelmez ([manuel emir](manuel-emir.md)).

## 2. Accepted — sahiplik ve strateji eşleme

HftSrvProd `src/Main/HftMain.cpp` `cbs.onAccepted`:

1. SDK mesajını HFT modeline çevirir; `orderbookId == 0` ise döner.
2. Hesap, enstrüman, strateji id ve tip ile stratejiyi arar. Kimlik kabulün passthrough bilgisinden çözülür.
3. Token'ı `OrderRegistry::addAcceptedOrder` ile kaydeder. Kayıt zaten varsa mevcut nesne korunur.
4. Strateji bulunduysa ayrıca `claimGlobalAcceptedToken` ile OS/handoff replay çift kabulünü eler.
5. İlk kabul ise `strategy->addOrder` ve `addSecondRuleOrder` çağırır. Strateji bulunamadıysa registry kaydı yine kalır; stratejiye olay işlenmez.
6. Duplicate olmayan kabulü GUI olay kuyruğuna koyar. `internal_ouch` için token → OUCH kullanıcı haritasını da doldurur.

Strateji çağrısı callback thread'inde **doğrudandır**; AlgoWorker'ın ITCH kuyruğundan geçmez. Registry nesneleri gün içinde silinmez; strateji depth'lerinin ham pointer sahipliği buna bağlıdır. Kimlik alanları için [emir yaşam döngüsü § 1](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#1-emir-modeli).

## 3. Executed — strateji ile GUI neden ayrılır?

| Yol | Thread | Sonuç |
|-----|--------|-------|
| `onExecuted` | OUCH recv; combiner açıksa ITCH client thread'i de olabilir | Registry'den kabulü bulur → `strategy->executeOrder`. GUI'ye yayın yapmaz. |
| `onWireExecuted` | Emrin kendi OUCH bağlantısının recv thread'i | Registry'de kabul varsa GUI olay kuyruğuna koyar; stratejiye yeniden işlemez. |

Combiner açıkken kendi gönderdiği emrin fill'i ITCH'ten daha erken gelebilir; OUCH tekrarı SDK'da elenir. GUI yalnız wire fill'ini kullanarak kabul/fill sırasını korur. Replay'den adopt edilen emirler combiner'a alınmaz. Mekanizma: [MAOrderSDK combiner](../10-servisler/maordersdk/emir-akisi.md#9-combiner-srccombiner).

**Sınır:** Bu koruma HFT'nin OS yolunda daha önce işlediği execute'un handoff replay'inde tekrar gelmesini elemez (K-57). `globalExecutedMatches` yazılması tek başına dedup değildir; HFT'nin SDK callback'i bu seti okumaz. Canlı tekrarın oluştuğu ayrıca doğrulanmalıdır.

## 4. Diğer olaylar

| Olay | Stratejiye işlem | GUI'ye işlem |
|------|-----------------|---------------|
| Rejected | Passthrough'tan stratejiyi bulur → `rejectOrder` + `onCancelResponse` | Her ret kuyruğa konur. SDK yerel retleri de dahildir; bunlar BIST'e gönderilmiş emir değildir. |
| Replaced | Önceki kabulü bulur, registry anahtarını eski token'dan yeniye taşır → `updateOrder` | Eski fiyat mutasyondan önce alınır, `REPLACED` olayında gönderilir. |
| Canceled | Registry'deki kabulden strateji/yönü bulur → `deleteOrder` + `onCancelResponse` | `CANCELED` olayı kuyruğa konur. |

Execute/cancel/replace'te registry kaydı yoksa olay loglanıp düşer. Yerel ret `enterOrder`'ı çağıran thread'de senkron gelebilir; bütün callback'ler için tek bir recv thread'i varsayılmaz. Ret kodlarının sahibi [emir yaşam döngüsü § 5](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#5-ret-ve-hata-kodları)'tir.

## 5. HFT → trade-data-app

HftSrvProd `src/Strategy/Service/StrategyServiceImpl.cpp` `FetchOrders`:

1. Motor token'ını doğrular, başlangıçta sabit **3 s** bekler. Bu süre replay'in tamamlandığını garanti etmez.
2. Önce önceki stream'in yazamadığı `unsentOrderEvents`, ardından `internalOuchOrdersQueue`; batch sınırı **50**.
3. `buildStrategyOrderFromEvent` ile `StrategyOrder` oluşturur. Fiyat **raw**, miktar **lot**, latency alanları **ns**'dir; tam wire sözleşmesi [komutlar-ve-grpc](../10-servisler/hftsrvprod/komutlar-ve-grpc.md)'dedir.
4. `Write` başarısızsa batch'i geri saklar ve stream'den çıkar. ⚠ master'da yok: bu koruma için [branch farkları](../10-servisler/hftsrvprod/README.md) esas alınır.

trade-data-app `pkg/gui/connections/hft.go` `getOrdersFromService`, ilk aldığı **batch'i** geçmiş sayar (`IsOrderHistoryReceived=false`). Bu protokolde ayrı bir "geçmiş bitti" işareti yoktur; HFT'nin ilk batch'i bütün günün geçmişini içermek zorunda değildir. Aynı gateway motorla yeniden bağlandığında `alreadyConnected` nedeniyle ilk batch doğrudan atlanır; HFT'nin batch'i saklaması tek başına uçtan uca kayıpsızlık sağlamaz.

## 6. trade-data-app → GUI ve emir defteri işaretleri

`pkg/gui/connections/ws_listener.go` `transmitOuchMessages`:

1. HFT `FetchOrdersResponse`'unu ortak `OrdersResponse` modeline çevirir.
2. `OrderService.checkUserOrders` geçmişi belleğe ekler; kabul/dolum/iptal/replace ile kalan lot ve fiyat haritalarını günceller.
3. `processOuchMessage` GUI emir olayına dönüştürür. Process ömründeki ilk HFT geçmiş batch'i canlı WS'e yayınlanmaz; bellekte tutulur.
4. `/ws/v1/orders/start` istemcisinin abone olduğu **hesap ve strateji tipi** eşleşiyorsa gönderir. Yeni abone, gateway belleğindeki filtreli geçmişi ayrıca alır.
5. Canlı olaylar ilgili fiyat seviyesinde sentetik ITCH güncellemesi üretir; `/itch` üzerinde "benim emrim" işaretleri, pasif emirler panelinde kalan emir görünümü güncellenir.

Emir defteri anahtarı hesap/enstrüman/strateji id/tip içerir; panel başka kimliğe aboneyse BIST'te yaşayan emir o panelde işaretlenmeyebilir. Bellek, yarışlar ve yeniden bağlantı sınırları [veri-akisi § 5.4](../10-servisler/trade-data-app/veri-akisi.md#54-order-service-orderservicego-ve-bellekteki-emir-durumu)'te tutulur.

## 7. order-service yedek yolundan giden emrin dönüşü

1. order-service SDK callback'i `OrderResponseCallBack` üzerinden iki kola ayrılır: uygulamaya MARpc, GUI gateway'ine `SubscribeToOrders`.
2. HFT ouch-sdk callback'leri `OuchManager::acceptedOrders` haritasını kullanır; bu harita `OrderRegistry`'den ayrıdır. Stratejiye doğrudan işlem yapılır; HFT'nin `internalOuchOrdersQueue`'suna yayın yapılmaz.
3. GUI olayı order-service stream'inden gelir. trade-data-app `orderservice.go` önce yayınlar, sonra `checkUserOrders` çağırır; HFT yolundaki sıra tersidir. Cancel miktarı yarışı ve geçmiş sıfırlanması için K-24 ve [veri akışı](../10-servisler/trade-data-app/veri-akisi.md#54-order-service-orderservicego-ve-bellekteki-emir-durumu).
4. Handoff'tan sonra order-service devredilen kullanıcının yeni BIST olaylarını görmez; o kullanıcının dönüşünü HFT SDK yolu taşır. Kabul iki yolda görülebilir; bunun global kabul kapısıyla elenmesi § 2'deki sınırlar içindedir.

## Kontrol noktaları

| Görülen durum | Kontrol edilecek yer |
|---------------|---------------------|
| REST başarılı, kabul/ret yok | Yol seçimi, order-service sessiz düşüşleri, MARpc bağlantısı: [manuel emir](manuel-emir.md#6-hata-yolları-özet) |
| Strateji dolumu biliyor, GUI bilmiyor | `onWireExecuted`, `FetchOrders`, HFT batch atlama ve WS aboneliği |
| GUI biliyor, strateji bilmiyor | Strateji bulunamadı log'u, registry/userbook kimliği, AlgoProd `isStrategyInfoMapFilled` |
| order-service reconnect sonrası HFT emirleri görünmüyor | Gateway bellek sıfırlaması (K-24); geçmiş ve iptal-token çözümü de etkilenir |
| Restart/handoff sonrası pozisyon fazla | Execute replay tekrarı (K-57); [kopma ve kurtarma](kopma-ve-kurtarma.md) |
