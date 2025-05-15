# PRD: Projeto de Orquestração de Contêineres com Integração WhatsApp

## 1. Visão geral do produto

### 1.1 Título e versão do documento

*   PRD: Projeto de Orquestração de Contêineres com Integração WhatsApp
*   Versão: 1.0

### 1.2 Resumo do produto

Este documento descreve os requisitos para a configuração e gerenciamento de um ambiente de desenvolvimento e produção utilizando Docker e Docker Compose. O objetivo principal é encapsular a aplicação principal, suas dependências (como bancos de dados) e a API de integração com o WhatsApp (Evolution API) em contêineres, facilitando a implantação, escalabilidade e portabilidade do sistema.

O projeto visa simplificar o setup do ambiente para desenvolvedores e garantir consistência entre os diferentes estágios (desenvolvimento, teste, produção). A solução permitirá que a aplicação principal (`app`) se comunique de forma eficaz com a Evolution API e seus microsserviços de suporte (Redis, RabbitMQ, Minio, PostgreSQL dedicado para Evolution API, e um conversor de áudio).

## 2. Objetivos

### 2.1 Objetivos de negócio

*   Acelerar o ciclo de desenvolvimento e implantação de novas funcionalidades.
*   Reduzir a complexidade de configuração do ambiente para novos desenvolvedores.
*   Garantir a consistência e reprodutibilidade do ambiente em diferentes máquinas e estágios.
*   Facilitar a escalabilidade dos componentes da aplicação e da API do WhatsApp.
*   Melhorar a estabilidade e a confiabilidade da aplicação através de um ambiente isolado e controlado.

### 2.2 Objetivos do usuário

*   **Desenvolvedores**: Ter um ambiente de desenvolvimento local que espelhe a produção, fácil de configurar e iniciar com um único comando.
*   **Desenvolvedores**: Ser capaz de depurar e testar a integração entre a aplicação principal e a API do WhatsApp de forma eficiente.
*   **Administradores de Sistema/DevOps**: Implantar e gerenciar a aplicação e seus componentes de forma simplificada e automatizada.
*   **Administradores de Sistema/DevOps**: Monitorar e escalar os serviços individualmente conforme a necessidade.

### 2.3 Não objetivos

*   Gerenciar a infraestrutura física ou provedor de nuvem onde os contêineres serão executados.
*   Desenvolver a funcionalidade interna da aplicação principal (`app`) além de sua capacidade de interagir com os serviços definidos.
*   Desenvolver a API Evolution ou seus componentes (serão utilizadas imagens prontas).
*   Fornecer uma interface gráfica de gerenciamento para os contêineres (além das UIs já embutidas em alguns serviços como RabbitMQ Management, Minio Console ou pgAdmin opcional).

## 3. Personas de usuário

### 3.1 Principais tipos de usuário

*   Desenvolvedor da Aplicação Principal
*   Engenheiro de DevOps/Administrador de Sistema

### 3.2 Detalhes básicos da persona

*   **Desenvolvedor da Aplicação (DevApp)**: Responsável por codificar, testar e depurar a aplicação principal (`app`) que consome a API do WhatsApp. Necessita de um ambiente local estável e fácil de usar.
*   **Engenheiro de DevOps (DevOpsEng)**: Responsável por implantar, gerenciar, escalar e monitorar a aplicação em ambientes de produção e staging. Necessita de uma configuração robusta e automatizável.

### 3.3 Acesso baseado em função

*   **DevApp**: Acesso para iniciar, parar, reconstruir e visualizar logs dos contêineres no ambiente de desenvolvimento. Acesso aos códigos-fonte montados nos volumes.
*   **DevOpsEng**: Acesso total para gerenciar os contêineres em todos os ambientes, configurar variáveis de ambiente, gerenciar volumes persistentes e redes.

## 4. Requisitos funcionais

