---
kapsam: MTrader ürün kimliği, müşteri ile MeeApps sorumlulukları ve özelliğin testten müşteriye geçiş süreci
kullanici_beyani:
  tarih: 2026-10-24
  baglam: Kullanıcının rehber revizyonunda açıkladığı şirket çalışma ve test süreci
dogrulama: 2026-10-24
durum: taslak
---

# MTrader: ürün, müşteri ve geliştirme süreci

Şirket/ürün kimliği ve iş sürecinin tek referansıdır. Kaynak, kullanıcının 24 Ekim 2026 tarihli açıklamasıdır; koddan veya canlı ortamdan doğrulanmış dağıtım kanıtı değildir. Teknik mekanizmalar [branch ve ortamlar](branch-ve-ortamlar.md) ile [operasyon](../40-operasyon/README.md) belgelerindedir.

## Kimlik ve kullanım

- **MeeApps**, ürünü geliştiren şirkettir.
- **MTrader**, MeeApps'in geliştirdiği **algoritmik işlem botudur** (Algorithmic Trading Bot). Kullanıcıya yönelik adı büyük/küçük harfleriyle bu şekilde yazılır.
- Müşteriler aracı kurumlardır. Günlük işlem kullanıcıları bu kurumların çalışanlarıdır; traderlar ve fon yöneticileri bunlara örnektir.
- MeeApps, ürünü geliştirir, test eder ve müşterilere sunar. Şirket adına her gün düzenli trade yapmak için kullanmaz; özellikleri ve senaryoları sınamak için kullanır.
- Arayüz, motor, SDK, yönetim ve operasyon bileşenleri ürünün yapısını oluşturur. Repo isimleri ve kod/protokol alanlarının özgün yazımı değiştirilmez.

## Özellikten müşteri dağıtımına

| Aşama | Çalışma ve geçiş |
|---|---|
| Kapsam ve senaryolar | Özellik detayları, olası senaryo/problemler ve etkilenen alanlar değerlendirilir; etkiye göre görevler dağıtılır. |
| Geliştirme ve geliştirici testi | Yazılımcılar görevlerini tamamlar ve kendi ön testlerini yapar. |
| Test ortamı | Geliştirme test ortamına alınır, bir süre test edilir ve izlenir. Çıkan hatalara müdahale edilir; ilgili senaryolar yeniden sınanır. |
| Preprod, düşük lot | Önceki aşamalardan sonra preprod'a geçilir. Anlaşılmış gerçek traderlar özelliği test eder; başlangıç testleri düşük lotla sürer. |
| Preprod, yüksek lot | İlk preprod testlerinde sorun çıkmaz ve kararlılık doğrulanırsa yüksek lot testlerine geçilir; bir süre daha izlenir. |
| Müşterilere dağıtım | Bu aşamada da sorun görülmezse özellik tüm müşterilere aktarılır. |

Preprod'un ilk testleri dahil önceki test aşamalarında düşük lot kullanılır. Lotların sayısal sınırı, test süreleri, ölçülebilir kararlılık eşiği ve son dağıtım onayını veren kişi belirtilmedi; uydurulmaz. Gerçek traderın katılımı, ortamın teknik olarak hangi borsa bağlantısını kullandığını tek başına kanıtlamaz.

Bu iş akışı branch adıyla birebir aynı şey değildir. Test/preprod katılımı, lot ölçeği ve kabul aşamaları burada; branch'ler, CI ve müşteri sürüm envanteri teknik belgelerde tutulur.

## Dokümantasyona etkisi

Müşterinin işlem günü ile MeeApps'in geliştirme/test döngüsü ayrı anlatılır. Hata kayıtları teknik takipte kalır; doğrulanan davranış değişikliğinin rehbere etkisi düzeltme kapanışında kontrol edilir. Bu açıklama yeni canlı test, deploy veya tüm açık sorunları çözme komutu değildir.
