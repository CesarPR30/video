# Abrir el video en DaVinci Resolve

DaVinci Resolve no abre proyectos de Premiere (`.prproj`), pero importa la secuencia en XML. Se convierte la versión renderizada de 60 s, porque la cámara, el cursor y los títulos ya vienen dentro de cada clip y pasan sin pérdidas.

La versión editable no se convierte: sus títulos y zooms son efectos propios de Premiere.

## 1. Preparar los archivos

Instala DaVinci Resolve desde [blackmagicdesign.com](https://www.blackmagicdesign.com/products/davinciresolve). La versión gratuita basta.

En la carpeta `video/`, ejecuta:

```
python armar_davinci.py
```

Esto crea `Demo_Factoring_DaVinci.xml` con las rutas de tu computadora. Si mueves o vuelves a clonar la carpeta, ejecútalo otra vez. Solo usa la librería estándar de Python.

## 2. Crear el proyecto

1. Abre Resolve y crea un proyecto nuevo.
2. Ve a **File > Project Settings > Master Settings** y fija:
   - **Timeline resolution:** 1920 x 1080 HD.
   - **Timeline frame rate:** 30.
   - **Playback frame rate:** 30.
3. Guarda los ajustes.

Hazlo antes de importar: Resolve no deja cambiar la cadencia del proyecto después.

## 3. Importar la secuencia

1. Ve a **File > Import > Timeline** (`Ctrl + Shift + I`) y elige `Demo_Factoring_DaVinci.xml`.
2. Deja marcada **Automatically import source clips into media pool** y acepta.
3. Si algún clip aparece en rojo, selecciónalo en el Media Pool, haz clic derecho en **Relink Selected Clips** y elige la carpeta `clips_60s`.

Revisa que se vea así:

| Pista | Contenido |
|---|---|
| V1 | 24 tomas con 23 disolvencias |
| V2 | Aviso "Cifras ilustrativas" |
| A1 y A2 | Efectos de sonido |
| A3 | Música estéreo |

La línea de tiempo dura 60 s y tiene 8 marcadores, uno por sección.

## 4. Exportar

1. Abre la página **Deliver**, con el cohete abajo a la derecha.
2. Elige el preset **H.264 Master** o configura MP4, H.264, 1920 x 1080 y 30 fps, con audio AAC.
3. Indica nombre y carpeta, y pulsa **Add to Render Queue** y luego **Render All**.

`previa_60s.mp4` es la referencia: el resultado debe verse y sonar igual.

## Cambiar el contenido

- **Cortes, orden, disolvencias y volumen:** edítalos en Resolve.
- **Cifras o títulos:** vienen grabados dentro de los clips, así que hay que regenerarlos con los pasos de [README.md](README.md#regenerar-con-el-modelo-real). Después, ejecuta `python armar_davinci.py` y vuelve a importar.
- **Aviso de V2:** las tomas actuales muestran las cifras simuladas anteriores. Quita el aviso solo después de regenerarlas.
