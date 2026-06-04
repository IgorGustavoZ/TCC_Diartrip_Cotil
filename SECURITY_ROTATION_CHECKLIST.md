# Checklist de Rotação de Credenciais — Diartrip

> **URGENTE:** As credenciais abaixo foram expostas em commits públicos do repositório.
> Trate-as como comprometidas e rotacione IMEDIATAMENTE, mesmo que o repositório
> seja privado — git history preserva o histórico mesmo após remoção.

---

## 🔴 Ação Imediata (já expostas no git)

### 1. Banco de Dados MySQL
- **Credenciais:** foram expostas em commits anteriores — valores removidos deste arquivo
- **Ação:**
  - [ ] Alterar senha do usuário MySQL
  - [ ] Verificar logs de acesso por IPs desconhecidos
  - [ ] Criar novo usuário com senha forte (≥ 32 chars aleatórios)
  - [ ] Restringir acesso por IP no firewall do servidor MySQL

### 2. JWT Secret Key
- **Chave:** foi exposta em commits anteriores — valor removido deste arquivo
- **Impacto:** Qualquer pessoa pode forjar tokens JWT válidos para qualquer usuário
- **Ação:**
  - [ ] Gerar nova chave com `python -c "import secrets; print(secrets.token_hex(64))"`
  - [ ] **TODOS os tokens existentes tornam-se inválidos** — usuários precisarão re-logar
  - [ ] Atualizar `SECRET_KEY` no servidor de produção ANTES de publicar

### 3. OpenRouter API Key
- **Chave:** foi exposta em commits anteriores — valor removido deste arquivo
- **Impacto:** Uso da sua cota de IA (geração de texto paga) por terceiros
- **Ação:**
  - [ ] Revogar a chave exposta
  - [ ] Gerar nova chave
  - [ ] Verificar logs de uso por chamadas suspeitas

### 4. Cloudinary Credentials
- **Credenciais:** foram expostas em commits anteriores — valores removidos deste arquivo
- **Impacto:** Upload/delete de imagens ilimitado na sua conta Cloudinary
- **Ação:**
  - [ ] Acessar https://cloudinary.com/console/settings/api-keys
  - [ ] Revogar o API Key/Secret exposto
  - [ ] Gerar novo par de credenciais
  - [ ] Verificar se imagens foram deletadas ou modificadas maliciosamente

### 5. MySQL Root Password (docker-compose)
- **Senha:** foi exposta em commits anteriores — valor removido deste arquivo
- **Ação:**
  - [ ] Alterar `MYSQL_ROOT_PASSWORD` em qualquer ambiente que usou este compose
  - [ ] Verificar se o container MySQL tem porta exposta publicamente

---

## Como gerar credenciais seguras

```bash
# JWT Secret Key (64 bytes = 128 chars hex)
python -c "import secrets; print(secrets.token_hex(64))"

# Senha de banco de dados forte
python -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%'; print(''.join(secrets.choice(chars) for _ in range(32)))"
```

---

## Como remover do histórico git (se necessário)

Se o repositório for público ou você quiser limpar o histórico:

```bash
# Usando git-filter-repo (recomendado)
pip install git-filter-repo
git filter-repo --path backend/.env --invert-paths
git filter-repo --path .env.example --invert-paths

# Forçar push (DESTRUTIVO — avise colaboradores)
git push origin --force --all
git push origin --force --tags
```

> Nota: Mesmo após limpeza do histórico, credenciais já expostas devem ser
> consideradas comprometidas e rotacionadas.

---

## Prevenção futura

O arquivo `.gitignore` foi criado/atualizado com as seguintes regras:
- `backend/.env` nunca será rastreado
- `*.env` nunca será rastreado
- Apenas `*.env.example` (sem valores reais) é permitido

**Verificação antes de cada commit:**
```bash
git status  # confirme que .env não aparece como "Changes to be committed"
git diff --cached --name-only | grep -E "\.env$"  # deve retornar vazio
```
