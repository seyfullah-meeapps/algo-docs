---
kapsam: Frontend geliştiriciliğinden proje yönetimine geçen okuyucu için ders indeksi ve öğrenme rotası
dogrulama: 2026-10-24
durum: taslak
---

# Dersler ve öğrenme rotası

Amaç, projeyi temelden öğrenip bir bildirimin hangi bileşene ait olduğunu ayırt edebilmek; beklenen davranışı tanımlamak, test etmek, kanıtıyla issue açmak ve doğru sorumluluğa yönlendirmek. Frontend bilgisi başlangıç noktasıdır. C++ geliştirme uzmanlığı bütün derslerin ön koşulu değildir.

Bu klasör insan için eğitim katmanıdır. Teknik doğruluk kaynağı kod, ayrıntıların tek adresi mevcut bilgi tabanıdır. Derslerde açıklama ve örnek bulunur; bütün parametre sözleşmeleri tekrar kopyalanmaz. Belgeler taslaktır. `dogrulama` bu aktarımın tarihidir; kaynak kodun bugün yeniden doğrulandığı anlamına gelmez. Kaynak sürümleri bağlantılı teknik belgelerde ve [manifestte](../manifest.yaml) bulunur.

## Nerede kaldık?

24 Ekim 2026'da eski `meeapps-ai/dersler` içindeki yedi kayıt okundu, ders numaraları korunarak revize edildi. Eski çalışma listesi referans alındı; eski repo değiştirilmedi. Ders kaydının bulunması, okuyucunun konuyu tamamladığı veya yeni revizyonu onayladığı anlamına gelmez. Henüz yeni bir ders oturumu yapılmadı.

**İlk adım:** [Aktarım ve düzeltme notlarını](aktarim-notlari.md) birlikte gözden geçirmek; sonra aşağıdaki kısa tekrar sorularıyla başlangıç seviyesini belirlemek. **İlk yeni ders:** Ders 06 — ekrandaki bir HFT ayarının motora ve emir dönüşüne yolculuğu.

## Eski derslerden taşınan kayıtlar

| No | Konu | Durum |
|---|---|---|
| 00 | [gRPC ve servis iletişimi](ders-00-grpc.md) | Revize edildi; birlikte tekrar bekliyor |
| 01 | [Borsa, emir ve emir defteri](ders-01-borsa-emir-emir-defteri.md) | Revize edildi; birlikte tekrar bekliyor |
| 02 | [Fiyat adımı, limitler ve emir yaşam döngüsü](ders-02-fiyat-adimi-tavan-taban-emir-yasam-dongusu.md) | Revize edildi; birlikte tekrar bekliyor |
| 03 | [Seanslar, müzayede ve pozisyon](ders-03-seanslar-muzayede-pozisyon-aciga-satis.md) | Revize edildi; birlikte tekrar bekliyor |
| 03b | [Uptick, bait ve brüt takas](ders-03b-uptick-bait-brut-takas.md) | Revize edildi; tarihsel kural iddiaları taşınmadı |
| 04 | [Varant, dayanak ve HFT](ders-04-varant-ve-hft.md) | Revize edildi; birlikte tekrar bekliyor |
| 05 | [Sistemin haritası](ders-05-sistemin-haritasi.md) | Revize edildi; birlikte tekrar bekliyor |

## Bundan sonraki sıra

Önce temel kavramların kısa tekrarı ve ortak test dili; sonra **HFT → Arbitraj → Toplu Emirler → Tavan → Taban**. BYF en son. Ağ ve C++ ayrıntıları ilgili stratejinin ihtiyacı kadar açılır; bütün SDK'ların bitmesi strateji derslerine başlama şartı değildir.

