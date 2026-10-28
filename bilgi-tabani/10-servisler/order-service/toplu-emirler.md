---
kapsam: order-service toplu (zamanlanmış) emir akışları — sabah (OUCH/VİOP/FIX), açılış (vadeli/pay/varant), YİP, teorik/akşam, off-hours bayrağı; zamanlama, OUCH kullanıcılarına dağıtım, son atış ve -110023 döngüsü, fazla kopya iptali, DB durum güncellemesi, thread modeli
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# Toplu emirler

Servis özeti [README.md](README.md)'de. Kardeş dosyalar:
- gRPC/MARpc arayüzleri ve `OrderDispatcher`: [arayuzler.md](arayuzler.md)
- MAOrderSDK adaptörü, kullanıcı yükleme, callback'ler, handoff ayrıntısı: [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md)
- Risk: [risk.md](risk.md)
- `config.yaml` anahtar referansı ve müşteri config'leri: [kalicilik-ve-config.md](kalicilik-ve-config.md)

Kod:
- `Managers/OrderManager.{h,cpp}`: tekrarlı akış (sabah, VİOP sabah, FIX sabah, teorik), off-hours thread'i
- `Managers/RepeatableOrders/*.h`: son atış
- `Managers/Sdk/MAOSdkManager.cpp`: thread'lerin başlatılması (`StartProperly`), açılış/YİP (`SendOpeningOrders`, `SendYipOpeningOrders`), `DisconnectMorningOrderUsers`
- `Data/Models/BulkOrder.h`
- `Service/Network/OrderService.cpp`: DB çağrıları
- `Service/servicemodel/OrderServiceImpl.cpp`: GUI kaydı
- `OrderServiceApplication.cpp`: zamana bağlı handoff tetiği

⚠ master'da yok (2026-10-22): `origin/master` (298403b) hâlâ eski `Managers/Ouch/OuchManager` + `Managers/Fix/FIXManager` yapısındadır. Şunlar `development` ve `preprod`'da var, master'da yok:
- YİP akışı ve varant açılış grubu
- OUCH başına slice/round dağıtımı (`PrepareSliceRounds`)
- `schedPolicy` ve `coreToPin`

Bu dosya `development`'ı anlatır.

Ölçek: emir `Price` alanı raw tamsayı fiyattır (ITCH ölçeği, TL değil); kademe açılımı da ITCH tick'iyle yapılır. Saat alanları yerel saattir (`localtime`/`mktime`, sunucu TZ'si). Saat kaynağı `std::chrono::system_clock`'tur, yani duvar saati; doğruluğu sunucunun saat senkronuna bağlıdır. ❓ doğrulanmadı: prod sunucularda NTP/PTP kurulumu.

## 1. Akışlar özeti

| Akış | Tetik (config) | DB'den seçilen satırlar | Protokol / kullanıcı | Kod |
|------|----------------|-------------------------|----------------------|-----|
| Sabah (pay) | `repeatableOrders.ouch[type=morning]` | `OrderType=MORNING`, OUCH, aktif, pay piyasası, `part` partition'ı | OUCH: partition'daki bütün OUCH kullanıcıları | `OrderManager::SendRepeatableOrders` |
| Sabah VİOP | `repeatableOrders.ouch[type=morning_viop]` | `MORNING`, OUCH, aktif, **vadeli** piyasa | OUCH | aynı |
| FIX sabah | `repeatableOrders.fix[type=morning]` | `MORNING`, FIX, aktif, pay | FIX kullanıcıları (`SendOrderWithUsername` FIX yolu) | aynı |
| Teorik | `repeatableOrders.fix[type=theoric]` (OUCH altına da yazılabilir) | `OrderType=EVENING`, satırın protokolü, aktif, pay | FIX (örnek config) | aynı (`kTheoric` → `GetEveningOrders`) |
| Açılış | `openingOrders.derivative` / `equity` / `warrant` | `OrderType=OPENING`, OUCH **ve** FIX, aktif, gruba ait | Satır protokolüne göre: OUCH round-robin veya FIX `getNextFixClient` | `MAOSdkManager::SendOpeningOrders` |
| YİP | `openingOrders.yip.sessions[]` | `OPENING` ve `is_yip`; yalnız pay (varant/sertifika değil) | aynı | `MAOSdkManager::SendYipOpeningOrders` |
| Off-hours | `eveningSessionStart` | — (gönderim akışı değil) | `SendOrderAsync` yolu | `OrderManager::Start` içindeki `offhours_invertor` |

Config'teki `type` değeri `StartProperly` içinde büyük harfe çevrilir (`MORNING`, `MORNING_VIOP`, `THEORIC`). Bilinmeyen tip `kUnknown` olur ve akış hiçbir şey göndermez. `mode: repeat` alanı parse edilmez, etkisi yoktur.

## 2. GUI'den kayıt (order-service tarafı)

