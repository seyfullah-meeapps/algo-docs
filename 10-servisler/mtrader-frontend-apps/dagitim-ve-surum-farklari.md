---
kapsam: Admin frontend/backend branch eşleşmesi, development/master alan farkları, SPA build ve deploy sınırları
kaynak:
  - repo: mtrader-frontend-apps
    branch: main
    commit: db10c12
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: trade-data-app
    branch: master
    commit: 4a43e19
  - repo: mtrader-frontend-apps
    branch: feat/ouch-repeat-count-core-to-pin
    commit: 8ba2a67
dogrulama: 2026-10-23
durum: taslak
---

# Dağıtım ve sürüm farkları

Frontend referansı main db10c12; backend development 1cca9a8 / master 4a43e19. Yerel klon snapshot'larıdır; sunucudaki bundle/binary bu oturumda incelenmedi.

## 1. Frontend ↔ backend sözleşme farkı

| Alan | Panel main | Backend development | Backend master |
|------|------------|---------------------|----------------|
| Hesap repeat_count | Tip, zorunlu sayısal form alanı, payload | UserAccount tag 5 reserved; kaldırılmış | Mevcut |
| Order-user is_dedicated | Form, liste/CSV, payload | OrderUser tag 11 reserved; kaldırılmış | Mevcut |
| Order-user repeat_count | Tip/form yok | Optional int32; create yoksa 0, update yoksa koru | Yok |
| Order-user core_to_pin | Tip/form yok | Optional int32; create yoksa −1, update yoksa koru | Yok |

**K-221:** Panel development sözleşmesine yetişmemiş. Hesap tekrar alanı yeni backend'de hesap alanı değildir; OUCH tekrar/CPU ayarları panelden girilemez. Backend'den repeat_count gelmeyen edit formu `account.repeat_count` değerini zorunlu Zod number alanına verir; submit doğrulaması başarısız olabilir (koddan çıkarım; browser testi yapılmadı).

Bilinmeyen JSON alanının gateway'de reddedilmesi/atlanması çalıştırılarak test edilmedi; "bütün create/update kesin HTTP 400" sonucu çıkarılmaz. ⚠ master'da farklı: eski iki alan master'da hâlâ var; development uyumsuzluğu doğrudan prod arızası sayılmaz.

Sözleşme kaynakları trade-data-app `admin_ui.proto`/`admin_ui.yaml`; UI seçeneği backend desteğinin kanıtı değildir. Alanların tüketimi [alanlar-ve-servislere-etkisi](alanlar-ve-servislere-etkisi.md)'ndedir.

**Yolda (2026-10-23 fetch):** `feat/ouch-repeat-count-core-to-pin` (`8ba2a67`) tiplerinde yeni OUCH alanları bulunuyor, fakat main'e merge edilmemiş. Bu nedenle K-221 açık; feature'ı mevcut panel desteği sayma. [Güncel branch karşılaştırması](../../_surec/kaynak-karsilastirmasi-2026-10-23.md#6-son-iki-haftada-aktif-referansa-merge-edilmemiş-branchler).

## 2. Build ve servis etme

- `react-router.config.ts`: ssr:false, statik SPA. `npm run dev`: React Router dev server; `npm run typecheck`: typegen + TypeScript.
- Build script'i `react-router build` sonrası client dosyalarını build köküne taşır, client/server alt dizinlerini kaldırır. POSIX mv/rm kullanır; PowerShell'e doğrudan taşınabilir değildir.
- `npm start`, `react-router-serve ./build/server/index.js` bekler; build script'i server dizinini kaldırır. Production Dockerfile statik nginx kullanır.
- Dockerfile nginx:alpine, build → `/usr/share/nginx/html`; `default.conf` try_files ile SPA route fallback sağlar, 80/443 dinlenir.
- `VITE_API_URL` build sırasında bundle'a gömülür; çalışan container env'i hazırlanmış bundle'ı yeniden yazmaz.
- TLS sertifikası/özel anahtar imaja kopyalanır. Gerçek içerik burada tekrarlanmaz; secrets takibi K-15'tir.

## 3. CI ve müşteri yönlendirmesi

`.github/workflows/adminui.yml`: main değişiklikleri → müşteri matrisi, `npm install --include=dev && npm run build` → image build/push (`github.sha` tag) → VPN/SSH ile container stop/rm, pull ve yeni container.

API şablonu `https://admin<MUSTERI>.meeapps.com.tr[:<PORT>]/v1`; müşteri portları aynı değildir. UI nginx'i statik dosyaları sunar; /v1 yönlendirmesi dış proxy ile birlikte değerlendirilir. Port/config sahipliği [operasyon config referansı](../../40-operasyon/config-referansi.md#31-port-matrisi)'ndadır.

Bu oturumda CI, build veya deploy çalıştırılmadı; kaynak workflow'u başarılı canlı dağıtım kanıtı değildir.

## Şüpheli

- **Build/start uyumsuzluğu (K-228):** npm start server build'i bekler, build script'i o dizini siler. Docker/nginx ayrı yoldur; script amacı netleştirilmeli, çalıştırılarak test edilmedi.
- CI ayrı test/typecheck adımı olmadan build yapar; alan sözleşmesi farklarının deploy öncesi kontrol edildiği varsayılmaz. Canlı müşteri/backend eşlemesi ayrıca doğrulanmalıdır.
