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
    aylik_kira_tutari = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Aylık Kira Tutarı (₺)")
    yillik_kira_tutari = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Yıllık Kira Tutarı (₺)")
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

    def _takip_baslangic(self):
        """Ödeme takibinin başladığı ay — kaydedildiği ay veya en eski ödeme, hangisi önceyse."""
        kayit_ay = self.olusturulma_tarihi.date().replace(day=1)
        en_eski = self.odemeler.order_by('yil', 'ay').first()
        if en_eski:
            odeme_ay = self.olusturulma_tarihi.date().replace(
                year=en_eski.yil, month=en_eski.ay, day=1
            )
            return min(kayit_ay, odeme_ay)
        return kayit_ay

    def _donem_tutari(self):
        """Anlık kira tutarı (form/gösterim için). Yıllık varsa yıllık, yoksa aylık."""
        if self.yillik_kira_tutari:
            return self.yillik_kira_tutari
        return self.aylik_kira_tutari or Decimal('0')

    def _donem_ay_sayisi(self):
        """Yıllık kirada 1 dönem = 12 ay, aylık kirada 1 dönem = 1 ay."""
        return 12 if self.yillik_kira_tutari else 1

    def _tarihce_tutari(self, tarih):
        """
        Verilen tarihe (date nesnesi, ayın 1'i) ait geçerli kira tutarını tarihçeden döndür.
        Tarihçe yoksa anlık tutarı kullan (geriye dönük uyumluluk).
        """
        # O tarihten önce veya o tarihte başlamış en son kaydı bul
        gecmis = self.zam_gecmisi.filter(
            gecerlilik_tarihi__lte=tarih
        ).order_by('-gecerlilik_tarihi').first()

        if gecmis:
            if gecmis.yillik_kira_tutari:
                return gecmis.yillik_kira_tutari, True
            return gecmis.aylik_kira_tutari or Decimal('0'), False

        # O tarihten önce kayıt yoksa — en eski tarihçe kaydını kullan
        # (zam öncesi aylara yanlışlıkla yeni tutar uygulanmasını engeller)
        en_eski = self.zam_gecmisi.order_by('gecerlilik_tarihi').first()
        if en_eski:
            if en_eski.yillik_kira_tutari:
                return en_eski.yillik_kira_tutari, True
            return en_eski.aylik_kira_tutari or Decimal('0'), False

        # Hiç tarihçe kaydı yoksa anlık değeri kullan (yeni eklenen kiracı)
        if self.yillik_kira_tutari:
            return self.yillik_kira_tutari, True
        return self.aylik_kira_tutari or Decimal('0'), False

    def toplam_beklenen(self, bitis_yil=None, bitis_ay=None):
        """Kaydedildiği aydan bugüne kadar beklenen toplam kira tutarı (tarihçe bazlı)."""
        bugun = timezone.now().date()
        if bitis_yil and bitis_ay:
            bitis = bugun.replace(year=bitis_yil, month=bitis_ay, day=1)
        else:
            bitis = bugun

        baslangic = self._takip_baslangic()
        bitis_ay_basi = bitis.replace(day=1)

        if baslangic > bitis_ay_basi:
            return Decimal('0')

        toplam = Decimal('0')
        current = baslangic
        # Yıllık modda aynı yıl/oran bloğunu tekrar saymamak için
        yillik_sayilan = set()

        while current <= bitis_ay_basi:
            tutar, yillik_mod = self._tarihce_tutari(current)

            if yillik_mod:
                # Yıllık modda: her başlamış yıl için bir kez tam yıllık tutar ekle
                # "Yıl" = aynı gecerlilik_tarihi bloğunda takvim yılı
                yil_key = (current.year, tutar)
                if yil_key not in yillik_sayilan:
                    yillik_sayilan.add(yil_key)
                    toplam += tutar
            else:
                # Aylık mod: her ay ayrı ayrı ekle
                toplam += tutar

            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return toplam

    def bu_ay_borc(self):
        """Bu ay için eksik kalan tutarı döndürür. Yıllık modda toplam borcu gösterir."""
        if self.yillik_kira_tutari:
            return self.toplam_borc()
        bugun = timezone.now().date()
        ay_basi = bugun.replace(day=1)
        beklenen, _ = self._tarihce_tutari(ay_basi)
        odenen = self.odemeler.filter(
            yil=bugun.year, ay=bugun.month
        ).aggregate(t=models.Sum('odenen_tutar'))['t'] or Decimal('0')
        fark = beklenen - odenen
        return fark if fark > 0 else Decimal('0')

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
        """Kaydedildiği aydan en son ödemeye kadar tüm ayları döndür (tarihçe bazlı)."""
        bugun = timezone.now().date()
        baslangic = self._takip_baslangic()

        # Bitiş: bugün veya en son ödemenin ayı — hangisi daha ileriyse
        son_odeme = self.odemeler.order_by('-yil', '-ay').first()
        if son_odeme:
            son_odeme_ay = bugun.replace(year=son_odeme.yil, month=son_odeme.ay, day=1)
            bitis = max(bugun.replace(day=1), son_odeme_ay)
        else:
            bitis = bugun.replace(day=1)

        if baslangic > bitis:
            return []

        aylar = []
        current = baslangic
        while current <= bitis:
            odemeler = self.odemeler.filter(yil=current.year, ay=current.month)
            odenen = odemeler.aggregate(t=models.Sum('odenen_tutar'))['t'] or Decimal('0')
            # O aya ait geçerli tutarı tarihçeden al
            beklenen, yillik_mod = self._tarihce_tutari(current)
            aylar.append({
                'yil': current.year,
                'ay': current.month,
                'ay_adi': self._ay_adi(current.month),
                'beklenen': beklenen,
                'odemeler': odemeler,
                'odendi': odenen >= beklenen,
                'odenen': odenen,
                'eksik': max(beklenen - odenen, Decimal('0')),
                'yillik_mod': yillik_mod,
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
        ('nakit', 'Nakit'),
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


class KiraZamGecmisi(models.Model):
    """
    Kira tutarının tarihçesini tutar. Her zam yapıldığında yeni bir kayıt oluşturulur.
    Böylece geçmiş aylardaki beklenen tutar doğru hesaplanır.
    """
    kiraci = models.ForeignKey(
        Kiraci, on_delete=models.CASCADE,
        related_name='zam_gecmisi', verbose_name="Kiracı"
    )
    gecerlilik_tarihi = models.DateField(verbose_name="Geçerlilik Tarihi (Ay Başı)")
    aylik_kira_tutari = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Aylık Kira Tutarı (₺)"
    )
    yillik_kira_tutari = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Yıllık Kira Tutarı (₺)"
    )
    aciklama = models.CharField(max_length=200, blank=True, verbose_name="Açıklama (ör. TÜFE zammı)")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kira Zam Geçmişi"
        verbose_name_plural = "Kira Zam Geçmişleri"
        ordering = ['kiraci', 'gecerlilik_tarihi']
        unique_together = [('kiraci', 'gecerlilik_tarihi')]

    def __str__(self):
        tutar = self.yillik_kira_tutari or self.aylik_kira_tutari or 0
        return f"{self.kiraci.firma_adi} — {self.gecerlilik_tarihi.strftime('%m/%Y')} → {tutar} ₺"


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
