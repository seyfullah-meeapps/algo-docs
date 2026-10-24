---
kapsam: İnsan rehberinin amacı, kapsamı, yapısı ve kullanıcıyla alınan kalıcı kararlar
dogrulama: 2026-10-24
durum: taslak
---

# Rehbere özel kararlar

Bu dosya genel yapı kararlarının tek adresidir. Konu soruları ilgili konu dosyalarında, tamamlanan iş ve sonraki adım [ilerleme kaydında](ilerleme.md) bulunur. Tarihler Europe/Istanbul bağlamındadır.

## Kullanıcı bağlamı — 24 Ekim 2026

Kullanıcı frontend'i yazdı; diğer katmanlardaki bilgisi sınırlı. PM rolünde problem tespiti, test, issue düzenleme ve görev atamadan sorumlu. Projeyi temelden öğrenmek ve sonradan/yeni gelenlere kullanılabilir bir yol haritası bırakmak istiyor. Eski `meeapps-ai` dersleri başlangıç malzemesiydi; artık önceki ders düzeninden vazgeçilebileceğini açıkça belirtti.

## Geçerli kararlar

24 Ekim 2026 ek kararı: Kredili işlemler, pozisyon/bakiye konusunda ayrı başlıkta ele alınacak; vadeli girişinde yalnız kısa ayrım bulunacak. Kullanıcının anladığını belirttiği sade, tek sözleşmeli nakit/teminat örneği korunsun.

