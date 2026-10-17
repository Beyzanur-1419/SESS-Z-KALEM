# Model Kararı ve Ortam Gereksinimleri

## Karar

Ana model: **`gemma3:4b`** (Ollama üzerinden, yaklaşık 4.3 milyar parametre — "4.2B"
dediğiniz muhtemelen bu, Gemma 3 ailesinin 4B varyantı). Şu an bir takım üyesinin
makinesinde indiriliyor; bu, demo/geliştirme boyunca **tüm takımın referans aldığı
tek model** olacak — ölçüm tablosu ve prompt ayarları bu modele göre yapılacak.
Proje Özeti'nde zaten "yavaşsa daha küçük boyut" notu var; fallback olarak
`gemma3:1b` hazırda tutulmalı (bkz. aşağı).

## Neden 4b (27b/12b değil, 1b değil)

- **1b**: çok hızlı ama bağlamsal çıkarım (gizli teklif bedeli, kod adı gibi kalıbı
  olmayan bilgiyi anlama) için muhtemelen yetersiz — projenin çekirdek özelliği bu.
- **12b/27b**: daha güçlü ama CPU-only bir dizüstünde demo sırasında yavaşlama riski
  yüksek; "ilk cevap yavaşsa 'analiz ediliyor' göstergesi" notu zaten bu riski
  öngörmüş.
- **4b**: ikisi arasında, 8GB'lık sıradan bir dizüstünde bile GPU olmadan çalışabilecek
  en dengeli nokta — demo günü güvenilirliği, ham kaliteden daha önemli.

## Ortam gereksinimleri (Ollama + gemma3:4b)

| Kaynak | Minimum | Önerilen | Not |
|---|---|---|---|
| RAM | ~4 GB boş | 6-8 GB boş | Q4_K_M nicemlemede model ~2.2 GB bellek kaplıyor; + KV cache/işletim payı |
| Disk | ~3 GB boş | 5 GB boş | Model dosyası + Ollama'nın kendi önbelleği için pay |
| GPU | Gerekli değil | 6 GB+ VRAM (RTX 4060 ve üzeri) varsa | CPU-only'de de çalışır, GPU sadece hızlandırır |
| OS | Linux / macOS / Windows | — | Ollama üçünde de yerel HTTP servisi (`localhost:11434`) olarak çalışıyor |
| Ollama sürümü | Güncel kararlı sürüm | — | `ollama --version` ile kontrol edin, hepinizde aynı sürüm olsun |

Üç takım üyesinin de demo/geliştirme makineleri bu eşiklerin altındaysa (özellikle
4GB RAM altı), onu şimdiden öğrenmemiz lazım — model indirmesi bitmeden önce kontrol
edilmeli.

## Bugün herkesin kendi makinesinde doğrulaması gerekenler

1. `ollama pull gemma3:4b` tamamlandıktan sonra `ollama list` ile modelin göründüğünü
   doğrulayın.
2. `ollama run gemma3:4b "test"` ile **Wi-Fi kapalıyken** bir cevap alabildiğinizi
   doğrulayın — bu, demonun en kritik iddiasının (internetsiz çalışıyor) önceden
   kanıtlanmasıdır.
3. Basit bir zamanlama yapın: kısa bir paragraf + "bu metindeki gizli bilgiyi bul"
   türünden bir istem gönderip cevap süresini not edin. 10-15 saniyeyi aşıyorsa
   demo akışına "analiz ediliyor" göstergesi şart, aşmıyorsa bile iyi bir referans
   sayı olur.
4. Sonuçları (RAM/CPU/GPU, cevap süresi, model indirme boyutu) bu dosyaya veya ekip
   kanalına not düşün — en yavaş makine demo makinesi olmamalı.

## Fallback planı

`gemma3:4b` beklenenden yavaş/kararsız çıkarsa: `ollama pull gemma3:1b` ile aynı
mimariyi (aynı prompt, aynı şema) değiştirmeden küçük modele geçiş yapılabilir —
tasarım bunu zaten destekliyor (`docs/api-contract.md`'deki şema model boyutundan
bağımsız).
