#!/usr/bin/env python3
"""gitbombando — "Bombando no GitHub": reel 9:16 com o Top 10 do GitHub (dia, semana ou mês), gráficos e o avatar do Nei.
Motor de telejornal copiado do r7ex (que veio do eventosextremospub); roda sozinho pelo timer (auto/rodar.sh).

  python3 gb.py coletar <pasta> [dia|semana|mes]   Top 10 → pesquisa/top10.json (coleta/trending.py)
  python3 gb.py checar <pasta>            portão do roteiro (ficha.yaml escrita pelo claude -p a partir de auto/roteiro.md)
  python3 gb.py imagens <pasta>           Codex desenha a capa (manchete); cartões dos 10 projetos + ranking; print do inema.club
  python3 gb.py avatar <pasta>            avatar no estúdio do HeyGen (precisa de avatar/APROVADO_HEYGEN)
  python3 gb.py cena <pasta>              tempos das palavras + ritmo + cena.js
  python3 gb.py render <pasta>            vídeo → <pasta>/video.mp4 (tela :99)
  python3 gb.py revisar <pasta>           folha de 18 quadros + revisor claude -p (auto/revisor.md) → revisao.json
  python3 gb.py fazer <pasta>             checar → imagens + avatar → cena → render → revisar
  python3 gb.py publicar <pasta>          YouTube lives4 (yt-pubx) → bot v3 → tópico do INEMA.TOOLS no Telegram
"""
import concurrent.futures as cf
import datetime as dt
import json, os, re, shutil, subprocess, sys
from pathlib import Path

import yaml

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R))
from nucleo import cartao, cena as CENA, pecas, retempo as RT, ritmo as RITMO  # noqa: E402

VERSAO = "1.0.0"
CANAL = os.environ.get("GB_CANAL", "lives4")
PERFIL = Path(os.environ.get("R7X_HEYGEN_PERFIL", Path.home() / ".cache/inemaccbot/perfil-heygen"))
TEMPLATE_HEYGEN = os.environ.get("R7X_HEYGEN_TEMPLATE", "TEMPLATE-AVATAR16")
HEYGEN_DIR = R / "heygen"
TELA = ":99"
TROCAS_PADRAO = {"inema ponto club": "inema.club", "dois mil e vinte e seis": "2026", "dois mil e vinte e sete": "2027"}
PERIODO = {"dia": "HOJE", "semana": "NA SEMANA", "mes": "NO MÊS"}
UNID = {"dia": "⭐ HOJE", "semana": "⭐ NA SEMANA", "mes": "⭐ NO MÊS"}
ANTES = {"dia": "ONTEM", "semana": "HÁ 7 DIAS", "mes": "HÁ 30 DIAS"}
NOME = {"dia": "Top 10 do dia", "semana": "Top 10 da semana", "mes": "Top 10 do mês"}
PROIBIDO = re.compile(r"\b(tu|teu|tua|teus|tuas|contigo|segue o canal|se inscreve|inscreva-se|mort[eoa]s?|morreu|óbitos?)\b", re.I)
ESTILO = ("Estilo foto cinematográfica realista de impacto, como pôster de filme: UM único objeto ou assunto principal, grande, "
          "na metade de CIMA do quadro, numa AÇÃO ou estado dramático; luz dramática de cinema (foco forte ou contraluz com "
          "recorte), sombras profundas, contraste alto; luz do assunto amarela (#FACC15) ou, se houver perigo, vermelha (#ff2a1f); "
          "fundo liso e escuro (#0c0c10), a metade de baixo escura e vazia. Sem logotipo de empresa, sem marca d'água, sem pessoas "
          "reconhecíveis (rostos de lado, na sombra ou de costas).")


def log(*a):
    print("[gb]", *a, flush=True)


def falha(msg):
    sys.exit(f"[gb] REPROVOU: {msg}")


def ler(pasta):
    p = Path(pasta).resolve()
    return p, yaml.safe_load((p / "ficha.yaml").read_text()), json.loads((p / "pesquisa/top10.json").read_text())


def br(n):
    return f"{int(n):,}".replace(",", ".")


def legenda(f, txt):
    for a, b in {**TROCAS_PADRAO, **(f.get("trocas") or {})}.items():
        txt = txt.replace(a, b)
    return txt


