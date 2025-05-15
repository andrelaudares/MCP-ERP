import httpx
import os
from datetime import datetime

OMIE_APP_KEY = os.getenv("OMIE_APP_KEY")
OMIE_APP_SECRET = os.getenv("OMIE_APP_SECRET")
OMIE_BASE_URL = "https://app.omie.com.br/api/v1"

async def call_omie_api(call: str, param: list, timeout: int = 30):
    """Faz uma chamada para a API Omie."""
    url = f"{OMIE_BASE_URL}/geral/clientes/"
    if call == "ListarPedidos":
        url = f"{OMIE_BASE_URL}/produtos/pedido/"

    payload = {
        "call": call,
        "app_key": OMIE_APP_KEY,
        "app_secret": OMIE_APP_SECRET,
        "param": param
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Erro HTTP ao chamar API Omie: {e.response.status_code} - {e.response.text}")
            return {"error": True, "details": e.response.text, "status_code": e.response.status_code}
        except httpx.RequestError as e:
            print(f"Erro de requisição ao chamar API Omie: {e}")
            return {"error": True, "details": str(e)}
        except Exception as e:
            print(f"Erro inesperado ao chamar API Omie: {e}")
            return {"error": True, "details": str(e)}

def _is_cnpj(identificador: str) -> bool:
    """Verifica de forma simples se o identificador parece um CNPJ (apenas números e com 14 dígitos)."""
    # Remove caracteres não numéricos comuns em CNPJ (., /, -)
    cleaned_id = ''.join(filter(str.isdigit, identificador))
    return len(cleaned_id) == 14

async def listar_clientes_omie(identificador_cliente: str):
    """
    Busca clientes na API Omie pelo nome/nome fantasia ou CNPJ.
    Se o identificador parecer um CNPJ, busca por 'cnpj_cpf' dentro de 'clientesFiltro'.
    Caso contrário, busca por 'nome_fantasia LIKE ...'.
    """
    if _is_cnpj(identificador_cliente):
        cnpj_limpo = ''.join(filter(str.isdigit, identificador_cliente))
        # Corrigido para usar a estrutura 'clientesFiltro' conforme os exemplos
        params = [{
            "pagina": 1,
            "registros_por_pagina": 5, # Esperamos poucos resultados para um CNPJ específico
            "apenas_importado_api": "N",
            "clientesFiltro": {
                "cnpj_cpf": cnpj_limpo
            }
        }]
        print(f"Buscando cliente por CNPJ: {cnpj_limpo} com params: {params}")
    else:
        # Mantendo a busca por nome como estava, pois não há exemplo de filtro de nome em clientesFiltro.
        # Se necessário, isso pode ser ajustado se houver um formato específico para nome em clientesFiltro.
        params = [{
            "pagina": 1,
            "registros_por_pagina": 5,
            "apenas_importado_api": "N",
            "cFiltro": f"nome_fantasia LIKE '%{identificador_cliente}%'"
            # Se o filtro de nome também for via clientesFiltro, seria algo como:
            # "clientesFiltro": { "nome_fantasia_contem": identificador_cliente }
            # Mas isso é uma suposição e precisaria ser confirmado pela documentação da Omie.
        }]
        print(f"Buscando cliente por nome/nome fantasia: {identificador_cliente} com params: {params}")
    
    return await call_omie_api("ListarClientes", params)

async def encontrar_pedidos_cliente(id_cliente: int, apenas_ultimo_pedido: bool = True):
    """
    Encontra pedidos de um cliente específico na API Omie.
    Ordena os pedidos pela data de previsão e pode retornar apenas o mais recente.
    """
    print(f"Buscando pedidos para o cliente ID: {id_cliente}")
    params = [{"filtrar_por_cliente": id_cliente}]
    # O endpoint correto para ListarPedidos é /produtos/pedido/
    # A função call_omie_api lida com isso.
    data = await call_omie_api("ListarPedidos", params)

    if not data or "pedido_venda_produto" not in data:
        print(f"Nenhum pedido encontrado ou formato de resposta inesperado para o cliente ID: {id_cliente}. Resposta: {data}")
        return {"error": "Nenhum pedido encontrado ou formato de resposta inesperado."}

    pedidos = data["pedido_venda_produto"]
    if not pedidos:
        print(f"Array de pedidos vazio para o cliente ID: {id_cliente}")
        return {"pedidos": []} # Retorna uma lista vazia se não houver pedidos

    # Ordenar pedidos por data de previsão (mais recente primeiro)
    # Assumindo que 'dPrevisao' existe em 'info' e está no formato 'dd/mm/aaaa'
    try:
        pedidos_ordenados = sorted(
            pedidos,
            key=lambda p: datetime.strptime(p.get("info", {}).get("dPrevisao", "01/01/1900"), "%d/%m/%Y"),
            reverse=True
        )
    except ValueError as e:
        print(f"Erro ao converter data de previsão: {e}. Usando lista original.")
        pedidos_ordenados = pedidos #Fallback se houver erro na data

    if apenas_ultimo_pedido and pedidos_ordenados:
        print(f"Retornando o último pedido para o cliente ID: {id_cliente}: {pedidos_ordenados[0]}")
        return {"pedido": pedidos_ordenados[0]}
    else:
        print(f"Retornando todos os pedidos ({len(pedidos_ordenados)}) para o cliente ID: {id_cliente}")
        return {"pedidos": pedidos_ordenados}

# Exemplo de uso (para teste direto do arquivo, se necessário)
if __name__ == "__main__":
    import asyncio
    async def main_test():
        # Teste listar_clientes_omie
        # print("Testando listar_clientes_omie:")
        # clientes = await listar_clientes_omie("NOME EXEMPLO") # Substitua por um nome de cliente de teste
        # print(json.dumps(clientes, indent=2))

        print("\nTestando encontrar_pedidos_cliente:")
        # Substitua pelo ID de um cliente que tenha pedidos para testar
        # Exemplo: ID de cliente fictício. Você precisará de um ID válido.
        # pedidos_cliente = await encontrar_pedidos_cliente(12345678) # Substitua por um ID de cliente válido
        # print(json.dumps(pedidos_cliente, indent=2))

        # Teste com cliente que talvez não tenha pedidos ou ID inválido
        print("\nTestando encontrar_pedidos_cliente (cliente sem pedidos ou ID inválido):")
        pedidos_cliente_sem_pedidos = await encontrar_pedidos_cliente(999999999) # ID provavelmente inválido
        print(json.dumps(pedidos_cliente_sem_pedidos, indent=2))

    #asyncio.run(main_test()) # Comente ou remova esta linha para uso normal como módulo
    pass 