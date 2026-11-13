"""Escribe en el .prproj lo que la API de Premiere no puede (con Premiere cerrado): textos y suavizado.

La API de Premiere no puede escribir 'Texto de origen': guarda un valor invalido. Aqui se toma el bloque
binario original de Basic Title y se le apunta al texto, fuente y tamano de cada titulo, sin mover nada.
"""
import base64, gzip, json, re, shutil, struct
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PRJ = RAIZ / "Demo_Factoring_Editable.prproj"
FUENTE = "SegoeUI-Bold"
PATRON = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]*">)([^<]+)(<)'


def blob(base, texto, tam):
    b = bytearray(base)
    def agrega(cad, puntero):
        d = cad.encode("utf8")
        while len(b) % 4: b.append(0)
        ini = len(b); b.extend(struct.pack("<I", len(d)) + d + b"\0")
        struct.pack_into("<I", b, puntero, ini - puntero)
    agrega(texto, 272); agrega(FUENTE, 224)
    while len(b) % 4: b.append(0)
    struct.pack_into("<I", b, 0, len(b) - 12)
    return bytes(b)


INFLUENCIA = "0.5"      # como Suavizar entrada/salida en Premiere, algo mas marcado


def suavizar(lista):
    """Keyframes Bezier con tangente plana: arrancan y frenan suave. Los lineales no se tocan."""
    claves = []
    for k in lista.rstrip(";").split(";"):
        c = k.split(",")
        if len(c) >= 8 and c[2] == "5":
            c[4], c[5], c[6], c[7] = "0", INFLUENCIA, "0", INFLUENCIA
            if len(c) >= 14: c[10:14] = ["0", "0", "0", "0"]      # trayectoria recta en Posicion
        claves.append(",".join(c))
    return ";".join(claves) + ";"


def main():
    x = gzip.open(PRJ).read().decode("utf8")
    x, n_kf = re.subn(r"<Keyframes>([^<]+)</Keyframes>", lambda m: f"<Keyframes>{suavizar(m.group(1))}</Keyframes>", x)
    textos = {t["id"]: t for t in json.loads((RAIZ / "editable_textos.json").read_text(encoding="utf8"))}
    base = (RAIZ / "basic_title.bin").read_bytes()
    hechos = set()
    def cambia(m):
        v = base64.b64decode(m.group(2))
        try: marca = v.decode("utf-16-le")
        except UnicodeDecodeError: return m.group(0)
        if marca not in textos: return m.group(0)
        hechos.add(marca); t = textos[marca]
        return m.group(1) + base64.b64encode(blob(base, t["t"], t["tam"])).decode() + m.group(3)
    x2 = re.sub(PATRON, cambia, x)
    faltan = set(textos) - hechos
    if faltan: raise SystemExit(f"No encontre los titulos {sorted(faltan)}; no se modifico el proyecto")
    with gzip.open(PRJ, "wb") as f: f.write(x2.encode("utf8"))
    print(f"{len(hechos)} titulos escritos, {n_kf} propiedades suavizadas")


if __name__ == "__main__":
    main()
