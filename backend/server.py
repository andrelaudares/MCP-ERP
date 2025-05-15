import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import httpx # Adicionado para Evolution API
import json # Adicionado para Evolution API
from typing import Optional, Dict, Any, List # Adicionado List
from pydantic import BaseModel # Adicionado BaseModel

# Carregar variáveis de ambiente do .env
load_dotenv()

# Importar o executor do agente
from backend.agent import run_agent # mcp não é mais passado

# Configurações da Evolution API (do .env)
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME") # Adicionado para nome da instância

# LOGS ADICIONADOS PARA DEBUG
print(f"[ENV DEBUG] EVOLUTION_API_URL lido: '{EVOLUTION_API_URL}' (Tipo: {type(EVOLUTION_API_URL)})")
print(f"[ENV DEBUG] EVOLUTION_API_KEY lido: '{EVOLUTION_API_KEY}' (Tipo: {type(EVOLUTION_API_KEY)})")
print(f"[ENV DEBUG] EVOLUTION_INSTANCE_NAME lido: '{EVOLUTION_INSTANCE_NAME}' (Tipo: {type(EVOLUTION_INSTANCE_NAME)})")

if not all([EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_NAME]):
    print("ALERTA: Variáveis da Evolution API não estão completamente configuradas no .env")
    # Você pode querer levantar um erro aqui se elas forem estritamente necessárias para iniciar
    # raise ValueError("Variáveis da Evolution API não estão completamente configuradas.")

# --- Modelos Pydantic para o payload do Webhook ---
class WebhookKey(BaseModel):
    remoteJid: str
    fromMe: bool
    id: str

class WebhookMessageContent(BaseModel):
    conversation: Optional[str] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None 
    # Adicione outros tipos de mensagem se necessário (imageMessage, videoMessage, etc.)

class WebhookData(BaseModel):
    key: WebhookKey
    message: Optional[WebhookMessageContent] = None # Tornar opcional, pois pode não estar presente em todos os eventos
    pushName: Optional[str] = None
    timestamp: Optional[int] = None
    messageType: Optional[str] = None

class EvolutionWebhookPayload(BaseModel):
    event: str
    instance: Optional[str] = None
    data: Optional[WebhookData] = None # Tornar opcional, pois pode não estar presente em todos os eventos
    webhook_id: Optional[str] = None
# --- Fim dos Modelos Pydantic ---

# --- Modelo Pydantic para a rota de teste do agente ---
class TestAgentQuery(BaseModel):
    user_query: str
    chat_history: Optional[List[Dict[str, str]]] = None
# --- Fim do Modelo Pydantic para Teste ---

app = FastAPI(
    title="MCP-ERP Evolution API Webhook",
    description="Recebe webhooks da Evolution API e processa mensagens com um agente PydanticAI. Inclui uma rota de teste para o agente.", # Descrição atualizada
    version="0.2.2" # Version bump
)

# Simples armazenamento em memória para histórico de chat (para demonstração)
# Em produção, use um banco de dados como Redis ou similar.
chat_histories: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY_LENGTH = 10 # Manter as últimas 10 trocas por conversa

