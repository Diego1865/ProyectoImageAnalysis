r"""Experimentos reproducibles para el informe. No modifica la aplicación Tkinter.

Ejecutar desde la raíz: .\env\Scripts\python.exe PracticaSegmentacion/experimento_segmentacion.py
"""
from pathlib import Path
import csv
import json
import sys

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidencia'
ROI = (490, 280, 125, 330)
AREA_MIN = 150
SEED = 2026


def kapur(image):
    """Maximiza H(clase <= t) + H(clase > t), sin ponderar por masa."""
    p = np.bincount(image.ravel(), minlength=256).astype(float) / image.size
    cumulative = np.cumsum(p)
    term = np.zeros(256)
    valid = p > 0
    term[valid] = -p[valid] * np.log(p[valid])
    h = np.cumsum(term)
    score = np.full(256, -np.inf)
    for t in range(255):
        w = cumulative[t]
        if 1e-12 < w < 1 - 1e-12:
            score[t] = h[t] / w + np.log(w) + (h[-1] - h[t]) / (1-w) + np.log(1-w)
    return int(np.argmax(score)) if np.isfinite(score).any() else int(image.flat[0])


def histogram_minimum(image):
    """Valle entre dos máximos locales altos separados al menos 20 niveles.

    Suaviza histograma con gaussiana sigma=2. Si no hay dos picos, lo informa;
    no sustituye silenciosamente por otro método.
    """
    hist = np.bincount(image.ravel(), minlength=256).astype(np.float32)
    hist = cv2.GaussianBlur(hist.reshape(1, -1), (0, 0), 2).ravel()
    peaks = [i for i in range(1, 255) if hist[i] > hist[i-1] and hist[i] >= hist[i+1]]
    peaks.sort(key=lambda i: hist[i], reverse=True)
    for a in peaks:
        for b in peaks:
            if abs(a-b) >= 20:
                lo, hi = sorted((a, b))
                return lo + int(np.argmin(hist[lo:hi+1]))
    return None


def transform(image, method):
    """Transformaciones puntuales de la guía; cálculo siempre en coma flotante."""
    r = image.astype(np.float64) / 255
    if method == 'uniforme':
        return cv2.equalizeHist(image)
    functions = {
        'exponencial': lambda: 1-np.exp(-r),
        'rayleigh_guia': lambda: np.sqrt(r),
        'hipercubica': lambda: r**4,
        'logaritmica': lambda: np.log1p(image.astype(float))/np.log(256),
        'potencia_2': lambda: r**2,
        'gamma_07': lambda: r**.7,
        'gamma_15': lambda: r**1.5,
        'desplazamiento_30': lambda: r+30/255,
        'desplazamiento_m30': lambda: r-30/255,
        'contraccion': lambda: (80+120*r)/255,
        'expansion': lambda: (image.astype(float)-float(image.min())) / max(float(image.max())-float(image.min()), 1),
    }
    if method not in functions:
        raise ValueError(method)
    return np.clip(np.rint(255*functions[method]()), 0, 255).astype(np.uint8)


def mask(image, method):
    if method == 'Otsu':
        t, result = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        return float(t), result
    if method == 'Kapur':
        t = kapur(image)
    elif method == 'Minimo':
        t = histogram_minimum(image)
        if t is None:
            return None, None
    elif method == 'Media':
        t = float(np.mean(image))
    else:
        raise ValueError(method)
    return float(t), np.uint8(image <= t)*255


def measurements(binary, min_area=AREA_MIN):
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    records = []
    cleaned = np.zeros_like(binary)
    for label in range(1, n):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        component = np.uint8(labels == label)*255
        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        perimeter = sum(cv2.arcLength(c, True) for c in contours)
        cleaned[labels == label] = 255
        records.append(dict(area=area, perimeter=round(perimeter, 2),
                            cx=round(float(centroids[label, 0]), 2),
                            cy=round(float(centroids[label, 1]), 2)))
    records.sort(key=lambda a: a['cy'])
    return int(n-1), records, cleaned


def fill_holes(binary):
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    flooded = padded.copy()
    cv2.floodFill(flooded, None, (0, 0), 255)
    return cv2.bitwise_or(padded, cv2.bitwise_not(flooded))[1:-1, 1:-1]


