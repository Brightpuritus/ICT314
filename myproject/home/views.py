from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from .models import Player, Game
import uuid
from io import BytesIO
import base64

def index(request):
    if request.user.is_authenticated:
        return redirect('topup_games')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('topup_games')
        else:
            return render(request, 'index.html', {'error': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'})
    
    return render(request, 'index.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('topup_games')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        errors = []
        if not username:
            errors.append('กรุณากรอกชื่อผู้ใช้')
        elif len(username) < 3:
            errors.append('ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร')
        elif User.objects.filter(username=username).exists():
            errors.append('ชื่อผู้ใช้นี้มีผู้ใช้แล้ว')
        
        if not password:
            errors.append('กรุณากรอกรหัสผ่าน')
        elif len(password) < 6:
            errors.append('รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร')
        
        if password != password_confirm:
            errors.append('รหัสผ่านไม่ตรงกัน')
        
        if errors:
            return render(request, 'register.html', {'errors': errors, 'username': username})
        
        # Create user
        user = User.objects.create_user(username=username, password=password)
        # Create player profile
        Player.objects.create(user=user, name=username)
        
        # Log in the user
        login(request, user)
        return redirect('topup_games')
    
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('index')    

@login_required(login_url='index')
def topup_games(request):
    games = Game.objects.all()  # ดึงข้อมูลเกมทั้งหมดจากฐานข้อมูล
    username = request.user.username  # ดึงชื่อผู้ใช้ที่ล็อกอิน

    # ดึงพ้อยต์ของผู้ใช้จาก Player
    try:
        player = Player.objects.get(user=request.user)
        user_points = player.points
    except Player.DoesNotExist:
        user_points = 0  # หากไม่มี Player ให้ตั้งค่าเริ่มต้นเป็น 0

    return render(request, 'topup_games.html', {
        'games': games,
        'username': username,
        'user_points': user_points,
    })

@login_required(login_url='index')
def topup_form(request, game_id):
    try:
        game = Game.objects.get(id=game_id)  # ดึงข้อมูลเกมจากฐานข้อมูล
    except Game.DoesNotExist:
        return render(request, 'error.html', {'message': 'ไม่พบเกม'})

    amounts = [10, 50, 100, 500, 1000]  # ตัวเลือกแพ็กเกจการเติมเงิน
    return render(request, 'topup_form.html', {
        'game_id': game.id,
        'game_name': game.name,
        'amounts': amounts
    })

def generate_qr_code(data):
    """สร้าง QR code และส่งกลับเป็น base64 string"""
    try:
        # import qrcode lazily so management commands (makemigrations) won't fail if
        # the qrcode library isn't installed in the dev environment.
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # แปลงเป็น base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

@login_required(login_url='index')
def topup_process(request, game_id):
    """ประมวลผลการเติมเงิน"""
    if request.method == 'POST':
        user = request.POST.get('user', '').strip()
        amount = request.POST.get('amount', '')
        
        errors = []
        if not user:
            errors.append('กรอกชื่อผู้เล่น/ยูสเซอร์ด้วย')
        if not amount:
            errors.append('เลือกจำนวนเงินด้วย')
        
        try:
            amount_val = int(amount)
            if amount_val <= 0:
                errors.append('จำนวนเงินไม่ถูกต้อง')
        except Exception:
            errors.append('จำนวนเงินไม่ถูกต้อง')
        
        if errors:
            amounts = [10, 50, 100, 500, 1000]
            return render(request, 'topup_form.html', {
                'game_id': game_id,
                'game_name': request.POST.get('game_name'),
                'amounts': amounts,
                'errors': errors,
                'form': {'user': user, 'amount': amount}
            })
        
        # สร้าง transaction ID จำลอง
        tx_id = str(uuid.uuid4())[:8]
        # ถ้ามีการส่งค่าใช้พ้อยต์มา ให้ตรวจสอบกับบัญชีผู้เล่น (ยังไม่ตัดพ้อยต์จริงๆ จนกว่าจะยืนยัน)
        use_points_req = 0
        try:
            use_points_req = int(request.POST.get('use_points', '0') or 0)
            if use_points_req < 0:
                use_points_req = 0
        except Exception:
            use_points_req = 0

        # ดึงพ้อยต์จากบัญชี login user ไม่ใช่จากชื่อที่ป้อนในฟอร์ม
        logged_in_user = request.user
        player = None
        available_points = 0
        if logged_in_user and logged_in_user.is_authenticated:
            player = getattr(logged_in_user, 'player_profile', None)
            if player is None:
                # Try to find by username and link
                player = Player.objects.filter(name=logged_in_user.username).first()
                if player:
                    player.user = logged_in_user
                    player.save()
                else:
                    # Create a fresh Player for this user
                    player = Player.objects.create(user=logged_in_user, name=logged_in_user.username)
            available_points = player.points if player else 0

        # กำหนดจำนวนพ้อยต์ที่สามารถใช้จริง ๆ ได้ (ไม่เกินที่ผู้เล่นมี และไม่เกินจำนวนเงิน)
        try:
            amount_val = int(amount)
        except Exception:
            amount_val = 0

        used_points = min(available_points, use_points_req, amount_val)
        payable_amount = max(0, amount_val - used_points)

        # สร้าง QR code ที่เก็บข้อมูลการเติมเงิน (จำนวนที่ต้องจ่ายคือ payable_amount)
        qr_data = f"TOPUP|{tx_id}|{user}|{request.POST.get('game_name')}|{payable_amount}|THB"
        qr_code_base64 = generate_qr_code(qr_data)

        # แสดงหน้า QR code พร้อมส่งข้อมูลไป (ยังไม่ตัดพ้อยต์จริงจนกว่าจะยืนยัน)
        return render(request, 'topup_qrcode.html', {
            'user': user,
            'game_name': request.POST.get('game_name'),
            'amount': payable_amount,
            'original_amount': amount_val,
            'used_points': used_points,
            'available_points': available_points,
            'game_id': game_id,
            'tx_id': tx_id,
            'qr_code': qr_code_base64,
        })
    
    return render(request, 'error.html', {'message': 'Invalid request'})

@login_required(login_url='index')
def topup_confirm(request, game_id):
    """ยืนยันการชำระเงินและแสดงหน้าสำเร็จ"""
    # ดึงข้อมูลจาก URL parameters หรือ query string
    user = request.GET.get('user', '').strip()
    game_name = request.GET.get('game_name', '')
    amount = request.GET.get('amount', '')
    tx_id = request.GET.get('tx_id', '')
    used_points_param = request.GET.get('used_points', '0')
    
    if not all([user, game_name, amount, tx_id]):
        return render(request, 'error.html', {'message': 'ข้อมูลการเติมเงินไม่ครบ'})
    
    # สร้าง QR code ใหม่สำหรับแสดงในหน้าสำเร็จ
    qr_data = f"TOPUP|{tx_id}|{user}|{game_name}|{amount}|THB"
    qr_code_base64 = generate_qr_code(qr_data)

    # ปรับยอดพ้อยต์ของผู้เล่น: หักพ้อยต์ที่ใช้ (ถ้ามี) แล้วบวกพ้อยต์จากการเติมเงิน
    player_points_after = None
    bonus_points = 0
    logged_in_user = request.user
    if logged_in_user and logged_in_user.is_authenticated:
        try:
            # Get or create player for logged-in user
            player = getattr(logged_in_user, 'player_profile', None)
            if player is None:
                # Try to find by username and link
                player = Player.objects.filter(name=logged_in_user.username).first()
                if player:
                    player.user = logged_in_user
                    player.save()
                else:
                    # Create a fresh Player for this user
                    player = Player.objects.create(user=logged_in_user, name=logged_in_user.username)
            
            # หักพ้อยต์ที่ส่งมาจากหน้าก่อน (ใช้จริงสูงสุดเท่าที่มี)
            try:
                used_points = int(used_points_param or 0)
            except Exception:
                used_points = 0

            deducted = player.use_points(used_points) if used_points > 0 else 0

            # คำนวณพอยต์ใหม่: 100 บาท = 1 พอยต์
            try:
                paid_amount = int(amount)
            except Exception:
                paid_amount = 0

            if paid_amount > 0:
                # ให้พอยต์ใหม่ตามยอดที่จ่ายจริง (100 บาท = 1 พอยต์)
                bonus_points = paid_amount // 100
                if bonus_points > 0:
                    player.add_points(bonus_points)

            player_points_after = player.points
        except Exception as e:
            print(f"Error updating player points: {e}")

    return render(request, 'topup_success.html', {
        'tx_id': tx_id,
        'user': user,
        'game_name': game_name,
        'amount': amount,
        'game_id': game_id,
        'qr_code': qr_code_base64,
        'used_points': used_points_param,
        'bonus_points': bonus_points,
        'player_points': player_points_after,
    })

@login_required(login_url='index')
def get_user_points(request):
    """API endpoint to get current user's points"""
    user = request.user
    try:
        player = getattr(user, 'player_profile', None)
        if player:
            points = player.points
        else:
            # Try to find by username and link
            player = Player.objects.filter(name=user.username).first()
            if player:
                player.user = user
                player.save()
                points = player.points
            else:
                # Create a fresh Player for this user
                player = Player.objects.create(user=user, name=user.username)
                points = 0
        return JsonResponse({
            'success': True,
            'points': points,
            'username': user.username
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required(login_url='index')
def add_game(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '').strip()
        url = request.POST.get('url', '').strip()

        # ตรวจสอบว่ากรอกข้อมูลครบถ้วนหรือไม่
        if not name or not url:
            messages.error(request, 'กรุณากรอกข้อมูลให้ครบถ้วน')
            return render(request, 'add_game.html')

        # บันทึกเกมใหม่ลงในฐานข้อมูล
        Game.objects.create(name=name, icon=icon or '🎮', url=url)
        messages.success(request, f'เพิ่มเกม "{name}" สำเร็จ!')
        return redirect('topup_games')

    return render(request, 'add_game.html')

@login_required(login_url='index')
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.method == 'POST':
        game.name = request.POST.get('name', game.name)
        game.icon = request.POST.get('icon', game.icon)
        game.url = request.POST.get('url', game.url)
        game.save()
        messages.success(request, f'แก้ไขเกม "{game.name}" สำเร็จ!')
        return redirect('topup_games')

    return render(request, 'edit_game.html', {'game': game})

@login_required(login_url='index')
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        game_name = game.name
        game.delete()
        messages.success(request, f'ลบเกม "{game_name}" สำเร็จ!')
        return redirect('topup_games')

    return render(request, 'confirm_delete.html', {'game': game})
