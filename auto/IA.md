# IA independente por etapa — gitbombando 1.4.0

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

Também é possível editar só o YAML. O comando `configurar` valida antes de salvar e troca o arquivo de forma atômica. Não abre menu nem chama modelos. Se editar YAML à mão, rode `./ia validar` antes da próxima execução. IDs dos modelos devem ser completos: não usar `opus`, `sonnet` ou um modelo inexistente no provedor escolhido. A validação verifica a estrutura e as capacidades do adaptador, sem consultar catálogo remoto, saldo, login ou disponibilidade do modelo.

| Etapa | O que controla | Tipos/motores disponíveis |
|---|---|---|
| roteiro | Ficha do vídeo, com correção pelo portão | assinatura/claude, assinatura/codex, api/anthropic |
| capa | Agente que usa image_gen para desenhar a capa | assinatura/codex |
| revisao_video | Revisão visual dos quadros do vídeo | assinatura/claude, assinatura/codex, api/anthropic |
| carrossel_filtro | Seleção dos projetos do tema do dia | assinatura/claude, assinatura/codex, api/anthropic |
| carrossel_textos | Textos dos dois tipos de carrossel | assinatura/claude, assinatura/codex, api/anthropic |
| carrossel_revisao | Revisão visual dos slides | assinatura/claude, assinatura/codex, api/anthropic |
| metricool_agenda | Consulta da agenda para manter 1 h entre posts | assinatura/claude + MCP instalado |
| metricool_publicacao | Agendamento do vídeo e dos carrosséis | assinatura/claude + MCP instalado |

Os dois carrosséis compartilham as etapas carrossel_*. Os modos dia/semana/mês compartilham roteiro/capa/revisao_video. Os modelos dos revisores precisam aceitar imagens. Alterar o modelo da capa altera o agente Codex; a ferramenta de imagem continua sendo image_gen da assinatura. Avatar/HeyGen, Whisper, render, coleta e publicadores sem IA não têm esforço de raciocínio e não são alterados por este arquivo.

## Tipos, motor, modelo e esforço

- `tipo`: `assinatura` ou `api`.
- `motor`: `claude` ou `codex` na assinatura; `anthropic` para API direta.
- `modelo`: ID completo escolhido para essa etapa.
- `esforco`: `low`, `medium`, `high`, `xhigh`; Claude/Anthropic também aceitam `max`. O provedor ainda precisa suportar esse nível no modelo escolhido.
- `timeout`: limite em segundos, de 1 a 3600.
- `max_tokens`: teto de saída na API. Não representa um teto de gasto em dólares. Roteiro e textos podem fazer até duas tentativas para corrigir validação; a consulta da agenda também tenta até duas vezes. Publicação não tem repetição automática pelo executor.

As configurações iniciais explicitam Opus 5.5/low para escrita, filtro e Metricool; Opus 5.5/medium para revisão; gpt-6.1-sol/medium para capa. Claude e Codex CLI têm as chaves e seletores de modelo/esforço herdados removidos do ambiente. Modelo/esforço são passados por flags explícitas; o login e os conectores existentes permanecem disponíveis. Nenhum adaptador troca automaticamente para um serviço pago.

## API Anthropic (preparada, desativada)

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

A interface da API foi conferida na [documentação Messages](https://platform.claude.com/docs/en/api/messages/create) e na [documentação de esforço](https://platform.claude.com/docs/en/build-with-claude/effort). Os testes usam respostas simuladas; não houve chamada paga nesta entrega. A disponibilidade real do modelo/chave depende de teste autorizado.

## Verificação local

```bash
python3 -m unittest discover -s tests -v
./ia validar
bash -n auto/rodar.sh auto/carrossel.sh auto/metritds.sh
```

A trava de intervalo usada pelo projeto está em `auto/intervalo.py`, cópia local da regra de 1 h do metricool-inematds com a chamada de IA substituída pelo executor. Não altera o serviço compartilhado dos outros projetos. As marcas continuam usando o registro compartilhado de horários em `~/.local/share/metricool-intervalo/`.

Verificação desta entrega (15/11/2026): 12 testes passaram e o portão real aprovou uma ficha de 13 partes/2.272 caracteres em pasta temporária. A chamada mínima real do Claude aceitou as opções, mas retornou o limite semanal até 16/11 às 21h; não houve resposta de modelo nem publicação.