*   **Orquestração de Contêineres** (Prioridade: Alta)
    *   Permitir a inicialização de todos os serviços definidos no `docker-compose.yaml` com um único comando (ex: `docker-compose up`).
    *   Permitir a parada de todos os serviços com um único comando (ex: `docker-compose down`).
    *   Garantir que os serviços dependentes iniciem na ordem correta (ex: `app` depende de `db` e `evolution-api`).
    *   Permitir a reconstrução de imagens de serviços específicos quando necessário (ex: `docker-compose build app`).
*   **Serviço da Aplicação Principal (`app`)** (Prioridade: Alta)
    *   Deve ser construído a partir de um `Dockerfile` localizado no contexto do projeto.
    *   Deve montar os diretórios `src`, `scripts`, `tasks`, `alembic` e o arquivo `alembic.ini` do host para permitir desenvolvimento iterativo.
    *   Deve se conectar ao serviço de banco de dados `db`.
    *   Deve se conectar ao serviço `evolution-api` para interações com o WhatsApp.
    *   As variáveis de ambiente necessárias para a `app` devem ser configuráveis via `docker-compose.yaml` e/ou arquivos `.env`.
*   **Serviço de Banco de Dados da Aplicação (`db`)** (Prioridade: Alta)
    *   Utilizar a imagem `postgres:16`.
    *   Permitir a configuração de usuário, senha e nome do banco via variáveis de ambiente.
    *   Garantir a persistência dos dados através de um volume Docker (`postgres_adk_data`).
    *   Expor a porta `5432` do contêiner para a porta `5432` do host.
*   **Serviços da Evolution API e Dependências** (Prioridade: Alta)
    *   **`evolution-api`**:
        *   Utilizar a imagem `atendai/evolution-api:v2.2.3`.
        *   Configurar corretamente as variáveis de ambiente para autenticação, conexão com seu banco de dados (`evolution_postgres`), Redis, RabbitMQ e Minio.
        *   Expor a porta `8080` para comunicação.
        *   Garantir a persistência de dados de instâncias via volume (`evolution_instances`).
    *   **`evolution_postgres`**:
        *   Utilizar a imagem `postgres:15`.
        *   Configurar usuário, senha e nome do banco dedicados.
        *   Persistir dados no volume `postgres_evo_data`.
        *   Mapear a porta interna `5432` para uma porta de host configurável (ex: `5433`).
    *   **`redis`**:
        *   Utilizar a imagem `redis:7`.
        *   Persistir dados no volume `redis_data`.
    *   **`rabbitmq`**:
        *   Utilizar a imagem `rabbitmq:management`.
        *   Configurar usuário e senha.
        *   Persistir dados no volume `rabbitmq_data`.
        *   Incluir healthcheck para garantir a prontidão do serviço.
    *   **`minio`**:
        *   Utilizar a imagem `quay.io/minio/minio`.
        *   Configurar usuário root e senha.
        *   Persistir dados no volume `minio_data`.
        *   Incluir healthcheck.
    *   **`audio-converter`**:
        *   Utilizar a imagem `atendai/evolution-audio-converter:latest`.
        *   Configurar porta e chaves de API necessárias.
*   **Rede de Contêineres** (Prioridade: Alta)
    *   Todos os serviços devem operar em uma rede Docker customizada (`app-network`) do tipo `bridge` para permitir a comunicação interna via nomes de serviço.
*   **Gerenciamento de Configuração** (Prioridade: Alta)
    *   Permitir a configuração da maioria dos parâmetros dos serviços (portas, credenciais, chaves de API) através de variáveis de ambiente, idealmente centralizadas em um arquivo `.env` na raiz do projeto.
*   **Persistência de Dados** (Prioridade: Alta)
    *   Garantir que os dados críticos dos bancos de dados, Redis, RabbitMQ, Minio e instâncias da Evolution API sejam persistidos em volumes Docker para sobreviver a reinicializações de contêineres.

## 5. Experiência do usuário

### 5.1 Pontos de entrada e fluxo do primeiro usuário

*   **Desenvolvedor (DevApp)**:
    1.  Clona o repositório do projeto.
    2.  Configura o arquivo `.env` com as credenciais e parâmetros necessários.
    3.  Executa `docker-compose up -d` (ou `docker-compose up --build` pela primeira vez).
    4.  Verifica os logs com `docker-compose logs -f app` (ou outros serviços).
    5.  Acessa a aplicação (`app`) e as UIs dos serviços (Minio console, RabbitMQ management) pelos respectivos `localhost:porta`.
