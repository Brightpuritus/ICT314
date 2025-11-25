from .models import Player


def user_points(request):
    """Context processor to inject logged-in user's points as `user_points`.

    Behavior:
    - If user is authenticated, attempt to find a Player linked to that user.
    - If not found, try to find a Player with the same username and attach it to
      the user to avoid duplicate accounts.
    - If still not found, create a Player for the user.
    - Return {'user_points': <points int>}
    """
    if not request.user or not request.user.is_authenticated:
        return {"user_points": None}

    user = request.user
    try:
        # Prefer a Player linked to the user
        player = getattr(user, "player_profile", None)
        if player is None:
            # Try to find by username and link
            player = Player.objects.filter(name=user.username).first()
            if player:
                player.user = user
                player.save()
            else:
                # Create a fresh Player for this user
                player = Player.objects.create(user=user, name=user.username)
        return {"user_points": player.points}
    except Exception:
        # Fail silently to avoid breaking page render; return None
        return {"user_points": None}