| Sıra | Ders / modül | Ortaya çıkacak somut çıktı | Ana kaynak |
|---|---|---|---|
| 06 | UI'dan motora: HFT başlatma, ayar, snapshot, emir dönüşü | Bir komut ve bir emir için uçtan uca izleme çizelgesi | [Strateji başlatma](../30-akislar/strateji-baslatma.md), [emir dönüşü](../30-akislar/emir-donusu.md) |
| 07 | PM için test ve issue temeli | Ortam/commit içeren bir test kaydı ve örnek issue | [Çalışma düzeni](calisma-duzeni.md) |
| 08–10 | HFT Classic: modlar; tetik/lot; TP/stop/second rule; ayar değişimi | Parametre sözlüğü, durum geçişleri, sınır ve regresyon matrisi | [HFT](../20-stratejiler/hft-classic.md) |
| 11–13 | Arbitraj: spot–vadeli ilişki; giriş/çıkış; hedge ve kısmi dolum | İki bacak için miktar/fiyat hesabı ve tek bacak açık kalma senaryoları | [Arbitraj](../20-stratejiler/arbitraj.md), [AlgoProd emri](../30-akislar/algoprod-emri.md) |
| 14–15 | Toplu Emirler: sabah/açılış/akşam/YİP; zamanlama ve handoff | Kayıt ile gönderim ayrımı, saat ve tekrar testleri, replay kontrolü | [Sabah emri ve handoff](../30-akislar/sabah-emri-ve-handoff.md) |
| 16–17 | Tavan: giriş, erime, çıkış, yeniden kapanma | Eşik altı/eşit/üstü ve bekleyen emirli ayar değişikliği matrisi | [Tavan](../20-stratejiler/tavan.md) |
| 18–19 | Taban: giriş, kısmi IOC, satış, stop ve timer | Sıfır/kısmi/tam dolum ve kapanmayan pozisyon senaryoları | [Taban](../20-stratejiler/taban.md) |
| 20 | Kopma, kurtarma ve sabah operasyonu | Katmana göre belirti/kanıt tablosu; release kontrol listesi | [Kopma ve kurtarma](../30-akislar/kopma-ve-kurtarma.md), [operasyon](../40-operasyon/README.md) |
| 21–23 | Teorik Fiyat, Varant, Varant Toplu | Her biri için aynı davranış ve test dosyası | [Strateji kataloğu](../20-stratejiler/README.md) |
| 24 | VWAP | Hacme göre yürütme ve tamamlanma kontrolü | [VWAP](../20-stratejiler/vwap.md) |
| 25 | BYF / Fon Takibi | Sepet, fiyat ve emir ilişkisi; en düşük öncelik | [Fon takibi](../20-stratejiler/fon-takibi.md) |
| 26 | Kapanış uygulaması ve yeni gelen rehberi | Bildirimden teste, issue'ya, doğrulamaya kadar örnek çalışma | Önceki derslerin onaylanan notları |

Bu satırlar plan, henüz yazılmış veya işlenmiş dersler değildir. Bir modül gerektiğinde bölünebilir. Toplu Emirler (`collective-orders`) ile Varant Toplu (`bulk-warrant`) farklı konulardır; öncelik sırasındaki üçüncü konu **Toplu Emirler** olarak alınmıştır.

## Her stratejide cevaplayacağımız sorular

1. Hangi ürün, hesap, mod ve seans için çalışıyor? Başlamadan hangi veriler hazır olmalı?
2. UI alanının wire adı, tipi, birimi, varsayılanı ve geçerli sınırları ne?
3. Hangi olay, hangi koşulla hangi yönde/fiyatta/miktarda emir doğuruyor?
4. Kabul, ret, sıfır/kısmi/tam gerçekleşme ve iptal sırasında durum nasıl değişiyor?
5. Parametre çalışırken değişirse mevcut emir, pozisyon ve timer ne oluyor? Durdurma neyi yapıyor?
6. Beklenen davranışla bilinen uygulama farkı ne? Development ve prod farkı var mı?
7. Bunu hangi veriyle, hangi ortamda ve hangi kanıtla test edebiliriz?

Ortak format: [strateji çalışma şablonu](sablon-strateji.md). Parametre kombinasyonlarının tümünü körlemesine denemek yerine temel akış, tek alan değişimi, sınırlar ve birbirini etkileyen alanlar ayrı senaryolar olur.

## Birlikte başlarken kısa tekrar

- REST isteği başarılı döndü; emir BIST'te kabul edilmiş sayılır mı?
- 1.000 lot IOC emrinin 300 lotu doldu. Açık emir ve pozisyon açısından ne kaldı?
- UI defteri güncel, HFT emir vermiyor. Aynı veri ve aynı bağlantıyı kullandıklarını varsayabilir miyiz?
- “Stop kapalı ama satış geldi” bildiriminde ilk hangi ayarları ve olayları isteriz?

Cevaplar ders oturumunda konuşulup ilgili dersin oturum kaydına yazılacak. Kullanıcı yanıtları önceden doldurulmaz.
