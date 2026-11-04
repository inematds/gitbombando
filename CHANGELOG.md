# CHANGELOG — gitbombando

## 1.1.0 — 04/11/2026
- Gráfico de semana/mês: a curva "total por dia" dos retratos só entra quando cobre todos os dias do período (7/30);
  senão o painel mostra "antes × agora" (total − ganho → total), que bate com o "+N" do cartão.
- Capa: `pecas.abertura` sobe ou desce a arte conforme a manchete (termina acima de 800 px; topo nunca acima de 120 px),
  para a legenda do gancho e o avatar não cobrirem a manchete. `manchete()` ignora "caixas" de 600+ px (arte dourada).
- Revisor: o contador animado do painel não conta como número errado (confere a pílula 🔥 do cartão).
- `rodar.sh`: avatar já enviado (`avatar/video_id.txt`) = retoma sem refazer coleta e roteiro. `GB_PESADO=<script>` põe o
  render atrás de uma trava externa.

## 1.0.0 — 28/10/2026
- Primeira versão: coleta do GitHub Trending (dia/semana/mês) ordenada por estrelas ganhas, retrato de estrelas de hora em hora,
  roteiro por `claude -p`, cartões dos 10 projetos + ranking, capa do Codex, avatar no estúdio HeyGen, painel com contador e
  gráfico, revisor `claude -p`, publicação no lives4 + bot v3 + tópico fixo no INEMA.TOOLS, timer diário às 16:00.
