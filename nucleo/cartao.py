"""Cartões do gitbombando (1080x1920, tudo na metade de CIMA; a de baixo fica para legenda, painel e avatar).

- cartao_repo: a posição (#10 … #1) grande, foto do dono, nome, o que faz em português, linguagem e estrelas;
- cartao_ranking: os 10 projetos em barras (estrelas ganhas no período) — o "panorama".

HTML desenhado aqui e fotografado pelo Chrome headless do Playwright (o mesmo do pecas.screenshot).
Cores e fontes do kit INEMA: preto #0c0c10, amarelo #FACC15, títulos Archivo Black/Sora, corpo Inter.
"""
import html, subprocess, tempfile
from pathlib import Path

from .pecas import CHROME

PERIODO = {"dia": "HOJE", "semana": "NA SEMANA", "mes": "NO MÊS"}
COR_LING = {"Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Rust": "#dea584", "Go": "#00ADD8",
            "Shell": "#89e051", "C++": "#f34b7d", "C": "#555555", "Java": "#b07219", "Kotlin": "#A97BFF", "Swift": "#F05138",
            "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26", "CSS": "#663399", "Dart": "#00B4AB", "Ruby": "#701516",
            "C#": "#178600", "Zig": "#ec915c", "Lua": "#000080", "PHP": "#4F5D95", "Vue": "#41b883", "MDX": "#fcb32c"}

BASE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@500;700;800;900&family=Sora:wght@700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:#0c0c10;color:#e6e6e6;font-family:Inter,sans-serif;overflow:hidden}
.glow{position:absolute;left:-200px;top:-260px;width:1480px;height:1300px;
  background:radial-gradient(ellipse at 50% 40%,rgba(250,204,21,.16),rgba(250,204,21,0) 62%)}
