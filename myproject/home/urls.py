from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('api/get-points/', views.get_user_points, name='get_user_points'),
    path('topup/', views.topup_games, name='topup_games'),
    path('topup/<str:game_id>/', views.topup_form, name='topup_form'),
    path('topup/<str:game_id>/process/', views.topup_process, name='topup_process'),
    path('topup/<str:game_id>/confirm/', views.topup_confirm, name='topup_confirm'),
    path('register/', views.register, name='register'),
]
