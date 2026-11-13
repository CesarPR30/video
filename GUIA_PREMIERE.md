# Guía para editar el video en Premiere, sin Claude

Todo lo de esta guía se hace a mano en Premiere. Abre `Demo_Factoring_Editable.prproj`.

## Qué es editable

| Pista | Contenido | Cómo se cambia |
|---|---|---|
| V1 | Grabaciones y fondos | Movimiento en Controles de efectos |
| V2 | Ventana flotante y logo | Escala y Opacidad |
| V3 | Aviso de cifras simuladas | Borrar cuando exista el modelo real |
| V4 y V5 | Títulos | Doble clic en el texto, o panel Gráficos esenciales |
| A1 y A2 | Efectos de sonido | Arrastrar, borrar o cambiar ganancia |
| A3 | Música | Reemplazar por otra pista |

## Cambiar un texto

1. Selecciona el clip de texto en V4 o V5.
2. Con la herramienta Texto (T), haz clic sobre él en el Monitor de programa y escribe.
3. La fuente y el color se cambian en Gráficos esenciales.
4. El tamaño se ajusta en **Controles de efectos > Texto > Transformar > Escala**. Por ejemplo, 190 en los títulos grandes.

## Cambiar un zoom

Cada toma tiene keyframes en **Controles de efectos > Movimiento > Escala y Posición**.

- **Escala 50 %** es la pantalla completa. **100 %** es zoom 2x, el máximo sin perder nitidez.
- Para un zoom más lento, separa los keyframes. Para uno más rápido, acércalos.
- Para suavizar: clic derecho en el keyframe > **Bézier automático**, o **Suavizar entrada** y **Suavizar salida**.
- Si sobra Movimiento en una toma, borra los keyframes y deja Escala en 50 % y Posición en 960, 540.

## Agregar sombra a la ventana flotante

La ventana (`ventana_resumen` y `ventana_cierre`, en V2) no trae sombra y tiene las esquinas rectas.

1. En Efectos, busca **Sombra paralela** y arrástrala a cada clip.
2. En Controles de efectos usa Opacidad 45 %, Dirección 180°, Distancia 22 y Suavizado 80.

## Regrabar la pantalla a mano

Hazlo cuando cambien las cifras y no puedas correr los scripts.

1. Abre `dashboard/index.html` con doble clic. No necesita internet.
2. Pon el navegador en pantalla completa con **F11**.
3. Graba con **Win + Alt + R**, o con OBS a 2560×1440 y 30 fps.
4. Graba cada toma por separado, unos segundos más larga de lo necesario.
5. Mueve el mouse despacio y haz pausas antes de cada clic.

Para reemplazar sin perder keyframes:

1. Importa la grabación en Premiere.
2. Selecciona el clip en la línea de tiempo.
3. Mantén **Alt** y arrastra la grabación del panel Proyecto sobre el clip.

Los keyframes se conservan, pero el encuadre cambia porque tu grabación no es 4K. Con grabación de 2560×1440, multiplica cada Escala por 1.5: los 50 % pasan a 75 % y el máximo nítido será 100 %, o sea zoom de 1.33x. Más que eso se verá algo suave.

Las tomas de tarjetas aisladas se grabaron con el resto de la pantalla oculto. Si las grabas a mano, usa zoom sobre la tarjeta real, o agrega el efecto **Recortar** sobre un fondo de color.

## Regenerar con scripts

**No necesitas a Claude para esto**, solo Python y este proyecto:

```
cd video
powershell -ExecutionPolicy Bypass -File construir_editable.ps1
```

Guarda tu trabajo y cierra Premiere antes de correrlo. Si ya existe el proyecto, lo renombra como respaldo y crea uno nuevo: **tus ediciones a mano no pasan al nuevo**. Para actualizar sin perderlas, reemplaza las grabaciones de `clips_editable/` y conserva el proyecto.

Si solo cambió el texto de un título, cámbialo a mano. Los scripts leen las cifras de `dashboard/inputs/`.

**Nunca lances el script con Premiere abierto:** cerraría esa sesión.

El script tarda unos 6 minutos y deja cuadros de control en `verificacion/`.

## Las tomas

Los valores salen de los keyframes del proyecto.

<!-- TOMAS -->
| Inicio | Dura | Toma | Escala | Posición (x, y) |
|---|---|---|---|---|
| 00:00:00 | 3 s | `t_pregunta` | título | texto en V4 y V5 |
| 00:03:00 | 3 s | `t_cifras` | título | texto en V4 y V5 |
| 00:06:00 | 3 s | `ventana_resumen` | ventana flotante | ver Movimiento en V2 |
| 00:09:00 | 1 s | `t_cuanto` | título | texto en V4 y V5 |
| 00:10:00 | 2.5 s | `hero_figura` | 92 % → 95 % | 1772, 705 → 1824, 592 |
| 00:12:15 | 2.5 s | `hero_kpis` | 109 % → 109 % | 1802, 540 → 118, 579 |
| 00:15:00 | 3.5 s | `etapas` | 95 % → 95 % | 1824, 528 → 96, 540 |
| 00:18:15 | 1 s | `t_simula` | título | texto en V4 y V5 |
| 00:19:15 | 2 s | `sim_tab` | 80 % → 50 % | 960, 864 → 960, 540 |
| 00:21:15 | 3.5 s | `sim_slider` | 110 % → 110 % | 960, 540 → 960, 540 |
| 00:25:00 | 2.5 s | `sim_tiles` | 74 % → 74 % | 960, 540 → 960, 540 |
| 00:27:15 | 2.5 s | `sim_curva` | 75 % → 75 % | 960, 540 → 960, 540 |
| 00:30:00 | 2.5 s | `sim_lectura` | 88 % → 93 % | 960, 540 → 960, 540 |
| 00:32:15 | 1 s | `t_quienes` | título | texto en V4 y V5 |
| 00:33:15 | 2.5 s | `lista_mapa` | 56 % → 59 % | 960, 606 → 960, 633 |
| 00:36:00 | 3 s | `lista_tabla` | 50 % → 72 % | 960, 540 → 1347, 783 |
| 00:39:00 | 3 s | `lista_ficha` | 88 % → 88 % | 240, 945 → 240, 575 |
| 00:42:00 | 1 s | `t_porque` | título | texto en V4 y V5 |
| 00:43:00 | 2.5 s | `importancia` | 85 % → 90 % | 960, 572 → 960, 573 |
| 00:45:15 | 3.5 s | `red_grafo` | 71 % → 87 % | 656, 454 → 587, 467 |
| 00:49:00 | 2 s | `red_tiles` | 72 % → 75 % | 960, 540 → 960, 540 |
| 00:51:00 | 4.5 s | `pitch` | 77 % → 83 % | 960, 543 → 960, 543 |
| 00:55:15 | 2 s | `ventana_cierre` | ventana flotante | ver Movimiento en V2 |
| 00:57:15 | 2.5 s | `t_cierre` | título | texto en V4 y V5 |
<!-- /TOMAS -->
