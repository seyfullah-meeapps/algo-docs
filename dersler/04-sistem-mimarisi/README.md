---
kapsam: Bizim sistemimiz konu dosyaları ve kapsamları
dogrulama: 2026-10-24
durum: taslak
---

# Bizim sistemimiz — bölüm indeksi

| Konu | Kapsam | Durum |
|---|---|---|
| [Repo ve bileşen haritası](01-repolar-ve-bilesenler.md) | Repo, uygulama/kütüphane ve görev; HFT, AlgoProd, hub, gateway, UI ve yardımcılar | Planlandı |
| [Container, süreç ve dağıtım haritası](02-container-ve-dagitim.md) | Compose/service/image/binary/config eşlemesi; container dışında çalışan süreçler; ortam kanıtı | Planlandı |
| [Bağlantılar ve protokoller](03-iletisim-semasi.md) | İstemci/sunucu; REST/WS/gRPC/MARpc/ITCH/OUCH/FIX okları ve port/config kaynağı | Planlandı |
| [Piyasa verisi ve itch-sdk](04-piyasa-verisi-yolu.md) | BIST, SDK, motor/hub ve UI; snapshot, partition, callback, kurtarma ve ayrı veri yolları | Planlandı |
| [Emir SDK’ları ve gateway](05-emir-sdk-ve-gateway.md) | MAOrderSDK, ouch-sdk, network-sdk, order-service; motor yönlendirmeleri ve risk sınırları | Planlandı |
| [Hub, veritabanı ve GUI](06-hub-veritabani-ve-gui.md) | trade-data-app, veri sahipliği, REST/WS, kimlik/yetki, komut ve olay dağıtımı | Planlandı |
| [Motorlar ve strateji durumu](07-motorlar-ve-strateji-durumu.md) | HFT/AlgoProd, strateji kimliği, ayarlar, command, snapshot, pozisyon ve start/stop | Planlandı |
| [Açılış, handoff ve replay](08-acilis-handoff-ve-replay.md) | Bağımlılık ve hazırlık; OUCH devri; doğrudan/yedek yol; replay gate ve restart | Planlandı |
| [Bir işlemin uçtan uca akışı](09-uctan-uca-islem.md) | UI başlat, hub, motor, piyasa tetiği, emir, callback ve ekran; ayrı sequence şemaları | Planlandı |
| [Kopma ve gözlem noktaları](10-kopma-ve-gozlem.md) | ITCH, OUCH, MARpc, gRPC ve WS kopmaları; belirtiden katmana; log/metric ve tekrar olaylar | Planlandı |
| [Ortam, config ve release](11-ortam-config-ve-release.md) | Development/preprod/prod, eski/yeni GUI; image/binary/config ve sürüm farkları | Planlandı |

[Ana indeks](../README.md)
