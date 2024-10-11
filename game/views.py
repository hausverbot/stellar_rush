from django.shortcuts import render


# Create your views here.
def game(request, room_name):
    return render(request, 'game.html', {"room_name": room_name})


def room(request):
    return render(request, "game_lobby.html")
