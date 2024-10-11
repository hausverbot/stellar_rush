from django.urls import path
from . import views

urlpatterns = [
    path('', views.room, name='rooms'),
    path("<str:room_name>/", views.game, name="game_phaser"),
]