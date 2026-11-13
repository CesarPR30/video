"""Motor de captura cuadro por cuadro del dashboard.

Reloj virtual: los timers, requestAnimationFrame y transiciones CSS avanzan solo cuando
se pide un cuadro, asi el video queda fluido sin importar cuanto tarde cada captura.
Camara: se captura a alta densidad y se recorta con precision subpixel, sin saltos.
"""
import base64, io, json, math, os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

RAIZ = Path(__file__).resolve().parent
DASH = RAIZ.parent / "dashboard" / "index.html"
# VIDEO_MODO=editable: graba 4K limpio, sin camara, y guarda los movimientos para hacerlos keyframes en Premiere
EDITABLE = os.environ.get("VIDEO_MODO") == "editable"
CLIPS = RAIZ / ("clips_editable" if EDITABLE else "clips_60s")
FPS = 30
COLA = 8                    # cuadros extra en cabeza y cola: permiten disolvencias en Premiere
VW, VH = 1440, 810          # viewport CSS
DSF = 3                     # densidad de captura: permite zoom 2.25x sin perder nitidez
OW, OH = (3840, 2160) if EDITABLE else (1920, 1080)   # salida
NAVY = (0, 28, 79)
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = os.environ.get("FFMPEG") or "ffmpeg"

JS_RELOJ = r"""
(() => {
  let semilla = 20261113;
  Math.random = () => { semilla = (semilla * 1664525 + 1013904223) >>> 0; return semilla / 4294967296; };
  let ahora = 0, id = 1;
  const raf = new Map(), tim = new Map(), inicio = new WeakMap();
  performance.now = () => ahora;
  const D0 = 1794000000000; Date.now = () => D0 + ahora;
  window.requestAnimationFrame = f => { raf.set(id, f); return id++; };
  window.cancelAnimationFrame = i => raf.delete(i);
  window.setTimeout = (f, d = 0, ...a) => { tim.set(id, { f, t: ahora + (+d || 0), a }); return id++; };
  window.clearTimeout = i => tim.delete(i);
  window.setInterval = (f, d = 0, ...a) => { tim.set(id, { f, t: ahora + d, a, cada: d || 16 }); return id++; };
  window.clearInterval = i => tim.delete(i);
  window.__tick = dt => {
    ahora += dt;
    for (const [i, x] of [...tim].sort((a, b) => a[1].t - b[1].t)) {
      if (x.t > ahora || !tim.has(i)) continue;
      if (x.cada) x.t += x.cada; else tim.delete(i);
      x.f(...x.a);
    }
    const q = [...raf]; raf.clear(); q.forEach(([, f]) => f(ahora));
    for (const a of document.getAnimations()) {
      if (!inicio.has(a)) { inicio.set(a, ahora - dt); a.pause(); }
      const fin = a.effect.getComputedTiming().endTime, t = ahora - inicio.get(a);
      if (fin !== Infinity && t >= fin) a.finish(); else a.currentTime = t;
    }
  };
})();
"""

CSS_VIDEO = """
html{scroll-behavior:auto!important}
*{cursor:none!important}
::-webkit-scrollbar{display:none}
:focus,:focus-visible{outline:none!important}
.drawer{transition:transform .65s cubic-bezier(.22,.8,.2,1),visibility 0s!important}
.scrim{transition:opacity .55s!important}
.reveal.in{transition:opacity .75s ease-in-out,transform .75s ease-in-out!important}
#vc{position:fixed;left:0;top:0;width:0;height:0;z-index:99999;pointer-events:none;visibility:visible!important}
#vc svg{position:absolute;left:-5px;top:-3px;width:34px;height:41px;filter:drop-shadow(0 3px 6px rgba(0,20,60,.35));transform-origin:5px 3px;visibility:visible!important}
#vc svg *{visibility:visible!important}
#vr{position:absolute;left:0;top:0;width:44px;height:44px;margin:-22px;border-radius:50%;border:3px solid #ED590C;opacity:0;visibility:visible!important}
html.iso{background:var(--iso,#F5F7FA)!important}
html.iso body{background:transparent!important}
html.iso body *{visibility:hidden}
html.iso .vv,html.iso .vv *{visibility:visible}
html.iso .vv.vfloat{background:#fff!important;border-radius:18px!important;box-shadow:0 0 0 26px #fff,0 26px 46px rgba(0,28,79,.13)!important}
html.iso #tooltip,html.iso #tooltip *{visibility:visible}
html.iso .reveal{opacity:1!important;transform:none!important}
"""
JS_CURSOR = r"""
css => {
  const s = document.createElement("style"); s.textContent = css; document.head.append(s);
  const c = document.createElement("div"); c.id = "vc"; c.style.opacity = 0;
  c.innerHTML = '<div id="vr"></div><svg viewBox="0 0 24 29"><path d="M3 2v21l5.6-5 3.6 8.4 3.9-1.7-3.6-8.2H20z" fill="#fff" stroke="#002D74" stroke-width="1.7" stroke-linejoin="round"/></svg>';
  document.body.append(c);
  const svg = c.querySelector("svg"), r = c.querySelector("#vr");
  window.__cursor = (x, y, esc, ripple, vis) => {
    c.style.transform = `translate(${x}px,${y}px)`; c.style.opacity = vis;
    svg.style.transform = `scale(${esc})`;
    r.style.opacity = ripple > 0 ? ripple : 0; r.style.transform = `scale(${1.5 - ripple})`;
  };
}
"""