def panel(items, path, columns=3, title=None):
    rows = (len(items)+columns-1)//columns
    fig, axes = plt.subplots(rows, columns, figsize=(columns*3.2, rows*3.5), squeeze=False)
    for ax, item in zip(axes.ravel(), items):
        label, arr = item
        ax.imshow(arr, cmap='gray' if arr.ndim == 2 else None, vmin=0, vmax=255)
        ax.set_title(label, fontsize=10)
        ax.axis('off')
    for ax in axes.ravel()[len(items):]:
        ax.axis('off')
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def checks():
    # Límites y convenciones que afectan directamente las medidas del informe.
    a = np.array([[0, 64, 128, 255]], np.uint8)
    assert transform(a, 'gamma_07')[0, 1] > a[0, 1]
    assert transform(a, 'gamma_15')[0, 1] < a[0, 1]
    np.testing.assert_array_equal(transform(a, 'desplazamiento_30'), [[30, 94, 158, 255]])
    assert transform(a, 'contraccion').min() == 80
    assert transform(a, 'contraccion').max() == 200
    assert 20 <= kapur(np.array([[20, 20, 200, 200]], np.uint8)) < 200
    ring = np.zeros((20, 20), np.uint8)
    ring[3:17, 3:17] = 255
    ring[7:13, 7:13] = 0
    assert fill_holes(ring).sum() == 196*255
    _, records, _ = measurements(fill_holes(ring), 1)
    assert records[0]['area'] == 196 and records[0]['perimeter'] == 52


