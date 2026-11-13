"""Arma el proyecto EDITABLE: la camara, la ventana flotante y los titulos son nativos de Premiere.

Pistas: V1 grabaciones y fondos · V2 ventana flotante y logo · V3 aviso · V4 y V5 texto
        A1-A2 efectos · A3 musica
Salida: Demo_Factoring_Editable.xml, crear_editable.jsx, editable_textos.json y GUIA_PREMIERE.md
Los pasos completos estan en construir_editable.ps1.
"""
import json, math, os, re, shutil, sys
os.environ["VIDEO_MODO"] = "editable"
from pathlib import Path
import numpy as np
from xml.sax.saxutils import escape
import motor
from motor import COLA, CLIPS, FPS, RAIZ, VW, VH
from tomas import DURACION

BASE = RAIZ / "clips_60s"           # musica y efectos ya mezclados
NOMBRE = "Demo_Factoring_Editable"
ESCALA_BASE = 50.0                  # grabacion 4K en secuencia 1080p: 100 % = zoom 2x sin perder nitidez
VENTANA = ("ventana_resumen", "ventana_cierre")
FUENTE = "SegoeUI-Bold"

# Titulos: (texto, tamano, y, segundo de entrada dentro de la toma, tipo de entrada)
def cifras():
    def lee(n): return json.loads(re.search(r"=\s*(\{.*\});?\s*$", (RAIZ.parent / "dashboard" / "inputs" / f"{n}.js").read_text(encoding="utf8").split(f"window.DASH.{n}", 1)[1], re.S).group(1))
    return lee("meta"), lee("resumen")

def titulos():
    meta, res = cifras()
    return {
        "t_pregunta": ("fondo_navy", [("¿A qué empresas debemos contactar?", 84, .5, .15, "tecleo")]),
        "t_cifras": ("fondo_navy", [(f"{res['embudo']['evaluables']:,} empresas evaluadas.", 80, .44, .05, "sube"),
                                    (f"Solo {meta['supuestos']['capacidad_contactos']:,} contactos por campaña.", 80, .56, 1.5, "sube")]),
        "t_cuanto": ("fondo_navy", [("¿Cuánto?", 190, .47, 0, "golpe"), ("Base habilitada", 52, .63, .12, "sube")]),
        "t_simula": ("fondo_naranja", [("¿Y si cambia?", 180, .47, 0, "golpe"), ("La capacidad comercial", 52, .63, .12, "sube")]),
        "t_quienes": ("fondo_navy", [("¿Quiénes?", 190, .47, 0, "golpe"), ("Probabilidad de conversión", 52, .63, .12, "sube")]),
        "t_porque": ("fondo_naranja", [("¿Por qué?", 190, .47, 0, "golpe"), ("Sustento de negocio", 52, .63, .12, "sube")]),
        "t_cierre": ("fondo_navy", [("¿Cuánto?    ¿Quiénes?    ¿Por qué?", 88, .42, .1, "sube"), ("Campaña de factoring · DataFest 2026", 38, .68, .9, "sube")]),
    }


def clamp_cam(cx, cy, z):
    w, h = VW / z, VH / z
    return min(max(cx, w / 2), VW - w / 2), min(max(cy, h / 2), VH - h / 2)

def a_premiere(v):
    """(cx, cy, log zoom) en pixeles del dashboard -> escala y posicion de Movimiento."""
    z = math.exp(v[2]); cx, cy = clamp_cam(v[0], v[1], z)
    return round(ESCALA_BASE * z, 3), round(.5 + (.5 - cx / VW) * z, 5), round(.5 + (.5 - cy / VH) * z, 5)

def claves_camara(info):
    """Keyframes en cuadros de la toma. Un tramo de un cuadro es el encuadre inicial, no una animacion."""
    v = tuple(info["cam"]["v0"]); salida = [(0, v, "bezier")]
    for ini, dur, dest, ease in info["cam"]["tramos"]:
        dest = tuple(dest)
        if dur <= 1:
            salida = [(k, dest if k == 0 else w, m) for k, w, m in salida] if ini == 0 else salida + [(ini, dest, "bezier")]
            v = dest; continue
        fin = min(ini + dur, info["cuadros"])
        if fin < ini + dur:                       # el clip se corta antes: se calcula el valor al cortar
            t = (fin - ini) / dur; e = motor.EASES[ease](t); dest = tuple(a + (b - a) * e for a, b in zip(v, dest))
        modo = "lineal" if ease == "lin" else "bezier"
        salida = [(k, w, m) for k, w, m in salida if k != ini] + [(ini, v, modo), (fin, dest, modo)]
        v = dest
    return salida


