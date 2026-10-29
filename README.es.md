# gitbombando — Bombando no GitHub

[![Bombando no GitHub](guia/assets/banner-es.jpg)](https://inematds.github.io/gitbombando/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

gitbombando crea automáticamente, todos los días a las 16 h, un reel vertical (9:16) llamado **Bombando no GitHub**: los 10 proyectos que más estrellas ganaron en GitHub ese día, en cuenta regresiva del #10 al #1. Cada proyecto aparece en una tarjeta con su posición, la foto de su dueño, una explicación sencilla de lo que hace y el número de estrellas, con un contador y un gráfico debajo. El avatar de Nei presenta todo con un llamado contundente y termina pidiendo un comentario. Los domingos también sale el Top 10 de la semana y el día 1, el del mes. El video se publica en YouTube (canal INEMA Tec), en el bot de Nei y en un tema fijo del grupo INEMA.TOOLS en Telegram. Es para quienes quieren saber qué está causando sensación en tecnología sin leer inglés ni código. Se ejecuta en la máquina de INEMA (Python, Node, Codex, Claude Code y la suscripción de HeyGen).

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/gitbombando/guia/es/**

---

## El proceso, de principio a fin (10 pasos)

🧠 = sesión con Nei (consume tokens) · ⚙️ = script/timer (cero tokens) · 🤖 = `claude -p` breve (sesión nueva)

| # | Paso | Comando / qué ocurre | Quién |
|---|---|---|---|
| 0 | Retrato de las estrellas | timer `gitbombando-retrato` cada hora: `coleta/retrato.py` guarda las estrellas de los proyectos en tendencia en `historico/estrelas.jsonl` (da forma a la curva de los gráficos) | ⚙️ |
| 1 | Agenda | timer `gitbombando.timer` a las 16:00 → `auto/rodar.sh <dia>`: siempre el día; los domingos también la semana; el día 1, también el mes | ⚙️ |
| 2 | Recolección | `coleta/trending.py <pasta> dia\|semana\|mes`: página de GitHub Trending + API de GitHub (descripción, README, lenguaje, estrellas, foto del dueño); Top 10 ordenado por las estrellas ganadas → `pesquisa/top10.json` | ⚙️ |
| 3 | Guion | `claude -p` con `auto/roteiro.md` escribe `ficha.yaml`: gancho sensacionalista con el dato más contundente, panorama, #10 → #1, pregunta final | 🤖 |
| 4 | Control del guion | `python3 gb.py checar <pasta>`: 13 partes en orden, proyectos correctos, 1.300–2.500 caracteres, titular de ≤ 6 palabras, sin cifras en el texto hablado, "você", CTA solo inema.club | ⚙️ |
| 5 | Avatar + imágenes | `gb.py fazer`: envía el guion al estudio de HeyGen (suscripción; autorización permanente de Nei, 28/10/2026) y, al mismo tiempo, crea la portada con el titular (Codex), el ranking, 10 tarjetas y una captura de inema.club | ⚙️ |
| 6 | Montaje | duración de cada palabra (Whisper), ritmo (~182 palabras/min, pausa antes del #1), escena con contador y gráfico para cada proyecto, render en el motor de noticiero | ⚙️ |
| 7 | Revisión | `claude -p` con `auto/revisor.md` lee la hoja de 18 cuadros: aprobado, continúa; rechazado, se detiene y avisa en v3 | 🤖 |
| 8 | Publicación | `gb.py publicar`: YouTube **lives4** (yt-pubx, título con #Shorts, enlaces de los 10 en la descripción) → bot **v3** → tema fijo **BOMBANDO NO GITHUB** en INEMA.TOOLS | ⚙️ |
| 9 | Guardar | git commit + push (guion, datos e historial; los archivos multimedia quedan fuera) | ⚙️ |

Prueba sin publicar: `SEM_YT=1 SEM_BOT=1 SEM_TG=1 SEM_GIT=1 auto/rodar.sh 2026-10-28 dia`.
Omitir un día: una línea `AAAA-MM-DD` (o `AAAA-MM-DD semana`) en `auto/pular.txt`.

## Instalación de los timers (una vez)

```bash
cp auto/systemd/gitbombando* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now gitbombando-retrato.timer gitbombando.timer
```

## Qué aparece en el video

- **Portada (cuadro 0):** titular de hasta 6 palabras diseñado por Codex, con el número más contundente del día en amarillo.
- **Panorama:** los 10 en barras (estrellas ganadas) y la suma en un contador.
- **Cada proyecto:** tarjeta con `#posición`, foto del dueño, nombre, lo que hace en portugués, lenguaje, total de estrellas y fecha de creación. Debajo, el contador de estrellas ganadas llega al número justo cuando se menciona, y el gráfico muestra la curva por hora (día) o por día (semana/mes) cuando ya hay retratos, o «antes × ahora» con el crecimiento en %.
- **Cierre:** pregunta en un recuadro rojo, el gesto de escribir un comentario y la píldora inema.club.

## Fuentes y límites

- Solo la página github.com/trending y la API de GitHub. La lista de stargazers de la API responde 404 desde 2026, por eso la curva se construye a partir de los retratos por hora del propio proyecto.
- El Top 10 se ordena por las estrellas ganadas durante el período (el orden de la página de Trending mezcla otras señales).

Licencia MIT.