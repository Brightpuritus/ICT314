from django.db import models
from django.conf import settings


class Player(models.Model):
	"""Simple player/account model to track points for top-up users.

	This model can be linked to Django's auth User via the optional `user`
	OneToOneField. Existing deployments that used `name` will continue to
	work — when a logged-in user is detected we will try to link by name.
	"""
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.CASCADE,
		related_name='player_profile'
	)
	name = models.CharField(max_length=150, unique=True)
	points = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.points} pts)"

	def add_points(self, amount: int):
		self.points = max(0, self.points + int(amount))
		self.save()

	def use_points(self, amount: int) -> int:
		"""Attempt to use `amount` points. Returns actual points deducted."""
		amount = int(amount)
		deducted = min(self.points, max(0, amount))
		self.points -= deducted
		self.save()
		return deducted
