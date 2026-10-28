---
kapsam: itch-sdk'nın parse ettiği/atladığı ITCH mesajları (byte düzeni, ölçek, timestamp modeli) ve OrderbookInfo/OrderDepth emir defteri modeli (kitap güncellemesi, header/kademe hesabı, state, execute verisi, snapshot sıralaması, thread modeli)
kaynak:
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
dogrulama: 2026-10-22
durum: taslak
---

# itch-sdk — ITCH mesajları ve emir defteri

İndeks: [README.md](README.md). Bu dosyada olmayanlar:
- UDP/SOUP alımı, sequence/gap, Rewinder, Glimpse TCP oturumu, canlı paket tamponlama → [alim-yolu.md](alim-yolu.md)
- C API abonelikleri, callback imzalarının kullanımı, momentum (max-size) kuralları, tiering, config → [abonelik-api.md](abonelik-api.md)
- HFT tarafında bu olayların nasıl tüketildiği → [hftsrvprod/itch-entegrasyonu.md](../hftsrvprod/itch-entegrasyonu.md)
- BIST fiyat adımı/limit kuralları → [00-genel/borsa-kurallari.md](../../00-genel/borsa-kurallari.md)

Repoda BIST ITCH spesifikasyon dosyası yok. Byte düzenleri koddan (`Clients/ItchClient.cpp` `parse*Direct`) alınmıştır. Koddan okunmayan alanlar için eski bilgi tabanındaki pcap notu (`context-itch-sdk/pcap-field-notes.md`) ipucu olarak anılır ve işaretlenir.

## 1. Kod yerleri: iki parse katmanı

- **Hot path (kullanılan):** `ItchClient::parseItchMessage` → `parseAddOrderDirect`, `parseOrderExecutedDirect`, `parseOrderDeleteDirect`, `parseOrderBookDirectoryDirect`, `parseOrderBookStateDirect`, `parseEquilibriumPriceUpdateDirect`, `parseTickSizeTableDirect`, FlushOrder inline. Ham pointer + `ntohl`/`be64toh`, sabit ofset.
- **`Messages/...` DTO sınıfları** (`Messages/Orders/AddOrder`, `OrderExecutedWithPrice`, `Messages/ReferanceData/OrderBookDirectory`, `TradeMessage`, `SecondMessage`, `SystemEventMessage`, `CombinationOrderbookLeg` …): CMake'te derlenir ama parse yolunda **kullanılmaz**. Kullanılan tek `Messages/` kodu `Messages/Session/*` (Glimpse login/logout, Rewinder `RequestPacket`). DTO'lar okuma referansıdır; içlerindeki hatalar için bkz. Şüpheli 7.
- Aynı `parseItchMessage` hem canlı UDP'den (`processPacket`, `processRewinderQueue`) hem Glimpse TCP'den (`GlimpseClient::parseTCPData`) çağrılır. Glimpse çağrısında `timestamp` (packetTs) ve `demux_timestamp` **0** geçilir.

## 2. Mesaj kataloğu

### 2.1 Ortak kurallar

- Mesaj tipi = byte 0 (ASCII). Enum: `Globals/Enumarations.h` `itch::MessageType`.
- Bütün tamsayılar **big-endian**. `uint32` → `ntohl`, `uint64` → `be64toh`. Fiyatlar `int32` (signed), miktarlar `uint64` (lot), orderId `uint64`, orderbookId `uint32`.
- Byte 1–4 her mesajda `timestamp` (`uint32`, **o saniye içindeki ns**, bkz. §3). Kod bunu yalnız A/E/C/D'de okur.
- Uzunluk kontrolü: her parser `len < N` ise **sessizce** döner (log yok). Fazla uzun mesaj kabul edilir, fazlası okunmaz.
- Bilinmeyen tip `default:` dalında sessizce atlanır (log satırı yorum içinde).

### 2.2 Dispatch tablosu

| Tip | Enum | İşlem | Min `len` |
|-----|------|-------|-----------|
| `T` | `SecondMessage` | `currentFeedSecond_` güncellenir, callback yok | 5 |
| `R` | `OrderBookDirectory` | `OrderbookInfo` **yaratılır** | 130 |
| `L` | `TickSizeTableEntry` | tick tablosuna satır eklenir | 25 |
| `O` | `OrderBookStateMessage` | state enum'a çevrilir, `setState` | 29 |
| `Z` | `EquilibriumPriceUpdate` | `setEquilibriumPrice` → callback | 53 |
| `A` | `AddOrder` | `addOrderDirect` | 45 |
| `F` | `AddOrderWithMPID` | `parseAddOrderDirect` (A ile aynı parser) | 45 (bkz. §2.5) |
| `E` | `OrderExecutedMessage` | `executeOrderDirect(priceReliable=true)` | 38 |
| `C` | `OrderExecutedWithPriceMessage` | `executeOrderDirect(priceReliable=false)` | 38 |
| `D` | `OrderDeleteMessage` | `deleteOrderDirect` | 18 |
| `Y` | `FlushOrder` | `deleteOrderLevels()` | 9 |
| `P` | `TradeMessage` | **atlanır** (açık `return`) | — |
| `U` | `OrderReplaceMessage` | **atlanır** (`default`) | — |
| `S` | `SystemEventMessage` | **atlanır** (`default`) | — |
| `M` | `CombinationOrderbookLegMessage` | **atlanır** (`default`) | — |
| `G` | `EndOfGlimpse` | yalnız Glimpse TCP'de, `GlimpseClient` işler → [alim-yolu.md](alim-yolu.md) | — |
| `V` ve diğerleri | enum'da yok | **atlanır** (`default`) | — |

