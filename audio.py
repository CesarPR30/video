"""Musica original y efectos, sintetizados aqui mismo: no hay muestras ni licencias de terceros.

Musica: 120 BPM en Re mayor, 60 s. La estructura sigue al video: entra de a pocos, crece en el
Simulador, llega a su punto alto en Quienes/Por que, respira en la frase para el jurado y resuelve
en el cierre. Uso: python audio.py
"""
import re, subprocess, wave
import numpy as np
from motor import CLIPS, FFMPEG

SR, DUR = 48000, 60.0
N = int(SR * DUR)
rng = np.random.default_rng(2026)
ACORDES = {"Bm": ([50, 54, 57, 61], 35), "G": ([50, 55, 59, 62], 31), "D": ([50, 54, 57, 62], 38), "A": ([49, 52, 57, 61], 33)}
FORMA = [(0, "Bm"), (4, "G"), (8, "D"), (12, "A"), (16, "Bm"), (20, "G"), (24, "D"), (28, "A"), (32, "Bm"), (36, "G"), (40, "D"), (44, "A"), (48, "G"), (52, "A"), (56, "A"), (58, "D")]
FIN_FORMA = [t for t, _ in FORMA[1:]] + [62]

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def curva(puntos, t): return np.interp(t, *zip(*puntos))
def lienzo(): return np.zeros((N + SR * 3, 2))

def poner(b, t, x, pan=0.):
    i = int(t * SR)
    if i >= b.shape[0]: return
    x = x[:b.shape[0] - i]
    b[i:i + x.size, 0] += x * np.cos((pan + 1) * np.pi / 4)
    b[i:i + x.size, 1] += x * np.sin((pan + 1) * np.pi / 4)

def wav(ruta, x):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1 if y.ndim == 1 else 2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())

def lufs(ruta):
    o = subprocess.run([FFMPEG, "-hide_banner", "-i", str(ruta), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1]); p = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)[-1])
    return i, p

# ---------- musica ----------
def pad():
    bajo, alto = lienzo(), lienzo()
    for (t0, nombre), t1 in zip(FORMA, FIN_FORMA):
        dur = t1 - t0 + 1.0; n = int(dur * SR); t = np.arange(n) / SR
        env = np.minimum(t / .6, 1) * np.minimum((dur - t) / 1.0, 1) ** 1.5
        for m in ACORDES[nombre][0]:
            for k, (cents, pan) in enumerate(((-5, -.6), (5, .6))):
                f = hz(m) * 2 ** (cents / 1200); fase = rng.uniform(0, 6.28)
                poner(bajo, t0, sum(np.sin(2 * np.pi * f * h * t + fase * h) / h ** 1.4 for h in (1, 2, 3)) * env, pan)
                poner(alto, t0, sum(np.sin(2 * np.pi * f * h * t + fase * h) / h ** 1.1 for h in (4, 5, 6, 8)) * env, pan)
    return bajo, alto

def pluck():
    b = lienzo(); patron = [0, 2, 1, 3, 2, 1, 3, 2]
    for i, t in enumerate(np.arange(6, 58, .25)):
        nombre = next(n for (a, n), z in zip(FORMA, FIN_FORMA) if a <= t < z)
        nota = sorted(ACORDES[nombre][0])[patron[i % 8]] + 24
        d = .55; x = np.arange(int(d * SR)) / SR; f = hz(nota)
        s = (np.sin(2 * np.pi * f * x) + .28 * np.sin(4 * np.pi * f * x) * np.exp(-x * 14)) * np.exp(-x * 8) * np.minimum(x / .004, 1)
        poner(b, t, s * (1 if i % 4 == 0 else .72) * rng.uniform(.88, 1), .35 * np.sin(i * .7))
    return b

def bajo_linea():
    b = lienzo()
    for i, t in enumerate(np.arange(18, 58, .25)):
        if 51 <= t < 56: continue
        nombre = next(n for (a, n), z in zip(FORMA, FIN_FORMA) if a <= t < z)
        f = hz(ACORDES[nombre][1] + 12); x = np.arange(int(.23 * SR)) / SR
        s = (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x)) * np.minimum(x / .006, 1) * np.minimum((.23 - x) / .05, 1)
        poner(b, t, s * (.75 if i % 2 == 0 else 1))
    return b

