---
kapsam: Admin paneli giriş noktası — rolü, kaynak sürümler, alt belge indeksi ve trade-data-app sınırı
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
dogrulama: 2026-10-23
durum: taslak
---

# mtrader-frontend-apps — Admin paneli

GUI operatörlerini, hesapları, OUCH/FIX kullanıcılarını ve ilişkilerini yönetir. Emir göndermez, strateji çalıştırmaz, servis restart etmez. MySQL'e doğrudan bağlanmaz; trade-data-app AdminService REST gateway'ini kullanır.

| Soru | Belge |
|------|-------|
| Route, liste/CSV, form, auth, HTTP istemcisi ve cache nerede? | [Arayüz ve oturum](arayuz-ve-oturum.md) |
| Alan hangi DB kaydını etkiler; kaydetmek canlı servise ne zaman yansır? | [Alanlar ve servislere etkisi](alanlar-ve-servislere-etkisi.md) |
| Branch, frontend/backend farkları, build/deploy nasıl? | [Dağıtım ve sürüm farkları](dagitim-ve-surum-farklari.md) |
| REST/RPC uç listesi ve gateway gövde biçimi | [trade-data-app API § 8](../trade-data-app/api.md#8-adminservice-admin_uiproto--admin_uiyaml-admin_apigo--rest-adminapiport) |
| DB ilişkileri | [trade-data-app şema](../trade-data-app/sema.md) |
| Sabah/handoff ve restart | [Sabah emri](../../30-akislar/sabah-emri-ve-handoff.md), [kopma/kurtarma](../../30-akislar/kopma-ve-kurtarma.md) |

## Önce bil

- Referans **main db10c12**; development güncel referans değildir. Repo genel branch kuralının istisnasıdır.
- React 19, React Router 7 framework mode, Vite, TypeScript, Tailwind 4; SPA (ssr:false). React Query veri/cache; React Hook Form + Zod formlar. Tam sürümler package.json/lock dosyasındadır.
- Paneldeki alan ile backend desteği aynı şey değildir: Dedicated/hesap tekrar alanları eski sözleşmeye aittir; development backend farklıdır.
- DB kaydı başarılı olması canlı OUCH oturumunun güncellendiğini kanıtlamaz; otomatik reload varsayılmaz.
- Admin girişleri Admins, panelin yönettiği GUI kullanıcıları Users tablosundadır. Admin hesapları için CRUD ekranı yoktur.
- Kaynak branch'ler incelendi; canlı sunucunun bundle/binary sürümü doğrulanmadı. Dosyalar kullanıcı incelemesini bekleyen taslaktır.
