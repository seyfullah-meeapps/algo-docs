---
kapsam: Yerel doküman kontrol aracının kullanımı, kontrol kapsamı ve doğrulamadığı davranışlar
dogrulama: 2026-10-23
durum: taslak
---

# Doküman kontrolü

Repo kökünde, Python 3.10+ ve standart kütüphane ile:

```powershell
python _surec/kontrol.py
python _surec/kontrol.py --sources C:/Users/Seyf/algo-workspace
```

İlk komut yalnız bu bilgi tabanını okur. İkincisi kaynak klonlarını Git ile salt okunur kontrol eder. Fetch, checkout, config değişikliği, dosya yazımı ve ağ erişimi yapmaz. `safe.directory` yalnız çağrı kapsamında ilgili klon yoluna verilir; global Git ayarı yazılmaz. Hata varsa çıkış kodu 1, temizse 0'dır.

## Kontroller

- Markdown belgelerinde frontmatter: kapsam, ISO tarih, geçerli durum. Teknik bölüm belgelerinde kaynak kaydı; repo/branch/commit alanları ve commit yazımı.
- Göreli inline Markdown bağlantılarında hedef dosya ve başlık; repo dışına çıkan yollar. Fenced/inline kod örnekleri bağlantı sayılmaz.
- Dosya başına 400 satır sınırı; ACIK-KONULAR'da tekrarlanan K numaraları.
- Manifest repo kayıtlarında branch/commit/belge yolu ve hedef README varlığı.
- Yeni klasör düzeninde teknik kaynak denetimi `bilgi-tabani/` içindeki numaralı bölümlere, konu numarası denetimi `issues/ACIK-KONULAR.md` dosyasına uygulanır. Gizli araç dizinleri, geçici teslim/üretim alanları ve arşivlenmiş çalışma dosyaları taranmaz; junction/symlink hedeflerine girilmez.
- `--sources` ile beyan edilen commit'lerin ve yerel origin branch ref'lerinin commit nesnesine çözülmesi. Kısa/tam hash aynı nesneye çözülürse resolved_commits sayısında bir kez sayılır.

AGENTS.md ve CLAUDE.md agent talimatlarıdır; CHANGELOG oturum kaydıdır. Bu üç dosyaya otomatik frontmatter zorlanmaz. Sözlük, süreç ve indeks belgeleri kaynak bağlantılı derlemedir; doğrudan bir repo kaydı zorunluluğu teknik bölüm belgelerine uygulanır. Bu istisnalar [`kontrol.py`](kontrol.py)'de açıktır; teknik doğrulama etiketi üretmez.

## Sınırlar

Bu araç genel bir YAML/Markdown parser'ı değildir; bu reponun frontmatter ve inline bağlantı biçimini kontrol eder. Tam YAML sözdizimi, reference-style link'ler ve GitHub'ın bütün HTML/emoji başlık ayrıntıları için garanti vermez.

Commit nesnesinin bulunması iddianın o kodla doğru olduğunu, SHA'nın beyan edilen branch'in atası olduğunu veya remote'un güncel olduğunu kanıtlamaz. Ağdan tazelik kontrolü [`guncelleme.md`](guncelleme.md)'nin ayrı işidir. İddia/ölçek/emir/risk doğruluğu ilgili koddan incelenir.

`durum: dogrulandi` yapmaz. Kullanıcı taslak incelemesi, canlı binary/config, borsa davranışı, build ve kurtarma testi yerine geçmez. Son inceleme kaydı [`inceleme-durumu.md`](inceleme-durumu.md)'ndadır.
