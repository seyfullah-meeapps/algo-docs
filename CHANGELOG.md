# CHANGELOG

Her güncelleme oturumu bir kayıt. En yeni en üstte.

## 2026-10-24 — Frontend markası ve rehber okunabilirliği

- Frontend development b0474c3 içindeki özgün beyaz logo ve `app/global.css` renk tokenları okunarak yayın katmanına uygulandı; frontend değiştirilmedi. Kaynak/renk/ölçü kaydı eklendi.
- Koyu logolu kapak, marka yeşili, nötr iç sayfalar ve üst/alt bilgi; PDF gövdesi 11 → 10,25 pt, başlıklar 18/12 pt ve genişletilmiş başlık/paragraf araları. HTML düzeni aynı markaya uyarlandı; EPUB göreli yazı boyutu ayrı stile alındı.
- Üç çıktı yeniden üretildi; PDF sayfaları ve HTML görünümü görsel kontrol edildi. İlk bölüm içeriği değiştirilmedi; tasarım revizyonu kullanıcı incelemesini bekliyor.

## 2026-10-24 — A4 PDF, HTML ve EPUB yayın düzeni

- Quarto 1.10.18 resmi Windows ZIP'i checksum ile doğrulanıp proje içine taşınabilir kuruldu. MD kaynaklarını koruyan hazırlama/üretim scripti, A4 Typst şablonu, yayın listesi ve tekrar kurulum scripti eklendi.
- Kapak, otomatik içindekiler, sayfa numaraları ve ilk bölümden 5 sayfalık A4 örnek üretildi. SVG şema PDF/HTML/EPUB için eşlendi; kaynak Mermaid değişimi sessiz eski görsel kullanmak yerine hata verir.
- Tek üretim, kaydetmede PDF yenileme ve canlı HTML için VS Code görevleri/kullanım yönergesi eklendi. Canlı kaynak yenilemesi ve geri alma doğrulandı. PDF sayfaları görsel incelendi; A4, Türkçe metin/font, sayfa sınırları ve EPUB paketi kontrol edildi; ayrı EPUB okuyucu görünümü denenmedi.
- Yönetim/karar/soru takibi MD'de korunur; okuma kitabı yalnız seçilen konuları içerir. Araç, geçici dosya ve çıktılar Git dışında. Kaynak/publish talimatları yeni kullanıcı isteğiyle güncellendi; push yok.

## 2026-10-24 — Rehberin ilk konu anlatımı

- “Ne yapıyoruz ve neyi amaçlıyoruz?” taslağı yazıldı: ürün amacı, kullanıcı kontrolü, basit veri–karar–emir–sonuç örneği, kavramsal Mermaid akışı ve bileşenlerin görev özeti.
- Mevcut KB kaynakları ve referans commit'ler belirtildi; yeni kod/internet/canlı doğrulama yapılmadı. Kullanıcının yazım sürerken kodları inceleme bağlamı kaydedildi; okuma/onay varsayılmadı.
- Ana/bölüm indeksleri ve devam kayıtları güncellendi. Sıradaki konu kullanıcılar ve örnek iş günü; 47 konu iskelet olarak kaldı.

## 2026-10-24 — Hata anlatımı ve düzeltme sonrası rehber bakımı

- Kullanıcı mevcut hataların rehberde anlatılmamasını istedi. Teknik takip ayrı tutulacak; doğrulanan düzeltmenin rehbere etkisi kapanış kontrolüne dahil edildi.
- Kararlar, agent/yazım kuralları, strateji şablonu ve devam kayıtları güncellendi. Düzelmemiş davranışın çalışıyormuş gibi yazılmaması korundu. Temel yazım tercihleri netleşti; sonraki içerik uygulamanın amacı.

## 2026-10-24 — Rehberin teknik derinliği

- Kullanıcı mantık/davranış odaklı ana metni, gerektiğinde kısa açıklamalı kodu ve derin ayrıntıların ayrı bölümde tutulmasını kabul etti. Karar, yazım düzeni ve devam kayıtları güncellendi.
- Sıradaki netleştirme bilinen uygulama sorunlarının anlatımda gösterimi; sorun incelemesi veya konu yazımı başlatılmadı.

## 2026-10-24 — Rehberin okuyucusu netleşti

