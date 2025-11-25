from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('topup/', views.topup_games, name='topup_games'),
    path('topup/<str:game_id>/', views.topup_form, name='topup_form'),
    path('topup/<str:game_id>/process/', views.topup_process, name='topup_process'),
    path('register/', views.register, name='register'),
]
