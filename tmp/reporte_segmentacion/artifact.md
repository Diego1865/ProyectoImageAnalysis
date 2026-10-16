# Contrato de la plantilla

Referencia: C:/Users/dibao/Downloads/plantilla_informe_practica-Segmentación.docx
SHA256: ae4b8d3a92b1d709dd93db71de7090b1f6c9ef45adc0c6aca996c5493f09378a
Una sección carta vertical 8.5 por 11 pulgadas, márgenes de 1 pulgada,
encabezado y pie a 0.5 pulgadas, una columna, sin encabezados ni pies.
La caché de app.xml indica dos páginas; render de referencia pendiente por
ausencia del LibreOffice incluido. Se intentó render_docx.py y se conserva el
diagnóstico. Conversión alternativa con Word en progreso.

Normal: tema minorHAnsi, 12 pt, después 8 pt, interlineado 278/240.
Title: 28 pt, después 4 pt. Heading 1: 20 pt, antes 18 pt, después 4 pt.
Heading 2: 16 pt, antes 8 pt, después 4 pt. La guía de documentos requiere
títulos negros, por lo que se elimina el color temático azul de los encabezados.
Se conservan la familia tipográfica y el sistema de página de la plantilla.

Slots: document.xml/body/p[2] título; p[4:6] nombre, grupo y fecha;
secciones Introducción, Resultados, Análisis y Discusión, Evaluación Técnica,
Conclusiones y Anexos. Los párrafos vacíos son slots de expansión. Los
subtítulos Heading2 se reutilizan para ordenar texto y resultados. La tabla
de cinco columnas vacía es el patrón de comparación de filtros, se expande
a cuatro filas de observaciones. Se añaden tablas numéricas derivadas de
este patrón. La extensión a más páginas es necesaria por las capturas.

Contenido: título identifica práctica 4 conforme al mensaje del usuario;
el cuerpo aclara que PDF y plantilla la numeran como 5. Datos personales
quedan en blanco. No hay campos, dibujos, controles, comentarios, notas o
encabezados en la fuente. El inventario completo se conserva en
template-inventory.json. Partes preservadas: tema, numeración, configuración,
fuentes, webSettings, core y app. Partes editables: document.xml, styles.xml,
relaciones del documento y Content_Types al incorporar imágenes.

Verificación: comparar hash de referencia y partes preservadas, geometría y
orden de secciones. Verificar medidas contra resultados.json. Renderizar
con Word como alternativa si el conversor incluido no está disponible,
inspeccionar todas las páginas PNG antes de entregar.

Resultado de QA: el conversor incluido no tenía LibreOffice. Word instalado
exportó correctamente al establecer la impresora de métricas Microsoft Print
to PDF. Referencia renderizada e inspeccionada: 2 páginas, template-render.
Documento final: 15 páginas, 12 figuras, 8 tablas. Render final en
verified-render. Todas las páginas se inspeccionaron; las páginas sin cambios
se comprobaron también por igualdad exacta de píxeles con el render revisado.
Se corrigieron saltos de página, párrafos huérfanos, bordes heredados de la
tabla y la interpretación de una diferencia nula en el orden de operaciones.
La referencia conserva su hash y todas las partes preserve-only permanecen
idénticas byte por byte. Se mantienen tamaño carta y márgenes originales.
El usuario solicitó finalmente DOCX, por lo que no se entrega formato DOC.
