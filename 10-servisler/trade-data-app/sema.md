---
kapsam: trade-data-app'in MySQL şeması — tablolar, kolonlar, ilişkiler, kim yazar/okur, ayar saklama modeli, şema yönetimi (koddan çıkarılmış)
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-22
durum: taslak
---

# trade-data-app — MySQL şeması

Repoda **şema tanımı (CREATE TABLE) yok, migration aracı yok.** Buradaki kolon listeleri `pkg/db/mysql/*.go` içindeki SQL'den ve `pkg/db/models/*.go` struct'larından çıkarıldı. Bir kolonun tipi, NULL olup olmadığı ve hangi kolonlarda unique key olduğu koddan kesin görünmüyor. `ON DUPLICATE KEY UPDATE` kullanılan yerlerde bir unique key var demektir, ama hangi kolonlarda olduğu bilinmiyor ve `❓` ile işaretli. Kesin şema canlı DB'den (`SHOW CREATE TABLE`) alınmalı.

Servisin genel yapısı: [`README.md`](README.md). API uçları: [`api.md`](api.md). ITCH ve veri akışı: [`veri-akisi.md`](veri-akisi.md). VERDA/AKD/BYF: [`entegrasyonlar.md`](entegrasyonlar.md). DB bağlantı ayarları: [`config.md`](config.md).

## Erişim katmanı

| Dosya | İçerik |
|-------|--------|
| `pkg/db/database.go` | `Database` interface'i, tüm DB fonksiyonlarının listesi |
| `pkg/db/repository.go` | `CreateDatabase`: yalnızca `DatabaseTypeMysql` destekleniyor |
| `pkg/db/mysql/mysqldb.go` | `MysqlDB` singleton. Bağlantı dizesi `multiStatements=true&parseTime=true`. `Login` (Application_Users) ve `AdminLogin` (Admins) burada, diğer fonksiyonlar alt nesnelere yönlendiriliyor. |
| `pkg/db/mysql/ouchdb.go` (`OrdersDB`) | order-service ihtiyaçları: OUCH/FIX kullanıcıları, emir, pozisyon, enstrüman, hesap–strateji, endeks |
| `pkg/db/mysql/algodb.go` (`AlgoDB`) | Enstrüman yazımı, strateji ayarları, arbitraj, fon, skor, mum (TimeBased) |
| `pkg/db/mysql/guidb.go` (`GuiDB`) | GUI girişi/OTP, izinli stratejiler, paneller |
| `pkg/db/mysql/admin_db.go` (`AdminDB`) | Admin CRUD: Users, Ouchs, Accounts ve ilişki tabloları |

ORM yok, düz `database/sql` kullanılıyor. Yazımların çoğu transaction'sız. Transaction kullananlar: `SetStrategySettings`, `SetPanelData`, `InsertInstrumentsBulk`, `UpdateAllInstrumentsInfo`, `InsertTimeBasedData`, Admin'in `InsertOrderUser`/`UpdateOrderUser`/`CreateUserAccount`/`UpdateUserAccount` fonksiyonları ve `SetIndiceInstruments`'in insert kısmı.

## İlişki haritası

```
Users ──< Users_Accounts >── Accounts ──< Users_Ouch >── Ouchs ──> Application_Users
                               │                                        ▲
                               ├──< Account_Allowed_Strategies >── Strategies ──< Applications_Strategies
                               │                                    │   │
                               └──< Accounts_Strategies ────────────┘   └──< StrategyAttributes
                                     │ (account, strategy, instrument,           │
                                     │  identifier, applicationUser ─────────────┼──> Application_Users)
                                     │                                           │
                                     ├──< StrategySettings >─────────────────────┘
                                     ├──< Positions
                                     ├──< Orders (+ mainOrderId → Orders.id)
                                     ├──< Arbitrage (spotStrategy, derivativeStrategy)
                                     │      └──< Arbitrage_Package ──< Arbitrage_Basket_Package
                                     ├──< Fund (fundStrategy) ──< Fund_Package ──< Fund_Und_Package (accountStrategy)
                                     └──< Strategy_Panels (strategy, secondStrategy) >── Panels (pk) ──> Users

Instrument ──< Instrument_Indices (indiceId, instrumentId → Instrument.id)
Instrument ──< Instrument_Futures (underlyingInstrument)
Instrument ··· Accounts_Strategies.instrument, Scores.instrument, TimeBased/Volatility.instrument (yalnızca id ile; FK var mı ❓)
Admins: bağımsız
```

Soru → yol:
- **OUCH kullanıcısı hesaba nasıl bağlanıyor:** `Ouchs.id` → `Users_Ouch.ouch`, `Users_Ouch.userAccount` → `Accounts.id`. Bir Ouch birden çok hesaba bağlanabilir, bir hesap da birden çok Ouch'a. Her Ouch tek bir `Application_Users` satırına bağlı (`Ouchs.applicationUser`).
- **GUI kullanıcısı hangi hesapları görür:** `Users_Accounts(user, account)`.
- **Hesap hangi stratejiyi açabilir:** `Account_Allowed_Strategies(account, strategy)`. Bu bir izin. Çalışan strateji örnekleri `Accounts_Strategies` tablosundadır.
- **Bir stratejinin ayarları nerede:** `StrategySettings`. Satırlar `Accounts_Strategies.id` ve `StrategyAttributes.id` ile bağlanır. Ayrıntı aşağıda, "Ayar saklama modeli" bölümünde.

