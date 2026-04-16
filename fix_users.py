import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiracitakip.settings')
django.setup()

from django.contrib.auth.models import User
from kiraci.models import Kiraci, UserProfile

u = User.objects.get(id=1)

# Kiracilari admin'e bagla
count = Kiraci.objects.filter(user=None).update(user=u)
print(f'{count} kiraci admin kullanicisina baglandi.')

# Admin icin profil olustur (yoksa)
profil, created = UserProfile.objects.get_or_create(user=u)
if created:
    print('Admin profili olusturuldu.')
else:
    print('Admin profili zaten var.')

print('Bitti.')
