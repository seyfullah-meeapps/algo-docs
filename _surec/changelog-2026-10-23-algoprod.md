---
kapsam: 23 Ekim AlgoProd derinleştirme oturumunun değişiklik arşivi
dogrulama: 2026-10-26
durum: taslak
---

## 2026-10-23 — AlgoProd derinleştirme (madde 11)

Kaynak: AlgorithmicTrading `development` `0dc32a7`, `master` `aa150ee` (prod; 31 commit geride, 12 master-only commit), `add-order-sdk` `7d7f705`. Karşılaştırma için HftSrvProd `4275ccc`, order-service `b86c0cf`, trade-data-app `1cca9a8`, ouch-sdk `0c3589e`, mtrader-trade-ui `b0474c3` / `main` `6715182`.

- `bilgi-tabani/10-servisler/algorithmic-trading/` alt dosyalara bölündü:
  - `uygulama-ve-threadler.md`
  - `emir-yolu.md`
  - `grpc-ve-veri.md`
  - README artık indeks ve "önce bil" özeti.
- `bilgi-tabani/20-stratejiler/arbitraj.md`, `vwap.md`, `fon-takibi.md` koda karşı yeniden doğrulandı ve genişletildi. master farkları işaretlendi.
- **Eski README'de yanlış çıkanlar:**
  - Gün sonu `EndOfMessages` kapanışı ölü kod.
  - "Yeni emir 10 sn içinde dönmezse strateji durur" yanlış: yeni emirde bekleme yok.
  - "Bütün emirler `send`" yanlış: iptal ve replace çoğu yerde takibi atlıyor.
  - `Channel_Enum` her stratejide okunmuyor.
  - Stratejilerin olay kuyrukları TBB değil, moodycamel.
  - Açılışta `SettingsManager` ve gRPC'nin restore'dan önce açılması eksikti.
  - `UpdateArbitragePackage` hiç çağrılmıyor.
  - `FetchAkd` yalnız kullanılmayan stratejide.
- **Strateji dosyalarında yanlış çıkanlar:**
  - **Arbitraj:**
    - "Aktif stop → piyasa emri" yanlış: DAY limit gidiyor.
    - `Passive_Barrier` okunmuyor.
    - Paket tutarlılık kontrolü yalnız development'ta var.
  - **VWAP:** AKD filtresi pratikte kapalı; Overall işlevsiz.
  - **Fon Takibi:**
    - `Byf_Start/Stop_Time` kullanılmıyor.
    - Eşlenemeyen sembolde strateji durmuyor.
    - Lot eşiği BIST minimum birimi değil, sepet değeri / fon fiyatı.
- **Diğer dosyalarda:**
  - `log-imzalari` § 5: AlgoProd gün sonunda kendiliğinden kapanmaz.
  - `algorithmic-trading/config`: timeout satırı düzeltildi.
  - `trade-data-app/entegrasyonlar`: `FetchAkd` VWAP'ta yok.
  - `trade-data-app/veri-akisi`: AlgoProd health sunuyor.
  - `mtrader-trade-ui/backend-sozlesmesi`: `subscribeToOrderbook` AlgoProd'da boş.
  - `sozluk`: VWAP PTRM durması düzeltildi.
  - Katalog: `TradeByVolumeOverall` işlevsiz.
- **Yeni konular K-194 – K-207** (ACIK-KONULAR § AlgorithmicTrading). Kodla doğrulananlar:
  - **K-194, prod:** Fon Takibi lot düzeltmesi (2025-08) master'da yok.
  - **K-195, prod:** Arbitraj faiz `/100` düzeltmesi master'da yok.
  - **K-196:** Kanal 0'lı emir yanıtsız düşüyor.
  - **K-200:** Gün sonu kapanışı ölü kod.
  - **K-204:** `SubscribeToOrderbook` `return`'süz.
  - **K-206:** AKD kurum listesi hiç doldurulmuyor.