1. GUI → trade-data-app `GuiSendOrders`. `MORNING`/`OPENING`/`EVENING` için ENTER veya REPLACE olayında kademe açılımı yapılır, ama yalnızca `ItchEnabled` ise ve orderbook ITCH'te bulunursa.
   - `LevelCount` kadar satır üretilir: ilki ana emirdir (`IsMainOrder=true`), diğerleri alt emirdir.
   - Her kademe bir tick uzaktadır: alışta fiyat düşer, satışta artar. Tick `itchManager.GetTickSize(obId, price)` ile o fiyat bandından alınır.
   - ENTER'da alt emirlerin `MainOrderId`'si 0'dır.
   - ITCH kapalıysa tek satır gider, açılım yapılmaz.
   - ❓ doğrulanmadı: `LevelCount=0` gelirse döngü hiç dönmez ve satır üretilmez; GUI'nin her zaman ≥1 gönderip göndermediği bilinmiyor.
2. order-service `OrderServiceImpl::SendOrder` (gRPC ayrıntısı: [arayuzler.md](arayuzler.md)). Her satır için:
   - **ENTER:** `GenerateToken()` ile bir **DB satır token'ı** üretilir. Bu token yalnızca planlanan satırı tanımlar, OUCH token'ı olarak kullanılmaz. Ardından `InsertCollectiveOrder` satırı tipine göre `morningOrders` / `openingOrders` / `eveningOrders` üye vektörlerine ekler.
   - **CANCEL:** yalnız ana emirde `RemoveCollectiveOrder` → `OrderService::RemoveOrder` (`DataService.DeleteOrders`).
   - **REPLACE:** ana emirde önce silme, sonra yeni token ile ekleme.
3. İstek sonunda dolu her vektör için `BulkInsertMorningOrder` / `Opening` / `Evening` → `OrderService::BulkInsertOrder` çağrılır:
   - Her **ana** emir için ayrı bir `DataService.SetOrders` isteği gider. İsteğe, ana emirle aynı `PassThrough` (custom_data) değerine sahip bütün alt emirler eklenir.
   - `account_strategy_id=0` olan ana emir atlanır.
   - Dönen `orderid` ana emre yazılır.
4. `PublishCollectiveOrders`: her ana emir için GUI stream'ine `kOrderAccepted` + tip (`kMorningOrder` / `kOpeningOrder` / `kEveningOrder`) yayınlanır.
5. `RemoveOrder` başarılı olursa GUI'ye `kOrderCanceled` yayınlanır.

Satırın `is_active`, `is_main_order`, `main_order_id`, `level_count`, `is_yip` ve `protocol` alanları istekten gelir. Toplu akışlar yalnız `IsActive()` satırları gönderir.

## 3. Tekrarlı akış: `OrderManager::SendRepeatableOrders(config)`

Sabah, VİOP sabah, FIX sabah ve teorik aynı fonksiyonu kullanır. `StartProperly` her config satırı için (önce `ouch`, sonra `fix` listesi) bir **detached `std::thread`** açar.

### 3.1 Zamanlama

- `T = GetTimePoint(hour, minute, second)` bugünün yerel saatidir; milisaniye burada yoktur.
- `IsLateToSend(5, T)`: T'ye 5 sn'den az kaldıysa (veya T geçtiyse) akış **hiçbir şey yapmadan döner**. Bu durumda emir gönderilmez, DB'deki satırlar aktif kalır, akışın kendisi disconnect da çağırmaz.
- `WaitUntilFetch`: T − 60 sn'ye kadar `sleep_for(seconds)` ile bekler (tam saniyeye kırpılır). Servis T−60 ile T−5 arasında başlatıldıysa beklemeden çeker.
- Gönderici thread'inde ise:
  1. T anına kadar `sleep_for(100 µs)` döngüsüyle beklenir (yoklama + uyku; saf busy-wait değildir).
  2. T'ye gelince `sleep_for(millisecond ms)` eklenir.
  3. İlk emrin gerçek çıkış anı ≈ T + `millisecond` + uyku gecikmesidir. ❓ doğrulanmadı: FIFO 99 altında gerçek gecikme ölçülmedi.

### 3.2 Emir seçimi: `PartitionRepeatableNoNRepetableOrders`

- `MORNING` → `GetMorningOrders(protocol)` + pay piyasası.
- `MORNING_VIOP` → `GetMorningOrders(protocol)` + vadeli piyasası.
- `THEORIC` → `GetEveningOrders(protocol)` + pay piyasası.

`OrderService::GetOrders` satırları config satırının protokolüne (`ouch` listesi → OUCH, `fix` listesi → FIX) göre süzer. Hesap-strateji bulunamayan satırlar atlanır.

Bir satırın seçilmesi için hepsi gerekir:
- `IsActive()`
- yön `kBuy` veya `kSell`
- enstrüman bulunmuş
- piyasa uyuyor
- `instrument.Partition() == config.part`

Tekrarlı/tekrarsız ayrımı:
- **Tekrarlı:** bütün alışlar. `repeatSellOrders: true` ise satışlar da.
- **Tekrarsız:** `repeatSellOrders: false` iken satışlar.

