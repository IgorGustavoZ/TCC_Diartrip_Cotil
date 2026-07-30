# Diartrip

Plataforma de gerenciamento de viagens em grupo com app mobile (Flutter), app desktop (C# WPF) e API REST (Python/FastAPI).

## Tecnologias

### Backend (API)
- Python 3.11+
- FastAPI
- MySQL (connection pool com retry automático)
- Redis (rate limiting e blacklist de tokens)
- Uvicorn
- Docker / Docker Compose
- bcrypt (senhas)
- JWT (autenticação via Cookies HttpOnly)
- Pydantic v2 (validação de dados e limites)
- OpenAI SDK via OpenRouter (IA)
- Cloudinary (upload e hospedagem de imagens)
- pytest (testes automatizados E2E)
- python-multipart (upload de arquivos)
- Decimal (precisão financeira)

### Mobile (Flutter)
- Flutter 3.41.5 / Dart SDK ≥ 3.0
- Dio + cookie_jar (HTTP com CSRF automático)
- web_socket_channel (chat em tempo real via WebSocket)
- Provider (gerenciamento de estado)
- image_picker + crop_your_image (câmera e recorte)
- cached_network_image (cache de imagens)
- flutter_markdown (renderização de respostas da IA)
- Sentry (crash reporting em produção)
- mockito + http_mock_adapter (testes)

### Desktop (C# WPF)
- .NET 8 / WPF
- QuestPDF (geração de relatórios em PDF)
- PDFsharp (manipulação de PDF)

### CI/CD
- GitHub Actions (pytest + cobertura ≥ 70 %, flutter analyze + testes ≥ 80 %, docker build)
- Codecov (relatórios de cobertura)

---

## Funcionalidades

### Autenticação
- Login com JWT (token válido por 2 horas)
- Armazenamento seguro via Cookies HttpOnly
- Verificação de estado do usuário no banco em cada requisição

### Usuários
- Criar usuário com senha criptografada (bcrypt)
- Atualizar perfil com biografia e foto (validação de magic bytes)
- Deletar própria conta

### Grupos de viagem
- Criar grupo (admin automático) com código de convite único
- Gestão de membros com proteção contra race conditions (FOR UPDATE)
- Exclusão em cascata completa de todos os dados do grupo

### Gastos e Balanço
- Registro de gastos com divisão automática entre membros
- **Precisão Financeira**: uso de Decimal para evitar erros de arredondamento
- Balanço dinâmico de débitos e créditos entre participantes
- Dashboard geral, pessoal e administrativo
- Exportação de relatório em PDF (desktop)

### Chat em Tempo Real
- WebSocket por grupo (sem polling)
- Mensagens entregues instantaneamente a todos os membros conectados

### Chat IA
- Assistente contextualizado por viagem (destino, orçamento, datas)
- Processamento assíncrono para não travar o pool de conexões do banco
- Histórico de mensagens por grupo

---

## Segurança e Arquitetura

- **Service Layer**: lógica de negócio isolada em `services/`
- **Integridade**: Transações com rollback automático via context manager
- **Proteção de Upload**: Validação de magic bytes para impedir arquivos maliciosos
- **Rate Limiting**: Proteção anti-spam no chat e cadastro

---

## Como executar

### API — Com Docker (recomendado)

**Pré-requisitos:** Docker Desktop instalado e rodando.

```bash
# 1. Configure o ambiente
cp backend/.env.example backend/.env
# Edite backend/.env e preencha SECRET_KEY e as demais variáveis

# 2. Primeira execução (cria volumes e aplica o schema)
docker compose up --build

# 3. Execuções seguintes
docker compose up
```

A API estará disponível em `http://localhost:8000`.  
Para parar: `docker compose down`. Para resetar o banco: `docker compose down -v`.

> **Nota:** Se a porta 3306 já estiver em uso localmente, altere `MYSQL_HOST_PORT=3307` no `backend/.env` (o container sempre usa 3306 internamente).

---

### API — Sem Docker (ambiente local)

```bash
# 1. Ambiente
python -m venv venv
# Ativar venv
pip install -r requirements.txt

# 2. Configurar .env
# Preencha as variáveis de banco, JWT e APIs conforme o backend/.env.example
# Certifique-se de que MySQL e Redis estejam rodando localmente

# 3. Executar
cd backend
uvicorn main:app --reload
```

---

### App Mobile (Flutter)

**Pré-requisitos:** Flutter SDK 3.41.5+ instalado.

```bash
cd diartrip_flutter

# Instalar dependências e gerar mocks
flutter pub get
dart run build_runner build --delete-conflicting-outputs

# Rodar (escolha o dispositivo/emulador)
flutter run

# Rodar no Chrome (web)
flutter run -d chrome
```

> Certifique-se de que a API está rodando e que o endereço base no app aponta para `http://localhost:8000`.

---

### App Desktop (C# WPF)

**Pré-requisitos:** .NET 8 SDK instalado.

```bash
# Login
cd desktop/frmLogin
dotnet run

# Lobby (após login)
cd desktop/frmLobby
dotnet run
```

Ou abra a solução no Visual Studio e pressione F5.

---

## Testes

### Backend
```bash
pytest tests/test_api_full.py -v
```
A suíte de testes valida o fluxo completo: criação de usuários, grupos, gastos, balanço financeiro e travas de segurança.

### Flutter
```bash
cd diartrip_flutter

# Unit + widget
flutter test test/unit test/widget --reporter expanded

# No Chrome
flutter test test/unit test/widget --platform chrome --reporter expanded
```

---

## Estrutura

```text
├── README.md
├── docker-compose.yml
├── docker/
│   └── mysql/init/      → Schema SQL aplicado na criação do banco
├── docs/
│   ├── DOCKER.md        → Guia Docker detalhado
│   └── TESTING.md       → Guia de testes
├── scripts/             → Scripts de utilidade
├── backend/
│   ├── frontend/        → HTML + CSS + JS + imagens (servidos pelo FastAPI)
│   │   ├── index.html
│   │   ├── lobby.html
│   │   ├── login.html
│   │   ├── form.html
│   │   ├── lobby-pags/
│   │   ├── static/
│   │   └── imagens/
│   ├── routes/          → Controladores HTTP
│   ├── services/        → Lógica de negócio e acesso ao MySQL
│   ├── utils/           → Autenticação, segurança, rate limit
│   ├── tests/           → Testes automatizados (pytest)
│   ├── alembic/         → Migrações de banco
│   ├── main.py          → Inicialização e rotas
│   ├── database.py      → Pool de conexões MySQL (lazy init com retry)
│   ├── schemas.py       → Schemas Pydantic
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example     → Template de variáveis de ambiente
├── diartrip_flutter/    → App mobile Flutter
└── desktop/             → App desktop C# WPF (.NET 8)
```
