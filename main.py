import os
import sys
import json
import copy
import configparser
import swatch
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from classes import Swatch, ColorMode, SwatchType
from color_models import Color


def create_swatch_from_data(data: dict, is_normalized: bool) -> Swatch:
    """Создает объект Swatch из словаря данных"""
    return Swatch(
        name=data['name'],
        type=SwatchType(data['type']),  # используем Enum
        mode=ColorMode(data['data']['mode']),  # используем Enum
        color=Color.create_from_data(data['data'], is_normalized=is_normalized)
    )

def swatch_to_data(swatch: Swatch) -> dict:
    """Преобразует объект Swatch в словарь для сохранения"""
    # return {
    #     'name': swatch.name,
    #     'type': swatch.type.value,  # преобразуем Enum в строку
    #     'data': color_to_data(swatch.color)
    # }
    return {
        'name': swatch.name,
        'type': swatch.type.value,  # преобразуем Enum в строку
        'data': swatch.color.to_data()
    }


class SwatchEditor(tk.Tk):
    def __init__(self, file_path=None):
        super().__init__()
        self.title("Swatch Editor")
        self.geometry("600x400")
        self.swatches: list[Swatch] = []
        self.file_path = file_path  # текущий файл ASE
        self.swatch_size = 40
        self.create_menu()
        self.create_ui()
        self.canvas.bind("<Double-1>", self.on_double_click)
        self.bind("<Configure>", lambda e: self.draw_swatches())

        # Автоматическая загрузка файла при запуске
        if file_path:
            self.load_ase_file(file_path)

    def create_menu(self):
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load", command=self.load_ase_dialog)
        file_menu.add_command(label="Save", command=self.save_ase)
        file_menu.add_command(label="Save As...", command=self.save_ase_as_dialog)
        file_menu.add_command(label="Export Json", command=self.export_json)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add", command=self.add_swatch)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.config(menu=menubar)

    def create_ui(self):
        self.canvas = tk.Canvas(self)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_swatches()

    def export_json(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.swatches, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Export Json", f"Exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export JSON: {e}")

    def draw_swatches(self):
        self.canvas.delete("all")
        padding_x = 10
        padding_y = 5
        spacing_x = self.swatch_size + 10 + 150  # квадратик + отступ + ширина текста
        spacing_y = self.swatch_size + padding_y
        width = self.winfo_width()
        cols = max(1, width // spacing_x)

        for index, sw in enumerate(self.swatches):
            row = index // cols
            col = index % cols
            x = padding_x + col * spacing_x
            y = padding_y + row * spacing_y
            x2 = x + self.swatch_size
            y2 = y + self.swatch_size

            try:
                hex_color = sw.color.to_hex()
            except Exception as e:
                print(f"⚠️ Ошибка в цвете {sw.name}: {e}")
                hex_color = "#888888"

            self.canvas.create_rectangle(x, y, x2, y2, fill=hex_color, outline="black")
            # Текст справа от квадратика, с вертикальным центром
            self.canvas.create_text(x2 + 10, y + self.swatch_size // 2,
                                    text=sw.name,
                                    anchor='w',
                                    font=("Arial", 12))

    def load_ase_file(self, filename: str) -> None:
        """Загружает ASE файл и обновляет интерфейс"""
        try:
            # Загружаем сырые данные из ASE файла
            raw_swatches = swatch.parse(filename)
            # Конвертируем каждый словарь в объект Swatch
            self.swatches = [create_swatch_from_data(raw, is_normalized=True) for raw in raw_swatches]
            self.file_path = filename
            self.title(f"Swatch Editor - {filename}")
            self.draw_swatches()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ASE: {e}")
            self.file_path = None

    def load_ase_dialog(self):
        filename = filedialog.askopenfilename(filetypes=[("ASE files", "*.ase")])
        if filename:
            self.load_ase_file(filename)

    def save_ase(self):
        if not self.file_path:
            self.save_ase_as_dialog()
            return

        try:
            # Конвертируем объекты Swatch обратно в словари
            raw_swatches = [swatch_to_data(sw) for sw in self.swatches]

            # Сохраняем в ASE файл
            swatch.write(raw_swatches, self.file_path)
            messagebox.showinfo("Save", f"Saved to {self.file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save ASE: {e}")

    def save_ase_as_dialog(self):
        filename = filedialog.asksaveasfilename(defaultextension=".ase", filetypes=[("ASE files", "*.ase")])
        if filename:
            self.file_path = filename
            self.save_ase()
            self.title(f"Swatch Editor - {filename}")

    def add_swatch(self):
        default_data = {
            "name": "New Swatch",
            "type": "Spot",
            "data": {
                "mode": "RGB",
                "values": [0, 0, 0]
            }
        }
        new_swatch = create_swatch_from_data(default_data, is_normalized=False)
        self.swatches.append(new_swatch)
        self.open_edit_window(len(self.swatches) - 1)

    def on_double_click(self, event):
        x, y = event.x, event.y
        idx = self.get_swatch_index_at(x, y)
        if idx is not None:
            self.open_edit_window(idx)

    def get_swatch_index_at(self, x, y):
        padding_x = 10
        padding_y = 5
        spacing_x = self.swatch_size + 10 + 150
        spacing_y = self.swatch_size + padding_y
        width = self.winfo_width()
        cols = max(1, width // spacing_x)

        row = y // spacing_y
        col = x // spacing_x
        idx = row * cols + col
        if 0 <= idx < len(self.swatches):
            # Проверяем, что клик был в пределах квадратика или названия (по горизонтали)
            rel_x = x % spacing_x
            rel_y = y % spacing_y
            if 0 <= rel_x <= spacing_x and 0 <= rel_y <= spacing_y:
                return idx
        return None

    def open_edit_window(self, idx):
        # Мы будем работать с temp_swatch, а original_swatch останется нетронутым.
        original_swatch = self.swatches[idx]
        temp_swatch = copy.deepcopy(original_swatch)

        def update_mode_menu(*args):
            current_type = type_var.get()
            current_mode = mode_var.get()

            # Удаляем текущее меню
            mode_menu['menu'].delete(0, 'end')

            # Обновляем доступные режимы
            modes = ["CMYK"] if current_type == SwatchType.PROCESS.value else ["CMYK", "RGB", "LAB"]

            # Добавляем новые опции
            for mode in modes:
                mode_menu['menu'].add_command(
                    label=mode,
                    command=tk._setit(mode_var, mode)
                )

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
            # deprecated
            # else:
            #     # Создаем объект цвета и получаем значения в пользовательском формате
            #     color_obj = color_class(*values, is_normalized=True)
            #     values = color_obj.to_user()

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

        # deprecated
        # def on_mode_change(*args):
        #     # При смене mode ставим нули в цвета
        #     draw_color_inputs(mode_var.get(), None)

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
            # ### ИЗМЕНЕНИЕ 4: Применяем все изменения из копии к оригиналу ###
            # Обновляем метаданные в нашей временной копии
            temp_swatch.name = name_var.get()
            temp_swatch.type = SwatchType(type_var.get())
            # temp_swatch.mode и temp_swatch.color уже актуальны благодаря on_mode_change и update_color_square

            # Заменяем оригинальный объект в списке на измененную копию
            self.swatches[idx] = temp_swatch

            self.draw_swatches()
            win.destroy()

        def on_cancel():
            win.destroy()

        # Кнопка Delete (как раньше)
        def delete_swatch():
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{temp_swatch.name}'?"):
                del self.swatches[idx]
                self.draw_swatches()
                win.destroy()

        btn_save = tk.Button(btn_frame, text="Save", command=on_save)
        btn_save.pack(side="left", padx=10)
        btn_cancel = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        btn_cancel.pack(side="left", padx=10)
        btn_delete = tk.Button(btn_frame, text="Delete", command=delete_swatch)
        btn_delete.pack(side="left", padx=10)

        # В конце функции, после создания всех виджетов:
        win.wait_window()


if __name__ == '__main__':
    # Определяем путь к папке, где находится .exe или .py скрипт
    if getattr(sys, 'frozen', False):
        # Приложение "заморожено" с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Приложение запущено как обычный .py скрипт
        application_path = os.path.dirname(os.path.abspath(__file__))

    # По умолчанию, не загружаем никакой файл
    swatch_file_to_load = None

    try:
        config_path = os.path.join(application_path, 'config.ini')
        config = configparser.ConfigParser()

        # config.read() не вызывает ошибку, если файла нет, а возвращает пустой список.
        # Мы проверяем, что файл был успешно прочитан.
        if config.read(config_path):
            # Получаем имя файла из конфига. Используем .get() для безопасности.
            config_swatch_name = config.get('Settings', 'swatch_file', fallback=None)

            if config_swatch_name:
                # Строим полный путь к файлу относительно папки приложения
                potential_path = os.path.join(application_path, config_swatch_name)

                # Если такой файл реально существует, мы его будем загружать
                if os.path.exists(potential_path):
                    swatch_file_to_load = potential_path

    except configparser.Error as e:
        # Если в config.ini ошибка, просто выводим информацию в консоль для отладки
        # и запускаем приложение пустым.
        print(f"Error reading config file: {e}")

    # Запускаем приложение. Если файл не был найден, file_path будет None.
    app = SwatchEditor(file_path=swatch_file_to_load)
    app.mainloop()
