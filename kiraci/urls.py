from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('giris/', views.giris, name='giris'),
    path('kayit/', views.kayit, name='kayit'),
    path('cikis/', views.cikis, name='cikis'),
    path('profil/', views.profil, name='profil'),

    # Kiracı
    path('', views.kiraci_listesi, name='kiraci_listesi'),
    path('kiraci/ekle/', views.kiraci_ekle, name='kiraci_ekle'),
    path('kiraci/<int:pk>/', views.kiraci_detay, name='kiraci_detay'),
    path('kiraci/<int:pk>/duzenle/', views.kiraci_duzenle, name='kiraci_duzenle'),
    path('kiraci/<int:pk>/excel/', views.kiraci_excel, name='kiraci_excel'),
    path('kiraci/<int:pk>/sil/', views.kiraci_sil, name='kiraci_sil'),

    # Ödeme
    path('kiraci/<int:kiraci_pk>/odeme/ekle/', views.odeme_ekle, name='odeme_ekle'),
    path('odeme/<int:pk>/duzenle/', views.odeme_duzenle, name='odeme_duzenle'),
    path('odeme/<int:pk>/sil/', views.odeme_sil, name='odeme_sil'),

    # Bildirim yanıt
    path('bildirim/onayla/<str:token>/', views.odeme_onayla, name='odeme_onayla'),
    path('bildirim/reddet/<str:token>/', views.odeme_reddet, name='odeme_reddet'),

    # Özet
    path('aylik-ozet/', views.aylik_ozet, name='aylik_ozet'),
]
