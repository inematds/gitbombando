#!/usr/bin/env bash
# Rodada automática do "Bombando no GitHub" (reel 9:16 com o Top 10 do GitHub; lives4 + bot v3 + tópico no INEMA.TOOLS).
# Pedido do Nei em 28/10/2026: "crie uma agenda para 4 da tarde rodar e publicar todo dia" (avatar incluso, sem aprovação).
# coleta (GitHub) → roteiro (claude -p, assinatura) → avatar (estúdio HeyGen) + cartões + capa (Codex) → render
#   → revisor (claude -p) → YouTube lives4 + bot v3 + Telegram → git push.
# uso: auto/rodar.sh [AAAA-MM-DD, padrão hoje] [dia|semana|mes]
#   O timer das 16:00 chama auto/rodar.sh sem modo = "auto": sempre o dia; no domingo também a semana; no dia 1º também o mês.
# Teste: ED=<pasta de teste> AVATAR_DE=<mp4 já gravado> (não gasta avatar) SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_GIT=1 GB_SEM_HISTORICO=1.
# Pular: linha "AAAA-MM-DD" (tudo) ou "AAAA-MM-DD semana" em auto/pular.txt.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DIA="${1:-$(date +%F)}"; MODO="${2:-auto}"
if [ "$MODO" = auto ]; then
  bash "$0" "$DIA" dia
  [ "$(date -d "$DIA" +%u)" = 7 ] && bash "$0" "$DIA" semana
  [ "$(date -d "$DIA" +%d)" = 01 ] && bash "$0" "$DIA" mes
  exit 0
fi
case "$MODO" in
  dia) SUF=top10-dia; NOME_MODO="do dia"; PERIODO="hoje" ;;
  semana) SUF=top10-semana; NOME_MODO="da semana"; PERIODO="na semana" ;;
  mes) SUF=top10-mes; NOME_MODO="do mês"; PERIODO="no mês" ;;
  *) echo "modo inválido: $MODO"; exit 2 ;;
