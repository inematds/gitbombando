# gitbombando — Bombando no GitHub

Reel 9:16 automático com o **Top 10 do GitHub** (os projetos do Trending que mais ganharam estrelas), contagem regressiva
do #10 ao #1, cartão de cada projeto, gráficos e o avatar do Nei. Explicação completa e o processo passo a passo: `README.md`.

- Autor dos commits: `inematds <inematds@gmail.com>`. Repo `inematds/gitbombando`.
- **Pedido do Nei (28/10/2026):** "um sistema estilo eventosextremospub + r7ex com uma reels do dia, semana e mês, mostrando
  os gráficos e explicando cada um dos top 10 … a chamada tem de ser sensacionalista … coloque no lives4 e manda para o v3 …
  crie sempre um tópico no inema.tools, vai colocando sempre no mesmo post … agenda para 4 da tarde rodar e publicar todo dia".
  Isso é a **autorização em pé** do avatar no estúdio HeyGen (assinatura) e da publicação diária sem aprovação: o
  `auto/rodar.sh` grava o `avatar/APROVADO_HEYGEN` de cada rodada com essa data. Nunca pela API do HeyGen para gerar.
- **Independente**: motor (`motor/`), estúdio HeyGen (`heygen/`), Whisper/ritmo/cena (`nucleo/`) são cópias do r7ex de
  28/10/2026. Não importar nada do r7ex/eventosextremospub; mudar aqui não afeta eles.
- **APIs:** só a do GitHub (liberada em 05/10/2026) para coletar; Telegram (liberado para publicar conteúdo). O roteirista e o
  revisor são `claude -p` (assinatura); a capa é Codex `image_gen` (assinatura). Nenhuma outra API.
- A lista de stargazers da API do GitHub responde **404** (desde 2026): a curva de estrelas vem dos nossos retratos de hora em
  hora (`coleta/retrato.py`, timer `gitbombando-retrato`, `historico/estrelas.jsonl`). Sem 3 retratos, o gráfico do projeto
  é "antes × agora" (total − ganho no período → total).
- **Top 10 = ordenado pelas estrelas ganhas no período** entre os projetos da página do Trending (a ordem da página mistura
  outros sinais e o gráfico ficava sem sentido). `pos_trending` guarda a ordem original.
- Rodada: timer `gitbombando.timer` 16:00 → `auto/rodar.sh <dia>` (= `dia`; no domingo também `semana`; no dia 1º também `mes`).
  Uma por vez (trava `auto/.rodando`). Teste isolado: `ED=<pasta fora de edicoes/> AVATAR_DE=<mp4> SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_METRI=1 SEM_GIT=1 GB_SEM_HISTORICO=1 auto/rodar.sh <dia> <modo>`
  (`GB_PESADO=<script>` põe o render atrás de uma trava externa). Avatar já enviado (`avatar/video_id.txt`) = retoma sem refazer roteiro.
  Pular: `AAAA-MM-DD` ou `AAAA-MM-DD semana` em `auto/pular.txt`. Edição já publicada não roda de novo (`FORCAR=1` refaz).
- **Metritds (01/11/2026):** além do lives4, cada reel aprovado vai ao Instagram + TikTok `inema.tds` pelo Metricool da
  conta inematds (conector MCP `metricool-inematds`, apelido "metritds") com `auto/metritds.sh` (agora + 10 min, UTC).
  Info da conta: `~/projetos/metricool-inematds`. `SEM_METRI=1` pula. Marca feito em `<edição>/metritds.txt`; teste com `RASCUNHO=1 SEM_BOT=1`.
- Revisor `claude -p` (`auto/revisor.md`) lê `build/folha.jpg` (18 quadros): reprovado = não publica e avisa no v3 com o
  comando para publicar assim mesmo (`python3 gb.py publicar <pasta>`).
- Telegram: tópico fixo no INEMA.TOOLS, id em `auto/telegram-topico.txt` (criado na 1ª rodada); cada rodada posta dentro
  dele com `postar_topico.py --topico`. **Nunca apagar mensagem/tópico sem aprovação individual do Nei.**
- Reel nunca chega a 3 min (portão em 178 s); fala 1.300–2.500 caracteres; tom "você", CTA só inema.club, nunca "morte".
- Falhou? Linha em `FALHAS.md` (data | o que quebrou | menor correção | prompt/infra).

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under
## Lessons, so it never happens again.

## Lessons
- Publicação direta: no v3 vai só a mensagem azul (metritds, com YouTube + sugestão do revisor), sem o vídeo; o vídeo só vai ao v3 quando o revisor reprova ou com SEM_METRI=1. (Nei, 01/11/2026)
- Gráfico de semana/mês com retratos parciais contradiz o "+N" do cartão: curva "total por dia" só com o período inteiro coberto; senão "antes × agora". (semana 04/11/2026)
