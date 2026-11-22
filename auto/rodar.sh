#!/usr/bin/env bash
# Reel do "Bombando no GitHub" (9:16, avatar do Nei). Quem chama é auto/grade.sh (grade do Nei, 18/11/2026).
# coleta → roteiro → avatar (estúdio HeyGen) + cartões + capa (Codex) → render → revisor → fila do x3 → INEMA.TOOLS → git push.
# uso: auto/rodar.sh [AAAA-MM-DD] [dia|semana|mes|top5|area|agentes]
#   dia e semana/mes: Top 10 no lives4 · top5: Top 5 da semana no lives8 · area: Top 5 da área no lives3 · agentes: Top 5 no lives7.
#   Publica ao ficar pronto. Tenta o HeyGen 3 vezes; revisor reprovou = capa nova e novo render, uma vez. O v3 só recebe erro.
# Teste: ED=<pasta> AVATAR_DE=<mp4> SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_GIT=1 GB_SEM_HISTORICO=1 · GB_SO_COLETA=1 · GB_PARAR_APOS_ROTEIRO=1
# Pular: linha "AAAA-MM-DD" (tudo) ou "AAAA-MM-DD <modo>" em auto/pular.txt.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DIA="${1:-$(date +%F)}"; MODO="${2:-auto}"
if [ "$MODO" = auto ]; then
  bash "$0" "$DIA" dia
  [ "$(date -d "$DIA" +%d)" = 01 ] && bash "$0" "$DIA" mes
  exit 0
fi
COLETA=trending; TOP=10; MODO_F="$MODO"; CANAL=lives4
case "$MODO" in
  dia) SUF=top10-dia; NOME_MODO="do dia"; PERIODO="hoje" ;;
  semana) SUF=top10-semana; NOME_MODO="da semana"; PERIODO="na semana" ;;
  mes) SUF=top10-mes; NOME_MODO="do mês"; PERIODO="no mês" ;;
  top5) SUF=top5-semana; NOME_MODO="da semana"; PERIODO="na semana"; MODO_F=semana; TOP=5; CANAL=lives8 ;;
  area) SUF=top5-area; NOME_MODO="da área do dia"; PERIODO="por dia"; MODO_F=area; COLETA=area; CANAL=lives3 ;;
  agentes) SUF=top5-agentes; NOME_MODO="de sistemas de agentes"; PERIODO="por dia"; MODO_F=area; COLETA=agentes; CANAL=lives7 ;;
  *) echo "modo inválido: $MODO"; exit 2 ;;
esac
export GB_CANAL="${GB_CANAL:-$CANAL}"; CANAL="$GB_CANAL"
if [ "$COLETA" = trending ]; then CRITERIO="que mais ganharam estrelas $PERIODO no GitHub Trending"
else CRITERIO="que mais crescem no assunto do campo area, medidos em estrelas por dia desde a criação"; fi
ED="${ED:-$RAIZ/edicoes/$DIA-$SUF}"; mkdir -p "$ED/pesquisa" "$ED/avatar"
LOG="$ED/rodada.log"; exec >>"$LOG" 2>&1
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH" DISPLAY="${DISPLAY:-:99}"
coletar() {
  if [ "$COLETA" = trending ]; then
    [ "$TOP" = 5 ] && export GB_SEM_HISTORICO=1
    GB_TOP=$TOP timeout 9000 python3 "$RAIZ/coleta/trending.py" "$ED" "$MODO_F"
  else timeout 1800 python3 "$RAIZ/coleta/area_top.py" "$ED" "$COLETA" "$DIA"; fi
}
# a grade coleta antes da fila dos reels, para o carrossel do mesmo horário não esperar o avatar
if [ "${GB_SO_COLETA:-}" = 1 ]; then
  [ -s "$ED/pesquisa/top10.json" ] && exit 0
  coletar > "$ED/pesquisa/coleta.log" 2>&1; exit $?
