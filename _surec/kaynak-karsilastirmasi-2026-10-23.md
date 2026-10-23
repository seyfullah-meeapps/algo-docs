---
kapsam: Origin fetch/pull sonrası development ve master/main/preprod uçlarının doküman baseline'larıyla karşılaştırması; risk belgesi ilk teknik incelemesi ve henüz merge edilmemiş işler
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: itch-sdk
    branch: development
    commit: 35a3b5c
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: ouch-sdk
    branch: development
    commit: 0c3589e
  - repo: network-sdk
    branch: development
    commit: 3c1b42f
  - repo: performance-sdk
    branch: development
    commit: 6e47f20
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-frontend-apps
    branch: main
    commit: db10c12
  - repo: Algo-Setup
    branch: development
    commit: 2a3c5d5
  - repo: algo-configs
    branch: master
    commit: ab35dde
  - repo: Warrant-Selector
    branch: main
    commit: 582987f
  - repo: Itch-Replayer
    branch: main
    commit: c4b6029
  - repo: order-service
    branch: fix_sell_orders_per_account
    commit: f1c8ab0
  - repo: mtrader-frontend-apps
    branch: feat/ouch-repeat-count-core-to-pin
    commit: 8ba2a67
  - repo: mtrader-trade-ui
    branch: feat/new-gui-updates
    commit: e707fa8
  - repo: mtrader-trade-ui
    branch: feat/sweep-left-ask
    commit: d2c35c7
  - repo: mtrader-trade-ui
    branch: feat/toplu-varant-kaan
    commit: 16af0c0
dogrulama: 2026-10-23
durum: taslak
---

# Güncel kaynak karşılaştırması — 2026-10-23

Bu kayıt remote tazeliği ile teknik içerik doğrulamasını ayırır. 15 klonun tamamı `C:/Users/Seyf/algo-workspace` altındadır; günlük masaüstü klonlarına dokunulmadı.

## 1. Güncelleme işlemi

1. Her klonda branch, HEAD ve çalışma ağacı kontrol edildi: 15'i de temizdi.
2. Her repoda `git fetch origin` başarılı oldu; development yanında var olan master/main/preprod/preproduction ve feature ref'leri de güncellendi.
3. Manifestte referans olan temiz çalışma branch'inde `git pull --ff-only origin <branch>` çalıştırıldı; hepsi Already up to date döndü. Merge/reset veya uygulama kodu düzenlemesi yapılmadı.
4. Master/main karşılaştırmaları güncel `origin/master` / `origin/main` ref'lerinden yapıldı; çalışma kopyalarını branch'ler arasında taşımak gerekmedi. Master adı olmayan repoda hayali branch oluşturulmadı.
5. Partial clone'da eksik feature blob'ları ihtiyaç oldukça origin'den alındı. Doküman doğrulama SHA'ları topluca ilerletilmedi; yeni commit olmadığından manifest baseline'ları değişmedi.

## 2. Referans branch tazeliği

Son sütun dokümanın doğrulanan commit'i ile çekilen referans uç arasındaki farktır; development ile master/main'in birbirine eşit olduğu anlamına gelmez.

