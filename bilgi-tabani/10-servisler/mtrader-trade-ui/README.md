---
kapsam: mtrader-trade-ui — operatör arayüzü; giriş ve indeks; iki GUI'nin karşılaştırması, alt dosyalar, kısa özetler, deploy
kaynak:
  - repo: mtrader-trade-ui
    branch: development
    commit: b0474c3
  - repo: mtrader-trade-ui
    branch: main
    commit: 6715182
dogrulama: 2026-10-22
durum: taslak
---

# mtrader-trade-ui

**MTrader**, MeeApps'in geliştirdiği algoritmik işlem botunun ürün adıdır; bu repo onun kullanıcı arayüzüdür. Düzenli kullanıcıları müşteri aracı kurumların çalışanlarıdır; MeeApps ekibi geliştirme/test için kullanır. [Ürün ve geliştirme süreci](../../00-genel/urun-ve-gelistirme-sureci.md).

Operatör arayüzü. **Aynı repoda iki ayrı uygulama var**, ikisi de prod'da (parçalı geçiş). Hangi müşterinin hangisini kullandığı: [`00-genel/branch-ve-ortamlar.md`](../../00-genel/branch-ve-ortamlar.md#eski-gui--yeni-gui-parçalı-geçiş). Bir GUI sorusunda önce müşterinin hangi GUI'de olduğunu belirle.

