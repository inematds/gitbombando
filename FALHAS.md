# FALHAS — gitbombando

Uma linha por falha, mais recente no topo.

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-11-22 | Reel top5 (semana/área) não renderiza desde 21/11: "The source image cannot be decoded" — gb.py grava o fecho como prints/p13-c.png fixo (top10 tem 13 partes) e o cena.js do top5 (8 partes) pede p8-c.png, que não existe | nome do fecho = p{nº de partes}-c.png; + conferir imagens antes do render e 3 tentativas consertando só a falha (v1.10.1) | infra |
| 2026-11-18 | Reel do dia parou: card do estúdio HeyGen ficou Draft depois do Enviar e a rodada não tentou de novo | reenviar o avatar antes de desistir; refeito à mão às 17:15 | infra |
| 2026-11-17 | Reel reprovado: a capa desenhou a manchete abaixo de 42% da altura e a legenda caiu em cima | medir onde a manchete termina e pedir outra capa antes do render; capa refeita e publicada em 18/11 no lives7 | prompt |
| 2026-11-15 | Duas retomadas consultaram agenda em paralelo e agendaram vídeos na mesma marca às 16:42 | serializar consulta→criação→recibo por marca e corrigir post de 13/11 para 17:42; releitura confirmou | infra |
| 2026-11-15 | updateScheduledPost recusou networkData com redes vazias fora de providers | enviar só configurações das redes ativas Instagram/TikTok, preservando conteúdo; data corrigida no mesmo post | infra |
| 2026-11-15 | Estúdio HeyGen não reabria título já gerado após correção da fala | título interno leva hash da fala para distinguir revisão; novo avatar enviado | infra |
| 2026-11-15 | Metricool não baixava o MP4 de 31 MB da release e retornava timeout | gerar cópia social 720p de 11 MB e resolver CDN; master aprovado preservado, dois vídeos aceitos | infra |
| 2026-11-15 | Roteiro da semana trouxe IAs na fala, expressão que o avatar pode ler em inglês | trocar por inteligências artificiais antes de publicar e bloquear IAs no portão/prompt; avatar anterior preservado | prompt |
| 2026-11-15 | Vídeo de 13/11 parou porque Whisper não alinhou a fala f12 | retranscrever o mesmo avatar pela fila GPU; novo alinhamento 95%, sem regenerar avatar | infra |
| 2026-11-15 | Carrossel de 13/11 recomendava dois trainers de jogos suspeitos e foi reprovado | retirar os dois itens, preservar backup e reconstruir/revisar Top 6; aprovado | prompt |
| 2026-11-15 | Integração Codex/MCP recusou configuração com invalid transport antes de consultar agenda | usar segmento sem aspas em overrides -c mcp_servers.metricool-inematds; consulta real e regressão verificadas | infra |
| 2026-11-15 | Comando configurar reserializava YAML e apagava comentários de orientação | substituir só escalares da etapa pelos índices do parser, preservando comentários; teste de regressão | infra |
| 2026-11-15 | package.json ainda marcava 1.2.0 enquanto o pipeline estava em 1.3.0 | alinhar package.json, lockfile e VERSAO na entrega 1.4.0 | infra |
| 2026-11-09 | Carrossel da área reprovado: print do README de android-ad-cleaner era só o QR de um grupo de WeChat | prints.tem_qr: descarta imagem com QR legível ≥4% da área (0 falsos em 104 prints antigos) | infra |
| 2026-11-09 | Vídeo do dia não saiu: às 06:30 o Trending tinha só 9 projetos (exigimos 10) | coleta espera 20 min e tenta de novo até 6× (timeout da coleta 15 min → 2h30) | infra |
| 2026-11-09 | Carrossel Top 10 reprovado no portão: gancho em 3 linhas empurrou a caixa do repo para fora (slide 8) | render encolhe o gancho até a página caber (até 55%) | prompt + infra |
| 2026-11-08 | Carrossel da área reprovado pelo revisor: nome longo cortado no meio da letra na lista do fecho | span com ellipsis na .lista | infra |
| 2026-11-08 | Vídeo do dia não montou: Whisper residente recusou conexão às 08:35, caminho antigo pulou 83–112 s (pódio) e o tapa-buraco não transcreveu o trecho → "fala f11 não achada" | tapa-buraco recorta só o buraco (±1 s) em vez de ir até o fim do áudio (8b13a80); remontar com o mesmo avatar | infra |
| 2026-11-08 | Vídeo dia+semana não saiu (github.com sem login 504) e carrosséis de 07/11 caíram por 1 imagem (opengraph 429) | trending.baixar tenta com login do Firefox; prints espera no 429 e usa cartão INEMA; nada de travar por 1 repo | infra |
| 2026-11-04 | Semana 04/11 reprovada: gráfico "NA SEMANA" com total por dia de retratos parciais (6 de 7 dias) + contador animado pego no meio = "contradiz o top10.json"; manchete da capa atrás do avatar | gráfico semana/mês só com retratos cobrindo o período todo, senão "antes × agora" (`DIAS_CURVA`); `revisor.md` explica o contador; `pecas.abertura` sobe a arte se a manchete passar de 800 px | prompt + infra |
| 2026-11-04 | Edição 01/11: "fala f11 não achada" — o Whisper pulou 29 s com fala (pódio) | `_tapa_buracos` no retempo: buraco > 8 s retranscreve do buraco ao fim (591e0ff). Mesma cópia existe no rtex, r7ex e eventosextremospub | infra |
| 28/10/2026 | Telegram "database is locked": outra sessão postava com a mesma conta | `telegram()` espera o `lsof` da sessão ficar livre (até 10 min) e não reposta edição já postada | infra |
| 28/10/2026 | 1ª edição parou na cena: caixa do comentário procurava a palavra "pede" (padrão do r7ex) que o roteiro não usa | `cta.de` padrão = 1ª palavra da fala final (`ficha_motor`) + aviso mostra as 2 últimas linhas do fazer.log | infra |
| 28/10/2026 | curva de estrelas pela API (`/stargazers`) respondeu 404 em todos os projetos | retrato próprio de hora em hora (`coleta/retrato.py`) + gráfico "antes × agora" enquanto não há 3 retratos | infra |
