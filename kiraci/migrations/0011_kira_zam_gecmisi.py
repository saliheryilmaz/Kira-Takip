from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kiraci', '0010_alter_kiraci_aylik_kira_tutari'),
    ]

    operations = [
        migrations.CreateModel(
            name='KiraZamGecmisi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gecerlilik_tarihi', models.DateField(verbose_name='Geçerlilik Tarihi (Ay Başı)')),
                ('aylik_kira_tutari', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Aylık Kira Tutarı (₺)')),
                ('yillik_kira_tutari', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Yıllık Kira Tutarı (₺)')),
                ('aciklama', models.CharField(blank=True, max_length=200, verbose_name='Açıklama (ör. TÜFE zammı)')),
                ('olusturulma_tarihi', models.DateTimeField(auto_now_add=True)),
                ('kiraci', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zam_gecmisi',
                    to='kiraci.kiraci',
                    verbose_name='Kiracı',
                )),
            ],
            options={
                'verbose_name': 'Kira Zam Geçmişi',
                'verbose_name_plural': 'Kira Zam Geçmişleri',
                'ordering': ['kiraci', 'gecerlilik_tarihi'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='kirazamgecmisi',
            unique_together={('kiraci', 'gecerlilik_tarihi')},
        ),
    ]
