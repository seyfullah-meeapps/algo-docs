---
kapsam: İşlem ve takas ayrımı; T+2, iş günü, netleştirme, brüt takas, tedbirler ve tarihli T+1 hazırlıkları
dis_kaynak:
  - url: https://www.borsaistanbul.com/piyasalar/pay-piyasasi/takas-esaslari
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/sss/pay-piyasasi
    erisim: 2026-10-24
  - url: https://www.borsaistanbul.com/files/duyuru-38907-TR.pdf
    erisim: 2026-10-24
  - url: https://www.mkk.com.tr/duyurular/pay-takas-suresinin-t2den-t1e-kisaltilmasi-projesi-senaryolu-testleri-hk
    erisim: 2026-10-24
dogrulama: 2026-10-24
durum: taslak
---

# Takas, T+2 ve brüt takas

**İşlem**, alışla satışın eşleşmesidir. **Takas**, bu işlemden doğan nakit ve kıymet yükümlülüklerinin yerine getirilmesidir. Emir gerçekleşince bir yükümlülük doğar; paranın ve kıymetin takasının tamamlanması ayrı aşamadır.

## T+2 ne demek?

**T**, işlem günüdür. **T+2**, işlem gününü izleyen ikinci **iş günü** anlamına gelir. Borsa İstanbul'un Pay Piyasası takas esasları sayfası, 24 Ekim 2026 erişiminde bu düzeni belirtir; ödeme karşılığı teslim ve çoklu netleştirme esaslarını açıklar. [Borsa İstanbul — Takas esasları](https://www.borsaistanbul.com/piyasalar/pay-piyasasi/takas-esaslari)

Arada tatil olmayan varsayımsal bir hafta düşünelim:

| İşlem günü | T+1 | T+2 |
|---|---|---|
| Pazartesi | Salı | Çarşamba |
| Cuma | Pazartesi | Salı |

Araya resmi tatil girerse bu basit çizelge değişir. T+2, “48 saat sonra” değildir. Takas takvimi ile bilgisayarın takvim günü hesabını ayırırız.

## Satış bedeli neden hemen çekilemeyebilir?

Satış gerçekleştiğinde hesapta bir takas alacağı oluşabilir. Kurum bu alacağı yeni alışlarda kullanmaya izin verse bile aynı tutarın hemen dışarı çekilebilmesi ayrı meseledir. **Alış gücü**, **takas alacağı** ve **çekilebilir nakit** aynı anda aynı rakam olmak zorunda değildir.

Örneğin 2.000 TL'lik satışın gerçekleştiğini söylemek, o anda banka hesabımıza 2.000 TL transfer edebileceğimizi tek başına göstermez. Kurumun kuralları, takas takvimi ve varsa borç/blokaj birlikte değerlendirilir.

## Netleştirme ne yapar?

Aynı takas tarihine ait yükümlülükler belirli kurallarla mahsuplaştırılabilir. Aynı paydan 100 adet alıp 40 adet sattığımız sade örnekte net kıymet farkı 60 adettir. Buna **netleştirme** deriz; iki ayrı işlemin kaydı silinmez, teslim edilecek net fark belirlenir.

Bu örnek her müşterinin her üründe sınırsız gün içi al-sat yapabileceği anlamına gelmez. Üye ve müşteri düzeyindeki hesap, ürün ve tedbir koşulları ayrıca önemlidir.

## Brüt takas neyi değiştirir?

**Brüt takas**, ilgili işlemler için netleştirmenin kaldırılmasıdır. Alışın nakit, satışın kıymet yükümlülüğü ayrı karşılanır. Alış için yeterli nakit ve satış için yeterli kıymetin takas tarihinde hesapta bulunması gerekir. “100 aldım, 100 sattım, hiç kaynağa gerek kalmadı” yaklaşımı uygulanamaz. [Borsa İstanbul — Brüt takas açıklaması](https://www.borsaistanbul.com/sss/pay-piyasasi)

Brüt takas bazı pazar kurallarından veya belirli paya getirilen tedbirden kaynaklanabilir. Başlangıç/bitiş tarihi ile diğer tedbirleri de okumak gerekir. Emir paketi kısıtı, kredili işlem yasağı ve brüt takas aynı tedbir değildir; birlikte uygulanabilmeleri onları aynı kavram yapmaz.

## T+1 hazırlığı ile canlı takas düzeni

BIST'in **29 Ağustos 2025** duyurusu T+1 için hazırlıkların 31 Aralık 2026'ya kadar tamamlanmasını ister. MKK'nın **5 Haziran 2026** duyurusu ise senaryolu testleri anlatır. Bunlar test ve hazırlık belgeleridir; tek başlarına “canlı takas T+1 oldu” kanıtı değildir. [BIST hazırlık duyurusu](https://www.borsaistanbul.com/files/duyuru-38907-TR.pdf), [MKK test duyurusu](https://www.mkk.com.tr/duyurular/pay-takas-suresinin-t2den-t1e-kisaltilmasi-projesi-senaryolu-testleri-hk)

Bu rehberde Pay Piyasası için yukarıda tarihli T+2 referansı kullanılıyor. Gerçek bir işlem için o günün yürürlük duyurusu ve takas takvimi kontrol edilir. Pay vadelisinin fiziki teslimatı, endeks vadelisinin nakdi uzlaşması ve spot pay takası aynı süreç sayılmaz.

## MTrader testinde takas bağlamı

Bir testte yalnız pozisyon miktarını değil, takasa konu alacak/borcu, kullanılabilir kıymeti ve tedbir bilgisini de belirleriz. Bir emrin fiyat ve miktarı uygun olsa bile ürünün işlem kısıtları farklı olabilir. Uygulamanın brüt takas veya diğer tedbirleri nasıl kontrol ettiği sistem/strateji bölümünde kodla açıklanacak.

## Sorularımız ve netleşen noktalar

**24 Ekim 2026 — Kullanıcı yönlendirmesi, anlamı korunmuş özet:** Borsa tarafının kalan konuları topluca tamamlansın; kullanıcı bölümün tamamını okuyup birlikte revize edecek. Bu dosya bu kapsamda taslak yazıldı; ayrı bir konu sorusu henüz yok. Örnekler agent tarafından eğitim amacıyla oluşturuldu.

## Kaynaklar ve doğrulama

Resmi BIST takas sayfası ile brüt takas SSS, 29 Ağustos 2025 hazırlık duyurusu ve 5 Haziran 2026 MKK testi okundu; erişim 24 Ekim 2026. Bu tarihli kaynaklar dışında bir canlı T+1 yürürlük tarihi uydurulmadı. Örnek günlerde resmi tatil olmadığı varsayıldı. Canlı hesap veya takas entegrasyonu test edilmedi.

Bu tur MTrader kaynak kodu, canlı binary/config veya gerçek işlem testi yapılmadı. Projeye ilişkin bağlantılar mevcut KB taslaklarına dayanır; bunlar yeni kod doğrulaması değildir.

## Devam notu

Borsa bölümünün tamamıyla birlikte kullanıcı revizyonuna sunulacak.

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
