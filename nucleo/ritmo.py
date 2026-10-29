"""Ritmo da fala e cartão do fecho segurado (Nei, 28/10/2026) — corrige o avatar do HeyGen UMA vez, na montagem.

Medido em 4 edições (28/10): 202–222 palavras/min, nenhum silêncio ≥ 0,3 s e o cartão do comentário 0,8–1,6 s na tela,
com o vídeo cortando na última palavra. O HeyGen fala no ritmo dele (encurtar o roteiro só encurta o vídeo), então:
  1. estica a fala até ~182 palavras/min (atempo, que preserva o tom, + vídeo no mesmo fator: a boca continua casada),
     no máximo 12% (K_MAX) — nada de acelerar;
  2. abre um silêncio de ~0,75 s antes da máxima (1ª palavra da parte 6 ou `ritmo.pausa_antes` da ficha), cortando no
     ponto mais silencioso do vão e segurando o quadro (tpad clone);
  3. segura o quadro final do avatar CAUDA s depois da última palavra (o cartão do comentário fica parado; a trilha continua).
O original vai para avatar/avatar-heygen.mp4 + avatar/tempos-heygen.json; avatar.mp4 e tempos.json passam a ser os
corrigidos (os tempos são recalculados pela conta, nunca retranscritos — Whisper de novo pode perder fala, FALHAS 21/10).
avatar/ritmo.json guarda a decisão (lido pelo cena.py e pelo compor_avatar.sh). R7X_SEM_RITMO=1 desliga.
"""
import json, os, shutil, subprocess, wave
from pathlib import Path

ALVO_WPM = 182          # meio da faixa 160–190 pedida pelo Nei
K_MAX = 1.12            # esticar mais que 12% começa a soar arrastado
PAUSA = 0.75            # silêncio total antes da máxima (vão natural + inserido), dentro de 0,5–0,9 s
PAUSA_MIN = 0.5         # o inserido nunca é menor que isto (o vão natural do HeyGen tem respiração, não é silêncio)
CAUDA = 9.0             # segundos de cartão depois da última palavra (Nei: 8–10 s)
VERSAO = 1


def _dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


