"""Segmentación, ruido y ECC sobre matrices, sin dependencia de Tkinter.

Las imágenes de color usan RGB. Las máscaras usan 0=fondo, 255=objeto.
"""
import cv2
import numpy as np


def gray(image):
    arr = np.asarray(image, dtype=np.uint8)
    if arr.ndim == 2:
        return arr.copy()
    if arr.ndim == 3 and arr.shape[2] == 3:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    raise ValueError('Se requiere una imagen RGB o en escala de grises.')


def segment(image, method='otsu', threshold=127, dark=False):
    source = gray(image)
    mode = cv2.THRESH_BINARY_INV if dark else cv2.THRESH_BINARY
    if method == 'otsu':
        mode |= cv2.THRESH_OTSU
    elif method != 'fixed':
        raise ValueError('Método de segmentación desconocido.')
    value, mask = cv2.threshold(source, threshold if method == 'fixed' else 0, 255, mode)
    return value, mask


def salt_pepper(image, amount=.02, seed=2026):
    if not 0 <= amount <= 1:
        raise ValueError('La proporción de ruido debe estar entre 0 y 1.')
    result = np.asarray(image, dtype=np.uint8).copy()
    rng = np.random.default_rng(seed)
    positions = rng.choice(result.shape[0] * result.shape[1],
                           int(amount * result.shape[0] * result.shape[1]), replace=False)
    y, x = np.unravel_index(positions, result.shape[:2])
    values = rng.choice([0, 255], len(positions)).astype(np.uint8)
    result[y, x] = values if result.ndim == 2 else values[:, None]
    return result


def gaussian_noise(image, sigma=20, mean=0, seed=2026):
    if sigma < 0:
        raise ValueError('Sigma debe ser mayor o igual a cero.')
    rng = np.random.default_rng(seed)
    arr = np.asarray(image, dtype=np.uint8)
    return np.clip(arr.astype(float) + rng.normal(mean, sigma, arr.shape), 0, 255).astype(np.uint8)


def smooth(image, method='median', kernel=3):
    if kernel < 3 or kernel % 2 != 1:
        raise ValueError('El tamaño de ventana debe ser impar y al menos 3.')
    if method == 'median':
        return cv2.medianBlur(image, kernel)
    if method == 'gaussian':
        return cv2.GaussianBlur(image, (kernel, kernel), 0)
    raise ValueError('Filtro desconocido.')


def logical(a, b=None, operation='AND'):
    if operation == 'NOT':
        return cv2.bitwise_not(a)
    if b is None or a.shape != b.shape:
        raise ValueError('Las máscaras A y B deben tener exactamente el mismo tamaño.')
    functions = {'AND': cv2.bitwise_and, 'OR': cv2.bitwise_or, 'XOR': cv2.bitwise_xor}
    if operation not in functions:
        raise ValueError('Operación lógica desconocida.')
    return functions[operation](a, b)


def relational(image, operation, value):
    functions = {'>': np.greater, '<': np.less, '==': np.equal}
    if operation not in functions:
        raise ValueError('Operación relacional desconocida.')
    return np.uint8(functions[operation](gray(image), value)) * 255


def components(mask, connectivity=8, min_area=1):
    if connectivity not in (4, 8) or min_area < 1:
        raise ValueError('Vecindad 4 u 8 y área mínima positiva requeridas.')
    mask = gray(mask)
    if not np.isin(mask, [0, 255]).all():
        raise ValueError('ECC requiere una máscara binaria (0 y 255).')
    n, labels, stats, centers = cv2.connectedComponentsWithStats(mask, connectivity=connectivity)
    regions = []
    view = np.zeros((*mask.shape, 3), dtype=np.uint8)
    rng = np.random.default_rng(42)
    for label in range(1, n):
        x, y, w, h, area = map(int, stats[label])
        if area < min_area:
            continue
        number = len(regions) + 1
        roi = labels[y:y+h, x:x+w] == label
        region = np.uint8(roi) * 255
        contours, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        patch = view[y:y+h, x:x+w]
        patch[roi] = rng.integers(70, 240, size=3)
        cv2.drawContours(patch, contours, -1, (255, 255, 255), 1)
        cx, cy = map(float, centers[label])
        cv2.putText(view, str(number), (x, max(y + 13, 13)), cv2.FONT_HERSHEY_SIMPLEX,
                    .45, (255, 255, 255), 1)
        regions.append(dict(number=number, label=label, area=area, x=x, y=y,
                            width=w, height=h, cx=cx, cy=cy))
    return dict(raw_count=n-1, count=len(regions), regions=regions, labels=labels, view=view)


def chain_code(labels, label, bounds=None):
    """Freeman-8 de un contorno exterior, incluido el paso de cierre.

    Coordenadas de imagen: x a la derecha, y hacia abajo. No incluye agujeros.
    """
    x, y = 0, 0
    if bounds is not None:
        x, y, w, h = bounds
        labels = labels[y:y+h, x:x+w]
    contours, _ = cv2.findContours(np.uint8(labels == label) * 255,
                                  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise ValueError('La región seleccionada no existe.')
    points = max(contours, key=len).reshape(-1, 2)
    points = points + np.array([x, y])
    directions = {(1, 0): 0, (1, -1): 1, (0, -1): 2, (-1, -1): 3,
                  (-1, 0): 4, (-1, 1): 5, (0, 1): 6, (1, 1): 7}
    code = [] if len(points) == 1 else [directions[tuple(map(int, b-a))]
            for a, b in zip(points, np.roll(points, -1, axis=0))]
    return dict(start_xy=points[0].tolist(), code=code, steps=len(code),
                convention='0 E, 1 NE, 2 N, 3 NO, 4 O, 5 SO, 6 S, 7 SE',
                note='Contorno exterior; no incluye agujeros. Un píxel aislado tiene 0 pasos.')
