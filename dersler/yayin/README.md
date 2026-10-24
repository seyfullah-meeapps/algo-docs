---
kapsam: Markdown rehberinden A4 PDF, HTML ve EPUB üretme, okuma ve canlı revizyon düzeni
dogrulama: 2026-10-24
durum: taslak
---

# Okuma, revizyon ve kitap çıktısı

Bu bilgisayarda Python ve proje içine taşınabilir kurulmuş Quarto 1.10.18 hazır. Zorunlu ek indirme yok. Araç `.tools/` altında; sistem PATH ayarı değiştirilmedi. PDF, Quarto'nun beraberinde gelen Typst motoruyla üretilir; ayrıca LaTeX kurulumu gerekmez. İstersen VS Code'un resmi Quarto uzantısını ekleyebilirsin, fakat aşağıdaki görevler için zorunlu değildir.

## En kısa kullanım

1. VS Code'da repo klasörünü aç.
2. **Ctrl+Shift+B**: “Rehber: PDF + HTML + EPUB üret” görevini çalıştırır.
3. `output/pdf/meeapps-rehber.pdf` dosyasını bir PDF okuyucuda aç. Kitabın adı **MTrader — Algoritmik İşlem Botu**; dosya adı mevcut okuma bağlantılarını korumak için aynı kaldı. Gerçek A4 sayfaları ve içindekiler burada görünür.
4. Değişiklikleri kaynak konu `.md` dosyasında yap veya değiştirmek istediğin yeri sohbette belirt.
5. Yeniden **Ctrl+Shift+B** yap. Aynı dosya adlarıyla güncel çıktılar üretilir.

PDF dosyası okuyucu tarafından kilitlenirse kapatıp tekrar üret. Okuyucu dosya değişince otomatik yenilemiyorsa yeniden aç/yenile. Kullanıcı düzenlemeleri bir sonraki çalışma sırasında okunur; mevcut değişiklikler ezilmez.

## Kaydettiğimde otomatik yenilensin

**Terminal → Run Task / Görevi Çalıştır** menüsünden:

| Görev | Ne yapar? |
|---|---|
| Rehber: PDF + HTML + EPUB üret | Üç çıktıyı bir kere üretir |
| Rehber: A4 PDF değişikliklerini izle | Kaynak MD veya yayın ayarı değişince PDF'yi yeniden üretir; PDF okuyucuda izlenir |
| Rehber: Canlı tarayıcı önizlemesi | Yerel HTML önizlemesini başlatır; MD kaydedilince sayfa yenilenir |

Canlı önizleme için görev başladıktan sonra tarayıcıda `http://localhost:8765` açılır. Bu yerel önizlemedir; dışarı yayınlama değildir. HTML akıcı ekran görünümüdür; PDF'deki sabit A4 sayfa kırılımları için PDF görevini kullan.

İzleme/önizleme terminali açık kalır; durdurmak için **Ctrl+C**. Yeni bir kitap çıktısı almak için tek seferlik üretim görevini çalıştır. Canlı HTML oturumu son PDF/EPUB dosyalarını kendi başına yenilemez.

## Terminal komutları

Repo kökünde:

```powershell
python dersler/yayin/uret.py --format all
python dersler/yayin/uret.py --format pdf --watch
python dersler/yayin/uret.py --preview
python dersler/yayin/uret.py --format epub
```

Çıktılar:

- `output/pdf/meeapps-rehber.pdf`: A4, 20 mm kenar boşluğu, Arial 10,25 pt, sayfa numarası, logolu kapak ve otomatik içindekiler.
- `output/rehber/index.html`: yerel HTML kitabının giriş sayfası. Diğer HTML dosyaları ve `site_libs` klasörüyle birlikte kullanılır.
- `output/rehber/meeapps-rehber.epub`: ekran/yazı boyutuna göre akan e-kitap. PDF ile aynı sayfa sayısı beklenmez. EPUB uyumlu bir okuyucu gerekir; PDF okurken gerekli değildir.

Güncel ilk bölüm revizyonu 7 A4 sayfadır; bu sabit hedef değildir. Bölüm/metin değişince sayfa sayısı ve içindekiler yeniden hesaplanır. Kapak ve içindekiler toplam sayfaya dahildir. Kullanıcının kaldırdığı “Okumaya başlamadan” sayfası artık üretilmez; HTML'nin giriş sayfası ilk konunun kendisidir.

