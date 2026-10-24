---
kapsam: Konu bazlı rehberde çalışan agent için kalıcı oturum ve yazım talimatları
dogrulama: 2026-10-24
durum: taslak
---

# Rehber üzerinde çalışacak agent için

Bu klasör insan için konu bazlı rehberdir; repo kökündeki AI bilgi tabanının okuyucu biçimini burada aynen uygulama. Açıklamalar temelden ilerler; anlaşılır örnek ve görseller kullanılır. Kök AGENTS.md'nin doğruluk, gizlilik, branch ve tek kaynak kuralları geçerlidir.

## Her oturumun başı

1. Kök `OTURUM-NOTLARI.md`, bu dosya, `README.md`, `kararlar.md`, `ilerleme.md` ve `calisma-duzeni.md` okunur.
2. İlerleme kaydındaki sıradaki konu ve kullanıcının son yönlendirmesi birlikte değerlendirilir. Arşivdeki eski ders sırasından devam edilmez.
3. İlgili konu dosyasının soru/yanıtları, kaynakları ve devam notu okunur. Mevcut yanıtlar yeniden keşfedilmeye çalışılmaz.

## Çalışırken

- Bir konu bir Markdown dosyasıdır; büyüyünce alt konulara böl ve indeksleri güncelle. Birleştirilmiş Word/PDF bu aşamada istenmedi.
- İndeks sırasıyla içerikleri doldur; iskeletleri yazılmış sayma. Güncel devam noktası `ilerleme.md` içindedir.
- Kullanıcının gerçek sorularını ve verdiği bağlamı ilgili konu dosyasındaki “Sorularımız ve netleşen noktalar” bölümüne tarihli ekle. Soru ile agent yorumunu ayır; cevaplanmayan soruya yanıt uydurma. Yapı kararlarının tek adresi `kararlar.md`.
- “Planlandı”, “yazıldı”, “kullanıcıyla konuşuldu/okundu” ayrı durumlardır. Sessizlik veya dosyanın açık olması içerik onayı değildir.
- Güncel borsa kuralı, seans, T+N, tedbir veya değişebilir teknik bilgi yazılırken resmi/birincil kaynakları internetten doğrula. URL, erişim, belge sürümü ve yürürlük kapsamını yaz. İnternetten bilgi doğrulamayı uygulama testi olarak sunma.
- Projenin davranışında kod esas: kaynak repo/branch/commit, GUI ve backend alan eşleşmesi, ölçek ve prod farkı belirtilir. Canlı binary/config doğrulanmadıysa bunu söyle.
- Teknik ayrıntının aslı kök bilgi tabanında kalır. Burada açıklama, öğretici örnek ve kaynak bağlantısı bulunur; çelişkili ikinci bir parametre sözleşmesi üretilmez.
- Frontend kaynaklarından çizilen SVG temsili şemadır; gerçek ekran görüntüsü diye sunulmaz. Ekrana erişilemiyorsa gerekli çekim tarifiyle yer tutucu bırakılır.
- Öğrenme/rehber çalışması açık bug kuyruğunu otomatik yeniden açmaz. Gerçek yeni teknik bulgu kök açık konu düzenine göre kaydedilir.
- Mevcut hataları rehberin okuyucu anlatımına ve dikkat kutularına ekleme. Hata takibi teknik bilgi tabanı/issue tarafında kalır. Düzeltme doğrulanınca etkilenen rehber dosyaları ve örnek/görsel/test beklentileri güncellenir; bu kontrolü düzeltme kapanışının parçası yap. Düzelmemiş hedef davranışı çalışıyormuş gibi yazma. Ayrıntılı bakım düzeni `calisma-duzeni.md` içindedir.

## Her oturumun sonu

İlgili konu dosyasının devam notu, bölüm/ana indeks durumları, `ilerleme.md` ve kök oturum notlarının “Şu an/Sıradaki” alanları güncellenir. Yeni karar varsa `kararlar.md`, belge değişikliği varsa kök `CHANGELOG.md` güncellenir. Yapısal kontrol ve diff kontrolü çalıştırılır. Önceki push reddi onaysız tekrar denenmez.
