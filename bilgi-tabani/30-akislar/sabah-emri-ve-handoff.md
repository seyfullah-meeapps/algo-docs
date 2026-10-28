---
kapsam: Bir iş gününün zaman çizelgesi — toplu emir girişi, servis açılışları, sabah gönderimi, OUCH handoff (order-service → HFT), replay gate, açılış/YİP/teorik gönderimleri, gece kapanış; handoff gelmezse, geç açılışta ve geç restart'ta ne olur
kaynak:
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: HftSrvProd
    branch: master
    commit: 052dd96
  - repo: order-service
    branch: master
    commit: 298403b
  - repo: AlgorithmicTrading
    branch: master
    commit: aa150ee
  - repo: AlgorithmicTrading
    branch: add-order-sdk
    commit: 7d7f705
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-23
durum: taslak
---

# Sabah emri ve OUCH handoff — gün boyu akış

Bu dosya yalnızca **sırayı, tetikleri ve sınırları** verir. Mekanizmalar ayrıntı dokümanlarında; her adımda link var:
- Toplu emir akışları: [order-service/toplu-emirler](../10-servisler/order-service/toplu-emirler.md)
- Handoff, order-service tarafı: [order-service/sdk-ve-oturumlar § 7](../10-servisler/order-service/sdk-ve-oturumlar.md#7-ouch-handoff--order-service-tarafı)
- Handoff ve replay gate, HFT tarafı: [hftsrvprod/emir-yasam-dongusu § 4](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı), [strateji-cekirdegi § Replay gate](../10-servisler/hftsrvprod/strateji-cekirdegi.md#replay-gate)
- Log satırları: [log-imzalari § Sabah işleri](../40-operasyon/log-imzalari.md#sabah-işleri), [§ Handoff ve replay](../40-operasyon/log-imzalari.md#handoff-ve-replay-hft-tarafı)
- Operatörün sabah kontrolü: [sabah-kontrolleri](../40-operasyon/sabah-kontrolleri.md)
- Kopma ve restart senaryoları: [kopma-ve-kurtarma](kopma-ve-kurtarma.md)

Saatler Algo-Setup `development` müşteri config'lerinden (yerel saat, `Europe/Istanbul`). Repo örnek `config.yaml`'ı farklıdır (ör. vadeli açılış 09:40:00.100, varant ve YİP blokları dolu; [toplu-emirler § 8](../10-servisler/order-service/toplu-emirler.md#8-örnek-zaman-çizelgesi-örnek-configyaml-servis-0900dan-önce-başlamış)). Müşterinin gerçek değeri her zaman kendi config'idir.

**Prod farkı:** Handoff prod'da da var. `master`'da HFT tarafı (052dd96) development ile aynı mekanizmadır (MAOrderSDK, 4 denemeli `connectUser`, replay gate, 20 s watchdog). order-service `master`'ı (298403b) ise eski `Managers/Ouch/OuchManager` yapısındadır; ayrıntı § 12.

## Özet zaman çizelgesi

| Saat | Süreç | Tetik | Ne olur |
|------|-------|-------|---------|
| Önceki gün / gün içi | GUI → trade-data-app → order-service → DB | Operatör | Toplu emir satırı (`MORNING` / `OPENING` / `EVENING`) DB'ye yazılır (§ 1) |
| 22:30 (önceki akşam) | Algo-Setup `backupAllDatabases.sh` → `dbNightEvent.sh` | cron | `RemoveOldData`: OUCH `STRATEGY`/`EVENING` ve VİOP satırları silinir; pay `MORNING`/`OPENING` satırları **kalır** (§ 1) |
| 07:43 / 07:44 / 07:45 | trade-data-app / order-service / HFT | cron | Açılış; order-service bütün OUCH kullanıcılarına login olur, HFT login olmaz (§ 2) |
| ~07:45 + 20 s | HFT | zero-handoff watchdog | Replay gate açılır (§ 2) |
| 09:19:00 | order-service | `repeatableOrders.ouch[morning_viop]` T−60 s | VİOP sabah satırları çekilir (§ 3) |
| 09:20:00.010 | order-service | T + `millisecond` | VİOP sabah gönderimi; akış sonunda handoff tetiği A (⚠ K-84, § 5) |
| 09:29:00 / 09:30:00.100 | order-service | `openingOrders.derivative` | Vadeli açılış çekimi / gönderimi (§ 8) |
| 09:39:00 | order-service | T−60 s | OUCH ve FIX sabah satırları çekilir |
| 09:40:00.120–146 | order-service | T + `millisecond` | FIX ve OUCH sabah gönderimi: round'lar, son atış (§ 4) |
| ~09:40:03+ | order-service | thread'ler join + 2 s | Fazla kopya iptali, satırlar pasif, handoff tetiği A (§ 4–5) |
| 09:40:30 | order-service | `morning` T + 30 s | Handoff tetiği B: kalan `onlyMorningOrderUser` kullanıcıları (§ 5) |
| handoff + ~10–15 s | HFT | `onReplayCompleted` (her kullanıcı) | Gate açılır, HFT emirleri MAOrderSDK'dan doğrudan gider (§ 6–7) |
| 09:59:00 / 10:00:00.100 | order-service | `openingOrders.equity` | Pay açılış çekimi / gönderimi (§ 8) |
| 18:00:00 / 18:01:00.130 | order-service | `repeatableOrders.fix[theoric]` | Teorik (`EVENING`) satırları FIX'ten (§ 9) |
| 19:00:00 | order-service | `eveningSessionStart` | `offhours` bayrağı (§ 9) |
| 23:29 / 23:30 / 23:45 | HFT / order-service / trade-data-app | cron `docker stop` | Kapanış (§ 10) |

Cron saatleri `hft_order_db` modu içindir; diğer modlar: [kurulum-ve-dagitim § setup_mode](../40-operasyon/kurulum-ve-dagitim.md#setup_mode--servisler-ve-crontab-development).

## 1. Toplu emir girişi (önceki gün veya gün içi)

1. Operatör Toplu Emirler ekranından emir girer. Yeni GUI `collectiveOrderPayloads.ts`, eski GUI `OrderForm.tsx` (fiyat sabit ×1000, VİOP'ta 10× sapma: K-163). Wire alanları: [backend-sozlesmesi § 6](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#6-emir-gönderme-post-v1sendorders).
2. `POST /v1/sendOrders` → trade-data-app `GuiSendOrders`: ITCH açıksa `LevelCount` kademeye açar (fiyat raw, her kademe bir tick) → order-service gRPC `SendOrder`.
3. order-service satırları DB'ye yazar (`BulkInsertMorningOrder` / `Opening` / `Evening` → `DataService.SetOrders`) ve GUI stream'ine `kOrderAccepted` yayınlar. Ayrıntı: [toplu-emirler § 2](../10-servisler/order-service/toplu-emirler.md#2-guiden-kayıt-order-service-tarafı).

- Toplu satır order-service'in **belleğinde tutulmaz**. Akış saatinde DB'den taze çekilir. Bu yüzden gün içi order-service restart'ı girilmiş satırları kaybettirmez.
- **Kesim anı T−60 s'dir.** Çekimden sonra girilen satır o günün akışına girmez. ❓ doğrulanmadı: satır aktif kaldığı ve `GetOrders` tarih filtresi uygulamadığı için ([kalicilik-ve-config § RetrieveSentOrders](../10-servisler/order-service/kalicilik-ve-config.md#retrievesentorders-açılışta)), ertesi günün aynı akışında gider. YİP için bu davranış belgelenmiş (seans N+1).
- Akış sonrası satırlar `is_active=false` ile yeniden yazılır, GUI'de "pasif" görünür. Ertesi gün gitmesi için operatörün yeniden aktifleştirmesi gerekir. Gönderilemeyen satırlar da pasife alınır (K-93).

## 2. 07:4x — servis açılışları

Sıra ve bağımlılık: [sistem-haritasi § Başlatma sırası](../00-genel/sistem-haritasi.md#başlatma-sırası).

| Servis | Handoff açısından ne yapar | Hazır log'u |
|--------|----------------------------|-------------|
| trade-data-app | ITCH snapshot'ı bekler, gRPC'yi açar. WS ve motor bağlantıları ilk `DataService.Login`'den (order-service) sonra açılır | [log-imzalari § 1](../40-operasyon/log-imzalari.md#1-trade-data-app-madatabaseservice) |
| order-service | **Bütün** OUCH kullanıcılarına sırayla login olur; `onlyMorningOrderUser` ayrımı yoktur. FIX logon. Toplu akış thread'lerini kurar (`… will be fetched at …`). `morning` satırı için T + 30 s handoff zamanlayıcısını kurar | [log-imzalari § order-service Açılış](../40-operasyon/log-imzalari.md#açılış-1) |
| HFT | MAOrderSDK `start()`, **`connectUser` yok**. Glimpse → strateji yükleme (hepsi durmuş, bakiye 0) → order-service'e MARpc login → `getAllOrders` | [log-imzalari § HFT Açılış](../40-operasyon/log-imzalari.md#açılış-2) |

- **Watchdog:** HFT `startPeriodicJobs` içinde tek seferlik 20 s zamanlayıcı kurar. 20 s sonunda henüz handoff yoksa replay gate açılır ve `no OUCH handoff within 20s — opening gate (zero-handoff)` basılır. Bu her sabah normaldir. 20 s **HFT açılışından** sayılır, 09:40'tan değil.
- 07:45:20 ile handoff arasında HFT stratejileri (operatör başlatırsa) **OS yolundan** emir gönderir: HFT → ouch-sdk → order-service → BIST ([emir-yasam-dongusu § 2](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#2-gönderim)). Seans açılmadan giden emri BIST `-110023` ile reddeder.

## 3. T−60 s — DB'den çekim

- Her `repeatableOrders` satırı ayrı detached thread'dir. `WaitUntilFetch` T−60 s'ye kadar uyur, `GetMorningOrders(protocol)` ile satırları çeker.
- Seçim koşulları (aktif, `B`/`S`, piyasa, `part`) ve tekrarlı/tekrarsız ayrımı: [toplu-emirler § 3.2–3.3](../10-servisler/order-service/toplu-emirler.md#32-emir-seçimi-partitionrepeatablenonrepetableorders).
- Kullanıcılar `GetUsers(protocol, part, mode)` ile **DB'den taze** okunur. Tekrarlı satırlar izinli kullanıcılara kopyalanır; 24 Ekim development `26e9a02` tekrarsız satırları kullanıcılar arasında böler. Ayrıntı ve kapasite sınırı [güncel dağıtım farkında](../10-servisler/order-service/toplu-emirler.md#24-ekim-güncel-davranış-farkı); eski “bütün satırlar her kullanıcıya” özeti güncel değildir.
- Servis T−5 s'den sonra açıldıysa akış log basmadan atlanır (K-94).

## 4. T — sabah gönderimi

Ayrıntı: [toplu-emirler § 3.4–3.6](../10-servisler/order-service/toplu-emirler.md#34-gönderici-thread-sendrepeatableorderstoexchangemarket).

1. **Thread'ler:** OUCH kullanıcısı başına bir `pthread`, `SCHED_FIFO` 99 (`repeatableOrders.settings.schedPolicy`), çekirdek DB `coreToPin`. T + `millisecond` anına kadar 100 µs yoklamalı uyku.
2. **Round'lar:** `max_repeat − 1` round, aralarında `duration / (max_repeat − 1)` **ms** uyku (`duration` ms'dir; `OrderManager.cpp` `elapse_interval`; config referansı bu birime göre düzeltildi). Round'larda ret beklenmez. `packOrders: true` ise round tek pakette gider.
3. **Son atış** (`repeatLastShot`):
   - `false`: 1 s uyku + her emri bir kez gönder.
   - `true`: `-110023` ("Illegal transaction at this time") alan emir 500 µs aralıkla yeniden gönderilir; yanıt gelmeyen alışa 2 ms sonra en çok `timeoutOrderCount` (varsayılan 2) timeout kopyası. Kabul veya başka ret alan emir listeden çıkar. Üst sınır **900 ms** ("Sending guaranteed last shot timed out!").
4. **Gönderim sonrası** (bütün thread'ler join edildikten sonra, sırayla):
   1. Gönderilen her kopya `STRATEGY` olarak DB'ye yazılır.
   2. 2 s uyku.
   3. `CancelRepeatedOrders`: hesapta `IsCancelAllowed` açıksa, aynı (hesap-strateji, fiyat, yön, miktar, TIF, tip) grubundaki kabullerden en erken `OrderRepeatRemainingCount` adedi tutulur, kalanı iptal edilir. İptal izni yoksa bütün kopyalar borsada kalır (K-92).
   4. Satırlar silinip pasif olarak yeniden yazılır.
   5. Handoff tetiği A (§ 5).

Log: `repeatable_orders: N non_repeatable_orders: M`, `Cancellation starting...` ([log-imzalari § Sabah işleri](../40-operasyon/log-imzalari.md#sabah-işleri)).

## 5. Handoff — order-service tarafı

Ayrıntı: [sdk-ve-oturumlar § 7](../10-servisler/order-service/sdk-ve-oturumlar.md#7-ouch-handoff--order-service-tarafı).

| Tetik | Ne zaman | Kapsam |
|-------|----------|--------|
| **A. Akış sonu** | Her `repeatableOrders` satırı (§ 4.4.5) | O satırın `GetUsers` kullanıcıları; pazar süzülmez. Satır yoksa (0 emir) veya akış geç kaldıysa çalışmaz |
| **B. Zamanlayıcı** | `ouch[type == "morning"]` T (saniye) + 30 s | Henüz devredilmemiş bütün `onlyMorningOrderUser` kullanıcıları |
| **C. Geç başlatma** | order-service `morning` T'den sonra açıldıysa, hemen | Aynı (§ 11.3) |

Her kullanıcı için `TryDisconnectUser`:
1. Kullanıcının `applicationUsername`'i (ör. HFT'nin MARpc kullanıcısı) order-service'e bağlı olana kadar 500 ms aralıkla **süresiz** beklenir (`… not connected yet, waiting...`).
2. `markIntendedDown`: reconnect shim'i bu kullanıcı için gün boyu kapalı.
3. `disconnectUser`: yalnız TCP soketi kapanır. **SoupBinTCP LogoutRequest gönderilmez** (K-86). BIST oturumu TCP kapanışıyla düşer.
4. MARpc `UserDisconnected` (kullanıcı adı, açık metin şifre, birincil ip/port, izinli hesaplar, `callbackNumber/total`) uygulama kullanıcısının bütün bağlantılarına gider.

- `morning_viop` akışı (09:20) da A tetiğini çalıştırır ve pazar süzmez. VİOP sabah satırı olan bir günde **pay** kullanıcıları da ~09:21'de devredilir; 09:40 pay sabah emirleri bağlı olmayan kullanıcıya yönlenir ve sessizce gitmez (K-84).
- B zamanlayıcısı, sabah akışı 30 s içinde bitmediyse kullanıcıyı akışın ortasında kapatabilir (K-85).
- Config'te `type: MORNING` (büyük harf) yazılırsa B kurulmaz (K-89).

## 6. Handoff — HFT tarafı

Ayrıntı: [emir-yasam-dongusu § 4](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#4-handoff--hft-tarafı). Log sırası: [log-imzalari § Handoff ve replay](../40-operasyon/log-imzalari.md#handoff-ve-replay-hft-tarafı).

1. `ouchSDK::orderUserDisconnected` ouch-sdk callback thread'inde çalışır. Kullanıcılar sırayla işlenir.
2. Process ömründe **ilk** callback'te `registerExpectedReplays(total > 0 ? total : 1)`: gate **kapanır** (watchdog açmış olsa bile) ve tek seferlik 60 s güvenlik zamanlayıcısı kurulur.
3. `maordersdk::OuchUser` handoff verisinden kurulur (`market = Equity` sabit, ikincil endpoint yok) → `connectUser`. `Ok`/`AlreadyConnected` dışı sonuçta 1, 2, 3, 4 s arayla 4 deneme daha. Hepsi başarısızsa yalnız WARN: o kullanıcı gün boyu kimsede bağlı değildir (2026-08-03 olayı; [kopma-ve-kurtarma](kopma-ve-kurtarma.md)).
4. Login sonrası BIST günün mesajlarını sequence 1'den replay eder. SDK yabancı token'ları adopt eder. Accept'ler `claimGlobalAcceptedToken` ile ayıklanır; execute'lar ayıklanmaz (K-57).
5. Her kullanıcı için `replay_quiet_window_ms` (varsayılan 10 000 ms, HFT `sdkReplayQuietWindowMs`) boyunca yeni veri gelmezse ve en az bir server heartbeat görüldüyse `onReplayCompleted` → `notifyUserReplayCompleted`. Sayaç 0'a inince gate açılır (`ALL OUCH user replays complete`). Mekanizma: [ouch-protokolu § 5](../10-servisler/maordersdk/ouch-protokolu.md#5-sequence-replay-ve-onreplaycompleted).
6. 60 s içinde bitmezse gate zorla açılır (`replay gate TIMEOUT … FORCING gate open`).

Gate kapalıyken: stratejiler ITCH olayı işlemez ve emir göndermez; olaylar kuyrukta birikir ve gate açılınca bayat olarak işlenir (K-55). GUI manuel emirleri, `cancelAllOrders` ve `closePosition` gate'e takılmaz.

## 7. HFT canlı

- Devredilen hesapların emirleri artık SDK yolundan gider: `ownsAccount(hesap)` true → MAOrderSDK → BIST. Koşullar ve yol seçimi tablosu: [emir-yasam-dongusu § 2](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#2-gönderim).
- Handoff öncesi OS yolundan açılmış emirler replay'den sonra SDK'nındır (`ownsOrder` true). Replay'den önceki kısa aralıkta bunların cancel'ı OS yoluna gider ve order-service'te `onSdkError(10)` ile sessizce düşer ([§ Handoff öncesi açılmış emirlerin sahipliği](../10-servisler/hftsrvprod/emir-yasam-dongusu.md#handoff-öncesi-açılmış-emirlerin-sahipliği)).
- order-service bu kullanıcıların olaylarını artık görmez. Sabah emirlerinin 09:40 sonrası fill/cancel'ları order-service'in DB'sine ve GUI stream'ine gitmez ([sdk-ve-oturumlar § 7.5](../10-servisler/order-service/sdk-ve-oturumlar.md#75-handoff-sonrası-o-kullanıcıyla-ilgili-order-service-davranışı)).
- Gün içi ikinci bir handoff turu gate'i yeniden kurmaz (`replaysRegistered` static).

## 8. Açılış gönderimleri (vadeli, pay, varant, YİP)

Ayrıntı: [toplu-emirler § 4–5](../10-servisler/order-service/toplu-emirler.md#4-açılış-akışı-maosdkmanagersendopeningordersconfig-group).

| Grup | Config | Müşteri saati | Not |
|------|--------|---------------|-----|
| Vadeli | `openingOrders.derivative` | 09:30:00.100 | Handoff'tan önce |
| Pay | `openingOrders.equity` | 10:00:00.100 | Handoff'tan sonra |
| Varant/sertifika | `openingOrders.warrant` | yok → akış kapalı | ⚠ master'da yok |
| YİP | `openingOrders.yip.sessions[]` | yok → akış kapalı; YİP bayraklı satırlar hiç gitmez | ⚠ master'da yok |

- T−60 s'de `OPENING` satırları (OUCH + FIX) çekilir. T + ms'den itibaren her 75 µs bir tur, üst sınır **2000 ms**. `-110023` alan satır bir sonraki turda yeniden gönderilir; başka ret veya kabul satırı bitirir.
- OUCH satırında kullanıcı `NextClientForAccount` round-robin'iyle seçilir; `onlyMorningOrderUser` kullanıcıları da listededir. **Pay açılışı handoff'tan sonradır:** seçilen kullanıcı devredilmişse `SubmitEnterOrder` boş döner (`onSdkError(1)`) ve sonraki turda sıradaki kullanıcı denenir. Hesabın order-service'te bağlı başka OUCH kullanıcısı yoksa satır 2 s boyunca hiç gitmez ve pasife alınır (koddan çıkarım, `MAOSdkManager::SendOpeningOrders`; doğrula). Aynı durum K-84 ile 09:21'de devir olmuşsa vadeli açılışı da etkiler.
- Açılış akışı devredilmiş kullanıcının emirlerini HFT'ye yönlendirmez; HFT'nin bağlantısını kullanmanın yolu yoktur.

## 9. Gün içi ve akşam

- **Teorik:** `repeatableOrders.fix[theoric]` 18:01:00.130. `EVENING` satırları § 4 akışıyla, FIX kullanıcılarından gider; satırlar sonra silinir. OUCH protokollü `EVENING` satırı, `ouch` listesinde `theoric` satırı olmadığından gitmez ([toplu-emirler § 6](../10-servisler/order-service/toplu-emirler.md#6-teorik-akşam-ve-off-hours)). FIX kullanıcıları handoff'a girmez.
- **Off-hours:** `eveningSessionStart` (19:00) sonrası order-service `SendOrderAsync` yolundaki emirlere `off_hours` bayrağı koyar. Toplu akışlar ve HFT SDK yolu (`toSdkMsg`: "off_hours: unused") koymaz (Şüpheli).

## 10. Gece kapanış

- 22:00 `setup_copy_binary.sh` (bozuk, K-179); 22:30 DB yedeği + `RemoveOldData`.
- 23:29 HFT, 23:30 order-service, 23:45 trade-data-app `docker stop`. HFT/AlgoProd SIGTERM almaz, SIGKILL ile ölür (K-183). Kapanışta stratejiler durdurulmaz, emirler iptal edilmez, pozisyon yazılmaz ([strateji-cekirdegi § Servis restart'ı](../10-servisler/hftsrvprod/strateji-cekirdegi.md#servis-restartı)). Log arşivi: [log-imzalari § 5](../40-operasyon/log-imzalari.md#5-kapanış).
- OUCH oturumları TCP kapanışıyla düşer. BIST End of Session (`Z`) gelirse SDK `onUserDisconnected` üretmez (K-113).

## 11. Sapmalar

### 11.1 Handoff hiç gelmezse

Handoff'un hiç gelmediği durumlar ve sonucu:

| Neden | Sonuç |
|-------|-------|
| DB'de `onlyMorningOrderUser` kullanıcı yok | Normal kurulum biçimi. order-service kullanıcıları gün boyu tutar; HFT emirleri gün boyu OS yolundan gider (gate 20 s'de açık). |
| Kullanıcının `applicationUsername`'i boş | `TryDisconnectUser` erken döner, kullanıcı order-service'te kalır; aynı sonuç. |
| HFT order-service'e MARpc ile hiç bağlanmadı (K-151) | Tetik thread'i süresiz bekler ve `disconnect_mutex_`'i tutar (K-85); kullanıcı order-service'te kalır. HFT'nin OS yolu da yok: HFT emir gönderemez. |
| Sabah satırı yok **ve** B tetiği kurulmadı (`MORNING` büyük harf, K-89) | A çalışmaz (0 emir), B yok → devir yok, OS yolu. |
| Uygulama kullanıcısı AlgoProd | AlgoProd `orderUserDisconnected`'ı işlemez ("not implemented"; development ve master). order-service kullanıcıyı yine kapatır → o kullanıcı gün boyu kimsede bağlı değil (§ 13). |

- HFT tarafında gate 20 s watchdog'uyla zaten açıktır; stratejiler OS yolundan çalışır. "Emirler order-service yolundan gider" ifadesi yalnız order-service kullanıcıyı hâlâ tutuyorsa doğrudur.
- OS yolunda: risk kontrolü order-service'tedir, hot path değildir, ret kodları ve combiner farklıdır ([sistem-haritasi § Emir yolları](../00-genel/sistem-haritasi.md#emir-yolları)).

### 11.2 Geç açılış

- **BIST seansı geç açılırsa:** sabah son atışı 900 ms, açılış döngüsü 2 s sonra durur. Kabul almayan satırlar gönderilmemiş olarak pasife alınır; ayrı bir "gönderilmedi" durumu yoktur (K-93). Akış yine biter ve handoff (A, B) normal yürür. Gün içinde toplu akışı yeniden çalıştırmanın yolu yoktur; emirler elle (GUI strateji ekranı / HFT manuel emir) girilmelidir.
- **HFT 09:40'tan sonra açılırsa:** order-service'in A/B tetiği HFT bağlanana kadar bekler; HFT MARpc login'i (Glimpse + strateji yüklemesinden sonra) gelince devir hemen olur. Watchdog gate'i 20 s'de açmış olabilir; handoff gelince gate yeniden kapanır, replay sonrası açılır.
- **order-service T−5 s'den (açılışta T−30 s'den) sonra açılırsa:** ilgili akışlar o gün gönderilmez (K-94); bkz. § 11.3.

### 11.3 order-service 09:40'tan sonra yeniden başlatılırsa

Ayrıntı: [sdk-ve-oturumlar § 9](../10-servisler/order-service/sdk-ve-oturumlar.md#9-oturumlar-yeniden-bağlanma-ve-kopma-senaryoları) "Gün içi restart, sabah saatinden sonra".

1. Geçmiş akışlar atlanır (sabah için log da basılmaz). Gelecek akışlar (ör. 10:00 pay açılışı, 18:01 teorik) normal çalışır.
2. Açılışta **bütün** OUCH kullanıcılarına login denenir; HFT'nin tuttuğu kullanıcılar için BIST'in ikinci login'e ne yaptığı ❓ doğrulanmadı. Reddedilirse shim 1 s aralıkla denemeye devam eder.
3. Tetik C hemen çalışır, ama HFT'nin order-service'e bağlanmasını bekler. Çalışan HFT, eski MARpc bağlantısının koptuğunu fark etmez ve yeniden bağlanmaz (K-152). Bu yüzden **HFT de yeniden başlatılmalıdır**; aksi halde tetik süresiz bekler ve HFT'nin OS yolu ölü kalır.
4. HFT yeniden bağlanınca devir tekrarlanır: HFT yeni bir process ise `connectUser` + replay + gate normal yürür.
5. Replay order-service'te de olur: accept/reject/cancel olayları uygulamalara yeniden yayılır, OUCH replay fill'leri 10 s penceresinden sonra pozisyonu ikinci kez yazar ve risk bakiyesine yeniden uygulanır (K-73).

Önerilen sıra (koddan çıkarım): HFT ve AlgoProd'u durdur → order-service'i başlat → HFT/AlgoProd'u başlat. Gerekçe ve diğer restart'lar: [kopma-ve-kurtarma § Servis restart'ları](kopma-ve-kurtarma.md#servis-restartları).

## 12. ⚠ master'da farklı (order-service 298403b)

- Toplu akışlar ve handoff `Managers/Ouch/OuchManager` + `Managers/Fix/FIXManager` içindedir; MAOrderSDK ve `SdkSessionManager` yoktur.
- Tetikler aynıdır: akış sonu (`OrderManager.cpp` → `DisconnectMorningOrderUsers`), `morning` + 30 s zamanlayıcı, geç başlatma (`OrderServiceApplication.cpp`; `type == "morning"` küçük harf kontrolü master'da da var).
- Devirde `OuchClient::Logout()` önce SoupBinTCP **LogoutRequest gönderir**, sonra bağlantıyı kapatır. development'taki K-86 master'da yoktur.
- YİP, varant açılış grubu, slice/round dağıtımı, `schedPolicy`/`coreToPin` yoktur ([toplu-emirler](../10-servisler/order-service/toplu-emirler.md)).
- ❓ doğrulanmadı: master'daki OUCH kopma/yeniden bağlanma davranışı ve sabah akışının ayrıntıları (bu dosya development'ı anlatır).

## 13. AlgoProd'un yeri

- **Bugün (development 0dc32a7, master aa150ee):** AlgoProd handoff'a katılmaz. Bütün emirleri ouch-sdk → order-service yolundan gider ([algorithmic-trading/emir-yolu](../10-servisler/algorithmic-trading/emir-yolu.md)). `ouchSDK::orderUserDisconnected` yalnız `"called, but not implemented"` basar. Bu yüzden AlgoProd'un kullandığı OUCH kullanıcıları `onlyMorningOrderUser` **olmamalıdır**. Olursa ve `applicationUsername` AlgoProd'u gösterirse, order-service kullanıcıyı kapatır, AlgoProd devralmaz ve o bağlantı devralınmaz; hesabın başka bağlı kullanıcısı da yoksa hesap OUCH'suz kalır.
- `sdk-ve-oturumlar § 7.4`'teki AlgoProd sınırı kodla kontrol edildi: `UserDisconnected` işlenmez; servis belgesi de buna göre düzeltildi.
- **🚧 `add-order-sdk` (7d7f705, merge edilmedi, K-13):** AlgoProd HFT ile aynı modeli alır: `orderUserDisconnected` → `connectUser` (4 deneme), `MAOrderSdkRouter` ile hesap bazlı yol seçimi, handoff süresince yerel ret 2001, `getAllOrders` + BIST replay tekrar elemesi, replay bitene kadar strateji kilidi ([emir-yolu § 11](../10-servisler/algorithmic-trading/emir-yolu.md)). Merge edilince bu dosyanın § 5–7'si AlgoProd için de geçerli olacak; FIX ve devredilmemiş hesaplar order-service'te kalır.

## Şüpheli

- **doğrula — Pay açılışı devredilmiş hesaplarda gitmeyebilir.** `SendOpeningOrders` OUCH satırı için `NextClientForAccount` ile yalnız order-service'in kullanıcılarını dener. 10:00'da hesabın bütün OUCH kullanıcıları HFT'ye devredilmişse `SubmitEnterOrder` her turda boş döner, 2 s sonra satır pasife alınır; ret veya CRIT dışı bir iz kalmaz (`User cannot be obtained` da basılmaz, çünkü kullanıcı listede). Prod kurulumunda HFT hesaplarının morning-only olmayan ikinci bir OUCH kullanıcısı olup olmadığına bakılmalı (§ 8).
- **doğrula — Çekimden sonra girilen toplu satır ertesi gün gidebilir.** `GetOrders` tarih filtresi uygulamaz, `RemoveOldData` pay `MORNING`/`OPENING` satırlarını silmez; T−60 s'den sonra girilen aktif satır o gün gitmez ama aktif kalır (§ 1).
- **doğrula — Akşam seansında `off_hours`.** Bayrak yalnız order-service `SendOrderAsync` yolunda set edilir. HFT SDK yolu (`MsgConvert.cpp`: "off_hours … unused, ctor defaults") ve toplu akışlar set etmez. BIST'in akşam seansında bayrağı gerektirip gerektirmediği bilinmiyor (§ 9).
- **doğrula — AlgoProd uygulama kullanıcısına bağlı morning-only kullanıcı devralınmaz; başka canlı kullanıcı yoksa hesap OUCH'suz kalır** (§ 13). Kurulum kuralı olarak belgelenmeli; admin panelinde engel yok.
