#!/usr/bin/env python3
"""Coleta do carrossel "Top da área": os repositórios que mais crescem numa área (uma área por dia da semana).

uso: python3 carrossel/area.py <pasta-da-edição> [AAAA-MM-DD]
grava <pasta>/pesquisa/area.json. Só a API do GitHub (busca por tópico, via `gh api`).

Critério: repositórios criados nos últimos 120 dias (se faltar, 365), com atividade nas últimas 2 semanas,
ordenados pelas estrelas por dia desde a criação. Ficam de fora os que já saíram nessa área nas últimas 8 semanas
(historico/carrossel-area.jsonl), senão os gigantes aparecem toda semana.
"""
import base64
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
HIST = R / "historico/carrossel-area.jsonl"
QTD = 8
# conteúdo adulto/sem filtro não entra (revisor reprovou em 04/11/2026)
IMPROPRIO = re.compile(r"nsfw|uncensor|adult|porn|hentai|nude|nudify|undress|18\+|xxx|deepnude|jailbreak|sex", re.I)

# 1 = segunda … 7 = domingo (Nei, 04/11/2026: "um por dia, pegando assunto e vendo os melhores de cada um")
AREAS = {
    1: {"chave": "agentes", "nome": "AGENTES DE IA", "curto": "agentes de IA",
        "topicos": ["ai-agents", "ai-agent", "agents", "llm-agent", "multi-agent", "agentic-ai"]},
    2: {"chave": "claude-code", "nome": "CLAUDE CODE E MCP", "curto": "Claude Code, MCP e skills",
        "topicos": ["claude-code", "mcp", "model-context-protocol", "mcp-server", "claude-skills", "agent-skills"]},
    3: {"chave": "video-imagem", "nome": "IA PARA VÍDEO E IMAGEM", "curto": "vídeo e imagem com IA",
        "topicos": ["video-generation", "text-to-video", "image-generation", "text-to-speech", "comfyui", "video-editing"]},
    4: {"chave": "seguranca", "nome": "SEGURANÇA", "curto": "segurança digital",
        "topicos": ["security", "cybersecurity", "pentesting", "security-tools", "osint", "red-team"]},
    5: {"chave": "automacao", "nome": "AUTOMAÇÃO", "curto": "automação e produtividade",
        "topicos": ["automation", "workflow-automation", "productivity", "self-hosted", "browser-automation", "rpa"]},
    6: {"chave": "dev-web", "nome": "DEV WEB E APPS", "curto": "desenvolvimento web e apps",
        "topicos": ["web-development", "nextjs", "react", "frontend", "fullstack", "mobile-app"]},
    7: {"chave": "modelos-locais", "nome": "IA NO SEU PC", "curto": "modelos de IA rodando no seu computador",
        "topicos": ["local-llm", "ollama", "llama-cpp", "llm-inference", "self-hosted-ai", "on-device-ai"]},
}


def log(*a):
    print("[area]", *a, flush=True)


def gh(caminho, *extra):
    for k in range(3):
        r = subprocess.run(["gh", "api", *extra, caminho], capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            return r.stdout
        log(f"gh falhou ({r.stderr.strip()[:160]}); tentativa {k + 1}")
        time.sleep(8 * (k + 1))
    raise RuntimeError(f"gh api {caminho}")


def usados(chave, dia):
    out = set()
    if HIST.exists():
        limite = dia - dt.timedelta(weeks=8)
        for linha in HIST.read_text().splitlines():
            try:
                h = json.loads(linha)
            except ValueError:
                continue
            if h.get("area") == chave and dt.date.fromisoformat(h["dia"]) >= limite:
                out.update(h.get("repos", []))
    return out


def buscar(area, dia, dias_criado):
    desde = (dia - dt.timedelta(days=dias_criado)).isoformat()
    ativo = (dia - dt.timedelta(days=14)).isoformat()
    achados = {}
    for t in area["topicos"]:
        q = f"topic:{t} created:>={desde} pushed:>={ativo} stars:>=300 archived:false fork:false"
        try:
            j = json.loads(gh(f"search/repositories?q={q.replace(' ', '+')}&sort=stars&order=desc&per_page=30"))
        except RuntimeError as e:
            log(e); continue
        for it in j.get("items", []):
            alvo = " ".join([it["full_name"], it.get("description") or "", " ".join(it.get("topics") or [])])
            if IMPROPRIO.search(alvo):
                log(f"fora (impróprio): {it['full_name']}"); continue
            achados.setdefault(it["full_name"], it)
        time.sleep(2.5)  # busca: 30 por minuto
    return achados


def readme(nome):
    try:
        rd = json.loads(gh(f"repos/{nome}/readme"))
        txt = base64.b64decode(rd.get("content", "")).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""
    txt = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", txt)
    return re.sub(r"\n\s*\n+", "\n", txt).strip()[:2500]


def main(a):
    if not a:
        sys.exit(__doc__)
    ed = Path(a[0]); dia = dt.date.fromisoformat(a[1]) if len(a) > 1 else dt.date.today()
    area = AREAS[dia.isoweekday()]
    ja = usados(area["chave"], dia)
    log(f"{dia} · {area['nome']} · tópicos {area['topicos']} · fora {len(ja)} já usados")
    achados = {}
    for dias in (120, 365):
        achados = {k: v for k, v in buscar(area, dia, dias).items() if k not in ja}
        if len(achados) >= QTD:
            break
        log(f"só {len(achados)} com {dias} dias; ampliando")
    if len(achados) < QTD:
        sys.exit(f"só {len(achados)} repositórios na área {area['nome']}")
    hoje = dt.datetime.combine(dia, dt.time(12), dt.timezone.utc)
    itens = []
    for nome, j in achados.items():
        criado = dt.datetime.fromisoformat(j["created_at"].replace("Z", "+00:00"))
        idade = max(1.0, (hoje - criado).total_seconds() / 86400)
        itens.append({"nome": nome, "dono": j["owner"]["login"], "repo": j["name"],
                      "descricao_en": j.get("description") or "", "linguagem": j.get("language"),
                      "estrelas_total": j["stargazers_count"], "forks": j.get("forks_count"),
                      "criado_em": j["created_at"], "atualizado_em": j.get("pushed_at"), "idade_dias": round(idade),
                      "por_dia": round(j["stargazers_count"] / idade), "topicos": j.get("topics") or [],
                      "site": j.get("homepage") or None, "licenca": (j.get("license") or {}).get("spdx_id"),
                      "dono_foto": j["owner"].get("avatar_url"), "default_branch": j.get("default_branch") or "main",
                      "url": j.get("html_url")})
    itens.sort(key=lambda x: -x["por_dia"])
    top = itens[:QTD]
    for k, it in enumerate(top, 1):
        it["pos"] = k
        it["readme"] = readme(it["nome"])
        log(f"#{k} {it['nome']} · {it['estrelas_total']} estrelas · {it['por_dia']}/dia · {it['idade_dias']} dias")
    (ed / "pesquisa").mkdir(parents=True, exist_ok=True)
    out = {"tipo": "area", "dia": dia.isoformat(), "area": {k: area[k] for k in ("chave", "nome", "curto", "topicos")},
           "coletado_em": dt.datetime.now().isoformat(timespec="seconds"), "fonte": "api.github.com/search/repositories",
           "candidatos": len(itens), "itens": top}
    (ed / "pesquisa/area.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    log(f"ok: {len(top)} de {len(itens)} candidatos")


if __name__ == "__main__":
    main(sys.argv[1:])
