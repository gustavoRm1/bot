#!/usr/bin/env python3
"""
Sistema de Comunicação entre Bot e Dashboard
Arquivo compartilhado para sincronização de dados
"""

import json
import os
import time
from datetime import datetime
from threading import Lock

# Lock para thread safety
data_lock = Lock()

# Arquivo de dados compartilhado
DATA_FILE = "bot_dashboard_data.json"

# Dados padrão
default_data = {
    "stats": {
        "total_users": 0,
        "total_payments": 0,
        "pending_payments": 0,
        "confirmed_payments": 0,
        "total_downsells_sent": 0,
        "downsell_conversions": 0
    },
    "unique_users": {},
    "recent_events": [],
    "bot_status": "offline",
    "last_update": datetime.now().isoformat(),
    "downsell_config": {
        "enabled": True,
        "downsells": [
            {
                "id": "downsell_extremo_001",
                "text": "👁️‍🗨️ Os conteúdos mais extremos da comunidade estão aqui.\nE você ainda tá de fora por menos de R$16…\n\n🚫 Fl@gr@s que nunca deviam vazar.\n🎥 Câmeras escondidas no ato.\n📂 Nudes deletados e recuperados.\n\n👉 Ou você entra agora, ou continua só imaginando o que os outros já estão vendo.",
                "sendTime": 5,
                "discount": 5,
                "mediaFile": "https://t.me/MIDIASBOTIS/3",
                "audioFile": "",
                "recipients": "all",
                "content_type": "video",
                "paymentButtons": [
                    {
                        "text": "❌🤫𝐕𝐈𝐓𝐀𝐋𝐈𝐂𝐈𝐎(5% 𝐨𝐟𝐟)🤫❌ 𝐩𝐨𝐫 𝟏𝟖,𝟗𝟕",
                        "price": 18.97,
                        "description": "Acesso vitalício com 5% de desconto",
                        "orderBump": {
                            "enabled": True,
                            "title": "SALA VERMELHA",
                            "price": 12.90,
                            "message": "📦 DESBLOQUEAR SALA VERMELHA 📦\n\n🚷 Arquivos deletados do servidor principal e salvos só pra essa liberação.\n✅ Amador das faveladas\n✅ Amador com o pai depois do banho ⭐️🤫\n✅ Vídeos que muitos procuram várias países.\n✅ Conteúdo de cameras com áudio original.\n💥 Ative agora e leva 1 grupo s3cr3to bônus.",
                            "acceptButton": "✅ Aceitar Oportunidade",
                            "declineButton": "❌ Não Quero Bônus"
                        }
                    },
                    {
                        "text": "❌🤫𝟭 𝗺ê𝘀(5% 𝐨𝐟𝐟) 🤫❌ 𝐩𝐨𝐫 𝟏𝟒,𝟐𝟐",
                        "price": 14.22,
                        "description": "Acesso mensal com 5% de desconto",
                        "orderBump": {
                            "enabled": True,
                            "title": "PACOTE SOMBRIO",
                            "price": 12.90,
                            "message": "📦 DESBLOQUEAR PACOTE SOMBRIO 📦\n\n🚷 Arquivos esquecidos e salvos só pra essa liberação.\n✅ Amador das faveladas\n✅ Amador com o pai depois do banho ⭐️🤫\n✅ Vídeos que já foi esquecidos em vários países.\n✅ Conteúdo de cameras com áudio original.\n💥 Ative agora e leva 1 grupo s3cr3to bônus.",
                            "acceptButton": "✅ Aceitar Oportunidade",
                            "declineButton": "❌ Não Quero Bônus"
                        }
                    }
                ]
            }
        ],
        "active_timers": {}
    },
    "user_sessions": {},
    "pending_payments": {},
    "settings": {
        "messages": {
            "start_message": """🚷 𝗩𝗢𝗖Ê 𝗔𝗖𝗔𝗕𝗢𝗨 𝗗𝗘 𝗘𝗡𝗧𝗥𝗔𝗥 𝗡𝗢 𝗔𝗕𝗜𝗦𝗠𝗢 — 𝗘 𝗔𝗤𝗨𝗜 𝗡Ã𝗢 𝗘𝗫𝗜𝗦𝗧𝗘 𝗩𝗢𝗟𝗧𝗔. 

💎 O maior e mais pr🔞curad🔞 Rateio de Grupos VIPs do Telegram está aberto… mas não por muito tempo. 

🔞 OnlyF4ns, Privacy, Close Friends VAZADOS 🔞 Famosas, Nov!nhas +18, Amadoras & Milf's insaciáveis 🔞 L!ves completas, conteúdos escondidos e traições reais gravadas. 

🎭 Casais abertos | 🎥 V!d3os de surub4s | 😈 Segredos de inc3sto | 🚨 Fet!ches 🔞cultos do c0rno moderno. 

🔥 𝗔𝘁𝘂𝗮𝗹𝗶𝘇𝗮çõ𝗲𝘀 𝗗𝗶á𝗿𝗶𝗮𝘀 — 𝗡𝗮𝗱𝗮 𝗳𝗶𝗰𝗮 𝘃𝗲𝗹𝗵𝗼. 
🔒 𝗖𝗼𝗺𝗽𝗿𝗮 𝟭𝟬𝟬% 𝗦𝗲𝗴𝘂𝗿𝗮 — 𝗡𝗶𝗻𝗴𝘂é𝗺 𝗱𝗲𝘀𝗰𝗼𝗯𝗿𝗲. 
⚡️ 𝗔𝗰𝗲𝘀𝘀𝗼 𝗜𝗺𝗲𝗱𝗶𝗮𝘁𝗼 — 𝗘𝗺 𝗺𝗲𝗻𝗼𝘀 𝗱𝗲 𝟭 𝗺𝗶𝗻𝘂𝘁𝗼 𝘃𝗼𝗰ê 𝗷á 𝗲𝘀𝘁á 𝗱𝗲𝗻𝘁𝗿𝗼. 

❌ Aqui não tem "achismos": são os vídeos que NINGUÉM teria coragem de postar publicamente. 
👉 Se você sair agora, nunca mais encontra esse conteúdo. 

🎁 𝗕ô𝗻𝘂𝘀 𝗦ó 𝗛𝗼𝗷𝗲: 𝗮𝗼 𝗮𝘀𝘀𝗶𝗻𝗮𝗿, 𝘃𝗼𝗰ê 𝗿𝗲𝗰𝗲𝗯𝗲 𝗮𝗰𝗲𝘀𝘀𝗼 𝘀𝗲𝗰𝗿𝗲𝘁𝗼 𝗮 +𝟰 𝗚𝗿𝘂𝗽𝗼𝘀 𝗩𝗜𝗣'𝘀 𝗼𝗰𝘂𝗹𝘁𝗼𝘀 (𝗻𝗼𝘃!𝗻𝗵𝟰𝘀 +𝟭𝟴, 𝗰𝗮𝘀𝗮𝗱𝗮𝘀 𝗿𝗲𝗮𝗶𝘀, 𝗳𝗹@𝗴𝗿@𝘀 & 𝗺í𝗱𝗶𝗮𝘀 𝗲𝘅𝗰𝗹𝘂í𝗱𝗮𝘀 𝗱𝗮 𝘄𝟯𝗯).""",
            "order_bump_vitalicio": """📦 DESBLOQUEAR SALA VERMELHA 📦

🚷 Arquivos deletados do servidor principal e salvos só pra essa liberação. 

✅ Amador das faveladas 
✅ Amador com o pai depois do banho ⭐️🤫 
✅ Vídeos que muitos procuram várias países. 
✅ Conteúdo de cameras com áudio original. 

💥 Ative agora e leva 1 grupo s3cr3to bônus.""",
            "order_bump_mensal": """📦 DESBLOQUEAR PACOTE SOMBRIO 📦

🚷 Arquivos esquecidos e salvos só pra essa liberação. 

✅ Amador das faveladas 
✅ Amador com o pai depois do banho ⭐️🤫 
✅ Vídeos que já foi esquecidos em vários países. 
✅ Conteúdo de cameras com áudio original. 

💥 Ative agora e leva 1 grupo s3cr3to bônus."""
        },
        "buttons": {
            "vitalicio_text": "❌🤫𝐕𝐈𝐓𝐀𝐋𝐈𝐂𝐈𝐎(𝐏𝐑𝐎𝐌𝐎)🤫❌ 𝐩𝐨𝐫 𝟏𝟗.𝟗𝟕",
            "mensal_text": "❌🤫𝟭 𝗺ê𝘀 🤫❌ 𝐩𝐨𝐫 𝟏𝟒.𝟗𝟕",
            "aceitar_bonus": "✅ Aceitar Oportunidade",
            "nao_quero_bonus": "❌ Não Quero Bônus"
        },
        "prices": {
            "vitalicio": 19.97,
            "mensal": 14.97,
            "vitalicio_bonus": 32.87,
            "mensal_bonus": 27.87
        }
    }
}

