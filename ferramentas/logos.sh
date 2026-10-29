#!/usr/bin/env bash
# Baixa o pacote de logos de IA/tecnologia (MIT, @lobehub/icons-static-png) para ~/.cache/r7ex/lobe-icons (D13, 20/10/2026).
set -euo pipefail
D=~/.cache/r7ex/lobe-icons; T=$(mktemp -d); cd "$T"
npm pack @lobehub/icons-static-png@1.97.1 --silent >/dev/null && tar xzf lobehub-icons-static-png-*.tgz
mkdir -p "$D" && rm -rf "$D/dark" && cp -r package/dark package/package.json "$D/" && rm -rf "$T"
echo "logos em $D/dark ($(ls "$D/dark" | wc -l) arquivos)"
# Linguagens/ferramentas fora do lobe-icons (21/10/2026): simple-icons (CC0) → <id>-color.png na cor da marca (rust em branco)
T=$(mktemp -d); cd "$T"; npm pack simple-icons@13.21.0 --silent >/dev/null && tar xzf simple-icons-*.tgz
python3 - "$D" <<'PY'
import sys, cairosvg, pathlib
D = pathlib.Path(sys.argv[1])
for n, c in {"pydantic": "#E92063", "polars": "#CD792C", "ruff": "#D7FF64", "uv": "#DE5FE9", "python": "#3776AB", "typescript": "#3178C6", "rust": "#FFFFFF", "php": "#777BB4"}.items():
    svg = open(f"package/icons/{n}.svg").read().replace("<svg ", f'<svg fill="{c}" ', 1)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(D / "dark" / (f"{n}.png" if n == "rust" else f"{n}-color.png")), output_width=512, output_height=512)
PY
rm -rf "$T"; echo "logos simple-icons adicionados"
