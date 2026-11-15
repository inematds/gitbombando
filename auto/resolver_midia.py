#!/usr/bin/env python3
"""Resolve o redirecionamento público da release antes de o Metricool baixar a mídia.
A URL final pode conter assinatura temporária; imprimir só para captura pelo chamador.
"""
import sys
import urllib.request


def resolver(url):
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'gitbombando-publicacao'})
    with urllib.request.urlopen(req, timeout=30) as response:
        destino = response.geturl()
        if response.status != 200 or not destino.startswith('https://'):
            raise ValueError('Mídia pública indisponível')
        return destino


if __name__ == '__main__':
    try:
        print(resolver(sys.argv[1]))
    except Exception:
        print('Falha ao resolver a mídia pública; nenhuma publicação criada.', file=sys.stderr)
        sys.exit(1)
