---
kapsam: HFT sanity incelemesindeki açık kaynak adayları ve ürün/ortam teyitleri için toplu issue metni
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

# HFT — yeni GUI ve motor davranışı inceleme bulguları

Bu metin statik kaynak adaylarını ve ürün/ortam teyitlerini toplar. Yeni manuel test yapılmadı. Excel'deki 98 testin tamamı Test Edilmedi; aşağıdaki maddeler kesin canlı hata listesi değildir. Kaynak kapsamı ve kapanan eski iddialar [inceleme kaydındadır](../../bilgi-tabani/test-incelemeleri/hft-inceleme-2026-10-26.md). Çözüm önerisi ve kabul ölçütü içermez.

## 1. Kâr al ve stop-loss alan sözleşmesi

**R02, P17/P18 — K-252:** Yeni GUI Alarak Başla için satış pasif kademesini açar; kapalı alış alanı normalizasyonda 0 olur. `HftClassic::sendAskOrder` kâr al fiyatını `Buy_Passive_Level` ile kurar; `sendPassiveSellInfoOrder` da bu alanı kullanır. Ekranda girilen `Sell_Passive_Level` bu alış girişinin kâr al mesafesiyle eşleşmez. Kâr al/stop hazırlığı yapılmayabilir veya farklı ayardan etkilenebilir. Canlı yeniden üretim yok.

**R03, P20 — K-236:** `useHftSettingsForm` kapalı stop-loss için 0 gönderir. Motor karar yolları bayrağı okumaz; −1 kapalı seviyedir. Uygun TP ön koşulları oluşursa 0 giriş fiyatında stop hesabına dönüşebilir. R02 yüzünden TP hazırlığı oluşmayan koşulda bu aday bağımsız tetiklenmeyebilir.

## 2. Miktar ve tek işlem kontrolü

**R01 — K-253:** `HftClassic::SendBidOrder` miktar dallarında balance, header ve fake emir miktarları birlikte kullanılır. Aynı ekonomik miktarın iki terimde sayılması kaynak adayıdır; fazla satış etkisi henüz yeniden üretilmedi. Eski 5 lot → 10 lot anlatısı bu incelemenin canlı kanıtı değildir.

**R10, P19 — K-237:** `isSameSideSingleOperation` iki tarafta da alış başlangıcı koşulunu kullanır. Satış başlangıcında accept mandalı kurulmayabilir; `setCommand` mandalı sıfırlar. Tek işlemin accept, fill veya tam döngü olarak tanımı ve stratejinin durması ayrı ürün sözleşmesidir.

## 3. Saat, durdurma ve seans kapsamı

**R05, P13:** Start_Time/Stop_Time parse edilip saklanır; Classic karar yolu saat aralığını uygulamaz. Ekranda kaydedilen aralık motorun zaman filtresi değildir.

**R06:** `stopStrategy` piyasa aboneliğini kaldırır; `cancelAllOrders` ayrı yoldur. Bekleyen emirler kalabilir. Emir callbacklerinin tamamının kesildiği eski genelleme geçersizdir. Durdurmanın emir iptali içermesi ürün kararı gerektirir.

**R07/R08:** Emir kabulünde kurulan saniye kuralı işi ile TP/stop yolları, yeni tetik yolundaki aynı running/seans kontrollerini paylaşmaz. Bekleyen işin durdurma veya seans değişimi sonrasında emir üretmesi olasıdır. İşin kayıt/silme sırası ve borsanın kabulü canlıda sınanmadı. Teknik dayanak: Classic ve [periyodik işler](../../bilgi-tabani/10-servisler/hftsrvprod/strateji-cekirdegi.md).

## 4. Emir ve pozisyon politikaları

**R09:** Classic genel ret yolu gönderim mandalını çözebilir; tekrar tetiklenmede yeniden emir denenebilir. PTRM reddinde kalıcı durdurma/sayaç politikası bu yolda saptanmadı. Fiili ret döngüsü ölçülmedi.

**R11, P11:** Üst alış sınırı 0, alış karşılaştırmasını engelleyebilir; alt satış sınırı 0 aynı anlama gelmez. Boş/0 alanın ürün anlamı netleştirilmelidir.

**R12, P12:** Aynı Time_In_Force pasif kâr al şablonuna da uygulanır. Anında gerçekleşme isteyen geçerlilik türlerinde bekleyen kâr al emri kalmayabilir; saniye kuralı ve kapatma şablonları ayrıca değerlendirilir.

**R13:** Normal girişte TP hazırlığı/tetiklenmesi tam dolum yoluna bağlıdır. Kısmi dolum sonrası bekleyen veya iptal edilen kalan miktarın koruma kapsamı ürün kararı ve test gerektirir; bütün özel yollar için koşulsuz genellenmez.

