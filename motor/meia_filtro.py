#!/usr/bin/env python3
"""Trechos do avatar em MEIA tela (metade de baixo, 1080x960 em y 960) para o compor_avatar.sh (LAYOUT=canto).

Uso: meia_filtro.py <meia.txt> <entrada-com-o-quadro> <saida>
meia.txt: uma linha "ini fim" (segundos) por trecho, escrita pelo r7ex/cena.py. Imprime um pedaço de filter_complex
que pega [<entrada>] (o quadro já com o PiP) e devolve [<saida>] com o rosto grande por cima nesses trechos:
cada trecho é um recorte do avatar (trim mantém o tempo original) com dissolve de 0,35 s na entrada e na saída —
o PiP fica por baixo o tempo todo, então a troca vira um dissolve rosto grande ↔ PiP (Nei, 21/10/2026).
"""
import os
import sys
from pathlib import Path

FADE = .35
TAG = os.environ.get("R7X_TAG", str(Path(__file__).resolve().parent / "tag-nei.txt"))   # VPS da Tiza: R7X_TAG=tag-tiza.txt
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def filtro(meia, entrada, saida):
    tr = [tuple(map(float, l.split())) for l in Path(meia).read_text().splitlines() if l.strip()]
    if not tr:
        return f"[{entrada}]null[{saida}];"
    n = len(tr)
    out = [f"[1:v]crop=1215:1080:352:0,scale=1080:960,setsar=1,fps=30,"
           f"drawbox=x=0:y=0:w=1080:h=4:color=0xE2A23B@1:t=fill,"
           f"drawbox=x=28:y=886:w=390:h=44:color=0x0b0f14@0.85:t=fill,drawbox=x=28:y=886:w=6:h=44:color=0xff2a1f@1:t=fill,"
           f"drawtext=fontfile={FONTE}:textfile={TAG}:x=46:y=897:fontsize=22:fontcolor=white,"
           f"format=yuva420p,split={n}" + "".join(f"[mz{k}]" for k in range(n)) + ";"]
    ant = entrada
    for k, (a, b) in enumerate(tr):
        f = f"[mz{k}]trim=start={a}:end={b + FADE}"
        if a > 0:
            f += f",fade=t=in:st={a}:d={FADE}:alpha=1"
        f += f",fade=t=out:st={b - FADE / 2:.3f}:d={FADE}:alpha=1[m{k}];"
        nxt = saida if k == n - 1 else f"q{k}"
        f += f"[{ant}][m{k}]overlay=0:960:eof_action=pass:repeatlast=0[{nxt}];"
        out.append(f)
        ant = nxt
    return "".join(out)


if __name__ == "__main__":
    print(filtro(*sys.argv[1:4]))
