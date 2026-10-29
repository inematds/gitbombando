// [GEO=geo-nne.js] node render.mjs <pasta-com-cena.js> <saida.mp4|--quadros t1,t2,...> [--fps 30] [--dur N]
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const [, , pasta, saida, ...resto] = process.argv;
const opt = k => { const i = resto.indexOf(k); return i >= 0 ? resto[i + 1] : null; };
const fps = Number(opt('--fps') || 30);

// página = mapa.html do motor, com cena.js da pasta
const html = fs.readFileSync(path.join(aqui, 'mapa.html'), 'utf8')
  .replace('src="geo.js"', `src="file://${path.resolve(aqui, process.env.GEO || 'geo.js')}"`)
  .replace('src="cena.js"', `src="file://${path.resolve(pasta, 'cena.js')}"`);
const tmp = path.resolve(pasta, '.mapa.html');
fs.writeFileSync(tmp, html);

const browser = await chromium.launch({ args: (process.env.GL || '--use-angle=vulkan --enable-features=Vulkan').split(' ').concat(['--allow-file-access-from-files', '--ignore-gpu-blocklist']) });
// layout "largo" (explicação longa no YouTube) = 1920x1080; o resto é 9:16
const largo = fs.readFileSync(path.resolve(pasta, 'cena.js'), 'utf8').includes('"layout": "largo"');
const page = await browser.newPage({ viewport: largo ? { width: 1920, height: 1080 } : { width: 1080, height: 1920 } });
page.on('pageerror', e => console.error('pageerror', e.message));
await page.goto('file://' + tmp);
await page.waitForFunction(() => window.pronto && window.render, null, { timeout: 60000 });
await page.evaluate(() => window.pronto);
// Sem GPU (VPS da Tiza, 25/10/2026): o mapa deck.gl (WebGL) em software custava ~10 s por quadro; no r7ex ele fica todo
// coberto pelas telas (comparado pixel a pixel: 0,01% da tela, atrás de uma etiqueta). R7X_SEM_MAPA=1 → ~0,2 s por quadro.
if (process.env.R7X_SEM_MAPA === '1') await page.addStyleTag({ content: '#mapa{display:none!important}' });
const dur = Number(opt('--dur') || await page.evaluate(() => window.CENA.duracao));

if (saida === '--quadros') {
  const ts = (opt('--quadros') || resto[0]).split(',').map(Number);
  for (const t of ts) {
    await page.evaluate(t => window.render(t), t);
    const f = path.resolve(pasta, `q_${String(t).replace('.', '_')}.jpg`);
    await page.screenshot({ path: f, type: 'jpeg', quality: 85 });
    console.log(f);
  }
} else {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', saida], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * fps); const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stderr.write(`\r${i}/${n} ${((Date.now() - t0) / 1000 / (i + 1)).toFixed(2)}s/quadro `);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.error(`\nok ${saida}`);
}
await browser.close();
fs.rmSync(tmp, { force: true });   // outra prévia na mesma pasta pode ter apagado (15/10/2026)
