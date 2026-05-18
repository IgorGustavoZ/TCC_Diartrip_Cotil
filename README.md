# Diartrip API

API REST feita em Python usando FastAPI para gerenciamento de viagens em grupo.

## Tecnologias
- Python 3.12+
- FastAPI
- MySQL (connection pool)
- Uvicorn
- bcrypt (senhas)
- JWT (autenticação Bearer)
- PyJWT
- Pydantic v2 (validação com EmailStr)
- OpenAI SDK via OpenRouter (IA)
- pytest (testes automatizados)
- python-multipart (upload de arquivos)
- email-validator

---

## Funcionalidades

### Autenticação
- Login com JWT (token válido por 2 horas)
- Proteção de todas as rotas com token Bearer
- Validação de formato de e-mail no cadastro

### Usuários
- Criar usuário com senha criptografada (bcrypt)
- Visualizar perfil próprio ou de outros usuários
- Atualizar próprio perfil
- Deletar própria conta

### Grupos de viagem
- Criar grupo (criador vira admin automaticamente)
- Definir destino, datas, tipo, preferências e orçamento
- Listar e buscar grupos do usuário
- Atualizar grupo (apenas admin)
- Deletar grupo com cascata completa (apenas admin)
- Entrar em grupo por código de convite
- Código de convite gerado automaticamente na criação

### Membros do grupo
- Listar membros do grupo
- Adicionar membro por ID (apenas admin)
- Remover membro (admin ou o próprio usuário)
- Promover membro para admin
- Rebaixar admin para membro comum
- Sair do grupo
- Proteção contra remoção do último admin com membros ativos

### Roteiros
- Criar roteiro (qualquer membro do grupo)
- Listar roteiros do usuário
- Buscar roteiro por ID
- Atualizar roteiro (qualquer membro)
- Deletar roteiro (apenas admin)

### Gastos
- Registrar gasto (membro do grupo)
- Divisão de valor entre membros verificados do grupo
- Listar gastos do grupo
- Balanço financeiro por membro (a pagar / a receber)
- Atualizar gasto (dono ou admin)
- Deletar gasto (dono ou admin)

### Dashboard
- Visão geral: orçamento total, consumido, restante e distribuição por categoria
- Visão pessoal: quanto paguei, minhas dívidas, últimos gastos
- Painel admin: ranking de gastos, contagem de membros, fotos e roteiros

### Fotos
- Upload de imagens (JPG, PNG, WebP)
- Validação de magic bytes (não apenas extensão)
- Limite de 5 MB por arquivo
- Listar fotos do grupo
- Deletar foto (dono ou admin)
- Servir arquivos estáticos via `/uploads`

### Feed / Posts
- Publicar post com texto e imagem opcional (até 10 MB)
- Listar feed global (100 posts mais recentes)
- Listar posts de um usuário específico
- Deletar próprio post

### Chat IA
- Integração com OpenRouter (modelo configurável via `.env`)
- Assistente contextualizado por viagem (destino, datas, orçamento, tipo)
- Histórico de conversas por grupo
- Respostas formatadas em Markdown
- Rate limit: 10 mensagens por minuto por usuário

---

## Segurança e Arquitetura

- **Service Layer**: toda lógica de banco de dados separada em `services/`
- **Permissões centralizadas**: `checar_membro_grupo()` em `utils/dependencies.py`, usado por todos os services
- **Connection pool**: `MySQLConnectionPool` com 10 conexões reutilizáveis
- **Validação de entrada**: EmailStr, magic bytes em uploads, rate limiting no chat
- **Transações**: rollback automático em caso de erro via context manager

---

## Autenticação

A API usa JWT.

### Login
```
POST /login
```

### Resposta
```json
{
  "mensagem": "Login realizado com sucesso",
  "usuario_id": 1,
  "token": "..."
}
```

### Uso do token
Enviar no header:
```
Authorization: Bearer SEU_TOKEN
```

---

## Como executar

### 1. Clone o repositório
```
git clone https://github.com/IgorGustavoZ/ProjetoDiartrip
```