- Ana okuyucunun kullanıcı, sonraki okuyucuların görevi devralan ve ekibe katılan kişiler olduğu kaydedildi. Şirket içi bilgi aktarımı amacı ve rehberin ana çalışma konusu olması karar/ilerleme/oturum kayıtlarına işlendi.
- Yazım öncesi sorular tek tek ilerliyor; sıradaki açık tercih teknik/kod anlatım derinliği. İçerik veya teknik doğrulama yapılmadı.

## 2026-10-24 — Derslerden konu bazlı rehbere geçiş

- Kullanıcının isteğiyle önce ayrıntılı indeks yaklaşımına geçildi: uygulama amacı, borsa, teknik temel, mimari, stratejiler ve test/PM için altı bölüm, 48 ayrı konu iskeleti. İçerikler henüz yazılmadı; iskeletler `bos`.
- Eski 11 ders/yönetim dosyası `dersler/arsiv/` altında korundu, göreli bağlantılar düzeltildi; eski sıra geçersiz olarak işaretlendi.
- Rehbere özel AGENTS, kararlar, ilerleme, yazım/soru/kaynak/görsel düzeni ve strateji şablonu oluşturuldu. Kullanıcının bağlamı ve gerçek yapı soruları kaydedildi.
- Kök talimatlar, giriş ve oturum devam noktası yeni yapıya bağlandı. Bu tur internet/kod doğrulaması, uygulama testi veya görsel üretimi yok; ilk içerik uygulamanın amacı olacak. Önceki push reddi nedeniyle gönderim tekrar denenmedi.

## 2026-10-24 — Derslerin aktarımı ve PM öğrenme rotası

- Kullanıcının yeni talebiyle `dersler/` açıldı. Eski meeapps-ai içindeki yedi ders ve çalışma listesi incelendi; numaralar korunarak dersler yeniden yazıldı, eski repo değiştirilmedi.
- Handoff/SDK yolu, ölçek, token, mod/strateji ayrımları mevcut KB'ye göre revize edildi. Doğrulanmamış güncel mevzuat ve kesin kâr/dolum iddiaları taşınmadı; değişiklik gerekçeleri aktarım notlarına yazıldı.
- HFT → Arbitraj → Toplu Emirler → Tavan → Taban önceliği, BYF en son olacak şekilde ders indeksi oluşturuldu. Parametre/durum/ayar değişikliği/test şablonu ve PM test/issue/görev yönlendirme düzeni eklendi.
- README, AGENTS ve oturum notları eğitim kapsamına bağlandı. Dersler hazırlanmış taslaktır; kullanıcıyla yeni ders işlenmedi, uygulama testi veya yeni sorun araştırması yapılmadı.
- Yapısal kontrol: 105 Markdown, 1.526 bağlantı, 0 hata. `git diff --check` temiz; kaynak repo kontrolü bu aktarımda çalıştırılmadı.

## 2026-10-24 — İlk aşamanın nihai kapanışı

- Kullanıcı sorun araştırmalarını şimdilik kapsam dışında bıraktı; yazım/derinleştirme ve ikinci kaynak karşılaştırması tamamlanmış ilk aşama olarak kapatıldı. Yeni araştırma veya canlı işlem açılmadı.
- README, agent talimatı, manifest, inceleme durumu ve oturum notları aynı kapanış kararına bağlandı. Açık konuların otomatik görev kuyruğu olmadığı, kullanıcıdan beklenen işlem bulunmadığı belirtildi.
- Kapanış raporundaki eski “CI run incelenmedi / yeni feature incelenmedi” ifadeleri sonraki kanıtlarla düzeltildi. Yerel harness, statik kaynak ve gerçek entegrasyon sınırları ayrıldı; K-240 artifact/dağıtım dahil kalan teknik doğrulamalar ayrı aşamaya ertelendi.
- Taslak etiketleri ve tam baseline commit'leri korundu; aşama kapanışı toplu içerik onayı sayılmadı. Son yapısal/kaynak referansı ve diff kontrolleri çalıştırıldı; aktif sıradaki iş bırakılmadı.

## 2026-10-24 — K-240 SDK kaynak zinciri

