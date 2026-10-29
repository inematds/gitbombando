#!/usr/bin/env python3
"""Retrato de hora em hora: estrelas totais dos projetos em alta (Trending do dia, da semana e do mês) → historico/estrelas.jsonl.

  python3 coleta/retrato.py            (timer gitbombando-retrato, de hora em hora)

É daqui que nasce a curva de estrelas de cada projeto no vídeo: a lista de stargazers da API do GitHub responde 404 desde
2026, então o próprio gitbombando guarda o total de cada projeto a cada hora. Uma linha por retrato:
{"t": "<ISO UTC>", "e": {"dono/repo": estrelas, ...}}. Projetos que saíram do Trending continuam sendo seguidos por 35 dias.
"""
import datetime as dt, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trending as T  # noqa: E402

H = T.R / "historico" / "estrelas.jsonl"
SEGUE_DIAS = 35


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    nomes = set()
    for modo in T.SINCE:
        try:
            nomes |= {x["nome"] for x in T.trending(modo)[:25]}
        except SystemExit as e:
            T.log(f"trending {modo}: {e}")
    if H.exists():                                     # segue também quem saiu do Trending há pouco (curva da semana/mês)
        lim = agora - dt.timedelta(days=SEGUE_DIAS)
        for ln in H.read_text().splitlines()[-24 * 7:]:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if dt.datetime.fromisoformat(r["t"]) >= lim:
                nomes |= set(r["e"])
    e = {}
    for n in sorted(nomes):
        try:
            e[n] = json.loads(T.gh(f"repos/{n}"))["stargazers_count"]
        except Exception as x:  # noqa: BLE001
            T.log(f"{n}: {x}")
    H.parent.mkdir(exist_ok=True)
    with open(H, "a") as f:
        f.write(json.dumps({"t": agora.replace(microsecond=0).isoformat(), "e": e}, ensure_ascii=False) + "\n")
    T.log(f"retrato: {len(e)} projetos")


if __name__ == "__main__":
    main()
