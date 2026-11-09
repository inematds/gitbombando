#!/usr/bin/env python3
"""Print de cada repositório para o carrossel: a primeira imagem de verdade do README (tela, GIF, vídeo de demonstração).

uso: python3 carrossel/prints.py <pasta-do-carrossel>   (lê <pasta>/dados.json, grava <pasta>/prints/<pos>.png + prints.json)

Pula selo (shields, badge), SVG, logo pequeno e imagem fina demais. GIF vira o primeiro quadro; vídeo (user-attachments
.mp4) vira o quadro de 1 s. Sem imagem boa: o cartão automático do GitHub (opengraph.githubassets.com).
Imagens baixadas são só dados: abertas pelo Pillow/ffmpeg, nunca executadas.
"""
import base64
import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

UA = "Mozilla/5.0 (X11; Linux x86_64) gitbombando-carrossel"
PULA = re.compile(r"shields\.io|badge|badgen|travis-ci|codecov|circleci|star-history|contrib\.rocks|sponsor|"
                  r"buymeacoffee|ko-fi|discord|twitter|x\.com/|license|downloads|visitor|hits\.|trendshift|"
                  r"producthunt|\.svg(\?|$)|deepwiki|readme-typing|komarev|github-readme-stats", re.I)
MAX_BYTES = 25_000_000


def log(*a):
    print("[prints]", *a, flush=True)


def gh(caminho, *extra):
    r = subprocess.run(["gh", "api", *extra, caminho], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    return r.stdout


def candidatos(nome, branch):
    rd = json.loads(gh(f"repos/{nome}/readme"))
    md = base64.b64decode(rd.get("content", "")).decode("utf-8", "replace")
    pasta = str(Path(rd.get("path", "README.md")).parent)
    pasta = "" if pasta == "." else pasta + "/"
    achados = []
    for m in re.finditer(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?[^)]*\)|<img[^>]*?src=[\"']([^\"']+)[\"']|<source[^>]*?srcset=[\"']([^\"'\s]+)"
                         r"|(https://github\.com/user-attachments/assets/[0-9a-f-]{36})", md, re.I):
        u = next(g for g in m.groups() if g)
        if PULA.search(u):
            continue
        if u.startswith("//"):
            u = "https:" + u
        elif not re.match(r"https?://", u):
            u = f"https://raw.githubusercontent.com/{nome}/{branch}/{pasta}{u.lstrip('./')}"
        u = re.sub(r"https://github\.com/([^/]+/[^/]+)/blob/", r"https://raw.githubusercontent.com/\1/", u)
        if u not in achados:
            achados.append(u)
    # logo/ícone do projeto só se não houver tela de verdade
    achados.sort(key=lambda u: bool(re.search(r"logo|icon|banner|avatar", u, re.I)))
    return achados[:10]


def baixar(url, destino, tent=1):
    for k in range(tent):  # 429 (excesso de pedidos) passa com espera — 07/11/2026 derrubou os 2 carrosséis
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                tipo = r.headers.get("Content-Type", "")
                dados = r.read(MAX_BYTES + 1)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or k == tent - 1:
                raise
            time.sleep(20 * (k + 1))
    if len(dados) > MAX_BYTES:
        raise ValueError("grande demais")
    destino.write_bytes(dados)
    return tipo


