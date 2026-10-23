---
kapsam: Çalışma oturumlarının devamlılığı — alınan kararlar, mevcut durum, sıradaki işler
dogrulama: 2026-10-23
durum: taslak
---

# Oturum notları

Yeni oturuma başlayan agent **önce bunu okur**. Her oturumda karar alındıkça ve iş bittikçe güncellenir; oturum bitmeden "Şu an" ve "Sıradaki" bölümleri mutlaka güncel bırakılır.
Doküman değişikliklerinin ayrıntısı `CHANGELOG.md`'de, açık sorunlar `ACIK-KONULAR.md`'de; burada tekrarlanmaz.

## Şu an (2026-10-23)

- Bütün dosyalar `taslak`; kullanıcı gözden geçirmesi bekleniyor. **Planlanan derinleştirme maddeleri 1–9 ve 11–13 tamamlandı.**
- Madde 12: yedi akış + README indeks, K-208–K-220; `1c5a5d9` main'e push edildi.
- Madde 13: admin README indeks + üç alt dosya, K-221–K-228; kaynak kod ve development/master sözleşme farkları kontrol edildi.
- Madde 10 teknik hazırlığı: tüm repo yapısal taraması ve özet çelişkilerinin temizliği tamamlandı. `_surec/kontrol.py` bağlantı/frontmatter/manifest/kaynak-ref kontrolü yapar; içerik onayı vermez. İnceleme sırası `_surec/inceleme-durumu.md` içinde.
- Kaynak kontrolü `C:\Users\Seyf\algo-workspace` snapshot'larında yapıldı. Fetch, browser/build/deploy veya canlı kurtarma denemesi yapılmadı; uygulama kaynakları değişmedi.
- Ekli konuşma doküman commit'lerine dahil edilmedi. Remote mevcut `seyfullah-meeapps/algo-docs`. **Admin belgeleri yerel main üzerinde commit'lendi; push otomatik onay incelemesince hedef sahipliği/gönderim yetkisi yeterince doğrulanmadığı için reddedildi. Tekrar gönderim için kullanıcıdan bu hedefe açık onay bekleniyor.** Madde 12 daha önce push edilmişti.

## Sıradaki

**Sıradaki: kullanıcı içerik incelemesi (madde 10); teknik hazırlık tamamlandı.** İncelenen belgeler onaylandıkça `durum: dogrulandi` yapılır. Planlanan derinleştirme bitti; `ACIK-KONULAR.md` bug?/iş konuları ayrı sonraki çalışma olarak ele alınır, bu oturumda kod düzeltmesi yapılmadı.

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
12. ~~`30-akislar/` yeniden doğrulama/genişletme~~ ✅ 2026-10-23
13. ~~Admin paneli (`mtrader-frontend-apps`) derinleştirme~~ ✅ 2026-10-23

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

- **2026-10-23 (Codex genel kontrol):** 84 Markdown belgesi ve yerel bağlantılar tarandı; manifest/frontmatter kaynakları 15 klonda 23 farklı commit nesnesine çözüldü. Gate/watchdog, handoff saati ve thread güvenliği özetleri düzeltildi; kontrol aracı ve inceleme sırası eklendi. Durum etiketleri taslak kaldı. Önceki push engeli nedeniyle remote'a tekrar gönderim denenmedi.


- **2026-10-23 (Codex admin):** Madde 13 tamamlandı; üç alt belge ve README indeks, K-221–K-228. Panel main ↔ backend development/master alan farkları belgelendi. Sıradaki kullanıcı taslak incelemesi ve ayrı kod sorunu çalışması.


- **2026-10-23 (Codex devam):** Transkript ve çalışma ağacı karşılaştırıldı. Madde 12 tamamlandı; yedi akış, README indeks ve çapraz düzeltmeler, K-208–K-220. Kritik yollar kaynak kodla kontrol edildi; canlı kurtarma denenmedi. Sıradaki madde 13.


- **2026-10-23 (6. oturum, devam):** Kullanım limitinden sonra devam. AlgoProd (madde 11) derinleştirildi; K-194–K-207. master'da olmayan iki strateji düzeltmesi (K-194, K-195) prod'u etkiliyor.
- **2026-10-22 (3. oturum):** Kullanıcının `dogrulama-2026-10-22` branch'i main'e alındı (borsa kuralları, sözlük, ❓ temizliği — bkz. CHANGELOG). `ACIK-KONULAR.md` ve bu dosya açıldı. Push kuralı kondu; transkript silindi. Öncelik: doküman tamamlama (boşluk analizi). trade-data-app ve HftSrvProd derinleştirildi; HftSrvProd sonrası kullanıcı isteğiyle duruldu.
- **2026-10-22 (5. oturum, bulut):** Kaynak repolar salt okunur bağlandı. itch-sdk derinleştirildi (3 alt dosya, K-126–K-148); K-06 kapandı, K-01 teşhisi düzeltildi. ouch-sdk/network-sdk derinleştirildi (K-149–K-162); K-07 kapandı. mtrader-trade-ui derinleştirildi (K-163–K-178).
- **2026-10-22 (6. oturum):** Doğrulamalar (madde 9): borsa kuralları resmi prosedürden, K-10–K-12 kapandı, K-04 netleşti (K-192, K-193).
- **2026-10-22 (6. oturum):** Operasyon (madde 8) derinleştirildi: kurulum, config indeksi + AlgoProd config, log imzaları, sabah kontrolleri (K-179–K-191); K-05, K-09, K-175 kapandı.
- **2026-10-22 (4. oturum):** Önceki transkriptten devam; order-service (5 alt dosya, K-69–K-99) ve MAOrderSDK (4 alt dosya, K-100–K-125) derinleştirildi.
- **2026-10-22 (2. oturum, transkript dışı):** `dogrulama-2026-10-22` branch'inde ❓'ler koddan kapatıldı, `borsa-kurallari.md` ve `sozluk.md` yazıldı.
- **2026-10-22 (1. oturum):** Yapı kuruldu; sistem haritası, 9 strateji, 13 servis, operasyon ve akışlar taslak yazıldı. Kullanım limitinde kesildi.