**R16, P23:** `HftTrackerForm::handleDeleteStrategy` panel kaydı başarılıysa aboneliği ve satırı kaldırır, bu dalda motor stop komutu yoktur. Panelde görünmeyen strateji çalışmayı sürdürebilir. Panelden çıkarma ile stratejiyi sonlandırmanın aynı işlem olup olmadığı ürün kararıdır.

## 5. Açılış, devir ve veri bağımlılıkları

**R18:** Replay başladıktan sonraki 60 saniyelik timeout kapalı gate'i zorla açabilir. Ayrı 20 saniyelik zero-handoff watchdog pending=0 koşulunda gate'i açar; order-service yedek yolu kullanılabilir. İlki eksik replay ile devam riski taşır; ikincisi tek başına açık emir kaybı kanıtı değildir.

**R19, P30:** `ownsAccount` sağlanmazsa emir order-service yoluna düşer. Log vardır; kullanıcıya görünür alarm/izleme entegrasyonu teyit edilmedi. Yol değişimi gecikme ve operasyon görünürlüğünü etkileyebilir.

**R20 — teyit bekliyor:** DB/ayar/limit yükleme hatasının uçtan uca etkisi kesinleşmedi. SDK yerel retleri ve yedek yolun kendi kontrolleri nedeniyle “büyük emirler kontrolsüz gider” eski genellemesi kullanılmaz.

**R26:** `HftMain` Glimpse tamamlanmasını timeout olmadan bekler. Tamamlanmayan snapshot açılışı bekletebilir. Aktif lisans çağrısı yorumdadır; lisans beklemesi bu maddeye dahil değildir.

Kaynak ayrıntısı: [emir yaşam döngüsü](../../bilgi-tabani/10-servisler/hftsrvprod/emir-yasam-dongusu.md) ve [açılış](../../bilgi-tabani/10-servisler/hftsrvprod/README.md).

## 6. Risk kontrollerinin kapsamı

**R21:** İncelenen HFT strateji yolunda genel saniyelik emir hız sınırı saptanmadı. Dış ağ geçidi/SDK/borsa sınırları aynı kapsam değildir. Tekrarlayan tetik/ret emir yoğunluğunu artırabilir.

**R22:** Classic karar yolunda stratejiler arası toplam pozisyon eşiğine bağlı durdurma saptanmadı. Dış kurum kontrolleri ayrıca teyit edilmelidir; toplu emir iptali strateji durdurmayla eşit sayılmaz.

**R23 — teyit bekliyor:** Doğrudan SDK yolu order-service risk zincirinden geçmez. Yedek yolda `database.riskControl` ve bypass koşulları geçerlidir. “Hiçbir emir yolunda kurum limiti kontrol edilmez” sonucu çıkarılamaz. Dağıtılmış config ve kurum entegrasyonu incelenmedi. Ayrıntı: [order-service risk](../../bilgi-tabani/10-servisler/order-service/risk.md).

## 7. Kuyruk, parçalı emir ve komut tipleri

**R28:** Strateji piyasa verisi kuyruğunda kapasite aşımı olay kaybına dönüşebilir; sayaç ve görünür raporlama yolları farklıdır. Bu tur taşma üretilmedi. Kaynak: [strateji çekirdeği](../../bilgi-tabani/10-servisler/hftsrvprod/strateji-cekirdegi.md).

**R29:** Limit nedeniyle bölünen emirlerde parçaların ret/kabulü tek atomik sonuç değildir; bir parça reddedilirken diğerleri gönderilebilir. Parent/child sonuçlarının strateji durumuna etkisi [SDK emir akışına](../../bilgi-tabani/10-servisler/maordersdk/README.md) ve kullanılan sürüme bağlıdır.

**R30:** Parser beklenen wire tipini bulamadığında varsayılan değere dönebilir. Yeni GUI Long/Int/Bool tiplerini açıkça üretir; bu kayıt hatalı komut/harici istemci kapsamındadır, yeni GUI'nin fiilen yanlış tip gönderdiği kanıtı değildir.

## 8. Ayrı ortam ve zamanlama teyitleri

**R24:** Önceki restart/alarm iddiası gerçek container politikası ve izleme ile doğrulanmadı. Servisin kesin ertesi güne kadar kapalı kalacağı söylenemez.

**R27:** Tarih, log yolu ve kalıcılık dağıtılmış config/mount ile teyit bekler. Örnek config tek başına kayıp log kanıtı değildir.

**R31:** `setOrderPrice` header fiyatını şablonlara yazar. Tetik/header callback sırası eriyen kademenin fiyatını etkileyebilir; zamanlamalı yeniden üretim yapılmadı.

**R33:** Token kayıtlarının ömrü ve config satır sonu yorum ayrıştırması iki ayrı eski iddiadır. Bazı registry kayıtları raw pointer ömrü nedeniyle kasıtlı tutulur; yalnız bellek büyümesi hata kanıtı değildir. Güncel kaynak yolu ve özgün olay ayrı teyit bekler.
