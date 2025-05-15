import logging # LOGGING ADICIONADO
logging.basicConfig(level=logging.DEBUG) # LOGGING ADICIONADO

import os
from dotenv import load_dotenv
# from pydantic_ai import Agent # Alterado de PydanticAI para Agent # Linha duplicada comentada
# from pydantic_ai.llm.gemini import GeminiModel # REMOVIDO
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any # Adicionado Any

# Importar a lógica real da API Omie
from backend.omie_api import encontrar_pedidos_cliente, listar_clientes_omie
# Importar classes específicas para configuração explícita do modelo
from pydantic_ai import Agent # Garantir que Agent está importado aqui
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
# from pydantic_ai.exceptions import ModelError, ModelHTTPError # REMOVIDO

load_dotenv()

# Configurar o cliente LLM (Gemini)
# Certifique-se de que a variável de ambiente GEMINI_API_KEY está definida
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("A variável de ambiente GEMINI_API_KEY não está definida.")

# Instanciação explícita do modelo e provedor Gemini
gemini_llm = GeminiModel(
    model_name='gemini-2.0-flash',  # MUDAR PARA 2.0-FLASH COM PROMPT COMPLETO
    provider=GoogleGLAProvider(api_key=GEMINI_API_KEY)
)

class ItemPedido(BaseModel):
    produto: Optional[str] = Field(None, description="Nome ou código do produto no pedido.")
    quantidade: Optional[float] = Field(None, description="Quantidade do produto.")
    valor_unitario: Optional[float] = Field(None, description="Valor unitário do produto.")
    valor_total: Optional[float] = Field(None, description="Valor total para este item (quantidade * valor_unitário).")

class PedidoCliente(BaseModel):
    id_pedido: Optional[str] = Field(None, description="Identificador único do pedido.")
    data_previsao: Optional[str] = Field(None, description="Data de previsão de entrega do pedido (formato dd/mm/aaaa).")
    valor_total_pedido: Optional[float] = Field(None, description="Valor total do pedido.")
    itens: Optional[List[ItemPedido]] = Field(default_factory=list, description="Lista de itens do pedido.")
    # Adicione outros campos relevantes do pedido que você deseja que o agente conheça

class RespostaBuscaPedidos(BaseModel):
    pedido: Optional[PedidoCliente] = Field(None, description="O último pedido encontrado para o cliente.")
    pedidos: Optional[List[PedidoCliente]] = Field(default_factory=list, description="Lista de todos os pedidos encontrados, se solicitado.")
    mensagem_erro: Optional[str] = Field(None, description="Mensagem de erro, se houver.")
    detalhes_cliente: Optional[Dict[str, Any]] = Field(None, description="Detalhes do cliente encontrado.")

# Classe BuscarIdClienteTool COMENTADA - substituída pela função abaixo
# class BuscarIdClienteTool(BaseModel):
#     """
#     [TESTE EXTREMO] Uma ferramenta de teste que não recebe argumentos e deve ser sempre chamada quando 
#     o usuário pedir para encontrar um ID de cliente.
#     Output: Um dicionário contendo {'id_cliente': 'EXTREME_TEST_ID_789'}
#     """
#     # SEM ARGUMENTOS AQUI POR ENQUANTO
#     # identificador_cliente: str = Field(description="Nome, nome fantasia ou CNPJ do cliente a ser buscado para obter seu ID numérico.")
# 
#     async def run(self) -> Dict[str, Any]:
#         print("[BuscarIdClienteTool EXTREME TEST] MÉTODO RUN INVOCADO SEM ARGUMENTOS")
#         return {"id_cliente": "EXTREME_TEST_ID_789"}