def main():
    infos = {}
    for n in DURACION:
        if n.startswith("t_"): continue
        j = CLIPS / f"{n}.json"
        if not j.exists(): sys.exit(f"Falta la grabacion {n}: correr tomas.py en modo editable")
        infos[n] = json.loads(j.read_text(encoding="utf8"))
        if infos[n]["cuadros"] != round(DURACION[n] * FPS): sys.exit(f"{n}: {infos[n]['cuadros']} cuadros")
    for f in BASE.glob("sfx_*.wav"): shutil.copy2(f, CLIPS / f.name)
    shutil.copy2(BASE / "musica_60s.wav", CLIPS / "musica_60s.wav")

    import armar_premiere as ap
    ap.CLIPS = CLIPS
    W, H = 3840, 2160
    def fvideo(fid, ruta, dur, w=W, h=H):
        return ap.file_video(fid, ruta, dur).replace(f"<width>{motor.OW}</width>", f"<width>{w}</width>").replace(f"<height>{motor.OH}</height>", f"<height>{h}</height>") if (w, h) != (motor.OW, motor.OH) else ap.file_video(fid, ruta, dur)

    tit = titulos(); v1, v2, marcas, cortes, largos = [], [], [], [], []
    vistos = set(); datos = {"clips": [], "ventanas": [], "textos": [], "fps": FPS, "cola": COLA, "escala_base": ESCALA_BASE}
    t = 0; nombres = list(DURACION); ini_av = fin_av = None
    FONDOS = {}
    def fuente(n):
        return tit[n][0] if n in tit else ("fondo_navy" if n in VENTANA else n)
    for k, n in enumerate(nombres):
        c = round(DURACION[n] * FPS); src = fuente(n); largo_src = json.loads((CLIPS / f"{src}.json").read_text(encoding="utf8"))["cuadros"] + 2 * COLA
        fid = f"f_{src}"
        ref = f'<file id="{fid}"/>' if fid in vistos else fvideo(fid, CLIPS / f"{src}.mp4", largo_src)
        vistos.add(fid)
        v1.append(f'<clipitem id="v_{n}"><name>{n if n not in VENTANA else src}</name><enabled>TRUE</enabled><duration>{largo_src}</duration>{ap.rate()}<start>{t}</start><end>{t + c}</end><in>{COLA}</in><out>{COLA + c}</out>{ref}</clipitem>')
        if n in ap.SECCIONES: marcas.append(f"<marker><name>{escape(ap.SECCIONES[n])}</name><comment></comment><in>{t}</in><out>-1</out></marker>")
        if n == ap.PRIMERA_CON_CIFRAS: ini_av = t
        if n in infos and n not in VENTANA:
            datos["clips"].append({"nombre": n, "indice": k, "claves": [[(COLA + f) / FPS, *a_premiere(v), m] for f, v, m in claves_camara(infos[n])]})
        if n in VENTANA:
            lg = infos[n]["cuadros"] + 2 * COLA
            v2.append(f'<clipitem id="w_{n}"><name>{n}</name><enabled>TRUE</enabled><duration>{lg}</duration>{ap.rate()}<start>{t}</start><end>{t + c}</end><in>{COLA}</in><out>{COLA + c}</out>{fvideo("f_" + n, CLIPS / (n + ".mp4"), lg)}</clipitem>')
            tr = infos[n]["ven"]; vals = [(0, tr["v0"][0], "bezier")]
            cl = [(0, tr["tramos"][0][2][0], "bezier")] if tr["tramos"] and tr["tramos"][0][1] <= 1 else vals
            for a, b, val, e in tr["tramos"]:
                if b <= 1: continue
                fin = min(a + b, c); cl += [(a, cl[-1][1], "bezier"), (fin, val[0] if fin == a + b else cl[-1][1] + (val[0] - cl[-1][1]) * motor.EASES[e]((fin - a) / b), "bezier")]
            datos["ventanas"].append({"nombre": n, "ini": t / FPS, "dur": c / FPS, "claves": [[(COLA + f) / FPS, round(ESCALA_BASE * s, 3), m] for f, s, m in cl], "in": COLA / FPS})
        if n in tit:
            for texto, tam, y, ent, tipo in tit[n][1]:
                datos["textos"].append({"t": texto, "tam": tam, "y": y, "ini": t / FPS, "dur": c / FPS, "ent": ent, "tipo": tipo})
        if n == ap.ULTIMA_CON_CIFRAS: fin_av = t + c
        t += c
        if k < len(nombres) - 1: cortes.append(t)
    total = t

    def luz(n):
        return "claro" if n in infos and n not in VENTANA and n not in ("hero_kpis", "pitch") else ("naranja" if n in tit and tit[n][0] == "fondo_naranja" else "oscuro")
    largos = [ap.DISOLVENCIA_LARGA if luz(a) != luz(b) else ap.DISOLVENCIA for a, b in zip(nombres, nombres[1:])]
    cuerpo = []
    for k, clip in enumerate(v1):
        cuerpo.append(clip)
        if k < len(cortes): cuerpo.append(ap.disolvencia(cortes[k], largos[k]))

    t_c = sum(round(DURACION[n] * FPS) for n in nombres[:-1]); cc = round(DURACION["t_cierre"] * FPS); ini_logo = t_c + 15; dl = cc - 15
    v2.append(f'<clipitem id="logo"><name>logo_bcp</name><enabled>TRUE</enabled><duration>{dl}</duration>{ap.rate()}<start>{ini_logo}</start><end>{t_c + cc}</end><in>0</in><out>{dl}</out><stillframe>TRUE</stillframe>{fvideo("f_logo", CLIPS / "logo_bcp.png", dl, 1920, 1080)}</clipitem>')
    d = fin_av - ini_av
    v3 = (f'<clipitem id="aviso"><name>aviso_simulado</name><enabled>TRUE</enabled><duration>{d}</duration>{ap.rate()}<start>{ini_av}</start><end>{fin_av}</end><in>0</in><out>{d}</out><stillframe>TRUE</stillframe>{fvideo("f_aviso", CLIPS / "aviso_simulado.png", d, 1920, 1080)}</clipitem>')

    # audio: mismas pistas que la version de 60 s
    x60 = (RAIZ / "Demo_Factoring_60s.xml").read_text(encoding="utf8")
    audio = re.search(r"<audio><numOutputChannels>.*</audio>(?=</media></sequence>)", x60, re.S).group(0).replace(quote_ruta(BASE), quote_ruta(CLIPS))
    fmt = f"<format><samplecharacteristics>{ap.rate()}<width>1920</width><height>1080</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance><colordepth>24</colordepth></samplecharacteristics></format>"
    pista = lambda c: f"<track>{c}<enabled>TRUE</enabled><locked>FALSE</locked></track>"
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq1"><name>Demo Factoring Editable</name><duration>{total}</duration>{ap.rate()}'
           f'<timecode>{ap.rate()}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode><in>-1</in><out>-1</out>{"".join(marcas)}'
           f'<media><video>{fmt}{pista("".join(cuerpo))}{pista("".join(v2))}{pista(v3)}{pista("")}{pista("")}</video>{audio}</media></sequence></xmeml>\n')
    (RAIZ / f"{NOMBRE}.xml").write_text(xml, encoding="utf8")
    datos["logo_ini"] = ini_logo / FPS
    for i, x in enumerate(datos["textos"]): x["id"] = f"T{i:02d}"
    (RAIZ / "editable_textos.json").write_text(json.dumps(datos["textos"], ensure_ascii=False, indent=1), encoding="utf8")
    plantilla = (RAIZ / "editable_plantilla.jsx").read_text(encoding="utf8")
    (RAIZ / "crear_editable.jsx").write_text(plantilla.replace("/*DATOS*/null", json.dumps(datos, ensure_ascii=True)), encoding="utf8")
    print(f"{NOMBRE}.xml: {total / FPS:.2f} s; {len(datos['clips'])} clips con camara, {sum(len(c['claves']) for c in datos['clips'])} keyframes, {len(datos['textos'])} textos, {largos.count(ap.DISOLVENCIA_LARGA)} disolvencias largas")
    guia(datos, nombres)