| Kimlik | Karar | Dayanak |
|---|---|---|
| R-01 | Ders dizisi yerine konu bazlı, ileride yazılı dokümana dönüşebilecek rehber | Kullanıcının son talebi |
| R-02 | Sıra: kısa uygulama açıklaması → borsa temelleri → teknik temeller → bizim sistemimiz → stratejiler; sonunda test/PM uygulaması | Kullanıcının önerdiği akış; test/PM bölümü önceki amacı tamamlayan düzenleme |
| R-03 | Önce ayrıntılı indeks; sonra içerikleri sırayla doldurma | Kullanıcının açık talebi; bu tur anlatım yazımı değil yapı turu |
| R-04 | Her konu ayrı `.md`; büyüyen başlık alt dosyalara bölünür | Kullanıcının açık talebi |
| R-05 | Kullanıcının bağlamı, sorusu ve konuşulan açıklamalar ilgili konuya tarihli eklenir | Kullanıcının açık talebi; sorular ana anlatımı da iyileştirecek |
| R-06 | Kararlar, yazım kuralları ve ilerleme rehberin içinde kalıcı tutulur | Başka agent/sohbet ile kayıpsız devam isteği |
| R-07 | Strateji sırası HFT → Arbitraj → Toplu Emirler → Tavan → Taban; BYF en düşük öncelik | İlk kullanıcı talebi geçerli; Toplu Emirler ve Varant Toplu ayrı |
| R-08 | GUI ve backend aynı strateji anlatımında bağlanır; parametre ve değişiklik sonucu açıklanır | İlk ve ikinci kullanıcı talepleri |
| R-09 | Borsa ve teknik kaynaklar gerektiğinde internetten güncel doğrulanır; proje davranışı koddan teyit edilir | Kullanıcı izin ve beklentisi; doğrulamanın türü açık yazılır |
| R-10 | Gerçek ekran, temsili SVG ve kullanıcı tarafından eklenecek görsel birbirinden ayrılır | Kullanıcının görsel seçenekleri; hiçbiri bu tur üretilmedi |
| R-11 | `dersler/` adı şimdilik korunur; eski 11 dosya `arsiv/` altındadır | Geri dönüş ve mevcut bağlantıları koruyan uygulama tercihi; arşiv güncel plan değildir |
| R-12 | Kullanıcı okudukça sorularla metni geliştireceğiz; yazılanı okunmuş/onaylanmış saymayacağız | Kullanıcının “sen yazdıkça okurum” talebi |
| R-13 | İlk ve ana okuyucu kullanıcıdır; rehber sonrasında görevi devralacak ve ekibe katılacak kişiler için kritik şirket içi bilgi aktarım kaynağı olacak | Kullanıcının okuyucu sorusuna açık yanıtı |
| R-14 | Rehber bir süre ana çalışma konusu; yazıma başlamadan açık tercihler tek tek netleştirilecek | Kullanıcının önceki talebi; henüz cevaplanmamış tercihler kararlaştırılmış sayılmaz |
| R-15 | Ana metin çalışma mantığı, parametreler ve beklenen davranışa odaklanır; gerektiğinde kısa açıklamalı kod örnekleri verilir. Dosya/fonksiyon referansları ve daha derin C++ ayrıntıları ayrı teknik ayrıntı bölümünde tutulur; satır satır kod anlatımı hedeflenmez | Kullanıcı önerilen derinliği kabul etti: “çok ayrıntı olmasın” |
| R-16 | Mevcut hatalar rehberde anlatılmaz; sorun takibi teknik bilgi tabanı/issue tarafında kalır. Düzeltme doğrulandıktan sonra etkilenen rehber anlatımı, örnek, GUI/parametre, şema ve test beklentisi güncellenir | Kullanıcının açık tercihi; düzelmemiş davranış çalışıyormuş gibi yazılmaz |
| R-17 | Markdown kaynakları korunarak Quarto ile A4 PDF, HTML ve EPUB üretilir. A4 PDF'de otomatik içindekiler/sayfa numarası bulunur; EPUB akışkandır. Kaydetme sonrası izleme ve revizyon için yerel görevler kullanılır | Kullanıcı örnek çıktı ve sürdürülebilir üretim kurulumunu kabul etti |
| R-18 | Kitap listesi açıkça yönetilir; boş konular, karar/ilerleme dosyaları ve süreç bölümleri okuma çıktısına alınmaz. Bunlar kaynak MD'de kalır | Önerilen okuma/yazım ayrımının uygulanması; ilk örnek yalnız yazılmış konuyu içerir |
| R-19 | Rehber frontend logosu ve renk tokenlarını kullanır; metin küçültülüp başlık/paragraf boşlukları artırılır. Marka kaynağı ve ölçüler `yayin/marka.md` içinde tutulur | Kullanıcı ilk tasarımda yazıları büyük ve başlık aralarını yakın buldu; bu tur revize edildi, henüz yeni tasarım onayı yok |
| R-20 | Beyaz kapak/yeşil logo alanı/küçük ok uçları görsel olarak uygun bulundu. İlk bölümün iki konusu yazılıp birlikte okumaya sunulacak; kullanıcı revizyonlarından önce ikinci bölüme geçilmeyecek | Kullanıcının “böyle çok güzel oldu … ilk bölümü bitirelim ardından okuyup … revizeler vereyim” talebi; içerik onayı sayılmaz |
| R-21 | Ürün adı MTrader, şirket MeeApps; ürün algoritmik işlem botu olarak tanımlanır. Müşteriler aracı kurumlar; günlük kullanıcılar onların çalışanlarıdır. MeeApps düzenli trade yapmaz, ürünü geliştirme/test için kullanır | Kullanıcının açık kimlik ve rol düzeltmesi; tek kaynak `00-genel/urun-ve-gelistirme-sureci.md` |
| R-22 | Özellik detayları/senaryolar ve etki alanları → görev dağılımı → geliştirici ön testi → test ortamında izleme/düzeltme → anlaşılmış traderlarla düşük lot preprod → kararlılık sonrası yüksek lot → müşterilere aktarım | Kullanıcının açıkladığı iş süreci; lot sınırı/süre/onay kişisi belirtilmedi, uydurulmaz |
| R-24 | Rehber yalnız MTrader dokümanıdır; şirket anlatımı tekrarlanmaz. Genel test çerçevesi stratejiye özgü parametreler, koşullar ve beklenen sonuçlara dayanır | MeeApps birden fazla ürün geliştiriyor; kullanıcı tek emir örneğine dayanan test metninin genelleştirilmesini istedi |
| R-23 | “Okumaya başlamadan” sayfası kaldırılır; ana başlıklar sayı ve metin yerine bölüm rozeti ve marka zeminli şeritle zenginleştirilir | Kullanıcının içerik ve sayfa tasarımı revizyonu |

