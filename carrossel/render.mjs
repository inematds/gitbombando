#!/usr/bin/env node
// Carrossel do Bombando no GitHub: slides.json → PNG 1080x1350 (capa, um slide por repositório, fecho) + relatorio.json
// uso: node carrossel/render.mjs <pasta-do-carrossel>   (lê <pasta>/slides.json, grava <pasta>/slides/)
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const CD = path.resolve(process.argv[2] || ".");
const S = JSON.parse(fs.readFileSync(path.join(CD, "slides.json"), "utf8"));
const SAIDA = path.join(CD, "slides");
fs.rmSync(SAIDA, { recursive: true, force: true });
fs.mkdirSync(SAIDA, { recursive: true });

const esc = s => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const arq = p => pathToFileURL(path.resolve(CD, p)).href;
const css = fs.readFileSync(path.join(AQUI, "base.css"), "utf8")
  .replace(/url\("\{\{FONTS\}\}\/([\w-]+)\.ttf"\)/g, (_, f) =>
    `url(data:font/ttf;base64,${fs.readFileSync(path.join(AQUI, "fonts", `${f}.ttf`)).toString("base64")})`);

// ícones de traço fino (estilo Lucide, MIT), cor por currentColor
const I = {
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
  video: '<path d="m22 8-6 4 6 4V8z"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4"/>',
  code: '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
  terminal: '<path d="m4 17 6-6-6-6M12 19h8"/>',
  bot: '<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M12 8V4H8M2 14h2M20 14h2M9 13v2M15 13v2"/>',
  brain: '<path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 1 5 3 3 0 0 0 4 4 3 3 0 0 0 3-2V5a3 3 0 0 0-3-2zM15 3a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-1 5 3 3 0 0 1-4 4 3 3 0 0 1-3-2"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',
  layers: '<path d="m12 2 10 5-10 5L2 7l10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  cpu: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
  database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5M3 12a9 3 0 0 0 18 0"/>',
  wand: '<path d="m15 4 5 5L9 20l-5-5L15 4zM18 2v2M22 6h-2M5 3v2M3 4h2"/>',
  chart: '<path d="M3 3v18h18M7 16l4-4 3 3 5-6"/>',
  folder: '<path d="M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  link: '<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>',
  chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  doc: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
  seta: '<path d="M5 12h14M13 6l6 6-6 6"/>',
};
const ico = (n, cls = "ico") => `<svg class="${cls}" viewBox="0 0 24 24">${I[n] || I.zap}</svg>`;
const ESTRELA = '<svg class="ico" viewBox="0 0 24 24"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/></svg>';
const GH = '<svg class="gh" viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>';

const total = S.slides.length + 2;
const topo = i => `<div class="top"><span class="serie">${esc(S.serie)}</span><span>${esc(S.conta)} · ${i}/${total}</span></div>`;

function capa() {
  const c = S.capa;
  const lista = c.fundo || [];
  const fundo = Array.from({ length: 12 }, (_, k) => lista.length ? `<img src="${arq(lista[k % lista.length])}">` : "").join("");
  let man = esc(c.manchete);
  if (c.destaque) man = man.replace(esc(c.destaque), `<span class="hl">${esc(c.destaque)}</span>`);
  return `<div class="page capa"><div class="mosaico">${fundo}</div><div class="veu"></div><div class="dentro">
    <div class="kicker">${esc(S.conta)} · ${esc(S.data_br)}</div>
    <div class="grande" data-fit>${esc(c.linha1)}</div>
    <div class="media" data-fit>${esc(c.linha2)}</div>
    <div class="manchete" data-fit>${man}</div>
    <div class="numero">${ESTRELA}<b>${esc(c.numero)}</b><span>${esc(c.numero_rotulo)}</span></div>
    <div class="arrasta">ARRASTA PRO LADO ${ico("seta")}</div></div></div>`;
}

function slide(s, i) {
  const bens = (s.beneficios || []).slice(0, 2).map(b => `<div class="bem"><div class="ic">${ico(b.icone)}</div>
    <div><h4>${esc(b.titulo)}</h4><p>${esc(b.texto)}</p></div></div>`).join("");
  const fluxo = (s.fluxo || []).map(esc).map(p => `<div class="p">${p}</div>`).join(`<svg class="seta ico" viewBox="0 0 24 24">${I.seta}</svg>`);
  return `<div class="page">${topo(i)}
    <div class="cab"><div class="pos">${String(s.pos).padStart(2, "0")}</div><div class="pilula">${GH}<span class="n">${esc(s.repo)}</span></div></div>
    <div class="gancho" data-fit>${esc(s.gancho[0])}<span class="l2">${esc(s.gancho[1])}</span></div>
    <div class="print"><img class="fundo" src="${arq(s.print)}"><img class="img" src="${arq(s.print)}">
      <div class="selo">${ESTRELA}${esc(s.stat)}<small>${esc(s.stat_rotulo)}</small></div></div>
    <div class="oque"><div class="ic">${ico("doc")}</div><div><h3 data-fit>O que é o ${esc(s.repo)}?</h3><p data-fit>${esc(s.o_que_e)}</p></div></div>
    <div class="bens">${bens}</div>
    <div class="fluxo"><div class="rot">COMO<br>USA</div>${fluxo}</div>
    <div class="repo">${GH}<div class="t"><small>REPOSITÓRIO NO GITHUB</small><b style="font-size:${(u => u.length > 44 ? 21 : u.length > 33 ? 25 : 29)(s.url.replace(/^https?:\/\//, ""))}px">${esc(s.url.replace(/^https?:\/\//, ""))}</b></div>
      <div class="info"><b>${esc(s.total)}</b> estrelas<br>${esc(s.info2)}</div></div></div>`;
}

