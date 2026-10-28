---
kapsam: IP/port, istemci/sunucu, TCP, UDP ve multicast; kayıp, sıra ve gecikme
dis_kaynak:
  - url: https://www.rfc-editor.org/rfc/rfc9293.html
    erisim: 2026-10-25
  - url: https://www.rfc-editor.org/rfc/rfc768.txt
    erisim: 2026-10-25
  - url: https://www.rfc-editor.org/rfc/rfc1112.html
    erisim: 2026-10-25
dogrulama: 2026-10-25
durum: taslak
---

# Ağ, TCP, UDP ve multicast

İki programın veri göndermesi, bir binadan diğerindeki belirli masaya evrak yollamaya benzer. Önce adresi, sonra o adreste hangi uygulamaya ulaşacağımızı bilmemiz gerekir. Veriyi nasıl taşıdığımız ise kayıp, sıra ve gecikme davranışını belirler.

## IP, port ve bağlantı

**IP adresi**, ağdaki hedefi; **port**, o hedefte hangi iletişim ucuna gidildiğini belirtir. Binanın adresi ve kapı numarası gibi düşünebiliriz. Aynı makinede farklı portları dinleyen birden fazla servis olabilir. Gerçek hedef için IP/port yanında TCP mi UDP mi kullanıldığı da önemlidir.

**Sunucu**, belirli bir uçta bağlantı veya veri bekleyen; **istemci**, o uca ulaşmayı başlatan taraftır. Bu, ürünün büyüklüğüyle ilgili değildir. Aynı servis bir bağlantıda sunucu, başka bağlantıda istemci olabilir.

**Socket**, uygulamanın bu iletişimi işletim sistemi üzerinden yürüttüğü uçtur. “Socket açıldı” yalnız bir hazırlık adımı olabilir; karşı uçla kimlik doğrulaması ve uygulama hazırlığı ayrıca gerekebilir.

## TCP: sıralı bir bayt akışı

**TCP**, bağlantı üzerinden sıralı ve güvenilir bir bayt akışı sağlar. Kayıp veriyi yeniden iletme ve alıcıya göre akışı düzenleme mekanizmaları vardır. Ancak karşı uygulamanın iş isteğini başarıyla yaptığını söylemez. Mektubun masaya ulaşması, içindeki emrin uygulanmasıyla aynı değildir. [TCP — RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)

Önemli ayrıntı: **TCP uygulama mesajlarının sınırlarını korumaz.** “EMİR-A” ve “EMİR-B” diye iki gönderim yapan programı düşünelim. Alıcı bir okumada “EMİR-AEM”, sonraki okumada “İR-B” görebilir; ikisini birlikte de alabilir. Protokol bu yüzden mesaj uzunluğu veya ayırıcı gibi bir **çerçeveleme (framing)** kuralı kullanır.

Bu bir parçalı okuma örneğidir; veri kaybını tek başına göstermez. Alıcı, parçaları biriktirip tam mesajı çıkarmalıdır. TCP'nin sıra garantisi de farklı bağlantılardaki olayları tek bir ortak sıraya koymaz.

## UDP: ayrı datagramlar

**UDP**, datagram denilen ayrı veri birimleri gönderir. Datagram sınırı vardır; fakat protokol tek başına teslimi, sırayı veya tekrar gelmemeyi garanti etmez. Kayıp denetimi gerekiyorsa uygulama/protokol katmanı bunu kurar. [UDP — RFC 768](https://www.rfc-editor.org/rfc/rfc768.txt)

Bir hoparlörden numaralı duyurular yapıldığını düşünelim: 101, 102, 103, 104. Dinleyici 101, 102, 104 duyduysa **103 eksiktir**. 104'ü duymak, 103'te ne söylendiğini tamamlamaz. Piyasa verisinde eksik mesaj bir iptal veya miktar değişikliği olabilir; defter sonraki olayları alsa da hatalı kalabilir.

**Sequence number (sıra numarası)** boşluğu görmeye yardım eder. Örnekte numaralar eğitim amaçlıdır; gerçek protokolde paket mi mesaj mı sayıldığı ve oturum değişince numaranın nasıl ele alındığı kendi sözleşmesinden okunur.

## Multicast: aynı yayının birçok dinleyicisi

**Unicast**, belirli bir hedefe gönderimdir. **Multicast**, bir gruba yapılan yayının o gruba katılmış birden fazla alıcıya dağıtılmasıdır. Aynı yayını birçok masanın dinlemesine benzer; herkes için ayrı uygulama bağlantısı açma fikrinden farklıdır. [IP multicast — RFC 1112](https://www.rfc-editor.org/rfc/rfc1112.html)

Multicast güvenilirlik garantisi değildir. Bir dinleyici mesajı alırken diğeri ağ veya yerel alım koşulları yüzünden kaçırabilir. Doğru gruba katılmak, doğru ağ arayüzünü kullanmak ve paketlerin uygulamaya kadar geldiğini görmek ayrı kontrollerdir.

| Taşıma biçimi | Benzetme | Uygulamada ayrıca düşünülür |
|---|---|---|
| TCP | Sıralı evrak akışı | Mesaj sınırı ve iş sonucu |
| UDP unicast | Tek adrese numaralı duyuru | Kayıp, sıra ve tekrar |
| UDP multicast | Gruba ortak duyuru | Her alıcının eksiksizliği |

MTrader'daki kavramların teknik adresi [ITCH alım yolu](../../bilgi-tabani/10-servisler/itch-sdk/alim-yolu.md); kayıp kurtarmanın borsa bağlamı [Glimpse ve Rewinder](../02-borsa-temelleri/11-glimpse-rewinder-replay.md) konusudur. Burada taşımanın mantığını öğreniyoruz; gerçek kanal ve portları ezberlemiyoruz.

## Gecikmeyi tek bir “ağ sorunu” diye adlandırmayalım

Bir olayın geç görünmesinin olası yerlerini ayıralım: ağda taşınma, işletim sistemi tamponu, uygulama kuyruğu, işleme ve ekran güncellemesi. “Paket geldi” bilgisinin yanında **ne zaman, hangi sıra numarasıyla ve hangi katmana geldiği** işe yarar.

Öğretici bir kontrol: yayın akarken alıcıdaki sayaç artıyor, fakat ekrandaki fiyat değişmiyorsa paketin ilgili ürüne ait olup olmadığına ve uygulamanın onu işleyip işlemediğine bakarız. Yalnız paket sayacı, bütün yolun sağlıklı olduğunu kanıtlamaz.

## Sorularımız ve netleşen noktalar

25 Ekim 2026: Bölümün toplu yazımı kullanıcı talebidir. Numaralı duyuru ve parçalı TCP okuması agent'ın örnekleridir; MTrader'da gözlenmiş olay değildir.

## Kaynaklar ve doğrulama

RFC 9293 (TCP, 2022), RFC 768 (UDP, 1980) ve RFC 1112 (multicast temel modeli, 1989) resmi metinleri 25 Ekim 2026'da okundu. Bunlar belirli ağın konfigürasyonunu veya performansını kanıtlamaz. MTrader bağlantıları mevcut KB'ye yönlendirmedir; SDK kodu veya canlı ağ bu konuda yeni doğrulanmadı.

## Devam notu

Taslak tamamlandı; toplu kullanıcı incelemesi bekleniyor. Sonraki konu [HTTP, REST ve WebSocket](03-rest-websocket.md).

[Bölüm indeksi](README.md) · [Ana indeks](../README.md)
