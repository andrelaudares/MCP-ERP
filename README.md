# MCP ERP App - Agente Conversacional Omie

## Visão Geral

Este projeto implementa um backend conversacional inteligente para integração com Omie, Evolution e outros sistemas, usando:
- **FastAPI** para expor endpoints HTTP
- **PydanticAI Agent** para orquestração e raciocínio
- **MCP (FastMCP)** para registro e execução de ferramentas (tools)

## Arquitetura

```
[Usuário/Sistema externo]
        |
        v
  [FastAPI /webhook]
        |
        v
   [agent.py (PydanticAI)]
        |
        v
   [MCP (FastMCP) / Tools]
        |
        v
   [Integrações externas: Omie, Evolution, etc.]
```

## Como rodar

1. **Configure o arquivo `.env`** na raiz do projeto (veja `.env.example` para variáveis obrigatórias).
2. **Suba o ambiente com Docker Compose:**
   ```bash
   docker-compose up --build
   ```
3. O serviço FastAPI estará disponível em `http://localhost:8000`.

## Subindo o ambiente Docker (comandos úteis)

Para garantir que todas as dependências estejam atualizadas e o ambiente limpo, utilize os seguintes comandos:

```bash
# Parar e remover todos os containers, se necessário
docker compose down

# (Re)construir a imagem do serviço principal (app)
docker compose build app

# Subir todos os serviços em segundo plano
docker compose up -d

# Ver logs do serviço principal (app)
docker compose logs -f app
```

- O comando `docker compose up --build` também pode ser usado para buildar e subir tudo de uma vez.
- Para acessar o container do app para depuração:
```bash
docker compose exec app /bin/bash
```

## Endpoint principal

### POST `/webhook`

Recebe uma mensagem e retorna a resposta do agente.

**Exemplo de requisição:**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Quais os últimos pedidos do cliente com CNPJ 12345678900?"}'
```

**Resposta:**
```json
{
  "resposta": "O último pedido do cliente com CNPJ 12345678900 é o pedido número 4411..."
}
```

## Como adicionar novas tools ao agente

1. Edite o arquivo `backend/agent.py`.
2. Crie uma nova função com o decorator `@agent.tool`:
   ```python
   @agent.tool
   def nova_tool(ctx: RunContext[AgentDeps], parametro: str) -> dict:
       # Lógica da tool
       return {...}
   ```
3. O agente poderá usar essa tool automaticamente ao interpretar mensagens relevantes.

## Como expandir a integração
- Adicione novas tools ao MCP (FastMCP) para expor funcionalidades externas.
- Registre essas tools no agente para orquestração inteligente.
- O agente pode combinar raciocínio LLM com automação de ferramentas.

## Testes
- Recomenda-se criar testes para o endpoint `/webhook` usando `pytest` ou `httpx`.

---
Dúvidas? Abra uma issue ou consulte a documentação interna do projeto.
