# Bot Telegram com Integração Paradise

## 🚀 Sobre o Projeto

Bot do Telegram com sistema multi-bot para alto tráfego, integrado com **Paradise** como gateway principal de pagamentos PIX.

## ✨ Funcionalidades

- **Sistema Multi-Bot**: Suporte a múltiplos bots simultaneamente
- **Gateway Paradise**: Integração principal com Paradise para PIX
- **Fallback Automático**: PushynPay e SyncPay como backup
- **Webhooks**: Confirmação instantânea de pagamentos
- **Orderbumps**: Sistema de upsells integrado
- **Dashboard**: Monitoramento em tempo real

## 🔧 Arquivos Principais

- `bot.py` - Bot principal com integração Paradise
- `shared_data.py` - Sistema de dados compartilhados
- `requirements.txt` - Dependências Python
- `start_bot.bat` - Script de inicialização Windows
- `index.php` - Referência da integração Paradise
- `flix_template.json` - Template do checkout Paradise
- `bot_simple.py` - Versão simplificada para testes

## 🚀 Como Usar

1. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar tokens** no `bot.py`:
   - Tokens dos bots Telegram
   - API Key do Paradise
   - Configurações dos gateways

3. **Executar o bot**:
   ```bash
   python bot.py
   ```
   ou
   ```bash
   start_bot.bat
   ```

## 🔑 Configurações Paradise

- **API Key**: `sk_c3728b109649c7ab1d4e19a61189dbb2b07161d6955b8a9e722`
- **Base URL**: `https://multi.paradisepags.com/api/v1`
- **Product Hash**: `prod_6c60b3dd3ae2c63e`

## 📊 Sistema de Pagamentos

1. **Paradise** (Principal) - PIX automático
2. **PushynPay** (Fallback 1) - PIX backup
3. **SyncPay** (Fallback 2) - PIX backup

## 🎯 Funcionalidades Avançadas

- **Webhooks Paradise**: Confirmação instantânea
- **Rate Limiting**: Proteção contra spam
- **Logs Detalhados**: Monitoramento completo
- **Multi-tenant**: Suporte a múltiplos produtos
- **Orderbumps**: Sistema de upsells

## 📝 Logs

- `bot.log` - Logs gerais do sistema
- `events.log` - Eventos importantes

## 🔒 Segurança

- Validação de webhooks
- Rate limiting por usuário
- Logs de auditoria
- Fallback automático

---

**Desenvolvido com integração Paradise como gateway principal**
