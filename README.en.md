# gitbombando — Bombando no GitHub

[![Bombando no GitHub](guia/assets/banner-en.jpg)](https://inematds.github.io/gitbombando/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

gitbombando automatically creates a vertical reel (9:16) called **Bombando no GitHub** every day (published at 11:00) and two Instagram carousels: **Top 10 do GitHub** (14:00) and **Top da área** (18:00, one area per weekday). The reel shows the 10 projects that gained the most stars on GitHub that day, in a countdown from #10 to #1. Each project appears on a card with its position, the owner's photo, what it does in plain Portuguese, and the number of stars, with a counter and chart below. Nei's avatar presents everything with a strong hook and closes by asking for a comment. On Sundays, the Top 10 of the week is also published, and on the 1st, the Top 10 of the month. The video goes to YouTube (channel lives4), Instagram and TikTok @inema.tds, Nei's bot, and a pinned topic in the INEMA.TOOLS group on Telegram. The carousels go to Instagram and TikTok @inema.tds and a pinned topic in the INEMA.DEV group on Telegram. It's for anyone who wants to know what's trending in technology without reading English or code. It runs on INEMA's machine (Python, Node, Codex, Claude Code, and a HeyGen subscription).

## 📖 User guide

Complete guide (landing page + step-by-step instructions): **https://inematds.github.io/gitbombando/guia/en/**

---

## The process, from start to finish (13 steps)

🧠 = session with Nei (uses tokens) · ⚙️ = script/timer (zero tokens) · 🤖 = short `claude -p` (new session)

| # | Step | Command / what happens | Who |
|---|---|---|---|
| 0 | Star snapshots | Hourly `gitbombando-retrato` timer: `coleta/retrato.py` saves stars for trending projects in `historico/estrelas.jsonl` (used to plot the charts) | ⚙️ |
| 1 | Schedule | `gitbombando.timer` at **06:30** → `auto/rodar.sh <dia>` (generates while the HeyGen studio is free): the daily one, always published at **11 AM** (`GB_PUBLICAR_AS`); on Sundays, after that, the weekly one, and on the 1st, the monthly one, which come out as soon as they're ready (early afternoon) | ⚙️ |
| 2 | Collection | `coleta/trending.py <pasta> dia\|semana\|mes`: GitHub Trending page + GitHub API (description, README, language, stars, owner's photo); Top 10 ranked by stars gained → `pesquisa/top10.json` | ⚙️ |
| 3 | Script | `claude -p` with `auto/roteiro.md` writes `ficha.yaml`: sensational hook with the strongest fact, overview, #10 → #1, final question | 🤖 |
| 4 | Script gate | `python3 gb.py checar <pasta>`: 13 parts in order, correct projects, 1,300–2,500 characters, headline ≤ 6 words, no numerals in spoken lines, "you", CTA only inema.club | ⚙️ |
| 5 | Avatar + images | `gb.py fazer`: sends the script to the HeyGen studio (subscription; Nei's authorization in place, 28/10/2026) and, at the same time, creates the headline cover (Codex), ranking, 10 cards, and inema.club screenshot | ⚙️ |
| 6 | Assembly | Timing for each word (Whisper), pacing (~182 words/min, pause before #1), scene with counter and chart for each project, render in the news broadcast engine | ⚙️ |
| 7 | Review | `claude -p` with `auto/revisor.md` reads the 18-frame sheet: approved means it continues; rejected means it stops and notifies in v3 | 🤖 |
| 8 | Publish | `gb.py publicar`: YouTube **lives4** (yt-pubx, title with #Shorts, links to all 10 in the description) → bot **v3** → pinned topic **BOMBANDO NO GITHUB** in INEMA.TOOLS | ⚙️ |
| 8b | Metritds | `auto/metritds.sh <pasta>`: uploads the video to the repo's `social` release and schedules it (now + 10 min) on **Instagram + TikTok inema.tds** through the Metricool account for inematds (connector `metricool-inematds`, via `claude -p`); blue notification in v3 | 🤖 |
| 9 | Save | git commit + push (script, data, and history; media stays out) | ⚙️ |
| 10 | Top 10 carousel | `gitbombando-carrossel-top10` timer at 12:45 → `auto/carrossel.sh <dia> top10` (publishes at **14:00**): reuses the video collection; `claude -p` with `carrossel/textos.md` writes the hook, "what it is", 2 benefits, and each project's workflow; screenshot of each project taken from its README (`carrossel/prints.py`); 12 slides 1080×1350 (`carrossel/render.mjs`); copy and design gates; reviewer `claude -p` (`carrossel/revisor.md`) | ⚙️🤖 |
| 11 | Area carousel | `gitbombando-carrossel-area` timer at 16:45 → `auto/carrossel.sh <dia> area` (publishes at **18:00**): `carrossel/area.py` searches GitHub for repositories in the day's area created in the last 120 days, ranked by stars per day, without repeating those from the last 8 weeks and excluding adult content; then follows the same process as step 10 with 8 projects | ⚙️🤖 |
| 12 | Publish the carousel | `carrossel/carrossel.py publicar`: album in the pinned topic **BOMBANDO NO GITHUB - Carrosséis diários** in **INEMA.DEV** (Telegram) → carousel on Instagram + photos on TikTok inema.tds (Metricool, now + 10 min) → blue notification in v3 → git. Rejected = not published, with a notification in v3 | ⚙️🤖 |

Test without publishing: `ED=/tmp/teste-video AVATAR_DE=<avatar.mp4> SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_METRI=1 SEM_GIT=1 GB_SEM_HISTORICO=1 auto/rodar.sh 2026-10-28 dia`.
Carousel without publishing: `ED=/tmp/teste SEM_TG=1 SEM_METRI=1 SEM_BOT=1 SEM_GIT=1 auto/carrossel.sh 2026-11-04 area`
(`RASCUNHO=1` instead of `SEM_METRI=1` schedules it on Metricool as a draft).
Skip a day: line `AAAA-MM-DD` (or `AAAA-MM-DD semana`, `AAAA-MM-DD carrossel`, `AAAA-MM-DD carrossel-top10`, `AAAA-MM-DD carrossel-area`) in `auto/pular.txt`.

## Timer installation (once)

```bash
cp auto/systemd/gitbombando* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando.timer gitbombando-carrossel-top10.timer gitbombando-carrossel-area.timer
```

## What appears in the video

- **Cover (frame 0):** large "TOP 10 DO GITHUB" headline at the top + a headline of up to 6 words designed by Codex, with the day's strongest number in yellow.
- **Overview:** the 10 projects in bars (stars gained) and the total in a counter.
- **Each project:** card with `#position`, owner's photo, name, what it does in Portuguese, language, total stars, and creation
  date. Below, the counter for stars gained reaches the number at the moment it's spoken, and the chart shows the hourly curve
  (day) or daily curve (week/month) when snapshots are available, or "before × now" with growth as a %.
- **Closing:** question in a red box, the gesture of a comment being typed, and the inema.club pill.

## The carousels

- **Cover:** mosaic of project screenshots, "TOP 10 DO GITHUB HOJE" (or "TOP 8" + the area), a headline of up to 6 words, and
  the total stars.
- **One slide per project** (starting at #1): position, name, 2-line hook, README screenshot with stars gained, "What it
  is", 2 benefits, "how to use" in 3 steps, and repository link with total stars.
- **Closing:** "links are in the caption", the list of projects, the day's schedule, and inema.club. The caption includes the links.
- **Areas:** Monday AI agents · Tuesday Claude Code and MCP · Wednesday AI for video and images · Thursday security · Friday
  automation · Saturday web development and apps · Sunday AI on your PC (`carrossel/area.py`, `AREAS`).

## Sources and limits

- Only the github.com/trending page and the GitHub API. The API's stargazer list has returned 404 since 2026, so the curve
  comes from the project's own hourly snapshots.
- The Top 10 is ranked by stars gained during the period (the Trending page order mixes in other signals).

MIT License.
