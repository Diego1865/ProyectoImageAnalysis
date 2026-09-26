from tkinter import *
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
import cv2

imagen_original = None
imagen_gris = None

def cargar_imagen():

    global imagen_original
    global imagen_gris

    ruta = filedialog.askopenfilename(
        title="Seleccionar imagen",
        filetypes=[
            ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
            ("Todos los archivos", "*.*")
        ]
    )

    if ruta == "":
        return

    try:

        imagen_original = Image.open(ruta).convert("RGB")
        imagen_gris = None

        mostrar_imagen_interfaz(imagen_original)

        etiqueta_archivo.config(
            text=f"Imagen cargada: {ruta}"
        )

        etiqueta_info.config(
            text=f"Tamaño: {imagen_original.width} x "
                 f"{imagen_original.height} píxeles | "
                 f"Modo: {imagen_original.mode}"
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            f"No se pudo abrir la imagen.\n\n{error}"
        )

def mostrar_imagen_interfaz(imagen):
    imagen_preview = imagen.copy()
    # Tamaño máximo para mostrar dentro de la interfaz
    imagen_preview.thumbnail(
        (650, 400),
        Image.Resampling.LANCZOS
    )
    imagen_tk = ImageTk.PhotoImage(imagen_preview)
    panel_imagen.config(
        image=imagen_tk,
        text=""
    )
    # Evitar que Python elimine la imagen de memoria
    panel_imagen.image = imagen_tk

def verificar_imagen():

    if imagen_original is None:

        messagebox.showwarning(
            "Aviso",
            "Primero debes cargar una imagen."
        )

        return False

    return True

def separar_rgb():

    if not verificar_imagen():
        return

    r, g, b = imagen_original.split()

    plt.figure(figsize=(12, 4))

    plt.subplot(1, 3, 1)
    plt.imshow(r, cmap="Reds")
    plt.title("Componente Rojo")
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.imshow(g, cmap="Greens")
    plt.title("Componente Verde")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.imshow(b, cmap="Blues")
    plt.title("Componente Azul")
    plt.axis("off")

    plt.tight_layout()
    plt.show()

def convertir_grises():

    global imagen_gris

    if not verificar_imagen():
        return

    imagen_np = np.array(imagen_original)

    imagen_gris = cv2.cvtColor(
        imagen_np,
        cv2.COLOR_RGB2GRAY
    )

    imagen_pil = Image.fromarray(imagen_gris)

    mostrar_imagen_interfaz(imagen_pil)

    etiqueta_resultado.config(
        text="Resultado actual: Escala de grises"
    )

def mostrar_original():

    if not verificar_imagen():
        return

    mostrar_imagen_interfaz(imagen_original)

    etiqueta_resultado.config(
        text="Resultado actual: Imagen original"
    )

def mostrar_histograma():

    if not verificar_imagen():
        return

    gris = cv2.cvtColor(
        np.array(imagen_original),
        cv2.COLOR_RGB2GRAY
    )

    plt.figure(figsize=(8, 5))

    plt.hist(
        gris.ravel(),
        bins=256,
        range=[0, 256]
    )

    plt.title("Histograma de intensidad")
    plt.xlabel("Nivel de intensidad")
    plt.ylabel("Cantidad de píxeles")
    plt.grid()

    plt.show()

def binarizar():

    if not verificar_imagen():
        return

    gris = cv2.cvtColor(
        np.array(imagen_original),
        cv2.COLOR_RGB2GRAY
    )

    # Obtener valor del control deslizante
    umbral = slider_umbral.get()

    _, binaria = cv2.threshold(
        gris,
        umbral,
        255,
        cv2.THRESH_BINARY
    )

    imagen_pil = Image.fromarray(binaria)

    mostrar_imagen_interfaz(imagen_pil)

    etiqueta_resultado.config(
        text=f"Resultado actual: Binarización | Umbral = {umbral}"
    )