Atlananların gerekçesi (kod yorumu / pcap notu):
- `P`: kitabı değiştirmez. Kod yorumu: "safe to drop while strategies react only to order-book events (E)". Kasıtlı.
- `U`: pcap notuna göre BIST replace'i `D` + `A` (aynı orderId) olarak yayınlar; `U` kullanılmaz. Kasıtlı ama kodda yorum yok.
- `S`, `M`, `V` (Short Sell Status): parser yok. `V` Glimpse'te geliyor (pcap notu); açığa satış kısıtı SDK'dan alınamaz.

### 2.3 Referans veri mesajları

**`R` OrderBookDirectory** (130 bayt). Canlı akışta görülmez, yalnız Glimpse'ten gelir (pcap notu).

| Ofset | Uz. | Tip | Alan | Not |
|-------|-----|-----|------|-----|
| 0 | 1 | char | `'R'` | |
| 1 | 4 | u32 | timestamp | okunur, kullanılmaz |
| 5 | 4 | u32 | orderbookId | |
| 9 | 32 | ASCII | symbol | sağdan boşluk/`\n\r\t` kırpılır |
| 41 | 32 | ASCII | longName | kırpılır |
| 73 | 12 | ASCII | isinCode | kırpılır |
| 85 | 1 | u8 | product | `Public/enums.h` `Product` (Cash=5, FutureCont=3, EquityWarrant=14, IndexCont=50 …) |
| 86 | 3 | ASCII | currency | kırpılır |
| 89 | 2 | u16 | decimalPrice | fiyatın ondalık basamağı (§4) |
| 91 | 2 | u16 | decimalNominal | |
| 93 | 4 | u32 | oddLotSize | |
| 97 | 4 | u32 | roundLotSize | `OrderbookInfo`'da `uint64` saklanır |
| 101 | 4 | u32 | blockLotSize | |
| 105 | 8 | u64 | nominalValue | |
| 113 | 1 | u8 | numberOfLegs | |
| 114 | 4 | u32 | underlyingId | ≠0 ise `underlyingIdToOrderbook`'a yazılır |
| 118 | 4 | i32 | strikePrice | raw, `decimalStrikePrice` ölçeğinde |
| 122 | 4 | u32 | expirationDate | ❓ doğrulanmadı: biçim (YYYYMMDD?) |
| 126 | 2 | u16 | decimalStrikePrice | |
| 128 | 1 | u8 | putCall | `PutCall` Put=1, Call=2 |
| 129 | 1 | u8 | rankingType | `RankingType` kPriceTime=1 |

- Glimpse bitince `clientThreadMain` her orderbook'un `underlyingId`'sini aynı partition'daki orderbook'a bağlar (`setUnderlyingOrderbookInfo`). Farklı partition'daki dayanak bağlanmaz.
- `Messages/ReferanceData/OrderBookDirectory` DTO'su varantlarda `longName`'den strike/vade/ihraççı çözüyordu (`UtilityClass::getOrderbookInfoFromLongName`). Direct parser bunu **yapmaz**; varantta strike/vade wire alanlarından gelir.
- `O` mesajı `R`'den önce gelirse state `waitingOrderbookStates`'te bekletilir, `R` işlenince `setState` ile uygulanır.

**`L` TickSizeTableEntry** (25 bayt)

| Ofset | Uz. | Tip | Alan |
|-------|-----|-----|------|
| 5 | 4 | u32 | orderbookId |
| 9 | 8 | i64 | tickSize (raw fiyat ölçeğinde, §4) |
| 17 | 4 | i32 | prxFrom (raw) |
| 21 | 4 | i32 | prxTo (raw) |

Orderbook yoksa `LOG_ERROR` ("Tick size table entry for … not found") ve atlanır. Varsa `tickSizeTable` vektörüne **eklenir** (temizlenmez, sıralanmaz).

**`O` OrderBookState** (29 bayt): 5 `u32` orderbookId, 9 `20` bayt state adı (boşluk dolgulu ASCII). Eşleme §7.

**`Z` EquilibriumPriceUpdate** (53 bayt)

