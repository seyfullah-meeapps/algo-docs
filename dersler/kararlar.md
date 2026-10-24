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

## Konuşmada netleşen sorular — 24 Ekim 2026

**Kullanıcı sorusu, anlamı korunarak özet:** Önce ürün amacı, borsa ve teknik temel, sonra sistem bağlantıları ve GUI/backend stratejileri şeklindeki akış uygun mu?

**Agent yanıtı:** Bu sıra kavramları somut sisteme bağlar; frontend bilgisi backend'e geçişte kullanılabilir. Mimariyi bileşen, dağıtım ve sequence şemalarına ayırmak okunabilirliği artırır. Bu bir yazım yaklaşımıdır; sistemin container eşlemesinin doğrulandığı anlamına gelmez.

**Kullanıcının devam talebi, özet:** Her alan ayrı Markdown olsun; sorular ve bağlam dosyalarda kalsın; ayrıntılı indeks oluşturulsun; farklı agent ile devamda kararlar kaybolmasın; eski ders yapısı bırakılabilir.

**Bu turdaki karşılığı:** Altı bölüm, 48 planlı konu, bölüm indeksleri, yerel agent talimatları ve ilerleme kaydı. Henüz konu anlatımı, internet araştırması, kod incelemesi veya görsel çalışması yapılmadı.

## Değişen önceki kararlar

Önceki “önce eski derslerin revizyonunu tekrar et, ardından Ders 06 ve hemen stratejiye geç” planı geçersizdir. Yeni başlangıç uygulamanın amacı, sonra borsa ve teknik ön bilgidir. Eski materyal silinmedi; yeni rehberin doğrulanmış veya tamamlanmış kısmı olarak sayılmıyor.
