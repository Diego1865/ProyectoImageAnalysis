# Laboratorio de Análisis de Imágenes

## Ejecutar

Desde la raíz del proyecto en PowerShell:

```powershell
.\env\Scripts\python.exe image_processing_lab.py
```

Dependencias: `requirements_image_processing_lab.txt`.

## Funciones integradas

- **Práctica 1 - Pseudocolor:** mapas de OpenCV y mapas personalizados.
- **Práctica 2:** grises, RGB, HSV (matiz, saturación y brillo), histograma.
- **Miniproyecto ECC:** segmentación fija/Otsu, inversión, conteo V4/V8,
  regiones con colores, contornos y números, área, caja y centroide,
  código de cadena Freeman de cada contorno exterior.
- **Ruido:** sal y pimienta con proporción configurable; gaussiano con media y sigma.
- **Filtros:** mediana y gaussiano con ventana configurable.
- **Operaciones lógicas:** AND, OR, XOR con una imagen B y NOT.
- **Relacionales:** >, < y == respecto a un nivel de gris configurable.
- **Experimentos:** comparación base/ruido/filtro y lote de al menos cuatro fotografías.
- **Evidencia:** exportación PNG, conteos CSV, parámetros, regiones y cadenas JSON.

## Flujo del miniproyecto

1. Abre una foto y entra en **Miniproyecto ECC > Parámetros del experimento**.
2. Elige Otsu o umbral fijo. Activa **objetos oscuros** cuando el fondo sea claro.
   Segmentar produce objetos blancos y fondo negro.
3. Aplica **Segmentar**, revisa la máscara y después **Comparar conteo V4 / V8**.
   Si la máscara ya es binaria, el conteo conserva su polaridad; usa NOT si está invertida.
4. La tabla muestra el conteo bruto y el conteo tras el filtro de área por separado.
   El valor inicial de área mínima es 20 píxeles; usa 1 para conservar todas las regiones.
5. Selecciona una región en la lista para ver sus propiedades y código de cadena.
   El código incluye el cierre del contorno. Convención: 0 E, 1 NE, 2 N, 3 NO,
   4 O, 5 SO, 6 S, 7 SE. No describe agujeros interiores.
6. Para comparar antes y después, ejecuta **Experimento antes / ruido / filtro**.
   Sal y pimienta se aplica a la máscara y se limpia con mediana. El ruido
   gaussiano se aplica a los grises y se suaviza antes de segmentar de nuevo.
7. Para las cuatro imágenes, ejecuta **Experimento por lote**. Todas usan los
   parámetros actuales. La semilla fija permite repetir el experimento.
8. En resultados elige una imagen para verla o pulsa **Exportar evidencia**.
   Se crea una subcarpeta nueva, conservando exportaciones anteriores. El archivo
   `imagenes.json` relaciona cada PNG con su etapa. Los resultados de una ventana
   conservan los parámetros utilizados aunque cambies los ajustes posteriormente.

Para operaciones lógicas, carga B desde el menú. A y B deben tener el mismo tamaño;
no se redimensionan automáticamente. Las imágenes no binarias se segmentan con los
parámetros actuales. NOT intercambia objeto y fondo, por lo que también cambia la
interpretación del conteo. Las operaciones que modifican la imagen pasan por el
historial y permiten Deshacer/Rehacer; las comparaciones abren ventanas independientes.

El ECC cuenta regiones conectadas: dos objetos que se tocan o traslapan pueden
contar como una sola región. V8 conecta diagonales; V4 solo conecta vecinos
ortogonales. El filtro de área puede eliminar objetos pequeños reales: compara
siempre el conteo bruto, el filtrado y la inspección manual. Puedes repetir con
distintos umbrales y condiciones de captura para discutir sus efectos.

## Organización del código

- `image_processing_lab.py`: aplicación principal, interfaz e historial existentes.
- `image_lab/experiments.py`: procesamiento de matrices, sin interfaz.
- `image_lab/experiment_ui.py`: parámetros, acciones, resultados y exportación ECC.
- `tests/test_experiments.py`: comprobaciones de conectividad, ruido, operaciones,
  segmentación, códigos de cadena e integración con el historial.

Las imágenes de color en la aplicación usan RGB. Las máscaras usan 0 y 255.
El reporte, la reflexión individual y la presentación se elaboran a partir de
resultados reales; el programa no los genera automáticamente.

## Verificar

```powershell
.\env\Scripts\python.exe -m unittest discover -s tests -v
```