.grade{position:absolute;inset:0;height:1180px;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
  linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:60px 60px;
  -webkit-mask-image:linear-gradient(#000 70%,transparent)}
%CSS%
</style></head><body><div class="glow"></div><div class="grade"></div>%CORPO%</body></html>"""

CSS_REPO = """
.rot{position:absolute;left:64px;top:150px;font:900 26px Inter;letter-spacing:5px;color:#FACC15}
.pos{position:absolute;right:56px;top:112px;font:400 300px/1 'Archivo Black';color:#FACC15;letter-spacing:-8px;
  text-shadow:0 0 60px rgba(250,204,21,.35)}
.pos small{font-size:120px;vertical-align:top;letter-spacing:0;margin-right:6px;opacity:.9}
.foto{position:absolute;left:64px;top:220px;width:220px;height:220px;border-radius:36px;border:6px solid #FACC15;
  object-fit:cover;background:#16161e;box-shadow:0 20px 60px rgba(0,0,0,.6)}
.nome{position:absolute;left:64px;right:64px;top:480px}
.dono{font:800 38px Inter;color:#a8a8b3;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.repo{font:400 %TAM%px/1.02 'Archivo Black';color:#fff;letter-spacing:-1px;word-break:break-word}
.desc{position:absolute;left:64px;right:64px;top:%DESC_Y%px;font:800 44px/1.25 Inter;color:#f1f1f1}
.desc b{background:linear-gradient(transparent 58%,rgba(250,204,21,.85) 58%);color:#fff}
.chips{position:absolute;left:64px;right:64px;top:%CHIPS_Y%px;display:flex;flex-wrap:wrap;gap:14px}
.chip{border:2px solid #272730;background:#16161e;border-radius:40px;padding:10px 22px;font:800 30px Inter;color:#e6e6e6;white-space:nowrap}
.chip i{display:inline-block;width:20px;height:20px;border-radius:50%;margin-right:10px;vertical-align:-1px}
.chip.am{border-color:#FACC15;color:#FACC15}
.chip.vm{border-color:#ff2a1f;color:#ff8a80}
"""

CSS_RANK = """
.rot{position:absolute;left:56px;right:56px;top:150px;font:900 28px Inter;letter-spacing:5px;color:#FACC15}
.tit{position:absolute;left:56px;right:56px;top:192px;font:400 92px/1 'Archivo Black';color:#fff;letter-spacing:-2px}
.tit b{color:#FACC15;font-weight:400}
.lista{position:absolute;left:56px;right:56px;top:318px}
.r{display:flex;align-items:center;gap:16px;height:76px}
.n{flex:0 0 64px;font:400 40px 'Archivo Black';color:#FACC15;text-align:right}
.r img{flex:0 0 52px;width:52px;height:52px;border-radius:12px;background:#16161e}
.nm{flex:0 0 330px;font:800 30px Inter;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar{flex:1;height:34px;background:rgba(255,255,255,.07);border-radius:9px;overflow:hidden}
.bar i{display:block;height:100%;background:#FACC15;border-radius:9px}
.r.top .bar i{background:linear-gradient(90deg,#FACC15,#ff2a1f)}
.v{flex:0 0 150px;text-align:right;font:900 32px Inter;color:#fff}
.fonte{position:absolute;left:56px;top:1100px;font:700 22px Inter;color:#8a8a96}
"""


def br(n):
    return f"{int(n):,}".replace(",", ".")


def _foto(pasta, it):
    return html.escape(it.get("dono_foto") or f"https://github.com/{it['dono']}.png", quote=True)


def fotografar(doc, saida, espera=6000):
    if not CHROME:
        raise SystemExit("Chrome headless do Playwright não encontrado em ~/.cache/ms-playwright")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(doc); tmp = f.name
    subprocess.run([str(CHROME[-1]), "--no-sandbox", "--hide-scrollbars", "--window-size=1080,1920", "--force-device-scale-factor=1",
                    f"--virtual-time-budget={espera}", f"--screenshot={saida}", "file://" + tmp], capture_output=True, timeout=120)
    Path(tmp).unlink(missing_ok=True)
    if not Path(saida).exists():
        raise SystemExit(f"cartão não saiu: {saida}")
    return Path(saida)


def cartao_repo(it, modo, desc_pt, saida, destaque=None):
    """desc_pt: o que o projeto faz, em português (até ~110 letras); destaque: uma palavra dele, marcada em amarelo"""
    repo = it["repo"]
    tam = 112 if len(repo) <= 12 else 92 if len(repo) <= 17 else 74 if len(repo) <= 24 else 60
    linhas_nome = 1 if len(repo) * tam * 0.62 < 950 else 2
    desc_y = 480 + 50 + int(tam * 1.05 * linhas_nome) + 40
    chips_y = desc_y + 44 * 1.25 * min(3, max(1, len(desc_pt) // 34 + 1)) + 40
    d = html.escape(desc_pt)
    if destaque and destaque in desc_pt:
        d = d.replace(html.escape(destaque), f"<b>{html.escape(destaque)}</b>", 1)
    ling = it.get("linguagem")
    chips = []
    if ling:
        chips.append(f'<span class="chip"><i style="background:{COR_LING.get(ling, "#a8a8b3")}"></i>{html.escape(ling)}</span>')
    if it.get("estrelas_total"):
        chips.append(f'<span class="chip">⭐ {br(it["estrelas_total"])}</span>')
    chips.append(f'<span class="chip am">🔥 +{br(it["estrelas_periodo"])} {PERIODO[modo].lower()}</span>')
    if it.get("criado_em"):
        a, m = it["criado_em"][:4], it["criado_em"][5:7]
        chips.append(f'<span class="chip">criado em {m}/{a}</span>')
    corpo = (f'<div class="rot">TOP 10 GITHUB · {PERIODO[modo]}</div><div class="pos"><small>#</small>{it["pos"]}</div>'
             f'<img class="foto" src="{_foto(None, it)}">'
             f'<div class="nome"><div class="dono">{html.escape(it["dono"])} /</div><div class="repo">{html.escape(repo)}</div></div>'
             f'<div class="desc">{d}</div><div class="chips">{"".join(chips)}</div>')
    css = CSS_REPO.replace("%TAM%", str(tam)).replace("%DESC_Y%", str(desc_y)).replace("%CHIPS_Y%", str(int(chips_y)))
    return fotografar(BASE.replace("%CSS%", css).replace("%CORPO%", corpo), saida)


def cartao_ranking(top, modo, data_br, saida):
    mx = max(x["estrelas_periodo"] for x in top) or 1
    linhas = []
    for x in sorted(top, key=lambda x: x["pos"]):
        top1 = " top" if x["pos"] == 1 else ""
        linhas.append(f'<div class="r{top1}"><span class="n">{x["pos"]}</span><img src="{_foto(None, x)}">'
                      f'<span class="nm">{html.escape(x["repo"])}</span><span class="bar"><i style="width:{100 * x["estrelas_periodo"] / mx:.1f}%"></i></span>'
                      f'<span class="v">+{br(x["estrelas_periodo"])}</span></div>')
    tit = {"dia": "BOMBANDO <b>HOJE</b>", "semana": "BOMBANDO <b>NA SEMANA</b>", "mes": "BOMBANDO <b>NO MÊS</b>"}[modo]
    corpo = (f'<div class="rot">TOP 10 GITHUB · {data_br}</div><div class="tit">{tit}</div>'
             f'<div class="lista">{"".join(linhas)}</div><div class="fonte">⭐ estrelas ganhas {PERIODO[modo].lower()} · fonte: github.com/trending</div>')
    return fotografar(BASE.replace("%CSS%", CSS_RANK).replace("%CORPO%", corpo), saida)