*   **Engenheiro de DevOps (DevOpsEng)**:
    1.  Acessa o servidor de implantação.
    2.  Obtém a última versão do código e do `docker-compose.yaml`.
    3.  Configura as variáveis de ambiente específicas do ambiente (staging/produção).
    4.  Executa os comandos do Docker Compose para implantar ou atualizar os serviços.

### 5.2 Experiência principal

*   **Inicialização do Ambiente**: DevApp/DevOpsEng executa `docker-compose up`. Todos os serviços são iniciados em segundo plano. A experiência deve ser rápida e os logs devem indicar claramente o sucesso ou falha de cada serviço.
    *   *Para uma boa primeira experiência*: Fornecer um arquivo `.env.example` claro. Os serviços devem iniciar sem erros com configurações padrão (onde aplicável) ou após o preenchimento do `.env`.
*   **Desenvolvimento na `app`**: DevApp edita o código no diretório `./src` (ou outros montados). As alterações são refletidas no contêiner `app` (se a aplicação suportar hot-reloading) ou após uma reconstrução rápida (`docker-compose build app && docker-compose up -d app`).
    *   *Para uma boa primeira experiência*: O hot-reloading da `app` deve funcionar, se aplicável à stack tecnológica, ou o ciclo de build/restart deve ser ágil.
*   **Interação com API WhatsApp**: A `app` consegue enviar requisições para `http://evolution-api:8080` e receber respostas.
    *   *Para uma boa primeira experiência*: Configurações de API KEY da Evolution API e outras conexões devem estar claras e fáceis de ajustar no `.env`.
*   **Acesso a Dados**: A `app` consegue se conectar ao `db:5432`. A Evolution API consegue se conectar ao `evolution_postgres:5432`.
    *   *Para uma boa primeira experiência*: As strings de conexão devem ser facilmente configuráveis e os bancos de dados devem estar prontos para aceitar conexões após o `up`.

### 5.3 Funcionalidades avançadas e casos de borda

*   Executar comandos dentro de um contêiner (ex: `docker-compose exec app bash`).
*   Visualizar logs específicos de um serviço (ex: `docker-compose logs -f evolution-api`).
*   Escalar serviços horizontalmente (se aplicável e suportado pelo Docker Compose e pela arquitetura do serviço, ex: `docker-compose up --scale app=3`).
*   Lidar com falhas de inicialização de um serviço (ex: um serviço dependente não está pronto). O Docker Compose deve tentar reiniciar ou as dependências (`depends_on` com `condition`) devem gerenciar isso.
*   Atualização de versões de imagens (ex: `postgres:16` para `postgres:16.1`).

### 5.4 Destaques de UI/UX

*   A "UI" principal é a interface de linha de comando (CLI) do `docker-compose`. Deve ser responsiva e fornecer feedback claro.
*   As UIs web de serviços como RabbitMQ Management (`localhost:15672`), Minio Console (`localhost:9001`) e pgAdmin opcional (`localhost:5050`) devem estar acessíveis e funcionais.
*   A documentação do projeto (README.md) deve guiar o usuário sobre como configurar e rodar o ambiente.

## 6. Narrativa

Mariana, uma desenvolvedora backend, precisa integrar rapidamente um novo chatbot WhatsApp a uma aplicação web existente. Ela quer focar na lógica do chatbot e não perder tempo configurando bancos de dados, filas de mensagens e a API do WhatsApp em sua máquina local, nem se preocupar com inconsistências quando o projeto for para produção. Ela encontra este projeto de orquestração de contêineres. Com um simples `docker-compose up`, todo o ambiente, incluindo a API do WhatsApp, seu banco de dados dedicado, e as dependências da aplicação principal, sobe em minutos. Mariana pode agora desenvolver e testar a integração diretamente, sabendo que o ambiente é idêntico ao que será usado em produção, economizando tempo e evitando dores de cabeça com configuração.