def bateria():
    b = lienzo(); golpes = []
    def bombo(t, v):
        x = np.arange(int(.32 * SR)) / SR
        fase = 2 * np.pi * np.cumsum(46 + 100 * np.exp(-x * 34)) / SR
        poner(b, t, np.sin(fase) * np.exp(-x * 11) * v); golpes.append(t)
    for t in np.arange(6, 18, 1.0): bombo(t, .45)
    for t in np.arange(18, 51, .5): bombo(t, .85 if t < 32 else 1)
    for t in (56, 56.5, 57, 57.5): bombo(t, .75)
    bombo(58, 1.)
    for t in np.arange(32.25, 51, .5):
        x = np.arange(int(.07 * SR)) / SR
        poner(b, t, np.diff(rng.normal(size=x.size + 1)) * np.exp(-x * 75) * .13, .25)
    for t in np.arange(32.5, 51, 1.0):
        x = np.arange(int(.22 * SR)) / SR
        poner(b, t, np.diff(rng.normal(size=x.size + 1)) * np.exp(-x * 24) * .2, -.15)
    return b, golpes

def eco(x, seg=.375, g=.34, veces=4):
    y = x.copy(); d = int(seg * SR)
    for k in range(1, veces + 1):
        c = k % 2
        y[d * k:, c] += x[:-d * k, 0 if c else 1] * g ** k
    return y

def reverb(x, largo=1.5):
    n = int(largo * SR); t = np.arange(n) / SR; salida = np.zeros_like(x); tam = 1 << int(np.ceil(np.log2(x.shape[0] + n)))
    for c in range(2):
        ir = rng.normal(size=n) * np.exp(-t * 5.2)
        salida[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], tam) * np.fft.rfft(ir / np.sqrt((ir ** 2).sum()), tam), tam)[:x.shape[0]]
    return salida

