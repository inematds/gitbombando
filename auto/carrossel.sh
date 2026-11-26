#!/usr/bin/env bash
# Carrossel do Bombando no GitHub (grade do Nei, 18/11/2026; quem chama é auto/grade.sh).
# Publicação sem aprovação: Telegram INEMA.FTD + fila do x3 (GB_CANAL_CARROSSEL). O v3 só recebe erro.
# dados → textos → prints do README + slides → portão → revisor → publica → git.
# uso: auto/carrossel.sh <AAAA-MM-DD> top10|top5|area|agentes
# Teste: ED=<pasta> SEM_TG=1 SEM_X3=1 SEM_BOT=1 SEM_GIT=1 auto/carrossel.sh 2026-11-04 area
# Pular: linha "AAAA-MM-DD carrossel" (todos) ou "AAAA-MM-DD carrossel-<tipo>" em auto/pular.txt.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DIA="${1:-$(date +%F)}"; TIPO="${2:?top10, top5, area ou agentes}"
case "$TIPO" in top10|top5|area|agentes) ;; *) echo "tipo inválido: $TIPO"; exit 2 ;; esac
ED="${ED:-$RAIZ/edicoes/$DIA-carrossel-$TIPO}"; mkdir -p "$ED"
exec >>"$ED/rodada.log" 2>&1
exec 7>"$RAIZ/auto/.carrossel-$TIPO"; flock -w 7200 7 || { echo "outra rodada do carrossel $TIPO segurou a trava"; exit 1; }
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
echo "=== $(date '+%F %T') carrossel $TIPO $DIA"
grep -qxE "$DIA carrossel(-$TIPO)?" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
grep -qx "$DIA" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
if [ -s "$ED/x3.txt" ] && grep -q "mensagens publicadas" "$ED/telegram.log" 2>/dev/null && [ -z "${FORCAR:-}" ]; then
  echo "já publicado; FORCAR=1 refaz"; exit 0
fi
BOT="$RAIZ/bin/enviar_bot_v3.mjs"
case "$TIPO" in top10) NOME="Carrossel Top 10" ;; top5) NOME="Carrossel Top 5 da semana" ;; area) NOME="Carrossel Top 5 da área" ;; agentes) NOME="Carrossel Top 5 de agentes" ;; esac
avisar() {
  echo "$1" > "$ED/aviso.txt"; rm -f "$ED/aviso.txt.envio-v3.json" "$ED/folha.jpg.envio-v3.json"
  ARQ="$ED/aviso.txt"; [ -s "$ED/folha.jpg" ] && ARQ="$ED/folha.jpg"
  [ "${SEM_BOT:-}" = 1 ] || node "$BOT" "$ARQ" "Falhou: Bombando no GitHub · $NOME · $(date -d "$DIA" +%d/%m/%Y)
$1
Para publicar assim mesmo: cd $RAIZ && python3 carrossel/carrossel.py publicar $ED" || echo "falhou o aviso"
  echo "AVISO: $1"; exit 1
}

python3 "$RAIZ/auto/ia.py" validar >/dev/null || avisar "configuração de IA inválida (auto/ia.yaml)"

python3 "$RAIZ/carrossel/carrossel.py" fazer "$ED" "$TIPO" "$DIA" > "$ED/fazer.log" 2>&1
RC=$?
V=$(python3 -c "import json;print(json.load(open('$ED/revisao.json'))['veredito'])" 2>/dev/null)
[ "$RC" = 0 ] && [ "$V" = aprovado ] || avisar "revisor/portão: ${V:-sem veredito} — $(python3 -c "import json;print(json.load(open('$ED/revisao.json')).get('motivo',''))" 2>/dev/null || tail -2 "$ED/fazer.log" | cut -c1-300)"

python3 "$RAIZ/carrossel/carrossel.py" publicar "$ED" > "$ED/publicar.log" 2>&1 || echo "publicar saiu com erro (ver publicar.log)"
tail -8 "$ED/publicar.log"

if [ "${SEM_GIT:-}" != 1 ]; then
  cd "$RAIZ"
  for f in "edicoes/$DIA-carrossel-$TIPO"/{dados.json,textos.json,slides.json,prints.json,revisao.json,telegram.md,x3.txt,v3.txt} \
           historico auto/telegram-topico-carrossel-ftd.txt; do
    [ -e "$f" ] && git add -- "$f"
  done
  git -c user.name=inematds -c user.email=inematds@gmail.com commit -qm "Bombando no GitHub · $NOME · $(date -d "$DIA" +%d/%m/%Y) (rodada automática)" \
    && { git pull -q --rebase --autostash && git push -q && echo "push ok"; } || echo "git: nada a commitar ou falhou"
fi
echo "=== fim $(date '+%F %T')"
