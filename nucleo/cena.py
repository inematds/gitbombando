"""ficha.yaml + avatar/tempos.json → cena.js do motor do eventosextremospub (mapa.html).
Mesma lógica do gerar_cena.py da edição modelo eventosextremospub/edicoes/2026-10-18-do-chat-ao-agente."""
import difflib, json, re, unicodedata
from pathlib import Path

BORDA = {"red": "rgba(255,42,31,.7)", "am": "rgba(250,204,21,.75)", "vd": "rgba(34,197,94,.7)"}
NUM = re.compile(r"\d")
MAX_LEG = 21                          # letras por bloco de legenda (23 já encosta na borda; 25 vazou)


def n(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode())


def _roteiro(t, texto):
    """troca as palavras ouvidas pelas da legenda, mantendo os tempos"""
    tok, W = texto.split(), t["palavras"]
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [n(x) for x in tok], [n(p["w"]) for p in W], autojunk=False).get_opcodes():
        if op == "equal":
            out += [{"w": tok[i1 + k], "t": W[j1 + k]["t"], "f": W[j1 + k]["f"]} for k in range(i2 - i1)]
        elif i2 > i1:
            a = W[j1]["t"] if j2 > j1 else (W[j1 - 1]["f"] if j1 else t["ini"])
            b = W[j2 - 1]["f"] if j2 > j1 else (W[j1]["t"] if j1 < len(W) else a + .3)
            d = (b - a) / (i2 - i1)
            out += [{"w": tok[i1 + k], "t": round(a + k * d, 3), "f": round(a + (k + 1) * d, 3)} for k in range(i2 - i1)]
    return out


def acha(palavras, palavra, k=1):
    achou = 0
    for p in palavras:
        if n(palavra) == n(p["w"]) or (len(n(palavra)) > 3 and n(palavra) in n(p["w"])):
            achou += 1
            if achou == k:
                return p["t"]
    return None


def sem_markdown(x):
    """tira o **negrito** de markdown dos textos da tela: a tela não lê markdown e os asteriscos apareciam crus
    (bigtech-ipo/troco, 20/10/2026)"""
    if isinstance(x, str):
        return x.replace("**", "")
    if isinstance(x, list):
        return [sem_markdown(v) for v in x]
    if isinstance(x, dict):
        return {k: sem_markdown(v) for k, v in x.items()}
    return x


def comentario(cta):
    """o texto que aparece sendo digitado no campo de comentário: cta.comentario, ou a palavra em CAIXA ALTA do cta.b
    ("comenta EU VOU COORDENAR ou…" → "EU VOU COORDENAR"), ou um pedido do link"""
    if cta.get("comentario"):
        return str(cta["comentario"])
    m = re.search(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9]{2,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9]{1,})*", sem_markdown(str(cta.get("b", ""))))
    return m.group(0) if m else "quero o link 🙋"


