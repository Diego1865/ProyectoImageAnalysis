# Segmentación de regiones y ajuste de brillo

La entrega es `Practica Segmentación.docx`. Falta únicamente el grupo. Se usaron las tres monedas como objetos de interés.

El script independiente complementa las funciones de la aplicación principal.
No añade los métodos nuevos a los menús de Tkinter.

Desde la raíz del proyecto, ejecutar en PowerShell:

```powershell
.\env\Scripts\python.exe PracticaSegmentacion/experimento_segmentacion.py
```

Los resultados se escriben en `evidencia`: imágenes PNG, máscaras finales,
`resultados.json` y `comparacion_umbrales.csv`. Se conservan las fotografías
sin modificar en `imagenes`. La región usada es x=490, y=280, ancho=125 y
alto=330, sin redimensionar. Las medidas se expresan en píxeles.

La foto con monedas separadas produce tres regiones finales. La foto con
monedas próximas produce dos: las dos superiores permanecen conectadas.
El informe analiza esta limitación; no afirma una segmentación perfecta.

La semilla del ruido es 2026. Los resultados se reproducen con las mismas
versiones y parámetros registrados en el JSON. Al ejecutar el script se
comprueban casos conocidos de gamma, saturación, contracción, Kapur,
relleno de huecos, área y perímetro.
