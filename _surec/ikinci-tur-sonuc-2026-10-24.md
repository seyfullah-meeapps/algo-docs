---
kapsam: 23–24 Ekim statik kod karşılaştırmasının kapanışı, kaynak tazeliği, kapsam ve kalan doğrulamalar
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: c2b5060
  - repo: order-service
    branch: development
    commit: 26e9a02
  - repo: Algo-Setup
    branch: development
    commit: cade7d0
dogrulama: 2026-10-24
durum: taslak
---

# İlk aşama kapanışı — 24 Ekim 2026

**İlk aşama tamamlandı; aktif devam işi yok.** Kullanıcının son kapsam kararıyla sorun araştırmaları şimdilik ertelendi. Planlanan doküman yazımı, servis/strateji/akış/operasyon derinleştirmesi, development–master/main karşılaştırması ve son tutarlılık kontrolü kapatıldı. Açık konuların çözümü, artifact incelemesi veya canlı test bu kapanışın ön şartı değildir.

Planlanan konu bazlı statik karşılaştırma ve kapanış tutarlılık taraması tamamlandı. Bu, her repo satırının yeniden incelendiği, bütün açık adayların doğrulandığı veya prod'un test edildiği anlamına gelmez. Kaynak uygulama kodları değiştirilmedi; dokümanlar kullanıcı içerik onayını bekleyen taslak durumundadır.

## Kapsam

| Konu | Yapılan / kanıt |
|------|------------------|
| Risk ve emir kimliği | Risk çekirdeği, yerel ret, token/registry ve GUI kuyruğu; [23 Ekim raporu](kaynak-karsilastirmasi-2026-10-23.md) |
| SDK / FIX | Replay/combiner ve main farkları; legacy FIX fill/replace, şifre/config/ret; [SDK karşılaştırması](../bilgi-tabani/10-servisler/maordersdk/branch-ve-replay-kontrolu.md), [FIX karşılaştırması](../bilgi-tabani/10-servisler/order-service/fix-branch-karsilastirmasi.md) |
| HFT stratejileri | Classic, Tavan/Taban callback/timer, Varant 13/15, Teorik ve ilgili feature ayrımları; ayrıntılar ilgili strateji belgelerinde |
| AlgoProd stratejileri | Fon hedge eşiği, Arbitraj branch/ret/paket, VWAP AKD/Overall/stop-loss; [24 Ekim raporu](kaynak-karsilastirmasi-2026-10-24.md) |
| GUI / admin | Yeni GUI seçilmiş payload/snapshot alanları, admin main/backend alanları; eski GUI'nin bütün yolları ve gateway uçtan uca testi kapsam dışı |
| Operasyon | Paket-source deltası, SDK/service CI hedef ve matrix, run/config seçimi; canlı binary/port/tuning envanteri kapsam dışı |

## Tazelik ve baseline

23 Ekim'de 15 repoda fetch + referans pull yapıldı. 24 Ekim'de dokuz repo yeniden güncellendi; altısının remote kontrolü 23 Ekim'dedir. Tam liste ve uçlar tarihli raporlardadır. Bu kapanışta yeni network turu yapılmadı; rapor, incelenmiş snapshot'ları kapatır.

24 Ekim'de SDK `c2b5060`, order-service `26e9a02`, Setup `cade7d0` development'a ilerledi. Brüt-takas per-call açılış istisnası ve tekrarsız satır dağıtımı ilgili belgelere işlendi. Manifestte tam doğrulama SHA'ları topluca ilerletilmedi; dosya frontmatter'ındaki eski baseline ile tarihli ek bölüm ayrımı korunur. Yeni alan dışındaki eski içeriğin tamamı bu yeni SHA'lara karşı onaylandı sayılmaz.