### 2. Acesse a pasta
```
cd ProjetoDiatrip-main
```

### 3. Crie o ambiente virtual
```
python -m venv venv
```

### 4. Ative
```
venv\Scripts\activate
```

### 5. Instale dependências
```
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Configure o .env
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=diartrip

SECRET_KEY=sua_chave_secreta_longa
ALGORITHM=HS256

OPENROUTER_API_KEY=sua_api_key
IA_MODEL=mistralai/mistral-7b-instruct:free

ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:8000
```

### 7. Execute
```
uvicorn main:app --reload
```

### 8. Acesse a documentação
```
http://127.0.0.1:8000/docs
```

---

## Testes

```
pytest tests/
```

Os testes usam banco de dados real (sem mocks). O `conftest.py` faz limpeza automática antes e depois de cada sessão de testes.

---

## Estrutura

```
/routes          → controladores HTTP (sem SQL)
/services        → lógica de negócio e acesso ao banco
/utils           → auth, dependências de permissão, rate limiter, security
/tests           → suíte de testes pytest
/uploads         → arquivos enviados pelos usuários
/static          → assets estáticos (CSS)
/imagens         → imagens da aplicação
/lobby-pags      → páginas HTML do frontend
main.py          → inicialização do FastAPI e routers
database.py      → connection pool MySQL
conftest.py      → fixtures globais de teste
```

---

## Endpoints

### Usuários
- `POST /usuarios` — cadastrar usuário
- `GET /usuarios/me` — perfil do usuário logado
- `GET /usuarios/{id_usuario}` — buscar usuário por ID
- `PUT /usuarios/{id_usuario}` — atualizar próprio perfil
- `DELETE /usuarios/{id_usuario}` — deletar própria conta

### Login
- `POST /login`

### Grupos
- `GET /grupos` — listar grupos do usuário
- `GET /grupos/buscar?nome=...` — buscar grupos por nome
- `POST /grupos/entrar` — entrar em grupo por código de convite
- `GET /grupos/{id_grupo}` — detalhes do grupo
- `POST /grupos` — criar grupo
- `PUT /grupos/{id_grupo}` — atualizar grupo (admin)
- `DELETE /grupos/{id_grupo}` — deletar grupo (admin)

### Membros
- `GET /grupos/{id_grupo}/membros`
- `POST /grupos/{id_grupo}/membros` — adicionar membro (admin)
- `DELETE /grupos/{id_grupo}/membros/{id_usuario_remover}` — remover membro
- `PUT /grupos/{id_grupo}/membros/{id_usuario_promover}/promover` — promover para admin
- `PUT /grupos/{id_grupo}/membros/{id_usuario_rebaixar}/rebaixar` — rebaixar para membro
- `DELETE /grupos/{id_grupo}/sair` — sair do grupo

### Roteiros
- `GET /roteiros`
- `GET /roteiros/{id_roteiro}`
- `POST /roteiros`
- `PUT /roteiros/{id_roteiro}`
- `DELETE /roteiros/{id_roteiro}` — apenas admin

### Gastos
- `GET /grupos/{id_grupo}/gastos`
- `POST /grupos/{id_grupo}/gastos`
- `GET /grupos/{id_grupo}/balanco`
- `PUT /gastos/{id_gasto}`
- `DELETE /gastos/{id_gasto}`

### Dashboard
- `GET /grupos/{id_grupo}/dashboard/geral`
- `GET /grupos/{id_grupo}/dashboard/pessoal`
- `GET /grupos/{id_grupo}/dashboard/admin` — apenas admin

### Fotos
- `GET /grupos/{id_grupo}/fotos`
- `POST /grupos/{id_grupo}/fotos`
- `DELETE /fotos/{id_foto}`

### Posts / Feed
- `GET /posts` — feed global
- `GET /posts/usuario/{alvo_id}` — posts de um usuário
- `POST /posts` — publicar post
- `DELETE /posts/{id_post}`

### Chat IA
- `GET /chat` — histórico de conversas
- `POST /chat` — enviar mensagem (rate limit: 10/min)