| | Yeni GUI | Eski GUI |
|-|----------|----------|
| Branch | `development` (preprod'a da gidiyor) | `main` (prod imajı) |
| Kaynak | `app/` | `src/` |
| Teknoloji | React 19, React Router (framework mode, `ssr:false`), Vite, Zustand, TanStack Query, Dockview, Tailwind v4 | Vite + Ionic + Electron, React, context'ler |
| Geçmiş | Kişisel repoda (`mtrader-new`) sıfırdan yazıldı, 2026-09-14'te merge edildi (`7e14a00`) | Development'taki son hali `59f1689`; `main`'de üstüne yalnız deploy commit'leri |
| Varant Toplu | Var (`bulk-warrant`) | **Yok** |
| Toplu emirler | Toplu Emirler workspace'i (`collective-orders`): sabah, açılış, akşam, YİP | Tek ekran: "Sabah Emri" kartı (`COLLECTIVE_ORDERS` izni) → `OrderForm.tsx`; sabah, açılış, akşam. YİP yok |
| Fiyat ölçeği | Enstrümanın `decimalCount`'u | Çoğu yerde sabit ×1000 (VİOP'ta sapma riski, K-163) |
| WebSocket yeniden bağlanma | Var (sınırsız, jitter'lı; pasif emirler paneli hariç) | Yok |

**Yeni GUI'nin asıl ayrıntı kaynağı repodaki `AGENTS.md`'dir** (~1500 satır, güncel tutuluyor). Bu bilgi tabanı onu tekrar etmez; hangi başlığın hangi soruyu cevapladığı [yeni-gui § 8](yeni-gui.md#8-repo-agentsmd-başlık-haritası)'de.

## Alt dosyalar

| Dosya | Soru |
|-------|------|
| [`backend-sozlesmesi.md`](backend-sozlesmesi.md) | İki GUI ortak: bağlantı ayarları, login → OTP → token ve oturum, REST uçları (yeni/eski GUI kullanım sütunlu), WebSocket feed'leri ve iki GUI'nin socket yönetimi, strateji komut payload'u, emir gönderme, JSON lehçesi ve **ölçek tablosu** |
| [`yeni-gui.md`](yeni-gui.md) | Yeni GUI: teknoloji ve build, route ağacı ve guard'lar, workspace modeli, panel kataloğu, store'lar ve React Query anahtarları, ortak UI kuralları, eski GUI'den bilerek korunan/değiştirilen davranışlar, `AGENTS.md` başlık haritası |
| [`eski-gui.md`](eski-gui.md) | Eski GUI (prod): platformlar, routing, ekranlar, context'ler, tarayıcı depolaması, strateji ekranları ve fiyat ölçeği, emir ekranları, socket yönetimi, panel düzeni, auth, yeni GUI ile farklar, kod okuma ipucu |

Strateji başına UI ayrıntısı strateji dosyalarının "UI" bölümlerindedir ([`20-stratejiler/`](../../20-stratejiler/README.md)); bunlar çoğunlukla yeni GUI'yi anlatır, eski GUI farkları `eski-gui.md` § 3'te.

## Kısa özetler

Ayrıntı alt dosyalarda; burada yalnız yön bulmak için.

- **Backend:** trade-data-app. REST :6621 (grpc-gateway, protojson; 64-bit sayılar **string**), WebSocket :6623 (Go json, sayılar **number**). Login başarısız olsa da HTTP **200** döner, sonuç gövdededir; OTP 120 sn ([backend-sozlesmesi § 2](backend-sozlesmesi.md#2-kimlik-doğrulama-ve-oturum)).
- **WS feed'leri:** Yeni GUI `socketStore`'da altı merkezi socket tutar (market → `/ws/v1/best`, command → `/ws/v1/strategy`, order → `/ws/v1/orders`, bounds, equilibrium, itch). `/ws/v1/passive-orders`'ı yalnız pasif emirler paneli açar ([backend-sozlesmesi § 4](backend-sozlesmesi.md#4-websocket-feedleri)).
- **Strateji komutu:** `POST /v1/setStrategyCommands`, `map<string, Any>` alanlar; yeni GUI her komutta tam payload gönderir ([backend-sozlesmesi § 5](backend-sozlesmesi.md#5-strateji-komut-sözleşmesi-post-v1setstrategycommands)).
- **Workspace modeli:** `STRATEGY_WORKSPACE_CONFIGS` strateji başına route, panel, abonelik ve socket'i tanımlar; `matchesStrategyKey` `HFT_WARRANT_ADVANCED` ⊃ `HFT_WARRANT` ⊃ `HFT` önek çakışmasını çözer ([yeni-gui § 3](yeni-gui.md#3-workspace-modeli-applibstrategyworkspacets)).
- **Panel kapsamı eşit değil:** VWAP'ın tracker'ı yok; Teorik'in ayar modalı yok; Fon Takibi'nde tracker yok, strateji emir defteri üzerinden yönetilir, paketler ayrı özet panelinde.
- **Eski GUI'de tarayıcı depolaması:** token ve (OTP yeniden gönderimi için) şifre `sessionStorage`'da ([eski-gui § 2.5](eski-gui.md#25-tarayıcı-depolaması-önemli)).

Açık sorunlar: [`ACIK-KONULAR.md`](../../../issues/ACIK-KONULAR.md) § mtrader-trade-ui.

## Komutlar (yeni GUI)

```
npm install
npm run dev            # geliştirme
npm run check          # typecheck + lint + format + i18n + contrast (CI'da YOK; push öncesi elle)
npm run build          # deploy workflow yalnız install + build yapar; Vite type-check etmez
```

Node: `.nvmrc` `22.23.1`, `package.json` `engines` `>=22.22.0`. Test script'i yok; bu bir ürün kararı.

## Deploy

- `.github/workflows/algo_gui.yaml`, **elle tetiklenir**, müşteri listesi parametre olarak verilir.
- Branch → Docker imajı:
  - `development` → `mtrader-frontend-dev` (container `MTraderGuiDev`)
  - `preprod` → `mtrader-frontend-preprod`
  - `main` → `mtrader-frontend`
- Ayrıntı: [`00-genel/branch-ve-ortamlar.md`](../../00-genel/branch-ve-ortamlar.md#gui-dağıtımı-mtrader-trade-ui).
- ⚠ Workflow'daki müşteri kataloğunda SSH bilgileri düz metin (K-15).
