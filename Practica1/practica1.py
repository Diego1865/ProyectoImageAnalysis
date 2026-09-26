import tkinter as tk
from tkinter import filedialog, ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


class AppPseudocolor:

    def __init__(self, root):
        self.root = root
        self.root.title("Práctica 1: Pseudocolor en Imágenes - ESCOM")
        self.root.geometry("950x650")
        self.root.config(bg="#f0f0f0")

        self.image_path = None
        self.img_gray = None
        self.tk_img_orig = None
        self.tk_img_proc = None

        # Título principal
        title_label = tk.Label(
            root,
            text="Conversor de Imagen a Pseudocolor",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
            fg="#333"
        )
        title_label.pack(pady=15)

        # Panel de controles
        control_frame = tk.Frame(root, bg="#f0f0f0")
        control_frame.pack(pady=10)

        self.btn_cargar = tk.Button(
            control_frame,
            text="Cargar Imagen",
            command=self.cargar_imagen,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=12,
            pady=6
        )
        self.btn_cargar.pack(side=tk.LEFT, padx=10)

        tk.Label(
            control_frame,
            text="Selecciona el Mapa de Color:",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            fg="#555"
        ).pack(side=tk.LEFT, padx=5)

        self.colormaps = [
            "JET",
            "HOT",
            "OCEAN",
            "BONE",
            "PINK",
            "Piedra Marina",
            "Tierra Personalizado",
            "INFERNO"
        ]

        self.combo_map = ttk.Combobox(
            control_frame,
            values=self.colormaps,
            state="readonly",
            width=24,
            font=("Arial", 10)
        )

        self.combo_map.current(0)
        self.combo_map.pack(side=tk.LEFT, padx=5)
        self.combo_map.bind(
            "<<ComboboxSelected>>",
            self.procesar_imagen
        )

        # Contenedor principal
        display_frame = tk.Frame(root, bg="#f0f0f0")
        display_frame.pack(
            pady=15,
            fill=tk.BOTH,
            expand=True,
            padx=20
        )

        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.rowconfigure(0, weight=1)

        # Imagen original
        frame_orig = tk.LabelFrame(
            display_frame,
            text=" 1. Imagen en Escala de Grises ",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            fg="#333",
            padx=10,
            pady=10
        )

        frame_orig.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10
        )

        self.panel_original = tk.Label(
            frame_orig,
            text="Sin imagen cargada",
            bg="#e0e0e0",
            fg="#666",
            font=("Arial", 10)
        )

        self.panel_original.pack(
            fill=tk.BOTH,
            expand=True
        )

        # Imagen procesada
        frame_proc = tk.LabelFrame(
            display_frame,
            text=" 2. Imagen con Pseudocolor ",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            fg="#333",
            padx=10,
            pady=10
        )

        frame_proc.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=10
        )

        self.panel_procesada = tk.Label(
            frame_proc,
            text="Resultado",
            bg="#e0e0e0",
            fg="#666",
            font=("Arial", 10)
        )

        self.panel_procesada.pack(
            fill=tk.BOTH,
            expand=True
        )


    def cargar_imagen(self):

        file_path = filedialog.askopenfilename(
            filetypes=[
                (
                    "Archivos de Imagen",
                    "*.jpg *.jpeg *.png *.bmp"
                )
            ]
        )

        if file_path:

            self.image_path = file_path

            pil_img = Image.open(file_path).convert("L")

            self.img_gray = np.array(
                pil_img,
                dtype=np.uint8
            )

            self.actualizar_vista()
            self.procesar_imagen(None)


    def actualizar_vista(self):

        if self.img_gray is not None:

            img_pil = Image.fromarray(
                self.img_gray
            )

            img_pil.thumbnail((400, 400))

            self.tk_img_orig = ImageTk.PhotoImage(
                img_pil
            )

            self.panel_original.config(
                image=self.tk_img_orig,
                text=""
            )


    def procesar_imagen(self, event=None):

        if self.img_gray is None:
            return

        seleccion = self.combo_map.get()

        # JET
        if seleccion == "JET":

            colored = cv2.applyColorMap(
                self.img_gray,
                cv2.COLORMAP_JET
            )

            colored = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB
            )

        # HOT
        elif seleccion == "HOT":

            colored = cv2.applyColorMap(
                self.img_gray,
                cv2.COLORMAP_HOT
            )

            colored = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB
            )

        # OCEAN
        elif seleccion == "OCEAN":

            colored = cv2.applyColorMap(
                self.img_gray,
                cv2.COLORMAP_OCEAN
            )

            colored = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB
            )

        # BONE
        elif seleccion == "BONE":

            colored = cv2.applyColorMap(
                self.img_gray,
                cv2.COLORMAP_BONE
            )

            colored = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB
            )

        # PINK
        elif seleccion == "PINK":

            colored = cv2.applyColorMap(
                self.img_gray,
                cv2.COLORMAP_PINK
            )

            colored = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB
            )

        # INFERNO
        elif seleccion == "INFERNO":

            colored = cv2.applyColorMap(
                self.img_gray,
                cv2.COLORMAP_INFERNO
            )

            colored = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB
            )

        # PERSONALIZADO: PIEDRA MARINA
        elif seleccion == "Piedra Marina":

            colores_piedra = [
                (0.12, 0.12, 0.18),
                (0.20, 0.28, 0.35),
                (0.32, 0.45, 0.50),
                (0.55, 0.65, 0.62),
                (0.82, 0.85, 0.80)
            ]

            mapa_piedra = LinearSegmentedColormap.from_list(
                "PiedraMap",
                colores_piedra,
                N=256
            )

            norm_img = self.img_gray.astype(
                np.float32
            ) / 255.0

            rgba = mapa_piedra(norm_img)

            colored = (
                rgba[:, :, :3] * 255
            ).astype(np.uint8)

        # PERSONALIZADO: TIERRA
        elif seleccion == "Tierra Personalizado":

            colores_tierra = [
                (0.60, 0.40, 0.20),
                (0.80, 0.60, 0.50),
                (0.90, 0.70, 0.60),
                (0.70, 0.50, 0.30),
                (0.50, 0.30, 0.20)
            ]

            mapa_tierra = LinearSegmentedColormap.from_list(
                "TierraMap",
                colores_tierra,
                N=256
            )

            norm_img = self.img_gray.astype(
                np.float32
            ) / 255.0

            rgba = mapa_tierra(norm_img)

            colored = (
                rgba[:, :, :3] * 255
            ).astype(np.uint8)

        else:
            return

        # Mostrar imagen procesada
        img_pil = Image.fromarray(colored)

        img_pil.thumbnail((400, 400))

        self.tk_img_proc = ImageTk.PhotoImage(
            img_pil
        )

        self.panel_procesada.config(
            image=self.tk_img_proc,
            text=""
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = AppPseudocolor(root)
    root.mainloop()