| Ofset | Uz. | Tip | Alan |
|-------|-----|-----|------|
| 5 | 4 | u32 | orderbookId |
| 9 | 8 | u64 | availableBidQuantity (lot, denge fiyatında) |
| 17 | 8 | u64 | availableAskQuantity |
| 25 | 4 | i32 | equilibriumPrice (raw) |
| 29 | 4 | i32 | bestBidPrice (raw) |
| 33 | 4 | i32 | bestAskPrice (raw) |
| 37 | 8 | u64 | bestBidQuantity |
| 45 | 8 | u64 | bestAskQuantity |

`OrderbookInfo::setEquilibriumPrice` alanları saklar ve callback'i çağırır. Kitaba dokunmaz. Callback'in son parametresi adı `packetTs` olsa da buraya **ITCH timestamp'i** (saniye içi ns) geçilir (`parseEquilibriumPriceUpdateDirect`). Orderbook yoksa `LOG_ERROR`.

**`T` SecondMessage** (5 bayt): 1 `u32` saniye. Pcap notuna göre Unix epoch saniyesi. Diğer mesajların ns alanı bu saniyeye göredir.

### 2.4 Emir mesajları

**`A` AddOrder** (45 bayt)

| Ofset | Uz. | Tip | Alan | Not |
|-------|-----|-----|------|-----|
| 1 | 4 | u32 | timestamp | saniye içi ns |
| 5 | 8 | u64 | orderId | |
| 13 | 4 | u32 | orderbookId | |
| 17 | 1 | char | side | `'B'`/`'S'` (`'T'` enum'da var) |
| 18 | 4 | u32 | rankingSeqNum | kuyruk sırası (§9) |
| 22 | 8 | u64 | quantity | lot |
| 30 | 4 | i32 | price | raw |
| 34 | 2 | — | orderAttributes | **okunmaz** |
| 36 | 1 | — | lotType | **okunmaz** |
| 37 | 8 | u64 | rankingSeqTime | kuyruk zamanı (§9) |

**`E` OrderExecuted** (min 38; pcap notuna göre wire 52 = 38 + 14 reserved)

| Ofset | Uz. | Tip | Alan | Not |
|-------|-----|-----|------|-----|
| 1 | 4 | u32 | timestamp | saniye içi ns |
| 5 | 8 | u64 | orderId | **kitaptaki (pasif) emir** |
| 13 | 4 | u32 | orderbookId | |
| 17 | 1 | char | side | pasif emrin tarafı |
| 18 | 8 | u64 | executedQuantity | lot, bu eşleşmedeki |
| 26 | 8 | u64 | matchId | **okunmaz** |
| 34 | 4 | u32 | comboGroupId | **okunmaz** |

**`C` OrderExecutedWithPrice** (pcap notuna göre 58): ilk 38 bayt `E` ile aynı, aynı parser kullanılır. 52'deki `tradePrice` (i32), 56 `occurredAtCross`, 57 `printable` **okunmaz**. Fark yalnız `priceReliable=0` bayrağıdır: callback'teki fiyat pasif emrin kitap fiyatıdır, işlem fiyatı değildir (§8).

**`D` OrderDelete** (18 bayt): 1 ts, 5 orderId, 13 orderbookId, 17 side. Silinen miktar mesajda yoktur, kitaptaki emirden alınır.

**`Y` FlushOrder** (9 bayt): 5 `u32` orderbookId. Kitabın tamamı silinir (§6). Her flush `LOG_INFO` ("Order book flushed") basar.

### 2.5 `F` AddOrderWithMPID

`parseAddOrderDirect`'e gider, yani **45 bayttan kısa ise atılır**. DTO düzenine göre (`Messages/Orders/AddOrderWithMPID`: lotType'tan sonra 7 bayt participantId, rankingSeqTime yok) `F` 44 bayttır. Bu durumda her `F` sessizce düşer. 45+ bayt gelirse 37–44 baytı (participantId) `rankingSeqTime` diye okunur. ❓ doğrulanmadı: canlı `F` uzunluğu. Pcap'te `F` hiç görülmedi. Eski bilgi tabanı "aynı handler, MPID ignore" diyordu; doğrusu bu (Şüpheli 2).

## 3. Timestamp modeli

Bir olayın üç ayrı zamanı vardır, birbirine karıştırılmamalıdır:

| Ad | Tip | Kaynak | Birim / domen |
|----|-----|--------|---------------|
| ITCH `timestamp` / callback `ts` | `uint32` | mesaj byte 1–4 | Son `T` saniyesi içindeki **ns** (0 … 999 999 999). Her saniye sıfırlanır. |
| `execAbsNs` | `uint64` | `ItchClient::parseOrderExecutedDirect` | `currentFeedSecond_ × 1e9 + timestamp`. Mutlak epoch ns. Yalnız momentum biriktiricisine gider, callback'e çıkmaz. |
| `packetTs` / `receive_timestamp` | `uint64` | `Globals/TimestampExtract.h` `extractHwTimestamp` | `SCM_TIMESTAMPING` ts[0]: kernel **SW** RX zamanı, `CLOCK_REALTIME` epoch ns. HW ts[2] bilerek kullanılmaz (PHC senkron değil). |

