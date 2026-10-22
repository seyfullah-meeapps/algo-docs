---
kapsam: Alan ve iç terimler sözlüğü — her terim kısa tanım + ayrıntının olduğu dosya
dogrulama: 2026-10-22
durum: taslak
---

# Sözlük

Bu dosya yeni bilgi içermez. Tanımlar bu repodaki diğer dokümanlardan derlenmiştir; ayrıntı ve kaynak kod için linke git. Bir tanım linklenen dosyayla çelişirse doğru olan linklenen dosyadır.

## Protokoller ve piyasa verisi

| Terim | Anlam | Ayrıntı |
|-------|-------|---------|
| **ITCH** | BIST piyasa verisi protokolü (UDP multicast, MoldUDP64). Spot 4, VİOP 6 partition; birincil + ikincil hat. | [itch-sdk](../10-servisler/itch-sdk/README.md) |
| **Glimpse** | ITCH'in TCP snapshot servisi. Açılışta partition başına emir defterinin o anki halini verir. | [itch-sdk](../10-servisler/itch-sdk/alim-yolu.md#6-glimpse-ve-canlıya-geçiş) |
| **Rewinder** | ITCH'in UDP gap-recovery servisi. Sequence boşluğunda eksik paketler buradan istenir. | [itch-sdk](../10-servisler/itch-sdk/alim-yolu.md#5-gap-ve-rewinder) |
| **OUCH** | BIST emir protokolü (SoupBinTCP üzerinde). Piyasa emri yoktur; limit emirle taklit edilir. | [MAOrderSDK](../10-servisler/maordersdk/README.md) |
| **FIX** | FIX 5.0SP2 emir kanalı (QuickFIX, MAOrderSDK'ya statik gömülü). AlgoProd'da strateji başına `Channel_Enum` ile seçilir. | [MAOrderSDK](../10-servisler/maordersdk/README.md) |
| **MARpc** | network-sdk'nın TCP RPC'si; ouch-sdk ↔ order-service (:8000). BIST ile ilgisi yok. | [network-sdk](../10-servisler/network-sdk/README.md) |
| **ouch-sdk** | **order-service'in istemci SDK'sı.** İsmine rağmen BIST'e bağlanmaz. | [ouch-sdk](../10-servisler/ouch-sdk/README.md) |
| **MAOrderSDK** | BIST'e doğrudan OUCH/FIX bağlanan SDK. | [MAOrderSDK](../10-servisler/maordersdk/README.md) |
| **VERDA** | Borsa İstanbul günlük dosyaları: tavan/taban, maks emir değeri, brüt takas. trade-data-app TradeVerifier okur. | [trade-data-app](../10-servisler/trade-data-app/README.md#entegrasyonlar) |
| **AKD** | Aracı kurum dağılımı (Foreks). VWAP filtresinde kullanılır. | [vwap](../20-stratejiler/vwap.md#akd-aracı-kurum-dağılımı-filtresi) |
| **BYF / PCF** | Borsa yatırım fonu / fonun sepet dosyası. Fon Takibi kullanır. | [fon-takibi](../20-stratejiler/fon-takibi.md) |
| **PTRM** | Borsanın ön-işlem risk kontrolü. `-8500xx` ret kodlarıyla döner; Taban ve VWAP ilk redde durur. | [taban](../20-stratejiler/taban.md#tolerans-ve-durma) |

## Emir defteri ve emir

| Terim | Anlam | Ayrıntı |
|-------|-------|---------|
| **Header** | Bir taraftaki en iyi fiyat kademesi (best bid / best ask) ve miktarı. | [hft-classic](../20-stratejiler/hft-classic.md) |
| **Kademe (level)** | Emir defterinde bir fiyat seviyesi. "N kademe" = N tick uzaklık. | |
| **Erime** | Header miktarının bir eşiğin altına inmesi; kademenin kırılacağı sinyali. | [hft-classic](../20-stratejiler/hft-classic.md#tetik-erime) |
| **Tick** | Fiyat adımı. Tablo ITCH'ten gelir (`itchsdk_get_tick_size`). | [borsa-kurallari](borsa-kurallari.md) |
| **Raw fiyat** | Enstrümanın `decimalCount` ölçeğinde tam sayı fiyat (`priceDivider = 10^DecimalCount`). Ölçek hataları sistemin en pahalı hatalarıdır. | [yazim-kurallari](../_surec/yazim-kurallari.md) |
| **KIE** | Kalanı iptal et emri (IOC). Dolmayan kısım borsada iptal olur. | [tavan](../20-stratejiler/tavan.md), [taban](../20-stratejiler/taban.md) |
| **FaK** | Fill and Kill; AlgoProd arbitrajda aktif türev emri. | [arbitraj](../20-stratejiler/arbitraj.md) |
| **DAY** | Gün sonuna kadar geçerli limit emir. | |
| **Father order ref** | Büyük emir parçalandığında parçaları bağlayan referans. | [hftsrvprod](../10-servisler/hftsrvprod/README.md#emir-gönderme-deseni) |
| **Combiner** | MAOrderSDK'nın kendi fill'lerimizi OUCH'tan önce ITCH'ten yakalayan bileşeni. | [MAOrderSDK](../10-servisler/maordersdk/emir-akisi.md#9-combiner-srccombiner) |
| **Max-size / momentum** | Agresif emrin enstrümanın azami emir büyüklüğüne ulaşması (`isMaxSizeExecution`). | [itch-sdk](../10-servisler/itch-sdk/README.md) |
| **Denge (teorik) fiyatı** | Müzayede seansında oluşacak eşleşme fiyatı. | [teorik-fiyat](../20-stratejiler/teorik-fiyat.md) |

## Strateji ve sistem terimleri

| Terim | Anlam | Ayrıntı |
|-------|-------|---------|
| **StrategyType** | Strateji tipinin wire numarası; proto, DB, `unique_key` ve UI'da aynı. Değiştirilmez. ⚠ HFT `StrategyService`'in iki mesajı (`SubscribeToOrderbookRequest`, `StrategyOrder`) ayrı bir numaralandırma (`StrType`) kullanır. | [strateji kataloğu](../20-stratejiler/README.md) |
| **unique_key** | Strateji kimliği: `<orderbookId>_<hesap>_<strategyIdentifier>_<StrategyType>`. | [strateji kataloğu](../20-stratejiler/README.md) |
| **Tavan / Taban** | Günlük fiyat limitinin üst / alt sınırı; aynı adlı stratejiler (MaxPrice 9, MinPrice 14). | [tavan](../20-stratejiler/tavan.md), [taban](../20-stratejiler/taban.md) |
| **Second rule** | Emirden belirli süre sonra çalışan çıkış/bekleme kuralı. **Birimi stratejiye göre değişir** (HFT saniye, Tavan/Taban ms). | [hft-classic](../20-stratejiler/hft-classic.md#second-rule-saniye-kuralı) |
| **OUCH handoff (sabah devri)** | Sabah emirlerinden sonra order-service'in OUCH kullanıcılarını HFT'ye devretmesi. | [sistem haritası](sistem-haritasi.md#ouch-handoff-sabah-devri) |
| **Replay gate** | Handoff sonrası OUCH replay bitene kadar HFT stratejilerinin kapalı tutulması. | [sistem haritası](sistem-haritasi.md#ouch-handoff-sabah-devri) |
| **Hot / cold (tiering)** | Fiyat eşiğine göre stratejinin ITCH callback'lerini açıp kapatması. | [tavan](../20-stratejiler/tavan.md#hotcold-tiering-performans) |
| **Hot path** | ITCH alımı → strateji kararı → OUCH gönderimi (HFT, handoff sonrası). | [sistem haritası](sistem-haritasi.md#performans-prensipleri-tüm-c-kodu-için) |
| **Toplu emirler** | Sabah / açılış / akşam / YİP emirleri (`OrderType`); order-service gönderir. | [order-service](../10-servisler/order-service/toplu-emirler.md) |
| **Son atış** | Seans açılmadan giden sabah emri `-110023` ile reddedildikçe, kabul alınana kadar (en çok 900 ms) yeniden gönderme; yalnız `repeatLastShot: true` iken. Amaç kuyruk önceliği. | [order-service](../10-servisler/order-service/toplu-emirler.md) |
| **Paket** | Arbitraj / Fon Takibi'nde açılan bir pozisyon kaydı (DB'de). | [arbitraj](../20-stratejiler/arbitraj.md) |

## Uygulama adları (eş anlamlılar)

| Ad | Aynı şey |
|----|----------|
| HFT | HftSrvProd, MAHft (container) |
| AlgoProd | AlgorithmicTrading, algotrading, `algo_prod`, MAAlgoProd |
| trade-data-app | MADatabaseService, DatabaseService, data app |
| order-service | PiramitOrderService (binary), MAOrderService (container), `orderserv` |
| Yeni GUI / eski GUI | mtrader-trade-ui `development` / `main` |
