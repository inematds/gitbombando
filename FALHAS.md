# FALHAS — gitbombando

Uma linha por falha, mais recente no topo.

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
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
