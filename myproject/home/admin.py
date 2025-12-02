from django.contrib import admin
from .models import Game, Order, Player

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon')
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'game', 'player_name', 'original_amount', 'paid_amount', 'bonus_points', 'status', 'created_at')
    search_fields = ('transaction_id', 'player_name', 'game__name')
    list_filter = ('status', 'game', 'created_at')
    readonly_fields = ('transaction_id', 'created_at', 'user')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('original_amount', 'used_points', 'paid_amount', 'bonus_points')
        return self.readonly_fields
