---
kapsam: Uçtan uca akış kataloğu — hangi senaryonun hangi dosyada olduğu, ortak sınırlar ve kaynak sürümler
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: order-service
    branch: development
    commit: b86c0cf
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-23
durum: taslak
---

# Uçtan uca akışlar

Akış dosyaları servisler arasındaki sırayı, sınırları ve hata yollarını bağlar. Strateji mantığı `20-stratejiler/`, servis iç yapısı `10-servisler/`, operasyon adımları `40-operasyon/` altındaki belgelerde kalır.

| Soru / senaryo | Dosya |
|----------------|-------|
| ITCH paketi HFT kararına ve BIST emrine nasıl dönüşür? Thread, kuyruk, gate ve ölçüm noktaları nerede? | [Hot path](hot-path.md) |
| Accepted/Executed/Rejected/Cancel/Replace stratejiye ve GUI'ye nasıl döner? | [Emir dönüşü](emir-donusu.md) |
| GUI'den başlat/durdur/ayar güncellemesi, snapshot ve restart sonrası durum nasıl işler? | [Strateji başlatma](strateji-baslatma.md) |
| Manuel emir hangi motora gider; Serbest, iptal, replace ve fiyat ölçeği nasıl ayrılır? | [Manuel emir](manuel-emir.md) |
| AlgoProd strateji emri, userbook dönüşü, arbitraj hedge'i ve paket kalıcılığı nasıl işler? | [AlgoProd emri](algoprod-emri.md) |
| Sabah/toplu emir, OUCH handoff, replay gate, açılış ve akşam akışının zaman çizelgesi nedir? | [Sabah emri ve handoff](sabah-emri-ve-handoff.md) |
| ITCH/OUCH/MARpc/gRPC/WS kopunca ve servis restart edilince ne olur? | [Kopma ve kurtarma](kopma-ve-kurtarma.md) |

## Okuma sınırları

- Referans `development`; prod branch farkları ilgili akışta commit ile belirtilir. Canlı binary ve müşteri sunucusu bu oturumda incelenmedi.
- REST başarı yanıtı, BIST kabulü veya hedge dolumu anlamına gelmez. Dönüş olayı ayrı izlenir.
- HFT doğrudan SDK yolu ile order-service yedek yolu ayrıdır; AlgoProd referans sürümde yalnız order-service kullanır.
- Saatler örnek/config değerleridir; sabit borsa kuralı veya bütün müşteriler için ortak handoff saati sayılmaz.
- Kopma/restart kurtarma sıraları koddan çıkarımdır; canlıda uygulanmış ve sınanmış prosedür olarak sunulmaz. Ayrıntı [kopma ve kurtarma](kopma-ve-kurtarma.md)'dadır.
- Bütün dosyalar kullanıcı incelemesini bekleyen `taslak` durumundadır.
