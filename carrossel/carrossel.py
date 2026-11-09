#!/usr/bin/env python3
"""Carrosséis diários do Bombando no GitHub (Instagram/TikTok inema.tech, marca FTD do lives3 + tópico no INEMA.DEV; Nei 09/11/2026: "carrossel no lives3, os outros no lives4").

Dois tipos (Nei, 04/11/2026: "2 carrosséis e 1 vídeo diário"):
  top10  — os 10 do GitHub Trending do dia (reusa a coleta do vídeo da manhã), sai às 14h
  area   — o Top 8 de uma área por dia da semana (carrossel/area.py), sai às 18h

  python3 carrossel/carrossel.py dados    <pasta> top10|area [AAAA-MM-DD]   → dados.json
  python3 carrossel/carrossel.py textos   <pasta>      claude -p (carrossel/textos.md) → textos.json + portão
  python3 carrossel/carrossel.py montar   <pasta>      prints do README → slides.json → slides/*.png + portão + folha.jpg
  python3 carrossel/carrossel.py revisar  <pasta>      claude -p olha a folha (carrossel/revisor.md) → revisao.json
  python3 carrossel/carrossel.py fazer    <pasta> top10|area [dia]   tudo acima, na ordem
  python3 carrossel/carrossel.py publicar <pasta>      Telegram INEMA.DEV → metritds (Instagram + TikTok) → aviso azul no v3

Desligar partes: SEM_TG=1 SEM_METRI=1 SEM_BOT=1. RASCUNHO=1 agenda no Metricool como rascunho.
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml
from PIL import Image

AQUI = Path(__file__).resolve().parent
R = AQUI.parent
CONTA = "@inema.tech"
GRUPO_TG = "INEMA.DEV"
TOPICO_TG = R / "auto/telegram-topico-carrossel.txt"
HIST = R / "historico/carrossel-area.jsonl"
AGENDA = "Todo dia no <b>@inema.tech</b>: <b>14h</b> Top 10 do GitHub · <b>18h</b> Top da área"
ICONES = {"zap", "video", "image", "mic", "code", "terminal", "bot", "brain", "shield", "lock", "search", "globe", "layers",
          "clock", "cpu", "database", "wand", "chart", "folder", "link", "chat", "download"}
PROIBIDO = re.compile(r"revolucion|incrível|inacreditável|insano|mude sua vida|!!|\bmort[eoa]s?\b|\btu\b|\bteu\b", re.I)
SEM_CHAVE = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}   # claude -p sempre pela assinatura


def log(*a):
    print("[carrossel]", *a, flush=True)


def falha(msg):
    sys.exit(f"[carrossel] REPROVOU: {msg}")


def br(n):
    return f"{int(n):,}".replace(",", ".")


def ler(cd):
    cd = Path(cd).resolve()
    return cd, json.loads((cd / "dados.json").read_text())


def data_br(d):
    return dt.date.fromisoformat(d["dia"]).strftime("%d/%m/%Y")


def tema(d):
    if d["tipo"] == "top10":
        return "os 10 projetos que mais ganharam estrelas hoje no GitHub (Top 10 do dia)"
    return f"os {len(d['itens'])} repositórios que mais crescem no GitHub na área {d['area']['curto']}"


# ------------------------------------------------------------------ dados
def cmd_dados(cd, tipo, dia=None):
    cd = Path(cd).resolve(); dia = dia or dt.date.today().isoformat()
    (cd / "pesquisa").mkdir(parents=True, exist_ok=True)
    if tipo == "top10":
        ed = R / f"edicoes/{dia}-top10-dia"
        fonte = ed / "pesquisa/top10.json"
        if not fonte.exists():   # o vídeo da manhã não coletou: coleta aqui mesmo
            log("sem a coleta do vídeo; coletando o Trending agora")
            subprocess.run([sys.executable, R / "coleta/trending.py", cd, "dia"], check=True, timeout=900,
                           env={**os.environ, "GB_ESPERA_TRENDING": "0"})  # carrossel não espera (08/11/2026)
            fonte = cd / "pesquisa/top10.json"
        top = json.loads(fonte.read_text())
        desc = {}
        if (ed / "ficha.yaml").exists():
            for x in yaml.safe_load((ed / "ficha.yaml").read_text()).get("partes", []):
                if x.get("repo"):
                    desc[x["repo"]] = x.get("desc", "")
        itens = []
        for it in sorted(top["top10"], key=lambda x: int(x["pos"])):
            itens.append({k: it.get(k) for k in ("pos", "nome", "dono", "repo", "descricao_en", "linguagem", "estrelas_periodo",
                                                  "estrelas_total", "criado_em", "url", "topicos")}
                         | {"readme": (it.get("readme") or "")[:1500], "desc_pt": desc.get(it["nome"], "")})
        d = {"tipo": "top10", "dia": dia, "itens": itens, "soma": sum(int(x["estrelas_periodo"]) for x in itens),
             "fonte": "github.com/trending"}
    else:
        subprocess.run([sys.executable, AQUI / "area.py", cd, dia], check=True, timeout=1800)
        a = json.loads((cd / "pesquisa/area.json").read_text())
        itens = [it | {"readme": (it.get("readme") or "")[:1500], "desc_pt": ""} for it in a["itens"]]
        d = {"tipo": "area", "dia": dia, "area": a["area"], "itens": itens, "fonte": a["fonte"]}
    (cd / "dados.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    log(f"dados: {d['tipo']} · {len(d['itens'])} repositórios")


# ------------------------------------------------------------------ textos (claude -p) + portão
def checar_textos(d, t):
    erros = []
    c = t.get("capa") or {}
    man = (c.get("manchete") or "").strip()
    if not man or len(man.split()) > 6 or len(man) > 44:
        erros.append(f"capa.manchete: até 6 palavras e 44 caracteres ({man!r})")
    if re.search(r"\d", man):
        erros.append("capa.manchete sem algarismo")
    if c.get("destaque") and c["destaque"].upper() not in man.upper():
        erros.append("capa.destaque tem de estar na manchete")
    reps = t.get("repos") or {}
    for it in d["itens"]:
        x = reps.get(it["nome"])
        if not x:
            erros.append(f"{it['nome']}: faltou"); continue
        g = x.get("gancho") or []
        if len(g) != 2 or any(not s or len(s) > 20 for s in g):
            erros.append(f"{it['nome']}: gancho = 2 linhas de até 20 caracteres ({g})")
        oq = x.get("o_que_e") or ""
        if not 60 <= len(oq) <= 180:
            erros.append(f"{it['nome']}: o_que_e com {len(oq)} caracteres (80–170)")
        bs = x.get("beneficios") or []
        if len(bs) != 2:
            erros.append(f"{it['nome']}: 2 benefícios")
        for b in bs:
            if b.get("icone") not in ICONES:
                b["icone"] = "zap"
            if not b.get("titulo") or len(b["titulo"]) > 26 or not 25 <= len(b.get("texto") or "") <= 90:
                erros.append(f"{it['nome']}: benefício fora do tamanho ({b})")
        fl = x.get("fluxo") or []
        if len(fl) != 3 or any(not s or len(s) > 16 for s in fl):
            erros.append(f"{it['nome']}: fluxo = 3 passos de até 15 caracteres ({fl})")
        tudo = " ".join([*g, oq, *(b.get("titulo", "") + " " + b.get("texto", "") for b in bs), *fl])
        if PROIBIDO.search(tudo):
            erros.append(f"{it['nome']}: palavra proibida ({PROIBIDO.search(tudo).group(0)})")
        if re.search(r"\d[\d.,]*\s*(mil\s*)?estrelas", tudo, re.I):
            erros.append(f"{it['nome']}: número de estrelas no texto")
    for k in ("legenda_abertura", "telegram"):
        if not (t.get(k) or "").strip():
            erros.append(f"faltou {k}")
        elif PROIBIDO.search(t[k]):
            erros.append(f"{k}: palavra proibida")
    return erros


def cmd_textos(cd):
    cd, d = ler(cd)
    pedido = ((AQUI / "textos.md").read_text().replace("{CD}", str(cd)).replace("{TEMA}", tema(d))
              .replace("{DATA_BR}", data_br(d)))
    for tent in (1, 2):
        (cd / "textos.json").unlink(missing_ok=True); (cd / "ERRO.txt").unlink(missing_ok=True)
        extra = ""
        if tent == 2:
            extra = "\n\nA tentativa anterior voltou do portão com estes erros; corrija todos:\n- " + "\n- ".join(erros)
        with open(cd / "textos.log", "a") as lg:
            subprocess.run(["claude", "-p", pedido + extra, "--permission-mode", "bypassPermissions", "--add-dir", str(cd)],
                           cwd=cd, stdout=lg, stderr=subprocess.STDOUT, timeout=1800, env=SEM_CHAVE, stdin=subprocess.DEVNULL)
        if (cd / "ERRO.txt").exists():
            falha("roteirista: " + (cd / "ERRO.txt").read_text()[:300])
        try:
            t = json.loads((cd / "textos.json").read_text())
        except Exception as e:  # noqa: BLE001
            erros = [f"textos.json ilegível ({e})"]; continue
        erros = checar_textos(d, t)
        if not erros:
            (cd / "textos.json").write_text(json.dumps(t, ensure_ascii=False, indent=1))
            log("textos OK"); return
        log("portão dos textos:", erros)
    falha("textos reprovados no portão: " + "; ".join(erros)[:600])


# ------------------------------------------------------------------ montar (prints + slides + portão)
def cmd_montar(cd):
    cd, d = ler(cd)
    t = json.loads((cd / "textos.json").read_text())
    subprocess.run([sys.executable, AQUI / "prints.py", cd], check=True, timeout=1800)
    pj = json.loads((cd / "prints.json").read_text())
    slides = []
    for it in d["itens"]:
        x = t["repos"][it["nome"]]
        if d["tipo"] == "top10":
            stat, rot = f"+{br(it['estrelas_periodo'])}", "hoje"
            criado = dt.date.fromisoformat(it["criado_em"][:10]) if it.get("criado_em") else None
            info2 = (it.get("linguagem") or "") + (f" · desde {criado.strftime('%m/%Y')}" if criado else "")
        else:
            stat, rot = f"+{br(it['por_dia'])}", "por dia"
            info2 = (it.get("linguagem") or "") + f" · criado há {it['idade_dias']} dias"
        slides.append({"pos": it["pos"], "nome": it["nome"], "repo": it["repo"], "url": it.get("url") or f"https://github.com/{it['nome']}",
                       "gancho": x["gancho"], "o_que_e": x["o_que_e"], "beneficios": x["beneficios"], "fluxo": x["fluxo"],
                       "print": f"prints/{it['pos']}.png", "print_fonte": (pj.get(it["nome"]) or {}).get("fonte"),
                       "stat": stat, "stat_rotulo": rot, "total": br(it["estrelas_total"] or 0), "info2": info2.strip(" ·")})
    # mosaico da capa: prints de verdade do README primeiro
    fundo = [s["print"] for s in slides if s["print_fonte"] == "readme"][:12]
    fundo += [s["print"] for s in slides if s["print"] not in fundo][: 12 - len(fundo)]
    n = len(slides)
    if d["tipo"] == "top10":
        capa = {"linha1": "TOP 10", "linha2": "DO GITHUB HOJE", "numero": f"+{br(d['soma'])}",
                "numero_rotulo": "estrelas ganhas pelos 10 em 24 horas"}
        serie = "TOP 10 DO GITHUB"
        fecho = {"titulo_a": "Os 10 links estão", "titulo_b": "na legenda.",
                 "texto": "Salve este post para testar com calma e mande para quem vive de tecnologia."}
    else:
        capa = {"linha1": f"TOP {n}", "linha2": d["area"]["nome"],
                "numero": f"+{br(sum(it['por_dia'] for it in d['itens']))}",
                "numero_rotulo": f"estrelas por dia, somando os {n} (criados nos últimos meses)"}
        serie = f"TOP {n} · {d['area']['nome']}"
        fecho = {"titulo_a": f"Os {n} links estão", "titulo_b": "na legenda.",
                 "texto": f"Salve para testar depois. Amanhã tem outra área, sempre às 18h."}
    capa |= {"manchete": t["capa"]["manchete"].upper(), "destaque": (t["capa"].get("destaque") or "").upper(), "fundo": fundo}
    fecho["agenda"] = AGENDA
    S = {"tipo": d["tipo"], "serie": serie, "conta": CONTA, "data_br": data_br(d), "capa": capa, "slides": slides, "fecho": fecho}
    (cd / "slides.json").write_text(json.dumps(S, ensure_ascii=False, indent=1))
    subprocess.run(["node", AQUI / "render.mjs", cd], check=True, timeout=900, cwd=R)
    # portão do desenho
    rel = json.loads((cd / "relatorio.json").read_text())
    erros = []
    for p in rel["paginas"]:
        for c in p["caixas"]:
            if c["estourou"]:
                erros.append(f"{p['nome']}: texto não coube ({c['classe']})")
        if p["fora"]:
            erros.append(f"{p['nome']}: passou do fim da página ({p['fora']})")
        for i in p["imagens"]:
            if not i["ok"]:
                erros.append(f"{p['nome']}: imagem quebrada ({i['src']})")
        if p["altura_print"] is not None and p["altura_print"] < 250:
            erros.append(f"{p['nome']}: print espremido ({p['altura_print']} px)")
        if "Sora" not in p["fontes"]:
            erros.append(f"{p['nome']}: fonte Sora não carregou")
    pngs = sorted((cd / "slides").glob("*.png"))
    if len(pngs) != n + 2:
        erros.append(f"{len(pngs)} slides (esperado {n + 2})")
    for p in pngs:
        if Image.open(p).size != (1080, 1350):
            erros.append(f"{p.name}: tamanho errado")
    folha(cd, pngs)
    if erros:
        falha("; ".join(erros)[:800])
    log(f"montado: {len(pngs)} slides, portão OK")


def folha(cd, pngs):
    cols, w, h = 4, 360, 450
    linhas = (len(pngs) + cols - 1) // cols
    f = Image.new("RGB", (cols * w + (cols - 1) * 8, linhas * h + (linhas - 1) * 8), "#333")
    for k, p in enumerate(pngs):
        f.paste(Image.open(p).convert("RGB").resize((w, h)), ((k % cols) * (w + 8), (k // cols) * (h + 8)))
    f.save(cd / "folha.jpg", quality=88)


# ------------------------------------------------------------------ revisor (claude -p)
def cmd_revisar(cd):
    cd, d = ler(cd)
    pedido = ((AQUI / "revisor.md").read_text().replace("{CD}", str(cd)).replace("{TEMA}", tema(d))
              .replace("{DATA_BR}", data_br(d)))
    try:
        r = subprocess.run(["claude", "-p", "--output-format", "json", "--allowedTools", "Read", "--add-dir", str(cd), "--", pedido],
                           cwd=cd, capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL, env=SEM_CHAVE)
        res = json.loads(r.stdout)["result"].strip()
        v = json.loads(res[res.index("{"): res.rindex("}") + 1])
        assert v.get("veredito") in ("aprovado", "reprovado")
    except Exception as e:  # noqa: BLE001
        v = {"veredito": "erro", "motivo": f"revisor não respondeu direito: {str(e)[:200]}"}
    (cd / "revisao.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    log("revisor:", json.dumps(v, ensure_ascii=False))
    return v


def cmd_fazer(cd, tipo, dia=None):
    cd = Path(cd).resolve()
    if not (cd / "dados.json").exists():
        cmd_dados(cd, tipo, dia)
    if not (cd / "textos.json").exists():
        cmd_textos(cd)
    cmd_montar(cd)
    v = cmd_revisar(cd)
    if v["veredito"] == "erro":
        v = cmd_revisar(cd)
    return v


# ------------------------------------------------------------------ publicar
def textos_pub(cd, d, S, t):
    """legenda do Instagram/TikTok e post do Telegram, com os links"""
    links = "\n".join(f"{s['pos']}. {s['nome']} — {s['url']}" for s in S["slides"])
    titulo = (f"Top 10 do GitHub · {S['data_br']}" if d["tipo"] == "top10"
              else f"Top {len(S['slides'])} do GitHub · {d['area']['curto']} · {S['data_br']}")
    leg = (f"{titulo}\n\n{t['legenda_abertura'].strip()}\n\n{links}\n\nCursos grátis de IA em inema.club\n"
           f"#github #opensource #ia #programacao #inemaclub")
    return titulo, leg[:2150]


def telegram(cd, d, S, t, titulo):
    tg = Path.home() / "projetos/telegramtopicosindex"
    log_tg = cd / "telegram.log"
    if log_tg.exists() and "mensagens publicadas" in log_tg.read_text():
        log("Telegram: já postado"); return True
    pngs = sorted((cd / "slides").glob("*.png"))
    linhas = [f"🔥 **{titulo}**", "", t["telegram"].strip(), "", "[[album:" + "|".join(str(p) for p in pngs) + "]]", "---",
              "🔗 **Os links**"]
    for s in S["slides"]:
        linhas.append(f"{s['pos']}. **{s['nome']}** · {s['stat']} ⭐ {s['stat_rotulo']} — {s['o_que_e']}\n   {s['url']}")
    linhas += ["", "Qual desses você vai testar primeiro? 👇"]
    md = cd / "telegram.md"; md.write_text("\n".join(linhas) + "\n")
    cmd = [str(tg / "venv/bin/python"), "postar_topico.py", "--grupo", GRUPO_TG, "--texto", str(md), "--enviar"]
    if TOPICO_TG.exists():
        cmd += ["--topico", TOPICO_TG.read_text().strip(), "--titulo", titulo]
    else:
        cmd += ["--titulo", "BOMBANDO NO GITHUB - Carrosséis diários", "--capa", str(pngs[0]),
                "--fonte", "📟 Gerado todo dia pelo gitbombando: 14h Top 10 do GitHub · 18h Top da área"]
    livre = 0
    for _ in range(90):   # sessão compartilhada: só posta com 15 s seguidos livre (LESSONS 15/10/2026)
        ocupado = subprocess.run(["lsof", str(tg / "telegram_session.session")], capture_output=True).returncode == 0
        livre = 0 if ocupado else livre + 5
        if livre >= 15:
            break
        time.sleep(5)
    with open(log_tg, "w") as lg:
        r = subprocess.run(cmd, cwd=tg, stdout=lg, stderr=subprocess.STDOUT, timeout=900)
    if r.returncode:
        log("⚠ Telegram falhou (telegram.log)"); return False
    if not TOPICO_TG.exists():
        for ln in reversed((tg / "logs/postagens.jsonl").read_text().strip().splitlines()[-20:]):
            ev = json.loads(ln)
            if ev.get("etapa") == "criar_topico" and ev.get("titulo", "").startswith("BOMBANDO NO GITHUB - Carross"):
                TOPICO_TG.write_text(f"{ev['topico']}\n"); log("tópico do INEMA.DEV criado:", ev["topico"]); break
    return True


def metritds(cd, d, S, leg, titulo):
    """carrossel no Instagram + TikTok (modo foto) inema.tech (marca FTD) pelo Metricool da conta inematds (claude -p, assinatura)"""
    marca = cd / "metritds.txt"
    if marca.exists() and not os.environ.get("RASCUNHO") and not os.environ.get("FORCAR"):
        log("metritds: já agendado"); return {"ok": True, "redes": marca.read_text().splitlines()[1:2]}
    rel = "social"
    if subprocess.run(["gh", "release", "view", rel, "-R", "inematds/gitbombando"], capture_output=True).returncode:
        subprocess.run(["gh", "release", "create", rel, "-R", "inematds/gitbombando", "--title", "Vídeos para redes sociais",
                        "--notes", "Cópias das peças do Bombando no GitHub usadas pelo Metricool (Instagram/TikTok inema.tds)."],
                       capture_output=True)
    urls = []
    with tempfile.TemporaryDirectory() as tmp:
        arqs = []
        for k, p in enumerate(sorted((cd / "slides").glob("*.png")), 1):
            j = Path(tmp) / f"gitbombando-{cd.name}-{k:02d}.jpg"
            Image.open(p).convert("RGB").save(j, quality=92)
            arqs.append(j)
            urls.append(f"https://github.com/inematds/gitbombando/releases/download/{rel}/{j.name}")
        r = subprocess.run(["gh", "release", "upload", rel, *map(str, arqs), "-R", "inematds/gitbombando", "--clobber"],
                           capture_output=True, text=True, timeout=900)
        if r.returncode:
            return {"ok": False, "erro": "upload na release: " + r.stderr[:200]}
    (cd / "metritds-texto.txt").write_text(leg)
    alvo = time.time() + 600
    quando = time.strftime("%Y-%m-%dT%H:%M:00", time.gmtime(alvo))   # UTC (lição do metricool-pub2)
    rascunho = "true" if os.environ.get("RASCUNHO") else "false"
    pedido = f"""Use só as ferramentas do servidor MCP metricool-inematds.
