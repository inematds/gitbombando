# gitbombando — Bombando no GitHub

[![Bombando no GitHub](guia/assets/banner-en.jpg)](https://inematds.github.io/gitbombando/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

gitbombando automatically creates a vertical (9:16) reel every day at 4:00 PM called **Bombando no GitHub**: the 10 projects that gained the most stars on GitHub that day, counting down from #10 to #1. Each project appears on a card showing its position, the owner's photo, what it does in plain English, and its star count, with a counter and a chart below. Nei's avatar presents everything with a strong hook and closes by asking for a comment. On Sundays, the weekly Top 10 also comes out, and on the 1st, the monthly one. The video goes to YouTube (INEMA Tec channel), Nei's bot, and a pinned topic in the INEMA.TOOLS group on Telegram. It's for anyone who wants to know what's trending in technology without reading English or code. It runs on INEMA's machine (Python, Node, Codex, Claude Code, and a HeyGen subscription).

## 📖 User guide

Complete guide (landing page + walkthrough): **https://inematds.github.io/gitbombando/guia/en/**

---

## The process, from start to finish (10 steps)

🧠 = session with Nei (uses tokens) · ⚙️ = script/timer (zero tokens) · 🤖 = short `claude -p` (new session)

| # | Step | Command / what happens | Who |
|---|---|---|---|
| 0 | Star snapshots | Hourly `gitbombando-retrato` timer: `coleta/retrato.py` saves the stars of trending projects in `historico/estrelas.jsonl` (which powers the chart curves) | ⚙️ |
| 1 | Schedule | `gitbombando.timer` at 4:00 PM → `auto/rodar.sh <dia>`: always runs the daily edition; on Sundays, the weekly edition too; on the 1st, the monthly edition too | ⚙️ |
| 2 | Collection | `coleta/trending.py <pasta> dia\|semana\|mes`: GitHub Trending page + GitHub API (description, README, language, stars, owner's photo); Top 10 sorted by stars gained → `pesquisa/top10.json` | ⚙️ |
| 3 | Script | `claude -p` with `auto/roteiro.md` writes `ficha.yaml`: sensationalist hook featuring the strongest fact, overview, #10 → #1, closing question | 🤖 |
| 4 | Script gate | `python3 gb.py checar <pasta>`: 13 parts in order, correct projects, 1,300–2,500 characters, headline ≤ 6 words, no numerals in the spoken text, "you", CTA only to inema.club | ⚙️ |
| 5 | Avatar + images | `gb.py fazer`: sends the script to the HeyGen studio (subscription; ongoing authorization from Nei, 10/28/2026) and, at the same time, creates the headline cover (Codex), ranking, 10 cards, and inema.club screenshot | ⚙️ |
| 6 | Assembly | Word timing (Whisper), pacing (~182 words/min, pause before #1), scene with counter and chart for each project, render in the news broadcast engine | ⚙️ |
| 7 | Review | `claude -p` with `auto/revisor.md` reads the 18-frame sheet: approved proceeds; rejected stops and alerts in v3 | 🤖 |
| 8 | Publish | `gb.py publicar`: YouTube **lives4** (yt-pubx, title with #Shorts, links to all 10 in the description) → bot **v3** → pinned topic **BOMBANDO NO GITHUB** in INEMA.TOOLS | ⚙️ |
| 9 | Save | git commit + push (script, data, and history; media stays out) | ⚙️ |

Test without publishing: `SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_GIT=1 auto/rodar.sh 2026-10-28 dia`.
Skip a day: add a line `AAAA-MM-DD` (or `AAAA-MM-DD semana`) to `auto/pular.txt`.

## Timer installation (one time)

```bash
cp auto/systemd/gitbombando* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando.timer
```

## What appears in the video

- **Cover (frame 0):** headline of up to 6 words designed by Codex, with the day's biggest number in yellow.
- **Overview:** the 10 projects in bars (stars gained) and their sum on a counter.
- **Each project:** card with `#position`, owner's photo, name, what it does in plain English, language, total stars, and creation date. Below it, the gained-stars counter climbs to the number at the moment it's spoken, and the chart shows the hourly curve (day) or daily curve (week/month) when snapshots are available, or "before × now" with growth as a %.
- **Closing:** question in a red box, the comment gesture being typed, and the inema.club pill.

## Sources and limitations

- Only the github.com/trending page and the GitHub API. The API's stargazers list has returned 404 since 2026, so the curve comes from the project's own hourly snapshots.
- The Top 10 is sorted by stars gained during the period (the Trending page order mixes in other signals).

MIT License.