Sıralama: enstrüman id artan; aynı enstrümanda alış fiyatı azalan (en iyi önce), satış fiyatı artan.

### 3.3 Hesaplara ve kullanıcılara dağıtım

**`PrepareAccountOrders`:**
- Satırlar, açılışta yüklenen `user_accounts`'taki hesaplara ayrılır.
- Hesapta `RepeatOnlyBestBuy` (DB `repeat_only_top_levels`) açıksa, her (enstrüman, yön) için ilk `BestBuyCount` (`repeat_levels`) emir tekrarlı kalır. Kalanlar tekrarsıza taşınır. Sıralama sayesinde en iyi fiyatlı emirler tekrarlanır.

**Kullanıcılar:**
- `user_service->GetUsers(protocol, part, mode)` DB'den taze okunur.
- Süzme yalnız partition ve prod/test moduna göredir; **piyasa süzülmez**.
- Bir kullanıcı, `IsAccountAllowed` ile izinli olduğu her hesaba eşlenir (`ouch_accounts`, `account_ouches`).

### 24 Ekim güncel davranış farkı

Development `26e9a02` tekrarsız dağıtım düzeltmesini içerir; artık ayrı feature sayılmaz. Tekrarsız satır i, hesabın kullanıcı listesindeki `i % N` kullanıcısına atanır; tekrarlı satırlar izinli kullanıcılara kopyalanır. Kapasiteden atılan satırın başka kullanıcıya yeniden dağıtım garantisi yoktur. `SendOpeningOrders` ayrıca `skip_brut_takas=true` geçirir; diğer çağrıların varsayılanı false. SDK `c2b5060` bu seçeneği destekler; bütün risk kontrolleri kapanmaz. Master uçları değişmedi; canlı test yok.

**`PrepareOuchOrders`:** Aşağıdaki hesap artık kullanıcıya atanan tekrarsız satır sayısıyla yapılır. Eski `b86c0cf` bütün tekrarsızları da her kullanıcıya veriyordu. Kullanıcı başına tekrar sayısı:

```
ouch_repeat = 0                                   (tekrarlı emir yoksa)
ouch_repeat = RepeatCount                         (Capacity == 0: sınırsız)
ouch_repeat = min(RepeatCount, (Capacity − Σtekrarsız) / Σtekrarlı)   (tamsayı bölme; Capacity ≤ Σtekrarsız ise 0)
```

- `Σ` kullanıcının bütün hesapları üzerinden alınır. `RepeatCount`, `Capacity` ve `CoreToPin` DB'deki OUCH/FIX kullanıcı satırından gelir (`ouchrepeatcount`, `ouchcapacity`, `ouchcoretopin`).
- Tekrarlı liste, hesabın emirlerinin `ouch_repeat` kez arka arkaya kopyasıdır.
- Tekrarsız emirler `Capacity` bütçesiyle kırpılır (fazlası atılır, CRIT log).
- **Rotasyon:** Bir hesap birden fazla kullanıcıya izinliyse, her kullanıcının listesi `ouch_index × (unique / kullanıcı_sayısı)` kadar döndürülür. Böylece kullanıcılar farklı emirden başlar.

`PrepareBulkOrders` kullanıcı başına bir `BulkOrder` üretir. İçinde hesap başına bir `AccountSlice` (tekrarlı, tekrarsız) bulunur.

### 3.4 Gönderici thread: `SendRepeatableOrdersToExchangeMarket`

`OrderManager::SendRepeatableOrders(bulkOrders, threads, schedPolicy)`:
- Her `BulkOrder` için bir `pthread` açar.
- `coreToPin ≥ 0` ise `pthread_setaffinity_np` ile o çekirdeğe sabitler. `-1` veya `≥ CPU_SETSIZE` ise sabitlemez.
- `schedPolicy` `OTHER` değilse `SCHED_FIFO` öncelik 99 kullanır, `OTHER` ise `SCHED_OTHER` 0. Varsayılan FIFO'dur.
- Politika thread oluşturulduktan **sonra** ayarlanır. Ayar başarısız olursa yalnız log yazılır.
- Sonunda hepsini `pthread_join` ile bekler.

Thread içinde:
1. **Round hesabı:** `PrepareSliceRounds` her slice için tekil emir sayısını (`orders_per_repeat`) ve `repeat = ceil(tekrarlı / tekil)` değerini yeniden hesaplar. Tekillik anahtarı: orderbook, yön, fiyat, miktar, hesap-strateji id, strateji identifier. `max_repeat` slice'ların en büyüğüdür.
2. **Aralık:** `elapse_interval = duration / (max_repeat − 1)` **ms**. `duration` config'ten gelir, birimi ms'dir. `max_repeat ≤ 1` ise aralık 0'dır.
3. T + ms beklenir (§3.1).
4. **Round'lar:** `max_repeat − 1` round koşar; son round son atışa ayrılır.
   - Her round'da hesaplar pozisyon bazlı round-robin ile **iç içe** gönderilir (A1 B1 C1 A2 B2 …).
   - Gönderim `SendOrderWithUsername(order, ouch_user, insert_to_entered_orders=true, insert_to_db=false)` ile yapılır. Dönen SDK token'ı `all_sent_orders`'a eklenir.
   - Round sonunda `clock_nanosleep(CLOCK_REALTIME, relative, elapse_interval)` ile uyunur.
   - Round'larda ret beklenmez, yeniden gönderim yoktur.
