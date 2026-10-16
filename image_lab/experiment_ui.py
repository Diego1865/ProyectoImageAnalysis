"""Controles de las prácticas 3-a, 3-b y miniproyecto ECC."""
import csv
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import cv2
from PIL import Image

from . import experiments as ops


class ExperimentMixin:
    def build_experiment_menu(self, menubar):
        self.exp_method = tk.StringVar(value='otsu')
        self.exp_dark = tk.BooleanVar(value=False)
        self.exp_threshold = tk.IntVar(value=127)
        self.exp_area = tk.IntVar(value=20)
        self.exp_noise = tk.DoubleVar(value=.02)
        self.exp_sigma = tk.DoubleVar(value=20)
        self.exp_mean = tk.DoubleVar(value=0)
        self.exp_seed = tk.IntVar(value=2026)
        self.exp_kernel = tk.IntVar(value=3)
        self.exp_relation = tk.StringVar(value='>')
        self.exp_operand = None
        menu = tk.Menu(menubar, tearoff=0)
        entries = [
            ('Parámetros del experimento...', self.experiment_settings),
            ('Segmentar (fondo negro / objetos blancos)', self.segment_current),
            ('Invertir máscara (NOT)', lambda: self.logic_current('NOT')),
            ('Comparar conteo V4 / V8 y código de cadena', self.count_current),
            ('Experimento antes / ruido / filtro', self.compare_noise),
            ('Experimento por lote (4 o más fotos)...', self.batch_experiment),
            ('Aplicar ruido sal y pimienta', lambda: self.noise_current('salt')),
            ('Aplicar ruido gaussiano', lambda: self.noise_current('gaussian')),
            ('Filtro de mediana', lambda: self.filter_current('median')),
            ('Filtro gaussiano', lambda: self.filter_current('gaussian')),
            ('Cargar imagen B para operaciones lógicas...', self.load_operand),
            ('AND con B', lambda: self.logic_current('AND')),
            ('OR con B', lambda: self.logic_current('OR')),
            ('XOR con B', lambda: self.logic_current('XOR')),
            ('Operación relacional (>, <, ==)', self.relation_current),
        ]
        for label, command in entries:
            menu.add_command(label=label, command=command)
        menubar.add_cascade(label='Miniproyecto ECC', menu=menu)

    def experiment_settings(self):
        win = tk.Toplevel(self.root)
        win.title('Parámetros de segmentación, ruido y conteo')
        fields = [
            ('Método', self.exp_method, ['otsu', 'fixed']),
            ('Umbral fijo / comparación (0-255)', self.exp_threshold, None),
            ('Área mínima en píxeles (1 = sin filtro)', self.exp_area, None),
            ('Sal y pimienta: proporción [0, 1]', self.exp_noise, None),
            ('Gaussiano: sigma (>= 0)', self.exp_sigma, None),
            ('Gaussiano: media', self.exp_mean, None),
            ('Semilla aleatoria (>= 0)', self.exp_seed, None),
            ('Ventana del filtro (impar >= 3)', self.exp_kernel, None),
            ('Operador relacional', self.exp_relation, ['>', '<', '==']),
        ]
        for row, (label, variable, choices) in enumerate(fields):
            ttk.Label(win, text=label).grid(row=row, column=0, padx=12, pady=5, sticky='w')
            widget = (ttk.Combobox(win, textvariable=variable, values=choices, state='readonly')
                      if choices else ttk.Entry(win, textvariable=variable))
            widget.grid(row=row, column=1, padx=12, pady=5)
        ttk.Checkbutton(win, text='Objetos oscuros sobre fondo claro (invertir al segmentar)',
                        variable=self.exp_dark).grid(row=9, columnspan=2, padx=12, pady=8)
        ttk.Label(win, text='Los parámetros se aplican a la próxima operación.\n'
                  'Mediana para sal y pimienta; gaussiano para ruido gaussiano.').grid(row=10, columnspan=2, padx=12)
        ttk.Button(win, text='Validar y cerrar', command=lambda: self._close_settings(win)).grid(row=11, columnspan=2, pady=12)

    def _close_settings(self, win):
        try:
            self._experiment_params()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror('Parámetros inválidos', str(exc), parent=win)
            return
        win.destroy()

    def _experiment_params(self):
        p = dict(method=self.exp_method.get(), threshold=self.exp_threshold.get(),
                 dark=self.exp_dark.get(), area=self.exp_area.get(), amount=self.exp_noise.get(),
                 sigma=self.exp_sigma.get(), mean=self.exp_mean.get(), seed=self.exp_seed.get(),
                 kernel=self.exp_kernel.get(), relation=self.exp_relation.get())
        if (p['method'] not in ('otsu', 'fixed') or not 0 <= p['threshold'] <= 255
                or p['area'] < 1 or not 0 <= p['amount'] <= 1 or p['sigma'] < 0
                or p['seed'] < 0 or p['kernel'] < 3 or p['kernel'] % 2 != 1
                or not np.isfinite([p['sigma'], p['mean']]).all()):
            raise ValueError('Revisa los intervalos indicados en los parámetros.')
        return p

    def _run_experiment_action(self, action):
        if not self.require_image():
            return
        try:
            action(self._experiment_params())
        except (ValueError, tk.TclError, OSError, cv2.error) as exc:
            messagebox.showerror('Experimento', str(exc), parent=self.root)

    def _mask(self, image, p):
        # Una máscara ya binaria conserva su polaridad. NOT permite invertirla explícitamente.
        source = ops.gray(image)
        if np.isin(source, [0, 255]).all():
            return source
        return ops.segment(source, p['method'], p['threshold'], p['dark'])[1]

    def segment_current(self):
        def action(p):
            threshold, mask = ops.segment(self.current_image, p['method'], p['threshold'], p['dark'])
            self.commit(mask, f'Segmentación {p["method"]} (T={threshold:.0f})')
        self._run_experiment_action(action)

    def noise_current(self, kind):
        def action(p):
            image = (ops.salt_pepper(self.current_image, p['amount'], p['seed']) if kind == 'salt'
                     else ops.gaussian_noise(self.current_image, p['sigma'], p['mean'], p['seed']))
            self.commit(image, 'Ruido sal y pimienta' if kind == 'salt' else 'Ruido gaussiano')
        self._run_experiment_action(action)

    def filter_current(self, method):
        self._run_experiment_action(lambda p: self.commit(
            ops.smooth(self.current_image, method, p['kernel']), f'Filtro {method} {p["kernel"]}x{p["kernel"]}'))

    def load_operand(self):
        path = filedialog.askopenfilename(title='Imagen B (mismo tamaño que A)',
                                          filetypes=[('Imágenes', '*.png *.jpg *.jpeg *.bmp *.tif *.tiff')])
        if path:
            try:
                with Image.open(path) as image:
                    self.exp_operand = np.array(image.convert('RGB'))
                self.status_left.config(text=f'Imagen B: {Path(path).name}')
            except OSError as exc:
                messagebox.showerror('Imagen B', str(exc))

    def logic_current(self, operation):
        def action(p):
            if operation != 'NOT' and self.exp_operand is None:
                raise ValueError('Carga primero una imagen B desde Miniproyecto ECC.')
            a = self._mask(self.current_image, p)
            b = None if operation == 'NOT' else self._mask(self.exp_operand, p)
            self.commit(ops.logical(a, b, operation), f'Operación lógica {operation}')
        self._run_experiment_action(action)

    def relation_current(self):
        self._run_experiment_action(lambda p: self.commit(
            ops.relational(self.current_image, p['relation'], p['threshold']),
            f'Relacional {p["relation"]} {p["threshold"]}'))

    def count_current(self):
        def action(p):
            mask = self._mask(self.current_image, p)
            self._show_ecc_results('Conteo de la imagen actual', [('segmentada', mask)], p,
                                   [('Original', self.current_image.copy())])
        self._run_experiment_action(action)

    def _noise_stages(self, image, p):
        mask = self._mask(image, p)
        salt = ops.salt_pepper(mask, p['amount'], p['seed'])
        noisy_gray = ops.gaussian_noise(ops.gray(image), p['sigma'], p['mean'], p['seed'])
        # Incluso si el ruido es 0 se respeta la polaridad elegida para la foto gris.
        dark = False if np.isin(ops.gray(image), [0, 255]).all() else p['dark']
        gauss_mask = ops.segment(noisy_gray, p['method'], p['threshold'], dark)[1]
        smooth_gray = ops.smooth(noisy_gray, 'gaussian', p['kernel'])
        return [('base', mask), ('sal_pimienta', salt),
                ('sal_pimienta_mediana', ops.smooth(salt, 'median', p['kernel'])),
                ('gaussiano', gauss_mask),
                ('gaussiano_filtrado', ops.segment(smooth_gray, p['method'], p['threshold'], dark)[1])]

    def compare_noise(self):
        self._run_experiment_action(lambda p: self._show_ecc_results(
            'Comparación de ruido y limpieza', self._noise_stages(self.current_image, p), p,
            [('Original', self.current_image.copy())]))

    def _show_ecc_results(self, title, stages, p, originals):
        rows, images, chains = [], list(originals), {}
        for name, mask in stages:
            images.append((name, mask.copy()))
            for connectivity in (4, 8):
                result = ops.components(mask, connectivity, p['area'])
                images.append((f'{name} V{connectivity}', result['view']))
                rows.append(dict(stage=name, connectivity=connectivity, raw_count=result['raw_count'],
                                 count=result['count'], min_area=p['area']))
                for region in result['regions']:
                    chains[f'{name}/V{connectivity}/objeto{region["number"]}'] = {
                        **region, **ops.chain_code(result['labels'], region['label'],
                            (region['x'], region['y'], region['width'], region['height']))}
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry('850x560')
        ttk.Label(win, text='Conteos de regiones conectadas. Fondo=0. Los objetos unidos pueden formar una sola región.').pack(pady=8)
        columns = ['stage', 'connectivity', 'raw_count', 'count', 'min_area']
        table = ttk.Treeview(win, columns=columns, show='headings', height=12)
        for name, text in zip(columns, ['Etapa / archivo', 'Vecindad', 'Sin filtrar', 'Tras área mínima', 'Área mínima']):
            table.heading(name, text=text)
            table.column(name, width=270 if name == 'stage' else 110)
        for row in rows:
            table.insert('', 'end', values=[row[k] for k in columns])
        table.pack(fill='both', expand=True, padx=10)
        chain_keys = list(chains)
        selected = tk.StringVar(value=chain_keys[0] if chain_keys else '')
        chooser = ttk.Combobox(win, values=chain_keys, textvariable=selected, state='readonly')
        chooser.pack(fill='x', padx=10, pady=6)
        text = tk.Text(win, height=5, wrap='word')
        text.pack(fill='x', padx=10)
        def show_chain(_event=None):
            text.config(state='normal')
            text.delete('1.0', 'end')
            value = chains.get(selected.get())
            text.insert('end', json.dumps(value, ensure_ascii=False) if value else 'No hay regiones aceptadas.')
            text.config(state='disabled')
        chooser.bind('<<ComboboxSelected>>', show_chain)
        show_chain()
        buttons = ttk.Frame(win)
        buttons.pack(pady=10)
        ttk.Button(buttons, text='Ver máscaras y etiquetas', command=lambda: self.open_component_window(
            title, images[:4])).pack(side='left', padx=4)
        # Selección individual evita abrir decenas de canvas en lotes.
        image_names = [name for name, _ in images]
        chosen_image = tk.StringVar(value=image_names[0])
        ttk.Combobox(buttons, values=image_names, textvariable=chosen_image, state='readonly', width=25).pack(side='left')
        ttk.Button(buttons, text='Ver seleccionada', command=lambda: self.open_component_window(
            chosen_image.get(), [images[image_names.index(chosen_image.get())]])).pack(side='left', padx=4)
        ttk.Button(buttons, text='Exportar evidencia...', command=lambda: self._export_ecc(
            p, rows, images, chains, win)).pack(side='left', padx=4)

    def _export_ecc(self, params, rows, images, chains, parent):
        target = filedialog.askdirectory(title='Carpeta de exportación', parent=parent)
        if not target:
            return
        try:
            from datetime import datetime
            # Carpeta nueva: evita sobrescribir experimentos previos.
            folder = Path(target) / ('ECC_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            folder.mkdir()
            with (folder / 'conteos.csv').open('w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            (folder / 'parametros.json').write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding='utf-8')
            (folder / 'regiones_y_cadenas.json').write_text(json.dumps(chains, ensure_ascii=False, indent=2), encoding='utf-8')
            manifest = []
            for i, (name, image) in enumerate(images):
                filename = f'imagen_{i:03d}.png'
                Image.fromarray(image).save(folder / filename)
                manifest.append(dict(file=filename, description=name))
            (folder / 'imagenes.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            messagebox.showinfo('Evidencia exportada', str(folder), parent=parent)
        except OSError as exc:
            messagebox.showerror('Exportación', str(exc), parent=parent)

    def batch_experiment(self):
        paths = filedialog.askopenfilenames(title='Selecciona al menos cuatro imágenes del experimento',
                                           filetypes=[('Imágenes', '*.png *.jpg *.jpeg *.bmp *.tif *.tiff')])
        if not paths:
            return
        if len(paths) < 4:
            messagebox.showwarning('Experimento por lote', 'La guía pide al menos cuatro imágenes. Selecciona cuatro o más.')
            return
        try:
            p = self._experiment_params()
            stages, originals = [], []
            for index, path in enumerate(paths, 1):
                name = f'{index:02d}_{Path(path).name}'
                with Image.open(path) as image:
                    arr = np.array(image.convert('RGB'))
                originals.append((name, arr))
                stages.extend((f'{name}/{stage}', mask) for stage, mask in self._noise_stages(arr, p))
            p = {**p, 'source_files': list(paths)}
            self._show_ecc_results('Experimento por lote', stages, p, originals)
        except (ValueError, tk.TclError, OSError, cv2.error) as exc:
            messagebox.showerror('Experimento por lote', str(exc))
