---
kapsam: K-240 için feature extended execution callback ve HFT build bağımlılığı
kaynak:
  - repo: itch-sdk
    branch: warrant-open-quote-log-pp
    commit: e800b3d
  - repo: HftSrvProd
    branch: hft_warrant_advanced
    commit: f20b5f2
dogrulama: 2026-10-24
durum: taslak
---

# Quote extended execution feature

24 Ekim fetch + development pull sonrası itch-sdk development `35a3b5c`, master `00c51b1` değişmedi. Yeni API `warrant-open-quote-log-pp` `e800b3d` dalında bulundu; remote contains kontrolünde commit yalnız bu dalda. Aynı adlı HFT dalı ile karıştırma: SDK `hft_warrant_advanced` `ffde0af` içinde bu API bulunmadı. Bütün SDK remote ref'leri içerik olarak taranmadı.

## Kaynak sözleşmesi

`Public/itch_sdk.h` içindeki `itch_on_order_executed_ex_fn`, eski execution callback parametrelerine sırayla `uint8_t isQuote`, `uint8_t quoteBuyer`, `uint64_t levelQtyAfter` ekler. HFT `f20b5f2` callback imzası bununla eşleşir. Yeni `itchsdk_subscribe_order_executed_ex` C export'u `SDKItchManager::subscribeOrderExecutedEx` üzerinden aynı ORDER_EXECUTED aboneliğini extended=true olarak kaydeder. Eski callback yolu korunur.

| Alan | SDK üretimi |
|---|---|
| isQuote | Resting emrin tutulan quote işareti; gerekirse `isQuoteOrder` kontrolü |
| quoteBuyer | Normal fill'de `!quote && quoteEventTs == timestamp` |
| levelQtyAfter | Fill uygulandıktan sonra ilgili taraf/fiyat derinliğindeki miktar |

Bu alanlar doğrudan borsadan gelen bir “aggressor kimliği” alanı değildir. Quote işareti aynı orderId'nin iki tarafta aynı ITCH ns'de eklenmesi ve aynı ns'deki quote olayları üzerinden hesaplanır. Canlı doğruluk oranı veya tüm quote yaşam döngüleri bu incelemede sınanmadı.

**Geç tanıma bildirimi:** `addOrderDirect` yeni quote çiftini fill'lerden sonra tanırsa `fireQuoteBuyerLate` çağırabilir. Bu ek extended callback `Side::Sell`, `executedQty=0`, `quoteBuyer=1`, `isQuote=0`, `packetTs=0` taşır; fiyat aynı ns'nin ilk non-quote sell fill fiyatıdır. Bu bir ek dolum değildir. Gerçek fill miktarına tekrar eklenmemelidir. HFT'nin kullanım sınırı [Varant Toplu feature bölümünde](../../20-stratejiler/varant-toplu.md#24-ekim--motor-feature-eşleşmesi).

## Build ve dağıtım sınırı

HFT `f20b5f2` `<MAItchSDK/itch_sdk.h>` include eder; CMake `find_library(... MAItchSDK)` kullanır, SDK commit'i sabitlemez. HFT workflow'u Algo-Setup `MAProdEnv/include/MAItchSDK` ile regular/onload library'lerini build ortamına kopyalar. Sadece kaynak imzasının eşleşmesi build ortamındaki header/library'nin doğru olduğunu kanıtlamaz.

SDK `e800b3d` workflow'u header ve library'yi birlikte artifact'e koyacak şekilde yazılmıştır; push tetik dalları master/development/pre_prod'dur. HFT workflow push tetik dalları master/development/preprod'dur. İncelenen iki feature dalı bu listelerde yoktur. Bu YAML kontrolü başarılı feature build'i/artifact'i veya başka manuel build yolunun yokluğunu kanıtlamaz; CI run bu alt turda incelenmedi.

Yerel Algo-Setup development `cade7d0` snapshot'ındaki `MAProdEnv/include/MAItchSDK/itch_sdk.h` yeni API adını taşımıyor. Bu snapshot, feature HFT'nin yeni header gereksinimini karşılamıyor. Kurulu `.so` export tablosu, feature'a özel Setup dalı, gerçek CI artifact'i ve müşteri binary seti henüz doğrulanmadı; bütün Setup ref'lerine genellenmez.

**K-240 açık:** GUI–HFT–SDK kaynak zinciri bulundu. Kalan iş uyumlu header/library artifact'inin ve birlikte build/dağıtımın kanıtı. ABI/link testi, tam build, ITCH replay, canlı emir veya deploy yapılmadı. Development/master belgelerindeki temel SDK davranışı bu feature'a geçirilmedi.
