from django.contrib import admin
from .models import Kiraci, Odeme

@admin.register(Kiraci)
class KiraciAdmin(admin.ModelAdmin):
    list_display = ['firma_adi', 'yetkili_kisi', 'telefon', 'aylik_kira_tutari', 'kira_baslangic_tarihi', 'aktif']
    list_filter = ['aktif']
    search_fields = ['firma_adi', 'yetkili_kisi']

@admin.register(Odeme)
class OdemeAdmin(admin.ModelAdmin):
    list_display = ['kiraci', 'ay', 'yil', 'odenen_tutar', 'odeme_turu', 'odeme_tarihi']
    list_filter = ['odeme_turu', 'yil', 'ay']
