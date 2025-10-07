#!/usr/bin/env python3
"""
Bot Telegram Simplificado - Apenas Paradise
"""

import logging
import os
import time
import requests
import uuid
import asyncio
import json
import re
from datetime import datetime
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_simple.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configurações Paradise
PARADISE_API_KEY = 'sk_c3728b109649c7ab1d4e19a61189dbb2b07161d6955b8f20b6023c55b8a9e722'
PARADISE_BASE_URL = 'https://multi.paradisepags.com/api/v1'
PARADISE_PRODUCT_HASH = 'prod_6c60b3dd3ae2c63e'

# Token do bot (usar apenas um para teste)
BOT_TOKEN = '8306671959:AAHeqNjcC9C3MpAVrCXRyer62vOyfLm_0MM'

class ParadiseGateway:
    """Integração com Paradise"""
    
    def __init__(self):
        self.api_key = PARADISE_API_KEY
        self.base_url = PARADISE_BASE_URL
        self.product_hash = PARADISE_PRODUCT_HASH
        self.timeout = 30
        
    def _get_headers(self):
        """Retorna headers para requisições Paradise"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': self.api_key
        }
    
    async def create_payment(self, amount, description, customer_data, user_id, checkout_url=None):
        """Cria um pagamento PIX via Paradise"""
        try:
            logger.info(f"Criando pagamento Paradise: R$ {amount}")
            
            # Gerar referência única
            reference = f'BOT-{user_id}-{int(time.time())}'
            
            # Preparar dados do cliente
            clean_document = re.sub(r'\D', '', customer_data.get('document', '12345678900'))
            clean_phone = re.sub(r'\D', '', customer_data.get('phone', '11999999999'))
            
            # Payload para Paradise API
            payload = {
                "amount": round(amount * 100),  # Paradise espera em centavos
                "description": description,
                "reference": reference,
                "checkoutUrl": checkout_url or '',
                "productHash": self.product_hash,
                "orderbump": [],
                "customer": {
                    'name': customer_data.get('name', f'Cliente {user_id}'),
                    'email': customer_data.get('email', f'cliente{user_id}@email.com'),
                    'document': clean_document,
                    'phone': clean_phone
                },
                "address": {
                    "street": "Rua do Produto Digital",
                    "number": "0",
                    "neighborhood": "Internet",
                    "city": "Brasil",
                    "state": "BR",
                    "zipcode": "00000000",
                    "complement": "N/A"
                }
            }
            
            # Fazer requisição para Paradise
            response = requests.post(
                f"{self.base_url}/transaction.php",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            logger.info(f"Paradise Response Status: {response.status_code}")
            
            if response.status_code >= 200 and response.status_code < 300:
                response_data = response.json()
                logger.info(f"Paradise Response Data: {response_data}")
                
                # Extrair QR Code
                qr_code = (response_data.get('qr_code') or 
                          response_data.get('pix_qr_code'))
                
                if qr_code:
                    pix_data = {
                        'id': response_data.get('id', reference),
                        'qr_code': qr_code,
                        'expires_at': response_data.get('expires_at'),
                        'amount': amount,
                        'reference': reference,
                        'gateway': 'paradise'
                    }
                    
                    logger.info(f"Paradise PIX criado com sucesso: {reference}")
                    return pix_data
                else:
                    logger.error("Paradise retornou sem QR Code")
                    return None
            else:
                logger.error(f"Paradise API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro Paradise: {e}")
            return None

# Instância global do Paradise
paradise = ParadiseGateway()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /start"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"/start executado por {user.first_name} (ID: {user_id})")
    
    # Mensagem inicial
    start_message = """Bem-vindo ao Bot Paradise!

Este bot usa Paradise como gateway principal para pagamentos PIX.

Clique no botão abaixo para testar:"""
    
    # Botões de teste
    keyboard = [
        [InlineKeyboardButton("Teste PIX R$ 19.97", callback_data="teste_1997")],
        [InlineKeyboardButton("Teste PIX R$ 14.97", callback_data="teste_1497")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(start_message, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botões"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Botão clicado: {query.data} por {user.first_name} (ID: {user_id})")
    
    if query.data == "teste_1997":
        await create_payment(query, 19.97, "TESTE VITALICIO", user_id)
    elif query.data == "teste_1497":
        await create_payment(query, 14.97, "TESTE MENSAL", user_id)

async def create_payment(query, amount, description, user_id):
    """Cria pagamento PIX via Paradise"""
    try:
        logger.info(f"INICIANDO CRIAÇÃO DE PAGAMENTO")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Amount: R$ {amount}")
        logger.info(f"Description: {description}")
        
        # Dados do cliente
        customer_data = {
            "name": query.from_user.first_name or f"Cliente {user_id}",
            "email": f"cliente{user_id}@example.com",
            "document": "12345678900",
            "phone": "11999999999"
        }
        
        # Criar pagamento via Paradise
        pix_data = await paradise.create_payment(
            amount=amount,
            description=description,
            customer_data=customer_data,
            user_id=user_id,
            checkout_url="https://oacessoliberado.shop/vip2"
        )
        
        if pix_data and pix_data.get('qr_code'):
            # Sucesso! Enviar PIX
            pix_code = pix_data.get('qr_code')
            
            # Mensagem do PIX
            pix_message = f"""PIX GERADO COM SUCESSO!

<pre>{pix_code}</pre>

Toque no codigo acima para copia-lo facilmente

Apos o pagamento, clique no botao abaixo para verificar:"""
            
            # Botão para verificar pagamento
            keyboard = [
                [InlineKeyboardButton("Verificar Pagamento", callback_data=f"verificar_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Enviar mensagem
            await query.message.reply_text(pix_message, reply_markup=reply_markup, parse_mode='HTML')
            logger.info(f"PIX enviado via Paradise")
            
        else:
            logger.error("Falha ao criar PIX via Paradise")
            await query.message.reply_text("ERRO: Falha ao gerar PIX. Tente novamente.")
        
    except Exception as e:
        logger.error(f"ERRO na create_payment: {e}")
        await query.message.reply_text("ERRO: Sistema temporariamente indisponível.")

async def main():
    """Função principal"""
    print("="*60)
    print("BOT TELEGRAM SIMPLIFICADO - PARADISE ONLY")
    print("="*60)
    
    # Criar aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Iniciar bot
    logger.info("Bot iniciado com sucesso")
    print("Bot rodando... Pressione Ctrl+C para parar")
    
    # Executar
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
