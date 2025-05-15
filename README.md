# MCP ERP App - Agente Conversacional Omie & Evolution API

## Visão Geral

Este projeto implementa um backend conversacional inteligente projetado para se integrar com a API Omie e receber webhooks da Evolution API (WhatsApp). Ele utiliza:

- **FastAPI:** Para criar uma API web robusta e rápida, incluindo o endpoint que recebe as mensagens da Evolution API.
- **PydanticAI Agent (com Gemini):** Para processar as mensagens recebidas, entender a intenção do usuário e orquestrar a execução de ferramentas (tools) para buscar informações ou executar ações.
- **Ferramentas Customizadas:** Funções Python que o agente pode chamar para interagir com a API Omie (buscar clientes, pedidos, etc.) ou com a Evolution API (enviar mensagens de resposta).
- **Docker e Docker Compose:** Para facilitar a configuração, o build e a execução do ambiente de desenvolvimento e produção.

O objetivo principal é permitir que usuários interajam com o sistema Omie através de mensagens do WhatsApp, com o agente atuando como intermediário inteligente.

## Arquitetura do Sistema

```
+-----------------+      +-------------------------+      +-----------------------------------+      +---------------------+      +----------------------+
| Usuário WhatsApp|----->|    Evolution API        |----->|  FastAPI App (Este Projeto)       |<---->|   PydanticAI Agent  |<---->|      API Omie        |
|                 |      | (Serviço Externo)       |      | Rodando no Docker via Uvicorn     |      | (backend/agent.py)  |      | (Serviço Externo)    |
|                 |      |                         |      | Endpoint: /webhook/evolution      |      |                     |      |                      |
+-----------------+      +-------------------------+      +-----------------------------------+      +---------------------+      +----------------------+
                                   ^                                      |
                                   |                                      v (Envia Resposta)
                                   +--------------------------------------+
```

1.  O usuário envia uma mensagem pelo WhatsApp.
2.  A Evolution API recebe essa mensagem e a encaminha para o endpoint `/webhook/evolution` da nossa aplicação FastAPI.
3.  A aplicação FastAPI passa a mensagem recebida para o `PydanticAI Agent`.
4.  O Agente analisa a mensagem, decide qual ferramenta usar (ex: buscar cliente no Omie) e a executa.
5.  A ferramenta interage com a API Omie.
6.  O Agente formula uma resposta com base nos dados obtidos.
7.  A aplicação FastAPI envia a resposta de volta para o usuário via Evolution API.

## Estrutura do Projeto

```
.
├── backend/                # Código principal da aplicação
│   ├── __init__.py
│   ├── agent.py            # Lógica do PydanticAI Agent e definição das tools
│   ├── omie_api.py         # Funções para interagir com a API Omie
│   └── server.py           # Aplicação FastAPI, endpoints (incluindo o webhook)
├── tasks/                  # Arquivos de tarefas gerados pelo Task Master (se usado)
├── .env                    # Arquivo para variáveis de ambiente (NÃO versionado)
├── .env.example            # Exemplo de arquivo .env
├── .gitignore
├── docker-compose.yaml     # Configuração dos serviços Docker
├── Dockerfile              # Instruções para construir a imagem Docker da aplicação
├── prd.md                  # Product Requirements Document (se usado)
├── README.md               # Este arquivo
└── requirements.txt        # Dependências Python do projeto principal (instaladas no Docker)
```

## Variáveis de Ambiente Essenciais

Crie um arquivo `.env` na raiz do projeto, baseado no `.env.example`. As seguintes variáveis são cruciais:

-   `PYTHONUNBUFFERED=1`: Garante que os logs do Python apareçam imediatamente no console do Docker.
-   `GEMINI_API_KEY`: Sua chave de API para o Google Gemini, usada pelo PydanticAI Agent.
-   `OMIE_APP_KEY`: Sua chave de aplicação para a API Omie.
-   `OMIE_APP_SECRET`: Seu segredo de aplicação para a API Omie.
-   `EVOLUTION_API_URL`: URL base da sua instância da Evolution API. **Importante:** Se a Evolution API estiver rodando em outro container Docker na mesma rede, use o nome do serviço Docker e a porta interna (ex: `http://evolution-api:8080`).
-   `EVOLUTION_API_KEY`: Sua chave de API para a Evolution API.
-   `EVOLUTION_INSTANCE_NAME`: O nome da sua instância configurada na Evolution API.

**Exemplo de `.env`:**
```env
PYTHONUNBUFFERED=1

# Google Gemini
GEMINI_API_KEY="sua_chave_gemini_aqui"

# Omie API
OMIE_APP_KEY="sua_omie_app_key"
OMIE_APP_SECRET="sua_omie_app_secret"

# Evolution API
EVOLUTION_API_URL="http://evolution-api:8080" # Ajuste conforme sua configuração Docker
EVOLUTION_API_KEY="sua_evolution_api_key"
EVOLUTION_INSTANCE_NAME="seu_nome_de_instancia_evolution"
```

## Comandos Docker Essenciais

Para gerenciar o ambiente Docker:

1.  **Parar e remover containers, volumes e redes (limpeza completa):**
    ```bash
    docker compose down -v
    ```
    *Use com cautela, pois `-v` remove os volumes de dados (ex: banco de dados da Evolution API se gerenciado no mesmo compose).*

2.  **Parar e remover containers (sem remover volumes):**
    ```bash
    docker compose down
    ```

3.  **Construir ou Reconstruir as imagens dos serviços (especialmente o `app`):**
    ```bash
    docker compose build app
    ```
    *Faça isso sempre que alterar o `Dockerfile` ou o `requirements.txt`.*

4.  **Subir todos os serviços em segundo plano (detached mode):**
    ```bash
    docker compose up -d
    ```

5.  **Subir os serviços e reconstruir se necessário, mostrando logs no terminal:**
    ```bash
    docker compose up --build
    ```
    *Útil para desenvolvimento e para ver o output inicial.*

6.  **Visualizar logs de um serviço específico (ex: `app`):**
    ```bash
    docker compose logs -f app
    ```
    *O `-f` (follow) mostra os logs em tempo real.*

7.  **Acessar o terminal de um container em execução (ex: `app`):**
    ```bash
    docker compose exec app /bin/bash
    ```
    *Útil para depuração dentro do container.*

**Fluxo recomendado para iniciar ou atualizar:**
```bash
docker compose down # Opcional, para garantir um ambiente limpo
docker compose build app
docker compose up -d
docker compose logs -f app
```

## Endpoint Principal: Webhook da Evolution API

### `POST /webhook/evolution`

Este é o endpoint que a Evolution API chamará quando uma nova mensagem do WhatsApp for recebida na instância configurada.

-   **Método:** `POST`
-   **Corpo da Requisição (Body):** A Evolution API envia um payload JSON contendo os detalhes da mensagem. A estrutura exata pode ser consultada na documentação da Evolution API, mas geralmente inclui informações sobre o remetente (`remoteJid`), o tipo de mensagem e o conteúdo (`body` para mensagens de texto).
    Nossa aplicação espera um payload como:
    ```json
    {
        "event": "messages.upsert", // ou similar
        "instance": "seu_nome_de_instancia_evolution",
        "data": {
            "key": {
                "remoteJid": "5511999998888@s.whatsapp.net", // Número do remetente
                "fromMe": false,
                "id": "MSG_ID_WHATSAPP"
            },
            "message": {
                "conversation": "Qual o último pedido do cliente XPTO?" // Conteúdo da mensagem
                // ... outros campos dependendo do tipo de mensagem
            }
            // ...
        },
        "destination": "SUA_URL_WEBHOOK_CONFIGURADA",
        "date_time": "2024-07-30T10:00:00Z",
        "sender": "5511999998888@s.whatsapp.net", // Pode variar
        "server_url": "URL_DO_SEU_SERVIDOR_EVOLUTION",
        "apikey": "SUA_API_KEY_EVOLUTION_SE_CONFIGURADA_PARA_ENVIO_NO_WEBHOOK"
    }
    ```
    *(Nota: O payload exato pode variar. A aplicação em `backend/server.py` está preparada para extrair `data.message.conversation` e `data.key.remoteJid`)*

