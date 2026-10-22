---
kapsam: Dokümanların repolardaki yeni commit'lere göre periyodik güncellenme prosedürü
dogrulama: 2026-10-22
durum: taslak
---

# Güncelleme prosedürü

Kullanıcı "dokümanı güncelleyelim" dediğinde agent bu adımları izler. **Kullanıcı onayı olmadan dokümana yazılmaz.**

## 1. Repoları çek

`manifest.yaml`'daki her repo için referans branch'i fetch et. Çalışma kopyası olarak kullanıcının günlük klonlarına değil, ayrı bir workspace'e (mevcut kurulumda `C:\Users\Seyf\algo-workspace`) bak — günlük klonlarda commit edilmemiş iş olabilir.

```bash
git -C <repo> fetch origin
git -C <repo> log --oneline <dogrulanan_commit>..origin/<branch>
```

## 2. Değişiklik özeti çıkar

Her repo için `<dogrulanan_commit>..origin/<branch>` aralığını incele:

- Merge commit'lerini PR başlığıyla grupla (ne geldi).
- Diff'te dokümanı etkileyen değişiklikleri ayıkla: yeni/değişen strateji, wire alanı, komut, config anahtarı, thread modeli, protokol, DB şeması, endpoint.
- Saf refactor, log, format değişikliklerini "dokümanı etkilemez" diye tek satırda geç.
- Etkilenen doküman dosyalarını listele.

Ayrıca kontrol et:
- `preprod`/`master`'da olup `development`'ta olmayan commit (hotfix) var mı?
- Yeni açılmış, aktif feature branch'ler (son 2 hafta) — henüz development'ta olmayan büyük işler (ör. yeni strateji) varsa "yolda" diye not et.

## 3. Kullanıcıya sun

Repo başına kısa özet + "şu dosyalar şöyle değişecek" önerisi. Kullanıcı doğrular, düzeltir veya eler.

## 4. Yaz

Onaylanan değişiklikler için:
- İlgili dosyaları güncelle; frontmatter'da `commit` ve `dogrulama`'yı yenile.
- `manifest.yaml`'da `dogrulanan_commit`, `commit_tarihi`, `son_guncelleme`.
- `CHANGELOG.md`'ye oturum kaydı ekle.
- `main`'e commit'le ve push et (içerik kullanıcı onayından geçtiği için ayrı PR gerekmez).

## Notlar

- Branch akışı `development → preprod → master`. İstisnalar (`algo-configs` master, `mtrader-frontend-apps` main, `Algo-Setup` ortam branch'leri) `manifest.yaml`'da.
- Bir dosyayı güncelleyemiyorsan (zaman, kapsam) `durum: eski` yap; agent'lar bunu cevaplarında belirtir.
