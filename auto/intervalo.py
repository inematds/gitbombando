#!/usr/bin/env python3
"""Cópia local da trava metricool-inematds (15/11/2026), com motor em ia.yaml.

Trava de 1 hora entre publicações da mesma marca no Metricool (Nei, 12/11/2026:
"não pode colocar vídeo com menos de uma hora entre publicações, a menos que eu autorize, valendo para todos").

uso: intervalo.py --conector metricool-inematds|metricool-pub2 --marca <label> --alvo <epoch> [--cwd <pasta>]
  imprime no stdout o epoch final (o próprio alvo ou o 1º horário livre depois dele, a >= 60 min de qualquer
  outro post da marca) e o motivo no stderr. Depois de agendar com sucesso, o script chamador registra o horário:
     intervalo.py --registrar --marca <label> --alvo <epoch final>
  INTERVALO_LIVRE=1  o Nei autorizou juntar: devolve o alvo sem conferir (fica registrado).
  Saída 3 = não consegui ler a agenda da marca; o chamador NÃO agenda (avisa como erro).

Fontes dos horários ocupados: getScheduledPosts da marca (o que ainda vai sair) + o registro local
~/.local/share/metricool-intervalo/<marca>.log (o que já saiu; o getScheduledPosts não mostra publicado).
"""
import argparse, datetime as dt, json, os, re, subprocess, sys
from pathlib import Path
from zoneinfo import ZoneInfo
from ia import executar as executar_ia

GAP = 3600
REG = Path.home() / ".local/share/metricool-intervalo"
CWD = {"metricool-inematds": Path.home() / "projetos/metricool-inematds",
       "metricool-pub2": Path.home() / "projetos/metricool-pub2"}


def log(msg):
    print(f"intervalo: {msg}", file=sys.stderr)


def reg_arq(chave):
    return REG / (re.sub(r"[^A-Za-z0-9._-]", "_", chave) + ".log")


def registrados(chave):
    a = reg_arq(chave)
    if not a.exists():
        return []
    out = []
    for ln in a.read_text().splitlines():
        try:
            out.append(int(ln.split()[0]))
        except Exception:
            pass
    return out


def agenda(conector, marca, alvo, cwd):
    """horários (epoch) dos posts agendados da marca entre alvo-2h e alvo+3 dias; None se falhar"""
    de = dt.datetime.fromtimestamp(alvo - 7200, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")
    ate = dt.datetime.fromtimestamp(alvo + 3 * 86400, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")
    qual = (f'a marca cujo label é exatamente "{marca}"' if marca else "a marca (deve haver só uma)")
    pedido = f"""Use só as ferramentas do servidor MCP {conector}. Só leitura: não crie, mude nem apague nada.
1) getBrandSettings: pegue o blogId e o timezone de {qual}. Se não existir, responda {{"ok":false,"erro":"marca não encontrada"}}.
2) getScheduledPosts com brandId = esse blogId, fromDate = {de}, toDate = {ate}, timezone = o da marca.
3) Responda APENAS uma linha JSON, sem crase: {{"ok":true,"posts":[{{"dateTime":"<publicationDate.dateTime exatamente como veio>","timezone":"<publicationDate.timezone exatamente como veio>"}}, ...]}}
   (lista vazia se não houver nenhum; inclua rascunhos também)."""
    tools = f"mcp__{conector}__getBrandSettings mcp__{conector}__getScheduledPosts"
    for tentativa in (1, 2):
        try:
            resposta = executar_ia("metricool_agenda", pedido, cwd, agente=True, ferramentas=tools)
        except Exception as e:
            log(f"claude -p falhou: {e}")
            continue
        m = re.findall(r'\{.*"ok".*\}', resposta)
        try:
            d = json.loads(m[-1])
        except Exception:
            log(f"resposta sem JSON (tentativa {tentativa}): {resposta.strip()[-200:]}")
            continue
        if not d.get("ok"):
            log(f"não leu a agenda: {d.get('erro')}")
            continue
        out = []
        for p in d.get("posts", []):
            try:
                t = dt.datetime.fromisoformat(p["dateTime"].replace("Z", ""))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=ZoneInfo(p.get("timezone") or "UTC"))
                out.append(int(t.timestamp()))
            except Exception:
                log(f"horário ilegível ignorado: {p}")
        return out
    return None


def livre(alvo, ocupados):
    t = alvo
    while True:
        perto = [p for p in ocupados if abs(p - t) < GAP]
        if not perto:
            return t
        t = max(perto) + GAP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conector", default="metricool-inematds")
    ap.add_argument("--marca", default="")
    ap.add_argument("--alvo", type=int, required=True)
    ap.add_argument("--cwd")
    ap.add_argument("--registrar", action="store_true")
    a = ap.parse_args()
    chave = a.marca or a.conector   # marca única do conector (pub2) = nome do conector
    if a.registrar:
        REG.mkdir(parents=True, exist_ok=True)
        with reg_arq(chave).open("a") as f:
            f.write(f"{a.alvo} {dt.datetime.fromtimestamp(a.alvo):%F %H:%M}"
                    f"{' livre' if os.environ.get('INTERVALO_LIVRE') else ''}\n")
        return 0
    br = lambda e: dt.datetime.fromtimestamp(e, ZoneInfo("America/Sao_Paulo")).strftime("%d/%m %H:%M")
    if os.environ.get("INTERVALO_LIVRE"):
        log(f"INTERVALO_LIVRE=1 (Nei autorizou): {br(a.alvo)} sem conferir")
        print(a.alvo)
        return 0
    ag = agenda(a.conector, a.marca, a.alvo, a.cwd or str(CWD.get(a.conector, Path.cwd())))
    if ag is None:
        log("não consegui ler a agenda: não agendar")
        return 3
    t = livre(a.alvo, ag + registrados(chave))
    log(f"{a.marca or a.conector}: {br(a.alvo)} ok" if t == a.alvo
        else f"{a.marca or a.conector}: {br(a.alvo)} a menos de 1 h de outro post → {br(t)}")
    print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
