"""Transcrição local com tempo por palavra (Whisper large-v3 do inemavox) e comparação de fala.
CÓPIA de ~/projetos/cardshorts/cardshorts.py (18/10/2026) para o r7ex funcionar sozinho: mudar aqui não afeta o cardshorts.
O inemavox continua sendo a ferramenta da máquina (como ffmpeg e codex)."""
import json, os, re, subprocess, time, unicodedata, urllib.request
from pathlib import Path

HOME = Path.home()
CFG = {"inemavox": os.environ.get("CS_INEMAVOX", str(HOME / "projetos/inemavox"))}


def sh(*a, **k):
    subprocess.run([str(x) for x in a], check=True, **k)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


_EQUIV = {"duzentas": "duzentos", "trezentas": "trezentos", "quatrocentas": "quatrocentos", "quinhentas": "quinhentos",
          "seiscentas": "seiscentos", "setecentas": "setecentos", "oitocentas": "oitocentos", "novecentas": "novecentos",
          "uma": "um", "duas": "dois", "catorze": "quatorze", "pra": "para"}


_UN = "zero um dois tres quatro cinco seis sete oito nove dez onze doze treze quatorze quinze dezesseis dezessete dezoito dezenove".split()
_DZ = "_ _ vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split()
_CT = "_ cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos".split()
# feminino e variantes que o texto escrito usa e o Whisper não (ou vice-versa)


def extenso(n):
    """Inteiro por extenso em português (até bilhões), só para comparar fala com transcrição."""
    if n < 20:
        return _UN[n]
    if n < 100:
        return _DZ[n // 10] + ("" if n % 10 == 0 else " e " + _UN[n % 10])
    if n < 1000:
        if n == 100:
            return "cem"
        return _CT[n // 100] + ("" if n % 100 == 0 else " e " + extenso(n % 100))
    for base, sing, plur in ((10**9, "um bilhao", "bilhoes"), (10**6, "um milhao", "milhoes"), (1000, "mil", "mil")):
        if n >= base:
            q, r = divmod(n, base)
            cab = sing if q == 1 else f"{extenso(q)} {plur}"
            return cab + ("" if r == 0 else (" e " if r < 100 or r % 100 == 0 else " ") + extenso(r))


def _numeros(s):
    def troca(m):
        txt = m.group(0)
        if "," in txt:  # 1,5 → um virgula cinco
            a, b = txt.split(",", 1)
            return f" {extenso(int(a.replace('.', '')))} virgula {extenso(int(b))} "
        return f" {extenso(int(txt.replace('.', '')))} "
    return re.sub(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", troca, s)


def norm(s):
    s = unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()
    s = _numeros(s)
    return [_EQUIV.get(w, w) for w in re.sub(r"[^a-z0-9 ]", " ", s).split()]

WHISPER_PORTA = int(os.environ.get("CS_WHISPER_PORTA", "7871"))


def _whisper_residente(w16, palavras):
    """Whisper que carrega o modelo UMA vez (inemavox/whisper_daemon.py, 15/10/2026): sobe o daemon se não
    estiver no ar e transcreve por ele. Devolve os segmentos, ou None para cair no caminho antigo."""
    if os.environ.get("CS_WHISPER_RESIDENTE", "1") == "0":
        return None
    base = f"http://127.0.0.1:{WHISPER_PORTA}"

    def no_ar():
        try:
            return urllib.request.urlopen(base + "/saude", timeout=5).status == 200
        except Exception:
            return False

    try:
        if not no_ar():
            import fcntl
            with open(HOME / ".cache/whisper_daemon.lock", "w") as lk:  # só um processo sobe o daemon
                fcntl.flock(lk, fcntl.LOCK_EX)
                if not no_ar():
                    subprocess.Popen([os.environ.get("CS_WHISPER_PY", str(HOME / "miniconda3/envs/chatterbox/bin/python3")),
                                      "whisper_daemon.py", "--porta", str(WHISPER_PORTA)], cwd=CFG["inemavox"],
                                     stdout=open(HOME / ".cache/whisper_daemon.log", "a"), stderr=subprocess.STDOUT,
                                     start_new_session=True)
                    for _ in range(90):  # até 3 min para carregar o large-v3
                        time.sleep(2)
                        if no_ar():
                            break
        req = urllib.request.Request(base + "/transcrever", headers={"Content-Type": "application/json"},
                                     data=json.dumps({"audio": str(Path(w16).resolve()), "lang": os.environ.get("CS_LANG", "pt"),
                                                      "words": palavras}).encode())
        return json.loads(urllib.request.urlopen(req, timeout=1800).read())["segments"]
    except Exception as e:
        print(f"[r7ex] whisper residente indisponível ({e}); usando o caminho antigo", flush=True)
        return None


def transcrever(wav, pasta, palavras=False):
    """Transcrição local (Whisper large-v3 pelo inemavox). Devolve a lista de palavras ou segmentos."""
    pasta.mkdir(parents=True, exist_ok=True)
    w16 = pasta / "a16.wav"
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ar", "16000", "-ac", "1", w16)
    segs = _whisper_residente(w16, palavras)
    if segs is not None:
        return [w for s in segs for w in s.get("words", [])] if palavras else segs
    # large-v3 carrega ~10 GB na GPU: entra na fila única da máquina (wifi/scripts/gpu-fila, 20/10/2026)
    fila = os.environ.get("R7X_GPU_FILA", "/home/nmaldaner/projetos/wifi/scripts/gpu-fila")   # sem a fila (VPS), roda direto
    cmd = ([fila, "r7ex-whisper", "--"] if os.access(fila, os.X_OK) else []) + ["python3", "transcrever_v1.py", "--in", w16, "--outdir", pasta / "t", "--whisper-model", "large-v3",
           "--src", os.environ.get("CS_LANG", "pt")]  # CS_LANG=es: reel traduzido (REA ES, 13/10/2026)
    if palavras:
        cmd.append("--words")
    sh(*cmd, cwd=CFG["inemavox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segs = json.loads((pasta / "t/transcript.json").read_text())
    segs = segs.get("segments", segs) if isinstance(segs, dict) else segs
    return [w for s in segs for w in s.get("words", [])] if palavras else segs


