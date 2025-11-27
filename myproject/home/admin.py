from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon')  # แสดงคอลัมน์ในหน้า Admin
    search_fields = ('name',)  # เพิ่มช่องค้นหาด้วยชื่อเกม
    list_filter = ('name',)  # เพิ่มตัวกรอง
