"""
Veri migrasyonu: Mevcut kiracıların mevcut kira tutarlarını KiraZamGecmisi tablosuna
başlangıç kaydı olarak ekler.

Geçerlilik tarihi olarak şu öncelik sırası kullanılır:
  1. kira_baslangic_tarihi varsa ayın 1'i
  2. Yoksa olusturulma_tarihi'nin ayı
"""
from django.db import migrations


def backfill_zam_gecmisi(apps, schema_editor):
    Kiraci = apps.get_model('kiraci', 'Kiraci')
    KiraZamGecmisi = apps.get_model('kiraci', 'KiraZamGecmisi')

    for kiraci in Kiraci.objects.all():
        # Geçerlilik tarihi: kira başlangıç tarihi varsa onu kullan, yoksa kayıt tarihi
        if kiraci.kira_baslangic_tarihi:
            gecerlilik = kiraci.kira_baslangic_tarihi.replace(day=1)
        else:
            gecerlilik = kiraci.olusturulma_tarihi.date().replace(day=1)

        # Aynı kiracı+tarih için zaten kayıt yoksa ekle
        if not KiraZamGecmisi.objects.filter(
            kiraci=kiraci,
            gecerlilik_tarihi=gecerlilik
        ).exists():
            KiraZamGecmisi.objects.create(
                kiraci=kiraci,
                gecerlilik_tarihi=gecerlilik,
                aylik_kira_tutari=kiraci.aylik_kira_tutari,
                yillik_kira_tutari=kiraci.yillik_kira_tutari,
                aciklama='Otomatik: sistem kurulumu sırasında oluşturuldu',
            )


def reverse_backfill(apps, schema_editor):
    KiraZamGecmisi = apps.get_model('kiraci', 'KiraZamGecmisi')
    KiraZamGecmisi.objects.filter(
        aciklama='Otomatik: sistem kurulumu sırasında oluşturuldu'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('kiraci', '0011_kira_zam_gecmisi'),
    ]

    operations = [
        migrations.RunPython(backfill_zam_gecmisi, reverse_code=reverse_backfill),
    ]
