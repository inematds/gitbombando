#!/usr/bin/env python3
"""Carrosséis do Bombando no GitHub (grade do Nei, 18/11/2026): Telegram INEMA.FTD + fila do x3.

Tipos: top10 (dia) · top5 (semana) · area (área do dia) · agentes. Reusam a coleta do reel do mesmo horário.

  python3 carrossel/carrossel.py dados    <pasta> <tipo> [AAAA-MM-DD]   → dados.json
  python3 carrossel/carrossel.py textos   <pasta>      carrossel/textos.md → textos.json + portão
  python3 carrossel/carrossel.py montar   <pasta>      prints do README → slides.json → slides/*.png + portão + folha.jpg
  python3 carrossel/carrossel.py revisar  <pasta>      revisor olha a folha → revisao.json
  python3 carrossel/carrossel.py fazer    <pasta> <tipo> [dia]   tudo acima, na ordem
  python3 carrossel/carrossel.py publicar <pasta>      Telegram INEMA.FTD → fila do x3 (GB_CANAL_CARROSSEL); v3 só se falhar

Desligar partes: SEM_TG=1 SEM_X3=1 SEM_BOT=1. GB_CONTA = @ que aparece nos slides.
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml
from PIL import Image

AQUI = Path(__file__).resolve().parent
R = AQUI.parent
sys.path.insert(0, str(R))
from auto.ia import executar as executar_ia
CONTA = os.environ.get("GB_CONTA", "@inema.tech")
CANAL_X3 = os.environ.get("GB_CANAL_CARROSSEL", "lives9")   # grade do Nei, 18/11/2026: tudo entra pela fila do x3
X3 = Path.home() / "projetos/yt-pub-x3/yt-pub-x3"
GRUPO_TG = "INEMA.FTD"
TOPICO_TG = R / "auto/telegram-topico-carrossel-ftd.txt"
HIST = R / "historico/carrossel-area.jsonl"
AGENDA = "Todo dia tem <b>Top do GitHub</b> novo"
FONTES = {"top10": "top10-dia", "top5": "top5-semana", "area": "top5-area", "agentes": "top5-agentes"}
ICONES = {"zap", "video", "image", "mic", "code", "terminal", "bot", "brain", "shield", "lock", "search", "globe", "layers",
          "clock", "cpu", "database", "wand", "chart", "folder", "link", "chat", "download"}
PROIBIDO = re.compile(r"revolucion|incrível|inacreditável|insano|mude sua vida|!!|\bmort[eoa]s?\b|\btu\b|\bteu\b", re.I)


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
        return f"os {len(d['itens'])} projetos que mais ganharam estrelas hoje no GitHub (Top {len(d['itens'])} do dia)"
    if d["tipo"] == "top5":
        return f"os {len(d['itens'])} projetos que mais ganharam estrelas na semana no GitHub (Top {len(d['itens'])} da semana)"
    return f"os {len(d['itens'])} repositórios que mais crescem no GitHub na área {d['area']['curto']}"


# ------------------------------------------------------------------ dados
def coletar(tipo, cd, dia):
    """Sem a coleta do reel do mesmo horário, coleta aqui mesmo (carrossel não espera: 08/11/2026)."""
    env = {**os.environ, "GB_ESPERA_TRENDING": "0"}
    if tipo == "top10":
        cmd = [sys.executable, R / "coleta/trending.py", cd, "dia"]
    elif tipo == "top5":
        cmd = [sys.executable, R / "coleta/trending.py", cd, "semana"]
        env |= {"GB_TOP": "5", "GB_SEM_HISTORICO": "1"}
    else:
        cmd = [sys.executable, R / "coleta/area_top.py", cd, tipo, dia]
    subprocess.run(cmd, check=True, timeout=1800, env=env)


def cmd_dados(cd, tipo, dia=None):
    cd = Path(cd).resolve(); dia = dia or dt.date.today().isoformat()
    (cd / "pesquisa").mkdir(parents=True, exist_ok=True)
    ed = R / f"edicoes/{dia}-{FONTES[tipo]}"
    fonte = ed / "pesquisa/top10.json"
    if not fonte.exists():
        log("sem a coleta do vídeo; coletando agora")
        coletar(tipo, cd, dia)
        fonte = cd / "pesquisa/top10.json"
    top = json.loads(fonte.read_text())
    desc = {}
    if (ed / "ficha.yaml").exists():
        for x in yaml.safe_load((ed / "ficha.yaml").read_text()).get("partes", []):
            if x.get("repo"):
                desc[x["repo"]] = x.get("desc", "")
    ordem = sorted(top["top10"], key=lambda x: int(x["pos"]))
    extra = lambda it: {"readme": (it.get("readme") or "")[:1500], "desc_pt": desc.get(it["nome"], "")}
    if tipo in ("top10", "top5"):
        itens = [{k: it.get(k) for k in ("pos", "nome", "dono", "repo", "descricao_en", "linguagem", "estrelas_periodo",
                                         "estrelas_total", "criado_em", "url", "topicos")} | extra(it) for it in ordem]
        d = {"tipo": tipo, "dia": dia, "itens": itens, "soma": sum(int(x["estrelas_periodo"]) for x in itens),
             "fonte": "github.com/trending"}
    else:
        d = {"tipo": "area", "dia": dia, "area": top["area"], "itens": [it | extra(it) for it in ordem], "fonte": top["fonte"]}
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
              .replace("{DATA_BR}", data_br(d)).replace("{CONTA}", CONTA))
    for tent in (1, 2):
        (cd / "textos.json").unlink(missing_ok=True); (cd / "ERRO.txt").unlink(missing_ok=True)
        extra = ""
        if tent == 2:
            extra = "\n\nA tentativa anterior voltou do portão com estes erros; corrija todos:\n- " + "\n- ".join(erros)
        resposta = executar_ia("carrossel_textos", pedido + extra, cd, arquivos=[cd / "dados.json"])
        with open(cd / "textos.log", "a") as lg:
            lg.write(resposta + "\n")
        (cd / "textos.json").write_text(resposta)
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
        if d["tipo"] in ("top10", "top5"):
            stat, rot = f"+{br(it['estrelas_periodo'])}", "hoje" if d["tipo"] == "top10" else "na semana"
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
    if d["tipo"] in ("top10", "top5"):
        hoje = d["tipo"] == "top10"
        capa = {"linha1": f"TOP {n}", "linha2": "DO GITHUB HOJE" if hoje else "DO GITHUB NA SEMANA", "numero": f"+{br(d['soma'])}",
                "numero_rotulo": f"estrelas ganhas pelos {n} em {'24 horas' if hoje else '7 dias'}"}
        serie = f"TOP {n} DO GITHUB"
        fecho = {"titulo_a": f"Os {n} nomes estão", "titulo_b": "na legenda.",
                 "texto": "Busque o nome no GitHub. Salve este post para testar com calma e mande para quem vive de tecnologia."}
    else:
        capa = {"linha1": f"TOP {n}", "linha2": d["area"]["nome"],
                "numero": f"+{br(sum(it['por_dia'] for it in d['itens']))}",
                "numero_rotulo": f"estrelas por dia, somando os {n} (criados nos últimos meses)"}
        serie = f"TOP {n} · {d['area']['nome']}"
        fecho = {"titulo_a": f"Os {n} nomes estão", "titulo_b": "na legenda.",
                 "texto": "Busque o nome no GitHub. Salve para testar depois e mande para quem vive de tecnologia."}
    capa |= {"manchete": t["capa"]["manchete"].upper(), "destaque": (t["capa"].get("destaque") or "").upper(), "fundo": fundo}
    fecho["agenda"] = AGENDA
    S = {"tipo": d["tipo"], "serie": serie, "conta": CONTA, "data_br": data_br(d), "capa": capa, "slides": slides, "fecho": fecho}
    (cd / "slides.json").write_text(json.dumps(S, ensure_ascii=False, indent=1))
    subprocess.run(["node", AQUI / "render.mjs", cd], check=True, timeout=900, cwd=R)
    # portão do desenho
    rel = json.loads((cd / "relatorio.json").read_text())
    erros = []
    leves = []   # defeito pequeno: não barra; o revisor olha a imagem e decide (Nei, 09/11/2026: "pouca coisa, deixa rodar")
    for p in rel["paginas"]:
        for c in p["caixas"]:
            if c["estourou"]:
                leves.append(f"{p['nome']}: texto não coube ({c['classe']})")
        if p["fora"]:
            erros.append(f"{p['nome']}: passou do fim da página ({p['fora']})")
        for i in p["imagens"]:
            if not i["ok"]:
                erros.append(f"{p['nome']}: imagem quebrada ({i['src']})")
        if p["altura_print"] is not None and p["altura_print"] < 250:
            leves.append(f"{p['nome']}: print espremido ({p['altura_print']} px)")
        if "Sora" not in p["fontes"]:
            erros.append(f"{p['nome']}: fonte Sora não carregou")
    pngs = sorted((cd / "slides").glob("*.png"))
    if len(pngs) != n + 2:
        erros.append(f"{len(pngs)} slides (esperado {n + 2})")
    for p in pngs:
        if Image.open(p).size != (1080, 1350):
            erros.append(f"{p.name}: tamanho errado")
    folha(cd, pngs)
    if leves:
        (cd / "avisos.txt").write_text("\n".join(leves) + "\n")
        log("avisos leves (o revisor decide):", "; ".join(leves)[:300])
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
              .replace("{DATA_BR}", data_br(d)).replace("{CONTA}", CONTA))
    try:
        arquivos = [cd / "slides.json"]
        if (cd / "avisos.txt").exists(): arquivos.append(cd / "avisos.txt")
        res = executar_ia("carrossel_revisao", pedido, cd, arquivos=arquivos,
                          imagens=[cd / "folha.jpg", *sorted((cd / "slides").glob("*.png"))])
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
    if v["veredito"] == "reprovado" and nova_tentativa_prints(cd, v):
        cmd_montar(cd)
        v = cmd_revisar(cd)
        if v["veredito"] == "erro":
            v = cmd_revisar(cd)
    return v


def nova_tentativa_prints(cd, v):
    """Revisor reprovou print (Nei, 26/11/2026: "faz a nova tentativa automática"): troca só esses prints pelo próximo
    da escada (README → cartão do GitHub → cartão INEMA) e revisa de novo. Uma vez só; o resto da reprovação continua parando."""
    cd = Path(cd)
    marca = cd / "prints-trocar.json"
    if marca.exists():
        return False   # já foi a nova tentativa
    S = json.loads((cd / "slides.json").read_text())
    nomes = {s["nome"] for s in S["slides"]}
    ruins = [n for n in (v.get("prints_ruins") or []) if n in nomes]
    if not ruins and "print" in (v.get("motivo") or "").lower():   # revisor sem o campo novo: slide k = posição k-1 (1 é a capa)
        por_pos = {s["pos"]: s["nome"] for s in S["slides"]}
        ruins = [por_pos[k - 1] for k in (v.get("slides_ruins") or []) if isinstance(k, int) and k - 1 in por_pos]
    if not ruins:
        return False
    fonte = {s["nome"]: s.get("print_fonte") for s in S["slides"]}
    trocar = {n: "cartao" if fonte.get(n) in ("opengraph", "cartao-inema") else "opengraph" for n in ruins}
    marca.write_text(json.dumps(trocar, ensure_ascii=False, indent=1))
    log("revisor reprovou print; nova tentativa com", json.dumps(trocar, ensure_ascii=False))
    return True


# ------------------------------------------------------------------ publicar
def textos_pub(cd, d, S, t):
    """legenda do Instagram/TikTok (Metricool): só os nomes, SEM link (regra do Nei 05/11/2026; os links ficam no Telegram)"""
    links = "\n".join(f"{s['pos']}. {s['nome']}" for s in S["slides"])
    assunto = {"top10": "", "top5": " na semana"}.get(d["tipo"])
    titulo = (f"Top {len(S['slides'])} do GitHub{assunto} · {S['data_br']}" if assunto is not None
              else f"Top {len(S['slides'])} do GitHub · {d['area']['curto']} · {S['data_br']}")
    leg = (f"{titulo}\n\n{t['legenda_abertura'].strip()}\n\n{links}\n\nTá tudo no inema.club: lá você aprende a integrar estes projetos em vez de só copiar, direto na internet\n"
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
                "--fonte", "📟 Gerado todo dia pelo gitbombando: Top do GitHub e tops por área"]
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
                TOPICO_TG.write_text(f"{ev['topico']}\n"); log(f"tópico do {GRUPO_TG} criado:", ev["topico"]); break
    return True


def entregar_x3(cd, S, leg, titulo):
    """Põe o carrossel na fila do x3; quem publica nas redes é o x3 (Nei, 18/11/2026: "tudo direto no x3")."""
    marca = cd / "x3.txt"
    if marca.exists() and not os.environ.get("FORCAR"):
        log("x3: já entregue"); return {"ok": True, "item": marca.read_text().strip()}
    pasta = cd / "x3"
    shutil.rmtree(pasta, ignore_errors=True); pasta.mkdir()
    for k, p in enumerate(sorted((cd / "slides").glob("*.png")), 1):
        Image.open(p).convert("RGB").save(pasta / f"{k:02d}.jpg", quality=92)
    (pasta / "post.json").write_text(json.dumps({"tipo": "carrossel", "titulo": titulo, "texto_rs": leg, "quando": "agora"}, ensure_ascii=False))
    r = subprocess.run([str(X3), "enviar", str(pasta), "--canal", CANAL_X3], capture_output=True, text=True, timeout=600)
    saida = r.stdout + r.stderr
    m = re.search(r"item (\d+)", saida)
    shutil.rmtree(pasta, ignore_errors=True)
    if r.returncode or not m:
        return {"ok": False, "erro": saida[-300:]}
    marca.write_text(f"{CANAL_X3} item {m.group(1)}\n")
    return {"ok": True, "item": f"{CANAL_X3} item {m.group(1)}"}


def cmd_publicar(cd):
    cd, d = ler(cd)
    S = json.loads((cd / "slides.json").read_text()); t = json.loads((cd / "textos.json").read_text())
    titulo, leg = textos_pub(cd, d, S, t)
    ok_tg = None if os.environ.get("SEM_TG") else telegram(cd, d, S, t, titulo)
    res = {"ok": None} if os.environ.get("SEM_X3") else entregar_x3(cd, S, leg, titulo)
    if d["tipo"] == "area" and (ok_tg or res.get("ok")):
        HIST.parent.mkdir(exist_ok=True)
        with HIST.open("a") as h:
            h.write(json.dumps({"dia": d["dia"], "area": d["area"]["chave"], "repos": [s["nome"] for s in S["slides"]]},
                               ensure_ascii=False) + "\n")
    rev = json.loads((cd / "revisao.json").read_text()) if (cd / "revisao.json").exists() else {}
    faixa = "🟦" * 12
    tg_txt = {None: "pulado", True: f"ok (tópico {TOPICO_TG.read_text().strip() if TOPICO_TG.exists() else '?'})", False: "⚠ FALHOU"}[ok_tg]
    x3_txt = ("pulado" if res.get("ok") is None else f"ok · {res.get('item')}" if res.get("ok") else f"⚠ NÃO ENTROU: {res.get('erro', '')[:200]}")
    msg = (f"{faixa}\n🔵 CARROSSEL · {titulo}\n{faixa}\nTelegram {GRUPO_TG}: {tg_txt}\nFila do x3: {x3_txt}"
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
