"""Serializa consulta, agendamento e recibo por marca, inclusive processos distintos."""
import fcntl
from functools import wraps
from pathlib import Path
import time


def serializar(marca, timeout=1800):
    def decorar(func):
        @wraps(func)
        def executar(*args, **kwargs):
            pasta = Path.home()/'.local/share/metricool-intervalo'
            pasta.mkdir(parents=True, exist_ok=True)
            with (pasta/('inematds_'+marca+'.publicacao.lock')).open('w') as lock:
                limite = time.monotonic()+timeout
                while True:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() >= limite:
                            raise TimeoutError('trava de publicação ocupada')
                        time.sleep(1)
                return func(*args, **kwargs)
        return executar
    return decorar
