#!/usr/bin/env python3
"""Top 10 do GitHub Trending (dia, semana ou mês) com os dados de cada projeto → <pasta>/pesquisa/top10.json.

  python3 coleta/trending.py <pasta> [dia|semana|mes]

Fontes (só GitHub; API do GitHub liberada pelo Nei em 05/10/2026):
- github.com/trending?since=daily|weekly|monthly (página pública; não existe API de trending): os projetos em alta e
  "N stars today/this week/this month". O Top 10 é ordenado pelas estrelas ganhas no período (pos_trending guarda a ordem
  original da página);
- `gh api repos/<dono>/<repo>`: descrição, linguagem, tópicos, site, estrelas totais, forks, data de criação, foto do dono;
- `gh api repos/<dono>/<repo>/readme`: o começo do README (para o roteirista entender o que o projeto faz);
- curva de estrelas: dos nossos retratos de hora em hora (coleta/retrato.py → historico/estrelas.jsonl), porque a lista de
  stargazers da API responde 404 desde 2026; e sempre o "antes × agora" do período (total − ganho → total).
- historico/<modo>.jsonl: um retrato do Top 10 por rodada (quantas vezes o projeto já apareceu).
"""
import base64, datetime as dt, html, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SINCE = {"dia": "daily", "semana": "weekly", "mes": "monthly"}
PERIODO = {"dia": "today", "semana": "this week", "mes": "this month"}
UA = "Mozilla/5.0 (X11; Linux x86_64) gitbombando/1.0 (+https://github.com/inematds/gitbombando)"


def log(*a):
    print("[coleta]", *a, flush=True)


def baixar(url, tent=3):
    for k in range(tent):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            log(f"falhou {url} ({e}); tentativa {k + 1}")
            time.sleep(5 * (k + 1))
    raise SystemExit(f"não baixou {url}")


def num(s):
    return int(re.sub(r"[^\d]", "", s or "0") or 0)


def trending(modo):
    s = baixar(f"https://github.com/trending?since={SINCE[modo]}")
    linhas = s.split('class="Box-row"')[1:]
    out = []
    for b in linhas:
        m = re.search(r'<h2 class="h3 lh-condensed">\s*<a [^>]*href="/([^"/]+)/([^"]+)"', b)
        if not m:
            continue
        dono, repo = m.group(1), m.group(2)
        desc = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', b, re.S)
        ling = re.search(r'itemprop="programmingLanguage">([^<]+)<', b)
        est = re.search(rf'href="/{re.escape(dono)}/{re.escape(repo)}/stargazers"[^>]*>.*?</svg>\s*([\d,]+)', b, re.S)
        frk = re.search(rf'href="/{re.escape(dono)}/{re.escape(repo)}/forks"[^>]*>.*?</svg>\s*([\d,]+)', b, re.S)
        per = re.search(r'([\d,]+)\s+stars?\s+(today|this week|this month)', b)
        out.append({"pos": len(out) + 1, "nome": f"{dono}/{repo}", "dono": dono, "repo": repo,
                    "descricao_en": html.unescape(re.sub(r"<[^>]+>", "", desc.group(1))).strip() if desc else "",
                    "linguagem": ling.group(1).strip() if ling else None,
                    "estrelas_total_trending": num(est.group(1)) if est else None, "forks_trending": num(frk.group(1)) if frk else None,
                    "estrelas_periodo": num(per.group(1)) if per else 0})
    return out


