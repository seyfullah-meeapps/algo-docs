---
kapsam: Admin alanlarının DB karşılığı, ilişkiler, çalışan servislere yansıma sınırları ve kayıt sorunları
kaynak:
  - repo: mtrader-frontend-apps
    branch: main
    commit: db10c12
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
  - repo: order-service
    branch: development
    commit: b86c0cf
dogrulama: 2026-10-23
durum: taslak
---

# Alanlar ve servislere etkisi

Kaynak: panel `app/types/`, form/API fonksiyonları; trade-data-app `api/protobuf-spec/admin_ui.{proto,yaml}`, `pkg/servicemodels/admin_api.go`, `pkg/db/mysql/admin_db.go`. Kesin endpoint listesi [API § 8](../trade-data-app/api.md#8-adminservice-admin_uiproto--admin_uiyaml-admin_apigo--rest-adminapiport)'dedir. Eski/yeni backend farkları [dağıtım ve sürüm farkları](dagitim-ve-surum-farklari.md#1-frontend--backend-sözleşme-farkı)'ndadır.

## 1. Kayıtlar ve ilişkiler

| Panel kaydı | DB | İlişkiler |
|-------------|----|-----------|
| GUI kullanıcısı | `Users` | account_ids → `Users_Accounts` |
| Hesap | `Accounts` | user_ids → `Users_Accounts`; order_user_ids → `Users_Ouch`; allowed_strategy_ids → `Account_Allowed_Strategies` |
| OUCH/FIX kullanıcısı | `Ouchs` | account_ids → `Users_Ouch` |
| Admin giriş hesabı | `Admins` | Panelde CRUD yok; GUI kullanıcısı yaratmak admin yaratmaz |

Int64 id'ler JSON'da string olabilir. Hesap API'si order_user_ids/allowed_strategy_ids öğelerini String ile normalize eder. Bunlar hesap numarası veya strategyIdentifier değildir; allowed_strategy_ids backend `Strategies` kayıt id'leridir. UI enum etiketleriyle eşitlik varsayılmaz.

## 2. Hesap alanları

| JSON alanı | Anlam / etki |
|------------|-------------|
| `account_name` | Emirde kullanılan hesap adı; yalnız görsel etiket değil |
| `user_ids` | GUI kullanıcısı ↔ hesap; form en az bir kullanıcı ister |
| `order_user_ids` | Hesabın izinli OUCH/FIX kullanıcıları |
| `allowed_strategy_ids` | İzinli strateji DB kayıtları; sabit UI liste sorunu § Şüpheli |
| `order_capacity` | Accounts.orderCapacity; tüketim/birim [risk](../order-service/risk.md)'te, etiketten lot/fiyat limiti çıkarılmaz |
| `remaining_count` | Fazla sabah kopyası iptalinde tutulacak kabul sayısı; lot değil |
| `repeat_only_top`, `repeat_levels` | Sabah tekrar fiyat seviyeleri; [toplu-emirler](../order-service/toplu-emirler.md) |
| `is_cancel_allowed` | Fazla sabah kopyası iptal izni; kapalıysa kopyalar kalabilir (K-92) |
| `client_type`, `agency_fund_code` | BIST hesap kategorisi/fon kodu; [SDK hesap alanları](../order-service/sdk-ve-oturumlar.md) |
| `repeat_count` | Panelde mevcut; development AdminService hesabında kaldırılmış, yeni alan OUCH kullanıcısında |

Panel hesap tipi olarak müşteri/fon sunar; proto daha fazla AccountClientType tanımlar. DB'de bir tipin bulunması panelden seçilebildiği anlamına gelmez.

## 3. OUCH/FIX alanları

| Alan | Davranış |
|------|----------|
| username/password, ana/ikincil IP-port | BIST oturum bilgisi; gerçek değerler bu belgede yazılmaz |
| `market` | MARKET_TYPE_EQUITY / MARKET_TYPE_DERIVATIVE |
| `protocol` | Proto UNKNOWN=0, OUCH=1, FIX=2; normal panel seçimi enum adı gönderir. UI key:0/1 wire enum'u değildir. |
| `capacity` | OUCH kullanıcı kapasitesi; tekrar hesabının girdisi |
| `is_production` | order-service ortam filtresi; yalnız görsel tercih değil |
| `is_active` | DB aktifliği; kaydetmek açık soketi otomatik kapatmaz |
| `only_morning_order_user` | Sabah sonrası devir; applicationUser eşlemesi de gerekir |
| `account_ids` | İzinli hesaplar |
| `sender_sub_id`, `sender_comp_id`, `target_comp_id` | FIX kimlikleri |
| `is_dedicated` | Panelde var, development proto'da kaldırılmış |
| `repeat_count`, `core_to_pin` | Development backend'de var, panelde yok. Create yoksa 0/−1; update yoksa DB değeri korunur. CPU −1 pinsizdir. |

`applicationUser` frontend/proto alanı değildir. `AdminDB.InsertOrderUser` yeni kullanıcıda **sabit DB id 4** yazar; update eşlemeyi değiştirmez. DB'de 4'ün hangi uygulama kullanıcısı olduğu koddan belirlenemez. Morning-only işaretlemek doğru HFT uygulamasına devri tek başına kurmaz.

## 4. Kaydetmenin canlı etkisi

```text
Form → Axios REST → grpc-gateway AdminService → AdminApi → AdminDB → MySQL
```

- Panel CRUD'u motor komutu, OUCH disconnect/connect, reload veya restart çağırmaz.
- Hesap/order-user update'lerinde ilişki listeleri silinip yeniden yazılır. Eksik/boş liste patch anlamına gelmez; ilişkiler kaldırılabilir. Eşzamanlı eski formlar ilişkileri ezebilir.
- Transaction olsa da bazı ilişki insert hataları log/continue ile atlanır ve commit sürer. HTTP başarı bütün ilişkilerin yazıldığını kanıtlamaz; yeniden GET ile kontrol gerekir.
- order-service `MAOSdkManager::StartProperly` kullanıcıları, route'ları ve connection ayarlarını açılışta kurar. DB kaydı açık oturumu kendiliğinden yeniden yapılandırmaz.
- Toplu hazırlık ise `UserService::GetUsers(protocol,part,mode)` ile DB'den taze okur. Yeni DB değeri ile önceden kurulmuş SDK bağlantısı farklı anlara ait olabilir; "her şey anında" veya "hiçbir şey restart'a kadar uygulanmaz" genellemeleri yanlıştır.
- Handoff sonrası HFT bağlantısı da panelden güncellenmez. Gerekli yeniden devir/restart değerlendirmesi [kopma ve kurtarma](../../30-akislar/kopma-ve-kurtarma.md)'dadır; kayıt başarısı bağlantı testi değildir.

## Şüpheli

- **Sabit uygulama kullanıcısı (K-223):** Yeni kayıt applicationUser=4, panelden seçilemez. Müşteri DB eşlemesi doğrulanmalı. AlgoProd'un handoff'u devralmadığı referans sürüm için K-220.
- **Boş order-user parolası (K-224):** Frontend boş parolayı payload'dan çıkarır. Proto string yokluğu boş string olur; `AdminApi.UpdateOrderUser` → `AdminDB.UpdateOrderUser` SQL'i parolayı koşulsuz yazar. Formdaki parolayı boşaltıp kaydetmek DB parolasını silebilir. GUI kullanıcısı UpdateUser boş parolayı korur; iki yol aynı değildir. Canlı test yapılmadı.
- **İzin listesi eskimiş (K-222):** `app/types/accounts.ts` listesi 0–12'de biter, 12'yi Basket Arbitraj adlandırır; 13/14/15 seçenekleri yoktur. Form backend GetStrategies kullanmaz. Gerçek DB id eşleşmeleri ve mevcut izinlerin tekrar kayıtta korunması doğrulanmalı.
- **Kısmi ilişki kaydı (K-227):** AdminDB insert/update ilişki hatalarının bazıları rollback yerine devam eder; başarıya rağmen seçimin bir kısmı eksik kalabilir. Toplu DELETE de tek transaction değildir.
- **Parola görünürlüğü:** GetOrderUsers/GetOrderUser düz metin OUCH/FIX parolası döner, form belleğine girer. Rol/log sorunları mevcut K-16/K-17 kapsamındadır.
