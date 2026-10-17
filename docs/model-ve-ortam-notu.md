# Model Kararı ve Ortam Gereksinimleri

## Karar (güncellendi)

Ana model: **`gemma4:e4b`** (Ollama üzerinden, ~4.4 milyar parametre, 32K bağlam,
"thinking mode" destekli). **Önceki sürümde burada `gemma3:4b` yazıyordu — bu
yanlıştı**, Dilara'nın `engine/llm.py`'si gerçekte `gemma4:e4b` ile yazılıp test
edildi; bu dosya o gerçeğe göre düzeltildi. Model, `SESSIZ_KALEM_MODEL` ortam
değişkeniyle değiştirilebilir (`llm.py`'de tanımlı).

**Gemma 4'ün "thinking mode" özelliği önemli**: cevap vermeden önce varsayılan
olarak içsel olarak "düşünüyor" (4000 tokene kadar) — bu hem gecikmeyi artırır
hem JSON çıktısını bozabilir. `llm.py` bu yüzden istekte `think: false`
gönderiyor; model bunu desteklemiyorsa (ör. gemma3 ailesine dönülürse)
parametresiz tekrar deniyor. **Bu detayı atlamayın** — "thinking" kapatılmazsa
hem demo yavaşlar hem format bozulabilir.

## Neden e4b (daha büyük/küçük değil)

- Daha küçük varyantlar bağlamsal çıkarım (gizli teklif bedeli, kod adı gibi
  kalıbı olmayan bilgiyi anlama) için muhtemelen yetersiz — projenin çekirdek
  özelliği bu.
- Daha büyük varyantlar CPU-only bir dizüstünde demo sırasında yavaşlama riski
  taşıyor.
- `e4b`, 8GB'lık sıradan bir dizüstünde (GPU olmadan, Q4 nicemleme ile) makul
  hızda çalışabiliyor — demo günü güvenilirliği ham kaliteden daha önemli.

## Ortam gereksinimleri (Ollama + gemma4:e4b)

| Kaynak | Minimum | Önerilen | Not |
|---|---|---|---|
| RAM | ~6 GB boş | 8 GB boş | Q4_K_M nicemlemede model ~3.5 GB VRAM/bellek kaplıyor; + KV cache/işletim payı |
| Disk | ~4 GB boş | 6 GB boş | Model dosyası + Ollama'nın kendi önbelleği için pay |
| GPU | Gerekli değil | 6-8 GB+ VRAM varsa | CPU-only'de de çalışır (8GB RAM'lik bir dizüstü yeterli), GPU sadece hızlandırır |
| OS | Linux / macOS / Windows | — | Ollama üçünde de yerel HTTP servisi (`localhost:11434`) olarak çalışıyor |
| Ollama sürümü | Güncel kararlı sürüm (Gemma 4 desteği olan) | — | `ollama --version` ile kontrol edin, hepinizde aynı sürüm olsun |

Üç takım üyesinin de demo/geliştirme makineleri bu eşiklerin altındaysa (özellikle
6GB RAM altı), onu şimdiden öğrenmemiz lazım — model indirmesi bitmeden önce
kontrol edilmeli.

## Bugün herkesin kendi makinesinde doğrulaması gerekenler

1. `ollama pull gemma4:e4b` tamamlandıktan sonra `ollama list` ile modelin
   göründüğünü doğrulayın.
2. `ollama run gemma4:e4b "test"` ile **Wi-Fi kapalıyken** bir cevap alabildiğinizi
   doğrulayın — bu, demonun en kritik iddiasının (internetsiz çalışıyor) önceden
   kanıtlanmasıdır.
3. Basit bir zamanlama yapın: kısa bir paragraf + "bu metindeki gizli bilgiyi bul"
   türünden bir istem gönderip cevap süresini not edin. "Thinking mode" kapalı
   (`think: false`) olduğunda bile 10-15 saniyeyi aşıyorsa demo akışına "analiz
   ediliyor" göstergesi şart.
4. Sonuçları (RAM/CPU/GPU, cevap süresi, model indirme boyutu) bu dosyaya veya
   ekip kanalına not düşün — en yavaş makine demo makinesi olmamalı.

## Fallback planı

`gemma4:e4b` beklenenden yavaş/kararsız çıkarsa: `llm.py`'deki
`SESSIZ_KALEM_MODEL` ortam değişkenini değiştirerek (örn. `gemma3:4b`'ye)
mimariyi değiştirmeden geçiş yapılabilir — tasarım bunu zaten destekliyor
(`docs/api-contract.md`'deki şema model boyutundan/ailesinden bağımsız). Dikkat:
`gemma3` ailesi "thinking mode" desteklemez, `llm.py` bunu zaten otomatik
algılayıp parametresiz tekrar deniyor.