def binarizar_otsu():

    if not verificar_imagen():
        return

    gris = cv2.cvtColor(
        np.array(imagen_original),
        cv2.COLOR_RGB2GRAY
    )

    umbral, binaria = cv2.threshold(
        gris,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    imagen_pil = Image.fromarray(binaria)

    mostrar_imagen_interfaz(imagen_pil)

    etiqueta_resultado.config(
        text=f"Binarización automática Otsu | "
             f"Umbral calculado = {umbral:.0f}"
    )

def mostrar_hsv():

    if not verificar_imagen():
        return

    imagen_np = np.array(imagen_original)

    hsv = cv2.cvtColor(
        imagen_np,
        cv2.COLOR_RGB2HSV
    )

    h, s, v = cv2.split(hsv)

    plt.figure(figsize=(12, 4))

    plt.subplot(1, 3, 1)
    plt.imshow(h, cmap="gray")
    plt.title("H - Matiz")
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.imshow(s, cmap="gray")
    plt.title("S - Saturación")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.imshow(v, cmap="gray")
    plt.title("V - Brillo")
    plt.axis("off")

    plt.tight_layout()
    plt.show()

ventana = Tk()

ventana.title("Práctica 1 - Análisis Digital de Imágenes")

ventana.geometry("900x900")

ventana.resizable(True, True)

titulo = Label(
    ventana,
    text="EXPLORANDO LA IMAGEN DIGITAL CON PYTHON",
    font=("Arial", 18, "bold")
)

titulo.pack(pady=15)


subtitulo = Label(
    ventana,
    text="Práctica 1 - Análisis de Imágenes",
    font=("Arial", 12)
)

subtitulo.pack()

boton_cargar = Button(
    ventana,
    text="Cargar imagen",
    font=("Arial", 12),
    command=cargar_imagen
)

boton_cargar.pack(pady=15)

etiqueta_archivo = Label(
    ventana,
    text="No se ha cargado ninguna imagen",
    font=("Arial", 9)
)

etiqueta_archivo.pack()


etiqueta_info = Label(
    ventana,
    text=""
)

etiqueta_info.pack(pady=5)

panel_imagen = Label(
    ventana,
    text="Selecciona una imagen para comenzar",
    relief="sunken"
)

panel_imagen.pack(pady=10)


etiqueta_resultado = Label(
    ventana,
    text="Resultado actual: Ninguno",
    font=("Arial", 10, "bold")
)

etiqueta_resultado.pack(pady=5)

frame_botones = Frame(ventana)

frame_botones.pack(pady=10)


Button(
    frame_botones,
    text="Original",
    command=mostrar_original,
    width=15
).grid(row=0, column=0, padx=5, pady=5)


Button(
    frame_botones,
    text="Componentes RGB",
    command=separar_rgb,
    width=15
).grid(row=0, column=1, padx=5, pady=5)


Button(
    frame_botones,
    text="Escala de grises",
    command=convertir_grises,
    width=15
).grid(row=0, column=2, padx=5, pady=5)


Button(
    frame_botones,
    text="Histograma",
    command=mostrar_histograma,
    width=15
).grid(row=1, column=0, padx=5, pady=5)


Button(
    frame_botones,
    text="Modelo HSV",
    command=mostrar_hsv,
    width=15
).grid(row=1, column=1, padx=5, pady=5)


Button(
    frame_botones,
    text="Binarización Otsu",
    command=binarizar_otsu,
    width=15
).grid(row=1, column=2, padx=5, pady=5)

Label(
    ventana,
    text="Umbral de binarización",
    font=("Arial", 10, "bold")
).pack(pady=(10, 0))


slider_umbral = Scale(
    ventana,
    from_=0,
    to=255,
    orient=HORIZONTAL,
    length=400
)

slider_umbral.set(128)

slider_umbral.pack()


Button(
    ventana,
    text="Aplicar binarización",
    command=binarizar,
    width=25
).pack(pady=10)

ventana.mainloop()