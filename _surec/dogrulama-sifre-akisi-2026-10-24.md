---
kapsam: K-233/K-234 gerçek C++ handler gövdelerinin sahte DB ve oturum adaptörleriyle yerel doğrulaması
kaynak:
  - repo: MAOrderSDK
    branch: development
    commit: c2b5060
  - repo: order-service
    branch: development
    commit: 26e9a02
dogrulama: 2026-10-24
durum: taslak
---

# Şifre akışı yerel doğrulaması

SDK/order-service yeniden fetch/development pull edildi; uçlar değişmedi. [K-233/K-234 ayrıntısı](../10-servisler/order-service/fix-branch-karsilastirmasi.md#k-233--1409suz-logonda-sdk-ve-host-şifre-sonucu-ayrışıyor) artık yalnız statik çağrı okumasına dayanmıyor: aşağıdaki handler senaryoları Windows/MSVC ile çalıştırıldı. Uygulama kodu değiştirilmedi; gerçek şifre, oturum ve DB kullanılmadı.

## Nasıl çalıştırılır?

```powershell
python _surec/dogrula_sifre_akisi.py --sources C:/Users/Seyf/algo-workspace
```

Araç Visual Studio C++ Build Tools gerektirir; WSL/QuickFIX kurulumu yapmaz. Yedi gerçek fonksiyon gövdesini kaynak dosyalarından çalışma anında çıkarır, geçici klasörde C++17 derler ve test executable'ını çalıştırır. Kaynak klonları ve servis config'leri yazılmaz. Fonksiyon metinlerinin SHA-256 önekleri çıktıda basılır; test mantığının Python'da yeniden yazılmış bir eşdeğeri kullanılmaz.

SDK `FixEngine::fromAdmin`; host `seedFixPassword`, `armFromConfig`, `onFixPasswordChangeResult`, `onUserConnected`, `FixPasswordPromoteNeeded`, `PromoteFixPasswordIfNeeded` gövdeleri değiştirilmeden derlemeye katılır. DB RPC'si sahte bellek DB'sidir; QuickFIX Message/Session ve kullanıcı/config tiplerinin yalnız gereken yüzeyi adaptördür. Worker callback'i testte senkron çalıştırılır; gerçek thread scheduler sınanmaz.

## Sonuçlar

A/B/P yalnız test işaretçileridir, gerçek credential değildir. Başlangıç DB/live=A; yeni config adayı B.

| Senaryo | Beklenen kontrol / gözlenen sonuç |
|---------|-----------------------------------|
| Logon, 1409 yok | **K-233 gözlendi:** SDK=B, host live=A, başarılı promote sonrası DB=A ve pending boş |
| Logon, 1409=0 | Kontrol geçti: SDK=DB=B, pending boş |
| Logon, 1409=1 | Kontrol geçti: SDK=DB=B, pending boş |
| Manuel pending yazımı başarısız | **K-234 gözlendi:** DB değişmediği halde armFromConfig B döndürür, host armed=B |
| Önceden çözülmemiş pending=P | Kontrol geçti: yeni config adayı reddedilir, DB write çağrısı yapılmaz |

Beş senaryo assertion'ları geçti. Bu araç kusurların mevcut davranışını **gözlemleyen** testtir; PASS kusurun giderildiği anlamına gelmez. İleride kod düzelirse gözlem assertion'ı başarısız olabilir; araç o zaman kaynakla birlikte yeniden değerlendirilmelidir.

## Sınırlar

Bu bir full SDK/order-service build'i veya QuickFIX entegrasyonu değildir. Test `fromAdmin` sonrası host'un gerçek `onUserConnected` handler'ını çağırarak Logon sınırını taklit eder; gerçek QuickFIX'in bu yanıtı üretmesi/teslimi, BIST'in 1409'suz Logon göndermesi, async worker yarışları ve uzak DB hata semantiği test edilmedi. Otomatik renew'ün tamamı çalıştırılmadı; yalnız manuel config ve sonuç/promote yolları yürütüldü. Bu nedenle prod'da şifre kaybı yaşandığı sonucu çıkarılmaz.

Kaynak deltasına veya üçüncü taraf kütüphane davranışına göre sahte adaptörler yeniden kontrol edilmelidir. İlk derleme denemelerindeki komut tırnaklama ve eksik adaptör yüzeyi hataları düzeltildi; rapordaki sonuçlar son başarılı C++ derlemesine aittir.