Teorik feature `26ce9b2` takipte [statik delta olarak incelendi](../bilgi-tabani/20-stratejiler/teorik-fiyat.md#24-ekim--feature-26ce9b2-farkı): açılış yayını, own-state guard, sıfır denge ve ters emir fiyatı farkları kaydedildi. Development/master'a merge edilmemiş; runtime zamanlaması sınanmadı. Varant GUI feature/motor eşleşmesi K-240 açık. Feature yorumları referans veya prod davranışı sayılmadı.

## Kayda alınan teknik takip — ertelendi

K-240 takibinde [GUI–motor kaynak eşleşmesi](../bilgi-tabani/20-stratejiler/varant-toplu.md#24-ekim--motor-feature-eşleşmesi) ve [SDK API karşılığı](../bilgi-tabani/10-servisler/itch-sdk/quote-executed-feature.md) bulundu: GUI d2c35c7 ↔ HFT f20b5f2 ↔ itch-sdk e800b3d. Açık kalan kapsam uyumlu header/library artifact'i ve birlikte dağıtım eşleşmesidir; development desteği sayılmaz.

Sorun ayrıntıları tek yerde tutulur; indeks [ACIK-KONULAR](../issues/ACIK-KONULAR.md). Aşağıdaki kayıtlar tamamlanmış incelemeyi ve kalan kanıt sınırını gösterir; aktif iş sırası değildir. Yeni kullanıcı talebi olmadan bunlar üzerinden araştırma sürdürülmez.

| Kayıt | Son durum / ertelenen sınır |
|---------|-------|
| 1 | K-243 takipte geri çekildi: [gerçek preprod run kanıtı](dogrulama-k243-2026-10-24.md). Development dosya farkı mevcut run'ın main'e yazdığı anlamına gelmiyor |
| 2 | K-233/K-234 gerçek handler gövdeleriyle [yerel 5 senaryoda gözlendi](dogrulama-sifre-akisi-2026-10-24.md); düzeltilmedi, canlı entegrasyon sınırı sürüyor |
| 3 | [K-241/K-242 Varant](../bilgi-tabani/20-stratejiler/varant.md#ikinci-kod-turu--ret-ve-parçalı-satış-sınırları): [yerel handler senaryoları](dogrulama-varant-2026-10-24.md) tamamlandı; gerçek SDK/host entegrasyonu ve prod platform davranışı sınanmalı |
| 4 | K-194/K-195 ve diğer branch bulguları: kurulu binary/config kanıtıyla müşteri etkisi belirlenmeli |

## Kontrol ve tamamlanmayanlar

Yerel bağlantı/frontmatter/satır sınırı/K-id/manifest ve yerel kaynak commit nesnesi kontrolleri `kontrol.py --sources` ile çalıştırıldı. Bu araç içerik doğruluğu, ABI, runtime veya remote atalık testi yapmaz. Tam uygulama build'i, browser, gerçek QuickFIX/ACK zamanlama testi, canlı emir/şifre/DB işlemi ve deploy yapılmadı. Takipte iki odaklı C++ harness çalıştırıldı (toplam 10 senaryo); bunlar sahte adaptörlerle gerçek handler gövdelerini sınar. K-243 için var olan bir CI run/job salt okunur incelendi. Bunlar tam entegrasyon veya prod doğrulaması değildir.

Teorik yeni feature ucu ve K-240 GUI–motor–SDK kaynak zinciri incelendi; bunlar incelenmemiş işler olarak bırakılmadı. K-240 artifact/dağıtım ve diğer runtime kanıtları bilinçli olarak ayrı aşamaya ertelendi. Bu aşama için kullanıcıdan beklenen işlem yok.

## Teslim ve bakım

Giriş [README](../README.md), agent haritası [AGENTS](../AGENTS.md), repo/branch/commit envanteri [manifest](../manifest.yaml), açık kayıtlar [indeks](../issues/ACIK-KONULAR.md), yeniden çalıştırılabilir kontrol [kontrol aracı](kontrol.md). Kaynak tazeliği yukarıdaki tarihli raporlarla sınırlıdır; kapanış için bütün repolarda yeni fetch veya tüm kodu yeniden inceleme iddiası yoktur.

Belgelerin `taslak` etiketi korunur; ilk aşamanın tamamlanması içeriklerin topluca onaylandığı anlamına gelmez. Tam baseline SHA'ları kısmi incelemeler nedeniyle ilerletilmedi. İleride kullanıcı doküman güncellemesi veya belirli bir sorun çalışması isterse yeni kapsam açılır; sürekli bir “sıradaki” kuyruğu bırakılmadı. Değişiklikler yerel commit olarak kaydedilir; bu agent remote'a push yapmadı.
