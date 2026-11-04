"""Tempo de cada palavra do avatar, dividido nas 7 falas (cópia do método de eventosextremospub/avatar/retempo.py):
tira o áudio do avatar.mp4, transcreve com Whisper (cardshorts) e alinha a sequência de palavras com falas.json."""
import difflib, json, subprocess
from pathlib import Path

from . import whisper as cs


def _tapa_buracos(wav, pal, tdir, buraco=8.0):
    """O Whisper às vezes pula um trecho inteiro com fala (01/11/2026: 29 s sumidos no pódio, áudio sem silêncio).
    Achou um buraco > `buraco` s entre palavras: retranscreve do buraco até o fim e troca o resto da transcrição."""
    for _ in range(3):
        i = next((k for k in range(len(pal) - 1) if pal[k + 1]["start"] - pal[k]["end"] > buraco), None)
        if i is None:
            return pal
        ini = pal[i]["end"]
        tr = Path(tdir) / f"trecho-{int(ini)}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ini), "-i", wav, tr], check=True)
        novo = cs.transcrever(tr, Path(tdir) / f"trecho-{int(ini)}", palavras=True)
        if not novo:
            return pal
        pal = pal[:i + 1] + [{**p, "start": p["start"] + ini, "end": p["end"] + ini} for p in novo]
    return pal


def retempo(pasta):
    pasta = Path(pasta); av = pasta / "avatar"
    falas = json.loads((pasta / "falas.json").read_text())
    wav = av / "avatar.wav"
    tj = av / "tempos.json"
    if tj.exists() and wav.exists() and tj.stat().st_mtime > (av / "avatar.mp4").stat().st_mtime:
        # mesmo avatar e mesmas falas: reaproveita. Retranscrever pode sair diferente e perder uma fala
        # (rust-fim-python, 21/10/2026: "fala f6 não achada" na remontagem, com o mesmo avatar que já tinha passado)
        velho = json.loads(tj.read_text())
        if [t["fala"] for t in velho] == [f["fala"] for f in falas]:
            esp = [w for f in falas for w in cs.norm(f["fala"])]
            ouv = [w for t in velho for p in t["palavras"] for w in cs.norm(p["w"])]
            return cs.dur(wav), difflib.SequenceMatcher(None, esp, ouv).ratio()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", av / "avatar.mp4", "-vn", "-ac", "1", "-ar", "48000", wav], check=True)
    pal = _tapa_buracos(wav, cs.transcrever(wav, av / "t", palavras=True), av / "t")
    ouv = [(w, i) for i, p in enumerate(pal) for w in cs.norm(p["word"])]
    esp = [(w, k) for k, f in enumerate(falas) for w in cs.norm(f["fala"])]
    m = difflib.SequenceMatcher(None, [w for w, _ in esp], [w for w, _ in ouv], autojunk=False)
    fala_de = {}
    for a, b, n in m.get_matching_blocks():
        for j in range(n):
            fala_de.setdefault(ouv[b + j][1], esp[a + j][1])
    atual, dono = 0, []
    for i in range(len(pal)):
        atual = fala_de.get(i, atual); dono.append(atual)
    tempos = []
    for k, f in enumerate(falas):
        ps = [p for p, d in zip(pal, dono) if d == k]
        if not ps:
            raise SystemExit(f"fala {f['id']} não achada na transcrição do avatar")
        tempos.append({"id": f["id"], "fala": f["fala"], "ini": 0, "fim": 0,
                       "palavras": [{"w": p["word"].strip(), "t": round(p["start"], 3), "f": round(p["end"], 3)} for p in ps]})
    for k, t in enumerate(tempos):
        t["ini"] = 0.0 if k == 0 else round(tempos[k - 1]["palavras"][-1]["f"] + 0.05, 3)
    for k, t in enumerate(tempos):
        t["fim"] = round(tempos[k + 1]["ini"], 3) if k + 1 < len(tempos) else round(cs.dur(wav), 3)
    (av / "tempos.json").write_text(json.dumps(tempos, ensure_ascii=False, indent=1))
    sem = difflib.SequenceMatcher(None, [w for w, _ in esp], [w for w, _ in ouv]).ratio()
    return cs.dur(wav), sem