async def send_evolution_api_message(remote_jid: str, text: str):
    """Envia uma mensagem de texto para um JID usando a Evolution API."""
    if not all([EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_NAME]):
        print("Erro: Configurações da Evolution API incompletas. Não é possível enviar mensagem.")
        return None # Ou levantar uma exceção

    send_message_url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
    payload = {
        "number": remote_jid,
        "text": text,
        "options": {
            "delay": 1200,
            "presence": "composing", # "unavailable" (parar de digitar), "available" (online) ou "composing" (digitando)
        }
    }
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            print(f"Enviando para Evolution API: URL={send_message_url}, JID={remote_jid}, Texto='{text[:50]}...'") # Log reduzido
            response = await client.post(send_message_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status() # Levanta exceção para respostas 4xx/5xx
            print(f"Resposta da Evolution API (envio): {response.status_code}, {response.text[:100]}") # Log reduzido
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Erro HTTP ao enviar mensagem para Evolution API: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Erro de requisição ao enviar mensagem para Evolution API: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao enviar mensagem para Evolution API: {e}")
            return None

@app.post("/webhook/evolution")
async def receive_webhook(payload: EvolutionWebhookPayload):
    """
    Endpoint para receber webhooks da Evolution API.
    O corpo da requisição é validado pelo modelo EvolutionWebhookPayload.
    """
    try:
        # O payload já foi validado e parseado pelo FastAPI graças ao type hint EvolutionWebhookPayload
        print(f"Webhook recebido (validado por Pydantic): {payload.model_dump_json(indent=2)[:500]}...")

        if payload.event == "messages.upsert" and payload.data and payload.data.message:
            data = payload.data
            message_info = data.message # Acesso direto ao modelo
            
            user_message_text = None
            if message_info.conversation:
                user_message_text = message_info.conversation
            elif message_info.extendedTextMessage and message_info.extendedTextMessage.get("text"):
                user_message_text = message_info.extendedTextMessage["text"]
            # O fallback para mensagem citada foi removido para simplificar,
            # pois a estrutura exata de 'messageContextInfo' não foi modelada.
            # Pode ser adicionado depois se necessário.

            sender_jid = data.key.remoteJid
            is_from_me = data.key.fromMe

            if is_from_me or not user_message_text or not sender_jid:
                print("Mensagem ignorada (própria, vazia ou sem JID).")
                return JSONResponse(content={"status": "message ignored"}, status_code=200)

            print(f"Mensagem de: {sender_jid}, Texto: '{user_message_text}'")

            # Gerenciar histórico de chat
            if sender_jid not in chat_histories:
                chat_histories[sender_jid] = []
            
            current_chat_history = chat_histories[sender_jid]
            current_chat_history.append({"role": "user", "content": user_message_text})
            if len(current_chat_history) > MAX_HISTORY_LENGTH * 2: # *2 para pares user/assistant
                current_chat_history = current_chat_history[-MAX_HISTORY_LENGTH*2:]
            chat_histories[sender_jid] = current_chat_history # Atualiza o histórico

            # Passar a mensagem do usuário e o histórico para o agente
            # A instância `mcp` não é mais necessária aqui
            agent_response_text = await run_agent(user_message_text, chat_history=current_chat_history)
            print(f"Resposta do agente para {sender_jid}: '{agent_response_text}'")

            # Adicionar resposta do agente ao histórico
            current_chat_history.append({"role": "assistant", "content": agent_response_text})
            if len(current_chat_history) > MAX_HISTORY_LENGTH * 2:
                current_chat_history = current_chat_history[-MAX_HISTORY_LENGTH*2:]
            chat_histories[sender_jid] = current_chat_history

            # Enviar a resposta do agente de volta via Evolution API
            if agent_response_text:
                await send_evolution_api_message(sender_jid, agent_response_text)
            
            return JSONResponse(content={"status": "message processed"}, status_code=200)
        else:
            event_name = payload.event if payload else "N/A"
            print(f"Webhook ignorado (evento não é messages.upsert, sem data ou sem message): {event_name}")
            return JSONResponse(content={"status": "event ignored"}, status_code=200)

    except HTTPException: # Repassar HTTPExceptions levantadas intencionalmente
        raise
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        # Melhor logar o traceback completo para depuração interna
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

# --- Nova Rota para Testar o Agente Diretamente ---
@app.post("/test_agent", response_model=str) # response_model=str para indicar que a resposta é uma string simples
async def test_agent_endpoint(query: TestAgentQuery):
    """
    Endpoint para testar a lógica do agente PydanticAI diretamente.
    Recebe uma `user_query` e um `chat_history` opcional.
    Retorna a resposta textual do agente.
    """
    try:
        print(f"[Test Agent Endpoint] Recebida query: {query.user_query}")
        if query.chat_history:
            print(f"[Test Agent Endpoint] Histórico: {query.chat_history}")
        
        agent_response = await run_agent(query.user_query, chat_history=query.chat_history)
        print(f"[Test Agent Endpoint] Resposta do agente: {agent_response}")
        return agent_response
    except Exception as e:
        print(f"[Test Agent Endpoint] Erro: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao testar o agente: {str(e)}")
# --- Fim da Nova Rota de Teste ---

@app.get("/")
async def read_root():
    return {"message": "MCP-ERP Evolution API Webhook está online."}

# Para rodar localmente com Uvicorn:
# uvicorn backend.server:app --reload --port 8000 