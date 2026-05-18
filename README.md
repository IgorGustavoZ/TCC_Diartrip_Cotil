# fastApi-tcc

API REST feita em Python usando FastAPI para gerenciamento de viagens em grupo.

## Tecnologias
- Python
- FastAPI
- MySQL
- Uvicorn
- bcrypt
- JWT (autenticação)
- Upload de arquivos (imagens)
- Integração com IA via OpenRouter

---

## Funcionalidades

## Integração com IA

O sistema possui um assistente virtual integrado usando OpenRouter.

A IA consegue:
- sugerir roteiros
- recomendar restaurantes
- indicar pontos turísticos
- responder dúvidas sobre a viagem
- manter contexto da conversa
- considerar orçamento e preferências do usuário

A resposta é contextualizada usando:
- destino da viagem
- datas
- tipo de viagem
- preferências
- histórico recente do chat

### Autenticação
- Login com JWT
- Proteção de rotas com token Bearer

### Usuários
- Criar usuário com senha criptografada
- Listar usuários (autenticado)
- Atualizar próprio usuário
- Deletar próprio usuário

### Grupos de viagem
- ### Grupos de viagem
- Criar grupo (usuário vira admin automaticamente)
- Destino principal
- Data de início e fim
- Tipo de viagem
- Preferências do usuário
- Orçamento da viagem

### Membros do grupo
- Listar membros
- Adicionar membro (admin)
- Remover membro
- Promover membro para admin
- Sair do grupo

### Roteiros
- Criar roteiro (apenas membro do grupo)
- Listar roteiros
- Buscar roteiro por ID
- Atualizar roteiro (apenas membro)
- Deletar roteiro (apenas membro)

### Gastos
- Criar gasto (membro do grupo)
- Listar gastos do grupo
- Atualizar gasto (dono ou admin)
- Deletar gasto (dono ou admin)

### Fotos
- Upload de imagens (jpg, png, webp)
- Limite de 5MB por arquivo
- Listar fotos do grupo
- Deletar foto (dono ou admin)
- Servir arquivos estáticos via `/uploads`

### Chat IA
- Integração com OpenRouter
- Assistente contextualizado por viagem
- Histórico de conversas
- Sugestões de roteiro
- Recomendações de turismo
- Respostas formatadas em Markdown
- Contexto automático da viagem selecionada
---

## Autenticação

A API usa JWT.

### Login
```
POST /login
```

### Resposta
```
{
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
C:\Python314\python.exe -m venv venv
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
SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
OPENROUTER_API_KEY=sua_api_key
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

## Estrutura

```
/routes
/utils
/uploads
main.py
database.py
```

---

## Endpoints

### Usuários
- POST /usuarios  
- GET /usuarios  
- GET /usuarios/{id_usuario}  
- PUT /usuarios/{id_usuario}  
- DELETE /usuarios/{id_usuario}  

### Login
- POST /login  

### Grupos
- GET /grupos  
- GET /grupos/{id_grupo}  
- GET /grupos/buscar  
- POST /grupos  
- PUT /grupos/{id_grupo}  
- DELETE /grupos/{id_grupo}  

### Membros
- GET /grupos/{id_grupo}/membros  
- POST /grupos/{id_grupo}/membros  
- DELETE /grupos/{id_grupo}/membros/{id_usuario}  
- PUT /grupos/{id_grupo}/membros/{id_usuario}  
- DELETE /grupos/{id_grupo}/sair  

### Roteiros
- GET /roteiros  
- GET /roteiros/{id_roteiro}  
- POST /roteiros  
- PUT /roteiros/{id_roteiro}  
- DELETE /roteiros/{id_roteiro}  

### Gastos
- GET /grupos/{id_grupo}/gastos  
- POST /grupos/{id_grupo}/gastos  
- PUT /gastos/{id_gasto}  
- DELETE /gastos/{id_gasto}  

### Fotos
- GET /grupos/{id_grupo}/fotos  
- POST /grupos/{id_grupo}/fotos  
- DELETE /fotos/{id_foto}  

### Chat
- GET /chat  
- POST /chat   
