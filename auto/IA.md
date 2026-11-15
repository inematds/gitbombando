# IA independente por etapa — gitbombando 1.6.0

A configuração está em `auto/ia.yaml`, dentro deste repositório. Não usa o modelo ou o esforço dos terminais nem o arquivo central modelos.env. Cada chamada lê a configuração atual e registra os valores utilizados na pasta da edição, em `ia-execucoes.jsonl` (sem chave e sem prompt). Não é necessário reiniciar timers ou serviços: a próxima chamada usa a alteração. Uma chamada em andamento termina com a configuração que já recebeu.

## Ver e alterar sem mexer em código

Na pasta `~/projetos/gitbombando`:

```bash
./ia ver
./ia configurar roteiro --esforco medium
./ia configurar revisao_video --modelo claude-opus-5-5 --esforco high
./ia configurar carrossel_textos --tipo assinatura --motor codex --modelo gpt-6.1-sol --esforco medium
./ia validar
```

Também é possível editar só o YAML. O comando `configurar` valida antes de salvar, preserva todos os comentários `#` e troca o arquivo de forma atômica. Não abre menu nem chama modelos. Se editar YAML à mão, rode `./ia validar` antes da próxima execução. IDs dos modelos devem ser completos: não usar `opus`, `sonnet` ou um modelo inexistente no provedor escolhido. A validação verifica a estrutura e as capacidades do adaptador, sem consultar catálogo remoto, saldo, login ou disponibilidade do modelo.

| Etapa | O que controla | Tipos/motores disponíveis |
|---|---|---|
| roteiro | Ficha do vídeo, com correção pelo portão | assinatura/claude, assinatura/codex, api/anthropic, api/openai, api/openrouter |
| capa | Agente que usa image_gen para desenhar a capa | assinatura/codex |
| revisao_video | Revisão visual dos quadros do vídeo | assinatura/claude, assinatura/codex, api/anthropic, api/openai, api/openrouter |
| carrossel_filtro | Seleção dos projetos do tema do dia | assinatura/claude, assinatura/codex, api/anthropic, api/openai, api/openrouter |
| carrossel_textos | Textos dos dois tipos de carrossel | assinatura/claude, assinatura/codex, api/anthropic, api/openai, api/openrouter |
| carrossel_revisao | Revisão visual dos slides | assinatura/claude, assinatura/codex, api/anthropic, api/openai, api/openrouter |
| metricool_agenda | Consulta da agenda para manter 1 h entre posts | assinatura/claude + MCP instalado |
| metricool_publicacao | Agendamento do vídeo e dos carrosséis | assinatura/claude + MCP instalado |

Os dois carrosséis compartilham as etapas carrossel_*. Os modos dia/semana/mês compartilham roteiro/capa/revisao_video. Os modelos dos revisores precisam aceitar imagens. Alterar o modelo da capa altera o agente Codex; a ferramenta de imagem continua sendo image_gen da assinatura. Avatar/HeyGen, Whisper, render, coleta e publicadores sem IA não têm esforço de raciocínio e não são alterados por este arquivo.

## Tipos, motor, modelo e esforço

- `tipo`: `assinatura` ou `api`.
- `motor`: `claude` ou `codex` na assinatura; `anthropic`, `openai` ou `openrouter` para API direta. As cinco opções estão documentadas com `#` no próprio `auto/ia.yaml`, prontas para consultar e copiar ao editar uma etapa.
- `modelo`: ID completo escolhido para essa etapa.
- `esforco`: `low`, `medium`, `high`, `xhigh`; Claude/Anthropic também aceitam `max`; OpenAI/OpenRouter aceitam ainda `none`, `minimal` e `max`, conforme o modelo. O provedor ainda precisa suportar esse nível no modelo escolhido.
- `timeout`: limite em segundos, de 1 a 3600.
- `max_tokens`: teto de saída na API. Não representa um teto de gasto em dólares. Roteiro e textos podem fazer até duas tentativas para corrigir validação; a consulta da agenda também tenta até duas vezes. Publicação não tem repetição automática pelo executor.

