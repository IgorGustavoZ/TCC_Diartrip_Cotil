// Regra ÚNICA de "viagem passada" do Web — a mesma do app Flutter
// (Grupo.jaPassou em diartrip_flutter/lib/models/grupo.dart):
//   - a data de referência é o fim da viagem (ou o início, se não houver fim);
//   - passada = essa data é ANTERIOR a hoje, comparando só o dia (sem hora).
//     Viagem que termina hoje, em andamento ou sem data nenhuma NÃO é passada.
//
// Toda página que precisa decidir se uma viagem já passou (Lobby, viagem.html
// — Visão Geral, Gastos, Roteiro, Informações, Administração) deve usar esta
// função, para que nenhuma tela trate a mesma viagem de forma diferente.
// `viagem` é o objeto que a API já devolve ({data_inicio, data_fim, ...});
// `hoje` só existe para tornar a regra testável.
function viagemJaPassou(viagem, hoje) {
    if (!viagem) return false
    const ref = viagem.data_fim || viagem.data_inicio
    if (!ref) return false
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(ref))
    if (!m) return false
    const data = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
    if (isNaN(data.getTime())) return false
    const agora = hoje || new Date()
    const hojeSemHora = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate())
    return data < hojeSemHora
}
