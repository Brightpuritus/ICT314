#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from home.models import Player

print("=" * 60)
print("ผู้ใช้ทั้งหมดในระบบ")
print("=" * 60)

users = User.objects.all()
for user in users:
    print(f"\nชื่อผู้ใช้: {user.username}")
    print(f"อีเมล: {user.email}")
    print(f"เป็น Staff: {user.is_staff}")
    print(f"เป็น Superuser: {user.is_superuser}")
    
    # ดูพอยต์ของผู้ใช้
    try:
        player = user.player_profile
        print(f"พอยต์: {player.points}")
    except:
        print(f"พอยต์: ไม่มีข้อมูล")
    print("-" * 60)

print("\n" + "=" * 60)
print("ข้อมูลพอยต์ทั้งหมด")
print("=" * 60)

players = Player.objects.all()
for player in players:
    print(f"\nชื่อผู้เล่น: {player.name}")
    print(f"พอยต์: {player.points}")
    print(f"สร้างเมื่อ: {player.created_at}")
    if player.user:
        print(f"ผูกกับผู้ใช้: {player.user.username}")
    else:
        print(f"ผูกกับผู้ใช้: ไม่ได้ผูก")
    print("-" * 60)

print("\nทั้งหมด:")
print(f"จำนวนผู้ใช้: {users.count()}")
print(f"จำนวนผู้เล่น: {players.count()}")