function fecho() {
  const f = S.fecho;
  const lista = S.slides.map(s => `<div><b>${String(s.pos).padStart(2, "0")}</b><span class="n">${esc(s.repo)}</span></div>`).join("");
  return `<div class="page fecho">${topo(total)}<div class="dentro">
    <h2>${esc(f.titulo_a)} <span class="hl">${esc(f.titulo_b)}</span></h2>
    <div class="sub">${esc(f.texto)}</div>
    <div class="lista">${lista}</div>
    <div class="agenda">${f.agenda}</div>
    <div class="club">inema.club · cursos grátis de IA</div></div></div>`;
}

const paginas = [{ nome: "01-capa.png", html: capa() },
  ...S.slides.map((s, k) => ({ nome: `${String(k + 2).padStart(2, "0")}-${s.pos}.png`, html: slide(s, k + 2) })),
  { nome: `${String(total).padStart(2, "0")}-fecho.png`, html: fecho() }];

const browser = await chromium.launch({ args: ["--no-sandbox", "--allow-file-access-from-files"] });
const rel = { paginas: [] };
try {
  const page = await (await browser.newContext({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 })).newPage();
  const tmp = path.join(SAIDA, ".pagina.html");
  for (const p of paginas) {
    fs.writeFileSync(tmp, `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>${css}</style></head><body>${p.html}</body></html>`);
    await page.goto(pathToFileURL(tmp).href);
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(i => (i.complete ? null : i.decode().catch(() => null))));
    });
    // encolhe a letra até caber (até 30%) e anota o que não coube
    const medida = await page.evaluate(() => {
      const caixa = document.querySelector(".page").getBoundingClientRect();
      const out = [];
      for (const el of document.querySelectorAll("[data-fit]")) {
        const base = parseFloat(getComputedStyle(el).fontSize);
        let k = 1;
        const estoura = () => el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + base * 0.2;
        while (estoura() && k > 0.7) { k -= 0.04; el.style.fontSize = base * k + "px"; }
        out.push({ classe: el.className, escala: +k.toFixed(2), estourou: estoura() });
      }
      // nada pode passar do fim da página (o que empurra o rodapé para fora)
      const passou = () => [...document.querySelectorAll(".page *")].some(e => e.getBoundingClientRect().bottom > caixa.bottom + 1
        && !e.closest(".mosaico") && !e.closest(".print"));
      // 09/11/2026: gancho em 3 linhas empurrou a caixa do repo para fora. Encolhe o gancho até a página caber (até 55%).
      const g = document.querySelector(".gancho");
      if (g) {
        const gb = parseFloat(getComputedStyle(g).fontSize);
        let kg = parseFloat(g.style.fontSize || gb) / gb;
        while (passou() && kg > 0.55) { kg -= 0.04; g.style.fontSize = gb * kg + "px"; }
      }
      const fora = [...document.querySelectorAll(".page *")].filter(e => e.getBoundingClientRect().bottom > caixa.bottom + 1
        && !e.closest(".mosaico") && !e.closest(".print")).map(e => e.className.baseVal ?? e.className).slice(0, 5);
      const pr = document.querySelector(".print");
      const imgs = [...document.images].map(i => ({ src: decodeURI(i.src.split("/").pop()), ok: i.naturalWidth > 0 }));
      return { caixas: out, fora, imagens: imgs, altura_print: pr ? Math.round(pr.getBoundingClientRect().height) : null,
        fontes: [...document.fonts].filter(f => f.status === "loaded").map(f => f.family) };
    });
    await page.locator(".page").screenshot({ path: path.join(SAIDA, p.nome) });
    rel.paginas.push({ nome: p.nome, ...medida });
    console.log("ok", p.nome);
  }
  fs.rmSync(tmp, { force: true });
} finally {
  await browser.close();
}
fs.writeFileSync(path.join(CD, "relatorio.json"), JSON.stringify(rel, null, 1));
console.log(`pronto: ${paginas.length} slides em ${SAIDA}`);
