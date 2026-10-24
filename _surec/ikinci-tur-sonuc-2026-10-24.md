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

# İkinci statik tur — sonuç

Planlanan konu bazlı statik karşılaştırma ve kapanış tutarlılık taraması tamamlandı. Bu, her repo satırının yeniden incelendiği, bütün açık adayların doğrulandığı veya prod'un test edildiği anlamına gelmez. Kaynak uygulama kodları değiştirilmedi; dokümanlar kullanıcı içerik onayını bekleyen taslak durumundadır.

## Kapsam

| Konu | Yapılan / kanıt |
|------|------------------|
| Risk ve emir kimliği | Risk çekirdeği, yerel ret, token/registry ve GUI kuyruğu; [23 Ekim raporu](kaynak-karsilastirmasi-2026-10-23.md) |
| SDK / FIX | Replay/combiner ve main farkları; legacy FIX fill/replace, şifre/config/ret; [SDK karşılaştırması](../10-servisler/maordersdk/branch-ve-replay-kontrolu.md), [FIX karşılaştırması](../10-servisler/order-service/fix-branch-karsilastirmasi.md) |
| HFT stratejileri | Classic, Tavan/Taban callback/timer, Varant 13/15, Teorik ve ilgili feature ayrımları; ayrıntılar ilgili strateji belgelerinde |
| AlgoProd stratejileri | Fon hedge eşiği, Arbitraj branch/ret/paket, VWAP AKD/Overall/stop-loss; [24 Ekim raporu](kaynak-karsilastirmasi-2026-10-24.md) |
| GUI / admin | Yeni GUI seçilmiş payload/snapshot alanları, admin main/backend alanları; eski GUI'nin bütün yolları ve gateway uçtan uca testi kapsam dışı |
| Operasyon | Paket-source deltası, SDK/service CI hedef ve matrix, run/config seçimi; canlı binary/port/tuning envanteri kapsam dışı |

## Tazelik ve baseline

23 Ekim'de 15 repoda fetch + referans pull yapıldı. 24 Ekim'de dokuz repo yeniden güncellendi; altısının remote kontrolü 23 Ekim'dedir. Tam liste ve uçlar tarihli raporlardadır. Bu kapanışta yeni network turu yapılmadı; rapor, incelenmiş snapshot'ları kapatır.

24 Ekim'de SDK `c2b5060`, order-service `26e9a02`, Setup `cade7d0` development'a ilerledi. Brüt-takas per-call açılış istisnası ve tekrarsız satır dağıtımı ilgili belgelere işlendi. Manifestte tam doğrulama SHA'ları topluca ilerletilmedi; dosya frontmatter'ındaki eski baseline ile tarihli ek bölüm ayrımı korunur. Yeni alan dışındaki eski içeriğin tamamı bu yeni SHA'lara karşı onaylandı sayılmaz.

Teorik feature `bfe65e2` incelendikten sonra `26ce9b2`'ye ilerledi; yeni uç yeniden incelenmedi. Varant GUI feature/motor eşleşmesi K-240 açık. Feature yorumları referans veya prod davranışı sayılmadı.

## Öncelikli takip

Sorun ayrıntıları tek yerde tutulur; indeks [ACIK-KONULAR](../ACIK-KONULAR.md). Aşağıdaki sıra takip önerisidir, bug düzeltme veya deploy yapıldığı anlamına gelmez.

| Öncelik | Takip |
|---------|-------|
| 1 | K-243 takipte geri çekildi: [gerçek preprod run kanıtı](dogrulama-k243-2026-10-24.md). Development dosya farkı mevcut run'ın main'e yazdığı anlamına gelmiyor |
| 2 | K-233/K-234 gerçek handler gövdeleriyle [yerel 5 senaryoda gözlendi](dogrulama-sifre-akisi-2026-10-24.md); düzeltilmedi, canlı entegrasyon sınırı sürüyor |
| 3 | [K-241/K-242 Varant](../20-stratejiler/varant.md#ikinci-kod-turu--ret-ve-parçalı-satış-sınırları): [yerel handler senaryoları](dogrulama-varant-2026-10-24.md) tamamlandı; gerçek SDK/host entegrasyonu ve prod platform davranışı sınanmalı |
| 4 | K-194/K-195 ve diğer branch bulguları: kurulu binary/config kanıtıyla müşteri etkisi belirlenmeli |

## Kontrol ve tamamlanmayanlar

Yerel bağlantı/frontmatter/satır sınırı/K-id/manifest ve yerel kaynak commit nesnesi kontrolleri `kontrol.py --sources` ile çalıştırıldı. Bu araç içerik doğruluğu, ABI, runtime veya remote atalık testi yapmaz. Build, browser, QuickFIX/ACK zamanlama testi, CI run incelemesi, canlı emir/şifre/DB işlemi ve deploy yapılmadı.

Sonraki iş, kalan açık adayları ayrı doğrulama senaryolarıyla ele almak ve incelenmemiş yeni feature ucunu kontrol etmektir. K-243 sonradan gerçek run kanıtıyla geri çekildi; kanıt yukarıda. Bu rapor ilk yazıldığında yerel commit'teydi; sonraki oturum başında yerel main origin/main ile eşit gözlendi, bu agent push yapmadı.
