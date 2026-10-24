---
kapsam: Çalışma oturumlarının devamlılığı — alınan kararlar, mevcut durum, sıradaki işler
dogrulama: 2026-10-24
durum: taslak
---

# Oturum notları

Yeni oturuma başlayan agent **önce bunu okur**. Her oturumda karar alındıkça ve iş bittikçe güncellenir; oturum bitmeden "Şu an" ve "Sıradaki" bölümleri mutlaka güncel bırakılır.
Doküman değişikliklerinin ayrıntısı `CHANGELOG.md`'de, açık sorunlar `ACIK-KONULAR.md`'de; burada tekrarlanmaz.

## Şu an (2026-10-24)

**Rehber ana çalışma konusu.** Ana okuyucu kullanıcının kendisi; sonrasında görevi devralan/yeni katılan kişiler için şirket içi bilgi aktarım kaynağı olacak. Mantık ve davranış ana metinde, gerektiğinde kısa kod; derin ayrıntılar ayrı bölümde. Mevcut hatalar rehberde anlatılmayacak; teknik takip ayrı kalacak, düzeltme doğrulanınca rehber güncellemesi kapanışta kontrol edilecek. Düzelmemiş hedef davranış çalışıyormuş gibi yazılmaz. Kararlar `dersler/kararlar.md` içinde; yazıma başlamak için zorunlu açık tercih yok. Sıradaki içerik uygulamanın amacı. İçerik yazımına başlanmadı.

**Aktif kapsam: konu bazlı insan rehberinin indeksi.** Kullanıcı önceki ders düzeninden vazgeçip gelecekte yazılı dokümana dönüştürülebilecek bir rehber istedi. Yeni sıra ve kararlar `dersler/kararlar.md`, ayrıntılı indeks `dersler/README.md`, devam noktası `dersler/ilerleme.md` içinde. Altı bölüm ve 48 ayrı konu iskeleti oluşturuldu; anlatımlar henüz yazılmadı. Eski 11 dosya `dersler/arsiv/` altında tarihsel olarak korundu. Konu bazlı soru/yanıt kaydı, kaynak ve görsel kuralları `dersler/calisma-duzeni.md`, agent talimatları `dersler/AGENTS.md` içinde. Bu tur internet/kod araştırması veya uygulama testi yok.

Önceki push otomatik onay incelemesince reddedildi; kullanıcı henüz uzak depoya gönderim onayı vermedi. Bu tur push tekrar denenmez. Teknik incelemenin ilk aşama kapanışı aşağıdaki tarihsel kapsamıyla geçerlidir.

**İlk aşama tamamlandı. Aktif devam işi yok.** Kullanıcı dokümantasyonun ilk aşamasını kapatmamızı, sorunlara şimdilik odaklanmamamızı istedi. Planlanan yazım, derinleştirme, güncel development–master/main karşılaştırması ve kapanış tutarlılığı tamamlandı. Tek kapanış kaydı `_surec/ikinci-tur-sonuc-2026-10-24.md`; açık indeks korunur, otomatik takip kuyruğu değildir. Belgeler içerik onayı yerine geçmemesi için taslak kaldı.

## Tamamlanan teknik takip (tarihsel kayıt)

- K-240 SDK kaynağı bulundu: warrant-open-quote-log-pp e800b3d; extended callback HFT f20b5f2 ile eşleşiyor. Aynı adlı SDK hft_warrant_advanced dalında API yok. Ayrıntı `10-servisler/itch-sdk/quote-executed-feature.md`; kaynak zinciri tamam, artifact/header/library ve dağıtım açık. SDK fetch/pull sonrası development/master aynı. QuoteBuyer çıkarımı ve sıfır miktarlı geç bildirim belgelendi.

- K-240 GUI–motor kaynak eşleşmesi bulundu: GUI d2c35c7 ↔ HFT hft_warrant_advanced f20b5f2. Parser/miktar/snapshot ve maliyet kapanışı incelendi; yeni executed_ex callback ve quote alanları SDK bağımlılığı getiriyor. Ayrıntı `20-stratejiler/varant-toplu.md`; K-240 SDK/dağıtım kapsamıyla açık. Development/master değişmedi; build/canlı test yok.

- Teorik feature 26ce9b2 statik delta incelemesi tamamlandı. HFT fetch/pull sonrası development/master aynı, commit yalnız feature dalında; açılış bildirimi, own-state guard, sıfır denge ve reverse Expected_Price farkları `20-stratejiler/teorik-fiyat.md` içinde. K-04 değişmedi; runtime/build yok.

