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

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/gitbombando/guia/**

---

## O processo, do início ao fim (13 passos)

🧠 = sessão com o Nei (gasta tokens) · ⚙️ = script/timer (zero token) · 🤖 = `claude -p` curto (sessão nova)

| # | Passo | Comando / o que acontece | Quem |
|---|---|---|---|
| 0 | Retrato das estrelas | timer `gitbombando-retrato` de hora em hora: `coleta/retrato.py` guarda as estrelas dos projetos em alta em `historico/estrelas.jsonl` (vira a curva dos gráficos) | ⚙️ |
| 1 | Agenda | timer `gitbombando.timer` às **09:00** → `auto/rodar.sh <dia>` (gera com o estúdio do HeyGen livre): o dia sempre, publicado às **11:00** (`GB_PUBLICAR_AS`); no domingo, depois dele, a semana e, no dia 1º, o mês, que saem assim que ficam prontos (começo da tarde) | ⚙️ |
| 2 | Coleta | `coleta/trending.py <pasta> dia\|semana\|mes`: página do GitHub Trending + API do GitHub (descrição, README, linguagem, estrelas, foto do dono); Top 10 ordenado pelas estrelas ganhas → `pesquisa/top10.json`; com menos de 10 no Trending espera até 1 h e, se ainda faltar, segue com Top N (mínimo 5) | ⚙️ |
| 3 | Roteiro | `claude -p` com `auto/roteiro.md` escreve `ficha.yaml`: gancho sensacionalista com o fato mais forte, panorama, #10 → #1, pergunta final | 🤖 |
| 4 | Portão do roteiro | `python3 gb.py checar <pasta>`: N+3 partes na ordem (13 no Top 10), projetos certos, 1.300–2.500 caracteres, manchete ≤ 6 palavras, sem algarismo na fala, "você", CTA só inema.club | ⚙️ |
| 5 | Avatar + imagens | `gb.py fazer`: fala ao estúdio do HeyGen (assinatura; autorização em pé do Nei, 28/10/2026) e, ao mesmo tempo, capa com a manchete (Codex), ranking, 10 cartões e print do inema.club | ⚙️ |
| 6 | Montagem | tempo de cada palavra (Whisper), ritmo (~182 palavras/min, pausa antes do #1), cena com contador e gráfico em cada projeto, render no motor de telejornal | ⚙️ |
| 7 | Revisão | `claude -p` com `auto/revisor.md` lê a folha de 18 quadros: aprovado segue; reprovado para e avisa no v3 | 🤖 |
| 8 | Publicar | `gb.py publicar`: YouTube **lives4** (yt-pubx, título com #Shorts, links dos 10 na descrição) → bot **v3** → tópico fixo **BOMBANDO NO GITHUB** no INEMA.TOOLS | ⚙️ |
| 8b | Metritds | `auto/metritds.sh <pasta>`: sobe o vídeo na release `social` do repo e agenda (agora + 10 min) no **Instagram + TikTok inema.tds** (marca do lives4) pelo Metricool da conta inematds (conector `metricool-inematds`, via `claude -p`); dia ~11:10, semana 13:00, mês 15:00; aviso azul no v3 | 🤖 |
| 9 | Guardar | git commit + push (roteiro, dados e histórico; mídia fica fora) | ⚙️ |
| 10 | Carrossel Top 10 | timer `gitbombando-carrossel-top10` às 12:45 → `auto/carrossel.sh <dia> top10` (publica às **14:00**): reusa a coleta do vídeo; `claude -p` com `carrossel/textos.md` escreve gancho, "o que é", 2 benefícios e o fluxo de cada um; print de cada projeto tirado do README (`carrossel/prints.py`); 12 slides 1080×1350 (`carrossel/render.mjs`); portão do texto e do desenho; revisor `claude -p` (`carrossel/revisor.md`) | ⚙️🤖 |
| 11 | Carrossel da área | timer `gitbombando-carrossel-area` às 16:45 → `auto/carrossel.sh <dia> area` (publica às **18:00**): `carrossel/area.py` busca no GitHub os repositórios da área do dia criados nos últimos 120 dias, ordenados por estrelas por dia, sem repetir as últimas 8 semanas e sem conteúdo adulto; depois o mesmo caminho do passo 10 com 8 projetos | ⚙️🤖 |
| 12 | Publicar o carrossel | `carrossel/carrossel.py publicar`: álbum no tópico fixo **BOMBANDO NO GITHUB - Carrosséis diários** do **INEMA.DEV** (Telegram) → carrossel no Instagram + fotos no TikTok **inema.tech** (marca FTD = lives3, desde 09/11/2026; Metricool, agora + 10 min, legenda sem link) → aviso azul no v3 → git. Reprovado = não publica e avisa no v3 | ⚙️🤖 |

Teste sem publicar: `ED=/tmp/teste-video AVATAR_DE=<avatar.mp4> SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_METRI=1 SEM_GIT=1 GB_SEM_HISTORICO=1 auto/rodar.sh 2026-10-28 dia`.
Carrossel sem publicar: `ED=/tmp/teste SEM_TG=1 SEM_METRI=1 SEM_BOT=1 SEM_GIT=1 auto/carrossel.sh 2026-11-04 area`
(`RASCUNHO=1` no lugar de `SEM_METRI=1` agenda no Metricool como rascunho).
Pular um dia: linha `AAAA-MM-DD` (ou `AAAA-MM-DD semana`, `AAAA-MM-DD carrossel`, `AAAA-MM-DD carrossel-top10`, `AAAA-MM-DD carrossel-area`) em `auto/pular.txt`.

## Instalação dos timers (uma vez)

```bash
cp auto/systemd/gitbombando* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando.timer gitbombando-carrossel-top10.timer gitbombando-carrossel-area.timer
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
