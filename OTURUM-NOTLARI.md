---
kapsam: Çalışma oturumlarının devamlılığı — alınan kararlar, mevcut durum, sıradaki işler
dogrulama: 2026-10-23
durum: taslak
---

# Oturum notları

Yeni oturuma başlayan agent **önce bunu okur**. Her oturumda karar alındıkça ve iş bittikçe güncellenir; oturum bitmeden "Şu an" ve "Sıradaki" bölümleri mutlaka güncel bırakılır.
Doküman değişikliklerinin ayrıntısı `CHANGELOG.md`'de, açık sorunlar `ACIK-KONULAR.md`'de; burada tekrarlanmaz.

## Şu an (2026-10-23)

- Strateji ikinci turu başladı: HFT yeniden fetch/development pull sonrası aynı uçlarda. Classic çekirdek/command dosyaları master ile aynı; K-236 stop enable alanı ve K-237 tek işlem yön kontrolü kaydedildi. Tavan/Taban branch farkları işaretlendi; K-235 Taban PTRM stop master'da yok. Bu alt tur bütün Tavan/Taban callback/timer sıralarını tamamlamaz.

- FIX şifre/config/ret alt turu tamamlandı; order-service ve SDK yeniden fetch/pull sonrası aynı uçlarda. K-233 (1409'suz Logon SDK/host ayrımı), K-234 (manuel adayda DB yazma hatasına rağmen arm) kaydedildi; crash-safe garanti ifadesi daraltıldı. K-120 ortak ret sınırı açık. Statik inceleme, şifre değişimi/canlı test yok.

- Legacy FIX fill/replay ve replace alt turu tamamlandı. order-service/SDK yeniden fetch/pull sonrası aynı uçlarda. K-121'in master'da da olduğu teyit edildi; K-232 legacy geçmiş fill'in yeniden pozisyon kuyruğuna girmesi adayı kaydedildi. Ayrıntı `10-servisler/order-service/fix-branch-karsilastirmasi.md`. Kaynak branch bulguları; prod sonucu/canlı test yok.

- Replay/combiner ve SDK development/main ana fark turu tamamlandı: yeni süreç adopt'u ile süreç içi reconnect ayrıldı; K-106 açıklaması düzeltildi, K-231 main hard-cap koşulu eklendi. SDK yeniden fetch/pull sonrası aynı uçlarda. Ayrıntı `10-servisler/maordersdk/branch-ve-replay-kontrolu.md`; statik inceleme, canlı test yok.

- HFT/SDK callback-token alt turu tamamlandı; altı ilgili repoda yeniden fetch/development pull yapıldı, uçlar aynı. K-56 daraltıldı; iki HFT branch'inde GUI kuyruğu/rekey sorunu adayı K-230 kaydedildi. Statik inceleme; canlı/zamanlamalı test yok.

- Planlanan derinleştirme maddeleri 1–9 ve 11–13 tamamlandı; belgeler kullanıcı incelemesini bekleyen taslak.
- **Yeni aşama: güncel development + master/main ile ikinci kod incelemesi.** Kullanıcı özellikle pull ile tazelik istedi. 15 kaynak klon temizdi; hepsinde origin fetch ve referans branch'te pull --ff-only başarılı. Referans uçları manifest baseline'larıyla aynı; kaynak uygulama dosyalarında değişiklik yok.
- Güncel uçlar, preprod/preproduction farkları ve aktif merge edilmemiş işler `_surec/kaynak-karsilastirmasi-2026-10-23.md` içinde. Yeni fetch/pull sonucu, önceki salt yerel yapısal taramadan ayrıdır.
- **İlk içerik turu:** order-service risk çekirdeği, SDK callback/limit noktaları ve HFT/AlgoProd risk ret eşlemesi kontrol edildi. Risk belgesindeki koşulsuz geçiş/koruma ifadeleri düzeltildi; K-74 netleştirildi, K-229 eklendi. Legacy FIX akışının tamamı henüz yeniden incelenmedi.
- Admin repeat_count/core_to_pin geliştirmesi ayrı feature branch'te, main'e merge edilmemiş; K-221 açık kaldı.
- Önceki yerel commit'ler `00a6c99` (admin) ve `3c86c9b` (genel kontrol) henüz push edilmedi. Mevcut remote `seyfullah-meeapps/algo-docs`; önceki otomatik onay reddi nedeniyle bu oturumda push denenmedi.

## Sıradaki

**Sıradaki: Tavan/Taban top-up, reClose ve callback/timer sıralarının kalan ayrıntıları.** Classic accept/fill/reject, stop ve tek işlem alt turu ile üç stratejinin branch farkları kaydedildi. Ardından diğer stratejiler, GUI/admin/operasyon izlenecek. FIX statik karşılaştırması tamamlandı; entegrasyon/gerçek exchange ve prod doğrulaması yapılmadı. Bütün bilgi tabanının ikinci doğrulaması henüz tamamlanmadı.

Kullanıcı içerik onayı geldikçe durum etiketi kapsamına göre güncellenir; genel devam talimatıyla topluca dogrulandi yapılmaz. Uygulama bug düzeltmesi/deploy bu doküman incelemesinin dışında kaldı.

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
- **Tazelik (2026-10-23 kullanıcı isteği):** İkinci inceleme development ile birlikte master/main güncel origin uçlarına karşı yapılır. Başlangıçta fetch, temiz referans çalışma branch'inde pull --ff-only; yerel değişiklikler ezilmez. Manifest istisnaları korunur.
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

- **2026-10-23 (güncel kaynak/risk):** 15 repoda fetch + referans pull yapıldı; baseline'lar aynı. Development/master/main ve preprod ref'leri kıyaslandı. Risk belgesi ilk içerik turu, K-74 düzeltmesi, K-229; admin feature ayrı kaydedildi. Sıradaki HFT/SDK emir yaşam döngüsü. Push engeli nedeniyle değişiklikler yerel tutuldu.


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