## Tablolar

Tipler Go tarafındaki karşılıklarıdır (struct alanı veya Scan hedefi). DB'deki kolon tipi kesin değil.

### Kimlik ve yetki

**`Users`**: GUI (mtrader-trade-ui) kullanıcıları.
- Kolonlar: `id`, `username`, `password` (MD5 hex; `CreateUser` hash'liyor, `ResetPassword` hash'liyor), `email`, `phone`, `otpEnabled`, `lastOtp`, `lastOtpTime` (unix **saniye**), `resetPasswordToken` (sıfırlamadan sonra NULL).
- Yazan: Admin `InsertUser`/`UpdateUser`/`DeleteUser`; GUI `SetOtpCode` (son OTP'den 120 sn geçmediyse güncellemez), `ForgetPassword`, `ResetPassword`.
- Okuyan: `GuiLogin`, `CheckOtpCode` (kod 120 sn geçerli), Admin `GetUsers`/`GetUser`.
- ❓ doğrulanmadı: `UpdateUser` `user.Password` doluysa onu olduğu gibi yazıyor. Hash'in API katmanında alınıp alınmadığı kontrol edilmedi (`admin_api.go`, `UpdateUser`).

**`Admins`**: Admin paneli kullanıcıları. Kolonlar: `id`, `username`, `password` (MD5 hex). Yalnızca `AdminLogin` okuyor. Kodda bu tabloya yazan yer yok.

**`Application_Users`**: Servis (uygulama) hesapları. gRPC `Login` bunlarla yapılır (order-service, HFT, AlgoProd). Ayrıca strateji ve emirlerin hangi motora ait olduğunu belirleyen sahiplik anahtarıdır.
- Kolonlar: `id`, `username`, `password` (MD5 hex).
- Okuyan: `Login`, `GetApplicationUsers`. Çoğu sorgu `(SELECT id FROM Application_Users WHERE username=?)` alt sorgusuyla username'den id çözüyor. Kodda bu tabloya yazan yer yok.

**`Accounts`**: Müşteri/işlem hesabı. Wire'daki `account` / `accountName` buradaki `accountName`'dir.
- Kolonlar: `id`, `accountName` (hesap adı string olarak birçok alt sorguda anahtar gibi kullanılıyor, bkz. `getRelatedUserId`), `orderCapacity`, `remainingCount` (Go: `OrderRepeatRemaining`), `isCancelAllowed`, `clientType` (Go: `ClientType.Id`; ayrı bir tip tablosu kodda yok), `agencyFundCode` (nullable), `repeatOnlyTopLevels`, `repeatLevels`.
- `OrderUser.OrderRepeatCount` alanındaki yoruma göre iptal sonrası bekletme (hold-after-cancel) ayarı `Accounts` tablosunda kalıyor; sabah turu sayısı ise `Ouchs.repeatCount`'ta.
- Yazan: Admin `CreateUserAccount`/`UpdateUserAccount`/`DeleteUserAccount`.
- Okuyan: `GetOrderUsers` (order-service'e Ouch ile birlikte gider), GUI `GetAccounts`, Admin `GetUserAccounts`/`GetUserAccount`.

**`Ouchs`**: OUCH ve FIX emir oturumu kullanıcıları (Go: `OrderUser`). Adında "Ouch" geçiyor ama FIX kullanıcıları da burada tutulur; ayırt eden kolon `protocol`.
- Kolonlar: `id`, `username`, `password` (**düz metin**; OUCH/FIX login için gerekiyor), `pendingPassword` (FIX şifre yenilemesi sırasında BIST'e gönderilmiş ama henüz kabul edilmemiş aday), `ip`, `port`, `secondaryIp`, `secondaryPort`, `capacity`, `repeatCount` (OUCH başına sabah turu sayısı), `coreToPin` (order-service sabah gönderim thread'inin CPU çekirdeği; `-1` = pinlenmemiş; API'de alan yoksa `-1`), `relatedMarket` (int32), `isActive`, `isProduction`, `protocol` (`ProtocolType`: 0=OUCH, 1=FIX, 2=None), `senderSubId`, `senderCompId`, `targetCompId`, `onlyMorningOrderUser`, `applicationUser` (→ `Application_Users.id`).
- Yazan: Admin `InsertOrderUser`, `UpdateOrderUser`, `DeleteOrderUser`; DataService `UpdateOrderUserPassword` (`password` ve `pendingPassword` tek UPDATE ile yazılır, kabul edilmiş şifre her zaman bu iki kolondan birindedir). `UpdateOrderUser` şifre gerçekten değiştiyse `pendingPassword`'ü temizler.
- Okuyan: `GetOrderUsers(protocol)`. Bu sorgu `isActive=1` ve verilen protokoldeki Ouch'ları, bağlı hesapları ve hesapların `Accounts_Strategies` satırlarını (GROUP_CONCAT `id:identifier:strategy:instrument`, `|` ayraçlı) tek seferde döndürür. **Hiç hesaba bağlı olmayan Ouch dönmez** (`INNER JOIN Users_Ouch`).
- ⚠ `InsertOrderUser` `applicationUser` kolonunu **sabit `4`** ile yazıyor. `UpdateOrderUser` bu kolonu hiç güncellemiyor. ❓ doğrulanmadı: 4'ün hangi Application_User olduğu (muhtemelen order-service, ama DB'ye bakılmadı).

**`Users_Accounts`** (`user`, `account`): Users ↔ Accounts, N:M. `AddUserToAccount` `INSERT IGNORE` kullanıyor, bu yüzden (user, account) üzerinde unique key olmalı ❓. Admin update fonksiyonları ilişkiyi tamamen silip baştan yazar.

**`Users_Ouch`** (`ouch`, `userAccount`): Ouchs ↔ Accounts, N:M. İsimdeki "Users" yanıltıcı: `userAccount` kolonu `Accounts.id`'yi gösterir.

**`Strategies`**: Strateji tipleri. Kolonlar: `id`, `strategyName` (ör. `ARBITRAGE`, `HFT_WARRANT_ADVANCED`). **`id` doğrudan GUI'nin `strategyType` değeridir**, auto-increment'e bırakılmaz (`scripts/sql/hft_warrant_advanced.sql`: HFT_WARRANT=13, HFT_WARRANT_ADVANCED=15). `models.Strategy`'deki `ServerIp`/`ServerPort` alanları hiçbir sorguda okunmuyor. Okuyan: `GetStrategies`. Kodda bu tabloya yazan yer yok, satırlar SQL script'iyle ekleniyor.

**`Account_Allowed_Strategies`** (`account`, `strategy`): Hesaba izin verilen strateji tipleri. GUI'deki strateji listesi buradan gelir (`GetAccountAllowedStrategies`, `Users_Accounts` üzerinden kullanıcıya filtrelenir). Admin yazar; `AllowStrategyForAccount` `INSERT IGNORE` kullanıyor, bu yüzden unique key olmalı ❓.

**`Applications_Strategies`** (`strategy`, `applicationUser`): Strateji tipi → hangi uygulama kullanıcısı (motor). Okuyan: `GetApplicationStrategy(strategyName)`; ilk satırı alır. Kodda bu tabloya yazan yer yok. Not: GUI'nin strateji tipini dış uygulamaya eşlemesi kod içinde ayrıca yapılıyor (`getApplicationFromStrategyType`, bkz. [`README.md`](README.md)).

### Strateji örnekleri ve ayarları

**`Accounts_Strategies`**: Çalışan (veya bir kez kaydedilmiş) bir strateji örneği. Emir, pozisyon, ayar, arbitraj, fon ve panel satırlarının hepsi bu tablonun `id`'sine bağlanır. Wire'daki `AccountStrategyId` / `strategyId` (Orders, Positions) bu `id`'dir.
- Kolonlar: `id`, `strategy` (→ `Strategies.id` = strategyType), `account` (→ `Accounts.id`), `identifier` (strateji tanımlayıcısı, wire'da `StrategyIdentifier`), `instrument` (orderbook id), `timestamp`, `applicationUser` (→ `Application_Users.id`), `isOverallStrategy` (Go: `OverallStrategyVal` int32).
- Yazan: DataService `SetAccountStrategy` (`OrdersDB.SetAccountStrategy`), GUI `SetPanelData` (yeni panelde, eksik örnekleri ekler), arbitraj Excel import'u. Hepsi `INSERT ... ON DUPLICATE KEY UPDATE timestamp=?` kullanır.
- Unique key ❓: `verifyAccountStrategyExists` (account, instrument, identifier, applicationUser, strategy) ile arıyor; key büyük olasılıkla bu kolonlar üzerinde.
- ⚠ `timestamp` birimi tutarsız: `SetAccountStrategy` **ms**, `SetPanelData` **saniye** yazıyor.
- ❓ doğrulanmadı: Satır zaten varsa `SetAccountStrategy`'nin döndürdüğü `LastInsertId` güvenilir değil. `Panels`'teki `LAST_INSERT_ID(pk)` hilesi burada kullanılmamış. Bu durumda çağırana 0 veya yanlış id dönebilir.

**`StrategyAttributes`**: Strateji tipi başına izin verilen ayar anahtarları ve tipleri.
- Kolonlar: `id`, `strategy_id` (→ `Strategies.id`), `attribute_name` (wire'daki ayar anahtarı, ör. `Strategy_Start`, `Warrant_List`), `value_type` (protobuf Any TypeUrl, bkz. aşağı), `description` (nullable; GUI'ye `SettingsDescs` olarak gider).
- Okuyan: `SetStrategySettings` (anahtar doğrulama), `GetStrategySettings` (tip dönüşümü), `GetStrategyAttributes` (GUI tip kontrolü `checkStrategyAttributesType`, arbitraj Excel üretimi), `GetPanelData` (`Arb_Strategy_Type`).
- Kodda bu tabloya yazan yer yok, satırlar SQL script'iyle ekleniyor.

**`StrategySettings`**: Strateji örneği başına ayar değerleri (EAV).
- Kolonlar: `attribute` (→ `StrategyAttributes.id`), `accountStrategy` (→ `Accounts_Strategies.id`), `settingsVal` (string). Uzun JSON listeleri için kolonun `TEXT` olması gerekiyor; script `ALTER TABLE StrategySettings MODIFY COLUMN settingsVal TEXT` notunu düşüyor, eski kurulumlarda kolon hâlâ varchar olabilir.
- Unique key ❓ (attribute, accountStrategy): yazım `ON DUPLICATE KEY UPDATE settingsVal=?` ile yapılıyor.
- Yazan: AlgoService `SetStrategySettings` (HFT/AlgoProd), arbitraj Excel import'u. Okuyan: AlgoService `GetStrategySettings(applicationUser)` (motor açılışta kendi ayarlarını geri yükler), GUI Excel export, `GetPanelData`.

### Emir ve pozisyon

**`Orders`**: order-service'in kalıcı emirleri. `scripts/sql/orders_isyip.sql` yorumuna göre bunlar açılış (sabah) emirleridir: order-service işaretli satırları belirli seans saatinde gönderir. ❓ doğrulanmadı: başka `type` değerlerinin de burada tutulup tutulmadığı; `GetOrders` `type` ile filtreleyebiliyor.
- Kolonlar: `id`, `quantity` (uint64, lot), `price` (uint32; ❓ raw tamsayı fiyat olması bekleniyor, ölçeği order-service tarafında doğrulanmalı), `side`, `strategy` (→ `Accounts_Strategies.id`), `type` (OrderType), `applicationUser` (→ `Application_Users.id`; insert'te username'den çözülür), `orderToken`, `customData`, `customDataSize`, `timestamp` (insert anı, unix **ms**), `protocol`, `timeInForce`, `regularOrderType`, `isActive`, `isMainOrder`, `levelCount`, `isYip` (TINYINT(1) NOT NULL DEFAULT 0; Yakın İzleme Pazarı bayrağı), `mainOrderId` (nullable → `Orders.id`; alt emirlerin ana emri).
- `models.Order`'daki `ApplicationType`, `LatencyWritingNs`, `LatencyNetworkNs`, `LatencyBistNs`, `InternalOuch` alanları DB'ye **yazılmıyor**. `GetOrders` `ApplicationType`'ı doldurmadığı için bu alan hep 0 döner.
- Yazan: DataService `SetOrders` (`OrdersDB.SetOrders`):
  1. Önce her ana emir (`isMainOrder=1`) tek tek insert edilir ve DB id'si alınır.
  2. Alt emirler strateji bazında gruplanır. `mainOrderId` aynı çağrıdaki ana emirden alınır. Öyle bir ana emir yoksa istekteki `MainOrderId` ile `Orders`'ta `isMainOrder=1` bir satır aranır, bulunamazsa hata döner.
  3. `OrderId` 0 ise auto-increment kullanılır, değilse id açıkça yazılır.
  4. Dönüş değeri: ilk ana emrin DB id'si. Transaction yok; yarıda kalan çağrı kısmi kayıt bırakabilir.
- Silen: DataService `DeleteOrders`. Önce `mainOrderId = id` olan alt emirleri, sonra satırın kendisini siler. Transaction yok.
- Okuyan: DataService `GetOrders(orderType)`. `Application_Users` ve `Accounts_Strategies` ile INNER JOIN yapar; strateji satırı silinmiş emir dönmez.

**`Positions`**: Strateji örneği başına net pozisyon.
- Kolonlar: `id`, `strategy` (→ `Accounts_Strategies.id`), `position` (int32, lot, net), `price` (uint32, son fiyat; ❓ ölçek doğrulanmadı, muhtemelen raw).
- Yazan: DataService `SetPosition`: `INSERT ... ON DUPLICATE KEY UPDATE position=position+?, price=?`. Gelen değer **delta** olarak eklenir, mutlak değer olarak yazılmaz; `price` üzerine yazılır. Unique key ❓ `strategy`.
- Okuyan: DataService `GetPositions`. Enstrüman, hesap ve application user bilgisi JOIN ile `Accounts_Strategies` üzerinden gelir. `Positions` tablosunda enstrüman kolonu yok; `SetPosition` isteğindeki `InstrumentId` kullanılmıyor.

### Enstrüman ve referans veri

**`Instrument`**: Tüm enstrümanlar. C++ servisleri ve GUI'nin referans verisi buradan gelir.
- Kolonlar ve kaynakları:

| Kolon | Go alanı | Yazan | Not |
|-------|----------|-------|-----|
| `id` | `Id` | ITCH | ITCH `OrderBookID` |
| `symbol`, `longName`, `isinCode`, `currency` | | ITCH | |
| `decimalCount` | yazarken `DecimalPrice`, okurken `DecimalCount` | ITCH | Fiyat bölücü `10^decimalCount` |
| `nominalDecimal`, `strikePrice`, `decimalStrikePrx`, `expirationDate` | | ITCH | |
| `oddLotSize`, `roundLotSize`, `blockLotSize`, `nominalValue` | | ITCH (yalnız ilk insert) | Duplicate'te güncellenmez |
| `financialProduct` | | ITCH (yalnız ilk insert) | Endeks: `comvars.FinancialProductIndex` |
| `underlyingId`, `underlyingSymbol` | | ITCH | |
| `relatedMarket` | `Market` | ITCH (yalnız ilk insert) | |
| `relatedPart` | `Part` | ⚠ ITCH insert'inde **sabit `1`** | ITCH'ten gelen partition yazılmıyor; duplicate'te de güncellenmiyor |
| `relatedBazaar` | `Bazaar` | ITCH | `InstrumentBazaarType`: 1=Yıldız, 2=Ana, 3=Alt Pazar (yalnız pay) |
| `isActive` | | ITCH | Açılışta `itchEnabled` ise önce tümü 0 yapılır, snapshot'ta gelenler 1 olur |
| `lastPrice` | float64 | ITCH (yalnız ≠0 ise) ve TradeVerifier | Raw (×10^decimalCount). VERDA değeri ×1000 ile yazılıyor |
| `minPrice`, `maxPrice` | float64 | **Yalnız TradeVerifier** | Taban/tavan, raw. VERDA pay bülteni ×1000 |
| `maxOrderValue` | `MaxAllowedVol` uint64 | ITCH ilk insert (`maxAllowedLot`), sonra TradeVerifier | VERDA `MaxOrderVal` |
| `isBrutTakas` | | Yalnız TradeVerifier | Açılışta tümü 0 yapılır, sonra VERDA brüt takas listesine göre yazılır |

- ITCH yazımı: `itch.Manager.insertInstruments` → `InsertInstrumentsBulk`. Satır satır `INSERT ... ON DUPLICATE KEY UPDATE`; hata veren satır loglanıp atlanır. `lastPrice` 0 ise `INSERT_INSTRUMENT_WO_LAST_PRICE_UPDATE` kullanılır ve mevcut fiyat korunur.
- TradeVerifier yazımı: `cmd/dataapp/main.go` → `UpdateAllInstrumentsBurutTakasAsInactive` → `UpdateAllInstrumentsInfo` (`lastPrice`, `minPrice`, `maxPrice`, `maxOrderValue`, `isBrutTakas`; id ile, tek transaction). Yalnızca pay piyasası sabah dosyaları işleniyor; türevlerin `minPrice`/`maxPrice`'ı burada güncellenmiyor. Ayrıntı: [`entegrasyonlar.md`](entegrasyonlar.md), [`README.md`](README.md) açılış adım 6.
- ⚠ ×1000 sabit çarpan, `decimalCount`'u 3 olmayan bir enstrümanda ölçek uyumsuzluğu yaratır. ❓ doğrulanmadı: pay enstrümanlarının hepsinde `decimalCount=3` olup olmadığı.
- Okuyan: `GetInstruments`/`GetInstrumentById` (yalnız `isActive=1`; açılışta ITCH manager da buradan yükler), `GetAllIndices` (`_CF` içermeyen endeksler), `GetIndiceInstrumentInfo`, `GetAllInstrumentsInIndice`, `GetIndice`, `GetAllInstrumentsWithFuture`.

**`Instrument_Indices`**: Endeks → içerdiği enstrümanlar.
- Kolonlar: `indiceId` (→ `Instrument.id`, endeks), `instrumentId` (→ `Instrument.id`), `isTopIndice`, `isMainIndice`.
- Yazan: ITCH `createInstrumentIndices` → `SetIndiceInstruments`. Endeksin satırlarını siler (transaction dışında), sonra transaction içinde yeniden yazar.
- ⚠ `isMainIndice` kolonuna Go'daki `IsSectorIndice` yazılıyor. Kolon adına rağmen anlamı **"bu enstrümanın sektör endeksi"**. `GetIndice(isMainIndice=true)` bu yüzden sektör endeksini döndürür.

**`Instrument_Futures`** (`underlyingInstrument`): Vadeli kontratı olan dayanaklar (pay ve id=3). ITCH `createUnderlyingRelations` → `SetInstrumentsWithFutures` tabloyu tamamen silip baştan yazar. Okuyan: `GetAllInstrumentsWithFuture`. *(README'deki tablo listesinde yok.)*

**`TimeBased`** ve **`Volatility`**: Aynı kolon yapısında iki tablo (`TimeBasedTableType`). Tablo adı sorguya `fmt.Sprintf` ile ekleniyor.
- Kolonlar: `type` (`TimeBasedBlockType`: 0=Day, 1=Hour, 2=Minute, 3=Second, 4=Milisecond, 5=All), `timestamp` (Go `time.Time`), `instrument`, `high`, `low`, `open`, `close` (int64), `totalVolume`, `totalQty`, `totalSellVolume`, `totalSellQty`, `totalBuyVolume`, `totalBuyQty` (uint64).
- Unique key ❓ (type, timestamp, instrument): yazım upsert ile yapılıyor.
- Yazan: `history.CandleStickManager` (`historyManagerEnabled`). Okuyan: `history`, `pricedata`, `volatility` yöneticileri, AlgoService zaman serisi ucu, `GetIndiceOpeningPrice` (bugünün ilk `type=2` (dakika) mumunun `open` değeri).
- ❓ `GetIndiceOpeningPrice` `FROM_UNIXTIME(timestamp)` kullanıyor, oysa yazım `time.Time` ile yapılıyor (kolon büyük olasılıkla DATETIME). Kolon DATETIME ise bu filtre hiçbir satırla eşleşmez. *(`Volatility` README'deki tablo listesinde yok.)*

**`Scores`**: AKD tabanlı enstrüman/endeks skorları.
- Kolonlar: `instrument`, `timestamp` (`time.Time`), `score` (int32), `dsDaScore` (float64), `decision` (`DecisionType`: 0=None, 1=Buy, 2=Sell, 3=CloseBuy, 4=CloseSell), `isTired`, `isProperBuy`, `isProperSell`.
- Yazan: `extdata/akd` skor hesaplayıcıları ve AlgoService `SetInstrumentScores` (upsert). Okuyan: `GetInstrumentScores` (timestamp DESC, LIMIT).
- ❓ Upsert'in unique key'i bilinmiyor. Key `instrument` ise enstrüman başına tek satır kalır ve "son N skor" okuması anlamsızlaşır.

### Arbitraj ve fon (strateji kalıcılığı)

Strateji mantığı: [`20-stratejiler/arbitraj.md`](../../20-stratejiler/arbitraj.md), [`20-stratejiler/fon-takibi.md`](../../20-stratejiler/fon-takibi.md).

**`Arbitrage`**: Spot + türev strateji çifti.
- Kolonlar: `id`, `strategyType` (string; GUI eşlemesi `Arb_Strategy_Type` ayarındaki karakter kodu: `I`(73)=Faiz, `T`(84)=Çift Vade, `F`(70)=Spread, `R`(82)=Çift Vade Faiz; `GetPanelData`), `derivativePosition`, `spotPosition`, `totalProfit` (int64), `timestamp`, `spotStrategy`, `derivativeStrategy` (ikisi de → `Accounts_Strategies.id`; `strategyName='ARBITRAGE'` olan satırlar).
- Yazan: AlgoService `SetArbitrageData`, Excel import'u. `RemoveOld` ise eski çift önce silinir, ardından upsert yapılır. Paket yazım hataları **yutulur**: fonksiyon paket hatasında da `nil` döner.
- Okuyan: `GetArbitrageData`, `GetAllArbitrageData` (application user'a göre), `GetAllArbitrageDataByUser` (GUI kullanıcısına göre, `Users_Accounts` üzerinden), `GetAccountArbitrageStrategy`.

**`Arbitrage_Package`**:
- Kolonlar: `id`, `packageToken`, `arbitrage` (→ `Arbitrage.id`), `initContractQty`, `contractQty`, `arbitrageSide` (`ArbitrageSide`: 65=`A` Above, 66=`B` Below), `derivativePrice`, `underlyingPrice` (int64; ❓ ölçek), `underlyingExecQty`, `isActive`, `isCompleted`, `timestamp`, `interestRate` (float32), `actualOpeningMargin`, `actualClosingMargin`, `expectedOpeningMargin`, `expectedClosingMargin` (float32).
- Yazım `SetArbitragePackageData` ile yapılır: önce INSERT denenir, **herhangi bir hata** olursa `packageToken` ile UPDATE'e düşülür (unique key ❓ `packageToken`). Silme: `DeleteArbitragePackageData(token)`.
- `GetAllArbitrageData` margin kolonlarını okumuyor; `GetArbitrageData` ve `GetAllArbitrageDataByUser` okuyor.

**`Arbitrage_Basket_Package`** (`id`, `arbitragePackage` → `Arbitrage_Package.id`, `indiceInstrument`, `indiceInstrumentQty`): Endeks arbitrajında paket başına sepet bacakları.
- ⚠ bug adayı: `setArbitrageBasketPackage` UPDATE yolunda 3 placeholder'a 2 argüman veriyor (`id` eksik). Mevcut sepet satırının güncellenmesi her seferinde hata vermeli.

**`Fund`** (`id`, `spotPosition`, `fundPosition`, `totalProfit`, `timestamp`, `fundStrategy` → `Accounts_Strategies.id`), **`Fund_Package`** (`id`, `packageToken`, `packageSide` (`FundSide`: 0=None, 1=Buy, 2=Sell), `fundQty`, `initFundQty`, `isActive`, `isCompleted`, `fundPrice`, `fund` → `Fund.id`, `timestamp`), **`Fund_Und_Package`** (`id`, `package` → `Fund_Package.id`, `sentQty`, `acceptedQty`, `executedQty`, `meanPrice`, `weight`, `isCompleted`, `accountStrategy` → `Accounts_Strategies.id`):
- Yazan: AlgoService `SetFundData`. `Fund` upsert ile yazılır; `Fund_Package` için INSERT denenir, hata olursa `packageToken` ile UPDATE yapılır. `Fund_Und_Package` id ≤ 0 ise INSERT, değilse UPDATE.
- Okuyan: `GetFundData`, `GetAllFundDatas`.

### GUI panelleri

**`Panels`**: Kullanıcının kaydettiği strateji panelleri.
- Kolonlar: `pk` (auto-increment), `id` (panel adı/kodu, trim'lenir), `description`, `user` (→ `Users.id`), `strategy` (strateji tipi), `isActive`.
- Unique key (user, strategy, id): `SetPanelData`'daki yoruma göre. Upsert `LAST_INSERT_ID(pk)` ile mevcut satırın `pk`'sini döndürür.

**`Strategy_Panels`** (`panelId` → `Panels.pk`, `strategy` → `Accounts_Strategies.id`, `secondStrategy` → `Accounts_Strategies.id`, nullable; ikinci bacak, ör. arbitraj): Panel içindeki strateji örnekleri.
- Yazan: GUI `SetPanel` / Excel import (`SetPanelData`, tek transaction). Yeni panelde eski satırlar silinir ve eksik `Accounts_Strategies` satırları da açılır.
- Okuyan: `GetPanelData(user, strategy)`.

## Mekanizmalar

### Ayar saklama modeli (`StrategyAttributes` + `StrategySettings`)

- Ayarlar EAV modelinde tutulur. Bir strateji örneğinin (`Accounts_Strategies` satırı) her ayar anahtarı `StrategySettings`'te bir satırdır. Değer her zaman **string** olarak yazılır (`fmt.Sprintf("%v")`; `isComplexSetting` her zaman `false`, JSON listeleri de string olarak saklanır).
- **Yazım** (`AlgoDB.SetStrategySettings`, tek mutex ve tek transaction):
  1. `Accounts.accountName` → hesap id'si bulunur. Yoksa hata.
  2. (account, instrument, identifier, applicationUser username, strategyName) ile `Accounts_Strategies` satırı aranır. Yoksa hata: ayar yazılmadan önce strateji örneğinin `SetAccountStrategy` ile açılmış olması gerekir.
  3. Gelen her anahtar için (`strategyName`, `attribute_name`) eşleşen `StrategyAttributes` satırı aranır. **Tek bir anahtar bile eksikse tüm transaction rollback olur**: hata `StrategyAttribute not found for '<key>' in strategy '<name>'` olur ve o mesajdaki hiçbir ayar kaydedilmez. Motor genelde mesajın tamamını yolladığı için ayarlar restart'ta kaybolur.
- **Okuma** (`GetStrategySettings(applicationUser)`): Değer `value_type`'a göre çevrilir:

| `value_type` | Dönüş |
|--------------|-------|
| `type.googleapis.com/clientmodels.IntValue` | int32 |
| `type.googleapis.com/clientmodels.LongValue` | int64 |
| `type.googleapis.com/clientmodels.DoubleValue` | float64 |
| `type.googleapis.com/clientmodels.BoolValue` | bool |
| diğer her şey | string (`clientmodels.StringValue` dahil) |

  Parse hatası (ör. IntValue tipli satırda sayı olmayan değer) tüm çağrıyı hata ile döndürür; o application user'ın hiçbir ayarı yüklenmez.
- **Tip ailesi:** GUI `servicemodels.Gui*Value` yollar; `ConvertFields` bunu `clientmodels.*Value`'ya çevirir ve `checkStrategyAttributesType` TypeUrl'yi `value_type` ile karşılaştırır. Motorlar AlgoService'e `servicemodels.Algo*Value` ile yazar; `ConvertAlgoFields` tanımadığı TypeUrl'yi **sessizce atlar**. DB'deki `value_type` her zaman `clientmodels.*` ailesindendir.
- ⚠ `checkStrategyAttributesType` attribute'ları strateji tipine göre filtrelemiyor. İki strateji aynı `attribute_name`'i farklı `value_type` ile tanımlarsa birinin GUI komutu "Wrong type" hatası alır.

**Yeni bir wire (ayar) alanı eklerken DB'de ne gerekir:**
1. İlgili strateji için `StrategyAttributes`'a satır eklenmeli: `strategy_id` = `Strategies.id`, `attribute_name` = wire anahtarı (birebir, büyük/küçük harf dahil), `value_type` = beş `clientmodels.*` TypeUrl'sinden biri, `description`. Bu satır yoksa o stratejinin **tüm** ayar kaydı rollback olur.
2. GUI'nin gönderdiği yardımcı alanlar (`Strategy_Identifier`, `Command_Type`, `Strategy_Unique_Key`, `Account` vb.) de mesajda geliyorsa onlar için de satır gerekir (`hft_warrant_advanced.sql` yorumu).
3. Değer uzunsa `StrategySettings.settingsVal` kolonunun `TEXT` olduğu doğrulanmalı.
4. Yeni bir **strateji tipi** ekleniyorsa: `Strategies`'e GUI `strategyType` değeriyle aynı sabit `id` ile satır, hesaplara `Account_Allowed_Strategies` satırı, gerekiyorsa `Applications_Strategies` satırı eklenmeli. Örnek şablon: `scripts/sql/hft_warrant_advanced.sql` (idempotent `INSERT ... WHERE NOT EXISTS`, transaction, sonda doğrulama SELECT'i).
5. Kod tarafında `servicemodels` tip eşlemesi (`getApplicationFromStrategyType`) ayrıca güncellenmeli; DB tek başına yetmez (bkz. [`README.md`](README.md)).

### Orders / Positions kalıcılığı

- İkisinin de tek yazarı DataService gRPC'sidir (`ouch_api.go`: `SetOrders`, `DeleteOrders`, `SetPosition`). İstemci order-service'tir (README). trade-data-app bu tablolara kendi inisiyatifiyle yazmaz.
- GUI'den gelen emir (`/v1/sendOrders`) trade-data-app'te DB'ye yazılmaz; order-service'e veya motora iletilir. `gui_api.go`'daki `ordService.SetOrders` bir gRPC istemci sarmalayıcısıdır, `OrdersDB.SetOrders` değil.
- `Orders` açılış emri deposudur. order-service `GetOrders` ile okur, gönderdikten sonra veya iptalde `DeleteOrders` ile siler. ❓ doğrulanmadı: silme zamanlaması order-service tarafında.
- `Positions` delta-toplamalıdır. Aynı dolumun iki kez bildirilmesi pozisyonu iki kez artırır; idempotent değildir.

### Enum'lar (`pkg/db/models/enums.go`, `insturment_bazaars.go`)

| Enum | Değerler | DB'de |
|------|----------|-------|
| `DatabaseType` | 0=Unknown, 1=Mysql | — (config) |
| `ProtocolType` | 0=Ouch, 1=Fix, 2=None | `Ouchs.protocol` |
| `DecisionType` | 0=None, 1=Buy, 2=Sell, 3=CloseBuy, 4=CloseSell | `Scores.decision` |
| `ArbitrageSide` | 0=None, 65 (`A`)=Above, 66 (`B`)=Below | `Arbitrage_Package.arbitrageSide` |
| `FundSide` | 0=None, 1=Buy, 2=Sell | `Fund_Package.packageSide` |
| `TimeBasedBlockType` | 0=Day, 1=Hour, 2=Minute, 3=Second, 4=Milisecond, 5=All | `TimeBased.type`, `Volatility.type` |
| `TimeBasedTableType` | `NONE`, `TimeBased`, `Volatility` | Tablo adı |
| `InstrumentBazaarType` | 0=Unknown, 1=Primary (Yıldız), 2=Secondary (Ana), 3=Other (Alt) | `Instrument.relatedBazaar` |

`Orders.side`, `type`, `protocol`, `timeInForce`, `regularOrderType` proto enum'larının sayısal değerleridir (`ouch-data.proto`), Go modelinde enum tipi olarak tanımlı değiller.

## Şema yönetimi

- **Migration yok.** Repoda `CREATE TABLE`, migration aracı (goose, flyway vb.) veya şema dump'ı yok. Servis açılışta şemayı oluşturmaz veya kontrol etmez; eksik kolon ilk sorguda SQL hatası olarak ortaya çıkar.
- Şema değişiklikleri elle çalıştırılan, tek seferlik SQL script'leriyle yapılıyor (`scripts/sql/`):
  - `orders_isyip.sql`: `ALTER TABLE Orders ADD COLUMN isYip ...`. Yorumu, script'in kodu deploy etmeden **önce** her DB'ye ayrı ayrı uygulanması gerektiğini söylüyor (dev → test → prod).
  - `hft_warrant_advanced.sql`: Strateji ve attribute satırları (DML), çalıştırmadan önce `mysqldump` yedeği önerisi.
- Sonuç: Kod ile DB arasındaki uyum ortam başına elle sağlanıyor. Yeni bir kolona dokunan bir trade-data-app sürümü deploy edilmeden önce ilgili script hedef DB'de çalıştırılmış olmalı. ❓ doğrulanmadı: Algo-Setup tarafında şema script'lerinin tutulduğu ayrı bir yer olup olmadığı.

## Ölü kod

`OrdersDB.UpdateMaxOrderVolume` (`symbol LIKE 'X%'` ile `maxOrderValue` güncelliyor) ve `OrdersDB.GetAllIndiceInstruments` `Database` interface'inde yok ve hiçbir yerden çağrılmıyor.
