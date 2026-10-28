---
kapsam: HFT sanity Excel revizyonunun kaynak kapsamı, eski iddiaların ayrılması ve doğrulama kaydı
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: MAOrderSDK
    branch: development
    commit: c2b5060
  - repo: Algo-Setup
    branch: development
    commit: cade7d0
dogrulama: 2026-10-26
durum: taslak
---

# HFT sanity incelemesi

## Güncel hazırlık — 28 Ekim

Kullanıcı, `codex-session-01a17c66-999e-7a91-87ca-7af1a0720d09.md` oturumundaki Arbitraj revizyonlarının HFT karşılığını inceleyip planlamayı istedi. Bu aşama hazırlıktır: Excel ve issue içerikleri değiştirilmedi; kaynak kod yeniden doğrulanmadı. Frontmatter'daki kaynak commitleri 26 Ekim incelemesine aittir.

Referans Arbitrajın son düzenidir: Genel, Senaryolar, Ayar Rehberi ve gizli Listeler. Ana sanity ve genişletilmiş kontroller ayrılır; sorun/karar takibi Excel'de tutulmaz. Mevcut görsel tasarım korunur. HFT'nin 8 ön koşul, 57 senaryo, 33 regresyon ve 31 parametre kaydı salt okunur incelendi. Nihai test sayısı henüz belirlenmedi.

### Revizyon planı

1. Aktif HFT dosyası ile varsa kullanıcı teslim kopyasını karşılaştır; sonuç, gözlem, kişi/tarih ve kanıtları kimlikleriyle koru. Silinen kimlikleri yeniden kullanma; değişen adımlardaki eski sonucu yeni test kanıtı sayma.
2. Genel sayfasında kullanıcı hazırlığını tut. G03–G05 gibi DB, handoff ve replay kontrollerini teknik belgeye ayır; kullanıcıya gözleyebileceği hazır olma koşullarını yaz. Test hesabı, araç, ortam/sürüm ve başlangıç değerlerini anlaşılır kaydet.
3. Senaryoları ana sanity ve genişletilmiş kontroller olarak sınıflandır. Ekleme, ayar kaydı, başlat/durdur, temel tetik/emir/gerçekleşme ve ekran takibi ana akış adaylarıdır. Pozisyonlu/pozisyonsuz modları ayrı tut. Özel seans, kısmi gerçekleşme ve ek ayar kombinasyonlarını genişletilmiş kapsam açısından değerlendir. A12/C05 emir yolu, D04 teknik metrik, E05/E07 servis yeniden başlatma ve E08 log yedeği gibi kontrolleri kullanıcı sanity'sinden ayır. Bu ön sınıflandırma kabul davranışı değildir.
4. Parametre Eşleştirme'yi Ayar Rehberi'ne dönüştür: ekrandaki ad, anlam/birim, kullanılacağı mod ve hazırlık. Wire alanları, fonksiyon/repo adları, uyum etiketleri ve sorun anlatıları çıkarılır. P26–P31 gibi ekran dışı altyapı kayıtları kullanıcı ayarı gibi sunulmaz. Bilinmeyen birim veya davranış için örnek uydurulmaz.
5. Regresyon sekmesini ve diğer sayfalardaki sorun/karar takibini kaldırmadan önce açık kayıtların [toplu issue](../../issues/sanity/hft-toplu-issue.md) karşılıklarını kontrol et. Excel'den çıkarılması sorunun giderildiği anlamına gelmez; issue'lar topluca silinmez. Kullanıcının tamamen çıkardığı konular tekrar takip maddesi yapılmaz.
6. İçerik revizyonunda ilgili kaynakları fetch sonrası `origin/development` üzerinden salt okunur kontrol et; gerektiğinde master/main farkını ayır. GUI kaynakları `hftPayload.ts`, `useHftSettingsForm.ts`, `HftTrackerForm.tsx`, `addPositionCommand.ts`; motor kaynakları HftClassic, komut okuyucu ve GUIManager'dır. Limit/devir için gerektiğinde MAOrderSDK, order-service ve Algo-Setup incelenir. Uygulama dosyaları değiştirilmez; kritik açıklamaların kaynak commitleri teknik kayıtta tutulur.
7. Teknik sonucu önce raporla; yalnız ürün niyeti koddan çıkmıyorsa kullanıcıya tek konu halinde sor. Önerilen sıra: kâr al/stop-loss → tek işlem ve miktar → saat/durdurma/seans → fiyat sınırı ve emir tipi → kalan ekran/ortam konuları. Bunlar mevcut issue başlıklarıdır, yeni doğrulanmış hata değildir. Arbitraj kararları HFT'ye otomatik uygulanmaz. Ortak GUI kararları güncel HFT uygulamasıyla karşılaştırılır; kullanıcıdan aynı karar tekrar istenmez.
8. Teslimde kimlikler/kullanıcı girdileri, özet formülleri, açılır listeler, filtreler, sekme bağlantıları ve görünür sayfaların okunabilirliği kontrol edilir. Güncel kapsam sanity README'sine, teknik kanıt bu dosyaya, açık sorunlar yalnız issue dosyasına yazılır. Canlı test yapılmadıkça sonuç atanmaz.

**Devam noktası:** Hazırlık tamamlandı. Sonraki çalışma HFT satırlarını sınıflandırmak ve ilk teknik konu olan kâr al/stop-loss alanlarını güncel kaynakla karşılaştırmaktır. Bu tur Excel, issue, uygulama kodu veya uzak depo değiştirilmedi.