- K-241/K-242 development 4275ccc gövdeleriyle yerelde sınandı: beş senaryo beklendiği gibi. MSVC senkron ret yeniden kilidinde istisna; iki satış ACK'i sonrası son token'a toplam miktarla replace gözlendi. Kanıt `_surec/dogrulama-varant-2026-10-24.md`; adaylar açık, tam entegrasyon/canlı test veya uygulama düzeltmesi yok.

- K-233/K-234 handler düzeyinde yerelde yeniden üretildi: gerçek C++ gövdeleri, sahte DB/QuickFIX yüzeyi, MSVC; 5 senaryo geçti. Script `_surec/dogrula_sifre_akisi.py`, kanıt `_surec/dogrulama-sifre-akisi-2026-10-24.md`. SDK/order-service fetch/pull sonrası c2b5060/26e9a02 aynı. Canlı entegrasyon veya uygulama düzeltmesi yapılmadı.

- İlk teknik takip tamamlandı: K-243 geri çekildi. Preprod workflow'unda override var; başarılı run/job log'u hedef preprod gösteriyor. Kanıt `_surec/dogrulama-k243-2026-10-24.md`; development dosyası yanlış genellenmişti. K-243 numarası tekrar kullanılmaz (sonraki yeni numara 244).
- Bu oturum başında main origin/main ile eşitti; önceki commit'lerin push beklediği bilgisi artık güncel değil. Bu agent push yapmadı. Yeni doğrulama değişiklikleri ayrıca yerel commit'lenir.

### Kapanış anının durumu (teknik takip öncesi)

- Planlanan konu bazlı ikinci statik inceleme ve kapanış tutarlılık kontrolü tamamlandı. Sonuç/kapsam: `_surec/ikinci-tur-sonuc-2026-10-24.md`. Tüm kod satırları veya canlı sistem doğrulandı denmiyor; belgeler taslak.
- 23 Ekim 15 repo, 24 Ekim dokuz repo fetch/pull edildi. SDK c2b5060, order-service 26e9a02, Setup cade7d0 farkları işlendi; tam baseline'lar ilerletilmedi. Teorik feature 26ce9b2 yeniden incelenmedi, K-240 eşleşmesi açık.
- Son tutarlılık taramasında sabah akışı dağıtım özeti ve SDK API brüt-takas özeti güncellendi. Build/browser/CI run/canlı emir/DB/deploy testi yok; yerel commit'ler push engeli nedeniyle bekliyor.

## Önceki alt turlar (tarihsel ilerleme kaydı)

- CI/config kaynak alt turu tamamlandı: K-243 SDK preprod artifact push job'ının main hedefinde kalması adayı eklendi. Aktif SDK/service matrix regular/onload; Mlx koşullu adımları aktif build kanıtı değil. K-182 ini/toml farkı sürüyor. CI run/deploy/canlı sunucu incelenmedi.

- Operasyon ilk alt turunda gerçek delta geldi: Algo-Setup dev cade7d0, SDK dev c2b5060, order-service dev 26e9a02. Açılış için skip_brut_takas ve tekrarsız satır dağıtımı güncellendi; K-92 daraltıldı. Bugün toplam dokuz repo fetch/pull edildi. Baseline'lar topluca ilerletilmedi; kalan config/CI incelemesi sürüyor.

- Admin/backend alan alt turu tamamlandı: admin main ve TDA development fetch/pull, main/master ref'leri aynı. K-221 liste render sınırı ve K-224 password SQL yolu yeniden kontrol edildi; yeni sorun numarası yok. Bugün toplam beş kaynak repo güncellendi; canlı DB/browser testi yapılmadı.

- GUI/HFT payload-snapshot alt turu tamamlandı: iki repo yeniden fetch/pull, referans uçlar aynı. Saat alias'ı ve süre/delta dönüşümleri kontrol edildi; Classic stop kapatma farkı sürüyor. Bugün toplam üç repo güncellendi (AlgoProd+GUI+HFT). Teorik feature ucu 26ce9b2'ye ilerledi, yeni uç incelenmedi.

- AlgoProd kalan AKD/Overall/stop-loss ve paket/hedge statik alt turu tamamlandı. Bugün yalnız AlgorithmicTrading yeniden fetch/pull edildi; dev/master aynı. K-205/K-206 sürüyor, yeni sorun numarası yok. Bugünkü kanıt ve sınırlar `_surec/kaynak-karsilastirmasi-2026-10-24.md` içinde; önceki 15 repo kontrolü 23 Ekim tarihidir.

- AlgoProd ikinci turunun ilk alt turu tamamlandı: fetch/pull sonrası uçlar aynı. K-194 Q>L koşuluyla daraltıldı; K-195 faiz branch farkı tekrar görüldü. VWAP incelenen strateji/command kaynakları iki branch'te aynı. Fon sepet ret/completion ve Arbitraj başlatma/ret yolları kontrol edildi; prod binary/config sonucu çıkarılmadı.

