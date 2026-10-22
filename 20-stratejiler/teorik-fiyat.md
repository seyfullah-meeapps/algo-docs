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
   - Saat **UTC 12:00'den önceyse** (İstanbul 15:00) "sabah emir toplama", sonrası "akşam emir toplama" sayılır (`nightEmirToplama`).
3. **Değerlendirme:** Orderbook durumu **Eşleştirme**'ye geçtiğinde `evaluateTheoreticalOrders` çalışır. Her emir için:
   - Alış: `Expected_Price ≥ denge` → tut, değilse aksiyon al.
   - Satış: `Expected_Price ≤ denge` → tut, değilse aksiyon al.
4. **Aksiyon:**
   - **Akşam:** emir **iptal** edilir.
   - **Sabah:** aynı miktar ve fiyattan **ters yönde** DAY emir gönderilir. Tip `TheoreticalOrder`, `REGULAR_ORDER_STANDART`.

## Bilinen durumlar

- `executeOrder` pozisyonu güncellemiyor; ilgili kod yorum satırına alınmış. ❓ Kasıtlı mı, doğrulanmadı.
- `updateOrder` replace sonrası `orderMap`'i güncellemiyor; yalnızca log basıyor.
- Ayar alanı yok: `TheoreticalPriceCommand` yalnızca ortak alanları taşır.

## UI

- Yeni GUI route `theoretical-price`. Ayar modalı yok.
- Tracker denge fiyatını trade-data-app `/ws/v1/equilibrium/start` feed'inden gösterir. Bu feed subscribe olunca snapshot göndermez; satır borsa denge güncellemesi yayınlayana kadar (yalnızca müzayedelerde) boş kalır.

Müzayede ve denge fiyatı kavramları: `00-genel/borsa-kurallari.md`.