5. **`packOrders: true`:** Round'un emirleri bir `EnterOrderPackage`'a toplanır ve `SendPackagedOrderWithUsername` ile tek döngüde gönderilir. Bu yol kullanıcı/piyasa çözümlemesini bir kez yapar ve emir başına log basmaz.
6. **Son atış listesi:** Her slice'ın tekrarsız emirleri ile tekrarlı listesinin son chunk'ı (`(repeat−1)·tekil` indeksinden sona) birleştirilir. `ouch_repeat=0` ise bu liste yalnız tekrarsızlardan oluşur.

`SendOrderWithUsername` kullanıcıyı önce OUCH (`users`), sonra FIX (`fix_users_`) haritasında arar ve SDK'ya **tam rota** (`preferred_ouch_username`, `no_split=true`) ile verir. Hesap alanları kullanıcının **piyasasına** göre doldurulur (`PrepareAccountFields`). **Risk kontrolü yapılmaz**; `checkEnterOrder` yalnız `OrderDispatcher` yolundadır ([risk.md](risk.md)).

### 3.5 Son atış (`Managers/RepeatableOrders/`)

`ILastShotStrategy` arayüzünde tek metod vardır: `execute()`. Strateji `repeatLastShot` ile seçilir.

**`SingleLastShotStrategy`** (`repeatLastShot: false`):
- 1 sn uyur.
- Listedeki her emri bir kez gönderir (`insert_to_db=false`).
- Ret veya kabul izlenmez.

**`RepeatedLastShotStrategy`** (`repeatLastShot: true`):
1. Liste tekilleştirilir (anahtar §3.4 ile aynı) ve her tekil emir bir kez gönderilir.
2. Liste boşalana kadar **uykusuz** bir döngü döner. Her emir için:
   - **Ana token reddedildi, kod `-110023`** (veya açıklama `"REJ- <-110023> : Illegal transaction at this time"`; FIX retlerinde kod yalnız metinde gelir):
     - Son gönderimden bu yana 500 µs dolmadıysa kalan süre uyunur.
     - Emir yeniden gönderilir (`insert_to_db=true`) ve yeni token ana token olur.
   - **Ana token başka bir kodla reddedildi:** emir listeden çıkar ve bir daha denenmez.
   - **Ana token veya timeout kopyalarından biri kabul edildi:** emir listeden çıkar.
   - **Yanıt yok ve son gönderimden > 2 ms geçti:** timeout kopyası gönderilir. Koşullar:
     - Emir **alış** olmalı.
     - Emrin timeout kopyası sayısı `< timeoutOrderCount` olmalı. Config'te yoksa varsayılan 2'dir.
     - Kopya ana token'ı değiştirmez. `-110023` ile reddedilen timeout kopyası listeden düşer ve yeni bir kopyaya yer açar.
3. **Durma:** liste boşalınca veya son atış başladıktan **900 ms** sonra (`steady_clock`, "Sending guaranteed last shot timed out!" CRIT). Seans 900 ms içinde açılmazsa kalan emirler gönderilmemiş kalır.

Her gönderim `all_sent_orders`'a eklenir. Amaç: seans açılmadan önce `-110023` alan emri açılış anında yeniden göndererek kuyruğun önüne geçmek.

### 3.6 Gönderim sonrası

Bütün thread'ler join edilince sırayla şunlar olur:

1. **`BulkInsertStrategyOrder(all_sent_orders)`:** gönderilen her kopya `STRATEGY` tipiyle DB'ye yazılır. Böylece servis yeniden başlarsa emirler geri yüklenir.
2. **2 sn uyku** (`sleep_for(seconds(2))`). Kabuller gelsin diye beklenir. Süre gönderim başından değil, **son atış bitip thread'ler join edildikten sonra** başlar.
3. **`CancelRepeatedOrders`:**
   - `all_sent_orders` içinde kabul edilmiş token'lar şu anahtarla gruplanır: `AccountStrategy.Id + Price + Side + Quantity + TimeInForce + RegularOrderType` (ayraçsız string birleştirme).
   - Gruplama **bütün OUCH kullanıcıları** üzerindendir.
   - Grubun hesabında `IsCancelAllowed` (DB `iscancelallowed`) açıksa, kabuller `Timestamp`'e göre sıralanır. İlk `OrderRepeatRemainingCount` (DB `orderrepeatremaining`) adet tutulur, kalanlara `SendOrderAsync(CancelOrder)` gönderilir.
   - İptal izni yoksa hiçbir kopya iptal edilmez.