- Varant (13)/Teorik Fiyat statik ikinci turu tamamlandı; HFT yeniden fetch/pull sonrası uçlar aynı. K-241 senkron ret/recursive olmayan mutex, K-242 tek satış token'ı/parçalı fill sınırı eklendi. Teorik ilk eşleşme feature bfe65e2 incelendi, referans davranışına geçirilmedi; K-04 devam ediyor.

- Süpürme UI/wire alt turu tamamlandı: HFT ve GUI fetch/pull sonrası referans uçlar aynı. Tavan `Should_Sweep` nihai payload'da pozitif Melt_Lot ile kapılanır; motor aynı kısıtı uygulamaz. Varant Toplu `Sweep_Left_Ask` ayrı GUI feature dalındadır; development motor desteği yok (K-240), eşleşen HFT feature doğrulanmadı.

- Varant Toplu development callback/trigger/reprice alt turu tamamlandı; HFT fetch/pull sonrası referans uç değişmedi, master'da sınıf yok. Her alış fill'ine koşulsuz satış ve her yarışta açığa düşmeme ifadeleri daraltıldı. K-239 boş-kuyruk next-check gecikme adayı kaydedildi. Yeni origin `theo-cancel-on-first-eslestirme` ref'i görüldü; içeriği henüz incelenmedi.

- Tavan/Taban top-up, reClose ve callback/timer statik alt turu tamamlandı. HFT yeniden fetch/pull sonrası aynı uçlarda. Önceki “Taban timer master'da yok” ifadesi yanlıştı; timer iki branch'te de mevcut, düzeltildi. K-238 çalışma saati filtresinin koruyucu olaylara da uygulanmasını kaydeder. TTL'nin callback'te kontrol edildiği ve Tavan restore / Taban lift farkı açıklandı.

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

**Rehber için:** İndeks değişiklikleri gelirse işle; içerik yazımına geçildiğinde `dersler/01-uygulama/01-ne-yapiyoruz.md` ile başla. Eski Ders 06 planı geçersiz. Önce `dersler/AGENTS.md`, kararlar, indeks, ilerleme ve çalışma düzenini oku. Konuşulan gerçek soruları ilgili konuya tarihli kaydet; yazılmışı okunmuş/onaylanmış sayma. Güncel borsa iddialarını içerik yazılırken resmi kaynaklardan doğrula. Açık bug araştırması bu kapsamla otomatik açılmadı.

**İlk aşama için sıradaki iş yok.** Yeni kullanıcı talebi gelmeden kaynak/feature/CI araştırmasına veya açık sorun doğrulamasına devam edilmez. Gelecekte doküman güncellemesi istenirse `_surec/guncelleme.md` uygulanır; sorun çalışması istenirse yalnız seçilen kapsam ele alınır. K-240 artifact/dağıtım, Teorik zamanlama, gerçek SDK/host entegrasyonu ve prod davranışı doğrulamaları bu aşamadan ertelendi; eksik doküman yazımı sayılmaz. K-233/K-234 düzeltilmedi, K-243 geri çekildi.

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

- **İlk aşama kapanışı (2026-10-24):** Doküman çalışması tamamlanır; sorunlara şimdilik odaklanılmaz. Sonraya bırakılan teknik doğrulamaları otomatik sıradaki iş olarak sürdürme. Genel kapanış talebi içeriklerin topluca `dogrulandi` yapılması anlamına gelmez.

- **Amaç / okuyucu:** Bilgi tabanının okuyucusu AI agent; insana özet ve cevap üretmek için. Eski `MeeApps/meeapps-ai`'nin yerini alır, eski repoya dokunulmaz.
- **Dil:** Metin Türkçe, terimler ve kod isimleri İngilizce.
- **Referans branch:** `development`; akış `development → preprod → master`. Prod farkları `⚠ master'da yok` ile işaretlenir. İstisnalar `manifest.yaml`'da.
- **Eğitim kapsamı (2026-10-24):** Önceki kişisel dersler kapsam dışı kararı kullanıcı talebiyle değişti. İnsan için dersler `dersler/` altında; öncelik HFT → Arbitraj → Toplu Emirler → Tavan → Taban, BYF en son. Toplu Emirler, Varant Toplu'dan ayrıdır. Teknik kaynaklar mevcut yerinde kalır; eğitim katmanı anlatım, örnek ve gerçek konuşma notlarını tutar.
- **Kapsam dışı:** mate, Backoffice, Kripdome/DTA, Algo-GUI (en eski arayüz), `mtrader-new` (yeni GUI'nin kişisel öncül reposu, artık `mtrader-trade-ui` development'ta).
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
