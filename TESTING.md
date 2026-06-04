# Guia de Testes — Diartrip

## Sumário

- [Visão geral](#visão-geral)
- [Diagnóstico e matriz de risco](#diagnóstico-e-matriz-de-risco)
- [Backend (Python / pytest)](#backend-python--pytest)
- [Flutter (unit + widget)](#flutter-unit--widget)
- [Flutter Integration Tests](#flutter-integration-tests)
- [Flutter Web (Chrome)](#flutter-web-chrome)
- [Flutter Desktop (Windows)](#flutter-desktop-windows)
- [Cobertura de código](#cobertura-de-código)
- [CI/CD — GitHub Actions](#cicd--github-actions)
- [Como criar novos testes](#como-criar-novos-testes)

---

## Visão geral

| Camada | Framework | Localização | Cobertura-alvo |
|--------|-----------|-------------|----------------|
| Backend API | pytest + unittest.mock | `backend/tests/` | ≥ 70 % |
| Flutter models | flutter_test | `diartrip_flutter/test/unit/models/` | 100 % |
| Flutter core | flutter_test | `diartrip_flutter/test/unit/core/` | 100 % |
| Flutter providers | flutter_test + http_mock_adapter | `diartrip_flutter/test/unit/providers/` | ≥ 80 % |
| Flutter widgets | flutter_test | `diartrip_flutter/test/widget/` | ≥ 80 % |
| Flutter integração | integration_test | `diartrip_flutter/integration_test/` | fluxos críticos |

---

## Diagnóstico e matriz de risco

### Cobertura antes desta suite

| Componente | Estado anterior |
|------------|----------------|
| Backend — rotas, services, utils | **14 arquivos de teste existentes** (~3 174 linhas) |
| Flutter — models, providers, screens | **Zero** (apenas placeholder) |
| CI/CD | **Nenhum workflow** configurado |

### Fluxos críticos e prioridade

| Fluxo | Prioridade | Coberto por |
|-------|-----------|-------------|
| Login / logout | Alta | `test_auth.py`, `auth_provider_test.dart`, `login_screen_test.dart`, `app_test.dart` |
| Cadastro de usuário | Alta | `test_usuarios.py`, `register_screen_test.dart`, `app_test.dart` |
| JWT — criação, decode, revogação | Alta | `test_security.py`, `auth_provider_test.dart` |
| CSRF protection | Alta | `test_auth.py` (CsrfTestClient) |
| Rate limiting | Alta | `test_chat_ia.py`, `test_utils.py` |
| Grupos — CRUD + convite | Alta | `test_grupos.py`, `grupo_test.dart` |
| Gastos — divisão decimal | Alta | `test_gastos.py`, `test_budget_calc.py`, `gasto_test.dart` |
| Dashboard — cálculos | Média | `test_dashboard.py`, `dashboard_test.dart` |
| Chat IA — prompt injection | Alta | `test_chat_ia.py` |
| Posts / Feed | Média | `test_posts.py`, `post_test.dart` |
| Roteiros | Baixa | `test_roteiros.py`, `roteiro_test.dart` |
| Upload de fotos | Média | `test_fotos.py` |
| WebSocket — chat grupo | Média | `test_api_full.py` |
| Serialização Flutter models | Alta | `*_test.dart` em `unit/models/` |
| apiError — extração de mensagens | Alta | `api_client_test.dart` |

---

## Backend (Python / pytest)

### Pré-requisitos

```bash
cd backend
pip install -r requirements.txt pytest-cov
```

> O banco **não é necessário**: todos os testes usam `MagicMock` para o MySQL
> e fallback em memória para o Redis (`REDIS_URL=""`).

### Executar todos os testes

```bash
cd backend
pytest
```

### Executar com cobertura

```bash
pytest --cov=. --cov-omit="tests/*,conftest.py" --cov-report=term-missing
```

### Executar um arquivo específico

```bash
pytest tests/test_auth.py -v
pytest tests/test_gastos.py -v -k "divisao"
```

### Estrutura dos testes

```
backend/
├── conftest.py              # fixtures raiz (limpeza de DB)
└── tests/
    ├── conftest.py          # fixtures globais: mocks de DB/Redis/Cloudinary,
    │                        # CsrfTestClient, make_cursor, fake_get_db, factories
    ├── test_auth.py         # login, logout, JWT, cookies
    ├── test_security.py     # criação/decode de JWT, bcrypt, revogação de token
    ├── test_usuarios.py     # CRUD de usuário, validação de senha, foto de perfil
    ├── test_grupos.py       # CRUD de grupo, busca, código de convite
    ├── test_gastos.py       # despesas, divisão, balanço
    ├── test_fotos.py        # upload/validação de imagem (magic bytes, tamanho)
    ├── test_dashboard.py    # cálculos de percentual e categorias
    ├── test_chat_ia.py      # prompt building, rate limit, injeção de prompt
    ├── test_posts.py        # feed social
    ├── test_roteiros.py     # itinerários
    ├── test_api_full.py     # cenários end-to-end multi-rota
    ├── test_budget_calc.py  # precisão decimal na divisão de gastos
    └── test_utils.py        # funções utilitárias
```

### Variáveis de ambiente para testes

O `conftest.py` seta automaticamente todas as variáveis necessárias via
`os.environ.setdefault`. Não é necessário criar `.env` para rodar os testes.

---

## Flutter (unit + widget)

### Pré-requisitos

```bash
cd diartrip_flutter
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```

### Executar todos os testes unitários e de widget

```bash
flutter test test/
```

### Executar por categoria

```bash
# Apenas models
flutter test test/unit/models/

# Apenas providers
flutter test test/unit/providers/

# Apenas core (apiError, etc.)
flutter test test/unit/core/

# Apenas widgets
flutter test test/widget/
```

### Executar com cobertura

```bash
flutter test test/ --coverage
# Relatório HTML (requer lcov instalado):
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

### Estrutura dos testes Flutter

```
diartrip_flutter/
├── test/
│   ├── unit/
│   │   ├── models/
│   │   │   ├── usuario_test.dart    # fromJson, iniciais (edge cases)
│   │   │   ├── grupo_test.dart      # fromJson, Membro.isAdmin
│   │   │   ├── gasto_test.dart      # fromJson, divisão, nulos
│   │   │   ├── roteiro_test.dart    # fromJson, descrição nula
│   │   │   ├── post_test.dart       # fromJson, campos opcionais
│   │   │   ├── mensagem_test.dart   # fromJson, campos ausentes
│   │   │   └── dashboard_test.dart  # todos os submodels de dashboard
│   │   ├── core/
│   │   │   └── api_client_test.dart # apiError — 11 cenários
│   │   └── providers/
│   │       └── auth_provider_test.dart  # tryAutoLogin, login, logout, update
│   └── widget/
│       ├── helpers/
│       │   └── fake_auth_provider.dart  # FakeAuthProvider sem rede
│       ├── login_screen_test.dart       # renderização, validação, loading, toggle
│       └── register_screen_test.dart    # renderização, validação, loading, toggle
└── integration_test/
    └── app_test.dart
```

### Como funciona o FakeAuthProvider

Todos os widget tests usam `FakeAuthProvider` em vez do `AuthProvider` real,
eliminando qualquer dependência de rede:

```dart
final auth = FakeAuthProvider();
auth.loginError = Exception('Credenciais inválidas'); // simula falha
// ou
auth.setLoading(true); // simula estado de carregamento
```

### Como o AuthProvider é testado com rede mockada

O `auth_provider_test.dart` inicializa `dio` com `DioAdapter` de
`http_mock_adapter`, interceptando chamadas HTTP sem tocar na rede real:

```dart
setUpAll(() {
  api.cookieJar = DefaultCookieJar();
  api.dio = Dio(BaseOptions(baseUrl: 'http://test.local', ...));
  dioAdapter = DioAdapter(dio: api.dio);
});

// Em cada teste:
dioAdapter.onGet('/usuarios/me', (server) => server.reply(200, {...}));
```

---

## Flutter Integration Tests

Os integration tests requerem o **backend FastAPI rodando** e um
**usuário de teste pré-cadastrado**.

### Criar usuário de teste no backend

```bash
curl -X POST http://127.0.0.1:8000/usuarios \
  -H "Content-Type: application/json" \
  -d '{"nome":"Integration Tester","email":"integration@diartrip.test","senha":"Teste1234"}'
```

### Executar

```bash
cd diartrip_flutter

# Dispositivo padrão (emulador/simulador conectado)
flutter test integration_test/app_test.dart

# Chrome
flutter test integration_test/app_test.dart --platform chrome

# Windows Desktop
flutter test integration_test/app_test.dart -d windows
```

### Fluxos cobertos

| Teste | Descrição |
|-------|-----------|
| App sobe sem erros | Verifica splash screen ou tela de login |
| Login renderiza | Campos, botão e links presentes |
| Login credenciais inválidas | Exibe mensagem de erro |
| Login credenciais válidas | Navega para lobby |
| Cadastro abre a partir do login | Navega para RegisterScreen |
| Formulário de cadastro valida | Erros de validação funcionam |
| Drawer de navegação | Acessível na tela autenticada |

---

## Flutter Web (Chrome)

```bash
cd diartrip_flutter
flutter test test/unit test/widget --platform chrome
```

> Os integration tests com `--platform chrome` requerem `chromedriver` instalado
> e o backend rodando.

---

## Flutter Desktop (Windows)

```bash
cd diartrip_flutter

# Testes unitários e de widget (sem backend)
flutter test test/unit test/widget

# Integration tests (requer backend)
flutter test integration_test/app_test.dart -d windows

# Build de verificação
flutter build windows --release
```

---

## Cobertura de código

### Backend

```bash
cd backend
pytest --cov=. --cov-omit="tests/*,conftest.py" --cov-report=html:htmlcov
# Abre htmlcov/index.html no browser
```

Meta: **≥ 70 %** de linhas (CI falha abaixo disso via `--cov-fail-under=70`).

### Flutter

```bash
cd diartrip_flutter
flutter test test/ --coverage
# Requer lcov:
genhtml coverage/lcov.info -o coverage/html
```

Meta: **≥ 80 %** de linhas para `lib/models/` e `lib/core/`.

---

## CI/CD — GitHub Actions

O arquivo `.github/workflows/ci.yml` executa 4 jobs em paralelo a cada
push ou pull request para `main` / `develop`:

| Job | Runner | O que faz |
|-----|--------|-----------|
| `backend` | ubuntu-latest | `pytest --cov` + upload para Codecov |
| `flutter` | ubuntu-latest | `flutter analyze` + `flutter test` + coverage |
| `flutter-web` | ubuntu-latest | `flutter test --platform chrome` |
| `flutter-windows` | windows-latest | `flutter test` no Windows |
| `all-checks` | ubuntu-latest | Falha se qualquer job acima falhar |

### Segredos necessários (opcionais para Codecov)

```
CODECOV_TOKEN   → token do projeto em codecov.io
```

### Ver status no GitHub

Após o primeiro push, acesse:
`https://github.com/<seu-usuario>/ProjetoDiartrip/actions`

---

## Como criar novos testes

### Novo model Flutter

1. Crie `test/unit/models/<nome>_test.dart`
2. Importe o model: `import 'package:diartrip_flutter/models/<nome>.dart';`
3. Teste `fromJson` com:
   - campos obrigatórios
   - campos opcionais ausentes/nulos
   - tipos numéricos (int → double)
   - edge cases (strings vazias, listas vazias)

```dart
test('campos obrigatórios mapeados', () {
  final obj = MeuModel.fromJson({'id': 1, 'nome': 'X'});
  expect(obj.id, 1);
  expect(obj.nome, 'X');
});
```

### Novo widget test

1. Crie `test/widget/<nome>_test.dart`
2. Use `FakeAuthProvider` para substituir o provider real
3. Use `_buildSubject()` com `MaterialApp` + rotas básicas
4. Teste: renderização, validação, estados de loading, navegação

```dart
testWidgets('meu widget renderiza', (tester) async {
  await tester.pumpWidget(_buildSubject());
  expect(find.text('Meu Texto'), findsOneWidget);
});
```

### Novo teste de backend

1. Crie `backend/tests/test_<feature>.py`
2. Use os fixtures de `conftest.py`: `client`, `client_usuario`, `client_admin`
3. Para controlar o DB: `make_cursor(rows=[...])` + `patch("database.get_db", fake_get_db(conn))`

```python
def test_minha_rota(client_usuario):
    cursor = make_cursor(rows=[{"id": 1, "nome": "X"}])
    conn = make_connection(cursor)
    with patch("database.get_db", fake_get_db(conn)):
        resp = client_usuario.get("/minha-rota")
    assert resp.status_code == 200
```

### Novo integration test

Adicione um `group` em `integration_test/app_test.dart`:

```dart
group('Meu fluxo', () {
  testWidgets('descrição', (tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 4));
    // ...interações...
  });
});
```

---

## Referência rápida

```bash
# Backend
cd backend && pytest                         # todos os testes
cd backend && pytest -k "test_login"         # filtrar por nome
cd backend && pytest --co -q                 # listar testes sem rodar

# Flutter
cd diartrip_flutter
flutter test test/                           # unit + widget
flutter test test/ --coverage                # com cobertura
flutter test test/ --platform chrome         # web
flutter test integration_test/app_test.dart  # integração
flutter analyze                              # lint
dart run build_runner build                  # gerar mocks
```
