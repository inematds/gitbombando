# gitbombando — Bombando no GitHub

[![Bombando no GitHub](guia/assets/banner-es.jpg)](https://inematds.github.io/gitbombando/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

gitbombando crea cada día, automáticamente, un reel vertical (9:16) llamado **Bombando no GitHub** (sale a las 11h) y dos carruseles de
Instagram: el **Top 10 do GitHub** (14h) y el **Top da área** (18h, un área por día de la semana). El reel muestra los 10 proyectos que más
ganaron estrellas en GitHub ese día, en cuenta regresiva del #10 al #1. Cada proyecto aparece en una tarjeta con su posición,
la foto de su dueño, lo que hace explicado en portugués sencillo y el número de estrellas, con un contador y un gráfico debajo. El avatar de
Nei presenta todo con una llamada contundente y cierra pidiendo un comentario. Los domingos también sale el Top 10 de la semana y el día 1, el
del mes. El video se publica en YouTube (canal lives4), Instagram y TikTok @inema.tds, el bot de Nei y un tema fijo
del grupo INEMA.TOOLS en Telegram. Los carruseles se publican en Instagram y TikTok @inema.tds y en un tema fijo del grupo
INEMA.DEV en Telegram. Es para quienes quieren saber qué está causando furor en tecnología sin leer inglés ni código. Se ejecuta en la máquina de INEMA
(Python, Node, Codex, Claude Code y la suscripción de HeyGen).

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/gitbombando/guia/es/**

---

## El proceso, de principio a fin (13 pasos)

🧠 = sesión con Nei (consume tokens) · ⚙️ = script/timer (cero tokens) · 🤖 = `claude -p` corto (sesión nueva)

| # | Paso | Comando / qué sucede | Quién |
|---|---|---|---|
| 0 | Retrato de las estrellas | timer `gitbombando-retrato` cada hora: `coleta/retrato.py` guarda las estrellas de los proyectos en tendencia en `historico/estrelas.jsonl` (se convierte en la curva de los gráficos) | ⚙️ |
| 1 | Agenda | timer `gitbombando.timer` a las **06:30** → `auto/rodar.sh <dia>` (genera cuando el estudio de HeyGen está libre): el del día, siempre publicado a las **11 h** (`GB_PUBLICAR_AS`); los domingos, después de ese, el de la semana, y el día 1, el del mes, que se publican en cuanto están listos (a primera hora de la tarde) | ⚙️ |
| 2 | Recopilación | `coleta/trending.py <pasta> dia\|semana\|mes`: página de GitHub Trending + API de GitHub (descripción, README, lenguaje, estrellas, foto del dueño); Top 10 ordenado por las estrellas ganadas → `pesquisa/top10.json` | ⚙️ |
| 3 | Guion | `claude -p` con `auto/roteiro.md` escribe `ficha.yaml`: gancho sensacionalista con el dato más contundente, panorama, #10 → #1, pregunta final | 🤖 |
| 4 | Filtro del guion | `python3 gb.py checar <pasta>`: 13 partes en orden, proyectos correctos, 1.300–2.500 caracteres, titular ≤ 6 palabras, sin cifras en lo que se dice, "você", CTA solo inema.club | ⚙️ |
| 5 | Avatar + imágenes | `gb.py fazer`: envía el diálogo al estudio de HeyGen (suscripción; autorización vigente de Nei, 28/10/2026) y, al mismo tiempo, crea la portada con el titular (Codex), el ranking, 10 tarjetas y una captura de inema.club | ⚙️ |
| 6 | Edición | tiempo de cada palabra (Whisper), ritmo (~182 palabras/min, pausa antes del #1), escena con contador y gráfico en cada proyecto, renderizado en el motor de noticiero | ⚙️ |
| 7 | Revisión | `claude -p` con `auto/revisor.md` lee la hoja de 18 cuadros: aprobado, sigue; rechazado, se detiene y avisa en v3 | 🤖 |
| 8 | Publicar | `gb.py publicar`: YouTube **lives4** (yt-pubx, título con #Shorts, enlaces de los 10 en la descripción) → bot **v3** → tema fijo **BOMBANDO NO GITHUB** en INEMA.TOOLS | ⚙️ |
| 8b | Metritds | `auto/metritds.sh <pasta>`: sube el video a la release `social` del repo y lo programa (ahora + 10 min) en **Instagram + TikTok inema.tds** mediante Metricool de la cuenta inematds (conector `metricool-inematds`, vía `claude -p`); aviso azul en v3 | 🤖 |
| 9 | Guardar | git commit + push (guion, datos e historial; los archivos multimedia quedan fuera) | ⚙️ |
| 10 | Carrusel Top 10 | timer `gitbombando-carrossel-top10` a las 12:45 → `auto/carrossel.sh <dia> top10` (publica a las **14:00**): reutiliza la recopilación del video; `claude -p` con `carrossel/textos.md` escribe el gancho, "qué es", 2 beneficios y el flujo de cada uno; captura de cada proyecto tomada del README (`carrossel/prints.py`); 12 diapositivas 1080×1350 (`carrossel/render.mjs`); filtro de texto y diseño; revisor `claude -p` (`carrossel/revisor.md`) | ⚙️🤖 |
| 11 | Carrusel del área | timer `gitbombando-carrossel-area` a las 16:45 → `auto/carrossel.sh <dia> area` (publica a las **18:00**): `carrossel/area.py` busca en GitHub los repositorios del área del día creados en los últimos 120 días, ordenados por estrellas por día, sin repetir las últimas 8 semanas y sin contenido para adultos; después sigue el mismo proceso del paso 10 con 8 proyectos | ⚙️🤖 |
| 12 | Publicar el carrusel | `carrossel/carrossel.py publicar`: álbum en el tema fijo **BOMBANDO NO GITHUB - Carrosséis diários** de **INEMA.DEV** (Telegram) → carrusel en Instagram + fotos en TikTok inema.tds (Metricool, ahora + 10 min) → aviso azul en v3 → git. Rechazado = no se publica y avisa en v3 | ⚙️🤖 |

Prueba sin publicar: `ED=/tmp/teste-video AVATAR_DE=<avatar.mp4> SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_METRI=1 SEM_GIT=1 GB_SEM_HISTORICO=1 auto/rodar.sh 2026-10-28 dia`.
Carrusel sin publicar: `ED=/tmp/teste SEM_TG=1 SEM_METRI=1 SEM_BOT=1 SEM_GIT=1 auto/carrossel.sh 2026-11-04 area`
(`RASCUNHO=1` en lugar de `SEM_METRI=1` programa en Metricool como borrador).
Saltar un día: línea `AAAA-MM-DD` (o `AAAA-MM-DD semana`, `AAAA-MM-DD carrossel`, `AAAA-MM-DD carrossel-top10`, `AAAA-MM-DD carrossel-area`) en `auto/pular.txt`.

## Instalación de los timers (una vez)

```bash
cp auto/systemd/gitbombando* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando.timer gitbombando-carrossel-top10.timer gitbombando-carrossel-area.timer
```

## Qué aparece en el video

- **Portada (cuadro 0):** llamada grande "TOP 10 DO GITHUB" arriba + titular de hasta 6 palabras diseñado por Codex, con el número más contundente del día en amarillo.
- **Panorama:** los 10 en barras (estrellas ganadas) y la suma en un contador.
- **Cada proyecto:** tarjeta con `#posición`, foto del dueño, nombre, lo que hace en portugués, lenguaje, total de estrellas y fecha de
  creación. Debajo, el contador de estrellas ganadas llega al número justo cuando se menciona y aparece el gráfico: la curva por hora
  (día) o por día (semana/mes) cuando ya hay retratos, o "antes × ahora" con el crecimiento en %.
- **Cierre:** pregunta en un recuadro rojo, el gesto de escribir un comentario y la píldora inema.club.

## Los carruseles

- **Portada:** mosaico con las capturas de los proyectos, "TOP 10 DO GITHUB HOJE" (o "TOP 8" + el área), un titular de hasta 6 palabras y
  la suma de estrellas.
- **Una diapositiva por proyecto** (del #1 en adelante): posición, nombre, gancho de 2 líneas, captura del README con las estrellas ganadas, "Qué
  es", 2 beneficios, "cómo se usa" en 3 pasos y el enlace del repositorio con el total de estrellas.
- **Cierre:** "los enlaces están en la descripción", la lista de proyectos, la agenda del día e inema.club. La descripción incluye los enlaces.
- **Áreas:** lunes agentes de IA · martes Claude Code y MCP · miércoles IA para video e imagen · jueves seguridad · viernes
  automatización · sábado desarrollo web y apps · domingo IA en tu PC (`carrossel/area.py`, `AREAS`).

## Fuentes y límites

- Solo la página github.com/trending y la API de GitHub. La lista de stargazers de la API responde 404 desde 2026, por eso la curva
  se genera a partir de los retratos del propio proyecto, tomados cada hora.
- El Top 10 se ordena por las estrellas ganadas durante el período (el orden de la página de Trending mezcla otras señales).

Licencia MIT.
