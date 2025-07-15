from __future__ import annotations
from typing import TYPE_CHECKING
import copy
import tkinter as tk
from tkinter import messagebox, filedialog

from models import Swatch, ColorMode, SwatchType
from models import Color

if TYPE_CHECKING:
    from controllers import SwatchController


class SwatchEditorView(tk.Tk):
    """
    Класс View. Отвечает только за отображение GUI и делегирует все
    действия пользователя контроллеру. Не содержит бизнес-логики.
    """
    def __init__(self):
        super().__init__()
        self.controller = None
        self.title("Swatch Editor")
        self.geometry("600x400")

        self.layout = {
            'padding_x': 10,
            'padding_y': 5,
            'swatch_size': 40,
            'text_gap': 10,
            'text_width': 150
        }

        # View больше не хранит список образцов. Он получает его от контроллера для отрисовки.
        self.swatches_to_display: list[Swatch] = []

        # self.create_menu()
        self.create_ui()
        self.canvas.bind("<Double-1>", self.on_double_click)
        self.bind("<Configure>", lambda e: self.draw_swatches())

    def set_controller(self, controller: SwatchController):
        """Связывает View с контроллером и завершает настройку GUI."""
        self.controller = controller
        # Теперь, когда контроллер гарантированно существует, создаем меню
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        # Команды теперь вызывают методы контроллера
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
        self.canvas = tk.Canvas(self)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    # --- Публичные методы, вызываемые Контроллером ---

    def update_swatches(self, swatches: list[Swatch]):
        """API для контроллера: обновить список образцов и перерисовать."""
        self.swatches_to_display = swatches
        self.draw_swatches()

    def update_title(self, file_path: str | None):
        """API для контроллера: обновить заголовок окна."""
        if file_path:
            self.title(f"Swatch Editor - {file_path}")
        else:
            self.title("Swatch Editor")

    # todo open_edit_window нужно еще переделать под новую архитектуру.
    # В частности, разобраться с этим swatch_to_edit, temp_swatch, original_swatch
    def open_edit_window(self, idx: int, swatch_to_edit: Swatch):
        # Мы будем работать с temp_swatch, а original_swatch останется нетронутым.
        temp_swatch = copy.deepcopy(swatch_to_edit)

        def update_mode_menu(*args):
            current_type = type_var.get()
            current_mode = mode_var.get()

            # Удаляем текущее меню
            # mode_menu['menu'].delete(0, 'end')

            # Обновляем доступные режимы
            modes = ["CMYK"] if current_type == SwatchType.PROCESS.value else ["CMYK", "RGB", "LAB"]

            # # Добавляем новые опции
            # for mode in modes:
            #     mode_menu['menu'].add_command(
            #         label=mode,
            #         command=tk._setit(mode_var, mode)
            #     )

            # Обновляем меню
            menu = mode_menu["menu"]
            menu.delete(0, "end")
            for mode in modes:
                menu.add_command(label=mode, command=tk._setit(mode_var, mode))

            # Если текущий режим стал невалидным, автоматически переключаемся
            if current_mode not in modes:
                mode_var.set(modes[0])

        # Сначала обновляем размеры родителя
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win_w = 350
        win_h = 350
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2


        win = tk.Toplevel(self)
        win.title(f"Edit Swatch - {temp_swatch.name}")
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # Сделать окно модальным
        win.transient(self)  # связывает окно с главным
        win.grab_set()  # блокирует все остальные окна приложения

        # Поля редактирования
        tk.Label(win, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        name_var = tk.StringVar(value=temp_swatch.name)
        name_entry = tk.Entry(win, textvariable=name_var)
        name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Создаем меню Type с обработчиком
        tk.Label(win, text="Type:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        type_var = tk.StringVar(value=temp_swatch.type.value)
        type_menu = tk.OptionMenu(win, type_var, "Spot", "Process")
        type_menu.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        type_var.trace_add('write', update_mode_menu)

        # Создаем меню Mode
        tk.Label(win, text="Mode:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        # deprecated mode_var = tk.StringVar(value=current_swatch.get("data", {}).get("mode", "CMYK"))
        mode_var = tk.StringVar(value=temp_swatch.mode.value)
        mode_menu = tk.OptionMenu(win, mode_var, "CMYK", "RGB", "Lab")
        mode_menu.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Цвета — контейнер для замены в будущем
        color_frame = tk.Frame(win, relief=tk.RIDGE, borderwidth=1)
        color_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="we")

        def draw_color_inputs(mode, values=None):
            # Очистка
            for w in color_frame.winfo_children():
                w.destroy()

            color_class = Color.get_class_by_mode(mode)

            # Получаем метаданные из класса цвета
            labels, ranges = color_class.get_metadata()

            # Проверяем значения
            if values is None or len(values) != len(labels):
                raise Exception('Некорректные значения цвета')

            def update_color_square(*args):
                # Собираем текущие значения из полей ввода
                try:
                    current_values = [float(var.get()) for var in color_vars]

                    # Создаем объект цвета текущего режима
                    temp_color = color_class(*current_values, is_normalized=False)

                    # Обновляем временный объект, а не основной
                    temp_swatch.color = temp_color

                    hex_color = temp_color.to_hex()
                    color_square.config(bg=hex_color)

                except (ValueError, Exception) as e:
                    print(f"Ошибка обновления цвета: {e}")

            color_vars = []
            for i, (label, rng) in enumerate(zip(labels, ranges)):
                tk.Label(color_frame, text=label + ":").grid(row=i, column=0, sticky="e", padx=2, pady=2)
                var = tk.StringVar(value=str(values[i]))
                entry = tk.Entry(color_frame, textvariable=var, width=10)
                entry.grid(row=i, column=1, sticky="w", pady=2)
                color_vars.append(var)

                # Ползунок
                scale = tk.Scale(color_frame, from_=rng[0], to=rng[1], orient="horizontal", length=100, resolution=1)
                scale.set(float(values[i]))
                scale.grid(row=i, column=2, padx=2)

                # Синхронизация поля и ползунка
                def make_scale_callback(var, scale):
                    def on_var_change(*_):
                        try:
                            scale.set(float(var.get()))
                        except Exception:
                            pass
                        update_color_square()
                    return on_var_change

                def make_entry_callback(var, scale):
                    def on_scale_change(val):
                        var.set(str(val))
                        update_color_square()
                    return on_scale_change

                var.trace_add('write', make_scale_callback(var, scale))
                scale.config(command=make_entry_callback(var, scale))


            # Цветной квадратик справа
            color_square = tk.Label(color_frame, width=4, height=2, bg=temp_swatch.color.to_hex(), relief=tk.SUNKEN, borderwidth=2)
            color_square.grid(row=0, column=3, rowspan=len(labels), padx=10, pady=2, sticky="ns")

        # Рисуем поля при открытии окна с текущими значениями
        draw_color_inputs(mode_var.get(), temp_swatch.color.to_user())

        def on_mode_change(*args):
            old_mode = temp_swatch.mode
            new_mode = ColorMode(mode_var.get())

            if old_mode != new_mode:
                try:
                    # Конвертируем текущий цвет в новый режим
                    new_color = temp_swatch.color.convert_to(new_mode)
                    temp_swatch.color = new_color
                    temp_swatch.mode = new_mode

                    # Обновляем UI новыми значениями
                    draw_color_inputs(new_mode.value, new_color.to_user())

                except Exception as e:
                    messagebox.showerror("Ошибка", f"Ошибка конвертации: {str(e)}")
                    mode_var.set(old_mode.value)


        mode_var.trace_add('write', on_mode_change)

        # Принудительно обновляем меню Mode при открытии окна
        update_mode_menu()

        # Кнопки Save и Cancel
        btn_frame = tk.Frame(win)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)


        def on_save():
            # 5. ПЕРЕД СОХРАНЕНИЕМ обновляем объект из полей ввода
            temp_swatch.name = name_var.get()
            temp_swatch.type = SwatchType(type_var.get())
            # Цвет и режим уже обновлены через trace-коллбэки

            # Передаем полностью обновленную копию в контроллер
            self.controller.save_edited_swatch(idx, temp_swatch)
            win.destroy()

        def on_cancel():
            win.destroy()

        # Кнопка Delete
        def delete_swatch():
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{temp_swatch.name}'?"):
                self.controller.delete_swatch(idx)
                win.destroy()

        btn_save = tk.Button(btn_frame, text="Save", command=on_save)
        btn_save.pack(side="left", padx=10)
        btn_cancel = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        btn_cancel.pack(side="left", padx=10)
        btn_delete = tk.Button(btn_frame, text="Delete", command=delete_swatch)
        btn_delete.pack(side="left", padx=10)

        # В конце функции, после создания всех виджетов:
        win.wait_window()
        # END OF open_edit_window

    # Методы для показа диалогов, которые вызывает контроллер
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
        # ... (код отрисовки остается почти таким же, но использует self.swatches_to_display)
        # ...
        spacing_x, spacing_y, cols = self._get_grid_params()

        for index, sw in enumerate(self.swatches_to_display):
            row = index // cols
            col = index % cols
            x = self.layout['padding_x'] + col * spacing_x
            y = self.layout['padding_y'] + row * spacing_y
            x2 = x + self.layout['swatch_size']
            y2 = y + self.layout['swatch_size']

            try:
                hex_color = sw.color.to_hex()
            except Exception as e:
                print(f"⚠️ Ошибка в цвете {sw.name}: {e}")
                hex_color = "#888888"

            self.canvas.create_rectangle(x, y, x2, y2, fill=hex_color, outline="black")
            self.canvas.create_text(x2 + 10, y + self.layout['swatch_size'] // 2,
                                    text=sw.name,
                                    anchor='w',
                                    font=("Arial", 12))

    def on_double_click(self, event):
        x, y = event.x, event.y
        idx = self.get_swatch_index_at(x, y)
        if idx is not None:
            # Передаем управление контроллеру
            self.controller.edit_swatch(idx)

    # ... (методы _get_grid_params и get_swatch_index_at остаются здесь, т.к. это логика View) ...
    def _get_grid_params(self):
        # ... (без изменений)
        spacing_x = self.layout['swatch_size'] + self.layout['text_gap'] + self.layout['text_width']
        spacing_y = self.layout['swatch_size'] + self.layout['padding_y']
        width = self.winfo_width()
        cols = max(1, width // spacing_x)
        return spacing_x, spacing_y, cols

    def get_swatch_index_at(self, x, y):
        # ... (без изменений)
        spacing_x, spacing_y, cols = self._get_grid_params()
        if x < self.layout['padding_x'] or y < self.layout['padding_y']: return None
        col = (x - self.layout['padding_x']) // spacing_x
        row = (y - self.layout['padding_y']) // spacing_y
        idx = row * cols + col
        if 0 <= idx < len(self.swatches_to_display):
            relative_y = (y - self.layout['padding_y']) % spacing_y
            if relative_y < self.layout['swatch_size']:
                return idx
        return None
