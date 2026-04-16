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
    class Meta:
        model = Kiraci
        fields = [
            'firma_adi', 'yetkili_kisi', 'telefon', 'email',
            'adres', 'kira_baslangic_tarihi', 'kira_bitis_tarihi',
            'aylik_kira_tutari', 'depozit', 'kira_gunu',
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
            'depozit': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'kira_gunu': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 28}),
            'sozlesme': forms.FileInput(attrs={'class': 'form-file'}),
            'notlar': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class OdemeForm(forms.ModelForm):
    class Meta:
        model = Odeme
        fields = ['yil', 'ay', 'odenen_tutar', 'odeme_turu', 'odeme_tarihi', 'aciklama']
        widgets = {
            'yil': forms.NumberInput(attrs={'class': 'form-input', 'min': 2020, 'max': 2099}),
            'ay': forms.Select(attrs={'class': 'form-input'}, choices=[
                (i, ad) for i, ad in enumerate(
                    ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                     'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'], 0
                ) if i > 0
            ]),
            'odenen_tutar': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'odeme_turu': forms.Select(attrs={'class': 'form-input'}),
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
            self.fields['odeme_tarihi'].initial = bugun
            if kiraci:
                self.fields['odenen_tutar'].initial = kiraci.aylik_kira_tutari
