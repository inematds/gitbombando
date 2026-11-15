#!/usr/bin/env python3
"""Salva roteiro e devolve erros do portão ao modelo; no máximo duas tentativas."""
import json
from pathlib import Path
import subprocess
import sys
import yaml
from ia import executar, RAIZ


def gerar(pasta, anterior, pedido):
    p = Path(pasta).resolve()
    arquivos = [p/'pesquisa/top10.json', Path(anterior)/'ficha.yaml']
    extra = ''
    for _ in range(2):
        texto = executar('roteiro', pedido + extra, p, arquivos=arquivos)
        try:
            ficha = yaml.safe_load(texto)
            if not isinstance(ficha, dict):
                raise ValueError('O roteiro deve ser um objeto YAML')
            (p/'ficha.yaml').write_text(yaml.safe_dump(ficha, allow_unicode=True, sort_keys=False))
            r = subprocess.run([sys.executable, str(RAIZ/'gb.py'), 'checar', str(p)],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                print(r.stdout)
                return
            erro = r.stdout + r.stderr
        except yaml.YAMLError:
            erro = 'Resposta não é YAML válido'
        except ValueError as e:
            erro = str(e)
        extra = '\n\nCorrija o roteiro anterior abaixo segundo o portão.\n' + texto + '\nErros:\n' + erro[-5000:]
    raise ValueError('Roteiro reprovado após duas tentativas: ' + erro[-1000:])


if __name__ == '__main__':
    try:
        gerar(sys.argv[1], sys.argv[2], sys.stdin.read())
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
