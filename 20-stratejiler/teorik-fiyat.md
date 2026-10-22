---
kapsam: Teorik Fiyat (TheoreticalPrice, StrategyType 8) — müzayede (emir toplama) emirlerinin denge fiyatına göre iptali veya ters emirle kapatılması
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-22
durum: taslak
---

# Teorik Fiyat (`TheoreticalPrice`, 8)

Müzayede seanslarında (açılış/kapanış emir toplama) operatörün girdiği emirleri **denge (teorik) fiyatına** göre korur. Kendi başına emir üretmez. Operatör "teorik emir" girer, strateji o emri izler.

Kod: `src/Strategy/HftTheoreticalPrice.{h,cpp}`, `src/Commands/TheoreticalPriceCommand.*` (ayar alanı yok), `src/Commands/TheoreticalPriceOrderCommand.*`, `src/GUI/GUIManager.cpp` `handleTheoreticalOrder`.

## Akış

1. **Emir girişi:** Operatör GUI'den **teorik emir** girer: `ORDER_EVENT_TYPE = TheoreticalOrder` ve `Expected_Price` (beklenen fiyat, raw). Emir tipi `TheoreticalOrder` ile gönderilir. Strateji yoksa önce oluşturulur.
   - Emir **FIX kanalıyla** girilirse order-service üzerinden gider; MAOrderSDK yolu yalnızca OUCH içindir.
2. **İzleme:** Strateji başlatılınca dayanağın ITCH **denge fiyatı güncellemelerine** (`EquilibriumPriceUpdate`) abone olur ve son denge fiyatını tutar.
   - Her denge güncellemesinde saat yeniden hesaplanır: `hour = (ts / 1e9 / 3600) % 24`, `hour <= 12` ise "sabah emir toplama", değilse "akşam emir toplama" (`nightEmirToplama`). `ts`, olayın `packetTs`'idir (kernel alım anı, epoch ns, `ItchSdkClient::onEquilibriumPriceUpdateCallback`). Yani sınır **UTC 13:00 = İstanbul 16:00**.
   - ⚠ `packetTs` Glimpse ve XLIO yolunda 0'dır ([itch-sdk](../10-servisler/itch-sdk/README.md)). 0 gelirse `hour = 0` olur ve akşam müzayedesi de "sabah" sayılır: emir iptal edilmez, **ters emir gönderilir**. ❓ doğrulanmadı: XLIO/mlx kullanan müşteri var mı (bugün yok, [kurulum-ve-dagitim](../40-operasyon/kurulum-ve-dagitim.md)).
3. **Değerlendirme:** Orderbook durumu **Eşleştirme**'ye geçtiğinde `evaluateTheoreticalOrders` çalışır. Her emir için:
   - Alış: `Expected_Price ≥ denge` → tut, değilse aksiyon al.
   - Satış: `Expected_Price ≤ denge` → tut, değilse aksiyon al.
4. **Aksiyon:**
   - **Akşam:** emir **iptal** edilir.
   - **Sabah:** aynı miktar ve fiyattan **ters yönde** DAY emir gönderilir. Tip `TheoreticalOrder`, `REGULAR_ORDER_STANDART`.

## Bilinen durumlar

- `executeOrder` yalnız log basar (K-04). `updatePosition`, kalan miktarın düşülmesi ve tamamen dolan emrin `deleteBaseOrder` ile silinmesi yorum satırındadır. Kod yorumla birlikte `c819f28` (2025-12-01, "for evren2") commit'inde geldi; nedeni yazılı değil. Sonuçları:
  - Strateji pozisyonu dolumlarla değişmez.
  - Dolan emir `orderMap`'te kalır. Sonraki her **Eşleştirme** geçişinde yeniden değerlendirilir ve şunlardan biri olur:
    - Akşam modunda: dolmuş token için iptal gönderilir. Zararsız; ret döner.
    - Sabah modunda: dolmuş emir için **ters yönde emir** gönderilir.
  - Değerlendirmede kullanılan miktar `sdkOrderAccepted.getQuantity()`'dir. Kısmi dolumdan sonra da ilk miktardır.
  - ❓ doğrulanmadı: aynı gün sabah modunda ikinci bir Eşleştirme geçişi olup olmadığı. Örneğin devre kesici sonrası tek fiyat ya da YİP'in günde 5 tek fiyat süreci ([borsa-kurallari](../00-genel/borsa-kurallari.md#seanslar)). Olursa risk gerçek.
- `updateOrder` replace sonrası `orderMap`'i güncellemiyor; yalnızca log basıyor.
- Ayar alanı yok: `TheoreticalPriceCommand` yalnızca ortak alanları taşır.

## UI

- Yeni GUI route `theoretical-price`. Ayar modalı yok.
- Tracker denge fiyatını trade-data-app `/ws/v1/equilibrium/start` feed'inden gösterir. Bu feed subscribe olunca snapshot göndermez; satır borsa denge güncellemesi yayınlayana kadar (yalnızca müzayedelerde) boş kalır.

Müzayede ve denge fiyatı kavramları: `00-genel/borsa-kurallari.md`.