esac
ED="${ED:-$RAIZ/edicoes/$DIA-$SUF}"; mkdir -p "$ED/pesquisa" "$ED/avatar"
LOG="$ED/rodada.log"; exec >>"$LOG" 2>&1
exec 8>"$RAIZ/auto/.rodando"; flock -w 14400 8 || { echo "outra rodada segurou a trava por horas"; exit 1; }
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH" DISPLAY="${DISPLAY:-:99}"
echo "=== $(date '+%F %T') Bombando no GitHub $MODO $DIA (v$(grep -o 'VERSAO = "[^"]*' "$RAIZ/gb.py" | cut -d'"' -f2))"
grep -qx "$DIA" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
grep -qx "$DIA $MODO" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
[ -s "$ED/youtube-lives4.txt" ] && [ -z "${FORCAR:-}" ] && { echo "já publicado hoje ($(cat "$ED/youtube-lives4.txt")); FORCAR=1 refaz"; exit 0; }
# vídeo já feito e revisado nesta pasta: retoma sem refazer roteiro nem avatar
[ -s "$ED/video.mp4" ] && [ -s "$ED/revisao.json" ] && REUSAR=1
BOT="$RAIZ/bin/enviar_bot_v3.mjs"
DATA_BR=$(date -d "$DIA" +%d/%m/%Y)
avisar() {  # aviso "Falhou" no bot v3 e sai
  echo "$1" > "$ED/aviso.txt"; rm -f "$ED/aviso.txt.envio-v3.json"
  [ "${SEM_BOT:-}" = 1 ] || node "$BOT" "$ED/aviso.txt" "Falhou: Bombando no GitHub ($MODO) · $DATA_BR
$1" || echo "falhou o envio do aviso"
  echo "AVISO: $1"; exit "${2:-1}"
}

# 1. coleta (só GitHub)
if [ -s "$ED/pesquisa/top10.json" ] && [ "${REUSAR:-}" = 1 ]; then echo "reusando a coleta"
else timeout 900 python3 "$RAIZ/coleta/trending.py" "$ED" "$MODO" > "$ED/pesquisa/coleta.log" 2>&1 \
  || avisar "coleta do GitHub Trending falhou: $(tail -1 "$ED/pesquisa/coleta.log")"; fi

# 2. roteiro pelo claude -p (assinatura); modelo = a ficha aprovada mais recente do mesmo modo
PREV=$(ls -d "$RAIZ"/edicoes/*-"$SUF" 2>/dev/null | grep -vx "$ED" | sort | tail -1)
[ -n "$PREV" ] && [ -f "$PREV/ficha.yaml" ] || PREV="$RAIZ/modelo"
if [ -s "$ED/ficha.yaml" ] && [ "${REUSAR:-}" = 1 ] && python3 "$RAIZ/gb.py" checar "$ED" >/dev/null 2>&1; then echo "reusando ficha.yaml"
else
  rm -f "$ED/ERRO.txt" "$ED/ficha.yaml"
  PROMPT=$(sed -e "s|{ED}|$ED|g" -e "s|{PREV}|$PREV|g" -e "s|{RAIZ}|$RAIZ|g" -e "s|{DATA_BR}|$DATA_BR|g" -e "s|{MODO}|$MODO|g" \
               -e "s|{NOME_MODO}|$NOME_MODO|g" -e "s|{PERIODO}|$PERIODO|g" "$RAIZ/auto/roteiro.md")
  ( cd "$ED" && timeout 3600 env -u ANTHROPIC_API_KEY claude -p "$PROMPT" --permission-mode bypassPermissions \
      --add-dir "$RAIZ" > "$ED/claude.log" 2>&1 ) || echo "claude -p saiu com erro"
  [ -f "$ED/ERRO.txt" ] && avisar "o roteiro não saiu: $(head -c 400 "$ED/ERRO.txt")"
  python3 "$RAIZ/gb.py" checar "$ED" > "$ED/checar.log" 2>&1 || avisar "roteiro reprovado no portão: $(tail -c 500 "$ED/checar.log")"
fi

# 3. avatar autorizado em pé (Nei, 28/10/2026: "rodar e publicar todo dia"), imagens, cena, render e revisor
[ -f "$ED/avatar/APROVADO_HEYGEN" ] || echo "Rodada diária autorizada pelo Nei em 28/10/2026 (gitbombando: rodar e publicar todo dia às 16h)." > "$ED/avatar/APROVADO_HEYGEN"
if [ -n "${AVATAR_DE:-}" ] && [ ! -s "$ED/avatar/avatar.mp4" ]; then
  [ -s "$AVATAR_DE" ] || { echo "AVATAR_DE não existe: $AVATAR_DE (nada foi gravado no HeyGen)" | tee /dev/stderr; exit 2; }
  cp "$AVATAR_DE" "$ED/avatar/avatar.mp4"
fi
python3 "$RAIZ/gb.py" fazer "$ED" > "$ED/fazer.log" 2>&1 || avisar "montagem falhou: $(tail -2 "$ED/fazer.log" | cut -c1-400)"
V=$(python3 -c "import json;print(json.load(open('$ED/revisao.json'))['veredito'])" 2>/dev/null)
if [ "$V" = erro ]; then python3 "$RAIZ/gb.py" revisar "$ED" >> "$ED/fazer.log" 2>&1; V=$(python3 -c "import json;print(json.load(open('$ED/revisao.json'))['veredito'])"); fi
if [ "$V" != aprovado ]; then
  rm -f "$ED/video.mp4.envio-v3.json"
  [ "${SEM_BOT:-}" = 1 ] || node "$BOT" "$ED/video.mp4" "Falhou: Bombando no GitHub ($MODO) · $DATA_BR — revisor $V, NÃO publiquei
$(python3 -c "import json;print(json.load(open('$ED/revisao.json')).get('motivo',''))")
Para publicar assim mesmo: cd $RAIZ && python3 gb.py publicar $ED"
  echo "revisor: $V"; exit 1
fi

# 4. publicar: YouTube lives4, bot v3, tópico no INEMA.TOOLS
python3 "$RAIZ/gb.py" publicar "$ED" > "$ED/publicar-gb.log" 2>&1 || echo "publicar saiu com erro (ver publicar-gb.log)"
tail -3 "$ED/publicar-gb.log"

# 5. git (autor inematds); mídia fica fora pelo .gitignore
if [ "${SEM_GIT:-}" != 1 ]; then
  cd "$RAIZ"
  for f in "edicoes/$DIA-$SUF"/{ficha.yaml,falas.json,revisao.json,yt.txt,telegram.md,youtube-lives4.txt,pesquisa/top10.json} historico auto/telegram-topico.txt; do
    [ -e "$f" ] && git add -- "$f"
  done
  git -c user.name=inematds -c user.email=inematds@gmail.com commit -qm "Bombando no GitHub · $MODO $DATA_BR (rodada automática)" \
    && { git pull -q --rebase --autostash && git push -q && echo "push ok"; } || echo "git: nada a commitar ou falhou"
fi
echo "=== fim $(date '+%F %T')"
