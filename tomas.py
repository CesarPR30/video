"""Las tomas del video. Uso: python tomas.py [nombre ...]  (sin nombres: todas, en paralelo).

Cada toma abre el dashboard real, asi que al regenerar con el modelo real cambian las cifras
sin tocar nada aqui. DURACION define orden y largo: todas caen en multiplos de 0.5 s para que
los cortes coincidan con el pulso de la musica (120 BPM). Deben sumar 60 s.
"""
import subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright
import motor
from motor import Toma, VW, VH, RAIZ, CLIPS

TITULO = (RAIZ / "graficos" / "titulo.html").as_uri()
CLARO, OSCURO = "#F5F7FA", "#001C4F"

DURACION = {
    "t_pregunta": 3.0, "t_cifras": 3.0, "ventana_resumen": 3.0, "t_cuanto": 1.0, "hero_figura": 2.5, "hero_kpis": 2.5, "etapas": 3.5,
    "t_simula": 1.0, "sim_tab": 2.0, "sim_slider": 3.5, "sim_tiles": 2.5, "sim_curva": 2.5, "sim_lectura": 2.5,
    "t_quienes": 1.0, "lista_mapa": 2.5, "lista_tabla": 3.0, "lista_ficha": 3.0,
    "t_porque": 1.0, "importancia": 2.5, "red_grafo": 3.5, "red_tiles": 2.0, "pitch": 4.5, "ventana_cierre": 2.0, "t_cierre": 2.5,
}
# Se renderiza pero no entra al timeline: con datos simulados todos los indices dan ~1.00x.
# Con el modelo real puede ser una toma fuerte: agregarla a DURACION, despues de lista_ficha.
EXTRAS = {"dumbbell": 3.5}


def url(**k): return f"{TITULO}?{urlencode(k)}"
def toma(b, nombre, **k): return Toma(b, nombre, duracion={**DURACION, **EXTRAS}[nombre], **k)
def titulo(b, nombre, **k): return toma(b, nombre, url=url(**k))


def t_pregunta(b): return titulo(b, "t_pregunta", tipo="pregunta")
def t_cifras(b):   return titulo(b, "t_cifras", tipo="cifras")
def t_cuanto(b):   return titulo(b, "t_cuanto", tipo="seccion", t="¿Cuánto?", s="Base habilitada", c="claro")
def t_simula(b):   return titulo(b, "t_simula", tipo="seccion", t="¿Y si cambia?", s="La capacidad comercial", c="naranja")
def t_quienes(b):  return titulo(b, "t_quienes", tipo="seccion", t="¿Quiénes?", s="Probabilidad de conversión", c="claro")
def t_porque(b):   return titulo(b, "t_porque", tipo="seccion", t="¿Por qué?", s="Sustento de negocio", c="naranja")
def t_cierre(b):   return titulo(b, "t_cierre", tipo="cierre")


def ventana_resumen(b):
    s = toma(b, "ventana_resumen")
    s.ven.a(0, 1, (.74,)); s.esperar(1.1)
    s.ven.a(s.f, 39, (1.0,)); s.esperar(1.3)
    return s

def hero_figura(b):
    s = toma(b, "hero_figura")
    s.aislar(".hero", CLARO)
    s.enfocar(".hero-figure", dur=.03, pad=170, zmax=1.9)
    s.esperar(1.1)
    r = s.rect(".hero-note"); r["x"] -= 40; r["w"] += 80; r["y"] -= 120; r["h"] += 150
    s.cam_rect(r, 1.2, pad=60, zmax=1.9)
    return s

def hero_kpis(b):
    s = toma(b, "hero_kpis")
    s.aislar(".hero-kpis", OSCURO)
    r = s.rect(".hero-kpi", 0); s.cam_rect({**r, "w": r["w"] * 2.1}, .03, pad=30, zmax=2.2)
    s.esperar(.3)
    r = s.rect(".hero-kpi", 3); s.cam_rect({**r, "x": r["x"] - r["w"] * 1.1, "w": r["w"] * 2.1}, 2.0, pad=30, zmax=2.2)
    return s

