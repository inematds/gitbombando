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
        c = self.cfg['etapas']['roteiro']
        with patch.object(ia, 'ler_chave', return_value='teste'), \
             patch.object(ia.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps({
                 'stop_reason': 'max_tokens', 'content': [{'type': 'text', 'text': 'parcial'}]}).encode())) as net, \
             self.assertRaisesRegex(ValueError, 'incompleta'):
            ia.chamar_api(c, {**self.cfg['api'], 'autorizada': True, 'autorizacao': 'teste sem rede'}, 'teste', [])
        self.assertEqual(net.call_count, 1)

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
