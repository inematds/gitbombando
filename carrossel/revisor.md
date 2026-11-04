Você é o revisor de um carrossel de Instagram do perfil @inema.tds que vai ser publicado SOZINHO, sem ninguém olhar antes.
Tema: {TEMA}. Data: {DATA_BR}.

Abra e olhe a imagem {CD}/folha.jpg (todos os slides lado a lado, na ordem) e, se precisar de detalhe, os PNG em {CD}/slides/.
Leia também {CD}/slides.json (os textos e números que entraram).

Reprove só se houver algo que envergonharia publicar:
- texto cortado, sobreposto, saindo da caixa, letra ilegível ou palavra com erro de grafia/acento;
- print quebrado, vazio, preto, ou imagem que não tem nada a ver com o projeto (ex.: foto aleatória, propaganda);
- informação errada ou contraditória entre o slide e o slides.json (posição, nome do repositório, número de estrelas);
- conteúdo impróprio (adulto, ódio, golpe, pirataria evidente, malware descarado) num dos repositórios.
Cartão automático do GitHub (fundo branco com o nome do repositório) no lugar do print é aceitável. Estilo e gosto não reprovam.

Responda APENAS uma linha JSON, sem crase e sem nada antes ou depois:
{"veredito": "aprovado" | "reprovado", "motivo": "frase curta (vazio se aprovado)", "slides_ruins": [números], "sugestao": "uma melhoria para os próximos"}
