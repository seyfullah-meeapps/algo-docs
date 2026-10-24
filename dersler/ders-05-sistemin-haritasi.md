---
kapsam: Servis/SDK ayrımı, üç emir yolu, handoff ve PM için arıza sınırlarını okuma
dogrulama: 2026-10-24
durum: taslak
---

# Ders 05 — Sistemin haritası

Amaç: bir problemi “backend sorunu” diye bırakmadan hangi katmanda kanıt arayacağımızı seçmek. Eski dersin sekiz bileşenli haritası güncel bilgi tabanına göre genişletildi. Teknik ayrıntının tek kaynağı [sistem haritasıdır](../00-genel/sistem-haritasi.md); burada öğrenme özeti var.

## Program ile kütüphane

| Bileşen | Tür | Öğrenirken akılda kalacak görevi |
|---|---|---|
| mtrader-trade-ui | Arayüz | Kullanıcı komutları ve gelen olayları gösterir |
| trade-data-app | Go servisi | DB, REST/WS gateway, servisler arası veri/komut aracılığı |
| HftSrvProd | C++ motor | Classic, Tavan, Taban, Teorik ve varant stratejileri |
| AlgorithmicTrading / AlgoProd | C++ motor | Arbitraj, VWAP ve Fon Takibi |
| order-service | C++ gateway | Toplu emirler, AlgoProd emir yolu, risk ve oturumlar |
| itch-sdk | Kütüphane | Piyasa verisi, defter, snapshot ve gap kurtarma |
| MAOrderSDK | Kütüphane | BIST emir bağlantısı ve olayları |
| ouch-sdk + network-sdk | Kütüphaneler | Uygulamanın gateway ile MARpc iletişimi |
| Admin paneli | Arayüz | Hesap/kullanıcı ve ilgili ayarların yönetimi |

SDK tek başına çalışan servis değildir. `ouch-sdk` adından hareketle BIST'e doğrudan bağlanıyor sanma; gateway'e bağlanır. Performans, kurulum ve bağımsız yardımcı araçlar ana teknik haritada ayrıca bulunur.

## Üç emir yolu

```text
HFT, handoff sonrası: motor → MAOrderSDK → BIST
HFT, handoff öncesi:  motor → ouch-sdk → order-service → BIST
AlgoProd referansı:   motor → ouch-sdk → order-service → BIST

Toplu Emirler: UI → trade-data-app → order-service → zamanlanmış gönderim
```

Handoff, sabah emirleri sonrasında ilgili OUCH kullanıcılarının gateway'den HFT'ye devridir. Bağlantıyı açmak, replay ve stratejiye izin verilmesi ayrı aşamalardır. “HFT asla gateway'e uğramaz” ifadesi bu nedenle eksiktir. AlgoProd'un doğrudan SDK geçişi ayrı feature çalışmasıdır; referans sürümün davranışı gibi anlatılmaz.

## Veri ile kontrol yolu

UI, hub'a REST/WS ile bağlanır. Hub motorlara gRPC komutları gönderir, olayları alır. UI defterini hub'ın kendi ITCH beslemesi üretir; HFT'nin strateji verisi kendi ITCH yolundadır. Emir defteri, emir olayları ve strateji durumu farklı akışlardır.

Açılışın öğrenme sırası: hub/veri → order-service → motorlar → UI. Bu sadece süreçlerin çalışması değildir; snapshot, login, bağlantı, handoff/replay ve gerekli verilerin hazır olması kontrol edilir. Hub'da GUI bağlantılarının başlaması da başarılı DataService login'iyle ilişkilidir. Gerçek kontrol adımları [operasyon belgelerindedir](../40-operasyon/README.md).

## PM için belirtiyi bölmek

| Bildirim | İlk ayrım |
|---|---|
| “Emir gitmedi” | Komut ulaştı mı, tetik oluştu mu, motor emir üretti mi, yerel ret mi geldi? |
| “Emir ekranda yok” | Borsadan dönüş var mı; hub stream/WS ve UI aboneliği ne durumda? |
| “Arbitraj yavaş” | HFT doğrudan yoluna göre değerlendirmek yerine AlgoProd + gateway yolu ölçülmeli |
| “Defter güncel ama strateji bekliyor” | UI ve motor feed'i, çalışma state'i, gate ve ayarlar ayrı kontrol edilmeli |
| “Hub gitti, motor devam etti” | Yerleşmiş hızlı yol ile yeni komut/gözlem/kayıt bağımlılıkları ayrılmalı |

Hot path düşük gecikmeye duyarlı ITCH→karar→emir yoludur. Kontrol ve bildirim yollarının yavaşlığı da önemlidir; “hub gecikirse yalnız ekran etkilenir” diye kesin genelleme yapılmaz. Yeni komut, veri hazırlığı ve gözlenebilirlik de etkilenebilir.

## Alıştırma

Bir “Arbitraj emri reddedildi” bildirimi için sırayla UI payload'ı, hub yönlendirmesi, AlgoProd kararı, gateway risk sonucu ve borsa dönüşü istenir. Bunlardan hangisinin eksik olduğu problemi henüz çözmez ama araştırma sınırını daraltır. Gerçek kişiye görev atamadan önce bu sınır ve kanıt yazılır.

Kaynaklar: [emir yolları](../00-genel/sistem-haritasi.md), [sabah/handoff](../30-akislar/sabah-emri-ve-handoff.md), [AlgoProd emri](../30-akislar/algoprod-emri.md), [kopma ve kurtarma](../30-akislar/kopma-ve-kurtarma.md).

## Oturum kaydı

Eski kayıtta sıradaki konu UI gezisiydi. Yeni rotada bunun yerine UI bilgisini backend'e bağlayan Ders 06 planlandı. Henüz işlenmedi.
