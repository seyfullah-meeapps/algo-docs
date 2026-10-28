---
kapsam: Konu dosyaları, soru kayıtları, kaynak doğrulaması, görseller ve yazılı çıktı kuralları
dogrulama: 2026-10-24
durum: taslak
---

# Rehberin yazım ve kayıt düzeni

Bu rehber insan içindir. Kısa bir açıklamadan somut örneğe, ardından bizim sistemdeki karşılığına ilerler. Yeni teknik terim ilk kullanımda açıklanır. “Bunu biliyorsun” varsayımı yapılmaz; frontend bilgisinden yararlanan benzetmeler gerektiğinde kullanılır.

Kullanıcının seçtiği derinlik: ana metin çalışma mantığı, parametreler ve beklenen davranışa odaklanır. Kod yalnız gerektiğinde kısa ve açıklamalı verilir. Dosya/fonksiyon referansları ve derin C++ ayrıntıları ayrı “Teknik ayrıntı” bölümünde tutulur; satır satır kod incelemesi hedeflenmez. Kaynak kod doğrulaması yine yapılır.

Ürün adı **MTrader**, şirket adı **MeeApps**. Müşterinin günlük kullanımı ile şirketin geliştirme/test çalışması ayrı anlatılır. Kaynak [ürün ve geliştirme süreci](../bilgi-tabani/00-genel/urun-ve-gelistirme-sureci.md) kullanıcı beyanına dayanır; şirket süreci kodla doğrulanmış dağıtım kanıtı gibi sunulmaz.

## Konu dosyası

Her dosya tek soruya/konuya odaklanır. Önerilen sıra: amaç ve ön bilgi; kavramların açıklaması; küçük örnek; sistemdeki karşılık; şekil/akış; sık karışan noktalar; gerçek sorular; kaynak/doğrulama; devam notu. İskeletler bu bölümleri içerir, boş bölümler hazır içerik sayılmaz. 400 satırı aşmadan alt konulara bölünür; dosya adları Türkçe karakter içermez.

Frontmatter `durum: bos` iskelet, `taslak` yazılmış fakat inceleme bekleyen içeriktir. `dogrulandi` ancak beyan edilen kapsamın kanıtı ve repo kuralları sağlanınca kullanılır. `dogrulama` düzenleme tarihini tek başına teknik doğrulama kanıtına dönüştürmez. Kod iddiası yazılan dosyada `kaynak` repo/branch/commit eklenir; dış kaynak iddialarında `dis_kaynak` ve erişim tarihi tutulur.

## Kullanıcının soruları ve bağlam

Kullanıcı soru sorunca önce cevaplanır; sonra aynı konu dosyasına kayıt eklenir:

```text
Tarih: YYYY-MM-DD
Kullanıcının sorusu: Gerçek soru; uzun ise anlamı korunmuş özet olarak etiketlenir.
Bağlam: Hangi örnek/ekran/ayar üzerine soruldu?
Yanıt ve netleşen nokta: Anlaşılan kavram ve gerekiyorsa kaynak.
Metindeki değişiklik: Hangi açıklama veya örnek geliştirildi?
Açık kalan: Yanıtlanmadıysa açıkça belirtilir.
```

Soru birden çok konuya değiniyorsa asıl kaydı bir dosyada tutulur, diğerlerinden bağlanır. Kullanıcının sorusu, agent'ın ürettiği alıştırma ve agent'ın varsayımı birbirine karıştırılmaz. Kullanıcıya atfedilen yanıt uydurulmaz. Genel kapsam kararları [kararlar](kararlar.md) dosyasına yazılır; bütün sohbet her konuya tekrar kopyalanmaz.

Yazılı çıktı alınırken ana anlatım doğrudan okunabilir olmalı. Soruların yararlı açıklamaları ana metne işlenir; tarihli soru kayıtları kaynak MD'de ayrı bölüm olarak kalır. Kullanıcı A4 PDF, HTML ve EPUB üretimini başlattı. Mevcut okuma çıktısında soru/süreç/kaynak takip bölümleri çıkarılır; ileride bunları kaynakça/soru eki olarak sunma tercihi ayrıca ele alınabilir. Üretim ve revizyon adımları [yayın düzeninde](yayin/README.md).

## Kaynak ve doğrulama

- Seans, emir koşulu, takas süresi, açığa satış ve tedbirler için resmi Borsa İstanbul/SPK/Takasbank/MKK kaynakları ilgili konuda araştırılır. Ürün, pazar, tarih, belge sürümü ve yürürlük kapsamı yazılır. “T+2” başlığı her üründe bugün aynı kural geçerli iddiası değildir.
- Teknik kavramlarda güncel doğrulama gerekiyorsa protokolün/ürünün resmi dokümanı veya birincil kaynak kullanılır. Arama sonucu özeti nihai kanıt değildir.
- Projede kod ve gerçek sürüm esas alınır; internet bizim implementasyonumuzu kanıtlamaz. Referans ve prod farkı açık yazılır. Eski KB aktarımı yeni kod kontrolü diye sunulmaz.
- Kaynak bulunamaz veya çelişirse belirsizlik belirtilir; kesin hüküm üretilmez. İnternet erişimi, kod incelemesi, simülasyon, build, replay ve canlı test ayrı ayrı kaydedilir.
- Kritik emir, risk, ölçek ve zaman hesabı anlatımında birimler ile ilgili kod kontrol edilir. Gerçek müşteri/hesap, IP, parola ve token maskelenir.

## Düzeltme sonrası rehber bakımı

Mevcut hatalara okuyucuya yönelik rehber anlatımında yer verilmez. Hata kayıtları, neden analizi ve düzeltme kanıtları teknik bilgi tabanı/issue tarafında tutulur. Bu seçim yanlış veya henüz gerçekleşmeyen davranışı kesin bilgi olarak yazma izni değildir. Kaynakla tutarlı anlatım henüz mümkün değilse ilgili ayrıntı yazım takibinde bekletilir.

Her davranış düzeltmesinde kapanış kontrolü: etkilenen rehber dosyalarını belirle; düzeltme commit'i ve doğrulama sonucunu teknik kayıtta tut; ilgili anlatımı, sayısal örneği, parametre tablosunu, görsel/şemayı ve test beklentisini kontrol edip güncelle. Kaynak sürümünü ve ilerleme/changelog kaydını güncelle. Etki yoksa teknik kapanış kaydına “rehber etkisi yok” yaz. Rehberde geriye dönük bug hikâyesi ekleme. Kod değişmiş olması tek başına canlı ortamın da düzeldiği kanıtı değildir.

## Görsel hazırlama

Mimari için küçük bileşen, dağıtım ve sequence çizimleri kullanılır; kaynak/config doğrulanmadan container adı ve bağlantı uydurulmaz. Gerçek ekran görüntüsü çalıştırılan sürümle etiketlenir. Koddan çizilen SVG “temsili” diye belirtilir; frontend'in render çıktısı gibi sunulmaz. Yer tutucuda ekran/route, görünmesi gereken alanlar ve maskelenecek bilgiler yazılır. Görseller konuya ait alt dizinde tutulur, göreli bağlantı kullanılır. Şimdilik hiçbir görsel hazır değildir.

## Oturum kapatma

İlgili konu, bölüm indeksi, [ilerleme](ilerleme.md), gerekiyorsa [kararlar](kararlar.md), kök oturum notları ve changelog güncellenir. `python _surec/kontrol.py` ve `git diff --check` çalıştırılır. Açık konu indeksine yalnız gerçek yeni teknik bulgu girilir; yazılmayı bekleyen başlıklar bug sayılmaz.
