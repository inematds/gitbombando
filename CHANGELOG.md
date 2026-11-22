# CHANGELOG — gitbombando

## 1.11.2 — 22/11/2026
- Todo reel vai também ao grupo INEMA.FREE (https://t.me/+Trl-P9FduY8zMjdh), pela conta do Nei: vídeo com legenda curta e, abaixo, os links dos tops e depois o link do YouTube (`bin/postar_free.py`, uma vez por edição em `free.log`).
- Se o vídeo ainda está na fila do x3, um serviço à parte (`gb-free-<edição>`) espera o YouTube publicar (até 12 h) e posta já com o link.

## 1.10.2 — 22/11/2026
- Vídeo que entrou na fila do x3 mas espera o horário do canal (lives8: 07, 13, 19 h) conta como entregue: sem "Falhou" falso no v3; o item fica em `x3-<canal>.txt` e a rodada não põe de novo na fila.

## 1.10.1 — 22/11/2026
- Falha não para mais a rodada: até 3 tentativas para qualquer erro, cada uma conserta só o que falhou (render refaz a partir da cena; avatar que não fala o roteiro é reenviado sozinho; HeyGen sem envio reenvia como antes). Nei: "se encontrar uma falha, conserta só a falha e continua, até 3 tentativas".
- Antes do render, toda imagem do `cena.js` é conferida; faltando, refaz imagens e cena; se ainda faltar, usa a tela boa mais próxima e registra `SUBSTITUÍ` no log.
- Fecho do inema.club passa a se chamar `p<nº de partes>-c.png` (era `p13` fixo e derrubou o top5 de 8 partes em 21 e 22/11).
- Aviso de falha no v3 traz a linha `REPROVOU` do log, não mais o fim do log ("Node.js v24.22.3").

## 1.9.1 — 18/11/2026
- Grade nova (`auto/grade.sh`): 07:00 Top 10 do dia, 08:00 Top 5 da semana, 09:30 Top 5 da área, 10:00 Top 5 de agentes, domingo 09:00 Top 10 da semana.
- Reels em lives4, lives8, lives3 e lives7; carrosséis em lives9 e lives12 pela fila do x3 e no Telegram INEMA.FTD. Nada direto no Metricool.
- HeyGen tenta 3 vezes; revisor reprovou = capa nova e novo render, uma vez. O v3 só recebe erro.

## 1.8.1 — 18/11/2026
- O vídeo entra na fila do x3 no lives4; YouTube e redes saem de lá. O metritds fica só para rodada manual com `SEM_YT=1`.

## 1.7.1 — 15/11/2026
- Publicação serial por marca durante consulta, criação e recibo; rechecagem do recibo após a trava impede corrida entre retomadas. Marcas diferentes continuam independentes.
- Cópia social 720p menor e URL CDN para contornar timeout de ingestão de MP4 pelo Metricool; master aprovado preservado.
- Portão/prompt bloqueiam IAs na fala; revisão do avatar recebe título interno com hash da fala.
- 23 testes locais aprovados; publicação real dos carrosséis e vídeos pelo Codex/MCP.

## 1.7.0 — 15/11/2026
- Metricool integrado à assinatura Codex: consulta e publicação usam MCP metricool-inematds no perfil autenticado ~/.codex-2. Claude segue disponível por configuração.
- Ferramentas MCP limitadas por etapa, shell sem escrita, demais conectores desativados só na chamada e confirmação obrigatória da conta inematds.
- Legendas anexadas ao executor, JSON do conector normalizado e verificação de mídia já agendada para evitar duplicação.
- Agenda com horário inválido bloqueia agendamento; retomada de semana/mês respeita 2h/4h após horário efetivo do dia.
- 21 testes locais e consulta real de agenda pelo executor integrado aprovados.

## 1.6.0 — 15/11/2026
- Pedido do Nei: ativar Claude API para operação. Cinco etapas de texto/revisão passam a Anthropic; autorização e escopo registrados no YAML.
- Capa permanece Codex/image_gen; Metricool permanece Claude por assinatura/MCP. OpenAI/OpenRouter continuam desativadas.

## 1.5.0 — 15/11/2026
- Cinco opções documentadas com `#` no próprio auto/ia.yaml: Claude/Codex por assinatura e APIs Anthropic/OpenAI/OpenRouter. O comando configurar preserva comentários, inclusive inline.
- Adaptadores OpenAI Responses e OpenRouter com esforço explícito, texto/visão e autorização independente por serviço; sem chamadas reais a esses dois provedores.
- Testes reais de roteiro aprovados pela API Anthropic (Opus 5.5/low) e assinatura Codex (gpt-6.1-sol/medium); configurações isoladas, sem publicação nem ativação de API nos crons.
- 18 testes locais; capa permanece Codex/image_gen por assinatura.

## 1.4.0 — 15/11/2026
- Motor, tipo, modelo e esforço por etapa em `auto/ia.yaml`, com comandos `./ia ver/configurar/validar`; sem herança de modelo/esforço dos terminais.
- Roteiro, filtro, textos e revisores aceitam Claude/Codex por assinatura ou Anthropic direta (texto/visão, desativada até autorização explícita).
- Capa e chamadas do Metricool também têm configuração explícita; trava de intervalo local usa a etapa metricool_agenda sem mudar outros projetos.
- Scripts controlam arquivos, portões e até duas tentativas de roteiro; registro por chamada em ia-execucoes.jsonl. Sem fallback pago.
- package.json alinhado à versão do pipeline.

## 1.3.0 — 09/11/2026
- Coleta: github.com sem login dá 504 → tenta com o login do Firefox do servidor; Trending com menos de 10 espera até 1 h e
  segue com Top N (5 a 10) — vídeo, roteiro, portão, ranking, selo e carrossel contam N.
- Vídeo gera às 09:00 (era 06:30) e publica às 11:00; semana às 13:00 e mês às 15:00 (YouTube e Metricool).
- Capa: quando título + manchete passam de 600 px, mede pelo TOP 10 amarelo e sobe a arte (manchete não cai atrás do avatar).
- Whisper: tapa-buraco retranscreve só o buraco (pulava o pódio de novo).
- Carrossel: vai para o Instagram/TikTok inema.tech (marca FTD, lives3); legenda sem link; gancho encolhe até caber;
  lista do fecho com reticências; QR code legível no README é descartado; cartão INEMA quando falta imagem;
  filtro de tema da área (`claude -p`) tira projeto que só usa a etiqueta.
- Revisores: defeito pequeno que não atrapalha entender vira sugestão e a peça segue (Nei: "pouca coisa, deixa rodar").

## 1.2.0 — 04/11/2026
- Dois carrosséis diários (`carrossel/`, `auto/carrossel.sh`): Top 10 do GitHub às 14h e Top da área às 18h (uma área por dia da
  semana, busca por tópico na API do GitHub). Slide no estilo "repositório da semana": gancho, print do README, o que é, 2
  benefícios, como usa e link. Portão de texto e de desenho + revisor `claude -p`. Publica no tópico fixo do INEMA.DEV
  (álbum), no Instagram (carrossel) e no TikTok (fotos) inema.tds pelo Metricool e avisa no v3.
- Vídeo: gera às 06:30 (estúdio HeyGen livre) e publica às 11:00 (`GB_PUBLICAR_AS`), no lugar das 16:00.

## 1.1.0 — 04/11/2026
- Gráfico de semana/mês: a curva "total por dia" dos retratos só entra quando cobre todos os dias do período (7/30);
  senão o painel mostra "antes × agora" (total − ganho → total), que bate com o "+N" do cartão.
- Capa: `pecas.abertura` sobe ou desce a arte conforme a manchete (termina acima de 800 px; topo nunca acima de 120 px),
  para a legenda do gancho e o avatar não cobrirem a manchete. `manchete()` ignora "caixas" de 600+ px (arte dourada).
- Revisor: o contador animado do painel não conta como número errado (confere a pílula 🔥 do cartão).
- `rodar.sh`: avatar já enviado (`avatar/video_id.txt`) = retoma sem refazer coleta e roteiro. `GB_PESADO=<script>` põe o
  render atrás de uma trava externa.

## 1.0.0 — 28/10/2026
- Primeira versão: coleta do GitHub Trending (dia/semana/mês) ordenada por estrelas ganhas, retrato de estrelas de hora em hora,
  roteiro por `claude -p`, cartões dos 10 projetos + ranking, capa do Codex, avatar no estúdio HeyGen, painel com contador e
  gráfico, revisor `claude -p`, publicação no lives4 + bot v3 + tópico fixo no INEMA.TOOLS, timer diário às 16:00.
