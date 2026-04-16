from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
import calendar


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    callmebot_api_key = models.CharField(max_length=50, blank=True, verbose_name="CallMeBot API Key")
    whatsapp_no = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp No (5XXXXXXXXX)")
    email_bildirimleri = models.BooleanField(default=False, verbose_name="Email Bildirimleri")
    bildirim_email = models.EmailField(blank=True, verbose_name="Bildirim Email Adresi")
    smtp_host = models.CharField(max_length=100, blank=True, default='smtp.gmail.com', verbose_name="SMTP Sunucu")
    smtp_port = models.IntegerField(default=587, verbose_name="SMTP Port")
    smtp_user = models.EmailField(blank=True, verbose_name="SMTP Kullanıcı (Gmail)")
    smtp_password = models.CharField(max_length=100, blank=True, verbose_name="SMTP Şifre / App Password")

    class Meta:
        verbose_name = "Kullanıcı Profili"

    def __str__(self):
        return self.user.username


class Kiraci(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kiraciler', verbose_name="Kullanıcı", null=True)
    firma_adi = models.CharField(max_length=200, verbose_name="Firma Adı")
    yetkili_kisi = models.CharField(max_length=150, blank=True, verbose_name="Yetkili Kişi")
    telefon = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, verbose_name="Adres")
    kira_baslangic_tarihi = models.DateField(verbose_name="Kira Başlangıç Tarihi")
    kira_bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Kira Bitiş Tarihi")
    aylik_kira_tutari = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Aylık Kira Tutarı (₺)")
    sozlesme = models.FileField(upload_to='sozlesmeler/', blank=True, null=True, verbose_name="Sözleşme Dosyası")
    depozit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Depozit (₺)")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    kira_gunu = models.IntegerField(default=1, verbose_name="Kira Ödeme Günü (ayın kaçı)")
    whatsapp_no = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp No (5XXXXXXXXX)")
    aktif = models.BooleanField(default=True, verbose_name="Aktif Kiracı")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kiracı"
        verbose_name_plural = "Kiracılar"
        ordering = ['firma_adi']

    def __str__(self):
        return self.firma_adi

    def toplam_beklenen(self, bitis_yil=None, bitis_ay=None):
        """Başlangıçtan bugüne kadar beklenen toplam kira tutarı."""
        bugun = timezone.now().date()
        if bitis_yil and bitis_ay:
            bitis = bugun.replace(year=bitis_yil, month=bitis_ay, day=1)
        else:
            bitis = bugun

        baslangic = self.kira_baslangic_tarihi.replace(day=1)
        bitis_ay_basi = bitis.replace(day=1)

        ay_sayisi = 0
        current = baslangic
        while current <= bitis_ay_basi:
            ay_sayisi += 1
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return self.aylik_kira_tutari * ay_sayisi

    def toplam_odenen(self):
        return self.odemeler.aggregate(
            toplam=models.Sum('odenen_tutar')
        )['toplam'] or Decimal('0')

    def toplam_borc(self):
        beklenen = self.toplam_beklenen()
        odenen = self.toplam_odenen()
        fark = beklenen - odenen
        return fark if fark > 0 else Decimal('0')

    def ay_listesi(self):
        """Başlangıçtan bugüne kadar tüm ayları döndür."""
        bugun = timezone.now().date()
        aylar = []
        current = self.kira_baslangic_tarihi.replace(day=1)
        bitis = bugun.replace(day=1)

        while current <= bitis:
            odemeler = self.odemeler.filter(yil=current.year, ay=current.month)
            odenen = odemeler.aggregate(t=models.Sum('odenen_tutar'))['t'] or Decimal('0')
            aylar.append({
                'yil': current.year,
                'ay': current.month,
                'ay_adi': self._ay_adi(current.month),
                'beklenen': self.aylik_kira_tutari,
                'odemeler': odemeler,
                'odendi': odenen >= self.aylik_kira_tutari,
                'odenen': odenen,
                'eksik': max(self.aylik_kira_tutari - odenen, Decimal('0')),
            })
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return list(reversed(aylar))

    @staticmethod
    def _ay_adi(ay):
        aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        return aylar[ay]


class Odeme(models.Model):
    ODEME_TURU_CHOICES = [
        ('resmi', 'Resmi (Banka/Havale)'),
        ('gayri_resmi', 'Gayri Resmi (Belgesiz)'),
        ('elden', 'Elden (Nakit)'),
    ]

    kiraci = models.ForeignKey(Kiraci, on_delete=models.CASCADE, related_name='odemeler', verbose_name="Kiracı")
    yil = models.IntegerField(verbose_name="Yıl")
    ay = models.IntegerField(verbose_name="Ay")
    odenen_tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Ödenen Tutar (₺)")
    odeme_turu = models.CharField(max_length=20, choices=ODEME_TURU_CHOICES, verbose_name="Ödeme Türü")
    odeme_tarihi = models.DateField(default=timezone.now, verbose_name="Ödeme Tarihi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ödeme"
        verbose_name_plural = "Ödemeler"
        ordering = ['-yil', '-ay', '-olusturulma_tarihi']

    def __str__(self):
        return f"{self.kiraci.firma_adi} - {self.ay}/{self.yil}"

    @property
    def ay_adi(self):
        aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        return aylar[self.ay]


class BildirimLog(models.Model):
    kiraci = models.ForeignKey(Kiraci, on_delete=models.CASCADE, related_name='bildirimler')
    yil = models.IntegerField()
    ay = models.IntegerField()
    gonderildi_at = models.DateTimeField(auto_now_add=True)
    mesaj = models.TextField(blank=True)
    token = models.CharField(max_length=64, blank=True, unique=True, null=True)
    yanitlandi = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Bildirim Logu"
        verbose_name_plural = "Bildirim Logları"
        ordering = ['-gonderildi_at']

    def __str__(self):
        return f"{self.kiraci.firma_adi} - {self.ay}/{self.yil}"