def musica():
    pb, pa = pad(); pl = pluck(); ba = bajo_linea(); dr, golpes = bateria()
    t = np.arange(pb.shape[0]) / SR
    bomba = np.ones(t.size)                                     # el pad respira con el bombo
    for g in golpes:
        i = int(g * SR); j = min(i + SR // 3, t.size)
        bomba[i:j] = np.minimum(bomba[i:j], 1 - .38 * np.exp(-(t[i:j] - g) / .11))
    g_alto = curva([(0, .10), (18, .22), (32, .55), (51, .8), (56, .5), (58, .9), (64, .9)], t)
    g_pad = curva([(0, 0), (1.2, .85), (32, 1), (64, 1)], t)
    g_pl = curva([(0, 0), (5.9, 0), (6, .34), (18, .55), (32, .72), (51, .78), (56, .5), (58, .7), (64, .7)], t)
    p = (pb * g_pad[:, None] * .075 + pa * (g_alto * g_pad)[:, None] * .05) * bomba[:, None]
    q = eco(pl * g_pl[:, None] * .17)
    mezcla = p + q + ba * .2 * bomba[:, None] + dr * .42
    mezcla += reverb(p * .55 + q * .5 + dr * .05)
    mezcla = mezcla[:N]
    tt = t[:N]; mezcla *= curva([(0, 1), (58.5, 1), (60, 0)], tt)[:, None] ** 1.5
    mezcla[:SR // 50] *= np.linspace(0, 1, SR // 50)[:, None]
    mezcla = np.tanh(mezcla * 1.15) / 1.15
    mezcla /= np.abs(mezcla).max() / .7
    r = CLIPS / "musica_60s.wav"; wav(r, mezcla)
    i, _ = lufs(r); mezcla *= 10 ** ((-17.5 - i) / 20)           # deja lugar a los efectos
    wav(r, mezcla); return lufs(r)


# ---------- efectos ----------
def golpe(d, f, dec, v):
    t = np.arange(int(SR * d)) / SR
    return (np.sin(2 * np.pi * f * t) * .55 + np.diff(rng.normal(size=t.size + 1)) * .12) * np.exp(-t * dec) * v

def soplo(d, pico, c0, c1, v):
    n = int(d * SR); t = np.arange(n) / SR; ruido = rng.normal(size=n); y = np.zeros(n); e = 0.
    corte = c0 + (c1 - c0) * np.sin(np.minimum(t / d / pico, 1) * np.pi / 2) ** 2
    corte = np.where(t / d > pico, c1 + (c0 - c1) * ((t / d - pico) / (1 - pico)), corte)
    for i in range(n):
        e += corte[i] * (ruido[i] - e); y[i] = e
    env = np.where(t / d < pico, (t / d / pico) ** 2, ((1 - t / d) / (1 - pico)) ** 2.4)
    return y * env * v / (np.abs(y * env).max() + 1e-9)

# dB, ajustados midiendo cada efecto contra la musica que suena debajo
GANANCIA = {"clic": 4.5, "tecleo": 8.5, "whoosh": 5.5, "ficha": 4.5, "pop": 4.5, "slider": 14.5, "burbujas": 8.5, "cierre": 3.5}

def efectos():
    d = {}
    c = golpe(.05, 2100, 150, .3); c[int(.016 * SR):] += golpe(.05, 1500, 170, .2)[:c.size - int(.016 * SR)]
    d["clic"] = c
    n = len("¿A qué empresas debemos contactar?"); p = np.zeros(int(SR * (.4 + .042 * n + .15)))
    for i in range(n):
        g = golpe(.028, rng.uniform(2200, 3100), 210, rng.uniform(.1, .17)); a = int(SR * (.4 + .042 * i + rng.uniform(-.004, .004)))
        p[a:a + g.size] += g
    d["tecleo"] = p
    d["whoosh"] = soplo(.55, .62, .02, .22, .26)
    d["ficha"] = soplo(.7, .5, .012, .12, .24)
    t = np.arange(int(.12 * SR)) / SR
    d["pop"] = np.sin(2 * np.pi * np.cumsum(330 + 300 * np.minimum(t / .05, 1)) / SR) * np.exp(-t * 34) * np.minimum(t / .003, 1) * .2
    s = np.zeros(int(2.3 * SR)); u = 0.
    while u < 2.2:
        k = u / 2.2; g = golpe(.016, 1050 + 380 * k, 330, .07); a = int(u * SR); s[a:a + g.size] += g[:s.size - a]
        u += .05 + .025 * np.sin(k * np.pi)
    d["slider"] = s
    b = np.zeros(int(1.6 * SR)); penta = [74, 76, 78, 81, 83, 86, 88]
    for _ in range(22):
        u = rng.uniform(0, 1.3) ** 1.2; f = hz(rng.choice(penta)); t = np.arange(int(.09 * SR)) / SR
        g = np.sin(2 * np.pi * f * t) * np.exp(-t * 48) * np.minimum(t / .002, 1) * rng.uniform(.03, .075); a = int(u * SR); b[a:a + g.size] += g
    d["burbujas"] = b
    t = np.arange(int(2.0 * SR)) / SR; e = np.zeros(t.size)
    for m, v in ((62, .6), (69, .5), (74, .55), (78, .35), (81, .3), (86, .16)):
        f = hz(m); e += sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * (2.4 + q * r)) for r, a, q in ((1, 1, .4), (2.76, .3, .9), (5.4, .1, 1.4))) * v
    d["cierre"] = e * np.minimum(t / .004, 1) * np.minimum((2 - t) / .4, 1) * .11
    d = {k: x * 10 ** (GANANCIA[k] / 20) for k, x in d.items()}
    for k, x in d.items(): wav(CLIPS / f"sfx_{k}.wav", x)
    return {k: x.size / SR for k, x in d.items()}


if __name__ == "__main__":
    print("efectos", {k: round(v, 2) for k, v in efectos().items()})
    print("musica LUFS, pico:", musica())
