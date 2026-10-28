---
kapsam: Ders notu, öğrenme takibi, test kanıtı, issue ve görev yönlendirme düzeni
dogrulama: 2026-10-24
durum: taslak
---

# Dersleri nasıl tutacağız?

Her dersin başında amaç, ön koşul ve teknik kaynaklar bulunur. Ana metin konu anlatımıdır. Sonundaki **Oturum kaydı** yalnız gerçekten konuşulan soruları, kullanıcının açıklamalarını ve birlikte alınan kararları taşır. Önceden hazırlanmış anlatım “konu işlendi” diye kaydedilmez.

Bir derse devam edince aynı dosyaya tarihli oturum eklenir: konuşulan konu, soru/yanıt, netleşen kavram, açık kalan nokta, alıştırma sonucu ve sonraki adım. Yanlış bir açıklama düzeltilir; önemli değişiklik kısaca not edilir. Uzayan oturumlar ayrı dosyaya ayrılıp dersten bağlanır. Hassas değerler maskelenir.

İlerleme durumları: **planlandı → hazırlandı → konuşuldu → uygulandı → tekrar tamamlandı**. Bu öğrenme durumudur; frontmatter'daki `taslak/dogrulandi` teknik belge durumundan ayrıdır. Ders 00–05 ve 03b yalnız eski kayıtları bulunmuş, revize edilmiş durumdadır.

## Test kaydı

Her test şu bilgileri içermeli:

| Alan | Yazılacak bilgi |
|---|---|
| Kimlik ve amaç | Örn. `HFT-TP-001`; sınanan tek davranış |
| Sürüm | UI, motor, gateway/SDK için ilgili branch/commit; biliniyorsa binary sürümü |
| Ortam | Test/replay/preprod; config farkları; saat dilimi |
| Ön koşul | Hesap, enstrüman, seans, bağlantı/handoff, başlangıç pozisyonu ve açık emirler |
| Ayarlar | UI değerleri + gönderilen payload; fiyat ve süre birimleri |
| Girdi ve adımlar | Başlangıç defteri ve sıralı piyasa/emir olayları; değişen tek ayar |
| Beklenen | Gönderilecek veya gönderilmeyecek emir; yön/fiyat/lot/TIF; sonraki durum |
| Gözlenen | Gerçek olay dizisi, emir kimlikleri, zaman damgaları |
| Kanıt | Maskeli payload/log/replay dosyası; ekran görüntüsü destekleyici olabilir |
| Sonuç | Geçti / kaldı / koşul oluşmadı / bloke; bağlı issue ve tekrar sonucu |

Beklenti bir dokümana veya koda dayanmalı. Beklenen davranış belirsizse önce ürün kararı sorusu yazılır; keyfî bir beklentiyle bug ilan edilmez. Statik kod incelemesi, yerel simülasyon ve uçtan uca test ayrı kanıtlardır. Emir üreten testin ortamı ve izni belirlenmeden canlı işlem yapılmaz.

## Issue kaydı ve görev atama

Issue başlığı tetikleyiciyi ve sonucu söyler: “Pozisyonsuz HFT'de stop kapatıldıktan sonra … koşulunda … oluyor.” Gövde: etki, sürüm/ortam, tekrar adımları, beklenen/gözlenen, kanıt, tekrar sıklığı ve kabul kriteri. Parola, token, gerçek hesap veya müşteri bilgisi eklenmez.

Severity etkiyi anlatır (ör. yanlış miktarlı emir, açık pozisyon, yalnız görünüm). Priority ise etki, maruz kalan kullanıcı, sıklık, geçici çözüm ve sürüm takvimine göre iş sırasını anlatır. Eğitimdeki strateji sırası otomatik issue önceliği değildir.

| Bulgudaki sınır | İlk inceleme sorumluluğu |
|---|---|
| UI değeri ile payload farklı | Frontend |
| Payload doğru; hub yanlış motora/yanlış alanla yönlendiriyor | trade-data-app/backend |
| Motor girdisi doğru; emir kararı veya state yanlış | İlgili HFT/AlgoProd motor geliştiricisi |
| Emir doğru; SDK callback/token/replay tutarsız | SDK/gateway geliştiricisi |
| Sürüm, config, oturum, saat veya servis hazırlığı uyuşmuyor | Operasyon ve ilgili servis geliştiricisi |

Bu tablo başlangıç yönlendirmesidir; kişi adı ve ekip kapasitesi bilinmeden gerçek kişiye atama yapılmaz. Birden fazla katman etkileniyorsa bir ana sorumlu ve bağlı işler belirlenir. Kabul kriteri, düzeltmeden sonra hangi aynı senaryonun hangi çıktıyla geçeceğini belirtir. Kapanış için düzeltme sürümü, tekrar testi ve gereken regresyon kanıtı kaydedilir.

Yeni teknik şüphe bulunursa [ACIK-KONULAR](../../issues/ACIK-KONULAR.md) indeksine tek satır ve ayrıntı bağlantısı eklenir. Mevcut K numarası varsa ona bağlanılır. Eğitim sorusu tek başına yeni bug kaydı değildir. Bu klasörü oluşturmak yeni sorun araştırması başlatmaz.

## Rehbere dönüşüm

Rota sonunda konuşma kayıtlarından onaylanan açıklamalar ve tekrarlanabilir örnekler seçilir. Teknik ayrıntılar yine mevcut kaynağa bağlanır. Yeni gelen okuyucu her modülde kavramı açıklayabilmeli, örneği çözebilmeli ve örnek bir test/issue üretebilmeli. Yazılı rehberin biçimi o aşamada seçilir; bugünden ikinci bir teknik kaynak üretilmez.