## 7. Métricas de sucesso

### 7.1 Métricas centradas no usuário

*   Tempo para um novo desenvolvedor ter o ambiente rodando localmente (objetivo: < 15 minutos após clonar o repo e ler o README).
*   Número de problemas reportados relacionados à inconsistência de ambiente entre desenvolvedores ou entre desenvolvimento e produção (objetivo: próximo de zero).
*   Facilidade percebida para iniciar, parar e depurar os serviços (medida por pesquisa interna ou feedback).

### 7.2 Métricas de negócio

*   Redução no tempo de onboarding de novos desenvolvedores.
*   Aumento na velocidade de implantação de novas features que dependem da API do WhatsApp.
*   Redução de bugs em produção causados por diferenças de ambiente.

### 7.3 Métricas técnicas

*   Tempo médio para `docker-compose up` (objetivo: < 2 minutos em uma máquina razoável após o download inicial das imagens).
*   Uso de recursos (CPU, memória) pelos contêineres em idle e sob carga.
*   Estabilidade dos serviços (número de reinícios inesperados dos contêineres).

## 8. Considerações técnicas

### 8.1 Pontos de integração

*   Aplicação (`app`) <> Banco de Dados Principal (`db`) via rede Docker.
*   Aplicação (`app`) <> Evolution API (`evolution-api`) via rede Docker.
*   Evolution API (`evolution-api`) <> `evolution_postgres`, `redis`, `rabbitmq`, `minio`, `audio-converter` via rede Docker.
*   Exposição de portas dos serviços para o host (ex: `app` na 8000, `evolution-api` na 8080, `db` na 5432, etc.).

### 8.2 Armazenamento de dados e privacidade

*   Todos os dados persistentes devem ser armazenados em volumes Docker nomeados para fácil gerenciamento e backup.
*   Credenciais e chaves de API devem ser gerenciadas através de variáveis de ambiente e arquivos `.env` (que não devem ser versionados no Git, exceto por um `.env.example`).
*   Considerar as implicações de privacidade dos dados armazenados pela Evolution API (mensagens, contatos), especialmente se dados reais forem usados em desenvolvimento.

### 8.3 Escalabilidade e desempenho

*   A arquitetura com Docker Compose permite escalar alguns serviços (ex: `app`) usando `docker-compose up --scale app=N`, mas para ambientes de produção de alta carga, Kubernetes ou similar pode ser necessário.
*   Monitorar o desempenho dos bancos de dados e ajustar `max_connections` ou outros parâmetros conforme necessário.
*   Garantir que as configurações de `healthcheck` sejam adequadas para determinar a real prontidão dos serviços.

### 8.4 Desafios potenciais

*   Conflitos de porta no host se as portas padrão já estiverem em uso.
*   Gerenciamento de múltiplas instâncias da Evolution API (se necessário) pode exigir configurações mais complexas.
*   Consumo de recursos (CPU/RAM) por tantos contêineres rodando simultaneamente em máquinas de desenvolvimento menos potentes.
*   Manter as versões das imagens Docker atualizadas e testar a compatibilidade.
*   Complexidade na configuração inicial do `.env` devido ao grande número de variáveis.

## 9. Marcos e sequenciamento

### 9.1 Estimativa do projeto

*   Médio: 1-2 semanas (para configurar, testar exaustivamente e documentar o `docker-compose.yaml` e o fluxo de trabalho).

### 9.2 Tamanho e composição da equipe

*   Pequena Equipe: 1-2 pessoas
    *   1 Engenheiro de DevOps (ou Desenvolvedor Sênior com experiência em Docker)
    *   1 Desenvolvedor da Aplicação (para testar a integração e o fluxo de desenvolvimento)

### 9.3 Fases sugeridas

*   **Fase 1**: Configuração e Teste dos Serviços Base (1 semana)
    *   Key deliverables: `docker-compose.yaml` funcional com `app`, `db`, `evolution-api`, `evolution_postgres`, `redis`, `rabbitmq`, `minio`, `audio-converter`. Todos os serviços iniciam, se comunicam e persistem dados. Documentação básica (README.md) para setup.
