"""Teste de contratos reais do fluxo, sem rede, geração de mídia ou publicação."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
sys.path.insert(0, str(R/'auto'))
from auto import ia
from auto import roteiro


def modulo(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ContratosIA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        self.cfg = copy.deepcopy(ia.carregar(R/'auto/ia.yaml'))
        for nome, c in self.cfg['etapas'].items():
            c.update(tipo='assinatura', motor='codex' if nome == 'capa' else 'claude',
                     modelo='gpt-6.1-sol' if nome == 'capa' else 'claude-opus-5-5',
                     esforco='medium' if nome in ('capa', 'revisao_video', 'carrossel_revisao') else 'low')
        self.cfg['api'].update(autorizada=False, autorizacao='')
        self.cfg['api'].pop('etapas_autorizadas', None)
        self.path = self.p/'ia.yaml'
        self.salvar()
        self.env = patch.dict(os.environ, {'GB_IA_CONFIG': str(self.path)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def salvar(self):
        self.path.write_text(yaml.safe_dump(self.cfg))

    def test_assinatura_independente_dos_modelos_e_chaves_globais(self):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'segredo-teste', 'OPENAI_API_KEY': 'segredo-teste',
                                     'ANTHROPIC_MODEL': 'outro', 'CLAUDE_CODE_EFFORT_LEVEL': 'high'}):
            def executar(cmd, **kwargs):
                self.assertEqual(cmd[cmd.index('--model')+1], 'claude-opus-5-5')
                self.assertEqual(cmd[cmd.index('--effort')+1], 'low')
                self.assertNotIn('ANTHROPIC_API_KEY', kwargs['env'])
                self.assertNotIn('OPENAI_API_KEY', kwargs['env'])
                self.assertNotIn('ANTHROPIC_MODEL', kwargs['env'])
                self.assertNotIn('CLAUDE_CODE_EFFORT_LEVEL', kwargs['env'])
                self.assertEqual(kwargs['cwd'], self.p)
                return subprocess.CompletedProcess(cmd, 0, json.dumps({'result': '{"ok":true}',
                                    'modelUsage': {'claude-opus-5-5': {}}, 'usage': {}}), '')
            with patch.object(ia.subprocess, 'run', side_effect=executar):
                self.assertEqual(json.loads(ia.executar('roteiro', 'responda JSON', self.p)), {'ok': True})
        evento = json.loads((self.p/'ia-execucoes.jsonl').read_text())
        self.assertEqual(evento['modelo'], 'claude-opus-5-5')
        self.assertEqual(evento['status'], 'ok')
        self.assertNotIn('segredo-teste', (self.p/'ia-execucoes.jsonl').read_text())

    def test_trocar_uma_etapa_nao_altera_outras_nem_faz_chamada(self):
        antes = copy.deepcopy(self.cfg['etapas'])
        with patch.object(sys, 'argv', ['ia', 'configurar', 'roteiro', '--tipo', 'assinatura',
                          '--motor', 'codex', '--modelo', 'gpt-6.1-sol', '--esforco', 'high']), \
             patch.object(ia.subprocess, 'run') as run, patch.object(sys, 'stdout', io.StringIO()):
            ia.main()
            run.assert_not_called()
        depois = ia.carregar(self.path)
        self.assertEqual(depois['etapas']['roteiro']['motor'], 'codex')
        for etapa in antes:
            if etapa != 'roteiro': self.assertEqual(antes[etapa], depois['etapas'][etapa])

    def test_configuracao_invalida_nao_sobrescreve_arquivo(self):
        antes = self.path.read_bytes()
        with patch.object(sys, 'argv', ['ia', 'configurar', 'capa', '--motor', 'claude']), \
             self.assertRaisesRegex(ValueError, 'capa|ID completo'):
            ia.main()
        self.assertEqual(antes, self.path.read_bytes())

    def test_codex_recebe_esforco_imagens_e_resposta_final(self):
        self.cfg['etapas']['revisao_video'].update(motor='codex', modelo='gpt-6.1-sol', esforco='high')
        self.salvar()
        image = self.p/'folha.png'; image.write_bytes(b'fake')
        def executar(cmd, **kwargs):
            self.assertIn('model_reasoning_effort="high"', cmd)
            self.assertEqual(cmd[cmd.index('-m')+1], 'gpt-6.1-sol')
            self.assertIn(str(image), cmd)
            self.assertIn('read-only', cmd)
            Path(cmd[cmd.index('-o')+1]).write_text('{"veredito":"aprovado"}')
            return subprocess.CompletedProcess(cmd, 0, 'eventos nao sao a resposta', '')
        with patch.object(ia.subprocess, 'run', side_effect=executar):
            res = ia.executar('revisao_video', 'revise', self.p, imagens=[image])
        self.assertEqual(json.loads(res)['veredito'], 'aprovado')

    def test_api_bloqueada_antes_de_ler_chave_ou_conectar(self):
        self.cfg['etapas']['roteiro'].update(tipo='api', motor='anthropic')
        self.salvar()
        with patch.object(ia, 'ler_chave') as key, patch.object(ia.urllib.request, 'urlopen') as net, \
             self.assertRaisesRegex(ValueError, 'API desativada'):
            ia.executar('roteiro', 'teste', self.p)
        key.assert_not_called(); net.assert_not_called()
        self.assertEqual(json.loads((self.p/'ia-execucoes.jsonl').read_text())['status'], 'erro')

    def test_api_texto_visao_esforco_e_alias_da_chave(self):
        keyfile = self.p/'secrets.env'; keyfile.write_text('nome-com-hifen="chave-simulada"\n')
        self.cfg['api'].update(autorizada=True, autorizacao='Autorização FICTÍCIA só para teste sem rede',
                              arquivo_chaves=str(keyfile), chave_nome='nome-com-hifen')
        self.cfg['etapas']['revisao_video'].update(tipo='api', motor='anthropic', esforco='high')
        self.salvar()
        image = self.p/'folha.png'; image.write_bytes(b'fake')
        data = self.p/'numeros.json'; data.write_text('{"total":10}')
        def resposta(req, timeout):
            body = json.loads(req.data)
            self.assertEqual(body['output_config'], {'effort': 'high'})
            self.assertEqual(body['model'], 'claude-opus-5-5')
            self.assertEqual(req.get_header('X-api-key'), 'chave-simulada')
            self.assertEqual(body['messages'][0]['content'][1]['type'], 'image')
            self.assertIn('"total":10', body['messages'][0]['content'][0]['text'])
            return io.BytesIO(json.dumps({'model': 'claude-opus-5-5', 'stop_reason': 'end_turn',
                  'content': [{'type': 'text', 'text': '{"veredito":"aprovado"}'}],
                  'usage': {'output_tokens': 20}}).encode())
        with patch.object(ia.urllib.request, 'urlopen', side_effect=resposta):
            res = ia.executar('revisao_video', 'olhe', self.p, arquivos=[data], imagens=[image])
        self.assertEqual(json.loads(res)['veredito'], 'aprovado')
        self.assertNotIn('chave-simulada', (self.p/'ia-execucoes.jsonl').read_text())

    def test_api_truncada_e_recusada_sem_retry(self):
        c = {**self.cfg['etapas']['roteiro'], 'motor': 'anthropic'}
        with patch.object(ia, 'ler_chave', return_value='teste'), \
             patch.object(ia.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps({
                 'stop_reason': 'max_tokens', 'content': [{'type': 'text', 'text': 'parcial'}]}).encode())) as net, \
             self.assertRaisesRegex(ValueError, 'incompleta'):
            ia.chamar_api(c, {**self.cfg['api'], 'autorizada': True, 'autorizacao': 'teste sem rede'}, 'teste', [])
        self.assertEqual(net.call_count, 1)

    def test_configurar_preserva_documentacao_com_hash_e_comentario_inline(self):
        texto = (R/'auto/ia.yaml').read_text().replace('\n    esforco: low\n', '\n    esforco: low # ajuste simples\n', 1)
        self.path.write_text(texto)
        comentarios = [l.lstrip() for l in texto.splitlines() if l.lstrip().startswith('#')]
        with patch.object(sys, 'argv', ['ia', 'configurar', 'roteiro', '--esforco', 'high',
                                       '--chave-nome', 'alias-com-hifen']), \
             patch.object(sys, 'stdout', io.StringIO()):
            ia.main()
        atual = self.path.read_text()
        self.assertEqual(comentarios, [l.lstrip() for l in atual.splitlines() if l.lstrip().startswith('#')])
        self.assertIn('esforco: "high" # ajuste simples', atual)
        self.assertEqual(ia.carregar(self.path)['etapas']['roteiro']['chave_nome'], 'alias-com-hifen')

    def test_autorizacao_anthropic_nao_autoriza_openai_ou_openrouter(self):
        self.cfg['api'].update(autorizada=True, autorizacao='somente Anthropic')
        for motor in ('openai', 'openrouter'):
            with self.subTest(motor=motor):
                self.cfg['etapas']['roteiro'].update(tipo='api', motor=motor, modelo='modelo-exemplo')
                self.salvar()
                with patch.object(ia, 'ler_chave') as key, patch.object(ia.urllib.request, 'urlopen') as net, \
                     self.assertRaisesRegex(ValueError, 'API desativada'):
                    ia.executar('roteiro', 'teste', self.p)
                key.assert_not_called(); net.assert_not_called()

    def test_api_recusa_etapa_fora_do_escopo_autorizado(self):
        c = {**self.cfg['etapas']['roteiro'], 'motor': 'anthropic', '_etapa': 'roteiro'}
        api = {**self.cfg['api'], 'autorizada': True, 'autorizacao': 'somente teste de filtro',
               'etapas_autorizadas': ['carrossel_filtro']}
        with patch.object(ia, 'ler_chave') as key, self.assertRaisesRegex(ValueError, 'esta etapa'):
            ia.chamar_api(c, api, 'teste', [])
        key.assert_not_called()

    def test_api_openai_responses_texto_visao_e_esforco(self):
        c = {**self.cfg['etapas']['revisao_video'], 'motor': 'openai', 'modelo': 'modelo-openai'}
        api = {'autorizada': True, 'autorizacao': 'FICTÍCIA, teste sem rede'}
        imagem = self.p/'imagem.png'; imagem.write_bytes(b'fake')
        def resposta(req, timeout):
            body = json.loads(req.data)
            self.assertEqual(req.full_url, 'https://api.openai.com/v1/responses')
            self.assertEqual(req.get_header('Authorization'), 'Bearer fake')
            self.assertEqual(body['reasoning']['effort'], 'medium')
            self.assertEqual(body['max_output_tokens'], c['max_tokens'])
            self.assertFalse(body['store'])
            self.assertEqual(body['input'][0]['content'][1]['type'], 'input_image')
            return io.BytesIO(json.dumps({'status': 'completed', 'model': c['modelo'],
                    'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{"ok":true}'}]}],
                    'usage': {'input_tokens': 30, 'output_tokens': 10}}).encode())
        with patch.object(ia, 'ler_chave', return_value='fake'), \
             patch.object(ia.urllib.request, 'urlopen', side_effect=resposta):
            res, info = ia.chamar_api(c, api, 'teste', [imagem])
        self.assertEqual(json.loads(res), {'ok': True})
        self.assertEqual(info['modelo_retornado'], c['modelo'])

    def test_api_openrouter_envia_slug_esforco_e_desliga_fallback(self):
        c = {**self.cfg['etapas']['roteiro'], 'motor': 'openrouter', 'modelo': 'anthropic/claude-opus-5.5'}
        api = {'autorizada': True, 'autorizacao': 'FICTÍCIA, teste sem rede'}
        def resposta(req, timeout):
            body = json.loads(req.data)
            self.assertEqual(req.full_url, 'https://openrouter.ai/api/v1/chat/completions')
            self.assertEqual(body['model'], c['modelo'])
            self.assertEqual(body['reasoning'], {'effort': 'low', 'exclude': True})
            self.assertFalse(body['provider']['allow_fallbacks'])
            self.assertTrue(body['provider']['require_parameters'])
            return io.BytesIO(json.dumps({'model': c['modelo'], 'choices': [
                       {'finish_reason': 'stop', 'message': {'content': '{"ok":true}'}}]}).encode())
        with patch.object(ia, 'ler_chave', return_value='fake'), \
             patch.object(ia.urllib.request, 'urlopen', side_effect=resposta):
            res, _ = ia.chamar_api(c, api, 'teste', [])
        self.assertEqual(json.loads(res), {'ok': True})

    def test_openai_e_openrouter_recusam_resposta_incompleta(self):
        casos = [('openai', {'status': 'incomplete', 'output': []}),
                 ('openrouter', {'choices': [{'finish_reason': 'length', 'message': {'content': 'parcial'}}]})]
        for motor, body in casos:
            with self.subTest(motor=motor), patch.object(ia, 'ler_chave', return_value='fake'), \
                 patch.object(ia.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(body).encode())), \
                 self.assertRaisesRegex(ValueError, 'incompleta'):
                ia.chamar_api({**self.cfg['etapas']['roteiro'], 'motor': motor},
                             {'autorizada': True, 'autorizacao': 'FICTÍCIA, sem rede'}, 'teste', [])


    def test_metricool_codex_limita_conector_e_ferramentas_sem_shell_livre(self):
        home = self.p/'codex-home'; home.mkdir()
        (home/'config.toml').write_text('[mcp_servers.metricool-inematds]\nurl="https://ai.metricool.com/mcp"\n[mcp_servers.metricool]\nurl="https://ai.metricool.com/mcp"\n')
        c = {**self.cfg['etapas']['metricool_agenda'], 'motor': 'codex', 'modelo': 'gpt-6.1-sol',
             'codex_home': str(home)}
        cmd = ia.comando(c, 'mcp__metricool-inematds__getBrandSettings mcp__metricool-inematds__getScheduledPosts',
                         True, self.p/'resposta')
        self.assertIn('mcp_servers.metricool-inematds.enabled=true', cmd)
        self.assertIn('mcp_servers.metricool.enabled=false', cmd)
        filtro = next(x for x in cmd if 'enabled_tools=' in x)
        self.assertNotIn('createScheduledPost', filtro)
        self.assertIn('getScheduledPosts', filtro)
        self.assertIn('read-only', cmd)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', cmd)
        self.assertEqual(ia.ambiente(c)['CODEX_HOME'], str(home))
        self.cfg['etapas']['metricool_agenda'].update(c)
        ia.validar(self.cfg)

    def test_metricool_codex_recusa_ferramenta_fora_do_contrato(self):
        c = {**self.cfg['etapas']['metricool_publicacao'], 'motor': 'codex', 'modelo': 'gpt-6.1-sol'}
        with self.assertRaisesRegex(ValueError, 'fora do contrato'):
            ia.comando(c, 'mcp__metricool-inematds__deleteScheduledPost', True, self.p/'out')

    def test_intervalo_nao_ignora_horario_ilegivel(self):
        inter = modulo('intervalo_data_invalida', R/'auto/intervalo.py')
        with patch.object(inter, 'executar_ia', return_value='{"ok":true,"posts":[{"dateTime":"ilegivel"}]}'):
            self.assertIsNone(inter.agenda('metricool-inematds', 'FTD', 10000, str(self.p)))


    def test_publicacoes_da_mesma_marca_nao_sobrepoem_regiao_critica(self):
        from auto import metricool_lock
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor
        guarda = threading.Lock()
        ativos = 0
        maximo = 0
        @metricool_lock.serializar('FTD-teste', timeout=5)
        def publicar():
            nonlocal ativos, maximo
            with guarda:
                ativos += 1
                maximo = max(maximo, ativos)
            time.sleep(0.05)
            with guarda:
                ativos -= 1
        with patch.object(metricool_lock.Path, 'home', return_value=self.p):
            with ThreadPoolExecutor(2) as ex:
                tarefas = [ex.submit(publicar) for _ in range(2)]
                for t in tarefas: t.result()
        self.assertEqual(maximo, 1)

    def test_portao_real_bloqueia_sigla_ias_na_fala(self):
        (self.p/'pesquisa').mkdir()
        ficha = yaml.safe_load((R/'tests/fixtures/ficha.yaml').read_text())
        ficha['partes'][0]['fala'] += ' IAs.'
        (self.p/'ficha.yaml').write_text(yaml.safe_dump(ficha))
        (self.p/'pesquisa/top10.json').write_text((R/'tests/fixtures/top10.json').read_text())
        r = subprocess.run([sys.executable, str(R/'gb.py'), 'checar', str(self.p)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('nunca IAs', r.stderr)


    def test_metricool_nao_aceita_api_de_texto(self):
        self.cfg['etapas']['metricool_publicacao'].update(tipo='api', motor='anthropic')
        with self.assertRaisesRegex(ValueError, 'conector Metricool'):
            ia.validar(self.cfg)

    def test_erro_cli_nao_dispara_api_nem_expoe_stderr(self):
        with patch.object(ia.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'segredo')), \
             patch.object(ia, 'chamar_api') as api, self.assertRaises(RuntimeError) as err:
            ia.executar('roteiro', 'teste', self.p)
        api.assert_not_called()
        self.assertNotIn('segredo', str(err.exception))
        self.assertNotIn('segredo', (self.p/'ia-execucoes.jsonl').read_text())

    def test_roteiro_corrige_pelo_portao_real_sem_publicar(self):
        (self.p/'pesquisa').mkdir()
        ficha = yaml.safe_load((R/'tests/fixtures/ficha.yaml').read_text())
        (self.p/'pesquisa/top10.json').write_text((R/'tests/fixtures/top10.json').read_text())
        prev = self.p/'anterior'; prev.mkdir(); (prev/'ficha.yaml').write_text(yaml.safe_dump(ficha))
        quebrada = copy.deepcopy(ficha); quebrada['publicar']['titulo'] = ''
        with patch.object(roteiro, 'executar', side_effect=[yaml.safe_dump(quebrada), yaml.safe_dump(ficha)]) as modelo:
            roteiro.gerar(self.p, prev, 'gere ficha')
        self.assertEqual(modelo.call_count, 2)
        self.assertIn('publicar.titulo', modelo.call_args.args[1])
        self.assertEqual(yaml.safe_load((self.p/'ficha.yaml').read_text()), ficha)
        self.assertFalse((self.p/'video.mp4').exists())

    def test_carrossel_textos_e_revisor_usam_os_contratos_existentes(self):
        car = modulo('carrossel_teste', R/'carrossel/carrossel.py')
        d = {'tipo': 'top10', 'dia': '2026-11-15', 'itens': [{'nome': 'teste/projeto'}]}
        (self.p/'dados.json').write_text(json.dumps(d))
        t = {'capa': {'manchete': 'SEU TRABALHO MAIS LEVE', 'destaque': 'LEVE'},
             'repos': {'teste/projeto': {'gancho': ['ORGANIZE TAREFAS', 'EM UM LUGAR'],
              'o_que_e': 'Um organizador de tarefas que ajuda você a acompanhar o trabalho diário em um único lugar.',
              'beneficios': [{'icone': 'zap', 'titulo': 'Organização', 'texto': 'Reúna as tarefas do dia para acompanhar o andamento.'},
                             {'icone': 'clock', 'titulo': 'Planejamento', 'texto': 'Defina a próxima tarefa e acompanhe suas entregas.'}],
              'fluxo': ['ABRA O PROJETO', 'CRIE A TAREFA', 'ACOMPANHE']}},
             'legenda_abertura': 'Veja os projetos do dia.', 'telegram': 'Aprenda no inema.club.'}
        with patch.object(car, 'executar_ia', return_value=json.dumps(t)):
            car.cmd_textos(self.p)
        self.assertEqual(car.checar_textos(d, json.loads((self.p/'textos.json').read_text())), [])
        (self.p/'slides.json').write_text('{}'); (self.p/'folha.jpg').write_bytes(b'fake')
        with patch.object(car, 'executar_ia', return_value='{"veredito":"aprovado"}') as modelo:
            self.assertEqual(car.cmd_revisar(self.p)['veredito'], 'aprovado')
        self.assertIn(self.p/'folha.jpg', modelo.call_args.kwargs['imagens'])

    def test_intervalo_preserva_uma_hora_e_recusa_agenda_indisponivel(self):
        inter = modulo('intervalo_teste', R/'auto/intervalo.py')
        self.assertEqual(inter.livre(10000, [10000, 13600]), 17200)
        with patch.object(inter, 'executar_ia', return_value='{"ok":false,"erro":"sem agenda"}'):
            self.assertIsNone(inter.agenda('metricool-inematds', 'FTD', 10000, str(self.p)))


if __name__ == '__main__':
    unittest.main()
