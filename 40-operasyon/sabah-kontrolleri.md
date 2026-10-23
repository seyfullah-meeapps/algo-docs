---
kapsam: Hafta içi her sabah 08:30'a kadar yapılan servis kontrolleri — sunucu, container, log ve canlı emir testi
kaynak:
  - repo: algo-configs
    branch: master
    commit: ab35dde           # doc/Development/Sabah_Kontrolleri.docx (insan için yazılmış asıl liste)
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
dogrulama: 2026-10-22
durum: taslak
---

# Sabah kontrolleri

Kaynak, algo-configs'teki `doc/Development/Sabah_Kontrolleri.docx` dosyasıdır. Adımlar güncel koda göre yeniden yazıldı. Docx'in eskimiş yerleri en sondaki tabloda.

Satırların tam biçimi, hangi kanalda (`docker logs` ya da dosya) göründüğü ve hata imzaları [log-imzalari.md](log-imzalari.md)'dedir. Bu dosya yalnızca **sırayı ve neye bakılacağını** verir.

**Son saat: 08:30.** Servisler cron'la 07:43–07:45'te başlar ([kurulum-ve-dagitim § setup_mode → servisler ve crontab](kurulum-ve-dagitim.md#setup_mode--servisler-ve-crontab-development)). İlk toplu emir çekimi 09:19'da yapılır (VİOP sabah). Arıza bu saatten önce giderilmelidir.

## Kontrol edilen sunucular

| Sunucu | Servisler | Ne zaman |
|--------|-----------|----------|
| `<HFT_SUNUCU_IP>` | trade-data-app (varsa), order-service, HftSrvProd | Her iş günü |
| `<ALGO_SUNUCU_IP>` | AlgoProd | Her iş günü |
| `<TEST_SUNUCU_IP>` | HFT sunucusuyla aynı | Yalnız test dönemlerinde |

- Müşteri sunucusunda hangi servislerin bulunduğu `setup_mode`'a bağlıdır ([kurulum-ve-dagitim](kurulum-ve-dagitim.md)).
- Bağlantı SSH ile yapılır; sunucu bilgileri bu bilgi tabanında yoktur.

## A. HFT sunucusu

### 1. Container'lar ayakta mı

```
docker ps
```

- Beklenen container'lar: `MADatabaseService` (`hft_order_db` modunda), `MAOrderService`, `MAHft`.
- Container adları branch'e ve compose varyantına göre değişir: development'ta `*Test`, preprod'da `*PreProd`. Tablo: [kurulum-ve-dagitim § Adlar](kurulum-ve-dagitim.md#adlar-compose-container_name).
- ❓ doğrulanmadı: Piramit sunucusundaki gerçek adlar. Docx bu sunucu için `MAOrderServiceProd` / `MAHftProd` diyor; Algo-Setup'ta bu adlar hiçbir branch'te yok.

### 2. trade-data-app (DB servisi)

`docker logs --tail 200 <db container>` → [log-imzalari § 1](log-imzalari.md#1-trade-data-app-madatabaseservice).

- `[SNAPSHOT] All configured markets are ready` ve `Binding to Signal Handler` satırları görülmeli.
- `Login Successfull for User: …` satırı order-service'in bağlandığını gösterir.
- ⚠ Bu log'da kullanıcı şifreleri ve token'lar düz metin basılır (K-180). Ekran görüntüsü paylaşırken dikkat edilmeli.

### 3. order-service

`docker logs --tail 200 <order-service container>` → [log-imzalari § 2 Açılış](log-imzalari.md#açılış-1).

- `Token is received: …` → DB servisinden token alındı.
- `Instruments were fetched successfully. Count: N` → `N` sıfır olmamalı ve dünkü değere yakın olmalı.
- `Grpc Server listening on 0.0.0.0:<grpcPort>` → servis **HAZIR**.
- OUCH login satırları (`Login accepted for user …`) müşteri config'lerinde `log.stdout: false` olduğu için `docker logs`'ta **görünmez**. Bunlara dosyada bakılır (4. adım).

### 4. Toplu emir zamanlayıcıları

Log dizini: `$HOME/workingDirectory/container-logs/<order-service log dizini>/`. Dizin adı branch'e göre değişir; development'ta `OrderServiceTest`. Bkz. [log-imzalari § 0](log-imzalari.md#0-log-nerede).

```
grep -a "will be fetched at" order_service.txt
grep -a "Login accepted for user" order_service.txt
```

- Aktif dosya `order_service.txt`'dir. `order_service.1.txt` en son **dönen** (eski) dosyadır; docx'in grep'lediği dosya buydu. Açılış satırları 256 MB'lık rotasyondan sonra `.1`'e geçebilir; bulunamazsa ikisine de bakılmalı.
- `fetched at` sonrasındaki sayı Unix epoch **nanosaniye**dir. Saati görmek için: `date -d @$((N/1000000000))`. Container saat dilimi `Europe/Istanbul`; host'un saat dilimi farklıysa `TZ=Europe/Istanbul date …` kullanılmalı.
- Beklenen satırlar ve saatler (Algo-Setup development müşteri config'leri; müşteri config'i farklıysa o geçerli). Tam tablo: [log-imzalari § Sabah işleri](log-imzalari.md#sabah-işleri).

  | Satır | Gösterdiği saat (TR) |
  |-------|----------------------|
  | `Type: MORNING_VIOP` | 09:19:00 |
  | `group: Derivative` | 09:29:00 |
  | `Type: MORNING` (OUCH ve FIX satırı ayrı; FIX satırında da `Protocol: Ouch` yazar) | 09:39:00 |
  | `group: Equity` | 09:59:00 |
  | `Type: THEORIC` | 18:00:00 |

- `Opening orders are not configured, flow is disabled. Group: Warrant` / `Group: Yip` WARN satırları, config'te bu bloklar yoksa normaldir.
- Satırın saati **bugünün** tarihini göstermiyorsa ya da beklenen satır yoksa order-service yeniden başlatılır (bkz. Yeniden başlatma).

### 5. HftSrvProd

`docker logs --tail 200 <hft container>` → [log-imzalari § 3](log-imzalari.md#3-hftsrvprod).

- `ItchSdkClient started (unified method).` → ITCH aboneliği (Glimpse) bütün partition'larda bitti.
- `DatabaseServiceClient::Connect - Connection result: SUCCESS` → DB servisinden token alındı.
- Banner'da `HFT INITIALIZATION COMPLETE` / `Status: LIVE`.
- `[DEBUG] ouchSDK::login() returned: true` → order-service'e bağlandı. Bu satır banner'dan sonra gelebilir. `called` satırı var ama `returned` yoksa order-service'e ulaşılamıyor demektir; bekleme zaman aşımsızdır ([log-imzalari § 3 Hata imzaları](log-imzalari.md#hata-imzaları-2)).
- `MAOrderSDK: 0 active OUCH user(s)`, `OUCH Users: 0 connected` ve `hft.txt`'teki `zero-handoff` satırı sabah **normaldir**. OUCH kullanıcıları 09:40'taki handoff'la gelir.
- Onload kullanan müşterilerde: `Restarting with Onload` var **ve** `ld.so … cannot be preloaded` hatası yok.

### 6. Canlı emir testi (seans öncesi ret)

Amaç: GUI → trade-data-app → order-service → BIST zincirinin uçtan uca açık olduğunu görmek. Seans dışında gönderilen emir BIST'ten `-110023 Illegal transaction at this time` koduyla reddedilmelidir.

1. GUI açılır, `<TEST_HESAP>` hesabı ve **GARAN** seçilir. Hesap müşteriye göre değişir; değer docx'te.
2. Sağ tık → emir gir: **alış**, miktar **1.000.000**, fiyat **14,00**.
3. Emir geçmişinde art arda birkaç emir (docx: 4–5) görülür. Hepsi reddedilmiş olmalıdır.
   - Birden fazla emir görünmesi beklenen bir davranıştır. MAOrderSDK, enstrümanın `max_order_value`'sunu aşan emri bölerek gönderir ([MAOrderSDK emir-akisi](../10-servisler/maordersdk/emir-akisi.md)).
4. Reddedilen emre tıklanır; ret açıklaması `Illegal transaction at this time` olmalıdır.

Kontrol listesine göre:
- Ret **BIST'ten** gelmelidir. `MAOrderSDK LOCAL REJECT (never sent to BIST) … code=100x` satırı yereldeki bir sorunu gösterir. 1001 açılışta eksik enstrüman listesi alındığını, 1003 ise hard cap'in aşıldığını gösterir ([log-imzalari § 2 Hata imzaları](log-imzalari.md#hata-imzaları-1)).
- Hiç yanıt gelmiyorsa OUCH oturumu açık değildir (3. ve 4. adım).

❓ doğrulanmadı: GARAN'ın günlük fiyat bandının dışındaki bir fiyatta (14,00) seans öncesi BIST'in önce fiyat kontrolü mü yoksa seans kontrolü mü yaptığı. Docx `-110023` beklediğini söylüyor.

## B. AlgoProd sunucusu

1. `docker ps` → `MAAlgoProd`. Docx `MAAlgorithmicTrading` diyor; Algo-Setup'taki ad her branch'te `MAAlgoProd`.
2. `docker logs --tail 200 MAAlgoProd` → [log-imzalari § 4](log-imzalari.md#4-algoprod-algorithmictrading). Beklenenler:
   - `login succesful` (order-service'e bağlandı)
   - `ItchSdkManager started (ITCH SDK v3).`
   - `Server listening on 0.0.0.0:<clientPort>` → **HAZIR**.
3. Canlı emir testi: Arbitraj GUI'sinde `DE-<TEST_HESAP>` hesabı ve en yakın vadeli **F_GARAN** kontratı seçilir. **Alış**, miktar **1**, fiyat **1**. Beklenen sonuç: ret, `Illegal transaction at this time`.

## Yeniden başlatma

Bağımlılık sırası: DB servisi → order-service → HFT/AlgoProd ([sistem haritası](../00-genel/sistem-haritasi.md#başlatma-sırası)). **Gün içi restart yalnız arızalı servise göre seçilmez:** MARpc otomatik yeniden bağlanmaz; HFT handoff kullanıcısı aynı order-service process'inden tekrar devredilmez.

Servis başına sonuçlar ve koddan çıkarılan yeniden başlatma sırası [kopma-ve-kurtarma § Servis restart'ları](../30-akislar/kopma-ve-kurtarma.md#servis-restartları)'ndadır. Canlıda denenmiş bir kurtarma prosedürü değildir. Restart öncesi gerçek handoff durumu, açık emirler ve pozisyon kontrol edilir; SetBalance OUCH bağlantısını geri getirmez.

Yeniden başlatma sonrasında bu belgedeki ilgili servis kontrolleri, OUCH bağlantısı/replay ve pozisyon kontrolü tekrarlanır; stratejiler otomatik başlamaz. Sabah toplu gönderim penceresinin kaçırılması restart ile telafi edilmez.

Dikkat edilecekler:
- order-service sabah saatinden (09:40) **sonra** başlatılırsa OUCH kullanıcılarını hemen HFT'ye devreder. `Late startup detected` satırı basılır ([log-imzalari § Sabah işleri, Handoff](log-imzalari.md#sabah-işleri)). Gönderim anı (T) geçmiş ya da T'ye 5 sn'den az kalmış tekrarlı akış log basmadan atlanır; açılış akışında sınır 30 sn'dir (`It is too late…`). Yani geç yeniden başlatma o günün geçmiş akışlarını **göndermez**.
- HFT ve AlgoProd `docker stop` ile temiz kapanmaz (`run.sh` `kill -15 <isim>` hatası, K-183). Süreç SIGKILL ile öldürülür.

## Docx ile farklar (2026-10-22)

| Docx | Güncel |
|------|--------|
| Container `MAOrderServiceProd`, `MAHftProd` (Piramit) | Algo-Setup'ta prod adı `MAOrderService`, `MAHft`. Piramit sunucusundaki ad doğrulanmadı |
| AlgoProd container `MAAlgorithmicTrading` | `MAAlgoProd` |
| `grep -a "fetch" order_service.1.txt` | Aktif dosya `order_service.txt`; aranacak sabit metin `will be fetched at` |
| `Morning Order For Part1/Part2`, `Opening Order For …` satırları | Bu biçimde satır kodda yok. Karşılıkları `Repeatable orders will be fetched at …, Type: MORNING` ve `Opening orders will be fetched at …, group: …` |
| Zaman damgası epochconverter.com ile çevrilir | Değer epoch **nanosaniye**. Sitede saniyeye çevrilmeden girilirse yanlış tarih gösterir; `date -d @$((N/1000000000))` |
| Yalnız 09:39 ve 09:59 kontrol edilir | Development config'lerinde ayrıca 09:19 (VİOP sabah), 09:29 (vadeli açılış) ve 18:00 (teorik) akışları var |
| Sunucu IP'leri ve test hesap numaraları açık yazılı | Bu bilgi tabanında maskeli (`<HFT_SUNUCU_IP>`, `<TEST_HESAP>`) |
