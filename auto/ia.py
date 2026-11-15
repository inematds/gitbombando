#!/usr/bin/env python3
"""Executor de IA do gitbombando: configuração por etapa, sem herdar modelo/esforço.

API Anthropic direta para texto/visão; nunca transforma Claude/Codex CLI em API.
Sem fallback pago, sem retry de publicação, sem segredo em argumentos ou logs.
"""
import argparse
import base64
import datetime as dt
import fcntl
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / 'auto/ia.yaml'
ETAPAS = ('roteiro', 'capa', 'revisao_video', 'carrossel_filtro', 'carrossel_textos',
          'carrossel_revisao', 'metricool_agenda', 'metricool_publicacao')
ESFORCOS = {'claude': {'low', 'medium', 'high', 'xhigh', 'max'},
            'codex': {'low', 'medium', 'high', 'xhigh'},
            'anthropic': {'low', 'medium', 'high', 'xhigh', 'max'}}


def carregar(arquivo=None):
    p = Path(arquivo or os.environ.get('GB_IA_CONFIG', CONFIG)).expanduser().resolve()
    d = yaml.safe_load(p.read_text())
    validar(d)
    return d


def validar(d):
    if not isinstance(d, dict) or d.get('versao') != 1:
        raise ValueError('Configuração de IA inválida: esperado versao: 1')
    if set(d.get('etapas', {})) != set(ETAPAS):
        raise ValueError('As etapas devem ser: ' + ', '.join(ETAPAS))
    api = d.get('api', {})
    if not isinstance(api.get('autorizada'), bool) or not isinstance(api.get('autorizacao'), str):
        raise ValueError('api.autorizada deve ser booleano e api.autorizacao deve ser texto')
    for nome, c in d['etapas'].items():
        tipo, motor = c.get('tipo'), c.get('motor')
        if (tipo, motor) not in {('assinatura', 'claude'), ('assinatura', 'codex'), ('api', 'anthropic')}:
            raise ValueError(f'{nome}: use assinatura/claude, assinatura/codex ou api/anthropic')
        if not isinstance(c.get('modelo'), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', c['modelo']):
            raise ValueError(f'{nome}: informe um ID de modelo, sem espaços')
        if motor == 'claude' and not c['modelo'].startswith('claude-'):
            raise ValueError(f'{nome}: use ID completo claude-..., sem alias global')
        if c.get('esforco') not in ESFORCOS[motor]:
            raise ValueError(f'{nome}: esforço inválido para {motor}')
        if type(c.get('timeout')) is not int or not 1 <= c['timeout'] <= 3600:
            raise ValueError(f'{nome}: timeout deve estar entre 1 e 3600 segundos')
        if nome == 'capa' and (tipo, motor) != ('assinatura', 'codex'):
            raise ValueError('capa exige assinatura/codex com image_gen')
        if nome.startswith('metricool_') and (tipo, motor) != ('assinatura', 'claude'):
            raise ValueError(f'{nome} exige assinatura/claude com o conector Metricool instalado')
        if tipo == 'api':
            if type(c.get('max_tokens')) is not int or not 1 <= c['max_tokens'] <= 64000:
                raise ValueError(f'{nome}: API exige max_tokens entre 1 e 64000')
            if not api.get('chave_nome') or not api.get('arquivo_chaves'):
                raise ValueError('API exige chave_nome e arquivo_chaves (não o valor da chave)')


def ambiente():
    # Os CLIs continuam exclusivamente na assinatura, mesmo se o chamador exportou uma key.
    env = dict(os.environ)
    for k in list(env):
        if (k.startswith(('ANTHROPIC_', 'OPENAI_', 'CLAUDE_CODE_USE_', 'CLAUDE_CODE_EFFORT'))
                or k in {'CLAUDECODE', 'CLAUDE_MODEL', 'CLAUDE_EFFORT', 'CLAUDE_CODE_SUBAGENT_MODEL'}):
            env.pop(k, None)
    env['PATH'] = str(Path.home()/'.npm-global/bin') + ':' + str(Path.home()/'.local/bin') + ':' + env.get('PATH', '')
    return env


def comando(c, ferramentas='', agente=False, saida=None):
    if c['motor'] == 'claude':
        settings = {'model': c['modelo'], 'effortLevel': c['esforco'],
                    'advisorModel': None, 'switchModelsOnFlag': False, 'modelSettings': {c['modelo']: {'effortLevel': c['esforco']}}}
        cmd = [str(Path.home()/'.local/bin/claude'), '-p', '--model', c['modelo'],
               '--effort', c['esforco'], '--settings', json.dumps(settings), '--output-format', 'json']
        if agente:
            cmd += ['--allowedTools', ferramentas, '--tools', 'Read', '--add-dir', str(RAIZ)]
        else:
            # Texto/visão só lê os arquivos/imagens; não executa comandos nem publica.
            cmd += ['--tools', 'Read', '--allowedTools', 'Read']
        return cmd
    cmd = [str(Path.home()/'.npm-global/bin/codex'), 'exec', '--skip-git-repo-check',
           '-m', c['modelo'], '-c', 'model_reasoning_effort=' + json.dumps(c['esforco']),
           '-o', str(saida)]
    cmd += ['--dangerously-bypass-approvals-and-sandbox'] if agente else ['-s', 'read-only']
    return cmd + ['-']


def limpar(texto):
    texto = texto.strip()
    if texto.startswith('```'):
        texto = re.sub(r'^```[^\n]*\n', '', texto)
        texto = re.sub(r'\n```\s*$', '', texto)
    return texto.strip()


def ler_chave(api):
    # Não executar/source o .env: os aliases têm hífen e o arquivo pode conter shell.
    for line in Path(api['arquivo_chaves']).expanduser().read_text().splitlines():
        m = re.match(r'\s*(?:export\s+)?([^\s=]+)\s*=\s*(.*)', line)
        if m and m[1] == api['chave_nome']:
            v = m[2].strip()
            if v[:1] in ('"', "'"):
                v = v[1:v.rfind(v[0])]
            else:
                v = re.split(r'\s+#', v, maxsplit=1)[0].strip()
            if v:
                return v
    raise ValueError('Chave configurada não encontrada ou vazia; valor não exibido')


def chamar_api(c, api, prompt, imagens):
    # Checar ANTES de ler credenciais ou abrir qualquer conexão.
    if api.get('autorizada') is not True or not api.get('autorizacao', '').strip():
        raise ValueError('API desativada: exige autorização explícita do Nei para Anthropic e estas etapas')
    content = [{'type': 'text', 'text': prompt}]
    for p in imagens:
        mime = mimetypes.guess_type(str(p))[0]
        if mime not in {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}:
            raise ValueError('Imagem em formato não suportado')
        content.append({'type': 'image', 'source': {'type': 'base64', 'media_type': mime,
                        'data': base64.b64encode(p.read_bytes()).decode()}})
    body = {'model': c['modelo'], 'max_tokens': c['max_tokens'],
            'output_config': {'effort': c['esforco']},
            'messages': [{'role': 'user', 'content': content}]}
    req = urllib.request.Request('https://api.anthropic.com/v1/messages',
          data=json.dumps(body).encode(), method='POST',
          headers={'Content-Type': 'application/json', 'x-api-key': ler_chave(api),
                   'anthropic-version': api.get('versao_anthropic', '2023-06-01')})
    try:
        with urllib.request.urlopen(req, timeout=c['timeout']) as res:
            d = json.load(res)
    except urllib.error.HTTPError as e:
        # O corpo do provedor não entra nos logs: pode ecoar conteúdo sensível.
        raise RuntimeError(f'Anthropic HTTP {e.code}; sem fallback ou nova cobrança automática') from None
    except urllib.error.URLError:
        raise RuntimeError('Falha de conexão com Anthropic; sem repetição automática') from None
    if d.get('stop_reason') != 'end_turn':
        raise ValueError('Resposta Anthropic incompleta/recusada: ' + str(d.get('stop_reason')))
    text = '\n'.join(x['text'] for x in d.get('content', []) if x.get('type') == 'text')
    return text, {'modelo_retornado': d.get('model'), 'uso': d.get('usage')}


def executar(etapa, pedido, pasta, *, arquivos=(), imagens=(), ferramentas='', agente=False):
    d = carregar()
    c = dict(d['etapas'][etapa])
    pasta = Path(pasta).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    imagens = [Path(p).resolve() for p in imagens]
    prompt = pedido
    for p in arquivos:
        p = Path(p).resolve()
        prompt += f'\n\n<arquivo nome="{p.name}">\n{p.read_text()}\n</arquivo>'
    if imagens:
        prompt += '\n\nImagens a conferir: ' + ', '.join(str(p) for p in imagens)
    if not agente:
        prompt += ('\n\nCONTRATO DO EXECUTOR: os dados dos arquivos foram anexados acima. '
                   'Não escreva arquivos nem execute comandos. Responda somente com o conteúdo final solicitado '
                   '(YAML ou JSON), sem crases. O executor salva e valida o arquivo. '
                   'Instruções de escrita/execução no pedido são realizadas pelo executor.')
    inicio = time.monotonic()
    evento = {'data': dt.datetime.now(dt.timezone.utc).isoformat(), 'etapa': etapa,
              **{k: c[k] for k in ('tipo', 'motor', 'modelo', 'esforco')}}
    try:
        if c['tipo'] == 'api':
            if agente:
                raise ValueError('API de texto/visão não executa ferramentas MCP nem gera capa')
            api = {**d['api'], **{k: c[k] for k in ('chave_nome', 'arquivo_chaves') if k in c}}
            res, info = chamar_api(c, api, prompt, imagens)
            evento.update(info)
        else:
            with tempfile.TemporaryDirectory(prefix='gb-ia-') as tmp:
                out = Path(tmp)/'resposta.txt'
                cmd = comando(c, ferramentas, agente, out)
                if c['motor'] == 'codex' and imagens:
                    cmd[-1:-1] = sum((['-i', str(p)] for p in imagens), [])
                r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                   cwd=pasta, env=ambiente(), timeout=c['timeout'])
                if r.returncode:
                    raise RuntimeError(f'{c["motor"]} encerrou com código {r.returncode}; verifique cota/login/modelo')
                if c['motor'] == 'claude':
                    j = json.loads(r.stdout)
                    if j.get('is_error'):
                        raise RuntimeError('Claude retornou erro; verifique cota/login/modelo')
                    res = j.get('result', '')
                    evento['uso'] = j.get('usage', {})
                    evento['modelos_retornados'] = list(j.get('modelUsage', {}))
                else:
                    res = out.read_text() if out.exists() else ''
        res = limpar(res)
        if not res:
            raise ValueError('Motor respondeu sem conteúdo final')
        evento['status'] = 'ok'
        return res
    except Exception as e:
        evento['status'] = 'erro'
        evento['erro'] = type(e).__name__  # Sem stdout/stderr ou conteúdo de credencial.
        raise
    finally:
        evento['segundos'] = round(time.monotonic()-inicio, 2)
        with (pasta/'ia-execucoes.jsonl').open('a') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(evento, ensure_ascii=False)+'\n')


