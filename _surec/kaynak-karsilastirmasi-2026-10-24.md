---
kapsam: AlgoProd ikinci inceleme devamı — VWAP AKD/Overall/stop-loss ve Arbitraj paket/hedge takibi
kaynak:
  - repo: AlgorithmicTrading
    branch: development
    commit: 0dc32a7
  - repo: AlgorithmicTrading
    branch: master
    commit: aa150ee
dogrulama: 2026-10-24
durum: taslak
---

# 2026-10-24 kaynak kontrolü

Önceki günün karşılaştırması: [2026-10-23](kaynak-karsilastirmasi-2026-10-23.md). Bugün AlgorithmicTrading, GUI, HFT, admin, trade-data-app, Algo-Setup, algo-configs, MAOrderSDK ve order-service origin fetch ve temiz referans pull --ff-only yapıldı. Diğer altı repo bugün yenilenmedi. Üç development ucu ilerledi (aşağıda); tam doğrulama baseline'ları ilerletilmedi.

## İncelenen yollar

- [VWAP](../20-stratejiler/vwap.md#24-ekim-kontrolü-akdoverall-ve-stop-loss): TradeByVolume setCommand/AKD aboneliği, Overall alanları ve periyodik döngüsü, checkStopLoss/runStrategy/exitProperly. TradeByVolume dizininde master/development farkı yok. Mevcut K-206 sürüyor; stop sonrasında aynı fonksiyon turunun devamı ayrıca açıklandı.
- [Arbitraj](../20-stratejiler/arbitraj.md#24-ekim-kontrolü-paket-ve-hedge): arePackagesConsistent ve checkPassiveUndOrders. Development paket tutarlılığı başlangıç denetimi hedge başarısı değildir. K-205 eksik order kaydı sonrası iterator okuma ve ret izleme sınırları açık kaldı.

Yeni sorun numarası açılmadı; mevcut adaylar koddan kontrol edildi. Kaynak uygulama dosyaları değiştirilmedi; build, canlı emir, AKD servis bağlantısı ve thread testi yapılmadı. Belge durumları taslak kaldı. Bugünkü kapsam tüm stratejilerin/UI/operasyonun yeniden doğrulanması değildir.

## GUI devamı — payload/snapshot

GUI development b0474c3/main 6715182 ve HFT development 4275ccc/master 052dd96 referansları değişmedi. [Sözleşme kontrolü](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md#24-ekim--strateji-snapshotpayload-kontrolü) saat alias'ı, süre/delta birimleri, Taban Finish_With_Sell ve Classic stop-loss sınırını kaydeder. Yeni sorun numarası yok. Fetch, Teorik feature ucunu bfe65e2→26ce9b2 güncelledi; yeni uç bu alt turda incelenmedi, önceki feature incelemesi yalnız eski commit'e aittir.

## Admin devamı — alan sözleşmesi

Admin main db10c12 / backend development 1cca9a8 ve master 4a43e19 uçları değişmedi; admin feature 8ba2a67 ayrı kaldı. [24 Ekim alan kontrolü](../10-servisler/mtrader-frontend-apps/dagitim-ve-surum-farklari.md#24-ekim-kaynak-kontrolü) K-221 hesap listesi render sınırını ve K-224 parola update yolunu açıklar. Optional OUCH alanları update'te korunur; parola için bu kural yok. Yeni sorun numarası, browser/DB testi veya gerçek parola işlemi yok.

## Operasyon devamı — paket ve kaynak deltası

| Repo | Önce → güncel development | Diğer uç |
|------|--------------------------|----------|
| Algo-Setup | 2a3c5d5 → cade7d0 | preprod 959be34; main 2907757 aynı |
| MAOrderSDK | a788782 → c2b5060 | preprod a647c9e; main d5adc6f aynı |
| order-service | b86c0cf → 26e9a02 | preprod 5f23f24; master 298403b aynı |

Setup altı header/binary dosyası değişti; script/workflow değişmedi. SDK EnterOrderOptions.skip_brut_takas ekledi; order-service açılış yolunda true geçiyor. Tekrarsız satır dağıtımı development'a merge edildi; 23 Ekim'deki “ayrı feature” kaydı tarihsel kaldı. [Paket ayrıntısı](../40-operasyon/kurulum-ve-dagitim.md#24-ekim-paket-güncellemesi), [emir farkı](../10-servisler/order-service/toplu-emirler.md#24-ekim-güncel-davranış-farkı). K-92 tekrarsız kopya ifadesi daraltıldı; diğer kısımları açık. Tam binary/prod doğrulaması veya deploy yapılmadı. Eski baseline belgelerini bütünüyle yeni commit'e onaylanmış sayma.

## Sıradaki

GUI/admin/operasyon ikinci turu: önce strateji payload/snapshot ile backend alan eşleşmeleri ve güncel branch farkları. Önceki gün belirlenen K-240 eşleşen motor feature konusu açık; bu turda ele alınmadı.
