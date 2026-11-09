Você escreve os textos de um CARROSSEL de Instagram do perfil @inema.tech (INEMA.CLUB, cursos grátis de IA).
Tema: {TEMA}. Data: {DATA_BR}.

Leia {CD}/dados.json. Para cada item tem: nome (dono/repo), descricao_en, readme (começo do README), topicos, linguagem
e, às vezes, desc_pt (uma frase já aprovada em português — use como base).

Escreva o arquivo {CD}/textos.json (só ele, JSON válido, UTF-8), exatamente neste formato:

{
  "capa": {"manchete": "ATÉ 6 PALAVRAS EM CAIXA ALTA", "destaque": "UMA PALAVRA DA MANCHETE"},
  "repos": {
    "dono/repo": {
      "gancho": ["LINHA 1", "LINHA 2"],
      "o_que_e": "uma ou duas frases",
      "beneficios": [
        {"icone": "...", "titulo": "...", "texto": "..."},
        {"icone": "...", "titulo": "...", "texto": "..."}
      ],
      "fluxo": ["PASSO 1", "PASSO 2", "PASSO 3"]
    }
  },
  "legenda_abertura": "2 ou 3 frases para abrir a legenda do post",
  "telegram": "2 ou 3 frases para o grupo do Telegram"
}

Regras (um portão automático confere; texto fora da regra volta):
- Uma entrada em "repos" para CADA item do dados.json, com o nome exatamente igual.
- gancho: 2 linhas em CAIXA ALTA, cada uma com no máximo 20 caracteres. Linha 1 diz o que a pessoa ganha ou faz; a linha 2
  fecha a ideia e sai em amarelo. Pode ser pergunta. Ex.: ["EDITAR VÍDEO", "CONVERSANDO?"], ["UM VÍDEO LONGO.", "VÁRIOS CORTES."].
- o_que_e: 80 a 170 caracteres. O que o projeto é e faz, em português simples, para quem não programa. Comece por
  "Um/Uma ..." (ex.: "Um editor de vídeo de código aberto em que você pede a edição numa conversa com a IA.").
- beneficios: 2, diferentes entre si. titulo até 24 caracteres; texto 35 a 80 caracteres. Coisas concretas que o README
  mostra (o que faz, onde roda, quanto custa, com o que liga). icone = um destes: zap, video, image, mic, code, terminal,
  bot, brain, shield, lock, search, globe, layers, clock, cpu, database, wand, chart, folder, link, chat, download.
- fluxo: 3 passos curtos de como se usa, cada um com no máximo 15 caracteres, CAIXA ALTA (ex.: "COLA O LINK", "A IA ESCOLHE", "CORTES PRONTOS").
- capa.manchete: o fato mais forte do conjunto, até 6 palavras, CAIXA ALTA, sem número (os números a capa já mostra);
  destaque = uma palavra que está na manchete.
- Português do Brasil, "você", voz ativa. Sem: revolucionário, incrível, inacreditável, insano, "mude sua vida", "!!",
  emoji, hashtag. Nunca a palavra "morte". Não use jargão sem explicar (API, CLI, framework, SDK, LLM): diga o que é
  ("um programa de terminal", "um modelo de IA"). Nomes de produto podem ficar (Claude Code, Python, Docker).
- Não invente: nada que o README ou a descrição não digam. Se não entender o projeto, descreva só o que está claro.
- Não escreva números de estrelas nos textos (o slide já mostra os números certos).
- legenda_abertura e telegram: chamem para o carrossel e para o inema.club, sem lista de links (a lista entra sozinha).

Se não conseguir ler o dados.json, escreva {CD}/ERRO.txt com o motivo. Não mexa em nenhum outro arquivo.