def quote_ruta(p):
    from urllib.parse import quote
    return quote(Path(p).resolve().as_posix(), safe="/").replace("%3A", "%3a", 1)


def tc(seg):
    f = round(seg * FPS); return f"{f // FPS // 60:02d}:{f // FPS % 60:02d}:{f % FPS:02d}"


def guia(datos, nombres):
    t, filas = 0, []
    por = {c["nombre"]: c for c in datos["clips"]}
    for n in nombres:
        d = DURACION[n]
        if n in por:
            cl = por[n]["claves"]; a, b = cl[0], cl[-1]
            filas.append(f"| {tc(t)} | {d:g} s | `{n}` | {a[1]:.0f} % → {b[1]:.0f} % | {a[2] * 1920:.0f}, {a[3] * 1080:.0f} → {b[2] * 1920:.0f}, {b[3] * 1080:.0f} |")
        elif n in VENTANA: filas.append(f"| {tc(t)} | {d:g} s | `{n}` | ventana flotante | ver Movimiento en V2 |")
        else: filas.append(f"| {tc(t)} | {d:g} s | `{n}` | título | texto en V4 y V5 |")
        t += d
    p = RAIZ / "GUIA_PREMIERE.md"; s = p.read_text(encoding="utf8")
    (p.write_text(re.sub(r"<!-- TOMAS -->.*<!-- /TOMAS -->", "<!-- TOMAS -->\n| Inicio | Dura | Toma | Escala | Posición (x, y) |\n|---|---|---|---|---|\n" + "\n".join(filas) + "\n<!-- /TOMAS -->", s, flags=re.S), encoding="utf8"))


if __name__ == "__main__":
    main()
