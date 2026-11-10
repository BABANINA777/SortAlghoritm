"""Модуль экрана второго практического задания: алгоритмы внешней сортировки."""

import customtkinter as ctk
from tkinter import filedialog
import csv
import os
from itertools import islice


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
        "key_column": 0
    }

    log_current_array = ["Лог:\n"]

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

    def render_table():
        # Контейнер для отображения лога и будущей таблицы
        table_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        table_frame.grid(row=0, column=1, sticky="nsew")
        #TODO отрисовывает таблицу из текущих данных в curentdata. кнопки у атрибутов таблицы кликабельны. имеют 3 состояния. выбранна и стрелочка вверх. выбрана и стрелочка вниз. не выбрана


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

    # ==========================================
    # 5. ОБРАБОТЧИКИ УПРАВЛЕНИЯ BOTTOM PANEL
    # ==========================================
    def on_step_forward():
        """Переход к следующему шагу внешней сортировки."""
        pass

    def on_step_back():
        """Откат к предыдущему шагу сортировки."""
        pass

    def toggle_play():
        # TODO производит сортировку и логгирует ее
        """Старт и пауза циклического воспроизведения шагов."""
        pass

    def on_reset():
        """Сброс состояния сортировки к исходным данным."""
        pass

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

    def load_file():
        """Загружает метаданные и первые 20 строк файла для предпросмотра."""
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
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = ","

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
                        preview_rows.append([parse_cell(cell) for cell in row])

            # Сохраняем метаданные и превью в состояние
            current_data["file_path"] = file_path
            current_data["headers"] = headers
            current_data["table"] = preview_rows  # Только превью! Полный файл остается на диске
            current_data["step"] = 0
            current_data["log_full_array"] = []

            file_name = os.path.basename(file_path)

            # Выводим информацию в лог
            log_current_array.clear()
            log_current_array.append("Лог:\n")
            log_current_array.append(
                f"[Файл выбран]: {file_name}\n"
                f"[Колонки]: {', '.join(headers)}\n"
                f"[Превью]: Загружено первых {len(preview_rows)} записей для показа.\n"
                f"[Режим]: Внешняя сортировка порциями (буфер RAM = 10 строк).\n\n"
            )
            update_log_display()

            # Обновление статус-бара
            step_label.configure(text="Шаг: 0")
            explanation_label.configure(
                text=f"Файл открыт: {file_name} (показано превью {len(preview_rows)} строк). Выберите атрибут."
            )

            # Прячем заглушку таблицы
            lbl_table_placeholder.pack_forget()

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
        command=load_file
    )
    btn_save.grid(row=0, column=1, padx=(5, 0))

    return frame