def montar(pasta, ficha, falas):
    pasta = Path(pasta)
    T = json.loads((pasta / "avatar/tempos.json").read_text())
    leg = {f["id"]: f["legenda"] for f in falas}
    for t in T:
        t["palavras"] = _roteiro(t, leg[t["id"]])
    F = {t["id"]: t for t in T}
    ids = [t["id"] for t in T]

    def em(fid, palavra, k=1):
        v = acha(F[fid]["palavras"], palavra, k)
        if v is None:
            raise SystemExit(f"{fid}: '{palavra}' não está na fala: " + " ".join(p["w"] for p in F[fid]["palavras"]))
        return v

    # com o ritmo (28/10/2026) o avatar já traz os 9 s de cartão depois da última palavra: o vídeo acaba junto com ele.
    # Sem ritmo, o antigo: 1,4 s depois do fim da fala.
    ritmo = json.loads((pasta / "avatar/ritmo.json").read_text()) if (pasta / "avatar/ritmo.json").exists() else None
    DUR = round(F[ids[-1]]["fim"] + (.1 if ritmo else 1.4), 2)
    BR = {"lon": -52.0, "lat": -14.0, "zoom": 3.4}       # mapa escondido atrás do fundo preto (o motor exige câmera)
    camera = [{"t": 0, **BR, "pitch": 30, "bearing": 0}, {"t": DUR, **BR, "pitch": 40, "bearing": 20}]

    telas = [{"src": "capa/preto.png", "ini": -1.0, "fim": DUR + 1, "fade": 0, "zoom": 0}]
    partes = ficha["partes"]
    for i, p in enumerate(partes):
        fid = f"f{i + 1}"
        a = -1.0 if i == 0 else F[fid]["ini"] - .1
        # a tela fica até a próxima terminar de entrar (fade .3): sem mergulho no preto na troca (quadro 5,0 s preto, 20/10/2026)
        b = F[f"f{i + 2}"]["ini"] + .3 if i + 1 < len(partes) else DUR + 1
        if i == 0:
            src, selo, zoom = "capa/abertura-desce.png", None, .03
        elif p.get("tela"):                              # gitbombando: cartão próprio (repo, ranking) já pronto em 1080x1920
            src, selo, zoom = p["tela"], p.get("selo_tela"), .03
        elif p.get("print"):
            src, selo, zoom = f"prints/p{i + 1}-c.png", p["print"].get("selo") or "print da página", .04
        elif p.get("logos"):                             # D13: produto citado = cartão com o logo real (20/10/2026)
            src, selo, zoom = f"capa/p{i + 1}.png", None, .05
        elif p.get("diagrama"):                          # diagrama animado (19/10/2026): fundo limpo, o motor desenha por cima
            src, selo, zoom = "capa/preto.png", None, 0
        else:
            src, selo, zoom = f"capa/p{i + 1}.png", "ilustração", .07
        lgs = p.get("logos") or []
        if i > 0 and len(lgs) > 1 and all(x.get("de") for x in lgs):   # uma tela por produto, troca na palavra (20/10/2026)
            ts = [a] + [em(fid, x["de"]) - .25 for x in lgs[1:]]
            for k in range(len(lgs)):
                fk = ts[k + 1] + .3 if k + 1 < len(lgs) else b
                telas.append({"src": f"capa/p{i + 1}-{k + 1}.png", "ini": ts[k], "fim": fk, "fade": .25, "zoom": .05})
            continue
        if i == 0 and ficha.get("gancho") and b > 2.6:
            # v1.2.0 (28/10/2026): troca de quadro a cada ~1 s até os 3 s — capa (0 s) → corte de aproximação (1 s) → outro (2 s),
            # a manchete sempre na tela. Corte seco de enquadramento, não pulso de brilho (que não conta como troca, video/style.md).
            from . import pecas
            desce = pasta / "capa/abertura-desce.png"
            if desce.exists() and not (pasta / "capa/abertura-desce-2.png").exists():
                pecas.batidas(desce)
            cortes = [-1.0, 1.0, 2.0]
            for k, src_k in enumerate([src, "capa/abertura-desce-1.png", "capa/abertura-desce-2.png"]):
                fk = cortes[k + 1] + .1 if k < 2 else b
                telas.append({"src": src_k, "ini": cortes[k], "fim": fk, "fade": .08, "zoom": .02 if k < 2 else .03,
                              "escurece": "base"})
            continue
        d = {"src": src, "ini": a, "fim": b, "fade": .3, "zoom": zoom}
        # escurece a foto por baixo da legenda/painel/avatar (a vinheta do motor fica ABAIXO das telas; 19/10/2026)
        if i == 0:
            d["escurece"] = "base"                        # abertura: só a faixa de baixo (o título do topo fica intacto)
        elif selo == "ilustração":
            d["escurece"] = "foto"                        # ilustração: faixa de baixo + brilho/saturação menores
        if selo:
            d["selo"] = selo
        telas.append(d)

    # D14 (Nei, 20/10/2026): embaixo só UMA coisa (título, número ou logo); a lista sobe para cima da imagem.
    # Ficha antiga com painel.itens: os itens viram a lista do alto (rótulo = painel.k).
    paineis, listas = [], []
    for i, p in enumerate(partes):
        pn = p.get("painel") or {}
        ls = p.get("lista") or ({"k": pn.get("k"), "itens": pn["itens"], "borda": pn.get("borda")} if pn.get("itens") else None)
        fid = f"f{i + 1}"
        fim = (F[f"f{i + 2}"]["ini"] if i + 1 < len(partes) else DUR) - .05
        if ls and ls.get("itens"):
            it = [{"t": em(fid, x[0], x[2] if len(x) > 2 else 1), "txt": x[1]} for x in ls["itens"]]
            listas.append({"ini": min(x["t"] for x in it) - .3, "fim": fim, "k": ls.get("k") or "", "itens": it,
                           **({"borda": BORDA[ls["borda"]]} if ls.get("borda") else {})})
        if not (pn.get("contador") or pn.get("titulo") or pn.get("logo") or pn.get("grafico") or pn.get("ranking")):
            continue
        a = em(fid, pn["de"]) - .1 if pn.get("de") else F[fid]["ini"]
        d = {"ini": a, "fim": fim, "k": pn.get("k", ""), "borda": BORDA[pn.get("borda", "am")]}
        if pn.get("titulo"):
            d["titulo"] = pn["titulo"]
            if pn.get("cor"):
                d["cor"] = pn["cor"]
        if pn.get("logo"):
            d["logo"] = f"capa/logo-{pn['logo']}.png"
        if pn.get("grafico"):                            # gitbombando: barras do motor (sobem com prog a partir de 'ini')
            g = dict(pn["grafico"]); g["ini"] = (em(fid, g.pop("em")) - .3) if g.get("em") else a + .6
            d["grafico"] = g
        if pn.get("ranking"):
            r = dict(pn["ranking"]); r["ini"] = (em(fid, r.pop("em")) - .3) if r.get("em") else a + .4
            d["ranking"] = r
        if pn.get("contador"):
            c = pn["contador"]
            ci = em(fid, c["em"]) - 1.0 if c.get("em") else a + .3
            d["contador"] = {"de": c.get("de", 0), "ate": c["ate"], "dec": c.get("dec", 0), "ini": ci,
                             "dur": c.get("dur", 1.2), "cor": c.get("cor", "#FACC15"), "unid": c.get("unid", "")}
        if pn.get("l"):
            d["l"] = pn["l"]
        paineis.append(d)

    # diagramas (19/10/2026, pedido do Nei: "não só imagem, animações e diagramas"): fluxo | hub | terminal,
    # cada nó/linha acende na palavra falada (de)
    diagramas = []
    for i, p in enumerate(partes):
        dg = p.get("diagrama")
        if not dg:
            continue
        fid = f"f{i + 1}"
        a = F[fid]["ini"] - .1
        b = (F[f"f{i + 2}"]["ini"] if i + 1 < len(partes) else DUR) - .1
        d = {"ini": a, "fim": b, "forma": dg.get("forma", "fluxo"), "titulo": dg.get("titulo", "")}
        itens = dg.get("nos") or dg.get("linhas") or []
        d["nos"] = [{**{k: v for k, v in x.items() if k not in ("de", "k", "logo")}, "t": em(fid, x["de"], x.get("k", 1)) - .05 if x.get("de") else a + .2}
                    for x in itens]
        for no, x in zip(d["nos"], itens):   # D13 no diagrama (28/10/2026): nó com `logo:` mostra o logo real no lugar do emoji
            if x.get("logo"):
                no["ic"] = f'<img src="capa/logo-{x["logo"]}.png" style="max-height:64px;max-width:64px;object-fit:contain">'
        if dg.get("centro"):
            c = dg["centro"]
            d["centro"] = {**{k: v for k, v in c.items() if k != "de"}, "t": em(fid, c["de"]) - .05 if c.get("de") else a + .1}
        diagramas.append(d)

    ult = f"f{len(partes)}"
    cta = {"ini": em(ult, ficha["cta"].get("de", "pede")), "fim": DUR,   # cta.de: deixa da pergunta (padrão "pede")
           "a": ficha["cta"]["a"], "b": ficha["cta"]["b"]}
    fala_fim = F[ult]["palavras"][-1]["f"]
    if DUR - fala_fim >= 4:   # cartão segurado (28/10/2026): o gesto de comentar é encenado depois da última palavra
        cta.update(fala_fim=fala_fim, comentario=comentario(ficha["cta"]))
    club = {"ini": em(ult, "inema.club"), "fim": DUR, "a": "inema.club", "b": ficha["club"]}
    fontes = [{"ini": .3, "fim": DUR, "html": ficha["fonte"]}]

    cores = {n(k): v for k, v in (ficha.get("cores") or {}).items()}
    for k in ("inemaclub", "comentarios", "link"):
        cores.setdefault(k, "#FACC15")
    legenda = []
    for t in T:
        bloco = []; ant = None
        for i, p in enumerate(t["palavras"]):
            w = p["w"]; k = n(w)
            # bloco cabe na largura: até 3 palavras e até MAX_LEG letras ("BILLION CONTEXT ENXUGANDO" vazou, 19/10)
            if bloco and len(" ".join(b["w"] for b in bloco) + " " + w) > MAX_LEG:
                legenda.append({"ini": bloco[0]["t"] - .05, "fim": ant["f"] + .12, "palavras": bloco})
                bloco = []
            ant = p
            cor = cores.get(k) or ("#FACC15" if NUM.search(k) else None)
            bloco.append({"w": w, "t": p["t"], **({"cor": cor} if cor else {})})
            if len(bloco) == 3 or w[-1:] in ".?!,:" or i == len(t["palavras"]) - 1:
                legenda.append({"ini": bloco[0]["t"] - .05, "fim": p["f"] + .12, "palavras": bloco})
                bloco = []
    for a, b in zip(legenda, legenda[1:]):
        a["fim"] = min(max(a["fim"], b["ini"]), b["ini"])

    # avatar (Nei, 21/10/2026): abre em MEIA tela na metade de baixo (1080x960) durante a parte 1 (gancho) e depois
    # vai para o PiP do canto; a ficha pode pedir `avatar: meia` em outra parte (o plano decide). O compor lê meia.txt.
    meia = []
    for i, p in enumerate(partes):
        if i > 0 and p.get("avatar", "pip") != "meia":
            continue
        a = 0.0 if i == 0 else round(F[f"f{i + 1}"]["ini"] - .1, 2)
        b = round(F[f"f{i + 2}"]["ini"] - .1, 2) if i + 1 < len(partes) else DUR
        if meia and a - meia[-1][1] < .3:
            meia[-1][1] = b
        else:
            meia.append([a, b])
    (pasta / "avatar/meia.txt").write_text("".join(f"{a} {b}\n" for a, b in meia))

    C = {"layout": "canto", "padding_baixo": 640, "meia": meia, "duracao": DUR, "padding_topo": 0, "marca": ficha["marca"], "selo": ficha["selo"],
         "camera": camera, "telas": telas, "hero": [], "paineis": paineis, "listas": listas, "diagramas": diagramas, "cta": cta, "club": club, "fontes": fontes, "legenda": legenda}
    (pasta / "cena.js").write_text("window.CENA=" + json.dumps(sem_markdown(C), ensure_ascii=False) + ";")
    return DUR, len(telas), len(paineis), len(legenda)
