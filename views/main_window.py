from __future__ import annotations
from typing import TYPE_CHECKING
import copy
import tkinter as tk
from tkinter import ttk, messagebox, filedialog  # Импортируем ttk
from pathlib import Path

from models import Swatch, ColorMode, SwatchType
from models import Color
from utils import get_version_from_pyproject

if TYPE_CHECKING:
    from controllers import SwatchController


class SwatchEditorView(tk.Tk):
    """
    Класс View. Отвечает только за отображение GUI и делегирует все
    действия пользователя контроллеру. Не содержит бизнес-логики.
    """

    def __init__(self):
        super().__init__()
        # Применяем тему ttk для современного вида.
        # Это улучшит внешний вид на Windows и Linux.
        style = ttk.Style(self)
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')

        self.controller = None
        self.title(f"Swatch Editor v{get_version_from_pyproject()}")
        self.geometry("600x400")

        self.layout = {
            'padding_x': 10,
            'padding_y': 5,
            'swatch_size': 40,
            'text_gap': 10,
            'text_width': 150
        }

        self.swatches_to_display: list[Swatch] = []

        self.create_ui()
        self.canvas.bind("<Double-1>", self.on_double_click)
        self.bind("<Configure>", lambda e: self.draw_swatches())

    def set_controller(self, controller: SwatchController):
        """Связывает View с контроллером и завершает настройку GUI."""
        self.controller = controller
        # Теперь, когда контроллер гарантированно существует, создаем меню
        self.create_menu()

    def create_menu(self):
        # tk.Menu не имеет прямого аналога в ttk и используется как есть
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.controller.new_swatch_file)
        file_menu.add_command(label="Load", command=self.controller.load_ase_dialog)
        file_menu.add_command(label="Save", command=self.controller.save_ase)
        file_menu.add_command(label="Save As...", command=self.controller.save_ase_as_dialog)
        file_menu.add_command(label="Export Json", command=self.controller.export_json_dialog)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add", command=self.controller.add_swatch)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.config(menu=menubar)

    def create_ui(self):
        """Создает основные виджеты интерфейса."""
        # tk.Canvas также не имеет аналога в ttk
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    # --- Публичные методы, вызываемые Контроллером ---

    def update_swatches(self, swatches: list[Swatch]):
        """API для контроллера: обновить список образцов и перерисовать."""
        self.swatches_to_display = swatches
        self.draw_swatches()

    def update_title(self, file_path: str | None):
        """API для контроллера: обновить заголовок окна."""
        title = f"Swatch Editor v{get_version_from_pyproject()} "
        if file_path:
            file_name = Path(file_path).name
            title += '[' + file_name + ']'
        self.title(title)

    def open_edit_window(self, idx: int, swatch_to_edit: Swatch):
        """Открывает окно редактирования с использованием виджетов ttk."""
        temp_swatch = copy.deepcopy(swatch_to_edit)

        # --- Настройка окна ---
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win_w = 400  # Немного шире для ttk виджетов
        win_h = 350
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2

        win = tk.Toplevel(self)
        win.title(f"Edit Swatch - {temp_swatch.name}")
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")
        win.transient(self)
        win.grab_set()

        # --- Основной фрейм ---
        main_frame = ttk.Frame(win, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- Виджеты ---
        # Name
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="e", pady=2)
        name_var = tk.StringVar(value=temp_swatch.name)
        name_entry = ttk.Entry(main_frame, textvariable=name_var)
        name_entry.grid(row=0, column=1, sticky="ew", pady=2)

        # Type (используем Combobox)
        ttk.Label(main_frame, text="Type:").grid(row=1, column=0, sticky="e", pady=2)
        type_var = tk.StringVar(value=temp_swatch.type.value)
        type_combobox = ttk.Combobox(main_frame, textvariable=type_var, values=[t.value for t in SwatchType], state='readonly')
        type_combobox.grid(row=1, column=1, sticky="ew", pady=2)

        # Mode (используем Combobox)
        ttk.Label(main_frame, text="Mode:").grid(row=2, column=0, sticky="e", pady=2)
        mode_var = tk.StringVar(value=temp_swatch.mode.value)
        mode_combobox = ttk.Combobox(main_frame, textvariable=mode_var, state='readonly')
        mode_combobox.grid(row=2, column=1, sticky="ew", pady=2)

        # Фрейм для редактирования цвета
        color_labelframe = ttk.LabelFrame(main_frame, text="Color Values", padding="10")
        color_labelframe.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        color_labelframe.columnconfigure(1, weight=1)  # Позволяем ползункам растягиваться

        # --- Динамические коллбэки и логика ---

        def update_mode_menu(*args):
            current_type = type_var.get()
            current_mode = mode_var.get()
            modes = ["CMYK"] if current_type == SwatchType.PROCESS.value else ["CMYK", "RGB", "LAB"]
            mode_combobox['values'] = modes
            if current_mode not in modes:
                mode_var.set(modes[0])

        type_var.trace_add('write', update_mode_menu)

        def draw_color_inputs(mode, values=None):
            for widget in color_labelframe.winfo_children():
                widget.destroy()

            color_class = Color.get_class_by_mode(mode)
            labels, ranges = color_class.get_metadata()

            if values is None or len(values) != len(labels):
                raise ValueError('Некорректные значения цвета')

            # Квадрат для предпросмотра цвета (используем tk.Label для простоты)
            color_square = tk.Label(color_labelframe, width=4, relief=tk.SUNKEN, borderwidth=2)
            color_square.grid(row=0, column=3, rowspan=len(labels), padx=(10, 0), pady=2, sticky="ns")

            color_vars = []

            def update_color_preview():
                try:
                    current_values = [float(var.get()) for var in color_vars]
                    temp_color = color_class(*current_values, is_normalized=False)
                    temp_swatch.color = temp_color
                    hex_color = temp_color.to_hex()
                    color_square.config(bg=hex_color)
                except (ValueError, Exception):
                    pass  # Игнорируем ошибки во время ввода

            for i, (label, rng) in enumerate(zip(labels, ranges)):
                ttk.Label(color_labelframe, text=label + ":").grid(row=i, column=0, sticky="w", padx=2, pady=3)

                scale_var = tk.DoubleVar(value=float(values[i]))
                entry_var = tk.StringVar(value=str(round(values[i])))
                color_vars.append(entry_var)

                scale = ttk.Scale(color_labelframe, from_=rng[0], to=rng[1], orient="horizontal", variable=scale_var)
                scale.grid(row=i, column=1, padx=5, pady=3, sticky="ew")

                entry = ttk.Entry(color_labelframe, textvariable=entry_var, width=5)
                entry.grid(row=i, column=2, padx=(0, 5), pady=3, sticky="w")

                # --- Логика синхронизации ---
                def make_callbacks(s_var, e_var, current_range):
                    def scale_to_entry(*_):
                        e_var.set(str(round(s_var.get())))
                        update_color_preview()

                    def entry_to_scale(*_):
                        try:
                            val = float(e_var.get())
                            clamped_val = max(current_range[0], min(val, current_range[1]))
                            if s_var.get() != clamped_val: s_var.set(clamped_val)
                            update_color_preview()
                        except (ValueError, TypeError):
                            pass

                    return scale_to_entry, entry_to_scale

                scale_cb, entry_cb = make_callbacks(scale_var, entry_var, rng)
                scale.config(command=scale_cb)
                entry_var.trace_add('write', entry_cb)

            update_color_preview()

        def on_mode_change(*args):
            if temp_swatch.mode.value == mode_var.get(): return
            old_mode, new_mode = temp_swatch.mode, ColorMode(mode_var.get())
            try:
                new_color = temp_swatch.color.convert_to(new_mode)
                temp_swatch.color, temp_swatch.mode = new_color, new_mode
                draw_color_inputs(new_mode.value, new_color.to_user())
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка конвертации: {str(e)}")
                mode_var.set(old_mode.value)

        mode_var.trace_add('write', on_mode_change)

        # --- Кнопки ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        def on_save():
            temp_swatch.name = name_var.get()
            temp_swatch.type = SwatchType(type_var.get())
            self.controller.save_edited_swatch(idx, temp_swatch)
            win.destroy()

        def on_cancel():
            win.destroy()

        def delete_swatch():
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{temp_swatch.name}'?"):
                self.controller.delete_swatch(idx)
                win.destroy()

        ttk.Button(btn_frame, text="Save", command=on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=delete_swatch).pack(side="left", padx=5)

        # --- Первоначальная отрисовка ---
        update_mode_menu()
        draw_color_inputs(mode_var.get(), temp_swatch.color.to_user())

        main_frame.columnconfigure(1, weight=1)
        win.wait_window()

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def ask_open_filename(self):
        return filedialog.askopenfilename(filetypes=[("ASE files", "*.ase")])

    def ask_save_as_filename(self, ext, ftypes):
        return filedialog.asksaveasfilename(defaultextension=ext, filetypes=ftypes)

    # --- Внутренние методы View ---

    def draw_swatches(self):
        self.canvas.delete("all")
        if not self.swatches_to_display: return
        spacing_x, spacing_y, cols = self._get_grid_params()

        for index, sw in enumerate(self.swatches_to_display):
            row, col = index // cols, index % cols
            x = self.layout['padding_x'] + col * spacing_x
            y = self.layout['padding_y'] + row * spacing_y
            x2 = x + self.layout['swatch_size']
            y2 = y + self.layout['swatch_size']

            try:
                hex_color = sw.color.to_hex()
            except Exception as e:
                print(f"⚠️ Ошибка в цвете {sw.name}: {e}")
                hex_color = "#888888"

            self.canvas.create_rectangle(x, y, x2, y2, fill=hex_color, outline="black", width=1)
            self.canvas.create_text(x2 + self.layout['text_gap'], y + self.layout['swatch_size'] // 2,
                                    text=sw.name, anchor='w', font=("Arial", 12))

    def on_double_click(self, event):
        idx = self.get_swatch_index_at(event.x, event.y)
        if idx is not None:
            self.controller.edit_swatch(idx)

    def _get_grid_params(self):
        spacing_x = self.layout['swatch_size'] + self.layout['text_gap'] + self.layout['text_width']
        spacing_y = self.layout['swatch_size'] + self.layout['padding_y']
        width = self.winfo_width()
        cols = max(1, width // spacing_x)
        return spacing_x, spacing_y, cols

    def get_swatch_index_at(self, x, y):
        spacing_x, spacing_y, cols = self._get_grid_params()
        if x < self.layout['padding_x'] or y < self.layout['padding_y']: return None
        col = (x - self.layout['padding_x']) // spacing_x
        row = (y - self.layout['padding_y']) // spacing_y
        idx = row * cols + col
        if 0 <= idx < len(self.swatches_to_display):
            # Проверяем, что клик был в пределах высоты квадрата
            relative_y = (y - self.layout['padding_y']) % spacing_y
            if relative_y < self.layout['swatch_size']:
                return idx
        return None
