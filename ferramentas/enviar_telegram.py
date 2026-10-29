#!/usr/bin/env python3
"""Manda um vídeo/imagem a um bot do Telegram qualquer (ex.: @tizaccbot na VPS da Tiza), sem o openpcbot.

  python3 ferramentas/enviar_telegram.py <arquivo> "<legenda>" --env /root/projetos/inemaccbot/.env [--chat <id>]

Token: BOT_TOKEN (ou TELEGRAM_BOT_TOKEN) lido do --env na hora; nunca impresso.
Chat: --chat, ou o primeiro de ALLOWED_CHAT_IDS do mesmo .env.
> 49 MB: faz <arquivo>-720p.mp4 e manda essa. Recibo em <arquivo>.envio-telegram.json (não reenvia).
"""
import argparse
import json
import mimetypes
import re
import subprocess
import sys
import uuid
import urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("arquivo")
ap.add_argument("legenda", nargs="?", default="")
ap.add_argument("--env", required=True)
ap.add_argument("--chat")
a = ap.parse_args()

arq = Path(a.arquivo)
if not arq.exists():
    sys.exit(f"Falhou: arquivo não existe: {arq}")
recibo = Path(str(arq) + ".envio-telegram.json")
if recibo.exists():
    print("já enviado:", recibo.read_text().strip())
    sys.exit(0)

env = {}
for linha in Path(a.env).read_text().splitlines():
    m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$", linha)
    if m and not linha.lstrip().startswith("#"):
        env[m.group(1)] = m.group(2).strip("\"'")
token = env.get("BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN")
chat = a.chat or (env.get("ALLOWED_CHAT_IDS", "").split(",")[0].strip())
if not token or not chat:
    sys.exit("Falhou: sem BOT_TOKEN ou chat no .env")

envio = arq
if arq.suffix == ".mp4" and arq.stat().st_size > 49 * 1024 * 1024:
    envio = arq.with_name(arq.stem + "-720p.mp4")
    if not envio.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", arq, "-vf", "scale=-2:1280", "-c:v", "libx264", "-b:v", "1500k",
                        "-maxrate", "2M", "-bufsize", "4M", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", envio], check=True)

metodo, campo = ("sendVideo", "video") if envio.suffix == ".mp4" else \
    ("sendPhoto", "photo") if envio.suffix.lower() in (".jpg", ".jpeg", ".png") else ("sendDocument", "document")
limite = uuid.uuid4().hex
corpo = []
for k, v in {"chat_id": chat, "caption": a.legenda[:1024], "supports_streaming": "true"}.items():
    corpo += [f"--{limite}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()]
tipo = mimetypes.guess_type(envio.name)[0] or "application/octet-stream"
corpo += [f"--{limite}\r\nContent-Disposition: form-data; name=\"{campo}\"; filename=\"{envio.name}\"\r\nContent-Type: {tipo}\r\n\r\n".encode(),
          envio.read_bytes(), f"\r\n--{limite}--\r\n".encode()]
req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metodo}", data=b"".join(corpo),
                             headers={"Content-Type": f"multipart/form-data; boundary={limite}"})
try:
    r = json.loads(urllib.request.urlopen(req, timeout=600).read())
except Exception as e:  # noqa: BLE001 — a mensagem não pode levar o token
    sys.exit(f"Falhou: envio ao Telegram — {str(e).replace(token, '***')[:200]}")
if not r.get("ok"):
    sys.exit(f"Falhou: Telegram respondeu {str(r)[:200]}")
recibo.write_text(json.dumps({"chat": chat, "message_id": r["result"]["message_id"], "arquivo": envio.name}))
print(f"enviado: {envio.name} → chat {chat} (msg {r['result']['message_id']})")