def etapas(b):
    s = toma(b, "etapas")
    s.aislar(".stages", CLARO)
    s.enfocar(".stage", 0, dur=.03, pad=30, zmax=1.9)
    s.esperar(.9)
    s.enfocar(".stage", 1, dur=.85, pad=30, zmax=1.9); s.esperar(1.25)
    s.enfocar(".stage", 2, dur=.85, pad=30, zmax=1.9)
    return s

def sim_tab(b):
    s = toma(b, "sim_tab")
    s.calentar(1.0)
    s.plano(VW / 2, 120, 1.6, .03); s.saltos_cam.add(s.f)
    s.mostrar_cursor(VW * .68, 170)
    s.esperar(.1)
    s.mover_a(".tabs button[data-view=simulador]", dur=.55)
    s.plano(VW / 2, VH / 2, 1.0, 1.1)
    s.click(mezcla=10)
    return s

def sim_slider(b):
    s = toma(b, "sim_slider", vista="simulador")
    s.aislar(".ctl", CLARO, flotar=True)
    s.enfocar(".ctl", dur=.03, pad=90, zmax=2.2)
    x, y = s.x_slider("#c-cap", 5000)
    s.mostrar_cursor(x + 110, y + 90)
    s.esperar(.3)
    s.mover(x, y, .55)
    x2, _ = s.x_slider("#c-cap", 12000)
    s.arrastrar(x2, y, 1.9)
    return s

def sim_tiles(b):
    s = toma(b, "sim_tiles", vista="simulador")
    s.calentar(1.0)
    s.aislar(".stack .tiles", CLARO)
    s.enfocar(".stack .tiles", dur=.03, pad=30)
    s.esperar(.4)
    s.deslizar("#c-cap", 12000, 1.6)
    return s

def sim_curva(b):
    s = toma(b, "sim_curva", vista="simulador")
    s.marcar("Valor esperado acumulado", "cv")
    s.scroll_ya("#cv", 86)
    s.calentar(1.6)
    s.aislar("#cv", CLARO)
    s.enfocar("#cv", dur=.03, pad=20)
    s.esperar(.3)
    s.deslizar("#c-cap", 12000, 1.8)
    return s

def sim_lectura(b):
    s = toma(b, "sim_lectura", vista="simulador")
    s.marcar("De dónde sale el valor", "cs")
    s.scroll_ya("#cs", 110)
    s.calentar(.8)
    s.aislar("#cs", CLARO)
    s.enfocar("#cs", dur=.03, pad=40, zmax=1.9)
    s.empuje(2.8)
    s.esperar(.3)
    r = s.rect("#cs path[fill='#002D74']")
    s.mostrar_cursor(r["x"] - 70, r["y"] + 170)
    s.mover(r["x"] + r["w"] / 2, r["y"] + r["h"] / 2, .8)
    return s

def lista_mapa(b):
    s = toma(b, "lista_mapa", vista="lista")
    s.marcar("Mapa de oportunidades", "mp")
    s.scroll_ya("#mp", 86)
    s.enfocar("#mp", dur=.03, pad=14)
    s.calentar(.03)
    s.empuje(2.8, 1.05)
    return s

def lista_tabla(b):
    s = toma(b, "lista_tabla", vista="lista")
    s.scroll_ya("table.data", 130)
    s.calentar(1.2)
    s.mostrar_cursor(VW * .7, VH * .8)
    s.esperar(.2)
    r = s.rect("table.data tbody tr", 2)
    s.plano(VW / 2 - 200, r["y"] + 40, 1.45, 1.3)
    s.mover_a("table.data tbody tr", 3, dur=.75); s.esperar(.15)
    s.mover_a("table.data tbody tr", 1, dur=.45); s.esperar(.15)
    s.mover_a("table.data tbody tr", 0, dur=.35); s.esperar(.1)
    s.click()
    return s

def lista_ficha(b):
    s = toma(b, "lista_ficha", vista="lista")
    s.calentar(1.0)
    s.cam_rect({"x": VW - 470, "y": 0, "w": 470, "h": 420}, .03, pad=10, zmax=1.75)
    s.page.evaluate("document.querySelector('table.data tbody tr').click()")
    s.esperar(1.2)
    s.cam_rect({"x": VW - 470, "y": 180, "w": 470, "h": 420}, 1.1, pad=10, zmax=1.75)
    return s

