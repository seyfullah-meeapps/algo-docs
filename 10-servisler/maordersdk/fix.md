---
kapsam: MAOrderSDK'nın FIX yolu — QuickFIX'in gömülmesi, FixEngine/FixConnection/FixCodec, SessionSettings, oturum yaşam döngüsü ve replay, mesaj encode/decode tag tabloları, FIX şifre yaşam döngüsü (1409), thread/kilit modeli, şüpheli davranışlar
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
  - repo: algo-configs
    branch: development
    commit: ab35dde
dogrulama: 2026-10-22
durum: taslak
---

# MAOrderSDK — FIX yolu

İndeks: [README.md](README.md). Bu dosyada olmayanlar:
- Public API, config struct'larının tamamı, callback listesi, `ownsAccount`, round-robin → [api-ve-yasam-dongusu.md](api-ve-yasam-dongusu.md)
- `enterOrder`/`cancelOrder`/`replaceOrder` iç yolu, bölme, yerel retler → [emir-akisi.md](emir-akisi.md)
- OUCH/SoupBinTCP → [ouch-protokolu.md](ouch-protokolu.md)
- Host tarafı (order-service): FIX kullanıcı yükleme, replay gate, şifre yenileme politikası, DB yazımı → [order-service/sdk-ve-oturumlar.md § 8](../order-service/sdk-ve-oturumlar.md); `fixSession.*` anahtarları → [order-service/kalicilik-ve-config.md](../order-service/kalicilik-ve-config.md)

Kod: `src/connection/fix/FixEngine.*`, `src/connection/fix/FixConnection.*`, `src/protocol/fix/FixCodec.*`, `src/protocol/fix/FixPassword.cpp`, `src/MAOrderSDK.cpp` (FIX dispatch: `routes_to_fix`, `pick_fix_connection`, `fix_send_one`, `fix_replace_one`), `tests/fix_codec_test.cpp`, `CMakeLists.txt`.

## 1. Build: QuickFIX gömme

- `CMakeLists.txt`: `find_library(QUICKFIX_STATIC_LIB NAMES libquickfix.a)`. Bulunamazsa `FATAL_ERROR`; FIX'siz build yoktur.
- `target_link_libraries(MAOrderSDK PRIVATE libquickfix.a)` + `-Wl,--exclude-libs,libquickfix.a`. QuickFIX sembolleri `libMAOrderSDK.so`'dan export edilmez. Gerekçe (CMake yorumu, issue #402): HftSrvProd aynı `.so`'yu linkler; dinamik `libquickfix` her prod imajına kurulmak zorunda kalırdı.
- CI (`.github/workflows/ordersdk.yaml`): QuickFIX `v1.16.0` (commit `8f5a2efb`) kaynaktan `--enable-static --disable-shared --with-pic`, `CXXFLAGS="-fPIC -O2"` ile derlenir. Matrix'te normal, `onload`, `mlx` varyantları vardır (Algo-Setup `MAProdEnv/lib`: `libMAOrderSDK.so`, `libMAOrderSDK_Onload.so`, `libMAOrderSDK_Mlx.so`).
- `fix_codec_test` `.so`'ya değil doğrudan `FixCodec.cpp` + `FixPassword.cpp` + `libquickfix.a`'ya linklenir (`.so` QuickFIX sembollerini gizlediği için).
- **Runtime bağımlılığı kalır:** `useDataDictionary=true` iken QuickFIX spec XML'lerini dosyadan okur. Varsayılan ve bütün müşteri config'lerindeki yollar: `/usr/local/include/quickfix/spec/FIX50SP2.xml`, `/usr/local/include/quickfix/spec/FIXT11.xml`. Bu dosyalar Algo-Setup `MAProdEnv/include/quickfix/spec/` ve algo-configs `container-images/dev-containers/MADevEnvironment/include/quickfix/spec/` altında, ikisi aynı (md5 eşit), stok QuickFIX spec'leri. ❓ doğrulanmadı: prod imajının bu XML'leri `/usr/local/include/quickfix/spec/`'e kopyaladığı.

## 2. Bileşenler

