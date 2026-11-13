"""Mide si hay movimientos bruscos, cuadro por cuadro. Uso: python validar.py [carpeta_clips]

- Salto: cambio grande y aislado entre dos cuadros, respecto a los cuadros vecinos.
- Primer cuadro: si el inicio del clip no coincide con lo que sigue (cuadro colado).
- Camara: velocidad maxima de paneo y zoom, si la toma la dejo registrada en su .json.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 240, 135
SALTO_MIN, SALTO_RATIO = 5.0, 5.0     # cambio medio en niveles de gris (0-255) y veces sobre los vecinos
PANEO_MAX, ZOOM_MAX = 70.0, 1.0       # % de pantalla por segundo, y log-zoom por segundo


def cuadros(ruta):
    o = subprocess.run([FF, "-loglevel", "error", "-i", str(ruta), "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return np.frombuffer(o, np.uint8).reshape(-1, H, W).astype(np.float32)


def revisar(ruta, cabeza=0):
    """cabeza: cuadros congelados al inicio, solo existen para la disolvencia y no cuentan como vecinos."""
    c = cuadros(ruta)[cabeza:]; d = np.abs(np.diff(c, axis=0)).mean((1, 2)); saltos = []
    for i, v in enumerate(d):
        ini = max(0, i - 8); vec = np.r_[d[ini:max(0, i - 1)], d[i + 2:i + 10]]
        base = float(np.median(vec)) if vec.size else 0
        if v >= SALTO_MIN and v >= SALTO_RATIO * max(base, .3): saltos.append((i, round(float(v), 1)))
    return c.shape[0], round(float(d.max()), 1), saltos


def main():
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "clips_60s"
    if destino.is_file():
        n, m, saltos = revisar(destino)
        print(f"{destino.name}: {n} cuadros = {n / 30:.2f} s, cambio maximo {m}, saltos aislados: {saltos or 'ninguno'}")
        return
    carpeta = destino
    total = 0
    print(f"{'toma':18}{'cuadros':>8}{'max':>7}{'paneo':>8}{'zoom':>7}  observaciones")
    for mp4 in sorted(carpeta.glob("*.mp4")):
        j = mp4.with_suffix(".json"); info = json.loads(j.read_text(encoding="utf8")) if j.exists() else {}
        n, m, saltos = revisar(mp4, info.get("cabeza", 0))
        pan, zoom = info.get("paneo_max", 0), info.get("zoom_max", 0)
        obs = []
        if saltos: obs.append("SALTOS " + ", ".join(f"c{i}={v}" for i, v in saltos[:5]))
        if pan > PANEO_MAX: obs.append("paneo rapido")
        if zoom > ZOOM_MAX: obs.append("zoom rapido")
        total += bool(obs)
        print(f"{mp4.stem:18}{n:>8}{m:>7}{pan:>8}{zoom:>7}  {'; '.join(obs) or 'ok'}")
    print(f"\ntomas con observaciones: {total}")


if __name__ == "__main__":
    main()