-   **Ação:**
    1.  Recebe o payload da Evolution API.
    2.  Extrai a mensagem do usuário e o identificador do remetente.
    3.  Passa a mensagem para o `PydanticAI Agent`.
    4.  O agente processa a mensagem, usa as tools Omie conforme necessário.
    5.  O agente formula uma resposta.
    6.  A aplicação envia a resposta de volta ao remetente usando a Evolution API.

-   **Resposta (para a Evolution API):**
    A aplicação retorna `JSONResponse(content={"status": "webhook recebido e processado"})` com status `200 OK` para a Evolution API para confirmar o recebimento. A resposta para o usuário final é enviada de forma assíncrona através de uma chamada separada para a Evolution API.

## Configurando o Webhook na Evolution API

Para que este sistema funcione, você precisa configurar sua instância da Evolution API para enviar eventos de mensagem para o endpoint `/webhook/evolution` da sua aplicação.

1.  **Acesse as configurações da sua instância na Evolution API.**
2.  **Encontre a seção de configuração de Webhooks Globais ou Webhooks de Mensagens.**
3.  **Configure a URL do Webhook:**
    *   Se sua aplicação FastAPI está rodando localmente e exposta via ngrok (ou similar) para testes, use a URL do ngrok: `https://seu-subdominio.ngrok.io/webhook/evolution`.
    *   Se a Evolution API e sua aplicação estão rodando em containers Docker na mesma máquina e rede, e sua aplicação está exposta na porta 8000 do host, a Evolution API pode precisar de uma URL acessível *do ponto de vista dela*. Se ela também estiver em Docker, pode ser o IP do host Docker e a porta mapeada, ou o nome do serviço da sua app se estiverem na mesma rede Docker Compose e a Evolution API conseguir resolver. Ex: `http://host.docker.internal:8000/webhook/evolution` (para Docker Desktop) ou o IP da sua máquina na rede local.
    *   **Importante:** Garanta que a Evolution API consiga alcançar a URL da sua aplicação.

## Como Adicionar Novas Ferramentas (Tools) ao Agente

O agente PydanticAI pode ser estendido com novas ferramentas para interagir com outras APIs ou executar lógica customizada.

1.  **Abra o arquivo `backend/agent.py`.**
2.  **Defina uma nova função Python.** Esta função será sua ferramenta. Ela deve ter uma docstring clara explicando o que faz, quais parâmetros aceita e o que retorna, pois o LLM usará essa descrição para decidir quando e como usar a ferramenta.
    ```python
    # backend/agent.py

    # ... outras tools ...

    def minha_nova_ferramenta(identificador_cliente: str, informacao_adicional: Optional[str] = None) -> Dict[str, Any]:
        """
        Esta ferramenta busca informações X sobre um cliente usando seu identificador.
        Se informação_adicional for fornecida, ela refina a busca.
        Retorna um dicionário com os detalhes encontrados ou uma mensagem de erro.
        """
        # Lógica da sua ferramenta aqui
        # Ex: chamar uma API, consultar um banco de dados, etc.
        print(f"Tool 'minha_nova_ferramenta' chamada com: {identificador_cliente}, {informacao_adicional}")
        if identificador_cliente == "123":
            return {"id": identificador_cliente, "info": "Dados encontrados", "extra": informacao_adicional}
        else:
            return {"erro": "Cliente não encontrado"}

    # ... (no final do arquivo, adicione a nova função à lista de tools)
    tools = [
        buscar_id_cliente_tool_func,
        buscar_pedidos_cliente_tool_func,
        minha_nova_ferramenta # Adicione sua nova ferramenta aqui
    ]

    # ... (o resto da configuração do Agent)
    ```
