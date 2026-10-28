---
kapsam: Taban sanity hazırlığında bulunan kaynak adayları ve ürün/ortam teyitleri
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

# Taban — kaynak incelemesi bulguları

Bu yerel taslak kod incelemesidir; canlı hata yeniden üretimi değildir. Kaynak yolları, commitler ve Excel kapsamı [inceleme kaydında](../../bilgi-tabani/test-incelemeleri/taban-inceleme-2026-10-26.md). Çözüm önerisi veya ürün adına kabul ölçütü içermez; uzak issue açılmadı.

## 1. Kapalı tolerans değeri

**K-259 · R01 · P16.** `encodeMinPriceSettings` tolerans kapalıyken `Tolerance=0` gönderir; `MinPriceCommand` da eksik değeri0 kabul eder. `HftMinPrice::openPosition` yaklaşık1417. satırda `toleranceCounter >= tolerance && tolerance != -1` ile durur. Başlangıç sayacı0 olduğunda uygun ilk giriş engellenir. Motorun sınırsız istisnası−1 ile GUI kapalı seçimi eşleşmez. Pozitif toleransla hazırlanan RB bu uyuşmazlığı gizleyen başarılı test olarak yorumlanmaz; kapalı seçenek E02/R01'de ayrıdır.

## 2. Emir miktarında sabit fiyat ölçeği

**K-260 · R02 · P13.** GUI `toUnitPrice` içinde `rawToDisplayPrice(rawMinPrice, divider)` kullanır; motor `openPosition` yaklaşık1442. satırda `TLSize * 1000 / tabanPrice` hesaplar. Divider1000 örneğinde uyumludur. Başka ölçekli enstrüman destekleniyorsa ekrandaki lot ile gönderilen miktar farklılaşabilir. Taban'ın gerçekten desteklediği enstrüman/ölçek kapsamı ve canlı gönderilen miktar henüz teyit edilmedi; kesin müşteri etkisi iddiası yok.

## 3. Sıfır lotta açık pozisyon bayrağı

**K-261 · R03 · A06.** `openPosition` yaklaşık1423–1451 arasında önce `isPositionOpen=true`, `isExiting=false`, açılış zamanını ve timerı kurar; ardından lotu hesaplar. `lot<=0` kontrolü emir göndermeden döner, açık bayrağı geri almaz.20 TL tabanda19 TL hedef bu yola girer. `shouldEnterPosition` açık bayrağında yeni girişi engeller; emir gönderilmediği için sıfır-fill cancel/reject callback toparlanması da kendiliğinden oluşmaz. Timer boş bakiye ile close yolunda `isExiting` de kurabilir. Bu kalıcılık yeni ayar/durum kurulması olmadan değerlendirilmelidir: `setCommand` içindeki `restorePositionState` flat durumu yeniden kurabilir. GUI yalnız pozitif TL şartı koyar; en az bir lot tutarı şartı değildir. Canlı/harness yeniden üretim yok.

## 4. Gönderilmeyen satıştan sonra çıkış bayrağı

**K-262 · R04 · C10.** `dumpPositionAtTaban` yaklaşık1667. satırdan itibaren `balance * tabanPrice > MAX_SELL_NOTIONAL` durumunda satış göndermeden döner. Sabit `.h:334` içinde `50000000000LL` raw tutardır; yorum50 milyon TL der. `closePosition` boş satış depth dalında bu void fonksiyonu çağırır, sonucu kontrol etmeden yaklaşık1542. satırda `isExiting=true` yapar. Sonraki `shouldEscapePosition` ve `recheckEscape` bu bayrakta geri döner. Bu yol gerçekleşirse gerçek satış yokken kaçışın sürüyor görünmesi mümkündür. Gerçek hesap limitleriyle erişilebilirliği ve olay sırası doğrulanmadı; yüksek tutar enjeksiyonu yalnız harness kapsamıdır. Pasif satış varken replace dalı bu özel erken dönüş yolundan ayrıdır.

## Ürün ve ortam teyitleri

R09 mevcut K-238'in saat filtresi ve timer kapsamını taşır. R10 tek kademe `<=` / tüm kademeler `<` farkını; R11 hold süresinin destek çöküşünü de geciktirmesini ürün kararı olarak ayırır. R13 tabandaki sabit tickle başka fiyat bandına taşınan hedefin geçerliliğini teyit ister. R14 eksik auto-mode varsayılanı ve iki hedefli legacy snapshotın GUI/motor öncelik farkını ayırır; normal GUI seçilmeyen hedefi0 yapar.

R16 manuel satış tokenının strateji orderMap/bakiye yoluna bağlanmasını (mevcut K-212), R17 Taban Lotu gösteriminin ürün anlamını (K-164), R18 PTRM development/master farkını (K-235) korur. R19 yeni GUI'nin göndermediği Finish_With_Sell ve development'ta kaldırılmış ayrı reClose lot/yüzde alanlarını hata listesine eklemez. `Close_Position_First` motor restore davranışı inceleme kaydı/O04/P17'de sınırlandırılmıştır; sırf kutu seçildi diye anlık satış varsayılmaz.
