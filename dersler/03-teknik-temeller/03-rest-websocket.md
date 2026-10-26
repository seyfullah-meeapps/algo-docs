---
kapsam: HTTP istek/yanıt, REST, kimlik/yetki, WebSocket ve reconnect
kaynak:
  - repo: trade-data-app
    branch: development
    commit: 1cca9a8
dis_kaynak:
  - url: https://www.rfc-editor.org/rfc/rfc9110.html
    erisim: 2026-10-25
  - url: https://www.rfc-editor.org/rfc/rfc6455.html
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# HTTP, REST ve WebSocket

Frontend'de bir sayfanın ilk verisini almakla, o sayfayı açık tutarken fiyatların güncellenmesi farklı ihtiyaçlardır. Birincisini “şu anki listeyi getir”, ikincisini “bundan sonraki değişiklikleri bana bildir” diye düşünebiliriz.

## HTTP: soru ve yanıt

**HTTP**, istemcinin istek gönderip sunucunun yanıt verdiği uygulama protokolüdür. İstek; yöntem, hedef adres, header'lar ve gerekirse body taşır. Yanıtın durum kodu ve gerekirse içeriği vardır. **HTTPS**, bu iletişimin TLS ile korunan halidir; kullanıcının iş yetkisini tek başına sağlamaz.

**REST**, HTTP'nin diğer adı değildir; kaynaklar ve ortak işlem anlamları etrafında kurulan bir mimari yaklaşımdır. Günlük konuşmada JSON dönen birçok HTTP API'ye REST denebilir. Asıl sözleşme, endpoint'in ne kabul edip ne döndürdüğüdür.

Öğretici bir API düşünelim: `GET /ornek/stratejiler/42` stratejiyi okumak, `POST /ornek/stratejiler/42/baslat` başlatma talebi yollamak için tanımlanmış olsun. Bu adresler **temsili**, gerçek MTrader endpoint'leri değildir. İkinci isteğin yanıtı “talebi aldım” olabilir; stratejinin piyasa emri ürettiği anlamına gelmeyebilir.

## Durum kodu hangi soruya yanıt verir?

| Kod | HTTP düzeyinde kısa anlamı | Takipte neye bakılır? |
|---|---|---|
| 200 | İstek başarılı işlendi | Body'deki iş sonucu |
| 202 | İşleme kabul edildi | Sonraki tamamlanma durumu |
| 400 | İstekle ilgili istemci hatası | Alanlar ve hata açıklaması |
| 401 | Geçerli kimlik doğrulama bilgisi yok | Oturum/token durumu |
| 403 | Sunucu isteği yerine getirmeyi reddediyor | Yetki ve erişim politikası |
| 500 | Sunucu isteği tamamlayamadı | Log ve korelasyon bilgisi |

Tablo genel anlamları anlatır; MTrader'ın her endpoint'inde bu kodların tamamının kullanıldığı iddiası değildir. Bir API, HTTP 200 içindeki body'de iş kuralı reddi taşıyabilir. “Network sekmesinde yeşil” ile “strateji çalıştı” aynı sonuç değildir. [HTTP semantiği — RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)

**Authentication**, “kimsin?”; **authorization**, “bu işi bu hesapta yapabilir misin?” sorusudur. Giriş yapmış bir kullanıcı, her hesap veya strateji için yetkili olmayabilir. Hata incelemesinde token'ın kendisini paylaşmak yerine zamanı, kullanıcı/hesap kapsamını ve maskelenmiş hata bilgisini kaydederiz.

## WebSocket: açık hat üzerinden olaylar

**WebSocket**, kurulduktan sonra her iki tarafın da mesaj gönderebildiği sürekli bir iletişim kanalıdır. Sürekli “fiyat değişti mi?” diye sormak yerine değişiklikleri açık hattan dinlemek gibi düşünebiliriz. WebSocket'in mesaj taşıması, hangi ürünlerin abone olunduğunu veya mesajların iş anlamını kendiliğinden belirlemez. [WebSocket — RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)

**Abonelik**, uygulama düzeyinde “şu ürünün/hesabın olaylarını istiyorum” seçimidir. Bağlantı kurulmuş olsa bile ilgili abonelik kurulmamışsa beklenen olay gelmeyebilir. **Push**, sunucunun her olay için yeni bir istemci isteği beklemeden veri göndermesidir.

MTrader'ın referans hub kodunda ayrı WebSocket yolları vardır; örneğin `/ws/v1/orders/start` ve `/ws/v1/strategy/start`. GUI servis sözleşmesi HTTP eşlemelerini de tanımlar. Ekrandaki liste isteği ile canlı olay hattını ayrı gözlemlemek anlamlıdır. Gerçek sözleşmeler [hub API](../../10-servisler/trade-data-app/api.md) ve [veri akışı](../../10-servisler/trade-data-app/veri-akisi.md) belgelerindedir.

## Sayfa açılıyor ama fiyatlar donuyor: nasıl düşünürüz?

Varsayımsal senaryo: liste HTTP ile geldi, ardından WebSocket koptu. Ekran eski listeyi göstermeye devam ediyor. Kullanıcı açısından uygulama açık, fakat veri artık güncel olmayabilir. **Bağlantı durumu ile verinin son güncelleme zamanı farklı bilgilerdir.**

Yeniden bağlantı (**reconnect**) kaçırılan olayları tek başına geri getirmez. Uygulamanın yeni abonelik, güncel görüntü veya olay geçmişi alma düzeni gerekir. Örneğin kopmadan önce 100 lot açık emir görünüyordu; kopuklukta tamamı gerçekleştiyse yalnız eski miktarı saklamak doğru olmaz. Yeniden bağlantıdan sonraki durumun güvenilir kaynaktan uzlaştırılması gerekir. Genel mantık [kurtarma konusunda](09-baglanti-ve-kurtarma.md) açıklanacak.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Kullanıcının toplu bölüm talebi kapsamında yazıldı. Temsili endpoint ve donan ekran örneği eğitim senaryosudur; canlı MTrader testi değildir.

## Kaynaklar ve doğrulama

RFC 9110 (2022) ve RFC 6455 (2011), erişim 25 Ekim 2026. trade-data-app development `1cca9a8`: `api/protobuf-spec/gui-data.proto` içindeki HTTP eşlemeleri ve `pkg/gui/connections/ws_listener.go` içindeki WebSocket upgrade/yolları salt okunur incelendi. KB referans commit'idir; yerel development daha ileridedir. Oturum, reconnect veya endpoint uçtan uca denenmedi; prod davranışı doğrulanmadı.

## Devam notu

Taslak tamamlandı; kullanıcı okuması bekleniyor. Sonraki konu [gRPC ve veri sözleşmeleri](04-grpc-protobuf-marpc.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
