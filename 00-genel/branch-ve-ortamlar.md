---
kapsam: Branch akışı, CI/CD, ortamlar, müşteriler ve hangi müşterinin hangi GUI sürümünde olduğu
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-frontend-apps
    branch: main
    commit: db10c12
dogrulama: 2026-10-22
durum: taslak
---

# Branch'ler ve ortamlar

## Branch akışı

`development → preprod → master` (bazı repolarda `master` yerine `main`).

- **development:** Aktif geliştirme. Bu bilgi tabanının referansı.
- **preprod:** Prod öncesi test. Piramit'in preprod sunucusunda koşar.
- **master / main:** Prod.
- Feature branch'ler development'a PR ile girer. Hotfix'ler bazen doğrudan preprod/master'a yapılır ve development'a geri taşınmayabilir. Güncellemede bunu kontrol et (`_surec/guncelleme.md`).

**İstisnalar** (`manifest.yaml`'da da var):

| Repo | Canlı branch | Neden |
|------|--------------|-------|
| `algo-configs` | `master` | `development` 2022'den beri güncellenmiyor |
| `mtrader-frontend-apps` | `main` | `development` 2026-03'ten beri güncellenmiyor |
| `Algo-Setup` | ortam başına | Branch = ortam (`development`, `preprod`, `main`, müşteri branch'leri). Birbirine merge edilmez; CI binary'leri doğrudan ilgili branch'e commit'ler. |
| `Warrant-Selector`, `Itch-Replayer` | `main` | Tek branch |

## C++ servislerin CI/CD'si

HftSrvProd (`hft.yml`), order-service (`orderservice.yml`), AlgorithmicTrading (`algo.yml`), trade-data-app (`dbservice.yaml`) aynı kalıbı izler:

1. `master` / `development` / `preprod`'a push → GitHub Actions tetiklenir.
2. Build `meeapps/maprodenv` Docker imajında yapılır. Bağımlı kütüphaneler (`libMARpc`, `libouchSDK`, `libMAItchSDK`, `libMAOrderSDK`, `libMAPerfSDK`) ve header'lar **Algo-Setup reposunun aynı isimli branch'inden** (`master` → `main`) alınır (`MAProdEnv/lib`, `MAProdEnv/include`).
3. HFT için iki varyant derlenir: `regular` ve `onload` (Solarflare Onload'lu SDK kütüphaneleriyle → `HftSrvProd_Onload`). Workflow'da `mlx` (Mellanox) varyantının adımları var ama matrix'te değil.
4. Çıkan binary Algo-Setup'ın ilgili branch'ine commit'lenir (ör. `HFT/HftSrvProd/`, commit mesajı "Commiting HFT Binary File").

Sonuç: **Bir SDK değişikliği, yeni `.so` dosyası Algo-Setup'a gelene kadar servis build'lerine yansımaz.** SDK repolarının CI'ı kütüphaneyi Algo-Setup'ın aynı isimli branch'inde `MAProdEnv/`'e yazar: itch-sdk (`itchsdk.yml`), MAOrderSDK (`ordersdk.yaml`), ouch-sdk (`ouch_actions.yml`; Doxygen dokümanını da algo-configs `doc/Development/Documentation/Ouch-SDK`'ya yazar), network-sdk (`network.yml`), performance-sdk (`performance.yml`).

Sunuculara dağıtım (Algo-Setup'tan sunucuya çekme, servis yeniden başlatma): `40-operasyon/`.

## GUI dağıtımı (mtrader-trade-ui)

`.github/workflows/algo_gui.yaml` — **elle tetiklenir** (`workflow_dispatch`, müşteri listesi parametresi; boşsa hepsi).

| Tetiklenen branch | Docker imajı | Container |
|-------------------|--------------|-----------|
| `development` | `meeapps/mtrader-frontend-dev:<müşteri>` | `MTraderGuiDev` |
| `preprod` | `meeapps/mtrader-frontend-preprod:<müşteri>` | `MTraderGuiPreProd` |
| diğer (`main`) | `meeapps/mtrader-frontend:<müşteri>` | `MTraderGui` |

Deploy: VPN (Piramit için IPsec, diğerleri FortiVPN) → SSH → `docker run`, müşteriye göre port eşlemesi. Aynı sunucuda dev ve prod GUI container'ları farklı isimlerle yan yana durabilir.

## Müşteriler / kurulumlar

GUI deploy kataloğunda (`algo_gui.yaml`) ve admin paneli workflow'unda (`mtrader-frontend-apps/.github/workflows/adminui.yml`) geçen kurulumlar:

| Kurulum | Not |
|---------|-----|
| Piramit | Prod |
| Piramit_Preprod | Preprod sunucusu |
| Piramit_Dev | Geliştirme sunucusu |
| Piramit_Algo | Ayrı algo sunucusu |
| A1 | |
| Alnus, Alnus_Yeni | Aynı sunucu, farklı portlar |
| Alnus Algo | Yalnızca admin paneli workflow'unda |
| Kanjo | |
| Global | |
| Marbas | |

Bağlantı bilgileri (host, kullanıcı, şifre) bu dokümanda **yer almaz**.

## Eski GUI / yeni GUI (parçalı geçiş)

- `mtrader-trade-ui` **`main` = eski GUI** (Vite + Ionic/Capacitor + Electron, kaynak `src/`).
- **`development` = yeni GUI** (React 19 + React Router 8, kaynak `app/`). Kişisel bir repoda (`mtrader-new`) sıfırdan yazıldı, 2026-09-14'te `development`'a merge edildi (merge `7e14a00`, PR #323). Eski GUI'nin development'taki son hali: `59f1689` (2026-09-09, merge'ün first parent'ı).
- **Müşteriler parçalı geçişte:** bazıları eski GUI'yi (prod imajı), bazıları yeni GUI'yi kullanıyor.

Kaynak: kullanıcı beyanı, 2026-10-22 (repodan çıkarılamıyor). Değişirse burası güncellenir.

| Kurulum | GUI |
|---------|-----|
| Piramit (prod) | eski |
| Piramit_Preprod | yeni |
| Piramit_Dev (test) | yeni |
| A1 | eski |
| Alnus (`alnus` subdomain) | eski |
| Alnus_Yeni (`alnusyeni` subdomain) | yeni |
| Kanjo | eski |
| Global, Marbas, Piramit_Algo | ❓ belirtilmedi |

Bir GUI sorusu cevaplanırken **müşterinin hangi GUI'yi kullandığı** belirleyicidir. Eski ve yeni GUI'nin davranış farkları: `10-servisler/mtrader-trade-ui/`.
