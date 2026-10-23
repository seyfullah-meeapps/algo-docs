---
kapsam: Admin frontend — route'lar, oturum ve JWT, API istemcisi, listeler, CSV, formlar ve cache sınırları
kaynak:
  - repo: mtrader-frontend-apps
    branch: main
    commit: db10c12
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dogrulama: 2026-10-23
durum: taslak
---

# Arayüz ve oturum

Giriş [README](README.md). Alanların DB/canlı servis etkileri [alanlar-ve-servislere-etkisi](alanlar-ve-servislere-etkisi.md)'ndedir. Route kaynağı `app/routes.ts`; ortak layout `app/layouts/dashboard-layout.tsx`.

## 1. Route ve kod haritası

| Route | Kod | İş |
|-------|-----|----|
| `/` | `routes/index.tsx` | Başlangıç yönlendirmesi |
| `/login` | `routes/login.tsx` | Kullanıcı adı/parola, GuestGuard; giriş sonrası `/accounts` |
| `/accounts`, `/accounts/new`, `/accounts/:id/edit` | `routes/accounts/` | Hesap listesi/oluşturma/düzenleme |
| `/users`, `/users/new`, `/users/:id/edit` | `routes/users/` | GUI kullanıcısı listesi/oluşturma/düzenleme |
| `/order-users`, `/order-users/new`, `/order-users/:id/edit` | `routes/order-users/` | OUCH/FIX kullanıcısı listesi/oluşturma/düzenleme |

Her CRUD ailesinin `app/lib/api/<aile>.ts`, `app/hooks/use-<aile>.ts` ve `_components/*-form.tsx` dosyaları vardır. `root.tsx`: QueryClient → ThemeProvider → AuthProvider → Outlet; bildirimler Sonner Toaster.

## 2. Login ve token ömrü

1. `useLogin` → `authApi.login` → `POST /authorize`, düz `{username,password}`. Gateway `admin_ui.yaml` `body: credentials` kuralıyla protobuf alanına bağlar; istemci ayrıca `credentials` zarfı göndermez.
2. Backend `AdminLogin`, `Admins` tablosunu MD5 hex ile kontrol eder. JWT, trade-data-app'in ortak helper'ından üretilir; süre ve kapsamın sahibi [API](../trade-data-app/api.md)'dir.
3. `access_token`, AuthProvider state ve `localStorage['auth_token']` içine yazılır. `getUserFromToken` payload'dan username okur; imza doğrulamaz.
4. İlk açılışta `exp` kontrolü (`exp` saniye, Date.now ms), ardından `/authorize/check`. Başarısızlıkta token temizlenir. Backend check handler'ı boş olsa da auth interceptor'dan geçer.
5. AuthGuard korumalı route mount/değişiminde son kontrolden **5 dk** geçmişse yeniden check yapar. Periyodik timer değildir; sayfa açık dururken her 5 dk kontrol garantisi yoktur.
6. Logout tarayıcı state/token temizliğidir; sunucuda token iptal RPC'si ve refresh token akışı yoktur.

Frontend guard backend yetkisi değildir. Rol/kapsam, şifre saklama ve log bulguları [API § 11](../trade-data-app/api.md#11-şüpheli-davranış-adayları-doğrulanmadı-koddan-okuma)'de (K-16–K-18) tutulur.

## 3. HTTP ve cache

- `app/lib/api-client.ts`: `VITE_API_URL`, yoksa `http://localhost:3000/v1`; JSON Axios istemcisi, timeout **30 000 ms**. Her istekte localStorage token'ı Bearer header'a eklenir.
- HTTP 401 token'ı silip `/login`'e gider. Diğer hatalar `getErrorMessage` ile message → error → Axios mesajı sırasıyla gösterilir. `AuthProvider.verifyToken`, ağ hatası dahil her başarısızlıkta logout yapar.
- Query varsayılanları: `retry:false`, `refetchOnWindowFocus:false`, `staleTime:5 dk`; mutation retry yoktur. Başarı ilgili query anahtarlarını invalid eder, servis reload'u yapmaz.
- Liste yenilenirken önceki veri gösterilebilir (`placeholderData`). Başarı toast'ı HTTP başarısına dayanır; bütün ilişkilerin veya canlı oturumun doğrulaması değildir.

## 4. Liste, toplu silme ve CSV

| Liste | Filtre | Backend kaynağı |
|-------|--------|-----------------|
| Kullanıcılar | username | `/users` |
| Hesaplar | kullanıcı, OUCH/FIX kullanıcısı | `/users/accounts` |
| OUCH/FIX kullanıcıları | username, hesap, kanal, aktiflik | `/orders/users` |

Sayfa/sayfa boyu/sıralama/filtre URL search parametrelerindedir. API `range=[(page−1)*perPage,page*perPage−1]` (iki uç dahil), `sort=[field,ASC|DESC]`, JSON filter yollar. Gövde `{data:[...]}`, toplam `X-Total-Count` header'ındadır. Sunucuda sınır dışı range panic riski K-19'dur.

- Tekil ve seçili satırları toplu silme vardır. Toplu DELETE `filter={id:[...]}` kullanır; backend kayıtları tek tek siler, tüm seçim atomik değildir.
- CSV dışa aktarma PapaParse ve UTF-8 BOM kullanır. "Tümünü al" fonksiyonları `range=[0,9999]` yollar: **10 000 kayıt sınırı**. Kullanıcı/order-user ilişki seçim sorguları ilk 1000 kayıtla; order-user formunun hesap seçimi de ilk 1000 kayıtla sınırlıdır.
- Order-user CSV görünür kolonları içerir; parola export kolonları arasında yoktur. Backend liste yanıtının şifre içermesi ayrı konudur.
- CSV import ekranı yoktur; export veri geri yükleme mekanizması değildir.

## 5. Formlar

| Form | Doğrulama / düzenleme sınırı |
|------|------------------------------|
| Kullanıcı | Username zorunlu, e-posta biçimi, OTP, hesaplar. Edit'te username/email/phone pasif; yeni parola boşsa payload'a eklenmez. |
| Hesap | En az bir kullanıcı, hesap adı, sayısal limitler ≥0; fon kodu, order-user ve izinli strateji seçimleri. |
| Order-user | Username, IPv4, pozitif port, piyasa, kapasite ≥0; ikincil IP doluysa IPv4 kontrolü. FIX alt alanları kanala göre gösterilir. |

Order-user edit formu backend'den gelen parolayı varsayılanına alır; göster/gizle düğmesi vardır. Boşaltılan parola payload'dan silinir; backend'de korunacağı varsayılmaz ([alanlar § Şüpheli](alanlar-ve-servislere-etkisi.md#şüpheli)). Port üst sınırı ve FIX alt alan zorunlulukları frontend şemasında tam doğrulanmaz.

## Şüpheli

- **Cache invalidation (K-225):** Create/delete order-user yalnız `['order-users-list']` invalid eder. Hesap dropdown'u `['order-users']` anahtarıyla sorgular; eski seçenekler 5 dk fresh cache/yeniden sorguya kadar kalabilir. Update yalnız detay anahtarını ve listeyi invalid eder, kök dropdown'u etmez.
- **Export/seçim sınırı (K-226):** "Tüm" export 10 000, bazı ilişki seçimleri 1000 kayıtla sınırlıdır. Limit üstü canlı veri sayısı doğrulanmadı.
- Logout sonrası QueryClient cache'ini temizleyen çağrı yoktur; aynı browser'da farklı kullanıcıyla login sonrası görünürlük ayrıca test edilmelidir.