- `packetTs` **0** olabilir: Glimpse'ten gelen bütün mesajlar, XLIO (Mellanox) yolu (`pktTs = 0`), cmsg gelmeyen paketler, `FlushOrder` (aşağıda). Rewinder paketlerinde `drainRewinderSocket` kendi `clock_gettime(CLOCK_REALTIME)` değerini koyar.
- `demux_timestamp`: `steady_clock` ns. Yalnız PerfSDK demux→callback gecikme ölçümü (`ENABLE_BENCHMARKS`). Callback'e çıkmaz.
- `TscClock` (`Globals/TscClock.h`): `rdtsc` × kalibre ölçek (10 ms kalibrasyon, `ItchReceiver` başında). Yalnız RX thread'inin metriklerinde kullanılır (demux süresi; batch başına `CLOCK_REALTIME − tsc.ns()` bias ile wire→demux). Hiçbir callback'e TSC zamanı gitmez.
- `currentFeedSecond_` ItchClient (partition) başına tutulur, Glimpse ve canlı akışta aynı değişkendir.
- ⚠ Eski bilgi tabanı ITCH ts'ini "gün başından ns/µs" diye anlatıyordu (`protocols.md` §6, `bugs-quirks.md` #16). Development'ta kod da yorumlar da "saniye içi ns" der (`ItchClient.h` `currentFeedSecond_` yorumu). Doğrusu bu.

**Callback başına hangi zaman gider:**

| Callback | `timestamp`/`ts` alanı |
|----------|------------------------|
| `order_add` | ITCH ts (u32) |
| `order_executed`, `order_delete`, `specific_order_events` | `ts` = ITCH ts, ayrıca `packetTs` |
| `header_changed`, `order_level_changed`, `price_threshold_crossing` | **Add kaynaklıysa ITCH ts (u32 genişletilmiş)**, execute/delete kaynaklıysa `packetTs`, flush'ta 0 |
| `equilibrium_price_update` | ITCH ts (adı `packetTs`) |
| `header_snapshot` | abonelik anındaki `system_clock` ns |
| `orderbook_state_changed` | zaman yok |

Header/level callback'lerinde aynı alanın kaynağa göre iki farklı domende gelmesi Şüpheli 3'tedir. HFT `ItchSdkClient` bunu `> 2020-01-01 epoch` testiyle ayırıyor ([itch-entegrasyonu.md](../hftsrvprod/itch-entegrasyonu.md)).

## 4. Fiyat ve miktar ölçeği