*   **Fase 2**: Refinamento, Testes de Integração e Documentação Final (1 semana)
    *   Key deliverables: Testes completos de integração entre `app` e `evolution-api`. Otimização de builds e configurações. Healthchecks robustos. Documentação detalhada do PRD e README. Arquivo `.env.example` completo.

## 10. Histórias de usuário

### 10.1. Como Desenvolvedor, quero iniciar todo o ambiente com um único comando

*   **ID**: US-001
*   **Descrição**: Como um Desenvolvedor da Aplicação (DevApp), quero iniciar todos os serviços (aplicação principal, bancos de dados, Evolution API e suas dependências) com um único comando para configurar rapidamente meu ambiente de desenvolvimento.
*   **Critérios de Aceitação**:
    *   Executar `docker-compose up -d` inicia todos os contêineres definidos no `docker-compose.yaml`.
    *   Nenhum erro é exibido durante a inicialização se as configurações no `.env` estiverem corretas.
    *   Todos os serviços estão acessíveis em suas respectivas portas na rede interna do Docker.

### 10.2. Como Desenvolvedor, quero que minhas alterações de código na aplicação principal sejam refletidas rapidamente

*   **ID**: US-002
*   **Descrição**: Como um DevApp, quero que as alterações que faço no código-fonte da aplicação principal (`./src`) sejam refletidas no contêiner `app` sem precisar reconstruir manualmente a imagem toda vez, para agilizar o desenvolvimento.
*   **Critérios de Aceitação**:
    *   O diretório `./src` (e outros relevantes como `./scripts`, `./tasks`, `./alembic`) do host está montado como um volume no contêiner `app`.
    *   Se a stack da `app` suportar hot-reloading, alterações no código devem ser automaticamente recarregadas.
    *   Caso contrário, um `docker-compose restart app` ou um `docker-compose build app && docker-compose up -d app` deve aplicar as alterações rapidamente.

### 10.3. Como Desenvolvedor, quero que os dados da minha aplicação e da Evolution API persistam entre reinicializações

*   **ID**: US-003
*   **Descrição**: Como um DevApp, quero que os dados dos bancos de dados (`db`, `evolution_postgres`), Redis, RabbitMQ, Minio e instâncias da Evolution API sejam mantidos mesmo se eu parar e reiniciar os contêineres (`docker-compose down && docker-compose up`).
*   **Critérios de Aceitação**:
    *   Volumes Docker nomeados estão configurados para `postgres_adk_data`, `postgres_evo_data`, `redis_data`, `rabbitmq_data`, `minio_data`, `evolution_instances`.
    *   Após um ciclo de `down` e `up`, os dados previamente salvos nos serviços estão intactos e acessíveis.

### 10.4. Como Desenvolvedor, quero configurar facilmente as credenciais e parâmetros dos serviços

*   **ID**: US-004
*   **Descrição**: Como um DevApp, quero poder configurar todas as credenciais (usuários, senhas de banco, chaves de API) e parâmetros específicos (portas, nomes de banco) através de um arquivo `.env` na raiz do projeto.
*   **Critérios de Aceitação**:
    *   Existe um arquivo `.env.example` no repositório com todas as variáveis necessárias e exemplos de valores.
    *   O `docker-compose.yaml` lê as variáveis do arquivo `.env`.
    *   Alterar um valor no `.env` e reiniciar os contêineres aplica a nova configuração.

### 10.5. Como Desenvolvedor, quero que a aplicação principal (`app`) consiga se comunicar com a Evolution API (`evolution-api`)

*   **ID**: US-005
*   **Descrição**: Como um DevApp, quero que minha aplicação (`app`) possa fazer requisições HTTP para o serviço `evolution-api` usando seu nome de serviço (ex: `http://evolution-api:8080`) para enviar e receber mensagens do WhatsApp.
*   **Critérios de Aceitação**:
    *   O serviço `app` e `evolution-api` estão na mesma rede Docker (`app-network`).
    *   Uma requisição de teste da `app` para um endpoint conhecido da `evolution-api` (após configuração da `EVOLUTION_API_KEY`) retorna uma resposta esperada.
    *   A `EVOLUTION_API_KEY` usada pela `app` para se autenticar na `evolution-api` é configurável via variáveis de ambiente.

