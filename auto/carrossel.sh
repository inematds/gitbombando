#!/usr/bin/env bash
# Carrossel diário do Bombando no GitHub (Nei, 04/11/2026: "2 carrosséis e 1 vídeo diário … 14h o carrossel, e um às 18h
# com os tops de cada área"). Publicação direta, sem aprovação: Telegram INEMA.DEV + Instagram/TikTok inema.tech (marca FTD, lives3) + aviso no v3.
# dados → textos (claude -p) → prints do README + slides → portão → revisor (claude -p) → espera a hora → publica → git.
# uso: auto/carrossel.sh <AAAA-MM-DD> top10|area
#   PUBLICAR_AS=HH:MM espera essa hora para publicar (o timer liga ~1h30 antes). Sem HeyGen: não disputa com o vídeo.
# Teste: ED=<pasta> SEM_TG=1 SEM_METRI=1 SEM_BOT=1 SEM_GIT=1 auto/carrossel.sh 2026-11-04 area
# Pular: linha "AAAA-MM-DD carrossel" (os dois) ou "AAAA-MM-DD carrossel-top10|carrossel-area" em auto/pular.txt.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DIA="${1:-$(date +%F)}"; TIPO="${2:?top10 ou area}"
case "$TIPO" in top10|area) ;; *) echo "tipo inválido: $TIPO"; exit 2 ;; esac
ED="${ED:-$RAIZ/edicoes/$DIA-carrossel-$TIPO}"; mkdir -p "$ED"
exec >>"$ED/rodada.log" 2>&1
exec 7>"$RAIZ/auto/.carrossel-$TIPO"; flock -w 7200 7 || { echo "outra rodada do carrossel $TIPO segurou a trava"; exit 1; }
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
echo "=== $(date '+%F %T') carrossel $TIPO $DIA"
grep -qxE "$DIA carrossel(-$TIPO)?" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
grep -qx "$DIA" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
if [ -s "$ED/metritds.txt" ] && grep -q "mensagens publicadas" "$ED/telegram.log" 2>/dev/null && [ -z "${FORCAR:-}" ]; then
  echo "já publicado; FORCAR=1 refaz"; exit 0
fi
BOT="$RAIZ/bin/enviar_bot_v3.mjs"
NOME=$([ "$TIPO" = top10 ] && echo "Carrossel Top 10" || echo "Carrossel Top da área")
avisar() {
  echo "$1" > "$ED/aviso.txt"; rm -f "$ED/aviso.txt.envio-v3.json" "$ED/folha.jpg.envio-v3.json"
  ARQ="$ED/aviso.txt"; [ -s "$ED/folha.jpg" ] && ARQ="$ED/folha.jpg"
  [ "${SEM_BOT:-}" = 1 ] || node "$BOT" "$ARQ" "Falhou: Bombando no GitHub · $NOME · $(date -d "$DIA" +%d/%m/%Y)
$1
Para publicar assim mesmo: cd $RAIZ && python3 carrossel/carrossel.py publicar $ED" || echo "falhou o aviso"
  echo "AVISO: $1"; exit 1
}

python3 "$RAIZ/carrossel/carrossel.py" fazer "$ED" "$TIPO" "$DIA" > "$ED/fazer.log" 2>&1
RC=$?
V=$(python3 -c "import json;print(json.load(open('$ED/revisao.json'))['veredito'])" 2>/dev/null)
[ "$RC" = 0 ] && [ "$V" = aprovado ] || avisar "revisor/portão: ${V:-sem veredito} — $(python3 -c "import json;print(json.load(open('$ED/revisao.json')).get('motivo',''))" 2>/dev/null || tail -2 "$ED/fazer.log" | cut -c1-300)"

if [ -n "${PUBLICAR_AS:-}" ]; then
  ALVO=$(date -d "$DIA $PUBLICAR_AS" +%s); AGORA=$(date +%s)
  [ "$AGORA" -lt "$ALVO" ] && { echo "pronto; esperando até $PUBLICAR_AS para publicar"; sleep $((ALVO - AGORA)); }
fi
python3 "$RAIZ/carrossel/carrossel.py" publicar "$ED" > "$ED/publicar.log" 2>&1 || echo "publicar saiu com erro (ver publicar.log)"
tail -8 "$ED/publicar.log"

if [ "${SEM_GIT:-}" != 1 ]; then
  cd "$RAIZ"
  for f in "edicoes/$DIA-carrossel-$TIPO"/{dados.json,textos.json,slides.json,prints.json,revisao.json,telegram.md,metritds-texto.txt,metritds.txt,v3.txt} \
           historico auto/telegram-topico-carrossel.txt; do
    [ -e "$f" ] && git add -- "$f"
  done
  git -c user.name=inematds -c user.email=inematds@gmail.com commit -qm "Bombando no GitHub · $NOME · $(date -d "$DIA" +%d/%m/%Y) (rodada automática)" \
    && { git pull -q --rebase --autostash && git push -q && echo "push ok"; } || echo "git: nada a commitar ou falhou"
fi
echo "=== fim $(date '+%F %T')"
