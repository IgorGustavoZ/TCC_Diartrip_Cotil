# Diartrip API

API REST feita em Python usando FastAPI para gerenciamento de viagens em grupo.

## Tecnologias
- Python 3.12+
- FastAPI
- MySQL (connection pool)
- Uvicorn
- bcrypt (senhas)
- JWT (autenticação via Cookies HttpOnly)
- Pydantic v2 (validação de dados e limites)
- OpenAI SDK via OpenRouter (IA)
- pytest (testes automatizados E2E)
- python-multipart (upload de arquivos)
- Decimal (precisão financeira)

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

### 1. Ambiente
```bash
python -m venv venv
# Ativar venv
pip install -r requirements.txt
```

### 2. Configurar .env
Preencha as variáveis de banco, JWT e APIs conforme o `.env.example`.

### 3. Executar
```bash
uvicorn main:app --reload
```

---

## Testes

```bash
pytest tests/test_api_full.py -v
```
A suíte de testes valida o fluxo completo: criação de usuários, grupos, gastos, balanço financeiro e travas de segurança.

---

## Estrutura

```text
/routes          → Controladores HTTP e esquemas Pydantic
/services        → Lógica de negócio e acesso ao MySQL
/utils           → Autenticação, dependências, segurança e rate limit
/tests           → Testes automatizados
/uploads         → Armazenamento local temporário
main.py          → Inicialização e rotas
database.py      → Pool de conexões MySQL
```