- SDK fiyatları **hiç ölçeklemez**. Wire `int32` raw değer olduğu gibi kitaba, callback'lere ve snapshot'a gider. TL = raw / 10^`decimalPrice`.
- `decimalPrice` `R` mesajından gelir. `OrderbookInfo::getDecimalPrice` ve snapshot `ItchOrderbookSnapshot.decimalPrice` ile okunur. HFT bu ölçeği ITCH'ten değil trade-data-app'ten alır ([itch-entegrasyonu.md](../hftsrvprod/itch-entegrasyonu.md)).
- Miktarlar **lot**. Pay adedi = lot × `roundLotSize`. SDK dönüşüm yapmaz.
- `strikePrice` ölçeği `decimalStrikePrice`'tır, `decimalPrice` değil.
- **Tick tablosu:** `OrderbookInfo::getTickSize(price)` vektörü sırayla tarar, `prxFrom ≤ price ≤ prxTo` olan **ilk** satırın `tickSize`'ını `int32`'ye kesip döndürür. Hiçbiri tutmazsa **1** döner.
  - `itchsdk_get_tick_size(obId, price)` → `SDKItchManager::getTickSize`: orderbook bulunamazsa **0**, bulunur ama satır tutmazsa **1**, aksi halde tick (raw, `int64` dönüş tipi ama değer int32'den gelir).
  - Snapshot'taki `tickSize` = `getTickSize(0)` → `uint16`'ya kesilir. Yani fiyat 0'ı içeren aralığın tick'i, yoksa 1. Kademeli tablolarda anlamı yoktur.
  - Aralık sınırları kapsayıcıdır. Bitişik aralıklar aynı sınırı paylaşıyorsa vektörde önce gelen kazanır.
- **Fiyat bantları (tavan/taban):** SDK'da yoktur. ITCH'te bu bilgiyi taşıyan mesaj parse edilmez. Kod yorumu (`OrderbookInfo.h` `execArmPrice`): "the SDK has no notion of tavan/taban". Strateji hesaplar.

## 5. Veri yapıları

`OrderBook/OrderDepth.h`, `OrderBook/OrderbookInfo.h`.

- `OrderbookInfo` = bir orderbook. `ItchClient::orderbookInfos` (`unordered_map<uint32_t, unique_ptr<OrderbookInfo>>`) içinde tutulur, `R` ile yaratılır. Ayrıca `nameToOrderbookId` (symbol → id) ve `underlyingIdToOrderbook` haritaları vardır.
- İçinde iki `OrderDepth` bulunur: `buyDepth{Side::Buy}`, `sellDepth{Side::Sell}`. `OrderDepth`'te `isBuyDepth` bool'u vardır. `Side::Buy` dışındaki her taraf (`Sell`, `Short`, `UnknownSide`) **sell** depth'e gider (`addOrderDirect`, `getOrderDepth`).
- `OrderDepth` alanları:
  - `orders`: `unordered_map<uint64_t orderId, Order>`. `Order` = orderId, side, quantity (lot), price (raw), timestamp, `rankingSeqTime`, `rankingSeqNum`.
  - `buyLevels`: `std::map<int32_t, uint64_t, std::greater>`, en yüksek fiyat başta. `sellLevels`: `std::map<int32_t, uint64_t>`, en düşük başta. Her depth yalnız kendi tarafının haritasını kullanır.
  - `totalQuantity`: tarafın toplam lotu, her seviye değişiminde güncellenen sayaç (O(1) `getTotalQuantity`). Alt taşma 0'a kırpılır (`addToTotal`).
- Kademe değeri = o fiyattaki emirlerin toplam lotu. Emir sayısı tutulmaz. Kademedeki emirler `getOrdersAtPrice` ile bütün `orders` taranarak bulunur (O(N)).
- `OrderbookSideState` (`buyState`/`sellState`) tanımlı ama güncellenmez. ❓ ölü alan.

## 6. Emir olaylarının kitaba etkisi

`OrderbookInfo::addOrderDirect` / `executeOrderDirect` / `deleteOrderDirect` / `deleteOrderLevels`. Her biri önce eski header'ı alır, kitabı değiştirir, sonra callback'leri sabit sırayla çağırır.

| Olay | Kitap | Callback sırası |
|------|-------|-----------------|
| **A** | `OrderDepth::addOrder`: yeni emir → `orders`'a eklenir, kademe += qty. **Aynı orderId zaten varsa** eski fiyat kademesinden eski qty düşülür, emir yeni fiyat/qty/ranking ile güncellenir. | pending header snapshot → `order_add` → (header değiştiyse) price-threshold + `header_changed` → `order_level_changed` |
| **E / C** | `OrderDepth::executeOrder`: `executedQty ≥ kalan` ise emir silinir ve kademeden kalan düşülür. Değilse kalan −= executed. Emir bulunamazsa hiçbir şey yapılmaz. | pending snapshot → `order_executed` → `specific_order_executed` → `specific_order_events(EXECUTED)` → (header değiştiyse) threshold + `header_changed` → `order_level_changed` (execution bilgisiyle) |
| **D** | Emir bulunursa tüm kalan miktar silinir (`deleteOrder(id, qty)`). | pending snapshot → `order_delete` → `specific_order_events(DELETED)` → (header) → `order_level_changed` |
| **Replace** | BIST `D` + `A` (aynı orderId) yollar. SDK bunları iki ayrı olay olarak işler: önce silme, sonra yeni ekleme. Arada header/level callback'leri ara durumu görür. | combiner tarafında `DELETED` "cancel veya replace" demektir (`itch_sdk.h` yorumu) |
| **Y** | Her duran emir için `order_delete` + `specific_order_events(DELETED)` üretilir (`ts=0`, `prevHeaderQty=0`, sıra `unordered_map` sırası), sonra iki taraf `clear()`. | threshold(0,0) → `header_changed(0,0)` → `order_level_changed` |

- Emir bulunamayan E/D'de callback'ler **yine çağrılır**: fiyat 0, D'de `deletedQty` 0. Kitap değişmediği için header/level callback'i genelde tetiklenmez.
- Delete callback'indeki `isHeaderOrder`: emrin fiyatı **eski buy header'a veya eski sell header'a** eşitse 1. Taraf ayrımı yapılmaz.
- `orderbookId` bilinmeyen (`orderbookInfos`'ta yok) A/E/D sessizce atılır.
- Flush'ta `ItchClient` `deleteOrderLevels()`'i argümansız çağırır, yani `packetTs = 0`.

## 7. Header ve kademe hesabı

- `getBuyHeader` = `buyLevels.begin()->first`, `getSellHeader` = `sellLevels.begin()->first`. Taraf boşsa **0** (fiyat 0 = "veri yok"; tiering de 0'ı bölge dışı sayar). Header qty = ilk kademenin toplam lotu.
- `getLevelPrice/Quantity(side, level)` **1-tabanlı** (`level ≤ 0` → 0), `std::advance` ile O(level). Kademe yoksa 0. `getDepthCount` = harita boyutu (dolu fiyat seviyesi sayısı).
- **`header_changed` yalnız header *fiyatı* değişince** tetiklenir: `oldBuyHeader != newBuyHeader || oldSellHeader != newSellHeader` (`fireCallbacksAfter*`). Header fiyatı sabitken qty'nin değişmesi bu callback'i tetiklemez; bu bilgi `order_level_changed` ile alınır. Callback'e giden qty'ler çağrı anındaki değerlerdir. (Eski bug #1, hâlâ geçerli. README'deki "fiyat veya miktar değişti" ifadesi yanlış.)
- `order_level_changed` her A/E/D/Y sonrası çağrılır. Abonelik başına son görülen `lastPrices/lastQuantities[level]` ile karşılaştırma yapılır. Callback'teki `changedLevelIndex` **0-tabanlı**dır. Eşik/sweep/max-size kuralları → [abonelik-api.md](abonelik-api.md).
- Atomik header aynası (`atomic_buyHeaderPrice`, `atomic_sellHeaderPrice`, `atomic_*HeaderQuantity`): feed thread'i her olayda yazar. Header snapshot aboneliği başka thread'den bunları okur (§10). Fiyat atomikleri olaydan **önce** eski header'a set edilir, header değiştiyse yenisine çekilir. Qty atomikleri olaydan sonra yazılır.

## 8. Orderbook state

`Public/enums.h` `OrderbookStateType`: `Other`(0), `AcilisEmirToplama`, `SurekliMuzayede`, `ViopSurekliMuzayede`, `Eslestirme`, `KapanisEmirToplama`.

`ItchClient::parseOrderBookStateDirect`, 20 bayt `memcmp` (`Globals/GlobalConstants.h`):

| Wire adı (20 bayt, boşluk dolgulu) | Enum |
|-----------------------------------|------|
| `P_ACILIS_EMIR_TPL`, `P_ACS_EMR_TP_PY_EIY` | `AcilisEmirToplama` |
| `P_KAPANIS_EMIR_TPL`, `P_KAPANIS_EMIR_TPL2` | `KapanisEmirToplama` |
| `P_SUREKLI_ISLEM` | `SurekliMuzayede` |
| `VIOP_SUREKLI_MZYD` | `ViopSurekliMuzayede` |
| `P_ESLESTIRME` | `Eslestirme` |
| diğer her şey | `Other` |

- Pcap'te görülen `P_SALTKOTASYON` ve `P_SUREKLI_ISLEM_HFL` eşlemede yok, **`Other`**'a düşer. Bu, eski bilgi tabanının işaret ettiği durumdur ve development'ta hâlâ geçerli.
- `setState` her `O` mesajında callback'i çağırır, aynı state tekrar gelse de (`newState == prevState` filtresi yok).
- State kitabı **etkilemez**: emir işleme, header/level callback'leri state'ten bağımsızdır. Müzayede/emir toplama fazında kitap çaprazlanmış olabilir (bid ≥ ask). SDK bunu düzeltmez. `continuousSession()` yardımcısı tanımlı ama SDK içinde kullanılmaz.
- Snapshot'ta `ItchOrderbookSnapshot.state` taşınır.

## 9. Execute olayları: veri kaynağı

`executeOrderDirect`, momentum'a girdi olan veriler. Momentum kuralları → [abonelik-api.md](abonelik-api.md).

- **Taraf:** `E`/`C`'deki side, **kitaptaki pasif emrin** tarafıdır. `order_executed` callback'ine bu taraf gider. Agresör karşı taraftır. SDK agresörü ayrıca hesaplamaz (Buy pasif → agresör satıcı, Sell pasif → agresör alıcı).
- **Fiyat (`prx`):** execute öncesi `Order.price` (pasif emrin kitap fiyatı). Emir kitapta yoksa 0. `C`'de gerçek işlem fiyatı farklı olabilir. `specific_order_events` bunu `priceReliable=0` ile bildirir. `order_executed` callback'inde bu bayrak **yok**.
- **`prevHeaderQty`:** execute'tan önce **pasif tarafın 1. kademe** toplam lotu (`getBuyHeaderQuantity`/`getSellHeaderQuantity`). Emrin kendi kademesi değil, her zaman header kademesidir.
- **`executedQty`:** bu tek eşleşmenin lotu, ham. Bir agresif emir birden çok pasif emri yerse her biri için ayrı `E` gelir. Toplama SDK'da yalnız level aboneliği içinde yapılır (`LevelCallbackEntry::accumQty`).
- **Gruplama anahtarı:** `execAbsNs` (mutlak ns, §3). Pencere 0 iken yalnız **aynı borsa damgasını** taşıyan fill'ler birleşir. Grup, abonelik tarafı = pasif taraf olan execution'larda biriktirilir (`execSide == subscribedSide`).
  - `packetTs` bilerek kullanılmaz: bir datagram birden fazla agresörü taşıyabilir, bir agresör iki datagrama bölünebilir, XLIO'da değer 0'dır (`OrderbookInfo.h` yorumu).
  - Tüketici kendi gruplamasını `order_executed`'daki `ts` (u32, saniye içi) ile yaparsa, farklı saniyelerdeki aynı ns değerleri çakışır (Şüpheli 4).

## 10. Snapshot (Glimpse) emirleri ve sıralama (PR #152)

- Glimpse emirleri canlı akışla **aynı yoldan** kitaba girer (`parseItchMessage` → `addOrderDirect`), `packetTs = 0` ile. Glimpse sırasında abone yoksa callback'ler boş geçer. Kitap, kademeler ve `rankingSeqNum/rankingSeqTime` dolar.
- Market'in bütün partition'ları bitince `SDKItchManager::fireSnapshotEndEvent` → `buildMarketSnapshot`. Snapshot son biten partition'ın ItchClient thread'inde kurulur. Diğer partition'lar o sırada canlı paketleri tamponladığı için kitaplar sabittir ([alim-yolu.md](alim-yolu.md)).
  - `isMarketGlimpseComplete` her iki market için Partition1–4 bekler.
- `buildOrderDepthSnapshot`: her kademe için `price`, `totalQuantity`, `side`, `orderCount` ve `orders[]` doldurulur. (Eski bug #10, "orderCount/orders doldurulmuyor", düzeltildi.)
- **Kuyruk sırası (PR #152):** `OrderDepth::getOrdersAtPrice`, kademedeki emirleri şu sırayla dizer: `rankingSeqTime` artan → `rankingSeqNum` artan → `orderId` artan. `ItchLevelInfo.orders[0]` kuyruğun başıdır (`itch_sdk.h` yorumu: "in exchange queue priority order").
  - Ranking alanları yalnız `A` mesajından gelir. Replace sonrası emir yeni `A`'nın ranking değerlerini alır.
  - `F` düşüyorsa (§2.5) o emirler hiç yoktur.
- Header snapshot (`itchsdk_subscribe_header_snapshot`): abonelik anında atomik header aynası okunup kuyruğa konur. Callback, o orderbook'taki **bir sonraki** A/E/D olayında feed thread'inde verilir, abonelik anındaki değerlerle (`firePendingHeaderSnapshot`). Olay gelmeyen orderbook'ta hiç gelmez.

## 11. Thread ve kilit modeli

- **Yazar:** bir orderbook'un `OrderbookInfo`/`OrderDepth`'ine yalnız o partition'ın **ItchClient thread'i** yazar (Glimpse fazı dahil; Glimpse aynı thread'de çalışır). Kitapta mutex yoktur. Bütün feed callback'leri bu thread'de, kitap güncellendikten sonra senkron çalışır.
- **Callback dizileri:** tip başına 32 slot (`MAX_CALLBACKS_PER_TYPE`; header snapshot 512 slot tanımlı ama ekleme döngüsü 32'ye bakar). Lock-free `std::atomic<Entry*>` + `active` bayrağı. Abone ekleme/çıkarma host thread'inden yapılır. Slot yeniden kullanımı (level: epoch, combiner: seqlock) → [abonelik-api.md](abonelik-api.md).
- **Başka thread'den okunanlar:**
  - atomik header aynası (güvenli)
  - `tickSizeTable` (`itchsdk_get_tick_size`): yalnız `L` ile yazılır, `L` pratikte yalnız Glimpse'te gelir. Glimpse sonrası fiilen salt okunurdur ama koruma yoktur.
  - `seedPriceThresholdCallback` (`itchsdk_seed_price_threshold`) ve `setCallbackEnabled(true)` → `reseedLevelCallback`: çağıran thread'de `std::map` header/kademe okur. Feed thread'i aynı anda yazıyorsa veri yarışı vardır (Şüpheli 5).
- Orderbook haritası (`orderbookInfos`) Glimpse sonrası değişmez kabul edilir (kod yorumu). Canlıda `R` gelirse bu varsayım bozulur (Şüpheli 6).

## Şüpheli

1. **`header_changed` qty değişimini kaçırır** (bug, eski #1, hâlâ var): `OrderbookInfo::fireCallbacksAfterAddOrder/ExecuteOrder/DeleteOrder` yalnız fiyatı karşılaştırır. Header fiyatı sabitken erime yalnız level callback'inden görülür.
2. **`F` sessizce düşebilir** (bug?): `parseAddOrderDirect` `len < 45` şartı. DTO düzenine göre `F` 44 bayt. 45+ bayt gelirse participantId `rankingSeqTime` olarak okunur. ❓ doğrulanmadı: canlı `F` uzunluğu/varlığı (pcap'te 0 adet).
3. **Header/level/threshold callback `timestamp`'i iki domende** (bug?): add kaynaklı olayda ITCH saniye içi ns (`fireCallbacksAfterAddOrder(…, timestamp)`), execute/delete'te `packetTs` (epoch ns), flush'ta 0. Aynı alanı karşılaştıran tüketici yanlış sonuç alır. `equilibrium_price_update` `packetTs` adlı parametrede ITCH ts taşır.
4. **`ts` saniye içi ve sarar:** `order_executed.ts` ile "aynı agresör" gruplaması yapan tüketici (ör. [varant-toplu.md](../../20-stratejiler/varant-toplu.md) "aynı ITCH ts") farklı saniyelerin aynı ns değerini birleştirebilir. Saniye bilgisi callback'e çıkmaz.
5. **Çapraz-thread kitap okuması** (bug?): `seedPriceThresholdCallback` ve `reseedLevelCallback` (`activateLevelEntry` üzerinden) host thread'inde `buyLevels/sellLevels` okur. `updateLevelCallback` host thread'inde `lastPrices` vektörünü `resize` eder, feed thread'i aynı anda iterasyon yapıyor olabilir.
6. **Canlı `R` orderbook'u değiştirir:** `parseOrderBookDirectoryDirect` her `R`'de yeni `OrderbookInfo` yaratıp haritadaki eskisinin yerine koyar. Eski nesne silinir; abonelikler, kitap, tick tablosu ve dayanak pointer'ları (`underlyingOrderbookInfo`) gider ya da sallanır. Pcap'e göre canlıda `R` yok. Glimpse retry'ında da aynı yol çalışır (yeni nesne).
7. **DTO hataları (kullanılmıyor, gizli):** `Messages/Orders/OrderExecutedWithPrice` `comboGroupId`'yi `uint64` okur (wire 4 bayt), bu yüzden `tradePrice`/`atCross`/`printable` 4 bayt kayar. `Globals/Enumarations.h` `operator<<(Side)` operatör önceliği yüzünden bool basar. Bu DTO'lardan biri parse yoluna bağlanırsa hata devreye girer.
8. **Flush sonrası header aynası bayat:** `deleteOrderLevels` atomik fiyatları eski header'a set eder, temizlikten sonra 0'a çekmez. Qty atomiklerini güncellemez. Flush ile sonraki ilk emir arasında açılan header snapshot aboneliği silinmiş kitabın header'ını alır.
9. **Tick tablosu kenar durumları:** satır bulunamazsa 1 döner (0 değil). `prxTo` için "0 = sonsuz" kuralı (pcap notu) kodda yok; son aralık `prxTo=0` gelirse o aralıktaki fiyatlar 1 alır. ❓ doğrulanmadı: BIST'in `prxTo=0` gönderip göndermediği. Snapshot `tickSize = getTickSize(0)` uint16'ya kesilir.
10. **State eşlemesi eksik:** `P_SALTKOTASYON`, `P_SUREKLI_ISLEM_HFL` ve listede olmayan diğer adlar `Other` olur. Aynı state tekrarında da callback çağrılır.
11. **`V` (Short Sell Status), `S`, `M`, `P` parse edilmez:** açığa satış kısıtı, sistem olayları, kombinasyon bacakları ve işlem fiyatı/hacmi SDK'dan alınamaz. `P`'nin atlanması kasıtlı.
12. **`isHeaderOrder` taraf karışık:** emrin fiyatı karşı tarafın header'ına eşitse de 1 olur. Çaprazlanmış kitapta (müzayede) yanlış pozitif verir.
13. **`OrderbookSideState`** (`prevHeaderQty`, `deletedQty` alanları) tanımlı ama hiç güncellenmez. ❓ ölü kod.
14. **`headerSnapshotCallbacks` başlatılmıyor** (bug?): `initializeCallbackArrays` bu diziyi `nullptr`'a çekmez. C++17'de (`CMAKE_CXX_STANDARD 17`) `std::atomic<T*>` varsayılan kurucusu değeri belirsiz bırakır ve nesne `make_unique` ile heap'te kurulur. `addHeaderSnapshotCallback`'teki `nullptr` CAS'ı çöp değerde başarısız olabilir. Bu durumda abonelik sessizce kaydolmaz (`subscribeHeaderSnapshot` dönüşü kontrol etmez). Dizi başka hiçbir yerde okunmaz ve temizlenmez. ❓ doğrulanmadı: pratikte (taze sayfa = sıfır) görülüp görülmediği.
15. **Dayanak bağlama partition içinde:** `underlyingId` yalnız aynı ItchClient'taki orderbook'a bağlanır. Dayanak başka partition'daysa `getUnderlyingOrderbookInfo()` null döner. ❓ doğrulanmadı: BIST'te varant ile dayanağının her zaman aynı partition'da olup olmadığı.
