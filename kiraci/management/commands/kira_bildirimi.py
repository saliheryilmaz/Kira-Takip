import urllib.request
import urllib.parse
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings as django_settings
from kiraci.models import Kiraci, Odeme, BildirimLog, UserProfile

SITE_URL = getattr(django_settings, 'SITE_URL', 'http://127.0.0.1:8000')


class Command(BaseCommand):
    help = 'Kira ödeme günü gelen kiracılara WhatsApp/Email bildirimi gönderir'

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true',
                            help='Tüm kiracılara test mesajı gönderir (kira günü/ödeme kontrolü yok)')

    def handle(self, *args, **options):
        bugun = timezone.now().date()
        yil, ay = bugun.year, bugun.month
        test_modu = options['test']

        kiraciler = Kiraci.objects.filter(aktif=True).select_related('user__profil')

        for kiraci in kiraciler:
            try:
                profil = kiraci.user.profil
            except (AttributeError, UserProfile.DoesNotExist):
                self.stdout.write(f'{kiraci.firma_adi}: Profil yok, atlanıyor.')
                continue

            if not test_modu:
                if bugun.day < kiraci.kira_gunu:
                    continue
                if Odeme.objects.filter(kiraci=kiraci, yil=yil, ay=ay).exists():
                    self.stdout.write(f'{kiraci.firma_adi}: Ödeme alındı, atlanıyor.')
                    continue
                # Hayır dendi mi? (yanitlandi=True ama ödeme yok → yarın tekrar sor)
                # Yanıtlanmamış log varsa bugün zaten gönderilmiş, atla
                bugun_log = BildirimLog.objects.filter(
                    kiraci=kiraci, yil=yil, ay=ay,
                    gonderildi_at__date=bugun, yanitlandi=False
                ).exists()
                if bugun_log:
                    self.stdout.write(f'{kiraci.firma_adi}: Bugün zaten gönderildi, atlanıyor.')
                    continue

            # Mesaj oluştur
            if test_modu:
                mesaj_wa = f"🧪 TEST\nFirma: {kiraci.firma_adi}\nKiraTakip bağlantısı başarılı!"
                mesaj_email = mesaj_wa
                token = None
            else:
                token = secrets.token_urlsafe(32)
                evet_url = f"{SITE_URL}/bildirim/onayla/{token}/"
                hayir_url = f"{SITE_URL}/bildirim/reddet/{token}/"
                ay_adi = self._ay_adi(ay)
                tarih_str = bugun.strftime('%d %B %Y').replace(
                    'January','Ocak').replace('February','Şubat').replace('March','Mart'
                    ).replace('April','Nisan').replace('May','Mayıs').replace('June','Haziran'
                    ).replace('July','Temmuz').replace('August','Ağustos').replace('September','Eylül'
                    ).replace('October','Ekim').replace('November','Kasım').replace('December','Aralık')
                mesaj_wa = (
                    f"🏠 {kiraci.firma_adi}\n"
                    f"{tarih_str} — {ay_adi} {yil} kirası\n"
                    f"Ödeme parası geldi mi?\n\n"
                    f"✅ Evet Alındı:\n{evet_url}\n\n"
                    f"❌ Hayır, yarın sor:\n{hayir_url}"
                )
                mesaj_email = mesaj_wa

            # WhatsApp
            api_key = profil.callmebot_api_key
            hedef_no = profil.whatsapp_no
            if api_key and hedef_no:
                if not hedef_no.startswith('+'):
                    hedef_no = '+90' + hedef_no.lstrip('0')
                if self._wa_gonder(hedef_no, mesaj_wa, api_key):
                    if not test_modu and token:
                        BildirimLog.objects.create(
                            kiraci=kiraci, yil=yil, ay=ay,
                            mesaj=mesaj_wa, token=token
                        )
                    self.stdout.write(self.style.SUCCESS(
                        f'{kiraci.firma_adi}: WhatsApp gönderildi → {hedef_no}'))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'{kiraci.firma_adi}: WhatsApp gönderilemedi!'))
            else:
                self.stdout.write(f'{kiraci.firma_adi}: WhatsApp ayarı eksik, atlanıyor.')

            # Email
            if profil.email_bildirimleri and profil.bildirim_email and profil.smtp_user and profil.smtp_password:
                if test_modu:
                    konu = 'KiraTakip - Test Email'
                    icerik = mesaj_email
                else:
                    konu = f'{kiraci.firma_adi} — {self._ay_adi(ay)} {yil} Kira Hatırlatması'
                    icerik = mesaj_email

                if self._email_gonder(profil, konu, icerik):
                    self.stdout.write(self.style.SUCCESS(
                        f'{kiraci.firma_adi}: Email gönderildi → {profil.bildirim_email}'))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'{kiraci.firma_adi}: Email gönderilemedi!'))

    def _wa_gonder(self, telefon, mesaj, api_key):
        try:
            url = (
                f"https://api.callmebot.com/whatsapp.php"
                f"?phone={telefon}&text={urllib.parse.quote(mesaj)}&apikey={api_key}"
            )
            with urllib.request.urlopen(url, timeout=10) as r:
                return r.status == 200
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'WhatsApp hatası: {e}'))
            return False

    def _email_gonder(self, profil, konu, icerik):
        try:
            msg = MIMEMultipart()
            msg['From'] = profil.smtp_user
            msg['To'] = profil.bildirim_email
            msg['Subject'] = konu
            msg.attach(MIMEText(icerik, 'plain', 'utf-8'))
            with smtplib.SMTP(profil.smtp_host, profil.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(profil.smtp_user, profil.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Email hatası: {e}'))
            return False

    def _ay_adi(self, ay):
        return ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'][ay]