- itch-sdk fetch/development pull sonrası 35a3b5c/master 00c51b1 aynı. Yeni executed_ex API warrant-open-quote-log-pp e800b3d içinde bulundu; HFT f20b5f2 callback imzası eşleşiyor. Aynı adlı SDK hft_warrant_advanced dalında API yok.
- QuoteBuyer çıkarımı, kalan kademe miktarı ve sıfır miktarlı geç quote bildirimi ayrı SDK feature belgesine yazıldı. HFT build'inin dış header/library bağımlılığı ve workflow tetik sınırları kaydedildi.
- K-240 artifact/dağıtım kapsamıyla açık. Kaynak incelemesi; CI run, binary export/link, replay veya canlı test yapılmadı. Sıradaki gerçek artifact/Setup eşleşmesi.

## 2026-10-24 — K-240 motor feature eşleşmesi

- HFT/GUI fetch ve development pull sonrası referanslar aynı. GUI d2c35c7 sözleşmesi HFT hft_warrant_advanced f20b5f2 parser/runtime/summary ve kapanış koduyla eşleştirildi; feature referans dallara merge edilmemiş.
- Motor aynı zamanda executed_ex API, quoteBuyer/isQuote/levelQtyAfter ve yeni tetik filtresi gerektiriyor. K-240 kaynak eşleşmesinden SDK/dağıtım eşleşmesine daraltıldı; kapatılmadı. Maliyet kapanış değişikliğinin sweep ayarından bağımsız olduğu kaydedildi.
- Kaynak delta incelemesi; build/link/replay/canlı emir yok. Sıradaki uyumlu itch-sdk ucu.

## 2026-10-24 — Teorik feature yeni uç incelemesi

- HFT fetch/development pull sonrası 4275ccc/master 052dd96 aynı. Feature 26ce9b2 yalnız kendi remote dalında; bfe65e2 sonrası tek commit/beş dosya incelendi.
- Açılış ilk eşleşme yayını, işleme anında own-state guard, sıfır denge koruması ve reverse emirde Expected_Price farkları ayrı feature bölümüne işlendi; referans akış değiştirilmedi.
- K-04/replace log-only sürüyor; statik inceleme, build/replay/canlı emir yok. Sıradaki K-240 motor eşleşmesi.

## 2026-10-24 — Varant handler senaryoları

- HFT development fetch/pull sonrası 4275ccc aynı. Dört gerçek C++ gövdesi, sahte SDK/mesaj yüzeyi ve gerçek mutex ile beş yerel senaryo sınandı.
- K-241 için MSVC yeniden kilit girişinde istisna gözlendi; prod kilitlenmesi olarak genellenmedi. K-242 iki ACK sonrası yalnız son token'a toplam miktarla replace üretildi. Kontroller geçti; kanıt `_surec/dogrulama-varant-2026-10-24.md`, araç `_surec/dogrula_varant_akisi.py`.
- Adaylar açık, belgeler taslak; tam entegrasyon/canlı işlem veya uygulama düzeltmesi yok. Sıradaki Teorik feature ucu.

## 2026-10-24 — Şifre handler'larıyla yerel senaryo doğrulaması

- SDK/order-service fetch/pull sonrası uçlar aynı. Gerçek yedi C++ fonksiyon gövdesini kaynaklardan çıkarıp MSVC ile derleyen, sahte DB/oturum kullanan araç eklendi; 5 senaryo geçti.
- K-233 1409'suz Logon sonucu ayrışması ve K-234 başarısız pending write sonrası aday döndürme handler düzeyinde gözlendi; 1409=0/1 ve mevcut pending kontrolleri geçti. Açık indeks/ayrıntı ve kanıt raporu güncellendi.
- Kaynak uygulama/şifre/DB değiştirilmedi. Full build, QuickFIX entegrasyonu ve gerçek async worker testi değil; PASS bug fix anlamına gelmez. Sıradaki Varant adayları.

## 2026-10-24 — K-243 gerçek run doğrulaması ve geri çekme

- SDK preprod a647c9e workflow'u ve başarılı push run 40012991193/job 120620335238 okundu. Hedef ref/destination_branch preprod; development dosyasından yapılan main'e yönlendirme genellemesi yanlıştı.
- K-243 açık indeksten çıkarıldı, kanıt dosyası eklendi; operasyon ve kapanış raporu düzeltildi. Numara tekrar kullanılmaz. CI tetiklenmedi/deploy yapılmadı.
- GitHub connector 404 sonrası gh CLI salt okunur sorguları kullanıldı. Oturum başında main origin/main ile eşitti; önceki push bekliyor bilgisi güncellendi, agent push yapmadı. Sıradaki şifre sonuç akışı.

