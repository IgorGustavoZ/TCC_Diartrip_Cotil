# Diartrip — Guia Docker

Este guia permite rodar toda a aplicação com **um único comando**, sem instalar MySQL, Redis ou configurar ambientes locais.

---

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inclui Docker e Docker Compose)
- Conta no [Cloudinary](https://cloudinary.com) (gratuita) para upload de imagens
- Conta no [OpenRouter](https://openrouter.ai) (gratuita) para o chat com IA

---

## Primeira execução

### 1. Configure o arquivo `.env`

```bash
cp backend/.env.example backend/.env
```

Abra `backend/.env` e preencha os campos obrigatórios:

```env
SECRET_KEY=          # python -c "import secrets; print(secrets.token_hex(32))"
OPENROUTER_API_KEY=  # chave do OpenRouter
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

As variáveis de banco e Redis já vêm preenchidas para o Docker (`DB_HOST=db`, `REDIS_URL=redis://redis:6379/0`).

### 2. Suba os containers

```bash
docker compose up --build
```

Na primeira execução, o Docker irá:
1. Baixar as imagens (`python:3.11-slim`, `mysql:8.0`, `redis:7-alpine`)
2. Instalar as dependências Python
3. Criar o banco de dados e aplicar o schema inicial
4. Iniciar a API com hot reload

A API estará disponível em: **http://localhost:8000**

> **Nota:** Na primeira vez, o MySQL leva ~20–30 segundos para inicializar. O backend aguarda automaticamente via `depends_on` com `condition: service_healthy`.

---

## Comandos do dia a dia

### Subir em background

```bash
docker compose up -d
```

### Ver logs em tempo real

```bash
# Todos os serviços
docker compose logs -f

# Apenas o backend
docker compose logs -f backend

# Apenas o banco
docker compose logs -f db
```

### Reiniciar um serviço específico

```bash
docker compose restart backend
```

### Derrubar os containers (dados preservados)

```bash
docker compose down
```

### Derrubar e apagar todos os dados (MySQL + Redis)

```bash
docker compose down -v
```

---

## Rodar os testes

Os testes do backend usam **mocks completos** de MySQL, Redis e Cloudinary — nenhum serviço externo é necessário.

```bash
# Roda os testes dentro do container backend
docker compose run --rm backend pytest

# Com cobertura de código
docker compose run --rm backend pytest --cov=. --cov-report=term-missing

# Um arquivo específico
docker compose run --rm backend pytest tests/test_gastos.py -v
```

---

## Conectar ao banco de dados com uma ferramenta externa

O MySQL fica exposto na porta `3306` do host. Use DBeaver, TablePlus ou MySQL Workbench com:

| Campo    | Valor           |
|----------|-----------------|
| Host     | `localhost`     |
| Porta    | `3306`          |
| Banco    | `diartrip`      |
| Usuário  | `diartrip_user` |
| Senha    | `diartrip_pass` |

---

## Estrutura dos containers

```
docker-compose.yml
│
├── backend        → FastAPI com hot reload (porta 8000)
│   ├── Dockerfile  (python:3.11-slim, usuário não-root)
│   └── .env        (variáveis de ambiente)
│
├── db             → MySQL 8.0 (porta 3306)
│   └── docker/mysql/init/01-schema.sql  (criado na primeira vez)
│
└── redis          → Redis 7 com persistência AOF (porta 6379)
```

### Volumes persistentes

| Volume             | Conteúdo                      |
|--------------------|-------------------------------|
| `diartrip-mysql-data` | Dados do banco MySQL       |
| `diartrip-redis-data` | Dados do Redis (blacklist, rate limit) |

---

## Migrar o banco existente para o Docker

Se você já tem um banco local com dados:

```bash
# 1. Exportar schema + dados do banco local
mysqldump -u root -p diartrip > backup_diartrip.sql

# 2. Suba apenas o MySQL primeiro
docker compose up -d db
# Aguarde ficar healthy (~30s)

# 3. Importe o backup
docker compose exec -i db mysql -u diartrip_user -pdiartrip_pass diartrip < backup_diartrip.sql

# 4. Suba o restante
docker compose up -d
```

---

## Adicionar schema novo (sem Alembic)

O projeto não usa migrations automáticas. Para adicionar uma coluna ou tabela:

```bash
# Acesse o MySQL dentro do Docker
docker compose exec db mysql -u diartrip_user -pdiartrip_pass diartrip

# Execute seu ALTER TABLE ou CREATE TABLE
mysql> ALTER TABLE usuarios ADD COLUMN preferencias JSON NULL;
```

Atualize também o arquivo `docker/mysql/init/01-schema.sql` para que novos ambientes recebam a mudança automaticamente.

---

## Rebuild após mudar dependências

Se você alterar o `requirements.txt`:

```bash
docker compose up --build backend
```

---

## Variáveis de ambiente de referência

| Variável              | Padrão Docker            | Descrição                              |
|-----------------------|--------------------------|----------------------------------------|
| `DB_HOST`             | `db`                     | Nome do serviço MySQL no Compose       |
| `DB_USER`             | `diartrip_user`          | Usuário do banco                       |
| `DB_PASSWORD`         | `diartrip_pass`          | Senha do banco                         |
| `DB_NAME`             | `diartrip`               | Nome do banco                          |
| `REDIS_URL`           | `redis://redis:6379/0`   | URL do Redis                           |
| `SECRET_KEY`          | —                        | Chave JWT (obrigatória, gere com Python) |
| `OPENROUTER_API_KEY`  | —                        | Chave OpenRouter para IA               |
| `CLOUDINARY_*`        | —                        | Credenciais Cloudinary para imagens    |
| `ALLOWED_ORIGINS`     | `http://localhost:8000`  | CORS                                   |
| `ENVIRONMENT`         | `development`            | `development` ou `production`          |

---

## Healthchecks

Todos os serviços possuem healthcheck configurado:

| Serviço   | Verificação                          | Intervalo |
|-----------|--------------------------------------|-----------|
| `backend` | `GET /health` → HTTP 200             | 30s       |
| `db`      | `mysqladmin ping`                    | 10s       |
| `redis`   | `redis-cli ping`                     | 10s       |

O backend só inicia após `db` e `redis` estarem healthy.

---

## CI/CD — GitHub Actions

O workflow `.github/workflows/ci.yml` executa automaticamente em push para `main` ou `develop`:

- **backend**: `pytest` com cobertura mínima de 70%
- **docker-build**: valida que `docker build` não quebra
- **flutter**: testes unit + widget + análise estática
- **flutter-web**: testes no Chrome
- **flutter-windows**: testes no Windows

---

## Segurança

O Dockerfile aplica boas práticas:
- **Usuário não-root** (`appuser`) — o processo nunca roda como root
- **Multi-stage build** — dependências de build não entram na imagem final
- **`python:3.11-slim`** — imagem mínima sem pacotes desnecessários
- **`.dockerignore`** — `venv/`, `.env`, `__pycache__`, `.git` excluídos do contexto

> Nunca comite o arquivo `.env`. Ele está no `.gitignore` por padrão.