def ease_out(t): return 1 - (1 - t) ** 4
def ease_io(t):  return t * t * t * (t * (6 * t - 15) + 10)
EASES = {"out": ease_out, "io": ease_io, "lin": lambda t: t}


class Pista:
    """Valor animado por tramos programados sobre el tiempo en cuadros."""
    def __init__(self, v): self.v0 = v; self.tramos = []
    def a(self, f, dur, valor, ease="io"):
        self.tramos.append((f, max(dur, 1), valor, EASES[ease], ease))
    def valor(self, f):
        v = self.v0
        for ini, dur, dest, e, _ in self.tramos:
            if f < ini: break
            t = min((f - ini + 1) / dur, 1)
            v = tuple(a + (b - a) * e(t) for a, b in zip(v, dest))
        return v


class Toma:
    def __init__(self, browser, nombre, url=None, vista="resumen", fondo=NAVY, duracion=None):
        self.nombre, self.f = nombre, 0
        self.limite = round(duracion * FPS) if duracion else None
        self.cola = 0; self.ultimo = None; self.mezcla = None; self.vis_obj = 0
        self.ctx = browser.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=DSF)
        self.page = self.ctx.new_page()
        self.page.add_init_script(JS_RELOJ)
        self.page.goto(url or f"{DASH.as_uri()}#{vista}", wait_until="load")
        self.page.evaluate("document.fonts.ready.then(()=>1)")
        self.page.evaluate(JS_CURSOR, CSS_VIDEO)
        self.cdp = self.ctx.new_cdp_session(self.page)
        self.cur = [VW * .62, VH * .78]; self.vis = 0; self.esc = 1; self.rip = 0
        self.cam = Pista((VW / 2, VH / 2, 0.0))     # cx, cy, log(zoom)
        self.ven = Pista((1.0,))                     # 1 pantalla completa, <1 ventana flotante
        self.fondo = Image.new("RGB", (OW, OH), fondo)
        self.eventos = []; self.calentando = False; self.saltos_cam = set()
        CLIPS.mkdir(exist_ok=True)
        self.salida = CLIPS / f"{nombre}.mp4"
        self.ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
            "-r", str(FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-c:v", "libx264", "-preset", "medium", "-crf", "13",
            "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-movflags", "+faststart", str(self.salida)], stdin=subprocess.PIPE)

    def page_y(self): return self.page.evaluate("scrollY")

    # ---------- cuadro ----------
    def cuadro(self):
        if self.limite is not None and self.f >= self.limite + self.cola: return
        self.vis = min(1, self.vis + 1 / 7) if self.vis_obj else 0
        self.page.evaluate("([dt,x,y,e,r,v])=>{__tick(dt);__cursor(x,y,e,r,v)}",
                           [1000 / FPS, self.cur[0], self.cur[1], self.esc, self.rip, self.vis])
        b = self.cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 97, "optimizeForSpeed": True,
            "clip": {"x": 0, "y": self.page_y(), "width": VW, "height": VH, "scale": DSF}})["data"]
        img = Image.open(io.BytesIO(base64.b64decode(b))).convert("RGB")
        if EDITABLE:
            return self.emitir(img.resize((OW, OH), Image.LANCZOS))
        cx, cy, lz = self.cam.valor(self.f); z = math.exp(lz)
        w, h = VW / z, VH / z
        cx = min(max(cx, w / 2), VW - w / 2); cy = min(max(cy, h / 2), VH - h / 2)
        k = img.width / VW
        caja = (max(0, (cx - w / 2) * k), max(0, (cy - h / 2) * k), min(img.width, (cx + w / 2) * k), min(img.height, (cy + h / 2) * k))
        s = self.ven.valor(self.f)[0]
        out = img.resize((OW, OH), Image.LANCZOS, box=caja) if s > .999 else self.ventana(img, caja, s)
        self.emitir(out)

    def emitir(self, out):
        if self.mezcla:
            desde, i, n = self.mezcla
            t = ease_io((i + 1) / n); out = Image.blend(desde, out, t)
            self.mezcla = (desde, i + 1, n) if i + 1 < n else None
        self.ultimo = out
        if self.calentando: return
        self.ff.stdin.write(out.tobytes())
        if self.f == 0:
            for _ in range(COLA): self.ff.stdin.write(out.tobytes())
        self.f += 1
        if self.f % 30 == 0: print(f"  {self.nombre}: {self.f / FPS:.0f}s", flush=True)

    def ventana(self, img, caja, s):
        w, h = round(OW * s), round(OH * s)
        p = img.resize((w, h), Image.LANCZOS, box=caja)
        k = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(k).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=round(36 * s), fill=255)
        k = k.resize((w, h), Image.LANCZOS)
        x, y = (OW - w) // 2, (OH - h) // 2
        out = self.fondo.copy()
        sombra = Image.new("L", (OW, OH), 0); sombra.paste(k.point(lambda v: v * .55), (x, y + 18))
        sombra = sombra.resize((OW // 8, OH // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((OW, OH), Image.BILINEAR)
        out.paste((0, 8, 28), mask=sombra); out.paste(p, (x, y), k)
        return out

    # ---------- acciones ----------
    def esperar(self, seg):
        for _ in range(round(seg * FPS)): self.cuadro()

    def calentar(self, seg):
        """Avanza el reloj sin grabar: la pagina ya animo lo inicial y el clip arranca limpio."""
        self.calentando = True; self.esperar(seg); self.calentando = False

    def empuje(self, seg, factor=1.06):
        """Acercamiento lento de camara desde el encuadre actual."""
        cx, cy, lz = self.cam.tramos[-1][2]
        self.cam.a(self.f, round(seg * FPS), (cx, cy, lz + math.log(factor)), "lin")

    def rect(self, sel, n=0):
        return self.page.evaluate("([s,n])=>{const e=document.querySelectorAll(s)[n];const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}}", [sel, n])

    def centro(self, sel, n=0):
        r = self.rect(sel, n); return r["x"] + r["w"] / 2, r["y"] + r["h"] / 2

    def mostrar_cursor(self, x=None, y=None):
        if x is not None: self.cur = [x, y]
        self.vis_obj = 1; self.page.mouse.move(*self.cur)

    def mover(self, x, y, dur=.8, ease="io"):
        x0, y0 = self.cur; n = max(round(dur * FPS), 1)
        for i in range(1, n + 1):
            t = EASES[ease](i / n)
            self.cur = [x0 + (x - x0) * t, y0 + (y - y0) * t - math.sin(t * math.pi) * min(26, abs(x - x0) * .04)]
            self.page.mouse.move(*self.cur); self.cuadro()

    def mover_a(self, sel, n=0, dur=.8, dx=0, dy=0):
        x, y = self.centro(sel, n); self.mover(x + dx, y + dy, dur)

    def click(self, mezcla=0):
        self.eventos.append(("click", self.f))
        for e in (.92, .86): self.esc = e; self.cuadro()
        if mezcla: self.mezcla = (self.ultimo, 0, mezcla)
        self.page.mouse.down(); self.page.mouse.up()
        for i in range(10):
            self.esc = min(1, .86 + .03 * i); self.rip = 1 - i / 10; self.cuadro()
        self.rip = 0

    def mover_recto(self, x, y, dur, ease="io"):
        x0, y0 = self.cur; n = max(round(dur * FPS), 1)
        for i in range(1, n + 1):
            t = EASES[ease](i / n); self.cur = [x0 + (x - x0) * t, y0 + (y - y0) * t]
            self.page.mouse.move(*self.cur); self.cuadro()

    def arrastrar(self, x, y, dur=2, ease="io", vuelta=None):
        self.eventos.append(("click", self.f)); self.eventos.append(("slider", self.f + 1))
        self.esc = .9; self.page.mouse.down(); self.cuadro()
        self.mover_recto(x, y, dur, ease)
        if vuelta: self.mover_recto(vuelta[0], vuelta[1], dur * .6, ease)
        self.page.mouse.up(); self.esc = 1; self.cuadro()

    def scroll(self, y, dur=1.0, ease="io"):
        y0 = self.page.evaluate("scrollY"); n = max(round(dur * FPS), 1)
        for i in range(1, n + 1):
            self.page.evaluate("y=>scrollTo({top:y,behavior:'instant'})", y0 + (y - y0) * EASES[ease](i / n)); self.cuadro()

    def scroll_ya(self, sel, margen=90, n=0):
        self.page.evaluate("([s,m,n])=>{const r=document.querySelectorAll(s)[n].getBoundingClientRect();scrollTo({top:scrollY+r.y-m,behavior:'instant'})}", [sel, margen, n])

    # ---------- camara ----------
    def cam_rect(self, r, dur=1.0, pad=30, ease="io", zmax=2.25):
        z = max(min(VW / (r["w"] + pad * 2), VH / (r["h"] + pad * 2), zmax), 1)
        if dur < .05: self.saltos_cam.add(self.f)
        self.cam.a(self.f, round(dur * FPS), (r["x"] + r["w"] / 2, r["y"] + r["h"] / 2, math.log(z)), ease)

    def enfocar(self, sel, n=0, dur=1.0, pad=30, ease="io", zmax=2.25):
        self.cam_rect(self.rect(sel, n), dur, pad, ease, zmax)

    def plano(self, cx, cy, z, dur=1.0, ease="io"):
        self.cam.a(self.f, round(dur * FPS), (cx, cy, math.log(z)), ease)

    def aislar(self, sel, fondo="#F5F7FA", flotar=False, n=0, centrar=True):
        self.page.evaluate("""([s,b,fl,n,c])=>{const h=document.documentElement;h.classList.add('iso');h.style.setProperty('--iso',b);
          document.querySelectorAll('.vv').forEach(e=>{e.classList.remove('vv','vfloat');e.style.removeProperty('transform')});
          const e=document.querySelectorAll(s)[n];e.classList.add('vv');if(fl)e.classList.add('vfloat');
          if(c){const r=e.getBoundingClientRect();e.style.setProperty('transform',`translate(${innerWidth/2-r.x-r.width/2}px,${innerHeight/2-r.y-r.height/2}px)`,'important');e.style.setProperty('transition','none','important')}}""", [sel, fondo, flotar, n, centrar])

    def marcar(self, texto, ident):
        """Da un id a la tarjeta cuyo h3 tiene ese texto, para poder apuntarle."""
        self.page.evaluate("""([t,i])=>{const h=[...document.querySelectorAll('h3')].find(x=>x.textContent.startsWith(t));h.closest('.card').id=i}""", [texto, ident])

    def deslizar(self, sel, v1, dur=2, ease="io"):
        """Mueve un slider sin cursor visible."""
        v0 = float(self.page.evaluate("s=>document.querySelector(s).value", sel)); n = max(round(dur * FPS), 1)
        self.eventos.append(("slider", self.f))
        for i in range(1, n + 1):
            self.page.evaluate("""([s,v])=>{const e=document.querySelector(s);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}""", [sel, v0 + (v1 - v0) * EASES[ease](i / n)])
            self.cuadro()

    def x_slider(self, sel, v):
        i = self.rect(sel); a = self.page.evaluate("s=>{const e=document.querySelector(s);return[+e.min,+e.max]}", sel)
        return i["x"] + 10 + (i["w"] - 20) * (v - a[0]) / (a[1] - a[0]), i["y"] + i["h"] / 2

    def velocidades(self):
        """Velocidad maxima de camara, en % de pantalla por segundo y log-zoom por segundo."""
        pan = zoom = 0; prev = self.cam.valor(0)
        for f in range(1, self.f):
            v = self.cam.valor(f)
            if f - 1 not in self.saltos_cam:
                pan = max(pan, math.hypot((v[0] - prev[0]) / VW, (v[1] - prev[1]) / VH) * 100 * FPS)
                zoom = max(zoom, abs(v[2] - prev[2]) * FPS)
            prev = v
        return round(pan, 1), round(zoom, 2)

    def fin(self):
        if self.limite is not None:
            if self.f > self.limite: print(f"  AVISO {self.nombre}: se paso de {self.limite} cuadros", flush=True)
            while self.f < self.limite: self.cuadro()
        self.cola = COLA
        for _ in range(COLA): self.cuadro()
        util = self.f - COLA
        self.ff.stdin.close(); self.ff.wait(); self.ctx.close()
        pan, zoom = self.velocidades()
        info = {"nombre": self.nombre, "cuadros": util, "cabeza": COLA, "eventos": self.eventos, "paneo_max": pan, "zoom_max": zoom,
                "cam": {"v0": self.cam.v0, "tramos": [(a, b, c, e) for a, b, c, _, e in self.cam.tramos]},
                "ven": {"v0": self.ven.v0, "tramos": [(a, b, c, e) for a, b, c, _, e in self.ven.tramos]}}
        (CLIPS / f"{self.nombre}.json").write_text(json.dumps(info), encoding="utf8")
        return info
