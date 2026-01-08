# 🚀 Hızlı Başlangıç Rehberi - Quick Start Guide

## 🎯 3 Adımda Başlayın / Get Started in 3 Steps

### 1️⃣ Kurulum / Installation

#### Linux / macOS:
```bash
# Gerekli bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
./baslat.sh
```

#### Windows:
```cmd
REM baslat.bat dosyasına çift tıklayın veya:
baslat.bat
```

### 2️⃣ Resimlerinizi Hazırlayın / Prepare Your Images

İhtiyacınız olan:
- ✅ **Kaynak resim**: Kullanmak istediğiniz yüzü içeren fotoğraf
- ✅ **Hedef resim**: Yüzün değiştirileceği fotoğraf

**İpuçları / Tips:**
- Resimlerde yüzler net ve açık görünmeli
- Frontal (ön) açıdan çekilmiş fotoğraflar en iyi sonucu verir
- Yeterli aydınlatma önemli
- JPG, PNG formatları desteklenir

### 3️⃣ Yüz Değiştirin! / Swap Faces!

1. Tarayıcınızda **http://localhost:7860** açılacak
2. Kaynak ve hedef resimleri yükleyin
3. "Yüz Değiştir" butonuna tıklayın
4. Sonucu indirin!

---

## 📊 Ayarlar Rehberi / Settings Guide

### Değiştirme Gücü / Swap Strength

| Değer | Sonuç | Kullanım |
|-------|-------|----------|
| 0.0 - 0.3 | Çok güçlü kaynak yüz | Tamamen kaynak yüzü kullanmak istediğinizde |
| 0.4 - 0.6 | **Dengeli (Önerilen)** | **Çoğu durum için ideal** |
| 0.7 - 1.0 | Hedef özellikleri korur | Sadece hafif değişiklik istediğinizde |

**Varsayılan: 0.5** (En doğal sonuç)

---

## 💡 Örnek Kullanım Senaryoları / Example Use Cases

### 🎬 Senaryo 1: Aile Fotoğrafı Düzenleme
**Durum:** Aile fotoğrafınızda birisinin gözleri kapalı
**Çözüm:**
1. Aynı kişinin gözleri açık başka bir fotoğrafını kaynak olarak kullanın
2. Sorunlu fotoğrafı hedef olarak yükleyin
3. Değiştirme gücünü 0.6'ya ayarlayın
4. İşleyin!

### 🎭 Senaryo 2: Yaratıcı Projeler
**Durum:** Farklı kıyafetlerle nasıl görüneceğinizi görmek istiyorsunuz
**Çözüm:**
1. Kendi yüzünüzü kaynak olarak kullanın
2. Farklı kıyafetli bir fotoğrafı hedef olarak yükleyin
3. Değiştirme gücünü 0.4-0.5 arası ayarlayın

### 📸 Senaryo 3: Portre İyileştirme
**Durum:** Eski bir fotoğrafta yüz kalitesi düşük
**Çözüm:**
1. Aynı kişinin daha kaliteli bir fotoğrafını kaynak olarak kullanın
2. Eski fotoğrafı hedef olarak yükleyin
3. Değiştirme gücünü 0.7-0.8 arası ayarlayın (orijinali daha çok korur)

---

## ❓ Sık Sorulan Sorular / FAQ

### S: İlk başlatma neden uzun sürüyor?
**C:** İlk kullanımda AI modelleri (yaklaşık 300-500MB) otomatik olarak indirilir. Sonraki kullanımlarda hızlı başlar.

### S: "Yüz bulunamadı" hatası alıyorum
**C:**
- Resimdeki yüzün net ve açık olduğundan emin olun
- Profil fotoğrafları yerine frontal (ön) fotoğraflar kullanın
- Yüz çok küçükse resmi kırparak yüzü büyütün
- Aydınlatmanın yeterli olduğundan emin olun

### S: Sonuç doğal görünmüyor
**C:**
- Değiştirme gücünü 0.4-0.6 arasında deneyin
- Benzer açılardan çekilmiş fotoğraflar kullanın
- Benzer aydınlatma koşullarındaki fotoğrafları tercih edin
- Kaynak ve hedef resimlerin çözünürlüklerinin yakın olmasına dikkat edin

### S: Çok yavaş çalışıyor
**C:**
- Büyük resimleri küçültmeyi deneyin (1920x1080 veya daha küçük ideal)
- Bilgisayarınızda GPU varsa, CUDA desteğini etkinleştirin (gelişmiş kullanıcılar için)
- Diğer uygulamaları kapatın