# FERRAMENTA COMO FUNÇÃO PYTHON, AGORA COM LÓGICA REAL E ARGUMENTO
async def buscar_id_cliente_tool_func(identificador_cliente: str) -> Dict[str, Any]:
    """
    Converte um identificador de cliente (nome, nome fantasia ou CNPJ) em um ID numérico de cliente Omie.
    Use esta ferramenta SEMPRE que o usuário fornecer um nome ou CNPJ e você precisar do ID numérico do cliente para usar com outras ferramentas.
    Input: Nome, nome fantasia ou CNPJ do cliente. Ex: "Padaria Central" ou "12.345.678/0001-99".
    Output: Um dicionário contendo {'id_cliente': <ID_NUMERICO_DO_CLIENTE>} se encontrado, 
            ou {'error': '<mensagem_de_erro_especifica>'} se não encontrado ou ocorrer um erro.
    """
    print(f"[buscar_id_cliente_tool_func] FUNÇÃO INVOCADA com identificador_cliente: '{identificador_cliente}'")
    try:
        resultado = await listar_clientes_omie(identificador_cliente)
        print(f"[buscar_id_cliente_tool_func] Resultado da API listar_clientes_omie para '{identificador_cliente}': {resultado}")

        if resultado and not resultado.get("error") and resultado.get("clientes_cadastro"):
            if not resultado["clientes_cadastro"]:
                msg_erro = f"Nenhum cliente encontrado com o identificador: '{identificador_cliente}'."
                print(f"[buscar_id_cliente_tool_func] {msg_erro}")
                return {"error": msg_erro}

            primeiro_cliente = resultado["clientes_cadastro"][0]
            id_cliente_omie = primeiro_cliente.get("codigo_cliente_omie") # Corrigido para codigo_cliente_omie
            # id_cliente = primeiro_cliente.get("codigo_cliente") # Linha original comentada
            nome_cliente_encontrado = primeiro_cliente.get("nome_fantasia") or primeiro_cliente.get("razao_social")

            if id_cliente_omie:
                retorno_sucesso = {"id_cliente": id_cliente_omie}
                print(f"[buscar_id_cliente_tool_func] Cliente encontrado: ID {id_cliente_omie}, Nome: {nome_cliente_encontrado} para identificador '{identificador_cliente}'. Retornando: {retorno_sucesso}")
                return retorno_sucesso
            else:
                msg_erro = f"ID do cliente (codigo_cliente_omie) não encontrado nos dados do cliente para o identificador '{identificador_cliente}'. Detalhes: {primeiro_cliente}"
                print(f"[buscar_id_cliente_tool_func] {msg_erro}")
                return {"error": msg_erro}
        elif resultado and resultado.get("error"):
            msg_erro_api = resultado.get("details", "Erro não detalhado pela API Omie.")
            msg_erro = f"Erro retornado pela API Omie ao buscar cliente '{identificador_cliente}': {msg_erro_api}"
            print(f"[buscar_id_cliente_tool_func] {msg_erro}")
            return {"error": msg_erro}
        else:
            msg_erro = f"Resposta inesperada ou nenhum cliente encontrado na API Omie para o identificador: '{identificador_cliente}'. Resposta da API: {resultado}"
            print(f"[buscar_id_cliente_tool_func] {msg_erro}")
            return {"error": msg_erro}
    except Exception as e:
        msg_erro = f"Erro inesperado no sistema ao tentar buscar o ID do cliente para '{identificador_cliente}': {str(e)}"
        print(f"[buscar_id_cliente_tool_func] ERRO CRÍTICO NA FERRAMENTA: {msg_erro}")
        import traceback
        traceback.print_exc()
        return {"error": msg_erro}