def dumbbell(b):
    s = toma(b, "dumbbell")
    s.marcar("¿Quiénes? El top 30%", "dm")
    s.aislar("#dm", CLARO)
    s.enfocar("#dm", dur=.03, pad=24, zmax=1.7)
    s.esperar(.9)
    x, y = s.centro("#dm .switch button", 1)
    s.mostrar_cursor(x, y + 110)
    s.mover_a("#dm .switch button", 1, dur=.7)
    s.click()
    return s

def importancia(b):
    s = toma(b, "importancia")
    s.marcar("¿Por qué? Lo que explica", "im")
    s.aislar("#im", CLARO)
    s.enfocar("#im", dur=.03, pad=24, zmax=1.7)
    s.empuje(2.8)
    return s

def red_grafo(b):
    s = toma(b, "red_grafo", vista="red")
    s.marcar("Proveedores de la ancla", "gr")
    s.scroll_ya("#gr", 76)
    s.page.evaluate("document.querySelector('#gr').classList.add('in')")
    s.enfocar("#gr .chart", dur=.03, pad=8, zmax=1.6)
    s.esperar(1.5)
    c = s.centro("#gr .chart")
    s.plano(c[0], c[1], 1.75, 2.2)
    return s

def red_tiles(b):
    s = toma(b, "red_tiles", vista="red")
    s.aislar(".stack .tiles", CLARO)
    s.enfocar(".stack .tiles", dur=.03, pad=30)
    s.empuje(2.3, 1.04)
    return s

def pitch(b):
    s = toma(b, "pitch")
    s.aislar(".pitch", OSCURO)
    s.enfocar(".pitch", dur=.03, pad=50, zmax=1.7)
    s.esperar(.1)
    s.empuje(4.7, 1.08)
    return s

def ventana_cierre(b):
    s = toma(b, "ventana_cierre")
    s.calentar(1.2)
    s.esperar(.2)
    s.ven.a(s.f, 48, (.74,))
    return s


TODAS = {f.__name__: f for f in (t_pregunta, t_cifras, ventana_resumen, t_cuanto, hero_figura, hero_kpis, etapas, t_simula, sim_tab, sim_slider,
         sim_tiles, sim_curva, sim_lectura, t_quienes, lista_mapa, lista_tabla, lista_ficha, dumbbell, t_porque, importancia, red_grafo,
         red_tiles, pitch, ventana_cierre, t_cierre)}


def una(nombre):
    with sync_playwright() as p:
        b = p.chromium.launch()
        TODAS[nombre](b).fin(); b.close()


def aviso():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=1920 / VW).new_page()
        pg.goto(url(tipo="aviso")); pg.wait_for_timeout(300)
        pg.screenshot(path=str(CLIPS / "aviso_simulado.png"), omit_background=True)
        if motor.EDITABLE:
            pg.goto(url(tipo="logo")); pg.wait_for_timeout(300)
            pg.screenshot(path=str(CLIPS / "logo_bcp.png"), omit_background=True)
            for n, c in (("fondo_navy", ""), ("fondo_naranja", "naranja")):
                s = Toma(b, n, url=url(tipo="fondo", c=c), duracion=4.0); s.fin()
        b.close()


if __name__ == "__main__":
    nombres = sys.argv[1:]
    if nombres and nombres[0] == "--una":
        una(nombres[1]); sys.exit()
    assert abs(sum(DURACION.values()) - 60) < 1e-6, sum(DURACION.values())
    CLIPS.mkdir(exist_ok=True)
    todas = nombres or [*DURACION, *EXTRAS]
    if motor.EDITABLE: todas = [n for n in todas if not n.startswith("t_")]   # los titulos son texto de Premiere
    t0 = time.time()
    def correr(n):
        r = subprocess.run([sys.executable, __file__, "--una", n], capture_output=True, text=True)
        print(("ok   " if r.returncode == 0 and "AVISO" not in r.stdout else "REVISAR"), n, [l for l in r.stdout.splitlines() if "AVISO" in l], flush=True)
        if r.returncode: print(r.stderr[-1500:], flush=True)
        return r.returncode
    with ThreadPoolExecutor(6) as ex: codigos = list(ex.map(correr, todas))
    if not nombres: aviso()
    print(f"listo en {time.time() - t0:.0f}s, fallos: {sum(1 for c in codigos if c)}")
