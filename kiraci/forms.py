from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Kiraci, Odeme, UserProfile


class KayitForm(UserCreationForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ornek@mail.com'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Kullanıcı adı'})
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})


class ProfilForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['callmebot_api_key', 'whatsapp_no', 'email_bildirimleri', 'bildirim_email', 'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password']
        widgets = {
            'callmebot_api_key': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'CallMeBot API Key'}),
            'whatsapp_no': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '5XXXXXXXXX'}),
            'email_bildirimleri': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'bildirim_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'bildirim@gmail.com'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'smtp.gmail.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-input'}),
            'smtp_user': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'gonderici@gmail.com'}),
            'smtp_password': forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'App Password (boşluksuz)'}, render_value=True),
        }


class KiraciForm(forms.ModelForm):

    # Yeni kira tutarının hangi aydan itibaren geçerli olduğunu seçmek için ek alan
    # Sadece düzenleme (zam) ekranında gösterilir, yeni kiracı eklerken kullanılmaz
    zam_gecerlilik_tarihi = forms.DateField(
        required=False,
        label='Yeni Tutar Geçerlilik Tarihi',
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        help_text='Kira tutarını değiştiriyorsanız hangi aydan itibaren geçerli olacağını seçin.'
    )

    class Meta:
        model = Kiraci
        fields = [
            'firma_adi', 'yetkili_kisi', 'telefon', 'email',
            'adres', 'kira_baslangic_tarihi', 'kira_bitis_tarihi',
            'aylik_kira_tutari', 'yillik_kira_tutari', 'depozit', 'kira_gunu',
            'sozlesme', 'notlar', 'aktif'
        ]
        widgets = {
            'firma_adi': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Firma adı'}),
            'yetkili_kisi': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ad Soyad'}),
            'telefon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '05XX XXX XX XX'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ornek@firma.com'}),
            'adres': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'kira_baslangic_tarihi': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'kira_bitis_tarihi': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'aylik_kira_tutari': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'yillik_kira_tutari': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Girilmezse aylık × 12'}),            'depozit': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'kira_gunu': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 28}),
            'sozlesme': forms.FileInput(attrs={'class': 'form-file'}),
            'notlar': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bugun = timezone.now().date()
        if not self.instance.pk:
            bugun_str = bugun.strftime('%Y-%m-%d')
            self.fields['kira_baslangic_tarihi'].widget.attrs['value'] = bugun_str
            self.fields['kira_baslangic_tarihi'].initial = bugun_str
        else:
            # Düzenleme modunda: varsayılan geçerlilik tarihi = bir sonraki ayın 1'i
            if bugun.month == 12:
                sonraki_ay = bugun.replace(year=bugun.year + 1, month=1, day=1)
            else:
                sonraki_ay = bugun.replace(month=bugun.month + 1, day=1)
            self.fields['zam_gecerlilik_tarihi'].initial = sonraki_ay.strftime('%Y-%m-%d')
            self.fields['zam_gecerlilik_tarihi'].widget.attrs['value'] = sonraki_ay.strftime('%Y-%m-%d')
        # Her iki alan da opsiyonel — form seviyesinde required=False
        self.fields['aylik_kira_tutari'].required = False
        self.fields['yillik_kira_tutari'].required = False

    def clean(self):
        cleaned = super().clean()
        aylik = cleaned.get('aylik_kira_tutari')
        yillik = cleaned.get('yillik_kira_tutari')
        if not aylik and not yillik:
            raise forms.ValidationError('Aylık veya yıllık kira tutarından en az birini girin.')
        return cleaned


class OdemeForm(forms.ModelForm):
    class Meta:
        model = Odeme
        fields = ['yil', 'ay', 'odenen_tutar', 'odeme_turu', 'odeme_tarihi', 'aciklama']
        widgets = {
            'yil': forms.HiddenInput(),
            'ay': forms.HiddenInput(),
            'odenen_tutar': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'odeme_turu': forms.HiddenInput(),
            'odeme_tarihi': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        kiraci = kwargs.pop('kiraci', None)
        super().__init__(*args, **kwargs)
        bugun = timezone.now().date()
        if not self.instance.pk:
            self.fields['yil'].initial = bugun.year
            self.fields['ay'].initial = bugun.month
            self.fields['odeme_tarihi'].initial = bugun.strftime('%Y-%m-%d')
            self.fields['odeme_tarihi'].widget.attrs['value'] = bugun.strftime('%Y-%m-%d')
            self.fields['odeme_turu'].initial = 'nakit'
            if kiraci:
                self.fields['odenen_tutar'].initial = kiraci._donem_tutari()

    def clean(self):
        cleaned = super().clean()
        odeme_tarihi = cleaned.get('odeme_tarihi')
        if odeme_tarihi:
            # Yıl ve ay'ı ödeme tarihinden otomatik al
            cleaned['yil'] = odeme_tarihi.year
            cleaned['ay'] = odeme_tarihi.month
        return cleaned
