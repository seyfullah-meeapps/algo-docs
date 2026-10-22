---
kapsam: Çalışma oturumlarının devamlılığı — alınan kararlar, mevcut durum, sıradaki işler
dogrulama: 2026-10-22
durum: taslak
---

# Oturum notları

Yeni oturuma başlayan agent **önce bunu okur**. Her oturumda karar alındıkça ve iş bittikçe güncellenir; oturum bitmeden "Şu an" ve "Sıradaki" bölümleri mutlaka güncel bırakılır.
Doküman değişikliklerinin ayrıntısı `CHANGELOG.md`'de, açık sorunlar `ACIK-KONULAR.md`'de; burada tekrarlanmaz.

## Şu an (2026-10-22)

- Bütün dosyalar `taslak`; `bos` kalmadı. Kullanıcı gözden geçirmesi bekleniyor.
- `main` push edildi; `dogrulama-2026-10-22` branch'i silindi. Önceki sohbetin transkripti silindi (içeriği bu dosyaya aktarıldı).
- **Madde 1 (trade-data-app), 2 (HftSrvProd) ve 3 (order-service) bitti** (README indeks + alt dosyalar). **Sıradaki: madde 4 (MAOrderSDK).** Not: `maordersdk/README.md` yerel ret tablosunda 1005, 1006 ve 1 kodları eksik (hftsrvprod dosyasında var); tek yerde tamamlanmalı.
- Yöntem: konu başına paralel agent alt dosya yazar → çelişkileri koddan kontrol et → README'yi indekse çevir → ACIK-KONULAR'a tek satır ekle → CHANGELOG → push.
- Remote: `seyfullah-meeapps/algo-docs` (kişisel hesap). Planlanan `MeeApps/algo-docs` (org) değil; bilinçli mi, sorulmadı.

## Sıradaki

**Öncelik: dokümanı tamamlamak.** `ACIK-KONULAR.md`'deki bug?/iş konularına doküman bitince bakılacak.

Boşluk analizi (2026-10-22): yeni KB ~3.100 satır, eski `meeapps-ai` ~25.000 satır; yeni dosyalar özet seviyesinde. Eski içerik kopyalanmaz, güncel koda karşı yeniden yazılır. Eksik derinlik:

1. ~~trade-data-app~~ ✅ 2026-10-22
2. ~~HftSrvProd~~ ✅ 2026-10-22
3. ~~order-service~~ ✅ 2026-10-22
4. **MAOrderSDK:** bağlantı yaşam döngüsü, emir akışı, OUCH mesajları.
5. **itch-sdk:** mesaj kataloğu, alım yolu, Glimpse/Rewinder ayrıntısı, bilinen buglar (K-06).
6. **ouch-sdk / network-sdk:** public API, wire protokolü (K-07).
7. **mtrader-trade-ui:** ekranlar, REST/WS kullanımı, auth — eski ve yeni GUI ayrı ayrı.
8. **Operasyon:** config referansı, açılış log imzaları, sabah kontrolleri (K-09).
9. **Doğrulamalar:** K-04, K-05, K-10–K-12.
10. Kullanıcı taslakları gözden geçirdikçe `durum: dogrulandi`.

## Kararlar

Kullanıcıyla alınmış kararlar; aksi söylenmedikçe geçerli.

- **Amaç / okuyucu:** Bilgi tabanının okuyucusu AI agent; insana özet ve cevap üretmek için. Eski `MeeApps/meeapps-ai`'nin yerini alır, eski repoya dokunulmaz.
- **Dil:** Metin Türkçe, terimler ve kod isimleri İngilizce.
- **Referans branch:** `development`; akış `development → preprod → master`. Prod farkları `⚠ master'da yok` ile işaretlenir. İstisnalar `manifest.yaml`'da.
- **Kapsam dışı:** kişisel dersler, mate, Backoffice, Kripdome/DTA, Algo-GUI (en eski arayüz), `mtrader-new` (yeni GUI'nin kişisel öncül reposu, artık `mtrader-trade-ui` development'ta).
- **Eski ve yeni GUI:** İkisi de prod'da (parçalı geçiş); ikisi de belgelenir. Müşteri ↔ GUI tablosu `00-genel/branch-ve-ortamlar.md`'de.
- **Kullanılmayan stratejiler** (OrderChase, Warrant Tracker, AKD, MovingAverage): tek satırla "kullanılmıyor", ayrıntı yazılmaz.
- **Klonlar:** Okuma `C:\Users\Seyf\algo-workspace`'teki taze klonlardan; masaüstündeki klonlara dokunulmaz.
- **Gizli bilgi:** Placeholder ile maskelenir. Kaynak repolardaki açık şifreler sonra ele alınacak (K-15).
- **İnternet:** Genel tarama yok; yalnızca belirli şüpheli/tarihe bağlı borsa iddiaları tek tek kontrol edilir.
- **Güncelleme akışı:** Kullanıcı "güncelleyelim" der → agent commit'leri inceleyip özet çıkarır → kullanıcı onaylar → yazılır → `main`'e push.
- **VİOP partition konusu** (K-01, K-02): incelemesi ertelendi.
- **Push:** Her adımdan sonra `main` commit'lenip push edilir (onay beklenmez). İşi biten branch'ler silinebilir.
- **Öncelik:** Önce doküman tamamlanır; sorun düzeltme/inceleme (ACIK-KONULAR bug?/iş) sonra.
- **Servis klasör yapısı:** Servis tek README'ye sığmıyorsa konu başına alt dosya; README giriş + indeks, ayrıntı alt dosyada (tekrar yok).
- **Not tutma:** Açık sorunlar `ACIK-KONULAR.md`'de tek satır + link; oturum devamlılığı bu dosyada.

## Geçmiş

En yeni en üstte; oturum başına birkaç satır.

- **2026-10-22 (3. oturum):** Kullanıcının `dogrulama-2026-10-22` branch'i main'e alındı (borsa kuralları, sözlük, ❓ temizliği — bkz. CHANGELOG). `ACIK-KONULAR.md` ve bu dosya açıldı. Push kuralı kondu; transkript silindi. Öncelik: doküman tamamlama (boşluk analizi). trade-data-app ve HftSrvProd derinleştirildi; HftSrvProd sonrası kullanıcı isteğiyle duruldu.
- **2026-10-22 (4. oturum):** Önceki transkriptten devam; order-service derinleştirildi (5 alt dosya, K-69–K-99).
- **2026-10-22 (2. oturum, transkript dışı):** `dogrulama-2026-10-22` branch'inde ❓'ler koddan kapatıldı, `borsa-kurallari.md` ve `sozluk.md` yazıldı.
- **2026-10-22 (1. oturum):** Yapı kuruldu; sistem haritası, 9 strateji, 13 servis, operasyon ve akışlar taslak yazıldı. Kullanım limitinde kesildi.
