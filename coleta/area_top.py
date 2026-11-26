#!/usr/bin/env python3
"""Top 5 por assunto, no formato do reel e do carrossel → <pasta>/pesquisa/top10.json (grade do Nei, 18/11/2026).

  python3 coleta/area_top.py <pasta> area|agentes [AAAA-MM-DD]

area    = a área do dia da semana (carrossel/area.py); na segunda, automação, porque agentes já tem horário próprio.
agentes = sempre sistemas de agentes e parecidos.
Critério: estrelas por dia desde a criação. Quem saiu na mesma área nas últimas 8 semanas fica de fora.
"""
import datetime as dt
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
from carrossel import area as A  # noqa: E402

QTD = 5
AGENTES = {"chave": "sistemas-agentes", "nome": "SISTEMAS DE AGENTES", "curto": "sistemas de agentes de IA",
           "topicos": ["ai-agents", "multi-agent", "agentic-ai", "agent-framework", "multi-agent-systems", "llm-agent"]}


def escolher(tipo, dia):
    if tipo == "agentes":
        return AGENTES
    semana = dia.isoweekday()
    return A.AREAS[5 if semana == 1 else semana]


def main(a):
    if len(a) < 2 or a[1] not in ("area", "agentes"):
        sys.exit(__doc__)
    ed = Path(a[0]).resolve(); dia = dt.date.fromisoformat(a[2]) if len(a) > 2 else dt.date.today()
    r = A.coletar(escolher(a[1], dia), dia, ed, QTD)
    for it in r["itens"]:
        it["estrelas_periodo"] = it["por_dia"]
    out = {"modo": "area", "periodo": "per day", "coletado_em": r["coletado_em"], "dia": r["dia"], "area": r["area"],
           "fonte": "https://github.com/topics", "top10": r["itens"], "soma_periodo": sum(x["por_dia"] for x in r["itens"])}
    (ed / "pesquisa").mkdir(parents=True, exist_ok=True)
    (ed / "pesquisa/top10.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    A.log("ok", ed / "pesquisa/top10.json")


if __name__ == "__main__":
    main(sys.argv[1:])
