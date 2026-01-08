# 🎭 Yüz Değiştirme Uygulaması - Face Swap App

## 📖 Açıklama / Description

Bu basit ve kullanıcı dostu uygulama ile bir resimdeki yüzü başka bir resme aktarabilirsiniz. FaceFusion teknolojisi kullanılarak geliştirilmiştir.

This simple and user-friendly application allows you to swap faces between images. Built with FaceFusion technology.

## 🚀 Kurulum / Installation

### Gereksinimler / Requirements

Python 3.10 veya üzeri / Python 3.10 or higher

### Adım 1: Bağımlılıkları Yükleyin / Install Dependencies

```bash
pip install -r requirements.txt
```

### Adım 2: Modelleri İndirin / Download Models (İlk Kullanımda Otomatik Yapılır)

Uygulama ilk çalıştırıldığında gerekli AI modellerini otomatik olarak indirecektir. İnternet bağlantınızın olduğundan emin olun.

The application will automatically download required AI models on first run. Make sure you have an internet connection.

## 💻 Kullanım / Usage

### Uygulamayı Başlatın / Start the Application

```bash
python face_swap_app.py
```

veya / or

```bash
python3 face_swap_app.py
```

Uygulama başlatıldığında otomatik olarak tarayıcınızda açılacaktır.

The application will automatically open in your browser.

**Varsayılan Adres / Default URL:** http://localhost:7860

## 📝 Nasıl Kullanılır / How to Use

1. **Kaynak Resim Yükleyin** / **Upload Source Image**
   - Kullanmak istediğiniz yüzü içeren resmi yükleyin
   - Upload the image containing the face you want to use

2. **Hedef Resim Yükleyin** / **Upload Target Image**
   - Yüzün değiştirileceği resmi yükleyin
   - Upload the image where the face will be swapped

3. **Değiştirme Gücünü Ayarlayın** / **Adjust Swap Strength**
   - 0.0 - 1.0 arası bir değer seçin (0.5 önerilir)
   - Select a value between 0.0 - 1.0 (0.5 recommended)
   - 0 = Tamamen kaynak yüz / Completely source face
   - 1 = Daha fazla hedef özelliği / More target features

4. **"Yüz Değiştir" Butonuna Tıklayın** / **Click "Swap Face" Button**
   - İşlem tamamlandığında sonucu göreceksiniz
   - You'll see the result when processing is complete

## ✨ Özellikler / Features

- ✅ Basit ve sezgisel Türkçe arayüz / Simple and intuitive Turkish interface
- ✅ Gerçek zamanlı yüz değiştirme / Real-time face swapping
- ✅ Ayarlanabilir karışım gücü / Adjustable blend strength
- ✅ Yüksek kaliteli sonuçlar / High-quality results
- ✅ Yerel çalışma (verileriniz güvende) / Runs locally (your data is safe)

## ⚙️ Ayarlar / Settings

### Port Değiştirme / Changing Port

Varsayılan port 7860'tır. Değiştirmek için `face_swap_app.py` dosyasının sonundaki şu satırı düzenleyin:

Default port is 7860. To change it, edit this line at the end of `face_swap_app.py`:

```python
app.launch(
    server_name="0.0.0.0",
    server_port=7860,  # Bu satırı değiştirin / Change this line
    share=False,
    show_error=True,
    quiet=False
)
```

### Harici Erişim / External Access

Uygulamayı internet üzerinden paylaşmak isterseniz `share=True` yapın:

To share the application over the internet, set `share=True`:

```python
app.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True,  # Bu değeri True yapın / Set this to True
    show_error=True,
    quiet=False
)
```

## 🔧 Sorun Giderme / Troubleshooting

### Model İndirme Hataları / Model Download Errors

Eğer modeller indirilirken hata alırsanız:

If you get errors while downloading models:

1. İnternet bağlantınızı kontrol edin / Check your internet connection
2. Uygulamayı yeniden başlatın / Restart the application
3. Firewall ayarlarınızı kontrol edin / Check your firewall settings

### Yüz Bulunamadı Hatası / Face Not Found Error

- Resimlerde yüzlerin açık ve net olduğundan emin olun
- Make sure faces in images are clear and visible
- Yüzler kameraya doğru bakmalı
- Faces should be looking towards the camera
- Çok küçük veya çok büyük resimlerde sorun olabilir
- Very small or very large images may cause issues

### Performans Sorunları / Performance Issues

- GPU desteği yoksa CPU kullanılır (daha yavaş)
- If no GPU support, CPU will be used (slower)
- Büyük resimleri küçültmeyi deneyin
- Try resizing large images
- Daha güçlü bir bilgisayar kullanın
- Use a more powerful computer

## 📋 Gereksinimler / Requirements

- Python 3.10+
- 4GB+ RAM
- İnternet bağlantısı (ilk kulanımda) / Internet connection (first use)
- 2GB+ boş disk alanı (modeller için) / 2GB+ free disk space (for models)

## 🛡️ Gizlilik / Privacy

Bu uygulama tamamen yerel olarak çalışır. Resimleriniz hiçbir sunucuya gönderilmez.

This application runs completely locally. Your images are not sent to any server.

## ⚠️ Uyarı / Warning

Bu uygulamayı sorumlu bir şekilde kullanın. Başkalarının izni olmadan yüzlerini kullanmayın.

Use this application responsibly. Do not use others' faces without permission.

## 🙏 Teşekkürler / Credits

Bu uygulama [FaceFusion](https://github.com/facefusion/facefusion) projesini kullanmaktadır.

This application uses the [FaceFusion](https://github.com/facefusion/facefusion) project.

## 📞 Destek / Support

Sorun yaşıyorsanız veya önerileriniz varsa lütfen bir issue açın.

If you experience issues or have suggestions, please open an issue.

---

**Keyifli Kullanımlar! / Enjoy!** 🎉
