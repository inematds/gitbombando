#!/usr/bin/env python3
"""Teste manual real de roteiro, em pasta isolada; nunca renderiza/publica ou altera o cron.

API Anthropic exige --autorizar-api e o pedido explícito do usuário na sessão.
Não testa OpenAI/OpenRouter: não foram autorizados para chamadas reais.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import yaml

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'auto'))
from ia import carregar
from roteiro import gerar


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--motor', choices=['anthropic', 'codex'], required=True)
    ap.add_argument('--autorizar-api', action='store_true')
    ap.add_argument('--destino', type=Path, required=True)
    ap.add_argument('--modelo')
    a = ap.parse_args()
    if a.motor == 'anthropic' and not a.autorizar_api:
        ap.error('API real exige --autorizar-api e autorização explícita do usuário')
    p = a.destino.resolve()/a.motor
    p.mkdir(parents=True, exist_ok=False)
    (p/'pesquisa').mkdir()
    origem = R/'edicoes/2026-11-14-top10-dia'
    d = json.loads((origem/'pesquisa/top10.json').read_text())
    # Mesmo Top 10 e números; limitar README à amostra necessária para testar o roteiro.
    for it in d['top10']:
        it['readme'] = (it.get('readme') or '')[:1500]
    (p/'pesquisa/top10.json').write_text(json.dumps(d, ensure_ascii=False, indent=1))
    cfg = carregar()
    c = cfg['etapas']['roteiro']
    if a.motor == 'anthropic':
        c.update(tipo='api', motor='anthropic', modelo=a.modelo or 'claude-opus-5-5', esforco='low',
                 timeout=180, max_tokens=12000)
        cfg['api'].update(autorizada=True,
            autorizacao='Nei, 15/11/2026: quero que testes se ele funciona com a api do claude; somente teste isolado',
            etapas_autorizadas=['roteiro'])
    else:
        c.update(tipo='assinatura', motor='codex', modelo=a.modelo or 'gpt-6.1-sol', esforco='medium', timeout=300)
    config = p/'config-teste.yaml'
    config.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))
    os.environ['GB_IA_CONFIG'] = str(config)
    n = len(d['top10'])
    substituicoes = {'ED': str(p), 'PREV': str(origem), 'RAIZ': str(R), 'DATA_BR': '14/11/2026',
                     'MODO': 'dia', 'NOME_MODO': 'do dia', 'PERIODO': 'hoje', 'N': str(n),
                     'N2': str(n+2), 'N3': str(n+3)}
    pedido = (R/'auto/roteiro.md').read_text()
    for k, v in substituicoes.items():
        pedido = pedido.replace('{'+k+'}', v)
    report = {'data': dt.datetime.now(dt.timezone.utc).isoformat(), 'motor': a.motor,
              'modelo': c['modelo'], 'esforco': c['esforco'], 'etapa': 'roteiro',
              'pasta': str(p), 'publicacao': False, 'config_cron_alterada': False}
    inicio = time.monotonic()
    try:
        gerar(p, origem, pedido)
        f = yaml.safe_load((p/'ficha.yaml').read_text())
        report.update(status='aprovado', partes=len(f['partes']),
                      caracteres_fala=len(' '.join(x['fala'].strip() for x in f['partes'])))
    except Exception as e:
        report.update(status='falhou', erro=str(e))
    report['segundos'] = round(time.monotonic()-inicio, 2)
    (p/'resultado.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'aprovado' else 1


if __name__ == '__main__':
    sys.exit(main())