## Neyi nerede düzenleyeceğiz?

| Düzenleme | Kaynak |
|---|---|
| Metin, örnek ve parametre açıklaması | İlgili konu `.md` dosyası |
| Kitaba girecek konu sırası, başlık, sürüm | [kitap.json](kitap.json) |
| A4 ölçüsü, yazı tipi/boyutu, format seçenekleri | [_quarto.yml](_quarto.yml) |
| PDF kapağı, başlık/tablo stili | [typst-show.typ](typst-show.typ) |
| HTML/EPUB stili | [styles.css](styles.css) |
| EPUB göreli yazı boyutu | [epub.css](epub.css) |
| Frontend logo/renk kaynakları ve tipografi kararları | [marka.md](marka.md) |
| İlk konudaki kavramsal şema | [akisin-ozeti.svg](akisin-ozeti.svg) |

Yeni yazılan konu otomatik olarak kitaba girmez: okunabilir duruma gelince `kitap.json` içindeki `chapters` listesine eklenir. `bos` ve `eski` durumundaki dosyalar üretimde reddedilir; taslak dosya kullanılabilir. Böylece 47 boş konu ilk örnek kitabı doldurmaz.

Üretim, kaynakları değiştirmeden `.build/` içinde geçici Quarto dosyaları hazırlar; canlı önizleme ayrı `.preview/` klasörünü kullanır. Frontmatter ve süreç bölümleri (“Sorularımız ve netleşen noktalar”, “Kaynaklar ve doğrulama”, “Devam notu”) mevcut okuma sürümüne alınmaz; kaynak MD'de kalır. Geçici `.qmd` veya çıktı PDF'sini düzenleme; tekrar üretimde üzerine yazılır. Aynı anda birden fazla PDF/tüm format üretimi başlatma.

Kitaba dahil konular arasındaki bağlantılar çıktı bölümüne çevrilir. Kitaba alınmamış yerel kaynak bağlantıları şimdilik düz metin olarak kalır; bozuk dosya bağlantısı üretilmez. Teknik kaynak kayıtları Markdown'da korunur. İleride kaynakça/soru eki eklemek ayrı yayın tercihi olacaktır.

İlk Mermaid akışı, üç formatta aynı SVG ile gösterilir. Kaynak Mermaid değişirse imza kontrolü üretimi durdurur; şema ve eşleşmesi güncellenmeden eski görsel sessizce kullanılmaz. Yeni Mermaid şemaları için de yayın görseli eklenmelidir; şu an her Mermaid türü için otomatik dönüştürücü kurulmadı.

## Başka bilgisayarda kurulum

Python 3 ve Quarto gerekir. Quarto sistemde kuruluysa üretim onu da bulur. Windows'ta aynı taşınabilir sürümü kurmak için:

```powershell
powershell -ExecutionPolicy Bypass -File dersler/yayin/kur.ps1
python dersler/yayin/uret.py --format all
```

Bu komut yalnız çağrı için script çalıştırma ilkesini değiştirir; kalıcı sistem ayarı değiştirmez. Kurulum resmi Windows ZIP paketini indirir, SHA-256 doğrular ve repo içindeki `.tools/` klasörüne açar. İlk kullanımda Quarto standart kullanıcı önbelleği oluşturabilir. İnternet kitap metnini yüklemek için kullanılmaz.

Araçlar, çıktılar ve geçici dosyalar Git'e alınmaz. Yayın ayarları, üretim/kurulum scriptleri ve VS Code görevleri Git'te saklanır. Yeni bilgisayarda çıktı yeniden üretilir.

## Doğrulama

İlk PDF'nin beş sayfası görüntülenerek kontrol edildi; sayfa boyutları A4, Türkçe metin ve gömülü fontlar, sayfa sınırları ve süreç notlarının çıkarılması kontrol edildi. EPUB ZIP/mimetype yapısı kontrol edildi; farklı EPUB okuyucularındaki görünüm henüz denenmedi. Yeni anlamlı tasarım değişikliğinde PDF yeniden görsel kontrol edilir.

Resmi kaynaklar: [Quarto kitapları](https://quarto.org/docs/books/), [Typst seçenekleri](https://quarto.org/docs/reference/formats/typst.html), [Quarto indirme](https://quarto.org/docs/download/). Erişim: 24 Ekim 2026. Bunlar çıktı aracının kaynaklarıdır; uygulamanın işleyişini doğrulamaz.
