---
kapsam: gRPC, sözleşme ve streaming kavramlarının projedeki kontrol ve bildirim yollarıyla ilişkisi
dogrulama: 2026-10-24
durum: taslak
---

# Ders 00 — gRPC ve servis iletişimi

Eski dersin iki tekrarlı anlatımı birleştirildi. Ön koşul: frontend'deki istek/yanıt fikri. Amaç: UI isteği ile servis çağrısını, çağrı başarısı ile emir sonucunu ayırmak.

## Önce problem

Frontend bir API'den veri ister. Aynı ihtiyaç backend programları arasında da vardır: C++ motor hesap listesini Go servisinden ister; Go servis strateji komutunu C++ motora iletir. Bunlar ayrı süreçlerdir. Ağ gecikebilir, bağlantı kesilebilir veya cevap gelmeden zaman aşımı olabilir.

RPC, başka bir süreçteki işlemi tanımlı bir arayüz üzerinden çağırmaktır. gRPC bunun için kullanılan altyapıdır. `.proto` dosyası mesajların alanlarını ve çağrıları tanımlar; bu sözleşmeden Go/C++ gibi diller için istemci/sunucu kodu üretilebilir. Protobuf ikili serileştirmedir; kendi başına “sıkıştırma” demek değildir. gRPC genellikle HTTP/2 üzerinden çalışır. Tipli sözleşme iki tarafın her sürümde otomatik uyumlu olduğu garantisi vermez.

**Unary:** tek istek, tek yanıt. Hesap listesini istemek buna örnektir. **Server streaming:** bir abonelik isteğine karşı sunucu zaman içinde birden fazla olay gönderir. Emir bildirimlerini dinlemek buna örnektir. Bağlantının açık olması her olayın tüketildiğini veya yeniden bağlantıda geçmişin otomatik geldiğini kanıtlamaz.

## Bizdeki yol

```text
UI → REST → trade-data-app → gRPC → ilgili motor
UI ← WebSocket ← trade-data-app ← gRPC stream ← motor olayları
```

Tarayıcı motora doğrudan gRPC çağırmaz. `trade-data-app`, REST/WS giriş noktası ve servisler arası aracı rolündedir. Aynı uygulama bazı çağrılarda sunucu, bazı çağrılarda istemcidir. REST tarafındaki grpc-gateway ile hub'ın başka motora yaptığı gRPC çağrısı iki ayrı adımdır.

HFT'nin handoff sonrası hızlı emir yolu ise `ITCH → motor kararı → MAOrderSDK → BIST OUCH` olur. gRPC ile komut taşımak ve OUCH ile borsaya emir göndermek farklı işlerdir. Handoff öncesindeki gateway yolu için [sistem haritasına](../../bilgi-tabani/00-genel/sistem-haritasi.md) bak.

## PM açısından neyi ayırıyoruz?

“Başlat'a bastım, başarılı döndü” en fazla ilgili isteğin işlenmesine dair kanıttır. Stratejinin çalışır duruma geçtiği, tetik oluştuğu, emrin gönderildiği ve borsada kabul edildiği ayrı olaylarla doğrulanır. Bir komut başarılı olup hiç emir çıkmaması geçerli bir bekleme durumu olabilir.

| Belirti | İlk toplanacak kanıt |
|---|---|
| UI isteği hata verdi | Endpoint, maskeli payload, HTTP yanıtı, zaman |
| İstek başarılı, motor durumu değişmedi | Hub yönlendirmesi, motor komut kaydı ve dönen durum |
| Motor emir üretmiş, UI göstermiyor | Emir callback'i, stream ve WS olayları, UI aboneliği |

## Alıştırma

1. REST 200 döndü; BIST kabulünü kanıtlayan hangi olay hâlâ eksik?
2. UI'da emir görünmüyorsa emir hiç gönderilmedi diyebilir miyiz?
3. Bir servis aynı anda hem gRPC client hem server olabilir mi?

Yanıt anahtarı: 1. İlgili emrin kabul olayı. 2. Hayır; bildirim yolu da incelenmeli. 3. Evet; çağrının yönüne bağlıdır.

Kaynaklar: [sistem haritası](../../bilgi-tabani/00-genel/sistem-haritasi.md), [hub veri akışı](../../bilgi-tabani/10-servisler/trade-data-app/veri-akisi.md), [strateji başlatma](../../bilgi-tabani/30-akislar/strateji-baslatma.md).

## Oturum kaydı

Eski kayıt revize edildi. Bu sürüm kullanıcıyla henüz konuşulmadı; yeni soru/yanıt ve alıştırma sonucu yok.
