# gitbombando — Bombando no GitHub

[![Bombando no GitHub](guia/assets/banner.jpg)](https://inematds.github.io/gitbombando/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O gitbombando faz sozinho, todo dia às 16h, um reel vertical (9:16) chamado **Bombando no GitHub**: os 10 projetos que mais
ganharam estrelas no GitHub naquele dia, em contagem regressiva do #10 ao #1. Cada projeto aparece num cartão com a posição,
a foto do dono, o que ele faz em português simples e o número de estrelas, com um contador e um gráfico embaixo. O avatar do
Nei apresenta tudo com chamada forte e fecha pedindo um comentário. Aos domingos sai também o Top 10 da semana, e no dia 1º o
do mês. O vídeo vai para o YouTube (canal INEMA Tec), para o bot do Nei e para um tópico fixo do grupo INEMA.TOOLS no
Telegram. É para quem quer saber o que está bombando em tecnologia sem ler inglês nem código. Roda na máquina do INEMA
(Python, Node, Codex, Claude Code e a assinatura do HeyGen).

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/gitbombando/guia/**

---

## O processo, do início ao fim (10 passos)

🧠 = sessão com o Nei (gasta tokens) · ⚙️ = script/timer (zero token) · 🤖 = `claude -p` curto (sessão nova)

| # | Passo | Comando / o que acontece | Quem |
|---|---|---|---|
| 0 | Retrato das estrelas | timer `gitbombando-retrato` de hora em hora: `coleta/retrato.py` guarda as estrelas dos projetos em alta em `historico/estrelas.jsonl` (vira a curva dos gráficos) | ⚙️ |
| 1 | Agenda | timer `gitbombando.timer` às 16:00 → `auto/rodar.sh <dia>`: o dia sempre; no domingo também a semana; no dia 1º também o mês | ⚙️ |
| 2 | Coleta | `coleta/trending.py <pasta> dia\|semana\|mes`: página do GitHub Trending + API do GitHub (descrição, README, linguagem, estrelas, foto do dono); Top 10 ordenado pelas estrelas ganhas → `pesquisa/top10.json` | ⚙️ |
| 3 | Roteiro | `claude -p` com `auto/roteiro.md` escreve `ficha.yaml`: gancho sensacionalista com o fato mais forte, panorama, #10 → #1, pergunta final | 🤖 |
| 4 | Portão do roteiro | `python3 gb.py checar <pasta>`: 13 partes na ordem, projetos certos, 1.300–2.500 caracteres, manchete ≤ 6 palavras, sem algarismo na fala, "você", CTA só inema.club | ⚙️ |
| 5 | Avatar + imagens | `gb.py fazer`: fala ao estúdio do HeyGen (assinatura; autorização em pé do Nei, 28/10/2026) e, ao mesmo tempo, capa com a manchete (Codex), ranking, 10 cartões e print do inema.club | ⚙️ |
| 6 | Montagem | tempo de cada palavra (Whisper), ritmo (~182 palavras/min, pausa antes do #1), cena com contador e gráfico em cada projeto, render no motor de telejornal | ⚙️ |
| 7 | Revisão | `claude -p` com `auto/revisor.md` lê a folha de 18 quadros: aprovado segue; reprovado para e avisa no v3 | 🤖 |
| 8 | Publicar | `gb.py publicar`: YouTube **lives4** (yt-pubx, título com #Shorts, links dos 10 na descrição) → bot **v3** → tópico fixo **BOMBANDO NO GITHUB** no INEMA.TOOLS | ⚙️ |
| 9 | Guardar | git commit + push (roteiro, dados e histórico; mídia fica fora) | ⚙️ |

Teste sem publicar: `SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_GIT=1 auto/rodar.sh 2026-10-28 dia`.
Pular um dia: linha `AAAA-MM-DD` (ou `AAAA-MM-DD semana`) em `auto/pular.txt`.

## Instalação dos timers (uma vez)

```bash
cp auto/systemd/gitbombando* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando.timer
```

## O que aparece no vídeo

- **Capa (quadro 0):** manchete de até 6 palavras desenhada pelo Codex, com o número mais forte do dia em amarelo.
- **Panorama:** os 10 em barras (estrelas ganhas) e a soma num contador.
- **Cada projeto:** cartão com `#posição`, foto do dono, nome, o que faz em português, linguagem, total de estrelas e data de
  criação. Embaixo, o contador das estrelas ganhas chegando ao número no instante em que é dito e o gráfico: a curva por hora
  (dia) ou por dia (semana/mês) quando já há retratos, ou "antes × agora" com o crescimento em %.
- **Fecho:** pergunta em caixa vermelha, o gesto do comentário sendo digitado e a pílula inema.club.

## Fontes e limites

- Só a página github.com/trending e a API do GitHub. A lista de stargazers da API responde 404 desde 2026, por isso a curva
  nasce dos retratos de hora em hora do próprio projeto.
- O Top 10 é ordenado pelas estrelas ganhas no período (a ordem da página do Trending mistura outros sinais).

Licença MIT.
