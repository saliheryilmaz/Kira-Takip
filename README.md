# 🏠 Kira Takip

> **Django tabanlı kiracı ve kira ödeme yönetim sistemi.**  
> WhatsApp & Gmail entegrasyonu ile otomatik ödeme hatırlatmaları.

---

## 📌 Proje Hakkında

**Kira Takip**, ev sahiplerinin kiracılarını, kira ödemelerini ve gecikmeleri tek bir panelden yönetebileceği full-stack bir web uygulamasıdır.

Uygulama; manuel takip ihtiyacını ortadan kaldırmak için **WhatsApp (CallMeBot API)** ve **Gmail SMTP** üzerinden otomatik bildirim gönderme altyapısı içermektedir. Kiracı ödeme durumuna göre sistem otomatik olarak hatırlatma mesajı iletir.

---

## 🚀 Özellikler

### 🏘️ Kiracı Yönetimi
- Kiracı ekleme, düzenleme ve silme
- Her kiracıya ait daire/mülk bilgisi tanımlama
- Kiracı iletişim bilgileri (telefon, e-posta) yönetimi

### 💸 Kira Ödeme Takibi
- Aylık kira kaydı oluşturma ve güncelleme
- Ödendi / ödenmedi durumu işaretleme
- Gecikmiş ödemelerin otomatik tespiti
- Ödeme geçmişi görüntüleme

### 📲 WhatsApp Bildirimleri (CallMeBot API)
- Ödeme yaklaştığında kiracıya otomatik WhatsApp mesajı
- Gecikmiş ödemeler için hatırlatma bildirimi
- CallMeBot API entegrasyonu ile kolay kurulum, sıfır maliyet

### 📧 E-posta Bildirimleri (Gmail SMTP)
- Django'nun e-posta altyapısı üzerinden Gmail SMTP ile bildirim
- HTML e-posta şablonları ile profesyonel görünüm
- Ödeme özeti ve hatırlatma e-postaları

### 📊 Yönetim Paneli
- Tüm kiracıların anlık ödeme durumu özeti
- Aylık gelir takibi
- Gecikmiş ödeme listesi

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| **Backend** | Python 3, Django |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Bildirimler** | CallMeBot API (WhatsApp), Gmail SMTP |
| **Veritabanı** | SQLite (geliştirme) / MySQL (üretim) |
| **Deployment** | PythonAnywhere |

---
## 📲 WhatsApp Entegrasyonu

Uygulama, ücretsiz [CallMeBot API](https://www.callmebot.com/blog/free-api-whatsapp-messages/) servisini kullanmaktadır.

```python
# Örnek kullanım
import requests

def send_whatsapp(phone, message, api_key):
    url = f"https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": phone,
        "text": message,
        "apikey": api_key
    }
    requests.get(url, params=params)
```

Aktivasyon için kiracının bir kez CallMeBot'a mesaj atması yeterlidir.

---

## 📧 Gmail SMTP Entegrasyonu

`settings.py` içinde aşağıdaki yapılandırma kullanılmaktadır:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
```

---

## 👤 Geliştirici

**Salih Eryılmaz**  
[GitHub](https://github.com/saliheryilmaz) 

---

## 📄 Lisans

Bu proje MIT lisansı ile lisanslanmıştır.
