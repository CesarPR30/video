"""Arma la secuencia de Premiere (FCP XML) y una previa con la mezcla completa.

Pistas: V1 tomas con disolvencias · V2 aviso de cifras simuladas (borrar con el modelo real)
A1-A2 efectos · A3-A4 musica estereo. Uso: python audio.py && python armar_premiere.py
"""
import json, subprocess, sys, wave
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape
import numpy as np
from audio import SR, lufs, wav
from motor import CLIPS, COLA, FFMPEG, FPS, OW, OH, RAIZ
from tomas import DURACION

NOMBRE = "Demo_Factoring_60s"
DISOLVENCIA, DISOLVENCIA_LARGA = 6, 12    # cuadros, centrada en cada corte
CONTRASTE_ALTO = 110                     # cambio medio de luz entre tomas (0-255) que pide la larga
SECCIONES = {"t_pregunta": "Pregunta", "ventana_resumen": "Resumen", "t_cuanto": "¿Cuánto?", "t_simula": "Simulador",
             "t_quienes": "¿Quiénes?", "t_porque": "¿Por qué?", "pitch": "Frase para el jurado", "t_cierre": "Cierre"}
LARGO_SLIDER = {"sim_slider": 1.9, "sim_tiles": 1.6, "sim_curva": 1.8}
PRIMERA_CON_CIFRAS, ULTIMA_CON_CIFRAS = "t_cifras", "ventana_cierre"


def rate(): return f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"

def url_archivo(p):
    return "file://localhost/" + quote(Path(p).resolve().as_posix(), safe="/").replace("%3A", "%3a", 1)

def largo_wav(p):
    with wave.open(str(p)) as w: return w.getnframes() / w.getframerate()

def file_video(fid, ruta, dur):
    v = f"<video><samplecharacteristics>{rate()}<width>{OW}</width><height>{OH}</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></video>"
    return f'<file id="{fid}"><name>{escape(Path(ruta).name)}</name><pathurl>{url_archivo(ruta)}</pathurl>{rate()}<duration>{dur}</duration><media>{v}</media></file>'

def file_audio(fid, ruta, dur, canales):
    a = f"<audio><samplecharacteristics><depth>16</depth><samplerate>{SR}</samplerate></samplecharacteristics><channelcount>{canales}</channelcount></audio>"
    return f'<file id="{fid}"><name>{escape(Path(ruta).name)}</name><pathurl>{url_archivo(ruta)}</pathurl>{rate()}<duration>{dur}</duration><media>{a}</media></file>'

def duraciones_disolvencia(infos):
    """Los cortes entre fondo oscuro y claro llevan una disolvencia mas larga."""
    def cuadro(nombre, n):
        o = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(CLIPS / f"{nombre}.mp4"), "-vf", "scale=96:54", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        return np.frombuffer(o, np.uint8).reshape(-1, 54, 96)[n].astype(float)
    out = []
    for a, b in zip(infos, infos[1:]):
        d = np.abs(cuadro(a["nombre"], COLA + a["cuadros"] - 1) - cuadro(b["nombre"], COLA)).mean()
        out.append(DISOLVENCIA_LARGA if d >= CONTRASTE_ALTO else DISOLVENCIA)
    return out


def disolvencia(corte, cuadros):
    m = cuadros // 2
    return (f"<transitionitem><start>{corte - m}</start><end>{corte + m}</end><alignment>center</alignment>{rate()}"
            "<effect><name>Cross Dissolve</name><effectid>Cross Dissolve</effectid><effectcategory>Dissolve</effectcategory><effecttype>transition</effecttype>"
            "<mediatype>video</mediatype><wipecode>0</wipecode><wipeaccuracy>100</wipeaccuracy><startratio>0</startratio><endratio>1</endratio><reverse>FALSE</reverse></effect></transitionitem>")