4. **`WorkAfterSendRepeatableOrders(ouch_orders, is_morning)`:** `ouch_orders`, seçilen **bütün** tekil DB satırlarıdır; gönderilip gönderilmediğine bakılmaz.
   - Her satır `RemoveOrder` ile DB'den silinir ve GUI'ye `kOrderCanceled` gider.
   - Sabah (`MORNING`, `MORNING_VIOP`): satırlar `is_active=false` ile `BulkInsertMorningOrder` üzerinden yeniden yazılır (yeni id). Ana olanlar `PublishCollectiveOrders(kMorningOrder)` ile GUI'ye "pasif" olarak yayınlanır.
   - Teorik: satırlar yalnız silinir.
5. **`DisconnectMorningOrderUsers(username)`:** akıştaki her kullanıcı için çağrılır (§7).

## 4. Açılış akışı: `MAOSdkManager::SendOpeningOrders(config, group)`

`StartProperly` her grup için, config bloğu varsa (`configured`), bir detached thread açar. Blok yoksa WARN basılır ve akış kapalı kalır.

**Grup üyeliği (`BelongsToOpeningGroup`):**

| Grup | Enstrüman |
|------|-----------|
| `kDerivative` | vadeli piyasası |
| `kEquity` | pay piyasası, varant/sertifika değil, `is_yip` değil |
| `kWarrant` | pay piyasası ve `IsWarrantOrCertificate()`. Config yorumu: finansal ürün 14/18. 10:00–10:02 arası yalnız piyasa yapıcı kotasyonu olduğu için 10:02'de gider. |
| `kYip` | `is_yip` ve pay ve varant/sertifika değil |

Vadeli veya varant satırındaki `is_yip` bayrağı yok sayılır.

**Zamanlama:**
- `remaining = T − now` (sn) < **30** ise "too late" log basılır ve dönülür.
- Çekme anı T − 1 dk'dır. Beklemede `sleep_for(200 µs)` yoklaması kullanılır.
- Çekmede `GetOpeningOrders(kOuch)` ve `GetOpeningOrders(kFix)` birleştirilir. Aktif ve gruba ait satırlar `enter_orders` haritasına DB token'ı anahtarıyla konur.
- Gönderim başlangıcı: `now − T ≥ millisecond` olana kadar 200 µs yoklama yapılır.

**Gönderim döngüsü:** Her 75 µs'de bir tur atılır, toplam süre üst sınırı **2000 ms**'dir (`timeout_duration`, `system_clock`). Satır başına davranış:

- **Kullanıcı seçimi:**
  - FIX satırı: `getNextFixClient(market, partition, account)`.
  - OUCH satırı: `NextClientForAccount(account+market)`. Bu, hesabın o piyasadaki OUCH kullanıcıları arasında round-robin'dir; `onlyMorningOrderUser` olanlar da dahildir.
- `SubmitEnterOrder(..., preserve_single_order=true, register=true)` ile gönderilir. Token SDK'dan gelir.
- **Ret `-110023`:** token temizlenir, sonraki turda yeniden gönderilir. Bekleme yoktur; tur aralığı ~75 µs'dir.
- **Başka bir ret:** satır "bitti" sayılır (`is_accepted=true` olarak işaretlenir) ve yeniden denenmez.
- **Kabul:** satır biter.
- Döngü bütün satırlar bitince veya 2 sn dolunca sona erer.

**Sonrası:**
1. Gönderilen denemeler `BulkInsertStrategyOrder` ile `STRATEGY` olarak yazılır (`is_yip` korunur).
2. Gruba ait bütün aktif satırlar `RemoveOrder` ile silinir. Gönderilmemiş veya zaman aşımına uğramış satırlar da buna dahildir.
   - Önce ana emirler işlenir. Silinemeyen ana emrin alt emirlerine dokunulmaz.
3. Vadeli dışındaki gruplarda silinen satırlar `is_active=false` ile `BulkInsertOpeningOrder` üzerinden yeniden yazılır ve `PublishCollectiveOrders(kOpeningOrder)` ile yayınlanır. Vadeli satırlar yalnız silinir.

## 5. YİP (Yakın İzleme Pazarı)

