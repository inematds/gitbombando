"""Peças de imagem do r7ex: tamanho 9:16, abertura deslocada, print de página num cartão, screenshot."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W, H = 1080, 1920
AMAR = (250, 204, 21)
FUNDO = (12, 12, 16)
CHROME = sorted(Path.home().glob(".cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))


def vertical(p):
    """leva a imagem a 1080x1920 (o image_gen às vezes devolve 941x1672 ou 1024x1536)"""
    im = Image.open(p).convert("RGB")
    if im.size != (W, H):
        k = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        x, y = (im.width - W) // 2, (im.height - H) // 2
        im = im.crop((x, y, x + W, y + H))
        im.save(p)
    return Path(p)


def abertura(p, dy=110):
    """desce a abertura 110 px com degradê no alto: o título não bate na faixa do topo → abertura-desce.png"""
    im = Image.open(vertical(p)).convert("RGB")
    out = Image.new("RGB", (W, H), FUNDO); out.paste(im.crop((0, 0, W, H - dy)), (0, dy))
    g = Image.new("L", (W, dy + 60), 0); d = ImageDraw.Draw(g)
    for y in range(dy + 60):
        d.line((0, y, W, y), fill=int(255 * max(0, 1 - y / (dy + 60))))
    out.paste(FUNDO, (0, 0), g)
    dst = Path(p).with_name("abertura-desce.png"); out.save(dst); return dst


BATIDAS = (1.05, 1.10)   # v1.2.0: aproximações da capa em 1 s e 2 s (≤ 1,25× com texto, DESIGN; a manchete fica na tela)


def manchete(im):
    """máscara (L) das letras da manchete escrita na arte (branco ou amarelo) + caixa (x0, y0, x1, y1), ou (None, None)"""
    import numpy as np
    a = np.asarray(im.convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    txt = (np.minimum(np.minimum(r, g), b) > 225) | ((r > 200) & (g > 170) & (b < 90))
    linhas = np.where(txt[:, 100:W - 100].sum(1) > 150)[0]          # linha de manchete: muita letra clara na largura
    if not len(linhas):
        return None, None
    y0, y1 = linhas.min(), linhas.max()
    cols = np.where(txt[y0:y1 + 1].sum(0) >= 6)[0]
    m = np.zeros(txt.shape, bool); m[y0:y1 + 1] = txt[y0:y1 + 1]
    return Image.fromarray((m * 255).astype("uint8")), (int(cols.min()), int(y0), int(cols.max()), int(y1))


def batidas(desce, ancora_y=480, margem=40, zoom_motor=1.03):
    """v1.2.0 (28/10/2026): a capa troca de quadro a cada ~1 s até os 3 s — dois cortes secos de aproximação na mesma arte,
    presos no meio da manchete. → abertura-desce-1.png, -2.png
    v1.2.1 (28/10/2026): manchete larga (ex.: 986 px) saía da tela no corte de 1,10× (+3% do motor). Quando não cabe,
    a arte aproxima e a manchete fica do tamanho original, colada por cima (letras + contorno, borda suave)."""
    im = Image.open(desce).convert("RGB"); out = []
    masc, caixa = manchete(im)
    if caixa:
        ancora_y = (caixa[1] + caixa[3]) / 2
    for i, k in enumerate(BATIDAS, 1):
        w, h = W / k, H / k
        x0, y0 = (W - w) / 2, ancora_y - ancora_y / k
        z = im.crop((round(x0), round(y0), round(x0 + w), round(y0 + h))).resize((W, H), Image.LANCZOS)
        if caixa and (caixa[2] - caixa[0]) * k * zoom_motor > W - 2 * margem:
            # faixa inteira da manchete (largura toda, folga de 30 px, 18 px de degradê): só as letras deixava "fantasma"
            # das letras aproximadas atrás das originais
            fa, fb, fd = max(0, caixa[1] - 30), min(H, caixa[3] + 30), 18
            faixa = Image.new("L", (W, H), 0); d = ImageDraw.Draw(faixa)
            d.rectangle((0, fa, W, fb), fill=255)
            for t in range(1, fd + 1):
                v = int(255 * (1 - t / (fd + 1)))
                d.line((0, fa - t, W, fa - t), fill=v); d.line((0, fb + t, W, fb + t), fill=v)
            z.paste(im, (0, 0), faixa)
        dst = Path(desce).with_name(f"abertura-desce-{i}.png")
        z.save(dst)
        out.append(dst)
    return out


def screenshot(url, saida):
    """print 540x960 @2x da página (Chrome headless do Playwright)"""
    if not CHROME:
        raise SystemExit("Chrome headless do Playwright não encontrado em ~/.cache/ms-playwright")
    subprocess.run([str(CHROME[-1]), "--no-sandbox", "--hide-scrollbars", "--window-size=540,960", "--force-device-scale-factor=2",
                    "--virtual-time-budget=8000", f"--screenshot={saida}", url], capture_output=True, timeout=90)
    if not Path(saida).exists():
        raise SystemExit(f"screenshot falhou: {url}")
    return Path(saida)


def print_card(raw, saida, brilho=0.85):
    """print num cartão de borda amarela no alto da tela (y 210); 0.85 de brilho (0.55 apagava páginas escuras, 18/10)"""
    pr = Image.open(raw).convert("RGB")
    pr = pr.crop((0, 0, pr.width, min(pr.height, int(pr.width * 1.02))))
    larg = 940; pr = pr.resize((larg, round(pr.height * larg / pr.width)), Image.LANCZOS)
    # o cartão termina em y ≤ 1090: a legenda tem a base em 1280 (66 px, cresce pra cima) e cobria o texto
    # do print (revisor, 19/10: "NOS COMENTÁRIOS" em cima de "NEWS.inema.pro" em 6 reels)
    pr = pr.crop((0, 0, larg, min(pr.height, 880)))
    pr = ImageEnhance.Brightness(pr).enhance(brilho)
    bg = Image.new("RGB", (W, H), FUNDO)
    x, y = (W - larg) // 2, 210
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x, y + 18, x + larg, y + pr.height + 18), 30, fill=210)
    bg.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    m = Image.new("L", pr.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pr.width - 1, pr.height - 1), 28, fill=255)
    bg.paste(pr, (x, y), m)
    ImageDraw.Draw(bg).rounded_rectangle((x - 3, y - 3, x + larg + 3, y + pr.height + 3), 30, outline=AMAR, width=5)
    bg.save(saida); return Path(saida)


def preto(saida):
    Image.new("RGB", (W, H), FUNDO).save(saida); return Path(saida)


# ---- D13 (Nei, 20/10/2026): "quando se fala do produto, ele vira referência" — cartão com o LOGO REAL do produto
LOGOS = Path.home() / ".cache/r7ex/lobe-icons/dark"           # pacote MIT @lobehub/icons-static-png (ferramentas/logos.sh baixa)
FONTE_NOME = Path.home() / ".local/share/fonts/Montserrat-Black.ttf"


def logo_png(ident):
    """arquivo do logo: <id>-color.png (cor da marca) ou <id>.png (branco, para fundo escuro)"""
    for n in (f"{ident}-color.png", f"{ident}.png"):
        if (LOGOS / n).exists():
            return LOGOS / n
    raise SystemExit(f"logo '{ident}' não existe em {LOGOS} (veja os nomes: ls {LOGOS} | grep -i <marca>; baixar: ferramentas/logos.sh)")


def _logo(ident, lado):
    im = Image.open(logo_png(ident)).convert("RGBA")
    im = im.crop(im.getbbox() or (0, 0, im.width, im.height))
    k = lado / max(im.size)
    return im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)


def _texto(d, cx, y, txt, larg, maxpx, cor=(255, 255, 255)):
    from PIL import ImageFont
    px = maxpx
    while px > 30:
        f = ImageFont.truetype(str(FONTE_NOME), px)
        if d.textlength(txt, font=f) <= larg:
            break
        px -= 4
    d.text((cx, y), txt, font=f, fill=cor, anchor="mt")


def logo_card(logos, saida, fundo=None):
    """1 ou 2 logos grandes com luz âmbar atrás e o nome embaixo de cada um; metade de baixo escura (legenda/painel/avatar).
    logos = [{"id": "openai", "nome": "GPT-6.5"}, ...]; fundo = cena do Codex com o centro vazio (opcional, escurecida)"""
    bg = Image.new("RGB", (W, H), FUNDO)
    if fundo and Path(fundo).exists():
        f = ImageEnhance.Brightness(Image.open(vertical(fundo)).convert("RGB")).enhance(.6)
        m = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(m)
        for y in range(H):                                            # some aos poucos abaixo de y 900
            dm.line((0, y, W, y), fill=int(255 * max(0, min(1, (1250 - y) / 350))))
        bg.paste(f, (0, 0), m)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((540 - 480, 470 - 400, 540 + 480, 470 + 400), fill=120)
    bg.paste(AMAR, (0, 0), glow.filter(ImageFilter.GaussianBlur(150)))
    cone = Image.new("L", (W, H), 0)                                  # foco de luz de cima
    ImageDraw.Draw(cone).polygon([(470, 0), (610, 0), (900, 820), (180, 820)], fill=40)
    bg.paste((255, 240, 200), (0, 0), cone.filter(ImageFilter.GaussianBlur(60)))
    d = ImageDraw.Draw(bg)
    n = len(logos)
    pos = [(540, 440)] if n == 1 else [(290, 420), (790, 420)]
    lado = 400 if n == 1 else 300
    for lg, (cx, cy) in zip(logos, pos):
        im = _logo(lg["id"], lado)
        x, y = cx - im.width // 2, cy - im.height // 2
        halo = Image.new("L", (W, H), 0); halo.paste(im.split()[3], (x, y))
        bg.paste((255, 255, 255), (0, 0), halo.filter(ImageFilter.GaussianBlur(28)).point(lambda v: v * .55))
        bg.paste(im, (x, y), im)
        if lg.get("nome"):
            _texto(d, cx, cy + lado // 2 + 50, lg["nome"].upper(), 960 if n == 1 else 480, 120 if n == 1 else 76)
    bg.save(saida); return Path(saida)


def logo_solto(ident, saida, lado=300):
    """logo sozinho (fundo transparente) para o painel de baixo"""
    _logo(ident, lado).save(saida); return Path(saida)
