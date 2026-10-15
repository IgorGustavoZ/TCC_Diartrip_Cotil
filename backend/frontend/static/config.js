// Configuração pública do frontend — nenhum valor aqui é secreto (o Client ID
// do Google é, por design, público: ele só identifica QUAL app está pedindo
// login, a validação de segredo de verdade acontece no backend). Centralizado
// aqui porque login.html e form.html usavam o mesmo valor copiado em cada
// arquivo, com risco de ficarem dessincronizados se um dia precisar trocar.
const DIARTRIP_GOOGLE_CLIENT_ID = "1004804130906-g5hfe3u1jkpavpmafjm3vctrnp0kc6bh.apps.googleusercontent.com"