## 2026-10-24 — İkinci statik turun kapanışı

- Konu bazlı inceleme kapsamı, dokuz/15 repo tazelik ayrımı, üç ilerleyen development ucu ve değişmeyen tam baseline'lar kapanış raporunda toplandı; README ve inceleme durumundan bağlandı.
- Son çelişki taramasında sabah akışı tekrarsız dağıtım özeti ve SDK API brüt-takas istisnası düzeltildi. Eski ilerleme notları tarihsel başlık altında ayrıldı.
- Durumlar taslak kaldı; bütün kod/canlı ortam doğrulandı denmedi. Sonraki öncelik açık adayların teknik doğrulaması. Build/canlı işlem/deploy/push yapılmadı.

## 2026-10-24 — CI hedef branch ve config/varyant kontrolü

- SDK/service güncel workflow'ları ve Setup run/config seçimi okundu. K-243 SDK preprod build artifact'ının push job'ında varsayılan main hedefine yönlenmesi statik adayı kaydedildi; gerçekleşmiş CI/prod değişimi iddia edilmedi.
- SDK aktif matrix regular/onload olarak düzeltildi; Mlx adımları/dosyasının güncel build kanıtı olmadığı açıklandı. K-182 ini/toml farkı sürüyor.
- Script/CI/container/deploy çalıştırılmadı; sıradaki kapanış kapsam ve tutarlılık kontrolü.

## 2026-10-24 — Operasyon paket deltası ve yeni emir davranışı

- Algo-Setup dev cade7d0/preprod 959be34'e ilerledi; paket SDK/header ve regular/Onload order-service binary'leri değişti, script/workflow değişmedi. algo-configs master aynı.
- Kaynaklar da fetch/pull edildi: SDK c2b5060 EnterOrderOptions.skip_brut_takas ekliyor; order-service 26e9a02 açılışta seçeneği kullanıyor ve tekrarsız satırları hesap kullanıcıları arasında bir kez dağıtıyor. Master/main uçları aynı.
- SDK emir, toplu emir, risk ve operasyon belgelerine kısmi güncel fark eklendi; K-92 daraltıldı. Tam baseline'lar ilerletilmedi. Deploy/binary/canlı emir çalıştırılmadı; kalan CI/config turu sırada.

## 2026-10-24 — Admin/backend alan sözleşmesi

- Admin main ve trade-data-app development fetch/pull: referans uçlar aynı. Admin feature ayrı kaldı; main frontend / backend development-master proto farkları tekrar okundu.
- K-221'e hesap listesinde eksik repeat_count için doğrudan toLocaleString çağrısının render sınırı eklendi. K-224 parola request/model/SQL yolu kontrol edildi; optional OUCH alanlarıyla aynı koruma varsayılmadı.
- Yeni sorun numarası ve uygulama değişikliği yok; browser/DB testi veya gerçek parola işlemi yapılmadı. Sıradaki operasyon/deploy kaynakları.

## 2026-10-24 — Yeni GUI strateji payload/snapshot

- GUI/HFT fetch/development pull: referans uçlar aynı. Teorik feature ucu 26ce9b2'ye ilerledi; yeni feature kodu incelenmedi, önceki kayıt eski commit kapsamındadır.
- Saat End_Time/Stop_Time alias'ı, second-rule ve momentum delta dönüşümleri, Taban Finish_With_Sell sözleşmesi ve Classic stop kapatma farkı kontrol edildi. Backend sözleşmesine kapsam tablosu eklendi; yeni sorun numarası yok.
- Browser/build/canlı test ve uygulama değişikliği yok. Bugünkü kaynak raporu üç repoda tazelik kontrolü yapıldığını gösterecek şekilde güncellendi; sıradaki admin/backend alanları.

## 2026-10-24 — AlgoProd kalan strateji yolları

- AlgorithmicTrading fetch/development pull: uçlar aynı; diğer repolar bugün yeniden kontrol edilmiş sayılmadı. Ayrı 24 Ekim kaynak raporu eklendi.
- VWAP AKD/Overall ve stop-loss, Arbitraj paket tutarlılığı/hedge takibi okundu. K-205/K-206 sürüyor; yeni numara açılmadı. Stop-loss sonrası aynı runStrategy turunun devamı ve başlangıç paket denetiminin runtime hedge garantisi olmadığı açıklandı.
- Build/canlı servis/emir testi ve uygulama değişikliği yok. Sıradaki GUI/admin/operasyon karşılaştırması.