def cue_lista(infos):
    """Lista de (efecto, cuadro de inicio, largo en cuadros o None)."""
    ev, t = [], 0
    for i in infos:
        n = i["nombre"]
        if n == "t_pregunta": ev.append(("tecleo", t, None))
        if n in ("t_cuanto", "t_simula", "t_quienes", "t_porque"): ev += [("whoosh", t - 11, None), ("pop", t, None)]
        if n == "ventana_resumen": ev.append(("ficha", t + 30, None))
        if n == "ventana_cierre": ev.append(("whoosh", t + 16, None))
        if n in ("lista_mapa", "red_grafo"): ev.append(("burbujas", t + 3, None))
        if n == "lista_ficha": ev.append(("ficha", t - 3, None))
        if n == "t_cierre": ev.append(("cierre", t + 15, None))
        for tipo, c in i["eventos"]:
            if tipo == "click": ev.append(("clic", t + c + 2, None))
            if tipo == "slider": ev.append(("slider", t + c, round(LARGO_SLIDER[n] * FPS)))
        t += i["cuadros"]
    return sorted((e for e in ev if e[1] >= 0), key=lambda e: e[1])


def main():
    infos = []
    for n, seg in DURACION.items():
        j = CLIPS / f"{n}.json"
        if not j.exists(): sys.exit(f"Falta la toma {n}: correr tomas.py")
        i = json.loads(j.read_text(encoding="utf8"))
        if i["cuadros"] != round(seg * FPS): sys.exit(f"{n} dura {i['cuadros']} cuadros, no {seg} s")
        infos.append(i)

    v1, marcadores, cortes, t = [], [], [], 0
    largos = duraciones_disolvencia(infos)
    ini_av = fin_av = None
    for k, i in enumerate(infos):
        n, c = i["nombre"], i["cuadros"]; largo = c + 2 * COLA
        v1.append(f'<clipitem id="v_{n}"><name>{n}</name><enabled>TRUE</enabled><duration>{largo}</duration>{rate()}<start>{t}</start><end>{t + c}</end><in>{COLA}</in><out>{COLA + c}</out>{file_video("f_" + n, CLIPS / (n + ".mp4"), largo)}</clipitem>')
        if n in SECCIONES: marcadores.append(f"<marker><name>{escape(SECCIONES[n])}</name><comment></comment><in>{t}</in><out>-1</out></marker>")
        if n == PRIMERA_CON_CIFRAS: ini_av = t
        t += c
        if n == ULTIMA_CON_CIFRAS: fin_av = t
        if k < len(infos) - 1: v1.append(disolvencia(t, largos[k])); cortes.append(t)
    total = t

    d = fin_av - ini_av
    v2 = (f'<clipitem id="aviso"><name>aviso_simulado</name><enabled>TRUE</enabled><duration>{d}</duration>{rate()}<start>{ini_av}</start><end>{fin_av}</end><in>0</in><out>{d}</out><stillframe>TRUE</stillframe>'
          f'{file_video("f_aviso", CLIPS / "aviso_simulado.png", d)}</clipitem>')

    # efectos: cada uno en la primera pista mono libre, para que no se pisen
    pistas = [[], [], []]; libre = [0, 0, 0]; vistos = set(); cues = cue_lista(infos)
    for k, (fx, ini, largo) in enumerate(cues):
        ruta = CLIPS / f"sfx_{fx}.wav"; total_fx = round(largo_wav(ruta) * FPS) or 1; dur = min(largo or total_fx, total_fx)
        p = next(i for i in range(3) if libre[i] <= ini); libre[p] = ini + dur
        fid = f"f_sfx_{fx}"
        ref = f'<file id="{fid}"/>' if fid in vistos else file_audio(fid, ruta, total_fx, 1)
        vistos.add(fid)
        pistas[p].append(f'<clipitem id="a{k}"><name>sfx_{fx}</name><enabled>TRUE</enabled><duration>{total_fx}</duration>{rate()}<start>{ini}</start><end>{ini + dur}</end><in>0</in><out>{dur}</out>{ref}<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem>')
    pistas = [p for p in pistas if p]
    mono = "".join(f'<track currentExplodedTrackIndex="0" totalExplodedTrackCount="1" premiereTrackType="Mono">{"".join(p)}<enabled>TRUE</enabled><locked>FALSE</locked></track>' for p in pistas)

    ruta_m = CLIPS / "musica_60s.wav"; dur_m = round(largo_wav(ruta_m) * FPS)
    def musica(lado):
        ref = file_audio("f_musica", ruta_m, dur_m, 2) if lado == 1 else '<file id="f_musica"/>'
        enlaces = "".join(f"<link><linkclipref>m{c}</linkclipref><mediatype>audio</mediatype><trackindex>{len(pistas) + c}</trackindex><clipindex>1</clipindex><groupindex>1</groupindex></link>" for c in (1, 2))
        clip = (f'<clipitem id="m{lado}"><name>musica_60s</name><enabled>TRUE</enabled><duration>{dur_m}</duration>{rate()}<start>0</start><end>{dur_m}</end><in>0</in><out>{dur_m}</out>{ref}'
                f'<sourcetrack><mediatype>audio</mediatype><trackindex>{lado}</trackindex></sourcetrack>{enlaces}</clipitem>')
        return f'<track currentExplodedTrackIndex="{lado - 1}" totalExplodedTrackCount="2" premiereTrackType="Stereo">{clip}<enabled>TRUE</enabled><locked>FALSE</locked><outputchannelindex>{lado}</outputchannelindex></track>'

    fmt = f"<format><samplecharacteristics>{rate()}<width>{OW}</width><height>{OH}</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance><colordepth>24</colordepth></samplecharacteristics></format>"
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq1"><name>Demo Factoring 60s</name><duration>{total}</duration>{rate()}'
           f'<timecode>{rate()}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>'
           f'<in>-1</in><out>-1</out>{"".join(marcadores)}<media><video>{fmt}'
           f'<track>{"".join(v1)}<enabled>TRUE</enabled><locked>FALSE</locked></track><track>{v2}<enabled>TRUE</enabled><locked>FALSE</locked></track></video>'
           f'<audio><numOutputChannels>2</numOutputChannels><format><samplecharacteristics><depth>16</depth><samplerate>{SR}</samplerate></samplecharacteristics></format>'
           f'{mono}{musica(1)}{musica(2)}</audio></media></sequence></xmeml>\n')
    (RAIZ / f"{NOMBRE}.xml").write_text(xml, encoding="utf8")
    print(f"{NOMBRE}.xml: {total / FPS:.2f} s, {len(infos)} tomas, {len(cortes)} disolvencias ({largos.count(DISOLVENCIA_LARGA)} largas), {len(cues)} efectos en {len(pistas)} pistas")
    previa(infos, cortes, largos, ini_av, fin_av, cues, total)