- `SendYipOpeningOrders` tek bir thread'dir. `yip.sessions` listesini saate göre sıralar ve her seans için sırayla `SendOpeningOrders(session, kYip)` çağırır.
- 30 sn'den yakın veya geçmiş seanslar "too late" ile atlanır. Servis gün içinde başlatılırsa bir sonraki seanstan devam eder.
- Her seans kendi T − 1 dk anında `is_yip` satırlarını çeker, gönderir ve **pasife alır**. Bu yüzden seans N'nin çekiminden sonra girilen YİP satırı seans N+1'de gider.
- YİP bloğu yoksa akış kapalıdır. Equity thread'i bu durumda YİP bayraklı satırlar için "it will not be sent" CRIT basar ve satırlar hiç gönderilmez.
- ❓ doğrulanmadı: borsanın güncel YİP seans saatleri ([borsa-kurallari](../../00-genel/borsa-kurallari.md#seanslar)).

## 6. Teorik, akşam ve off-hours

- **Teorik:** §3 akışıdır. `EVENING` tipli DB satırlarını gönderir; GUI'de "akşam" diye girilen satırlar bunlardır. Gönderimden sonra satırlar silinir (§3.6).
  - Örnek config yalnız FIX satırı içerir (18:01:00.130). Bu yüzden OUCH protokollü `EVENING` satırları, `ouch` listesinde `theoric` satırı yoksa **hiç gönderilmez**.
- **`offhours_invertor`:**
  - `OrderManager::Start` içinde detached bir thread'dir.
  - `eveningSessionStart` (yerel saat:dk:sn) anına kadar `sleep_until` ile uyur, sonra `offhours = kOffHourOrders` yapar.
  - Saat geçmişse hemen ayarlar. Gün içinde geri alınmaz (servis günlük yeniden başlatılıyor varsayımı ❓).
  - Bayrak yalnız `MAOSdkManager::SendOrderAsync` yolunda (`ouch_order.SetOffHours(this->offhours)` → `msg.off_hours`) emre işlenir. Bu yol `OrderDispatcher` üzerinden gelen AlgoProd/HFT/GUI strateji emirleridir.
  - Toplu akışların kullandığı `SendOrderWithUsername`, `SendPackagedOrderWithUsername` ve `SendOpeningOrders` bayrağı set etmez; bunlar `kNormalHours` gider.

## 7. Handoff ile ilişki

Ayrıntı: [sdk-ve-oturumlar.md](sdk-ve-oturumlar.md) ve [sistem haritası](../../00-genel/sistem-haritasi.md#ouch-handoff-sabah-devri).

**Tetikler:**
1. **Akış sonu:** §3.6 adım 5. Her tekrarlı akış, `GetUsers(protocol, part)` ile aldığı kullanıcılar için `DisconnectMorningOrderUsers(username)` çağırır.
   - `users` haritasında (OUCH) olmayan kullanıcılar (FIX) ve `OnlyMorningOrderUser=false` olanlar atlanır.
   - Akışta seçilen satır yoksa (`0` emir) akış erken döner ve disconnect çağrılmaz.
2. **Zaman:** `OrderServiceApplication::Start`, `ouch` listesindeki `type == "morning"` her satır için çalışır:
   - Şimdi T'den (saniye hassasiyetinde, ms yok) önceyse T + **30 sn**'de `TriggerOuchDisconnect` çalıştıran bir thread kurar.
   - Sonraysa hemen tetikler.
   - `TriggerOuchDisconnect`, henüz devredilmemiş bütün `onlyMorningOrderUser` kullanıcılarını devreder.
   - `morning_viop` ve FIX satırları bu tetiği kurmaz.

Devir sırası:
1. Uygulama kullanıcısının bağlanması beklenir (500 ms yoklama).
2. `markIntendedDown` + `sdk_->disconnectUser` çağrılır.
3. MARpc `UserDisconnected` gönderilir.

## 8. Örnek zaman çizelgesi (örnek `config.yaml`, servis 09:00'dan önce başlamış)

| Saat (yerel) | Ne olur |
|------|---------|
| 09:19:00 | `morning_viop` satırları çekilir (T−60 sn) |
| 09:20:00.050 | VİOP sabah: partition 1 OUCH kullanıcı thread'leri başlar. Round'lara 55 ms yayılır, son atış ≤ 900 ms sürer. Join + 2 sn sonra iptal, DB, disconnect. |
| 09:39:00 | OUCH sabah, FIX sabah ve vadeli açılış satırları çekilir |
| 09:40:00.100 | Vadeli açılış grubu gönderilir (≤ 2 sn) |
| 09:40:00.136 | FIX sabah (duration 24 ms) |
| 09:40:00.144 | OUCH sabah (duration 16 ms, `timeoutOrderCount` 2). Round'lar ~09:40:00.160'a kadar sürer, ardından son atış (≤ 900 ms). |
| ~09:40:03+ | 2 sn bekleme → `CancelRepeatedOrders` → sabah satırları pasif → `DisconnectMorningOrderUsers` |
| 09:40:30 | Zamana bağlı `TriggerOuchDisconnect` (sabah 09:40:00 + 30 sn); kalan `onlyMorningOrderUser` kullanıcıları devredilir |
| 09:59:00 | Pay açılışı ve YİP seans 1 satırları çekilir |
| 10:00:00.035 | YİP seans 1 |
| 10:00:00.050 | Pay açılışı (varant/sertifika ve YİP hariç) |
| 10:01:00 / 10:02:00.162 | Varant/sertifika çekimi / gönderimi |
| 12:59:00 / 13:00:00.040 | YİP seans 2 |
| 13:59:00 / 14:00:00.045 | YİP seans 3 |
| 18:00:00 / 18:01:00.130 | Teorik (FIX, `EVENING` satırları) çekim / gönderim, duration 20 ms |
| 19:00:00 | `offhours` = `kOffHourOrders` |

Bu saatler örnek config'tendir. Müşteri değerleri [kalicilik-ve-config.md](kalicilik-ve-config.md)'de.

## 9. Thread modeli

| Thread | Sayı | Tür | Yaşam |
|--------|------|-----|-------|
| `InsertOrdersToDatabaseAsync`, `InsertPositionToDatabaseAsync` | 1+1 | detached `std::thread`, bloklayan kuyruk | süreç boyu |
| `offhours_invertor` | 1 | detached, `sleep_until` | `eveningSessionStart`'a kadar |
| Tekrarlı akış koordinatörü | config satırı başına 1 (`ouch` + `fix`) | detached `std::thread`, varsayılan politika | gönderim + 2 sn + iptal + DB + disconnect sonrası biter |
| Gönderici (`SendRepeatableOrdersToExchangeMarket`) | akış başına kullanıcı başına 1 | `pthread`, FIFO 99 (veya OTHER), `coreToPin` | T'den ~1 dk önce doğar, son atış bitince biter; koordinatör join eder |
| Açılış | grup başına 1 (derivative/equity/warrant) | detached, varsayılan politika | gönderim + DB sonrası biter |
| YİP | 1 | detached | son seanstan sonra biter |
| Zamana bağlı handoff | sabah satırı başına 1 | detached, `sleep_until` | T+30 sn |

- Paylaşılan yapılar: `all_sent_orders`'ı `all_sent_orders_mtx` korur.
- Kabul/ret haritaları (`accepted_orders`, `rejected_orders`) SDK callback thread'lerinde yazılır. Son atış `GetOrderAccepted` / `GetOrderRejected` ile kilitli okur. Açılış döngüsü de kilitli okur.
- `GetTimePoint` ve açılış saat hesabı `localtime` statik tamponu nedeniyle `time_mtx` ile korunur.

## 10. Şüpheli

Her madde: tür, açıklama, kod yeri.

1. **bug? — Son atışta pointer anahtarlı haritalar `erase` sonrası kayıyor.**
   - `RepeatedLastShotStrategy::execute`, `order_timeout_map` ve `timedoutOrder_tokens_map`'i `&vector[i]` pointer'ıyla anahtarlıyor.
   - `unique_repeatable_last_shot_orders.erase(...)` sonraki elemanları kaydırdığı için bir emrin timeout token'ları ve zaman damgası başka bir emre ait görünür.
   - Sonuç: bir emir, başka bir emrin timeout kopyası kabul edildi diye `is_get_any_accept` ile kabul edilmiş sayılıp listeden düşebilir. Timeout zamanlaması da yanlış emirden okunur.
2. **bug? — Son atış FIFO 99 thread'inde uykusuz döngü.**
   - `RepeatedLastShotStrategy::execute`'un `while` döngüsü, `-110023` dışındaki yollarda uyumadan ≤ 900 ms döner.
   - Gönderici `coreToPin` ile SDK recv/callback thread'iyle aynı çekirdeğe sabitlenirse kabul ve retlerin işlenmesi gecikebilir. Bu da gereksiz timeout kopyalarına yol açar. doğrula: prod çekirdek yerleşimi.
3. **bug? — `CancelRepeatedOrders` `accepted_orders`'ı kilitsiz okuyor.**
   - `OrderManager::CancelRepeatedOrders`, `enter_order_mtx` almadan `accepted_orders.find` yapıyor. Aynı anda SDK callback'leri haritaya yazabilir (geç kabuller).
   - Ayrıca `user_accounts[...]` `operator[]` ile bilinmeyen hesap için boş `Account` ekleyebilir.
4. **bug? — İptal grup anahtarı ayraçsız.**
   - `CancelRepeatedOrders` içindeki `ss << Id << Price << Side << Quantity << TIF << Type` ifadesinde farklı (id, fiyat) çiftleri aynı string'i üretebilir (ör. id 1 / fiyat 2345 ile id 12 / fiyat 345).
   - Bu durumda başka bir hesap-stratejinin kabulleri aynı gruba girer ve iptal edilebilir. Olasılığı düşük.
5. **doğrula — İptal izni olmayan hesapta kopyalar kalıcı.**
   - Tekrarlı satırlar kullanıcılara kopyalanır; iptal izni yoksa fazla kopyalar kalabilir. Güncel `26e9a02` tekrarsızları böler; eski “her tekrarsız satış N kez gider” iddiası bu commit'e taşınmaz.
   - `OrderRepeatRemainingCount=0` ise de kabul edilen **bütün** kopyalar iptal edilir. Kasıtlı mı?
6. **doğrula — `morning_viop` sonrası disconnect pay OUCH kullanıcılarını da kapsıyor.**
   - `UserService::GetUsers(protocol, partition, mode)` piyasaya göre süzmüyor. VİOP sabah akışı (örnek 09:20) bittiğinde `DisconnectMorningOrderUsers`, partition'daki **pay** `onlyMorningOrderUser` kullanıcıları için de çağrılıyor.
   - Bu kullanıcılar 09:40 pay sabah akışından önce HFT'ye devredilmiş olur. Sonra `SendOrderWithUsername` ile gönderilen emirler bağlı olmayan kullanıcıya gider.
   - Aynı nedenle, bir hesap iki piyasada izinliyse sabah emirleri yanlış piyasanın kullanıcısından da gönderilir. `PrepareAccountFields` kullanıcının piyasasını kullanır.
7. **doğrula — Açığa satış (`kShortSell`) sabah satırları seçilmiyor.**
   - `PartitionRepeatableNoNRepetableOrders` yalnız `kBuy`/`kSell` süzüyor. `SHORT` yönlü `MORNING`/`EVENING` satırları gönderilmez.
   - `ouch_orders`'a da girmedikleri için pasife alınmaz, aktif kalırlar.
8. **doğrula — Kapasite yetmezse alışlar hiç gitmiyor.**
   - `PrepareOuchOrders`'ta `Capacity ≤ Σtekrarsız` veya `(Capacity−Σtekrarsız) < Σtekrarlı` ise `ouch_repeat=0` olur. Bu durumda o kullanıcıdan tekrarlı emirler (bütün alışlar) **bir kez bile** gönderilmez; son atış listesine de girmez.
   - Buna rağmen `WorkAfterSendRepeatableOrders` satırları pasife alır. `RepeatCount=0` olan kullanıcıda da durum aynıdır.
9. **doğrula — Gönderilmemiş satırlar da pasife alınıyor.**
   - Sabah: `WorkAfterSendRepeatableOrders` bütün seçilmiş satırları işler.
   - Açılış: silme döngüsü gruptaki bütün aktif satırları işler.
   - Bu nedenle kullanıcı bulunamayan, 2 sn / 900 ms içinde kabul almayan veya başka kodla reddedilen satırlar GUI'de "pasif" görünür. Gönderilmediklerine dair ayrı bir durum yoktur.
10. **bug? — Retry kopyaları DB'ye iki kez yazılıyor olabilir.**
    - `RepeatedLastShotStrategy`'nin `-110023` ve timeout yeniden gönderimleri `insert_to_db=true` ile `InsertOrderToDatabaseAsync`'e gidiyor. Aynı kopyalar `all_sent_orders` üzerinden `BulkInsertStrategyOrder` ile tekrar yazılıyor.
    - doğrula: DataService token'a göre upsert ediyor mu?
11. **bug? — GUI toplu emir vektörleri kilitsiz.**
    - `OrderServiceImpl::SendOrder` `morningOrders` / `openingOrders` / `eveningOrders` **üye** vektörlerine kilitsiz yazıp temizliyor. Eşzamanlı iki `SendOrder` RPC'si satırları karıştırabilir veya kaybedebilir.
12. **doğrula — Alt emir eşleşmesi `PassThrough` ile.**
    - `OrderService::BulkInsertOrder` alt emirleri ana emre `PassThrough` (custom_data) eşitliğiyle bağlıyor.
    - Aynı istekte aynı custom_data'lı (ör. boş) iki ana emir varsa her alt emir iki ana emrin isteğine de eklenir. Hiçbir ana emirle eşleşmeyen alt emir yazılmaz.
13. **bug? — `pthread_create` hatasında tanımsız davranış.**
    - `OrderManager::SendRepeatableOrders(bulkOrders, …)`, `pthread_create` başarısız olursa `continue` ediyor ama `threads[i]` ilklenmemiş kalıyor ve sonra `pthread_join` ediliyor.
    - `bulkOrders[i].release()` edilen nesne de sızıyor.
14. **doğrula — Açılışta `-110023` yeniden gönderimi ~75 µs aralıkla.**
    - `SendOpeningOrders`'ta sabah son atışındaki 500 µs koruması yok. 2 sn boyunca satır başına binlerce ret/yeniden gönderim olabilir.
    - OUCH kullanıcısı her denemede round-robin ile değişir; devredilmiş (bağlantısı kesik) `onlyMorningOrderUser` da seçilebilir.
15. **doğrula — Geç başlatma sessizce akışı atlıyor.**
    - Sabah/teorik için T−5 sn, açılış/YİP için T−30 sn sonrası başlatmada akış dönüyor.
    - Satırlar aktif kalır, gün içinde başka bir akış onları göndermez (log: "too late" yalnız açılışta).
16. **doğrula — Sıralama karşılaştırıcısı katı zayıf sıralama değil.**
    - `PartitionRepeatableNoNRepetableOrders`'daki `sort_order_tuples`, aynı enstrümanda alış ile satış karşılaştırılınca `a`'nın yönüne göre ters kural uyguluyor. `repeatSellOrders: true` iken `stable_sort` için tanımsız sıralama riski var.
    - Ayrıca tuple dizileri yığında VLA olarak tutuluyor.
