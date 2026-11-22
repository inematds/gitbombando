# gitbombando — Bombando no GitHub

[![Bombando no GitHub](guia/assets/banner.jpg)](https://inematds.github.io/gitbombando/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O gitbombando faz sozinho, todo dia, um reel vertical (9:16) chamado **Bombando no GitHub** (sai às 11h) e dois carrosséis de
Instagram: o **Top 10 do GitHub** (14h) e o **Top da área** (18h, uma área por dia da semana). O reel mostra os 10 projetos que mais
ganharam estrelas no GitHub naquele dia, em contagem regressiva do #10 ao #1. Cada projeto aparece num cartão com a posição,
a foto do dono, o que ele faz em português simples e o número de estrelas, com um contador e um gráfico embaixo. O avatar do
Nei apresenta tudo com chamada forte e fecha pedindo um comentário. Aos domingos sai também o Top 10 da semana, e no dia 1º o
do mês. O vídeo vai para o YouTube (canal lives4), para o Instagram e o TikTok @inema.tds, para o bot do Nei e para um tópico fixo
do grupo INEMA.TOOLS no Telegram. Os carrosséis vão para o Instagram e o TikTok @inema.tds e para um tópico fixo do grupo
INEMA.DEV no Telegram. É para quem quer saber o que está bombando em tecnologia sem ler inglês nem código. Roda na máquina do INEMA
(Python, Node, Codex, Claude Code e a assinatura do HeyGen).

## Controle de IA por etapa

O motor, modelo e esforço de cada etapa ficam em `auto/ia.yaml`, exclusivos deste projeto.
Veja com `./ia ver`; altere, por exemplo, com `./ia configurar roteiro --modelo claude-opus-5-5 --esforco medium`.
Para trocar texto/visão para Codex: `./ia configurar roteiro --tipo assinatura --motor codex --modelo gpt-6.1-sol --esforco medium`.
Confira com `./ia validar` (sem chamadas de IA). Instruções e limites: [auto/IA.md](auto/IA.md).
As cinco opções estão documentadas com `#` no próprio YAML: assinaturas Claude/Codex e APIs Anthropic/OpenAI/OpenRouter. A **API Anthropic está ativa nos crons para texto e revisão**, conforme autorização do Nei; OpenAI/OpenRouter seguem desativadas. Capa permanece Codex; Metricool usa Codex por assinatura/MCP (Claude também pode ser selecionado). Os testes reais de roteiro passaram com API Anthropic e assinatura Codex; detalhes em [auto/IA.md](auto/IA.md).

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/gitbombando/guia/**

---

## O processo, do início ao fim (11 passos)

🧠 = sessão com o Nei (gasta tokens) · ⚙️ = script/timer (zero token) · 🤖 = IA em sessão curta (`auto/ia.yaml`)

| Hora | Conteúdo | Reel (fila do x3) | Carrossel (fila do x3 + Telegram INEMA.FTD) |
|---|---|---|---|
| 07:00 | Top 10 do dia | lives4 | lives9 |
| 08:00 | Top 5 da semana | lives8 | lives12 |
| 09:30 | Top 5 da área do dia | lives3 | lives9 |
| 10:00 | Top 5 de sistemas de agentes | lives7 | lives12 |
| Domingo 09:00 | Top 10 da semana | lives4 | não tem |

| # | Passo | Comando / o que acontece | Quem |
|---|---|---|---|
| 0 | Retrato das estrelas | timer `gitbombando-retrato` de hora em hora: `coleta/retrato.py` | ⚙️ |
| 1 | Agenda | timers `gitbombando-grade-*` → `auto/grade.sh dia\|top5\|area\|agentes\|semana` | ⚙️ |
| 2 | Coleta | `coleta/trending.py` (dia, semana, `GB_TOP=5`) ou `coleta/area_top.py` (área e agentes) | ⚙️ |
| 3 | Carrossel | `auto/carrossel.sh <dia> <tipo>`: textos, prints, slides, portão e revisor; roda sem esperar o reel | 🤖 |
| 4 | Publicar carrossel | álbum no INEMA.FTD e `yt-pub-x3 enviar` no canal do horário | ⚙️ |
| 5 | Roteiro | `auto/rodar.sh <dia> <modo>` escreve `ficha.yaml` com `auto/roteiro.md` | 🤖 |
| 6 | Portão | `python3 gb.py checar <pasta>` | ⚙️ |
| 7 | Avatar e imagens | `gb.py fazer`: estúdio HeyGen e capa pelo Codex | ⚙️ |
| 8 | Montagem e revisão | cena, conferência das imagens (falta = refaz ou troca pela tela vizinha), render e revisor; reprovado = capa nova e novo render, uma vez | 🤖 |
|  | Falhou? | até 3 tentativas para qualquer erro, cada uma refaz só o que falhou (render, avatar ou envio ao HeyGen); o aviso no v3 traz a linha do erro | ⚙️ |
| 9 | Publicar reel | `gb.py publicar`: fila do x3, tópico no INEMA.TOOLS e grupo INEMA.FREE (links dos tops + YouTube, quando o vídeo sai) | ⚙️ |
| 10 | Guardar | git commit + push (roteiro, dados e histórico; mídia fica fora) | ⚙️ |

O projeto não fala com o Metricool: quem publica nas redes é o x3. O bot v3 só recebe erro. Os reels saem um por vez e publicam ao ficar prontos.

Teste sem publicar: `ED=<pasta> GB_TRAVA=<arquivo> GB_PARAR_APOS_ROTEIRO=1 SEM_BOT=1 SEM_GIT=1 auto/rodar.sh <dia> agentes`
Carrossel sem publicar: `ED=<pasta> SEM_TG=1 SEM_X3=1 SEM_BOT=1 SEM_GIT=1 auto/carrossel.sh <dia> area`
Pular: linha `AAAA-MM-DD`, `AAAA-MM-DD <modo>`, `AAAA-MM-DD carrossel` ou `AAAA-MM-DD carrossel-<tipo>` em `auto/pular.txt`.

## Instalação dos timers (uma vez)

```bash
cp auto/systemd/gitbombando-grade* auto/systemd/gitbombando-retrato.* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando-grade-{dia,top5,area,agentes,semana}.timer
```

## O que aparece no vídeo

- **Capa (quadro 0):** chamada grande "TOP 10 DO GITHUB" no alto + manchete de até 6 palavras desenhada pelo Codex, com o número mais forte do dia em amarelo.
- **Panorama:** os 10 em barras (estrelas ganhas) e a soma num contador.
- **Cada projeto:** cartão com `#posição`, foto do dono, nome, o que faz em português, linguagem, total de estrelas e data de
  criação. Embaixo, o contador das estrelas ganhas chegando ao número no instante em que é dito e o gráfico: a curva por hora
  (dia) ou por dia (semana/mês) quando já há retratos, ou "antes × agora" com o crescimento em %.
- **Fecho:** pergunta em caixa vermelha, o gesto do comentário sendo digitado e a pílula inema.club.

## Os carrosséis

- **Capa:** mosaico com os prints dos projetos, "TOP 10 DO GITHUB HOJE" (ou "TOP 8" + a área), uma manchete de até 6 palavras e
  a soma das estrelas.
- **Um slide por projeto** (do #1 em diante): posição, nome, gancho de 2 linhas, o print do README com as estrelas ganhas, "O que
  é", 2 benefícios, "como usa" em 3 passos e o link do repositório com o total de estrelas.
- **Fecho:** "os links estão na legenda", a lista dos projetos, a agenda do dia e inema.club. A legenda traz os links.
- **Áreas:** segunda agentes de IA · terça Claude Code e MCP · quarta IA para vídeo e imagem · quinta segurança · sexta
  automação · sábado dev web e apps · domingo IA no seu PC (`carrossel/area.py`, `AREAS`).

## Fontes e limites

- Só a página github.com/trending e a API do GitHub. A lista de stargazers da API responde 404 desde 2026, por isso a curva
  nasce dos retratos de hora em hora do próprio projeto.
- O Top 10 é ordenado pelas estrelas ganhas no período (a ordem da página do Trending mistura outros sinais).

Licença MIT.
