# Video demo del dashboard

Video de 60 s exactos en 1920×1080 a 30 fps. Las tomas se generan del dashboard real, así que al cambiar los datos se regeneran sin grabar nada a mano.

## Dónde ubicar esta carpeta

Los scripts que regeneran las tomas leen el dashboard desde `../dashboard`. Clona este repositorio dentro del repositorio del dashboard:

```
git clone https://github.com/CesarPR30/web.git
cd web
git clone https://github.com/CesarPR30/video.git video
```

El repositorio del dashboard ya ignora la carpeta `video/`. Para abrir el video en DaVinci basta esta carpeta sola.

## Versiones

| Versión | Proyecto | Para qué |
|---|---|---|
| **DaVinci Resolve** | `Demo_Factoring_DaVinci.xml`, generado con `python armar_davinci.py` | Editar y exportar gratis. Ver [GUIA_DAVINCI.md](GUIA_DAVINCI.md). |
| Editable | `Demo_Factoring_Editable.prproj` | Trabajar a mano en Premiere. Ver [GUIA_PREMIERE.md](GUIA_PREMIERE.md). |
| Renderizada | `Demo_Factoring_60s.prproj` | Cámara y títulos ya dentro de los clips, en Premiere. |

La editable usa grabaciones 4K de `clips_editable/`, con zooms, títulos y ventana nativos de Premiere. Se construye con `construir_editable.ps1`, con Premiere cerrado.

## Archivos de la versión renderizada

| Archivo | Para qué sirve |
|---|---|
| `previa_60s.mp4` | Todo unido con su mezcla, para revisar sin abrir Premiere. |
| `Demo_Factoring_60s.prproj` | Proyecto de Premiere. |
| `Demo_Factoring_60s.xml` | La misma secuencia, para importarla en otro proyecto. |
| `clips_60s/*.mp4` | Una toma por archivo, con cuadros extra para ajustar disolvencias. |
| `clips_60s/aviso_simulado.png` | Aviso "Cifras ilustrativas" (pista V2). |
| `clips_60s/musica_60s.wav` | Música original, 120 BPM. |
| `clips_60s/sfx_*.wav` | Efectos originales. |
| `clips_60s/dumbbell.mp4` | Toma extra, fuera del timeline. |

`clips/`, `Demo_Factoring.prproj` y `Demo_Factoring.xml` son la versión anterior de 83 s. Los scripts ya no la regeneran.

## En Premiere

| Pista | Contenido |
|---|---|
| V1 | Tomas con disolvencias |
| V2 | Aviso de cifras simuladas |
| A1 y A2 | Efectos |
| A3 | Música estéreo |

Todos los cortes caen sobre el pulso (múltiplos de 0.5 s). La cámara y el cursor vienen dentro de cada clip. Los proyectos de Premiere usan rutas absolutas: si mueves `video/`, Premiere pedirá volver a vincular los archivos. Para DaVinci basta ejecutar de nuevo `armar_davinci.py`.

## Regenerar con el modelo real

1. Ejecutar `ACTUALIZAR.bat` (ver el README principal). El video actual todavía muestra las cifras simuladas anteriores.
2. Desde `video/`:

```
python tomas.py
python audio.py
python armar_premiere.py
python validar.py
```

Requiere `playwright`, `pillow`, `numpy` e `imageio-ffmpeg`. Tarda unos 5 minutos.

3. Para DaVinci, ejecutar `python armar_davinci.py` y volver a importar el XML.
4. Borrar el aviso de V2.

**Con las predicciones de ML conectadas hoy, `tomas.py` falla en la toma `importancia`:** el dashboard oculta esa tarjeta porque ML no entregó la importancia de variables. Hasta tenerla, hay que quitar esa toma de `DURACION` y repartir sus 2.5 s, junto con el título `t_porque`, entre otras tomas.

**Ojo:** `armar_premiere.py` sobrescribe el XML. Si ya editaste la secuencia en Premiere, no vuelvas a importarlo: como los clips conservan nombre y duración, Premiere toma los archivos nuevos.

## Cambiar tomas

- `tomas.py`: guion. `DURACION` define orden y largo; cada toma debe ser múltiplo de 0.5 s y el total, 60 s.
- `audio.py`: música y efectos. `GANANCIA` tiene el nivel de cada efecto.
- `graficos/titulo.html`: títulos y cierre. Las cifras se leen de `dashboard/inputs/`.
- `motor.py`: captura, cámara y cursor.
- `validar.py`: mide saltos cuadro por cuadro y velocidad de cámara.

Una sola toma: `python tomas.py sim_slider`.

Para sumar `dumbbell`, agregarla a `DURACION` y quitar 3.5 s de otras tomas. Hoy no entra porque, con datos simulados, todos los índices dan cerca de 1.00x.
