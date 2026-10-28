# AGENTS.md — algo-docs

Bu repo MTrader'ın teknik bilgi tabanını, insan rehberini, yayınlarını, testlerini ve issue kayıtlarını birlikte tutar. **`bilgi-tabani/` AI agent'lar için yazılmıştır.** İnsan rehberi `dersler/`, okunabilir çıktılar `yayinlar/`, kullanıcı testleri `testler/`, sorun takibi `issues/` içindedir. Hedef okuyucu çalışılan alana göre seçilir.

## Önce bunu bil

- **Diğer repolar kesinlikle salt okunur.** Bu çalışma alanından uygulama repolarında kod değişikliği, düzeltme dalı/çalışma ağacı oluşturma, commit, PR, merge veya deploy yapılmaz. Kullanıcının bir sorunu inceletmesi ya da kendi yapacağı geliştirmeyi anlatması kod değişikliği yetkisi değildir. Kod yalnız kanıt toplamak için okunur; değişiklikler bu repodaki belge ve test dosyalarıyla sınırlıdır.
- **Kaynak repo yolu:** Motor incelemelerinde `C:\Users\Seyf\algo-workspace\AlgorithmicTrading` kullanılır; referans güncel `origin/development` içeriğidir. Masaüstündeki `AlgorithmicTrading` kopyası referans alınmaz. Diğer kaynak repolar da `C:\Users\Seyf\algo-workspace\` altından salt okunur incelenir. Fetch ile uzak referansları güncellemek, checkout dosyalarının da güncellendiği anlamına gelmez.
- **Güncel durum esastır.** Ürün belgeleri, sanity dosyaları ve açık sorun listeleri projenin güncel halini anlatır. Geçersiz veya kullanıcı tarafından giderilmiş kabul edilen konular silinir; “çözüldü”, tarihli kapanış veya geliştirme takibi olarak tutulmaz. Kullanıcının bildirdiği güncel davranış, kodla yeniden doğrulanmış gibi sunulmaz. Eski kimlikler yeni konulara verilmez. Kullanıcının tamamen çıkardığı konular yeniden açık soru, regresyon, kapanış özeti veya “önceden böyle çözülmüştü” hatırlatması olarak sunulmaz. Oturum notlarından da eski takip anlatısı kaldırılır; arşiv/yedeklerden görev türetilmez.

- **Ürün ve şirket:** Ürün `MTrader`, şirket `MeeApps`. Müşteriler aracı kurumlar; günlük kullanıcılar onların traderları/fon yöneticileridir. MeeApps geliştirme/test için kullanır. Kullanıcı beyanıyla netleşen özellik → test → preprod düşük/yüksek lot → müşteriler sürecinin tek kaydı `bilgi-tabani/00-genel/urun-ve-gelistirme-sureci.md`; bunu branch/CI akışıyla karıştırma.

- **Dil:** Metin Türkçe; teknik terimler, kod isimleri, wire alan adları İngilizce. Kullanıcıya hangi dilde sorulduysa o dilde cevap ver.
- **Doğruluk kaynağı kod.** Bu dokümanlar koddan damıtılmıştır ve belirli bir commit'e karşı doğrulanmıştır. Her dosyanın frontmatter'ında `kaynak` (repo, branch, commit) ve `dogrulama` (tarih) vardır. Cevabın kritikse (emir, fiyat ölçeği, risk, prod davranışı) ve repo erişimin varsa, ilgili koda bakıp teyit et.
- **Tazelik.** Repolar canlı; her gün commit alıyorlar. Bir bilginin güncel olup olmadığını sorarsan önce `manifest.yaml`'daki doğrulama commit'ine bak. Cevabında "şu commit itibarıyla" demekten çekinme.
- **Referans branch `development`.** Akış `development → preprod → master`. Prod'da çalışan davranış `master`'dır; dokümanlar `development`'ı anlatır ve prod'dan farklı olan yerleri açıkça işaretler (`⚠ master'da yok` gibi). İstisnalar `manifest.yaml`'da.
- **Gizli bilgi yok.** IP, kullanıcı adı, şifre, token `<PROD_IP>`, `<OUCH_USER>`, `<REDACTED>` gibi placeholder'larla maskelidir. Gerçek değeri tahmin etme, uydurma.
- **Bilmiyorsan söyle.** Dokümanda olmayan bir şeyi "muhtemelen" diye doldurma; "dokümanda yok, şu dosyaya bakılmalı" de.

## Çalışma oturumu (dokümanı yazan/güncelleyen agent için)

- **İlk aşama kapandı (2026-10-24).** Kullanıcı sorun araştırmalarını şimdilik kapsam dışında bıraktı. Yeni görev verilmeden açık konulardan otomatik devam zinciri oluşturma; belgeleri soruları yanıtlamak için kullan. Sonraki doküman güncellemesi veya sorun çalışması ayrı kullanıcı talebiyle başlar. Kapanış kapsamı `_surec/ikinci-tur-sonuc-2026-10-24.md` içinde.

- **Başlarken** `OTURUM-NOTLARI.md`'yi oku: kararlar, mevcut durum, sıradaki işler orada.
- **Çalışırken** karar alındıkça ve iş bittikçe `OTURUM-NOTLARI.md`'yi güncelle; oturum bitmeden "Şu an" ve "Sıradaki" güncel olsun (context dolarsa sonraki oturum buradan devam eder).
- Bulunan sorun / şüphe / doğrulanmamış iddia → `issues/ACIK-KONULAR.md`'ye **tek satır** + ayrıntı dosyasına link. Ayrıntı ilgili dosyada yazılır, indekste büyütülmez.

