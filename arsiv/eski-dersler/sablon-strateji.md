---
kapsam: Strateji derslerinde parametre, davranış, ayar değişikliği ve test kapsamı için ortak şablon
dogrulama: 2026-10-24
durum: taslak
---

# Strateji çalışma şablonu

Bu bir doldurma şablonudur; aşağıdaki boş alanlar doğrulanmış davranış sayılmaz. Teknik kaynakta eksik olan ayrıntı ders içinde uydurulmaz; kaynak kod kontrol edilerek önce ilgili teknik belgeye işlenir.

## Kimlik ve amaç

- Kullanıcı adı / route / wire türü / motor:
- Ne yapmayı amaçlıyor; hangi durumda kullanılmıyor:
- Kaynak belge ve ilgili kod sembolleri:
- Referans branch/commit; prod ve feature farkları:
- Ön koşul: veri, seans, hesap, pozisyon, emir oturumu:

## Parametre sözlüğü

| UI alanı | Wire / kod adı | Tip ve birim | UI varsayılanı / motor varsayılanı | Sınır, 0 ve kapalı değeri | Bağlı alanlar | Kaynak |
|---|---|---|---|---|---|---|
| Doldurulacak | — | TL/raw, lot, tick, ms/s açıkça yazılır | Aynı oldukları varsayılmaz | Negatif ve boş değer dahil | — | — |

Tam alan listesi teknik belgede tutulur; ders tablosu üzerinde çalışılan alanların öğretici görünümüdür. “Yüzde” alanında 5 mi 0,05 mi beklendiği; fiyat dönüşümü ve zaman dilimi açık yazılır. UI'da gizlenen alanın payload'dan silindiği varsayılmaz.

## Durum ve emir akışı

Başlangıç → çalışır/bekler → tetik → gönderim bekleniyor → kabul/ret → sıfır/kısmi/tam dolum → çıkış → yeniden giriş/durma. Gerçek durumlar ilgili stratejiye göre doldurulur.

| Önceki durum | Olay / koşul | Beklenen emir (yön, fiyat, miktar, TIF) | Sonraki durum / açık emir / pozisyon | Kanıt kaynağı |
|---|---|---|---|---|
| Doldurulacak | Eşik karşılaştırması `<` / `<=` dahil | Emir yoksa sebebi | Timer/mandal dahil | — |

## Çalışırken ayar değiştirme

| Değişen alan | Önce → sonra | O andaki pozisyon ve bekleyen emir | Hemen etkisi | Sonraki tetikte etkisi | Yeniden başlatma gerekli mi? |
|---|---|---|---|---|---|
| Doldurulacak | Tek alan değişir | Boş / kısmi / açık çıkış emri | Cancel/replace/yeni emir veya etkisiz | — | Doğrulanacak |

Mod değiştirme, start/stop, lot artırma/azaltma, fiyat limiti, eşik, süre, TP/stop açma/kapama ayrı ele alınır. “Strateji durdu” ile “bütün emirler iptal ve pozisyon kapandı” aynı kabul edilmez.

## Sayısal örnek ve test matrisi

Örnek başlangıç defteri, ayar seti ve sıralı olay dizisi yazılır. Her adımda beklenen miktar hesabı gösterilir. Sayılar eğitim verisidir; gerçek sembol/hesap kullanılmaz.

| Senaryo | Değişen koşul | Beklenen | Test türü | Gerçek sonuç / kanıt |
|---|---|---|---|---|
| Normal akış | Geçerli tetik ve yeterli miktar | Doldurulacak | Replay/entegrasyon | Çalıştırılmadı |
| Sınır | Eşik −1, eşik, eşik +1 | Ayrı beklentiler | — | Çalıştırılmadı |
| Birim | TL/raw; ms/s; fiyat bandı geçişi | — | — | Çalıştırılmadı |
| Dolum | Sıfır, kısmi, tam; birden çok fill | — | — | Çalıştırılmadı |
| Ret | Yerel ret ve borsa reti | — | — | Çalıştırılmadı |
| Değişiklik | Açık emir varken ayar/start/stop | — | — | Çalıştırılmadı |
| Kurtarma | Kopma/replay/restart; tekrar olay | — | — | Çalıştırılmadı |
| Etkileşim | Birbirini etkileyen iki ayar | — | — | Çalıştırılmadı |

Tavan/Taban'da kilit/bozulma ve timer; Arbitraj'da iki bacak, hedge oranı ve ret; Toplu Emirler'de gönderim saati, tekrar ve handoff gibi özel satırlar eklenir.

## Tasarım, mevcut davranış ve öğrenme kaydı

- Amaçlanan davranış / gözlenen uygulama farkı:
- Bağlı K numarası veya issue; test edilmemiş sınır:
- Kullanıcının kendi anlatımı ve çözdüğü örnek:
- Oturum tarihi, konuşulan sorular ve yanıtlar:
- Açık kalan soru ve bir sonraki adım:
