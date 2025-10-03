#!/usr/bin/env python3
"""
Bot do Telegram - Sistema Multi-Bot para Alto Tráfego
"""

import logging
import os
import time
import requests
import uuid
import asyncio
import json
import threading
from datetime import datetime
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from shared_data import (
    add_event, update_stats, set_bot_status, get_settings,
    add_user_session, update_user_session, get_user_session, remove_user_session,
    add_timer, remove_timer, get_expired_timers, get_downsell_config,
    increment_downsell_stats, add_unique_user, get_all_scheduled_downsells,
    update_downsell_schedule
)
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Dict, List, Tuple, Optional

# Configuração de logging otimizada para produção
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING,  # Apenas WARNING e ERROR em produção
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Logger separado para eventos importantes
event_logger = logging.getLogger('events')
event_logger.setLevel(logging.INFO)
event_handler = logging.FileHandler('events.log', encoding='utf-8')
event_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
event_logger.addHandler(event_handler)

# Configuração de tokens múltiplos
BOT_TOKENS = [
    '8306671959:AAHeqNjcC9C3MpAVrCXRyer62vOyfLm_0MM',  # Token 1
    '7562715822:AAEPe1Men2JZHLWl5hjtoHtFO7FN6tHnxyM',  # Token 2
    '8465360609:AAGQuceE1GceIDZftS0MuVVmTYT1ifoe3hY',  # Token 3
    '8225954437:AAFtdhf4_4r2EH3ydStFwRvhN1b4MVKxLgQ',  # Token 4
    '8376203049:AAHBw3rMvolNSuIfZ-Si1CRifyRyf6z6lCY',  # Token 5
    '8372884477:AAFl8GwuVNxWXXEumjwMbm63_l_DfdvvwqM',  # Token 6
    '8426700153:AAF3NtPQZaPelVRdos1h1QkhIvGRbeDi-jQ',  # Token 7
    '7344610657:AAH3_JTdnZH_0CkNxfhb0hAIptlfRseSaK8',  # Token 8
    '8300351452:AAEsDLhXi4Cf5WVqnQS2-7ZkjBExbn5Z17U',  # Token 9
    '8297063257:AAFFE3K8I6yycwZQ-fAGO6di0yr4n5jGh_w',  # Token 10
    '8443691990:AAFjgMtr38_rHw6HZlnIvf3cCKTpb7m4R7Q',  # Token 11
    '8339224972:AAEzCqgfTmPT3l6k2R9_-7L0En3c-bgOST0',  # Token 12
    '8316837637:AAFgDiXo4HvU9RVJJrcwlkAz8kHj2xlbSok',  # Token 13
    '8049999245:AAGHiasvg4X25RKQgdqsxLfaBjwiQI599oE',  # Token 14
    '8454123391:AAHfSpgEFB_9UXm66NuUmHhGGRE_TkuxiGk',  # Token 15
    '8383266949:AAEOs62d9yI1kgZ9tP6BsGTHGh4yLgcc_LI',  # Token 16
    '8382560938:AAE4dlx7fz4VfYDZrNWqLjWn4T7hG9XTN5g',  # Token 17
]

# Configuração de links por bot (OPÇÃO 1)
BOT_LINKS = {
    '8306671959:AAHeqNjcC9C3MpAVrCXRyer62vOyfLm_0MM': 'https://oacessoliberado.shop/vip2',  # Link padrão original
    '7562715822:AAEPe1Men2JZHLWl5hjtoHtFO7FN6tHnxyM': 'https://oacessoliberado.shop/vip2',  # Link padrão original
    '8465360609:AAGQuceE1GceIDZftS0MuVVmTYT1ifoe3hY': 'https://seusacessos.shop/acessoliberado',
    '8225954437:AAFtdhf4_4r2EH3ydStFwRvhN1b4MVKxLgQ': 'https://seusacessos.shop/acessoliberado',
    '8376203049:AAHBw3rMvolNSuIfZ-Si1CRifyRyf6z6lCY': 'https://seusacessos.shop/acessoliberado',
    '8372884477:AAFl8GwuVNxWXXEumjwMbm63_l_DfdvvwqM': 'https://seusacessos.shop/acessoliberado',
    '8426700153:AAF3NtPQZaPelVRdos1h1QkhIvGRbeDi-jQ': 'https://seusacessos.shop/acessoumosso',
    '7344610657:AAH3_JTdnZH_0CkNxfhb0hAIptlfRseSaK8': 'https://seusacessos.shop/acessoumosso',
    '8300351452:AAEsDLhXi4Cf5WVqnQS2-7ZkjBExbn5Z17U': 'https://seusacessos.shop/acessoumosso',
    '8297063257:AAFFE3K8I6yycwZQ-fAGO6di0yr4n5jGh_w': 'https://seusacessos.shop/acessoliberadinho',
    '8443691990:AAFjgMtr38_rHw6HZlnIvf3cCKTpb7m4R7Q': 'https://seusacessos.shop/acessoliberadinho',
    '8339224972:AAEzCqgfTmPT3l6k2R9_-7L0En3c-bgOST0': 'https://seusacessos.shop/acessoliberadinho',
    '8316837637:AAFgDiXo4HvU9RVJJrcwlkAz8kHj2xlbSok': 'https://seusacessos.shop/acessoliberadinho',
    '8049999245:AAGHiasvg4X25RKQgdqsxLfaBjwiQI599oE': 'https://seusacessos.shop/acessoliberado2',
    '8454123391:AAHfSpgEFB_9UXm66NuUmHhGGRE_TkuxiGk': 'https://seusacessos.shop/acessoliberado2',
    '8383266949:AAEOs62d9yI1kgZ9tP6BsGTHGh4yLgcc_LI': 'https://seusacessos.shop/acessoliberado2',  # Token 16
    '8382560938:AAE4dlx7fz4VfYDZrNWqLjWn4T7hG9XTN5g': 'https://seusacessos.shop/acessoliberado2',  # Token 17
}

# Configurações PushynPay (URLs CORRETAS)
PUSHYNPAY_TOKEN = '48868|59JBZdNBBZRHY1dI0sxmXvcj8LXWcJnV3oeRj8Vhefd226e7'
PUSHYNPAY_BASE_URL_SANDBOX = 'https://api-sandbox.pushinpay.com.br'
PUSHYNPAY_BASE_URL_PRODUCTION = 'https://api.pushinpay.com.br'

# Endpoints PushynPay corretos
PUSHYNPAY_ENDPOINTS = [
    f"{PUSHYNPAY_BASE_URL_SANDBOX}/api/pix/cashIn",
    f"{PUSHYNPAY_BASE_URL_PRODUCTION}/api/pix/cashIn"
]

# Configurações SyncPay Original (mantido como backup)
SYNCPAY_CLIENT_ID = '54f3518a-1e5f-4f08-8c68-5a79df3bddf9'
SYNCPAY_CLIENT_SECRET = 'f49f4e62-d0c6-4c17-a8ac-e036a0fc69a2'
SYNCPAY_BASE_URL = 'https://api.syncpayments.com.br'

# Sistema de múltiplos gateways
GATEWAYS = {
    'syncpay_original': {
        'name': 'SyncPay Original',
        'base_url': SYNCPAY_BASE_URL,
        'client_id': SYNCPAY_CLIENT_ID,
        'client_secret': SYNCPAY_CLIENT_SECRET,
        'active': True,
        'priority': 1,
        'max_amount': 10000.00,
        'min_amount': 1.00
    },
    'pushynpay': {
        'name': 'PushynPay',
        'base_url': PUSHYNPAY_BASE_URL_SANDBOX,  # Usar sandbox para testes
        'token': PUSHYNPAY_TOKEN,
        'active': True,  # ATIVADO - URLs corretas
        'priority': 1,  # Prioridade alta
        'max_amount': 10000.00,
        'min_amount': 0.50,  # Valor mínimo R$ 0,50 (50 centavos)
        'endpoints': PUSHYNPAY_ENDPOINTS
    }
}

# Controle de rate limiting inteligente para vendas
user_requests = {}  # {user_id: {'last_request': timestamp, 'pending_request': bool, 'last_action': 'start'|'button'|'message'}}
RESPONSE_COOLDOWN = 5  # 5 segundos de cooldown após responder

# Armazenamento de pagamentos pendentes
pending_payments = {}  # {user_id: {'payment_id': str, 'amount': float, 'plan': str}}

# Sistema multi-bot com controle de shutdown
active_bots = {}  # {token: {'application': app, 'bot': bot, 'status': 'active'|'failed'}}
bot_rotation_index = 0
shutdown_requested = False

# Sistema de gateways com failover
gateway_status = {}  # {gateway_id: {'status': 'active'|'failed', 'last_error': str, 'error_count': int}}
gateway_rotation_index = 0

# Sistema de comandos administrativos
ADMIN_USER_ID = 7676333385  # Seu ID do Telegram
ADMIN_COMMANDS = {
    '/admin': 'admin',
    '/gw': 'gateway',
    '/meuid': 'meu_id'
}

def signal_handler(signum, frame):
    """Handler para sinais de interrupção"""
    global shutdown_requested
    if not shutdown_requested:
        event_logger.info(f"Shutdown iniciado - sinal {signum}")
        shutdown_requested = True
        # Forçar saída após 5 segundos
        import threading
        def force_exit():
            import time
            time.sleep(5)
            logger.error("Shutdown forçado após timeout")
            os._exit(1)
        threading.Thread(target=force_exit, daemon=True).start()
    else:
        logger.error("Segundo sinal recebido - forçando saída imediata")
        os._exit(1)

# Registrar handlers de sinal
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_gateways():
    """Inicializa o sistema de gateways"""
    global gateway_status
    
    for gateway_id, config in GATEWAYS.items():
        gateway_status[gateway_id] = {
            'status': 'active' if config['active'] else 'inactive',
            'last_error': None,
            'error_count': 0,
            'last_success': None,
            'total_requests': 0,
            'successful_requests': 0
        }
    
    event_logger.info(f"Gateways inicializados: {len(gateway_status)}")

def get_best_gateway(amount=None):
    """Retorna o melhor gateway disponível baseado na prioridade e status"""
    global gateway_rotation_index
    
    # Filtrar gateways ativos e válidos para o valor
    available_gateways = []
    for gateway_id, config in GATEWAYS.items():
        if (gateway_status[gateway_id]['status'] == 'active' and 
            config['active'] and
            (amount is None or (config['min_amount'] <= amount <= config['max_amount']))):
            available_gateways.append((gateway_id, config))
    
    if not available_gateways:
        logger.error("Nenhum gateway disponível")
        return None
    
    # Ordenar por prioridade
    available_gateways.sort(key=lambda x: x[1]['priority'])
    
    # Selecionar gateway com melhor taxa de sucesso
    best_gateway = None
    best_success_rate = 0
    
    for gateway_id, config in available_gateways:
        status = gateway_status[gateway_id]
        if status['total_requests'] > 0:
            success_rate = status['successful_requests'] / status['total_requests']
        else:
            success_rate = 1.0  # Gateway novo, assumir 100% de sucesso
        
        if success_rate > best_success_rate:
            best_success_rate = success_rate
            best_gateway = gateway_id
    
    if best_gateway:
        # Log apenas se taxa de sucesso baixa
        if best_success_rate < 0.8:
            logger.warning(f"Gateway {GATEWAYS[best_gateway]['name']} com baixa taxa de sucesso: {best_success_rate:.2%}")
        return best_gateway
    
    # Fallback para primeiro gateway disponível
    return available_gateways[0][0]

def mark_gateway_failed(gateway_id, error_msg):
    """Marca um gateway como falhado"""
    if gateway_id in gateway_status:
        gateway_status[gateway_id]['status'] = 'failed'
        gateway_status[gateway_id]['last_error'] = error_msg
        gateway_status[gateway_id]['error_count'] += 1
        
        logger.error(f"Gateway {GATEWAYS[gateway_id]['name']} falhou: {error_msg}")
        
        # Tentar reativar após 5 minutos
        asyncio.create_task(reactivate_gateway_after_delay(gateway_id, 300))

def mark_gateway_success(gateway_id):
    """Marca um gateway como bem-sucedido"""
    if gateway_id in gateway_status:
        gateway_status[gateway_id]['status'] = 'active'
        gateway_status[gateway_id]['last_success'] = datetime.now()
        gateway_status[gateway_id]['successful_requests'] += 1
        gateway_status[gateway_id]['total_requests'] += 1
        
        # Reset error count após sucesso
        if gateway_status[gateway_id]['error_count'] > 0:
            gateway_status[gateway_id]['error_count'] = max(0, gateway_status[gateway_id]['error_count'] - 1)

async def reactivate_gateway_after_delay(gateway_id, delay_seconds):
    """Reativa um gateway após um delay"""
    await asyncio.sleep(delay_seconds)
    if gateway_id in gateway_status:
        gateway_status[gateway_id]['status'] = 'active'
        event_logger.info(f"Gateway {GATEWAYS[gateway_id]['name']} reativado")

def is_admin(user_id):
    """Verifica se o usuário é administrador"""
    return user_id == ADMIN_USER_ID

def activate_gateway(gateway_id):
    """Ativa um gateway específico"""
    if gateway_id in GATEWAYS:
        GATEWAYS[gateway_id]['active'] = True
        gateway_status[gateway_id]['status'] = 'active'
        gateway_status[gateway_id]['error_count'] = 0
        event_logger.info(f"Gateway {GATEWAYS[gateway_id]['name']} ativado pelo admin")
        return True
    return False

def deactivate_gateway(gateway_id):
    """Desativa um gateway específico"""
    if gateway_id in GATEWAYS:
        GATEWAYS[gateway_id]['active'] = False
        gateway_status[gateway_id]['status'] = 'inactive'
        event_logger.info(f"Gateway {GATEWAYS[gateway_id]['name']} desativado pelo admin")
        return True
    return False

def set_gateway_priority(gateway_id, priority):
    """Define a prioridade de um gateway"""
    if gateway_id in GATEWAYS:
        GATEWAYS[gateway_id]['priority'] = priority
        event_logger.info(f"Prioridade do gateway {GATEWAYS[gateway_id]['name']} alterada para {priority}")
        return True
    return False

def get_gateway_status_text():
    """Retorna status dos gateways em formato de texto"""
    status_text = "💳 **STATUS DOS GATEWAYS**\n\n"
    
    for gateway_id, status in gateway_status.items():
        gateway_name = GATEWAYS[gateway_id]['name']
        priority = GATEWAYS[gateway_id]['priority']
        
        if status['status'] == 'active':
            status_icon = "✅"
        elif status['status'] == 'failed':
            status_icon = "❌"
        else:
            status_icon = "⏸️"
        
        success_rate = "N/A"
        if status['total_requests'] > 0:
            success_rate = f"{(status['successful_requests'] / status['total_requests'] * 100):.1f}%"
        
        status_text += f"{status_icon} **{gateway_name}**\n"
        status_text += f"   Prioridade: {priority}\n"
        status_text += f"   Taxa de Sucesso: {success_rate}\n"
        status_text += f"   Requisições: {status['total_requests']}\n"
        if status['last_error']:
            status_text += f"   Último Erro: {status['last_error'][:50]}...\n"
        status_text += "\n"
    
    return status_text

def check_rate_limit(user_id, action_type="start"):
    """Sistema inteligente de rate limiting que prioriza a última ação"""
    current_time = time.time()
    
    if user_id not in user_requests:
        user_requests[user_id] = {
            'last_response': 0,
            'pending_request': False,
            'last_action': action_type,
            'last_action_time': current_time
        }
        return True
    
    user_data = user_requests[user_id]
    time_since_last_response = current_time - user_data['last_response']
    
    # Se passou mais de 5 segundos desde a última resposta, pode responder
    if time_since_last_response >= RESPONSE_COOLDOWN:
        user_data['last_action'] = action_type
        user_data['last_action_time'] = current_time
        return True
    
    # Se ainda está no cooldown, verifica se a nova ação é mais importante
    time_since_last_action = current_time - user_data['last_action_time']
    
    # Se a nova ação é mais recente (últimos 2 segundos), substitui a anterior
    if time_since_last_action <= 2:
        # Log apenas para debug se necessário
        pass
        user_data['last_action'] = action_type
        user_data['last_action_time'] = current_time
        return True
    
    # Se ainda está no cooldown e não é uma ação recente
    user_data['pending_request'] = True
    # Log apenas se cooldown muito longo (possível problema)
    if time_since_last_response > RESPONSE_COOLDOWN * 2:
        logger.warning(f"Usuário {user_id} com cooldown excessivo: {time_since_last_response:.1f}s")
    return False

def mark_response_sent(user_id):
    """Marca que uma resposta foi enviada para o usuário"""
    current_time = time.time()
    if user_id not in user_requests:
        user_requests[user_id] = {'last_response': 0, 'pending_request': False, 'last_action': 'start', 'last_action_time': 0}
    
    user_requests[user_id]['last_response'] = current_time
    user_requests[user_id]['pending_request'] = False

class SyncPayIntegration:
    """Integração profissional com SyncPay"""
    
    def __init__(self):
        self.client_id = SYNCPAY_CLIENT_ID
        self.client_secret = SYNCPAY_CLIENT_SECRET
        self.base_url = SYNCPAY_BASE_URL
        self.access_token = None
        self.token_expires_at = 0
    
    def get_access_token(self):
        """Obtém token de acesso da SyncPay"""
        try:
            if self.access_token and time.time() < self.token_expires_at:
                return self.access_token
            
            url = f"{self.base_url}/api/partner/v1/auth-token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.token_expires_at = time.time() + token_data['expires_in'] - 60  # 1 min de margem
                
                # Token obtido com sucesso
                return self.access_token
            else:
                logger.error(f"Erro ao obter token SyncPay: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter token SyncPay: {e}")
            return None
    
    def create_payment(self, amount, description, user_id):
        """Cria pagamento PIX na SyncPay usando API Cash-in"""
        try:
            # Criando pagamento SyncPay
            
            # Obter token de acesso primeiro
            token = self.get_access_token()
            if not token:
                logger.error("Token SyncPay não obtido")
                return None
            
            url = f"{self.base_url}/api/partner/v1/cash-in"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Dados do cliente (obrigatórios pela API)
            client_data = {
                'name': f'Usuário {user_id}',
                'cpf': '12345678900',  # CPF genérico para testes
                'email': f'user{user_id}@telegram.com',
                'phone': '11999999999'  # Telefone genérico
            }
            
            data = {
                'amount': amount,
                'description': description,
                'client': client_data,
                'webhook_url': 'https://webhook.site/your-webhook-url'  # Opcional
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                payment_data = response.json()
                event_logger.info(f"Pagamento SyncPay criado: R$ {amount}")
                
                return {
                    'payment_id': payment_data.get('identifier'),
                    'pix_code': payment_data.get('pix_code'),
                    'status': 'pending'
                }
            else:
                logger.error(f"Erro HTTP SyncPay {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão SyncPay: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao criar pagamento SyncPay: {e}")
            return None
    
    def check_payment_status(self, payment_id):
        """Verifica status do pagamento"""
        try:
            # Obter token de acesso primeiro
            token = self.get_access_token()
            if not token:
                return None
            
            url = f"{self.base_url}/api/partner/v1/payments/{payment_id}"
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao verificar pagamento SyncPay: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao verificar status SyncPay: {e}")
            return None

async def create_pix_payment_pushynpay(user_id, amount, plan_name, customer_data):
    """Cria um pagamento PIX usando PushynPay com formato correto da API"""
    payment_id = str(uuid.uuid4())
    
    # Dados do pagamento para PushynPay (formato correto da API)
    payment_data = {
        "value": int(amount * 100),  # Converter para centavos (PushynPay exige)
        "webhook_url": "https://webhook.site/test",  # URL de teste temporária
        "split_rules": []  # Regras de split (vazio para pagamento simples)
    }
    
    # Headers para autenticação PushynPay
    headers = {
        "Authorization": f"Bearer {PUSHYNPAY_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Tentar endpoints PushynPay
    for i, endpoint in enumerate(PUSHYNPAY_ENDPOINTS):
        try:
            # Tentativa de pagamento PushynPay
            
            response = requests.post(
                endpoint,
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            # Processando resposta PushynPay
            
            # Verificar diferentes códigos de sucesso
            if response.status_code in [200, 201, 202]:
                try:
                    pix_data = response.json()
                    
                    # Verificar se tem código PIX (formato PushynPay)
                    pix_code = pix_data.get('pix_code') or pix_data.get('qr_code') or pix_data.get('code') or pix_data.get('pix')
                    
                    if pix_code:
                        # Armazenar pagamento pendente
                        pending_payments[user_id] = {
                            'payment_id': payment_id,
                            'amount': amount,
                            'plan': plan_name,
                            'pix_code': pix_code,
                            'expires_at': pix_data.get('expires_at'),
                            'gateway': 'pushynpay',
                            'gateway_payment_id': pix_data.get('id') or pix_data.get('payment_id')
                        }
                        
                        event_logger.info(f"PIX PushynPay criado: R$ {amount}")
                        return pix_data
                    else:
                        logger.warning(f"Resposta PushynPay sem código PIX")
                        continue
                        
                except json.JSONDecodeError:
                    logger.error(f"Resposta PushynPay não é JSON válido")
                    continue
            elif response.status_code == 401:
                logger.error(f"Token PushynPay inválido")
                continue
            elif response.status_code == 422:
                logger.error(f"Dados PushynPay inválidos")
                continue
            else:
                logger.warning(f"Status PushynPay {response.status_code}")
                continue
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão PushynPay tentativa {i+1}")
            continue
        except Exception as e:
            logger.error(f"Erro PushynPay tentativa {i+1}: {e}")
            continue
    
    logger.error(f"Todas as tentativas PushynPay falharam")
    return None

async def create_pix_payment_syncpay_original(user_id, amount, plan_name, customer_data):
    """Cria um pagamento PIX usando SyncPay Original"""
    try:
        # Gerar ID único para o pagamento
        payment_id = str(uuid.uuid4())
        
        # Dados do cliente
        customer_info = {
            "name": customer_data.get("name", f"Cliente {user_id}"),
            "email": customer_data.get("email", f"cliente{user_id}@example.com"),
            "document": customer_data.get("document", "12345678900")
        }
        
        # Dados do pagamento
        payment_data = {
            "amount": amount,
            "description": f"Pagamento do plano {plan_name}",
            "customer": customer_info,
            "external_id": payment_id,
            "webhook_url": "https://your-webhook-url.com/syncpay-original-callback"
        }
        
        # Headers para autenticação SyncPay Original
        headers = {
            "Authorization": f"Bearer {SYNCPAY_CLIENT_SECRET}",
            "Content-Type": "application/json"
        }
        
        # Fazer requisição para criar PIX
        response = requests.post(
            f"{SYNCPAY_BASE_URL}/pix",
            json=payment_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            pix_data = response.json()
            
            # Armazenar pagamento pendente
            pending_payments[user_id] = {
                'payment_id': payment_id,
                'amount': amount,
                'plan': plan_name,
                'pix_code': pix_data.get('pix_code'),
                'expires_at': pix_data.get('expires_at'),
                'gateway': 'syncpay_original',
                'gateway_payment_id': pix_data.get('id')
            }
            
            event_logger.info(f"PIX SyncPay Original criado: R$ {amount}")
            return pix_data
            
        else:
            logger.error(f"Erro ao criar PIX SyncPay Original: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Erro na criação do PIX SyncPay Original: {e}")
        return None

async def create_pix_payment_with_fallback(user_id, amount, plan_name, customer_data):
    """Cria um pagamento PIX com failover automático entre gateways"""
    gateway_id = get_best_gateway(amount)
    
    if not gateway_id:
        logger.error("Nenhum gateway disponível para criar PIX")
        return None
    
    max_retries = 2
    current_gateway = gateway_id
    
    for attempt in range(max_retries):
        try:
            # Tentativa de criação de PIX
            
            if current_gateway == 'pushynpay':
                result = await create_pix_payment_pushynpay(user_id, amount, plan_name, customer_data)
            elif current_gateway == 'syncpay_original':
                result = await create_pix_payment_syncpay_original(user_id, amount, plan_name, customer_data)
            else:
                logger.error(f"Gateway desconhecido: {current_gateway}")
                return None
            
            if result:
                mark_gateway_success(current_gateway)
                return result
            else:
                mark_gateway_failed(current_gateway, f"Falha na criação do PIX (tentativa {attempt + 1})")
                
        except Exception as e:
            mark_gateway_failed(current_gateway, str(e))
            logger.error(f"Erro no gateway {current_gateway}: {e}")
        
        # Tentar próximo gateway
        current_gateway = get_best_gateway(amount)
        if not current_gateway or current_gateway == gateway_id:
            break
    
    logger.error("Todos os gateways falharam ao criar PIX")
    return None

def get_next_bot():
    """Retorna o próximo bot disponível (round-robin)"""
    global bot_rotation_index
    
    if not active_bots:
        logger.error("Nenhum bot ativo disponível")
        return None
    
    # Filtrar apenas bots ativos
    active_tokens = [token for token, info in active_bots.items() if info['status'] == 'active']
    
    if not active_tokens:
        logger.error("Nenhum bot ativo encontrado")
        return None
    
    # Round-robin
    token = active_tokens[bot_rotation_index % len(active_tokens)]
    bot_rotation_index += 1
    
    return active_bots[token]

async def initialize_bot(token):
    """Inicializa um bot individual"""
    try:
        # Inicializando bot
        
        # Criar aplicação do bot
        application = Application.builder().token(token).build()
        
        # Configurar handlers
        await setup_bot_handlers(application, token)
        
        # Testar conexão
        bot = application.bot
        bot_info = await bot.get_me()
        
        event_logger.info(f"Bot inicializado: @{bot_info.username}")
        
        return {
            'application': application,
            'bot': bot,
            'token': token,
            'status': 'active',
            'last_heartbeat': datetime.now(),
            'retry_count': 0
        }
        
    except Exception as e:
        logger.error(f"Erro ao inicializar bot: {e}")
        return None

async def setup_bot_handlers(application, token):
    """Configura os handlers para cada bot"""
    
    # Handler para comando /start
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user
        user_id = user.id
        
        # Verificar rate limiting inteligente
        if not check_rate_limit(user_id, "start"):
            # Usuário em cooldown
            return
        
        event_logger.info(f"/start executado por {user.first_name} (ID: {user_id})")
        add_event('INFO', f'Comando /start executado por {user.first_name}', user_id)
        
        # Adicionar usuário único (só incrementa se for novo usuário)
        is_new_user = add_unique_user(user_id, user.first_name, user.username)
        if is_new_user:
            event_logger.info(f"Novo usuário: {user.first_name} (ID: {user_id})")
        # else: usuário existente
        
        # Adicionar sessão de usuário para downsell
        add_user_session(user_id)
        
        # Mensagem principal
        message_text = """🚷 𝗩𝗢𝗖Ê 𝗔𝗖𝗔𝗕𝗢𝗨 𝗗𝗘 𝗘𝗡𝗧𝗥𝗔𝗥 𝗡𝗢 𝗔𝗕𝗜𝗦𝗠𝗢 — 𝗘 𝗔𝗤𝗨𝗜 𝗡Ã𝗢 𝗘𝗫𝗜𝗦𝗧𝗘 𝗩𝗢𝗟𝗧𝗔.
💎 O maior e mais pr🔞ibid🔞 Rateio de Grupos VIPs do Telegram está aberto… mas não por muito tempo.

🔞 OnlyF4ns, Privacy, Close Friends VAZADOS
🔞 Famosas, Nov!nhas +18, Amadoras & Milf's insaciáveis
🔞 L!ves completas, conteúdos escondidos e traições reais gravadas.

🎭 Casais abertos | 🎥 V!d3os de surub4s | 😈 Segredos de inc3sto | 🚨 Fet!ches 🔞cultos do c0rno moderno.

🔥 𝗔𝘁𝘂𝗮𝗹𝗶𝘇𝗮çõ𝗲𝘀 𝗗𝗶á𝗿𝗶𝗮𝘀 — 𝗡𝗮𝗱𝗮 𝗳𝗶𝗰𝗮 𝘃𝗲𝗹𝗵𝗼.
🔒 𝗖𝗼𝗺𝗽𝗿𝗮 𝟭𝟬𝟬% 𝗦𝗲𝗴𝘂𝗿𝗮 — 𝗡𝗶𝗻𝗴𝘂é𝗺 𝗱𝗲𝘀𝗰𝗼𝗯𝗿𝗲.
⚡️ 𝗔𝗰𝗲𝘀𝘀𝗼 𝗜𝗺𝗲𝗱𝗶𝗮𝘁𝗼 — 𝗘𝗺 𝗺𝗲𝗻𝗼𝘀 𝗱𝗲 𝟭 𝗺𝗶𝗻𝘂𝘁𝗼 𝘃𝗼𝗰ê 𝗷á 𝗲𝘀𝘁á 𝗱𝗲𝗻𝘁𝗿𝗼.

❌ Aqui não tem "achismos": são os vídeos que NINGUÉM teria coragem de postar publicamente.
👉 Se você sair agora, nunca mais encontra esse conteúdo.

🎁 𝗕ô𝗻𝘂𝘀 𝗦ó 𝗛𝗼𝗷𝗲: 𝗮𝗼 𝗮𝘀𝘀𝗶𝗻𝗮𝗿, 𝘃𝗼𝗰ê 𝗿𝗲𝗰𝗲𝗯𝗲 𝗮𝗰𝗲𝘀𝘀𝗼 𝘀𝗲𝗰𝗿𝗲𝘁𝗼 𝗮 +𝟰 𝗚𝗿𝘂𝗽𝗼𝘀 𝗩𝗜𝗣'𝘀 𝗼𝗰𝘂𝗹𝘁𝗼𝘀 (𝗻𝗼𝘃!𝗻𝗵𝟰𝘀, 𝗰𝗮𝘀𝗮𝗱𝗮𝘀 𝗿𝗲𝗮𝗶𝘀, 𝗳𝗹𝗮𝗴𝗿𝗮𝘀 𝗽𝗿🔞𝗶𝗯𝗶𝗱𝗼𝘀 & 𝗺í𝗱𝗶𝗮𝘀 𝗱𝗮 𝗱4️⃣ 𝗿𝗸 𝘄𝟯𝗯)."""
        
        # Botões
        keyboard = [
            [InlineKeyboardButton("❌🤫𝐕𝐈𝐓𝐀𝐋𝐈𝐂𝐈𝐎(𝐏𝐑𝐎𝐌𝐎)🤫❌ 𝐩𝐨𝐫 𝟏𝟗.𝟗𝟕", callback_data="vitalicio")],
            [InlineKeyboardButton("❌🤫𝟭 𝗺ê𝘀 🤫❌ 𝐩𝐨𝐫 𝟏𝟒.𝟗𝟕", callback_data="mensal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar vídeo principal via link
        video_link = "https://t.me/MDMDMDMDAA2/35"  # Link do vídeo principal
        
        try:
            await update.message.reply_video(
                video=video_link,
                caption=message_text,
                reply_markup=reply_markup,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30
            )
            # Vídeo enviado com sucesso
        except Exception as e:
            logger.error(f"Erro ao enviar vídeo: {e}")
            # Fallback: enviar apenas texto
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup
            )
            # Fallback para texto enviado
        
        # Marcar resposta como enviada
        mark_response_sent(user_id)
        
        # Iniciar timers de downsell se configurado
        start_downsell_timers(user_id)
    
    # Handler para botões
    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa cliques nos botões"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_id = user.id
        
        # Verificar rate limiting inteligente
        if not check_rate_limit(user_id, "button"):
            # Usuário em cooldown
            return
        
        # Botão clicado
        
        if query.data == "vitalicio":
            # Order bump para vitalício
            await send_order_bump(query)
        elif query.data == "mensal":
            # Order bump para mensal
            await send_order_bump_mensal(query)
        elif query.data == "aceitar_bonus":
            await create_payment(query, 32.87, "VITALÍCIO + SALA VERMELHA", user_id)
        elif query.data == "nao_quero_bonus":
            await create_payment(query, 19.97, "VITALÍCIO", user_id)
        elif query.data == "aceitar_bonus_mensal":
            await create_payment(query, 27.87, "1 MÊS + PACOTE SOMBRIO", user_id)
        elif query.data == "nao_quero_bonus_mensal":
            await create_payment(query, 14.97, "1 MÊS", user_id)
        elif query.data.startswith("verificar_pagamento"):
            # Extrair user_id do callback_data
            if "_" in query.data:
                user_id = int(query.data.split("_")[-1])
            else:
                user_id = query.from_user.id
            
            await check_payment_status(query, user_id)
        
        # Marcar resposta como enviada
        mark_response_sent(user_id)
    
    # Handler para mensagens
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens"""
        user = update.effective_user
        user_id = user.id
        text = update.message.text
        
        # Verificar rate limiting inteligente
        if not check_rate_limit(user_id, "message"):
            # Usuário em cooldown
            return
        
        # Mensagem recebida
        
        response = f"Você disse: {text}\nUse /help para comandos!"
        await update.message.reply_text(response)
        # Resposta enviada
        
        # Marcar resposta como enviada
        mark_response_sent(user_id)
    
    # Handler para /help
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        # Comando /help executado
        await update.message.reply_text("Comandos:\n/start - Iniciar\n/help - Ajuda\n/info - Info")
    
    # Handler para /info
    async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /info"""
        user = update.effective_user
        # Comando /info executado
        await update.message.reply_text(f"Bot Info:\nUsuário: {user.first_name}\nID: {user.id}")
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    
    # Handlers para comandos administrativos
    application.add_handler(CommandHandler("admin", admin_with_args_handler))
    application.add_handler(CommandHandler("gw", gateway_command_handler))
    application.add_handler(CommandHandler("meuid", admin_command_handler))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handlers configurados

async def admin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comandos administrativos usando argumentos"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Acesso negado. Apenas administradores podem usar este comando.")
        return
    
    command = update.message.text.lower()
    
    if command == '/admin':
        help_text = """🔧 **COMANDOS ADMINISTRATIVOS**

**Comandos principais:**
• `/admin ativar <pushyn|sync>` - Ativa gateway
• `/admin desativar <pushyn|sync>` - Desativa gateway  
• `/admin status` - Status dos gateways
• `/admin prioridade <pushyn|sync> <1|2>` - Define prioridade
• `/admin testar <pushyn|sync>` - Testa gateway

**Comandos rápidos:**
• `/gw pushyn` - Ativa PushynPay
• `/gw sync` - Ativa SyncPay Original
• `/gw status` - Status dos gateways

**Outros:**
• `/meuid` - Mostra seu ID"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    elif command == '/meuid':
        user = update.effective_user
        await update.message.reply_text(f"🆔 Seu ID: `{user.id}`\n\nNome: {user.first_name}\nUsername: @{user.username or 'N/A'}", parse_mode='Markdown')
    
    elif command == '/testar':
        await update.message.reply_text("🧪 Para testar PushynPay, use: `/admin testar pushyn`")
    
    else:
        await update.message.reply_text("❌ Comando administrativo não reconhecido")

async def admin_with_args_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /admin com argumentos"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Acesso negado.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: /admin <acao> [gateway] [prioridade]")
        return
    
    action = context.args[0].lower()
    
    if action == "ativar":
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /admin ativar <pushyn|sync>")
            return
        
        gateway = context.args[1].lower()
        if gateway == "pushyn":
            if activate_gateway('pushynpay'):
                await update.message.reply_text("✅ Gateway PushynPay ATIVADO!")
            else:
                await update.message.reply_text("❌ Erro ao ativar gateway PushynPay")
        elif gateway == "sync":
            if activate_gateway('syncpay_original'):
                await update.message.reply_text("✅ Gateway SyncPay Original ATIVADO!")
            else:
                await update.message.reply_text("❌ Erro ao ativar gateway SyncPay Original")
        else:
            await update.message.reply_text("❌ Gateway inválido. Use: pushyn ou sync")
    
    elif action == "desativar":
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /admin desativar <pushyn|sync>")
            return
        
        gateway = context.args[1].lower()
        if gateway == "pushyn":
            if deactivate_gateway('pushynpay'):
                await update.message.reply_text("❌ Gateway PushynPay DESATIVADO!")
            else:
                await update.message.reply_text("❌ Erro ao desativar gateway PushynPay")
        elif gateway == "sync":
            if deactivate_gateway('syncpay_original'):
                await update.message.reply_text("❌ Gateway SyncPay Original DESATIVADO!")
            else:
                await update.message.reply_text("❌ Erro ao desativar gateway SyncPay Original")
        else:
            await update.message.reply_text("❌ Gateway inválido. Use: pushyn ou sync")
    
    elif action == "status":
        status_text = get_gateway_status_text()
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    elif action == "prioridade":
        if len(context.args) < 3:
            await update.message.reply_text("Uso: /admin prioridade <pushyn|sync> <1|2>")
            return
        
        gateway = context.args[1].lower()
        priority = int(context.args[2])
        
        if gateway == "pushyn":
            if set_gateway_priority('pushynpay', priority):
                await update.message.reply_text(f"🎯 PushynPay definido como PRIORIDADE {priority}!")
            else:
                await update.message.reply_text("❌ Erro ao alterar prioridade")
        elif gateway == "sync":
            if set_gateway_priority('syncpay_original', priority):
                await update.message.reply_text(f"🎯 SyncPay Original definido como PRIORIDADE {priority}!")
            else:
                await update.message.reply_text("❌ Erro ao alterar prioridade")
        else:
            await update.message.reply_text("❌ Gateway inválido. Use: pushyn ou sync")
    
    elif action == "testar":
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /admin testar <pushyn|sync>")
            return
        
        gateway = context.args[1].lower()
        if gateway == "pushyn":
            await update.message.reply_text("🧪 Testando PushinPay...")
            
            # Dados de teste
            test_customer = {
                "name": "Teste PushynPay",
                "email": "teste@pushynpay.com",
                "document": "12345678900"
            }
            
            try:
                result = await create_pix_payment_pushynpay(
                    user_id, 0.50, "Teste PushynPay", test_customer  # R$ 0,50 = 50 centavos
                )
                
                if result:
                    pix_code = result.get('qr_code') or result.get('pix_code') or result.get('code')
                    if pix_code:
                        await update.message.reply_text(f"✅ PushynPay FUNCIONANDO!\n\n🎯 Código PIX: `{pix_code}`", parse_mode='Markdown')
                    else:
                        await update.message.reply_text(f"⚠️ PushinPay respondeu mas sem código PIX:\n```json\n{result}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text(
                        "❌ **PUSHYNPAY FALHOU**\n\n"
                        "🔍 **POSSÍVEIS CAUSAS:**\n"
                        "• Token inválido ou expirado\n"
                        "• Valor mínimo: R$ 0,50\n"
                        "• Problemas de conectividade\n\n"
                        "🛠️ **SOLUÇÕES:**\n"
                        "• Verificar token PushynPay\n"
                        "• Usar valor mínimo R$ 0,50\n"
                        "• Contatar suporte PushynPay",
                        parse_mode='Markdown'
                    )
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Erro no teste PushynPay: {e}")
                
        elif gateway == "sync":
            await update.message.reply_text("🧪 Testando SyncPay Original...")
            
            test_customer = {
                "name": "Teste SyncPay",
                "email": "teste@syncpay.com", 
                "document": "12345678900"
            }
            
            try:
                result = await create_pix_payment_syncpay_original(
                    user_id, 1.00, "Teste SyncPay", test_customer
                )
                
                if result:
                    pix_code = result.get('pix_code') or result.get('qr_code') or result.get('code')
                    if pix_code:
                        await update.message.reply_text(f"✅ SyncPay Original FUNCIONANDO!\n\n🎯 Código PIX: `{pix_code}`", parse_mode='Markdown')
                    else:
                        await update.message.reply_text(f"⚠️ SyncPay respondeu mas sem código PIX:\n```json\n{result}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text("❌ SyncPay Original FALHOU - Verifique os logs para detalhes")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Erro no teste SyncPay: {e}")
        else:
            await update.message.reply_text("❌ Gateway inválido para teste. Use: pushyn ou sync")
    
    else:
        await update.message.reply_text("❌ Ação inválida. Use: ativar, desativar, status, prioridade, testar")

async def gateway_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /gw com argumentos"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Acesso negado.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: /gw <pushyn|sync|status>")
        return
    
    action = context.args[0].lower()
    
    if action == "pushyn":
        if activate_gateway('pushynpay'):
            await update.message.reply_text("✅ Gateway PushynPay ATIVADO!")
        else:
            await update.message.reply_text("❌ Erro ao ativar gateway PushynPay")
    
    elif action == "sync":
        if activate_gateway('syncpay_original'):
            await update.message.reply_text("✅ Gateway SyncPay Original ATIVADO!")
        else:
            await update.message.reply_text("❌ Erro ao ativar gateway SyncPay Original")
    
    elif action == "status":
        status_text = get_gateway_status_text()
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    else:
        await update.message.reply_text("❌ Ação inválida. Use: pushyn, sync, status")

async def send_order_bump(query):
    """Envia order bump com vídeo e botões"""
    # Mensagem do order bump (SALA VERMELHA)
    order_bump_text = """📦 DESBLOQUEAR SALA VERMELHA 📦

🚷 Arquivos deletados do servidor principal e salvos só pra essa liberação.
✅ Amador das faveladinhas
✅ Amador com o papai depois do banho ⭐️🤫
✅ Vídeos que já foi banido em vários países.
✅ Conteúdo de cameras escondidas com áudio original.
💥 Ative agora e leva 1 grupo s3cr3to bônus."""
    
    # Botões do order bump
    keyboard = [
        [InlineKeyboardButton("✅ Aceitar Oportunidade", callback_data="aceitar_bonus")],
        [InlineKeyboardButton("❌ Não Quero Bônus", callback_data="nao_quero_bonus")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar vídeo do order bump via link
    video_link = "https://t.me/MDMDMDMDAA2/3"  # Link do order bump vitalício
    
    try:
            await query.message.reply_video(
            video=video_link,
                caption=order_bump_text,
                reply_markup=reply_markup
            )
        # Order bump enviado
    except Exception as e:
        logger.error(f"Erro ao enviar vídeo do order bump: {e}")
        await query.edit_message_text(order_bump_text, reply_markup=reply_markup)
        # Fallback para texto

async def send_order_bump_mensal(query):
    """Envia order bump mensal com vídeo e botões"""
    # Mensagem do order bump mensal (PACOTE SOMBRIO)
    order_bump_text = """📦 DESBLOQUEAR PACOTE SOMBRIO 📦

🚷 Arquivos deletados do servidor principal e salvos só pra essa liberação.
✅ Amador das faveladinhas
✅ Amador com o papai depois do banho ⭐️🤫
✅ Vídeos que já foi banido em vários países.
✅ Conteúdo de cameras escondidas com áudio original.
💥 Ative agora e leva 1 grupo s3cr3to bônus."""
    
    # Botões do order bump mensal
    keyboard = [
        [InlineKeyboardButton("✅ Aceitar Oportunidade", callback_data="aceitar_bonus_mensal")],
        [InlineKeyboardButton("❌ Não Quero Bônus", callback_data="nao_quero_bonus_mensal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar vídeo do order bump mensal via link
    video_link = "https://t.me/MDMDMDMDAA2/4"  # Link do order bump mensal
    
    try:
            await query.message.reply_video(
            video=video_link,
                caption=order_bump_text,
                reply_markup=reply_markup
            )
        # Order bump mensal enviado
    except Exception as e:
        logger.error(f"Erro ao enviar vídeo do order bump mensal: {e}")
        await query.edit_message_text(order_bump_text, reply_markup=reply_markup)
        # Fallback para texto

async def create_payment(query, amount, description, user_id):
    """Cria pagamento PIX com fallback simples entre gateways"""
    try:
        event_logger.info(f"Pagamento criado: R$ {amount} - {description}")
        
        # Dados do cliente
        customer_data = {
            "name": query.from_user.first_name or f"Cliente {user_id}",
            "email": f"cliente{user_id}@example.com",
            "document": "12345678900"
        }
        
        # Tentar PushinPay primeiro (já funcionava)
        # Tentando PushinPay primeiro
        try:
            payment_data = await create_pix_payment_pushynpay(user_id, amount, description, customer_data)
            if payment_data and payment_data.get('qr_code'):
                # PushinPay funcionou
                gateway_used = "pushynpay"
            else:
                raise Exception("PushinPay retornou sem código PIX")
        except Exception as e:
            logger.warning(f"PushinPay falhou: {e}")
            payment_data = None
        
        # Se PushinPay falhou, tentar SyncPay Original
        if not payment_data:
            # Tentando SyncPay Original
            try:
                payment_data = await create_pix_payment_syncpay_original(user_id, amount, description, customer_data)
                if payment_data and payment_data.get('pix_code'):
                    # SyncPay Original funcionou
                    gateway_used = "syncpay_original"
                else:
                    raise Exception("SyncPay retornou sem código PIX")
            except Exception as e:
                logger.warning(f"SyncPay Original falhou: {e}")
                payment_data = None
        
        # Se ambos falharam, usar fallback manual
        if not payment_data:
            logger.error("Ambos os gateways falharam, usando PIX manual")
            await create_fallback_payment(query, amount, description, user_id)
            return
        
        # Sucesso! Processar pagamento
        pix_code = payment_data.get('qr_code') or payment_data.get('pix_code')
        
        if not pix_code:
            logger.error(f"Código PIX não encontrado")
            await query.message.reply_text("❌ Erro ao gerar código PIX. Tente novamente.")
            return
        
        # Obter token do bot atual
        current_bot_token = None
        for token, bot_info in active_bots.items():
            if bot_info['status'] == 'active':
                current_bot_token = token
                break
        
        # Armazenar dados do pagamento
        pending_payments[user_id] = {
            'payment_id': payment_data.get('id', str(uuid.uuid4())),
            'amount': amount,
            'plan': description,
            'gateway': gateway_used,
            'pix_code': pix_code,
            'bot_token': current_bot_token  # Armazenar qual bot processou o pagamento
        }
        
        # Registrar pagamento pendente no sistema compartilhado
        from shared_data import add_pending_payment
        add_pending_payment(user_id, {
            'payment_id': payment_data.get('id') or str(uuid.uuid4()),
            'amount': amount,
            'plan': description,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'user_name': query.from_user.first_name or 'Usuário',
            'user_username': query.from_user.username or '',
            'gateway': gateway_used
        })
        
        # Marcar usuário como comprador
        update_user_session(user_id, purchased=True)
        
        # Mensagem do PIX com bloco de código HTML
        pix_message = f"""💠 Pague via Pix Copia e Cola:

<pre>{pix_code}</pre>

👆 Toque no código acima para copiá-lo facilmente

‼️ Após o pagamento, clique no botão abaixo para verificar:"""
        
        # Botão para verificar pagamento
        keyboard = [
            [InlineKeyboardButton("✅ Verificar Pagamento", callback_data=f"verificar_pagamento_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar mensagem com parse_mode HTML
        await query.message.reply_text(pix_message, reply_markup=reply_markup, parse_mode='HTML')
        event_logger.info(f"PIX enviado via {gateway_used}")
        
    except Exception as e:
        logger.error(f"Erro ao criar pagamento: {e}")
        try:
            await query.message.reply_text("❌ Erro ao processar pagamento. Tente novamente.")
        except:
            await query.answer("❌ Erro ao processar pagamento. Tente novamente.")

async def create_fallback_payment(query, amount, description, user_id):
    """Fallback: cria PIX manual quando SyncPay falha"""
    try:
        # Gerar PIX manual simples
        pix_code = f"00020126360014BR.GOV.BCB.PIX0114+5511999999999520400005303986540{amount:.2f}5802BR5925GRMPAY BOT TELEGRAM6009SAO PAULO62070503***6304"
        
        # Armazenar dados do pagamento (sem ID da SyncPay)
        pending_payments[user_id] = {
            'payment_id': f"manual_{user_id}_{int(time.time())}",
            'amount': amount,
            'plan': description,
            'manual': True
        }
        
        pix_message = f"""💠 PIX MANUAL - {description}

💰 Valor: R$ {amount:.2f}

📱 Para pagar:
1. Abra seu app de banco
2. Escaneie o QR Code ou copie o código PIX
3. Confirme o pagamento
4. Clique em "Verificar Pagamento"

‼️ Após o pagamento, clique no botão abaixo:"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Verificar Pagamento", callback_data=f"verificar_pagamento_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar nova mensagem em vez de editar
        await query.message.reply_text(pix_message, reply_markup=reply_markup, parse_mode='HTML')
        event_logger.info(f"PIX manual criado")
        
    except Exception as e:
        logger.error(f"Erro no fallback: {e}")
        try:
            await query.message.reply_text("❌ Sistema temporariamente indisponível. Tente novamente em alguns minutos.")
        except:
            await query.answer("❌ Sistema temporariamente indisponível. Tente novamente em alguns minutos.")

async def check_payment_status(query, user_id):
    """Verifica status do pagamento"""
    try:
        if user_id not in pending_payments:
            await query.edit_message_text("❌ Nenhum pagamento pendente encontrado.")
            return
        
        payment_info = pending_payments[user_id]
        payment_id = payment_info['payment_id']
        
        # Verificando status do pagamento
        
        # Se é pagamento manual, simular verificação
        if payment_info.get('manual'):
            await query.edit_message_text(f"""⏳ PAGAMENTO MANUAL

💰 Valor: R$ {payment_info['amount']:.2f}
📋 Plano: {payment_info['plan']}

🔄 Para pagamentos manuais, entre em contato com @seu_usuario após o pagamento para liberação imediata.

📱 Ou aguarde até 24h para liberação automática.""")
            return
        
        # Criar instância SyncPay
        syncpay = SyncPayIntegration()
        
        # Verificar na SyncPay
        status = syncpay.check_payment_status(payment_id)
        
        if status == 'paid':
            # Pagamento confirmado
            await query.edit_message_text(f"""🎉 PAGAMENTO CONFIRMADO!

✅ {payment_info['plan']}
💰 Valor: R$ {payment_info['amount']:.2f}

🎁 Seu acesso será liberado em até 5 minutos!
📱 Entre em contato com @seu_usuario para receber os links dos grupos.

Obrigado pela compra! 🚀""")
            
            # Enviar link de acesso liberado com token do bot
            bot_token = payment_info.get('bot_token')
            await send_access_link(user_id, bot_token)
            
            # Remover pagamento pendente
            del pending_payments[user_id]
            event_logger.info(f"Pagamento confirmado: R$ {payment_info['amount']}")
            
        elif status == 'pending':
            # Pagamento pendente - permitir verificação novamente
            keyboard = [
                [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f"verificar_pagamento_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"""⏳ PAGAMENTO AINDA NÃO CONFIRMADO

🔄 Aguarde alguns minutos e clique em "Verificar Novamente"

💡 O PIX pode levar até 5 minutos para ser processado
⏰ Você pode verificar quantas vezes quiser até ser autorizado

💰 Valor: R$ {payment_info['amount']:.2f}
📋 Plano: {payment_info['plan']}""", reply_markup=reply_markup)
            
        else:
            # Pagamento não encontrado ou erro - permitir nova verificação
            keyboard = [
                [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f"verificar_pagamento_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"""❌ PAGAMENTO NÃO IDENTIFICADO

🔄 Clique em "Verificar Novamente" para tentar mais uma vez

💡 Possíveis motivos:
• PIX ainda está sendo processado
• Aguarde alguns minutos após o pagamento
• Verifique se copiou o código PIX corretamente

💰 Valor: R$ {payment_info['amount']:.2f}
📋 Plano: {payment_info['plan']}""", reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Erro ao verificar pagamento: {e}")
        
        # Em caso de erro, também permitir nova verificação
        keyboard = [
            [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f"verificar_pagamento_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(f"""❌ ERRO AO VERIFICAR PAGAMENTO

🔄 Clique em "Verificar Novamente" para tentar mais uma vez

💡 Possíveis motivos:
• Problema temporário de conexão
• Aguarde alguns minutos e tente novamente
• Se persistir, entre em contato com @seu_usuario

💰 Valor: R$ {payment_info['amount']:.2f}
📋 Plano: {payment_info['plan']}""", reply_markup=reply_markup)

async def send_access_link(user_id, bot_token=None):
    """Envia o link de acesso liberado após confirmação do pagamento"""
    try:
        # Determinar qual link usar baseado no bot que processou o pagamento
        access_link = "https://oacessoliberado.shop/vip2"  # Link padrão
        
        if bot_token and bot_token in BOT_LINKS:
            access_link = BOT_LINKS[bot_token]
            event_logger.info(f"Usando link específico do bot: {access_link}")
        else:
            event_logger.info(f"Usando link padrão: {access_link}")
        
        access_message = f"""🔓 Para Liberar Seu Acesso
⬇️Clique aqui⬇️

{access_link}"""
        
        # Obter bot ativo para enviar mensagem
        active_bot = None
        for token, bot_info in active_bots.items():
            if bot_info['status'] == 'active':
                active_bot = bot_info['bot']
                break
        
        if active_bot:
            await active_bot.send_message(
                chat_id=user_id,
                text=access_message
            )
            
            event_logger.info(f"Link de acesso enviado: {access_link}")
            add_event('INFO', f'Link de acesso enviado para usuário {user_id}: {access_link}', user_id)
        
    except Exception as e:
        logger.error(f"Erro ao enviar link de acesso: {e}")
        add_event('ERROR', f'Erro ao enviar link de acesso: {e}', user_id)

def start_downsell_timers(user_id):
    """Inicia timers de downsell para um usuário"""
    downsell_config = get_downsell_config()
    
    if not downsell_config.get('enabled', False):
        return
    
    downsells = downsell_config.get('downsells', [])
    if not downsells:
        return
    
    event_logger.info(f"Iniciando {len(downsells)} timers de downsell")
    
    for i, downsell in enumerate(downsells):
        delay_minutes = downsell.get('sendTime', 5)  # Usar 'sendTime' em vez de 'delay_minutes'
        delay_seconds = delay_minutes * 60
        
        add_timer(user_id, i, delay_seconds)
        # Timer programado

async def start_downsell_scheduler():
    """Scheduler contínuo para gerenciar downsells"""
    event_logger.info("Scheduler de downsells iniciado")
    
    while True:
        try:
            # Obter todos os downsells agendados
            scheduled_downsells = get_all_scheduled_downsells()
            
            if scheduled_downsells:
                # Verificando downsells agendados
                current_time = datetime.now().timestamp()
            
            for ds in scheduled_downsells:
                # Verificar se é hora de enviar
                if ds["next_run"] <= current_time:
                    # Enviando downsell
                    
                    try:
                        # Enviar downsell
                        await send_downsell_to_user(ds["user_id"], ds["downsell"], ds["downsell_index"])
                        
                        # Marcar como enviado na sessão do usuário
                        user_session = get_user_session(ds["user_id"])
                        if user_session:
                            downsells_sent = user_session.get('downsell_sent', [])
                            downsells_sent.append(ds["downsell_index"])
                            update_user_session(ds["user_id"], downsell_sent=downsells_sent)
                        
                        # Remover timer (downsell enviado)
                        update_downsell_schedule(ds["id"])
                        
                        # Incrementar estatísticas
                        increment_downsell_stats('total_downsells_sent')
                        
                        event_logger.info(f"Downsell {ds['downsell_index']} enviado")
                        
                    except Exception as e:
                        logger.error(f"Erro ao enviar downsell {ds['downsell_index']}: {e}")
            
            # Aguardar 60 segundos antes da próxima verificação
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Erro no scheduler de downsells: {e}")
            await asyncio.sleep(60)  # Aguardar antes de tentar novamente

async def send_downsell_to_user(user_id, downsell, downsell_index):
    """Envia um downsell específico para um usuário"""
    try:
        # Obter bot disponível
        bot_info = get_next_bot()
        if not bot_info:
            logger.error("Nenhum bot disponível para enviar downsell")
            return
        
        bot = bot_info['bot']  # Obter o objeto Bot real
        
        # Texto do downsell
        downsell_text = downsell.get('text', '')
        
        # Criar botões de pagamento
        keyboard = []
        payment_buttons = downsell.get('paymentButtons', [])
        
        for button in payment_buttons:
            button_text = button.get('text', '')
            price = button.get('price', 0)
            description = button.get('description', '')
            
            # Criar callback_data para mostrar order bump primeiro
            if 'vitalício' in button_text.lower() or 'vitalicio' in button_text.lower():
                callback_data = "vitalicio"  # Vai mostrar order bump primeiro
            else:  # Mensal
                callback_data = "mensal"  # Vai mostrar order bump primeiro
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        # Se tem mídia, enviar vídeo com caption
        media_file = downsell.get('mediaFile', '')
        if media_file:
            try:
                if media_file.startswith('https://t.me/'):
                    # É um link do Telegram - enviar como vídeo com caption
                    await bot.send_video(
                        chat_id=user_id,
                        video=media_file,
                        caption=downsell_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    # É um arquivo local - enviar como vídeo
                    with open(media_file, 'rb') as f:
                        await bot.send_video(
                            chat_id=user_id,
                            video=f,
                            caption=downsell_text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
            except Exception as media_error:
                logger.warning(f"Erro ao enviar mídia do downsell: {media_error}")
                # Fallback: enviar apenas texto com botões
                await bot.send_message(
                    chat_id=user_id,
                    text=downsell_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            # Sem mídia - enviar apenas texto com botões
            await bot.send_message(
                chat_id=user_id,
                text=downsell_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        # Downsell enviado
        
    except Exception as e:
        logger.error(f"Erro ao enviar downsell para usuário {user_id}: {e}")

async def monitor_bots():
    """Monitora status dos bots"""
    while True:
        try:
            await asyncio.sleep(30)  # Verificar a cada 30 segundos
            
            # Verificar bots ativos
            for token, bot_info in list(active_bots.items()):
                try:
                    # Testar conexão com timeout
                    await asyncio.wait_for(
                        bot_info['bot'].get_me(),
                        timeout=10.0
                    )
                    bot_info['last_heartbeat'] = datetime.now()
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Bot {token[:20]}... timeout na conexão")
                    bot_info['status'] = 'failed'
                except Exception as e:
                    logger.warning(f"Bot {token[:20]}... perdeu conexão")
                    bot_info['status'] = 'failed'
                    logger.error(f"Bot {token[:20]}... marcado como falhado")
            
            # Tentar reconectar bots falhados
            await retry_failed_bots()
            
            # Log de status
            active_count = sum(1 for info in active_bots.values() if info['status'] == 'active')
            failed_count = sum(1 for info in active_bots.values() if info['status'] == 'failed')
            # Status dos bots
            
        except Exception as e:
            logger.error(f"Erro no monitoramento: {e}")
            # Se houver erro crítico no monitoramento, aguardar antes de continuar
            await asyncio.sleep(60)

async def retry_failed_bots():
    """Tenta reconectar bots que falharam"""
    for token, bot_info in list(active_bots.items()):
        if bot_info['status'] == 'failed' and bot_info['retry_count'] < 3:
            # Tentando reconectar bot
            
            try:
                # Tentar inicializar novamente
                new_bot_info = await initialize_bot(token)
                
                if new_bot_info:
                    active_bots[token] = new_bot_info
                    event_logger.info(f"Bot reconectado: {token[:20]}...")
                    
                    # Registrar evento
                    add_event('INFO', f'Bot {token[:20]}... reconectado automaticamente', 'system')
                else:
                    bot_info['retry_count'] += 1
                    logger.error(f"Falha ao reconectar bot (tentativa {bot_info['retry_count']})")
                    
            except Exception as e:
                bot_info['retry_count'] += 1
                logger.error(f"Falha ao reconectar bot: {e}")

async def shutdown_all_bots():
    """Shutdown graceful de todos os bots"""
    event_logger.info("Iniciando shutdown graceful")
    
    try:
        # Cancelar todas as tasks ativas primeiro
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        if tasks:
            # Cancelando tasks ativas
            for task in tasks:
                task.cancel()
        
        # Shutdown das aplicações
        for token, bot_info in active_bots.items():
            if bot_info['status'] == 'active':
                try:
                    app = bot_info['application']
                    if hasattr(app, 'updater') and app.updater.running:
                        await app.updater.stop()
                    if hasattr(app, 'stop'):
                        await app.stop()
                    if hasattr(app, 'shutdown'):
                        await app.shutdown()
                except Exception as e:
                    logger.warning(f"Erro no shutdown do bot: {e}")
        
        event_logger.info("Shutdown graceful concluído")
        
    except Exception as e:
        logger.error(f"Erro durante shutdown: {e}")
    finally:
        active_bots.clear()
        # Lista de bots ativos limpa

async def shutdown_single_bot(bot_info):
    """Shutdown de um único bot"""
    try:
        token = bot_info['token']
        # Shutdown bot
        
        # Shutdown da aplicação
        await bot_info['application'].shutdown()
        
        # Bot shutdown concluído
        
    except Exception as e:
        logger.error(f"Erro no shutdown do bot: {e}")

async def start_all_bots():
    """Inicia todos os bots configurados"""
    event_logger.info("Iniciando sistema de múltiplos bots")
    
    # Filtrar apenas tokens válidos
    valid_tokens = [token for token in BOT_TOKENS if token and not token.startswith('SEU_TOKEN')]
    
    if not valid_tokens:
        logger.error("Nenhum token válido encontrado")
        return False
    
    # Inicializar bots em paralelo
    tasks = []
    for token in valid_tokens:
        task = initialize_bot(token)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Processar resultados
    for i, result in enumerate(results):
        if isinstance(result, dict) and result:
            token = valid_tokens[i]
            active_bots[token] = result
            # Bot adicionado à lista ativa
        else:
            token = valid_tokens[i]
            logger.error(f"Bot falhou na inicialização: {result}")
    
    event_logger.info(f"Sistema iniciado: {len(active_bots)} bots ativos")
    return len(active_bots) > 0


async def run_single_bot(token: str, bot_info: Dict) -> None:
    """Executa um único bot de forma assíncrona"""
    try:
        logger.info(f"🤖 Executando bot {token[:20]}...")
        
        app = bot_info['application']
        
        # Inicializar o bot
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        logger.info(f"✅ Bot {token[:20]}... iniciado com sucesso")
        
        # Manter o bot rodando até shutdown ser solicitado
        while not shutdown_requested:
            await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"❌ Erro no bot {token[:20]}...: {e}")
        bot_info['status'] = 'failed'
        raise e
    finally:
        # Shutdown limpo
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            logger.info(f"🔄 Bot {token[:20]}... finalizado")
        except Exception as shutdown_error:
            logger.warning(f"⚠️ Erro no shutdown do bot {token[:20]}...: {shutdown_error}")

async def run_all_bots():
    """Executa todos os bots em paralelo usando um único event loop"""
    if not active_bots:
        logger.error("Nenhum bot ativo para executar!")
        return False
    
    logger.info(f"Executando {len(active_bots)} bots em paralelo...")
    
    # Criar tasks para cada bot ativo
    tasks = []
    for token, bot_info in active_bots.items():
        if bot_info['status'] == 'active':
            task = asyncio.create_task(
                run_single_bot(token, bot_info),
                name=f"bot_{token[:10]}"
            )
            tasks.append(task)
            logger.info(f"✅ Task criada para bot {token[:20]}...")
    
    if not tasks:
        logger.error("Nenhuma task criada!")
        return False
    
    try:
        # Executar todos os bots em paralelo
        logger.info(f"🚀 Iniciando {len(tasks)} bots simultaneamente...")
        
        # Aguardar até que shutdown seja solicitado ou todos os bots falhem
        while not shutdown_requested and any(not task.done() for task in tasks):
            await asyncio.sleep(1)
        
        if shutdown_requested:
            logger.info("🔄 Shutdown solicitado - cancelando tasks...")
        
    except KeyboardInterrupt:
        logger.info("🔄 Interrupção pelo usuário detectada")
    except Exception as e:
        logger.error(f"❌ Erro na execução dos bots: {e}")
    finally:
        # Cancelar todas as tasks pendentes
        for task in tasks:
            if not task.done():
                task.cancel()
                logger.info(f"🔄 Task {task.get_name()} cancelada")
    
    return True

async def supervise_bots():
    """Supervisiona os bots e reinicia em caso de falha"""
    while not shutdown_requested:
        try:
            event_logger.info("Iniciando supervisão dos bots")
            await run_all_bots()
            
        except Exception as e:
            if shutdown_requested:
                event_logger.info("Shutdown solicitado - parando supervisão")
                break
            logger.error(f"Erro na supervisão: {e}")
            event_logger.info("Reiniciando bots em 5 segundos")
            await asyncio.sleep(5)
    
    event_logger.info("Supervisão finalizada")

async def main():
    """Função principal - Sistema Multi-Bot Assíncrono"""
    print("="*70)
    print("🤖 SISTEMA MULTI-BOT TELEGRAM - ALTO TRÁFEGO")
    print("="*70)
    print("✅ Múltiplos bots rodando simultaneamente")
    print("✅ Troca automática quando um bot cai")
    print("✅ Distribuição de carga entre bots")
    print("✅ Monitoramento em tempo real")
    print("="*70)
    
    # Verificar se há tokens válidos
    valid_tokens = [token for token in BOT_TOKENS if token and not token.startswith('SEU_TOKEN')]
    
    if not valid_tokens:
        logger.error("❌ Nenhum token válido encontrado!")
        logger.info("💡 Adicione tokens válidos na lista BOT_TOKENS")
        return
    
    logger.info(f"📋 {len(valid_tokens)} token(s) válido(s) encontrado(s)")
    
    # Inicializar sistema de gateways
    initialize_gateways()
    
    # Inicializar todos os bots
    success = await start_all_bots()
    
    if not success:
        logger.error("❌ Nenhum bot pôde ser inicializado!")
        return
    
    logger.info(f"🚀 Sistema iniciado com {len(active_bots)} bot(s) ativo(s)")
    
    # Exibir status dos bots
    print("\n📊 STATUS DOS BOTS:")
    print("-" * 50)
    for token, bot_info in active_bots.items():
        status = "✅ Ativo" if bot_info['status'] == 'active' else "❌ Falhado"
        print(f"{status} - {token[:20]}...")
    
    # Exibir status dos gateways
    print("\n💳 STATUS DOS GATEWAYS:")
    print("-" * 50)
    for gateway_id, status in gateway_status.items():
        gateway_name = GATEWAYS[gateway_id]['name']
        
        if status['status'] == 'active':
            status_icon = "✅ Ativo"
            status_text = "Funcionando"
        else:
            status_icon = "❌ Falhado"
            status_text = status.get('last_error', 'Erro desconhecido')
        
        success_rate = "N/A"
        if status['total_requests'] > 0:
            success_rate = f"{(status['successful_requests'] / status['total_requests'] * 100):.1f}%"
        
        print(f"{status_icon} - {gateway_name}")
        print(f"    Status: {status_text}")
        print(f"    Sucesso: {success_rate}")
        print()
    
    print("\n🔄 Sistema rodando... Pressione Ctrl+C para parar")
    
    # Executar supervisão dos bots
    try:
        # Criar tasks para execução paralela
        tasks = []
        
        # Task 1: Supervisão dos bots
        supervise_task = asyncio.create_task(supervise_bots())
        tasks.append(supervise_task)
        
        # Task 2: Scheduler de downsells
        scheduler_task = asyncio.create_task(start_downsell_scheduler())
        tasks.append(scheduler_task)
        
        logger.info("🚀 Sistema iniciado com scheduler de downsells!")
        
        # Aguardar todas as tasks
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except KeyboardInterrupt:
        logger.info("🔄 Interrupção pelo usuário detectada")
    except Exception as e:
        logger.error(f"❌ Erro na execução: {e}")
    finally:
        logger.info("🔄 Iniciando shutdown...")
        await shutdown_all_bots()

def run_system():
    """Função wrapper para executar o sistema"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sistema interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        print(f"❌ Erro crítico: {e}")

if __name__ == '__main__':
    run_system()