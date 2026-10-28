---
kapsam: K-241/K-242 için kaynak gövdeleriyle odaklı yerel senaryolar
kaynak:
  - repo: HftSrvProd
    branch: development
    commit: 4275ccc
dogrulama: 2026-10-24
durum: taslak
---

# Varant yerel senaryo kanıtı

HftSrvProd development fetch/pull sonrası `4275ccc` değişmedi. [Araç](dogrula_varant_akisi.py), `HftWarrant.cpp` içinden `executeBuyOrders`, `rejectOrder`, `addOrder`, `replaceToTarget` gövdelerini değiştirmeden çıkarır ve MSVC C++17 ile geçici dizinde derler. SDK, manager ve mesaj yüzeyleri sahtedir; mutex gerçek `std::mutex`'tir. Kaynak uygulamaya yazmaz, borsaya bağlanmaz.

```powershell
python _surec/dogrula_varant_akisi.py --sources C:/Users/Seyf/algo-workspace
```

## Sonuçlar

| Senaryo | Gözlem |
|---|---|
| K-241: caller mutex tutarken SDK senkron reject çağırır | Gerçek `rejectOrder` girişinde MSVC `resource deadlock would occur` istisnası üretir; callback geri dönmez. |
| Kontrol: caller mutex tutmaz | Aynı callback ve gönderim normal döner. |
| K-242: aynı türev için S1 ve S2 satış accept'i, alış toplamı 60 | İki kayıt orderMap'te kalır; gerçek replace gövdesi yalnız S2'ye toplam 60 gönderir. |
| Kontrol: tekrar hedef replace | İkinci çağrıda ek replace gönderilmez. |
| Kontrol: tek satış accept'i | S1 token'ına 60 gönderilir. |

Beş senaryo beklendiği gibi sonuçlandı. Bu PASS, hata düzeltildi demek değildir. K-241/K-242 açık kalır.

## Kanıt sınırı

Caller fixture mutex'i tutar; tam `processItchEventTimed` yürütülmez. Araç kaynak caller'da kilit satırının `executeBuyOrders` çağrısından önce bulunduğunu ayrıca kontrol eder; bu kontrol tek başına tüm kontrol akışının analizi değildir. SDK senkron ret callback'i sahtedir. Üretim SDK/host yönlendirmesinin statik zinciri [Varant belgesindedir](../bilgi-tabani/20-stratejiler/varant.md#ikinci-kod-turu--ret-ve-parçalı-satış-sınırları).

MSVC sonucu istisnadır; Linux/prod'da aynı istisna veya kesin kilitlenme gözlendiği söylenmez. Üç saniyelik child-process watchdog, bloklanan varyantı sınırlar; bu çalıştırmada timeout olmadı.

K-242 fixture alış toplamını 60 olarak kurar ve iki satış ACK'i verir; gerçek buy fill → satış gönderimi uçtan uca oynatılmaz. ACK adaptörü emir miktarı taşımaz; her satışın 30 olduğu varsayımı borsada sınanmaz. Gözlenen yalnız tek token'a toplam miktarla replace kararıdır; borsanın replace kabulü, miktar semantiği ve fazla satış sonucu kanıtlanmadı.

Tam HFT build'i, gerçek SDK/ITCH/OUCH entegrasyonu, canlı emir veya uygulama düzeltmesi yapılmadı. Master için bu harness çalıştırılmadı; sonuç development gövdelerine aittir.

## Çıkarılan gövdelerin SHA-256 önekleri

| Gövde | Önek |
|---|---|
| executeBuyOrders | a38358d7383adc92 |
| rejectOrder | 27f26d51e4e2d8fe |
| addOrder | 00b6eba42bf3d0dc |
| replaceToTarget | 80d1c3b45861db03 |
