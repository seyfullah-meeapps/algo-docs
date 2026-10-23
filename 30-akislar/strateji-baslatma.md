---
kapsam: Operatörün GUI'den strateji ayarlayıp başlatması, durdurması ve ayar güncellemesi — REST → trade-data-app → HFT/AlgoProd gRPC → strateji → FetchCommands → WS → GUI; hata yolları ve restart sonrası geri yükleme
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui        # eski GUI
    branch: main
    commit: 6715182
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: trade-data-app          # prod farkı
    branch: master
    commit: 4a43e19
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading      # prod farkı
    branch: master
    commit: aa150ee
dogrulama: 2026-10-23
durum: taslak
---

# Akış: UI'dan strateji başlatma / durdurma / ayar güncelleme

Bu dosya yalnız **sırayı ve sınırları** anlatır. Ayrıntı:
- Payload biçimi, `commandType`, tam payload kuralı: [backend-sozlesmesi § 5](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#5-strateji-komut-sözleşmesi-post-v1setstrategycommands)
- trade-data-app REST ucu ve tip kontrolü: [api.md § 7](../10-servisler/trade-data-app/api.md#7-guiservice-gui-dataproto-gui_apigo--rest-restport); WS `/strategy` feed'i: [veri-akisi § 4.4](../10-servisler/trade-data-app/veri-akisi.md#44-wsv1strategystart--strateji-komutdurum)
- HFT tarafı: [komutlar-ve-grpc § 3.1](../10-servisler/hftsrvprod/komutlar-ve-grpc.md#31-strateji-komutu-uida-başlata-basınca-hftde-ne-olur), [strateji-cekirdegi § 2](../10-servisler/hftsrvprod/strateji-cekirdegi.md#2-strategymanager)
- AlgoProd tarafı: [grpc-ve-veri § 3.1](../10-servisler/algorithmic-trading/grpc-ve-veri.md#31-strateji-komutu-başlat--durdur--ayar-güncelle), [uygulama-ve-threadler § 5](../10-servisler/algorithmic-trading/uygulama-ve-threadler.md#5-strategymanager-ve-strateji-arayüzü)
- Strateji başına alanlar: [`20-stratejiler/`](../20-stratejiler/README.md)

## 0. Ön koşul: panel açma (strateji nesnesinin doğması)

Başlat'tan önce UI genelde paneli/satırı açar ve bu, motorda stratejiyi **ayarsız** yaratır:

| Motor | UI çağrısı | Motorda | Yan etki |
|-------|-----------|---------|----------|
| HFT | `POST /v1/subscribeToOrderbook` (Y `subscribe.ts`, E `subscribeToSingleHft/Theoretic/Varant`) | `StrategyServiceImpl::SubscribeToOrderbook`: strateji yoksa çıplak `BaseStrategyCommand` ile `createStrategy(…, false)` + `OuchManager::insertStrategy` (order-service'e kayıt, bloklar) | DB'ye **yalnız taban** varsayılan ayarlar yazılır; `static_pointer_cast` tanımsız davranışı ([komutlar-ve-grpc Şüpheli](../10-servisler/hftsrvprod/komutlar-ve-grpc.md#şüpheli-davranışlar-koddan)) |
| AlgoProd arbitraj | `POST /v1/subscribeToSingleArbitrage` | `SubscribeToFuture`: türev+dayanak için `insertStrategyInfo`, strateji yoksa `createArbitrageStrategy` (durmuş, `checkParams` atlanır) | `unique_key` motor kurar: `<hesap>_<sid>_<türevId>_<tipChar>` ([grpc-ve-veri § 2](../10-servisler/algorithmic-trading/grpc-ve-veri.md#2-rpcler)) |
| AlgoProd VWAP/Fon | — (ayrı abonelik yok) | Strateji ilk `setStrategyCommands` ile yaratılır | — |

`subscribeToOrderbook` AlgoProd tiplerinde çağrılırsa motor gövdesi `return`'süzdür (tanımsız davranış, K-204). Panel açma aynı zamanda WS `/strategy` aboneliğini kurar (aşağıda adım 8); echo'nun GUI'ye ulaşması buna bağlıdır.

## 1. Sıra diyagramı

```
GUI            trade-data-app (gRPC-gateway)         Motor (HFT :9050 / AlgoProd :9098)          trade-data-app (stream)    GUI
 │ POST /v1/setStrategyCommands                          │                                            │                        │
 │──────────────►│ ConvertFields, checkStrategyAttributesType (DB)                                    │                        │
 │               │ getApplicationFromStrategyType (REST kopyası)                                      │                        │
 │               │── SetCommandRequest(1, uniqueKey, fields) ──►│ gRPC sync thread:                   │                        │
 │               │   (deadline yok)                             │ parse → bul/yarat → setCommand      │                        │
 │               │                                              │ → saveStrategySettings (DB, sync)   │                        │
 │               │                                              │ → snapshot kuyruğa                  │                        │
 │◄── {success} ─│◄──────────── OK / status ────────────────────│                                     │                        │
 │               │                                              │── FetchCommands (StrategyResponse) ►│ commandPublisher       │
 │               │                                              │                                     │── /ws/v1/strategy ────►│ tablo
```

## 2. Adım adım (başlat)

1. **GUI** — Yeni GUI her strateji yolunu (modal, inline hücre, toplu işlem) `create<X>Payload` kurucusundan geçirir ve **tam** ayar listesini `Strategy_Start: true` ile yollar (`app/api/mutations/strategy.ts`, zarf `wrapGuiValue`). Eski GUI tracker başına elle kurulmuş alan listesi yollar (❓ doğrulanmadı: her yolun tam payload olduğu). Gövde: `{commandType: 1, uniqueKey, strategyType, fields: map<string, Any>}`; auth `Authorization: Bearer <JWT>` (48 sa, yenileme yok; [backend-sozlesmesi § 2](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#2-kimlik-doğrulama-ve-oturum)). Yeni GUI istemci zaman aşımı 10 sn, retry yok.
2. **trade-data-app** `GuiStrategySetCommands` (`pkg/servicemodels/gui_api.go`, gRPC handler thread'i):
   1. `guiExtServices == nil` → "Gui external services is not found" (order-service henüz login olmadı).
   2. `ConvertFields`: `GuiXValue` → `clientmodels.XValue`.
   3. `checkStrategyAttributesType`: **her istekte** DB'den `StrategyAttributes` okunur, mesajdaki alanın TypeUrl'i `value_type` ile karşılaştırılır; uyuşmazlık → hata. Tabloda olmayan alan kontrol edilmez.
   4. `getApplicationFromStrategyType` (**REST kopyası**): 4, 8, 9, 11, 12, 13, 14, 15 → HFT; 1, 2, 3, 5, 6, 7, 10 → AlgoProd; diğer → "Unknown strategy type". WS kopyası farklıdır (K-27). ⚠ master'da farklı (2026-10-23): trade-data-app `master`'da 15 (Varant Toplu) case'i yok → "Unknown strategy type".
   5. Servis bağlı değilse ("`IsConnected`" = token boş değil) "HFT service is not connected" / "Algorithmic trading service is not connected". Kuyruk yok, komut kaybolur.
   6. `SetStrategyCommand`: `CommandRequest{message_type = commandType, unique_key, fields}`, metadata `authorization: Bearer <motor token'ı>` (trade-data-app'in `StrategyLogin` token'ı; **GUI kullanıcısının kimliği motora gitmez**). `context.Background()` → **deadline yok**.
3. **Motor** — `StrategyServiceImpl::SetCommandRequest` → `checkAuthorization` (bellek içi token) → `message_type` 1:

| Adım | HFT (`GUIManager::dispatchStrategy`) | AlgoProd (`StrategyManager::commandReceived(map, key)`) |
|------|--------------------------------------|----------------------------------------------------------|
| Parametre kontrolü | yok (`checkParams` ölü) | `checkParams` (`Command_Type` + strateji başına zorunlu alanlar) → `INVALID_ARGUMENT "Missing or invalid parameters"` |
| Komut sınıfı | `CommandFactory::createStrategyCommand`, **`Strategy_Type`** ile | aynı adlı fabrika, **`Command_Type`** (iç char kodu, arbitraj 51) ile |
| Bulma | `getStrategy(Strategy_Unique_Key)` | `strategyMap[getStrategyKey()]` (ayraçsız iç anahtar) |
| Yoksa yaratma | `createStrategy(cmd, false)`: registry + worker ataması + `getDefaultSettings` DB'ye + snapshot | `StrategyFactory::createStrategy`; **istisna yutulur**, akış devam eder (K-203) |
| Uygulama | `strategy->setCommand(cmd)`: komut tamamen değişir; `Strategy_Start` → `startStrategy` → `initializeItchSubscriptions()` | `setCommand`: `commandPtrMutex`, `isStarted()` → `start()` (abonelikler `startProperly`'de; arbitraj worker havuzuna `assignStrategy`; ⚠ master'da yok, arbitraj kendi thread'inde) |
| DB | `saveStrategySettings(message)`: `Strategy_Start` hariç senkron `AlgoService.SetStrategySettings`, dönüş okunmaz | aynı (gelen map, `Strategy_Start` hariç) |
| Echo | `enqueueCommand` → global `globalCommandQueue` | `setStrategyNotifier(request.unique_key)`: anahtar kuyrukları açılır + snapshot |
| Yanıt | `OK` | `OK` |

4. **REST yanıtı** `{"success": true}`. Motorun gRPC status'ü trade-data-app'ten aynen döner; grpc-gateway onu HTTP'ye çevirir (koddan çıkarım: `INVALID_ARGUMENT`/`FAILED_PRECONDITION` → 400, `RESOURCE_EXHAUSTED` → 429, `INTERNAL`/düz Go hatası → 500). Gövde `{code, message}`.
5. **Echo** — HFT `FetchCommands` döngüsü global kuyruğu boşaltır; AlgoProd `GUIManager` `worker`'ı aktivite kuyruklarını anahtar kuyruklarına taşır, `FetchCommands` hepsini boşaltır. Mesaj `Command_Type_StrategyResponse`, `fields` = command snapshot'ı.
6. **trade-data-app** `getCommandsFromService` → `commandPublisher` → `/ws/v1/strategy/start` istemcilerinden `subbedKeys`'inde bu `unique_key` olanlara `{message_type, unique_key, fields}` (protojson; 64-bit sayılar string).
7. **GUI** snapshot girdisini **tamamen** değiştirir (Y). Çalışıyor göstergesi: HFT'de `Strategy_Start`/`Is_Running` (ikisi de komutun `started`'ı, gerçek `isRunning` değil); AlgoProd'da snapshot'ta `Strategy_Start`, gerçek durum özetteki `Is_Strategy_Running`.
8. **WS aboneliği** (panel açılırken, bir kez): `{Type:4, Body:{strategyType, commands:[{commandType, uniqueKey}]}}` → trade-data-app anahtarı istemciye ekler, motora `SubscribeToCommands` (ayrı goroutine, hata yalnız log). HFT: abonelik kaydı tutmaz, anlık snapshot'ı kuyruğa koyar. AlgoProd: anahtar kuyruklarını açar + `sendSnapshotOfStrategy`.

## 3. Durdurma ve ayar güncelleme

- **Durdurma** aynı uç, aynı yol; tek fark `Strategy_Start: false` (Y yine tam payload). HFT `stopStrategy` → `cleanupItchSubscriptions`; AlgoProd `stop()` → `exitProperly`. **Bekleyen emirler iptal edilmez** (HFT); AlgoProd arbitraj yalnız türev emirlerini, Fon Takibi yalnız fon emirlerini iptal eder ([arbitraj § Risk](../20-stratejiler/arbitraj.md#risk-ve-durma-koşulları), [fon-takibi § Risk](../20-stratejiler/fon-takibi.md#risk-ve-durma-koşulları)). İptal/pozisyon kapatma ayrı komutlardır (HFT 7/9; AlgoProd'da yok).
- **Ayar güncelleme** de aynı yoldur; ayrı RPC yok. Komut **birleştirilmez**, mesajda olmayan alan varsayılana döner (HFT kesin; Varant Toplu'da boş payload listeyi siler). Çalışan stratejiye yeni ayar `setCommand` ile anında uygulanır.
- Aynı anahtara art arda gelen iki komut koordine edilmez; sonraki öncekini ezer (yeni GUI'de **kabul edilmiş risk**, 2026-10-21; mtrader-trade-ui `AGENTS.md` → "Decisions and Boundaries").
- HFT `HftClassic::setCommand` kilidi 100 µs'de alamazsa `RESOURCE_EXHAUSTED`; komut yine de atanmış olabilir ([komutlar-ve-grpc Şüpheli](../10-servisler/hftsrvprod/komutlar-ve-grpc.md#şüpheli-davranışlar-koddan)).
- AlgoProd arbitraj başlatmada `arePackagesConsistent` tutmazsa `StrategyStartException` → `FAILED_PRECONDITION` (HTTP 400), strateji başlamaz, yeni yaratıldıysa map'ten silinir. ⚠ master'da farklı (2026-10-23): master'da her istisna `INTERNAL`, strateji map'te kalır ve yarım paketle de başlar.

## 4. Hata yolları

| Nerede | Durum | GUI'nin gördüğü |
|--------|-------|-----------------|
| trade-data-app | order-service hiç login olmadı | 500 "Gui external services is not found" |
| trade-data-app | Alan tipi `StrategyAttributes` ile uyuşmuyor | 500 "Wrong type for attribute: …" |
| trade-data-app | Motor bağlı değil / login hatası sonrası kalıcı vazgeçme ([veri-akisi § 5.1](../10-servisler/trade-data-app/veri-akisi.md#51-bağlanma-yeniden-bağlanma-bağlantı-yokken)) | 500 "… service is not connected" |
| trade-data-app | Motor bağlı görünüyor ama ölü (health tespitinden önce) | gRPC hatası (Unavailable → 503) |
| HFT | `Strategy_Type` tanınmıyor / yanlış wrapper (sessizce 0) | 400 "Invalid strategy command" |
| HFT | `createStrategy` başarısız (OrderChase vb.) | 400 "Failed to create strategy" |
| AlgoProd | `Command_Type` yok/tanımsız | 400 / 500 |
| AlgoProd | **Fabrika istisnası** (enstrüman yok, dayanak = türev, BYF vadeli yok) | **200 `success:true`**; ayar DB'ye yazılır, strateji yok, echo gelmez (K-203) |
| AlgoProd | `insertStrategyInfo` order-service'e ulaşamıyor (strateji ctor/başlatma) | İstek **asılı kalır** (ouch-sdk'da timeout yok, K-151); Y 10 sn'de zaman aşımı gösterir ama komut sunucuda uygulanabilir |
| İki motor | DB yazımı (`SetStrategySettings`) başarısız | Başarılı görünür; restart'ta eski ayar yüklenir |
| Eski GUI | Bazı yollar (toplu iptal, Varant) yanıtta olmayan `status`'a bakar | Başarıda da hata toast'ı (K-169) |
| WS | Echo gelmedi | Abonelik yok ya da motor/trade-data-app stream'i düştü (HFT `Write` hatasında mesaj kuyruğa geri konur ⚠ master'da yok; AlgoProd'da zombi stream mesaj çalar, K-204) |

## 5. Restart sonrası geri yükleme

| | HFT | AlgoProd |
|-|-----|----------|
| Ne zaman | ITCH Spot snapshot-end → `strat-loader` thread'i `loadStrategiesFromDb` | Açılış adım 9 `readAlgoSettings` (gRPC zaten açık, K-202) |
| Nasıl | `getStrategySettings` → `createStrategy(cmd, true)` (DB'ye yazmaz) | `getStrategySettings` → `commandReceived(cmd)`; anahtar bayt kırpma hack'i (K-203) |
| Durum | **Durmuş** (`Strategy_Start` DB'ye hiç yazılmaz), `balance=0`; pozisyon OUCH replay veya elle SetBalance ile | **Durmuş** (aynı sebep). `uygulama-ve-threadler § 5`'teki "`STRATEGY_STARTED` true ise başlatılır" dalı pratikte hiç çalışmaz. Arbitraj/Fon durumu `GetArbitrageData`/`GetFundData` ile geri gelir |
| GUI'ye snapshot | `createStrategy` her strateji için global kuyruğa snapshot koyar → trade-data-app'te bu anahtara hâlâ abone WS istemcisi varsa ulaşır | `setStrategyNotifier` çağrılmaz → anahtar kuyruğu yok → mesajlar **atılır**; GUI `SubscribeToCommands` tekrar gelene kadar güncelleme almaz |
| Token | trade-data-app'in eski token'ı geçersiz; health `Watch` kopmayı görünce yeniden `StrategyLogin` | aynı |

Operatör restart sonrası stratejileri **elle yeniden başlatmalıdır**. Ayrıntı: [strateji-cekirdegi § 4](../10-servisler/hftsrvprod/strateji-cekirdegi.md#4-yaşam-döngüsü-senaryoları), [grpc-ve-veri § 7.3](../10-servisler/algorithmic-trading/grpc-ve-veri.md#73-kalıcılık-ve-restart). Kopma senaryolarının geneli: [kopma-ve-kurtarma](kopma-ve-kurtarma.md).

## Şüpheli

- **bug? AlgoProd restart'ı sonrası `/strategy` sessiz kalabilir.** HFT'nin global kuyruğu abonelikten bağımsızdır, ama AlgoProd anahtar kuyruklarını yalnız GUI komutu veya `SubscribeToCommands` ile açar. trade-data-app motor yeniden bağlanınca abonelikleri yenilemez ([veri-akisi § 5.1](../10-servisler/trade-data-app/veri-akisi.md#51-bağlanma-yeniden-bağlanma-bağlantı-yokken)), yeni GUI de yalnız kendi WS'i koparsa yeniden subscribe eder. Sonuç: AlgoProd restart'ından sonra açık paneller (arbitraj aktiviteleri, özet) panel yeniden açılana kadar güncellenmez. ❓ doğrulanmadı: canlıda gözlendi mi. Bu, veri-akisi § 5.1'deki "motorların abonelik durumunu koruyup korumadığı" sorusunu HFT için "durum tutmuyor, gerek yok", AlgoProd için "kaybediyor" diye cevaplar.
- **güvenlik: strateji komutunda hesap sahipliği kontrol edilmez.** `GuiStrategySetCommands` JWT'yi yalnız doğrular; `fields`'taki hesap/`uniqueKey`'in token kullanıcısına ait olup olmadığına bakmaz, motora da trade-data-app'in kendi token'ı gider. Geçerli JWT'si olan her GUI kullanıcısı her hesabın stratejisini başlatıp durdurabilir (K-16 ailesi).
- **doğrula: backend-sozlesmesi § 5 "Motor hatası 500 + message"** ifadesi koda göre eksik: motorun gRPC kodu gateway'de korunur (ör. arbitraj `FAILED_PRECONDITION` → 400, [arbitraj § Paket](../20-stratejiler/arbitraj.md#paket-yönetimi-ve-kalıcılık) bunu doğru yazar). 500 yalnız düz Go hatası ve `INTERNAL`'da.
- **doğrula: trade-data-app → motor çağrısında deadline yok.** Motor kilitlenirse (ör. AlgoProd `insertStrategyInfo`, K-151) her yeni komut bir gRPC handler goroutine'ini süresiz tutar.
