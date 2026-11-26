"""Модуль экрана второго практического задания: алгоритмы внешней сортировки."""

import customtkinter as ctk
from tkinter import filedialog
import csv
import os
import tempfile
from itertools import islice
import copy


def create_screen2(parent, on_back):
    """Создает фрейм для внешней сортировки табличных файлов."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    # Конфигурация сетки основного контейнера экрана:
    # верхняя и нижняя панели имеют фиксированный размер, центральная растягивается
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_rowconfigure(2, weight=0)

    # ==========================================
    # 1. СОСТОЯНИЕ ДАННЫХ ЭКРАНА (STATE)
    # ==========================================
    current_data = {
        "step": 0,
        "delay_ms": 200,
        "is_running": False,
        "log_full_array": [],
        "headers": [],
        "table": [],
        "key_column": 0,
        "sort_direction": None,   # Направление: 'asc' (▲), 'desc' (▼) или None (не выбрано)
        "merge_method": "direct",  # Метод слияния: 'direct', 'natural', 'multiway'
        "temp_files": []
    }
    ram_buffer_size = 8

    log_current_array = ["Лог:\n"]
    log_full_array = ["Лог:\n"]
    initial_data = {}  # Глубокая копия состояния для возврата при сбросе (on_reset)

    # ==========================================
    # 2. ОСНОВНЫЕ ФРЕЙМЫ ИНТЕРФЕЙСА
    # ==========================================
    top_frame = ctk.CTkFrame(frame, fg_color="transparent")
    top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

    content_frame = ctk.CTkFrame(frame, fg_color="transparent")
    content_frame.grid(row=1, column=0, sticky="nsew")
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_rowconfigure(1, weight=0)

    # Контейнер для отображения лога и будущей таблицы
    main_container = ctk.CTkFrame(content_frame, fg_color="transparent")
    main_container.grid(row=0, column=0, sticky="nsew")
    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_columnconfigure(1, weight=3)
    main_container.grid_columnconfigure(2, weight=1)
    main_container.grid_rowconfigure(0, weight=1)

    # Информационная строка состояния и пояснений
    info_container = ctk.CTkFrame(content_frame, fg_color="transparent")
    info_container.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    info_container.grid_columnconfigure(0, weight=1)
    info_container.grid_columnconfigure(1, weight=2)
    info_container.grid_columnconfigure(2, weight=1)

    # Нижняя панель элементов управления
    bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
    bottom_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    bottom_frame.grid_columnconfigure(0, weight=0)
    bottom_frame.grid_columnconfigure(1, weight=1)
    bottom_frame.grid_columnconfigure(2, weight=0)
    bottom_frame.grid_columnconfigure(3, weight=1)
    bottom_frame.grid_columnconfigure(4, weight=0)
    player_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
    player_frame.grid(row=0, column=0, sticky="w")
    speed_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")  # Зона настройки задержки воспроизведения
    speed_frame.grid(row=0, column=2)
    file_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
    file_frame.grid(row=0, column=4, sticky="e")

    # ==========================================
    # 3. ВИДЖЕТЫ ВЕРХНЕЙ ПАНЕЛИ
    # ==========================================
    top_frame.grid_columnconfigure(0, weight=0)
    top_frame.grid_columnconfigure(1, weight=1)

    btn_back = ctk.CTkButton(
        top_frame,
        command=on_back,
        text="← Назад",
        height=40,
        width=80,
        font=("Arial", 12, "bold"),
        fg_color="#4A4A4A",
        hover_color="#3A3A3A"
    )
    btn_back.grid(row=0, column=0, padx=(0, 20), pady=5)

    # Переключатель метода внешней сортировки (прямое / естественное / многопутевое слияние)
    def on_method_change(value):
        """Обновляет выбранный метод слияния и сбрасывает прогресс сортировки."""
        method_map = {
            "Прямое слияние": "direct",
            "Естественное слияние": "natural",
            "Многопутевое слияние": "multiway",
        }
        current_data["merge_method"] = method_map.get(value, "direct")
        invalidate_sort_progress()

    method_selector = ctk.CTkSegmentedButton(
        top_frame,
        values=["Прямое слияние", "Естественное слияние", "Многопутевое слияние"],
        command=on_method_change,
        height=40,
        font=("Arial", 12, "bold"),
        selected_color="#4338CA",
        selected_hover_color="#3730A3",
        unselected_color="#37474F",
        unselected_hover_color="#263238",
    )
    method_selector.set("Прямое слияние")
    method_selector.grid(row=0, column=1, padx=10, pady=5)

    # ==========================================
    # 4. ВИДЖЕТЫ ЦЕНТРАЛЬНОЙ ОБЛАСТИ (ЛОГ И ПОЯСНЕНИЯ)
    # ==========================================

    def update_log_display():
        """Обновляет содержимое текстового лога на экране."""
        log_textbox.configure(state="normal")
        log_textbox.delete("1.0", "end")
        log_textbox.insert("1.0", "".join(log_current_array))
        log_textbox.see("end")
        log_textbox.configure(state="disabled")

    def update_temp_files_display():
        """Показывает серии и временные файлы, участвующие в проходах."""
        temp_files_textbox.configure(state="normal")
        temp_files_textbox.delete("1.0", "end")
        entries = current_data.get("temp_files", [])
        if not entries:
            temp_files_textbox.insert("end", "Временные серии пока не созданы.")
        else:
            for entry in entries:
                temp_files_textbox.insert(
                    "end",
                    f"{entry['name']}\n"
                    f"  {entry['role']}\n"
                    f"  {entry['status']}\n\n"
                )
        temp_files_textbox.configure(state="disabled")

    def render_table():
        """Отрисовывает таблицу данных с интерактивными кнопками сортировки в заголовках.

        Считывает метаданные (заголовки) и строки превью из current_data.
        Каждая кнопка заголовка циклически переключается между тремя состояниями:
        1. Не выбрана (нейтральный заголовок без стрелки).
        2. Выбрана по возрастанию (активный цвет и стрелка ▲).
        3. Выбрана по убыванию (активный цвет и стрелка ▼).
        """
        # Скрываем исходный контейнер-заглушку, если он все еще отображается на экране
        try:
            table_container.grid_remove()
        except NameError:
            pass

        # Очищаем ячейку сетки от ранее отрисованных таблиц во избежание утечки памяти и наслоения виджетов
        for widget in main_container.grid_slaves(row=0, column=1):
            try:
                if widget is not table_container:
                    widget.destroy()
            except NameError:
                widget.destroy()

        # Контейнер для отображения лога и будущей таблицы
        table_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        table_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        headers = current_data.get("headers", [])
        table_rows = current_data.get("table", [])

        # Если файл еще не выбран или пуст, отображаем поясняющую плашку-заглушку
        if not headers:
            placeholder = ctk.CTkLabel(
                table_frame,
                text="Таблица пока не загружена.\nНажмите «Загрузить CSV» для выбора файла.",
                font=("Arial", 16),
                text_color="#64748B"
            )
            placeholder.pack(expand=True, fill="both")
            return

        # Прокручиваемый контейнер: объединение кнопок заголовков и строк в общую сетку
        # гарантирует строгое попиксельное совпадение ширины колонок таблицы
        scroll_frame = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="#F8FAFC",
            corner_radius=10
        )
        scroll_frame.grid(row=0, column=0, sticky="nsew")

        # Настраиваем адаптивное распределение колонок по всей доступной ширине
        for col_idx in range(len(headers)):
            scroll_frame.grid_columnconfigure(col_idx, weight=1)

        active_col = current_data.get("key_column")
        sort_direction = current_data.get("sort_direction")

        def on_header_click(col_index: int):
            """Обрабатывает клик по колонке, выполняя циклический переход состояний сортировки."""
            if current_data.get("key_column") == col_index:
                # Циклический переход для текущей колонки: ▲ (asc) -> ▼ (desc) -> сброс (None)
                if current_data.get("sort_direction") == "asc":
                    current_data["sort_direction"] = "desc"
                elif current_data.get("sort_direction") == "desc":
                    current_data["sort_direction"] = None
                    current_data["key_column"] = None
                else:
                    current_data["sort_direction"] = "asc"
            else:
                # При клике на новую колонку сбрасываем предыдущую и начинаем с сортировки по возрастанию
                current_data["key_column"] = col_index
                current_data["sort_direction"] = "asc"

            invalidate_sort_progress()

            # Синхронизация статуса в нижней информационной панели с выбранным атрибутом
            current_dir = current_data.get("sort_direction")
            if current_dir == "asc":
                explanation_label.configure(
                    text=f"Ключевой атрибут: «{headers[col_index]}» (по возрастанию ▲)"
                )
            elif current_dir == "desc":
                explanation_label.configure(
                    text=f"Ключевой атрибут: «{headers[col_index]}» (по убыванию ▼)"
                )
            else:
                explanation_label.configure(
                    text="Ключевой атрибут не выбран. Нажмите на заголовок для выбора."
                )

            # Перерисовываем таблицу с обновленными индикаторами на кнопках
            render_table()

        # Отрисовка кнопок атрибутов в верхней строке (row=0)
        for col_idx, header_text in enumerate(headers):
            is_active = (col_idx == active_col and sort_direction is not None)

            # Формирование внешнего вида кнопки в зависимости от текущего состояния
            if is_active and sort_direction == "asc":
                btn_text = f"{header_text} ▲"
                btn_fg = "#4338CA"
                btn_hover = "#3730A3"
            elif is_active and sort_direction == "desc":
                btn_text = f"{header_text} ▼"
                btn_fg = "#4338CA"
                btn_hover = "#3730A3"
            else:
                btn_text = header_text
                btn_fg = "#37474F"
                btn_hover = "#263238"

            header_button = ctk.CTkButton(
                scroll_frame,
                text=btn_text,
                font=("Arial", 12, "bold"),
                height=32,
                fg_color=btn_fg,
                hover_color=btn_hover,
                text_color="#FFFFFF",
                command=lambda c=col_idx: on_header_click(c)
            )
            header_button.grid(row=0, column=col_idx, sticky="ew", padx=2, pady=(2, 6))

        # Отрисовка строк данных с чередованием цвета (зебра) для улучшения читаемости
        for row_idx, row_values in enumerate(table_rows):
            row_bg = "#FFFFFF" if row_idx % 2 == 0 else "#F1F5F9"
            for col_idx, cell_value in enumerate(row_values):
                if col_idx < len(headers):
                    cell_label = ctk.CTkLabel(
                        scroll_frame,
                        text=str(cell_value),
                        font=("Arial", 12),
                        text_color="#1E293B",
                        fg_color=row_bg,
                        corner_radius=4,
                        height=28
                    )
                    cell_label.grid(row=row_idx + 1, column=col_idx, sticky="ew", padx=2, pady=1)

    def sort_table():
        """Выполняет внешнюю сортировку таблицы с реальной записью серий на диск.

        Поддерживает три метода слияния, выбираемых пользователем:
        - 'direct'   — прямое двухпутевое слияние: равные порции по chunk_size строк;
        - 'natural'  — естественное слияние: серии формируются по уже упорядоченным
                       участкам исходного файла, а не по фиксированным порциям;
        - 'multiway' — многопутевое (k=4) слияние: одновременно сливаются до 4 серий.

        Промежуточные серии записываются в реальные временные файлы на диске через
        tempfile.NamedTemporaryFile, и удаляются после завершения алгоритма.
        В буфере RAM хранится одна исходная серия и по одной текущей строке каждой
        сливаемой серии; итоговая серия также записывается построчно на диск.

        Returns:
            list[dict]: Список шагов сортировки, где каждый шаг содержит:
                - 'log_line': текстовая запись для журнала;
                - 'explanation': понятное объяснение действия;
                - 'table': срез строк таблицы (до 20 записей) для предпросмотра;
                - 'action': тип операции ('read_chunk', 'sort_chunk', 'merge', 'done').
        """
        file_path = current_data.get("file_path")
        key_col = current_data.get("key_column")
        sort_direction = current_data.get("sort_direction")
        headers = current_data.get("headers", [])
        merge_method = current_data.get("merge_method", "direct")

        # Проверка наличия исходного файла на диске
        if not file_path or not os.path.exists(file_path):
            return [{
                "log_line": "Ошибка: Файл таблицы не загружен.\n",
                "explanation": "Сначала загрузите CSV-файл через кнопку «Загрузить CSV».",
                "table": [],
                "action": "error"
            }]

        # Проверка выбора ключевого атрибута и направления сортировки
        if key_col is None or key_col < 0 or key_col >= len(headers) or sort_direction is None:
            return [{
                "log_line": "Предупреждение: Ключевой атрибут сортировки не выбран.\n",
                "explanation": "Кликните по заголовку желаемой колонки таблицы, чтобы задать направление сортировки (▲ или ▼).",
                "table": current_data.get("table", []),
                "action": "warning"
            }]

        col_name = headers[key_col]
        is_reverse = (sort_direction == "desc")
        direction_text = "по убыванию (▼)" if is_reverse else "по возрастанию (▲)"

        method_names = {
            "direct": "Прямое двухпутевое слияние",
            "natural": "Естественное слияние",
            "multiway": "Многопутевое слияние (k=4)",
        }
        method_label = method_names.get(merge_method, merge_method)

        def detect_delimiter(sample):
            """Определяет разделитель даже при наличии поврежденных строк CSV."""
            try:
                return csv.Sniffer().sniff(sample, delimiters=";,|\t").delimiter
            except csv.Error:
                for line in sample.splitlines():
                    if line.strip():
                        candidates = [(line.count(char), char) for char in (";", ",", "|", "\t")]
                        count, delimiter = max(candidates)
                        if count:
                            return delimiter
                        break
                return ","

        column_count = len(headers)

        def normalize_row(raw_row):
            """Приводит строку CSV к ширине заголовка.

            Поврежденные строки CSV не должны останавливать сортировку: недостающие
            ячейки считаются пустыми, лишние ячейки игнорируются.
            """
            row = [parse_cell(cell) for cell in raw_row[:column_count]]
            if len(row) < column_count:
                row.extend([""] * (column_count - len(row)))
            return row

        def get_comparison_key(value):
            """Формирует универсальный ключ сравнения для безопасного сопоставления чисел и строк."""
            if isinstance(value, (int, float)):
                return (0, value)
            return (1, str(value).casefold())

        def compare_ordered(val_a, val_b):
            """Определяет, находится ли val_a перед val_b с учётом направления сортировки."""
            key_a, key_b = get_comparison_key(val_a), get_comparison_key(val_b)
            if is_reverse:
                return key_a >= key_b
            return key_a <= key_b

        # ----------------------------------------------------------------
        # Вспомогательные функции для работы с временными файлами на диске
        # ----------------------------------------------------------------

        temp_file_number = 0

        def create_run_file(role):
            """Создает пустую серию; строки записываются в нее постепенно."""
            nonlocal temp_file_number
            temp_file_number += 1
            file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False,
                encoding="utf-8", newline=""
            )
            current_data.setdefault("temp_files", []).append({
                "name": os.path.basename(file.name),
                "role": role,
                "status": "активен"
            })
            update_temp_files_display()
            return file

        def iter_run(path):
            """Читает серию построчно, не загружая ее целиком в память."""
            with open(path, mode="r", encoding="utf-8", newline="") as file:
                for row in csv.reader(file):
                    if row:
                        yield normalize_row(row)

        def preview_run(path, limit=20):
            """Возвращает только небольшой фрагмент серии для интерфейса."""
            return list(islice(iter_run(path), limit))

        def remove_tmpfiles(paths):
            """Удаляет список временных файлов, игнорируя ошибки отсутствия файла."""
            for p in paths:
                try:
                    os.remove(p)
                except OSError:
                    pass

        steps = []

        old_result = current_data.pop("sorted_result_path", None)
        current_data.pop("sorted_result_count", None)
        if old_result:
            try:
                os.remove(old_result)
            except OSError:
                pass
        current_data["temp_files"] = []
        update_temp_files_display()

        if merge_method == "direct":
            memory_description = (
                "Прямое двухпутевое слияние: начальные серии содержат по одной записи, "
                "при слиянии в RAM находятся две текущие записи, по одной из двух tempfiles."
            )
        elif merge_method == "multiway":
            memory_description = (
                f"Многопутевое слияние: начальная серия содержит до {ram_buffer_size} записей, "
                "при слиянии в RAM находится по одной текущей записи из каждой входной серии."
            )
        else:
            memory_description = (
                "Естественное слияние: серии выделяются по уже существующему порядку, "
                "при слиянии читается по одной текущей записи из каждой серии."
            )

        # Стартовая запись в лог с описанием параметров задачи
        steps.append({
            "log_line": (
                f"=== СТАРТ ВНЕШНЕЙ СОРТИРОВКИ ===\n"
                f"Файл: {os.path.basename(file_path)}\n"
                f"Метод: {method_label}\n"
                f"Ключевой атрибут: [{col_name}] (индекс {key_col})\n"
                f"Направление: {direction_text}\n"
                f"{memory_description}\n\n"
            ),
            "explanation": (
                f"Начинаем внешнюю сортировку ({method_label}) по атрибуту «{col_name}» "
                f"{direction_text}. {memory_description}"
            ),
            "table": current_data.get("table", []),
            "action": "start"
        })

        # ============================================================
        # Определение разделителя CSV-файла
        # ============================================================
        with open(file_path, mode="r", encoding="utf-8-sig") as fh:
            sample = fh.read(2048)
        delimiter = detect_delimiter(sample)

        # ============================================================
        # ФАЗА 1: Формирование начальных серий в зависимости от метода
        # ============================================================

        # Список путей к tmpfile текущего поколения серий
        run_paths = []
        chunk_size = 1 if merge_method == "direct" else ram_buffer_size

        if merge_method == "natural":
            # -----------------------------------------------------------
            # Естественное слияние: серия — максимальный уже упорядоченный
            # участок исходного файла; порции читаются построчно.
            # -----------------------------------------------------------
            steps.append({
                "log_line": "[Подготовка] Естественное слияние: ищем упорядоченные серии в файле...\n",
                "explanation": "Читаем файл построчно и выделяем серии — максимально длинные уже упорядоченные подпоследовательности.",
                "table": current_data.get("table", []),
                "action": "read_chunk"
            })

            with open(file_path, mode="r", encoding="utf-8-sig") as fh:
                reader = csv.reader(fh, delimiter=delimiter)
                next(reader, None)  # пропускаем заголовок

                run_file = None
                run_writer = None
                run_preview = []
                run_count = 0
                prev_key = None
                run_index = 0

                for raw_row in reader:
                    if not raw_row:
                        continue
                    row = normalize_row(raw_row)
                    cur_key = row[key_col]

                    # Если текущая строка нарушает порядок — завершаем серию
                    if prev_key is not None and not compare_ordered(prev_key, row[key_col]):
                        run_file.close()
                        run_index += 1
                        run_paths.append(run_file.name)
                        first_v = run_preview[0][key_col]
                        last_v = prev_key
                        steps.append({
                            "log_line": (
                                f"[Подготовка: Серия {run_index}] Естественная серия из {run_count} строк "
                            f"записана в {os.path.basename(run_file.name)}. "
                            f"Диапазон: [{first_v} … {last_v}]\n"
                            ),
                            "explanation": f"Серия №{run_index} ({run_count} строк) записана построчно на диск.",
                            "table": run_preview,
                            "action": "sort_chunk"
                        })
                        run_file = None
                        run_writer = None
                        run_preview = []
                        run_count = 0

                    if run_file is None:
                        run_file = create_run_file(f"Начальная естественная серия {run_index + 1}")
                        run_writer = csv.writer(run_file)
                    run_writer.writerow(row)
                    if len(run_preview) < 20:
                        run_preview.append(row)
                    run_count += 1
                    prev_key = cur_key

                # Последняя незакрытая серия
                if run_file is not None:
                    run_file.close()
                    run_index += 1
                    run_paths.append(run_file.name)
                    first_v = run_preview[0][key_col]
                    last_v = prev_key
                    steps.append({
                        "log_line": (
                            f"[Подготовка: Серия {run_index}] Последняя естественная серия из {run_count} строк "
                            f"записана в {os.path.basename(run_file.name)}. "
                            f"Диапазон: [{first_v} … {last_v}]\n"
                        ),
                        "explanation": f"Последняя серия №{run_index} ({run_count} строк) записана построчно на диск.",
                        "table": run_preview,
                        "action": "sort_chunk"
                    })

        else:
            # -----------------------------------------------------------
            # Прямое слияние и Многопутевое: читаем файл порциями по
            # chunk_size строк, сортируем каждую в памяти, пишем на диск.
            # -----------------------------------------------------------
            chunk_index = 0

            with open(file_path, mode="r", encoding="utf-8-sig") as fh:
                reader = csv.reader(fh, delimiter=delimiter)
                next(reader, None)  # пропускаем заголовок

                while True:
                    # Читаем строго chunk_size строк — реальное ограничение RAM
                    chunk = []
                    for raw_row in islice(reader, chunk_size):
                        if raw_row:
                            chunk.append(normalize_row(raw_row))

                    if not chunk:
                        break

                    chunk_index += 1
                    steps.append({
                        "log_line": f"[Подготовка: Серия {chunk_index}] Формирование серии из {len(chunk)} записи в RAM-буфере.\n",
                        "explanation": (
                            f"Для начальной серии читаем {len(chunk)} запись. "
                            "После сортировки она сразу записывается в отдельный tempfile."
                            if merge_method == "direct" else
                            f"Для начальной серии читаем до {len(chunk)} записей. "
                            "После сортировки серия сразу записывается в отдельный tempfile."
                        ),
                        "table": chunk[:20],
                        "action": "read_chunk"
                    })

                    # Внутренняя сортировка порции в RAM
                    sorted_chunk = sorted(
                        chunk,
                        key=lambda record: get_comparison_key(record[key_col]),
                        reverse=is_reverse
                    )

                    # Запись отсортированной серии на диск — не в RAM!
                    run_file = create_run_file(f"Начальная серия {chunk_index}")
                    csv.writer(run_file).writerows(sorted_chunk)
                    run_file.close()
                    run_paths.append(run_file.name)

                    first_val = sorted_chunk[0][key_col]
                    last_val = sorted_chunk[-1][key_col]
                    steps.append({
                        "log_line": (
                            f"[Подготовка: Серия {chunk_index}] Серия отсортирована в RAM и записана в tempfile. "
                            f"Файл: {os.path.basename(run_file.name)}. "
                            f"Диапазон ключа: [{first_val} … {last_val}]. "
                            f"Серия записана в tmpfile на диск.\n"
                        ),
                        "explanation": (
                            f"Начальная серия №{chunk_index} записана на диск. "
                            "При прямом слиянии дальше читается по одной текущей записи из двух tempfiles."
                            if merge_method == "direct" else
                            f"Начальная серия №{chunk_index} записана на диск. "
                            "При слиянии читается по одной текущей записи из каждой входной серии."
                        ),
                        "table": sorted_chunk[:20],
                        "action": "sort_chunk"
                    })

        steps.append({
            "log_line": f"\n[Подготовка завершена] Создано серий на диске: {len(run_paths)}. Начинаем проход 1 слияния.\n\n",
            "explanation": (
                f"Подготовлены {len(run_paths)} временных файлов. Подготовка не считается проходом. "
                "Начинаем проход 1 слияния. "
                "Для прямого слияния берутся две серии и по одной текущей записи из каждой."
                if merge_method == "direct" else
                f"Начальные серии записаны в {len(run_paths)} временных файлов. "
                "При слиянии читается по одной текущей записи из каждой входной серии."
            ),
            "table": (preview_run(run_paths[0]) if run_paths else []),
            "action": "preparation_done"
        })

        # ============================================================
        # ФАЗА 2: Слияние серий с диска
        # ============================================================

        merge_pass = 1

        def merge_group_to_file(group, pass_number, group_number):
            """Сливает серии потоково: в памяти только по одной строке из серии."""
            iterators = [iter_run(path) for path in group]
            current = []
            for iterator in iterators:
                try:
                    current.append(next(iterator))
                except StopIteration:
                    current.append(None)

            output = create_run_file(
                f"Результат прохода {pass_number}, группа {group_number} "
                f"из {len(group)} серий"
            )
            writer = csv.writer(output)
            preview = []
            input_names = [os.path.basename(path) for path in group]

            while any(row is not None for row in current):
                candidates = [(index, row) for index, row in enumerate(current) if row is not None]
                best_index, best_row = candidates[0]
                for index, row in candidates[1:]:
                    if compare_ordered(row[key_col], best_row[key_col]):
                        best_index, best_row = index, row

                writer.writerow(best_row)
                if len(preview) < 20:
                    preview.append(best_row)
                values = [str(row[key_col]) for _, row in candidates]
                steps.append({
                    "log_line": (
                        f"[Проход {pass_number}, Группа {group_number}] Потоковое слияние: "
                        f"выбираем «{best_row[key_col]}» из {values}; "
                        f"{input_names} -> {os.path.basename(output.name)}\n"
                    ),
                    "explanation": f"В памяти находятся только текущие строки {len(candidates)} серий; выбранная строка сразу записывается на диск.",
                    "table": preview[:20],
                    "action": "merge"
                })

                try:
                    current[best_index] = next(iterators[best_index])
                except StopIteration:
                    current[best_index] = None

            output.close()
            return output.name, preview

        while len(run_paths) > 1:
            next_run_paths = []
            group_size = 4 if merge_method == "multiway" else 2
            for start in range(0, len(run_paths), group_size):
                group = run_paths[start:start + group_size]
                new_path, _ = merge_group_to_file(group, merge_pass, start // group_size + 1)
                new_name = os.path.basename(new_path)
                for entry in current_data.get("temp_files", []):
                    if entry["name"] in {os.path.basename(path) for path in group}:
                        entry["status"] = f"использован в проходе {merge_pass}"
                    if entry["name"] == new_name:
                        entry["status"] = "активен"
                update_temp_files_display()
                next_run_paths.append(new_path)
            remove_tmpfiles(run_paths)
            run_paths = next_run_paths
            merge_pass += 1



        # ============================================================
        # Финал: оставляем итоговую серию на диске и показываем только превью
        # ============================================================
        final_path = run_paths[0] if run_paths else None
        final_table = preview_run(final_path) if final_path else []
        current_data["sorted_result_path"] = final_path
        current_data["sorted_result_count"] = sum(1 for _ in iter_run(final_path)) if final_path else 0
        for entry in current_data.get("temp_files", []):
            if final_path and entry["name"] == os.path.basename(final_path):
                entry["status"] = "итоговая серия"
        update_temp_files_display()

        steps.append({
            "log_line": f"\n=== СОРТИРОВКА УСПЕШНО ЗАВЕРШЕНА ===\nМетод: {method_label}\nВсего записей: {current_data['sorted_result_count']}\n",
            "explanation": "Все серии объединены потоково. Итоговая серия записана на диск; в интерфейсе показано только превью.",
            "table": final_table[:20],
            "action": "done"
        })

        return steps


    # Текстовое поле лога с автоматической прокруткой
    log_textbox = ctk.CTkTextbox(
        main_container,
        font=("Arial", 20),
        text_color="#1E293B",
        fg_color="transparent",
        activate_scrollbars=True
    )
    log_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # Контейнер для отображения таблицы (будет наполнен при загрузке файла)
    table_container = ctk.CTkFrame(main_container, fg_color="#F8FAFC", corner_radius=10)
    table_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

    temp_files_frame = ctk.CTkFrame(main_container, fg_color="#F8FAFC", corner_radius=10)
    temp_files_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=5)
    ctk.CTkLabel(
        temp_files_frame,
        text="Временные файлы",
        font=("Arial", 14, "bold"),
        text_color="#1E293B"
    ).pack(fill="x", padx=8, pady=(8, 4))
    temp_files_textbox = ctk.CTkTextbox(
        temp_files_frame,
        font=("Consolas", 11),
        text_color="#1E293B",
        fg_color="#FFFFFF"
    )
    temp_files_textbox.pack(expand=True, fill="both", padx=8, pady=(0, 8))
    temp_files_textbox.configure(state="disabled")

    lbl_table_placeholder = ctk.CTkLabel(
        table_container,
        text="Таблица пока не загружена.\nНажмите «Загрузить файл» для выбора CSV-файла.",
        font=("Arial", 16),
        text_color="#64748B"
    )
    lbl_table_placeholder.pack(expand=True, fill="both")

    # Отображение текущего номера шага
    step_label = ctk.CTkLabel(
        info_container,
        text=f"Шаг: {current_data['step']}",
        font=("Arial", 22, "bold")
    )
    step_label.grid(row=0, column=0, sticky="w", padx=(5, 0), pady=5)

    # Плашка с текстовым пояснением текущего действия
    explanation = "Загрузите файл таблицы для начала работы"
    explanation_label = ctk.CTkLabel(
        info_container,
        text=explanation,
        font=("Arial", 22),
        text_color="#4338CA"
    )
    explanation_label.grid(row=0, column=1, sticky="nsew", pady=5)

    update_log_display()
    update_temp_files_display()

    # ==========================================
    # 5. ОБРАБОТЧИКИ УПРАВЛЕНИЯ BOTTOM PANEL
    # ==========================================

    # Идентификатор активного таймера Tkinter для отмены автовоспроизведения при паузе/сбросе
    play_job_id = None

    def invalidate_sort_progress():
        """Сбрасывает рассчитанные шаги при изменении параметров сортировки."""
        nonlocal play_job_id
        if current_data.get("is_running"):
            current_data["is_running"] = False
            if play_job_id is not None:
                frame.after_cancel(play_job_id)
                play_job_id = None
            btn_play.configure(text="▶ Старт", fg_color="#2E7D32", hover_color="#1B5E20")
        current_data["log_full_array"] = []
        current_data["step"] = 0
        current_data.pop("sorted_full_table", None)
        old_result = current_data.pop("sorted_result_path", None)
        current_data.pop("sorted_result_count", None)
        if old_result:
            try:
                os.remove(old_result)
            except OSError:
                pass
        if initial_data:
            current_data["table"] = copy.deepcopy(initial_data.get("table", []))
        log_current_array.clear()
        log_current_array.append("Лог:\n")
        update_log_display()
        step_label.configure(text="Шаг: 0")
        render_table()

    def on_step_forward():
        """Выполняет один шаг сортировки вперед с выводом записи в лог и обновлением таблицы."""
        # Если шаги еще не сгенерированы, вычисляем их через sort_table
        if not current_data.get("log_full_array"):
            steps = sort_table()
            current_data["log_full_array"] = steps
            current_data["step"] = 0

            # Если вернулось сообщение об ошибке (например, файл не загружен или не выбран атрибут)
            if steps and steps[0].get("action") in ("error", "warning"):
                log_current_array.append(steps[0]["log_line"])
                update_log_display()
                explanation_label.configure(text=steps[0]["explanation"])
                return False

        # Проверяем, есть ли следующий шаг в очереди
        if current_data["step"] < len(current_data["log_full_array"]):
            step_item = current_data["log_full_array"][current_data["step"]]
            current_data["step"] += 1

            # Добавляем строку операции в текстовый лог экрана
            log_current_array.append(step_item["log_line"])
            update_log_display()

            # Обновляем счетчик шагов и понятное текстовое пояснение
            step_label.configure(text=f"Шаг: {current_data['step']}")
            explanation_label.configure(text=step_item["explanation"])

            # Напрямую обновляем данные таблицы в current_data для синхронизации отображения
            if "table" in step_item:
                current_data["table"] = list(step_item["table"])
                if "full_table" in step_item:
                    current_data["sorted_full_table"] = list(step_item["full_table"])
                render_table()

            # Если включен режим непрерывного автовоспроизведения, планируем следующий такт
            if current_data["is_running"]:
                nonlocal play_job_id
                play_job_id = frame.after(current_data["delay_ms"], play_tick)
            return True
        else:
            # Все шаги выполнены: останавливаем воспроизведение
            if current_data["is_running"]:
                toggle_play()
                explanation_label.configure(text="Сортировка завершена!")
            return False

    def on_step_back():
        """Откатывает один шаг назад, удаляет запись из лога и возвращает состояние таблицы."""
        # Ручной шаг назад автоматически ставит воспроизведение на паузу
        if current_data["is_running"]:
            toggle_play()

        if current_data["step"] > 0:
            current_data["step"] -= 1

            # Удаляем последнюю строку шага из лога (сохраняя начальные строки заголовка)
            if len(log_current_array) > 1:
                log_current_array.pop()
            update_log_display()

            step_label.configure(text=f"Шаг: {current_data['step']}")

            # Возвращаем пояснение и срез таблицы предыдущего шага либо начальное состояние
            if current_data["step"] > 0:
                prev_item = current_data["log_full_array"][current_data["step"] - 1]
                explanation_label.configure(text=prev_item["explanation"])
                if "table" in prev_item:
                    current_data["table"] = list(prev_item["table"])
                    render_table()
            else:
                explanation_label.configure(text="Исходное состояние данных. Шаг 0.")
                if initial_data and "table" in initial_data:
                    current_data["table"] = copy.deepcopy(initial_data["table"])
                    render_table()

    def play_tick():
        """Один такт циклического воспроизведения шагов по таймеру."""
        nonlocal play_job_id
        if not current_data["is_running"]:
            return

        if current_data["step"] < len(current_data["log_full_array"]):
            on_step_forward()
        else:
            toggle_play()
            explanation_label.configure(text="Сортировка успешно завершена!")

    def toggle_play():
        """Переключает воспроизведение между активным режимом и паузой."""
        nonlocal play_job_id

        # Если шаги еще не были рассчитаны, вычисляем их
        if not current_data.get("log_full_array"):
            steps = sort_table()
            current_data["log_full_array"] = steps
            current_data["step"] = 0

            # В случае ошибки выбора атрибута или файла прерываем старт
            if steps and steps[0].get("action") in ("error", "warning"):
                log_current_array.append(steps[0]["log_line"])
                update_log_display()
                explanation_label.configure(text=steps[0]["explanation"])
                return

        # Инвертируем состояние активности плеера
        current_data["is_running"] = not current_data["is_running"]

        if current_data["is_running"]:
            # Если дошли до конца и снова нажали Старт — перезапускаем воспроизведение с начала
            if current_data["step"] >= len(current_data["log_full_array"]):
                current_data["step"] = 0
                if initial_data and "table" in initial_data:
                    current_data["table"] = copy.deepcopy(initial_data["table"])
                    render_table()
                log_current_array.clear()
                log_current_array.append("Лог:\n")
                update_log_display()
                step_label.configure(text="Шаг: 0")

            # Визуальное переключение кнопки в состояние «Пауза»
            btn_play.configure(
                text="⏸ Пауза",
                fg_color="#C62828",
                hover_color="#8E0000"
            )
            # Запуск первого шага с текущей задержкой
            play_job_id = frame.after(current_data["delay_ms"], play_tick)
        else:
            # Остановка фонового таймера Tkinter при постановке на паузу
            if play_job_id is not None:
                frame.after_cancel(play_job_id)
                play_job_id = None

            # Возврат кнопки в состояние «Старт»
            btn_play.configure(
                text="▶ Старт",
                fg_color="#2E7D32",
                hover_color="#1B5E20"
            )

    def on_reset():
        """Сбрасывает процесс воспроизведения к исходному начальному состоянию."""
        nonlocal play_job_id
        if current_data["is_running"]:
            toggle_play()

        if play_job_id is not None:
            frame.after_cancel(play_job_id)
            play_job_id = None

        # Полное восстановление состояния current_data из глубокой копии начального состояния
        if initial_data:
            current_data.clear()
            current_data.update(copy.deepcopy(initial_data))
            render_table()
            update_temp_files_display()
        else:
            current_data["step"] = 0
            current_data["log_full_array"] = []

        # Сброс текстового лога к начальной информации о файле
        log_current_array.clear()
        log_current_array.append("Лог:\n")
        if current_data.get("file_path"):
            log_current_array.append(
                f"[Файл]: {os.path.basename(current_data['file_path'])}\n"
                f"[Статус]: Выполнен сброс шагов к исходному состоянию.\n\n"
            )
        update_log_display()

        step_label.configure(text=f"Шаг: {current_data['step']}")
        explanation_label.configure(text="Состояние сброшено в начало. Нажмите «▶ Старт» или «→».")

    def save_file():
        """Сохраняет текущую отсортированную таблицу в выбранный CSV-файл на диске."""
        headers = current_data.get("headers", [])
        result_path = current_data.get("sorted_result_path")
        table_rows = current_data.get("table", [])

        # Проверка наличия данных перед сохранением
        if not headers or (not result_path and not table_rows):
            explanation_label.configure(text="Нет данных для сохранения! Сначала загрузите файл.")
            return

        # Формирование предлагаемого имени результирующего файла
        orig_name = os.path.basename(current_data.get("file_path", "table.csv"))
        suggested_name = f"sorted_{orig_name}"

        save_path = filedialog.asksaveasfilename(
            title="Сохранить отсортированную таблицу",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=suggested_name
        )

        if not save_path:
            return

        try:
            # Сохранение с сохранением кодировки и исходного разделителя таблицы
            delimiter = current_data.get("delimiter", ";")
            with open(save_path, mode="w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f, delimiter=delimiter)
                if headers:
                    writer.writerow(headers)
                if result_path and os.path.exists(result_path):
                    with open(result_path, mode="r", encoding="utf-8", newline="") as result_file:
                        for row in csv.reader(result_file):
                            writer.writerow(row)
                else:
                    writer.writerows(table_rows)

            saved_name = os.path.basename(save_path)
            explanation_label.configure(text=f"Таблица успешно сохранена: {saved_name}")
            log_current_array.append(
                f"\n[Файл сохранен]: {saved_name}\n"
                f"[Записей]: {current_data.get('sorted_result_count', len(table_rows))}\n"
                f"[Путь]: {save_path}\n\n"
            )
            update_log_display()

        except Exception as e:
            explanation_label.configure(text=f"Ошибка сохранения файла: {e}")

    def on_delay_change(val):
        """Обновляет значение задержки шагов в миллисекундах."""
        current_data["delay_ms"] = int(val)
        lbl_delay.configure(text=f"Задержка: {int(val)} мс")

    def parse_cell(val: str):
        """Очищает строку от пробелов и приводит к числу, если это возможно."""
        val = val.strip()
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    def detect_delimiter(sample):
        """Определяет разделитель по заголовку, если Sniffer не справился."""
        try:
            return csv.Sniffer().sniff(sample, delimiters=";,|\t").delimiter
        except csv.Error:
            for line in sample.splitlines():
                if line.strip():
                    candidates = [(line.count(char), char) for char in (";", ",", "|", "\t")]
                    count, delimiter = max(candidates)
                    if count:
                        return delimiter
                    break
            return ","

    def load_file():
        """Загружает метаданные и первые 20 строк файла для предпросмотра."""
        nonlocal play_job_id
        if current_data.get("is_running"):
            current_data["is_running"] = False
            if play_job_id is not None:
                frame.after_cancel(play_job_id)
                play_job_id = None
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            preview_limit = 20

            with open(file_path, mode="r", encoding="utf-8-sig") as f:
                # Читаем небольшой фрагмент для определения разделителя
                sample = f.read(2048)
                f.seek(0)
                delimiter = detect_delimiter(sample)

                reader = csv.reader(f, delimiter=delimiter)

                # Считываем только заголовок (первая строка)
                headers = next(reader, None)
                if not headers:
                    explanation_label.configure(text="Выбранный файл пуст!")
                    return

                headers = [h.strip() for h in headers]

                # Считываем ровно до 20 строк для превью через итератор
                preview_rows = []
                for row in islice(reader, preview_limit):
                    if row:
                        parsed_row = [parse_cell(cell) for cell in row[:len(headers)]]
                        if len(parsed_row) < len(headers):
                            parsed_row.extend([""] * (len(headers) - len(parsed_row)))
                        preview_rows.append(parsed_row)

            # Сохраняем метаданные и превью в состояние
            current_data["file_path"] = file_path
            current_data["headers"] = headers
            current_data["table"] = preview_rows  # Только превью! Полный файл остается на диске
            current_data["delimiter"] = delimiter
            current_data["step"] = 0
            current_data["log_full_array"] = []
            current_data.pop("sorted_full_table", None)
            old_result = current_data.pop("sorted_result_path", None)
            current_data.pop("sorted_result_count", None)
            if old_result:
                try:
                    os.remove(old_result)
                except OSError:
                    pass
            current_data["temp_files"] = []
            update_temp_files_display()
            current_data["is_running"] = False
            current_data["temp_files"] = []
            current_data["sort_direction"] = None
            current_data["key_column"] = None

            # Глубокое копирование начального состояния для восстановления при сбросе
            initial_data.clear()
            initial_data.update(copy.deepcopy(current_data))
            update_temp_files_display()

            file_name = os.path.basename(file_path)

            # Выводим информацию в лог
            log_current_array.clear()
            log_current_array.append("Лог:\n")
            log_current_array.append(
                f"[Файл выбран]: {file_name}\n"
                f"[Колонки]: {', '.join(headers)}\n"
                f"[Превью]: Загружено первых {len(preview_rows)} записей для показа.\n"
                f"[Режим]: внешняя сортировка. Подготовка формирует начальные серии, затем начинаются проходы слияния.\n\n"
            )
            update_log_display()

            # Обновление статус-бара
            step_label.configure(text="Шаг: 0")
            explanation_label.configure(
                text=f"Файл открыт: {file_name} (показано превью {len(preview_rows)} строк). Выберите атрибут."
            )

            # Прячем заглушку таблицы
            lbl_table_placeholder.pack_forget()
            render_table()

        except Exception as e:
            explanation_label.configure(text=f"Ошибка чтения: {e}")

    # ==========================================
    # 6. ВИДЖЕТЫ НИЖНЕЙ ПАНЕЛИ
    # ==========================================

    btn_step_back = ctk.CTkButton(
        player_frame,
        text="←",
        width=48,
        height=36,
        font=("Arial", 16, "bold"),
        fg_color="#37474F",
        hover_color="#263238",
        command=on_step_back
    )
    btn_step_back.grid(row=0, column=0, padx=(0, 5))

    btn_play = ctk.CTkButton(
        player_frame,
        text="▶ Старт",
        width=95,
        height=36,
        font=("Arial", 12, "bold"),
        fg_color="#2E7D32",
        hover_color="#1B5E20",
        command=toggle_play
    )
    btn_play.grid(row=0, column=1, padx=5)

    btn_step_forward = ctk.CTkButton(
        player_frame,
        text="→",
        width=48,
        height=36,
        font=("Arial", 16, "bold"),
        fg_color="#37474F",
        hover_color="#263238",
        command=on_step_forward
    )
    btn_step_forward.grid(row=0, column=2, padx=5)

    btn_reset = ctk.CTkButton(
        player_frame,
        text="🔄",
        width=48,
        height=36,
        font=("Arial", 13, "bold"),
        fg_color="#37474F",
        hover_color="#263238",
        command=on_reset
    )
    btn_reset.grid(row=0, column=3, padx=(5, 0))

    lbl_delay = ctk.CTkLabel(
        speed_frame,
        text=f"Задержка: {current_data['delay_ms']} мс",
        font=("Arial", 18, "bold")
    )
    lbl_delay.grid(row=0, column=0, padx=(0, 10))

    delay_slider = ctk.CTkSlider(
        speed_frame,
        from_=10,
        to=1000,
        number_of_steps=99,
        width=160,
        command=on_delay_change
    )
    delay_slider.set(current_data["delay_ms"])
    delay_slider.grid(row=0, column=1)

    btn_load = ctk.CTkButton(
        file_frame,
        text="📂 Загрузить CSV",
        width=48,
        height=36,
        font=("Arial", 13, "bold"),
        fg_color="#37474F",
        hover_color="#263238",
        command=load_file
    )
    btn_load.grid(row=0, column=0, padx=(5, 0))

    btn_save = ctk.CTkButton(
        file_frame,
        text="💾 Сохранить результат",
        width=48,
        height=36,
        font=("Arial", 13, "bold"),
        fg_color="#37474F",
        hover_color="#263238",
        command=save_file
    )
    btn_save.grid(row=0, column=1, padx=(5, 0))

    return frame