| Sınıf | Rol |
|-------|-----|
| `FixEngine` | Tek `FIX::SocketInitiator` + `FIX::Application` + `FIX::MessageCracker`. Bütün `protocol==Fix` kullanıcılarının oturumları, emir registry'si (`orders_`), replay takibi, şifre akışı. `setOuchConfig` içinde kurulur, `start()` içinde başlar. |
| `FixConnection` | Kullanıcı başına ince `IConnection` tutamacı; yalnız round-robin havuzu için (OUCH ile simetri). `connect`/`disconnect`/`is_connected` → `FixEngine::connectUser`/`disconnectUser`/`isLoggedOn`. `send`/`receive`/`send_heartbeat` boştur. Kendi `OuchUser` kopyasını tutar (şifre swap'ı buna yansımaz, kullanılmaz). |
| `FixCodec` | Statik encode/decode. Legacy `OrderUtility.h` `ConvertFix*` + `FIXManager::onMessage` temel alınmıştır; fill fiyatı dahil birebir eşdeğer değildir ([branch karşılaştırması](../order-service/fix-branch-karsilastirmasi.md)). Header CompID/SubID'yi set etmez. |
| `FixOrderRecord` | Emir başına durum: `order` (gönderilen `EnterOrderMsg`), `token` (= ClOrdID), `username`, `price_divider`, `cum_qty`, `order_id` (BIST OrderID, hex parse). |
| `generateBistFixPassword` | `FixPassword.cpp` (§ 7). |

`FixEngine::sessions_` anahtarı kullanıcı adıdır ve ctor'dan sonra değişmez (kilitsiz okunur). `SessionID = (begin_string, fix_sender_comp_id, fix_target_comp_id, qualifier=username)`. Aynı CompID çiftine sahip iki kullanıcı qualifier ile ayrılır.

Kullanıcı alanları (`OuchUser`, `public/MAOrderStruct.h`): `protocol=WireProtocol::Fix`, `endpoint.ip/port`, `credentials.username/password/allowed_accounts`, `market` (fiyat böleni), `fix_sender_comp_id` (49), `fix_target_comp_id` (56), `fix_sender_sub_id` (50), `fix_new_password` (925). order-service bunları `Data/Models/OrderUser.cpp` setter'larıyla doldurur.

## 3. SessionSettings (`FixEngine::build_session_settings`)

`.cfg` okunmaz; her kullanıcı için bellek içi bir `FIX::Dictionary` kurulur ve `settings.set(session_id, d)` yapılır. **DEFAULT sözlüğü boş kalır.**

| Ayar | Kaynak | SDK varsayılanı (`FixSessionConfig`) | Müşteri config'leri (Algo-Setup `Configs/*/order-service-config.yaml`) |
|------|--------|-----------------|---------------|
| `socketConnectHost` / `socketConnectPort` | `OuchUser.endpoint` | — | DB'den, `<FIX_IP>`/`<FIX_PORT>` |
| BeginString (SessionID'de) | `begin_string` | `FIXT.1.1` | `FIXT.1.1` |
| `defaultApplVerID` | config | `FIX.5.0SP2` | `FIX.5.0SP2` |
| `connectionType` | config | `initiator` | `initiator` |
| `fileStorePath` | config | boş | `/workingDirectory/log/incoming.log` |
| `fileLogPath` | config | boş (= log yok) | `/workingDirectory/log/outgoing.log` |
| `allowUnknownMsgFields` | config | true | true |
| `validateUserDefinedFields` / `…Messages` | config | false / false | false / false |
| `resetOnLogon` / `resetOnLogout` / `resetOnDisconnect` | config | true / true / true | true / true / true |
| `useDataDictionary` + `dataDictionary` | config | true + `…/spec/FIX50SP2.xml` | aynı |
| `useTransportDataDictionary` + `transportDataDictionary` | config | true + `…/spec/FIXT11.xml` | aynı |
| `reconnectInterval` | config (**s**) | 3600 | 3600 |
| `heartBtInt` | config (**s**) | 30 | 30 |
| `startTime` / `endTime` | **sabit** `05:00:00` / `03:00:00` (FIXManager parity) | — | — |
| `replay_from_seq` | config (SDK'nın kendisi kullanır, QuickFIX ayarı değil) | 1 | anahtar yok → order-service varsayılanı 1 |

- **Store:** `FIX::FileStoreFactory(settings)` — FileStore (MemoryStore değil). `fileStorePath` bir **dizindir**; QuickFIX içinde oturum başına `FIXT.1.1-<SENDER>-<TARGET>-<username>.{seqnums,body,header,session}` dosyalarını tutar. Müşterilerde dizin adı `incoming.log`'dur.
- **Log:** `fileLogPath` boş değilse `FIX::FileLogFactory(cfg.file_log_path)` (path ctor; settings ctor DEFAULT sözlüğünden okuyacağı için bilinçli). Wire + event log bu dizine (müşterilerde `outgoing.log` dizini).
- `startTime`/`endTime`: `UseLocalTime` set edilmediği için UTC'dir → TR saatiyle oturum penceresi 08:00–06:00, **06:00–08:00 TR arası oturum dışı**. ❓ doğrulanmadı: QuickFIX'in bu pencere dışında oturumu kapatması ve yeni pencerede store'u (seq) sıfırlaması — QuickFIX standart davranışı, burada test edilmedi.
- **`reconnectInterval` gerçek davranışı (QuickFIX 1.16 `SocketInitiator`):** initiator tek bir `m_reconnectInterval` tutar; başlangıç değeri **30 s**, `onConfigure` yalnız DEFAULT sözlüğünden okur (burada boş). Per-session değer ilk `doConnect`'te okunup üye değişkene yazılır. Sonuç: proses açıldıktan sonra ilk bağlanma denemesi ≤30 s içinde, ilk dial'dan sonraki her yeniden deneme (kopma, 1409 reddi, şifre arm'ı sonrası relogon) **3600 s** pencereye bağlıdır. (QuickFIX kaynağı GitHub `v1.16.0` `SocketInitiator.cpp`'den okundu; prod binary'si üzerinde test edilmedi.)

### Replay anahtarı (`FixEngine::reset_seq_expected_no`)

`start()` içinde, store factory kurulmadan önce: `replay_from_seq != 0` ise her oturumun `<fileStorePath>/<Begin>-<Sender>-<Target>-<qualifier>.seqnums` dosyasında offset 13'ten itibaren 10 haneyi (`%010u`, beklenen **gelen** seq) üzerine yazar. Dosya yoksa (`ios::in|ios::out` açılamaz) sessizce hiçbir şey yapmaz. `reset*` bayraklarına bakmaz; `resetOnLogon=true` iken Logon `141=Y` taşıdığı için etkisizdir (kod yorumu "moot"). Davranışın order-service tarafı: [sdk-ve-oturumlar.md § 8](../order-service/sdk-ve-oturumlar.md).

## 4. Oturum yaşam döngüsü

| Adım | Kod | Ne olur |
|------|-----|---------|
| `MAOrderSDK::start()` | `FixEngine::start` | Settings → seq yazımı → FileStore/FileLog → `SocketInitiator`. Her oturuma `Session::logout("awaiting connectUser")` = oturum **disabled**; initiator disabled oturumu aramaz, kimlik bilgisi kullanılmaz. Sonra `initiator_->start()`. İstisna → `onSdkError(20, …)`, `start()` false döner (yeniden denenebilir). |
| `connectUser(username)` | `FixEngine::connectUser` | `Session::logon()` = oturumu enable eder ve **hemen** döner. `ConnectResult::Ok` login'in başarılı olduğunu göstermez; bağlantı initiator'ın sonraki connect turunda kurulur (§ 3). Zaten logged-on ise `AlreadyConnected`. FIX için `onLoginFailed` hiç çağrılmaz. |
| Logon gönderimi | `toAdmin` | Header'a `553 Username` = `credentials.username`, `554 Password` = `credentials.password` (`creds_mutex_` altında), `fix_new_password` doluysa `925 NewPassword`. Bütün admin mesajlarına `50 SenderSubID`. `resetOnLogon=true` → QuickFIX `141=Y` ekler. |
| Logon cevabı | `fromAdmin` → `track_replay`, şifre akışı (§ 7) | `20002` (DaysToPwdExpiry, BIST'e özel) varsa yalnız stdout'a log. |
| Logon tamam | `onLogon` | `onUserConnected(username)`; replay yoksa hemen `onReplayCompleted(username)`. |
| Logout / kopma | `onLogout` | Replay durumu sıfırlanır, `onUserDisconnected(username)`. Combiner zehirlenmez (FIX fill'leri combiner'a hiç girmez — kasıtlı). |
| Yeniden bağlanma | QuickFIX | Oturum enabled kaldıkça QuickFIX `reconnectInterval`'da yeniden arar. SDK'da OUCH'taki gibi bir shim yoktur. |
| `disconnectUser(username)` | `FixEngine::disconnectUser` | `Session::logout("intentional disconnect")` → oturum disabled, **retry yok**. Yeniden açmak için `connectUser`, `armFixPasswordChange` veya `setFixPassword` (üçü de `logon()` çağırır). |
| `stop()` | `FixEngine::stop` | `initiator_->stop()`. |

### Replay ve `is_replay` (`track_replay`, `finish_replay`)

Her gelen mesaj için çağrılır (`fromAdmin` ve `fromApp`). Durum `SessionEntry` içinde, yalnız QuickFIX thread'inde değişir.

1. **Logon cevabı**, MsgSeqNum > `Session::getExpectedTargetNum()` ise: `in_replay=true`, `replay_end_seq = Logon'un seq'i`. QuickFIX gap'i görüp ResendRequest'i kendisi atar.
2. Replay sırasında gelen mesajın ulaştığı seq (`SequenceReset` ise `36 NewSeqNo`, değilse MsgSeqNum) ≥ `replay_end_seq` **veya** mesajda `43 PossDupFlag=Y` yoksa → `finish_replay`. Aksi halde mesaj replay sayılır: `fromApp` thread_local `t_replayed_message=true` ile `crack` eder, decode edilen bütün callback mesajlarında `is_replay=true`.
3. Gap'i açığa çıkaran Logon QuickFIX kuyruğundan ikinci kez `verify()`'dan geçince de `finish_replay` çağrılır.
4. `finish_replay` logon başına bir kez (`replay_reported`) `onReplayCompleted` çağırır. Sıra: `onUserConnected` → replay callback'leri → `onReplayCompleted`.
5. `in_replay` dışında gelen PossDup mesajlar (oturum içi resend) `is_replay=false` ile gelir.

Giden tarafta `toApp`: header'da PossDupFlag=Y olan uygulama mesajı `FIX::DoNotSend` ile durdurulur → QuickFIX karşı tarafın ResendRequest'ine emirleri yeniden göndermez, GapFill gönderir. **Emirler hiçbir koşulda yeniden gönderilmez.**

`resetOnLogon=true` olan bütün müşteri config'lerinde replay oluşmaz; her logon'da `onReplayCompleted` `onLogon` içinden hemen gelir.

### Restart sürekliliği (registry)

- `adoptFixOrders` → `FixEngine::adoptOrder`: host'un DB'den tohumladığı emirler. Bilinmeyen `fix_username` veya zaten izlenen token atlanır.
- `adopt_from_er`: izlenmeyen ClOrdID'li bir ExecutionReport gelirse kayıt ER'nin kendi alanlarından (54, 48, 38, 44, 1, 14, 37) kurulur ve callback yine çalışır.

## 5. Encode (`FixCodec`)

Ortak: `send_to` header'dan `1128 ApplVerID`'yi siler (FIXManager parity) ve `Session::sendToTarget(msg, session_id)` ile yollar. `toApp` header'a `49`, `56`, `50`'yi kullanıcıdan yazar. `60 TransactTime` = gönderim anı (QuickFIX `TransactTime()` varsayılan ctor'u, UTC).

**Fiyat ölçeği:** raw `int64` fiyat, kullanıcının pazarına göre sabit bir bölenle ondalığa çevrilir: `Market::Equity` → **/1000**, `Market::Derivative` → **/100** (`price_divider_for`, `kEquityPriceDivider`, `kFuturePriceDivider`). `InstrumentLimit.decimal_count` FIX encode/decode'da **kullanılmaz** (yalnız bölme/hard-cap notional hesabında, [emir-akisi.md](emir-akisi.md)). Gelen fiyatlar `round(fiyat × bölen)` ile raw'a döner. Miktar (`38`, `151`, `32`, `14`) adet/lot, ölçeksiz; QuickFIX double alanı.

### NewOrderSingle (35=D) — `encode_enter_order`

| Tag | Alan | Değer |
|-----|------|-------|
| 11 | ClOrdID | token: host `client_order_id` doluysa **o**, boşsa SDK'nın 14 karakterlik token'ı (`draw_token`, OUCH ile aynı havuz). Bölmede çocuklar `<parent>#<i>`. |
| 54 | Side | `Buy`→`1`, `Sell`→`2`, `ShortSell`→`5`, diğer→`B` (AS_DEFINED) |
| 60 | TransactTime | şimdi |
| 40 | OrdType | `Market`→`1`, `Limit`→`2`, `MarketWithLeftoverLimit`→`K`, diğer (`Standard`, `Unknown`)→`2` |
| 1 | Account | `routing_account`, boşsa `client_account`, boşsa `exchange_info` |
| 528 | OrderCapacity | Equity'de `A` (agency); fon bloğunda `F`. Derivative'de yok. |
| 48 | SecurityID | `orderbook_id` ondalık string |
| 22 | SecurityIDSource | `8` (marketplace-assigned) |
| 38 | OrderQty | `quantity` |
| 59 | TimeInForce | `Day`→`0`, `GoodTillCancel`→`1`, `ImmediateOrCancel`→`3`, `FillOrKill`→`4`, `GoodTillDate`→`6`, `AtCrossing`→`9`, diğer→`0` |
| 44 | Price | yalnız OrdType `2` iken: `price / bölen` |
| 432 | ExpireDate | yalnız TIF `6`: `expire_date` (epoch **s**, UTC gününe çevrilir) → `"YYYYMMDD-00:00:00.000"` (eski ComVars formatı) |
| 453 grubu | NoPartyIDs | Equity && `client_category==Fund` && `client_account` dolu: `448=client_account`, `447=D`, `452=28`; ayrıca `528=F` |

`EnterOrderMsg`'ın OUCH'a özgü alanları (OpenClose, SMP, OffHours, diğer ClientCategory değerleri) FIX'te gönderilmez.

### OrderCancelRequest (35=F) — `encode_cancel_order`

`11` = yeni cancel token (`draw_token`; registry'ye **eklenmez**), `41 OrigClOrdID` = emrin token'ı, `54`, `60`, `1` (yukarıdaki sırayla), `48`, `22=8`, `38` = `rec.order.quantity`.

### OrderCancelReplaceRequest (35=G) — `encode_replace_order`

| Tag | Değer |
|-----|-------|
| 11 | yeni token (önce `"0"` ile kurulur, sonra üzerine yazılır) |
| 41 | eski token |
| 54, 40 | kayıttaki emirden |
| 60 | şimdi |
| 48, 22 | `orderbook_id`, `8` |
| 44 | `msg.price != 0` ise `msg.price / bölen` |
| 38 | `msg.quantity != 0` ise `msg.quantity + executed_qty` (`executed_qty` = kaydın `cum_qty`'si, yani host miktarı **kalan** miktar olarak yorumlanır); yalnız fiyat değişiyorsa `rec.order.quantity` |
| 1 | **yok** (eski converter'da yorum satırı, kasıtlı parity) |

`FixEngine::replaceOrder` yeni token için kaydı (eski kaydın kopyası; qty/price/passthrough güncellenmiş) **soket yazımından önce** registry'ye koyar; gönderim başarısızsa siler. Eski token da çözülebilir kalır.

## 6. Decode (`FixEngine::onMessage` + `FixCodec::decode_*`)

### ExecutionReport (35=8): ExecType (150) → callback

OrdStatus (39) hiç okunmaz.

| ExecType | Token çözümü | Callback | Alanlar |
|----------|--------------|----------|---------|
| `0` New, `D` Restated, `L` Triggered | 11 | `onAccepted` | `quantity`=151 LeavesQty, `price`=44×bölen, `order_id`=37 (hex), `orderbook_id`=48, `pre_trade_quantity`=kayıttaki qty; side/account/passthrough kayıttan. Kaydın `order_id`'si güncellenir. |
| `8` Rejected | 11 | `onRejected` | `reject_code`=103 OrdRejReason (BIST negatif kodlar, ör. `-420131`), `reject_reason`=58 Text; qty/orderbook/account/passthrough kayıttan |
| `5` Replaced | önceki=41, yeni=11 | `onReplaced` | `quantity`=`pre_trade_quantity`=151 LeavesQty, `price`=44×bölen (eski kaydın böleni), `order_id`=37; yeni kayda `order_id` ve 14>0 ise `cum_qty` yazılır |
| `4` Canceled, `C` Expired, `9` Suspended | 41 varsa o, yoksa 11 | `onCanceled` | `quantity`=38−14 (ikisi de varsa; kalan), `order_id`=kayıttaki; `reason_code` set edilmez (0) |
| `F` Trade, `1`, `2` (eski PartialFill/Fill) | 11 | önce `onWireExecuted`, sonra `onExecuted` (combiner yok) | `quantity`=32 LastQty, `price`=31 LastPx (yoksa 44)×bölen, `match_id`=880 TrdMatchID (**hex** parse); kaydın `cum_qty`'si 14 ile güncellenir |
| diğer (`6`, `E`, `A`, `I`, `H`, `G`…) | — | **yok**, sessizce düşer | |

Token kayıtta yoksa `adopt_from_er` denenir; o da olmazsa `onSdkError(22, …)`. Tüm callback mesajlarında `ouch_username` = FIX kullanıcısı, `timestamp` = 60 TransactTime → epoch **ns** (`transact_time_ns`: saniye×1e9 + milisaniye×1e6; ms altı kaybolur). `latency_*_ns` alanları FIX'te doldurulmaz (0).

### OrderCancelReject (35=9)

1. 11 ClOrdID kayıtlıysa = **replace reddi**: `onRejected` (client_order_id = yeni token, `reject_code`=102 CxlRejReason, `reject_reason`=58), sonra yeni token registry'den silinir (orijinal kalır).
2. Değilse 41 OrigClOrdID kayıtlıysa = **cancel reddi**:
   - 58 Text tam olarak `"REJ- Too late to cancel, already cancelled"` ise `onCanceled` (`quantity=0`, `order_id`=37).
   - Değilse `onRejected` (aynı alanlar).
3. İkisi de yoksa `onSdkError(22, …)`.

### Reject (35=3) ve BusinessMessageReject (35=j)

- **35=3** admin mesajıdır, `fromAdmin`'e gelir; yalnız `track_replay`'den geçer, **hiçbir callback üretilmez**.
- **35=j** `crack` edilir; FIX50SP2 `MessageCracker`'ın varsayılan handler'ı boştur (`{}`, Algo-Setup `MAProdEnv/include/quickfix/fix50sp2/MessageCracker.h`) → sessizce yutulur.
- Tanımsız diğer uygulama mesajları `UnsupportedMessageType` fırlatır; QuickFIX karşı tarafa BusinessMessageReject döner.

Bkz. Şüpheli #1.

## 7. Şifre yaşam döngüsü

### SessionStatus (1409) kodları

Anlamlar `public/MAOrderSDK.h` yorumlarından; SDK'nın davranışı koddan.

| 1409 | Anlam (kod yorumu) | Şifre değişimi yokken | Şifre değişimi sürerken (`fix_new_password` dolu) |
|------|---------------------|------------------------|------------------------------------------------|
| yok (−1) | — | Logon: normal. Logout: callback yok. | Logon'da: **başarı**. Logout'ta: başarısızlık, `onFixPasswordChangeResult(−1)`. |
| 0 | session active | Logout'ta gelirse `onFixLogonRejected(0)` | Logon'da: başarı |
| 1 | password changed | Logout'ta gelirse `onFixLogonRejected(1)` | Logon'da: başarı |
| 3 | yeni şifre politikaya uymuyor | Logout: `onFixLogonRejected(3)` | başarısızlık |
| 4 | logout complete | **callback yok** | başarısızlık (bkz. Şüpheli #4) |
| 5 | hatalı kullanıcı/şifre | Logout: `onFixLogonRejected(5)` | başarısızlık |
| 6 | hesap kilitli | Logout: `onFixLogonRejected(6)` | başarısızlık |
| 8 | şifre süresi doldu | Logout: `onFixLogonRejected(8)` | başarısızlık |
| 9 | hatalı SubID/CompID | Logout: `onFixLogonRejected(9)` | başarısızlık |
| 100 / 101 | oturum hataları | Logout: `onFixLogonRejected` | başarısızlık |
| diğer (2, 7…) | — | Logout'taysa `onFixLogonRejected` | Logon'da bile başarısızlık (yalnız −1/0/1 başarıdır) |

- ❓ doğrulanmadı: standart FIX'te 9 = "MsgSeqNum too low"dır; "hatalı SubID/CompID" BIST'e özgü bir kullanım olabilir. BIST FIX spec'i repoda yok.
- `fromAdmin` yalnız Logon (35=A) ve Logout (35=5) için bu mantığı çalıştırır. `1409` sayıya `stoi` ile çevrilir, çevrilemezse −1.
- Değişim yokken SDK oturumu **kapatmaz**: QuickFIX aynı şifreyle `reconnectInterval`'da yeniden dener. 5'te kilitlenme riskini önlemek host'un işidir (order-service `disconnectUser` yapar).

### API

| Çağrı | Etki |
|-------|------|
| `OuchUser.fix_new_password` (setOuchConfig'te) | İlk Logon'da 925 gider (order-service `fixSession.newPasswords` → `MAOSdkManager.cpp`). |
| `armFixPasswordChange(user, new)` → `FixEngine::armPasswordChange` | `creds_mutex_` altında `fix_new_password = new`; `Session::logon()` (enable). Logon bir sonraki connect turunda (§ 3) gider: `554` = mevcut şifre, `925` = yeni. Bilinmeyen/FIX olmayan kullanıcı veya boş şifre → false. |
| `setFixPassword(user, pw)` → `FixEngine::setSessionPassword` | `credentials.password = pw`, `fix_new_password` temizlenir, `logon()`. Çökme kurtarma içindir. |
| Başarı (yukarıdaki tablo) | `credentials.password = fix_new_password`, `fix_new_password` temizlenir (SDK belleğinde). Sonraki her relogon yeni şifreyle düz logon yapar; "yanmış" eski şifre bir daha denenmez. `onFixPasswordChangeResult(user, status)`. |
| Başarısızlık | `Session::logout("password change failed")` → oturum disabled (QuickFIX retry'ı durur), `fix_new_password` **temizlenmez**. `onFixPasswordChangeResult(user, status)`. Host yeniden `armFixPasswordChange` veya config + restart ile devam eder. |

`generateBistFixPassword(length = 10)` (`FixPassword.cpp`): `length < 4` → 4. Tam **bir** özel karakter (`*#+.`), geri kalanı sırayla büyük harf / küçük harf / rakam dönüşümlü; sonra `std::shuffle`. RNG `std::mt19937_64`, `std::random_device` ile tohumlanır (kriptografik değil). `%` ve `-` BIST'te 1409=3 alır.

### Host sorumluluğu ve çökme kurtarma

SDK hiçbir şifreyi kalıcı yazmaz. Sözleşme (`MAOrderSDK.h` yorumu): yeni şifre **arm edilmeden önce** kalıcı yazılmalı; wire'a çıktığı anda BIST kabul etmiş olabilir. `onFixPasswordChangeResult` 0/1 → host yeni şifreyi hemen kalıcılaştırır.

Çökme senaryosu: aday kalıcı yazıldı (pending) → arm → Logon gitti, BIST kabul etti → host terfi ettirmeden çöktü → restart'ta kalıcı şifre eski → Logon eski şifreyle → `onFixLogonRejected(5)` → host pending'i `setFixPassword(pending)` ile verir → sonraki connect turunda logon. order-service'teki uygulaması (DB `pendingPassword`, 5 deneme sınırı, `autoRenewExpiredPasswords`): [sdk-ve-oturumlar.md § 8](../order-service/sdk-ve-oturumlar.md).

## 8. Thread modeli ve kilitler

| Thread | Ne çalıştırır |
|--------|---------------|
| QuickFIX `SocketInitiator` thread'i (tek, bütün FIX oturumları için) | `onLogon`/`onLogout` → `onUserConnected`, `onUserDisconnected`, `onReplayCompleted`; `fromAdmin` → `onFixLogonRejected`, `onFixPasswordChangeResult`; `fromApp` → `onAccepted`, `onRejected`, `onReplaced`, `onCanceled`, `onWireExecuted`, `onExecuted`, `onSdkError(22)`; Logon/heartbeat için `toAdmin` |
| Host'un çağıran thread'i | `enterOrder`/`cancelOrder`/`replaceOrder` → `sendToTarget` → `toApp` (aynı thread'de), soket yazımı; `onSdkError(21)`; token-assignment callback'i |

- ER, `send_to` dönmeden QuickFIX thread'inde gelebilir; bu yüzden kayıt (ve perf `*_sent_at`) gönderimden **önce** yazılır.
- `onWireExecuted` FIX'te QuickFIX thread'inden gelir (OUCH'taki "emrin kendi recv thread'i" karşılığı).
- ❓ doğrulanmadı: QuickFIX 1.16 `SocketInitiator`'ın bütün oturumlar için tek thread kullandığı (QuickFIX kaynağından çıkarım; `ThreadedSocketInitiator` kullanılmıyor).

| Kilit | Korur |
|-------|-------|
| `creds_mutex_` | `SessionEntry.user.credentials.password` ve `fix_new_password` (QuickFIX thread'i okur/yazar, host `arm`/`set` ile yazar) |
| `orders_mutex_` | `orders_` map'i ve kayıtların `cum_qty`, `order_id`, `*_sent_at` alanları |
| (kilitsiz) | `sessions_` anahtarları (ctor'dan sonra sabit); `SessionEntry` replay alanları (yalnız QuickFIX thread'i); `t_replayed_message` thread_local |
| QuickFIX iç kilitleri | `Session` gönderimi, `Session::lookupSession` registry'si |

## 9. Bölme, yerel retler, round-robin

- Yerel retler (1001–1005 vb.) ve bölme matematiği FIX'te de **aynen** geçerlidir: FIX dispatch bunlardan sonra gelir (`MAOrderSDK::enterOrder`). Bölme çocukları FIX havuzunda round-robin'le dağılır; split iptal/replace çocuklara yayılır. FIX çocuk replace'inde `quantity=0` (= koru) gönderilir. Ayrıntı: [emir-akisi.md](emir-akisi.md).
- `routes_to_fix`: `preferred_ouch_username` bir FIX kullanıcısıysa her zaman FIX. Değilse yalnız hesap OUCH havuzunda **yoksa** ve FIX havuzunda varsa FIX. Havuzlar karışmaz.
- `pick_fix_connection`: preferred verilmişse yalnız o kullanıcı (hesap izinli ve logged-on olmalı). Değilse hesabın FIX bağlantıları arasında atomik sayaçla round-robin, ilk logged-on olan. `setFavoriteOuch` / `favorite_idle_reset_ms` FIX'e **uygulanmaz**.
- Uygun bağlantı yoksa `onSdkError(1, …)` ve `false` (host yedek yola düşebilir). `ownsAccount` FIX'te yalnız logged-on oturumları sayar.

## 10. Şüpheli

1. **bug? Oturum seviyesi Reject (35=3) ve BusinessMessageReject (35=j) host'a ulaşmıyor.** `FixEngine::fromAdmin` 35=3'ü yok sayar; 35=j QuickFIX'in boş varsayılan handler'ına düşer. BIST bir emri bu yollarla reddederse `onRejected` gelmez, emir host'ta "gönderildi" durumunda kalır. Doğrula: BIST'in NOS/OCR/OCRR'yi 35=3/35=j ile reddettiği durumlar var mı.
2. **bug? Miktar replace'inden sonra kaydın `order.quantity`'si "kalan" anlamına geçiyor.** `FixEngine::replaceOrder` kopyaya `order.quantity = msg.quantity` (kalan) yazar; `encode_replace_order` ise wire'a `msg.quantity + cum_qty` (toplam) gönderir. Aynı emirde sonraki **yalnız fiyat** replace'i `38 = rec.order.quantity` (kalan, cum_qty eklenmeden) gönderir. Cancel'daki `38` da aynı değeri kullanır. Legacy master FIXManager/OrderUtility aynı sayı farkını taşıyor ([ikinci tur örneği](../order-service/fix-branch-karsilastirmasi.md#k-121-legacy-kodda-da-mevcut)); exchange sonucu canlıda teyit edilmedi.
3. **doğrula: FIX fiyat böleni `decimal_count`'tan bağımsız.** Encode/decode equity'de sabit 1000, VİOP'ta sabit 100 kullanır; bölme/hard-cap ise raw fiyatı `10^decimal_count` ile yorumlar. Equity'de `decimal_count != 3` (veya VİOP'ta `!= 2`) olan bir enstrümanda wire fiyatı ile notional hesabı farklı ölçek kullanır.
4. **doğrula: Logon beklerken arm edilen şifre ve gelen Logout.** `armPasswordChange` logged-on bir oturumda da `fix_new_password`'ü set eder; değişim ancak sonraki Logon'da olur. Bu arada BIST'ten gelen herhangi bir Logout (1409=4 dahil, ya da 1409'suz) `fromAdmin`'de "değişim başarısız" sayılır: oturum disabled, `onFixPasswordChangeResult(4 / −1)`. order-service bunu yalnız 1409=8 / config akışında çağırdığı için pratikte oturum zaten logged-on değildir.
5. **bug? `connectUser(OuchUser)` FIX kullanıcısını OUCH olarak kurar.** Dinamik kayıt yolu `protocol` alanına bakmadan `OuchConnection` oluşturur. FIX kullanıcısı bu yolla eklenirse SoupBinTCP login'i dener. Bugün yalnız HFT handoff (OUCH) bu yolu kullanıyor.
6. **doğrula: Header'da kimlik alanları.** `toAdmin` 553/554/925'i Logon **header**'ına koyar (FIXT11'de body alanı). QuickFIX bunları header alanlarından sonra, body'den önce serialize eder; BIST'in kabul ettiği legacy FIXManager davranışıyla aynı olduğu varsayılır. Stok `FIXT11.xml`'de 1409/925 tanımlı değil; gelen Logout'un doğrulamadan geçmesi `allowUnknownMsgFields=true`'ya bağlıdır (QuickFIX `DataDictionary::shouldCheckTag`, ❓ doğrulanmadı). Bu ayar `false` yapılırsa 1409'lu Logout'lar reddedilebilir.
7. **Kasıtlı ama dikkat: yabancı emirler sahiplenilir.** `adopt_from_er` FIX oturumunda izlenmeyen her ClOrdID için kayıt kurar ve callback üretir. Aynı FIX kullanıcısıyla başka bir sistemden girilen emirler de host'a SDK emri gibi gelir.
8. **Host `client_order_id`'si doğrudan ClOrdID olur.** `fix_send_one` verilen id'yi wire'a koyar (bölme çocukları `<id>#<i>`); uzunluk/karakter kontrolü yok. ❓ doğrulanmadı: BIST ClOrdID uzunluk sınırı.
9. **doğrula: `ExpireDate` (432) formatı** `YYYYMMDD-00:00:00.000`dır (LocalMktDate normalde `YYYYMMDD`). Legacy parity; BIST'in kabul ettiği varsayılır.
10. **`reconnectInterval=3600` gecikmesi.** § 3: ilk dial'dan sonra yeniden bağlanma ve şifre relogon'u bir saate kadar sürebilir. `connectUser` `Ok` dönse de oturum o pencerede bağlı değildir.
11. **`ExecType` `H` (Trade Cancel) / `G` (Trade Correct)** sessizce düşer; dolum iptali host'a bildirilmez. Doğrula: BIST FIX'te bu ExecType'ları gönderiyor mu.
