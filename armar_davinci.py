"""Genera Demo_Factoring_DaVinci.xml para importarlo en DaVinci Resolve (gratis).

Parte de Demo_Factoring_60s.xml (la version renderizada) y hace tres cambios:
  1. Apunta cada archivo a la carpeta donde esta este script. Ejecutalo en cada computadora
     despues de clonar o mover la carpeta: las rutas del XML son absolutas.
  2. Deja la musica como un solo clip estereo. Premiere la parte en dos pistas mono
     enlazadas, y Resolve podria duplicarla.
  3. Quita los atributos propios de Premiere.

Solo usa la libreria estandar de Python. Uso: python armar_davinci.py
Pasos en DaVinci: ver GUIA_DAVINCI.md.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

RAIZ = Path(__file__).resolve().parent
ORIGEN = RAIZ / "Demo_Factoring_60s.xml"
DESTINO = RAIZ / "Demo_Factoring_DaVinci.xml"
CARPETAS = ["clips_60s"]          # donde buscar cada archivo por su nombre
FPS = 30


def url_local(ruta):
    return "file://localhost/" + quote(ruta.as_posix().lstrip("/"), safe="/:")


def main():
    if not ORIGEN.exists():
        sys.exit(f"Falta {ORIGEN.name}. Generalo con: python armar_premiere.py")
    arbol = ET.parse(ORIGEN)
    raiz = arbol.getroot()

    faltan = []
    for p in raiz.iter("pathurl"):
        nombre = Path(unquote(urlparse(p.text).path)).name
        ruta = next((RAIZ / c / nombre for c in CARPETAS if (RAIZ / c / nombre).exists()), None)
        if ruta is None:
            faltan.append(nombre)
            continue
        p.text = url_local(ruta)
    if faltan:
        sys.exit(f"No se encontraron en {', '.join(CARPETAS)}: {', '.join(sorted(set(faltan)))}")

    audio = raiz.find("./sequence/media/audio")
    for pista in list(audio.findall("track")):
        ids = [c.get("id") for c in pista.findall("clipitem")]
        if ids == ["m2"]:
            audio.remove(pista)          # segundo canal de la musica: el clip m1 ya es estereo
            continue
        for clip in pista.findall("clipitem"):
            for enlace in clip.findall("link"):
                clip.remove(enlace)
        for attr in ("currentExplodedTrackIndex", "totalExplodedTrackCount", "premiereTrackType"):
            pista.attrib.pop(attr, None)
        sal = pista.find("outputchannelindex")
        if sal is not None:
            pista.remove(sal)

    seq = raiz.find("sequence")
    seq.find("name").text = "Demo Factoring 60s (DaVinci)"
    ET.indent(arbol, space="  ")
    cuerpo = ET.tostring(raiz, encoding="unicode")
    DESTINO.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + cuerpo + "\n", encoding="utf-8")

    total = int(seq.find("duration").text)
    pistas_v = len(raiz.findall("./sequence/media/video/track"))
    pistas_a = len(raiz.findall("./sequence/media/audio/track"))
    clips = len(list(raiz.iter("clipitem")))
    disolvencias = len(list(raiz.iter("transitionitem")))
    print(f"{DESTINO.name}: {total / FPS:.2f} s a {FPS} fps, {pistas_v} pistas de video, {pistas_a} de audio, "
          f"{clips} clips, {disolvencias} disolvencias")
    print(f"Archivos en: {RAIZ / CARPETAS[0]}")


if __name__ == "__main__":
    main()
