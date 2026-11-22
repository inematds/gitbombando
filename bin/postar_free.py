#!/usr/bin/env python3
"""Posta o reel do gitbombando no grupo INEMA.FREE (https://t.me/+Trl-P9FduY8zMjdh), pela conta do Nei.

Nei, 22/11/2026: "quero sempre publicado também no INEMA.FREE".
O grupo não tem tópicos: vai o vídeo com legenda curta (título, resumo, YouTube) e, logo abaixo, o ranking com os links.
Usa o telegram.md que o gb.py já escreveu para o INEMA.TOOLS. Uma vez por edição (free.log).

uso: postar_free.py <pasta-da-edição> [url-do-youtube] [--ensaio]
"""
import asyncio
import os
import re
import subprocess
import sys
import time
from pathlib import Path

GRUPO_ID = 2242190548                       # INEMA.FREE
TG = Path.home() / "projetos/telegramtopicosindex"
LIMITE_LEGENDA = 1000                       # o Telegram corta legenda de mídia em 1024


def montar(p, url):
    md = (p / "telegram.md").read_text()
    md = re.sub(r"\n?\[\[img:[^\]]+\]\]\n?", "\n", md)
    md = re.sub(r"\n*▶️ No YouTube:.*", "", md)
    cab, _, ranking = md.partition("\n---\n")
    leg = cab.strip()
    if url:
        leg += f"\n\n▶️ No YouTube: {url}"
    leg += "\n\n📚 Grátis no inema.club"
    if len(leg) > LIMITE_LEGENDA:          # resumo longo: corta no fim de frase, mantém título e links
        titulo, _, resumo = cab.strip().partition("\n\n")
        sobra = LIMITE_LEGENDA - len(leg) + len(resumo) - 3
        resumo = resumo[:max(sobra, 0)].rsplit(". ", 1)[0] + "…"
        leg = f"{titulo}\n\n{resumo}" + (f"\n\n▶️ No YouTube: {url}" if url else "") + "\n\n📚 Grátis no inema.club"
    ranking = ranking.strip()
    if url:   # Nei, 22/11/2026: os links dos tops e, depois, o link do vídeo no YouTube
        ranking = ranking.replace("\n\nQual desses", f"\n\n▶️ Vídeo no YouTube: {url}\n\nQual desses", 1) \
            if "\n\nQual desses" in ranking else ranking + f"\n\n▶️ Vídeo no YouTube: {url}"
    return leg, ranking


async def enviar(p, legenda, ranking):
    sys.path.insert(0, str(TG)); os.chdir(TG)
    import extrator_rapido as ex
    from telethon import TelegramClient
    from telethon.tl.types import PeerChannel
    v = p / "video.mp4"; thumb = p / "video.jpg"
    if not thumb.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", v, "-frames:v", "1", "-vf", "scale=320:-1", thumb], check=False)
    c = TelegramClient(ex.SESSION, ex.API_ID, ex.API_HASH)
    await c.connect()
    try:
        g = await c.get_entity(PeerChannel(GRUPO_ID))
        m1 = await c.send_file(g, v, caption=legenda, parse_mode="md", supports_streaming=True,
                               thumb=str(thumb) if thumb.exists() else None)
        ids = [m1.id]
        if ranking:
            m2 = await c.send_message(g, ranking, parse_mode="md", link_preview=False)
            ids.append(m2.id)
        return ids
    finally:
        await c.disconnect()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ensaio = "--ensaio" in sys.argv
    p = Path(args[0]).resolve(); url = args[1] if len(args) > 1 else ""
    reg = p / "free.log"
    if reg.exists() and "postado" in reg.read_text():
        print("INEMA.FREE: esta edição já foi postada"); return
    legenda, ranking = montar(p, url)
    print(f"legenda ({len(legenda)} car.):\n{legenda}\n---\nranking ({len(ranking)} car.)")
    if ensaio:
        print("(ensaio: nada enviado)"); return
    for _ in range(60):   # sessão compartilhada: espera ficar livre, até 10 min
        if subprocess.run(["lsof", str(TG / "telegram_session.session")], capture_output=True).returncode:
            break
        time.sleep(10)
    ids = asyncio.run(enviar(p, legenda, ranking))
    reg.write_text(f"postado {time.strftime('%F %T')} mensagens {ids}\n")
    print(f"INEMA.FREE: postado, mensagens {ids}")


if __name__ == "__main__":
    main()
