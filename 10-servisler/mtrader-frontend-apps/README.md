---
kapsam: mtrader-frontend-apps — Admin paneli; ekranlar, backend, OUCH/FIX kullanıcı alanları, deploy
kaynak:
  - repo: mtrader-frontend-apps
    branch: main
    commit: db10c12
dogrulama: 2026-10-22
durum: taslak
---

# mtrader-frontend-apps (Admin paneli)

Müşteri kurulumlarında DB ayarlarını arayüzden yönetmek için kullanılan web paneli: kullanıcılar, hesaplar, OUCH/FIX kullanıcıları ve aralarındaki izinler.

- Canlı branch **`main`**; `development` 2026-03'ten beri güncel değil.
- Teknoloji: React Router (framework mode), Vite, TypeScript, Tailwind.

## Ekranlar (`app/routes/`)

| Route | Ne |
|-------|----|
| `login` | Admin girişi (`AdminService.Login`) |
| `users` (list / new / edit) | Uygulama kullanıcıları (GUI operatörleri) |
| `accounts` (list / new / edit) | Hesaplar; kullanıcı, OUCH kullanıcısı ve strateji izinleri |
| `order-users` (list / new / edit) | **OUCH/FIX kullanıcıları** (DB `Ouchs`) |

**OUCH/FIX kullanıcı formu alanları:**

| Alan | Anlam |
|------|-------|
| Kullanıcı adı, Parola | |
| Piyasa | Equity / Derivative |
| Kapasite | Sabah emri tekrar hesabında kullanılır |
| Kanal | OUCH / FIX |
| İzinli hesaplar | |
| FIX alanları | Sender Sub ID, Sender Comp ID, Target Comp ID |
| Ana / ikincil IP ve port | |
| Production Ortamı | order-service `mode` filtresi bu alana bakar |
| Aktif | |
| Dedicated Bağlantı | |
| **Yalnızca Sabah Emri** (`only_morning_order_user`) | Bu kullanıcı sabah emirlerinden sonra **HFT'ye devredilir** (OUCH handoff). Bkz. [order-service](../order-service/README.md#ouch-handoff-hftye-devir). |

## Backend

trade-data-app `AdminService` (`api/protobuf-spec/admin_ui.proto`), grpc-gateway REST üzerinden (`server.adminApiPort`, örnek 6688). İstemci tabanı `VITE_API_URL`; müşteri başına `https://admin<musteri>.meeapps.com.tr/v1`.

## Deploy

`.github/workflows/adminui.yml`, müşteri matrisi: Piramit, Alnus, Alnus Algo, A1, Marbas, Global, Kanjo. Docker imajı, VPN üzerinden kurulur.
