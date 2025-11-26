#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User

# ค้นหา admin และแก้ไขให้เป็น superuser
try:
    admin = User.objects.get(username='admin')
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password('admin123')  # ตั้งรหัสผ่าน
    admin.save()
    print("✅ อัปเดต admin สำเร็จ!")
    print(f"ชื่อผู้ใช้: admin")
    print(f"รหัสผ่าน: admin123")
    print(f"เป็น Staff: {admin.is_staff}")
    print(f"เป็น Superuser: {admin.is_superuser}")
except User.DoesNotExist:
    print("❌ ไม่พบ admin user")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