| Repo | Doküman referansı / güncel uç | development | master | main | Referansta yeni commit |
|------|------------------------------|-------------|--------|------|-----------------------|
| HftSrvProd | development `4275ccc` | `4275ccc` | `052dd96` | — | 0 |
| AlgorithmicTrading | development `0dc32a7` | `0dc32a7` | `aa150ee` | — | 0 |
| itch-sdk | development `35a3b5c` | `35a3b5c` | `00c51b1` | — | 0 |
| MAOrderSDK | development `a788782` | `a788782` | — | `d5adc6f` | 0 |
| order-service | development `b86c0cf` | `b86c0cf` | `298403b` | — | 0 |
| ouch-sdk | development `0c3589e` | `0c3589e` | `a8b9b02` | — | 0 |
| network-sdk | development `3c1b42f` | `3c1b42f` | `857f545` | — | 0 |
| performance-sdk | development `6e47f20` | `6e47f20` | `a46a361` | `69398d2` | 0 |
| trade-data-app | development `1cca9a8` | `1cca9a8` | `4a43e19` | — | 0 |
| mtrader-trade-ui | development `b0474c3` | `b0474c3` | — | `6715182` | 0 |
| mtrader-frontend-apps | main `db10c12` | `5951443` | — | `db10c12` | 0 |
| Algo-Setup | development `2a3c5d5` | `2a3c5d5` | — | `2907757` | 0 |
| algo-configs | master `ab35dde` | `ac65ac8` | `ab35dde` | — | 0 |
| Warrant-Selector | main `582987f` | — | — | `582987f` | 0 |
| Itch-Replayer | main `c4b6029` | — | — | `c4b6029` | 0 |

performance-sdk'da hem eski master hem main ref'i vardır; isimden canlı SDK binary sürümü çıkarılmadı. Admin/algo-configs eski development ref'leri tabloda özellikle gösterildi; bunlar manifest referansını değiştirme gerekçesi değildir.

## 3. Preprod karşılaştırması

Son sütun `doküman referansına özel / preprod'a özel` commit sayısıdır; merge commit'leri dahildir. Algo-Setup ortam branch'leri bağımsızdır, bu sayılar merge önerisi değildir.

| Repo | Çekilen test ortamı ref'i | Referansa özel / test ortamına özel |
|------|--------------------------|-----------------------------------|
| HftSrvProd | preprod `1d12633` | 0 / 1 |
| AlgorithmicTrading | preprod `b776d49` | 8 / 2 |
| MAOrderSDK | preprod `d2e750f` | 0 / 1 |
| order-service | preprod `f8f0789` | 0 / 6 |
| ouch-sdk | preprod `53e91bf` | 0 / 2 |
| network-sdk | preprod `7d67c8b` | 0 / 6 |
| performance-sdk | preprod `f75a93b` | 2 / 1 |
| trade-data-app | preproduction `6e33364` | 3 / 1 |
| mtrader-trade-ui | preprod `eff3d37` | 15 / 8 |
| Algo-Setup | preprod `346306a` | 187 / 256 |

## 4. Development ile master farkı yeni commit farkından ayrıdır

| Repo | Development'a özel / master'a özel | Bu incelemede anlamı |
|------|-----------------------------------|---------------------|
| HftSrvProd | 61 / 0 | Master development'ın gerisinde; development davranışı prod'a doğrudan taşınmaz |
| AlgorithmicTrading | 31 / 12 | Dallar ayrışmış; yalnız geride/ileride ilişkisi yok |
| order-service | 52 / 16 | Development SDK adapter, master legacy manager yapısı; risk callback yolu ayrıca ayrılır |
| trade-data-app | 60 / 9 | Master'a özel toplam 9 commit'in 6'sı merge dışı; önceki manifestteki 6 sayısı bu ayrım belirtilmeden yazılmıştı |

Bunlar fetch sonrasında hesaplandı; önceki doküman baseline'ından sonra yeni commit geldiğini söylemez. Branch ucu canlı sunucudaki binary/config sürümünün kanıtı değildir.

## 5. İlk teknik tur — emir/risk

İncelenen kaynaklar: order-service RiskManager/RiskInfo, OrderDispatcher, MAOSdkManager ve master OUCH callback'leri; MAOrderSDK enterOrder limit bloğu; trade-data-app risk RPC/proto ve GuiSendOrders; HFT/AlgoProd ret callback eşlemesi.

