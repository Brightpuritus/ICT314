from django.shortcuts import render
from .models import Player
import uuid
from io import BytesIO
import base64

def index(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'register.html')    

def topup_games(request):
    """หน้าแรกของเติมเกม - เลือกเกม"""
    games = [
        {'id': 'pubg', 'name': 'PUBG Mobile', 'icon': '🎮', 'color': '#FF6B6B'},
        {'id': 'rov', 'name': 'RoV (Realm of Valor)', 'icon': '⚔️', 'color': '#4ECDC4'},
        {'id': 'freefire', 'name': 'Free Fire', 'icon': '🔥', 'color': '#FFE66D'},
        {'id': 'genshin', 'name': 'Genshin Impact', 'icon': '✨', 'color': '#95E1D3'},
    ]
    return render(request, 'topup_games.html', {'games': games})

def topup_form(request, game_id):
    """หน้าฟอร์มเติมเงิน"""
    games_dict = {
        'pubg': 'PUBG Mobile',
        'rov': 'RoV (Realm of Valor)',
        'freefire': 'Free Fire',
        'genshin': 'Genshin Impact',
    }
    
    game_name = games_dict.get(game_id)
    if not game_name:
        return render(request, 'error.html', {'message': 'ไม่พบเกม'})
    
    amounts = [10, 50, 100, 500, 1000]
    return render(request, 'topup_form.html', {
        'game_id': game_id,
        'game_name': game_name,
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

        # หา player (สร้างถ้ายังไม่มี) เพื่อดูพ้อยต์ที่มี
        player = None
        if user:
            player, _ = Player.objects.get_or_create(name=user)
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
    if user:
        player, _ = Player.objects.get_or_create(name=user)
        # หักพ้อยต์ที่ส่งมาจากหน้าก่อน (ใช้จริงสูงสุดเท่าที่มี)
        try:
            used_points = int(used_points_param or 0)
        except Exception:
            used_points = 0

        deducted = player.use_points(used_points) if used_points > 0 else 0

        # ให้พ้อยต์ใหม่ตามยอดที่จ่ายจริง (สมมติ 1 THB = 1 point)
        try:
            paid_amount = int(amount)
        except Exception:
            paid_amount = 0

        if paid_amount > 0:
            player.add_points(paid_amount)

        player_points_after = player.points

    return render(request, 'topup_success.html', {
        'tx_id': tx_id,
        'user': user,
        'game_name': game_name,
        'amount': amount,
        'game_id': game_id,
        'qr_code': qr_code_base64,
        'used_points': used_points_param,
        'player_points': player_points_after,
    })
