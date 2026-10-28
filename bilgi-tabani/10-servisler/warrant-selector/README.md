---
kapsam: Warrant-Selector — varant takas tarayıcısı; ne üretir, veri kaynakları, Varant Toplu ile ilişkisi
kaynak:
  - repo: Warrant-Selector
    branch: main
    commit: 582987f
dogrulama: 2026-10-22
durum: taslak
---

# Warrant-Selector (varant takas tarayıcısı)

Python aracı (CLI + Flask web arayüzü). Seçilen BIST30 dayanağı ve ihraççı için canlı varant listesini çıkarır, sonra her varantta **ihraççı dışındaki aracı kurumların takas payını** inceler. Bu pay eşiği aşan varantları CSV olarak verir: kod, tip (C/P), vade, kullanım fiyatı, dış kurumlar ve lotları, takas oranı, **kotasyon lotu**.

Stack servislerine bağlı değildir.

**Varant Toplu ile ilişkisi:** Bu aracın ürettiği CSV, [Varant Toplu](../../20-stratejiler/varant-toplu.md) stratejisine UI'dan yüklenen varant dosyasıdır (`/v1/parseWarrantFile`; kullanıcı beyanı, 2026-10-22). Çıktı alanları (varant tipi, kullanım fiyatı, vade, kotasyon lotu) `Warrant_List` alanlarına karşılık gelir.

## Kullanım

```text
python3 run.py HİSSE İHRAÇÇI TAKAS_EŞİĞİ MİNİMUM_VADE_GÜNÜ TİP [--source foreks|fintables]
```

- Takas eşiği doğrudan yüzde olarak verilir (`0.5` = %0,5); karşılaştırma `>` ile yapılır.
- Minimum vade günü katı alt sınırdır: `18` verilirse en az 19 gün kalanlar listelenir.
- Tip: `C` alım, `P` satım, `A` hepsi.
- İhraççılar: `AKYAT BNPPC GARAN GSINT INFOY ISMEN`.
- Çıktı: `out/<HİSSE>.csv`. Web arayüzünde birden çok hisse seçilirse ZIP olarak iner.

## Veri kaynakları

| Kaynak | Tanım / takas / kotasyon | Kimlik |
|--------|--------------------------|--------|
| **Foreks** (varsayılan) | Foreks feed-definition; MKK üye bazlı saklama; kotasyon lotu **09:59–10:02 açılış kaydından** okunur (`recorder.py`, ~9.800 varant, tek websocket, `QUOTE_STORE_DIR/YYYY-MM-DD.json`, 30 gün saklama) | Foreks token'ı **Backoffice**'ten alınır (hesap no + şifre, ortam değişkeni) |
| **Fintables** | Fintables API; kotasyon lotu canlı izlenir (60 sn × en fazla 3 tur, yalnız tekil `c=1` kotasyonlar) | `FINTABLES_TOKEN` |

Kimlik bilgileri yalnızca sunucunun ortam değişkenlerinde tutulur.

## Çalıştırma

- Docker Compose: `web` ve `recorder` servisleri `quotes` volume'unu paylaşır.
- Ubuntu servisi: Gunicorn ile çalışır (`deploy/warrant-selector.service`, `/etc/warrant-selector.env`).
- CI: `.github/workflows/docker.yml`.
