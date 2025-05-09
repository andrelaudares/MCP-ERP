import asyncio
from fastmcp import Client

async def main():
    # Conecta-se ao server.py.
    # Quando usamos Client("server.py"), ele tentará executar 'python server.py'
    # como um subprocesso.
    print("Tentando conectar ao servidor MCP em server.py...")
    try:
        async with Client("server.py") as client:
            print("Conectado! Listando ferramentas...")
            tools = await client.list_tools()
            if not tools:
                print("Nenhuma ferramenta encontrada no servidor.")
                return

            print(f"Ferramentas encontradas: {[t.name for t in tools]}")

            if "encontrar_pedidos_cliente" not in [t.name for t in tools]:
                print("A ferramenta 'encontrar_pedidos_cliente' não foi encontrada.")
                return

            print("\\nChamando encontrar_pedidos_cliente com CNPJ (exemplo)...")
            # SUBSTITUA "SEU_CNPJ_DE_TESTE_AQUI" por um CNPJ real para teste
            # ou deixe None para testar a validação de entrada
            cnpj_teste = "172.033.798-50" # ou None
            nome_fantasia_teste = None # ou um nome para teste
            cidade_teste = None # ou uma cidade para teste
            
            # Certifique-se de que pelo menos um parâmetro é fornecido se não for testar o erro
            if not any([cnpj_teste, nome_fantasia_teste, cidade_teste]) and cnpj_teste != "SEU_CNPJ_DE_TESTE_AQUI":
                 print("Forneça pelo menos um critério de teste (CNPJ, nome fantasia ou cidade) em client_test.py")
                 return

            params = {}
            if cnpj_teste and cnpj_teste != "SEU_CNPJ_DE_TESTE_AQUI":
                params["cnpj_cpf"] = cnpj_teste
            if nome_fantasia_teste:
                params["nome_fantasia"] = nome_fantasia_teste
            if cidade_teste:
                params["cidade"] = cidade_teste
            
            if not params:
                 print("Nenhum parâmetro de teste válido fornecido para encontrar_pedidos_cliente.")
                 print("Edit client_test.py para adicionar um CNPJ, nome fantasia ou cidade para teste.")
                 # Vamos testar a chamada sem parâmetros para ver a mensagem de erro da ferramenta
                 params = {"cnpj_cpf": None, "nome_fantasia": None, "cidade": None}


            print(f"Chamando com parâmetros: {params}")
            result = await client.call_tool("encontrar_pedidos_cliente", params)
            print("\\nResultado da chamada à ferramenta:")
            
            # Tenta analisar o resultado se for uma string JSON e imprimir de forma formatada
            if result and hasattr(result, 'text') and isinstance(result.text, str):
                try:
                    import json
                    parsed_result = json.loads(result.text)
                    print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(result.text) # Se não for JSON válido, imprime como está
            elif isinstance(result, str): # Caso a ferramenta retorne uma string de erro diretamente
                print(result)
            else:
                print(result) # Fallback para outros tipos de resultado

    except Exception as e:
        print(f"Ocorreu um erro durante o teste do cliente: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