A configuração atual usa API Anthropic com Opus 5.5/low para escrita e filtro; Opus 5.5/medium para revisão. Metricool mantém Claude por assinatura com Opus 5.5/low; gpt-6.1-sol/medium para capa. Claude e Codex CLI têm as chaves e seletores de modelo/esforço herdados removidos do ambiente. Modelo/esforço são passados por flags explícitas; o login e os conectores existentes permanecem disponíveis. Nenhum adaptador troca automaticamente para um serviço pago.

## APIs diretas (Anthropic ativa; OpenAI/OpenRouter desativadas)

O executor usa a Messages API diretamente para texto e visão. Não usa API por dentro de Claude Code/Codex. Os scripts anexam dados e imagens, recebem YAML/JSON e salvam os arquivos; o modelo não executa comandos. Isso permite trocar o modelo sem reconstruir a lógica do cron.

Somente depois de o Nei autorizar expressamente a API da Anthropic para as etapas escolhidas:

1. Registrar o pedido em `api.autorizacao` e mudar `api.autorizada` para `true` no YAML.
2. Selecionar cada etapa desejada, por exemplo:

```bash
./ia configurar roteiro --tipo api --motor anthropic --modelo claude-opus-5-5 --esforco low --chave-nome inemapro-api-key
./ia validar
```

A chave fica no arquivo definido em `api.arquivo_chaves`; `api.chave_nome` é o nome padrão da entrada. `--chave-nome` permite uma chave diferente para cada etapa, sem copiá-la. Nomes com hífen são lidos como dados, sem executar/source o `.env`. A configuração e o log guardam referências, nunca o valor. Não habilitar API como tentativa de contornar cota da assinatura sem o pedido explícito do Nei.

Com API desativada, a execução é recusada antes de ler a chave ou conectar à rede. Configurar `tipo: api` sozinho não autoriza consumo. Os adaptadores de capa e Metricool recusam API, pois exigem capacidades ausentes numa chamada de texto/visão. Para eliminar também essa dependência do Claude, será necessário implementar um acesso direto autorizado ao Metricool; esta versão não inventa um substituto para o conector.

