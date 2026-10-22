---
kapsam: Bu repodaki dokümanların nasıl yazılacağı
dogrulama: 2026-10-22
durum: taslak
---

# Yazım kuralları

## Frontmatter (her dosyada zorunlu)

```yaml
---
kapsam: Tek cümle — bu dosya neyi cevaplar
kaynak:                       # bilginin damıtıldığı kod; birden fazla olabilir
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc           # kısa SHA yeterli
dogrulama: 2026-10-22         # kodla en son karşılaştırıldığı gün
durum: dogrulandi             # dogrulandi | taslak | eski | bos
---
```

Kaynağı kod olmayan dosyalarda (ör. borsa kuralları) `kaynak` yerine `dis_kaynak` altında URL ve erişim tarihi yazılır.

## İçerik

- **Agent için yaz.** Süsleme, motivasyon cümlesi, "bu bölümde şunu öğreneceksiniz" yok. Olgu, isim, yer.
- **Tek konu, tek dosya.** Bir dosya bir soruyu cevaplar. 400 satırı geçiyorsa bölünmeli.
- **Tekrar yok.** Bilgi tek yerde yazılır; başka yerde gerekiyorsa link verilir. Kısa bir tekrar kaçınılmazsa (ör. tablo özeti) kaynağı linklenir.
- **Kod referansı ver.** `src/Strategy/HftClassic.cpp` gibi repo-göreli yol; gerekiyorsa sembol adı (`HftClassic::onHeaderChanged`). Satır numarası verme — hızlı eskiyor; sembol adı yeterli.
- **Birim ve ölçek açık yazılır.** Fiyat raw mı TL mi, ×1000 mi, ms mi s mi — her wire alanında belirtilir. Bu sistemdeki en pahalı hatalar ölçek hatalarıdır.
- **Prod farkı işaretlenir.** `development`'ta olup `master`'da olmayan davranış: `⚠ master'da yok (2026-10-22)`.
- **Bilinen bug ≠ tasarım.** Kasıtlı garip davranışlar "kasıtlı" diye, bilinen buglar "bug" diye etiketlenir; ikisi karıştırılmaz.
- **Belirsizlik saklanmaz.** Doğrulanamayan iddia `❓ doğrulanmadı:` önekiyle yazılır.

## Gizli bilgi

IP, hostname, kullanıcı adı, şifre, token, müşteri adı → placeholder: `<PROD_IP>`, `<OUCH_USER>`, `<REDACTED>`, `<MUSTERI>`. Config örneklerinde değerler maskelenir, anahtar isimleri kalır.

## Dosya adları

Küçük harf, Türkçe karakter yok, kelimeler `-` ile: `emir-yasam-dongusu.md`. Her klasörün giriş noktası `README.md`.
