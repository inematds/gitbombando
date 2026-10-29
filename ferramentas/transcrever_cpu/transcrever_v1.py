#!/usr/bin/env python3
"""Transcrição em CPU para máquina sem GPU (VPS), no lugar do inemavox/transcrever_v1.py.

Mesmos argumentos que o r7ex/whisper.py passa:
  python3 transcrever_v1.py --in a16.wav --outdir t --whisper-model large-v3 --src pt [--words]
Grava <outdir>/transcript.json = {"segments": [{"start", "end", "text", "words": [{"word", "start", "end"}]}]}.

Usa faster-whisper (int8). O modelo pedido é trocado por R7X_WHISPER_CPU (padrão "small"): o retempo alinha
contra o texto conhecido, então o modelo pequeno basta e cabe em 3,7 GB.
Se o faster-whisper não estiver no python atual, reexecuta no venv R7X_WHISPER_VENV (padrão ~/.venvs/whisper).
Uso no r7ex: CS_INEMAVOX=<esta pasta> CS_WHISPER_RESIDENTE=0.
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from faster_whisper import WhisperModel
except ImportError:
    venv = Path(os.environ.get("R7X_WHISPER_VENV", Path.home() / ".venvs/whisper"))
    venv_py = venv / "bin/python3"
    # o python do venv é link para o do sistema: comparar o prefixo, não o executável resolvido
    if venv_py.exists() and Path(sys.prefix).resolve() != venv.resolve():
        os.execv(str(venv_py), [str(venv_py), __file__, *sys.argv[1:]])
    sys.exit("faster-whisper ausente (crie o venv: python3 -m venv ~/.venvs/whisper && ~/.venvs/whisper/bin/pip install faster-whisper)")

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="entrada", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--whisper-model", default="small")
ap.add_argument("--src", default="pt")
ap.add_argument("--words", action="store_true")
a = ap.parse_args()

modelo = os.environ.get("R7X_WHISPER_CPU", "small")
m = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
# áudio decodificado pelo ffmpeg (16 kHz mono float32): evita o PyAV, que quebra com versões novas do faster-whisper
import subprocess  # noqa: E402
import numpy as np  # noqa: E402
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.entrada, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                     check=True, capture_output=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
segs, _ = m.transcribe(audio, language=a.src, word_timestamps=True, vad_filter=False, beam_size=5)
saida = []
for s in segs:
    saida.append({"start": s.start, "end": s.end, "text": s.text,
                  "words": [{"word": w.word, "start": w.start, "end": w.end} for w in (s.words or [])]})
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
(out / "transcript.json").write_text(json.dumps({"segments": saida}, ensure_ascii=False))
print(f"ok {len(saida)} segmentos, modelo {modelo} (cpu int8)")