3.  **A docstring é crucial!** O PydanticAI usa a docstring e as anotações de tipo para entender como chamar a ferramenta.
4.  O agente agora poderá usar essa ferramenta automaticamente ao interpretar mensagens relevantes. Não é necessário usar o decorator `@agent.tool` com a versão do PydanticAI que estamos usando, apenas adicionar a função à lista de `tools`.

## Troubleshooting Comum

-   **`ConnectTimeout` ou `ConnectionRefusedError` ao tentar chamar a Evolution API a partir da `app`:**
    *   **Causa:** A `EVOLUTION_API_URL` no `.env` está incorreta ou o container da Evolution API não está acessível a partir do container `app`.
    *   **Solução:**
        *   Verifique se o nome do serviço e a porta em `EVOLUTION_API_URL` (ex: `http://evolution-api:8080`) correspondem exatamente ao nome do serviço e à porta exposta da Evolution API no seu `docker-compose.yaml`.
        *   Certifique-se de que ambos os containers (sua `app` e a `evolution-api`) estão na mesma rede Docker. Se estiverem em `docker-compose.yaml` separados, eles precisam ser explicitamente conectados a uma rede customizada compartilhada.
        *   Teste a conectividade de dentro do container `app`: `docker compose exec app curl http://evolution-api:8080/status` (substitua com sua URL e um endpoint válido da Evolution API).

-   **Agente não usa as ferramentas Omie ou retorna respostas genéricas:**
    *   **Causa:** O `SYSTEM_PROMPT` em `backend/agent.py` pode não estar claro o suficiente, as docstrings das funções-ferramenta podem ser ambíguas, ou o modelo LLM pode estar tendo dificuldade em entender a tarefa.
    *   **Solução:**
        *   Refine o `SYSTEM_PROMPT` para ser mais explícito sobre quando e como usar as ferramentas.
        *   Melhore as docstrings das funções-ferramenta (`buscar_id_cliente_tool_func`, `buscar_pedidos_cliente_tool_func`) para descrever claramente seus propósitos, parâmetros e o que retornam.
        *   Verifique se a `GEMINI_API_KEY` está correta e se o modelo Gemini está funcionando.
        *   Simplifique a pergunta do usuário para testar uma ferramenta de cada vez.

-   **Erro `Attribute "app" not found in module "backend.server"` ao iniciar o container `app`:**
    *   **Causa:** Geralmente indica que o comando `uvicorn backend.server:app` no `Dockerfile` ou `docker-compose.yaml` não consegue encontrar o objeto `app = FastAPI()` no arquivo `backend/server.py`. Isso pode acontecer se o arquivo estiver vazio, com erro de sintaxe, ou se o objeto `app` não estiver definido no escopo global do módulo.
    *   **Solução:** Verifique o arquivo `backend/server.py` para garantir que ele contém `app = FastAPI()` e que não há erros de importação ou sintaxe que impeçam o arquivo de ser carregado corretamente. Verifique se o `WORKDIR` no `Dockerfile` está correto (`/app/`) e se os arquivos são copiados para o local esperado.

-   **Webhook não é chamado pela Evolution API:**
    *   **Causa:** A URL configurada na Evolution API está incorreta, sua aplicação não está acessível externamente (se a Evolution API for externa), ou há um problema de rede/firewall.
    *   **Solução:** Verifique a URL do webhook nas configurações da Evolution API. Use ferramentas como `ngrok` para expor sua aplicação localmente para testes. Verifique os logs da sua aplicação e da Evolution API.

---
Dúvidas? Abra uma issue ou consulte a documentação interna do projeto.