A interface da API foi conferida na [documentação Messages](https://platform.claude.com/docs/en/api/messages/create) e na [documentação de esforço](https://platform.claude.com/docs/en/build-with-claude/effort). O adaptador Anthropic foi testado com chamada real autorizada em 15/11/2026. OpenAI/OpenRouter só receberam testes com respostas simuladas, sem consultar catálogo, carregar chaves reais ou consumir esses serviços.

## Verificação local

```bash
python3 -m unittest discover -s tests -v
./ia validar
bash -n auto/rodar.sh auto/carrossel.sh auto/metritds.sh
```

A trava de intervalo usada pelo projeto está em `auto/intervalo.py`, cópia local da regra de 1 h do metricool-inematds com a chamada de IA substituída pelo executor. Não altera o serviço compartilhado dos outros projetos. As marcas continuam usando o registro compartilhado de horários em `~/.local/share/metricool-intervalo/`.

Verificação anterior, v1.4.0 (15/11/2026): 12 testes passaram e o portão real aprovou uma ficha de 13 partes/2.272 caracteres em pasta temporária. A chamada mínima real do Claude aceitou as opções, mas retornou o limite semanal até 16/11 às 21h; não houve resposta de modelo nem publicação.

## OpenAI (modelos da família Codex) e OpenRouter

Na assinatura, `motor: codex` executa o CLI autenticado pelo login. Na API, `motor: openai` chama a Responses API diretamente: não transforma o CLI em cliente de API. O ID de modelo disponível e a cobrança da API são independentes da assinatura. O exemplo gpt-6.1-sol não é garantia de acesso pela sua chave de API.

```yaml
# API OpenAI, somente após autorização explícita:
# tipo: api
# motor: openai
# modelo: gpt-6.1-sol
# esforco: medium
# chave_nome: OPENAI_API_KEY
#
# API OpenRouter, somente após autorização explícita:
# tipo: api
# motor: openrouter
# modelo: anthropic/claude-opus-5.5
# esforco: low
# chave_nome: OPENROUTER_API_KEY
```

As autorizações são separadas: `api.autorizada/autorizacao` é somente Anthropic; OpenAI usa `api.openai.autorizada/autorizacao`; OpenRouter usa `api.openrouter.autorizada/autorizacao`. Cada serviço tem sua referência de chave e herda `arquivo_chaves` do bloco api, podendo sobrescrevê-lo. `etapas_autorizadas: [roteiro]`, quando informado no bloco do serviço, restringe a autorização a essa lista. O teste real da Anthropic usou essa restrição em configuração isolada; não ativou API nos crons.

Referências do protocolo: [OpenAI Responses](https://developers.openai.com/api/reference/resources/responses/methods/create), [OpenRouter API](https://openrouter.ai/docs/api/reference/overview) e [esforço no OpenRouter](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens). OpenRouter recebe o slug completo e `reasoning.effort`, exige suporte aos parâmetros e desativa fallback de provedor. Cada modelo precisa aceitar o esforço e, para revisão, imagens. Não houve teste de rede OpenAI/OpenRouter.

## Testes reais autorizados — 15/11/2026

Os dois motores geraram uma ficha do Top 10 de 14/11, com os mesmos dados e o mesmo pedido. O programa salvou o YAML e executou o portão real `python3 gb.py checar <pasta>`. Ambos passaram na primeira tentativa.

| Motor | Modelo / esforço | Resultado do roteiro | Tempo observado |
|---|---|---|---|
| API Anthropic, chave inemapro-api-key | claude-opus-5-5 / low | 13 partes, 2.275 caracteres, aprovado | 37,87 s |
| Assinatura Codex | gpt-6.1-sol / medium | 13 partes, 1.945 caracteres, aprovado | 42,15 s |

A chamada Anthropic retornou o modelo claude-opus-5-5 e registrou 22.138 tokens de entrada e 4.649 de saída (1.643 de raciocínio). São contagens medidas, não estimativa de custo em dinheiro. O teste Codex usou a assinatura, sem chave de API.

Evidência compacta: `tests/resultados/2026-11-15.json`. Artefatos completos locais: `~/projetos/output/gitbombando-testes-ia-2026-11-15/{anthropic,codex}/` (ficha, dados, configuração isolada e log de execução). Nenhum vídeo/avatar/imagem foi gerado e nada foi publicado. Os testes cobrem geração e validação de roteiro; não provam revisão visual ou publicação por esses motores.

O script `tests/teste_motores_reais.py` permite repetir o teste em um destino novo. `--motor anthropic --autorizar-api` só pode ser usado dentro de autorização explícita vigente; `--motor codex` usa a assinatura. Os 18 testes automáticos locais continuam sem rede e verificam também OpenAI/OpenRouter simulados, isolamento de autorizações e preservação dos comentários.

## Ativação em produção — 15/11/2026 (v1.6.0)

Pedido posterior do Nei: “entao deixa ele operacional com claude api, ok”. Anthropic ativada em roteiro, revisao_video, carrossel_filtro, carrossel_textos e carrossel_revisao. Chave referenciada: inemapro-api-key no wifi/.env. Os modelos e esforços permanecem Opus 5.5/low para texto/filtro e Opus 5.5/medium para revisão. O YAML registra a autorização e limita o uso às cinco etapas. Não é necessário reiniciar os timers; as próximas chamadas leem a configuração.

A capa permanece Codex por assinatura. A consulta da agenda e o agendamento pelo Metricool permanecem Claude por assinatura/MCP: a API de texto não fornece esse conector. Portanto, o limite semanal da assinatura ainda pode impedir a publicação no Metricool, embora texto e revisão já usem API. Não houve reexecução de edições anteriores nesta ativação. OpenAI/OpenRouter seguem desativadas.
