"""
IMAGE PROCESSING LABORATORY - ESCOM
Aplicación integradora para prácticas de Análisis de Imágenes.

Integra:
- Práctica 1: pseudocolor con mapas OpenCV y personalizados.
- Práctica 2: RGB, grises, histograma y HSV.
- Segmentación, ruido, operaciones lógicas/relacionales y miniproyecto ECC.

Diseñada como base modular para agregar futuras prácticas.
"""

import colorsys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageTk

from image_lab.experiment_ui import ExperimentMixin


APP_TITLE = "IMAGE PROCESSING LABORATORY - ESCOM"
CLASSIC_BG = "#d4d0c8"
WORKSPACE_BG = "#808080"
PANEL_BG = "#efefef"
TITLE_BG = "#0a246a"
TITLE_FG = "white"


class ImageProcessingLab(ExperimentMixin):
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x800")
        self.root.minsize(1050, 680)
        self.root.configure(bg=CLASSIC_BG)

        # --------------------------
        # Estado de la aplicación
        # --------------------------
        self.file_path = None
        self.original_rgb = None
        self.current_image = None
        self.current_operation = "Sin imagen"

        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 20

        self.original_photo = None
        self.result_photo = None
        self.gradient_photo = None
        self._resize_job = None

        # Información usada para traducir coordenadas del canvas a píxeles
        self.canvas_maps = {}

        # Mapas de pseudocolor de la práctica 1
        self.colormaps = [
            "JET",
            "HOT",
            "OCEAN",
            "BONE",
            "PINK",
            "INFERNO",
            "Piedra Marina",
            "Tierra Personalizado",
        ]

        self._build_menu()
        self._build_top_toolbars()
        self._build_main_layout()
        self._build_status_bar()

        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_result())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Escape>", lambda e: self.clear_pixel_info())

        self.update_gradient_preview()
        self._update_ui_state()

    # ============================================================
    # CONSTRUCCIÓN DE INTERFAZ
    # ============================================================

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label="Abrir imagen...\tCtrl+O", command=self.open_image)
        menu_file.add_command(label="Guardar resultado como...\tCtrl+S", command=self.save_result)
        menu_file.add_separator()
        menu_file.add_command(label="Cerrar imagen", command=self.close_image)
        menu_file.add_separator()
        menu_file.add_command(label="Salir", command=self.root.destroy)
        menubar.add_cascade(label="Archivo", menu=menu_file)

        menu_edit = tk.Menu(menubar, tearoff=0)
        menu_edit.add_command(label="Deshacer\tCtrl+Z", command=self.undo)
        menu_edit.add_command(label="Rehacer\tCtrl+Y", command=self.redo)
        menu_edit.add_separator()
        menu_edit.add_command(label="Restaurar original", command=self.restore_original)
        menubar.add_cascade(label="Editar", menu=menu_edit)

        menu_image = tk.Menu(menubar, tearoff=0)
        menu_image.add_command(label="Imagen original", command=self.restore_original)
        menu_image.add_command(label="Escala de grises", command=self.convert_to_gray)
        menu_image.add_separator()
        menu_image.add_command(label="Componentes RGB", command=self.show_rgb_components)
        menu_image.add_command(label="Componentes HSV", command=self.show_hsv_components)
        menu_image.add_command(label="Histograma de intensidad", command=self.show_histogram)
        menubar.add_cascade(label="Práctica 2", menu=menu_image)

        menu_colors = tk.Menu(menubar, tearoff=0)
        for cmap_name in self.colormaps:
            menu_colors.add_command(
                label=cmap_name,
                command=lambda name=cmap_name: self.apply_pseudocolor(name),
            )
        menubar.add_cascade(label="Práctica 1 - Pseudocolor", menu=menu_colors)

        self.build_experiment_menu(menubar)

        menu_filters = tk.Menu(menubar, tearoff=0)
        menu_filters.add_command(label="Mediana", command=lambda: self.filter_current('median'))
        menu_filters.add_command(label="Gaussiano", command=lambda: self.filter_current('gaussian'))
        menubar.add_cascade(label="Filtros", menu=menu_filters)

        menu_edges = tk.Menu(menubar, tearoff=0)
        menu_edges.add_command(
            label="Módulo preparado para futuras prácticas...",
            command=lambda: self.future_feature("Bordes"),
        )
        menubar.add_cascade(label="Bordes", menu=menu_edges)

        menu_window = tk.Menu(menubar, tearoff=0)
        menu_window.add_command(label="Ajustar imágenes al área", command=self.refresh_views)
        menu_window.add_command(label="Limpiar información de píxel", command=self.clear_pixel_info)
        menubar.add_cascade(label="Ventana", menu=menu_window)

        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=menu_help)

        self.root.config(menu=menubar)

    def _build_top_toolbars(self):
        # Barra superior estilo software clásico
        toolbar = tk.Frame(self.root, bg=CLASSIC_BG, bd=1, relief="raised")
        toolbar.pack(fill="x")

        file_group = self._toolbar_group(toolbar, "Archivo")
        self._tool_button(file_group, "Abrir", self.open_image, 8)
        self._tool_button(file_group, "Guardar", self.save_result, 8)
        self._tool_button(file_group, "Reset", self.restore_original, 8)

        tools_group = self._toolbar_group(toolbar, "Práctica 2")
        self._tool_button(tools_group, "Grises", self.convert_to_gray, 8)
        self._tool_button(tools_group, "RGB", self.show_rgb_components, 6)
        self._tool_button(tools_group, "HSV", self.show_hsv_components, 6)
        self._tool_button(tools_group, "Hist.", self.show_histogram, 6)

        colors_group = self._toolbar_group(toolbar, "Práctica 1")
        self.toolbar_cmap = ttk.Combobox(
            colors_group,
            values=self.colormaps,
            state="readonly",
            width=18,
        )
        self.toolbar_cmap.set("JET")
        self.toolbar_cmap.pack(side="left", padx=3, pady=4)
        self.toolbar_cmap.bind("<<ComboboxSelected>>", self._sync_colormap_from_toolbar)
        self._tool_button(colors_group, "Aplicar", self.apply_selected_pseudocolor, 7)

        threshold_group = self._toolbar_group(toolbar, "Binarización")
        self._tool_button(threshold_group, "Umbral", self.apply_threshold, 8)
        self._tool_button(threshold_group, "Otsu", self.apply_otsu, 6)

    def _toolbar_group(self, parent, title):
        frame = tk.LabelFrame(
            parent,
            text=title,
            bg=CLASSIC_BG,
            bd=1,
            relief="groove",
            font=("Segoe UI", 8),
            padx=2,
            pady=0,
        )
        frame.pack(side="left", padx=2, pady=2)
        return frame

    @staticmethod
    def _tool_button(parent, text, command, width=7):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            relief="raised",
            bd=1,
            font=("Segoe UI", 8),
            padx=2,
            pady=2,
        )
        btn.pack(side="left", padx=1, pady=2)
        return btn

    def _build_main_layout(self):
        main = tk.Frame(self.root, bg=CLASSIC_BG)
        main.pack(fill="both", expand=True)

        # --------------------------
        # Barra lateral izquierda
        # --------------------------
        left = tk.Frame(main, bg=CLASSIC_BG, width=48, bd=1, relief="raised")
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Tools", bg=CLASSIC_BG, font=("Segoe UI", 8, "bold")).pack(pady=(6, 3))

        self._side_button(left, "O", "Abrir imagen", self.open_image)
        self._side_button(left, "↺", "Restaurar original", self.restore_original)
        self._side_button(left, "G", "Escala de grises", self.convert_to_gray)
        self._side_button(left, "RGB", "Componentes RGB", self.show_rgb_components, small=True)
        self._side_button(left, "HSV", "Componentes HSV", self.show_hsv_components, small=True)
        self._side_button(left, "H", "Histograma", self.show_histogram)
        self._side_button(left, "B", "Binarización", self.apply_threshold)
        self._side_button(left, "P", "Pseudocolor", self.apply_selected_pseudocolor)

        # --------------------------
        # Área central de trabajo
        # --------------------------
        center = tk.Frame(main, bg=WORKSPACE_BG, bd=2, relief="sunken")
        center.pack(side="left", fill="both", expand=True)

        self.workspace = center

        documents = tk.Frame(center, bg=WORKSPACE_BG)
        documents.pack(fill="both", expand=True, padx=12, pady=12)
        documents.grid_columnconfigure(0, weight=1, uniform="docs")
        documents.grid_columnconfigure(1, weight=1, uniform="docs")
        documents.grid_rowconfigure(0, weight=1)

        self.original_doc, self.original_canvas, self.original_title = self._document_panel(
            documents, "Imagen original", 0
        )
        self.result_doc, self.result_canvas, self.result_title = self._document_panel(
            documents, "Resultado", 1
        )

        self.original_canvas.bind("<Motion>", lambda e: self.on_canvas_motion(e, self.original_canvas))
        self.result_canvas.bind("<Motion>", lambda e: self.on_canvas_motion(e, self.result_canvas))
        self.original_canvas.bind("<Leave>", lambda e: self.clear_pixel_info())
        self.result_canvas.bind("<Leave>", lambda e: self.clear_pixel_info())
        self.original_canvas.bind("<Configure>", self.schedule_refresh)
        self.result_canvas.bind("<Configure>", self.schedule_refresh)

        # --------------------------
        # Panel derecho de color / parámetros
        # --------------------------
        right = tk.Frame(main, bg=CLASSIC_BG, width=220, bd=1, relief="raised")
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(
            right,
            text="Colors",
            bg=CLASSIC_BG,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=8, pady=(8, 3))

        self.gradient_canvas = tk.Canvas(
            right,
            width=190,
            height=26,
            bd=1,
            relief="sunken",
            highlightthickness=0,
        )
        self.gradient_canvas.pack(padx=8, pady=3)

        self.color_swatch = tk.Label(right, bg="black", height=2, bd=2, relief="sunken")
        self.color_swatch.pack(fill="x", padx=8, pady=(3, 8))

        values = tk.LabelFrame(right, text="Píxel", bg=CLASSIC_BG, padx=6, pady=4)
        values.pack(fill="x", padx=8, pady=4)

        self.pixel_labels = {}
        for key in ["X", "Y", "R", "G", "B", "C", "M", "Yc", "H", "S", "V", "I"]:
            row = tk.Frame(values, bg=CLASSIC_BG)
            row.pack(fill="x")
            shown = "Y" if key == "Yc" else key
            tk.Label(row, text=f"{shown}=", width=3, anchor="e", bg=CLASSIC_BG).pack(side="left")
            lbl = tk.Label(row, text="-", width=14, anchor="w", bg="white", relief="sunken", bd=1)
            lbl.pack(side="left", fill="x", expand=True, pady=1)
            self.pixel_labels[key] = lbl

        image_info = tk.LabelFrame(right, text="Imagen", bg=CLASSIC_BG, padx=6, pady=4)
        image_info.pack(fill="x", padx=8, pady=4)
        self.lbl_filename = tk.Label(image_info, text="Sin imagen", bg=CLASSIC_BG, anchor="w", justify="left", wraplength=185)
        self.lbl_filename.pack(fill="x")
        self.lbl_dimensions = tk.Label(image_info, text="-", bg=CLASSIC_BG, anchor="w")
        self.lbl_dimensions.pack(fill="x")
        self.lbl_mode = tk.Label(image_info, text="-", bg=CLASSIC_BG, anchor="w")
        self.lbl_mode.pack(fill="x")

        threshold_box = tk.LabelFrame(right, text="Umbral", bg=CLASSIC_BG, padx=6, pady=4)
        threshold_box.pack(fill="x", padx=8, pady=4)
        self.threshold_var = tk.IntVar(value=128)
        self.threshold_scale = tk.Scale(
            threshold_box,
            from_=0,
            to=255,
            orient="horizontal",
            variable=self.threshold_var,
            length=175,
            bg=CLASSIC_BG,
            highlightthickness=0,
            command=self._threshold_changed,
        )
        self.threshold_scale.pack(fill="x")
        tk.Button(threshold_box, text="Aplicar", command=self.apply_threshold, width=10).pack(side="left", padx=2, pady=3)
        tk.Button(threshold_box, text="Otsu", command=self.apply_otsu, width=8).pack(side="left", padx=2, pady=3)

        pseudo_box = tk.LabelFrame(right, text="Pseudocolor", bg=CLASSIC_BG, padx=6, pady=4)
        pseudo_box.pack(fill="x", padx=8, pady=4)
        self.cmap_var = tk.StringVar(value="JET")
        self.cmap_combo = ttk.Combobox(
            pseudo_box,
            textvariable=self.cmap_var,
            values=self.colormaps,
            state="readonly",
            width=20,
        )
        self.cmap_combo.pack(fill="x", pady=2)
        self.cmap_combo.bind("<<ComboboxSelected>>", self._sync_colormap_from_side)
        tk.Button(
            pseudo_box,
            text="Aplicar pseudocolor",
            command=self.apply_selected_pseudocolor,
        ).pack(fill="x", pady=3)

    def _side_button(self, parent, text, tooltip, command, small=False):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            width=4,
            height=1,
            font=("Segoe UI", 7 if small else 10, "bold"),
            relief="flat",
            bg=CLASSIC_BG,
            activebackground="#e8e8e8",
        )
        btn.pack(pady=2)
        self._create_tooltip(btn, tooltip)

    @staticmethod
    def _create_tooltip(widget, text):
        # Tooltip mínimo, sin dependencias externas
        tip = {"window": None}

        def show(_event):
            if tip["window"] is not None:
                return
            x = widget.winfo_rootx() + widget.winfo_width() + 4
            y = widget.winfo_rooty()
            win = tk.Toplevel(widget)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{x}+{y}")
            tk.Label(
                win,
                text=text,
                bg="#ffffe0",
                relief="solid",
                bd=1,
                font=("Segoe UI", 8),
                padx=4,
                pady=2,
            ).pack()
            tip["window"] = win

        def hide(_event):
            if tip["window"] is not None:
                tip["window"].destroy()
                tip["window"] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _document_panel(self, parent, title, column):
        outer = tk.Frame(parent, bg=CLASSIC_BG, bd=2, relief="raised")
        outer.grid(row=0, column=column, sticky="nsew", padx=6, pady=6)

        titlebar = tk.Label(
            outer,
            text=title,
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=6,
            pady=3,
        )
        titlebar.pack(fill="x")

        canvas = tk.Canvas(
            outer,
            bg="#1f1f1f",
            bd=0,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True, padx=2, pady=2)
        canvas.create_text(
            200,
            160,
            text="Sin imagen cargada",
            fill="#c0c0c0",
            font=("Segoe UI", 11),
            tags="placeholder",
        )

        return outer, canvas, titlebar

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=CLASSIC_BG, bd=1, relief="sunken")
        bar.pack(fill="x", side="bottom")

        self.status_left = tk.Label(
            bar,
            text="Listo",
            bg=CLASSIC_BG,
            anchor="w",
            bd=1,
            relief="sunken",
            padx=5,
        )
        self.status_left.pack(side="left", fill="x", expand=True)

        self.status_operation = tk.Label(
            bar,
            text="Sin operación",
            bg=CLASSIC_BG,
            width=28,
            anchor="w",
            bd=1,
            relief="sunken",
            padx=5,
        )
        self.status_operation.pack(side="left")

        self.status_size = tk.Label(
            bar,
            text="0 x 0",
            bg=CLASSIC_BG,
            width=16,
            anchor="center",
            bd=1,
            relief="sunken",
        )
        self.status_size.pack(side="left")

    # ============================================================
    # ARCHIVO
    # ============================================================

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Abrir imagen",
            filetypes=[
                ("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Bitmap", "*.bmp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path:
            return

        try:
            pil = Image.open(path).convert("RGB")
            arr = np.array(pil, dtype=np.uint8)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo abrir la imagen.\n\n{exc}")
            return

        self.file_path = path
        self.original_rgb = arr
        self.current_image = arr.copy()
        self.current_operation = "Imagen original"
        self.undo_stack.clear()
        self.redo_stack.clear()

        self.lbl_filename.config(text=os.path.basename(path))
        h, w = arr.shape[:2]
        self.lbl_dimensions.config(text=f"{w} x {h} píxeles")
        self.lbl_mode.config(text="RGB / 8 bits por canal")

        self.original_title.config(text=f"Imagen original - {os.path.basename(path)}")
        self.result_title.config(text="Resultado - Imagen original")
        self.status_left.config(text=path)

        self.refresh_views()
        self._update_ui_state()

    def save_result(self):
        if not self.require_image():
            return

        path = filedialog.asksaveasfilename(
            title="Guardar resultado",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Bitmap", "*.bmp"),
                ("TIFF", "*.tif *.tiff"),
            ],
        )
        if not path:
            return

        try:
            arr = self.current_image
            if arr.ndim == 2:
                Image.fromarray(arr).save(path)
            else:
                Image.fromarray(self.ensure_rgb(arr)).save(path)
            self.status_left.config(text=f"Guardado: {path}")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo guardar la imagen.\n\n{exc}")

    def close_image(self):
        self.file_path = None
        self.original_rgb = None
        self.current_image = None
        self.current_operation = "Sin imagen"
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.canvas_maps.clear()

        for canvas in (self.original_canvas, self.result_canvas):
            canvas.delete("all")
            canvas.create_text(
                max(canvas.winfo_width() // 2, 200),
                max(canvas.winfo_height() // 2, 160),
                text="Sin imagen cargada",
                fill="#c0c0c0",
                font=("Segoe UI", 11),
            )

        self.original_title.config(text="Imagen original")
        self.result_title.config(text="Resultado")
        self.lbl_filename.config(text="Sin imagen")
        self.lbl_dimensions.config(text="-")
        self.lbl_mode.config(text="-")
        self.status_left.config(text="Listo")
        self.status_operation.config(text="Sin operación")
        self.status_size.config(text="0 x 0")
        self.clear_pixel_info()
        self._update_ui_state()

    # ============================================================
    # HISTORIAL / UTILIDADES
    # ============================================================

    def require_image(self):
        if self.current_image is None:
            messagebox.showwarning("Aviso", "Primero debes abrir una imagen.")
            return False
        return True

    def commit(self, new_image, description):
        if self.current_image is not None:
            self.undo_stack.append(self.current_image.copy())
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
        self.redo_stack.clear()

        self.current_image = np.asarray(new_image, dtype=np.uint8).copy()
        self.current_operation = description
        self.result_title.config(text=f"Resultado - {description}")
        self.status_operation.config(text=description)
        self.refresh_views()
        self._update_ui_state()

    def undo(self):
        if not self.undo_stack or self.current_image is None:
            self.status_left.config(text="No hay cambios para deshacer")
            return
        self.redo_stack.append(self.current_image.copy())
        self.current_image = self.undo_stack.pop()
        self.current_operation = "Deshacer"
        self.result_title.config(text="Resultado - Deshacer")
        self.status_operation.config(text="Deshacer")
        self.refresh_views()
        self._update_ui_state()

    def redo(self):
        if not self.redo_stack or self.current_image is None:
            self.status_left.config(text="No hay cambios para rehacer")
            return
        self.undo_stack.append(self.current_image.copy())
        self.current_image = self.redo_stack.pop()
        self.current_operation = "Rehacer"
        self.result_title.config(text="Resultado - Rehacer")
        self.status_operation.config(text="Rehacer")
        self.refresh_views()
        self._update_ui_state()

    def restore_original(self):
        if not self.require_image():
            return
        self.commit(self.original_rgb, "Imagen original")

    @staticmethod
    def ensure_gray(image):
        arr = np.asarray(image, dtype=np.uint8)
        if arr.ndim == 2:
            return arr
        if arr.ndim == 3 and arr.shape[2] == 3:
            return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        raise ValueError("Formato de imagen no compatible")

    @staticmethod
    def ensure_rgb(image):
        arr = np.asarray(image, dtype=np.uint8)
        if arr.ndim == 2:
            return cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
        if arr.ndim == 3 and arr.shape[2] == 3:
            return arr
        raise ValueError("Formato de imagen no compatible")

    # ============================================================
    # PRÁCTICA 1
    # ============================================================

    def convert_to_gray(self):
        if not self.require_image():
            return
        gray = self.ensure_gray(self.current_image)
        self.commit(gray, "Escala de grises")

    def apply_threshold(self):
        if not self.require_image():
            return
        gray = self.ensure_gray(self.current_image)
        threshold = int(self.threshold_var.get())
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        self.commit(binary, f"Binarización (umbral {threshold})")

    def apply_otsu(self):
        if not self.require_image():
            return
        gray = self.ensure_gray(self.current_image)
        threshold, binary = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        self.threshold_var.set(int(round(threshold)))
        self.commit(binary, f"Otsu (umbral {threshold:.0f})")
        self.status_left.config(text=f"Umbral automático calculado por Otsu: {threshold:.2f}")

    def show_histogram(self):
        if not self.require_image():
            return
        gray = self.ensure_gray(self.current_image)
        plt.figure("Histograma de intensidad", figsize=(8, 5))
        plt.clf()
        plt.hist(gray.ravel(), bins=256, range=(0, 256))
        plt.title("Histograma de intensidad")
        plt.xlabel("Nivel de intensidad")
        plt.ylabel("Cantidad de píxeles")
        plt.grid(alpha=0.25)
        plt.tight_layout()
        plt.show()

    def show_rgb_components(self):
        if not self.require_image():
            return
        rgb = self.ensure_rgb(self.current_image)
        r, g, b = cv2.split(rgb)

        red = np.zeros_like(rgb)
        green = np.zeros_like(rgb)
        blue = np.zeros_like(rgb)
        red[:, :, 0] = r
        green[:, :, 1] = g
        blue[:, :, 2] = b

        self.open_component_window(
            "Componentes RGB",
            [("R - Rojo", red), ("G - Verde", green), ("B - Azul", blue)],
        )

    def show_hsv_components(self):
        if not self.require_image():
            return
        rgb = self.ensure_rgb(self.current_image)
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)

        # H en OpenCV va de 0 a 179; se expande solo para visualización.
        h_display = cv2.normalize(h, None, 0, 255, cv2.NORM_MINMAX)

        self.open_component_window(
            "Componentes HSV",
            [("H - Matiz", h_display), ("S - Saturación", s), ("V - Brillo", v)],
        )

    # ============================================================
    # PRÁCTICA 2 - PSEUDOCOLOR
    # ============================================================

    def apply_selected_pseudocolor(self):
        name = self.cmap_var.get() or "JET"
        self.apply_pseudocolor(name)

    def apply_pseudocolor(self, name=None):
        if not self.require_image():
            return
        if name is None:
            name = self.cmap_var.get() or "JET"

        self.cmap_var.set(name)
        self.toolbar_cmap.set(name)
        self.update_gradient_preview()

        gray = self.ensure_gray(self.current_image)
        colored = self.colorize_gray(gray, name)
        self.commit(colored, f"Pseudocolor - {name}")

    def colorize_gray(self, gray, name):
        builtin = {
            "JET": cv2.COLORMAP_JET,
            "HOT": cv2.COLORMAP_HOT,
            "OCEAN": cv2.COLORMAP_OCEAN,
            "BONE": cv2.COLORMAP_BONE,
            "PINK": cv2.COLORMAP_PINK,
            "INFERNO": cv2.COLORMAP_INFERNO,
        }

        if name in builtin:
            bgr = cv2.applyColorMap(gray, builtin[name])
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        if name == "Piedra Marina":
            colors = [
                (0.12, 0.12, 0.18),
                (0.20, 0.28, 0.35),
                (0.32, 0.45, 0.50),
                (0.55, 0.65, 0.62),
                (0.82, 0.85, 0.80),
            ]
            cmap = LinearSegmentedColormap.from_list("PiedraMap", colors, N=256)
        elif name == "Tierra Personalizado":
            colors = [
                (0.60, 0.40, 0.20),
                (0.80, 0.60, 0.50),
                (0.90, 0.70, 0.60),
                (0.70, 0.50, 0.30),
                (0.50, 0.30, 0.20),
            ]
            cmap = LinearSegmentedColormap.from_list("TierraMap", colors, N=256)
        else:
            raise ValueError(f"Mapa de color no reconocido: {name}")

        norm = gray.astype(np.float32) / 255.0
        rgba = cmap(norm)
        return (rgba[:, :, :3] * 255).astype(np.uint8)

    # ============================================================
    # VENTANAS DE ANÁLISIS
    # ============================================================

    def open_component_window(self, title, items):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("1050x430")
        win.configure(bg=CLASSIC_BG)

        container = tk.Frame(win, bg=CLASSIC_BG)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        photos = []
        for index, (name, arr) in enumerate(items):
            frame = tk.LabelFrame(
                container,
                text=name,
                bg=CLASSIC_BG,
                font=("Segoe UI", 9, "bold"),
            )
            frame.grid(row=0, column=index, sticky="nsew", padx=5, pady=5)
            container.grid_columnconfigure(index, weight=1)
            container.grid_rowconfigure(0, weight=1)

            canvas = tk.Canvas(frame, bg="#1f1f1f", highlightthickness=0)
            canvas.pack(fill="both", expand=True)

            def draw(c=canvas, image=arr):
                w = max(c.winfo_width(), 300)
                h = max(c.winfo_height(), 300)
                pil = Image.fromarray(self.ensure_rgb(image) if image.ndim == 3 else image)
                pil.thumbnail((max(w - 12, 50), max(h - 12, 50)), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil)
                photos.append(photo)
                c.delete("all")
                c.create_image(w // 2, h // 2, image=photo, anchor="center")

            win.after(100, draw)

        # Mantener referencias vivas mientras la ventana exista.
        win._photos = photos

    # ============================================================
    # RENDERIZADO EN EL ÁREA CENTRAL
    # ============================================================

    def schedule_refresh(self, _event=None):
        if self._resize_job is not None:
            try:
                self.root.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.root.after(80, self.refresh_views)

    def refresh_views(self):
        self._resize_job = None
        if self.original_rgb is None or self.current_image is None:
            return

        self.original_photo = self.render_image_on_canvas(
            self.original_canvas,
            self.original_rgb,
            "original",
        )
        self.result_photo = self.render_image_on_canvas(
            self.result_canvas,
            self.current_image,
            "result",
        )

        h, w = self.current_image.shape[:2]
        mode = "Grises" if self.current_image.ndim == 2 else "RGB"
        self.status_size.config(text=f"{w} x {h}")
        self.lbl_mode.config(text=f"{mode} / 8 bits")

    def render_image_on_canvas(self, canvas, image, key):
        canvas.update_idletasks()
        cw = max(canvas.winfo_width(), 100)
        ch = max(canvas.winfo_height(), 100)

        arr = np.asarray(image, dtype=np.uint8)
        pil = Image.fromarray(arr)

        iw, ih = pil.size
        max_w = max(cw - 16, 30)
        max_h = max(ch - 16, 30)
        scale = min(max_w / iw, max_h / ih, 1.0)
        display_w = max(int(iw * scale), 1)
        display_h = max(int(ih * scale), 1)

        pil = pil.resize((display_w, display_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil)

        x0 = (cw - display_w) // 2
        y0 = (ch - display_h) // 2

        canvas.delete("all")
        canvas.create_image(x0, y0, image=photo, anchor="nw")

        self.canvas_maps[canvas] = {
            "array": arr,
            "x0": x0,
            "y0": y0,
            "display_w": display_w,
            "display_h": display_h,
            "image_w": iw,
            "image_h": ih,
            "key": key,
        }

        return photo

    # ============================================================
    # INFORMACIÓN DE PÍXEL / PANEL DERECHO
    # ============================================================

    def on_canvas_motion(self, event, canvas):
        meta = self.canvas_maps.get(canvas)
        if not meta:
            return

        x0 = meta["x0"]
        y0 = meta["y0"]
        dw = meta["display_w"]
        dh = meta["display_h"]

        if not (x0 <= event.x < x0 + dw and y0 <= event.y < y0 + dh):
            self.clear_pixel_info()
            return

        ix = int((event.x - x0) * meta["image_w"] / dw)
        iy = int((event.y - y0) * meta["image_h"] / dh)
        ix = min(max(ix, 0), meta["image_w"] - 1)
        iy = min(max(iy, 0), meta["image_h"] - 1)

        arr = meta["array"]
        if arr.ndim == 2:
            value = int(arr[iy, ix])
            r = g = b = value
        else:
            r, g, b = [int(v) for v in arr[iy, ix, :3]]

        c, m, y = 255 - r, 255 - g, 255 - b
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        h_deg = h * 360.0
        s_pct = s * 100.0
        v_pct = v * 100.0
        intensity = int(round(0.299 * r + 0.587 * g + 0.114 * b))

        values = {
            "X": str(ix),
            "Y": str(iy),
            "R": str(r),
            "G": str(g),
            "B": str(b),
            "C": str(c),
            "M": str(m),
            "Yc": str(y),
            "H": f"{h_deg:.1f}°",
            "S": f"{s_pct:.1f}%",
            "V": f"{v_pct:.1f}%",
            "I": str(intensity),
        }

        for key, value in values.items():
            self.pixel_labels[key].config(text=value)

        self.color_swatch.config(bg=f"#{r:02x}{g:02x}{b:02x}")
        self.status_left.config(text=f"Píxel ({ix}, {iy})  RGB=({r}, {g}, {b})")

    def clear_pixel_info(self):
        if not hasattr(self, "pixel_labels"):
            return
        for lbl in self.pixel_labels.values():
            lbl.config(text="-")
        self.color_swatch.config(bg="black")
        if self.file_path:
            self.status_left.config(text=self.file_path)
        else:
            self.status_left.config(text="Listo")

    def update_gradient_preview(self):
        if not hasattr(self, "gradient_canvas"):
            return

        name = self.cmap_var.get() if hasattr(self, "cmap_var") else "JET"
        gray = np.tile(np.arange(256, dtype=np.uint8), (20, 1))
        try:
            rgb = self.colorize_gray(gray, name)
        except Exception:
            rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        pil = Image.fromarray(rgb).resize((190, 26), Image.Resampling.BILINEAR)
        self.gradient_photo = ImageTk.PhotoImage(pil)
        self.gradient_canvas.delete("all")
        self.gradient_canvas.create_image(0, 0, image=self.gradient_photo, anchor="nw")

    # ============================================================
    # EVENTOS / ESTADO
    # ============================================================

    def _threshold_changed(self, value):
        try:
            n = int(float(value))
            self.status_operation.config(text=f"Umbral seleccionado: {n}")
        except ValueError:
            pass

    def _sync_colormap_from_side(self, _event=None):
        self.toolbar_cmap.set(self.cmap_var.get())
        self.update_gradient_preview()

    def _sync_colormap_from_toolbar(self, _event=None):
        self.cmap_var.set(self.toolbar_cmap.get())
        self.update_gradient_preview()

    def _update_ui_state(self):
        if self.current_image is None:
            self.status_operation.config(text="Sin operación")
        else:
            self.status_operation.config(text=self.current_operation)

    def future_feature(self, module):
        messagebox.showinfo(
            module,
            f"El módulo '{module}' ya está reservado en la interfaz para integrar "
            "las siguientes prácticas sin tener que rediseñar el programa.",
        )

    def show_about(self):
        messagebox.showinfo(
            "Acerca de",
            "IMAGE PROCESSING LABORATORY - ESCOM\n\n"
            "Aplicación integradora en Python + Tkinter + OpenCV.\n\n"
            "Módulos actuales:\n"
            "• Lectura de imágenes\n"
            "• RGB y HSV\n"
            "• Escala de grises\n"
            "• Histograma\n"
            "• Binarización fija y Otsu\n"
            "• Práctica 1: pseudocolor\n"
            "• Miniproyecto: ruido, filtros, operaciones y ECC V4/V8\n"
            "• Códigos de cadena y exportación de evidencia\n\n"
            "La arquitectura está preparada para agregar filtros, bordes y nuevas prácticas.",
        )


def main():
    root = tk.Tk()
    app = ImageProcessingLab(root)
    root.mainloop()


if __name__ == "__main__":
    main()
