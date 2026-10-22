# AGENTS.md — algo-docs

Bu repo, MeeApps'in BIST algo/HFT stack'inin **AI agent'lar için yazılmış** bilgi tabanıdır. Okuyucu bir insan değil, bir agent: insanın sorusunu cevaplamak, özet çıkarmak veya kod üzerinde çalışmadan önce bağlam toplamak için buradan okursun.

## Önce bunu bil

- **Dil:** Metin Türkçe; teknik terimler, kod isimleri, wire alan adları İngilizce. Kullanıcıya hangi dilde sorulduysa o dilde cevap ver.
- **Doğruluk kaynağı kod.** Bu dokümanlar koddan damıtılmıştır ve belirli bir commit'e karşı doğrulanmıştır. Her dosyanın frontmatter'ında `kaynak` (repo, branch, commit) ve `dogrulama` (tarih) vardır. Cevabın kritikse (emir, fiyat ölçeği, risk, prod davranışı) ve repo erişimin varsa, ilgili koda bakıp teyit et.
- **Tazelik.** Repolar canlı; her gün commit alıyorlar. Bir bilginin güncel olup olmadığını sorarsan önce `manifest.yaml`'daki doğrulama commit'ine bak. Cevabında "şu commit itibarıyla" demekten çekinme.
- **Referans branch `development`.** Akış `development → preprod → master`. Prod'da çalışan davranış `master`'dır; dokümanlar `development`'ı anlatır ve prod'dan farklı olan yerleri açıkça işaretler (`⚠ master'da yok` gibi). İstisnalar `manifest.yaml`'da.
- **Gizli bilgi yok.** IP, kullanıcı adı, şifre, token `<PROD_IP>`, `<OUCH_USER>`, `<REDACTED>` gibi placeholder'larla maskelidir. Gerçek değeri tahmin etme, uydurma.
- **Bilmiyorsan söyle.** Dokümanda olmayan bir şeyi "muhtemelen" diye doldurma; "dokümanda yok, şu dosyaya bakılmalı" de.

## Çalışma oturumu (dokümanı yazan/güncelleyen agent için)

- **Başlarken** `OTURUM-NOTLARI.md`'yi oku: kararlar, mevcut durum, sıradaki işler orada.
- **Çalışırken** karar alındıkça ve iş bittikçe `OTURUM-NOTLARI.md`'yi güncelle; oturum bitmeden "Şu an" ve "Sıradaki" güncel olsun (context dolarsa sonraki oturum buradan devam eder).
- Bulunan sorun / şüphe / doğrulanmamış iddia → `ACIK-KONULAR.md`'ye **tek satır** + ayrıntı dosyasına link. Ayrıntı ilgili dosyada yazılır, indekste büyütülmez.

## Harita — hangi soru, hangi dosya

| Soru tipi | Bak |
|-----------|-----|
| Sistem nasıl çalışıyor, kim kimle konuşuyor, hot path ne? | `00-genel/sistem-haritasi.md` |
| Branch'ler, ortamlar (dev/preprod/prod), müşteri hangi sürümde? | `00-genel/branch-ve-ortamlar.md` |
| Bir terimin anlamı (ITCH, OUCH, tavan, KIE, kademe, unique_key…) | `00-genel/sozluk.md` |
| BIST kuralı (fiyat adımı, fiyat limitleri, seanslar, açığa satış) | `00-genel/borsa-kurallari.md` |
| Bir strateji ne yapar, parametreleri ne, hangi motorda, UI'da nerede? | `20-stratejiler/` — önce `20-stratejiler/README.md` (katalog) |
| Bir servisin/kütüphanenin iç yapısı | `10-servisler/<repo>/README.md` |
| Bir verinin/emrin uçtan uca yolculuğu | `30-akislar/` |
| Kurulum, deploy, config, açılış log'ları | `40-operasyon/` |
| Bilinen sorunlar, şüpheli davranışlar, doğrulanmamış iddialar | `ACIK-KONULAR.md` |
| Doküman çalışması nerede kaldı, hangi kararlar alındı? | `OTURUM-NOTLARI.md` |
| Bu dokümanlar nasıl güncellenir? | `_surec/guncelleme.md` |
| Dosyalar nasıl yazılır (frontmatter, kurallar)? | `_surec/yazim-kurallari.md` |

Her repo için tek satırlık görev, referans branch ve doğrulama commit'i: `manifest.yaml`.

## Dizin yapısı

```
AGENTS.md            ← buradasın
manifest.yaml        ← repo → branch → doğrulanan commit → doküman yeri
CHANGELOG.md         ← her güncelleme oturumunun kaydı
ACIK-KONULAR.md      ← açık sorunlar; tek satır + link
OTURUM-NOTLARI.md    ← kararlar, mevcut durum, sıradaki işler
00-genel/            ← cross-cutting: harita, branch/ortam, sözlük, borsa kuralları
10-servisler/<repo>/ ← repo başına bir klasör; README.md giriş noktası
20-stratejiler/      ← strateji başına bir dosya (motor + wire + UI birlikte)
30-akislar/          ← uçtan uca senaryolar
40-operasyon/        ← kurulum, deploy, config, log imzaları
_surec/              ← bu repoyu yazma ve güncelleme kuralları
```

**Tekrar yok kuralı:** Bir bilgi tek bir yerde yazılır, diğer yerler oraya link verir. Strateji mantığı `20-stratejiler/`'de, servisin genel iç yapısı `10-servisler/`'de. İki yerde çelişki görürsen bu bir hatadır — kullanıcıya bildir.

## Durum etiketleri

Frontmatter'daki `durum` alanı:

- `dogrulandi` — belirtilen commit'e karşı kodla doğrulandı.
- `taslak` — yazıldı ama henüz kullanıcı onayından geçmedi.
- `eski` — kaynak repo doğrulama commit'inden belirgin şekilde ilerledi; güncelleme bekliyor.
- `bos` — iskelet; henüz içerik yok.

`bos` veya `eski` bir dosyadan cevap veriyorsan bunu kullanıcıya söyle.
