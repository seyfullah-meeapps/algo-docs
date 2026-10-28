---
kapsam: Log/metric/trace, korelasyon; unit/entegrasyon/replay/UAT ve sürüm kanıtı
dis_kaynak:
  - url: https://opentelemetry.io/docs/concepts/signals/logs/
    erisim: 2026-10-25
  - url: https://opentelemetry.io/docs/concepts/signals/metrics/
    erisim: 2026-10-25
  - url: https://opentelemetry.io/docs/concepts/signals/traces/
    erisim: 2026-10-25
  - url: https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Log, test ve sürüm bilgisi

“Başlat'a bastım, çalışmadı” değerli bir başlangıç gözlemidir; fakat geliştiricinin aynı durumu bulması için eksiktir. Hangi hesap, ürün, strateji, zaman ve sürüm? İstek nereye kadar gitti? Bu konu, gördüğümüz davranışı izlenebilir kanıta dönüştürmek için temel kavramları verir.

## Log, metric ve trace

**Log**, belirli bir olayın kaydıdır: “şu zamanda bu bağlantı kapandı” gibi. **Metric**, zaman içinde sayısal gözlemdir: saniyedeki olay, kuyruk uzunluğu veya gecikme dağılımı. **Trace**, bir işin farklı adımlarını ilişkilendirerek izlemektir; **span**, o izin belirli bir iş adımını temsil eder.

Restoran benzetmesiyle log “42 numaralı sipariş mutfağa girdi” notu; metric son saatteki ortalama bekleme; trace ise 42'nin siparişten teslimata bütün yoludur. Bu veriler birbirini tamamlar. Metric artışı belirli bir olayı bulmayı kolaylaştırabilir, log ise nedenini açıklayabilir. [OpenTelemetry — log](https://opentelemetry.io/docs/concepts/signals/logs/) · [metric](https://opentelemetry.io/docs/concepts/signals/metrics/) · [trace](https://opentelemetry.io/docs/concepts/signals/traces/)

Bu kavramları öğrenmek, MTrader'da bütün katmanlarda OpenTelemetry veya dağıtık trace kurulu olduğu anlamına gelmez. Gerçekte hangi kayıtların bulunduğu ilgili bileşende kontrol edilir.

## Aynı işi farklı log'larda nasıl buluruz?

**Korelasyon kimliği**, aynı iş veya olayın kayıtlarını ilişkilendirmeye yarayan kimliktir. Ürün kodu tek başına yeterli değildir: aynı üründe aynı anda birçok strateji ve emir olabilir. İstek kimliği, strateji kimliği, emir token'ı ve gerçekleşme kimliği farklı şeyleri temsil edebilir.

Öğretici akışta `istek-A` bir stratejiyi başlatma talebi, `strateji-42` çalışan strateji, `emir-B` ise onun ürettiği belirli emir olsun. Başlatma talebinin kabulü ile emir-B'nin borsa kabulü ayrı kayıtlardır. Birinin kimliğini diğerinin yerine kullanmayız; aralarındaki bağlantıyı takip ederiz.

Log'daki `INFO`, `WARN`, `ERROR` gibi seviye adları önem derecesi için kullanılır; bütün ürünlerde aynı iş sonucu anlamını taşımaz. Bir `ERROR` satırının nedeni ve sonraki toparlanma olayları birlikte okunur. Hata satırı bulunmaması da işlemin başarı kanıtı değildir.

## Test türleri hangi soruya yanıt verir?

| Test / inceleme | Örnek soru | Tek başına neyi kanıtlamaz? |
|---|---|---|
| Unit | Fiyat dönüşümü verilen girdide doğru mu? | Gerçek bağlantının çalıştığını |
| Entegrasyon | İki bileşen aynı mesajı doğru yorumluyor mu? | Bütün müşteri ortamını |
| Replay | Kaydedilen olay dizisiyle beklenen durum oluşuyor mu? | Canlı zamanlama ve her ağ koşulunu |
| Yük / performans | Belirli hızda kuyruk ve gecikme ne oluyor? | İş kurallarının tamamını |
| UAT / kullanıcı kabulü | Kullanıcının senaryosu ihtiyacı karşılıyor mu? | Bütün kod yollarını |
| Statik kod incelemesi | Bu dalda hangi koşullar var? | Çalışan binary'nin o koddan geldiğini |

Bu tablo bir zorunlu test listesi değildir; “test edildi” ifadesinin kapsamını anlatır. Örneğin sayısal dönüşüm testi geçerken yanlış config nedeniyle uygulama yanlış ürüne bağlanabilir. Bir katmandaki doğru sonuç, diğer katmanları otomatik doğrulamaz.

