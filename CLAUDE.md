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
- **IA por etapa (15/11/2026):** fonte exclusiva = `auto/ia.yaml`; controle com `./ia ver`, `./ia configurar <etapa> --tipo ... --motor ... --modelo ... --esforco ...` e `./ia validar`. Não herdar modelo/esforço global ou de modelos.env. O executor `auto/ia.py` sempre passa valores explícitos e registra `ia-execucoes.jsonl` na edição. Ver `auto/IA.md`.
- **APIs:** GitHub e Telegram seguem as autorizações existentes. Texto e revisão usam a API Anthropic, autorizada pelo Nei em 15/11/2026 ("entao deixa ele operacional com claude api, ok"). Os adaptadores Anthropic, OpenAI Responses e OpenRouter (texto/visão) estão implementados, Anthropic está ativada somente nas cinco etapas listadas em `api.etapas_autorizadas`; OpenAI/OpenRouter permanecem desativadas: NÃO ativar, carregar chave nem chamar API sem autorização explícita do Nei para o serviço e as etapas escolhidas; registrar em `api.autorizacao` (Anthropic), `api.openai.autorizacao` ou `api.openrouter.autorizacao`, com o booleano correspondente. Autorizar um serviço NÃO autoriza os demais. Claude Code e Codex CLI continuam só por assinatura, nunca por API. Sem fallback pago. Capa exige Codex/image_gen; Metricool aceita Claude ou Codex com seu MCP; operação atual em assinatura/codex, perfil ~/.codex-2, servidor metricool-inematds. Conta inematds@gmail.com conferida antes de agendar. API de texto não substitui essas ferramentas.
- **Teste autorizado (Nei, 15/11/2026):** "testes se ele funciona com a api do claude e se funciona com assinatura do codex" autorizou somente o teste isolado Anthropic, realizado com sucesso usando inemapro-api-key, e o teste Codex por assinatura. Esse teste não autorizava API diária; o pedido posterior de operação autorizou Anthropic nas etapas de texto/revisão. OpenAI/OpenRouter continuam sem autorização de consumo. Resultados em `tests/resultados/2026-11-15.json`. Exemplos editáveis com `#` ficam no próprio YAML e devem ser preservados.
- A lista de stargazers da API do GitHub responde **404** (desde 2026): a curva de estrelas vem dos nossos retratos de hora em
  hora (`coleta/retrato.py`, timer `gitbombando-retrato`, `historico/estrelas.jsonl`). Sem 3 retratos, o gráfico do projeto
  é "antes × agora" (total − ganho no período → total).
- **Top 10 = ordenado pelas estrelas ganhas no período** entre os projetos da página do Trending (a ordem da página mistura
  outros sinais e o gráfico ficava sem sentido). `pos_trending` guarda a ordem original.
- **Grade (Nei, 18/11/2026), `auto/grade.sh` + timers `gitbombando-grade-*`:** 07:00 Top 10 do dia (reel lives4, carrossel lives9) · 08:00 Top 5 da
  semana (lives8, carrossel lives12) · 09:30 Top 5 da área (lives3, carrossel lives9) · 10:00 Top 5 de agentes (lives7, carrossel lives12) ·
  domingo 09:00 Top 10 da semana (lives4). **Tudo entra pela fila do x3; o projeto não fala com o Metricool.** Carrossel também vai ao
  Telegram INEMA.FTD. O v3 só recebe erro. lives9 tem `rs.so_imagens` no x3: nas redes (FTD) só carrossel.
  Reels saem um por vez (trava `auto/.rodando`) e publicam ao ficar prontos. Teste isolado: `ED=<pasta fora de edicoes/> GB_TRAVA=<arquivo> AVATAR_DE=<mp4> SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_GIT=1 GB_SEM_HISTORICO=1 auto/rodar.sh <dia> <modo>`
  (`GB_PESADO=<script>` põe o render atrás de uma trava externa). Avatar já enviado (`avatar/video_id.txt`) = retoma sem refazer roteiro.
  Pular: `AAAA-MM-DD` ou `AAAA-MM-DD semana` em `auto/pular.txt`. Edição já publicada não roda de novo (`FORCAR=1` refaz).
- Revisor (`auto/revisor.md`) lê `build/folha.jpg` (18 quadros): reprovado = capa nova e novo render, uma vez; reprovado de novo =
  não publica e avisa no v3 com o comando para publicar assim mesmo (`python3 gb.py publicar <pasta>`). HeyGen: 3 tentativas.
- **Carrosséis:** `auto/carrossel.sh <dia> top10|top5|area|agentes`, chamado pela grade. Código em `carrossel/` (ver docstring de
  `carrossel.py`). Álbum no tópico fixo do INEMA.FTD (`auto/telegram-topico-carrossel-ftd.txt`) + fila do x3. Revisor reprovado = não publica. Áreas que já saíram:
  `historico/carrossel-area.jsonl` (8 semanas sem repetir). Conteúdo adulto fica fora na coleta (`IMPROPRIO`).
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