def fala_total(f):
    return " ".join(x["fala"].strip() for x in f["partes"])


def falas(p, f):
    out = [{"id": f"f{i + 1}", "fala": x["fala"].strip(), "legenda": legenda(f, x["fala"].strip())} for i, x in enumerate(f["partes"])]
    (p / "falas.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def repos(d):
    return {x["nome"]: x for x in d["top10"]}


# ------------------------------------------------------------------ portão do roteiro
def cmd_checar(pasta):
    p, f, d = ler(pasta)
    modo = d["modo"]; erros = []
    P = f.get("partes") or []
    if len(P) != 13:
        erros.append(f"são {len(P)} partes; o formato é 13 (gancho, panorama, os 10 projetos do #10 ao #1, comentário)")
    else:
        if P[0].get("etapa") != "gancho" or P[1].get("etapa") != "panorama" or P[-1].get("etapa") != "comentario":
            erros.append("ordem: parte 1 = gancho, 2 = panorama, 3–12 = repo, 13 = comentario")
        rp = repos(d)
        esperado = [x["nome"] for x in sorted(d["top10"], key=lambda x: -x["pos"])]   # contagem regressiva #10 → #1
        vistos = [x.get("repo") for x in P[2:12]]
        if vistos != esperado:
            erros.append(f"partes 3–12 têm de ser os projetos do #10 ao #1 na ordem: {esperado} (veio {vistos})")
        for i, x in enumerate(P[2:12], 3):
            if x.get("etapa") != "repo":
                erros.append(f"parte {i}: etapa deve ser repo")
            desc = str(x.get("desc") or "")
            if not 25 <= len(desc) <= 115:
                erros.append(f"parte {i}: desc com {len(desc)} letras (25–115: o que o projeto faz, em português simples)")
            if x.get("destaque") and x["destaque"] not in desc:
                erros.append(f"parte {i}: destaque '{x['destaque']}' não está na desc")
            if len(x["fala"]) > 270:
                erros.append(f"parte {i}: fala com {len(x['fala'])} caracteres (máx. 270 por projeto)")
            num = x.get("numero")
            if num and CENA.n(num) not in CENA.n(legenda(f, x["fala"])):
                erros.append(f"parte {i}: numero '{num}' não aparece na legenda da fala (use 'trocas' para o algarismo)")
            if x.get("repo") in rp and num and " " in str(num).strip():
                erros.append(f"parte {i}: numero '{num}' tem de ser UMA palavra da legenda (ex.: '2.371')")
    tot = fala_total(f) if P else ""
    if not 1300 <= len(tot) <= 2500:
        erros.append(f"fala total com {len(tot)} caracteres (1.300–2.500 ≈ 1 min 30 a 2 min 30 com o cartão final)")
    g = f.get("gancho") or {}
    man = str(g.get("manchete") or "")
    if not man or len(man.split()) > 6 or man != man.upper():
        erros.append("gancho.manchete: até 6 palavras, em CAIXA ALTA")
    if not g.get("destaque") or str(g.get("destaque")) not in man:
        erros.append("gancho.destaque tem de ser UMA palavra da manchete")
    if not g.get("objeto"):
        erros.append("gancho.objeto (objeto-metáfora com dano/ameaça no centro da capa)")
    if P and CENA.n(man) and CENA.n(man) in CENA.n(legenda(f, P[0]["fala"])):
        erros.append("a manchete não pode ser igual a um pedaço da fala (a tela grita mais que a voz)")
    if re.match(r"^\W*(os|as|top)?\s*(dez|10)\b", man, re.I) or re.match(r"^\W*(voc[eê] sabia|eu fiz)", P[0]["fala"] if P else "", re.I):
        erros.append("gancho de lista ('10 projetos…'), 'você sabia' ou 'eu fiz' é proibido: abra com o fato mais forte (número do #1, o projeto mais estranho)")
    if not (f.get("abertura") or {}).get("cena"):
        erros.append("abertura.cena")
    if P and ("inema ponto club" not in P[-1]["fala"]):
        erros.append("parte 13 precisa de 'inema ponto club'")
    for i, x in enumerate(P, 1):
        if re.search(r"\d", x.get("fala", "")):
            erros.append(f"parte {i}: algarismo na fala (o avatar lê errado): escreva por extenso e use 'trocas'")
        if PROIBIDO.search(x.get("fala", "")):
            erros.append(f"parte {i}: palavra proibida ({PROIBIDO.search(x['fala']).group(0)}): use 'você'; CTA só inema.club; nunca 'morte'")
        if x.get("fala", "").rstrip(".!?… ").split()[-1:] and re.fullmatch(r"(mil|cem|cento|\w+entos?|dez|vinte|trinta|quarenta|cinquenta|sessenta|setenta|oitenta|noventa|um|dois|três|quatro|cinco|seis|sete|oito|nove)",
                                                                         x["fala"].rstrip(".!?… ").split()[-1], re.I):
            erros.append(f"parte {i}: fala termina num número solto (a trilha corta a última sílaba): ponha a unidade depois")
    pub = f.get("publicar") or {}
    if not pub.get("titulo") or len(pub["titulo"]) > 90:
        erros.append("publicar.titulo (até 90 caracteres, chamada forte, sem '#Shorts' — o gb.py põe)")
    if not pub.get("telegram"):
        erros.append("publicar.telegram (texto curto do post no INEMA.TOOLS)")
    cta = f.get("cta") or {}
    if not (cta.get("a") and cta.get("b")):
        erros.append("cta.a e cta.b (a caixa vermelha de pergunta do fecho)")
    if erros:
        falha("\n  - " + "\n  - ".join(erros))
    log(f"roteiro OK: {len(P)} partes, {len(tot)} caracteres")


# ------------------------------------------------------------------ ficha do motor (a partir da ficha curta + top10.json)
def ficha_motor(p, f, d):
    """completa a ficha que o motor (nucleo/cena.py) entende: telas, painéis com contador e gráfico, fonte, selo, cta"""
    modo = d["modo"]; rp = repos(d); data_br = dt.date.fromisoformat(d["dia"]).strftime("%d/%m/%Y")
    M = {"marca": "INEMA · BOMBANDO NO GITHUB", "selo": f"TOP 10 {PERIODO[modo]}",
         "fonte": f"<b>github.com/trending</b> · estrelas ganhas {PERIODO[modo].lower()} · {data_br}",
         "gancho": f["gancho"], "abertura": f["abertura"], "trocas": f.get("trocas") or {}, "cores": f.get("cores") or {},
         "cta": {**f["cta"], "de": f["cta"].get("de") or f["partes"][-1]["fala"].split()[0].strip(",.?!:;")}, "club": f.get("club") or "aprenda a usar IA de verdade", "partes": []}
    for i, x in enumerate(f["partes"]):
        q = {"fala": x["fala"]}
        if x["etapa"] == "panorama":
            q["tela"] = "prints/ranking.png"; q["selo_tela"] = "github.com/trending"
            q["painel"] = {"k": f"10 PROJETOS · {PERIODO[modo]}", "borda": "am",
                           "contador": {"ate": d["soma_periodo"], "unid": "ESTRELAS", **({"em": x["numero"]} if x.get("numero") else {})}}
        elif x["etapa"] == "repo":
            it = rp[x["repo"]]
            q["tela"] = f"prints/r{it['pos']}.png"
            pn = {"k": f"#{it['pos']} · {it['nome']}"[:46], "borda": "am" if it["pos"] > 3 else "red",
                  "contador": {"ate": it["estrelas_periodo"], "unid": UNID[modo], "cor": "#FACC15",
                               **({"em": x["numero"]} if x.get("numero") else {})}}
            cv, cr = it.get("curva"), it.get("crescimento") or {}
            if cv and len(cv["v"]) >= 3 and cv.get("tipo") != "total":
                pn["grafico"] = {"rotulos": cv["rotulos"], "series": [{"nome": f"estrelas por {cv['unidade']}", "cor": "#FACC15", "v": cv["v"]}],
                                 "dur": 1.6, "marcar": list(range(0, len(cv["v"]), max(1, len(cv["v"]) // 6)))}
            elif cv and len(cv["v"]) >= 3:
                pn["grafico"] = {"rotulos": cv["rotulos"], "series": [{"nome": "estrelas no total", "cor": "#FACC15", "v": cv["v"]}], "dur": 1.6}
            elif cr.get("antes"):
                pn["grafico"] = {"rotulos": [ANTES[modo], "AGORA"], "dur": 1.4,
                                 "series": [{"nome": "estrelas no total", "cor": "#FACC15", "v": [cr["antes"], cr["agora"]]}]}
                if cr.get("pct"):
                    pn["l"] = f"+{str(cr['pct']).replace('.', ',')}% em {'24 h' if modo == 'dia' else '7 dias' if modo == 'semana' else '30 dias'}"
            q["painel"] = pn
        elif x["etapa"] == "comentario":
            q["print"] = {"url": "https://inema.club", "selo": "inema.club"}
        M["partes"].append(q)
    if f.get("ritmo"):
        M["ritmo"] = f["ritmo"]
    else:   # a pausa (~0,75 s, silêncio) vem antes do #1: o suspense da contagem regressiva
        M["ritmo"] = {"pausa_antes": {"parte": 12, "de": f["partes"][11]["fala"].split()[0].strip(",.:;!?")}}
    return M


# ------------------------------------------------------------------ imagens
def cmd_imagens(pasta):
    p, f, d = ler(pasta)
    capa, prints = p / "capa", p / "prints"; capa.mkdir(exist_ok=True); prints.mkdir(exist_ok=True)
    pecas.preto(capa / "preto.png")
    rp = repos(d); modo = d["modo"]; data_br = dt.date.fromisoformat(d["dia"]).strftime("%d/%m/%Y")
    tarefas = []
    with cf.ThreadPoolExecutor(4) as ex:
        tarefas.append(ex.submit(cartao.cartao_ranking, d["top10"], modo, data_br, prints / "ranking.png"))
        for x in f["partes"]:
            if x.get("etapa") == "repo":
                it = rp[x["repo"]]
                tarefas.append(ex.submit(cartao.cartao_repo, it, modo, x["desc"], prints / f"r{it['pos']}.png", x.get("destaque")))
        raw = prints / "raw-p13.png"
        if not raw.exists():
            tarefas.append(ex.submit(pecas.screenshot, "https://inema.club", raw))
        for t in tarefas:
            t.result()
    pecas.print_card(prints / "raw-p13.png", prints / "p13-c.png")
    g, a = f["gancho"], f["abertura"]
    if not (capa / "abertura.png").exists():
        pedido = (f"Gere 1 imagem com a ferramenta de geração de imagem (image_gen) e salve nesta pasta como abertura.png, em PNG, "
                  f"formato RETRATO 9:16 (o maior tamanho vertical disponível). {ESTILO}\n\n"
                  f"abertura.png — capa de impacto (é a capa do vídeo: tem de funcionar parada, num relance): {a['cena']}. "
                  f"No centro da cena, grande e nítido, o objeto-metáfora: {g['objeto']}. "
                  f"Manchete ESCRITA DENTRO da arte, em CAIXA ALTA, português, fonte bold sem serifa bem grossa, enorme, em 1 a 3 linhas: "
                  f"\"{g['manchete']}\" — tudo em branco, MENOS a palavra \"{g['destaque']}\", em amarelo #FACC15. "
                  "A manchete fica na METADE DE CIMA, entre 8% e 46% da altura, com margem de 7% nas laterais (nada encosta na borda); "
                  "a metade de baixo sem texto (ali entra o rosto). Contraste alto: letra legível em tamanho de miniatura. "
                  "Confira a grafia exata, com acentos; nenhuma outra palavra na imagem.\n\nNão mexa em nenhum outro arquivo. "
                  "Ao final, liste o arquivo salvo.\n")
        (capa / "pedido.txt").write_text(pedido)
        log("Codex: capa…")
        for tent in (1, 2):
            with open(capa / "codex.log", "w") as lg:
                subprocess.run(["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox"], input=pedido,
                               text=True, cwd=capa, stdout=lg, stderr=subprocess.STDOUT, timeout=1800)
            if (capa / "abertura.png").exists():
                break
        if not (capa / "abertura.png").exists():
            falha("o Codex não gerou capa/abertura.png (capa/codex.log)")
    pecas.vertical(capa / "abertura.png")
    pecas.abertura(capa / "abertura.png")
    log("imagens OK (capa, ranking, 10 cartões, print do inema.club)")


# ------------------------------------------------------------------ avatar (estúdio HeyGen, assinatura)
def avatar_enviar(p, f):
    av = p / "avatar"; av.mkdir(exist_ok=True)
    if (av / "avatar.mp4").exists() or (av / "video_id.txt").exists():
        return
    if not (av / "APROVADO_HEYGEN").exists():
        falha("falta avatar/APROVADO_HEYGEN")
    (av / "fala.txt").write_text(fala_total(f) + "\n")
    with open(av / "studio.log", "w") as lg:
        subprocess.run(["node", "heygen-studio.mjs", "--titulo", f"GBX-{p.name}", "--fala-arquivo", av / "fala.txt",
                        "--perfil", PERFIL, "--template", TEMPLATE_HEYGEN], cwd=HEYGEN_DIR, env=dict(os.environ, DISPLAY=TELA),
                       stdout=lg, stderr=subprocess.STDOUT, timeout=12000)
    s = (av / "studio.log").read_text()
    if "ERRO:" in s:
        falha("estúdio: " + s[s.index("ERRO:"):][:200])
    m = re.search(r"create-v4/([0-9a-f]{32})", s)
    if not m:
        falha("estúdio não devolveu o id (avatar/studio.log)")
    (av / "video_id.txt").write_text(m.group(1))
    log("avatar enviado ao estúdio:", m.group(1))


def avatar_esperar(p, minutos=300):
    av = p / "avatar"
    if (av / "avatar.mp4").exists():
        return
    r = subprocess.run(["node", "heygen-estudio-baixar.mjs", "--id", (av / "video_id.txt").read_text().strip(), "--saida", av / "avatar.mp4",
                        "--minutos", str(minutos), "--intervalo", "60"], cwd=HEYGEN_DIR, capture_output=True, text=True,
                       timeout=minutos * 60 + 1200)
    if r.returncode:
        falha("avatar no HeyGen: " + (r.stdout + r.stderr)[-300:])


def cmd_avatar(pasta):
    p, f, d = ler(pasta)
    falas(p, f)
    avatar_enviar(p, f)
    avatar_esperar(p)
    dd, sem = RT.retempo(p)
    log(f"avatar {dd:.1f} s · fala × roteiro {sem:.0%}")
    if sem < 0.88:
        falha(f"o avatar não fala o roteiro ({sem:.0%} < 88%)")


# ------------------------------------------------------------------ cena, render, revisão
def cmd_cena(pasta):
    p, f, d = ler(pasta)
    M = ficha_motor(p, f, d)
    (p / "ficha-motor.json").write_text(json.dumps(M, ensure_ascii=False, indent=1))
    fl = falas(p, f)
    for i, x in enumerate(M["partes"]):   # o motor lê a legenda desta lista
        fl[i]["legenda"] = legenda(M, x["fala"].strip())
    t = p / "avatar/tempos.json"
    if not t.exists() or t.stat().st_mtime < (p / "avatar/avatar.mp4").stat().st_mtime:
        dd, sem = RT.retempo(p); log(f"retempo {dd:.1f} s · {sem:.0%}")
    r = RITMO.aplicar(p, M)
    if r:
        log(f"ritmo: {r['wpm_heygen']:.0f} → {r['wpm']:.0f} palavras/min · {r['duracao']:.1f} s")
    # o comentário da parte 13 usa o print do inema.club (prints/p13-c.png), como no r7ex
    dur, nt, npn, nl = CENA.montar(p, M, fl)
    log(f"cena.js ok: {dur} s · {nt} telas · {npn} painéis · {nl} blocos de legenda")


def cmd_render(pasta):
    p, f, d = ler(pasta)
    env = dict(os.environ, DISPLAY=TELA, GEO="geo-br.js", LAYOUT="canto", MUSICA=str(R / "assets/trilha.mp3"), R7X_RENDER_TIMEOUT="3000")
    with open(p / "build-render.log", "w") as lg:
        r = subprocess.run(["bash", R / "motor/compor_avatar.sh", p, p / "video.mp4"], cwd=R, env=env, stdout=lg, stderr=subprocess.STDOUT,
                           timeout=4000)
    if r.returncode:
        txt = (p / "build-render.log").read_text()
        chave = [l.strip() for l in txt.splitlines() if re.search(r"Error|Timeout|exceeded|failed", l)]
        falha("render: " + (" | ".join(chave[:2]) if chave else txt[-400:]))
    dd = duracao(p / "video.mp4")
    log(f"vídeo {p / 'video.mp4'} · {dd:.1f} s")
    if dd >= 178:
        falha(f"{dd:.0f} s: reel não pode chegar a 3 min")


def duracao(v):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v]))


def cmd_folha(pasta):
    p = Path(pasta).resolve(); v = p / "video.mp4"; b = p / "build"; b.mkdir(exist_ok=True)
    dd = duracao(v)
    ts = [0.05, 1.2, 2.2] + [round(4 + (dd - 5) * i / 14, 2) for i in range(15)]
    qs = []
    for k, t in enumerate(ts):
        q = b / f"q{k:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", v, "-frames:v", "1", "-vf",
                        f"scale=300:-1,drawtext=text='{t}':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6", q], check=True)
        qs.append(q)
    lay = "|".join(f"{(i % 6) * 300}_{(i // 6) * 533}" for i in range(18))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", q] for q in qs), []), "-filter_complex", f"xstack=inputs=18:layout={lay}",
                    b / "folha.jpg"], check=True)
    log("folha", b / "folha.jpg")