## 2026-10-23 — AlgoProd branch/ret ve hedge eşiği

- AlgorithmicTrading fetch/development pull sonrası uçlar aynı. Fon Takibi kotasyon farkı, Arbitraj faiz/başlatma farkı ve VWAP incelenen strateji/command kaynaklarının aynı olması teyit edildi.
- K-194 sepet eşiği Q>L koşuluyla daraltıldı; K-194/K-195 kaynak branch bulguları prod binary/config sonucu gibi sunulmadı.
- Fon sepet reject/completion, Arbitraj başlatma ve türev ret yolu, VWAP accept/reject/lot sonu yolu okundu; üç belgeye inceleme kapsamı eklendi. Yeni sorun numarası açılmadı.
- Build/canlı hedge testi ve uygulama değişikliği yok. Kalan AKD/Overall/stop-loss ve paket ayrıntıları sırada.

## 2026-10-23 — Varant (13) ve Teorik Fiyat ikinci turu

- HFT yeniden fetch/development pull: uçlar aynı. Varant çekirdek/command ve Teorik çekirdek master/development farkları kontrol edildi; incelenen kaynaklar aynı.
- K-241 Varant senkron SDK reddinin recursive olmayan derivativeMutex'e yeniden girmesi, K-242 parçalı alışlara karşı tek satış token'ı sınırı kaydedildi. Toleransın stop()/iptal garantisi olmadığı ve replace mandalının ACK olmadığı açıklandı.
- Teorik theo-cancel-on-first-eslestirme bfe65e2 ayrı feature olarak incelendi: diğer orderbook ilk kapanış eşleşmesinden erken değerlendirme. Referans davranışına geçirilmedi; fill log-only K-04 sürüyor.
- Build/canlı test ve uygulama değişikliği yok. Sıradaki AlgoProd stratejileri.

## 2026-10-23 — Süpürme UI/wire ve feature ayrımı

- HFT ve GUI fetch/development pull sonrası referans uçlar değişmedi. Tavan form/toplu/nihai payload Should_Sweep kuralı ve motor parser/trigger karşılaştırıldı.
- Pozitif Melt_Lot şartının yeni GUI'de olduğu, motor garantisi olmadığı; eşik ile TLSize emir büyüklüğünün ayrı olduğu açıklandı. Bütün kademelerin mutlaka tek emirle alınacağı ifadesi daraltıldı.
- feat/sweep-left-ask d2c35c7 Varant Toplu alanı/yorumları referans motorla karşılaştırıldı. K-240 development motor eşleşmesi adayı; feature yorumları canlı destek sayılmadı. Tavan Should_Sweep ile Varant Sweep_Left_Ask ayrı belgelendi.
- Build/browser/canlı test yok; uygulama kodu değişmedi. Sıradaki Varant (13), Teorik Fiyat ve AlgoProd.

## 2026-10-23 — Varant Toplu motor ikinci turu

- HFT fetch/development pull sonrası referans uç değişmedi; master'da Varant Toplu sınıfı yok. Yeni theo-cancel-on-first-eslestirme remote ref'i görüldü, içeriği bu turda incelenmedi.
- Tetik, emir/replace, accept/fill/reject, close/release ve next-check yolları okundu. Satışın her fill'de koşulsuz yazıldığı ve her yarışta açığa düşmemenin garanti olduğu ifadeleri daraltıldı.
- SellRejected sonrası sonraki alış fill'lerinde otomatik satış olmadığının ve Frozen/Raised hedeflerinin ACK olmadığının altı çizildi. K-239 yoğun kuyrukta planlı repricing gecikmesi adayı kaydedildi.
- Build/canlı/zamanlamalı test ve uygulama değişikliği yok; UI ikinci turu henüz yapılmadı.

## 2026-10-23 — Tavan/Taban callback ve timer sıraları

