# FALHAS — gitbombando

Uma linha por falha, mais recente no topo.

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-11-04 | Edição 01/11: "fala f11 não achada" — o Whisper pulou 29 s com fala (pódio) | `_tapa_buracos` no retempo: buraco > 8 s retranscreve do buraco ao fim (591e0ff). Mesma cópia existe no rtex, r7ex e eventosextremospub | infra |
| 28/10/2026 | Telegram "database is locked": outra sessão postava com a mesma conta | `telegram()` espera o `lsof` da sessão ficar livre (até 10 min) e não reposta edição já postada | infra |
| 28/10/2026 | 1ª edição parou na cena: caixa do comentário procurava a palavra "pede" (padrão do r7ex) que o roteiro não usa | `cta.de` padrão = 1ª palavra da fala final (`ficha_motor`) + aviso mostra as 2 últimas linhas do fazer.log | infra |
| 28/10/2026 | curva de estrelas pela API (`/stargazers`) respondeu 404 em todos os projetos | retrato próprio de hora em hora (`coleta/retrato.py`) + gráfico "antes × agora" enquanto não há 3 retratos | infra |