fi
exec 8>"${GB_TRAVA:-$RAIZ/auto/.rodando}"; flock -w 14400 8 || { echo "outra rodada segurou a trava por horas"; exit 1; }
echo "=== $(date '+%F %T') Bombando no GitHub $MODO $DIA (v$(grep -o 'VERSAO = "[^"]*' "$RAIZ/gb.py" | cut -d'"' -f2)) → $CANAL"
grep -qx "$DIA" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
grep -qx "$DIA $MODO" "$RAIZ/auto/pular.txt" 2>/dev/null && { echo "pulado (auto/pular.txt)"; exit 0; }
[ -s "$ED/youtube-$CANAL.txt" ] && [ -z "${FORCAR:-}" ] && { echo "já publicado hoje ($(cat "$ED/youtube-$CANAL.txt")); FORCAR=1 refaz"; exit 0; }
# vídeo já feito e revisado nesta pasta: retoma sem refazer roteiro nem avatar
[ -s "$ED/video.mp4" ] && [ -s "$ED/revisao.json" ] && REUSAR=1
# avatar já enviado ao estúdio (máquina caiu no meio): mantém coleta e roteiro, senão a fala não bate com a ficha (04/11/2026)
[ -s "$ED/ficha.yaml" ] && [ -s "$ED/avatar/video_id.txt" ] && REUSAR=1
BOT="$RAIZ/bin/enviar_bot_v3.mjs"
DATA_BR=$(date -d "$DIA" +%d/%m/%Y)
avisar() {  # aviso "Falhou" no bot v3 e sai
  echo "$1" > "$ED/aviso.txt"; rm -f "$ED/aviso.txt.envio-v3.json"
  [ "${SEM_BOT:-}" = 1 ] || node "$BOT" "$ED/aviso.txt" "Falhou: Bombando no GitHub ($MODO) · $DATA_BR
$1" || echo "falhou o envio do aviso"
  echo "AVISO: $1"; exit "${2:-1}"
}

python3 "$RAIZ/auto/ia.py" validar >/dev/null || avisar "configuração de IA inválida (auto/ia.yaml)"

# 1. coleta (só GitHub)
if [ -s "$ED/pesquisa/top10.json" ] && { [ "${REUSAR:-}" = 1 ] || [ "${GB_COLETA_PRONTA:-}" = 1 ]; }; then echo "reusando a coleta"
else coletar > "$ED/pesquisa/coleta.log" 2>&1 || avisar "coleta falhou: $(tail -1 "$ED/pesquisa/coleta.log")"; fi

# 2. motor/modelo/esforço em auto/ia.yaml; referência = ficha aprovada anterior
PREV=$(ls -d "$RAIZ"/edicoes/*-"$SUF" 2>/dev/null | grep -vx "$ED" | sort | tail -1)
[ -n "$PREV" ] && [ -f "$PREV/ficha.yaml" ] || PREV="$RAIZ/modelo"
if [ -s "$ED/ficha.yaml" ] && [ "${REUSAR:-}" = 1 ] && python3 "$RAIZ/gb.py" checar "$ED" >/dev/null 2>&1; then echo "reusando ficha.yaml"
else
  rm -f "$ED/ERRO.txt" "$ED/ficha.yaml"
  N=$(python3 -c "import json;print(len(json.load(open('$ED/pesquisa/top10.json'))['top10']))")   # 5 a 10 (09/11/2026)
  PROMPT=$(sed -e "s|{ED}|$ED|g" -e "s|{PREV}|$PREV|g" -e "s|{RAIZ}|$RAIZ|g" -e "s|{DATA_BR}|$DATA_BR|g" -e "s|{MODO}|$MODO_F|g" \
               -e "s|{NOME_MODO}|$NOME_MODO|g" -e "s|{PERIODO}|$PERIODO|g" -e "s|{CRITERIO}|$CRITERIO|g" \
               -e "s|{N}|$N|g" -e "s|{N2}|$((N + 2))|g" -e "s|{N3}|$((N + 3))|g" "$RAIZ/auto/roteiro.md")
  printf '%s' "$PROMPT" | python3 "$RAIZ/auto/roteiro.py" "$ED" "$PREV" > "$ED/claude.log" 2>&1 \
    || avisar "roteirista falhou: $(tail -c 500 "$ED/claude.log")"
  [ -f "$ED/ERRO.txt" ] && avisar "o roteiro não saiu: $(head -c 400 "$ED/ERRO.txt")"
  python3 "$RAIZ/gb.py" checar "$ED" > "$ED/checar.log" 2>&1 || avisar "roteiro reprovado no portão: $(tail -c 500 "$ED/checar.log")"
fi
[ "${GB_PARAR_APOS_ROTEIRO:-}" = 1 ] && { echo "teste: parei depois do roteiro"; exit 0; }

# 3. avatar autorizado em pé (Nei, 28/10/2026: "rodar e publicar todo dia"), imagens, cena, render e revisor
[ -f "$ED/avatar/APROVADO_HEYGEN" ] || echo "Rodada diária autorizada pelo Nei em 28/10/2026 (gitbombando: rodar e publicar todo dia às 16h)." > "$ED/avatar/APROVADO_HEYGEN"
if [ -n "${AVATAR_DE:-}" ] && [ ! -s "$ED/avatar/avatar.mp4" ]; then
  [ -s "$AVATAR_DE" ] || { echo "AVATAR_DE não existe: $AVATAR_DE (nada foi gravado no HeyGen)" | tee /dev/stderr; exit 2; }
  cp "$AVATAR_DE" "$ED/avatar/avatar.mp4"
fi
veredito() { python3 -c "import json;print(json.load(open('$ED/revisao.json'))['veredito'])" 2>/dev/null; }
motivo() {  # a linha que explica a falha (22/11/2026: o aviso mandava só "Node.js v24.22.3")
  { grep -h "REPROVOU\|Error\|error" "$ED/fazer.log" | tail -1; } 2>/dev/null | grep . || tail -2 "$ED/fazer.log"
}
# até 3 tentativas para QUALQUER falha; cada uma conserta só o que falhou e segue (Nei, 22/11/2026).
# gb.py fazer pula o que já está pronto (avatar enviado/baixado, capa), e o render confere e conserta as imagens antes.
fazer() {
  for T in 1 2 3; do
    GB_TENTATIVA=$T python3 "$RAIZ/gb.py" fazer "$ED" > "$ED/fazer.log" 2>&1 && return 0
    cp "$ED/fazer.log" "$ED/fazer-t$T.log"
    echo "tentativa $T falhou: $(motivo | cut -c1-300)"
    [ "$T" = 3 ] && break
    if grep -q "estúdio" "$ED/fazer.log"; then sleep 300           # HeyGen não pegou o envio: reenvia com outro título (18/11/2026)
    elif grep -q "não fala o roteiro" "$ED/fazer.log"; then         # avatar errado: só ele é refeito, o resto fica
      mkdir -p "$ED/avatar/reprovado-t$T"; mv "$ED"/avatar/{avatar.mp4,video_id.txt,tempos.json} "$ED/avatar/reprovado-t$T/" 2>/dev/null
    else rm -f "$ED/video.mp4"; sleep 60; fi                         # render/cena/imagens: refaz a partir dali
  done
  return 1
}
V=$(veredito)
if [ "${REUSAR:-}" = 1 ] && [ "$V" = aprovado ] && [ "$ED/revisao.json" -nt "$ED/video.mp4" ]; then echo "reusando o vídeo aprovado"   # 04/11/2026
else fazer || avisar "montagem falhou depois de 3 tentativas: $(motivo | cut -c1-400)"; fi
V=$(veredito)
if [ "$V" = erro ]; then python3 "$RAIZ/gb.py" revisar "$ED" >> "$ED/fazer.log" 2>&1; V=$(veredito); fi
if [ "$V" = reprovado ]; then  # capa nova e novo render, com o mesmo avatar (Nei, 18/11/2026: "é só ajustar a capa e publicar")
  echo "revisor reprovou; refazendo com capa nova: $(python3 -c "import json;print(json.load(open('$ED/revisao.json')).get('motivo','')[:200])")"
  mkdir -p "$ED/capa/reprovada"; mv "$ED"/capa/abertura*.png "$ED/capa/reprovada/" 2>/dev/null; cp "$ED/revisao.json" "$ED/capa/reprovada/"
  fazer || avisar "montagem falhou ao refazer a capa, depois de 3 tentativas: $(motivo | cut -c1-400)"
  V=$(veredito); if [ "$V" = erro ]; then python3 "$RAIZ/gb.py" revisar "$ED" >> "$ED/fazer.log" 2>&1; V=$(veredito); fi
fi
if [ "$V" != aprovado ]; then
  rm -f "$ED/video.mp4.envio-v3.json"
  [ "${SEM_BOT:-}" = 1 ] || node "$BOT" "$ED/video.mp4" "Falhou: Bombando no GitHub ($MODO) · $DATA_BR — revisor $V, NÃO publiquei
$(python3 -c "import json;print(json.load(open('$ED/revisao.json')).get('motivo',''))")
Para publicar assim mesmo: cd $RAIZ && python3 gb.py publicar $ED"
  echo "revisor: $V"; exit 1
fi

# 4. publicar assim que fica pronto: fila do x3 (YouTube e redes) + tópico no INEMA.TOOLS; o v3 só recebe erro
python3 "$RAIZ/gb.py" publicar "$ED" > "$ED/publicar-gb.log" 2>&1 || echo "publicar saiu com erro (ver publicar-gb.log)"
tail -3 "$ED/publicar-gb.log"

# 5. git (autor inematds); mídia fica fora pelo .gitignore
if [ "${SEM_GIT:-}" != 1 ]; then
  cd "$RAIZ"
  for f in "edicoes/$DIA-$SUF"/{ficha.yaml,falas.json,revisao.json,yt.txt,telegram.md,"youtube-$CANAL.txt",pesquisa/top10.json} historico auto/telegram-topico.txt; do
    [ -e "$f" ] && git add -- "$f"
  done
  git -c user.name=inematds -c user.email=inematds@gmail.com commit -qm "Bombando no GitHub · $MODO $DATA_BR (rodada automática)" \
    && { git pull -q --rebase --autostash && git push -q && echo "push ok"; } || echo "git: nada a commitar ou falhou"
fi
echo "=== fim $(date '+%F %T')"