- HFT yeniden fetch/development pull: uçlar aynı. Pending-open TTL, restore top-up, Taban auto lift/manual cancel, reClose timer ve callback sonu kontrolleri okundu; master timer/restore varlığı kontrol edildi.
- Önceki turda yazılan “Taban reClose timer master'da yok” ifadesi düzeltildi: iki branch'te de var. Taban zamanlamasının yalnız ITCH saati olduğu ifadesi düzeltildi; sentetik olay system_clock, job steady_clock kullanır.
- K-238 çalışma saati filtresinin koruyucu timer/defter olaylarını da elemesi adayını kaydeder. Taban tüm seviye eşik sınırının strict < olduğu, TTL'nin otomatik gönderim timer'ı olmadığı açıklandı.
- Statik inceleme; build/canlı/zamanlamalı test ve kaynak uygulama değişikliği yok. Sıradaki diğer stratejiler.

## 2026-10-23 — HFT Classic ve Tavan/Taban branch farkları

- HFT yeniden fetch/development pull: uçlar aynı. Classic çekirdek/command dört dosyası development/master aynı; accept/fill/reject, stop ve tek işlem mandalı okundu.
- K-236 kullanılmayan stop enable bayrağı, K-237 satış dalında alış başlangıç bayrağı kontrolü kaydedildi. Tek işlem “stop” özeti mandal davranışına düzeltildi.
- Tavan momentum gate/window ve escape örneklemesi, Taban yeni alan/reClose timer/PTRM stop farkları belgelendi. K-235 PTRM duruşunun master'da olmadığı kaydedildi; üç stratejiye master kaynak metadata'sı eklendi.
- Statik alt tur; build/canlı emir testi ve uygulama değişikliği yok. Tavan/Taban top-up/reClose callback sıralarının tamamı henüz yeniden incelenmedi.

## 2026-10-23 — FIX şifre/config ve ret yolları

- order-service ve SDK yeniden fetch/development pull: uçlar aynı. Legacy master ile SDK/host oturum ayarları, sequence başlangıcı, 35=3/35=j ve cancel-reject yolları karşılaştırıldı; FIX branch belgesi genişletildi.
- K-233: 1409'suz Logon SDK'da başarı, host'ta bilinmiyor sayılıyor; eski live şifrenin promote edilip pending'in temizlenmesi statik adayı kaydedildi.
- K-234: manuel config pending yazımı başarısızken arm devam ediyor; otomatik akış DB onayı bekliyor. Koşulsuz crash-safe invariant düzeltildi, SDK/host belgeleri çapraz bağlandı.
- Şifre/uygulama kodu değiştirilmedi; canlı/QuickFIX testi yok. Planlanan FIX statik ikinci turu tamamlandı, sıradaki HFT Classic/Tavan/Taban strateji incelemesi.

## 2026-10-23 — Legacy FIX fill/replay ve replace

- order-service ve SDK yeniden fetch/development pull: uçlar aynı. Master FIXManager/OrderUtility/OrderManager ile development host ve SDK FIX dönüş/replay blokları karşılaştırıldı.
- Yeni FIX branch belgesi eklendi; README indeksi güncellendi. SDK codec'in birebir port olduğu iddiası fill fiyatı farkı nedeniyle düzeltildi.
- K-121 miktar replace sonrası kayıt/tag 38 sayı farkının legacy master'da da olduğu koddan teyit edildi; exchange sonucu test edilmedi. K-232 geçmiş rapor yeniden teslim edilirse legacy fill'in pozisyon kuyruğuna tekrar girmesi adayı kaydedildi.
- Build/canlı test yok; kaynak uygulama dosyaları değişmedi. Kalan FIX şifre/config ve ret yolları sırada; belgeler taslak.

## 2026-10-23 — SDK replay/combiner ve main farkları

- SDK yeniden fetch/pull edildi, uçlar değişmedi. Combiner ve OUCH connection development/main farkları, SDK callback/routing/limit blokları karşılaştırıldı; yeni branch/replay belgesi ve README indeksi eklendi.
- K-106 açıklamasında aynı süreçte eligible token kaydı ile yeni süreç adopt'u ayrıldı. Poison mevcut OUCH sayaçlarını sıfırlamaz; replay dedup sayılmadı.
- K-231 main hard cap'in yalnız enstrüman limiti aşımında koşması ve kontrolsüz notional çarpımı kaynak branch bulgusu olarak kaydedildi; prod binary/config iddiası yapılmadı. Risk belgesine çapraz bağlantı eklendi.
- Soket gönderim kilidi, reconnect temizliği, atomik trampoline ve token/split değişiklikleri branch tablosunda. Build/canlı test yok; sıradaki legacy FIX/master ve development SDK FIX karşılaştırması.