def _ponto_quieto(wav, a, b):
    """o instante mais silencioso (janela de 20 ms) entre a e b, para o corte não pegar meia sílaba"""
    import numpy as np
    with wave.open(str(wav)) as w:
        sr = w.getframerate(); n = w.getnchannels()
        w.setpos(max(0, int(a * sr))); x = np.frombuffer(w.readframes(max(1, int((b - a) * sr))), dtype=np.int16)
    if n > 1:
        x = x[::n]
    j = int(.02 * sr)
    if len(x) < 2 * j:
        return (a + b) / 2
    e = [float((x[i:i + j].astype(float) ** 2).mean()) for i in range(0, len(x) - j, j // 2)]
    return a + (e.index(min(e)) * (j // 2) + j / 2) / sr


def _pausa_idx(T, ficha):
    """(fala, palavra) da máxima: ritmo.pausa_antes = {parte: N, de: palavra} ou palavra (na parte 6); padrão 1ª palavra da parte 6"""
    from .cena import n as norm
    r = (ficha or {}).get("ritmo") or {}
    pa = r.get("pausa_antes")
    if pa is False or len(T) < 2:
        return None
    parte = (pa.get("parte") if isinstance(pa, dict) else None) or min(6, len(T) - 1)
    de = pa.get("de") if isinstance(pa, dict) else pa
    k = parte - 1
    if de:
        for j, p in enumerate(T[k]["palavras"]):
            if norm(de) == norm(p["w"]) or (len(norm(de)) > 3 and norm(de) in norm(p["w"])):
                return k, j
        raise SystemExit(f"ritmo.pausa_antes: '{de}' não está na fala da parte {parte}")
    return k, 0


def aplicar(pasta, ficha=None, refazer=False):
    """corrige avatar.mp4/tempos.json (idempotente). Devolve o dict do ritmo.json, ou None se desligado."""
    if os.environ.get("R7X_SEM_RITMO"):
        return None
    av = Path(pasta) / "avatar"; mp4, bruto, rj = av / "avatar.mp4", av / "avatar-heygen.mp4", av / "ritmo.json"
    tj, tbruto = av / "tempos.json", av / "tempos-heygen.json"
    novo_original = not rj.exists() or mp4.stat().st_mtime > rj.stat().st_mtime   # avatar.mp4 trocado (--de, novo HeyGen)
    if rj.exists() and not novo_original and not refazer:
        r = json.loads(rj.read_text())
        if r.get("versao") == VERSAO:
            return r
    if not bruto.exists() or (rj.exists() and novo_original):  # sem ritmo.json mas com o bruto = rodada que caiu no meio
        shutil.move(mp4, bruto); shutil.copy(tj, tbruto)       # tempos.json do retempo = do original
    T = json.loads(tbruto.read_text())
    wav0 = av / "avatar-heygen.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-vn", "-ac", "1", "-ar", "48000", wav0], check=True)
    d0 = _dur(bruto)
    pal = [p for t in T for p in t["palavras"]]
    t0, fl = pal[0]["t"], pal[-1]["f"]
    nw = sum(len(t["fala"].split()) for t in T)
    wpm0 = nw / max(1e-3, fl - t0) * 60
    k = round(min(K_MAX, max(1.0, wpm0 / ALVO_WPM)), 4)

    corte, P, pi = None, 0.0, _pausa_idx(T, ficha)
    if pi:
        fk, j = pi
        b = T[fk]["palavras"][j]["t"]
        a = T[fk]["palavras"][j - 1]["f"] if j else T[fk - 1]["palavras"][-1]["f"]
        a, b = min(a, b), max(a, b)
        corte = _ponto_quieto(wav0, max(0, a - .03), b + .03) if b > a else b - .02
        P = round(max(PAUSA_MIN, PAUSA - (b - a) * k), 3)

    def m(t):                                              # tempo do original → tempo do corrigido
        return round(t * k + (P if corte is not None and t >= corte else 0), 3)

    dk = d0 * k + P
    cauda = round(max(0.0, m(fl) + CAUDA - dk), 3)
    total = round(dk + cauda, 3)

    xs = corte * k if corte is not None else None
    v = f"[0:v]setpts={k}*PTS,fps=30"
    a_ = f"[0:a]aresample=48000,atempo={1 / k:.5f}"
    if xs is not None:
        v += (f",split[va][vb];[va]trim=end={xs:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={P}[v1];"
              f"[vb]trim=start={xs:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={cauda}[v2];[v1][v2]concat=n=2:v=1:a=0[v]")
        a_ += (f",asplit[aa][ab];[aa]atrim=end={xs:.3f},asetpts=PTS-STARTPTS,apad=pad_dur={P}[a1];"
               f"[ab]atrim=start={xs:.3f},asetpts=PTS-STARTPTS" + (f",apad=pad_dur={cauda}" if cauda > 0 else "") +
               "[a2];[a1][a2]concat=n=2:v=0:a=1[a]")
    else:
        v += (f",tpad=stop_mode=clone:stop_duration={cauda}" if cauda > 0 else "") + "[v]"
        a_ += (f",apad=pad_dur={cauda}" if cauda > 0 else "") + "[a]"
    tmp = av / "avatar.ritmo.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-filter_complex", v + ";" + a_, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{total:.3f}", tmp], check=True)
    tmp.replace(mp4)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", "48000", av / "avatar.wav"], check=True)

    # tempos.json do corrigido (mesma convenção do retempo: ini = fim da fala anterior + 0,05; última vai até o fim)
    for t in T:
        for p in t["palavras"]:
            p["t"], p["f"] = m(p["t"]), m(p["f"])
    for i, t in enumerate(T):
        t["ini"] = 0.0 if i == 0 else round(T[i - 1]["palavras"][-1]["f"] + .05, 3)
        if pi and i == pi[0] and pi[1] == 0:                # a tela da máxima entra junto com ela, não no começo do silêncio
            t["ini"] = round(max(t["ini"], t["palavras"][0]["t"] - .15), 3)
    for i, t in enumerate(T):
        t["fim"] = T[i + 1]["ini"] if i + 1 < len(T) else total
    tj.write_text(json.dumps(T, ensure_ascii=False, indent=1))
    ult = T[-1]["palavras"][-1]["f"]
    fala = ult - T[0]["palavras"][0]["t"]
    r = {"versao": VERSAO, "k": k, "wpm_heygen": round(wpm0, 1), "wpm": round(nw / fala * 60, 1), "palavras": nw,
         "fala_s": round(fala, 2), "pausa": ({"ini": m(corte) - P if corte is not None else None, "fim": m(corte) if corte is not None else None,
                                             "inserida": P, "fala": T[pi[0]]["id"] if pi else None} if pi else None),
         "ultima_palavra": ult, "cauda": round(total - ult, 2), "duracao": total}
    rj.write_text(json.dumps(r, ensure_ascii=False, indent=1))   # por último: mtime > avatar.mp4 marca "já aplicado"
    os.utime(tj)                                                  # tempos.json mais novo que avatar.mp4 (o retempo reaproveita)
    return r