def load_data():
    """Carregar dados do arquivo"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Garantir que todas as estruturas necessárias existam
                if 'downsell_config' not in data:
                    data['downsell_config'] = default_data['downsell_config'].copy()
                if 'user_sessions' not in data:
                    data['user_sessions'] = default_data['user_sessions'].copy()
                if 'unique_users' not in data:
                    data['unique_users'] = default_data['unique_users'].copy()
                if 'total_downsells_sent' not in data['stats']:
                    data['stats']['total_downsells_sent'] = 0
                if 'downsell_conversions' not in data['stats']:
                    data['stats']['downsell_conversions'] = 0
                return data
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
    
    return default_data.copy()

def save_data(data):
    """Salvar dados no arquivo"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")

def add_unique_user(user_id, user_name=None, username=None):
    """Adiciona um usuário único se não existir"""
    with data_lock:
        data = load_data()
        user_key = str(user_id)
        
        # Verificar se o usuário já existe
        if user_key not in data["unique_users"]:
            # Adicionar usuário único
            data["unique_users"][user_key] = {
                "user_id": user_id,
                "user_name": user_name,
                "username": username,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
            
            # Incrementar contador de usuários únicos
            data["stats"]["total_users"] += 1
            
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
            return True  # Usuário novo
        else:
            # Atualizar última vez visto
            data["unique_users"][user_key]["last_seen"] = datetime.now().isoformat()
            if user_name:
                data["unique_users"][user_key]["user_name"] = user_name
            if username:
                data["unique_users"][user_key]["username"] = username
            
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
            return False  # Usuário existente

def update_stats(stat_name, increment=1):
    """Atualizar estatísticas"""
    with data_lock:
        data = load_data()
        if stat_name in data["stats"]:
            data["stats"][stat_name] += increment
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def add_event(level, message, user_id=None):
    """Adicionar evento aos logs"""
    with data_lock:
        data = load_data()
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "user_id": user_id
        }
        
        data["recent_events"].append(event)
        
        # Manter apenas os últimos 100 eventos
        if len(data["recent_events"]) > 100:
            data["recent_events"] = data["recent_events"][-100:]
        
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def set_bot_status(status):
    """Definir status do bot"""
    with data_lock:
        data = load_data()
        data["bot_status"] = status
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def get_data():
    """Obter todos os dados"""
    with data_lock:
        return load_data()

def update_setting(section, key, value):
    """Atualizar configuração"""
    with data_lock:
        data = load_data()
        if section in data["settings"] and key in data["settings"][section]:
            data["settings"][section][key] = value
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
            return True
        return False

def get_settings():
    """Obter configurações"""
    with data_lock:
        data = load_data()
        return data["settings"]

# ===== FUNÇÕES ESPECÍFICAS PARA DOWSELL =====

def add_downsell(downsell_data):
    """Adiciona um downsell à configuração"""
    with data_lock:
        data = load_data()
        data["downsell_config"]["downsells"].append(downsell_data)
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def update_downsell(index, downsell_data):
    """Atualiza um downsell específico"""
    with data_lock:
        data = load_data()
        if 0 <= index < len(data["downsell_config"]["downsells"]):
            data["downsell_config"]["downsells"][index] = downsell_data
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
            return True
        return False

def remove_downsell(index):
    """Remove um downsell específico"""
    with data_lock:
        data = load_data()
        if 0 <= index < len(data["downsell_config"]["downsells"]):
            data["downsell_config"]["downsells"].pop(index)
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
            return True
        return False

def set_downsell_enabled(enabled):
    """Ativa/desativa sistema de downsell"""
    with data_lock:
        data = load_data()
        data["downsell_config"]["enabled"] = enabled
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def add_user_session(user_id):
    """Adiciona sessão de usuário para downsell"""
    with data_lock:
        data = load_data()
        data["user_sessions"][str(user_id)] = {
            "start_time": datetime.now().timestamp(),
            "purchased": False,
            "downsell_sent": [],
            "current_downsell": 0
        }
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def update_user_session(user_id, **kwargs):
    """Atualiza sessão de usuário"""
    with data_lock:
        data = load_data()
        if str(user_id) in data["user_sessions"]:
            data["user_sessions"][str(user_id)].update(kwargs)
            data["last_update"] = datetime.now().isoformat()
            save_data(data)

def get_user_session(user_id):
    """Retorna sessão de usuário"""
    with data_lock:
        data = load_data()
        return data["user_sessions"].get(str(user_id))

def remove_user_session(user_id):
    """Remove sessão de usuário"""
    with data_lock:
        data = load_data()
        if str(user_id) in data["user_sessions"]:
            del data["user_sessions"][str(user_id)]
            data["last_update"] = datetime.now().isoformat()
            save_data(data)

