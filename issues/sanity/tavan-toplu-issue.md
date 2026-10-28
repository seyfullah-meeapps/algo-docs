---
kapsam: Tavan sanity hazırlığında bulunan açık kaynak adayları ve ürün/ortam teyitleri
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
dogrulama: 2026-10-26
durum: taslak
---

# Tavan — kaynak incelemesi bulguları

Yeni GUI ve motor kaynakları incelendi; manuel test yapılmadı. Bu metin kesin canlı hata listesi değildir. Excel satırları ve tam kaynak yolları [inceleme kaydında](../../bilgi-tabani/test-incelemeleri/tavan-inceleme-2026-10-26.md). Çözüm önerisi veya ürün adına kabul ölçütü içermez; uzak issue açılmadı.

## 1. Tolerans kapalı değerinin uyuşmaması

**K-254 · R01 · P19.** GUI `encodeMaxPriceSettings` tolerans kutusu kapalıyken `Cancel_Tolarence=0` üretir. `HftMaxPrice::openPosition`, `cancelNumberForTolerance >= cancelTolarence && cancelTolarence != -1` koşuluyla durur. Başlangıç sayacı 0 iken diğer giriş şartları sağlandığında bu koşul ilk emri engelleyebilir. Motorun sınırsız istisnası −1; GUI'nin kapalı değeriyle eşleşmez. Kaynakta doğrulandı, GUI→wire→motor canlı yeniden üretim yok.

## 2. Yeni strateji saatleri ve sınır kapsamı

**K-03 · R02 · P07/P08.** `MaxPriceCommand::getDefaultSettings` 600/1200 yazar; parser alan yokken 36000/64800 kullanır. GUI mevcut pozitif değeri koruyabilir. Modalda geçerli saat kaydı yapılmadan başlatmada yanlış pencere taşınması adayı sürer; yeni stratejinin dağıtılmış DB/snapshot zinciri sınanmadı.

**K-238 · R06.** `processItchEventTimed` snapshot dışındaki bütün olayları açık saat aralığıyla filtreler. Start/End eşitliği dışarıdadır; timer ve koruyucu defter olayları da saat dışında elenir. Bitişte otomatik pozisyon kapatma garantisi yoktur; hedef ürün politikası kararı gerekir.

**R17.** Form `readMaxPriceStopTime` Stop_Time'ı, payload mevcut End_Time'ı öncelikli seçer. İki alias çelişkiliyse farklı saat görülebilir/gönderilebilir. Motor bazı Long giriş alanlarını snapshot'ta Int paketler; yeni GUI yeniden tipler. Çakışan fixture ve round-trip testi gerekir, mevcut canlı yanlış gönderim iddiası değildir.

## 3. Header girişinde tekrar beklemesi

**K-255 · R03 · P18.** `shouldEnterPosition` `tavanMeltedTimestamp + Open_Position_Second_Rule×100ms` koşulunu denetler. `HEADER_CHANGED` dalı ilk kilitlenmede doğrudan `openPosition` çağırır; bu fonksiyonda aynı süre kontrolü yoktur. Tavan bozulduktan hemen sonra yeniden kilitlenme, level yolundaki beklemeyi atlayabilir. Diğer giriş kapıları sürer. Gerçek zamanlı yeniden üretim yapılmadı.

## 4. TL ve lot çevriminin kapsamı

**K-256 · R04/R05 · P04.** GUI `toUnitPrice` enstrümanın divider değerini kullanır; motor normal giriş ve top-up hedefini `TLSize×1000/tavanPrice` ile hesaplar. Divider 1000 dışında desteklenen Tavan enstrümanı varsa hedefler ayrışabilir. Desteklenen enstrüman ölçekleri operasyon teyidi bekler; bütün payların yanlış miktar ürettiği sonucu çıkarılmaz.

GUI `calculateLotFromTl` pozitif tutarda en az 1 lot döndürür; motor tam sayı bölmesi tutar bir payın altındaysa 0 üretir. 20 TL tavanda 1 TL örneğinde gösterim ve motor hedefi ayrışabilir; decode ise `floor` kullanır. Sıfır miktarın SDK ret ve strateji durumuna etkisi ayrı test gerekir. `MAX_SELL_NOTIONAL` ham tutar sabitinin TL yorumu da ölçekle birlikte değerlendirilmelidir.

## 5. İptal onayından sonra kapanışın yeniden değerlendirilmesi