async def buscar_pedidos_cliente_tool_func(id_cliente: int) -> Dict[str, Any]:
    """
    Busca o último pedido de um cliente na API Omie usando o ID NUMÉRICO OBRIGATÓRIO do cliente.
    NÃO use esta ferramenta se você não tiver o ID numérico do cliente. Obtenha-o primeiro com buscar_id_cliente_tool_func.
    Input: ID numérico do cliente. Ex: 12345678.
    Output: Dicionário com detalhes do último pedido ou uma mensagem de erro.
    Exemplo de SUCESSO:
    {'pedido': {'id_pedido': '123', 'data_previsao': '25/12/2023', 'valor_total_pedido': 150.75, 'itens': [{'produto': 'Produto A', 'quantidade': 2, 'valor_unitario': 50.00, 'valor_total': 100.00}]}}
    Exemplo de ERRO ou NENHUM PEDIDO:
    {'error': 'Nenhum pedido encontrado para o cliente com ID 12345.'} ou {'error': 'Erro da API ao buscar pedidos: <detalhe do erro>'}
    """
    print(f"[buscar_pedidos_cliente_tool_func] FUNÇÃO INVOCADA com id_cliente: {id_cliente}")
    try:
        resultado = await encontrar_pedidos_cliente(id_cliente, apenas_ultimo_pedido=True) # apenas_ultimo_pedido=True por padrão
        print(f"[buscar_pedidos_cliente_tool_func] Resultado da API encontrar_pedidos_cliente para ID {id_cliente}: {resultado}")

        if resultado and not resultado.get("error"):
            if resultado.get('pedido') is not None or isinstance(resultado.get('pedidos'), list):
                if resultado.get('pedido') is None and isinstance(resultado.get('pedidos'), list) and not resultado.get('pedidos'):
                    msg_info = f"Nenhum pedido encontrado para o cliente com ID {id_cliente}."
                    print(f"[buscar_pedidos_cliente_tool_func] {msg_info}")
                    return {"error": msg_info}
                print(f"[buscar_pedidos_cliente_tool_func] Pedido(s) encontrado(s) para ID cliente: {id_cliente}. Retornando: {resultado}")
                return resultado # Retorna o dicionário completo como está em encontrar_pedidos_cliente
            else:
                msg_erro = f"Formato de resposta inesperado (sem 'pedido' ou 'pedidos' válidos) da API Omie para ID cliente: {id_cliente}. Resposta: {resultado}"
                print(f"[buscar_pedidos_cliente_tool_func] {msg_erro}")
                return {"error": msg_erro}
        elif resultado and resultado.get("error"):
            msg_erro_api = resultado.get("details", "Erro não detalhado pela API Omie.")
            msg_erro = f"Erro retornado pela API Omie ao buscar pedidos para ID {id_cliente}: {msg_erro_api}"
            print(f"[buscar_pedidos_cliente_tool_func] {msg_erro}")
            return {"error": msg_erro}
        else:
            msg_erro = f"Resposta inesperada ou vazia da API Omie ao buscar pedidos para ID cliente: {id_cliente}. Resposta: {resultado}"
            print(f"[buscar_pedidos_cliente_tool_func] {msg_erro}")
            return {"error": msg_erro}
    except Exception as e:
        msg_erro = f"Erro inesperado no sistema ao tentar buscar pedidos para ID {id_cliente}: {str(e)}"
        print(f"[buscar_pedidos_cliente_tool_func] ERRO CRÍTICO NA FERRAMENTA: {msg_erro}")
        import traceback
        traceback.print_exc()
        return {"error": msg_erro}

# SYSTEM_PROMPT principal, agora instruindo sobre ambas as funções
SYSTEM_PROMPT = """
You are a helpful assistant specialized in retrieving customer and order information from an Omie ERP system via provided tools.

Available Tools:
1. `buscar_id_cliente_tool_func(identificador_cliente: str)`:
   - Use this tool when the user provides a customer's CNPJ, name, or trade name and you need their numerical ID.
   - Input: The customer's CNPJ (e.g., "12.345.678/0001-99"), name, or trade name (e.g., "Padaria Central") as a string.
   - Output: A dictionary like `{{"id_cliente": <NUMERICAL_ID>}}` on success, or `{{"error": "<message>"}}` on failure.

2. `buscar_pedidos_cliente_tool_func(id_cliente: int)`:
   - Use this tool ONLY when you ALREADY HAVE the customer's NUMERICAL ID (obtained via `buscar_id_cliente_tool_func` if necessary).
   - This tool finds the LATEST order for the given numerical customer ID.
   - Input: The customer's numerical ID (e.g., 12345678) as an integer.
   - Output: A dictionary containing details of the latest order (e.g., `{{"pedido": {{...}} }}`) or an error (e.g., `{{"error": "<message>"}}`).

Workflow:
- If the user asks for order details (like last order, specific product in an order, total spent) using a CNPJ or name:
  1. FIRST, use `buscar_id_cliente_tool_func` with the provided CNPJ/name to get the numerical `id_cliente`.
  2. If `buscar_id_cliente_tool_func` returns an error or no ID, inform the user and STOP.
  3. If `buscar_id_cliente_tool_func` returns an `id_cliente`, THEN use `buscar_pedidos_cliente_tool_func` with this `id_cliente`.
  4. Based on the result from `buscar_pedidos_cliente_tool_func`, answer the user's original question about the order.

- If the user asks ONLY for the customer ID using a CNPJ or name:
  1. Use `buscar_id_cliente_tool_func`.
  2. Report the ID or error to the user.

- If the user asks for order details and provides a NUMERICAL customer ID directly:
  1. Use `buscar_pedidos_cliente_tool_func` directly with the provided numerical ID.
  2. Report the order details or error to the user.

General Instructions:
- Always confirm which tool you are using and what parameters you are passing, if any.
- If a tool returns an error, report the error clearly to the user.
- If you need to use `buscar_id_cliente_tool_func` first, tell the user you are doing that to get the ID, then proceed to use `buscar_pedidos_cliente_tool_func` if successful.
- Be clear about what information you found or could not find.
- Ask for clarification if the user's request is ambiguous.
"""