**Regresyon**, değişiklik sonrası daha önce çalışan davranışların bozulup bozulmadığına bakmaktır. İncelenen senaryo ve etkilenen komşu davranışlar önemlidir. Test/PM bölümünde bunları gerçek stratejilerin parametre ve akışlarına uygulayacağız.

## Beklenen ile gözlenen ayrı yazılır

Varsayımsal bir test kaydı düşünelim:

- **Ön koşul:** Test ortamı, ürün açık, hesap yetkili, strateji durmuş.
- **Adım:** Strateji-42 için 100 lot hedefle bir kez Başlat talebi gönder.
- **Beklenen:** Tanımlı başlatma sonucu ve doğru strateji durumu oluşsun.
- **Gözlenen:** HTTP yanıtı geldi, fakat 5 saniyelik gözlem aralığında strateji durumu değişmedi.
- **Kanıt:** Maskelenmiş istek/yanıt, ilgili olay hattı ve servis log'ları; zaman ve sürüm.

Burada “motor bozuk” sonucunu peşinen yazmıyoruz. Gözlem, talebin kabulü ile durum güncellemesi arasındaki farkı gösteriyor; sorumluluğu doğru katmana atamak için iz sürülecek. Beş saniye örnektir; gerçek kabul süresi ürün sözleşmesinden gelir.

## “Aynı sürüm” demek için ne gerekir?

**Branch**, hareket eden geliştirme çizgisidir; **commit**, belirli kaynak durumunu işaret eder. **Binary/image**, o kaynak ve bağımlılıklardan üretilmiş çıktıdır; **config**, hangi koşullarda çalışacağını belirler. Aynı branch adıyla farklı günlerde üretilmiş iki dosya aynı kodu taşımayabilir. [Git commit geçmişi](https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History)

Pratik bir kanıt kaydı şu bilgileri birbirine bağlar: **ortam + bileşen + kaynak commit/build kimliği + SDK bağımlılıkları + ilgili config + test zamanı**. Image tag'i yeniden kullanılabiliyorsa içerik kimliği/digest daha belirli olabilir. Ancak digest bile tek başına çalışan sürecin o image'dan başlatıldığını kanıtlamaz; çalışma bilgisiyle eşlenir.

MTrader'ın referans branch/ortam akışı ve istisnaları [branch ve ortamlar](../../bilgi-tabani/00-genel/branch-ve-ortamlar.md) belgesindedir. Müşteriye kabul süreci ise [ürün ve geliştirme sürecinde](../../bilgi-tabani/00-genel/urun-ve-gelistirme-sureci.md) kalır. “development'ta var”, “testten geçti” ve “müşteride çalışıyor” farklı beyanlardır.

## Kayıt toplamak da ölçümü etkileyebilir

Her olayda büyük metin üretmek veya diske yazmayı beklemek işleme süresini etkileyebilir. Ölçüm sırasında hangi log seviyelerinin açık olduğunu bilmek bu yüzden yararlıdır. Gereken kanıtı toplarken gerçek parola, token ve müşteri sırları maskelenir; olayları ilişkilendirmeye yarayan güvenli kimlikler korunur.

Bu bölümün ardından sistem mimarisini okurken artık “hangi süreç, hangi protokol, hangi veri, hangi thread, hangi zaman ve hangi sürüm?” sorularını ayrı sorabiliriz. Sonraki bölüm bu kelimeleri MTrader bileşenlerinin gerçek bağlantılarına yerleştirecek.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Kullanıcı teknik bölümün tamamını yazıp toplu incelemeye sunmamızı istedi. Bu konu ve örnek test kaydı bu kapsamda üretildi; gerçek hata kaydı veya çalıştırılmış test değildir.

## Kaynaklar ve doğrulama

OpenTelemetry resmi log/metric/trace kavramları ve Git resmi kitap bölümü, erişim 25 Ekim 2026. Test türü tablosu genel öğretici sınıflamadır; ürünün yürürlükteki zorunlu kalite süreci olarak sunulmaz. MTrader süreç/sürüm açıklamaları mevcut KB'ye yönlendirmedir; bu konuda CI, deployment, çalışan binary veya canlı test doğrulanmadı.

## Devam notu

Teknik Temeller'in 10 konusu taslak tamamlandı. Kullanıcının bu yeni bölüme toplu revizyonları bekleniyor. Sonraki bölüm Bizim Sistemimiz; açık geçiş talebi olmadan yazımına başlanmaz.


[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
