---
kapsam: Belge alanlarının ayrılması, arşivleme ve taşıma doğrulaması
dogrulama: 2026-10-28
durum: taslak
---

# Klasör düzeni ve commit kontrolü

Kullanıcı, AI belgeleri, insan rehberi/yayınları, issue'lar ve sanity dosyalarını ayırmayı; işi bitmiş dosyaları silmeyi veya tek yerde toplamayı istedi. Benzersiz içerik korunarak arşivleme tercih edildi. Aktif içerik girişleri kök [README](../README.md) içindedir.

## Taşınan alanlar

| Önce | Şimdi |
|---|---|
| Kökteki `00-genel`, `10-servisler`, `20-stratejiler`, `30-akislar`, `40-operasyon` | `bilgi-tabani/` altında aynı adlarla |
| Kökteki `ACIK-KONULAR.md` | `issues/ACIK-KONULAR.md` |
| `sanity tests/` içindeki dört aktif Excel | `testler/sanity/` |
| `sanity tests/` içindeki dört teknik inceleme | `bilgi-tabani/test-incelemeleri/` |
| `sanity tests/` içindeki dört toplu issue | `issues/sanity/` |
| Kökteki iki Mate Excel'i | `testler/referanslar/mate/` |
| Altı eski Excel yedek klasörü | `arsiv/test-yedekleri/` |
| `dersler/arsiv/` | `arsiv/eski-dersler/` |
| `output/rehber/` | `yayinlar/mtrader-rehberi/` |
| `output/pdf/` ve dokuz tamamlanmış `tmp/` çalışması | `arsiv/calisma/2026-10-27/` |

39 taşıma işlemiyle 407 dosya yeni konuma alındı. Teknik belgelerin kaynak commit'leri ve doğrulama tarihleri değiştirilmedi. Mevcut yerel kullanıcı değişiklikleri korundu; Git reset/commit/push yapılmadı. Boş kalan eski `output/` ve `sanity tests/` dizinleri kaldırıldı. Eski PDF ve görsel kontroller arşivde tarihsel kanıt olarak kaldı.

## Açık Arbitraj teslim kopyası

Kullanıcı, `outputs/arbitraj-sanity-20261027/MTrader_Arbitraj_Sanity_Test.xlsx` dosyasını **şimdilik açık bırakmayı** istedi. Dosya, kilit dosyası ve klasörü taşınmadı/değiştirilmedi. Açık dosya hash için okunamadığından aktif Excel ile aynı olduğu varsayılmadı. Kapandığında önce kullanıcı değişiklikleri karşılaştırılmalı; otomatik silme veya üzerine yazma yapılmamalı. Aktif dosyanın yeni adresi [testler/sanity](../testler/sanity/README.md) altındadır.

## Bakım ve doğrulama

- Markdown bağlantıları, agent talimatları ve manifest belge yolları yeni konumlara uyarlandı. Teknik kaynak denetimi yeni `bilgi-tabani/` konumunda sürer; K numarası denetimi `issues/ACIK-KONULAR.md` dosyasına taşındı.
- Yapısal denetimde geçici klasörlerdeki junction üzerinden dış araç bağımlılıklarının tarandığı görüldü. Dizin gezintisi gizli/geçici/üretilmiş alanları ve junction/symlink hedeflerini dışlayacak şekilde düzeltildi.
- Taşınan, belge/yayın dışındaki 261 dosyanın SHA-256 değeri aynı kaldı. Buna aktif Excel'ler, Mate dosyaları, yedekler ve ara çalışma dosyaları dahildir. Klasör düzenlemesi Excel içeriklerini değiştirmedi.
- Yayın scripti üç çıktıyı `yayinlar/mtrader-rehberi/` içine üretir; ikinci aktif PDF kopyası oluşturmaz. VS Code görevlerinin komut yolu değişmedi.
- PDF/HTML/EPUB yeniden üretimi tamamlandı. Sandbox içindeki HTML üretimi kullanıcı önbelleğine erişemedi; kullanıcı izin verdiği için üretim sandbox dışında tamamlandı. PDF 56 sayfa ve önceki PDF ile çıkarılan metni aynı; EPUB paket kontrolü başarılı; 24 HTML sayfasının yerel dosya bağlantıları geçerli.
- Önceki içerik snapshot'ları, taşıma planı, hash envanteri ve kontrol sonuçları `arsiv/calisma/2026-10-27/klasor-duzeni/` içinde korunur. Eski çalışma scriptleri tarihsel yollar içerebilir; aktif araç sayılmazlar.

Bu çalışma dosya düzenlemesidir; yeni uygulama testi, kaynak repo tazelik kontrolü, issue çözümü veya kitap içeriği onayı değildir. Güncel çalışma sırası [oturum notlarında](../OTURUM-NOTLARI.md), aktif test sürümleri [sanity dizininde](../testler/sanity/README.md) tutulur.

## Commit öncesi durum

- Ana klasör taşıması tamamdır. Git'te eski konumunda silinmiş görünen 90 takipli dosyanın tamamının yeni konumda karşılığı vardır. Yeni klasörlerin de commit'e dahil edilmesi gerekir; yalnız silinmiş dosyalar seçilmemelidir.
- 28 Ekim kontrolünde bitmiş 18 geçici çalışma klasörü ve 12 eski teslim klasörü `arsiv/calisma/2026-10-28/` altına alındı. Taşınan 1.099 normal dosyanın SHA-256 değerleri aynı kaldı; junction hedefleri izlenmedi veya değiştirilmedi.
- Kullanıcının açık bırakılmasını istediği `outputs/arbitraj-sanity-20261027/` ve güncel `outputs/arbitraj-guncel-29/` taşınmadı. Aktif dört Excel'in adresi `testler/sanity/` olarak kalır.
- Ara çalışma alanları, yerel teslimler, yayın çıktıları ve araç bağımlılıkları Git dışında kalır. Excel kilit dosyaları da `.gitignore` ile dışlanır. Yeni dosya adaylarında 10 MB üzeri dosya veya yanlışlıkla eklenen araç bağımlılığı bulunmadı.
- README'lerdeki eski Arbitraj sürüm bilgisi ve eski yedek yolu düzeltildi. Sürüm/kapsam için tek giriş `testler/sanity/README.md`; kitap çıktıları için `yayinlar/README.md` kullanılır.

Commit içeriği: kök giriş/talimat dosyaları, `manifest.yaml`, `bilgi-tabani/`, `dersler/`, `issues/`, `testler/`, eski ders/test yedekleri ve `_surec/` bakım dosyaları. `yayinlar/README.md` sürümlenir; üretilmiş PDF/EPUB/HTML yereldir ve yayın scriptiyle yeniden üretilir.

Kontrol komutları: `python _surec/kontrol.py`, `git diff --check`, `git status --short`. Stage sonrasında `git diff --cached --stat` ile yeni konumların ve eski konumlardaki kaldırmaların birlikte yer aldığı görülmelidir. Bu düzenleme sırasında stage, commit veya push yapılmadı.
