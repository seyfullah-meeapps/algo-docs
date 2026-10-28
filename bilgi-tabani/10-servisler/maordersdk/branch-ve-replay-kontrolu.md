---
kapsam: MAOrderSDK development ve main kod farkları, OUCH replay ile combiner durumunun ikinci incelemesi
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: a788782
  - repo: MAOrderSDK
    branch: main
    commit: d5adc6f
dogrulama: 2026-10-23
durum: taslak
---

# Branch farkları ve replay kontrolü

Bu dosya ikinci incelemenin branch farklarını kaydeder. Temel algoritma [emir akışında](emir-akisi.md), bağlantı/replay mekanizması [OUCH protokolünde](ouch-protokolu.md). SDK branch'i, uygulamaya linklenmiş binary sürümünü tek başına kanıtlamaz.

## Replay ve combiner sınırı

`OuchConnection::maybe_fire_replay_completed` en az bir ServerHeartbeat ve son SequencedData'dan itibaren quiet window bekler; veri yoksa login sonrası başlangıcı kullanır. Bu bir sessizlik ölçümüdür, exchange'den gelen açık bir “geçmiş bitti” işareti değildir. Canlı SequencedData da süreyi uzatır. Callback bir login için bir kez üretilir; OUCH olayları bu süre boyunca host'a iletilmeye devam eder. Development/main karşılaştırmasında bu karar algoritması değişmemiştir.

`MAOrderSDK::on_wire_accepted` önce host `onAccepted`'ı, sonra yalnız `combiner_eligible` kayıt için combiner `on_accepted`'ı çağırır. İki branch'te de:

| Durum | Combiner sonucu |
|-------|-----------------|
| Yeni süreç, bilinmeyen wire token replay accept'i | SDK kaydı adopt edilir; eligible false kalır, ITCH izleme kurulmaz. Fill OUCH yolundan geçer. |
| Aynı süreçte gönderilmiş ve hâlâ izlenen emir | Eligible true; duplicate accept mevcut combiner durumunu sıfırlamaz. Replay fill'leri mevcut sayaçlara yeniden girer. |
| Aynı süreçte bitmiş emir | Combiner kaydı silinir; SDK token haritası kalır ve eligible true'dur. Replay accept'i combiner durumunu yeniden kurabilir. |

`poison_all` ITCH teslimini durdurur; mevcut OUCH sayaçlarını ve daha önce teslim edilmiş miktarı temizlemez. Bu nedenle “poison sonrası her OUCH mesajı bütünüyle geçer” varsayımı yanlıştır: `on_executed_adjust` eski `delivered_rest` üzerinden hesaplamayı sürdürür. Poison, replay dedup mekanizması değildir. Tekrar teslimin miktarı olay sırasına ve mevcut duruma bağlıdır (K-106); canlıda yeniden üretilmedi.

`onWireExecuted`, OUCH combiner ayarlamasından önce çağrılır; GUI ham wire fill'i görür. ITCH kaynaklı `onExecuted` ile GUI olayı aynı teslim yolu değildir. Match ID tabanlı geçmiş dedup yoktur. HFT etkisi [emir yaşam döngüsü Şüpheli #2](../hftsrvprod/emir-yasam-dongusu.md#şüpheli-davranışlar-koddan)'dedir.

## Development ile main farkları

| Alan | Development `a788782` | Main `d5adc6f` |
|------|-----------------------|----------------|
| Hard cap | Limit bloğunda enstrüman bölme kararından önce `qty > cap/price`; çarpım taşması önlenir | Önce `price*qty`; yalnız `notional > instrument_limit` ise hard cap kontrol edilir |
| Sıfır fiyat | Market/MarketWithLeftoverLimit için izin verir | Emir türünden bağımsız 1005 ret |
| Yerel ret kimliği | Boş caller id için token atayıp assignment callback çağırabilir | Yerel ret caller id ile döner; boş kalabilir |
| Split kimliği | Boş caller id ile child wire token'ı public id olur | Boş parent için id üretip child logical id'lerini `parent#i` yapar |
| Routing | `routing_account`, preferred username ve FIX pool yolu | Bu ek routing/FIX dispatch yolları yok |
| Split replace başarısız child | Eski child id yeni listede tutulur | Yalnız başarılı child'lar yeni parent listesine girer |
| Soket yazımı | Bağlantı başına `send_mutex_` ile bütün mesaj korunur | `send_raw` içinde bu kilit yok |
| Yeniden connect | Eski recv thread join edilir, eski soket kapatılır; kendi recv thread'inden connect reddedilir | Bu temizlik/koruma yok; joinable thread üzerine atama terminate riski taşır |
| Combiner trampoline | Atomik `self_`, stop başında yönlendirme kesilir | Düz pointer, stop sonunda temizlenir |

Kaynaklar: `src/MAOrderSDK.cpp`, `src/combiner/Combiner.cpp`, `src/connection/ouch/OuchConnection.cpp`. Performans ölçümleri de development'ta kullanıcı/connection bazına taşınmıştır; metrik isimlerinin tam envanteri bu turda çıkarılmadı. FIX engine/codec'in bütün iç mantığı bu tabloyla doğrulanmış sayılmaz.

## Şüpheli

**K-231 — main hard cap koşulu:** Limit tablosu dolu, fiyat pozitif ve enstrüman limiti statik hard cap'ten yüksekse, `hard_cap < notional <= instrument_limit` emri main'de 1003 kontrolüne girmez. Örnek varsayımsal limitlerle: hard cap 50 milyon TL, enstrüman limiti 100 milyon TL, emir 75 milyon TL. Development aynı koşulda reddeder. Main ayrıca `price*qty` çarpımında taşma kontrolü yapmaz. Gerçek enstrüman/config değerleri ve prod'a linklenmiş SDK sürümü doğrulanmadı; bu bir kaynak branch bulgusudur.

## Doğrulama kapsamı

2026-10-23 origin fetch ve development pull --ff-only: zaten güncel. Yukarıdaki iki uç yerel Git nesnelerinden karşılaştırıldı; kaynak çalışma ağacı değiştirilmedi. İnceleme statiktir. Mevcut combiner testleri gerçek thread zamanlaması ve reconnect replay'ini kapsamıyor; bu oturumda build/test veya canlı emir denemesi yapılmadı. Legacy FIX ve host reconnect politikası ayrı inceleme gerektirir.
