#!/usr/bin/env bash
# Agenda o reel do "Bombando no GitHub" no Instagram + TikTok inema.tds pelo Metricool da conta inematds
# (conector MCP "metricool-inematds", apelido "metritds"). Pedido do Nei em 01/11/2026:
# "direcione o gitbombando publicar além do lives também para o metricool-inematds".
# uso: auto/metritds.sh <pasta-da-edição>
#   publica em agora + 10 min. RASCUNHO=1 agenda como rascunho · SEM_BOT=1 não avisa no v3 · FORCAR=1 refaz.
# Vídeo público para o Metricool: anexo da release "social" do repo público inematds/gitbombando.
set -uo pipefail
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
ED="$(cd "$1" && pwd)"; V="$ED/video.mp4"
LOG="$ED/metritds.log"; exec > >(tee -a "$LOG") 2>&1
echo "== $(date '+%F %T') metritds $ED"
[ -s "$V" ] || { echo "sem video.mp4"; exit 1; }
[ -s "$ED/metritds.txt" ] && [ -z "${RASCUNHO:-}${FORCAR:-}" ] && { echo "já agendado ($(head -1 "$ED/metritds.txt")): nada a fazer"; exit 0; }

ALVO=$(( $(date +%s) + 600 ))
QUANDO_UTC=$(date -u -d "@$ALVO" +%Y-%m-%dT%H:%M:00)   # UTC: o Metricool deslocou 1 h horário local perto da meia-noite (lição do metricool-pub2)
QUANDO_BR=$(TZ=America/Sao_Paulo date -d "@$ALVO" '+%d/%m %H:%M')

# 1. link público do vídeo
NOME="gitbombando-$(basename "$ED").mp4"
gh release view social -R inematds/gitbombando >/dev/null 2>&1 || \
  gh release create social -R inematds/gitbombando --title "Vídeos para redes sociais" \
     --notes "Cópias dos reels do Bombando no GitHub usadas pelo Metricool (Instagram/TikTok inema.tds)." >/dev/null
TMP="$(mktemp -d)"; cp "$V" "$TMP/$NOME"
gh release upload social "$TMP/$NOME" -R inematds/gitbombando --clobber || { echo "Falhou: upload na release"; rm -rf "$TMP"; exit 1; }
rm -rf "$TMP"
MEDIA="https://github.com/inematds/gitbombando/releases/download/social/$NOME"

# 2. legenda: título + top 10 (yt.txt) + YouTube + hashtags
TIT=$(python3 - "$ED" <<'PY'
import sys, yaml, pathlib
print(yaml.safe_load(pathlib.Path(sys.argv[1], "ficha.yaml").read_text())["publicar"]["titulo"])
PY
)
YTID=$(head -1 "$ED/youtube-lives4.txt" 2>/dev/null)
{
  if [ -s "$ED/yt.txt" ]; then head -c 1500 "$ED/yt.txt"; else echo "$TIT"; fi
  echo
  [ -n "$YTID" ] && echo "No YouTube: https://www.youtube.com/shorts/$YTID"
  echo "Curso gratuito em inema.club"
  echo "#github #opensource #ia #programacao #inemaclub"
} > "$ED/metritds-texto.txt"

# 3. agenda pelo conector metricool-inematds (claude -p, assinatura)
PEDIDO="Use só as ferramentas do servidor MCP metricool-inematds.
1) getBrandSettings: pegue o blogId da marca (deve haver só uma, label inema.tds) e veja em networksData quais destas redes estão conectadas: tiktok, instagram.
2) createScheduledPost UMA vez, com todas as redes conectadas (das duas) em providers:
   date = ${QUANDO_UTC}Z ; publicationDate = {dateTime: \"${QUANDO_UTC}\", timezone: \"UTC\"}
   media = [\"$MEDIA\"] ; text = conteúdo exato do arquivo $ED/metritds-texto.txt (leia com a ferramenta Read)
   draft = $([ -n "${RASCUNHO:-}" ] && echo true || echo false) ; autoPublish = true
   tiktokData = {privacyOption: \"PUBLIC_TO_EVERYONE\", title: primeira linha do texto (até 90 caracteres), isAigc: true}
   instagramData (só se instagram estiver conectado) = {type: \"REEL\", showReelOnFeed: true, isAiGenerated: true}
3) Responda APENAS uma linha JSON, sem crase: {\"ok\":true|false,\"redes\":[...],\"faltam\":[redes não conectadas],\"planner\":[plannerUrl...],\"erro\":\"texto do erro ou vazio\"}"
cd "$ED"
OUT=$(printf '%s' "$PEDIDO" | timeout 600 env -u ANTHROPIC_API_KEY claude -p \
      --allowedTools "mcp__metricool-inematds__getBrandSettings mcp__metricool-inematds__createScheduledPost Read" 2>&1)
echo "claude: $OUT"
J=$(printf '%s' "$OUT" | grep -o '{.*"ok".*}' | tail -1)
campo() { printf '%s' "$J" | python3 -c "import sys,json
try: d=json.loads(sys.stdin.read())
except Exception: d={}
v=d.get('$1','');print(', '.join(v) if isinstance(v,list) else v)" 2>/dev/null; }
OK=$(printf '%s' "$J" | python3 -c 'import sys,json;print("1" if json.loads(sys.stdin.read() or "{}").get("ok") else "")' 2>/dev/null)
REDES=$(campo redes); FALTAM=$(campo faltam); PLAN=$(campo planner); ERRO=$(campo erro)

FAIXA="🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦"
if [ -n "$OK" ]; then
  [ -z "${RASCUNHO:-}" ] && printf '%s\n%s\n' "$QUANDO_BR" "$REDES" > "$ED/metritds.txt"
  MSG="$FAIXA
🔵 METRITDS: INSTAGRAM/TIKTOK inema.tds $([ -n "${RASCUNHO:-}" ] && echo '(RASCUNHO DE TESTE)')
$FAIXA
Bombando no GitHub · $TIT
Quando: $QUANDO_BR · Redes: ${REDES:-?}$([ -n "$FALTAM" ] && printf '\nAinda não conectadas: %s' "$FALTAM")
Instagram: https://www.instagram.com/inema.tds/
TikTok: https://www.tiktok.com/@inema.tds
Metricool: ${PLAN:-https://app.metricool.com/planner}"
else
  MSG="$FAIXA
⚠ METRITDS: NÃO AGENDOU (Instagram/TikTok inema.tds)
$FAIXA
Bombando no GitHub · $TIT
Erro: ${ERRO:-$(printf '%s' "$OUT" | tail -c 300)}
Log: $LOG"
fi
echo "$MSG"
if [ -z "${SEM_BOT:-}" ]; then
  CAPA="$ED/metritds-capa.jpg"
  ffmpeg -v error -y -ss 3 -i "$V" -frames:v 1 -vf scale=540:-2 "$CAPA"
  rm -f "$CAPA.envio-v3.json"
  node "$RAIZ/bin/enviar_bot_v3.mjs" "$CAPA" "$MSG" || echo "falhou o envio ao bot"
fi
[ -n "$OK" ]