def gh(caminho, *extra):
    r = subprocess.run(["gh", "api", *extra, caminho], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    return r.stdout


def detalhes(it):
    try:
        j = json.loads(gh(f"repos/{it['nome']}"))
    except RuntimeError as e:
        log(f"{it['nome']}: sem detalhes ({e})"); return
    it.update(estrelas_total=j.get("stargazers_count"), forks=j.get("forks_count"), criado_em=j.get("created_at"),
              atualizado_em=j.get("pushed_at"), topicos=j.get("topics") or [], site=j.get("homepage") or None,
              licenca=(j.get("license") or {}).get("spdx_id"), dono_tipo=(j.get("owner") or {}).get("type"),
              dono_foto=(j.get("owner") or {}).get("avatar_url"), descricao_en=it["descricao_en"] or (j.get("description") or ""),
              url=j.get("html_url") or f"https://github.com/{it['nome']}")
    try:
        rd = json.loads(gh(f"repos/{it['nome']}/readme"))
        txt = base64.b64decode(rd.get("content", "")).decode("utf-8", "replace")
        txt = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", txt)        # tira html e imagens
        it["readme"] = re.sub(r"\n\s*\n+", "\n", txt).strip()[:2500]
    except Exception as e:  # noqa: BLE001
        it["readme"] = ""; log(f"{it['nome']}: sem README ({e})")


def curva(it, modo, agora):
    """curva de estrelas a partir dos NOSSOS retratos de hora em hora (coleta/retrato.py → historico/estrelas.jsonl).
    A lista de quem deu estrela (stargazers) responde 404 desde 2026, então a curva nasce do retrato: por hora (dia, 24 h)
    ou por dia (semana 7 d, mês 30 d). Sempre: 'antes × agora' do período (total − ganho no período → total)."""
    tot = it.get("estrelas_total") or 0
    ganho = it.get("estrelas_periodo") or 0
    if tot:
        antes = max(tot - ganho, 0)
        it["crescimento"] = {"antes": antes, "agora": tot, "ganho": ganho, "pct": round(100 * ganho / antes, 1) if antes else None}
    pts = RETRATOS.get(it["nome"], [])
    janela = {"dia": dt.timedelta(hours=24), "semana": dt.timedelta(days=7), "mes": dt.timedelta(days=30)}[modo]
    pts = sorted((t, v) for t, v in pts if t >= agora - janela - dt.timedelta(hours=1))
    if len(pts) < 3:
        return
    if modo == "dia":   # estrelas ganhas em cada hora (diferença entre retratos)
        rot, v = [], []
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            rot.append((t1 - dt.timedelta(hours=3)).strftime("%Hh")); v.append(max(v1 - v0, 0))
        it["curva"] = {"unidade": "hora", "rotulos": rot[-24:], "v": v[-24:], "pontos": len(pts)}
    else:               # total no fim de cada dia
        ult = {}
        for t, val in pts:
            ult[(t - dt.timedelta(hours=3)).date()] = val
        dias = sorted(ult)
        it["curva"] = {"unidade": "dia", "rotulos": [d.strftime("%d/%m") for d in dias], "v": [ult[d] for d in dias],
                       "tipo": "total", "pontos": len(pts)}


RETRATOS = {}


def ler_retratos():
    h = R / "historico" / "estrelas.jsonl"
    if not h.exists():
        return
    for ln in h.read_text().splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        t = dt.datetime.fromisoformat(r["t"])
        for nome, v in r["e"].items():
            RETRATOS.setdefault(nome, []).append((t, v))


def historico(itens, modo, dia):
    """um retrato por rodada; devolve, para cada projeto, quantas vezes já apareceu no Top 10 deste modo (dias seguidos)"""
    h = R / "historico" / f"{modo}.jsonl"
    h.parent.mkdir(exist_ok=True)
    vistos = {}
    if h.exists():
        for ln in h.read_text().splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r["dia"] >= dia:
                continue
            for x in r["itens"]:
                vistos.setdefault(x["nome"], []).append({"dia": r["dia"], "pos": x["pos"], "estrelas_total": x.get("estrelas_total")})
    for it in itens:
        it["vezes_antes"] = len(vistos.get(it["nome"], []))
        it["historico"] = vistos.get(it["nome"], [])[-10:]
    linhas = [ln for ln in (h.read_text().splitlines() if h.exists() else []) if f'"dia": "{dia}"' not in ln]
    linhas.append(json.dumps({"dia": dia, "itens": [{k: x.get(k) for k in ("pos", "nome", "estrelas_periodo", "estrelas_total")} for x in itens]},
                             ensure_ascii=False))
    h.write_text("\n".join(linhas) + "\n")


def main(a):
    if not a:
        sys.exit(__doc__)
    pasta = Path(a[0]).resolve(); modo = a[1] if len(a) > 1 else "dia"
    if modo not in SINCE:
        sys.exit(f"modo inválido: {modo}")
    (pasta / "pesquisa").mkdir(parents=True, exist_ok=True)
    agora = dt.datetime.now(dt.timezone.utc)
    ler_retratos()
    lista = trending(modo)
    log(f"trending {modo}: {len(lista)} projetos na página")
    if len(lista) < 10:
        raise SystemExit(f"o Trending trouxe só {len(lista)} projetos (página fora do ar ou mudou)")
    # Top 10 = os projetos do Trending com MAIS estrelas ganhas no período (a ordem do próprio Trending mistura outros sinais
    # e o gráfico ficava sem sentido: o 1º com 1.068 e o 4º com 2.371, 28/10/2026)
    for it in lista:
        it["pos_trending"] = it["pos"]
    top = sorted(lista, key=lambda x: -x["estrelas_periodo"])[:10]
    for k, it in enumerate(top, 1):
        it["pos"] = k
    for it in top:
        detalhes(it)
        curva(it, modo, agora)
        log(f"#{it['pos']} {it['nome']} +{it['estrelas_periodo']} ({it.get('estrelas_total')} no total)"
            + (f" · curva {it['curva']['pontos']} retratos" if it.get("curva") else ""))
    dia = (agora - dt.timedelta(hours=3)).date().isoformat()
    historico(top, modo, dia)
    out = {"modo": modo, "periodo": PERIODO[modo], "coletado_em": agora.isoformat(), "dia": dia,
           "fonte": f"https://github.com/trending?since={SINCE[modo]}", "top10": top,
           "soma_periodo": sum(x["estrelas_periodo"] for x in top)}
    (pasta / "pesquisa/top10.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    log("ok", pasta / "pesquisa/top10.json")


if __name__ == "__main__":
    main(sys.argv[1:])
