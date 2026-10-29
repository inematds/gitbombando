#!/usr/bin/env bash
# Mapa (modo avatar) + avatar do HeyGen na faixa 1080x608 em y=1110 (formato 9:16 do explicavideos) + trilha.
# Voz do HeyGen chega ~-26 dB: loudnorm a -14 LUFS (padrão de short) antes de mixar (09/10/2026).
# uso: motor/compor_avatar.sh <pasta-da-edicao> [saida.mp4]   (precisa de <edicao>/avatar/avatar.mp4 e cena.js gerado com --avatar)
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
E="$(cd "$1" && pwd)"; SAIDA="${2:-$E/video-avatar.mp4}"
MUSICA="${MUSICA:-$HOME/projetos/cardshorts/musicas/tensa.mp3}"
A="$E/avatar/avatar.mp4"
LAYOUT="${LAYOUT:-faixa}"
# canto + meia (21/10/2026): avatar/meia.txt (do cena.py) lista os trechos em que o rosto ocupa a metade de baixo
[ "${LAYOUT:-faixa}" = canto ] && [ ! -f "${MEIA_TXT:-$E/avatar/meia.txt}" ] && : > "$E/avatar/meia.txt"   # faixa = 1080x608 em y=1110 (explicavideos) · canto = rosto 400x453 embaixo à direita · largo = 16:9, avatar 640x1080 à direita (cena com layout "largo")
mkdir -p "$E/build"
# Portabilidade (25/10/2026, VPS sem GPU): fila de GPU e nome no rosto por variável; sem a fila, roda direto
GPU_FILA="${R7X_GPU_FILA:-/home/nmaldaner/projetos/wifi/scripts/gpu-fila}"
FILA=""; [ -x "$GPU_FILA" ] && FILA="$GPU_FILA r7ex-render --"
TAG="${R7X_TAG:-$AQUI/tag-nei.txt}"
# PULA_RENDER=1 reaproveita build/mapa-avatar.mp4 já renderizado (retomada depois de falha na montagem, 15/10/2026)
[ "${PULA_RENDER:-}" = 1 ] && [ -s "$E/build/mapa-avatar.mp4" ] || GPU_ESPERA_MIN=${GPU_ESPERA_MIN:-30} $FILA timeout "${R7X_RENDER_TIMEOUT:-1200}" node "$AQUI/render.mjs" "$E" "$E/build/mapa-avatar.mp4"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$A")
# fade só na música: o HeyGen termina logo após a última palavra e o fade na mistura engolia o CTA
FADE=$(python3 -c "print(max(0, $D - 1.4))")
# pausa antes da máxima (r7ex/ritmo.py, 28/10/2026): a trilha some junto com a voz nesse vão (silêncio de verdade, não
# só a voz calada com a cama subindo pelo sidechain); fora dele, 0.2 como sempre. Sem avatar/ritmo.json, 0.2 fixo.
VOLM=$(python3 - "$E/avatar/ritmo.json" <<'PY'
import json, sys, os
z = (json.load(open(sys.argv[1])).get("pausa") or {}) if os.path.exists(sys.argv[1]) else {}
a, b = z.get("ini"), z.get("fim")
print("0.2" if a is None else f"'0.2*clip(max(({a:.3f}-t)/0.08,(t-{b:.3f})/0.08),0,1)':eval=frame")
PY
)
if [ "$LAYOUT" = largo ]; then VID="[1:v]crop=640:1080:820:0,setsar=1,fps=30[av];[0:v][av]overlay=1280:0:shortest=1,drawbox=x=1276:y=0:w=4:h=1080:color=0xE2A23B@1:t=fill,drawbox=x=1304:y=1000:w=330:h=46:color=0x0b0f14@0.85:t=fill,drawbox=x=1304:y=1000:w=6:h=46:color=0xff2a1f@1:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=$TAG:x=1322:y=1013:fontsize=22:fontcolor=white[v];"; elif [ "$LAYOUT" = canto ]; then VID="[1:v]crop=900:1020:510:0,scale=400:453,setsar=1,fps=30[av];[0:v]drawbox=x=636:y=1286:w=408:h=461:color=0xE2A23B@1:t=fill[bg];[bg][av]overlay=640:1290:shortest=1,drawbox=x=640:y=1700:w=400:h=43:color=0x0b0f14@0.85:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=$TAG:x=656:y=1712:fontsize=19:fontcolor=white[v0];$(python3 "$AQUI/meia_filtro.py" "${MEIA_TXT:-$E/avatar/meia.txt}" v0 v)"; else VID="[1:v]scale=1080:608,setsar=1,fps=30[av];[0:v][av]overlay=0:1110:shortest=1,drawbox=x=28:y=1652:w=390:h=44:color=0x0b0f14@0.85:t=fill,drawbox=x=28:y=1652:w=6:h=44:color=0xff2a1f@1:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=$TAG:x=46:y=1663:fontsize=22:fontcolor=white[v];"; fi
ffmpeg -v error -y -i "$E/build/mapa-avatar.mp4" -i "$A" -stream_loop -1 -i "$MUSICA" -filter_complex \
  "$VID
   [1:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,asplit=2[voz][sc];[2:a]volume=$VOLM,aresample=48000[m];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300,afade=t=out:st=$FADE:d=1.4[md];
   [voz][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 23 -preset slow -maxrate 4M -bufsize 8M -c:a aac -b:a 192k -movflags +faststart -shortest "$SAIDA"
echo "ok $SAIDA ($(du -h "$SAIDA" | cut -f1))"