## Konuşmada netleşen sorular — 24 Ekim 2026

**Kullanıcı sorusu, anlamı korunarak özet:** Önce ürün amacı, borsa ve teknik temel, sonra sistem bağlantıları ve GUI/backend stratejileri şeklindeki akış uygun mu?

**Agent yanıtı:** Bu sıra kavramları somut sisteme bağlar; frontend bilgisi backend'e geçişte kullanılabilir. Mimariyi bileşen, dağıtım ve sequence şemalarına ayırmak okunabilirliği artırır. Bu bir yazım yaklaşımıdır; sistemin container eşlemesinin doğrulandığı anlamına gelmez.

**Kullanıcının devam talebi, özet:** Her alan ayrı Markdown olsun; sorular ve bağlam dosyalarda kalsın; ayrıntılı indeks oluşturulsun; farklı agent ile devamda kararlar kaybolmasın; eski ders yapısı bırakılabilir.

**Bu turdaki karşılığı:** Altı bölüm, 48 planlı konu, bölüm indeksleri, yerel agent talimatları ve ilerleme kaydı. Henüz konu anlatımı, internet araştırması, kod incelemesi veya görsel çalışması yapılmadı.

## Yazım öncesi netleştirme — 24 Ekim 2026

**Soru 1 — Ana okuyucu:** Rehber kimin bilgi düzeyine göre yazılacak?

**Kullanıcı yanıtı, anlamı korunmuş özet:** İlk ve ana okuyucu kendisi olacak. Sonrasında yerine gelecek veya ekibe katılacak arkadaşlar da kullanacak; şirket içi bilgi aktarımı için kritik bir doküman olacak.

**Yazıma etkisi:** Önce kullanıcının öğrenmesini destekleyen açıklamalar verilir. Metin yalnız mevcut sohbeti bilen kişiye hitap etmez; ürün, roller ve varsayımlar sonraki okuyucuya da yeterli bağlam sağlar.

**Soru 2 — Teknik derinlik:** Ana anlatımda mantık ve davranış, gerektiğinde kısa açıklamalı kod; derin ayrıntılar ayrı bölümde olsun mu?

**Kullanıcı yanıtı:** “çok ayrıntı olmasın ya önerdiğin gibi olsun”

**Sonuç:** R-15 kabul edildi. Bu tercih, iddiaları koddan doğrulama gereğini azaltmaz; okuyucuya sunulan ayrıntı seviyesini belirler.

**Soru 3 — Mevcut hatalar:** İlgili konuda kısa bir dikkat notuyla gösterilsin mi?

**Kullanıcı yanıtı:** “mevcut hatalardan dökümanda bahsetmeyelim. ama bunları süreçte bir yandan çözeceğiz onun için çözdükten sonra da dökümanı güncellemeyi unutmayalım”

**Sonuç:** Dikkat notu önerisi kabul edilmedi. R-16 geçerli. Hatalar ve düzeltme kanıtları rehberin okuyucu anlatımına taşınmaz. Henüz düzelmeyen davranış için hedef tasarım gerçek davranış diye sunulmaz; ilgili anlatım gerekiyorsa yazım takibinde bekletilir. Sorunların süreçte ele alınacağı kaydedildi; bu yanıt bütün açık sorunlarda otomatik düzeltme veya deploy başlatma talebi sayılmaz.

**Devam:** Okuyucu, teknik derinlik ve hataların kapsamı netleşti. Yazıma başlamak için başka zorunlu tercih yok; konuya özel eksikler ilgili bölümü yazarken sorulacak.

## Önceki planın değişimi

Önceki “önce eski derslerin revizyonunu tekrar et, ardından Ders 06 ve hemen stratejiye geç” planı geçersizdir. Yeni başlangıç uygulamanın amacı, sonra borsa ve teknik ön bilgidir. Eski materyal silinmedi; yeni rehberin doğrulanmış veya tamamlanmış kısmı olarak sayılmıyor.