def cmd_revisar(pasta):
    p = Path(pasta).resolve()
    cmd_folha(p)
    try:
        r = subprocess.run(["claude", "-p", "--output-format", "json", "--allowedTools", "Read", "--", (R / "auto/revisor.md").read_text()],
                           cwd=p, capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL,
                           env={k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"})
        res = json.loads(r.stdout)["result"].strip()
        v = json.loads(res[res.index("{"): res.rindex("}") + 1])
        assert v.get("veredito") in ("aprovado", "reprovado")
    except Exception as e:  # noqa: BLE001
        v = {"veredito": "erro", "motivo": f"revisor não respondeu direito: {str(e)[:200]}"}
    (p / "revisao.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    log("revisor:", json.dumps(v, ensure_ascii=False))
    return v


def cmd_fazer(pasta):
    cmd_checar(pasta)
    with cf.ThreadPoolExecutor(2) as ex:
        a = ex.submit(cmd_imagens, pasta); b = ex.submit(cmd_avatar, pasta)
        a.result(); b.result()
    cmd_cena(pasta); cmd_render(pasta)
    return cmd_revisar(pasta)


# ------------------------------------------------------------------ publicação
def cmd_publicar(pasta):
    p, f, d = ler(pasta)
    v = p / "video.mp4"; pub = f["publicar"]; modo = d["modo"]
    data_br = dt.date.fromisoformat(d["dia"]).strftime("%d/%m/%Y")
    url = ""
    if not os.environ.get("SEM_YT"):
        tit = pub["titulo"][:88] + " #Shorts"
        ctx = (f"Short '{NOME[modo]}' do GitHub ({data_br}) do INEMA com Nei Maldaner: os 10 projetos que mais ganharam estrelas "
               f"{PERIODO[modo].lower()} no GitHub Trending, do #10 ao #1. {pub.get('contexto', '')} Fonte: github.com/trending. "
               "Links dos 10 projetos na descrição. Curso gratuito em https://inema.club.")
        links = "\n".join(f"#{x['pos']} {x['nome']} — https://github.com/{x['nome']}" for x in sorted(d["top10"], key=lambda x: x["pos"]))
        (p / "yt.txt").write_text(pub["titulo"] + "\n\n" + links + "\n")
        with open(p / "publicar.log", "w") as lg:
            subprocess.run([str(Path.home() / "projetos/yt-pubx/yt-pubx"), "publicar", v, "--canal", CANAL, "--title", tit,
                            "--contexto", ctx, "--contexto-arquivo", p / "yt.txt"], stdout=lg, stderr=subprocess.STDOUT, timeout=2400)
        m = re.findall(r"watch\?v=([A-Za-z0-9_-]{6,})", (p / "publicar.log").read_text())
        if m:
            url = f"https://www.youtube.com/shorts/{m[-1]}"
            (p / f"youtube-{CANAL}.txt").write_text(m[-1] + "\n")
    st = f"publicado no {CANAL}: {url}" if url else ("(sem YouTube nesta rodada)" if os.environ.get("SEM_YT") else
                                                    f"⚠ NÃO publicou no {CANAL} (ver publicar.log)")
    rev = json.loads((p / "revisao.json").read_text()) if (p / "revisao.json").exists() else {}
    sug = rev.get("sugestoes") or []
    leg = (f"Bombando no GitHub · {NOME[modo]} · {data_br} · {duracao(v):.0f}s\n{st}\n" +
           (("🟥 SUGESTÃO: " + " | ".join(sug)[:500] + "\n") if sug else "") + pub["titulo"])
    if not os.environ.get("SEM_BOT"):
        Path(str(v) + ".envio-v3.json").unlink(missing_ok=True)
        subprocess.run(["node", R / "bin/enviar_bot_v3.mjs", v, leg], timeout=900)
    if not os.environ.get("SEM_TG"):
        telegram(p, f, d, url)
    log(st)
    return url


def telegram(p, f, d, url):
    """posta o vídeo e o resumo no tópico fixo do INEMA.TOOLS (cria o tópico na primeira vez e guarda o id)"""
    tg = Path.home() / "projetos/telegramtopicosindex"
    arq_top = R / "auto/telegram-topico.txt"
    modo = d["modo"]; data_br = dt.date.fromisoformat(d["dia"]).strftime("%d/%m/%Y")
    v = p / "video.mp4"; thumb = p / "video.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", v, "-frames:v", "1", "-vf", "scale=320:-1", thumb], check=False)
    rp = repos(d)
    linhas = [f"🔥 **{NOME[modo]} · {data_br}**", "", f["publicar"]["telegram"].strip(), "", "[[img:" + str(v) + "]]", "---",
              "🏆 **Os 10 que mais ganharam estrelas**"]
    for x in sorted(d["top10"], key=lambda x: x["pos"]):
        desc = next((q.get("desc") for q in f["partes"] if q.get("repo") == x["nome"]), "") or ""
        linhas.append(f"{x['pos']}. **{x['nome']}** · +{br(x['estrelas_periodo'])} ⭐ — {desc}\n   https://github.com/{x['nome']}")
    if url:
        linhas += ["", f"▶️ No YouTube: {url}"]
    linhas += ["", "Qual desses você vai testar primeiro? 👇"]
    md = p / "telegram.md"; md.write_text("\n".join(linhas) + "\n")
    cmd = [str(tg / "venv/bin/python"), "postar_topico.py", "--grupo", "INEMA.TOOLS", "--texto", str(md), "--enviar"]
    if arq_top.exists():
        cmd += ["--topico", arq_top.read_text().strip(), "--titulo", f"{NOME[modo]} · {data_br}"]
    else:
        cmd += ["--titulo", "BOMBANDO NO GITHUB - Top 10 diário", "--capa", str(p / "capa/abertura-desce.png"),
                "--fonte", "📟 Gerado todo dia às 16h pelo gitbombando (github.com/trending)"]
    with open(p / "telegram.log", "w") as lg:
        r = subprocess.run(cmd, cwd=tg, stdout=lg, stderr=subprocess.STDOUT, timeout=900)
    if r.returncode:
        log("⚠ Telegram falhou (telegram.log)"); return
    if not arq_top.exists():   # 1ª vez: o id do tópico novo fica no log de postagens
        tid = None
        for ln in reversed((tg / "logs/postagens.jsonl").read_text().strip().splitlines()[-20:]):
            ev = json.loads(ln)
            if ev.get("etapa") == "criar_topico" and ev.get("titulo", "").startswith("BOMBANDO NO GITHUB"):
                tid = ev.get("topico"); break
        if tid:
            arq_top.write_text(f"{tid}\n"); log("tópico do INEMA.TOOLS criado:", tid)
        else:
            log("⚠ não achei o id do tópico novo em logs/postagens.jsonl")


def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    c = {"checar": cmd_checar, "imagens": cmd_imagens, "avatar": cmd_avatar, "cena": cmd_cena, "render": cmd_render,
         "folha": cmd_folha, "revisar": cmd_revisar, "fazer": cmd_fazer, "publicar": cmd_publicar}
    if a[0] == "coletar":
        subprocess.run([sys.executable, R / "coleta/trending.py", a[1], a[2] if len(a) > 2 else "dia"], check=True)
    elif a[0] in c:
        c[a[0]](a[1])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