- [Risk belgesi](../10-servisler/order-service/risk.md) development ve master çekirdeğiyle karşılaştırıldı. Stream kopması kontrolü bütünüyle bypass etmez; eski limitlerle devam eder. K-74 ifadesi buna göre düzeltildi.
- SDK hard cap/brüt takas/bölme kontrolleri her emre koşulsuz uygulanmaz; mevcut K-104 sınırı risk belgesine taşındı. Yeni K-229, price=0 market alışında RiskManager'ın tahmini tutar hesabı yapmaması ile bu SDK sınırının birlikte etkisini kaydeder.
- Token'sız risk reddinin HFT ve AlgoProd'a eşlenmesi koddan açıklandı. ShortSell nakit kontrolünün her koşulda geçeceği iddiası daraltıldı.
- Ortak risk çekirdeğinde hesap yoksa geçirme, replace fark hesabı ve stream reconnect davranışı iki branch'te de mevcut. Development FIX replay apply_balance kuralı master'a genellenmedi; legacy FIX akışının tamamı henüz yeniden incelenmedi.

Bu tur bütün bilgi tabanının yeniden kodla doğrulanması değildir. Sonraki tur HFT/SDK emir yaşam döngüsü ve callback kimlik/sıra eşlemesi, ardından strateji kurallarıdır. Kullanıcı onayı ve canlı test olmadığı için belgeler taslak kalır.

## 6. Son iki haftada aktif, referansa merge edilmemiş branch'ler

2026-10-09 ve sonrası commit tarihine göre tarandı. Branch'in adı niyet hakkında ipucu verir; bütün içeriğinin doğru/çalışır olduğu veya prod'a çıkacağı anlamına gelmez.

| Repo | Branch | Uç | Commit tarihi |
|------|--------|----|---------------|
| AlgorithmicTrading | `add-order-sdk` | `7d7f705` | 2026-10-15 |
| order-service | `fix_sell_orders_per_account` | `f1c8ab0` | 2026-10-23 |
| trade-data-app | `ip_logging_hotfix_master` | `e3f2b14` | 2026-10-20 |
| trade-data-app | `fix_opening_order_level_count` | `80bac29` | 2026-10-20 |
| trade-data-app | `add-algo-order-stream` | `94545b2` | 2026-10-15 |
| trade-data-app | `feat/ouch-application-user` | `c2630c7` | 2026-10-12 |
| mtrader-trade-ui | `feat/toplu-varant-kaan` | `16af0c0` | 2026-10-23 |
| mtrader-trade-ui | `feat/sweep-left-ask` | `d2c35c7` | 2026-10-23 |
| mtrader-trade-ui | `feat/new-gui-updates` | `e707fa8` | 2026-10-22 |
| mtrader-frontend-apps | `feat/ouch-repeat-count-core-to-pin` | `8ba2a67` | 2026-10-12 |

Somut incelenenler:

- order-service `fix_sell_orders_per_account` (`f1c8ab0`): OrderManager non-repeatable satırları hesabın kullanıcıları arasında dağıtıyor; hesabın her kullanıcısına aynı satırın gitmesini değiştiriyor. Development'a merge edilmemiştir; güncel toplu emir belgesi bu dalın davranışına geçirilmedi.
- Admin `feat/ouch-repeat-count-core-to-pin` (`8ba2a67`): tiplerde repeat_count/core_to_pin ve application_user_id var, is_dedicated yok. Bu main desteği değildir; K-221 kapatılmadı. Backend tarafındaki feature eşleşmesi ayrıca incelenmelidir.
- GUI `feat/new-gui-updates` (`e707fa8`), `feat/sweep-left-ask` (`d2c35c7`) ve `feat/toplu-varant-kaan` (`16af0c0`) gelişmiş; development aynı kalmıştır. Kodun main/production davranışı gibi belgelenmediler. Sweep dalında varant toplu alanları değişiyor; tam strateji/wire incelemesi sonraki turda yapılmalı.
- AlgoProd `add-order-sdk` (`7d7f705`) hâlâ referansa merge edilmemiştir; doğrudan SDK yolunu development'ta var sayma.