## 2026-10-23 — HFT/SDK callback ve token alt turu

- Altı ilgili kaynak repoda yeniden fetch ve development pull yapıldı; uçlar değişmedi. HFT master/development registry ve callback farkları kontrol edildi.
- K-56 uçtan uca hard-cap aşımı iddiası daraltıldı; fallback denemesi ve ikinci yolun kendi kontrolleri ayrıldı. Replace sıfır alanlarının BIST semantiği teyit edilmiş sayılmadı.
- K-230 eski token'lı GUI olayının replace rekey'i sonrasında varsayılan proto'ya dönüşebilmesi statik kod senaryosuyla kaydedildi; gRPC özeti düzeltildi. Canlı test ve uygulama kodu değişikliği yok; belgeler taslak. Replay/combiner ve SDK main ayrıntılı turu sırada.

## 2026-10-23 — Remote tazeliği ve ikinci kod incelemesi: risk

- Kullanıcının development ve master/main'in güncel halleriyle kıyaslama isteği üzerine 15 kaynak klonda temizlik kontrolü, origin fetch ve referans branch pull --ff-only yapıldı. Hepsi zaten güncel; manifest doğrulama SHA'ları değiştirilmedi. Master/main ve test ortamı ref'leri de okundu; sonuçlar `_surec/kaynak-karsilastirmasi-2026-10-23.md` içinde.
- Manifestte son remote kontrol tarihi/raporu eklendi. trade-data-app master-only sayısı 9 toplam / 6 merge dışı olarak netleştirildi.
- order-service RiskManager/RiskInfo, development SDK callback'leri, master OUCH callback noktaları; MAOrderSDK limit bloğu, risk RPC/proto ve istemci ret eşlemesi incelendi. Risk belgesine güncel master farkları eklendi.
- Düzeltmeler: kopuk stream son limitlerle kontrolü sürdürür; SDK hard cap koşulsuz değildir; ShortSell TL kontrolü her koşulda geçmez; token'sız ret eşlemesi açıklandı. K-74 metni düzeltildi; K-229 price=0 market alış tutar kontrolü adayı eklendi (canlıda test edilmedi).
- order-service satış dağıtımı, GUI ve admin alanları için ayrı feature branch'ler kaydedildi; main/development davranışı sayılmadı. K-221 açık kaldı.
- Kapsam ilk risk içerik turudur; bütün KB yeniden kodla doğrulandı denmedi. Kaynak uygulama kodu, canlı sistem ve durum etiketleri değiştirilmedi; push tekrar denenmedi.

## 2026-10-23 — Genel tutarlılık ve taslak incelemesine hazırlık

- Tüm bilgi tabanı için `_surec/kontrol.py` eklendi: yerel inline bağlantılar/başlıklar, frontmatter alanları, 400 satır sınırı, K numarası tekilliği, manifest belge yolları; isteğe bağlı salt okunur Git commit ve yerel origin branch kontrolleri. Tam YAML parser'ı veya içerik doğrulaması değildir.
- `_surec/kontrol.md` kullanım/sınırları ve `_surec/inceleme-durumu.md` öncelikli kullanıcı incelemesi sırasını içerir. Ana README'ye frontmatter ve bağlantılar eklendi.
- HftSrvProd `4275ccc` StrategyManager/OuchManager ve callback/kilit noktaları kontrol edildi: 20 s zero-handoff watchdog, ilk handoff sonrası 60 s timeout ve gate'i atlayan yollar özetlerde ayrıldı. HFT restart'ı için eski belirsizlik K-215 senaryosuna bağlandı.
- Sistem haritasındaki bütün state'in korunmuş olduğu iddiası kaldırıldı; handoff login sayısı ilk + dört tekrar olarak netleştirildi. Sabah/log özetlerindeki sabit 09:40 ve her açılışta watchdog log'u varsayımları düzeltildi.
- Kontrol aracı gerçek repo üzerinde ve geçici örneklerle sınandı: kod içindeki sahte bağlantılar, Türkçe/tekrarlı başlıklar, eksik dosya/başlık. Kaynak nesneleri mevcut; remote fetch, canlı/build testi ve uygulama kodu değişikliği yok.
- `durum: dogrulandi` etiketi verilmedi. Önceki otomatik onay reddi nedeniyle push yeniden denenmedi; değişiklikler yerel commit'te tutulur.