### S: Birden fazla yüz varsa ne olur?
**C:** Uygulama en büyük/en belirgin yüzü otomatik olarak seçer.

### S: Video dosyalarıyla çalışır mı?
**C:** Şu anki versiyon sadece resimlerle çalışır. Video desteği için ana FaceFusion uygulamasını kullanabilirsiniz.

---

## 🔐 Gizlilik ve Güvenlik / Privacy & Security

### ✅ GÜVENLİ
- Tüm işlemler bilgisayarınızda yerel olarak yapılır
- Hiçbir resim internet üzerinden gönderilmez
- Verileriniz sizde kalır

### ⚠️ ÖNEMLİ UYARILAR
- Başkalarının rızası olmadan fotoğraflarını kullanmayın
- Yanıltıcı içerik oluşturmak için kullanmayın
- Yasa dışı amaçlar için kullanmayın
- Deepfake farkındalığı: Oluşturduğunuz içeriğin manipüle edilmiş olduğunu belirtin

---

## 🛠️ Gelişmiş Ayarlar / Advanced Settings

### Port Değiştirme
`face_swap_app.py` dosyasını düzenleyin:
```python
app.launch(
    server_name="0.0.0.0",
    server_port=7860,  # Burası değiştirilebilir / Can be changed
    share=False
)
```

### GPU Kullanımı (Gelişmiş)
GPU kullanmak için `face_swap_app.py` içindeki şu satırı değiştirin:
```python
state_manager.init_item('execution_providers', ['CUDAExecutionProvider', 'cpu'])
```

### Model Değiştirme
Farklı face swap modelleri kullanmak için:
```python
state_manager.init_item('face_swapper_model', 'inswapper_128')
# Seçenekler: inswapper_128, simswap_256, ghost_1_256, vb.
```

---

## 📞 Yardım İsteme / Getting Help

### Sorun mu yaşıyorsunuz?

1. **Önce FACE_SWAP_APP_TR.md dosyasındaki Sorun Giderme bölümünü okuyun**
2. **Hata mesajını tam olarak kopyalayın**
3. **Kullandığınız işletim sistemini ve Python versiyonunu belirtin**
4. **GitHub'da bir issue açın**

### Bilgi Toplama
Sorun bildirirken şu komutu çalıştırın:
```bash
python --version
pip list | grep -E "gradio|onnx|opencv"
```

---

## 🎓 Daha Fazla Öğrenin / Learn More

### İleri Seviye Kullanım
Daha fazla özellik için ana FaceFusion uygulamasını deneyin:
```bash
python facefusion.py run
```

### Dokümantasyon
- FaceFusion Docs: https://docs.facefusion.io
- FaceFusion GitHub: https://github.com/facefusion/facefusion

---

## 🌟 İpuçları ve Püf Noktalar / Tips & Tricks

### En İyi Sonuçlar İçin / For Best Results

1. **Resim Kalitesi**
   - En az 512x512 piksel
   - Net ve odaklanmış fotoğraflar
   - İyi aydınlatılmış

2. **Yüz Pozisyonu**
   - Frontal veya yarı-frontal açı
   - Yüz tam görünür
   - Saç veya aksesuarlar yüzü örtmemeli

3. **Benzerlik**
   - Benzer ışık koşulları
   - Benzer yüz ifadeleri
   - Benzer kamera açıları

4. **Deneme Yanılma**
   - Farklı değiştirme güçleri deneyin
   - Farklı kaynak fotoğraflar deneyin
   - Farklı kırpma ve boyutlar deneyin

### Yaygın Hatalar ve Çözümleri

| Sorun | Olası Neden | Çözüm |
|-------|-------------|-------|
| Yüz bulunamıyor | Yüz çok küçük | Resmi kırpın, yüzü büyütün |
| Renkler uyumsuz | Farklı ışık koşulları | Benzer aydınlatmalı fotoğraflar kullanın |
| Kenarlar keskin | Düşük değiştirme gücü | Değeri 0.5'e yükseltin |
| Yüz bulanık | Düşük kaynak kalitesi | Daha yüksek çözünürlüklü kaynak kullanın |

---

## 🎉 Başarılı Kullanım!

Artık hazırsınız! Uygulamayı başlatın ve yüz değiştirme işlemlerine başlayın.

You're ready to go! Launch the app and start swapping faces.

```bash
# Linux/macOS
./baslat.sh

# Windows
baslat.bat
```

**İyi eğlenceler! / Have fun!** 🚀
