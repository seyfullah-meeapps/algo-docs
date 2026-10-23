---
kapsam: Derinleştirme sonrası taslak incelemesinin kapsamı, giderilen özet çelişkileri ve kullanıcı değerlendirmesi öncelikleri
dogrulama: 2026-10-23
durum: taslak
---

# Taslak incelemesi — 2026-10-23

Madde 10 için hazırlık kaydıdır. Kullanıcı onayı veya bütün teknik iddiaların yeniden kodla doğrulandığı anlamına gelmez. Açık sorunların ayrıntısı ilgili dosyadadır; burada yalnız okuma sırası verilir.

## Yapılan kontrol

- Başlangıçtaki 82 Markdown dosyası tüm repo genelinde tarandı. Fenced kod içindeki C++ lambda ifadesi bağlantı sanılmadığında kırık dosya/başlık bağlantısı bulunmadı.
- Frontmatter ve manifestteki 15 kaynak repo kontrol edildi: 23 farklı commit nesnesi ve beyan edilen yerel origin branch ref'leri klonlarda mevcut. Fetch yapılmadı; güncel remote veya branch atalık kontrolü değildir.
- Son kontrolde 84 Markdown belgesi ve 1.344 yerel bağlantı temiz; metadata taşıyan 81 belgenin tamamı taslak.
- Yeniden çalıştırılabilir [`kontrol.py`](kontrol.py) ve [kullanımı](kontrol.md) eklendi. Giriş README'sine frontmatter ve inceleme bağlantıları eklendi.
- Özetlerdeki replay gate, handoff saati ve thread güvenliği ifadeleri kod/ayrıntı belgeleriyle karşılaştırıldı. 20 s zero-handoff watchdog ile handoff sonrasındaki 60 s timeout ayrıldı; manuel emir/close/cancel yollarının gate'i atlayabildiği açıklandı.
- Önceki oturumda kapatılan HFT restart belirsizliği, eski strateji çekirdeği metninden kaldırılıp ilgili kurtarma senaryosuna bağlandı.

## Kullanıcı incelemesi için sıra

| Öncelik | Okunacak belge | Değerlendirilecek sınır |
|---------|----------------|------------------------|
| 1 | [Sistem haritası](../00-genel/sistem-haritasi.md), [branch/ortamlar](../00-genel/branch-ve-ortamlar.md) | Gerçek müşteri/ortam ve canlı binary bilgisi kaynak branch'lerden ayrı doğrulanmalı |
| 2 | [Fon Takibi](../20-stratejiler/fon-takibi.md#şüpheli), [Arbitraj](../20-stratejiler/arbitraj.md#şüpheli) | K-194/K-195 development–master farkları; canlı davranış bu oturumda ölçülmedi |
| 3 | [Sabah/handoff](../30-akislar/sabah-emri-ve-handoff.md), [kopma/kurtarma](../30-akislar/kopma-ve-kurtarma.md) | K-215 ve restart bağımlılıkları; koddan çıkarılan sıra canlıda sınanmış prosedür değildir |
| 4 | [Manuel emir](../30-akislar/manuel-emir.md), [GUI sözleşmesi](../10-servisler/mtrader-trade-ui/backend-sozlesmesi.md) | Serbest emir yönlendirmesi, fiyat ölçeği ve gönderim yanıtı/BIST kabulü ayrımı |
| 5 | [Admin sürüm farkları](../10-servisler/mtrader-frontend-apps/dagitim-ve-surum-farklari.md), [alanların etkisi](../10-servisler/mtrader-frontend-apps/alanlar-ve-servislere-etkisi.md) | K-221/K-224; frontend alanları ile backend sürümü ve canlı oturum etkisi |

Kasıt/ürün kararı veya dış ortam gerektiren maddeler kod okuyarak kapatılmaz: örneğin [Teorik Fiyat K-04](../20-stratejiler/teorik-fiyat.md#bilinen-durumlar), canlı müşteri kurulumları ve ertelenmiş VİOP partition konuları. Açık sorunların tek indeksi [ACIK-KONULAR](../ACIK-KONULAR.md)'dır.

## Durum

Belgeler taslak olarak kalır. İncelenen belge kullanıcı tarafından kabul edilince durum etiketi ve manifest durumu kapsamına göre güncellenir; genel "devam" talimatı bütün dosyalara içerik onayı sayılmaz. Güncel çalışma/yayın durumu [oturum notlarında](../OTURUM-NOTLARI.md) tutulur.