Yarım kalan 26 Ekim oturumunun devamıdır. Aktif dosya [HFT Excel](../../testler/sanity/MTrader_HFT_Sanity_Test.xlsx), açık bulguların tek toplu metni [HFT issue taslağı](../../issues/sanity/hft-toplu-issue.md). Kullanıcı yeni GUI development kapsamındaki Arbitraj çalışmasının ardından HFT'nin tamamlanmasını istedi. Arbitraj dosyası bu devamda değiştirilmedi.

## Kaynak ve kanıt sınırı

Önceki oturumun kaynak incelemesi ve hazırladığı hücre değişiklikleri devralındı. Bu devamda HFT ve GUI çalışma ağaçlarının temiz olduğu ve HEAD'lerinin yukarıdaki commitlerle eşleştiği görüldü; kritik TP/stop-loss yolları tekrar okundu. Yeni fetch, build, canlı emir veya dağıtım testi yapılmadı. Önceki karşılaştırmada motor master `052dd96`, SDK main `d5adc6f` idi. Kaynak karşılaştırması müşteride çalışan binary/config doğrulaması değildir.

GUI kaynakları: `app/components/dockview/hft/hftPayload.ts`, `app/components/modals/hftSettings/useHftSettingsForm.ts`, `HftTrackerForm.tsx`, `addPositionCommand.ts`. Motor kaynakları: `src/Strategy/HftClassic.{cpp,h}`, `src/Commands/HftClassicCommand.cpp`, `src/GUI/GUIManager.cpp`, `src/Main/HftMain.cpp`, StrategyManager ve periyodik iş yolları. Genel davranış ayrıntıları mevcut [Classic](../20-stratejiler/hft-classic.md), [strateji çekirdeği](../10-servisler/hftsrvprod/strateji-cekirdegi.md), [emir yaşam döngüsü](../10-servisler/hftsrvprod/emir-yasam-dongusu.md) ve [risk](../10-servisler/order-service/risk.md) belgelerindedir.

## Eski iddiası kapanan regresyonlar

Buradaki kapanış yalnız eski hata iddiasının kaynak kapsamından çıkarılmasıdır. Satırlar regresyon amacıyla korunur; test sonucu **Test Edilmedi** kalır.

| Excel | Karar ve kaynak dayanağı |
|---|---|
| R04 | Yeni GUI pozisyonlu modda pozisyonsuz alanları gizler/kilitler ve ortak varsayılanlara çeker. Görünen ama etkisiz stop-loss kontrolü iddiası bu kapsamda geçersiz. |
| R14 | `createHftPayload` eksik Hft_Type ve Time_In_Force için 1 kullanır; eski 0 gönderme iddiası geçersiz. |
| R15 | Modal ve satır düzenlemesi ortak `normalizeHftFields` / payload yolunu kullanır. Eski iki farklı varsayılan iddiası taşınmadı. |
| R17 | Limit ve pozisyon fiyatı enstrümanın divider değeriyle ölçeklenir; sabit ×1000 iddiası geçersiz. |
| R25 | `HftMain.cpp` içindeki lisans kontrol çağrısı yorumdadır. Yardımcı sınıfta timeout eksikliği aktif açılışın kilitlendiğini kanıtlamaz. |
| R32 | GUI iptal/replace `ownsOrder` ile yol seçer; strateji yollarında da sahiplik koruması vardır. Genel koruma yokluğu iddiası geçersiz; handoff geçiş aralığı ayrı konudur. |

## Açık ve koşullu kayıtlar

R01–R03, R05–R13, R16, R18–R24, R26–R31 ve R33 kapsamları [toplu issue metninde](../../issues/sanity/hft-toplu-issue.md) tutulur. R20/R23/R24/R27/R31/R33 teyit bekler. R06/R11/R12/R13/R16 gibi ürün sözleşmesi gerektiren noktalar otomatik hata veya onaylanmış kabul ölçütü sayılmaz.

R01'deki eski 11.06.2026 ve 5 lot → 10 lot anlatısının özgün canlı kanıtı bu çalışma alanında doğrulanmadı; kesin gözlem cümlesi kaynak adayı olarak daraltıldı. R18'de 60 saniyelik replay timeout ile 20 saniyelik zero-handoff watchdog ayrıldı. R20/R23'te bütün emir yollarının aynı limit davranışına sahip olduğu genellemesi kaldırıldı. R33'te token yaşam döngüsü ve config yorum ayrıştırması iki bağımsız teyit olarak tutulur.

## Excel ve teslim kontrolü

Sürüm 1.2; 8 ön koşul, 57 senaryo, 33 regresyon ve 31 parametre. Toplam 98 testin tamamı Test Edilmedi. Test sonucu, kullanıcı gözlemi ve tarih/kişi alanları korunur. Kapsam dışı/teyit bekliyor sınıfları, Kısmen sonuç seçeneği, durum özetleri ve gerçek veri aralıklarına uygun filtreler eklendi. Kaynaklar yeni GUI'ye uyarlandı; satır silme beklentisi ürün kararı olarak ayrıldı. Replace geçmişinin yenilemede yüklenmemesi kullanıcı ürün kararı olarak korundu.

Önceki kopya `_yedek_2026-10-26-hft-inceleme/` içindedir. ZIP/XML, test kimliklerinin tekilliği, sonuç/gerçekleşen sonuç ve açılır liste kurallarının korunması paketleme sırasında doğrulandı. Artifact Tool ile yeniden hesaplama, formül hata taraması, özet incelemesi ve beş sayfadan altı aralığın görsel kontrolü geçti. Geçici kopyada bir sonucu Kısmen yapmak Test Edilmedi sayısını 8'den 7'ye, Kısmen sayısını 0'dan 1'e getirdi; geri alma da doğrulandı. Bu kontroller stratejinin manuel testi değildir; bu devamda native Excel açılışı yapılmadı.
