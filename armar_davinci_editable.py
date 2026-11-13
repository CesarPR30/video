"""Genera Demo_Factoring_Editable_DaVinci.fcpxml: la version EDITABLE para DaVinci Resolve.

A diferencia de Demo_Factoring_DaVinci.xml (clips ya renderizados), aqui la camara y los titulos
quedan editables en Resolve:
  V1  grabaciones 4K con keyframes de Zoom y Position (Inspector > Transform) y fondos de titulos
  V2  ventana flotante (escala y fundido) y logo del cierre
  V3  aviso de cifras simuladas
  V4  y V5 titulos de texto editables
  A1 a A3 efectos de sonido; A4 musica estereo

Lee Demo_Factoring_Editable.xml (cortes, disolvencias y audio) y crear_editable.jsx (keyframes y textos),
ambos generados por armar_editable.py. Solo usa la libreria estandar.
Uso: python armar_davinci_editable.py. Ejecutalo de nuevo si mueves la carpeta: las rutas son absolutas.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from xml.sax.saxutils import escape, quoteattr

RAIZ = Path(__file__).resolve().parent
CLIPS = RAIZ / "clips_editable"
ORIGEN = RAIZ / "Demo_Factoring_Editable.xml"
JSX = RAIZ / "crear_editable.jsx"
DESTINO = RAIZ / "Demo_Factoring_Editable_DaVinci.fcpxml"
FPS, W, H = 30, 1920, 1080
FUENTE = ("Segoe UI", "Bold")
FUNDIDO = 6                                   # cuadros de entrada y salida de la ventana
UID_DISOLVENCIA = "FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265"
UID_TITULO = ".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"
CLAVE_POS_TITULO = "9999/999166631/999166633/1/100/101"


def t(cuadros):
    cuadros = int(round(cuadros))
    return "0s" if cuadros == 0 else f"{cuadros}/{FPS}s"


def cuadro(seg):
    return int(round(seg * FPS))


def url(ruta):
    return "file:///" + quote(ruta.as_posix().lstrip("/"), safe="/:")


# ---------------------------------------------------------------- conversion de Premiere a FCPXML
# Premiere: Escala 50 % = 4K encajado en 1080p; Posicion normalizada, 0.5 = centro, y hacia abajo.
# FCPXML: scale 1 = encajado (adjust-conform fit); position en % del alto del cuadro, centro 0, y hacia arriba.
def escala(pct):
    return round(pct / 50.0, 5)


def posicion(px, py):
    return round((px - .5) * W / H * 100, 4), round((.5 - py) * 100, 4)


def curva(modo):
    return ' interp="linear" curve="linear"' if modo == "lineal" else ' interp="ease" curve="smooth"'


def animado(nombre, claves, fmt):
    """claves: [(cuadro local, valor, modo)]. Un solo valor no lleva keyframes."""
    vistos = {}
    for c, v, m in claves:
        vistos[c] = (v, m)
    claves = sorted((c, v, m) for c, (v, m) in vistos.items())
    if len({fmt(v) for _, v, _ in claves}) == 1:
        return None, fmt(claves[0][1])
    k = "".join(f'<keyframe time="{t(c)}" value="{fmt(v)}"{curva(m)}/>' for c, v, m in claves)
    return f'<param name="{nombre}"><keyframeAnimation>{k}</keyframeAnimation></param>', fmt(claves[0][1])


def leer_premiere():
    if not ORIGEN.exists() or not JSX.exists():
        sys.exit(f"Faltan {ORIGEN.name} o {JSX.name}. Generalos con: python armar_editable.py")
    datos = json.loads(re.search(r"var D = (\{.*?\});\n", JSX.read_text(encoding="utf8"), re.S).group(1))
    raiz = ET.parse(ORIGEN).getroot()
    archivos, faltan = {}, []

    def archivo(clip):
        f = clip.find("file")
        if f.find("pathurl") is not None:
            nombre = Path(unquote(urlparse(f.find("pathurl").text).path)).name
            media = f.find("media")
            canales = media.findtext("audio/channelcount") if media is not None else None
            archivos[f.get("id")] = {"nombre": nombre, "dur": int(f.findtext("duration")), "audio": media.find("video") is None,
                                     "canales": int(canales or 1), "png": nombre.lower().endswith(".png")}
            if not (CLIPS / nombre).exists():
                faltan.append(nombre)
        return f.get("id")

    def clips(pista):
        return [{"id": c.get("id"), "nombre": c.findtext("name"), "ini": int(c.findtext("start")), "fin": int(c.findtext("end")),
                 "in": int(c.findtext("in")), "file": archivo(c)} for c in pista.findall("clipitem")]

    video = [clips(p) for p in raiz.findall("./sequence/media/video/track")]
    audio = [clips(p) for p in raiz.findall("./sequence/media/audio/track")]
    disolvencias = [(int(x.findtext("start")), int(x.findtext("end"))) for x in raiz.iter("transitionitem")]
    marcadores = [(m.findtext("name"), int(m.findtext("in"))) for m in raiz.findall("./sequence/marker")]
    if faltan:
        sys.exit(f"No estan en {CLIPS.name}: {', '.join(sorted(set(faltan)))}")
    return datos, archivos, video, audio, disolvencias, marcadores, int(raiz.findtext("./sequence/duration"))


def main():
    datos, archivos, video, audio, disolvencias, marcadores, total = leer_premiere()
    v1, v2, v3 = video[0], video[1], video[2]
    camara = {c["indice"]: c["claves"] for c in datos["clips"]}
    ventanas = {v["nombre"]: v for v in datos["ventanas"]}

    # recursos
    rec = ['<format id="r1" name="FFVideoFormat1080p30" frameDuration="1/30s" width="1920" height="1080"/>',
           '<format id="r2" name="FFVideoFormat2160p30" frameDuration="1/30s" width="3840" height="2160"/>',
           '<format id="r3" name="FFVideoFormatRateUndefined" width="1920" height="1080"/>',
           f'<effect id="e1" name="Cross Dissolve" uid="{UID_DISOLVENCIA}"/>',
           f'<effect id="e2" name="Basic Title" uid="{UID_TITULO}"/>']
    ids = {}
    for fid, a in archivos.items():
        ids[fid] = f"a{len(ids) + 1}"
        src = url(CLIPS / a["nombre"])
        if a["png"]:
            rec.append(f'<asset id="{ids[fid]}" name={quoteattr(a["nombre"])} start="0s" duration="0s" hasVideo="1" format="r3" videoSources="1" src="{src}"/>')
        elif a["audio"]:
            rec.append(f'<asset id="{ids[fid]}" name={quoteattr(a["nombre"])} start="0s" duration="{t(a["dur"])}" hasAudio="1" audioSources="1" '
                       f'audioChannels="{a["canales"]}" audioRate="48000" src="{src}"/>')
        else:
            rec.append(f'<asset id="{ids[fid]}" name={quoteattr(a["nombre"])} start="0s" duration="{t(a["dur"])}" hasVideo="1" format="r2" videoSources="1" src="{src}"/>')

    # cada elemento conectado cuelga del clip de V1 que esta debajo de su inicio
    hijos = {i: [] for i in range(len(v1))}

    def padre(ini):
        return next(i for i, c in enumerate(v1) if c["ini"] <= ini < c["fin"]) if ini < v1[-1]["fin"] else len(v1) - 1

    def colgar(ini, xml_fn):
        i = padre(ini)
        hijos[i].append((ini, xml_fn(v1[i]["in"] + ini - v1[i]["ini"])))

    def blend(claves):
        p, v = animado("amount", claves, lambda x: f"{x:g}")
        return f'<adjust-blend amount="{v}">{p or ""}</adjust-blend>'

    # V2: ventanas flotantes y logo
    for c in v2:
        a, dur = archivos[c["file"]], c["fin"] - c["ini"]
        if c["nombre"] in ventanas:
            vn = ventanas[c["nombre"]]
            pe, ve = animado("scale", [(cuadro(s), escala(v), m) for s, v, m in vn["claves"]], lambda x: f"{x:g} {x:g}")
            ini_l = c["in"]
            op = blend([(ini_l, 0, "bezier"), (ini_l + FUNDIDO, 1, "bezier"), (ini_l + dur - FUNDIDO, 1, "bezier"), (ini_l + dur, 0, "bezier")])
            cuerpo = f'<adjust-transform scale="{ve}">{pe or ""}</adjust-transform>{op}'
            colgar(c["ini"], lambda off, c=c, dur=dur, cuerpo=cuerpo: f'<asset-clip ref="{ids[c["file"]]}" lane="1" offset="{t(off)}" name={quoteattr(c["nombre"])} start="{t(c["in"])}" duration="{t(dur)}" tcFormat="NDF">{cuerpo}</asset-clip>')
        else:                                             # logo: subido como en Premiere y con fundido de 0.5 s
            x, y = posicion(.5, .56)
            op = blend([(0, 0, "bezier"), (cuadro(.5), 1, "bezier")])
            colgar(c["ini"], lambda off, c=c, dur=dur: f'<video ref="{ids[c["file"]]}" lane="1" offset="{t(off)}" name={quoteattr(c["nombre"])} start="0s" duration="{t(dur)}"><adjust-transform position="{x:g} {y:g}"/>{op}</video>')
    # V3: aviso
    for c in v3:
        dur = c["fin"] - c["ini"]
        colgar(c["ini"], lambda off, c=c, dur=dur: f'<video ref="{ids[c["file"]]}" lane="2" offset="{t(off)}" name={quoteattr(c["nombre"])} start="0s" duration="{t(dur)}"/>')
    # V4 y V5: titulos
    usados = set()
    for k, x in enumerate(datos["textos"]):
        carril = 4 if x["ini"] in usados else 3
        usados.add(x["ini"])
        ini, fin = cuadro(x["ini"] + x["ent"]), cuadro(x["ini"] + x["dur"])
        y_px = round((.5 - x["y"]) * H, 1)
        texto = escape(x["t"])

        def titulo(off, k=k, carril=carril, dur=fin - ini, y_px=y_px, texto=texto, x=x):
            return (f'<title ref="e2" lane="{carril}" offset="{t(off)}" name={quoteattr(x["id"] + " " + x["t"][:24])} start="0s" duration="{t(dur)}">'
                    f'<param name="Position" key="{CLAVE_POS_TITULO}" value="0 {y_px:g}"/>'
                    f'<text><text-style ref="ts{k}">{texto}</text-style></text>'
                    f'<text-style-def id="ts{k}"><text-style font="{FUENTE[0]}" fontSize="{x["tam"]}" fontFace="{FUENTE[1]}" fontColor="1 1 1 1" alignment="center"/></text-style-def></title>')
        colgar(ini, titulo)
    # audio: efectos en A1-A3 y la musica estereo en un solo clip (A4)
    pistas_sfx = [p for p in audio if p and not p[0]["id"].startswith("m")]
    for n, p in enumerate(pistas_sfx, 1):
        for c in p:
            dur = c["fin"] - c["ini"]
            colgar(c["ini"], lambda off, c=c, dur=dur, n=n: f'<asset-clip ref="{ids[c["file"]]}" lane="-{n}" offset="{t(off)}" name={quoteattr(c["nombre"])} start="{t(c["in"])}" duration="{t(dur)}" audioRole="effects"/>')
    musica = next(c for p in audio for c in p if c["id"] == "m1")
    dur_m = musica["fin"] - musica["ini"]
    colgar(musica["ini"], lambda off: f'<asset-clip ref="{ids[musica["file"]]}" lane="-{len(pistas_sfx) + 1}" offset="{t(off)}" name="musica_60s" start="{t(musica["in"])}" duration="{t(dur_m)}" audioRole="music"/>')

    # V1: linea principal con camara, marcadores y disolvencias
    marcas = {}
    for nombre, ini in marcadores:
        marcas.setdefault(padre(ini), []).append((ini, nombre))
    espina = []
    for i, c in enumerate(v1):
        dur = c["fin"] - c["ini"]
        transform = ""
        if i in camara:
            k = camara[i]
            pe, ve = animado("scale", [(cuadro(s), escala(e), m) for s, e, px, py, m in k], lambda x: f"{x:g} {x:g}")
            pp, vp = animado("position", [(cuadro(s), posicion(px, py), m) for s, e, px, py, m in k], lambda v: f"{v[0]:g} {v[1]:g}")
            transform = f'<adjust-transform position="{vp}" scale="{ve}">{pp or ""}{pe or ""}</adjust-transform>'
        anclados = "".join(xml for _, xml in sorted(hijos[i], key=lambda h: h[0]))
        mk = "".join(f'<marker start="{t(c["in"] + ini - c["ini"])}" duration="1/30s" value={quoteattr(n)}/>' for ini, n in marcas.get(i, []))
        espina.append(f'<asset-clip ref="{ids[c["file"]]}" offset="{t(c["ini"])}" name={quoteattr(c["nombre"])} start="{t(c["in"])}" duration="{t(dur)}" tcFormat="NDF">{transform}{anclados}{mk}</asset-clip>')
        if i < len(disolvencias):
            a, b = disolvencias[i]
            espina.append(f'<transition name="Cross Dissolve" offset="{t(a)}" duration="{t(b - a)}"><filter-video ref="e1" name="Cross Dissolve"/></transition>')

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="1.8">'
           f'<resources>{"".join(rec)}</resources>'
           '<library><event name="Demo Factoring"><project name="Demo Factoring Editable (DaVinci)">'
           f'<sequence format="r1" duration="{t(total)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k"><spine>{"".join(espina)}</spine></sequence>'
           '</project></event></library></fcpxml>\n')
    arbol = ET.ElementTree(ET.fromstring(xml.split("\n", 2)[2]))
    ET.indent(arbol, space="  ")
    DESTINO.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n' + ET.tostring(arbol.getroot(), encoding="unicode") + "\n", encoding="utf-8")

    guia(v1, camara, datos["textos"])
    n_claves = xml.count("<keyframe ")
    print(f"{DESTINO.name}: {total / FPS:.2f} s, {len(v1)} clips en V1, {len(disolvencias)} disolvencias, "
          f"{len(datos['textos'])} titulos, {n_claves} keyframes, {len(marcadores)} marcadores")


def tc(cuadros):
    return f"{cuadros // FPS // 60:02d}:{cuadros // FPS % 60:02d}:{cuadros % FPS:02d}"


def guia(v1, camara, textos):
    """Tablas de respaldo en GUIA_DAVINCI.md, en las unidades del Inspector de Resolve."""
    def inspector(e, px, py):
        x, y = posicion(px, py)
        return f"{escala(e):.2f}", f"{x * H / 100:.0f}, {y * H / 100:.0f}"
    filas = []
    for i, c in enumerate(v1):
        if i not in camara:
            continue
        k = camara[i]
        z0, p0 = inspector(k[0][1], k[0][2], k[0][3])
        z1, p1 = inspector(k[-1][1], k[-1][2], k[-1][3])
        filas.append(f"| {tc(c['ini'])} | `{c['nombre']}` | {z0} → {z1} | {p0} → {p1} |")
    tit = [f"| {tc(cuadro(x['ini'] + x['ent']))} | {'V5' if i and textos[i - 1]['ini'] == x['ini'] else 'V4'} | {x['t']} | {x['tam']} |" for i, x in enumerate(textos)]
    bloque = ("<!-- EDITABLE -->\n**Cámara** (Inspector > Transform; Zoom 1.00 = pantalla completa, Position en píxeles desde el centro):\n\n"
              "| Inicio | Toma | Zoom | Position X, Y |\n|---|---|---|---|\n" + "\n".join(filas) +
              "\n\n**Títulos** (blanco, Segoe UI Bold, centrados):\n\n| Aparece | Pista | Texto | Tamaño |\n|---|---|---|---|\n" + "\n".join(tit) +
              "\n<!-- /EDITABLE -->")
    p = RAIZ / "GUIA_DAVINCI.md"
    s = p.read_text(encoding="utf8")
    if "<!-- EDITABLE -->" in s:
        p.write_text(re.sub(r"<!-- EDITABLE -->.*<!-- /EDITABLE -->", lambda _: bloque, s, flags=re.S), encoding="utf8")


if __name__ == "__main__":
    main()