**K-257 · R07 · B01/B10.** `closePosition` her iki yönü iptal ettikten sonra depth hâlâ doluysa satışa geçmeden döner. `deleteOrder` callback'i pending giriş ve restore top-up kontrol eder; `closePosition` çağırmaz. Kısmen dolmuş girişte kalan alış cancel ACK'i geldikten sonra yeni ITCH/timer olayı yoksa balance satışı gecikebilir. İncelenen callback akışından çıkarılan adaydır; gerçek callback/defter zamanlamasında yeniden üretilmedi.

## 6. Father-ref sayacında miktar aşımı

**K-258 · R19 · O02.** `updateQtyForFatherOrderRef` kalan miktar gelen `orderQty` değerinden küçükse `uint64_t` sayacı 0 yapar, ardından koşulsuz olarak `orderQty` çıkarır. Pozitif gelen miktarda unsigned alt taşma olur; `orderCompletelyAccepted` için sıfır koşulu sağlanmayabilir. Tekrarlanan veya beklenenden büyük callback'in bu yola ulaşması üretimde teyit edilmedi. Test harness'i miktar/sıra koşulunu ayrı kurmalıdır; yüksek lot canlı emir gerektirmez.

## 7. Ürün sözleşmesi ve farklı olay yolları

**R10:** Yeni GUI toplu kayıtta ve çalışan satır silmede stop gönderir. Motor stop abonelik/niyetleri temizler; bekleyen emirleri ve pozisyonu otomatik kapatmaz. Ürün beklentisi ayrıca belirlenmelidir.

**R11:** Finish_With_Buy son alış denemesinden sonra stop eder; fill garantisi değildir. `rejectOrder` father-ref miktarını günceller, pending niyeti temizler ve restore kontrolüne geçer. Taban'ın PTRM stop davranışı Tavan'a taşınamaz. Final-buy ret/kısmi kabulü ortam testi bekler.

**R12:** Recover açık olsa da `Cancel_Lot_Number=0` ise recover dalı false döner. Yüzde iptal ile recover kombinasyonunun ürün anlamı netleştirilmelidir.

**R13:** Max-size satış dalı doğrudan `closePosition` çağırır; normal `shouldCancelPosition` grace kontrolünden geçmez. Saat filtresi ve aile/depth kapıları yine geçerlidir. Sert çıkışın normal saniye kuralından farklı önceliği kaynakta görülür; kullanıcı beklentisi ve zamanlamalı test ayrı kalır.

## 8. Abonelik, fiyat bandı ve gizli alanlar

**R14:** Aktif kademe satış fiyatı tavan tick'i × N ile hesaplanır; momentum arm fiyatı ise tick adımlarını yürür. Fiyat bandı sınırında iki “N kademe” hesabı farklı olabilir. Geçerli fiyat ve borsa kabulü kontrol edilmedi.

**R15:** Is_Set_To_One girişte `meltLot=1` yapıp UI/kalıcılık güncellemesi kuyruğuna yazar; aynı noktada abonelik güncellemesi TODO'dur. SDK olay eşiğinin sonraki kayıt/abonelik değişiminde nasıl ilerlediği teyit bekler. Fazla callback tek başına fazla emir kanıtı değildir.

**K-63 · R20 · P33:** Formda görünmeyen Cancel_Time/Cancel_Volume_Ratio mevcut değerleri payload'da korunur. Bir alan 0 ise hacim yolu kapalıdır. `shouldCancelPositionViaVolume` son dalda bool return içermez; açık yol güvenilir davranış olarak sunulmaz. Eski header kaynağı iddiasının ortam etkisi ayrıca teyit bekler.

## 9. Henüz hata sayılmayan regresyon ve ortam kapsamı

**R08/R09:** Pending niyetin 2ms ömrü callback'te kontrol edilir; restore cancel ile alış birlikte gönderilebilir. Top-up `balance + restingBuy` üzerinden eksik hedefi hesaplar. Bunlar korunan kaynak davranışlarıdır; mükerrer fill veya yanlış miktarın gerçekleştiği bu tur gösterilmedi.

**R16:** Development momentum pencere/arm-price ve yüzde >100 desteği master'a genellenmez. Gate başarısızlığında alış threshold'unu 0'a düşürme denemesi gerçek SDK durumuyla doğrulanmalıdır; son güncellemenin de başarısız olması bir log satırından kapanmaz.

**R18:** Restart/replay/handoff ve kurum risk politikası dağıtılmış binary/config, log ve token mutabakatı gerektirir. İlgili altyapı kayıtları açık kalır; yeni bir kesin Tavan hatası olarak çoğaltılmaz.