# Usando a instância explícita do modelo Gemini
print("[Agent Setup] Verificando funções-ferramenta:")
# print(f"[Agent Setup] BuscarIdClienteTool: {BuscarIdClienteTool}") # Comentado 
print(f"[Agent Setup] buscar_id_cliente_tool_func: {buscar_id_cliente_tool_func}") 
print(f"[Agent Setup] buscar_pedidos_cliente_tool_func: {buscar_pedidos_cliente_tool_func}")
# print(f"[Agent Setup] EchoTool: {EchoTool}") # Comentado para teste
print(f"[Agent Setup] GEMINI_API_KEY está configurada: {bool(GEMINI_API_KEY)}") 
print(f"[Agent Setup] Instância gemini_llm: {gemini_llm}") 

# ai_client para TESTE com buscar_id_cliente_tool_func (com argumento)
ai_client = Agent(
    model=gemini_llm,
    tools=[buscar_id_cliente_tool_func, buscar_pedidos_cliente_tool_func],
    system_prompt=SYSTEM_PROMPT,
    verbose=True
)
print("[Agent Setup] Instância do Agent (com ambas as funções-ferramenta e SYSTEM_PROMPT principal) criada.")


async def run_agent(user_query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Executa o agente PydanticAI com a consulta do usuário e histórico de chat."""
    print(f"--- NOVA EXECUÇÃO DO AGENTE ---")
    print(f"[Agent] Query Recebida: '{user_query}'")
    
    current_conversation_for_run = []
    if chat_history:
        print(f"[Agent] Histórico do Chat Fornecido: {chat_history}")
        current_conversation_for_run.extend(chat_history)
    current_conversation_for_run.append({'role': 'user', 'content': user_query})
        
    print(f"[Agent] Input Completo para ai_client.run: {current_conversation_for_run}")
    
    try:
        print("[Agent] ANTES de ai_client.run()")
        agent_result = await ai_client.run(user_query) 
        print(f"[Agent] DEPOIS de ai_client.run(). Resultado bruto: {agent_result}")
        
        response_output = ""
        if hasattr(agent_result, 'output') and isinstance(agent_result.output, str):
            response_output = agent_result.output
        elif isinstance(agent_result, str):
            response_output = agent_result
        else:
            response_output = str(agent_result) 

        print(f"[Agent] Output Final para Resposta: {response_output}")
        return response_output
    except Exception as e:
        print(f"[Agent] ERRO CRÍTICO ao executar ai_client.run() ou processar seu resultado: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Desculpe, ocorreu um erro interno grave ao processar sua solicitação. Detalhe: {type(e).__name__}"

if __name__ == "__main__":
    import asyncio

    async def test_agent_flow():
        # Teste 1: CNPJ que deve encontrar cliente e pedido
        cnpj_valido_com_pedidos = "14.926.337/0001-39" # CNPJ da Aqualax
        query1 = f"Qual foi o último pedido do cliente com CNPJ {cnpj_valido_com_pedidos}?"
        print(f"--- Teste 1: {query1} ---")
        resposta1 = await run_agent(query1)
        print(f"Resposta do Agente 1: {resposta1}\n")

        # Teste 2: Apenas pedir o ID
        query2 = f"Qual o ID do cliente Aqualax Comercio de Banheiras?"
        print(f"--- Teste 2: {query2} ---")
        resposta2 = await run_agent(query2)
        print(f"Resposta do Agente 2: {resposta2}\n")

        # Teste 3: CNPJ que não existe (ou que você saiba que não tem pedidos)
        cnpj_invalido = "00.000.000/0000-00"
        query3 = f"Qual o último pedido do cliente com CNPJ {cnpj_invalido}?"
        print(f"--- Teste 3: {query3} ---")
        resposta3 = await run_agent(query3)
        print(f"Resposta do Agente 3: {resposta3}\n")

    asyncio.run(test_agent_flow()) 