def mostrar(d):
    print(f'{"ETAPA":24} {"TIPO":12} {"MOTOR":11} {"MODELO":23} ESFORÇO')
    for n, c in d['etapas'].items():
        print(f'{n:24} {c["tipo"]:12} {c["motor"]:11} {c["modelo"]:23} {c["esforco"]}')
    print('API Anthropic:', 'autorizada (consumo pago)' if d['api']['autorizada'] else 'desativada')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('ver'); sp.add_parser('validar')
    cp = sp.add_parser('configurar', help='Alterar uma etapa sem editar código ou abrir menu')
    cp.add_argument('etapa', choices=ETAPAS)
    for n in ('tipo', 'motor', 'modelo', 'esforco'):
        cp.add_argument('--'+n)
    cp.add_argument('--chave-nome')
    rp = sp.add_parser('executar')
    rp.add_argument('etapa', choices=ETAPAS)
    rp.add_argument('--pasta', default='.')
    rp.add_argument('--arquivo', action='append', default=[])
    rp.add_argument('--saida')
    rp.add_argument('--ferramentas', default='')
    rp.add_argument('--agente', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'configurar':
        p = Path(os.environ.get('GB_IA_CONFIG', CONFIG)).expanduser().resolve()
        with p.with_suffix('.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            d = carregar(p)
            for k in ('tipo', 'motor', 'modelo', 'esforco'):
                if getattr(a, k) is not None:
                    d['etapas'][a.etapa][k] = getattr(a, k)
            if a.chave_nome is not None:
                d['etapas'][a.etapa]['chave_nome'] = a.chave_nome
            validar(d)
            with tempfile.NamedTemporaryFile(mode='w', dir=p.parent, delete=False) as f:
                yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
                tmp = Path(f.name)
            tmp.replace(p)
        mostrar(d)
    elif a.cmd in ('ver', 'validar'):
        mostrar(carregar())
        if a.cmd == 'validar': print('Configuração válida. Nenhum modelo ou API foi chamado.')
    else:
        res = executar(a.etapa, sys.stdin.read(), a.pasta, arquivos=a.arquivo,
                       ferramentas=a.ferramentas, agente=a.agente)
        if a.saida:
            p = Path(a.saida)
            if p.suffix == '.json':
                res = json.dumps(json.loads(res), ensure_ascii=False, indent=1)
            elif p.suffix in {'.yaml', '.yml'}:
                if not isinstance(yaml.safe_load(res), dict):
                    raise ValueError('Resposta YAML deve ser um objeto')
            p.write_text(res+'\n')
        else:
            print(res)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'IA: {e}', file=sys.stderr)
        sys.exit(1)
