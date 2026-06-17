# ── Stage 1: Build Flutter Web ────────────────────────────────────────────────
# cirruslabs é a imagem Flutter Docker mais mantida e usada em CI/CD.
FROM ghcr.io/cirruslabs/flutter:stable AS builder

WORKDIR /app

# Copia pubspec primeiro — layer de cache: só re-executa pub get se pubspec mudar
COPY pubspec.yaml pubspec.lock ./

# Garante que o diretório de assets existe antes do build
RUN mkdir -p assets/images

RUN flutter pub get

# Copia o restante do código-fonte
COPY . .

# Build web em modo release (Dart compilado, tree-shaking, minificado)
# --release: remove assertions, habilita otimizações do compilador
# O renderer é escolhido automaticamente pelo Flutter (CanvasKit para melhor fidelidade)
RUN flutter build web --release

# ── Stage 2: Servir com Nginx ─────────────────────────────────────────────────
# nginx:alpine: ~7MB, suficiente para servir arquivos estáticos
FROM nginx:alpine

# Copia o build Flutter para o diretório padrão do nginx
COPY --from=builder /app/build/web /usr/share/nginx/html

# Configuração customizada: SPA routing + gzip + cache headers
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1