def add_timer(user_id, downsell_index, delay_seconds):
    """Adiciona timer para downsell"""
    with data_lock:
        data = load_data()
        timer_key = f"{user_id}_{downsell_index}"
        
        # Usar timestamp correto (forçar timestamp atual)
        current_time = datetime.now().timestamp()
        
        data["downsell_config"]["active_timers"][timer_key] = {
            "user_id": user_id,
            "downsell_index": downsell_index,
            "expires_at": current_time + delay_seconds,
            "created_at": current_time
        }
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def remove_timer(user_id, downsell_index):
    """Remove timer específico"""
    with data_lock:
        data = load_data()
        timer_key = f"{user_id}_{downsell_index}"
        if timer_key in data["downsell_config"]["active_timers"]:
            del data["downsell_config"]["active_timers"][timer_key]
            data["last_update"] = datetime.now().isoformat()
            save_data(data)

def get_expired_timers():
    """Retorna timers expirados"""
    with data_lock:
        data = load_data()
        current_time = datetime.now().timestamp()
        expired = []
        timers = data["downsell_config"]["active_timers"]
        
        for timer_key, timer_data in list(timers.items()):
            if timer_data["expires_at"] <= current_time:
                expired.append(timer_data)
                del timers[timer_key]
        
        if expired:
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
        
        return expired

def clear_all_timers():
    """Limpa todos os timers"""
    with data_lock:
        data = load_data()
        data["downsell_config"]["active_timers"].clear()
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def get_downsell_config():
    """Retorna configuração completa do downsell"""
    with data_lock:
        data = load_data()
        return data["downsell_config"]

def get_all_scheduled_downsells():
    """Retorna todos os downsells agendados ativos"""
    with data_lock:
        data = load_data()
        scheduled = []
        
        # Obter todos os timers ativos
        timers = data["downsell_config"]["active_timers"]
        downsells = data["downsell_config"]["downsells"]
        
        for timer_key, timer_data in timers.items():
            user_id = timer_data["user_id"]
            downsell_index = timer_data["downsell_index"]
            
            # Verificar se usuário ainda existe e não comprou
            user_session = data["user_sessions"].get(str(user_id))
            if not user_session or user_session.get('purchased', False):
                continue
            
            # Verificar se já enviou este downsell
            downsells_sent = user_session.get('downsell_sent', [])
            if downsell_index in downsells_sent:
                continue
            
            # Obter configuração do downsell
            if downsell_index < len(downsells):
                downsell = downsells[downsell_index]
                scheduled.append({
                    "id": timer_key,
                    "user_id": user_id,
                    "downsell_index": downsell_index,
                    "downsell": downsell,
                    "next_run": timer_data["expires_at"],
                    "created_at": timer_data["created_at"]
                })
        
        return scheduled

def update_downsell_schedule(timer_key):
    """Atualiza o agendamento de um downsell (remove após envio)"""
    with data_lock:
        data = load_data()
        timers = data["downsell_config"]["active_timers"]
        
        if timer_key in timers:
            del timers[timer_key]
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
            return True
        return False

def increment_downsell_stats(stat_name):
    """Incrementa estatísticas de downsell"""
    with data_lock:
        data = load_data()
        if stat_name in data["stats"]:
            data["stats"][stat_name] += 1
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

# Funções para gerenciar pagamentos pendentes
def generate_user_email(user_id):
    """Gera um email único para o usuário"""
    import random
    import string
    
    # Gerar string aleatória de 8 caracteres
    random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{random_chars}@email.com"

def add_pending_payment(user_id, payment_data):
    """Adiciona um pagamento pendente"""
    with data_lock:
        data = load_data()
        
        # Gerar email único para o usuário
        payment_data['generated_email'] = generate_user_email(user_id)
        
        data["pending_payments"][str(user_id)] = payment_data
        data["stats"]["pending_payments"] = len(data["pending_payments"])
        data["last_update"] = datetime.now().isoformat()
        save_data(data)

def get_pending_payments():
    """Retorna todos os pagamentos pendentes"""
    with data_lock:
        data = load_data()
        return data["pending_payments"]

def remove_pending_payment(user_id):
    """Remove um pagamento pendente"""
    with data_lock:
        data = load_data()
        if str(user_id) in data["pending_payments"]:
            del data["pending_payments"][str(user_id)]
            data["stats"]["pending_payments"] = len(data["pending_payments"])
            data["last_update"] = datetime.now().isoformat()
            save_data(data)

def update_payment_status(user_id, status):
    """Atualiza o status de um pagamento"""
    with data_lock:
        data = load_data()
        if str(user_id) in data["pending_payments"]:
            data["pending_payments"][str(user_id)]["status"] = status
            data["pending_payments"][str(user_id)]["updated_at"] = datetime.now().isoformat()
            
            # Se regenerando email, gerar novo
            if status == 'pending' and 'regenerate_email' in data["pending_payments"][str(user_id)]:
                data["pending_payments"][str(user_id)]["generated_email"] = generate_user_email(user_id)
                del data["pending_payments"][str(user_id)]["regenerate_email"]
            
            data["last_update"] = datetime.now().isoformat()
            save_data(data)
