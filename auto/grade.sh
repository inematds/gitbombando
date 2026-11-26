#!/usr/bin/env bash
# Grade diária do Bombando no GitHub (Nei, 18/11/2026). Cada horário coleta, faz o carrossel e entra na fila dos reels.
#   07:00 dia      Top 10 do dia        reel lives4   carrossel lives9
#   08:00 top5     Top 5 da semana      reel lives8   carrossel lives12
#   09:30 area     Top 5 da área do dia reel lives3   carrossel lives9
#   10:00 agentes  Top 5 de agentes     reel lives7   carrossel lives12
#   domingo 09:00 semana  Top 10 da semana  reel lives4  sem carrossel
# Tudo entra pela fila do x3. Carrossel também vai ao Telegram INEMA.FTD. O v3 só recebe erro.
# uso: auto/grade.sh dia|top5|area|agentes|semana [AAAA-MM-DD]
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
FAIXA="${1:?dia, top5, area, agentes ou semana}"; DIA="${2:-$(date +%F)}"
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH" DISPLAY="${DISPLAY:-:99}"
CARR=""; CANAL=""; CONTA=""
case "$FAIXA" in
  dia) CARR=top10; CANAL=lives9; CONTA=@inema.tech ;;
  top5) CARR=top5; CANAL=lives12; CONTA=@inema.tds ;;
  area) CARR=area; CANAL=lives9; CONTA=@inema.tech ;;
  agentes) CARR=agentes; CANAL=lives12; CONTA=@inema.tds ;;
  semana) ;;
  *) echo "faixa inválida: $FAIXA"; exit 2 ;;
esac
GB_SO_COLETA=1 bash "$RAIZ/auto/rodar.sh" "$DIA" "$FAIXA" || echo "coleta prévia falhou; a rodada tenta de novo"
if [ -n "$CARR" ]; then
  GB_CANAL_CARROSSEL=$CANAL GB_CONTA=$CONTA bash "$RAIZ/auto/carrossel.sh" "$DIA" "$CARR" &
fi
GB_COLETA_PRONTA=1 bash "$RAIZ/auto/rodar.sh" "$DIA" "$FAIXA"; RC=$?
[ "$FAIXA" = dia ] && [ "$(date -d "$DIA" +%d)" = 01 ] && bash "$RAIZ/auto/rodar.sh" "$DIA" mes
wait
exit "$RC"