### 10.6. Como Desenvolvedor, quero acessar as interfaces de gerenciamento de serviços como RabbitMQ e Minio

*   **ID**: US-006
*   **Descrição**: Como um DevApp, quero poder acessar as interfaces de usuário web do RabbitMQ (Management Plugin) e Minio (Console) através do meu navegador no `localhost` para monitorar e gerenciar esses serviços.
*   **Critérios de Aceitação**:
    *   A porta `15672` do RabbitMQ está mapeada para `localhost:15672`. Acessar essa URL exibe a UI de login.
    *   A porta `9001` (console) do Minio está mapeada para `localhost:9001`. Acessar essa URL exibe a UI de login do Minio.

### 10.7. Como Engenheiro de DevOps, quero que os serviços tenham healthchecks para garantir sua prontidão

*   **ID**: US-007
*   **Descrição**: Como um Engenheiro de DevOps (DevOpsEng), quero que serviços críticos como RabbitMQ e Minio (e opcionalmente outros) tenham `healthchecks` configurados no `docker-compose.yaml` para que o Docker possa verificar seu estado de saúde e para que serviços dependentes possam esperar pela sua prontidão.
*   **Critérios de Aceitação**:
    *   O serviço `rabbitmq` possui uma seção `healthcheck` que utiliza `rabbitmq-diagnostics check_port_connectivity` ou similar.
    *   O serviço `minio` possui uma seção `healthcheck` que utiliza `mc ready local` ou similar.
    *   Serviços que dependem destes (via `depends_on`) podem usar a condição `service_healthy`.

### 10.8. Como Desenvolvedor, quero poder visualizar logs agregados e individuais dos serviços

*   **ID**: US-008
*   **Descrição**: Como um DevApp, quero poder visualizar os logs de todos os serviços de forma agregada ou de um serviço específico para depurar problemas.
*   **Critérios de Aceitação**:
    *   `docker-compose logs` exibe os logs de todos os serviços.
    *   `docker-compose logs -f <nome_do_servico>` exibe os logs em tempo real do serviço especificado (ex: `app`, `evolution-api`).

### 10.9. Como Desenvolvedor, quero que a API de áudio (`audio-converter`) esteja funcional e acessível pela Evolution API

*   **ID**: US-009
*   **Descrição**: Como um DevApp, quero que o serviço `audio-converter` esteja corretamente configurado e que a `evolution-api` possa utilizá-lo para processamento de áudio, conforme configurado nas variáveis de ambiente.
*   **Critérios de Aceitação**:
    *   O serviço `audio-converter` inicia corretamente.
    *   A variável `API_AUDIO_CONVERTER` no serviço `evolution-api` está configurada para `http://audio-converter:4040/process-audio`.
    *   A `evolution-api` consegue enviar requisições para o `audio-converter` e processar áudios (verificável através de logs ou funcionalidade específica da Evolution API que use conversão de áudio).

### 10.10. Como Desenvolvedor, quero que a autenticação na Evolution API seja segura e configurável

*   **ID**: US-010
*   **Descrição**: Como um DevApp, quero que a chave de API (`AUTHENTICATION_API_KEY`) para a `evolution-api` seja configurável via variáveis de ambiente e que a minha aplicação `app` utilize uma chave de API (`EVOLUTION_API_KEY`) também configurável para se comunicar com ela.
*   **Critérios de Aceitação**:
    *   A `AUTHENTICATION_API_KEY` da `evolution-api` é definida no `.env` e carregada pelo serviço.
    *   A `EVOLUTION_API_KEY` que a `app` usa para se conectar à `evolution-api` é definida no `.env` e carregada pela `app`.
    *   A comunicação entre `app` e `evolution-api` só é bem-sucedida se as chaves estiverem corretamente configuradas. 