def run():
    checks()
    OUT.mkdir(exist_ok=True)
    summary = dict(roi_xywh=ROI, min_area=AREA_MIN, seed=SEED, connectivity=8,
                   versions=dict(python=sys.version.split()[0], opencv=cv2.__version__, numpy=np.__version__), images={})
    flat = []
    for name in ['monedas_separadas', 'monedas_juntas']:
        bgr = cv2.imread(str(ROOT/'imagenes'/f'{name}.jpeg'))
        if bgr is None:
            raise FileNotFoundError(name)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        full = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        x, y, w, h = ROI
        source = full[y:y+h, x:x+w].copy()
        folder = OUT/name
        folder.mkdir(exist_ok=True)
        marked = rgb.copy()
        cv2.rectangle(marked, (x, y), (x+w-1, y+h-1), (255, 0, 0), 3)
        panel([('Fotografia y ROI', marked), ('ROI original', source)], folder/'escena.png', 2)
        stages = {'Original': source, 'Mediana 5': cv2.medianBlur(source, 5),
                  'Mediana 5 + gamma 0.7': transform(cv2.medianBlur(source, 5), 'gamma_07')}
        results = []
        for stage, arr in stages.items():
            items = [(stage, arr)]
            for method in ['Otsu', 'Kapur', 'Minimo', 'Media']:
                t, binary = mask(arr, method)
                if binary is None:
                    continue
                raw, regions, _ = measurements(binary)
                row = dict(image=name, stage=stage, method=method, threshold=round(t, 2),
                           raw_count=raw, count=len(regions), area=sum(r['area'] for r in regions),
                           perimeter=round(sum(r['perimeter'] for r in regions), 2))
                results.append(row)
                flat.append(row)
                items.append((f'{method}: T={t:.1f}; N={len(regions)}', binary))
                cv2.imwrite(str(folder/f'{stage.replace(" ", "_")}_{method}.png'), binary)
            panel(items, folder/f'umbral_{list(stages).index(stage)}.png', 3)
        multi = np.where(source < 80, 0, np.where(source < 150, 127, 255)).astype(np.uint8)
        band = np.uint8((source >= 80) & (source <= 150))*255
        panel([('ROI original', source), ('Tres clases: 80 y 150', multi), ('Banda [80, 150]', band)], folder/'banda_multi.png')
        methods = ['uniforme', 'exponencial', 'rayleigh_guia', 'hipercubica', 'logaritmica',
                   'potencia_2', 'gamma_07', 'gamma_15', 'desplazamiento_30', 'desplazamiento_m30', 'contraccion', 'expansion']
        brightness = []
        for m in methods:
            arr = transform(source, m)
            t, binary = mask(arr, 'Otsu')
            raw, regions, _ = measurements(binary)
            brightness.append(dict(method=m, mean=round(float(arr.mean()), 2), min=int(arr.min()),
                                   max=int(arr.max()), threshold=t, count=len(regions), raw_count=raw))
        for start in [0, 6]:
            panel([(m.replace('_', ' '), transform(source, m)) for m in methods[start:start+6]],
                  folder/f'brillo_{start//6}.png', 3)
        fig, ax = plt.subplots(figsize=(8, 3))
        for label, arr in [('Original', source), ('Uniforme', transform(source, 'uniforme')),
                           ('Gamma 0.7', transform(source, 'gamma_07')), ('Expansion', transform(source, 'expansion'))]:
            ax.plot(np.bincount(arr.ravel(), minlength=256), label=label, linewidth=1)
        ax.set(xlabel='Intensidad', ylabel='Frecuencia', xlim=(0, 255))
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(folder/'histogramas.png', dpi=160)
        plt.close(fig)
        rng = np.random.default_rng(SEED)
        sp = source.copy()
        positions = rng.choice(source.size, int(.03*source.size), replace=False)
        sp.flat[positions] = rng.choice([0, 255], len(positions)).astype(np.uint8)
        gn = np.clip(source.astype(float)+np.random.default_rng(SEED).normal(0, 15, source.shape), 0, 255).astype(np.uint8)
        noise_records = []
        noise_items = []
        for label, noisy in [('Sal y pimienta', sp), ('Gaussiano', gn)]:
            for filtering, arr in [('Sin filtro', noisy), ('Mediana 5', cv2.medianBlur(noisy, 5)),
                                   ('Gaussiano 5', cv2.GaussianBlur(noisy, (5, 5), 0))]:
                t, binary = mask(arr, 'Otsu')
                raw, regions, _ = measurements(binary)
                noise_records.append(dict(noise=label, filtering=filtering,
                    mae=round(float(np.mean(np.abs(arr.astype(float)-source))), 3),
                    threshold=t, raw_count=raw, count=len(regions)))
                noise_items.append((f'{label}\n{filtering}', arr))
        panel(noise_items, folder/'ruido_filtros.png', 3)
        # Orden de operaciones y filtro paso altas: solo ilustración visual, no máscara.
        before = cv2.medianBlur(transform(sp, 'gamma_07'), 5)
        after = transform(cv2.medianBlur(sp, 5), 'gamma_07')
        sharp_source = transform(cv2.GaussianBlur(gn, (5, 5), 0), 'gamma_07')
        high = np.clip(sharp_source.astype(float)-.3*cv2.Laplacian(sharp_source, cv2.CV_64F), 0, 255).astype(np.uint8)
        panel([('Gamma y luego mediana', before), ('Mediana y luego gamma', after),
               ('Gaussiano, gamma y realce', high)], folder/'orden.png', 3)
        corrected = stages['Mediana 5 + gamma 0.7']
        t, initial = mask(corrected, 'Otsu')
        closed = cv2.morphologyEx(initial, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        filled = fill_holes(closed)
        opened = cv2.morphologyEx(filled, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        raw, regions, final = measurements(opened)
        overlay = cv2.cvtColor(source, cv2.COLOR_GRAY2RGB)
        contours, _ = cv2.findContours(final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(overlay, contours, -1, (255, 0, 0), 1)
        for i, r in enumerate(regions, 1):
            r['number'] = i
            cv2.putText(overlay, str(i), (int(r['cx']), int(r['cy'])), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 150, 255), 1)
        panel([('ROI original', source), ('Otsu tras mediana y gamma', initial),
               ('Cierre 5, relleno, apertura 3', final), ('Contornos y etiquetas', overlay)], folder/'final.png', 4)
        cv2.imwrite(str(folder/'mascara_final.png'), final)
        tfull, fullmask = mask(full, 'Otsu')
        panel([('Grises de escena completa', full), (f'Otsu global T={tfull:.0f}', fullmask)], folder/'global.png', 2)
        summary['images'][name] = dict(shape=list(full.shape), source_mean=round(float(source.mean()), 2),
            source_min=int(source.min()), source_max=int(source.max()), thresholds=results,
            brightness=brightness, noise=noise_records, final=dict(threshold=t, raw_count=raw,
            count=len(regions), regions=regions, area=sum(r['area'] for r in regions),
            perimeter=round(sum(r['perimeter'] for r in regions), 2)),
            order_max_difference=int(np.max(np.abs(before.astype(int)-after.astype(int)))))
    (OUT/'resultados.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    with (OUT/'comparacion_umbrales.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
