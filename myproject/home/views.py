from django.shortcuts import render
import uuid

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
        
        return render(request, 'topup_success.html', {
            'tx_id': tx_id,
            'user': user,
            'game_name': request.POST.get('game_name'),
            'amount': amount,
            'game_id': game_id
        })
    
    return render(request, 'error.html', {'message': 'Invalid request'})