def mezcla(cues, total):
    """Musica + efectos, igual que suenan en la secuencia."""
    def lee(p):
        with wave.open(str(p)) as w: return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32767, w.getnchannels()
    m, c = lee(CLIPS / "musica_60s.wav"); pista = m.reshape(-1, c).copy()
    for fx, ini, largo in cues:
        x, _ = lee(CLIPS / f"sfx_{fx}.wav"); a = int(ini / FPS * SR)
        if largo: x = x[:int(largo / FPS * SR)]
        z = x[:max(0, pista.shape[0] - a)]
        pista[a:a + z.size] += z[:, None]
    return pista


def previa(infos, cortes, largos, ini_av, fin_av, cues, total):
    """Reproduce la secuencia en un mp4: mismas disolvencias, aviso y mezcla."""
    wav(RAIZ / "_mezcla.wav", mezcla(cues, total))
    ent, fil = [], []; ult = len(infos) - 1
    for k, i in enumerate(infos):
        ent += ["-i", str(CLIPS / f"{i['nombre']}.mp4")]
        a = COLA - (0 if k == 0 else largos[k - 1] // 2); b = COLA + i["cuadros"] + (0 if k == ult else largos[k] // 2)
        fil.append(f"[{k}:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,format=yuv420p[c{k}]")
    prev = "c0"
    for k, (c, l) in enumerate(zip(cortes, largos), 1):
        fil.append(f"[{prev}][c{k}]xfade=transition=fade:duration={l / FPS}:offset={(c - l // 2) / FPS}[x{k}]"); prev = f"x{k}"
    n = len(infos)
    fil.append(f"[{n}:v]format=rgba[av];[{prev}][av]overlay=enable='between(t,{ini_av / FPS},{fin_av / FPS})':shortest=1[v]")
    sal = RAIZ / "previa_60s.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *ent, "-loop", "1", "-framerate", str(FPS), "-i", str(CLIPS / "aviso_simulado.png"), "-i", str(RAIZ / "_mezcla.wav"),
                    "-filter_complex", ";".join(fil), "-map", "[v]", "-map", f"{n + 1}:a", "-t", str(total / FPS), "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(sal)], check=True)
    print("mezcla LUFS, pico:", lufs(RAIZ / "_mezcla.wav")); (RAIZ / "_mezcla.wav").unlink()
    print(sal.name, "lista")


if __name__ == "__main__":
    main()