1) getBrandSettings: use a marca FTD (blogId 7908265, Instagram + TikTok inema.tech) e veja em networksData se instagram e tiktok estão conectados.
2) createScheduledPost UMA vez com as redes conectadas (das duas) em providers. É um CARROSSEL DE IMAGENS (não vídeo):
   date = {quando}Z ; publicationDate = {{dateTime: "{quando}", timezone: "UTC"}}
   media = {json.dumps(urls)} (nesta ordem, todas)
   text = conteúdo exato do arquivo {cd}/metritds-texto.txt (leia com a ferramenta Read)
   draft = {rascunho} ; autoPublish = true
   instagramData = {{type: "POST", isAiGenerated: true}}
   tiktokData = {{privacyOption: "PUBLIC_TO_EVERYONE", title: "{titulo[:88]}", photoCoverIndex: 0, autoAddMusic: true}}
   Se der erro por causa do TikTok (fotos), tente de novo SÓ com instagram e diga isso no campo erro.
3) Responda APENAS uma linha JSON, sem crase: {{"ok":true|false,"redes":[...],"faltam":[...],"planner":[...],"erro":"texto ou vazio"}}"""
    r = subprocess.run(["claude", "-p", "--allowedTools",
                        "mcp__metricool-inematds__getBrandSettings mcp__metricool-inematds__createScheduledPost Read"],
                       input=pedido, cwd=cd, capture_output=True, text=True, timeout=900, env=SEM_CHAVE)
    (cd / "metritds.log").write_text(r.stdout + r.stderr)
    m = re.findall(r'\{[^{}]*"ok"[^{}]*\}', r.stdout)
    try:
        res = json.loads(m[-1])
    except Exception:  # noqa: BLE001
        res = {"ok": False, "erro": r.stdout[-300:]}
    if res.get("ok") and not os.environ.get("RASCUNHO"):
        marca.write_text(time.strftime("%d/%m %H:%M", time.localtime(alvo)) + "\n" + ", ".join(res.get("redes", [])) + "\n")
    return res


def cmd_publicar(cd):
    cd, d = ler(cd)
    S = json.loads((cd / "slides.json").read_text()); t = json.loads((cd / "textos.json").read_text())
    titulo, leg = textos_pub(cd, d, S, t)
    ok_tg = None if os.environ.get("SEM_TG") else telegram(cd, d, S, t, titulo)
    res = {"ok": None} if os.environ.get("SEM_METRI") else metritds(cd, d, S, leg, titulo)
    if d["tipo"] == "area" and not os.environ.get("RASCUNHO") and (ok_tg or res.get("ok")):
        HIST.parent.mkdir(exist_ok=True)
        with HIST.open("a") as h:
            h.write(json.dumps({"dia": d["dia"], "area": d["area"]["chave"], "repos": [s["nome"] for s in S["slides"]]},
                               ensure_ascii=False) + "\n")
    rev = json.loads((cd / "revisao.json").read_text()) if (cd / "revisao.json").exists() else {}
    faixa = "🟦" * 12
    tg_txt = {None: "pulado", True: f"ok (tópico {TOPICO_TG.read_text().strip() if TOPICO_TG.exists() else '?'})", False: "⚠ FALHOU"}[ok_tg]
    mt_txt = ("pulado" if res.get("ok") is None else
              f"ok · {', '.join(res.get('redes', []))}" + (" (RASCUNHO)" if os.environ.get("RASCUNHO") else "") if res.get("ok")
              else f"⚠ NÃO AGENDOU: {res.get('erro', '')[:200]}")
    msg = (f"{faixa}\n🔵 CARROSSEL PUBLICADO DIRETO · {titulo}\n{faixa}\n"
           f"Telegram {GRUPO_TG}: {tg_txt}\nInstagram/TikTok inema.tech (FTD): {mt_txt}"
           + (f"\nAinda não conectadas: {', '.join(res['faltam'])}" if res.get("faltam") else "")
           + f"\n{len(S['slides']) + 2} slides · revisor: {rev.get('veredito', '?')}"
           + (f"\n🟥 SUGESTÃO: {rev['sugestao'][:300]}" if rev.get("sugestao") else ""))
    (cd / "v3.txt").write_text(msg + "\n")
    log(msg)
    deu_certo = ok_tg is not False and res.get("ok") is not False
    if not os.environ.get("SEM_BOT") and not deu_certo:  # Nei, 06/11/2026: v3 só quando ele pedir ou der erro
        capa = cd / "v3-capa.jpg"
        Image.open(cd / "slides/01-capa.png").convert("RGB").resize((540, 675)).save(capa, quality=88)
        Path(str(capa) + ".envio-v3.json").unlink(missing_ok=True)
        subprocess.run(["node", R / "bin/enviar_bot_v3.mjs", capa, msg], timeout=900)
    return ok_tg is not False and res.get("ok") is not False


def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    c, cd = a[0], a[1]
    if c == "dados":
        cmd_dados(cd, a[2], a[3] if len(a) > 3 else None)
    elif c == "fazer":
        v = cmd_fazer(cd, a[2], a[3] if len(a) > 3 else None)
        sys.exit(0 if v["veredito"] == "aprovado" else 3)
    elif c in ("textos", "montar", "revisar"):
        {"textos": cmd_textos, "montar": cmd_montar, "revisar": cmd_revisar}[c](cd)
    elif c == "publicar":
        sys.exit(0 if cmd_publicar(cd) else 1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