## 2026-10-23 — Admin paneli derinleştirme (madde 13)

Kaynak: mtrader-frontend-apps main `db10c12`, trade-data-app development `1cca9a8` / master `4a43e19`, order-service development `b86c0cf`. Yerel snapshot'lar kontrol edildi; fetch, browser testi, build veya canlı deploy yapılmadı.

- Admin README indekse çevrildi; arayüz/oturum, alanlar/servis etkisi, dağıtım/sürüm farkları üç alt dosyada belgelendi.
- Route, auth/API/cache, liste/CSV, hesap/kullanıcı/order-user formları; CRUD DB ilişkileri, kayıt atomikliği ve canlı bağlantıya yansıma sınırları kaynak koddan incelendi.
- Development backend'deki hesap repeat_count/Dedicated kaldırılması ve OUCH repeat_count/core_to_pin eklenmesi master proto ile karşılaştırıldı; prod'a doğrudan genellenmedi.
- Yeni konular K-221–K-228; önceki K-16/K-17/K-19/K-220 ile ilişkiler linklendi. Belirsiz gateway JSON alan davranışı ve canlı sonuçlar kesinleştirilmedi.
- Planlanan derinleştirme maddeleri 1–9 ve 11–13 tamamlandı. Madde 10 kullanıcı taslak incelemesine bağlı; kod sorunları sonraki çalışma konusu.

## 2026-10-23 — Uçtan uca akışlar (madde 12)

Kaynak: mevcut yerel klonlar; HftSrvProd `4275ccc` / master `052dd96`, AlgorithmicTrading `0dc32a7` / master `aa150ee`, order-service `b86c0cf` / master `298403b`, trade-data-app `1cca9a8` / master `4a43e19`; diğer kaynaklar akışların frontmatter'ında. Remote fetch ve canlı sunucu incelemesi yapılmadı.

- Önceki oturumdan kalan beş commit edilmemiş taslak incelendi; `emir-donusu.md` ve `algoprod-emri.md` yazıldı. `30-akislar/README.md` yedi akışın indeksine çevrildi.
- Kritik kod yolları kontrol edildi: HFT callback/registry/FetchOrders, GUI emir ve komut yönlendirmesi, AlgoProd userbook/kanal/timeout, handoff ve gün içi restart bağımlılıkları.
- Eski README'nin HFT OUCH otomatik reconnect iddiası kaldırıldı. Uygulama iptali ile BIST cancel-on-disconnect belirsizliği ayrıldı; SetBalance'ın bağlantı kurtarmadığı belirtildi.
- Çapraz düzeltmeler: `duration` ms; HFT health servisi mevcut; motor gRPC hata kodları her zaman HTTP 500 değil; HFT handoff master'da da var; AlgoProd referans sürüm handoff callback'i boş. Sabah kontrolü restart bölümü bağımlı servis akışına bağlandı.
- Yeni konular K-208–K-220. Mevcut K-16/K-24/K-57/K-151/K-152 ile ilişkiler akışlarda belirtildi; canlı gözlem gerektiren sonuçlar kesinleştirilmedi.
- Taslakların kullanıcı incelemesi bekleniyor; kaynak uygulamalarda veya canlı sistemde değişiklik yapılmadı.

## 2026-10-23 — AlgoProd derinleştirme (madde 11)

Kaynak: AlgorithmicTrading `development` `0dc32a7`, `master` `aa150ee` (prod; 31 commit geride, 12 master-only commit), `add-order-sdk` `7d7f705`. Karşılaştırma için HftSrvProd `4275ccc`, order-service `b86c0cf`, trade-data-app `1cca9a8`, ouch-sdk `0c3589e`, mtrader-trade-ui `b0474c3` / `main` `6715182`.

- `10-servisler/algorithmic-trading/` alt dosyalara bölündü:
  - `uygulama-ve-threadler.md`
  - `emir-yolu.md`
  - `grpc-ve-veri.md`
  - README artık indeks ve "önce bil" özeti.
- `20-stratejiler/arbitraj.md`, `vwap.md`, `fon-takibi.md` koda karşı yeniden doğrulandı ve genişletildi. master farkları işaretlendi.
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

[2026-10-22](_surec/changelog-2026-10-22.md)