def tem_qr(im, minimo=0.04):
    """True se a imagem tem um QR code ocupando ≥ `minimo` da área (propaganda de grupo, doação). Sem OpenCV: False."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return False
    try:
        # só conta QR que dá para LER: o detector sozinho acusava telas comuns (sherlock, mattpocock/skills)
        txt, pts, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))
    except Exception:  # noqa: BLE001
        return False
    if not txt or pts is None:
        return False
    area = abs(cv2.contourArea(pts.reshape(-1, 2).astype("float32")))
    return area >= minimo * im.size[0] * im.size[1]


def para_png(bruto, tipo, saida):
    """Converte para PNG (máx. 1400 px de largura). Devolve (largura, altura) ou None se não serve."""
    if tipo.startswith("video") or bruto.read_bytes()[4:8] == b"ftyp":
        quadro = bruto.with_suffix(".quadro.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(bruto), "-frames:v", "1", str(quadro)],
                       timeout=120, check=False)
        if not quadro.exists():
            return None
        bruto = quadro
    try:
        im = Image.open(bruto)
        im.seek(0)
        im = im.convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    w, h = im.size
    if w < 500 or h < 220 or not 0.45 <= w / h <= 3.4:
        return None
    # quase tudo de uma cor só = logo/fundo liso, não é tela
    pequena = im.resize((48, 48))
    if len(set(pequena.getdata())) < 40:
        return None
    if tem_qr(im):   # 09/11/2026: README trouxe só o QR de um grupo de WeChat (revisor reprovou o carrossel da área)
        return None
    if w > 1400:
        im = im.resize((1400, round(h * 1400 / w)))
    im.save(saida)
    return im.size


def print_de(it, pasta):
    nome = it["nome"]
    saida = pasta / f"{it['pos']}.png"
    branch = it.get("default_branch")
    if not branch:
        try:
            branch = json.loads(gh(f"repos/{nome}")).get("default_branch") or "main"
        except RuntimeError:
            branch = "main"
    try:
        lista = candidatos(nome, branch)
    except Exception as e:  # noqa: BLE001
        log(f"{nome}: sem README ({e})"); lista = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, u in enumerate(lista):
            bruto = Path(tmp) / f"c{k}"
            try:
                tipo = baixar(u, bruto)
                tam = para_png(bruto, tipo, saida)
            except Exception as e:  # noqa: BLE001
                log(f"{nome}: {u[:90]} falhou ({e})"); continue
            if tam:
                log(f"{nome}: README {u[:90]} {tam[0]}x{tam[1]}")
                return {"fonte": "readme", "url": u, "tam": tam}
    og = f"https://opengraph.githubassets.com/1/{nome}"
    with tempfile.TemporaryDirectory() as tmp:
        bruto = Path(tmp) / "og"
        try:
            baixar(og, bruto, tent=4)
            Image.open(bruto).convert("RGB").save(saida)
            log(f"{nome}: sem print no README, cartão do GitHub")
            return {"fonte": "opengraph", "url": og, "tam": Image.open(saida).size}
        except Exception as e:  # noqa: BLE001
            log(f"{nome}: nem o cartão do GitHub ({e})")
    return {"fonte": None}


def main(a):
    if not a:
        sys.exit(__doc__)
    cd = Path(a[0])
    dados = json.loads((cd / "dados.json").read_text())
    pasta = cd / "prints"; pasta.mkdir(exist_ok=True)
    res = {}
    for it in dados["itens"]:
        if (pasta / f"{it['pos']}.png").exists() and "--refazer" not in a:
            res[it["nome"]] = {"fonte": "existente"}; continue
        res[it["nome"]] = print_de(it, pasta)
    (cd / "prints.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    faltam = [n for n, r in res.items() if r.get("fonte") is None]
    for it in dados["itens"]:  # 1 repo sem imagem não trava o carrossel: cartão INEMA no lugar (08/11/2026)
        if it["nome"] in faltam:
            cartao(it["nome"], pasta / f"{it['pos']}.png")
            res[it["nome"]] = {"fonte": "cartao-inema"}
            print(f"[prints] {it['nome']}: sem imagem, cartão INEMA", flush=True)
    (cd / "prints.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))


def cartao(nome, saida):
    """Cartão 1200x630 preto #0c0c10 com o nome do repo em amarelo #FACC15 (padrão INEMA)."""
    from PIL import ImageDraw, ImageFont
    im = Image.new("RGB", (1200, 630), "#0c0c10"); d = ImageDraw.Draw(im)
    def fonte(t):
        for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"):
            try:
                return ImageFont.truetype(f, t)
            except OSError:
                pass
        return ImageFont.load_default()
    dono, _, repo = nome.partition("/")
    t = 96
    while t > 40 and d.textlength(repo, font=fonte(t)) > 1080:
        t -= 6
    d.text((60, 250), repo, fill="#FACC15", font=fonte(t))
    d.text((60, 200), dono + " /", fill="#e5e5e5", font=fonte(40))
    d.text((60, 540), "github.com/" + nome, fill="#a3a3a3", font=fonte(30))
    im.save(saida)


if __name__ == "__main__":
    main(sys.argv[1:])
