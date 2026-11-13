# Abrir el video en DaVinci Resolve

DaVinci Resolve no abre proyectos de Premiere (`.prproj`), pero importa la secuencia. Hay dos versiones:

| Versión | Archivo | Qué se puede editar |
|---|---|---|
| **Editable** | `Demo_Factoring_Editable_DaVinci.fcpxml` | Zooms, encuadres, títulos, ventana flotante, cortes y audio. Usa grabaciones 4K. |
| Renderizada | `Demo_Factoring_DaVinci.xml` | Cortes y audio. La cámara y los títulos vienen dentro de los clips. |

Instala DaVinci Resolve desde [blackmagicdesign.com](https://www.blackmagicdesign.com/products/davinciresolve). La versión gratuita basta.

## 1. Generar el archivo

En la carpeta `video/`, ejecuta según la versión:

```
python armar_davinci_editable.py
python armar_davinci.py
```

Cada script escribe las rutas de tu computadora. Si mueves o vuelves a clonar la carpeta, ejecútalo otra vez. Solo usan la librería estándar de Python.

## 2. Crear el proyecto

1. Abre Resolve y crea un proyecto nuevo.
2. Ve a **File > Project Settings > Master Settings** y fija:
   - **Timeline resolution:** 1920 x 1080 HD.
   - **Timeline frame rate:** 30.
   - **Playback frame rate:** 30.
3. En **Image Scaling**, deja **Input scaling** en **Scale entire image to fit**. Así las grabaciones 4K entran completas con Zoom 1.00.
4. Guarda los ajustes.

Hazlo antes de importar: Resolve no deja cambiar la cadencia del proyecto después.

## 3. Importar

1. Ve a **File > Import > Timeline** (`Ctrl + Shift + I`) y elige el `.fcpxml` o el `.xml`.
2. Deja marcada **Automatically import source clips into media pool** y acepta.
3. Si algún clip aparece en rojo, selecciónalo en el Media Pool, haz clic derecho en **Relink Selected Clips** y elige `clips_editable` o `clips_60s`, según la versión.

### Versión editable

| Pista | Contenido | Cómo se cambia |
|---|---|---|
| V1 | Grabaciones 4K y fondos de los títulos | **Inspector > Transform**: Zoom y Position, con keyframes |
| V2 | Ventana flotante y logo | Inspector: Zoom y Opacity |
| V3 | Aviso "Cifras ilustrativas" | Borrarlo cuando el video muestre cifras reales |
| V4 y V5 | Títulos | Selecciona el título y cambia el texto en el Inspector |
| A1 a A3 | Efectos de sonido | Mover, borrar o ajustar volumen |
| A4 | Música | Reemplazar por otra pista |

**Zoom 1.00** es la pantalla completa y **2.00** es el máximo sin perder nitidez. Para ver y mover los keyframes, abre el editor de keyframes del clip, con el ícono de rombo en la línea de tiempo.

**Lo que no pasa de Premiere:**

- Las animaciones de entrada de los títulos (tecleo, golpe y subida). En Resolve puedes usar un título **Text+** con una animación de la biblioteca **Effects > Titles**.
- La sombra de la ventana flotante. Agrégala con **Effects > OpenFX > Drop Shadow** si tu versión la incluye.

### Si algo no se importa

Resolve interpreta el FCPXML a su manera, y la conversión no se probó dentro de Resolve. Si una toma entra sin zoom o falta un título, usa estas tablas:

<!-- EDITABLE -->
**Cámara** (Inspector > Transform; Zoom 1.00 = pantalla completa, Position en píxeles desde el centro):

| Inicio | Toma | Zoom | Position X, Y |
|---|---|---|---|
| 00:10:00 | `hero_figura` | 1.85 → 1.90 | 812, -165 → 864, -52 |
| 00:12:15 | `hero_kpis` | 2.19 → 2.19 | 842, 0 → -842, -39 |
| 00:15:00 | `etapas` | 1.90 → 1.90 | 864, 12 → -864, 0 |
| 00:19:15 | `sim_tab` | 1.60 → 1.00 | 0, -324 → 0, 0 |
| 00:21:15 | `sim_slider` | 2.20 → 2.20 | 0, 0 → 0, 0 |
| 00:25:00 | `sim_tiles` | 1.48 → 1.48 | 0, 0 → 0, 0 |
| 00:27:15 | `sim_curva` | 1.51 → 1.51 | 0, 0 → 0, 0 |
| 00:30:00 | `sim_lectura` | 1.76 → 1.86 | 0, 0 → 0, 0 |
| 00:33:15 | `lista_mapa` | 1.12 → 1.17 | 0, -66 → 0, -93 |
| 00:36:00 | `lista_tabla` | 1.00 → 1.45 | 0, 0 → 387, -243 |
| 00:39:00 | `lista_ficha` | 1.75 → 1.75 | -720, -405 → -720, -35 |
| 00:43:00 | `importancia` | 1.70 → 1.79 | 0, -32 → 0, -33 |
| 00:45:15 | `red_grafo` | 1.43 → 1.75 | -304, 86 → -373, 73 |
| 00:49:00 | `red_tiles` | 1.45 → 1.50 | 0, 0 → 0, 0 |
| 00:51:00 | `pitch` | 1.54 → 1.65 | 0, -3 → 0, -3 |

**Títulos** (blanco, Segoe UI Bold, centrados):

| Aparece | Pista | Texto | Tamaño |
|---|---|---|---|
| 00:00:04 | V4 | ¿A qué empresas debemos contactar? | 84 |
| 00:03:02 | V4 | 664,548 empresas evaluadas. | 80 |
| 00:04:15 | V5 | Solo 5,000 contactos por campaña. | 80 |
| 00:09:00 | V4 | ¿Cuánto? | 190 |
| 00:09:04 | V5 | Base habilitada | 52 |
| 00:18:15 | V4 | ¿Y si cambia? | 180 |
| 00:18:19 | V5 | La capacidad comercial | 52 |
| 00:32:15 | V4 | ¿Quiénes? | 190 |
| 00:32:19 | V5 | Probabilidad de conversión | 52 |
| 00:42:00 | V4 | ¿Por qué? | 190 |
| 00:42:04 | V5 | Sustento de negocio | 52 |
| 00:57:18 | V4 | ¿Cuánto?    ¿Quiénes?    ¿Por qué? | 88 |
| 00:58:12 | V5 | Campaña de factoring · DataFest 2026 | 38 |
<!-- /EDITABLE -->

En cada toma, el valor de la izquierda va en el primer keyframe y el de la derecha en el último. Los keyframes intermedios mantienen el encuadre antes de moverse.

## 4. Exportar

1. Abre la página **Deliver**, con el cohete abajo a la derecha.
2. Elige el preset **H.264 Master** o configura MP4, H.264, 1920 x 1080 y 30 fps, con audio AAC.
3. Indica nombre y carpeta, y pulsa **Add to Render Queue** y luego **Render All**.

`previa_60s.mp4` es la referencia de ritmo y encuadre.

## Cambiar las cifras

- **Versión editable:** cambia los títulos en Resolve. Las grabaciones del dashboard se regraban con `construir_editable.ps1 -SoloArmar` o a mano, como explica [GUIA_PREMIERE.md](GUIA_PREMIERE.md#regrabar-la-pantalla-a-mano). Después, ejecuta `python armar_davinci_editable.py`.
- **Versión renderizada:** regenera los clips con [README.md](README.md#regenerar-con-el-modelo-real) y ejecuta `python armar_davinci.py`.
- **Aviso de V2/V3:** las tomas actuales muestran las cifras simuladas anteriores. Quita el aviso solo después de regrabarlas.