## Harita — hangi soru, hangi dosya

**İnsan rehberi (2026-10-24):** `dersler/` artık eski ders sırasıyla değil konu bazlı yazılı rehber olarak yürütülür. Alt talimat `dersler/AGENTS.md`; ayrıntılı indeks, kararlar ve ilerleme bu klasördedir. Önce uygulama amacı, borsa ve teknik temel, sonra sistem mimarisi ve stratejiler. Kullanıcı soruları/bağlamı ilgili konuya kaydedilir. İskelet, yazılmış içerik ve kullanıcı incelemesi ayrı durumlardır. Teknik ayrıntının asıl adresi mevcut KB'dir. Açık sorun araştırması otomatik başlamaz.

| Soru tipi | Bak |
|-----------|-----|
| Sistem nasıl çalışıyor, kim kimle konuşuyor, hot path ne? | `bilgi-tabani/00-genel/sistem-haritasi.md` |
| Branch'ler, ortamlar (dev/preprod/prod), müşteri hangi sürümde? | `bilgi-tabani/00-genel/branch-ve-ortamlar.md` |
| Bir terimin anlamı (ITCH, OUCH, tavan, KIE, kademe, unique_key…) | `bilgi-tabani/00-genel/sozluk.md` |
| BIST kuralı (fiyat adımı, fiyat limitleri, seanslar, açığa satış) | `bilgi-tabani/00-genel/borsa-kurallari.md` |
| Bir strateji ne yapar, parametreleri ne, hangi motorda, UI'da nerede? | `bilgi-tabani/20-stratejiler/` — önce `bilgi-tabani/20-stratejiler/README.md` (katalog) |
| Bir servisin/kütüphanenin iç yapısı | `bilgi-tabani/10-servisler/<repo>/README.md` |
| Bir verinin/emrin uçtan uca yolculuğu | `bilgi-tabani/30-akislar/` |
| Kurulum, deploy, config, açılış log'ları | `bilgi-tabani/40-operasyon/` |
| Bilinen sorunlar, şüpheli davranışlar, doğrulanmamış iddialar | `issues/ACIK-KONULAR.md` |
| Doküman çalışması nerede kaldı, hangi kararlar alındı? | `OTURUM-NOTLARI.md` |
| Bu dokümanlar nasıl güncellenir? | `_surec/guncelleme.md` |
| Dosyalar nasıl yazılır (frontmatter, kurallar)? | `_surec/yazim-kurallari.md` |

Her repo için tek satırlık görev, referans branch ve doğrulama commit'i: `manifest.yaml`.

## Dizin yapısı

```
README.md           ← bütün alanlara giriş
AGENTS.md           ← ortak agent talimatları
manifest.yaml       ← repo, branch, doğrulama commit'i ve teknik doküman yeri
OTURUM-NOTLARI.md    ← kararlar, mevcut durum ve sıradaki işler
CHANGELOG.md        ← güncelleme geçmişi
bilgi-tabani/       ← AI teknik belgeleri; 00/10/20/30/40 ve test-incelemeleri
dersler/            ← insan rehberinin Markdown kaynakları ve yayın araçları
yayinlar/           ← güncel PDF, EPUB ve HTML çıktıları
testler/            ← aktif sanity Excel'leri ve örnek dosyalar
issues/             ← açık konu indeksi ve issue taslakları
arsiv/              ← eski dersler, test yedekleri ve bitmiş çalışma dosyaları
_surec/             ← bakım kuralları, kontroller ve teknik inceleme kayıtları
tmp/                ← yalnız devam eden geçici işler (Git dışında)
outputs/            ← geçici teslim kopyaları
.tools/             ← yayın araçları
```

**Dosya yerleştirme:** Yeni dosya ilgili alanın README'sindeki düzene göre konur; köke Excel/PDF/issue bırakılmaz. Teknik test incelemeleri `bilgi-tabani/test-incelemeleri/`, kullanıcı testleri `testler/sanity/`, test kaynaklı issue taslakları `issues/sanity/` içindedir. Sanity Excel'lerine kod/repo referansı konmaz. İş bitince gerekli çalışma kanıtları `arsiv/calisma/<tarih>/` altında toplanır; arşivden otomatik görev başlatılmaz. Açık teslim dosyası taşınmaz veya üzerine yazılmaz; aktif dosyaya aktarım öncesi kullanıcının değişiklikleri karşılaştırılır.


**Tekrar yok kuralı:** Bir bilgi tek bir yerde yazılır, diğer yerler oraya link verir. Strateji mantığı `bilgi-tabani/20-stratejiler/`'de, servisin genel iç yapısı `bilgi-tabani/10-servisler/`'de. İki yerde çelişki görürsen bu bir hatadır — kullanıcıya bildir.

## Durum etiketleri

Frontmatter'daki `durum` alanı:

- `dogrulandi` — belirtilen commit'e karşı kodla doğrulandı.
- `taslak` — yazıldı ama henüz kullanıcı onayından geçmedi.
- `eski` — kaynak repo doğrulama commit'inden belirgin şekilde ilerledi; güncelleme bekliyor.
- `bos` — iskelet; henüz içerik yok.

`bos` veya `eski` bir dosyadan cevap veriyorsan bunu kullanıcıya söyle.
