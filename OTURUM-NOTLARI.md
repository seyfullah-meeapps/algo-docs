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
- Madde 1–7: trade-data-app, HftSrvProd, order-service, MAOrderSDK, itch-sdk, ouch-sdk/network-sdk, mtrader-trade-ui. **Madde 1–9 ve 11 bitti.** **Şu an madde 12 (`30-akislar/`) sürüyor:** akış başına dosya — `hot-path.md`, `emir-donusu.md` (agent A); `strateji-baslatma.md`, `manuel-emir.md`, `algoprod-emri.md` (agent B); `sabah-emri-ve-handoff.md`, `kopma-ve-kurtarma.md` (agent C). README indekse dönecek. Sonra 13 (admin paneli). Madde 10 kullanıcı incelemesine bağlı.
- Yöntem: konu başına paralel agent alt dosya yazar → çelişkileri koddan kontrol et → README'yi indekse çevir → ACIK-KONULAR'a tek satır ekle → CHANGELOG → push.
- Remote: `seyfullah-meeapps/algo-docs` (kişisel hesap). Planlanan `MeeApps/algo-docs` (org) değil; bilinçli mi, sorulmadı.

## Sıradaki

**Öncelik: dokümanı tamamlamak.** `ACIK-KONULAR.md`'deki bug?/iş konularına doküman bitince bakılacak.

Boşluk analizi (2026-10-22): yeni KB ~3.100 satır, eski `meeapps-ai` ~25.000 satır; yeni dosyalar özet seviyesinde. Eski içerik kopyalanmaz, güncel koda karşı yeniden yazılır. Eksik derinlik:

1. ~~trade-data-app~~ ✅ 2026-10-22
2. ~~HftSrvProd~~ ✅ 2026-10-22
3. ~~order-service~~ ✅ 2026-10-22
4. ~~MAOrderSDK~~ ✅ 2026-10-22
5. ~~itch-sdk~~ ✅ 2026-10-22
6. ~~ouch-sdk / network-sdk~~ ✅ 2026-10-22
7. ~~mtrader-trade-ui~~ ✅ 2026-10-22
8. ~~Operasyon~~ ✅ 2026-10-22
9. ~~Doğrulamalar~~ ✅ 2026-10-22 (K-04 kasıt sorusu açık)
10. Kullanıcı taslakları gözden geçirdikçe `durum: dogrulandi`.
11. ~~AlgoProd derinleştirme~~ ✅ 2026-10-23
12. **`30-akislar/`** güncel servis dokümanlarına göre yeniden doğrulama/genişletme.
13. **Admin paneli** (`mtrader-frontend-apps`) derinleştirme.

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

- **2026-10-23 (6. oturum, devam):** Kullanım limitinden sonra devam. AlgoProd (madde 11) derinleştirildi; K-194–K-207. master'da olmayan iki strateji düzeltmesi (K-194, K-195) prod'u etkiliyor.
- **2026-10-22 (3. oturum):** Kullanıcının `dogrulama-2026-10-22` branch'i main'e alındı (borsa kuralları, sözlük, ❓ temizliği — bkz. CHANGELOG). `ACIK-KONULAR.md` ve bu dosya açıldı. Push kuralı kondu; transkript silindi. Öncelik: doküman tamamlama (boşluk analizi). trade-data-app ve HftSrvProd derinleştirildi; HftSrvProd sonrası kullanıcı isteğiyle duruldu.
- **2026-10-22 (5. oturum, bulut):** Kaynak repolar salt okunur bağlandı. itch-sdk derinleştirildi (3 alt dosya, K-126–K-148); K-06 kapandı, K-01 teşhisi düzeltildi. ouch-sdk/network-sdk derinleştirildi (K-149–K-162); K-07 kapandı. mtrader-trade-ui derinleştirildi (K-163–K-178).
- **2026-10-22 (6. oturum):** Doğrulamalar (madde 9): borsa kuralları resmi prosedürden, K-10–K-12 kapandı, K-04 netleşti (K-192, K-193).
- **2026-10-22 (6. oturum):** Operasyon (madde 8) derinleştirildi: kurulum, config indeksi + AlgoProd config, log imzaları, sabah kontrolleri (K-179–K-191); K-05, K-09, K-175 kapandı.
- **2026-10-22 (4. oturum):** Önceki transkriptten devam; order-service (5 alt dosya, K-69–K-99) ve MAOrderSDK (4 alt dosya, K-100–K-125) derinleştirildi.
- **2026-10-22 (2. oturum, transkript dışı):** `dogrulama-2026-10-22` branch'inde ❓'ler koddan kapatıldı, `borsa-kurallari.md` ve `sozluk.md` yazıldı.
- **2026-10-22 (1. oturum):** Yapı kuruldu; sistem haritası, 9 strateji, 13 servis, operasyon ve akışlar taslak yazıldı. Kullanım limitinde kesildi.
